import os
import time

import psycopg2
from psycopg2 import sql
import yaml
from dotenv import load_dotenv

try:
    from src.logger import get_logger
except ModuleNotFoundError:
    from logger import get_logger

load_dotenv()
logger = get_logger(__name__)


def _connect_with_retry(max_attempts=3):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                connect_timeout=10,
            )
        except psycopg2.OperationalError as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            sleep_seconds = 2 ** attempt
            logger.warning("DB connect attempt %s failed. Retrying in %ss.", attempt, sleep_seconds)
            time.sleep(sleep_seconds)
    raise last_error


def _ensure_target_table(cur, table_name):
    # Serialize DDL by table name to avoid concurrent CREATE TABLE races.
    cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (table_name,))
    cur.execute("SELECT to_regclass(%s)", (table_name,))
    table_exists = cur.fetchone()[0] is not None
    if table_exists:
        return

    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typname = %s
              AND n.nspname = current_schema()
        )
        """,
        (table_name,),
    )
    conflicting_type_exists = cur.fetchone()[0]
    if conflicting_type_exists:
        raise RuntimeError(
            f"Cannot create table '{table_name}' because a PostgreSQL type with the same "
            "name already exists in the current schema. Rename DB_TABLE or drop/rename the "
            "conflicting type."
        )

    target_table = sql.Identifier(table_name)
    cur.execute(
        sql.SQL(
            """
            CREATE TABLE {} (
                user_id INT,
                post_id INT PRIMARY KEY,
                title TEXT,
                body TEXT,
                ingestion_time TIMESTAMP
            )
            """
        ).format(target_table)
    )


def load_to_postgres():
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    table_name = os.getenv("DB_TABLE")
    if not table_name:
        raise ValueError("DB_TABLE is required")

    file_path = config["paths"]["processed_data"]
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Processed file not found: {file_path}")

    conn = _connect_with_retry()
    try:
        with conn.cursor() as cur:
            _ensure_target_table(cur, table_name)
            target_table = sql.Identifier(table_name)

            cur.execute(
                """
                CREATE TEMP TABLE staging_posts (
                    user_id INT,
                    post_id INT,
                    title TEXT,
                    body TEXT,
                    ingestion_time TIMESTAMP
                ) ON COMMIT DROP
                """
            )

            with open(file_path, "r", encoding="utf-8") as f:
                next(f)  # Skip header
                cur.copy_expert(
                    """
                    COPY staging_posts
                    (user_id, post_id, title, body, ingestion_time)
                    FROM STDIN WITH CSV
                    """,
                    f,
                )

            cur.execute(
                sql.SQL(
                    """
                    INSERT INTO {} (user_id, post_id, title, body, ingestion_time)
                    SELECT s.user_id, s.post_id, s.title, s.body, s.ingestion_time
                    FROM (
                        SELECT DISTINCT ON (post_id)
                            user_id, post_id, title, body, ingestion_time
                        FROM staging_posts
                        ORDER BY post_id, ingestion_time DESC
                    ) s
                    ON CONFLICT (post_id) DO UPDATE
                    SET
                        user_id = EXCLUDED.user_id,
                        title = EXCLUDED.title,
                        body = EXCLUDED.body,
                        ingestion_time = EXCLUDED.ingestion_time
                    """
                ).format(target_table)
            )

        conn.commit()
        logger.info("Data loaded incrementally using COPY + upsert.")
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        load_to_postgres()
        print("Load completed.")
    except Exception as exc:
        print(f"Load failed: {exc}")
        raise
