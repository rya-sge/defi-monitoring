"""A Vault V2 and its Blue markets, for the web dashboard: allocation, market state, liquidations.

Every figure comes from the Morpho API (three queries: the vault's adapters, its markets, each
market's borrowers). A borrower's liquidating fall is 1 − 1/HF: the oracle fall at which its
health factor reaches 1. The vault's liquidations weigh each market's by the vault's share of
that market's supply, i.e. the part of the liquidated debt that was lent by the vault.

`python -m riskdep.dashboard <vault>...` writes out/vaults.json and out/markets.json, the SPA's fixtures.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import sources as S

VAULT_QUERY = """query($a:String!){ vaultV2ByAddress(address:$a, chainId:1){
 address name asset{ symbol } totalAssetsUsd liquidityUsd
 adapters(first:10){ items{ ... on MorphoMarketV1Adapter {
  positions(first:50){ items{ market{ marketId } state{ supplyAssetsUsd } } } } } } } }"""

MARKETS_QUERY = """query($ids:[String!]){ markets(first:100, where:{uniqueKey_in:$ids, chainId_in:[1]}){ items{
 marketId lltv collateralAsset{ symbol price{ usd } } loanAsset{ symbol }
 state{ supplyAssetsUsd borrowAssetsUsd liquidityAssetsUsd utilization borrowApy } } } }"""

BORROWERS_QUERY = """query($id:String!){
 marketPositions(first:1000, where:{marketUniqueKey_in:[$id], chainId_in:[1], borrowShares_gte:"1"}){
  items{ healthFactor state{ borrowAssetsUsd } } } }"""

DUST_USD = 1.0  # an allocation below a dollar is a leftover, not a position


def liquidations(f: S.Fetcher, market_id: str) -> list[dict]:
    """Every borrower of the market as (oracle fall that liquidates it, its debt), sorted by fall."""
    items = S.morpho(f, BORROWERS_QUERY, {"id": market_id})["marketPositions"]["items"]
    out = [
        {"drop": max(0.0, 1 - 1 / i["healthFactor"]), "debt_usd": i["state"]["borrowAssetsUsd"]}
        for i in items
        if i["healthFactor"] and i["state"]["borrowAssetsUsd"]
    ]
    return sorted(out, key=lambda x: x["drop"])


def _markets(f: S.Fetcher, ids: list[str]) -> dict[str, dict]:
    items = S.morpho(f, MARKETS_QUERY, {"ids": ids})["markets"]["items"]
    out = {}
    for m in items:
        st, coll = m["state"], m["collateralAsset"]
        out[m["marketId"].lower()] = {
            "id": m["marketId"].lower(),
            "label": f"{coll['symbol'] if coll else 'idle'}/{m['loanAsset']['symbol']}",
            "lltv": int(m["lltv"]) / 1e18,
            "collateral_price_usd": coll["price"]["usd"] if coll and coll["price"] else None,
            "supply_usd": st["supplyAssetsUsd"],
            "borrow_usd": st["borrowAssetsUsd"],
            "liquidity_usd": st["liquidityAssetsUsd"],
            "utilization": st["utilization"],
            "borrow_apy": st["borrowApy"],
        }
    return out


def market(f: S.Fetcher, market_id: str) -> dict:
    m = _markets(f, [market_id]).get(market_id.lower())
    if m is None:
        raise S.SourceError(f"{market_id} is not a Morpho Blue market on Ethereum")
    liq = liquidations(f, market_id)
    return {**m, "borrowers": len(liq), "liquidations": liq}


def vault(f: S.Fetcher, address: str) -> dict:
    v = S.morpho(f, VAULT_QUERY, {"a": address})["vaultV2ByAddress"]
    if v is None:
        raise S.SourceError(f"{address} is not a Morpho Vault V2 on Ethereum")
    alloc: dict[str, float] = {}
    for adapter in v["adapters"]["items"]:
        for p in (adapter.get("positions") or {}).get("items", []):
            usd = p["state"]["supplyAssetsUsd"] or 0
            if usd >= DUST_USD:
                alloc[p["market"]["marketId"].lower()] = usd
    info = _markets(f, list(alloc)) if alloc else {}
    total = v["totalAssetsUsd"] or 0
    markets, liq = [], []
    for mid, usd in sorted(alloc.items(), key=lambda kv: -kv[1]):
        m = info[mid]
        # two queries, two reads a moment apart: a sole lender can read as 100.0003 % of its market
        share_of_market = min(1.0, usd / m["supply_usd"]) if m["supply_usd"] else 0.0
        markets.append({**m, "allocation_usd": usd, "share_of_vault": usd / total if total else 0.0})
        liq += [
            {"drop": x["drop"], "debt_usd": x["debt_usd"] * share_of_market, "market": m["label"]}
            for x in liquidations(f, mid)
        ]
    return {
        "address": v["address"].lower(),
        "name": v["name"],
        "asset_symbol": v["asset"]["symbol"],
        "total_assets_usd": total,
        "liquidity_usd": v["liquidityUsd"],
        "markets": markets,
        "liquidations": sorted(liq, key=lambda x: x["drop"]),
    }


if __name__ == "__main__":
    f = S.Fetcher("offline")
    vaults = {v["address"]: v for v in (vault(f, a) for a in sys.argv[1:])}
    markets = {m["id"]: market(f, m["id"]) for v in vaults.values() for m in v["markets"]}
    out = Path("out")
    out.mkdir(exist_ok=True)
    (out / "vaults.json").write_text(json.dumps(vaults, indent=2))
    (out / "markets.json").write_text(json.dumps(markets, indent=2))
