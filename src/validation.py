REQUIRED_COLUMNS = {"userId", "id", "title", "body"}


def validate_data(df):
    if df.empty:
        raise ValueError("DataFrame is empty")

    missing_columns = REQUIRED_COLUMNS.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    required_df = df[list(REQUIRED_COLUMNS)]
    if required_df.isnull().any().any():
        raise ValueError("Null values found in required columns")

    if (df["id"].astype(str).str.strip() == "").any() or (df["userId"].astype(str).str.strip() == "").any():
        raise ValueError("Blank id/userId values are not allowed")

    if not df["id"].apply(lambda x: str(x).isdigit()).all():
        raise ValueError("Column id must contain only positive integers")

    if not df["userId"].apply(lambda x: str(x).isdigit()).all():
        raise ValueError("Column userId must contain only positive integers")

    if (df["title"].astype(str).str.strip() == "").any():
        raise ValueError("Column title must not contain blank values")

    if (df["body"].astype(str).str.strip() == "").any():
        raise ValueError("Column body must not contain blank values")

    if df["id"].duplicated().any():
        raise ValueError("Duplicate id values detected")

    return True
