"""A Vault V2 and its Blue markets, for the web dashboard: allocation, market state, liquidations.

Every figure comes from the Morpho API (three queries: the vault's adapters, its markets, each
market's borrowers), except each collateral's worst 1-year drawdown (DefiLlama coins). A borrower's
liquidating fall is 1 − 1/HF: the oracle fall at which its health factor reaches 1. The vault's
borrowers weigh each market's debt and collateral by the vault's share of that market's supply,
i.e. the part lent by the vault; the bad debt at a fall d, max(0, debt − collateral × (1 − d) / LIF),
is then the vault's own loss.

Each market also carries its borrower concentration (the largest and three largest borrowers' share of its debt) and,
when the vault has a recorded graph (fixtures/replay/graph-<vault>/), its oracle class and the freshness of the feeds
its oracle reads (D82, D155). The vault carries its exit liquidity at the block of its recorded state (the incident
or watch recording, `pipeline.vault_source`): what a plain withdrawal and forceDeallocate can pay, the Public
Allocator's reach, the largest depositor and the holders ahead of it (D62–D71). Both are read offline only, from
recordings, and are null when there is none: they add no network call to the dashboard.

`python -m riskdep.dashboard <vault>...` writes out/vaults.json and out/markets.json, the SPA's fixtures.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import clock
from . import sources as S
from .discover import morpho_lif

VAULT_QUERY = """query($a:String!){ vaultV2ByAddress(address:$a, chainId:1){
 address name asset{ symbol } totalAssetsUsd liquidityUsd
 adapters(first:10){ items{ ... on MorphoMarketV1Adapter {
  positions(first:50){ items{ market{ marketId } state{ supplyAssetsUsd } } } } } } } }"""

MARKETS_QUERY = """query($ids:[String!]){ markets(first:100, where:{uniqueKey_in:$ids, chainId_in:[1]}){ items{
 marketId lltv collateralAsset{ address symbol price{ usd } } loanAsset{ symbol }
 state{ supplyAssetsUsd borrowAssetsUsd liquidityAssetsUsd utilization borrowApy } } } }"""

BORROWERS_QUERY = """query($id:String!){
 marketPositions(first:1000, where:{marketUniqueKey_in:[$id], chainId_in:[1], borrowShares_gte:"1"}){
  items{ healthFactor state{ borrowAssetsUsd collateralUsd } } } }"""

DUST_USD = 1.0  # an allocation below a dollar is a leftover, not a position


def liquidations(f: S.Fetcher, market_id: str) -> list[dict]:
    """Every borrower of the market: the oracle fall that liquidates it, its debt and collateral, sorted by fall."""
    items = S.morpho(f, BORROWERS_QUERY, {"id": market_id})["marketPositions"]["items"]
    out = [
        {
            "drop": max(0.0, 1 - 1 / i["healthFactor"]),
            "debt_usd": i["state"]["borrowAssetsUsd"],
            "collateral_usd": i["state"]["collateralUsd"] or 0.0,
        }
        for i in items
        if i["healthFactor"] and i["state"]["borrowAssetsUsd"]
    ]
    return sorted(out, key=lambda x: x["drop"])


def _drawdown(f: S.Fetcher, address: str) -> float | None:
    """The collateral's worst 1-year drawdown, or None when DefiLlama has no price history for it."""
    dd = S.coin_drawdown(f, address)
    return dd["max_drawdown"] if dd["points"] else None


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
            "collateral_drawdown_1y": _drawdown(f, coll["address"]) if coll else None,
            "lif": morpho_lif(int(m["lltv"]) / 1e18),
            "supply_usd": st["supplyAssetsUsd"],
            "borrow_usd": st["borrowAssetsUsd"],
            "liquidity_usd": st["liquidityAssetsUsd"],
            "utilization": st["utilization"],
            "borrow_apy": st["borrowApy"],
        }
    return out


def concentration(debts: list[float]) -> tuple[float | None, float | None]:
    """D128, pure: the largest and the three largest borrowers' share of the market's debt; None with no debt."""
    total = sum(debts)
    if total <= 0:
        return None, None
    ranked = sorted(debts, reverse=True)
    return ranked[0] / total, sum(ranked[:3]) / total


