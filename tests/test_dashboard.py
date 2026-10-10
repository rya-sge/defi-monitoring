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
