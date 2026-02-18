# ETL Batch Pipeline

A Python batch ETL pipeline orchestrated with Apache Airflow 3.1 and Docker Compose.

The pipeline:
1. Extracts posts from `https://jsonplaceholder.typicode.com/posts`
2. Validates and transforms the dataset
3. Uploads processed CSV to Amazon S3
4. Loads data incrementally into PostgreSQL using `COPY` + upsert

## Quick Start (5 commands)
```powershell
Copy-Item .env.example .env
# Fill .env with real secrets/credentials before continuing
docker compose --env-file .env up airflow-init
docker compose --env-file .env up -d --build
docker compose --env-file .env exec airflow-scheduler airflow dags trigger batch_etl_pipeline
docker compose --env-file .env logs airflow-scheduler --tail=120
```

## Tech Stack
- Python 3.12+
- Apache Airflow 3.1.7
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
|-- Dockerfile
|-- requirements.txt
|-- requirements-dev.txt
|-- .env.example
`-- readme.md
```

## Pipeline Flow
- DAG: `batch_etl_pipeline`
- Schedule: `@daily`
- Start date: `2026-01-01`
- Catchup: `False`
- Task order: `extract -> transform -> upload_to_s3 -> load`

Task details:
- `extract`: reads API URL from `config/config.yaml`, writes `data/raw/posts.json`
- `transform`: validates required columns and values, renames fields (`userId -> user_id`, `id -> post_id`), adds `ingestion_time`, writes `data/processed/posts_clean.csv`
- `upload_to_s3`: uploads processed CSV to `s3://<BUCKET_NAME>/processed/posts_clean.csv`
- `load`: creates target table if needed, stages CSV via `COPY`, and upserts by `post_id`

## Configuration
### 1. App config (`config/config.yaml`)
```yaml
api:
  url: "https://jsonplaceholder.typicode.com/posts"

paths:
  raw_data: "data/raw/posts.json"
  processed_data: "data/processed/posts_clean.csv"
```

### 2. Environment variables
Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Required values in `.env`:

```env
POSTGRES_USER=etl_user
POSTGRES_PASSWORD=replace_with_strong_password
POSTGRES_DB=etl_db
AIRFLOW_IMAGE=apache/airflow:slim-3.1.7-python3.12
AIRFLOW_UID=50000

AIRFLOW_FERNET_KEY=replace_with_fernet_key
AIRFLOW_WEBSERVER_SECRET_KEY=replace_with_long_random_secret_at_least_64_chars
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

## Secrets Generation Commands
Use these PowerShell-safe commands to generate strong values.

Generate Airflow Fernet key:
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Generate Airflow webserver secret key (also used for API/JWT secret in compose):
```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Generate strong Postgres password:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

