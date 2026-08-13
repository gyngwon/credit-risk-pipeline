"""
Credit Risk Pipeline DAG

Simple 3-task chain: extract -> dbt run -> dbt test.
Orchestration logic intentionally kept minimal; the analytical depth
lives in the dbt models themselves (see dbt_project/models/).
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.bash import BashOperator

PROJECT_ROOT = "/Users/gyeongwonsong/credit-risk-pipeline"
DBT_PROJECT_DIR = f"{PROJECT_ROOT}/dbt_project"
VENV_PYTHON = f"{PROJECT_ROOT}/.venv/bin/python"
VENV_DBT = f"{PROJECT_ROOT}/.venv/bin/dbt"


def run_extract():
    import subprocess

    result = subprocess.run(
        [VENV_PYTHON, f"{PROJECT_ROOT}/extract/load_raw.py"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(f"Extract failed:\n{result.stderr}")


default_args = {
    "owner": "gyeongwon",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="credit_risk_pipeline",
    description="Extract Lending Club data, build dbt models, and validate with dbt tests.",
    default_args=default_args,
    schedule=None,  # manual trigger for this portfolio project; a real deployment
                     # would set e.g. "@daily"
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["credit-risk", "dbt", "analytics-engineering"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_raw_loans",
        python_callable=run_extract,
    )

    dbt_run_task = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_PROJECT_DIR} && {VENV_DBT} run",
    )

    dbt_test_task = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_PROJECT_DIR} && {VENV_DBT} test",
    )

    extract_task >> dbt_run_task >> dbt_test_task