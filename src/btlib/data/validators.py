import pandas as pd
import numpy as np
from btlib.core.enums import Side, OrderType, OrderStatus
from btlib.core.order_types import PortfolioState, Position, Fill, Order
from btlib.engine.accounting import apply_fill, mark_to_market
def validate_price(df: pd.DataFrame) -> None:
    if isinstance(df,pd.DataFrame):
        pass
    else:
        raise TypeError("Price data must be a pandas DataFrame")
    if isinstance(df.index,pd.DatetimeIndex):
        pass
    else:
        raise TypeError("Price data index must be a DatetimeIndex")
    
