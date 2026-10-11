"""A book of vaults under one incident (plan 2026-10-11-vault-book): the file, the sum, the recorded RockawayX book."""

import json
from pathlib import Path

import pytest

from riskdep import cli
from riskdep import vault_book as VB
from riskdep.vault_incident import MarketHit, VaultIncident

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "examples" / "rockawayx-ethereum.json"
A, B = "0x" + "a" * 40, "0x" + "b" * 40


def test_parse_checks_the_book():
    b = VB.parse({"vaults": [A, {"address": B.upper().replace("0X", "0x"), "label": "B", "depositor": "0xD"}]})
    assert b.weighting == "vault" and [v.address for v in b.vaults] == [A, B] and b.vaults[1].depositor == "0xd"
    for bad in ({}, {"vaults": []}, {"vaults": ["0x12"]}, {"vaults": [A, A]}, {"vaults": [A], "weighting": "x"}):
        with pytest.raises(ValueError):
            VB.parse(bad)
    assert VB.from_addresses([A, B], "0xD").weighting == "depositor"


def _inc(vault, total, loss, dep, stay, exposure, verdict="STAY", usd=1.0, hit=True):
    hits = [MarketHit("m", "X/USDC", 0.3, 1, 0, 0, loss, 1.0, loss, "constant-price", "", exposure)] if hit else []
    return VaultIncident(
        vault,
        vault[:6],
        "USDC",
        1,
        "0xd",
        {"X": 0.3},
        hits,
        total,
        loss,
        dep,
        stay,
        0,
        0,
        0,
        verdict,
        "",
        [],
        "0xusdc",
        usd,
    )


def test_aggregate_in_both_weightings():
    incs = [_inc(A, 100, 10, 50, 5, 40, "EXIT"), _inc(B, 200, 0, 20, 0, 0, hit=False)]
    incs[0].p_star, incs[0].p_star_year = 0.05, 0.46  # leaving A pays from a 5 % chance over the horizon
    v = VB.aggregate(VB.parse({"vaults": [A, B]}), [("x", 0.3)], incs)
    assert (v.value_usd, v.loss_usd, v.exposure_usd) == (300, 10, 40)
    assert v.headline.startswith("X −30%") and "Act first on" in v.headline
    d = VB.aggregate(VB.parse({"vaults": [A, B], "weighting": "depositor"}), [("x", 0.3)], incs)
    assert (d.value_usd, d.loss_usd, d.exposure_usd) == (70, 5, 20)  # the depositor's half of vault A
    eur = VB.aggregate(VB.parse({"vaults": [A]}), [("x", 0.3)], [_inc(A, 100, 10, 50, 5, 40, usd=1.1)])
    assert eur.loss_usd == pytest.approx(11)


