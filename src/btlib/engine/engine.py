from dataclasses import dataclass
import pandas as pd

@dataclass
class BacktestResults:
    ledger: pd.DataFrame
    targets: pd.DataFrame