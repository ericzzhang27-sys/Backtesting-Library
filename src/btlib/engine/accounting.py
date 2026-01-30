"""Accounting Transforms: Apply fills to PortfolioState and compute mark to market aggregates"""
from btlib.core.order_types import PortfolioState, Position, Fill
epsilon=1e-12


# Round down floating point precision error based on epsilon
def close_enough_zero(x: float) -> bool:
    return abs(x) <= epsilon
# Check sign of position quantity  
def sign(x:float) -> int:
    if x == 0 or close_enough_zero(x):
        return 0
    if x>0:
        return 1
    if x<0:
        return -1
def apply_fill(state: PortfolioState,fill: Fill) -> PortfolioState:
    if fill.symbol not in state.positions:
        state.positions[fill.symbol] = Position(fill.symbol,0,0) # Creates new position if not previously traded
    qty_0=state.positions[fill.symbol].qty
    price_0=state.positions[fill.symbol].avg_price
    trade_cash=fill.qty*fill.price
    state.cash-=trade_cash+fill.fees+fill.slippage
    if close_enough_zero(qty_0) or sign(fill.qty)==sign(qty_0): # Add/ Open
        #Calculates new average price 
        new_avg_price=(qty_0*price_0+fill.qty*fill.price)/(qty_0+fill.qty)
        state.positions[fill.symbol].avg_price=new_avg_price
        state.positions[fill.symbol].qty=qty_0+fill.qty
    elif sign(qty_0)!=sign(fill.qty) and abs(fill.qty)<=abs(qty_0): # Realize Profit
        closed=abs(fill.qty)
        realized_profit=closed*sign(qty_0)*(fill.price-price_0)
        state.positions[fill.symbol].realized_pnl+=realized_profit
        state.positions[fill.symbol].qty+=fill.qty
        if state.positions[fill.symbol].qty==0:
            state.positions[fill.symbol].avg_price=0
    elif sign(qty_0)!=sign(fill.qty) and abs(fill.qty)>abs(qty_0): # Flip Position e.g. long to short
        closed=abs(qty_0)
        realized_profit=closed*sign(qty_0)*(fill.price-price_0)
        state.positions[fill.symbol].realized_pnl+=realized_profit
        state.positions[fill.symbol].qty+=fill.qty
        state.positions[fill.symbol].avg_price=fill.price
    state.ts=fill.ts
    if close_enough_zero(state.positions[fill.symbol].qty):
        state.positions[fill.symbol].qty=0
        state.positions[fill.symbol].avg_price=0
    for sym in list(state.positions.keys()):
        if close_enough_zero(state.positions[sym].qty):
            state.positions.pop(sym, None)

    return state

#Mark current state   
def mark_to_market(state: PortfolioState, marks: dict[str,float]) -> dict:
    pf_summary={
                "equity": state.equity(marks),
                "gross_exposure" : state.gross_exposure(marks),
                "net_exposure" : state.net_exposure(marks),
                "unrealized_pnl": state.unrealized_pnl(marks),
                "realized_pnl": state.realized_pnl(marks),
                "leverage": state.leverage(marks)
                }
    return pf_summary



    



    