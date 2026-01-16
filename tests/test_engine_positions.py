# tests/test_engine_positions_only.py
import pandas as pd
import pytest

from btlib.data.market_data import MarketData
from btlib.engine.engine import run_positions_only
from btlib.engine.config import BacktestConfig


def make_market() -> MarketData:
    idx = pd.date_range("2024-01-01", periods=6, freq="D")
    close = pd.DataFrame(
        {
            "AAPL": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
            "MSFT": [200.0, 199.0, 201.0, 202.0, 203.0, 204.0],
        },
        index=idx,
    )
    return MarketData(close)


class NoFutureLeakStrategy:
    def on_bar(self, ts, data_upto_ts, state):
        assert not data_upto_ts.empty
        # strong Day 5 guarantee since ts comes from market.timestamps()
        assert data_upto_ts.index.max() == ts
        return {}


class DoNothingStrategy:
    def on_bar(self, ts, data_upto_ts, state):
        return {}


class ClipStrategy:
    def __init__(self, sym: str):
        self.sym = sym

    def on_bar(self, ts, data_upto_ts, state):
        return {self.sym: 2.0}  # intentionally too large


def test_no_future_leakage():
    market = make_market()
    cfg = BacktestConfig()
    res = run_positions_only(market, NoFutureLeakStrategy(), cfg)
    assert len(res.ledger) == len(market.timestamps())


def test_ledger_length_matches_timestamps():
    market = make_market()
    cfg = BacktestConfig()
    res = run_positions_only(market, DoNothingStrategy(), cfg)
    assert len(res.ledger) == len(market.timestamps())


def test_equity_constant_when_no_trading():
    market = make_market()
    cfg = BacktestConfig(initial_cash=123_456.0)
    res = run_positions_only(market, DoNothingStrategy(), cfg)

    # safer than Series == approx(scalar)
    diffs = (res.ledger["equity"] - cfg.initial_cash).abs()
    assert float(diffs.max()) == pytest.approx(0.0)


def test_target_clipping_applied():
    market = make_market()
    sym = market.symbols()[0]
    cfg = BacktestConfig(max_abs_weight=1.0, warmup_bars=0)
    res = run_positions_only(market, ClipStrategy(sym), cfg)

    # all bars clipped to +1.0 for that symbol
    assert res.targets[sym].tolist() == pytest.approx([cfg.max_abs_weight] * len(res.targets))
