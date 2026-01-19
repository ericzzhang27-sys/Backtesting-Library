from dataclasses import dataclass
import pandas as pd
from btlib.data.market_data import MarketData
from btlib.engine.strategy_base import Strategy
from btlib.engine.config import BacktestConfig
from btlib.core.order_types import PortfolioState
from btlib.engine.rebalance import targets_to_orders
@dataclass
class BacktestResults:
    ledger: pd.DataFrame
    targets: pd.DataFrame
def run_positions_only(market: MarketData, strategy: Strategy, cfg: BacktestConfig) -> BacktestResults:
    ts0=market.timestamps()[0]
    state=PortfolioState(ts = ts0,
                         cash = cfg.initial_cash,
                         positions={}
                         )
    ledger_rows=[]
    targets_rows=[]
    order_log=[]
    symbols=market.symbols()
    for i, ts in enumerate(market.timestamps()):
        hist = market.slice_upto(ts)

        # no-future guarantee (guard empty first)
        if not hist.empty and hist.index.max() > ts:
            raise ValueError(f"Future leakage at {hist.index.max()} (ts={ts})")

        marks = market.get_price_dict(ts)

        # --- WARMUP BARS ---
        if i < cfg.warmup_bars:
            targets = {}   
        else:
            targets = strategy.on_bar(ts, data_upto_ts=hist, state=state) or {}
        
        targets_rows.append({"ts": ts, **{s: float(targets.get(s, 0.0)) for s in symbols}})
        current_orders=[targets_to_orders(ts, targets, state, marks, cfg)]
        order_log.extend(current_orders)
        ledger_rows.append({
            "ts": ts,
            "cash": state.cash,
            "equity": state.equity(marks),
            "gross_exposure": state.gross_exposure(marks),
            "net_exposure": state.net_exposure(marks),
            "leverage": state.leverage(marks),
            "n_positions": len(state.positions),
            "orders": current_orders
        })



    ledger = pd.DataFrame(ledger_rows).set_index("ts")
    targets = pd.DataFrame(targets_rows).set_index("ts")
    return BacktestResults(ledger=ledger,targets=targets)
        
