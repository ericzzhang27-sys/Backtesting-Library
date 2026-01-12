import pandas as pd
def validate_price_frame(df: pd.DataFrame) -> None:
    if not isinstance(df,pd.DataFrame):
        raise TypeError("Price data must be a pandas DataFrame")
    if not isinstance(df.index,pd.DatetimeIndex):
        raise TypeError("Price data index must be a DatetimeIndex")
    if not df.index.is_monotonic_increasing:
        raise ValueError("Price data index must be sorted in ascending order")
    if df.index.has_duplicates:
        raise ValueError("Price data index must not contain duplicates")
    if not df.columns.is_unique:
        raise ValueError("Price data columns must be unique (no duplicate column names)")

    if not all(pd.api.types.is_numeric_dtype(dt) for dt in df.dtypes):
        raise TypeError("All price data columns must be numeric dtype")


    if df.empty:
        raise ValueError("Price data DataFrame is empty")
def require_columns(df: pd.DataFrame, required: list[str])-> None:
    pass
