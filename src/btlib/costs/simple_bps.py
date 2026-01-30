from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from btlib.costs.base import CostModel
from btlib.core.order_types import Fill

"""
A simple linear cost model that calculates fees and slippage as a
linearly increasing percentage of the notional value of each fill
"""
@dataclass(frozen = True)
class SimpleBpsCost(CostModel):
    fees_bps: float = 0.0
    slippage_bps: float = 0.0

    def __post_init__(self) -> None:
        for name, v in (("fees_bps", self.fees_bps), ("slippage_bps", self.slippage_bps)):
            v = float(v)
            if not np.isfinite(v):
                raise ValueError(f"{name} must be finite, got {v!r}")
            if v < 0.0:
                raise ValueError(f"{name} must be >= 0, got {v!r}")

    def compute(self, fill: Fill) -> tuple[float, float]:
        notional = abs(float(fill.qty)) * float(fill.price)
        fees = notional * (float(self.fees_bps) / 10_000.0)
        slippage = notional * (float(self.slippage_bps) / 10_000.0)
        return fees, slippage
