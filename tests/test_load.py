from pathlib import Path

import yaml

from src.load import load_to_postgres


class FakeCursor:
    def __init__(self):
        self.executed = []
        self.copied = []
        self.fetchone_results = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        self.executed.append((str(query), params))
        query_text = str(query)
        if "to_regclass" in query_text:
            self.fetchone_results.append((None,))
        elif "SELECT EXISTS" in query_text:
            self.fetchone_results.append((False,))

    def fetchone(self):
        if not self.fetchone_results:
            return (None,)
        return self.fetchone_results.pop(0)

    def copy_expert(self, sql_statement, file_obj):
        self.copied.append((sql_statement, file_obj.read()))


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.committed = False
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def test_load_to_postgres_executes_create_copy_upsert(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "data" / "processed").mkdir(parents=True)

    csv_path = Path("data/processed/posts_clean.csv")
    (tmp_path / csv_path).write_text(
        "user_id,post_id,title,body,ingestion_time\n1,1,t,b,2026-01-01 00:00:00\n",
        encoding="utf-8",
    )
    config = {"paths": {"processed_data": str(csv_path)}}
    (tmp_path / "config" / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")

    monkeypatch.setenv("DB_TABLE", "posts")
    fake_conn = FakeConnection()
    monkeypatch.setattr("src.load._connect_with_retry", lambda: fake_conn)

    load_to_postgres()

    assert fake_conn.committed is True
    assert fake_conn.closed is True
    assert len(fake_conn.cursor_obj.executed) >= 3
    assert fake_conn.cursor_obj.copied
