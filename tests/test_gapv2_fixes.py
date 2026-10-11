"""GAPV2 G19, G11, G12, G1 (plan 2026-10-11-gapv2-fixes, D240–D243)."""

import json

import pytest

from riskdep import cli, pipeline
from riskdep import exposure as XP
from riskdep import graph as GR
from riskdep import oracle_class as OC
from riskdep import vault_incident as VI
from riskdep.vault import WAD

YIELD = "0xE0181090c22579B6A217f1522cbf8c9f1F0C1965"
FX = "0x2cA22cb25558fa2018ecb1CE4eD8AF92Ee7ea423"
BELEM = "0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec"


def _hit(out, vault, label):
    inc = json.loads((out / f"vault-incident-{vault.lower()}.json").read_text())
    return inc, next(h for h in inc["hits"] if h["label"].startswith(label))


def test_g19_a_markdown_reaches_an_oracle_that_applies_the_tokens_rate(tmp_path):
    """siUSD −30 %: its oracle converts through siUSD's ERC-4626 rate, so it reads the loss and liquidates."""
    g = pipeline.vault_graph(YIELD.lower())
    nodes = {n["id"]: n for n in g["nodes"]}
    sh = {(nodes[s.node]["kind"], s.mode) for s in VI.engine_shocks(g, [("token", "siusd", 0.3, 0)])}
    assert ("Oracle", "reads-low") in sh and ("Asset", "price") in sh
    assert cli.main(["analyze", "--vault", YIELD, "--shock", "token=siUSD:0.30", "--out", str(tmp_path)]) == 0
    _, h = _hit(tmp_path, YIELD, "siUSD/USDC")
    assert h["liquidatable_debt"] > 5e6 and "oracle × 0.700" in h["engine"]


def test_g11_the_midas_feed_floor_holds_the_markdown_back(tmp_path, capsys):
    assert cli.main(["analyze", "--vault", BELEM, "--shock", "token=mGLOeuro:0.30", "--out", str(tmp_path)]) == 0
    _, h = _hit(tmp_path, BELEM, "mGLOeuro/EURCV")
    b = h["band"]
    assert b["floor_fall"] == pytest.approx(0.10) and b["timelock_h"] == 48 and b["now_bad_debt"] == 0
    assert h["bad_debt"] == pytest.approx(251_761, rel=1e-3)  # once the feed is upgraded
    assert "48 h at the earliest" in capsys.readouterr().out


def test_g12_a_value_computed_on_read():
    nav = OC.Probe("0x" + "11" * 20, description="Net Asset Value in USD", answer=1122879291821523144, decimals=18)
    nav.round_id, nav.history = 0, [nav.answer]
    assert OC.classify_input(nav)[0] == OC.CONSTANT_PRICE and OC.constant_kind(nav) == OC.EXCHANGE_RATE
    one = OC.Probe("0x" + "22" * 20, answer=10**18, decimals=18, history=[10**18])
    one.round_id = 0
    assert OC.constant_kind(one) == OC.FIXED
    g, *_ = GR.load([], [], True, "replay", pipeline.REPLAY_DIR / f"graph-{FX.lower()}")
    feed = next(n for n in g.nodes.values() if n["label"].startswith("Net Asset Value"))["details"]
    assert feed["constant_kind"] == OC.EXCHANGE_RATE and feed["freshness"].startswith("computed on read")


def test_g1_limits_under_shared_caps():
    total = 1000
    ids = [{"adapter": "A", "collateral": "C", "market": f"M{i}"} for i in range(3)]
    caps = {
        "A": (0, 10**9, WAD),
        "C": (0, 500, WAD),
        "M0": (0, 300, WAD),
        "M1": (0, 300, WAD),
        "M2": (0, 100, WAD // 2),
    }
    assert XP.market_limit(ids[2], caps, total) == 100  # min(100 absolute, 50 % × 1000)
    assert XP.group_limit(ids, caps, total) == 500  # 700 by market, capped by the shared collateral id
    assert XP.limit(None, total) == 0


def test_g1_the_belem_incident_at_the_caps(tmp_path):
    assert cli.main(["analyze", "--vault", BELEM, "--shock", "token=mGLOeuro:0.30", "--out", str(tmp_path)]) == 0
    inc, h = _hit(tmp_path, BELEM, "mGLOeuro/EURCV")
    assert h["cap_limit"] > h["vault_exposure"] and inc["at_caps_loss"] > inc["vault_loss"] * 2
