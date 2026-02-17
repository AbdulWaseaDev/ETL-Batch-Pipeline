import requests
import json
import os
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
try:
    from src.logger import get_logger
except ModuleNotFoundError:
    from logger import get_logger

logger = get_logger(__name__)


def _build_retrying_session():
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def extract_data():
    logger.info("Starting data extraction...")
    with open("config/config.yaml") as f:
        config = yaml.safe_load(f)

    url = config["api"]["url"]
    raw_path = config["paths"]["raw_data"]

    session = _build_retrying_session()
    response = session.get(url, timeout=(5, 30))
    response.raise_for_status()

    os.makedirs(os.path.dirname(raw_path), exist_ok=True)

    with open(raw_path, "w") as f:
        json.dump(response.json(), f)

    logger.info(f"Extraction completed. Wrote data to {raw_path}")


if __name__ == "__main__":
    extract_data()
