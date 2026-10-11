"""GAP C6 (plan 2026-10-11-bridges, D250–D252): PST's CCIP lanes and etrUSD's LayerZero peers, read on-chain; a forged
mint bounded by the rate limits; the drain it opens in the markets that take the token."""

import json

import pytest

from riskdep import bridge as BR
from riskdep import cli, pipeline, vault_incident

HUMA = "0x8aC91877b93330f52b2979a31a4879506021475c"
TORI = "0x3BD9AdAE6643dDcddD02746b8B60075E56DF9478"


def route(*lanes):
    return BR.Route("X", "ccip", "0x0", 100.0, list(lanes))


def test_a_mint_is_bounded_by_the_open_lanes():
    a = BR.Lane("p", "1.6", "Solana", True, True, 10.0, 10.0, 1.0)
    shut = BR.Lane("p", "1.6", "Base", False, True, 50.0, 50.0, 5.0)
    assert BR.minted(route(a, shut), 1) == 10.0 + 3600.0  # what the bucket holds, then its refill; a closed lane adds 0
    assert BR.minted(route(a, BR.Lane("q", "2.0", "Base", True)), 1) is None  # no rate limit: unbounded
    m = BR.markdown(route(BR.Lane("p", "1.6", "Solana", True, True, 100.0, 100.0, 0.0)), 1)
    assert m["minted"] == 100.0 and m["markdown"] == pytest.approx(0.5)  # 100 more against 100: half
    assert BR.markdown(route(shut), 1)["markdown"] == 0.0


def test_parse():
    rest, found = BR.parse(["bridge=PST", "bridge=etrUSD:4", "token=PST:0.1"])
    assert rest == ["token=PST:0.1"] and found == [("PST", 1.0), ("etrUSD", 4.0)]
    with pytest.raises(ValueError):
        BR.parse(["bridge=USDC"])
    assert vault_incident.parse_shocks(["drain=PST:1e6:6"]) == [("drain", "pst", 1e6, 6)]
    with pytest.raises(ValueError):
        vault_incident.parse_shocks(["drain=PST"])


def test_recorded_lanes():
    r = pipeline.block_snapshot("bridge")
    pst, etr = r["PST"], r["etrUSD"]
    (lane,) = pst.open_lanes()  # the 1.6.1 pool lists no remote pool: only the 2.0.0 one accepts messages
    assert lane.chain == "Solana" and lane.capacity == pytest.approx(7.7e6) and lane.rate == pytest.approx(6112)
    assert {h.label for h in pst.holders} == {"a timelock (3 h)", "a Safe 4/5"}
    assert BR.minted(pst, 1) == pytest.approx(7.7e6 + 6112 * 3600)
    assert not etr.open_lanes() and etr.holders[0].label == "a Safe 4/6"


def test_a_forged_pst_mint_drains_the_pst_markets(tmp_path, capsys):
    assert cli.main(["analyze", "--vault", HUMA, "--shock", "bridge=PST", "--out", str(tmp_path)]) == 0
    inc = json.loads((tmp_path / f"vault-incident-{HUMA.lower()}.json").read_text())
    hits = [h for h in inc["hits"] if h["event"] == "drain"]
    assert hits and inc["vault_loss"] > 0
    assert all(h["bad_debt"] > 0 and h["vault_loss"] == pytest.approx(h["bad_debt"] * h["vault_share"]) for h in hits)
    assert "29.7M unbacked PST" in capsys.readouterr().out


def test_no_lane_open_reaches_no_market(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["analyze", "--vault", TORI, "--shock", "bridge=etrUSD", "--out", str(tmp_path)])
