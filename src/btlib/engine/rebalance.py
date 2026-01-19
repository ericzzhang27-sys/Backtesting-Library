import numpy as np
import pandas as pd

from btlib.core.order_types import require_finite, Order, PortfolioState
from btlib.core.enums import OrderType
from btlib.engine.accounting import close_enough_zero
from btlib.engine import BacktestConfig


def sanitize_targets(
    targets: dict[str, float],
    symbols: list[str],
    max_abs_weight: float,
    *,
    clip: bool = True,
) -> dict[str, float]:
    """
    - Unknown symbol -> raise
    - Missing symbol -> weight 0 (because we build over full `symbols`)
    - Finite weights required
    - Clip (default) or raise if overweight
    """
    symbol_set = set(symbols)

    for sym in targets:
        if sym not in symbol_set:
            raise ValueError(f"{sym} not in symbol universe")

    clean: dict[str, float] = {}
    for sym in symbols:
        w = float(targets.get(sym, 0.0))
        require_finite(sym, w)

        if abs(w) > max_abs_weight:
            if clip:
                w = max(-max_abs_weight, min(max_abs_weight, w))
            else:
                raise ValueError(f"Weight greater than max: {w} for {sym}")

        clean[sym] = w

    return clean


def weights_to_target_shares(
    weights: dict[str, float],
    equity: float,
    prices: dict[str, float],
    allow_fractional: bool = True,
) -> dict[str, float]:
    """
    Converts weights -> target shares using marks at ts.
    Policy here: missing/NaN/<=0 prices => not tradable => omit from output.
    """
    require_finite("equity", float(equity))

    target: dict[str, float] = {}
    for sym, w in weights.items():
        px = prices.get(sym, None)
        if px is None:
            continue
        if (not np.isfinite(px)) or float(px) <= 0.0:
            continue

        target_dollars = float(w) * float(equity)
        shares = target_dollars / float(px)

        if not allow_fractional:
            # truncate toward 0
            shares = float(int(shares))

        target[sym] = shares

    return target


def targets_to_orders(
    ts: pd.Timestamp,
    targets: dict[str, float],
    state: PortfolioState,
    prices: dict[str, float],
    cfg: BacktestConfig,
) -> list[Order]:
    """
    Day 6: create *intended* MARKET orders to move from current holdings to target weights.
    No fills are simulated here.
    """
    # Universe: include all marked symbols + all held symbols (so omitted holdings can be flattened)
    symbols = sorted(set(prices.keys()) | set(state.positions.keys()))

    # Equity at current marks (PortfolioState.equity is strict: requires marks for ALL held symbols)
    equity = state.equity(prices)

    # Pull config safely (in case your cfg field names change later)
    max_abs_weight = getattr(cfg, "max_abs_weight", 1.0)
    min_order_notional = getattr(cfg, "min_order_notional", 10.0)
    allow_fractional = getattr(cfg, "allow_fractional_shares", True)

    weights = sanitize_targets(
        targets=targets,
        symbols=symbols,
        max_abs_weight=max_abs_weight,
        clip=True,  # matches your Day 6 "clipping works" test
    )

    target_shares = weights_to_target_shares(
        weights=weights,
        equity=equity,
        prices=prices,
        allow_fractional=allow_fractional,
    )

    orders: list[Order] = []
    for sym in symbols:
        px = prices.get(sym, None)

        # Not tradable if missing/invalid mark at ts
        if px is None or (not np.isfinite(px)) or float(px) <= 0.0:
            continue

        current = state.get_position(sym).qty

        # If sym was skipped in target_shares (e.g., invalid price), treat as "no trade"
        desired = target_shares.get(sym, current)
        delta = desired - current

        # Skip dust (also prevents Order rejecting qty==0)
        if close_enough_zero(delta):
            continue

        # Notional filter must be in dollars
        if abs(delta * float(px)) < float(min_order_notional):
            continue

        orders.append(
            Order(
                ts=pd.Timestamp(ts),
                order_type=OrderType.MARKET,  # MUST be enum; your Order.__post_init__ enforces this
                symbol=sym,
                qty=float(delta),
            )
        )

    return orders
