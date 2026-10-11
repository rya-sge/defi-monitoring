"""Discovery depth for the brief's PT position (plan 2026-10-11-depth): the pure layers, and the demo report."""

import json
from types import SimpleNamespace

from riskdep import cli, scenario
from riskdep import depth as DP

M = "0x" + "11" * 32
SIB = "0x" + "22" * 32
OTHER = "0x" + "33" * 32
COLL, UND = "0xc0", "0xu0"

GRAPH = {
    "nodes": [
        {"id": M, "kind": "Pool", "label": "Blue PT-X/USDC", "details": {"market_id": M}},
        {"id": "0xo", "kind": "Oracle", "label": "Oracle", "details": {"oracle_class": "price-tracking"}},
        {
            "id": "0xf",
            "kind": "Oracle",
            "label": "X / USD",
            "details": {"oracle_class": "price-tracking", "freshness": "updated 1.0 h ago", "stale": False},
        },
        {
            "id": SIB,
            "kind": "Pool",
            "label": "Blue X/DAI",
            "details": {
                "market_id": SIB,
                "sibling": True,
                "linked_by": "same collateral with PT-X/USDC",
                "total_borrow": "5",
                "loan_unit": "DAI",
                "liquidation_curve": [
                    {"oracle_fall": 0.05, "liquidatable_debt": 1.0, "bad_debt": 0.0},
                    {"oracle_fall": 0.1, "liquidatable_debt": 3.0, "bad_debt": 0.5},
                ],
            },
        },
        {
            "id": OTHER,
            "kind": "Pool",
            "label": "Blue Y/DAI",
            "details": {"market_id": OTHER, "sibling": True, "linked_by": "same collateral with Z/USDC"},
        },
        {"id": UND, "kind": "Asset", "label": "X", "details": {"pharos_grade": "C 55"}},
        {"id": "pharos:y", "kind": "External", "label": "Y", "details": {}},
        {
            "id": "protocol:p",
            "kind": "External",
            "label": "Pendle V2",
            "details": {"concentration": "Pendle V2: …", "concentrated": True},
        },
    ],
    "edges": [
        {"source": M, "target": "0xo", "rel": "priced by", "details": {}},
        {"source": "0xo", "target": "0xf", "rel": "reads", "details": {"role": "BASE_FEED_1"}},
        {"source": UND, "target": "pharos:y", "rel": "backed by (Pharos)", "details": {"share": 1.0}},
        {"source": COLL, "target": "protocol:p", "rel": "issued by", "details": {}},
    ],
}


def test_position_depth_reads_the_graph():
    d = DP.position_depth(GRAPH, M, [COLL, UND], [{"text": "x"}])
    assert [f["label"] for f in d["feeds"]] == ["X / USD"] and d["feeds"][0]["role"] == "BASE_FEED_1"
    (s,) = d["siblings"]  # Y/DAI is a sibling of another market: not listed
    assert s["label"] == "X/DAI" and s["liquidatable_at_fall"] == 3.0 and s["bad_debt_at_fall"] == 0.5
    assert d["grades"] == {"X": "C 55"} and d["backing"][0]["backed_by"] == "Y"
    assert d["protocols"]["Pendle V2"]["concentrated"]
    assert DP.position_depth(GRAPH, "0x" + "99" * 32, [], None) == {}
    text = " ".join(DP.lines(d))
    assert "X/DAI 3 DAI liquidatable" in text and "issuer grade (Pharos): X C 55" in text


def test_admin_rows_and_the_meta_oracle_text():
    c = SimpleNamespace(
        address="0xa",
        roles=["feed of the oracle of PT-X/USDC"],
        upgradeable=True,
        admin="0x" + "b" * 40,
        owner=None,
        symbol="X / USD",
    )
    lock = SimpleNamespace(timelock_delay=172_800)
    (row,) = DP.admin_rows({"0xa": c}, lambda a: lock)
    assert row["timelock_h"] == 48 and "through a 48 h timelock" in row["text"]
    p = scenario.OracleProfile(
        "meta-oracle",
        "",
        timelock_s=57_600,
        deviation_threshold=0.0075,
        on_primary=True,
        live=scenario.OracleProfile("constant-price", ""),
        other=scenario.OracleProfile("price-tracking", ""),
    )
    assert DP.profile_text(p).startswith("a meta-oracle reading its primary source (constant-price)")
    assert "after 16 h, to the other (price-tracking)" in DP.profile_text(p)


def test_the_demo_report_carries_the_extra_layers(tmp_path):
    """The brief's PT loop: the meta-oracle and its switch, who can change its tokens, three sibling markets on sUSDe,
    sUSDe's grade and backing, and the protocols' concentration."""
    assert cli.main(["analyze", "--demo", "--out", str(tmp_path), "--paths", "2000"]) == 0
    d = json.loads((tmp_path / "report.json").read_text())["discovery"]
    assert d["oracle_profile"].startswith("a meta-oracle") and "16 h" in d["oracle_profile"]
    assert [s["label"] for s in d["siblings"]][0] == "sUSDe/PYUSD" and len(d["siblings"]) == 3
    assert d["grades"]["sUSDe"] == "C 55" and d["backing"][0]["backed_by"] == "USDe"
    assert d["protocols"]["Ethena USDe"]["concentrated"] and d["protocols"]["Pendle V2"]["concentrated"]
    assert any("24 h timelock" in a["text"] for a in d["admin"])
    assert "Discovery depth" in (tmp_path / "report.html").read_text()
