import boto3
import yaml
import os
from botocore.config import Config
from dotenv import load_dotenv
try:
    from src.logger import get_logger
except ModuleNotFoundError:
    from logger import get_logger

load_dotenv()
logger = get_logger(__name__)

def upload_to_s3():
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    local_file = config["paths"]["processed_data"]
    bucket = os.getenv("BUCKET_NAME")
    region = os.getenv("REGION")
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    if not os.path.exists(local_file):
        raise FileNotFoundError(f"Processed file not found: {local_file}")
    if not bucket:
        raise ValueError("BUCKET_NAME is required")
    if not region:
        raise ValueError("REGION is required")
    if not access_key or not secret_key:
        raise ValueError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(retries={"max_attempts": 5, "mode": "standard"}),
    )

    s3_key = "processed/posts_clean.csv"

    s3.upload_file(local_file, bucket, s3_key)

    logger.info("File uploaded to S3 successfully.")
if __name__ == "__main__":
    upload_to_s3()
