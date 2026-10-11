"""Sky's backing read on-chain (plan 2026-10-11-sky, D223–D226)."""

import json

import pytest

from riskdep import cli, pipeline
from riskdep import graph as GR
from riskdep import sky as SK

SNAP = SK.Snapshot(
    1,
    {"peg module": 500.0, "Spark": 400.0, "crypto vaults": 100.0},
    {},
    450.0,
    60.0,
    50.0,
    0.04,
    700.0,
    300.0,
    400.0,
    400.0,
)


def test_sources_by_collateral_type():
    assert SK.source_of("LITE-PSM-USDC-A") == "peg module" and SK.source_of("ALLOCATOR-SPARK-A") == "Spark"
    assert SK.source_of("RWA009-A") == "RWA vaults" and SK.source_of("ETH-C") == "crypto vaults"


def test_the_loss_waterfall():
    """10 of net surplus, then 100 of debt auctions (25 % of a 400 SKY value), then USDS holders."""
    x = SK.sky_loss(SNAP, "spark", 0.5)  # 200 lost
    assert (x["surplus_usd"], x["auctions_usd"]) == (10, 100) and x["markdown"] == pytest.approx(90 / 1000)
    assert SK.sky_loss(SNAP, "peg module", 0.1)["exposed_usd"] == 450  # the peg module's USDC, not its debt
    assert SK.sky_loss(SNAP, "crypto vaults", 0.5)["markdown"] == 0
    with pytest.raises(ValueError):
        SK.sky_loss(SNAP, "maker", 0.5)
    assert SK.parse_sky(["sky=spark:0.2", "token=PST:0.1"]) == (["token=PST:0.1"], [("spark", 0.2)])


def test_the_recorded_core():
    s = pipeline.sky_snapshot("offline")
    assert s.total == pytest.approx(11.69e9, rel=1e-2) and s.debt["peg module"] / s.total == pytest.approx(
        0.447, abs=1e-3
    )
    assert s.psm_usdc == pytest.approx(4.42e9, rel=1e-2) and s.net_surplus == pytest.approx(-51.7e6, rel=1e-2)


def test_a_spark_loss_reaches_the_spark_vault(tmp_path, capsys):
    """Spark's allocation loses 20 %: 722M, 450M from debt auctions, USDS and sUSDS −2.36 %: the Spark USDT vault's
    sUSDS/USDT market (LLTV 96.5 %) has 1.7M of debt liquidatable, no bad debt."""
    spark = "0xb0c424116172B55CbB6dD3136F5989F7959e5B91"
    assert cli.main(["analyze", "--vault", spark, "--shock", "sky=spark:0.2", "--out", str(tmp_path)]) == 0
    inc = json.loads((tmp_path / f"vault-incident-{spark.lower()}.json").read_text())
    (hit,) = [h for h in inc["hits"] if h["label"].startswith("sUSDS/USDT")]
    assert hit["drop"] == pytest.approx(0.0236, abs=2e-4) and hit["liquidatable_debt"] > 1.5e6 and hit["bad_debt"] == 0
    assert "from debt auctions (SKY minted)" in capsys.readouterr().out


def test_sky_in_the_graph():
    g, *_ = GR.load([], [], True, "replay", pipeline.REPLAY_DIR / "graph-0xdf81987465681d0515058fe0a47a3bd174012730")
    assert GR.annotate_sky(g, pipeline.sky_snapshot("offline")) == 8
    assert g.nodes["sky:spark"]["details"]["share_of_backing"] == pytest.approx(0.309, abs=1e-3)
