from btlib.data.validators import validate_price_frame
import pandas as pd
import numpy as np
"""
Class containing market data, converting dataframes into usable dicts for orders, fills, and positions
"""
class MarketData:
    def __init__(self, close: pd.DataFrame) -> None:
        validate_price_frame(close)
        self.close = close.sort_index()
        self.close.columns = self.close.columns.astype(str)
    def timestamps(self) -> pd.Timestamp:
        return self.close.index
    def symbols(self) -> list[str]:
        return self.close.columns.tolist()
    def get_close(self, ts: pd.Timestamp) -> pd.Series:
        ts = pd.Timestamp(ts)
        if ts not in self.close.index:
            raise KeyError(f"Timestamp {ts} not found in market data")
        return self.close.loc[ts]
    def get_price_dict(self, ts: pd.Timestamp) -> dict[str,float]:
        get_close=self.get_close(ts)
        return get_close.to_dict()
    def slice_upto(self, ts: pd.Timestamp) -> pd.DataFrame:
        ts = pd.Timestamp(ts)

        if len(self.close.index) > 0 and ts < self.close.index[0]:
            return self.close.iloc[0:0]

        return self.close.loc[:ts]
    def tradable_symbols(self, ts: pd.Timestamp) -> list[str]:
        row = self.get_close(ts)
        mask = np.isfinite(row.astype(float))
        return row.index[mask].tolist()
