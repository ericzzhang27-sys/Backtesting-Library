# tests/test_metrics_sharpe_cagr.py
import numpy as np
import pandas as pd

from btlib.metrics.performance import sharpe, cagr, total_return, equity_to_returns


def test_sharpe_zero_when_std_zero():
    # Your sharpe() drops the first element, so make index length >= 2
    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    rets = pd.Series([0.0, 0.01, 0.01, 0.01, 0.01], index=idx, dtype=float)

    s = sharpe(rets, rf=0.0, periods_per_year=252)
    assert s == 0.0


def test_cagr_matches_total_return_when_n_equals_periods_per_year():
    # equity grows 1% per period for exactly 252 periods
    periods_per_year = 252
    n_periods = 252  # number of return periods
    idx = pd.date_range("2024-01-01", periods=n_periods + 1, freq="D")

    eq = 100.0 * (1.01 ** np.arange(n_periods + 1))
    equity = pd.Series(eq, index=idx, dtype=float)

    tr = total_return(equity)
    cg = cagr(equity, periods_per_year=periods_per_year)

    # With n == periods_per_year, exponent is 1, so CAGR == total_return
    assert np.isclose(cg, tr, rtol=0, atol=1e-12)


def test_equity_to_returns_raises_on_nonpositive_equity():
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    equity = pd.Series([100.0, 0.0, 110.0], index=idx, dtype=float)

    try:
        _ = equity_to_returns(equity)
        assert False, "expected ValueError for nonpositive equity"
    except ValueError:
        pass
