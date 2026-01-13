from dataclasses import dataclass

@dataclass
class BacktestConfig:
    initial_cash: float = 100_000
    allow_fractional_shares: bool = True
    warmup_bars: int = 0
    fail_on_missing_marks: bool = True
    max_abs_weight: float = 1.0
 