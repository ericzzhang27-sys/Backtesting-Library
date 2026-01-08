from btlib.data.validators import validate_price
import pandas as pd
import numpy as np
class MarketData:
    def __init__(self,close:pd.DataFrame):
        self.close=close.sort_index()
        self.close.columns=self.close.columns.astype(str)
        validate_price(close)
    def timestamps(self) -> pd.DatetimeIndex:
        return self.close.index
    def symbols(self) -> list[str]:
        return self.close.columns.tolist()
    def get_close(self, ts: pd.Timestamp) -> pd.Series:
        ts=pd.Timestamp(ts)
        if ts not in self.close.index:
            raise KeyError(f"Timestamp {ts} not found in market data")
        return self.close.loc[ts]
    def get_price_dict(self, ts: pd.Timestamp) -> dict[str,float]:
        get_close=self.get_close(ts)
        return get_close.to_dict()
    def slice_up_to(self, ts: pd.Timestamp) -> 'Market_Data':
        ts=pd.Timestamp(ts)
        
        sliced_close=self.close.loc[:ts]
        if sliced_close.empty:
            raise ValueError(f"No market data available up to timestamp {ts}")
        return MarketData(sliced_close)
    def tradeable_symbols(self, ts: pd.Timestamp) -> list[str]:
        ts=pd.Timestamp(ts)
        if ts not in self.close.index:
            raise KeyError(f"Timestamp {ts} not found in market data")
        return self.close.loc[ts].index.tolist()