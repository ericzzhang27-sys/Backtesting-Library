from dataclasses import dataclass
import pandas as pd
from btlib.data.market_data import MarketData
from btlib.engine.strategy_base import Strategy
from btlib.engine.config import BacktestConfig
from btlib.core import PortfolioState, Fill
from btlib.engine.rebalance import targets_to_orders
from btlib.execution import ExecutionModel, NextCloseExecution
from btlib.engine.accounting import apply_fill
from btlib.costs import SimpleBpsCost, CostModel
from btlib.reporting.reporting import build_fills, build_ledger, build_orders, build_targets, trades_from_fills
import numpy as np
@dataclass
class BacktestResults:
    ledger: pd.DataFrame
    targets: pd.DataFrame
    orders: pd.DataFrame
    fills: pd.DataFrame
    trades: pd.DataFrame
def run_positions_only(
        market: MarketData, 
        strategy: Strategy, 
        cfg: BacktestConfig, 
        execution_model: ExecutionModel | None = None, 
        cost_model: CostModel | None = None) -> BacktestResults:
    

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
                if not cost_model:
                    fees, slippage = 0.0, 0.0
                else:
                    fees, slippage= cost_model.compute(f)
                f2= Fill(f.ts,f.symbol,f.qty,f.price,fees,slippage, getattr(f, "tag", None))
                state = apply_fill(state,f2)

                fills_rows.append({
                    "ts_fill": f2.ts,
                    "symbol": f2.symbol,
                    "notional": abs(f2.qty * f2.price),
                    "qty": f2.qty,
                    "price": f2.price,
                    "fees": f2.fees,
                    "slippage": f2.slippage,
                    "tag": getattr(f2, "tag", None)
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
                "ts_submit": o.ts,
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
            "n_positions": sum(1 for p in state.positions.values() if abs(p.qty) > 1e-12)
        })

        

    ledger=build_ledger(ledger_rows)
    targets= build_targets(targets_rows,symbols)
    orders=build_orders(orders_rows)
    fills=build_fills(fills_rows)
    trades= trades_from_fills(fills)

    return BacktestResults(ledger=ledger,targets=targets, orders=orders,fills=fills, trades=trades)
        
