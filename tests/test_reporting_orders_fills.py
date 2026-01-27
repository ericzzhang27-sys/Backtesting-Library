import pandas as pd
import numpy as np

from btlib.data.market_data import MarketData
from btlib.engine.engine import run_positions_only
from btlib.engine.config import BacktestConfig


class BuyThenFlatStrategy:
    """
    Forces at least one buy and one sell:
    - First bar: target 1.0
    - From bar 3 onward: target 0.0
    """
    def on_bar(self, ts, data_upto_ts, state):
        n = len(data_upto_ts)  # 1 on first bar, 2 on second, etc.
        if n == 1:
            return {"AAPL": 1.0}
        if n >= 3:
            return {"AAPL": 0.0}
        return {"AAPL": 1.0}


def make_market() -> MarketData:
    idx = pd.date_range("2024-01-01", periods=6, freq="D")
    close = pd.DataFrame({"AAPL": [100, 101, 102, 103, 104, 105]}, index=idx, dtype=float)
    return MarketData(close)


def test_orders_and_fills_schema_and_notional():
    market = make_market()
    cfg = BacktestConfig()

    res = run_positions_only(market=market, strategy=BuyThenFlatStrategy(), cfg=cfg)

    orders = res.orders
    fills = res.fills

    # ---- Orders schema ----
    assert orders.index.name == "ts_submit"
    for c in ["symbol", "qty", "order_type", "tag"]:
        assert c in orders.columns, f"missing orders column: {c}"

    assert len(orders) > 0  # should have at least one order

    # ---- Fills schema ----
    assert fills.index.name == "ts_fill"
    for c in ["symbol", "qty", "price", "fees", "slippage", "notional", "tag"]:
        assert c in fills.columns, f"missing fills column: {c}"

    assert len(fills) > 0  # should have at least one fill

    # notional correctness
    expected = (fills["qty"].astype(float) * fills["price"].astype(float)).abs()
    assert np.allclose(fills["notional"].astype(float).to_numpy(), expected.to_numpy())
