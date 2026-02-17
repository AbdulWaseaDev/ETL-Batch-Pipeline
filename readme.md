# ETL Batch Pipeline

A Python batch ETL pipeline orchestrated with Apache Airflow.

The pipeline:
1. Extracts posts from `https://jsonplaceholder.typicode.com/posts`
2. Validates and transforms the dataset
3. Uploads processed CSV to Amazon S3
4. Loads data incrementally into PostgreSQL using `COPY` + upsert

## Tech Stack
- Python 3.12+
- Apache Airflow 3.1
- Pandas
- PostgreSQL (`psycopg2`)
- AWS S3 (`boto3`)
- Docker Compose
- Pytest

## Project Structure
```text
etl-batch-pipeline/
|-- dags/
|   `-- etl_dag.py
|-- src/
|   |-- extract.py
|   |-- transform.py
|   |-- validation.py
|   |-- s3_upload.py
|   |-- load.py
|   `-- logger.py
|-- config/
|   `-- config.yaml
|-- data/
|   |-- raw/
|   `-- processed/
|-- logs/
|   `-- pipeline.log
|-- tests/
|-- docker-compose.yml
|-- requirements.txt
|-- requirements-dev.txt
|-- .env.example
`-- readme.md
```

## Pipeline Flow
DAG: `batch_etl_pipeline`
Schedule: `@daily`
Task order: `extract -> transform -> upload_to_s3 -> load`

- `extract`: reads API URL from `config/config.yaml`, writes `data/raw/posts.json`
- `transform`: validates required columns and values, renames fields (`userId -> user_id`, `id -> post_id`), adds `ingestion_time`, writes `data/processed/posts_clean.csv`
- `upload_to_s3`: uploads processed CSV to `s3://<BUCKET_NAME>/processed/posts_clean.csv`
- `load`: creates target table if needed, stages CSV via `COPY`, and upserts by `post_id`

## Configuration
### 1. App config
`config/config.yaml`

```yaml
api:
  url: "https://jsonplaceholder.typicode.com/posts"

paths:
  raw_data: "data/raw/posts.json"
  processed_data: "data/processed/posts_clean.csv"
```

### 2. Environment variables
Copy `.env.example` to `.env` and set strong secrets:

```bash
POSTGRES_USER=etl_user
POSTGRES_PASSWORD=replace_with_strong_password
POSTGRES_DB=etl_db
AIRFLOW_IMAGE=apache/airflow:slim-3.1.7-python3.12

AIRFLOW_FERNET_KEY=replace_with_fernet_key
AIRFLOW_WEBSERVER_SECRET_KEY=replace_with_webserver_secret
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=replace_with_strong_admin_password
AIRFLOW_ADMIN_FIRSTNAME=Airflow
AIRFLOW_ADMIN_LASTNAME=Admin
AIRFLOW_ADMIN_EMAIL=admin@example.com

AWS_ACCESS_KEY_ID=replace_with_access_key
AWS_SECRET_ACCESS_KEY=replace_with_secret_key
BUCKET_NAME=replace_with_bucket_name
REGION=us-east-1

DB_USER=etl_user
DB_PASSWORD=replace_with_strong_password
DB_HOST=postgres
DB_PORT=5432
DB_NAME=etl_db
DB_TABLE=posts
```

## Setup (Local Python)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements-dev.txt
```

## Run ETL Manually
From project root:

```bash
python src/extract.py
python src/transform.py
python src/s3_upload.py
python src/load.py
```

## Run with Airflow (Docker Compose)
```bash
# Linux/macOS
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env

docker compose --env-file .env up -d
```

Airflow UI: `http://localhost:8080`

Login with `AIRFLOW_ADMIN_USERNAME` / `AIRFLOW_ADMIN_PASSWORD`, enable `batch_etl_pipeline`, then trigger a run.

## Testing
```bash
pytest -q
```

Current tests cover:
- DAG import and task dependencies
- Extract retry behavior
- Validation rules
- S3 upload behavior
- PostgreSQL load path (mocked connection)

## Output Artifacts
- Raw extract: `data/raw/posts.json`
- Processed data: `data/processed/posts_clean.csv`
- Logs: `logs/pipeline.log`

## Notes
- Incremental load uses `ON CONFLICT (post_id) DO UPDATE`
- `docker-compose.yml` requires explicit env values (`${VAR:?required}`)
- Use secure values for `POSTGRES_PASSWORD`, `AIRFLOW_FERNET_KEY`, and `AIRFLOW_WEBSERVER_SECRET_KEY`
