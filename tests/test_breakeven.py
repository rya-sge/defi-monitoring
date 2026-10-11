"""Breakeven probability and the Nexus outside view (plan 2026-10-11-breakeven)."""

import json
from pathlib import Path

import pytest

from riskdep import cli
from riskdep import nexus as NX
from riskdep import sources as S
from riskdep import vault_incident as VI

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "examples" / "rockawayx-ethereum.json"
FX = "0x2ca22cb25558fa2018ecb1ce4ed8af92ee7ea423"
BELEM = "0xd6d4b804014ef27836dbe9f8f6bf6c71251548ec"


def test_breakeven_formula():
    cost, p, py = VI.breakeven(stay=100.0, leave=0.0, par=1000.0, apy=0.073, days=30)
    assert cost == pytest.approx(6.0) and p == pytest.approx(0.06) and py == pytest.approx(1 - 0.94 ** (365 / 30))
    assert VI.breakeven(100.0, 100.0, 1000.0, 0.05, 30)[1] is None  # leaving first saves nothing
    assert VI.breakeven(1.0, 0.0, 1000.0, 0.05, 30)[1] > 1  # the yield given up exceeds the saving
    assert VI.breakeven(100.0, 0.0, 1000.0, None, 30) == (0.0, None, None)


def test_nexus_covers_and_implied_probability():
    products = [{"id": 446, "name": "Tori Finance", "type": 0}, {"id": 999, "name": "Other", "type": 0}]
    capacity = [{"id": 446, "min": 0.0233, "max": 0.0233, "usdc": 2.5e6}, {"id": 999, "min": 0, "max": 0, "usdc": 0}]
    trusd, strusd = "0xd0580192e98ea6ceb9c7b6191ed2e27560911697", "0x280839980a7ed0d7717f64125fe241012e5f5815"
    (c,) = NX.covers(products, capacity, [strusd, trusd, "0x" + "1" * 40])  # one product, listed once
    assert c.name == "Tori Finance" and c.kind == "protocol"
    lo, hi = NX.implied(c, 0.3)
    assert lo == pytest.approx(0.0233 / 1.5) and hi == pytest.approx(0.0233 / 0.6)
    assert "not on an issuer's markdown" in NX.outside_line(c, 0.3)


def test_recorded_nexus_offline():
    nx = NX.load(S.Fetcher("offline", ROOT / "fixtures" / "replay" / "nexus"))
    assert nx is not None and any(p["name"] == "Tori Finance" for p in nx[0])


def test_vault_breakeven_offline(tmp_path):
    assert cli.main(["analyze", "--vault", FX, "--shock", "token=fxSAVE:0.30", "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / f"vault-incident-{FX}.json").read_text())
    assert 0.08 < r["apy"] < 0.09 and r["horizon_days"] == 30
    assert r["exit_cost"] == pytest.approx(r["can_leave_now"] * r["apy"] * 30 / 365)
    assert r["p_star"] == pytest.approx(r["exit_cost"] / (r["loss_if_stay"] - r["loss_if_exit_first"]))
    assert any("f(x) Protocol" in o for o in r["outside"])


def test_dominant_depositor_stays_whatever_the_odds(tmp_path, capsys):
    """Belem's depositor is 99.46 % of the vault: leaving first saves less than the yield it gives up."""
    assert cli.main(["analyze", "--vault", BELEM, "--shock", "token=mGLOeuro:0.30", "--out", str(tmp_path)]) == 0
    assert json.loads((tmp_path / f"vault-incident-{BELEM}.json").read_text())["p_star"] > 1
    assert "stay even if the incident is certain" in capsys.readouterr().out


def test_book_acts_first_on_the_lowest_breakeven(tmp_path):
    assert cli.main(["analyze", "--book", str(BOOK), "--shock", "token=PST:0.30", "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / "book-incident.json").read_text())
    ranked = sorted((ln for ln in r["lines"] if ln["p_star"] is not None), key=lambda ln: ln["p_star"])
    assert ranked and f"Act first on {ranked[0]['name']}" in r["headline"]
    assert r["p_star"] is not None and any("book's breakeven" in n for n in r["notes"])
