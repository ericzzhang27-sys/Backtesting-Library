from dataclasses import dataclass
import pandas as pd
from btlib.data.market_data import MarketData
from btlib.engine.strategy_base import Strategy
from btlib.engine.config import BacktestConfig
from btlib.core.order_types import PortfolioState
from btlib.engine.rebalance import targets_to_orders
from btlib.execution import ExecutionModel, NextCloseExecution
from btlib.engine.accounting import apply_fill
import numpy as np
@dataclass
class BacktestResults:
    ledger: pd.DataFrame
    targets: pd.DataFrame
    orders: pd.DataFrame
    fills: pd.DataFrame
def run_positions_only(market: MarketData, strategy: Strategy, cfg: BacktestConfig, execution_model: ExecutionModel | None = None) -> BacktestResults:
    if execution_model is None:
        execution_model = NextCloseExecution()
    ts0=market.timestamps()[0]
    state=PortfolioState(ts = ts0,
                         cash = cfg.initial_cash,
                         positions={}
                         )
    pending_orders= []
    ledger_rows=[]
    targets_rows=[]
    orders_rows=[]
    fills_rows= []
    symbols=market.symbols()
    for i, ts in enumerate(market.timestamps()):

        marks = market.get_price_dict(ts)
        
        
        if i>0 and pending_orders:
            fills=execution_model.simulate_fills(ts,pending_orders,marks)
            for f in fills:
                state = apply_fill(state,f)
                fills_rows.append({
                    "ts": f.ts,
                    "symbol": f.symbol,
                    "qty": f.qty,
                    "price": f.price,
                    "fees": f.fees,
                    "slippage": f.slippage,
                    "order_tag": getattr(f, "order_tag", None)
                })
            pending_orders=[]
        hist = market.slice_upto(ts)

        # no-future guarantee (guard empty first)
        if not hist.empty and hist.index.max() > ts:
            raise ValueError(f"Future leakage at {hist.index.max()} (ts={ts})")
        # --- WARMUP BARS ---
        if i < cfg.warmup_bars:
            targets = {}   
        else:
            targets = strategy.on_bar(ts, data_upto_ts=hist, state=state) or {}
        # clip targets for logging + to match order sizing
        max_abs = getattr(cfg, "max_abs_weight", 1.0)
        clipped_targets = {s: float(targets.get(s, 0.0)) for s in symbols}
        for s in symbols:
            w = clipped_targets[s]
            if abs(w) > max_abs:
                clipped_targets[s] = max(-max_abs, min(max_abs, w))
        targets = clipped_targets

        held = list(state.positions.keys())
        bad_held = [
            sym for sym in held
            if sym not in marks or (not np.isfinite(marks[sym])) or float(marks[sym]) <= 0.0
        ]
        if bad_held:
            # treat as "no trading possible" this bar
            current_orders = []
        else:
            current_orders = targets_to_orders(ts, targets, state, marks, cfg)
        targets_rows.append({"ts": ts, **{s: float(targets.get(s, 0.0)) for s in symbols}})
        pending_orders.extend(current_orders)
        for o in current_orders:
            orders_rows.append({
                "ts": o.ts,
                "symbol": o.symbol,
                "qty": o.qty,
                "order_type": o.order_type,
                "tag": o.tag
            })

        fail_on_missing = getattr(cfg, "fail_on_missing_marks", True)
        if bad_held:
            if fail_on_missing:
                raise ValueError(f"Missing/invalid marks for held symbols at {ts}: {bad_held}")
            # Can't mark-to-market; avoid crashing and avoid inventing equity.
            equity = np.nan
            gross = np.nan
            net = np.nan
            lev = np.nan
        else:
            equity = state.equity(marks)
            gross = state.gross_exposure(marks)
            net = state.net_exposure(marks)
            lev = state.leverage(marks)

        ledger_rows.append({
            "ts": ts,
            "cash": state.cash,
            "equity": equity,
            "gross_exposure": gross,
            "net_exposure": net,
            "leverage": lev,
            "n_positions": len(state.positions),
        })

        

    fills = pd.DataFrame(fills_rows)
    if not fills.empty:
        fills = fills.set_index("ts").sort_index()
    else:
        fills = pd.DataFrame(
            columns=["symbol", "qty", "price", "fees", "slippage", "order_tag"]
        ).set_index(pd.Index([], name="ts"))

    ledger = pd.DataFrame(ledger_rows).set_index("ts")
    targets = pd.DataFrame(targets_rows).set_index("ts")
    orders = pd.DataFrame(orders_rows)
    if not orders.empty:
        orders = orders.set_index("ts").sort_index()
    else:
        orders = pd.DataFrame(columns=["symbol", "qty", "order_type", "tag"]).set_index(pd.Index([], name="ts"))

    return BacktestResults(ledger=ledger,targets=targets, orders=orders,fills=fills)
        
