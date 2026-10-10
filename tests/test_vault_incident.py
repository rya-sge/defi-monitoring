"""Incident mode for a vault depositor (plan 2026-10-11-vault-incident): parsing, the pure parts, the Belem vault."""

import json
from pathlib import Path

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


# --- wrapped collateral (D126, D127)


def test_match_token_direct_and_through_wrappers():
    sym = {"0xpt": "PT-trUSD", "0xstr": "strUSD", "0xtr": "trUSD"}
    assert VI.match_token("0xpt", ["0xstr", "0xtr"], sym, "0xpt") == ("", "PT-trUSD")
    assert VI.match_token("0xpt", ["0xstr", "0xtr"], sym, "trusd") == ("PT-trUSD → strUSD → trUSD", "trUSD")
    assert VI.match_token("0xpt", ["0xstr", "0xtr"], sym, "usdc") is None


def test_unseen_wrapped_markdown_is_a_hidden_shortfall():
    info = MarketInfo("m", 0.86, 18, "USDC", "X/USDC")
    price = 10**36
    pos = {"a": (100 * M, 80 * 10**6 * 10**12)}  # 100 collateral, debt 80
    totals = (80 * M, 80 * 10**6 * 10**12 + 10**6)
    nav = scenario.OracleProfile(OC.CONSTANT_PRICE, "nav")
    hidden = VI.market_hit("m", info, pos, totals, price, 0.30, 1.0, nav, via="X → Y")
    assert not hidden.seen and hidden.liquidatable_debt == 0
    assert hidden.bad_debt == pytest.approx(10, rel=1e-3)  # 80 − 100 × 0.7
    market = scenario.OracleProfile(OC.PRICE_TRACKING, "feed")
    seen = VI.market_hit("m", info, pos, totals, price, 0.30, 1.0, market, via="X → Y")
    assert seen.seen and seen.liquidatable_debt > 0  # a market oracle follows the markdown


def test_book_reaches_wrapped_trusd_offline(tmp_path):
    book = str(Path(__file__).resolve().parent.parent / "examples" / "rockawayx-ethereum.json")
    assert cli.main(["analyze", "--book", book, "--shock", "token=trUSD:0.30", "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / "book-incident.json").read_text())
    hit = {ln["name"] for ln in r["lines"] if ln["hit_markets"]}
    assert hit == {"RockawayX Tori Ecosystem", "RockawayX USDC Yield"} and r["loss_usd"] > 1_000_000
    assert cli.main(["analyze", "--book", book, "--shock", "token=USDC:0.30", "--out", str(tmp_path)]) == 0
    assert json.loads((tmp_path / "book-incident.json").read_text())["loss_usd"] == 0  # a loan asset ends a chain


def test_parse_shocks_both_kinds():
    assert VI.parse_shocks(["token=PST:0.3", "borrower=mGLOeuro:0.5", "borrower=all:0:3"]) == [
        ("token", "pst", 0.3, 0),
        ("borrower", "mgloeuro", 0.5, 1),
        ("borrower", "all", 0.0, 3),
    ]
    for bad in ("borrower=x", "borrower=:0.5", "borrower=x:1.5", "borrower=x:0.5:0", "borrower=x:a", "user=x:0.5"):
        with pytest.raises(ValueError):
            VI.parse_shocks([bad])
    assert VI.describe(("borrower", "all", 0.5, 2)) == (
        "the 2 largest borrowers of every market default, collateral recovered at 50%"
    )
    assert VI.describe(("pst", 0.3), {"pst": "PST"}) == "PST −30%"


def test_borrower_default_takes_the_largest():
    price = 10**36
    pos = {"a": (100 * M, 80 * M * 10**6), "b": (50 * M, 10 * M * 10**6)}  # debts 80 and 10
    totals = (90 * M, 90 * M * 10**6)
    debt, bad, who = VI.borrower_default(pos, totals, price, 0.5, 1)
    assert who == ["a"] and debt == pytest.approx(80 * M, rel=1e-9) and bad == pytest.approx(30 * M, rel=1e-9)
    _, bad2, who2 = VI.borrower_default(pos, totals, price, 0.0, 5)
    assert set(who2) == {"a", "b"} and bad2 == pytest.approx(90 * M, rel=1e-9)  # nothing recovered


def test_belem_borrower_default_offline(tmp_path, capsys):
    """mGLOeuro/EURCV is owed by one borrower: its default at 50 % recovery costs about a fifth of the vault."""
    args = ["analyze", "--vault", BELEM, "--shock", "borrower=mGLOeuro:0.5", "--out", str(tmp_path)]
    assert cli.main(args) == 0
    r = json.loads((tmp_path / f"vault-incident-{BELEM}.json").read_text())
    (h,) = r["hits"]
    assert h["event"] == "default" and len(h["defaulters"]) == 1 and h["top1_share"] > 0.99
    assert 1.0e6 < r["vault_loss"] < 1.1e6 and h["exit_route"] == "none"
    out = capsys.readouterr().out
    assert "the largest borrower of mGLOeuro defaults" in out and "no due date" in out
    both = ["analyze", "--vault", BELEM, "--shock", "token=mGLOeuro:0.3", "--shock", "borrower=mGLOeuro:0.5"]
    assert cli.main([*both, "--out", str(tmp_path)]) == 0
    r2 = json.loads((tmp_path / f"vault-incident-{BELEM}.json").read_text())
    assert r2["vault_loss"] > r["vault_loss"]  # the default is valued at the marked-down price, once


def test_no_liquidator_branch_on_thin_exit_liquidity(tmp_path):
    fx = "0x2ca22cb25558fa2018ecb1ce4ed8af92ee7ea423"
    assert cli.main(["analyze", "--vault", fx, "--shock", "token=fxSAVE:0.3", "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / f"vault-incident-{fx}.json").read_text())
    h = next(h for h in r["hits"] if not h["via"])
    assert h["exit_route"] == "thin" and h["liquidatable_debt"] > 0
    assert 0 < h["no_liquidator_shortfall"] < h["vault_loss"]  # no liquidation incentive paid, but liquidity locked
