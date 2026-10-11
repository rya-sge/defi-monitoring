"""Feed quality and TVL concentration (plan 2026-10-11-feed-quality): the pure rules, and both on the recordings."""

import json

import pytest

from riskdep import cli, pipeline
from riskdep import feeds as FD
from riskdep import tvl as TV
from riskdep.graph import annotate_tvl, load

BELEM = "0xd6d4b804014ef27836dbe9f8f6bf6c71251548ec"
YIELD = "0xe0181090c22579b6a217f1522cbf8c9f1f0c1965"
H = 3600


def test_freshness_against_its_own_rhythm():
    hourly = [i * H for i in range(10)]  # ten rounds, one an hour
    fresh = FD.freshness(9 * H, hourly, 10 * H)
    assert fresh.cadence_h == pytest.approx(1) and not fresh.stale and "usually every 1.0 h" in fresh.text
    assert FD.freshness(9 * H, hourly, 9 * H + 26 * H).stale  # 26 h: past 3 × 1 h and the 25 h floor
    assert not FD.freshness(9 * H, hourly, 9 * H + 20 * H).stale  # within the floor
    few = FD.freshness(H, [0, H], H + 8 * 24 * H)  # two rounds: no rhythm, the 7-day limit applies
    assert few.cadence_h is None and few.stale and "too few" in few.text
    assert FD.freshness(None, [], 0) is None


def test_recorded_belem_graph_flags_the_midas_nav_feed():
    """ROCK-VAULT-DEP.md: mGLOeuro's NAV feed was 17.5 days old on 2026-10-11."""
    g = pipeline.vault_graph(BELEM)
    by = {n["label"]: n["details"] for n in g["nodes"] if n["details"].get("freshness")}
    assert by["mGLOeuro/EUR"]["stale"] and "17.5 days" in by["mGLOeuro/EUR"]["freshness"]
    assert not by["WBTC / BTC"]["stale"]


def test_vault_incident_shows_the_stale_feed(tmp_path):
    assert cli.main(["analyze", "--vault", BELEM, "--shock", "token=mGLOeuro:0.30", "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / f"vault-incident-{BELEM}.json").read_text())
    (h,) = r["hits"]
    assert h["stale_feed"] and any("STALE" in x for x in h["feeds"])
    assert any("feed is stale" in n for n in r["notes"])


PROTOCOLS = [
    {"slug": "a", "name": "A", "category": "Lending", "tvl": 30e9},
    {"slug": "b", "name": "B", "category": "Lending", "tvl": 10e9},
    {"slug": "c", "name": "C", "category": "Niche", "tvl": 1e8},
    {"slug": "d", "name": "D", "category": "Other", "tvl": 960e9},
]


def test_concentration_of_defi_and_of_a_category():
    a, b, c = (TV.concentration(PROTOCOLS, s) for s in "abc")
    assert a.share_defi == pytest.approx(0.03, rel=1e-3) and a.rank == 1 and a.concentrated  # 3 % of DeFi
    assert b.share_category == pytest.approx(0.25) and b.rank == 2 and b.concentrated  # a quarter of a 40B category
    assert c.share_category == 1 and not c.concentrated  # all of a 100M category: not systemic
    assert TV.concentration(PROTOCOLS, "zz") is None


def test_recorded_graph_carries_protocol_concentration():
    rdir = cli.REPLAY_DIR / f"graph-{YIELD}"
    g, *_ = load([], [], True, "replay", rdir)
    assert annotate_tvl(g, pipeline.llama_protocols("offline")) >= 5
    prot = {n["label"]: n["details"] for n in g.nodes.values() if n["id"].startswith("protocol:")}
    assert prot["Pendle V2"]["concentrated"] and not prot["Tori Finance"]["concentrated"]
    assert 0.018 < prot["Morpho Blue"]["share_of_defi"] < 0.02
    runs_on = [e for e in g.edges if e["rel"] == "runs on" and e["target"] == "protocol:morpho-blue"]
    assert len(runs_on) >= 10  # every Blue market of the graph


def test_feedstale_in_the_watch_flags_the_midas_nav_feed():
    """D193: the watch's feed check on Belem's recorded graph block: the mGLOeuro NAV feed, 17.5 days old, is stale."""
    from types import SimpleNamespace

    from riskdep import sources as S
    from riskdep.admin import Contract

    rdir = cli.REPLAY_DIR / f"graph-{BELEM}"
    block = json.loads((rdir / "meta.json").read_text())["block"]
    feed = "0x8b7b1689396ef4468df1c0fab181d29b47089609"
    aw = SimpleNamespace(
        contracts={feed: Contract(feed, ["feed of the oracle of mGLOeuro/EURCV"], symbol="mGLOeuro/EUR")}
    )
    fw = FD.FeedWatch(S.Fetcher("offline", rdir), aw, block)
    (al,) = fw.startup(lambda _: None, block)
    assert al.event == "FeedStale" and "17.5 days" in al.title and al.level == "warn"
    assert fw.step(S.Fetcher("offline", rdir), block) == []  # already stale: no new alert
