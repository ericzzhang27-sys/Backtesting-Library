from dataclasses import dataclass
import pandas as pd
from btlib.data.market_data import MarketData
from btlib.engine.strategy_base import Strategy
from btlib.engine.config import BacktestConfig
from btlib.core.order_types import PortfolioState
@dataclass
class BacktestResults:
    ledger: pd.DataFrame
    targets: pd.DataFrame
def run_positions_only(market: MarketData, strategy: Strategy, cfg: BacktestConfig) -> BacktestResults:
    ts0=market.timestamps()[0]
    state=PortfolioState(ts = ts0,
                         cash = cfg.initial_cash,
                         positions={}
                         )
    ledger_rows=[]
    targets_rows=[]
    symbols=market.symbols()
    for i, ts in enumerate(market.timestamps()):
        hist = market.slice_upto(ts)

        # no-future guarantee (guard empty first)
        if not hist.empty and hist.index.max() > ts:
            raise ValueError(f"Future leakage at {hist.index.max()} (ts={ts})")

        marks = market.get_price_dict(ts)

        # --- WARMUP BARS ---
        if i < cfg.warmup_bars:
            targets = {}   
        else:
            targets = strategy.on_bar(ts, data_upto_ts=hist, state=state) or {}

        if cfg.max_abs_weight is not None:
            clipped = {}
            for s, w in targets.items():
                w = float(w)
                if abs(w) > cfg.max_abs_weight:
                    w = cfg.max_abs_weight if w > 0 else -cfg.max_abs_weight
                clipped[s] = w
            targets = clipped

        targets_rows.append({"ts": ts, **{s: float(targets.get(s, 0.0)) for s in symbols}})

        if cfg.fail_on_missing_marks:
            for sym in state.positions.keys():
                px = marks.get(sym, None)
                if px is None or not pd.notna(px):
                    raise ValueError(f"Missing mark for held position {sym} at {ts}")
        for sym in targets:
            if sym not in symbols:
                raise ValueError(f"{sym} not found in market data")
        ledger_rows.append({
            "ts": ts,
            "cash": state.cash,
            "equity": state.equity(marks),
            "gross_exposure": state.gross_exposure(marks),
            "net_exposure": state.net_exposure(marks),
            "leverage": state.leverage(marks),
            "n_positions": len(state.positions),
        })


    ledger = pd.DataFrame(ledger_rows).set_index("ts")
    targets = pd.DataFrame(targets_rows).set_index("ts")
    return BacktestResults(ledger=ledger,targets=targets)
        
