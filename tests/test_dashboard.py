"""The web dashboard's vault and market views, offline from the recorded Sentora RLUSD vault."""

import json

import pytest

from riskdep import clock
from riskdep import dashboard as D
from riskdep import sources as S

VAULT = "0x6dc58a0fdfc8d694e571dc59b9a52eeea780e6bf"


@pytest.fixture(scope="module")
def f():
    # the drawdown request is keyed by date: replay it on the snapshot's day
    clock.set_as_of(json.loads((S.SNAPSHOT_DIR / "as_of.json").read_text())["as_of"])
    return S.Fetcher("offline")


def test_vault_allocation_and_weighted_liquidations(f):
    v = D.vault(f, VAULT)
    assert v["markets"] and f.network_calls == 0
    shares = [m["share_of_vault"] for m in v["markets"]]
    assert shares == sorted(shares, reverse=True) and sum(shares) <= 1 + 1e-9
    # the vault's part of a market's liquidated debt never exceeds the market's
    for m in v["markets"]:
        whole = sum(x["debt_usd"] for x in D.liquidations(f, m["id"]))
        part = sum(x["debt_usd"] for x in v["liquidations"] if x["market"] == m["id"])
        assert part <= whole * (1 + 1e-9)


def test_market_borrowers(f):
    mid = D.vault(f, VAULT)["markets"][0]["id"]
    m = D.market(f, mid)
    drops = [x["drop"] for x in m["liquidations"]]
    assert m["borrowers"] == len(drops) > 0 and drops == sorted(drops) and drops[0] >= 0


def test_borrower_concentration(f):
    for m in D.vault(f, VAULT)["markets"]:
        debts = [x["debt_usd"] for x in D.liquidations(f, m["id"])]
        assert m["borrowers"] == len(debts)
        if debts:
            assert 0 < m["top1_share"] <= m["top3_share"] <= 1 + 1e-9
            assert m["top1_share"] == pytest.approx(max(debts) / sum(debts))


def test_oracles_and_exit_from_recordings(f):
    # RockawayX USDC Yield has a recorded graph and an incident recording; Sentora has a watch recording only
    v = D.vault(f, "0xe0181090c22579b6a217f1522cbf8c9f1f0c1965")
    classes = {m["oracle_class"] for m in v["markets"]}
    assert classes <= {"price-tracking", "constant-price", "not classified"} and "constant-price" in classes
    assert all(feed["label"] for m in v["markets"] for feed in m["feeds"])
    e = v["exit"]
    assert e and 0 < e["plain"] + e["forced"] <= e["total"] and 0 < e["position"] <= e["total"]
    assets = [h["assets"] for h in e["holders"]]
    assert assets == sorted(assets, reverse=True) and e["depositor"] == e["holders"][0]["address"]
    assert f.network_calls == 0


def test_graph_oracles_pure():
    graph = {
        "nodes": [
            {"id": "m", "kind": "Pool", "label": "Blue X/USDC", "details": {"oracle_class": "constant-price"}},
            {"id": "o", "kind": "Oracle", "label": "Oracle", "details": {}},
            {"id": "a", "kind": "Oracle", "label": "X / USD", "details": {"freshness": "1h ago", "stale": False}},
        ],
        "edges": [{"source": "m", "target": "o", "rel": "priced by"}, {"source": "o", "target": "a", "rel": "reads"}],
    }
    assert D.graph_oracles(graph) == {
        "m": ("constant-price", [{"label": "X / USD", "freshness": "1h ago", "stale": False}])
    }
    assert D.graph_oracles(None) == {} and D.concentration([]) == (None, None)
