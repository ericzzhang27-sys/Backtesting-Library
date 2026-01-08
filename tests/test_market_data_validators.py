import pandas as pd
import numpy as np
from btlib.core.enums import Side, OrderType, OrderStatus
from btlib.core.order_types import PortfolioState, Position, Fill, Order
from btlib.engine.accounting import apply_fill, mark_to_market
from btlib.data.validators import validate_price
from btlib.data.MarketData import Market_Data
symbol="AAPL"
ts="2025-06-23"
df=pd.DataFrame({symbol:[100,101,102]},index=pd.to_datetime(["2025-06-21","2025-06-22","2025-06-23"]))
md=MarketData(close=df)
print(md.get_close(ts))
