from dataclasses import dataclass
import pandas as pd
from btlib.data.market_data import MarketData
from btlib.engine.strategy_base import Strategy
from btlib.engine.config import BacktestConfig
from btlib.core.order_types import PortfolioState
from btlib.engine.accounting import mark_to_market
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
    symbols=market.symbols()
    for ts in market.timestamps():
        hist= market.slice_upto(ts)
        if hist.index.max() > ts and not hist.empty and hist.index.max()!=ts:
            raise ValueError(f"Future leakage at {hist.index.max()}")
        marks=market.get_price_dict(ts)
        targets=strategy.on_bar(ts, data_upto_ts = hist, state = state)
        targets_rows.append({"ts":ts, **{s:float(targets.get(s,0)) for s in symbols}})
        ledger_rows.append({"ts":ts, "cash": state.cash, "equity": state.equity(marks),
                    "gross_exposure": state.gross_exposure(marks),"net_exposure": state.net_exposure(marks),
                    "leverage": state.leverage(marks),"n_positions": len(state.positions)})
        if ts<(market.timestamps()[0]+pd.Timedelta(days=cfg.warmup_bars)):
            targets={}
    ledger=pd.DataFrame(ledger_rows).set_index("ts")
    targets=pd.DataFrame(targets_rows).set_index("ts")
    
    return BacktestResults(ledger=ledger,targets=targets)
        
