# tests/test_costs_monotonicity.py
from __future__ import annotations

import pandas as pd
import pytest

from btlib.data.market_data import MarketData
from btlib.engine.config import BacktestConfig
from btlib.engine.engine import run_positions_only
from btlib.costs.simple_bps import SimpleBpsCost


class OneRoundTripStrategy:
    """
    Day0: target 1.0 (open)
    Day1: target 0.0 (close)
    Day2: does nothing
    """
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def on_bar(self, ts, data_upto_ts, state):
        ts = pd.Timestamp(ts)
        t0 = pd.Timestamp("2024-01-01")
        t1 = pd.Timestamp("2024-01-02")
        if ts == t0:
            return {self.symbol: 1.0}
        if ts == t1:
            return {self.symbol: 0.0}
        return {self.symbol: 0.0}


def make_market_3day() -> MarketData:
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    close = pd.DataFrame({"AAPL": [100.0, 110.0, 120.0]}, index=idx)
    return MarketData(close)


def test_higher_costs_cannot_improve_results() -> None:
    market = make_market_3day()
    strat = OneRoundTripStrategy("AAPL")

    cfg = BacktestConfig()
    cfg.initial_cash = 10_000.0
    cfg.warmup_bars = 0

    # No costs
    res0 = run_positions_only(market=market, strategy=strat, cfg=cfg, cost_model=None)
    eq0 = float(res0.ledger["equity"].iloc[-1])

    # Higher costs
    cm = SimpleBpsCost(fees_bps=10.0, slippage_bps=10.0)
    res1 = run_positions_only(market=market, strategy=strat, cfg=cfg, cost_model=cm)
    eq1 = float(res1.ledger["equity"].iloc[-1])

    assert eq1 <= eq0 + 1e-12  # monotonicity (allow tiny float noise)

    # Stronger check: equity drop equals total charged costs (same fills/prices/qty)
    total_costs = float((res1.fills["fees"] + res1.fills["slippage"]).sum())
    assert (eq0 - eq1) == pytest.approx(total_costs, rel=1e-12, abs=1e-9)
