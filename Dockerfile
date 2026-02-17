ARG AIRFLOW_IMAGE=apache/airflow:slim-3.1.7-python3.12
FROM ${AIRFLOW_IMAGE}

WORKDIR /opt/airflow

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm -f /tmp/requirements.txt

COPY dags /opt/airflow/dags
COPY src /opt/airflow/src
COPY config /opt/airflow/config
COPY data /opt/airflow/data

ENV PYTHONPATH=/opt/airflow
