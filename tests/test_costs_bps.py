# tests/test_costs_simple_bps.py
from __future__ import annotations

import pytest

from btlib.core.order_types import Fill
from btlib.costs.simple_bps import SimpleBpsCost


def test_simple_bps_exact_math() -> None:
    # qty=10, price=100 -> notional=1000
    f = Fill(ts="2024-01-01", symbol="AAPL", qty=10, price=100.0)

    cm = SimpleBpsCost(fees_bps=10.0, slippage_bps=5.0)  # 10bp=0.1%, 5bp=0.05%
    fees, slippage = cm.compute(f)

    assert fees == pytest.approx(1.0)       # 1000 * 10/10000
    assert slippage == pytest.approx(0.5)   # 1000 * 5/10000


def test_simple_bps_sign_does_not_matter() -> None:
    f_long = Fill(ts="2024-01-01", symbol="AAPL", qty=10, price=100.0)
    f_short = Fill(ts="2024-01-01", symbol="AAPL", qty=-10, price=100.0)

    cm = SimpleBpsCost(fees_bps=10.0, slippage_bps=5.0)
    fees1, slip1 = cm.compute(f_long)
    fees2, slip2 = cm.compute(f_short)

    assert fees1 == pytest.approx(fees2)
    assert slip1 == pytest.approx(slip2)


def test_simple_bps_rejects_invalid_bps() -> None:
    with pytest.raises(ValueError):
        SimpleBpsCost(fees_bps=-1.0, slippage_bps=0.0)

    with pytest.raises(ValueError):
        SimpleBpsCost(fees_bps=0.0, slippage_bps=-0.01)

    with pytest.raises(ValueError):
        SimpleBpsCost(fees_bps=float("nan"), slippage_bps=0.0)

    with pytest.raises(ValueError):
        SimpleBpsCost(fees_bps=0.0, slippage_bps=float("inf"))


def test_fill_rejects_invalid_price() -> None:
    # Your SimpleBpsCost relies on Fill to enforce price > 0
    with pytest.raises(ValueError):
        Fill(ts="2024-01-01", symbol="AAPL", qty=10, price=0.0)

    with pytest.raises(ValueError):
        Fill(ts="2024-01-01", symbol="AAPL", qty=10, price=-5.0)
