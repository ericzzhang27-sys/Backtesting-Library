from dataclasses import dataclass
import pandas as pd
from btlib.data.market_data import MarketData
from btlib.engine.strategy import Strategy
from btlib.engine.config import BacktestConfig
@dataclass
class BacktestResults:
    ledger: pd.DataFrame
    targets: pd.DataFrame
def run_positions_only(market: MarketData, strategy: Strategy, cfg: BacktestConfig) -> BacktestResults:
    