def test_recorded_rockawayx_book_offline(tmp_path, capsys):
    assert cli.main(["analyze", "--book", str(BOOK), "--shock", "token=PST:0.30", "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / "book-incident.json").read_text())
    hit = {ln["name"] for ln in r["lines"] if ln["hit_markets"]}
    assert hit == {"RockawayX Confidential RWA USDC", "Huma USDC Main"}  # Huma's PST backs two vaults
    assert 5_000_000 < r["loss_usd"] < 5_400_000 and 98e6 < r["value_usd"] < 100e6
    assert "PST −30%" in capsys.readouterr().out


def test_ad_hoc_book_from_vault_flags(tmp_path):
    belem, huma = "0xd6d4b804014ef27836dbe9f8f6bf6c71251548ec", "0x8ac91877b93330f52b2979a31a4879506021475c"
    args = ["analyze", "--vault", belem, "--vault", huma, "--shock", "token=mGLOeuro:0.30", "--out", str(tmp_path)]
    assert cli.main(args) == 0
    r = json.loads((tmp_path / "book-incident.json").read_text())
    assert [ln["name"] for ln in r["lines"] if ln["hit_markets"]] == ["Belem RWA EURCV"]


def test_unrecorded_vault_is_refused(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["analyze", "--vault", "0x" + "1" * 40, "--shock", "token=x:0.3", "--out", str(tmp_path)])


def test_book_borrower_default_reaches_every_vault(tmp_path, capsys):
    args = ["analyze", "--book", str(BOOK), "--shock", "borrower=all:0.5", "--out", str(tmp_path)]
    assert cli.main(args) == 0
    r = json.loads((tmp_path / "book-incident.json").read_text())
    assert all(ln["hit_markets"] for ln in r["lines"]) and r["loss_usd"] > 10e6
    assert r["shocks"] == ["the largest borrower of every market defaults, collateral recovered at 50%"]


def test_book_contagion_skips_markets_the_book_holds(tmp_path):
    """PRIME/USDC is a sibling in the NUVA vault's graph, but RockawayX USDC Yield holds it: not contagion."""
    assert cli.main(["analyze", "--book", str(BOOK), "--shock", "token=PRIME:0.30", "--out", str(tmp_path)]) == 0
    note = next(n for n in json.loads((tmp_path / "book-incident.json").read_text())["notes"] if "contagion" in n)
    assert "PRIME/PYUSD" in note and "PRIME/USDC" not in note


def test_every_line_says_why(tmp_path):
    """IMPROVEMENT 2.1: every reached vault says why. Confidential RWA's 99 % holder is the Zama cShare pool, so its
    default depositor is now the largest public holder, for whom leaving first pays (plan 2026-10-11-zama)."""
    assert cli.main(["analyze", "--book", str(BOOK), "--shock", "token=PST:0.30", "--out", str(tmp_path)]) == 0
    lines = {ln["name"]: ln for ln in json.loads((tmp_path / "book-incident.json").read_text())["lines"]}
    assert lines["RockawayX Confidential RWA USDC"]["reason"].startswith("leaving pays above")
    assert lines["Huma USDC Main"]["reason"].startswith("leaving pays above")
    assert lines["Belem RWA EURCV"]["reason"] == ""  # not reached


def test_pocket_line_first_in_the_queue():
    inc = _inc(A, 1000, 100, 0, 0, 500)  # the vault loses 10 %
    inc.liquidity, inc.apy, inc.horizon_days = (200.0, 0.0, 0.0), 0.05, 30
    a, stay, leave, par, cost, p, _, verdict = VB.pocket(inc, 100.0)
    assert (a, stay, par) == (100, pytest.approx(10.0), 100) and leave == 0  # it all leaves at par, first
    assert cost == pytest.approx(100 * 0.05 * 30 / 365) and verdict == "EXIT"
    inc.exit_cost_rate = 0.11  # the brief's 11 % unwind: 11 to save 10
    assert VB.pocket(inc, 100.0)[-1] == "STAY"
    with pytest.raises(ValueError):
        VB.parse({"weighting": "pocket", "vaults": [A]})  # a pocket needs its amount


TEN = ROOT / "examples" / "brief-ten-pockets.json"


def test_the_briefs_ten_pockets(tmp_path):
    """The brief's book: ten 1M pockets, one hit (mGLOeuro is Belem's only). At an 11 % unwind, leaving costs
    110,000 for sure against 53k saved: stay; at the yield given up, leaving pays above a 4 % chance."""
    args = ["analyze", "--book", str(TEN), "--shock", "token=mGLOeuro:0.30", "--out", str(tmp_path)]
    assert cli.main([*args, "--exit-cost", "0.11"]) == 0
    r = json.loads((tmp_path / "book-incident.json").read_text())
    assert r["value_usd"] == pytest.approx(10e6) and [ln["name"] for ln in r["lines"] if ln["hit_markets"]] == [
        "Belem RWA EURCV"
    ]
    (hit,) = [ln for ln in r["lines"] if ln["hit_markets"]]
    assert hit["exit_cost_usd"] == pytest.approx(110_000) and hit["verdict"] == "STAY" and "110,000" in r["headline"]
    assert cli.main(args) == 0
    hit = next(ln for ln in json.loads((tmp_path / "book-incident.json").read_text())["lines"] if ln["hit_markets"])
    assert hit["verdict"] == "EXIT" and 0.03 < hit["p_star"] < 0.05


MIXED = ROOT / "examples" / "brief-mixed-book.json"


def test_the_briefs_own_pt_loop_as_a_pocket(tmp_path):
    """D177–D178: the brief's book with its own example, the PT-sUSDe loop on Morpho, as a borrow pocket next to nine
    vault pockets. sUSDe losing 8 % of its backing hits that pocket only: leaving it costs 110,000 for sure (the 11 %
    unwind) against a 776,708 loss if it stays: EXIT, by the same rule as a vault pocket."""
    args = ["analyze", "--book", str(MIXED), "--shock", "token=sUSDe:0.08", "--exit-cost", "0.11"]
    assert cli.main([*args, "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / "book-incident.json").read_text())
    (hit,) = [ln for ln in r["lines"] if ln["hit_markets"]]
    assert hit["name"].startswith("PT-sUSDe loop") and hit["verdict"] == "EXIT"
    assert hit["exit_cost_usd"] == pytest.approx(110_000) and 700_000 < hit["loss_usd"] < 850_000
    assert r["shocks"] == ["sUSDe −8%"] and "in 1 pocket(s)" in r["headline"]
    with pytest.raises(ValueError):
        VB.parse({"vaults": [{"kind": "borrow", "market": "0x12"}]})


THREE = ROOT / "examples" / "brief-three-shapes.json"


def test_a_pt_pocket_needs_its_pendle_market_and_amount():
    """D222: a PT held without a borrow."""
    ok = VB.parse({"weighting": "pocket", "vaults": [{"kind": "pt", "market": "0x" + "ab" * 20, "amount": 5}]})
    assert ok.vaults[0].kind == "pt" and ok.vaults[0].amount == 5
    for bad in ({"kind": "pt", "market": "0x12", "amount": 5}, {"kind": "pt", "market": "0x" + "ab" * 20}):
        with pytest.raises(ValueError):
            VB.parse({"weighting": "pocket", "vaults": [bad]})


def test_the_three_shapes_under_one_shock(tmp_path):
    """sUSDe −8 % with an 11 % unwind: the loop loses 78 % of its pocket and exits; the same PT held without a borrow
    loses 8 %, less than the cost of leaving, and stays."""
    args = ["analyze", "--book", str(THREE), "--shock", "token=sUSDe:0.08", "--exit-cost", "0.11"]
    assert cli.main([*args, "--out", str(tmp_path)]) == 0
    lines = {ln["name"]: ln for ln in json.loads((tmp_path / "book-incident.json").read_text())["lines"]}
    loop, held = lines["PT-sUSDe loop on Morpho (the brief's example)"], lines["PT-sUSDe held, no borrow"]
    assert loop["verdict"] == "EXIT" and loop["loss_usd"] == pytest.approx(776_708, rel=1e-3)
    assert held["verdict"] == "STAY" and held["loss_usd"] == pytest.approx(80_000, rel=1e-3)
