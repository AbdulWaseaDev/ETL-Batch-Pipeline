import pandas as pd
from src.validation import validate_data

def test_validate_empty_df():
    df = pd.DataFrame()
    try:
        validate_data(df)
        assert False
    except ValueError:
        assert True
