import pandas as pd

from btlib.reporting.reporting import trades_from_fills


def _fills_df(rows):
    df = pd.DataFrame(rows)
    return df.set_index("ts_fill").sort_index()


def test_trades_simple_long_round_trip_with_costs():
    t1 = pd.Timestamp("2024-01-01")
    t2 = pd.Timestamp("2024-01-02")

    fills = _fills_df([
        {"ts_fill": t1, "symbol": "AAPL", "qty":  10.0, "price": 100.0, "fees": 1.0, "slippage": 1.0, "notional": 1000.0, "tag": None},
        {"ts_fill": t2, "symbol": "AAPL", "qty": -10.0, "price": 110.0, "fees": 1.0, "slippage": 1.0, "notional": 1100.0, "tag": None},
    ])

    trades = trades_from_fills(fills)
    assert len(trades) == 1

    tr = trades.iloc[0]
    assert tr["symbol"] == "AAPL"
    assert tr["entry_ts"] == t1
    assert tr["exit_ts"] == t2
    assert tr["qty"] == 10.0
    assert tr["direction"] == "LONG"

    # Gross PnL
    assert tr["pnl_gross"] == 10.0 * (110.0 - 100.0)

    # With your v1 per-share allocation:
    # fees: 10*((1/10)+(1/10)) = 2
    # slippage: same = 2
    # net = 100 - 4 = 96
    assert tr["fees"] == 2.0
    assert tr["slippage"] == 2.0
    assert tr["pnl_net"] == 96.0


def test_trades_partial_closes_fifo():
    t1 = pd.Timestamp("2024-01-01")
    t2 = pd.Timestamp("2024-01-02")
    t3 = pd.Timestamp("2024-01-03")

    fills = _fills_df([
        {"ts_fill": t1, "symbol": "AAPL", "qty": 10.0, "price": 100.0, "fees": 0.0, "slippage": 0.0, "notional": 1000.0, "tag": None},
        {"ts_fill": t2, "symbol": "AAPL", "qty": -4.0, "price": 105.0, "fees": 0.0, "slippage": 0.0, "notional":  420.0, "tag": None},
        {"ts_fill": t3, "symbol": "AAPL", "qty": -6.0, "price":  95.0, "fees": 0.0, "slippage": 0.0, "notional":  570.0, "tag": None},
    ])

    trades = trades_from_fills(fills)
    assert len(trades) == 2

    assert trades.iloc[0]["qty"] == 4.0
    assert trades.iloc[0]["pnl_gross"] == 4.0 * (105.0 - 100.0)

    assert trades.iloc[1]["qty"] == 6.0
    assert trades.iloc[1]["pnl_gross"] == 6.0 * (95.0 - 100.0)


def test_trades_short_round_trip():
    t1 = pd.Timestamp("2024-01-01")
    t2 = pd.Timestamp("2024-01-02")

    fills = _fills_df([
        {"ts_fill": t1, "symbol": "AAPL", "qty": -10.0, "price": 100.0, "fees": 0.0, "slippage": 0.0, "notional": 1000.0, "tag": None},
        {"ts_fill": t2, "symbol": "AAPL", "qty":  10.0, "price":  90.0, "fees": 0.0, "slippage": 0.0, "notional":  900.0, "tag": None},
    ])

    trades = trades_from_fills(fills)
    assert len(trades) == 1

    tr = trades.iloc[0]
    assert tr["direction"] == "SHORT"
    assert tr["pnl_gross"] == 10.0 * (100.0 - 90.0)


def test_trades_flip_closes_and_leaves_open_lot():
    # Long 10, then sell 15 => one closing trade (10) + open short (5) with no trade yet
    t1 = pd.Timestamp("2024-01-01")
    t2 = pd.Timestamp("2024-01-02")

    fills = _fills_df([
        {"ts_fill": t1, "symbol": "AAPL", "qty":  10.0, "price": 100.0, "fees": 0.0, "slippage": 0.0, "notional": 1000.0, "tag": None},
        {"ts_fill": t2, "symbol": "AAPL", "qty": -15.0, "price": 110.0, "fees": 0.0, "slippage": 0.0, "notional": 1650.0, "tag": None},
    ])

    trades = trades_from_fills(fills)
    assert len(trades) == 1
    assert trades.iloc[0]["qty"] == 10.0
    assert trades.iloc[0]["pnl_gross"] == 10.0 * (110.0 - 100.0)
