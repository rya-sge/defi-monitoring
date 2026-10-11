"""Zama confidential vaults (plan 2026-10-11-zama): the registry, the pool, the exits, the graph, on the recordings."""

import json

from riskdep import cli, pipeline
from riskdep import exit_queue as EQ
from riskdep import zama as ZM
from riskdep.graph import annotate_zama, load

RWA = "0xc207d3f66537d7f66456808379a0e560cf20da36"
CSHARE = "0xb1b18ad1f16d744c470cb6b09cb826affcc9eb30"


def test_registry_lists_the_mainnet_vaults():
    assert len(ZM.Z["vaults"]) == 16 and ZM.entry(RWA)["cshare"] == CSHARE and ZM.is_pool(CSHARE.upper())
    assert not ZM.is_pool(RWA) and not ZM.is_pool(None)


def test_exits_say_the_batch_does_not_beat_an_incident_that_lands_at_once():
    z = ZM.ZamaState("v", CSHARE, 0.99, 1000, 1000 + 12 * 3600, None, 28, False, True)
    lines = ZM.exits(z, lands_at_once=True)
    assert "99.0%" in lines[0] and "12.0 h" in lines[1] and "does not beat" in lines[1]
    assert "amount becomes public" in lines[2] and "neither works" in lines[3]
    assert "does not beat" not in ZM.exits(z, lands_at_once=False)[1]


def test_a_cshare_is_not_a_fast_holder_ahead_in_the_queue():
    h = [EQ.Holder(CSHARE, 990, False), EQ.Holder("0x" + "a" * 40, 10, True)]
    assert sum(x.assets for x in h if x.fast) == 10  # the pool is not counted ahead of anyone


def test_confidential_rwa_incident_offline(tmp_path):
    """The 99 % holder is the cShare pool: the depositor is the largest public holder; the Zama exits are stated."""
    assert cli.main(["analyze", "--vault", RWA, "--shock", "token=PST:0.30", "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / f"vault-incident-{RWA}.json").read_text())
    assert r["depositor"] != CSHARE and r["depositor_assets"] < 0.02 * r["vault_total"] and r["verdict"] == "EXIT"
    z = " ".join(r["zama"])
    assert "99.1% of the vault is held confidentially" in z and "redeem batch 28" in z and "does not beat" in z


def test_graph_draws_the_hidden_layer():
    g, *_ = load([], [], True, "replay", cli.REPLAY_DIR / "graph-0xc207d3f66537d7f66456808379a0e560cf20da36")
    assert annotate_zama(g) == 1
    rels = {
        (g.nodes[e["source"]]["label"], e["rel"], g.nodes[e["target"]]["label"])
        for e in g.edges
        if e["target"] in g.nodes
    }
    assert ("cShare (confidential vault shares)", "decrypted by", "Zama Protocol (KMS, coprocessors)") in rels
    assert any(r == "accepts deposits only from" for _, r, _ in rels)  # the deposit gate
    assert pipeline.vault_graph(RWA) is not None  # the incident's graph is not annotated: the engine never sees it


def _recorded_events(vault):
    """The vault's real Zama events since its deployment, recorded through Etherscan (fixtures/replay/zama-events)."""
    from riskdep import sources as S
    from riskdep.abi import EVENTS, decode_log

    f = S.Fetcher("offline", cli.REPLAY_DIR / "zama-events")
    e = ZM.entry(vault)
    tp = {s.name: s.topic0 for s in EVENTS if s.contract == "zama"}
    rows = [
        (e["cshare"], x)
        for x in S.etherscan_logs(f, e["cshare"], tp["UnwrapFinalized"], None, e["deploy_block"], 26165600)
    ]
    rows += [
        (e["redeem_batcher"], x)
        for x in S.etherscan_logs(f, e["redeem_batcher"], tp["BatchCanceled"], None, e["deploy_block"], 26165600)
    ]
    logs = [
        {
            "address": a,
            "topics": x["topics"],
            "data": x["data"],
            "blockNumber": hex(x["block"]),
            "transactionHash": x["tx"],
            "logIndex": "0x0",
        }
        for a, x in rows
    ]
    return e, [decode_log(log, ZM.kinds(e)) for log in logs]


def test_z4_alerts_on_the_real_history_of_the_rwa_vault():
    """D191–D192 on Confidential RWA's real batches: two days with a large confidential outflow (5.6 % and 3.0 % of
    the vault), three instant exits above 1 %; the empty days (a zero aggregate, then a cancel) stay silent."""
    e, events = _recorded_events(RWA)
    supply = 26_340_839 * 10**18
    alerts = ZM.assess_events(events, e, supply, 10**12, 1)
    batches = [a for a in alerts if a.data.get("batch")]
    instant = [a for a in alerts if a.event == "Zama.Unwrap" and not a.data["batch"]]
    assert sorted(round(a.data["share_of_vault"], 3) for a in batches if a.level == "warn") == [0.030, 0.056]
    assert sum(1 for a in instant if a.level == "warn") == 3 and len(instant) == 14
    assert not [a for a in alerts if a.event == "Zama.BatchCanceled"]  # every cancel followed an empty day
    assert not [a for a in alerts if a.data.get("share_of_vault") == 0]


def test_z4_rules_on_admin_events():
    from riskdep.abi import Event

    e = ZM.entry(RWA)
    ev = [
        Event("Paused", "zama", e["redeem_batcher"], 1, "0xa", 0, {"account": "0x1"}),
        Event(
            "BatchCanceled", "zama", e["redeem_batcher"], 1, "0xb", 0, {"batchId": 29}
        ),  # no empty unwrap: a deadline
        Event("Upgraded", "zama", e["cshare"], 1, "0xc", 0, {"implementation": "0x" + "2" * 40}),
    ]
    got = {a.event: a.level for a in ZM.assess_events(ev, e, 10**24, 10**12, 1)}
    assert got == {"Zama.Paused": "critical", "Zama.BatchCanceled": "warn", "Zama.Upgraded": "critical"}
