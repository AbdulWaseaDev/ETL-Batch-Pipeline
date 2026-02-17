import json
from pathlib import Path

import yaml

from src.extract import extract_data


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload):
        self._payload = payload

    def get(self, _url, timeout):
        assert timeout == (5, 30)
        return _FakeResponse(self._payload)


def test_extract_data_writes_raw_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    raw_path = Path("data/raw/posts.json")
    config = {"api": {"url": "https://example.test/posts"}, "paths": {"raw_data": str(raw_path)}}
    (tmp_path / "config" / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")

    payload = [{"id": 1, "title": "hello"}]
    monkeypatch.setattr("src.extract._build_retrying_session", lambda: _FakeSession(payload))

    extract_data()

    written = json.loads((tmp_path / raw_path).read_text(encoding="utf-8"))
    assert written == payload
