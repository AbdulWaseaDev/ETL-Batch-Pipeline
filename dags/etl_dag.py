from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def run_extract():
    from src.extract import extract_data
    extract_data()


def run_transform():
    from src.transform import transform_data
    transform_data()


def run_upload_to_s3():
    from src.s3_upload import upload_to_s3
    upload_to_s3()


def run_load():
    from src.load import load_to_postgres
    load_to_postgres()

default_args = {
    "owner": "etl-team",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 1, 1),
    "execution_timeout": timedelta(minutes=10),
}

with DAG(
    dag_id="batch_etl_pipeline",
    default_args=default_args,
    schedule="@daily",
    catchup=False
) as dag:

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=run_extract
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=run_transform
    )

    upload_task = PythonOperator(
        task_id="upload_to_s3",
        python_callable=run_upload_to_s3
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=run_load
    )

    extract_task >> transform_task >> upload_task >> load_task
