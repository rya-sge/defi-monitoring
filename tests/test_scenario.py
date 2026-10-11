"""Incident mode (plan 2026-10-10-incident-mode): a known incident's impact, timing and verdict; the alert link."""

import json
from pathlib import Path

import pytest

from riskdep import cli, clock, decide, discover, pipeline, scenario
from riskdep import oracle_class as OC
from riskdep import sources as S
from riskdep.borrower import BorrowMarket, BorrowState
from riskdep.rules import Alert

SNAP = Path(__file__).resolve().parent.parent / "fixtures" / "snapshot"
DEMO_ORACLE = "0xf8b29e7e9c00ce531434775f7923cc9fbca01b08"


@pytest.fixture(scope="module")
def demo():
    clock.set_as_of(json.loads((SNAP / "as_of.json").read_text())["as_of"])  # cache keys hold the snapshot's date
    f = S.Fetcher("offline", SNAP)
    return f, discover.discover_morpho_position(f, pipeline.DEMO_MARKET, pipeline.DEMO_USER)


QUOTE = {"price_impact": 0.02, "fee_usd": 500.0, "source": "test quote"}


# --- parsing


def test_parse_shocks():
    assert scenario.parse_shocks(["oracle=0.10", "issuer_depeg=0.08"]) == {"oracle": 0.10, "issuer_depeg": 0.08}
    assert scenario.parse_shocks(None) == {}
    for bad in ("foo=0.1", "oracle=1.5", "oracle", "oracle=x"):
        with pytest.raises(ValueError):
            scenario.parse_shocks([bad])


# --- decision and timing (pure)


def test_verdict_given():
    assert decide.verdict_given(100.0, 50.0)[0] == "EXIT"
    assert decide.verdict_given(10.0, 50.0)[0] == "STAY"
    assert decide.verdict_given(100.0, 50.0, 5.0, 0.0)[0] == "REDUCE"  # a cheap de-lever beats both
    assert decide.verdict_given(100.0, 50.0, 40.0, 30.0)[0] == "EXIT"  # 70 > 50: leaving is cheaper


def P(kind, **kw):
    return scenario.OracleProfile(kind, "test", **kw)


def test_time_to_impact_by_oracle_type():
    dep = {"issuer_depeg": 0.08}
    assert scenario.time_to_impact(P(OC.CONSTANT_PRICE), dep).never
    assert scenario.time_to_impact(P(OC.PRICE_TRACKING, twap_s=900), dep).seconds == 900
    assert "next update" in scenario.time_to_impact(P(OC.PRICE_TRACKING), dep).text
    assert scenario.time_to_impact(P(OC.NOT_CLASSIFIED), dep).seconds is None
    assert scenario.time_to_impact(None, {"oracle": 0.1}).seconds == 0
    meta = P(
        "meta-oracle",
        timelock_s=57600,
        deviation_threshold=0.0075,
        on_primary=True,
        live=P(OC.CONSTANT_PRICE),
        other=P(OC.PRICE_TRACKING),
    )
    t = scenario.time_to_impact(meta, dep)
    assert t.seconds == 57600 and not t.never and "16 h" in t.text
    assert scenario.oracle_mode_for(meta, "market-tracking") == "fundamental"


# --- on the demo position (offline)


def test_demo_oracle_profile_is_read_from_the_snapshot(demo):
    f, _ = demo
    p = scenario.oracle_profile(f, DEMO_ORACLE)
    assert p.kind == "meta-oracle" and p.timelock_s == 57600 and p.on_primary is True
    assert p.live.kind == OC.CONSTANT_PRICE and p.other.kind == OC.PRICE_TRACKING


def test_oracle_shock_around_the_liquidation_distance(demo):
    _, pos = demo
    d = pos.liquidation_drop  # 5.16 % on the demo
    below = scenario.assess(pos, {"oracle": d - 0.002}, 0.0, QUOTE, None)
    above = scenario.assess(pos, {"oracle": d + 0.002}, 0.0, QUOTE, None)
    assert not below.liquidated and below.loss_usd == 0
    assert above.liquidated and above.loss_usd > 0
    assert above.verdict == "REDUCE" and above.reduction and not above.reduction["liquidated_after"]


