from __future__ import annotations

from typing import Any
import pandas as pd


# ----------------------------
# Required schemas
# ----------------------------

REQUIRED_LEDGER_COLS = [
    "ts",
    "cash",
    "equity",
    "gross_exposure",
    "net_exposure",
    "leverage",
    "n_positions",
]

REQUIRED_ORDERS_COLS = [
    "ts_submit",
    "symbol",
    "qty",
    "order_type",
    "tag",
]

REQUIRED_FILLS_COLS = [
    "ts_fill",
    "symbol",
    "qty",
    "price",
    "fees",
    "slippage",
    "notional",
    "tag",
]

TRADES_COLS = [
    "symbol",
    "entry_ts",
    "exit_ts",
    "qty",
    "entry_price",
    "exit_price",
    "direction",
    "pnl_gross",
    "fees",
    "slippage",
    "pnl_net",
    "holding_period",
]


# ----------------------------
# Small helpers
# ----------------------------

def _ensure_required_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing {name} columns: {missing}")

def _empty_df(columns: list[str], index_name: str) -> pd.DataFrame:
    return pd.DataFrame(columns=columns).set_index(pd.Index([], name=index_name))


# ----------------------------
# Builders
# ----------------------------

def build_ledger(rows: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    _ensure_required_columns(df, REQUIRED_LEDGER_COLS, "ledger")
    return df.set_index("ts").sort_index()


def build_orders(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return _empty_df(
            columns=[c for c in REQUIRED_ORDERS_COLS if c != "ts_submit"],
            index_name="ts_submit",
        )

    df = pd.DataFrame(rows)
    _ensure_required_columns(df, REQUIRED_ORDERS_COLS, "orders")
    return df.set_index("ts_submit").sort_index()


def build_fills(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return _empty_df(
            columns=[c for c in REQUIRED_FILLS_COLS if c != "ts_fill"],
            index_name="ts_fill",
        )

    df = pd.DataFrame(rows)
    _ensure_required_columns(df, REQUIRED_FILLS_COLS, "fills")

    if "notional" not in df.columns or df["notional"].isna().any():
        df["notional"] = (df["qty"].astype(float) * df["price"].astype(float)).abs()

    return df.set_index("ts_fill").sort_index()


def build_targets(rows: list[dict[str, Any]], symbols: list[str] | None = None) -> pd.DataFrame:
    """
    Your engine rows look like: {"ts": ts, **{sym: weight for sym in symbols}}
    This builder just sets index + optionally enforces column set/order.
    """
    if not rows:
        cols = [] if symbols is None else list(symbols)
        return pd.DataFrame(columns=cols).set_index(pd.Index([], name="ts"))

    df = pd.DataFrame(rows)
    if "ts" not in df.columns:
        raise ValueError("Missing targets column: ts")

    df = df.set_index("ts").sort_index()

    if symbols is not None:
        for s in symbols:
            if s not in df.columns:
                df[s] = 0.0
        df = df[list(symbols)]

    return df


# ----------------------------
# Trades from fills (FIFO)
# ----------------------------

def trades_from_fills(fills_df: pd.DataFrame) -> pd.DataFrame:
    """
    FIFO “round trip” reconstruction per symbol.

    """
    if fills_df is None or fills_df.empty:
        return pd.DataFrame(columns=TRADES_COLS)

    df = fills_df.copy()
    if df.index.name == "ts_fill":
        df = df.reset_index()
    elif "ts_fill" not in df.columns:
        raise ValueError("trades_from_fills expects fills indexed by ts_fill or a ts_fill column")

    _ensure_required_columns(df, REQUIRED_FILLS_COLS, "fills")

    df = df.sort_values(["symbol", "ts_fill"], kind="mergesort").reset_index(drop=True)

    # Lots per symbol: FIFO list of dicts
    # lot = {entry_ts, qty_open (signed), entry_price, fees, slippage}
    lots: dict[str, list[dict[str, Any]]] = {}
    trade_rows: list[dict[str, Any]] = []

    def sgn(x: float) -> int:
        if abs(x) <= 1e-12:
            return 0
        return 1 if x > 0 else -1

    for _, r in df.iterrows():
        sym = str(r["symbol"])
        ts = r["ts_fill"]
        q = float(r["qty"])
        px = float(r["price"])
        fees = float(r["fees"])
        slip = float(r["slippage"])

        if abs(q) <= 1e-12:
            continue

        sym_lots = lots.setdefault(sym, [])

        if not sym_lots:
            sym_lots.append(
                {"entry_ts": ts, "qty_open": q, "entry_price": px, "fees": fees, "slippage": slip}
            )
            continue

        exposure = sum(float(l["qty_open"]) for l in sym_lots)
        if sgn(exposure) == 0 or sgn(exposure) == sgn(q):
            sym_lots.append(
                {"entry_ts": ts, "qty_open": q, "entry_price": px, "fees": fees, "slippage": slip}
            )
            continue

        q_remaining = q

        while sym_lots and abs(q_remaining) > 1e-12:
            lot = sym_lots[0]
            lot_q = float(lot["qty_open"])
            lot_px = float(lot["entry_price"])
            lot_fees = float(lot["fees"])
            lot_slip = float(lot["slippage"])

            close_qty = min(abs(q_remaining), abs(lot_q))  

            direction = "LONG" if lot_q > 0 else "SHORT"

            if lot_q > 0:  # long
                pnl_gross = close_qty * (px - lot_px)
            else:          # short
                pnl_gross = close_qty * (lot_px - px)

            entry_fee_ps = lot_fees / abs(lot_q)
            entry_slip_ps = lot_slip / abs(lot_q)
            exit_fee_ps = fees / abs(q)
            exit_slip_ps = slip / abs(q)

            fees_alloc = close_qty * (entry_fee_ps + exit_fee_ps)
            slip_alloc = close_qty * (entry_slip_ps + exit_slip_ps)
            pnl_net = pnl_gross - fees_alloc - slip_alloc

            trade_rows.append(
                {
                    "symbol": sym,
                    "entry_ts": lot["entry_ts"],
                    "exit_ts": ts,
                    "qty": close_qty,
                    "entry_price": lot_px,
                    "exit_price": px,
                    "direction": direction,
                    "pnl_gross": pnl_gross,
                    "fees": fees_alloc,
                    "slippage": slip_alloc,
                    "pnl_net": pnl_net,
                    "holding_period": (pd.Timestamp(ts) - pd.Timestamp(lot["entry_ts"])),
                }
            )

            if abs(lot_q) <= close_qty + 1e-12:
                sym_lots.pop(0)
            else:
                new_lot_q = lot_q + close_qty * (1 if lot_q < 0 else -1)
                frac_remaining = abs(new_lot_q) / abs(lot_q)
                lot["qty_open"] = new_lot_q
                lot["fees"] = lot_fees * frac_remaining
                lot["slippage"] = lot_slip * frac_remaining

            # Reduce fill remaining (opposite sign)
            q_remaining = q_remaining + close_qty * (1 if q_remaining < 0 else -1)

        if abs(q_remaining) > 1e-12:
            frac = abs(q_remaining) / abs(q)
            sym_lots.append(
                {
                    "entry_ts": ts,
                    "qty_open": q_remaining,
                    "entry_price": px,
                    "fees": fees * frac,
                    "slippage": slip * frac,
                }
            )

    trades = pd.DataFrame(trade_rows, columns=TRADES_COLS)
    if not trades.empty:
        trades = trades.sort_values(["symbol", "exit_ts", "entry_ts"], kind="mergesort").reset_index(drop=True)
    return trades
