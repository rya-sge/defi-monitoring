"""GAPV2 G18 and G13 (plan 2026-10-11-issuer-stacks, D246–D249): infiniFi's loss waterfall and pending loss;
fxSAVE's NAV components."""

import json

import pytest

from riskdep import cli, pipeline
from riskdep import fx as FX
from riskdep import infinifi as IF

YIELD = "0xE0181090c22579B6A217f1522cbf8c9f1F0C1965"
FXV = "0x2cA22cb25558fa2018ecb1CE4eD8AF92Ee7ea423"
SNAP = IF.Snapshot(1, 100.0, 5.0, 20.0, 60.0, 100.0, 0.0)


def test_waterfall_in_the_order_of_handle_negative_yield():
    assert IF.waterfall(SNAP, 4.0)["buffer"] == 4.0  # the buffer covers it
    w = IF.waterfall(SNAP, 10.0)  # larger than the buffer: the buffer is skipped, liUSD takes it all
    assert w["buffer"] == 0 and w["locked"] == 10.0 and w["siusd_markdown"] == 0
    w = IF.waterfall(SNAP, 50.0)
    assert w["locked"] == 20.0 and w["staked"] == 30.0 and w["siusd_markdown"] == pytest.approx(0.5)
    w = IF.waterfall(SNAP, 90.0)
    assert w["staked"] == 60.0 and w["iusd"] == 10.0 and w["iusd_markdown"] == pytest.approx(0.1)


def test_a_pending_loss_warns_then_reaches_siusd():
    small = IF.Snapshot(1, 100.0, 5.0, 20.0, 60.0, 100.0, -10.0)
    big = IF.Snapshot(1, 100.0, 5.0, 20.0, 60.0, 100.0, -30.0)
    assert IF.pending_alert(SNAP, 1) is None
    assert IF.pending_alert(small, 1).level == "warn" and IF.pending_alert(big, 1).level == "critical"


def test_recorded_states():
    i, f = pipeline.block_snapshot("infinifi"), pipeline.block_snapshot("fx")
    assert i.locked == pytest.approx(15.17e6, rel=1e-2) and i.staked == pytest.approx(43.0e6, rel=1e-2)
    assert f.share("fxusd") == pytest.approx(0.97, abs=0.01) and f.share("aave") == pytest.approx(0.0, abs=1e-3)
    assert FX.markdown(f, "fxusd", 0.1)["markdown"] == pytest.approx(0.097, abs=1e-3)
    with pytest.raises(ValueError):
        FX.parse(["fx=curve:0.1"])


def test_an_infinifi_loss_reaches_the_siusd_market(tmp_path, capsys):
    """30 % of the backing: liUSD absorbs 15.2M, siUSD falls 5.54 %, and the siUSD/USDC market liquidates."""
    assert cli.main(["analyze", "--vault", YIELD, "--shock", "infinifi=0.30", "--out", str(tmp_path)]) == 0
    inc = json.loads((tmp_path / f"vault-incident-{YIELD.lower()}.json").read_text())
    h = next(h for h in inc["hits"] if h["label"].startswith("siUSD/USDC"))
    assert h["drop"] == pytest.approx(0.0554, abs=1e-3) and h["liquidatable_debt"] > 0
    assert "liUSD absorbs 15.2M" in capsys.readouterr().out


def test_an_fxusd_depeg_reaches_fxsave(tmp_path):
    assert cli.main(["analyze", "--vault", FXV, "--shock", "fx=fxusd:0.10", "--out", str(tmp_path)]) == 0
    inc = json.loads((tmp_path / f"vault-incident-{FXV.lower()}.json").read_text())
    h = next(h for h in inc["hits"] if h["label"].startswith("fxSAVE/USDC"))
    assert h["drop"] == pytest.approx(0.097, abs=1e-3)


def test_a_loss_liusd_absorbs_reaches_no_market(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["analyze", "--vault", YIELD, "--shock", "infinifi=0.05", "--out", str(tmp_path)])
