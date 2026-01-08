import pandas as pd
import numpy as np
from btlib.core.enums import Side, OrderType, OrderStatus
from btlib.core.order_types import PortfolioState, Position, Fill, Order
from btlib.engine.accounting import apply_fill, mark_to_market
def validate_price(df: pd.DataFrame) -> None:
    if not isinstance(df,pd.DataFrame):
        raise TypeError("Price data must be a pandas DataFrame")
    if not isinstance(df.index,pd.DatetimeIndex):
        raise TypeError("Price data index must be a DatetimeIndex")
    if not df.index.is_monotonic_increasing:
        raise ValueError("Price data index must be sorted in ascending order")
    if df.index.has_duplicates:
        raise ValueError("Price data index must not contain duplicates")
    if not {col: df[col].is_unique for col in df.columns}:
        raise ValueError("Price data columns must not contain duplicate values")
    if pd.api.types.is_numeric_dtype(df.dtypes):
        raise TypeError("All price data columns must be numeric dtype")
    if df.empty:
        raise ValueError("Price data DataFrame is empty")
def require_columns(df: pd.DataFrame, required: list[str])-> None:
    pass
class Market_Data:
    def __init__(self,close:pd.DataFrame):
        validate_price(close)
        self.close=close.sort_index
        self.close.columns=self.close.columns.astype(str)
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
        return Market_Data(sliced_close)
    def tradeable_symbols(self, ts: pd.Timestamp) -> list[str]:
        ts=pd.Timestamp(ts)
        if ts not in self.close.index:
            raise KeyError(f"Timestamp {ts} not found in market data")
        return self.close.loc[ts].index.tolist()