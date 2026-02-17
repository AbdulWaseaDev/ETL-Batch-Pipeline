import pandas as pd
import pytest

from src.validation import validate_data


def test_validate_data_rejects_missing_columns():
    df = pd.DataFrame([{"id": 1, "title": "a", "body": "b"}])
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_data(df)


def test_validate_data_rejects_duplicate_ids():
    df = pd.DataFrame(
        [
            {"userId": 1, "id": 10, "title": "a", "body": "x"},
            {"userId": 1, "id": 10, "title": "b", "body": "y"},
        ]
    )
    with pytest.raises(ValueError, match="Duplicate id"):
        validate_data(df)


def test_validate_data_accepts_valid_dataframe():
    df = pd.DataFrame(
        [
            {"userId": 1, "id": 10, "title": "hello", "body": "world"},
            {"userId": 2, "id": 11, "title": "foo", "body": "bar"},
        ]
    )
    assert validate_data(df) is True
