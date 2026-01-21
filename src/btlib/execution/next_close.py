# src/btlib/execution/next_close.py
from __future__ import annotations
import numpy as np
import pandas as pd
from btlib.core.order_types import Order, Fill
from btlib.execution.base import ExecutionModel

class NextCloseExecution(ExecutionModel):
    def simulate_fills(
        self,
        ts_fill: pd.Timestamp,
        orders: list[Order],
        bar_prices: dict[str, float],
    ) -> list[Fill]:
        fills: list[Fill] = []
        for o in orders:
            px = bar_prices.get(o.symbol, None)
            if px is None or (not np.isfinite(px)) or px <= 0:
                continue
            fills.append(
                Fill(
                    ts=ts_fill,
                    symbol=o.symbol,
                    qty=o.qty,
                    price=float(px),
                    fees=0.0,
                    slippage=0.0,
                    order_tag=o.tag,
                )
            )
        return fills
