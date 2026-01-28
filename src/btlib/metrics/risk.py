import pandas as pd

def drawdown_series(equity: pd.Series)->pd.Series:
    running_peak=equity.cummax()
    dd=equity/running_peak -1
    return dd
def max_drawdown(equity: pd.Series)-> float:
    dd=drawdown_series(equity)
    return dd.min()

