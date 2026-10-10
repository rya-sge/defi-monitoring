"""The dependency graph's structure and HTML output, and the recorded RockawayX graph (no network)."""

import json
from pathlib import Path

import pytest

from riskdep import sources as S
from riskdep.graph import Graph, build_all, to_html, write


def test_edges_are_unique_per_relation_and_updated():
    g = Graph()
    g.node("0xA", "Pool", "vault")
    g.node("0xB", "Pool", "market")
    g.edge("0xA", "0xB", "supplies", 1.0, "RLUSD")
    g.edge("0xa", "0xb", "supplies", 2.0, "RLUSD", share="10%")
    g.edge("0xA", "0xB", "priced by")
    assert len(g.edges) == 2
    assert g.edges[0]["amount"] == 2.0 and g.edges[0]["details"]["share"] == "10%"


def test_repeated_node_merges_details():
    g = Graph()
    g.node("0xA", "Asset", "USDC", issuer=None)
    g.node("0xa", "Asset", "USDC", issuer="Circle")
    assert len(g.nodes) == 1 and g.nodes["0xa"]["details"]["issuer"] == "Circle"


def test_html_embeds_the_graph(tmp_path):
    g = Graph()
    g.node("user:0x1", "Actor", "Address 0x1")
    g.node("0xm", "Pool", "Blue X/USDC")
    g.edge("user:0x1", "0xm", "borrows from", 1000.0, "USDC")
    page = to_html(g, "T", "S")
    assert "cytoscape@" not in page and "cytoscape/3.30.2/cytoscape.min.js" in page
    assert '"borrows from"' in page and "Actor" in page and "Position" not in page
    assert "node[sibling = 1]" in page  # sibling markets are drawn dashed
    assert 'join("\\n")' in page  # an escaped newline: a raw one inside a JS string breaks the whole page
    hp, jp = write(g, tmp_path / "g.html", "T", "S")
    assert json.loads(jp.read_text())["edges"][0]["amount"] == 1000.0


# --- sibling markets and oracle classes on the recorded RockawayX USDC Yield graph (plan 2026-10-10-sibling-markets)

ROCKAWAYX = (
    Path(__file__).resolve().parent.parent / "fixtures" / "replay" / "graph-0xe0181090c22579b6a217f1522cbf8c9f1f0c1965"
)
TERMINAL = {
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
    "0x8fffffd4afb6115b954bd326cbe7b4ba576818f6",  # USDC / USD
}


@pytest.fixture(scope="module")
def rockawayx():
    meta = json.loads((ROCKAWAYX / "meta.json").read_text())
    f = S.Fetcher("offline", ROCKAWAYX)
    return build_all(f, meta["block"], meta["users"], meta["vaults"], meta["siblings"])


def _markets(g):
    return {n["label"].removeprefix("Blue "): n for n in g.nodes.values() if "market_id" in n["details"]}


def test_held_markets_get_their_oracle_class(rockawayx):
    held = {k: n["details"]["oracle_class"] for k, n in _markets(rockawayx).items() if not n["details"].get("sibling")}
    assert held == {
        "PT-reUSD-10DEC2026/USDC": "price-tracking",  # min(Pendle TWAP, linear discount)
        "strUSD/USDC": "constant-price",  # RedStone fundamental
        "siUSD/USDC": "constant-price",  # vault rate × a feed pegged at 1.0
        "PRIME/USDC": "constant-price",  # exchange-rate feed that never falls
        "PT-strUSD-26NOV2026/USDC": "constant-price",  # linear discount × trUSD pegged at 1.0
        "etrUSD/USDC": "constant-price",  # RedStone fundamental
    }


def test_siblings_and_why(rockawayx):
    sib = {k: n["details"]["linked_by"] for k, n in _markets(rockawayx).items() if n["details"].get("sibling")}
    assert set(sib) == {
        "PRIME/PYUSD",
        "reUSD/USDC",
        "PT-reUSD-10DEC2026/USDT",
        "PRIME/AUSD",
        "siUSD/msUSD",
        "PT-trUSD-26NOV2026/USDC",
        "nvPRIME/USDC",
        "reUSD/USDT",
    }  # AUTO/USDC and PT-siUSD-7JAN2027/USDC were siblings at the former $100k borrow floor, below $1M of TVL
    assert "same collateral with PRIME/USDC" in sib["PRIME/PYUSD"] and "shared price input" in sib["PRIME/PYUSD"]
    assert sib["reUSD/USDC"] == "same underlying with PT-reUSD-10DEC2026/USDC (LLTV 91.5%)"
    assert "shared price input with PT-strUSD-26NOV2026/USDC" in sib["PT-trUSD-26NOV2026/USDC"]


