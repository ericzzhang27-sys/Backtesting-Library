# tests/test_rebalance_targets_to_orders.py
import math
import numpy as np
import pandas as pd
import pytest

from btlib.core.enums import OrderType
from btlib.core.order_types import PortfolioState
from btlib.engine import BacktestConfig
from btlib.engine.rebalance import targets_to_orders


def _cfg(
    *,
    max_abs_weight: float = 1.0,
    min_order_notional: float = 10.0,
    allow_fractional_shares: bool = True,
) -> BacktestConfig:
    """
    Helper to build a config with the fields Day 6 expects.
    If your BacktestConfig uses different field names, update here once.
    """
    cfg = BacktestConfig()
    cfg.max_abs_weight = max_abs_weight
    cfg.min_order_notional = min_order_notional
    cfg.allow_fractional_shares = allow_fractional_shares
    return cfg


def _orders_by_symbol(orders):
    return {o.symbol: o for o in orders}


def test_weight_1_produces_full_investment_buy():
    ts = pd.Timestamp("2024-01-02")
    state = PortfolioState(ts=ts, cash=1000.0, positions={})
    prices = {"A": 100.0}
    cfg = _cfg(min_order_notional=0.0)

    orders = targets_to_orders(ts=ts, targets={"A": 1.0}, state=state, prices=prices, cfg=cfg)
    assert len(orders) == 1
    o = orders[0]
    assert o.symbol == "A"
    assert o.order_type == OrderType.MARKET
    assert math.isclose(o.qty, 10.0, rel_tol=0, abs_tol=1e-9)


def test_weight_half_produces_half_investment_buy():
    ts = pd.Timestamp("2024-01-02")
    state = PortfolioState(ts=ts, cash=1000.0, positions={})
    prices = {"A": 100.0}
    cfg = _cfg(min_order_notional=0.0)

    orders = targets_to_orders(ts=ts, targets={"A": 0.5}, state=state, prices=prices, cfg=cfg)
    assert len(orders) == 1
    assert math.isclose(orders[0].qty, 5.0, rel_tol=0, abs_tol=1e-9)


def test_existing_position_reduces_correctly():
    ts = pd.Timestamp("2024-01-02")
    state = PortfolioState(ts=ts, cash=1000.0, positions={})
    state.get_position("A").qty = 10.0  # already long 10
    prices = {"A": 100.0}
    cfg = _cfg(min_order_notional=0.0)

    # equity = cash + 10*100 = 2000
    # target 0.5 => target dollars 1000 => target shares 10
    # delta = 0
    orders = targets_to_orders(ts=ts, targets={"A": 0.5}, state=state, prices=prices, cfg=cfg)
    assert orders == []


def test_existing_position_sells_down_to_target():
    ts = pd.Timestamp("2024-01-02")
    state = PortfolioState(ts=ts, cash=1000.0, positions={})
    state.get_position("A").qty = 10.0
    prices = {"A": 100.0}
    cfg = _cfg(min_order_notional=0.0)

    # equity = 2000
    # target 0.25 => target dollars 500 => target shares 5
    # delta = -5
    orders = targets_to_orders(ts=ts, targets={"A": 0.25}, state=state, prices=prices, cfg=cfg)
    assert len(orders) == 1
    assert math.isclose(orders[0].qty, -5.0, rel_tol=0, abs_tol=1e-9)


def test_long_to_short_crossing_delta_is_correct():
    ts = pd.Timestamp("2024-01-02")
    state = PortfolioState(ts=ts, cash=1000.0, positions={})
    state.get_position("A").qty = 5.0
    prices = {"A": 100.0}
    cfg = _cfg(min_order_notional=0.0)

    # equity = 1000 + 5*100 = 1500
    # target weight -1.0 => target dollars -1500 => target shares -15
    # delta = -15 - 5 = -20
    orders = targets_to_orders(ts=ts, targets={"A": -1.0}, state=state, prices=prices, cfg=cfg)
    assert len(orders) == 1
    assert math.isclose(orders[0].qty, -20.0, rel_tol=0, abs_tol=1e-9)


def test_clipping_overweight_to_max_abs_weight():
    ts = pd.Timestamp("2024-01-02")
    state = PortfolioState(ts=ts, cash=1000.0, positions={})
    prices = {"A": 100.0}
    cfg = _cfg(max_abs_weight=1.0, min_order_notional=0.0)

    # target weight 2.0 should be clipped to 1.0 -> 10 shares
    orders = targets_to_orders(ts=ts, targets={"A": 2.0}, state=state, prices=prices, cfg=cfg)
    assert len(orders) == 1
    assert math.isclose(orders[0].qty, 10.0, rel_tol=0, abs_tol=1e-9)


def test_min_notional_drops_tiny_orders():
    ts = pd.Timestamp("2024-01-02")
    state = PortfolioState(ts=ts, cash=1000.0, positions={})
    prices = {"A": 100.0}
    cfg = _cfg(min_order_notional=50.0)  # dollars

    # target 0.01 => target dollars 10 => target shares 0.1 => notional 10 < 50 => drop
    orders = targets_to_orders(ts=ts, targets={"A": 0.01}, state=state, prices=prices, cfg=cfg)
    assert orders == []


def test_integer_share_truncation_toward_zero():
    ts = pd.Timestamp("2024-01-02")
    state = PortfolioState(ts=ts, cash=1000.0, positions={})
    prices = {"A": 333.33}
    cfg = _cfg(min_order_notional=0.0, allow_fractional_shares=False)

    # equity 1000, target shares = 1000/333.33 = 3.00003..., truncate -> 3
    orders = targets_to_orders(ts=ts, targets={"A": 1.0}, state=state, prices=prices, cfg=cfg)
    assert len(orders) == 1
    assert orders[0].qty == 3.0


def test_omitted_symbol_flattens_existing_holding():
    ts = pd.Timestamp("2024-01-02")
    state = PortfolioState(ts=ts, cash=1000.0, positions={})
    state.get_position("MSFT").qty = 10.0

    # Must include mark for MSFT because PortfolioState.equity() requires it for held positions
    prices = {"AAPL": 100.0, "MSFT": 50.0}
    cfg = _cfg(min_order_notional=0.0)

    # Strategy only mentions AAPL; MSFT is omitted -> treated as 0 weight -> should sell to 0 shares
    orders = targets_to_orders(ts=ts, targets={"AAPL": 0.0}, state=state, prices=prices, cfg=cfg)
    od = _orders_by_symbol(orders)

    assert "MSFT" in od
    assert math.isclose(od["MSFT"].qty, -10.0, rel_tol=0, abs_tol=1e-9)
