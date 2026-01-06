from enum import Enum

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"
class OrderType(Enum):
    MARKET = "MARKET"
class TimeInForce(Enum):
    DAY = "DAY"
class OrderStatus(Enum):
    FILLED = "FILLED"
    CANCELED = "CANCELLED"
    REJECTED = "REJECTED"
    CREATED = "CREATED"