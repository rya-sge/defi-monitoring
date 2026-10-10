import networkx as nx
import numpy as np
import pytest

from riskdep.decide import sale_to_reach, verdict
from riskdep.discover import Position
from riskdep.simulate import SimResult


def pos(**kw):
    base = dict(
        label="t",
        collateral_units=1000.0,
        collateral_symbol="PT-X",
        collateral_address="0x1",
        pt_price_usd=1.0,
        debt_usd=900.0,
        lltv=0.915,
        lif=1.026,
        borrow_apy=0.04,
        implied_apy=0.06,
        health_factor=1.017,
        oracle_mode="market-tracking",
        underlying_drawdown_1y=0.02,
        graph=nx.DiGraph(),
    )
    base.update(kw)
    return Position(**base)


def sim(el, cvar99=0.0, days=30):
    return SimResult(days, 1000, el, 0, 0, 0, cvar99, 0.01, 0.0, [], 0.0, np.zeros(10))


QUOTE = {"price_impact": 0.01, "fee_usd": 0.0, "source": "test"}


def test_sale_to_reach_hits_the_target_drop():
    p = pos()
    sell = sale_to_reach(p, 0.12)
    after = pos(collateral_units=1000 - sell, debt_usd=900 - sell)
    assert after.liquidation_drop == pytest.approx(0.12)


def test_exit_when_expected_loss_beats_carry_and_exit_cost():
    d = verdict(pos(debt_usd=0.0, lltv=None), sim(el=50.0), QUOTE)
    assert d.verdict == "EXIT"


def test_stay_when_carry_covers_and_tail_is_small():
    d = verdict(pos(debt_usd=0.0, lltv=None), sim(el=0.1, cvar99=10.0), QUOTE)
    assert d.verdict == "STAY"


def test_reduce_when_liquidation_is_closer_than_the_stress():
    d = verdict(pos(), sim(el=0.1, cvar99=1.0), QUOTE, depeg_mean=0.08, resimulate=lambda p: sim(el=0.05))
    assert d.verdict == "REDUCE"
    assert d.reduction is not None and d.reduction.new_liquidation_drop == pytest.approx(d.stress_drop)
