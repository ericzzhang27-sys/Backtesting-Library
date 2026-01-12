import pandas as pd
import numpy as np
import pytest

# Try normal package import first; fall back to repo-root import if needed.
try:
    from btlib.data.validators import validate_price_frame
except Exception:  # pragma: no cover
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT / "src"))
    from btlib.data.validators import validate_price_frame


def _good_close_df() -> pd.DataFrame:
    idx = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
    return pd.DataFrame(
        {
            "AAPL": [100.0, 101.0, 102.0],
            "MSFT": [200.0, 201.0, 202.0],
        },
        index=idx,
    )


def test_rejects_non_datetime_index() -> None:
    df = _good_close_df()
    df.index = [1, 2, 3]  # not a DatetimeIndex
    with pytest.raises((TypeError, ValueError)):
        validate_price_frame(df)


def test_rejects_unsorted_index() -> None:
    df = _good_close_df()
    df = df.iloc[[1, 0, 2]]  # out of order
    with pytest.raises((TypeError, ValueError)):
        validate_price_frame(df)


def test_rejects_duplicate_timestamps() -> None:
    idx = pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"])
    df = pd.DataFrame({"AAPL": [100.0, 101.0, 102.0]}, index=idx)
    with pytest.raises((TypeError, ValueError)):
        validate_price_frame(df)


def test_rejects_non_numeric_column() -> None:
    df = _good_close_df()
    df["AAPL"] = ["x", "y", "z"]  # object dtype
    with pytest.raises((TypeError, ValueError)):
        validate_price_frame(df)


def test_rejects_empty_df() -> None:
    df = pd.DataFrame()
    with pytest.raises((TypeError, ValueError)):
        validate_price_frame(df)