def test_demo_depeg_waits_for_the_meta_oracle_switch(demo):
    f, pos = demo
    r = scenario.assess(pos, {"issuer_depeg": 0.08}, 0.75, QUOTE, scenario.oracle_profile(f, DEMO_ORACLE))
    assert not r.liquidated  # the live source is a linear discount
    assert r.after_switch and r.after_switch["liquidated"]  # the backup follows USDe / USD
    assert r.timing.seconds == 57600


def test_cli_incident_mode(tmp_path, capsys):
    assert cli.main(["analyze", "--demo", "--out", str(tmp_path), "--paths", "2000", "--shock", "oracle=0.10"]) == 0
    out = capsys.readouterr().out
    assert "INCIDENT" in out and "EX ANTE" in out
    inc = json.loads((tmp_path / "report.json").read_text())["incident"]
    assert inc["liquidated"] and inc["verdict"] in ("STAY", "REDUCE", "EXIT")
    with pytest.raises(SystemExit):
        cli.main(["analyze", "--demo", "--out", str(tmp_path), "--shock", "nothing=0.1"])


# --- the alert link (D93)


def test_alert_impact_both_directions():
    up = scenario.alert_impact(0.04, collateral_value=100.0, debt=90.0, lltv=0.915)
    assert not up["liquidated"] and up["loss"] == pytest.approx(100.0 * 0.04 / 1.04)
    down = scenario.alert_impact(-0.05, collateral_value=95.0, debt=90.0, lltv=0.915)
    assert down["liquidated"]  # the oracle reads 95 × 0.915 < 90


def _market():
    return BorrowMarket("0xm", "0xloan", "0xcoll", "0xorc", "0xirm", int(0.915e18), "USDC", "PT", 6, 18)


def test_divergence_alert_carries_the_impact():
    m = _market()
    st = BorrowState("0xm", 10**18, 1, 90 * 10**6, 100 * 10**24, 10**9, 10**8, None)  # collateral worth 100 USDC
    al = Alert("warn", 1, None, "OracleDivergence", "gap", "oracle vs market", None, {"market": "0xm", "gap": 0.04})
    scenario.enrich_divergence([al], {"0xm": m}, {"0xm": st}, {"0xm": P(OC.CONSTANT_PRICE)})
    assert al.data["incident"]["loss"] == pytest.approx(100 * 0.04 / 1.04)
    assert al.depositor_impact < 0 and "never" in al.detail
    other = Alert("warn", 1, None, "OracleDivergence", "gap", "x", None, {"market": "0xother", "gap": 0.04})
    scenario.enrich_divergence([other], {"0xm": m}, {"0xm": st}, {})
    assert "incident" not in other.data  # not a borrowed market


def test_ex_ante_mode_from_structure():
    meta = P(
        "meta-oracle",
        timelock_s=57600,
        live=P(OC.CONSTANT_PRICE),
        other=P(OC.PRICE_TRACKING),
        deviation_threshold=0.0075,
    )
    assert scenario.ex_ante_mode(meta, 30)[0] == "market-tracking"  # the switch happens within the horizon
    assert scenario.ex_ante_mode(meta, 0.5)[0] == "fundamental"  # 16 h after a 12 h horizon
    assert scenario.ex_ante_mode(P(OC.CONSTANT_PRICE), 30)[0] == "fundamental"
    assert scenario.ex_ante_mode(P(OC.NOT_CLASSIFIED), 30) is None


def test_demo_oracle_mode_is_no_longer_ambiguous(tmp_path):
    assert cli.main(["analyze", "--demo", "--out", str(tmp_path), "--paths", "2000"]) == 0
    pos = json.loads((tmp_path / "report.json").read_text())["position"]
    assert pos["oracle_mode"] == "market-tracking" and not pos["oracle_ambiguous"]
    assert any("within the 30-day horizon" in n for n in pos["notes"])
