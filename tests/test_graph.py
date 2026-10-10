"""The dependency graph's structure and HTML output (no network)."""

import json

from riskdep.graph import Graph, to_html, write


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
    hp, jp = write(g, tmp_path / "g.html", "T", "S")
    assert json.loads(jp.read_text())["edges"][0]["amount"] == 1000.0
