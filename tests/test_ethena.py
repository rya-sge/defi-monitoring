"""Ethena's backing venues (plan 2026-10-11-venues, D218–D221)."""

import json

import pytest

from riskdep import cli, pipeline
from riskdep import ethena as ET
from riskdep import graph as GR

SNAP = ET.Snapshot(0, 1000.0, {"Unallocated": 800.0, "Binance": 150.0, "OKX": 50.0}, {}, 10.0, 5.0, 4.8)


def test_venue_loss_after_the_reserve_fund():
    x = ET.venue_loss(SNAP, "binance", 0.4)  # 60 lost, 10 absorbed: 50 of 1000
    assert x["venue"] == "Binance" and x["lost_usd"] == 60 and x["absorbed_usd"] == 10
    assert x["markdown"] == pytest.approx(0.05)
    assert ET.venue_loss(SNAP, "OKX", 0.1)["markdown"] == 0  # 5 lost, within the reserve fund
    with pytest.raises(ValueError):
        ET.venue_loss(SNAP, "FTX", 0.5)


def test_parse_venue():
    assert ET.parse_venue(["oracle=0.1", "venue=Binance:0.5"]) == (["oracle=0.1"], [("Binance", 0.5)])
    for bad in ("venue=Binance", "venue=:0.5", "venue=Binance:2"):
        with pytest.raises(ValueError):
            ET.parse_venue([bad])


def test_the_recorded_backing():
    snap = pipeline.ethena_snapshot("offline")
    assert snap.total_usd == pytest.approx(4.769e9, rel=1e-3) and snap.share("Binance") == pytest.approx(
        0.134, abs=1e-3
    )
    assert snap.reserve_usd == pytest.approx(62.08e6, rel=1e-3)


def test_a_binance_failure_reaches_the_briefs_position(tmp_path, capsys):
    """Half the margin at Binance lost: 319M, 62M absorbed, USDe marked down 5.39 %: the PT loop is liquidated once
    the meta-oracle switches, and the verdict is EXIT."""
    assert cli.main(["analyze", "--demo", "--shock", "venue=Binance:0.5", "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / "report.json").read_text())
    inc = r["incident"]
    assert inc["shocks"]["issuer_depeg"] == pytest.approx(0.0539, abs=1e-4) and inc["verdict"] == "EXIT"
    assert inc["after_switch"]["liquidated"]
    assert any("Binance 13.4%" in s for s in r["discovery"]["venues"])
    assert "the reserve fund absorbs 62.1M" in capsys.readouterr().out


def test_venues_in_the_graph():
    g, *_ = GR.load([], [], True, "replay", pipeline.REPLAY_DIR / "graph-0xdf81987465681d0515058fe0a47a3bd174012730")
    assert GR.annotate_ethena(g, pipeline.ethena_snapshot("offline")) == 6
    assert g.nodes["venue:binance"]["details"]["share_of_backing"] == pytest.approx(0.134, abs=1e-3)
