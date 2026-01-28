import numpy as np
import pandas as pd
from btlib.engine.strategy_base import Strategy


class PairZScoreStrategy(Strategy):
    def __init__(
        self,
        sym_a: str,
        sym_b: str,
        lookback: int = 60,
        entry_z: float = 2.0,
        exit_z: float = 0.5,
        gross_weight: float = 1.0,
        use_log: bool = True,
        refit_every: int = 1,   # set to 5 or 10 for big speedup
    ):
        self.a = sym_a
        self.b = sym_b
        self.lookback = int(lookback)
        self.entry_z = float(entry_z)
        self.exit_z = float(exit_z)
        self.gross_weight = float(gross_weight)
        self.use_log = bool(use_log)
        self.refit_every = int(refit_every)

        self.regime = 0
        self._beta = 1.0
        self._bar_count = 0

    @staticmethod
    def _beta_no_intercept(y: np.ndarray, x: np.ndarray) -> float:
        # OLS slope y ~ beta * x (no intercept)
        denom = float(np.dot(x, x))
        if denom <= 0.0 or not np.isfinite(denom):
            return 1.0
        b = float(np.dot(x, y) / denom)
        if not np.isfinite(b):
            return 1.0
        return b

    def on_bar(self, ts, data_upto_ts: pd.DataFrame, state):
        # cheap guard
        if self.a not in data_upto_ts.columns or self.b not in data_upto_ts.columns:
            return {}

        # Only use the last lookback window (do NOT dropna over whole history)
        if len(data_upto_ts) < self.lookback:
            return {}

        window = data_upto_ts[[self.a, self.b]].iloc[-self.lookback:]

        # Fast NaN/inf check on just the window
        arr = window.to_numpy(dtype=float, copy=False)  # shape: (lookback, 2)
        if not np.isfinite(arr).all():
            return {}

        pa = arr[:, 0]
        pb = arr[:, 1]

        # guard: prices must be positive for logs
        if self.use_log:
            if (pa <= 0.0).any() or (pb <= 0.0).any():
                return {}
            xa = np.log(pa)
            xb = np.log(pb)
        else:
            xa = pa
            xb = pb

        # Optionally refit beta less often (speed)
        self._bar_count += 1
        if self.refit_every <= 1 or (self._bar_count % self.refit_every == 0):
            self._beta = self._beta_no_intercept(y=xa, x=xb)

        beta = self._beta

        # Spread stats in numpy
        spread = xa - beta * xb
        mu = float(spread.mean())
        sd = float(spread.std(ddof=1))
        if not np.isfinite(sd) or sd < 1e-12:
            return {}

        z = float((spread[-1] - mu) / sd)

        # Regime logic (sticky)
        if self.regime == 0:
            if z > self.entry_z:
                self.regime = -1
            elif z < -self.entry_z:
                self.regime = +1
        else:
            if abs(z) < self.exit_z:
                self.regime = 0

        if self.regime == 0:
            return {self.a: 0.0, self.b: 0.0}

        # weights, normalized to gross_weight
        w_a = (self.gross_weight / 2.0) * self.regime
        w_b = -(self.gross_weight / 2.0) * self.regime * beta

        gross = abs(w_a) + abs(w_b)
        if gross > 1e-12:
            scale = self.gross_weight / gross
            w_a *= scale
            w_b *= scale

        return {self.a: float(w_a), self.b: float(w_b)}
