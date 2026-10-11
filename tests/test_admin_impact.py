"""GAPV2 G10 and G2 (plan 2026-10-11-admin-impact, D244–D245): admin changes by what they can do to money already
deposited; who holds each role."""

import json

from riskdep import cli, pipeline
from riskdep import graph as GR
from riskdep import roles as RL
from riskdep import sources as S

BELEM = "0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec"


def test_classify_holders():
    assert RL.classify("0x", None, None, None)[0] == "EOA"
    assert RL.classify("0xef0100" + "ab" * 20, None, None, None) == ("EOA", "an EIP-7702 wallet (one key)")
    assert RL.classify("0x6080", None, None, 172800) == ("timelock", "a timelock (48 h)")
    assert RL.classify("0x6080", 3, 5, None) == ("Safe", "a Safe 3/5")
    assert RL.classify("0x6080", None, None, None)[0] == "contract"


def test_role_findings_by_role_and_key():
    owner = RL.Holder("0x" + "11" * 20, ["owner"], "EOA", "an EOA (one key)")
    alloc = RL.Holder("0x" + "22" * 20, ["allocator"], "Safe", "a Safe 1/1 (one key)", threshold=1, owners=1)
    safe = RL.Holder("0x" + "33" * 20, ["owner"], "Safe", "a Safe 4/8", threshold=4, owners=8)
    sent = RL.Holder("0x" + "44" * 20, ["sentinel"], "EOA", "an EOA (one key)")
    levels = [a.level for a in RL.findings([owner, alloc, safe, sent], 1)]
    assert levels == ["critical", "warn", "info", "info"]


def test_belem_roles_on_the_recorded_graph(tmp_path, capsys):
    d = pipeline.REPLAY_DIR / f"graph-{BELEM.lower()}"
    g, block, *_ = GR.load([], [], True, "replay", d)
    assert GR.annotate_roles(g, S.Fetcher("offline", d), block) == 3
    owner = next(n for n in g.nodes.values() if n["kind"] == "Admin" and n["label"].startswith("owner"))
    assert owner["details"]["holder_kind"] == "Safe" and owner["details"]["threshold"] == 4
    assert cli.main(["analyze", "--vault", BELEM, "--shock", "token=mGLOeuro:0.30", "--out", str(tmp_path)]) == 0
    notes = json.loads((tmp_path / f"vault-incident-{BELEM.lower()}.json").read_text())["notes"]
    one_key = next(n for n in notes if n.startswith("held by one key"))
    assert "allocator" in one_key and "sentinel" not in one_key
