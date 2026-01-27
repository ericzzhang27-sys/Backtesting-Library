import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional
from __future__ import annotations

"""
RETURNS: (EQUITY_f/EQUITY_i) - 1
PERIODS PER YEAR: 252
DDOF = 1
DRAWDOWN = EQUITY/EQUITY.CUMMAX - 1

"""
def equity_to_returns(equity: pd.Series)-> pd.Series:
    if (equity <= 0).any():
        raise ValueError("equity must be > 0 to compute returns")

    returns = equity.pct_change()
    returns.iloc[0]=0.0
    return returns

def total_return(equity: pd.Series) -> float:
    total_return =(equity.iloc[-1]/equity.iloc[0])-1
    return total_return

def cagr(equity: pd.Series, periods_per_year: int = 252)-> float:
    n=len(equity)-1
    if n<=0:
        return 0.0
    cagr = (equity.iloc[-1]/equity.iloc[0])**(periods_per_year/n)-1
    return cagr
def volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    returns= returns.iloc[1:]
    annual_vol=returns.std(ddof=1)*np.sqrt(periods_per_year)
    return annual_vol

def sharpe(returns: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    returns=returns.iloc[1:]
    per_period_rf=rf/periods_per_year
    excess=returns-per_period_rf
    excess = excess.replace([np.inf, -np.inf], np.nan).dropna()
    std=excess.std(ddof=1)
    if std<1e-12:
        return 0.0
    sharpe=(excess.mean()/std)*np.sqrt(periods_per_year)
    return sharpe

def turnover_stats(ledger: pd.DataFrame, fills: pd.DataFrame, periods_per_year: int = 252) -> dict[str, float]:
    if ledger is None or fills is None:
        return {}
    if ledger.empty or fills.empty:
        return {}
    if "equity" not in ledger.columns:
        return {}
    if "notional" not in fills.columns:
        return {}

    notional_by_ts = fills["notional"].groupby(level=0).sum()

    equity = ledger["equity"]
    aligned = pd.DataFrame({"notional": notional_by_ts}).join(equity, how="inner")
    aligned = aligned.replace([np.inf, -np.inf], np.nan).dropna(subset=["equity", "notional"])
    aligned = aligned[aligned["equity"] > 0.0]

    if aligned.empty:
        return {}

    turnover = aligned["notional"] / aligned["equity"]

    out: dict[str, float] = {
        "turnover_mean": float(turnover.mean()),
        "turnover_median": float(turnover.median()),
    }

    out["turnover_annualized"] = float(turnover.mean() * periods_per_year)

    return out
def performance_summary(ledger: pd.DataFrame, rf: float=0.0, periods_per_year=252)-> PerformanceMetrics:
    equity = ledger["equity"]
    returns= equity_to_returns(equity)

    tot= total_return(equity)
    c= cagr(equity, periods_per_year)
    av= volatility(returns,periods_per_year)
    s=sharpe(returns,rf,periods_per_year)
    return PerformanceMetrics(tot, c, av, s)

@dataclass(frozen=True)
class PerformanceMetrics:
    total_return: float
    cagr: float
    annual_vol: float
    sharpe: float
    max_drawdown: Optional[float] = None
