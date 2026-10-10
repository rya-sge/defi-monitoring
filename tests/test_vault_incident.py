"""Incident mode for a vault depositor (plan 2026-10-11-vault-incident): parsing, the pure parts, the Belem vault."""

import json

import pytest

from riskdep import cli, scenario
from riskdep import exit_queue as EQ
from riskdep import oracle_class as OC
from riskdep import vault_incident as VI
from riskdep.market_risk import MarketInfo

BELEM = "0xd6d4b804014ef27836dbe9f8f6bf6c71251548ec"
M = 10**18


def test_parse_token_shocks():
    assert VI.parse_token_shocks(["token=mGLOeuro:0.30", "token=0xABC:0.2"]) == [("mgloeuro", 0.3), ("0xabc", 0.2)]
    for bad in ("mGLOeuro:0.3", "token=mGLOeuro", "token=:0.3", "token=x:0", "token=x:1.5", "oracle=0.1"):
        with pytest.raises(ValueError):
            VI.parse_token_shocks([bad])


def test_nav_timing():
    assert "publishes" in VI.nav_timing(scenario.OracleProfile(OC.CONSTANT_PRICE, "nav"))
    assert "TWAP 900" in VI.nav_timing(scenario.OracleProfile(OC.PRICE_TRACKING, "t", twap_s=900))
    assert VI.nav_timing(None).startswith("unknown")


def test_market_hit_at_the_shocked_price():
    info = MarketInfo("m", 0.77, 18, "EURCV", "X/EURCV")
    price = 10**36  # one collateral unit = one loan unit, both 18 decimals
    pos = {"a": (100 * M, 70 * 10**6 * 10**12)}  # 100 collateral, borrow shares worth 70
    totals = (70 * M, 70 * 10**6 * 10**12 + 10**6)
    calm = VI.market_hit("m", info, pos, totals, price, 0.05, 1.0, None)
    assert calm.liquidatable_debt == 0 and calm.bad_debt == 0  # 95 × 0.77 = 73.2 > 70
    hit = VI.market_hit("m", info, pos, totals, price, 0.40, 0.5, None)
    lif = 1 / (0.3 * 0.77 + 0.7)
    assert hit.liquidatable_debt == pytest.approx(70, rel=1e-3)
    assert hit.bad_debt == pytest.approx(70 - 60 / lif, rel=1e-3)
    assert hit.vault_loss == pytest.approx(hit.bad_debt / 2)


def test_decide_exit_only_when_leaving_saves_enough():
    small = EQ.Liquidity(total=100 * M, position=10 * M, plain=20 * M, forced=0, penalty=0.0)
    v, why = VI.decide(small, 50 * M, 60 * M, M)[4:]
    assert v == "EXIT" and "withdraw" in why  # all 10 can leave at par: the loss falls from 5 to 0
    big = EQ.Liquidity(total=100 * M, position=99 * M, plain=20 * M, forced=0, penalty=0.0)
    assert VI.decide(big, 50 * M, 60 * M, M)[4] == "STAY"  # the loss falls on it either way
    assert VI.decide(small, 0, 0, M)[4] == "STAY"


@pytest.mark.parametrize("cut,bad_low,bad_high", [(0.10, 0, 0), (0.30, 240_000, 260_000), (0.50, 1_200_000, 1_260_000)])
def test_belem_nav_cut(tmp_path, capsys, cut, bad_low, bad_high):
    assert cli.main(["analyze", "--vault", BELEM, "--shock", f"token=mGLOeuro:{cut}", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    inc = json.loads((tmp_path / f"vault-incident-{BELEM}.json").read_text())
    (hit,) = inc["hits"]
    assert hit["oracle_class"] == OC.CONSTANT_PRICE and "publishes" in hit["timing"]
    assert bad_low <= hit["bad_debt"] <= bad_high and hit["vault_share"] == pytest.approx(1.0, abs=0.01)
    assert inc["verdict"] == "STAY" and "INCIDENT" in out  # a 99.46 % depositor loses about the same either way


def test_vault_mode_needs_a_token_shock(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["analyze", "--vault", BELEM, "--out", str(tmp_path)])
    with pytest.raises(SystemExit):
        cli.main(["analyze", "--vault", BELEM, "--shock", "oracle=0.1", "--out", str(tmp_path)])
