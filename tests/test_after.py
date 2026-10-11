"""After the incident (plan 2026-10-11-after, D228–D231): what has landed, what is still at risk, and the verdict on
that part only."""

import json

import pytest

from riskdep import after as AF
from riskdep import cli, pipeline

BELEM = "0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec"
YIELD = "0xE0181090c22579B6A217f1522cbf8c9f1F0C1965"
REUSD = "token=PT-reUSD-10DEC2026"


def test_the_fall_already_taken_is_not_applied_again():
    assert AF.remaining_drop(100, 100, 0.3) == (0.0, pytest.approx(0.3))  # a NAV feed not yet updated: all to come
    seen, todo = AF.remaining_drop(100, 90, 0.3)  # the oracle took 10 % of a 30 % incident
    assert seen == pytest.approx(0.1) and todo == pytest.approx(1 - 70 / 90)
    assert AF.remaining_drop(100, 65, 0.3)[1] == 0  # it fell further than the incident: nothing pending
    assert AF.landed_loss(10, 1.0, 0.9, 1) == pytest.approx(1) and AF.landed_loss(10, 1.0, 1.1, 1) == 0


def test_at_its_first_block_the_incident_is_all_still_to_come():
    """Read at the block the incident begins, nothing has landed and the pending part is the before-mode loss."""
    r = pipeline.after_incident(BELEM, 26165064, None, ["token=mGLOeuro:0.30"])
    assert r.landed == 0 and r.unrealised == 0 and r.pending == pytest.approx(251_761, rel=1e-3)


def test_the_reusd_episode_after_the_liquidations(tmp_path, capsys):
    """2026-08-25, the PT-reUSD market of RockawayX USDC Yield 132 blocks on: 16 liquidations repaid 35.19M, nothing
    written off; the price-tracking oracle already took the 2.45 % fall, so nothing is pending (no double count)."""
    args = ["analyze", "--vault", YIELD, "--since", "25829808", "--at", "25829940", "--shock", f"{REUSD}:0.0245"]
    assert cli.main([*args, "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / f"after-{YIELD.lower()}-25829808-25829940.json").read_text())
    (m,) = r["markets"]
    assert m["liquidations"] == 16 and m["repaid"] == pytest.approx(35_188_280, rel=1e-6) and m["written_off"] == 0
    assert m["oracle_seen"] > 0.0245 and r["pending"] == 0 and r["at_risk"] == 0 and r["landed"] == 0
    assert "what has landed is sunk either way" in capsys.readouterr().out


def test_a_larger_incident_leaves_a_pending_part_weighed_against_the_cost():
    """Had the incident been a 10 % fall, 7.42 % would still be to come: 9.8k pending for the vault; leaving would
    save its depositor 1.2k, less than the 11.1k it costs: STAY."""
    r = pipeline.after_incident(YIELD, 25829808, 25829940, [f"{REUSD}:0.10"])
    assert r.pending == pytest.approx(9_818, rel=1e-2) and r.markets[0].pending_drop == pytest.approx(0.0742, abs=1e-3)
    assert r.verdict == "STAY" and "less than the" in r.reason


def test_after_over_the_api():
    from fastapi.testclient import TestClient

    from riskdep.api import app

    body = {"vault": YIELD, "since": 25829808, "at": 25829940, "shocks": [f"{REUSD}:0.10"]}
    r = TestClient(app).post("/api/incident/after", json=body)
    assert r.status_code == 200 and r.json()["at_risk"] == pytest.approx(9_818, rel=1e-2)
