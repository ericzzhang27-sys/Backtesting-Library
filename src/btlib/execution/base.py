# base.py
from abc import ABC, abstractmethod
import pandas as pd
from btlib.core.order_types import Order, Fill

class ExecutionModel(ABC):
    @abstractmethod
    def simulate_fills(
        self,
        ts_fill: pd.Timestamp,
        orders: list[Order],
        bar_prices: dict[str, float],
    ) -> list[Fill]:
        raise NotImplementedError
