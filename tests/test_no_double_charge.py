# tests/test_no_double_charge.py
from __future__ import annotations

import pandas as pd
import pytest

from btlib.core.order_types import PortfolioState, Fill
from btlib.engine.accounting import apply_fill


def test_costs_subtracted_exactly_once_in_apply_fill() -> None:
    ts = pd.Timestamp("2024-01-01")
    state0 = PortfolioState(ts=ts, cash=10_000.0, positions={})

    # Buy 10 @ 100 with $1 fees and $0.50 slippage
    f = Fill(ts=ts, symbol="AAPL", qty=10.0, price=100.0, fees=1.0, slippage=0.5)

    state1 = apply_fill(state0, f)

    # trade_cash = 10*100 = 1000
    # cash should drop by trade_cash + fees + slippage exactly once
    assert state1.cash == pytest.approx(10_000.0 - 1000.0 - 1.0 - 0.5, abs=1e-9)
