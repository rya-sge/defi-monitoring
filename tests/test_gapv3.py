"""GAPV3 (plan 2026-10-11-gapv3, D253–D258): the Upshift vault behind etrUSD, a loan-asset depeg, the exposure on
venues not read, ETH+ and EURØP in the registry, and the book of every RockawayX vault on Ethereum."""

import json
from pathlib import Path

import pytest

from riskdep import cli, pipeline, vault_book, vault_incident
from riskdep import upshift as UP
from riskdep.discover import REGISTRY

ROOT = Path(__file__).resolve().parent.parent
TORI = "0x3BD9AdAE6643dDcddD02746b8B60075E56DF9478"
EUROP = "0x9C57E02bC31e7e463f439353D97bd8f42F5a7F9c"


def test_the_tori_vault_reports_its_nav_through_a_daily_cap():
    s = pipeline.block_snapshot("upshift")
    assert s.external / s.total > 0.99 and s.cap_bps_day == 5 and s.lag_s == 7 * 86400 and s.instant_fee == 0.05
    assert s.queued / s.supply == pytest.approx(0.36, abs=0.02) and s.timelock_s == 86400
    assert {h.label for h in s.holders} == {"a Safe 4/6", "an EOA (one key)"}
    assert UP.days_to_report(s, 0.10) == pytest.approx(222, abs=1)  # 1 / 0.9 − 1 = 11.1 %, at 0.05 % a day
    with pytest.raises(ValueError):
        UP.parse(["upshift=2"])


def test_an_upshift_loss_reaches_the_etrusd_market(tmp_path, capsys):
    assert cli.main(["analyze", "--vault", TORI, "--shock", "upshift=0.10", "--out", str(tmp_path)]) == 0
    inc = json.loads((tmp_path / f"vault-incident-{TORI.lower()}.json").read_text())
    h = next(h for h in inc["hits"] if h["label"].startswith("etrUSD/USDC"))
    assert h["drop"] == pytest.approx(0.10, abs=1e-3)
    assert "over 222 days" in capsys.readouterr().out


def test_the_exposure_on_venues_not_read():
    loss, words = vault_book.offchain([("token", "pst", 0.2, 0)])
    assert loss == pytest.approx(0.2 * 42.5e6) and "lends against PST" in words[0]
    assert vault_book.offchain([("token", "fxsave", 0.2, 0)]) == (0.0, [])


def test_registry_entries():
    assert REGISTRY["issuers"]["0xe72b141df173b999ae7c1adcbf60cc9833ce56a8"]["symbol"] == "ETH+"
    assert REGISTRY["stables"]["0x888883b5f5d21fb10dfeb70e8f9722b9fb0e5e51"]["symbol"] == "EURØP"
    book = vault_book.load(ROOT / "examples" / "rockawayx-ethereum-all.json")
    assert len(book.vaults) == 12 and EUROP.lower() in [v.address for v in book.vaults]


def test_a_loan_asset_depeg_is_the_depositors_own_loss(tmp_path):
    assert vault_incident.parse_shocks(["loan=EURØP:0.1"]) == [("loan", "europ", 0.1, 0)]
    assert cli.main(["analyze", "--vault", EUROP, "--shock", "loan=EURØP:0.1", "--out", str(tmp_path)]) == 0
    inc = json.loads((tmp_path / f"vault-incident-{EUROP.lower()}.json").read_text())
    assert not inc["hits"] and inc["vault_loss"] == pytest.approx(0.1 * inc["vault_total"], rel=1e-6)
    assert inc["loss_if_stay"] > inc["loss_if_exit_first"] and inc["verdict"] == "EXIT"
