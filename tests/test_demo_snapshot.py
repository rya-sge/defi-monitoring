"""End to end on the cached real snapshot: no network."""

from pathlib import Path

import pytest

from riskdep import cli, discover, pipeline, priors, simulate
from riskdep import sources as S

SNAP = Path(__file__).resolve().parent.parent / "fixtures" / "snapshot"


@pytest.fixture(scope="module")
def demo():
    f = S.Fetcher("offline", SNAP)
    return f, discover.discover_morpho_position(f, pipeline.DEMO_MARKET, pipeline.DEMO_USER)


def test_discovery_finds_every_layer(demo):
    f, p = demo
    kinds = {a["kind"] for _, a in p.graph.nodes(data=True)}
    assert {"chain", "issuer", "asset", "amm", "oracle", "lending", "stable"} <= kinds
    assert all(a.get("source") for _, a in p.graph.nodes(data=True))
    assert f.network_calls == 0


def test_attribution_adds_up(demo):
    f, p = demo
    prs = priors.layer_priors(f, p)
    s = simulate.run(p, prs, 30, n=20000)
    assert s.expected_loss_usd > 0
    assert abs(s.interaction_usd) < 0.25 * s.expected_loss_usd


def test_cli_offline_writes_report(tmp_path):
    assert cli.main(["analyze", "--demo", "--out", str(tmp_path), "--paths", "4000"]) == 0
    html = (tmp_path / "report.html").read_text()
    assert "Dependency stack" in html and ("STAY" in html or "REDUCE" in html or "EXIT" in html)
    assert (tmp_path / "report.json").exists()


def test_offline_miss_is_reported(tmp_path):
    f = S.Fetcher("offline", tmp_path)
    with pytest.raises(S.CacheMiss):
        discover.discover_morpho_position(f, pipeline.DEMO_MARKET, pipeline.DEMO_USER)


def test_demo_compares_holding_to_maturity(tmp_path):
    """D196 (K12): the demo's PT matures in 47 days, beyond the 30-day horizon: the verdict states the hold-to-maturity
    path (the PT redeems at par) against leaving now."""
    import json

    assert cli.main(["analyze", "--demo", "--out", str(tmp_path), "--paths", "4000"]) == 0
    reasons = json.loads((tmp_path / "report.json").read_text())["decision"]["reasons"]
    assert any(r.startswith("Held to maturity (47 days)") and "cheaper path" in r for r in reasons)
