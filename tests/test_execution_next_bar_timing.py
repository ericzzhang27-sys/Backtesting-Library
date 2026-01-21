import numpy as np
import pandas as pd

from btlib.data.market_data import MarketData
from btlib.engine.config import BacktestConfig
from btlib.execution.next_close import NextCloseExecution
from btlib.engine.engine import run_positions_only


class Day0OnlyLong:
    def __init__(self, sym: str, t0: pd.Timestamp):
        self.sym = sym
        self.t0 = t0

    def on_bar(self, ts, data_upto_ts, state):
        if ts == self.t0:
            return {self.sym: 1.0}
        return {}  # avoid generating new orders on later bars


def test_fill_uses_t_plus_1_price_jump():
    idx = pd.date_range("2024-01-01", periods=2, freq="D")
    close = pd.DataFrame({"AAPL": [100.0, 200.0]}, index=idx)
    market = MarketData(close)

    cfg = BacktestConfig(initial_cash=1000.0, warmup_bars=0)
    strat = Day0OnlyLong("AAPL", t0=idx[0])

    res = run_positions_only(market, strat, cfg, NextCloseExecution())

    assert len(res.fills) == 1
    assert res.fills.index[0] == idx[1]
    assert float(res.fills.iloc[0]["price"]) == 200.0

    # anti-lookahead: should be flat on Day0
    assert float(res.ledger.loc[idx[0], "leverage"]) == 0.0


def test_no_fill_when_price_nan():
    idx = pd.date_range("2024-01-01", periods=2, freq="D")
    close = pd.DataFrame({"AAPL": [100.0, np.nan]}, index=idx)
    market = MarketData(close)

    cfg = BacktestConfig(initial_cash=1000.0, warmup_bars=0)
    strat = Day0OnlyLong("AAPL", t0=idx[0])

    res = run_positions_only(market, strat, cfg, NextCloseExecution())

    # no fill, and engine should not crash
    assert res.fills.empty
    assert float(res.ledger.loc[idx[0], "leverage"]) == 0.0
    assert np.isnan(float(res.ledger.loc[idx[1], "equity"]))
    assert np.isnan(float(res.ledger.loc[idx[1], "leverage"]))

