import pandas as pd
import yaml
from datetime import datetime, timezone
try:
    from src.validation import validate_data
    from src.logger import get_logger
except ModuleNotFoundError:
    from validation import validate_data
    from logger import get_logger

logger = get_logger(__name__)

def transform_data():
    logger.info("Starting data transformation...")
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    raw_path = config["paths"]["raw_data"]
    processed_path = config["paths"]["processed_data"]

    df = pd.read_json(raw_path)

    validate_data(df)

    df.rename(columns={
        "userId": "user_id",
        "id": "post_id"
    }, inplace=True)

    df["ingestion_time"] = datetime.now(timezone.utc)

    df.to_csv(processed_path, index=False)

    logger.info("Transformation completed. Wrote data to %s", processed_path)

if __name__ == "__main__":
    transform_data()