def test_every_sibling_reaches_a_held_market_through_a_shared_node(rockawayx):
    g, markets = rockawayx, _markets(rockawayx)
    held = {n["id"] for n in markets.values() if not n["details"].get("sibling")}
    ids = {n["id"] for n in markets.values()}
    assert not [e for e in g.edges if e["source"] in ids and e["target"] in ids]  # no market → market edge (D80)
    adj = {}
    for e in g.edges:
        adj.setdefault(e["source"], set()).add(e["target"])
        adj.setdefault(e["target"], set()).add(e["source"])
    for n in markets.values():
        if not n["details"].get("sibling"):
            continue
        seen, frontier, reached = {n["id"]}, [n["id"]], False
        while frontier and not reached:
            nxt = []
            for x in frontier:
                for y in adj.get(x, ()):
                    if y in seen or y in TERMINAL:
                        continue
                    seen.add(y)
                    reached |= y in held
                    if y not in ids:
                        nxt.append(y)  # walk through assets, pools, oracles and feeds, never through another market
            frontier = nxt
        assert reached, n["label"]


def test_market_nodes_carry_what_the_engine_needs(rockawayx):
    m = _markets(rockawayx)
    for name, n in m.items():
        d = n["details"]
        assert [p["oracle_fall"] for p in d["liquidation_curve"]] == [0.02, 0.05, 0.1, 0.2, 0.3, 0.5], name
        assert d["total_borrow"] > 0 and d["collateral_of_borrowers"] > 0, name
    five = next(p for p in m["PT-reUSD-10DEC2026/USDC"]["details"]["liquidation_curve"] if p["oracle_fall"] == 0.05)
    assert five["liquidatable_debt"] > 30e6 and five["collateral_liquidatable"] > five["liquidatable_debt"]
    pt = m["PT-reUSD-10DEC2026/USDC"]["details"]
    edge = next(e for e in rockawayx.edges if e["rel"] == "takes as collateral" and e["source"] == pt["market_id"])
    assert edge["amount"] == pytest.approx(pt["collateral_of_borrowers"]) and edge["unit"] == "PT-reUSD-10DEC2026"


def test_wraps_edges_and_the_tvl_floor(rockawayx):
    g = rockawayx
    label = {nid: n["label"] for nid, n in g.nodes.items()}
    wraps = {(label[e["source"]], label[e["target"]]) for e in g.edges if e["rel"] == "wraps"}
    assert {("siUSD", "iUSD"), ("strUSD", "trUSD"), ("nvPRIME", "PRIME")} <= wraps
    # every loan token here is a dollar stablecoin, so the supply in loan units reads as TVL in USD (D79)
    assert all(n["details"]["total_supply"] >= 1e6 for n in _markets(g).values() if n["details"].get("sibling"))


# --- Belem RWA EURCV, the sponsor's vault curated by RockawayX (ROCK-VAULT.md), recorded 2026-10-11

BELEM = (
    Path(__file__).resolve().parent.parent / "fixtures" / "replay" / "graph-0xd6d4b804014ef27836dbe9f8f6bf6c71251548ec"
)


def test_belem_held_markets_and_the_midas_nav_feed():
    meta = json.loads((BELEM / "meta.json").read_text())
    g = build_all(S.Fetcher("offline", BELEM), meta["block"], meta["users"], meta["vaults"], meta["siblings"])
    held = {
        n["label"].removeprefix("Blue "): n["details"]["oracle_class"]
        for n in g.nodes.values()
        if "market_id" in n["details"] and not n["details"].get("sibling")  # siblings can share a held label
    }
    assert held == {
        "mGLOeuro/EURCV": "constant-price",  # Midas MGloEuroCustomAggregatorFeed: the issuer publishes the NAV
        "WBTC/EURCV": "price-tracking",
        "cbBTC/EURCV": "price-tracking",
        "wstETH/EURCV": "price-tracking",
        "steakEURCV/EURCV": "constant-price",  # ERC-4626 rate
        "oTFYe/EURCV": "constant-price",  # RedStone fundamental pegged at 1.0
    }
    nav = next(n for n in g.nodes.values() if n["label"] == "mGLOeuro/EUR")
    assert "CustomAggregator" in nav["details"]["class_basis"]
