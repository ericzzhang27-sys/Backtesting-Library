"""Accounting Transforms: Apply fills to PortfolioState and compute mark to market aggregates"""
"EPS-Dollars"
from dataclasses import replace
import numpy as np
from btlib.core.enums import Side, OrderType, OrderStatus
from btlib.core.order_types import PortfolioState, Position, Fill
epsilon=1e-9
def close_enough_zero(x):
    if abs(x)<epsilon:
        x=0
def sign(x):
    close_enough_zero(x)
    if x==0:
        return 0
    if x>0:
        return 1
    if x<0:
        return -1
def apply_fill(state: PortfolioState,fill: Fill) -> PortfolioState:
    qty_0=state.positions[fill.symbol].qty
    price_0=state.positions[fill.symbol].avg_price
    trade_cash=fill.qty*fill.price
    state.cash+=trade_cash-fill.fees-fill.slippage
    if fill.symbol not in state.positions:
        state.positions[fill.symbol]=Position(fill.symbol,0,0) # Creates new position if not previously traded
    if qty_0==0 or sign(fill.qty)==sign(qty_0):
        #Calculates new average price 
        new_avg_price=(qty_0*price_0+fill.qty*fill.price)/(qty_0+fill.qty)
        state.positions[fill.symbol]=new_avg_price
    if sign(qty_0)!=sign(fill.qty) and abs(fill.qty)<=abs(qty_0):
        closed=abs(fill.qty)
        realized_profit=closed*sign(qty_0)*(fill.price-price_0)-fill.fees-fill.slippage
        state.positions[fill.symbol].realized_pnl+=realized_profit
        
    

    



    