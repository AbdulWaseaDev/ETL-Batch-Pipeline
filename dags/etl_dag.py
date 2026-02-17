from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os
from src.logger import get_logger
from src.s3_upload import upload_to_s3

logger = get_logger(__name__)
logger.info("Starting ETL pipeline...")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.extract import extract_data
from src.transform import transform_data
from src.load import load_to_postgres

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
        python_callable=extract_data
    )

    transform_task = PythonOperator(
        task_id="transform",
        python_callable=transform_data
    )

    upload_task = PythonOperator(
        task_id="upload_to_s3",
        python_callable=upload_to_s3
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=load_to_postgres
    )

    extract_task >> transform_task >> upload_task >> load_task
