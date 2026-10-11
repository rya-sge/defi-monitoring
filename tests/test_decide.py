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


def test_a_gap_inside_the_sampling_error_is_not_a_reason():
    """IMPROVEMENT 2.2: carry 4.93 against an expected loss of 5.5; with ± 0.6 (95 %) the simulation cannot tell them
    apart, so it is no reason to REDUCE; with no sampling error it is."""
    p = pos(debt_usd=0.0, lltv=None)
    noisy = sim(el=5.5)
    noisy.expected_loss_se = 0.6 / 1.96
    d = verdict(p, noisy, QUOTE)
    assert d.verdict == "STAY" and "± $1" in d.reasons[0]
    assert verdict(p, sim(el=5.5), QUOTE).verdict == "REDUCE"


def test_exit_when_de_levering_leaves_the_tail_unsurvivable():
    """D195 (K13): the de-lever's simulated CVaR99 still above 90 % of equity: EXIT rather than REDUCE."""
    p = pos()
    d = verdict(p, sim(el=0.1, cvar99=1.0), QUOTE, depeg_mean=0.08, resimulate=lambda q: sim(el=0.05, cvar99=1e9))
    assert d.verdict == "EXIT" and "even after de-levering" in d.headline
    assert (
        verdict(p, sim(el=0.1, cvar99=1.0), QUOTE, depeg_mean=0.08, resimulate=lambda q: sim(el=0.05)).verdict
        == "REDUCE"
    )


# --- the priors: oracle exploits counted once (D232), Morpho Blue's core prior (D233)


def test_oracle_exploits_are_counted_by_the_oracle_layer_only():
    import json as _json

    from riskdep import clock, priors
    from riskdep import sources as S
    from riskdep.discover import REGISTRY

    clock.set_as_of(_json.loads((S.SNAPSHOT_DIR / "as_of.json").read_text())["as_of"])
    st = priors.hack_stats(S.Fetcher("offline"))
    assert st["oracle_moved"] == {"Lending": 3, "Yield Aggregator": 1}
    assert st["tier_rate"][2] == pytest.approx(0.025, abs=1e-4)
    p, note = priors.exploit_p_year(st, "morpho-blue", "Lending")
    assert p == pytest.approx(0.025, abs=1e-4) and "not applied (isolated markets" in note
    assert REGISTRY["protocols"]["morpho-blue"]["isolated_markets"]
    p_pendle, note_pendle = priors.exploit_p_year(st, "pendle-v2", "Yield")
    assert p_pendle == pytest.approx(0.0117, abs=2e-4) and "× category 'Yield'" in note_pendle
