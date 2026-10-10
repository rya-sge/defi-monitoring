"""Admin surface rules and the poller's filter handling (plan 2026-10-10-admin-surface, US14, US15)."""

from pathlib import Path

import pytest

from riskdep.abi import MORPHO_BLUE, Event
from riskdep.admin import Contract, apply_events, assess_changes, assess_divergence, assess_events
from riskdep.borrower import BorrowMarket
from riskdep.poller import MAX_ADDRESSES, Poller

TOKEN = "0x" + "aa" * 20
ORACLE = "0x" + "bb" * 20
NEW = "0x" + "cc" * 20
ZERO = "0x" + "00" * 20


def contracts():
    return {TOKEN: Contract(TOKEN, ["collateral of X/USDC"], mint_watch=True, is_collateral=True, symbol="X",
                            impl="0x" + "01" * 20, owner="0x" + "02" * 20, total_supply=1_000),
            ORACLE: Contract(ORACLE, ["feed of the oracle of X/USDC"], symbol="X / USD", aggregator="0x" + "03" * 20)}


def ev(name, address=TOKEN, contract="admin", **args):
    return Event(name, contract, address, 10, "0x" + "ab" * 32, 0, args)


@pytest.mark.parametrize("event,args,level", [
    ("Upgraded", {"implementation": NEW}, "critical"),
    ("BeaconUpgraded", {"beacon": NEW}, "critical"),
    ("AdminChanged", {"previousAdmin": ZERO, "newAdmin": NEW}, "warn"),
    ("OwnershipTransferred", {"previousOwner": ZERO, "newOwner": NEW}, "warn"),
    ("Paused", {"account": NEW}, "critical"),
    ("Unpaused", {"account": NEW}, "info"),
    ("RoleGranted", {"role": "0x" + "00" * 32, "account": NEW, "sender": NEW}, "warn"),
    ("RoleGranted", {"role": "0x" + "11" * 32, "account": NEW, "sender": NEW}, "info"),
    ("RoleRevoked", {"role": "0x" + "00" * 32, "account": NEW, "sender": NEW}, "info"),
])
def test_admin_events_on_a_collateral_token(event, args, level):
    al = assess_events([ev(event, **args)], contracts(), 10)
    assert len(al) == 1 and al[0].level == level


def test_pause_of_a_non_collateral_contract_is_warn():
    al = assess_events([ev("Paused", ORACLE, account=NEW)], contracts(), 10)
    assert al[0].level == "warn"


def test_feed_change_is_warn():
    al = assess_events([ev("AggregatorConfirmed", ORACLE, previous=ZERO, latest=NEW)], contracts(), 10)
    assert al[0].level == "warn" and "changed" in al[0].title


def test_large_mint_is_critical_small_is_silent():
    assert assess_events([ev("Transfer", **{"from": ZERO, "to": NEW, "value": 100})], contracts(), 10)[0].level == "critical"
    assert assess_events([ev("Transfer", **{"from": ZERO, "to": NEW, "value": 10})], contracts(), 10) == []
    assert assess_events([ev("Transfer", **{"from": NEW, "to": ZERO, "value": 900})], contracts(), 10) == []


def test_blue_owner_actions():
    al = assess_events([ev("SetOwner", MORPHO_BLUE, "blue", newOwner=NEW),
                        ev("EnableIrm", MORPHO_BLUE, "blue", irm=NEW)], contracts(), 10)
    assert [a.level for a in al] == ["warn", "info"]


def test_slot_change_without_event_is_alerted_once():
    cs = contracts()
    before = {a: (c.impl, c.admin, c.beacon, c.owner, c.aggregator) for a, c in cs.items()}
    after = dict(before)
    after[TOKEN] = (NEW,) + before[TOKEN][1:]
    al = assess_changes(before, after, cs, 10)
    assert al[0].level == "critical" and "Implementation" in al[0].title
    # the same change already seen through its Upgraded event: the snapshot moved, nothing more to report
    apply_events([ev("Upgraded", implementation=NEW)], cs)
    snap = {a: (c.impl, c.admin, c.beacon, c.owner, c.aggregator) for a, c in cs.items()}
    assert assess_changes(snap, after, cs, 10) == []


def test_oracle_divergence_on_crossing():
    m = BorrowMarket("0x" + "11" * 32, NEW, TOKEN, ORACLE, NEW, int(0.9e18), "USDC", "X", 6, 18)
    mk = {m.id: m}
    assert assess_divergence({m.id: 0.01}, {m.id: -0.05}, mk, 10)[0].event == "OracleDivergence"
    assert assess_divergence({m.id: -0.04}, {m.id: -0.05}, mk, 10) == []
    assert assess_divergence({}, {m.id: None}, mk, 10) == []


class FakeF:
    mode = "direct"

    def __init__(self, fail_optional=False):
        self.bodies, self.fail_optional = [], fail_optional

    def post_json(self, url, body):
        q = body["params"][0]
        self.bodies.append(q)
        if self.fail_optional and q.get("topics") == ["0xopt"]:
            return {"error": {"message": "Request blocked"}}
        return {"result": []}


def test_long_address_lists_are_split_and_optional_failures_tolerated(tmp_path):
    f = FakeF(fail_optional=True)
    addrs = [f"0x{i:040x}" for i in range(20)]
    p = Poller(f, {"0x" + "ab" * 20: "vault"}, [], tmp_path / "c",
               extra_filters=[{"address": addrs, "topics": ["0xopt"], "_optional": True}])
    p._logs(1, 2)
    sent = [q for q in f.bodies if q.get("topics") == ["0xopt"]]
    assert len(sent) == 3 and all(len(q["address"]) <= MAX_ADDRESSES for q in sent)
    assert all("_optional" not in q for q in f.bodies)
    assert len(p.warnings) == 3
