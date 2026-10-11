"""The fork demo (plan 2026-10-11-fork-demo): the Belem RWA EURCV crisis, played on a local mainnet fork with
scripts/fork/crisis-belem.sh and recorded with `watch --step 1 --record --record-as fork-belem`, replays offline with
the alerts in the order the acts produced them. If a change breaks the demo, this fails before the video is shown."""

import json

import pytest

from riskdep import admin as AD
from riskdep import sources as S
from riskdep.abi import Event
from riskdep.cli import REPLAY_DIR, main

VAULT = "0xd6d4b804014ef27836dbe9f8f6bf6c71251548ec"
RDIR = REPLAY_DIR / "fork-belem"
FEED = "0x8b7b1689396ef4468df1c0fab181d29b47089609"
TIMELOCK = "0xe3eee3e0d2398799c884a47fc40c029c8e241852"


@pytest.fixture(scope="module")
def alerts(tmp_path_factory):
    out = tmp_path_factory.mktemp("fork")
    fork_before = S.FORK
    try:
        assert main(["watch", "--vault", VAULT, "--replay", "--record-as", "fork-belem", "--out", str(out)]) == 0
    finally:
        S.FORK = fork_before  # the replay sets it from the recording's meta
    path = out / f"watch-{VAULT}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()]


def _first(alerts, event, contains=""):
    for i, a in enumerate(alerts):
        if a["event"] == event and contains in a["title"]:
            return i, a
    raise AssertionError(f"no {event} alert with {contains!r}: {[(a['event'], a['title'][:60]) for a in alerts]}")


def test_recording_is_a_fork_run_in_single_block_steps():
    meta = json.loads((RDIR / "start.json").read_text())
    assert meta["fork"] is True and meta["step"] == 1 and meta["vault"] == VAULT


def test_startup_findings(alerts):
    _, band = _first(alerts, "FeedBand")
    assert band["data"]["floor"] == pytest.approx(90_000) and band["data"]["room"] == pytest.approx(-0.10)
    assert "48 h" in band["title"]
    _, gate = _first(alerts, "ExitGate")
    assert gate["level"] == "info" and "abdicated" in gate["title"]
    _, tl = _first(alerts, "AdminSurface", "timelock")
    assert TIMELOCK in tl["data"]["timelocks"]
    # on a fork, the cross-checks against other sources are not run: no false "data sources disagree"
    assert not [a for a in alerts if a["event"] == "CrossCheck"]


def test_acts_in_order(alerts):
    i2, mark = _first(alerts, "Oracle", "moved")  # act 2: the issuer's markdown
    assert mark["title"].endswith("-10.0%")
    i3, _ = _first(alerts, "Blue.Liquidate")  # act 3: a liquidator steps in
    i4, _ = _first(alerts, "Blue.Withdraw", "100.0% utilised")  # act 4: the run empties the market
    i5, sub = _first(alerts, "Vault.Submit")  # act 5: the curator's gate is abdicated, so no critical
    assert sub["level"] == "info" and sub["data"]["abdicated"] is True
    i6, sched = _first(alerts, "Admin.CallScheduled")  # act 6: the upgrade is seen 48 h before it lands
    assert sched["level"] == "warn" and sched["data"]["victim"] == FEED and sched["data"]["delay"] == 172_800
    i6b, up = _first(alerts, "Admin.Upgraded")
    assert up["level"] == "critical"
    i6c, unreal = _first(alerts, "UnrealisedBadDebt")  # the new price uncovers the debt before anyone liquidates
    assert unreal["level"] == "critical"
    i7, bad = _first(alerts, "Blue.Liquidate", "Bad debt")  # act 7: the liquidation realises the loss
    assert bad["level"] == "critical"
    assert i2 < i3 < i4 < i5 < i6 < i6b < i6c < i7
    assert sched["block"] < up["block"] < bad["block"]


def test_loss_matches_the_chain(alerts):
    _, bad = _first(alerts, "Blue.Liquidate", "Bad debt")
    # 217,286 EURCV left the vault on-chain at act 7 (crisis-belem.sh prints it); the depositor holds ~99.99 %
    assert bad["depositor_impact"] == pytest.approx(-217_260, rel=0.002)


def test_timelock_alert_is_pure():
    tl = AD.Contract(TIMELOCK, timelock_delay=172_800, controls=[FEED])
    feed = AD.Contract(FEED, roles=["feed of the oracle of mGLOeuro/EURCV"], symbol="mGLOeuro/EUR")
    data = "0x99a88ec4" + FEED[2:].rjust(64, "0") + "76dc6dd9a59962062507eafec9cb57a549ca8f86".rjust(64, "0")
    e = Event(
        "CallScheduled",
        "admin",
        TIMELOCK,
        1,
        "0xab",
        0,
        {
            "id": "0x" + "11" * 32,
            "target": "0xbf25b58cb8dfad688f7bcb2b87d71c23a6600aac",
            "data": data,
            "delay": 172_800,
        },
    )
    (al,) = AD.assess_events([e], {TIMELOCK: tl, FEED: feed}, 1)
    assert al.level == "warn" and "upgrade of mGLOeuro/EUR" in al.title and "48 h" in al.title
    other = Event("CallScheduled", "admin", TIMELOCK, 1, "0xab", 0, {**e.args, "data": "0x12345678"})
    (al2,) = AD.assess_events([other], {TIMELOCK: tl, FEED: feed}, 1)
    assert al2.level == "info"


def test_band_findings_skip_a_distant_floor():
    near = AD.Contract("0xa", symbol="x", band=(90 * 10**8, 110 * 10**8, 8, 100 * 10**8))
    far = AD.Contract("0xb", symbol="y", band=(1, 10**20, 8, 100 * 10**8))
    out = AD.band_findings({"0xa": near, "0xb": far}, lambda _a: None, 1)
    assert [a.data["contract"] for a in out] == ["0xa"]
