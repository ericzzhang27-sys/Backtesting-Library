from btlib.data.market_data import MarketData
from btlib.engine.config import BacktestConfig
from btlib.execution import NextCloseExecution
from btlib.engine import run_positions_only  # your function
from examples.strategy import PairZScoreStrategy
from btlib.metrics import performance_summary
import yfinance as yf
import pandas as pd
tickers=["AAPL","MSFT" ]
close = yf.download(tickers, "2010-10-30","2025-10-30")["Close"]
# Suppose you already built a close-price DataFrame with columns ["AAPL","MSFT"] etc.
market = MarketData(close)

cfg = BacktestConfig(
    initial_cash=100_000.0,
    warmup_bars=60,          # match lookback so early bars don’t trade
    allow_fractional_shares=True,
    max_abs_weight=1.0,
)

strategy = PairZScoreStrategy("AAPL", "MSFT", lookback=60, entry_z=2.0, exit_z=0.5, gross_weight=1.0)

res = run_positions_only(
    market=market,
    strategy=strategy,
    cfg=cfg,
    execution_model=NextCloseExecution(),
    verbose= True
)

metrics = performance_summary(res.ledger, rf=0.0, periods_per_year=252).sharpe
print(metrics)
print(res.trades.sort_values("pnl_net"))
