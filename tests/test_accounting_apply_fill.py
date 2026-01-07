import pandas as pd
import numpy as np
from btlib.core.enums import Side, OrderType, OrderStatus
from btlib.core.order_types import PortfolioState, Position, Fill, Order
from btlib.engine.accounting import apply_fill, mark_to_market
symbol="AAPL"
ts="2025-06-23"
pf=PortfolioState(ts,cash=10000,positions={})
pf.get_position(symbol)
fill=Fill(ts,symbol,10,100)
pf=apply_fill(pf,fill)  #Result: PortfolioState(ts=Timestamp('2025-06-23 00:00:00'), cash=9000.0, positions={'AAPL': Position(symbol='AAPL', qty=10.0, avg_price=100.0, realized_pnl=0.0)})
fill=Fill(ts,symbol,10,110)
pf=apply_fill(pf,fill)  #Result: PortfolioState(ts=Timestamp('2025-06-23 00:00:00'), cash=7900.0, positions={'AAPL': Position(symbol='AAPL', qty=20.0, avg_price=105.0, realized_pnl=0.0)})
fill=Fill(ts,symbol,-5,120)
pf=apply_fill(pf,fill)  #Result: PortfolioState(ts=Timestamp('2025-06-23 00:00:00'), cash=8500.0, positions={'AAPL': Position(symbol='AAPL', qty=15.0, avg_price=105.0, realized_pnl=75.0)})
fill=Fill(ts,symbol,-15,90)
pf=(apply_fill(pf,fill))  #Result: PortfolioState(ts=Timestamp('2025-06-23 00:00:00'), cash=9850.0, positions={'AAPL': Position(symbol='AAPL', qty=0.0, avg_price=0, realized_pnl=-150.0)})
pf1=PortfolioState(ts,cash=10000,positions={})
pf1.get_position(symbol)
fill=Fill(ts,symbol,-10,100)
pf1=apply_fill(pf1,fill)  #Result: PortfolioState(ts=Timestamp('2025-06-23 00:00:00'), cash=10850.0, positions={'AAPL': Position(symbol='AAPL', qty=-10.0, avg_price=100.0, realized_pnl=-150.0)})
fill=Fill(ts,symbol,4,90)
pf1=apply_fill(pf1,fill) #PortfolioState(ts=Timestamp('2025-06-23 00:00:00'), cash=10640.0, positions={'AAPL': Position(symbol='AAPL', qty=-6.0, avg_price=100.0, realized_pnl=40.0)})

pf=PortfolioState(ts,cash=10000,positions={})
pf.get_position(symbol)
fill=Fill(ts,symbol,5,100)
pf=apply_fill(pf,fill) #PortfolioState(ts=Timestamp('2025-06-23 00:00:00'), cash=9500.0, positions={'AAPL': Position(symbol='AAPL', qty=5.0, avg_price=100.0, realized_pnl=0.0)})
fill=Fill(ts,symbol,-12,110)
pf=apply_fill(pf,fill) 
print(pf)
pf=PortfolioState(ts,cash=10000,positions={})
pf.get_position(symbol)
fill=Fill(ts,symbol,10,100,fees=2,slippage=3)
pf=apply_fill(pf,fill)
print(pf)
pf=PortfolioState(ts,cash=10000,positions={})
pf.get_position(symbol)
fill=Fill(ts,symbol,1e-13,100)
pf=apply_fill(pf,fill)
print(pf)