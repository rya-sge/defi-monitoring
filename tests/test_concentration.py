"""Shared feeds and supply concentration (plan 2026-10-11-shared-and-supply, D215–D217)."""

import json

import pytest

from riskdep import cli
from riskdep import graph as GR

BELEM = "0xd6d4b804014ef27836dbe9f8f6bf6c71251548ec"


def test_a_feed_read_by_two_markets_is_shared():
    g = GR.Graph()
    for m in ("m1", "m2"):
        g.node(m, "Pool", m)
    g.node("m2", "Pool", "m2", sibling=True)
    for o in ("o1", "o2", "feed"):
        g.node(o, "Oracle", o)
    g.edge("m1", "o1", "priced by")
    g.edge("m2", "o2", "priced by")
    g.edge("o1", "feed", "reads")
    g.edge("o2", "feed", "reads")
    assert GR.annotate_shared(g) == 1
    d = g.nodes["feed"]["details"]
    assert d["markets_reading"] == 2 and d["shared"] and "1 held, 1 sibling" in d["shared_text"]
    assert not g.nodes["o1"]["details"]["shared"]


def test_belem_graph_shares_and_supply(tmp_path, capsys):
    """mGLOeuro: 88.8 % of its supply posted in the Belem market; EUR/USD read by 5 markets, 3 of them the vault's."""
    assert cli.main(["graph", "--vault", BELEM, "--replay", "--out", str(tmp_path / "g")]) == 0
    out = capsys.readouterr().out
    assert "collateral supply: 12 token(s)" in out
    nodes = json.loads((tmp_path / "g.json").read_text())["nodes"]
    mglo = next(n for n in nodes if n["label"] == "mGLOeuro")["details"]
    assert mglo["share_in_morpho"] == pytest.approx(0.888, abs=1e-3)
    eur = next(n for n in nodes if n["label"] == "EUR / USD")["details"]
    assert eur["markets_reading"] == 5 and "3 held" in eur["shared_text"]


def test_the_pt_position_against_its_market_and_pool(tmp_path):
    """The demo position is half its market; the market holds 8.2× the PT of its Pendle pool."""
    assert cli.main(["analyze", "--demo", "--out", str(tmp_path)]) == 0
    d = json.loads((tmp_path / "report.json").read_text())["discovery"]
    share = " ".join(d["position_share"])
    assert "50% of its market's collateral" in share and "8.2× the PT in its Pendle pool" in share
    assert any("PT-sUSDE-26NOV2026: 34.8%" in s for s in d["supply"])
