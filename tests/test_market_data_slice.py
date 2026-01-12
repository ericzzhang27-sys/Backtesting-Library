import pandas as pd
import numpy as np
import pytest

try:
    from btlib.data.market_data import MarketData
except Exception:  # pragma: no cover
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT / "src"))
    from btlib.data import MarketData


def _close_df_with_nans() -> tuple[pd.DataFrame, pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    t0 = pd.Timestamp("2024-01-01")
    t1 = pd.Timestamp("2024-01-02")
    t2 = pd.Timestamp("2024-01-03")
    close = pd.DataFrame(
        {
            "AAPL": [100.0, np.nan, 102.0],
            "MSFT": [200.0, 201.0, 202.0],
        },
        index=pd.DatetimeIndex([t0, t1, t2]),
    )
    return close, t0, t1, t2


def test_slice_upto_is_inclusive() -> None:
    close, t0, t1, t2 = _close_df_with_nans()
    md = MarketData(close)
    s = md.slice_upto(t1)
    assert list(s.index) == [t0, t1]
    assert len(s) == 2


def test_slice_upto_no_future_leakage() -> None:
    close, _, t1, _ = _close_df_with_nans()
    md = MarketData(close)
    s = md.slice_upto(t1)
    assert s.index.max() == t1


def test_get_close_requires_exact_timestamp() -> None:
    close, _, t1, _ = _close_df_with_nans()
    md = MarketData(close)
    missing = t1 + pd.Timedelta(days=1, hours=1)  # not in index
    with pytest.raises(KeyError):
        md.get_close(missing)


def test_tradable_symbols_drops_only_nans() -> None:
    close, _, t1, _ = _close_df_with_nans()
    md = MarketData(close)
    tradable = md.tradable_symbols(t1)
    assert tradable == ["MSFT"]


def test_nans_preserved_in_raw_access() -> None:
    close, _, t1, _ = _close_df_with_nans()
    md = MarketData(close)
    row = md.get_close(t1)
    assert np.isnan(row["AAPL"])
    assert np.isfinite(row["MSFT"])


def test_slice_upto_before_first_returns_empty_df() -> None:
    close, t0, _, _ = _close_df_with_nans()
    md = MarketData(close)
    s = md.slice_upto(t0 - pd.Timedelta(days=10))
    assert isinstance(s, pd.DataFrame)
    assert s.empty
    # keep the same columns (helps warm-up logic)
    assert list(s.columns) == list(close.columns)