Generate strong Airflow admin password:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(20))"
```

## Local Python Setup (without Docker)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Run ETL manually:
```powershell
python src\extract.py
python src\transform.py
python src\s3_upload.py
python src\load.py
```

Run tests:
```powershell
pytest -q
```

## Docker Commands (Airflow + Postgres)
All Docker commands below assume `.env` exists.

Validate compose config:
```powershell
docker compose --env-file .env config
```

Build images:
```powershell
docker compose --env-file .env build
```

Initialize Airflow metadata + admin user (one-off):
```powershell
docker compose --env-file .env up airflow-init
```

Start all services in background:
```powershell
docker compose --env-file .env up -d
```

Start and rebuild:
```powershell
docker compose --env-file .env up -d --build
```

Force recreate containers:
```powershell
docker compose --env-file .env up -d --build --force-recreate
```

Show service status:
```powershell
docker compose --env-file .env ps
```

Stop services:
```powershell
docker compose --env-file .env stop
```

Start previously stopped services:
```powershell
docker compose --env-file .env start
```

Restart services:
```powershell
docker compose --env-file .env restart
```

Stop and remove containers/network:
```powershell
docker compose --env-file .env down
```

Stop and remove containers, network, and named volumes (destructive):
```powershell
docker compose --env-file .env down -v
```

## Docker Logs Commands
Show recent logs from all services:
```powershell
docker compose --env-file .env logs --tail=200
```

Follow all logs live:
```powershell
docker compose --env-file .env logs -f
```

Check init logs:
```powershell
docker compose --env-file .env logs airflow-init --tail=120
```

Check webserver logs:
```powershell
docker compose --env-file .env logs airflow-webserver --tail=120
```

Check scheduler logs:
```powershell
docker compose --env-file .env logs airflow-scheduler --tail=120
```

Check DAG processor logs:
```powershell
docker compose --env-file .env logs airflow-dag-processor --tail=120
```

Check Postgres logs:
```powershell
docker compose --env-file .env logs postgres --tail=120
```

## Airflow CLI Commands (inside containers)
List DAGs:
```powershell
docker compose --env-file .env exec airflow-scheduler airflow dags list
```

List DAG import errors:
```powershell
docker compose --env-file .env exec airflow-scheduler airflow dags list-import-errors
```

Show tasks for this DAG:
```powershell
docker compose --env-file .env exec airflow-scheduler airflow tasks list batch_etl_pipeline
```

Trigger DAG run:
```powershell
docker compose --env-file .env exec airflow-scheduler airflow dags trigger batch_etl_pipeline
```

Run one task for a specific execution date:
```powershell
docker compose --env-file .env exec airflow-scheduler airflow tasks test batch_etl_pipeline extract 2026-01-01
```

Check scheduler health job:
```powershell
docker compose --env-file .env exec airflow-scheduler sh -c 'airflow jobs check --job-type SchedulerJob --hostname "$HOSTNAME"'
```

## PostgreSQL Commands
Use values from your `.env` (defaults are `etl_user` and `etl_db`).

Open `psql` shell:
```powershell
docker compose --env-file .env exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>
```

Quick row count from `posts` table:
```powershell
docker compose --env-file .env exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB> -c "SELECT COUNT(*) FROM posts;"
```

Preview latest loaded records:
```powershell
docker compose --env-file .env exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB> -c "SELECT post_id, user_id, ingestion_time FROM posts ORDER BY ingestion_time DESC LIMIT 10;"
```

## API and UI Access
- Airflow UI: `http://localhost:8080`
- Health endpoint: `http://localhost:8080/api/v2/monitor/health`
- Login using `.env` values for:
  - `AIRFLOW_ADMIN_USERNAME`
  - `AIRFLOW_ADMIN_PASSWORD`

## Troubleshooting
If DAG appears but `extract` fails with `PermissionError` for `data/raw/posts.json` (Linux/macOS hosts):

```bash
sudo mkdir -p data/raw data/processed
sudo chown -R 50000:0 data
sudo chmod -R ug+rwX data
```

If scheduler shows auth/token issues after changing `.env` or compose config:

```powershell
docker compose --env-file .env down
docker compose --env-file .env up -d --build --force-recreate
```

If Airflow DAG is not visible:
```powershell
docker compose --env-file .env exec airflow-scheduler airflow dags list-import-errors
docker compose --env-file .env logs airflow-dag-processor --tail=200
```

## Tests
Run all tests:
```powershell
pytest -q
```

Run a specific test file:
```powershell
pytest -q tests\test_load.py
```

Current test coverage includes:
- DAG import and task dependencies
- Extract behavior with retrying session
- Validation rules
- S3 upload behavior
- PostgreSQL load path (mocked connection)

## Output Artifacts
- Raw extract: `data/raw/posts.json`
- Processed data: `data/processed/posts_clean.csv`
- App logs: `logs/pipeline.log`

## Notes
- Incremental load uses `ON CONFLICT (post_id) DO UPDATE`
- `docker-compose.yml` enforces required env vars using `${VAR:?required}`
- Keep `DB_HOST=postgres` when running via Docker Compose
- `AIRFLOW_WEBSERVER_SECRET_KEY` is reused for webserver/API/JWT secret config
