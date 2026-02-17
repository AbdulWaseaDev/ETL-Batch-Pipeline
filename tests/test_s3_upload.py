from pathlib import Path

import yaml

from src.s3_upload import upload_to_s3


def test_upload_to_s3_uses_expected_bucket_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "data" / "processed").mkdir(parents=True)

    processed_file = Path("data/processed/posts_clean.csv")
    (tmp_path / processed_file).write_text("user_id,post_id,title,body,ingestion_time\n", encoding="utf-8")
    config = {"paths": {"processed_data": str(processed_file)}}
    (tmp_path / "config" / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test-secret")
    monkeypatch.setenv("BUCKET_NAME", "unit-test-bucket")
    monkeypatch.setenv("REGION", "us-east-1")

    uploads = []

    class FakeS3Client:
        def upload_file(self, local_file, bucket, s3_key):
            uploads.append((local_file, bucket, s3_key))

    monkeypatch.setattr("src.s3_upload.boto3.client", lambda *args, **kwargs: FakeS3Client())

    upload_to_s3()

    assert uploads == [(str(processed_file), "unit-test-bucket", "processed/posts_clean.csv")]
