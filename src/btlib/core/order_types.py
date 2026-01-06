from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
# Force project root (the folder that contains /core) onto sys.path
import pandas as pd
import numpy as np
from btlib.core.enums import Side, OrderType, TimeInForce, OrderStatus


def require_finite(name: str, value: float) -> None:
        """Ensure that a given float value is finite (not NaN or infinite)."""
        if not np.isfinite(value):
            raise ValueError(f"{name} must be a finite number, got {value}")
@dataclass(frozen=True)
class Order:
    ts: pd.Timestamp
    order_type: OrderType
    symbol: str
    qty: float
    side: Side | None = None
    tag: str | None = None
    meta: dict[str, Any]=field(default_factory=dict)
    
        
    def __post_init__(self) -> None:
        object.__setattr__(self, "ts", pd.Timestamp(self.ts))
        if pd.isna(self.ts):
            raise ValueError("ts must be a valid timestamp")



        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValueError("symbol must be a non-empty string")
        require_finite("qty", float(self.qty))
        if not isinstance(self.order_type,OrderType):
            raise TypeError("order_type must be a valid order")
        if float(self.qty) == 0.0:
            raise ValueError("qty cannot be 0")
        
        if self.side is not None:
            if not isinstance(self.side,Side):
                raise TypeError("Must be a valid side")
            if self.side==Side.BUY and self.qty<0:
                raise ValueError("qty must be positive for buy")
            if self.side==Side.SELL and self.qty>0:
                raise ValueError("qty must be negative for sell")
        

        

@dataclass(frozen=True)
class Fill:
    ts: pd.Timestamp
    symbol: str
    qty: float
    price: float
    fees: float = 0.0
    slippage: float = 0.0
    order_tag: str | None = None
    exposure: float = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "ts", pd.Timestamp(self.ts))
        if pd.isna(self.ts):
            raise ValueError("ts must be a valid timestamp")


        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValueError("symbol must be a non-empty string")

        require_finite("qty", float(self.qty))
        if float(self.qty) == 0.0:
            raise ValueError("quantity cannot be 0")

        require_finite("price", float(self.price))
        if float(self.price) <= 0.0:
            raise ValueError("price must be a positive number")

        require_finite("fees", float(self.fees))
        if float(self.fees) < 0.0:
            raise ValueError("fees cannot be negative")

        require_finite("slippage", float(self.slippage))
        if float(self.slippage) < 0.0:
            raise ValueError("slippage cannot be negative")

        notional_exposure = abs(float(self.price) * float(self.qty))
        object.__setattr__(self, "exposure", notional_exposure)



@dataclass
class Position:
    symbol: str
    qty: float = 0.0
    avg_price: float = 0.0
    realized_pnl: float = 0.0
    def market_value(self, current_price: float) -> float:
        require_finite("current_price", float(current_price))
        if float(current_price) <= 0.0:
            raise ValueError("current_price must be > 0")
        require_finite("qty", float(self.qty))
        return float(self.qty) * float(current_price)

    def unrealized_pnl(self, current_price: float) -> float:
        require_finite("current_price", float(current_price))
        if float(current_price) <= 0.0:
            raise ValueError("current_price must be > 0")
        require_finite("qty", float(self.qty))
        require_finite("avg_price", float(self.avg_price))
        return (float(current_price) - float(self.avg_price)) * float(self.qty)
    
    
@dataclass
class PortfolioState:
    ts: pd.Timestamp
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    def __post_init__(self) -> None:
        
        self.ts = pd.Timestamp(self.ts)
        if pd.isna(self.ts):
            raise ValueError("ts must be a valid timestamp")


        require_finite("cash", float(self.cash))

        
        
    def get_position(self, symbol: str) -> Position:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("symbol must be a non-empty string")

        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)

        return self.positions[symbol]

        
    def equity(self, mark_prices: dict[str,float]) -> float:
        """Calculate the total equity of the portfolio based on the current market price."""        
        equity=self.cash
        for symbol, position in self.positions.items():
            current_price=mark_prices.get(symbol)
            if current_price is None:
                raise KeyError(f"Market price for symbol {symbol} not provided")
            equity += position.market_value(current_price)
        return equity
    
    def gross_exposure(self, mark_prices: dict[str, float]) -> float:
        total = 0.0
        for symbol, position in self.positions.items():
            if symbol not in mark_prices:
                raise KeyError(f"Market price for symbol {symbol} not provided")
            total += abs(position.market_value(mark_prices[symbol]))
        return total

    
    def net_exposure(self, mark_prices: dict[str, float]) -> float:
        """Calculate the net exposure of the portfolio based on the current market price."""
        exposure = 0.0
        for symbol, position in self.positions.items():
            current_price = mark_prices.get(symbol)
            if current_price is None:
                raise KeyError(f"Market price for symbol {symbol} not provided")
            exposure += position.market_value(current_price)
        return exposure
    
    def leverage(self, mark_prices: dict[str, float]) -> float:
        """Calculate the leverage of the portfolio based on the current market price."""
        if self.equity(mark_prices) <= 0:
            raise ValueError("Equity must be positive to calculate leverage")
        gross_exposure = self.gross_exposure(mark_prices)
        equity = self.equity(mark_prices)
        leverage = gross_exposure / equity
        return leverage
    def unrealized_pnl(self, mark_prices: dict[str, float]):
        total=0.0
        for symbol, position in self.positions.items():
            if symbol not in mark_prices:
                raise KeyError(f"Missing mark price for {symbol}")
            total+=position.unrealized_pnl(mark_prices[symbol])
        return total
    def realized_pnl(self) -> float:
        return sum(pos.realized_pnl for pos in self.positions.values())

