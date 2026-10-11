"""Detection → impact for a vault (plan 2026-10-11-detect): the rule, and the fork demo's recorded crisis."""

import json
from types import SimpleNamespace

import pytest

from riskdep import detect as DT
from riskdep.cli import REPLAY_DIR, main

VAULT = "0xd6d4b804014ef27836dbe9f8f6bf6c71251548ec"


def _st(prices):
    return SimpleNamespace(markets={m: SimpleNamespace(oracle_price=p) for m, p in prices.items()})


def test_falls_are_measured_from_the_last_answer():
    known = DT.last_prices({}, _st({"a": 100, "b": 100}))
    gap = _st({"a": None, "b": 99})  # a's oracle stops answering (a feed being upgraded)
    known = DT.last_prices(known, gap)
    assert known == {"a": 100, "b": 99}
    falls = DT.oracle_falls(known, _st({"a": 70, "b": 98}), {"a": 0, "b": 0})
    assert falls == {"a": pytest.approx(0.30)}  # b's 1 % is below impact_oracle_fall


@pytest.fixture(scope="module")
def impacts(tmp_path_factory):
    out = tmp_path_factory.mktemp("detect")
    from riskdep import sources as S

    fork = S.FORK
    try:
        assert main(["watch", "--vault", VAULT, "--replay", "--record-as", "fork-belem", "--out", str(out)]) == 0
    finally:
        S.FORK = fork
    rows = [json.loads(x) for x in (out / f"watch-{VAULT}.jsonl").read_text().splitlines()]
    return [r for r in rows if r["event"] == "OracleImpact"]


def test_the_fork_crisis_alerts_carry_the_impact(impacts):
    """Act 2, the issuer's −10 %: liquidatable, no loss yet; act 6, the NAV at 70,000 after the timelocked upgrade:
    the vault's loss stated when the price lands, 1.1 % from the 217,286 realised by the liquidation four blocks on."""
    act2, act6 = impacts
    assert act2["level"] == "warn" and act2["data"]["vault_loss"] == 0 and act2["data"]["verdict"] == "STAY"
    assert act2["data"]["liquidatable"] and "−10.0%" in act2["title"]
    assert act6["level"] == "critical" and "−22.2%" in act6["title"]
    assert act6["data"]["vault_loss"] == pytest.approx(217_286, rel=0.02)
    assert act6["depositor_impact"] == pytest.approx(-act6["data"]["loss_if_stay"])
    assert REPLAY_DIR.joinpath("fork-belem", "start.json").exists()
