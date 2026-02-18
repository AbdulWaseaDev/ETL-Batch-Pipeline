ARG AIRFLOW_IMAGE=apache/airflow:slim-3.1.7-python3.12
ARG AIRFLOW_VERSION=3.1.7
ARG PYTHON_VERSION=3.12
FROM ${AIRFLOW_IMAGE}
ARG AIRFLOW_VERSION
ARG PYTHON_VERSION

WORKDIR /opt/airflow

COPY requirements.txt /opt/airflow/requirements.txt

RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt" && \
    rm -f /opt/airflow/requirements.txt

COPY dags /opt/airflow/dags
COPY src /opt/airflow/src
COPY config /opt/airflow/config
COPY data /opt/airflow/data

ENV PYTHONPATH=/opt/airflow
