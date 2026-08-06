"""
Week 1: Extract raw Lending Club CSV data and load it into
- Local DuckDB (for fast local development/testing)
- BigQuery (for cloud-scale production, optional)
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import duckdb
from dotenv import load_dotenv

# ── Config ──────────────────────────────────────────
load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "loan.csv"          # adjust to your actual filename
DUCKDB_PATH = Path(__file__).parent.parent / "credit_risk.duckdb"
RAW_TABLE_NAME = "raw_loans"
SAMPLE_SIZE = 100_000                     # set to None to load the full file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ── 1. Extract CSV ────────────────────────────────
def extract_csv(csv_path: Path, sample_size: int | None = None) -> pd.DataFrame:
    if not csv_path.exists():
        logger.error(f"File not found: {csv_path}")
        sys.exit(1)

    logger.info(f"Reading CSV: {csv_path}")

    if sample_size:
        df = pd.read_csv(csv_path, low_memory=False, nrows=sample_size)
        logger.info(f"Sampled {len(df):,} rows (first {sample_size:,} rows of the file)")
    else:
        df = pd.read_csv(csv_path, low_memory=False)
        logger.info(f"Rows loaded: {len(df):,}, columns: {len(df.columns)}")

    return df


# ── 2. Load to DuckDB (local dev) ─────────────────
def load_to_duckdb(df: pd.DataFrame, db_path: Path, table_name: str) -> None:
    con = duckdb.connect(str(db_path))

    # Add a load-timestamp column so we can trace when data was ingested
    df = df.copy()
    df["_loaded_at"] = datetime.utcnow()

    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
    row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    logger.info(f"[DuckDB] Loaded {row_count:,} rows into '{table_name}' → {db_path}")
    con.close()


# ── 3. Load to BigQuery (cloud, optional) ─────────
def load_to_bigquery(df: pd.DataFrame, table_name: str) -> None:
    from google.cloud import bigquery

    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("GCP_DATASET")

    if not project_id or not dataset:
        logger.warning("GCP_PROJECT_ID or GCP_DATASET not set in .env — skipping BigQuery load.")
        return

    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.{dataset}.{table_name}"

    df = df.copy()
    df["_loaded_at"] = datetime.utcnow()

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # wait for the job to complete

    table = client.get_table(table_id)
    logger.info(f"[BigQuery] Loaded {table.num_rows:,} rows into '{table_id}'")


# ── Main ──────────────────────────────────────────
if __name__ == "__main__":
    df = extract_csv(CSV_PATH, sample_size=SAMPLE_SIZE)
    load_to_duckdb(df, DUCKDB_PATH, RAW_TABLE_NAME)

    # Skips automatically if GCP credentials/config aren't set up yet
    load_to_bigquery(df, RAW_TABLE_NAME)

    logger.info("Load complete.")