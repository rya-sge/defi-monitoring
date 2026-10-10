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
