import pandas as pd
from btlib.core.order_types import PortfolioState
from btlib.data.market_data import MarketData
class Strategy:
    def on_bar(self, 
                ts: pd.Timestamp, 
                data_upto_ts: pd.DataFrame,
                state: PortfolioState)->dict[str, float]:
        return {}
