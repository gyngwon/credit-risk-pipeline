"""
Extract raw Lending Club CSV data and load it into
- Local DuckDB (for fast local development/testing)
- BigQuery (for cloud-scale production, optional)

Sampling strategy: loans need time to reach a terminal status (Fully Paid /
Charged Off). Loans issued too recently are still "Current" and carry no
default signal. This script keeps only "matured" loans - issued at least
MATURITY_YEARS before the most recent issue date in the dataset - before
sampling, so the resulting sample has a realistic default rate.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import polars as pl
import duckdb
from dotenv import load_dotenv

# ── Config ──────────────────────────────────────────
load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "loan.csv"          # adjust to your actual filename
DUCKDB_PATH = Path(__file__).parent.parent / "credit_risk.duckdb"
RAW_TABLE_NAME = "raw_loans"
SAMPLE_SIZE = 100_000                     # set to None to keep all matured loans
MATURITY_YEARS = 5                        # matches the longest loan term (60 months)
RANDOM_SEED = 42

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ── 1. Extract & filter to matured loans ──────────
def extract_matured_loans(
    csv_path: Path,
    maturity_years: int,
    sample_size: int | None = None,
    seed: int = 42,
) -> pl.DataFrame:
    if not csv_path.exists():
        logger.error(f"File not found: {csv_path}")
        sys.exit(1)

    logger.info(f"Scanning CSV: {csv_path}")

    lazy_df = pl.scan_csv(csv_path, infer_schema_length=100_000, ignore_errors=True)

    lazy_df = lazy_df.with_columns(
        pl.col("issue_d").str.strptime(pl.Date, "%b-%Y", strict=False).alias("issue_date")
    )

    max_issue_date = lazy_df.select(pl.col("issue_date").max()).collect().item()
    cutoff_date = max_issue_date.replace(year=max_issue_date.year - maturity_years)
    logger.info(f"Most recent issue date: {max_issue_date} | maturity cutoff: {cutoff_date}")

    df_matured = lazy_df.filter(pl.col("issue_date") <= cutoff_date).collect()
    logger.info(f"Matured loans available: {df_matured.height:,}")

    if sample_size and df_matured.height > sample_size:
        df_matured = df_matured.sample(n=sample_size, seed=seed)

    logger.info(f"Final extract: {df_matured.height:,} rows, {df_matured.width} columns")
    return df_matured


# ── 2. Load to DuckDB (local dev) ─────────────────
def load_to_duckdb(df: pl.DataFrame, db_path: Path, table_name: str) -> None:
    con = duckdb.connect(str(db_path))

    df_with_meta = df.with_columns(pl.lit(datetime.utcnow()).alias("_loaded_at"))

    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_with_meta")
    row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    logger.info(f"[DuckDB] Loaded {row_count:,} rows into '{table_name}' → {db_path}")
    con.close()


# ── 3. Load to BigQuery (cloud, optional) ─────────
def load_to_bigquery(df: pl.DataFrame, table_name: str) -> None:
    from google.cloud import bigquery

    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("GCP_DATASET")

    if not project_id or not dataset:
        logger.warning("GCP_PROJECT_ID or GCP_DATASET not set in .env — skipping BigQuery load.")
        return

    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.{dataset}.{table_name}"

    df_pd = df.to_pandas()
    df_pd["_loaded_at"] = datetime.utcnow()

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df_pd, table_id, job_config=job_config)
    job.result()

    table = client.get_table(table_id)
    logger.info(f"[BigQuery] Loaded {table.num_rows:,} rows into '{table_id}'")


# ── Main ──────────────────────────────────────────
if __name__ == "__main__":
    df = extract_matured_loans(
        CSV_PATH,
        maturity_years=MATURITY_YEARS,
        sample_size=SAMPLE_SIZE,
        seed=RANDOM_SEED,
    )
    load_to_duckdb(df, DUCKDB_PATH, RAW_TABLE_NAME)

    # Skips automatically if GCP credentials/config aren't set up yet
    load_to_bigquery(df, RAW_TABLE_NAME)

    logger.info("Load complete.")