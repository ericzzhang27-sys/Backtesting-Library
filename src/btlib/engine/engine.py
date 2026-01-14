from dataclasses import dataclass
import pandas as pd
from btlib.data.market_data import MarketData
from btlib.engine.strategy_base import Strategy
from btlib.engine.config import BacktestConfig
from btlib.core.order_types import PortfolioState
@dataclass
class BacktestResults:
    ledger: pd.DataFrame
    targets: pd.DataFrame
def run_positions_only(market: MarketData, strategy: Strategy, cfg: BacktestConfig) -> BacktestResults:
    ts0=market.timestamps[0]
    state=PortfolioState(ts = ts0,
                         cash = cfg.initial_cash,
                         positions={}
                         )
    ledger_rows=[]
    targets_rows=[]
    symbols=market.symbols
    for ts in market.timestamps:
        hist= market.slice_upto(ts)
    if hist.index.max() > ts:
        raise ValueError("Date out of bound")