def graph_oracles(graph: dict | None) -> dict[str, tuple[str | None, list[dict]]]:
    """D82, D155, pure: market id → (oracle class, the feeds its oracle reads with their freshness), from a graph."""
    if graph is None:
        return {}
    nodes = {n["id"]: n for n in graph["nodes"]}
    priced = {e["source"]: e["target"] for e in graph["edges"] if e["rel"] == "priced by"}
    reads: dict[str, list[dict]] = {}
    for e in graph["edges"]:
        if e["rel"] == "reads" and e["target"] in nodes:
            d = nodes[e["target"]]["details"]
            reads.setdefault(e["source"], []).append(
                {"label": nodes[e["target"]]["label"], "freshness": d.get("freshness"), "stale": d.get("stale")}
            )
    return {
        mid: (nodes[mid]["details"].get("oracle_class"), reads.get(orc, []))
        for mid, orc in priced.items()
        if nodes.get(mid, {}).get("kind") == "Pool"
    }


def exit_liquidity(address: str) -> dict | None:
    """D62–D71: the vault's exit liquidity at its recorded state, in asset units; None without a recording."""
    from . import drain as DR
    from . import exit_queue as EQ
    from . import pipeline
    from . import vault as V
    from . import zama as ZM

    try:
        f, block, _ = pipeline.vault_source(address.lower(), "offline")
        view = V.discover_vault(f, address.lower(), block)
        dep = V.largest_depositor(f, view.address, frozenset(ZM.POOLS))
        st = V.read_state(f, view, block, dep)
    except (FileNotFoundError, S.CacheMiss, S.SourceError):
        return None
    unit = 10**view.decimals
    liq = EQ.liquidity(st)
    pa = DR.read_pa(f, view, block)
    holders, _ = EQ.holders(f, view.address, st.total_assets, st.total_supply)
    if not holders:  # a recording made for an incident holds the depositor lookup, not the holders query
        holders = [
            EQ.Holder(a, n * st.total_assets // st.total_supply, None)
            for a, n in V.holder_shares(f, view.address)
            if st.total_supply
        ]
    reach = max((DR.pa_inflow(view, st, pa, mid) for mid in st.markets), default=0) if pa.known else None
    return {
        "block": block,
        "total": liq.total / unit,
        "plain": liq.plain / unit,
        "forced": liq.forced / unit,
        "penalty": liq.penalty,
        "public_allocator": reach / unit if reach is not None else None,
        "depositor": dep,
        "position": liq.position / unit,
        "holders": [
            {"address": h.address, "assets": h.assets / unit, "fast": h.fast}
            for h in sorted(holders, key=lambda h: -h.assets)
        ],
    }


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
    from .pipeline import vault_graph

    oracles = graph_oracles(vault_graph(address))
    markets, liq = [], []
    for mid, usd in sorted(alloc.items(), key=lambda kv: -kv[1]):
        m = info[mid]
        # two queries, two reads a moment apart: a sole lender can read as 100.0003 % of its market
        share_of_market = min(1.0, usd / m["supply_usd"]) if m["supply_usd"] else 0.0
        borrowers = liquidations(f, mid)
        top1, top3 = concentration([x["debt_usd"] for x in borrowers])
        cls, feeds = oracles.get(mid, (None, []))
        markets.append(
            {
                **m,
                "allocation_usd": usd,
                "share_of_vault": usd / total if total else 0.0,
                "share_of_market": share_of_market,
                "borrowers": len(borrowers),
                "top1_share": top1,
                "top3_share": top3,
                "oracle_class": cls,
                "feeds": feeds,
            }
        )
        liq += [
            {
                "drop": x["drop"],
                "debt_usd": x["debt_usd"] * share_of_market,
                "collateral_usd": x["collateral_usd"] * share_of_market,
                "market": mid,
            }
            for x in borrowers
        ]
    return {
        "address": v["address"].lower(),
        "name": v["name"],
        "asset_symbol": v["asset"]["symbol"],
        "total_assets_usd": total,
        "liquidity_usd": v["liquidityUsd"],
        "markets": markets,
        "liquidations": sorted(liq, key=lambda x: x["drop"]),
        "exit": exit_liquidity(address),
    }


if __name__ == "__main__":
    clock.set_as_of(json.loads((S.SNAPSHOT_DIR / "as_of.json").read_text())["as_of"])
    f = S.Fetcher("offline")
    vaults = {v["address"]: v for v in (vault(f, a) for a in sys.argv[1:])}
    markets = {m["id"]: market(f, m["id"]) for v in vaults.values() for m in v["markets"]}
    out = Path("out")
    out.mkdir(exist_ok=True)
    (out / "vaults.json").write_text(json.dumps(vaults, indent=2))
    (out / "markets.json").write_text(json.dumps(markets, indent=2))
