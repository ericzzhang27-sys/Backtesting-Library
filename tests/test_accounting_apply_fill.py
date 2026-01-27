import pandas as pd
from btlib.core import PortfolioState, Fill
from btlib.engine.accounting import apply_fill

def test_apply_fill_opens_position():
    pf = PortfolioState(ts=pd.Timestamp("2025-06-23"), cash=10_000.0, positions={})
    fill = Fill(ts=pd.Timestamp("2025-06-23"), symbol="AAPL", qty=20.0, price=105.0, fees=0.0, slippage=0.0, tag=None)

    pf2 = apply_fill(pf, fill)

    assert pf2 is not None
    assert "AAPL" in pf2.positions
    assert pf2.positions["AAPL"].qty == 20.0
    assert pf2.cash == 10_000.0 - 20.0 * 105.0
