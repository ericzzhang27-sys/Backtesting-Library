import pandas as pd
import numpy as np

from btlib.data.market_data import MarketData
from btlib.engine import run_positions_only
from btlib.engine import BacktestConfig


class NoTradeStrategy:
    def on_bar(self, ts, data_upto_ts, state):
        # Always flat
        return {}


def make_market() -> MarketData:
    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    close = pd.DataFrame({"AAPL": [100, 101, 102, 103, 104]}, index=idx, dtype=float)
    return MarketData(close)


def test_ledger_schema_and_index_alignment():
    market = make_market()
    cfg = BacktestConfig()  # rely on your defaults (initial_cash, warmup_bars, etc.)

    res = run_positions_only(market=market, strategy=NoTradeStrategy(), cfg=cfg)

    ledger = res.ledger

    # Required columns
    required = [
        "cash",
        "equity",
        "gross_exposure",
        "net_exposure",
        "leverage",
        "n_positions",
    ]
    for c in required:
        assert c in ledger.columns, f"missing ledger column: {c}"

    # Index equals market timestamps
    assert list(ledger.index) == list(market.timestamps())
    assert ledger.index.is_monotonic_increasing

    # Equity finite each bar (no NaN propagation)
    assert np.isfinite(ledger["equity"].to_numpy()).all()

    # With no trades, exposures should stay 0 and equity == cash
    assert (ledger["gross_exposure"] == 0.0).all()
    assert (ledger["net_exposure"] == 0.0).all()
    assert (ledger["n_positions"] == 0).all()
    assert np.allclose(ledger["equity"].to_numpy(), ledger["cash"].to_numpy())
