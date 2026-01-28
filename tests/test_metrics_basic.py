# tests/test_metrics_basic.py
import numpy as np
import pandas as pd

from btlib.metrics.performance import (
    equity_to_returns,
    total_return,
    cagr,
    volatility,
    sharpe,
    performance_summary,
    PerformanceMetrics,
)
from btlib.metrics.risk import max_drawdown


def _equity(values):
    idx = pd.date_range("2024-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=idx, name="equity", dtype=float)


def test_constant_equity_metrics():
    eq = _equity([100.0, 100.0, 100.0])

    rets = equity_to_returns(eq)
    assert list(rets.index) == list(eq.index)
    assert np.allclose(rets.to_numpy(), np.array([0.0, 0.0, 0.0]))

    assert total_return(eq) == 0.0
    assert cagr(eq, periods_per_year=252) == 0.0
    assert max_drawdown(eq) == 0.0

    # vol/sharpe should be 0 for constant returns
    assert volatility(rets, periods_per_year=252) == 0.0
    assert sharpe(rets, rf=0.0, periods_per_year=252) == 0.0


def test_single_step_increase_returns_and_total_return():
    eq = _equity([100.0, 110.0])
    rets = equity_to_returns(eq)

    # first return filled to 0 by convention
    assert rets.iloc[0] == 0.0
    assert np.isclose(rets.iloc[1], 0.10, rtol=0, atol=1e-12)

    assert np.isclose(total_return(eq), 0.10, rtol=0, atol=1e-12)


def test_performance_summary_returns_dataclass():
    ledger = pd.DataFrame({"equity": _equity([100.0, 100.0, 100.0])})
    out = performance_summary(ledger, rf=0.0, periods_per_year=252)

    assert isinstance(out, PerformanceMetrics)
    assert out.total_return == 0.0
    assert out.cagr == 0.0
    assert out.annual_vol == 0.0
    assert out.sharpe == 0.0
    # max_drawdown may be None if you haven't wired it yet; accept either
    assert (out.max_drawdown is None) or (out.max_drawdown == 0.0)
