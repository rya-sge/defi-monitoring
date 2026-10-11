"""Dependency graph of an address's Morpho positions and of vaults, as JSON and as an interactive HTML page.

Node types follow docs/analysis/ANALYSIS_MONITORING.md §1:
  Actor     whose capital is at stake: an address with positions, or a Vault V2 (adapters folded in)
  Pool      where liquidity sits and is priced: a Blue market, a Pendle pool
  Asset     a token; a vault's share token only where another protocol reuses it (an oracle conversion)
  Oracle    a market oracle and the feeds it reads
  Admin     who decides for a vault: owner, curator, allocators, sentinels
  External  off-chain dependencies of a yield source (registry.json)
Every edge comes from an on-chain attribute or a role getter, with the amount it carries where one exists.

Sibling markets (plan 2026-10-10-sibling-markets, D76–D85): Blue markets no actor holds that share a held market's
collateral, underlying or base price input, or lend that collateral. They join the held market through the shared
asset, oracle or feed node, never through a market → market edge. Every Blue market carries its oracle class and its
liquidation curve, the data the propagation engine of docs/model/graph-propagation.md needs.
"""

from __future__ import annotations

import html
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from eth_abi import decode

from . import borrower as B
from . import clock, discover
from . import feeds as FD
from . import market_risk as MR
from . import oracle_class as OC
from . import siblings as SB
from . import sources as S
from .abi import MORPHO_BLUE
from .discover import REGISTRY
from .positions import discover_user
from .vault import _call, _symbol, _uint, discover_vault, read_state


class Graph:
    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []

    def node(self, nid: str, kind: str, label: str, **details) -> str:
        nid = nid.lower()
        if nid in self.nodes:
            self.nodes[nid]["details"].update({k: v for k, v in details.items() if v is not None})
        else:
            self.nodes[nid] = {
                "id": nid,
                "kind": kind,
                "label": label,
                "details": {k: v for k, v in details.items() if v is not None},
            }
        return nid

    def edge(self, a: str, b: str, rel: str, amount: float | None = None, unit: str | None = None, **details):
        """One edge per (source, target, relation); a repeated edge updates the amount and details."""
        key = (a.lower(), b.lower(), rel)
        for e in self.edges:
            if (e["source"], e["target"], e["rel"]) == key:
                if amount is not None:
                    e["amount"], e["unit"] = amount, unit
                e["details"].update({k: v for k, v in details.items() if v is not None})
                return
        self.edges.append(
            {
                "source": key[0],
                "target": key[1],
                "rel": rel,
                "amount": amount,
                "unit": unit,
                "details": {k: v for k, v in details.items() if v is not None},
            }
        )


def _short(a: str) -> str:
    return f"{a[:6]}…{a[-4:]}"


def _asset(g: Graph, f, token: str, block, symbol: str | None = None) -> str:
    token = token.lower()
    if token not in g.nodes:
        sym = symbol or _symbol(f, token, block)
        reg = REGISTRY["issuers"].get(token) or REGISTRY["stables"].get(token) or {}
        g.node(
            token,
            "Asset",
            sym,
            address=token,
            issuer=reg.get("issuer"),
            source="ERC-20 symbol() on-chain" + (", issuer from registry.json" if reg else ""),
        )
    return token


def _oracle(g: Graph, f, oracle: str, block) -> str:
    oracle = oracle.lower()
    if oracle in g.nodes:
        return oracle
    code = S.rpc(f, "eth_getCode", [oracle, hex(block)]) or ""
    impl = "0x" + code[22:62] if code.startswith("0x363d3d373d3d3d363d73") else None
    cls, basis, base, feeds, standard = OC.classify_market_oracle(f, oracle, block)
    for p in base:
        OC.read_pendle_markets(f, p, block)
    shape = "Morpho ChainlinkOracleV2" if standard else "custom (no ChainlinkOracleV2 getters)"
    price = _uint(S.rpc_batch(f, [_call(oracle, "price()")], block)[0])
    g.node(
        oracle,
        "Oracle",
        f"Oracle {_short(oracle)}",
        address=oracle,
        shape=shape,
        implementation=impl,
        price_raw=str(price) if price is not None else "reverts",
        oracle_class=cls,
        class_basis=basis,
        constant_kind=OC.oracle_constant_kind(base, standard),
        tracks_market=base[0].pendle_market() if not standard and base else None,
        source="price() and getters read on-chain; class from the base-side inputs (D82–D84)",
    )
    probes = {p.address: p for p in base if not p.vault}
    for name, addr in feeds:
        desc = S.rpc_batch(f, [_call(addr, "description()")], block)[0]
        label = name
        if desc:
            try:
                label = decode(["string"], bytes.fromhex(desc[2:]))[0]
            except Exception:
                pass
        if "VAULT" in name:
            # a vault share whose exchange rate the oracle applies: an asset reused by the oracle, not an actor
            fid = g.node(
                addr,
                "Asset",
                f"{_symbol(f, addr, block)} (vault share)",
                address=addr,
                role_in_oracle=name,
                source="oracle getter, symbol() on-chain",
            )
            g.edge(oracle, fid, "converts through", role=name)
        else:
            fcls = OC.classify_input(probes[addr]) if addr in probes else (None, None)
            fresh = (
                FD.freshness(probes[addr].updated_at, probes[addr].update_times, clock.now())
                if addr in probes
                else None
            )
            fid = g.node(
                addr,
                "Oracle",
                label,
                address=addr,
                role_in_oracle=name,
                oracle_class=fcls[0],
                class_basis=fcls[1],
                constant_kind=OC.constant_kind(probes[addr]) if addr in probes else None,
                tracks_market=probes[addr].pendle_market() if addr in probes else None,
                updated_at=probes[addr].updated_at if addr in probes else None,
                freshness=fresh.text if fresh else None,
                stale=fresh.stale if fresh else None,
                source="oracle getter, description() on-chain; freshness from its rounds (D155)",
            )
            g.edge(oracle, fid, "reads", role=name)
    return oracle


def _market(g: Graph, f, m: B.BorrowMarket, block, quotes_pt: bool = True) -> str:
    mid = g.node(
        m.id,
        "Pool",
        f"Blue {m.collateral_symbol}/{m.loan_symbol}",
        market_id=m.id,
        lltv=f"{m.lltv:.1%}",
        irm=m.irm,
        source="Morpho Blue idToMarketParams on-chain",
    )
    loan = _asset(g, f, m.loan_token, block, m.loan_symbol)
    coll = _asset(g, f, m.collateral_token, block, m.collateral_symbol)
    g.edge(mid, loan, "lends")
    g.edge(mid, coll, "takes as collateral")
    orc = _oracle(g, f, m.oracle, block)
    g.edge(mid, orc, "priced by")
    g.node(mid, "Pool", "", oracle_class=g.nodes[orc]["details"].get("oracle_class"))
    if quotes_pt and m.collateral_symbol.upper().startswith("PT-") and f"pendle:{m.collateral_token}" not in g.nodes:
        try:
            pm = discover.find_pendle_market(f, m.collateral_token)
        except (S.SourceError, S.CacheMiss):
            return mid
        pool = g.node(
            f"pendle:{m.collateral_token}",
            "Pool",
            f"Pendle {pm['name']} pool",
            address=pm["address"],
            expiry=pm["expiry"][:10],
            liquidity_usd=(pm.get("details") or {}).get("liquidity"),
            implied_apy=(pm.get("details") or {}).get("impliedApy"),
            days_to_maturity=round(
                (datetime.fromisoformat(pm["expiry"].replace("Z", "+00:00")).timestamp() - clock.now()) / 86400, 2
            ),
            source="Pendle API markets",
        )
        g.edge(coll, pool, "trades in / redeems through")
        und = pm["underlyingAsset"].split("-", 1)[-1].lower()
        uid = _asset(g, f, und, block)
        g.edge(pool, uid, "yield source")
        _ladders(g, f, m, pm, und, orc)
        reg = REGISTRY["issuers"].get(und)
        for i, dep in enumerate((reg or {}).get("dependencies", [])):
            ext = g.node(f"ext:{und}:{i}", "External", dep, source="registry.json")
            g.edge(uid, ext, "relies on")
    return mid


def _suppliers(g: Graph, f: S.Fetcher, m: B.BorrowMarket, block) -> None:
    """The main lenders of a market as actors (borrower.top_suppliers, D41)."""
    for sp in B.top_suppliers(f, m, block):
        kind = {"Vault V2": "Vault V2 (capital provider)", "Vault V1": "Vault V1 / MetaMorpho (capital provider)"}.get(
            sp.kind, "lender"
        )
        aid = g.node(
            sp.actor,
            "Actor",
            sp.label,
            address=sp.actor,
            actor_type=kind,
            adapter=sp.address if sp.address != sp.actor else None,
            source="market's top suppliers from the Morpho API; amounts on-chain",
        )
        g.edge(
            aid,
            m.id,
            "supplies",
            sp.assets / 10**m.loan_decimals,
            m.loan_symbol,
            share_of_market=f"{sp.share:.1%}",
            through_adapter=sp.address if sp.address != sp.actor else None,
            note="its withdrawal raises utilisation and the borrow rate of the market",
        )


def _siblings(
    g: Graph, f: S.Fetcher, held: dict[str, B.BorrowMarket], block
) -> tuple[dict[str, B.BorrowMarket], dict[str, tuple[str, str]]]:
    """Sibling markets of the held ones (D76–D79): found with the Morpho API, re-read on-chain, added through _market.
    Returns them and the underlyings read on the way."""
    seeds = [
        SB.Market(
            mid,
            m.collateral_token,
            m.loan_token,
            m.oracle,
            frozenset(
                e["target"] for e in g.edges if e["source"] == m.oracle and e["details"].get("role") in OC.BASE_ROLES
            ),
            label=m.label,
        )
        for mid, m in held.items()
    ]
    cands = SB.candidates(f)
    und = SB.underlyings(f, {c.collateral for c in cands} | {s.collateral for s in seeds}, block)
    found = SB.match(seeds, cands, {t: u for t, (u, _) in und.items()})
    markets = B.discover_markets(f, [s.id for s in found], block) if found else {}
    for s in found:
        if s.id not in markets:
            continue  # the API listed a market the chain does not know: the chain decides (D78)
        nid = _market(g, f, markets[s.id], block)
        g.node(
            nid,
            "Pool",
            "",
            sibling=True,
            linked_by="; ".join(f"{rel} with {held[seed].label}" for seed, rel in s.links),
            source="sibling found with the Morpho API markets query; parameters and oracle read on-chain",
        )
    return markets, und


def _wraps(g: Graph, f: S.Fetcher, und: dict[str, tuple[str, str]], block) -> None:
    """An ERC-4626 share → the asset it redeems into, for every asset of the graph (D80)."""
    missing = {nid for nid, n in g.nodes.items() if n["kind"] == "Asset" and nid.startswith("0x") and nid not in und}
    und = {**und, **SB.underlyings(f, missing, block)} if missing else und
    for nid in [k for k, n in g.nodes.items() if n["kind"] == "Asset"]:
        target, how = und.get(nid, (None, None))
        if how == "erc4626":
            g.edge(
                nid,
                _asset(g, f, target, block),
                "wraps",
                note="an ERC-4626 share: redeems into this asset at the vault's exchange rate",
            )


def _ladders(g: Graph, f: S.Fetcher, m: B.BorrowMarket, pm: dict, und: str, orc: str) -> None:
    """Real Pendle quotes for selling the PT at growing sizes (engine D112, D113), turned into marginal-price curves:
    on the PT, its pool against the underlying with no aggregator (the price a Pendle TWAP oracle reads); on the
    underlying, the underlying received then sold for the loan token through the aggregator (the dollars a liquidator
    gets). Sizes in USD at today's oracle price, the loan token counted at $1."""
    try:
        price = int(g.nodes[orc]["details"].get("price_raw"))
    except (TypeError, ValueError):
        return
    usd_per_pt = price * 10**m.collateral_decimals / 10**36 / 10**m.loan_decimals
    ratio = REGISTRY["engine"]["capacity_min_ratio"]
    sizes = discover.ladder_sizes((pm.get("details") or {}).get("liquidity"))
    pt = m.collateral_token
    internal, refused = discover.quote_ladder(
        f, pm["address"], pt, und, m.collateral_decimals, usd_per_pt, False, sizes
    )
    curve, cap = discover.marginal_curve(internal, ratio)
    if refused and cap is None:
        cap = internal[-1][0] if internal else 0.0  # Pendle could not route the next size: the pool is full there
    if curve or cap is not None:
        g.node(
            pt,
            "Asset",
            "",
            impact_curve=curve,
            capacity_usd=cap,
            impact_source="Pendle swap quotes: the PT sold into its pool for the underlying, no aggregator",
        )
    exits, refused2 = discover.quote_ladder(
        f, pm["address"], pt, m.loan_token, m.collateral_decimals, usd_per_pt, True, sizes
    )
    got = dict(internal)
    pts = [(got[usd], out) for usd, out in exits if usd in got]  # (underlying received, loan token received)
    if pts and pts[0][0] and "impact_curve" not in g.nodes[und]["details"]:
        usd_per_und = pts[0][1] / pts[0][0] / 10**m.loan_decimals
        curve2, cap2 = discover.marginal_curve([(u * usd_per_und, out) for u, out in pts], ratio)
        if refused2 and cap2 is None:
            cap2 = pts[-1][0] * usd_per_und
        if curve2 or cap2 is not None:
            g.node(
                und,
                "Asset",
                "",
                impact_curve=curve2,
                capacity_usd=cap2,
                impact_source=f"Pendle swap quotes: the underlying sold for {m.loan_symbol} through the aggregator",
            )


PAIR = re.compile(r"^\s*([A-Za-z0-9.\-]+)\s*/\s*USD\s*$")


def _tracks(g: Graph) -> None:
    """Ties each oracle input to the market it reads (engine D115): a Pendle TWAP input → the PT of its pool; a
    price-tracking 'SYM / USD' feed → the one asset of the graph with that symbol. An oracle whose base side reads a
    tracked input is marked `tracks_bound`, and so are the markets it prices."""
    pools = {n["details"].get("address", "").lower(): nid for nid, n in g.nodes.items() if nid.startswith("pendle:")}
    pt_of_pool = {e["target"]: e["source"] for e in g.edges if e["rel"] == "trades in / redeems through"}
    symbols: dict[str, list[str]] = {}
    for nid, n in g.nodes.items():
        if n["kind"] == "Asset":
            symbols.setdefault(n["label"], []).append(nid)
    for nid, n in list(g.nodes.items()):
        if n["kind"] != "Oracle":
            continue
        d = n["details"]
        pool = pools.get(d.get("tracks_market") or "")
        pair = PAIR.match(n["label"]) if d.get("oracle_class") == "price-tracking" else None
        if pool and pool in pt_of_pool:
            g.edge(nid, pt_of_pool[pool], "tracks", note="a Pendle TWAP of this PT's pool (PT against its underlying)")
        elif pair and len(symbols.get(pair.group(1), [])) == 1:
            g.edge(nid, symbols[pair.group(1)][0], "tracks", note=f"the {pair.group(1)} / USD market")
    tracked = {e["source"] for e in g.edges if e["rel"] == "tracks"}
    for nid, n in g.nodes.items():
        if n["kind"] == "Oracle" and n["details"].get("shape"):
            bound = nid in tracked or any(
                e["source"] == nid
                and e["rel"] == "reads"
                and str(e["details"].get("role", "")).startswith("BASE")
                and e["target"] in tracked
                for e in g.edges
            )
            g.node(nid, "Oracle", "", tracks_bound=bound)
    for e in g.edges:
        if e["rel"] == "priced by":
            g.node(e["source"], "Pool", "", oracle_tracks_bound=g.nodes[e["target"]]["details"].get("tracks_bound"))


def _market_state(g: Graph, f: S.Fetcher, markets: dict[str, B.BorrowMarket], block) -> None:
    """Supply, borrow, the collateral of the borrowers and the liquidation curve of every Blue market (D81), from all
    its borrowers (market_risk, D45)."""
    if not markets:
        return
    infos = {mid: MR.MarketInfo(mid, m.lltv, m.loan_decimals, m.loan_symbol, m.label) for mid, m in markets.items()}
    tracker = MR.Tracker(infos)
    tracker.refresh(f, block)
    ids = list(markets)
    calls = []
    for mid in ids:
        calls += [
            _call(MORPHO_BLUE, "market(bytes32)", ["bytes32"], [bytes.fromhex(mid[2:])]),
            _call(markets[mid].oracle, "price()"),
        ]
    res = S.rpc_batch(f, calls, block)
    prices = {mid: _uint(res[2 * i + 1]) for i, mid in enumerate(ids)}
    risks = tracker.compute(prices)
    for i, mid in enumerate(ids):
        m, r, raw = markets[mid], risks[mid], res[2 * i]
        ld, cd = 10**m.loan_decimals, 10**m.collateral_decimals
        supply, borrow = (decode(["uint128"] * 6, bytes.fromhex(raw[2:]))[0], r.total_borrow) if raw else (0, 0)
        coll = sum(c for c, _ in tracker.positions.get(mid, {}).values())
        tba, tbs = tracker.totals.get(mid, (0, 0))
        price = prices.get(mid)
        positions = [
            [c * price // 10**36 / ld, b * (tba + 1) // (tbs + 10**6) / ld]
            for c, b in tracker.positions.get(mid, {}).values()
            if b and price is not None
        ]  # collateral value at today's oracle price and debt, in loan units: the engine's input (D111)
        g.node(
            mid,
            "Pool",
            "",
            total_supply=supply / ld,
            total_borrow=borrow / ld,
            loan_unit=m.loan_symbol,
            utilization=f"{borrow / supply:.1%}" if supply else None,
            borrowers=r.borrowers,
            collateral_of_borrowers=coll / cd,
            collateral_unit=m.collateral_symbol,
            unrealised_bad_debt=r.unrealised_bad_debt / ld,
            lltv_value=m.lltv,
            free_liquidity=max(0, supply - borrow) / ld,
            loan_usd=1.0 if m.loan_token in REGISTRY["stables"] else None,
            _positions=positions,
            liquidation_curve=[
                {
                    "oracle_fall": p.drop,
                    "liquidatable_debt": p.liquidatable_debt / ld,
                    "positions": p.positions,
                    "bad_debt": p.bad_debt / ld,
                    "collateral_liquidatable": p.collateral / cd,
                }
                for p in r.curve
            ],
            state_source="Morpho Blue market() and every borrower's position() on-chain, borrowers from the Morpho API",
        )
        g.edge(
            mid,
            m.collateral_token,
            "takes as collateral",
            coll / cd,
            m.collateral_symbol,
            note="collateral of the market's borrowers; liquidations sell it (curve on the market)",
        )


def build(
    f: S.Fetcher, block: int, user: str | None = None, vaults: list[str] | None = None, siblings: bool = True
) -> Graph:
    g = Graph()
    vaults = [v.lower() for v in (vaults or [])]
    held: dict[str, B.BorrowMarket] = {}  # the seed markets of the sibling search (D76)
    if user:
        user = user.lower()
        up = discover_user(f, user)
        pos = g.node(
            f"user:{user}",
            "Actor",
            f"Address {_short(user)}",
            address=user,
            actor_type="address with positions",
            source="Morpho API userByAddress (positions), Morpho Blue position() on-chain (amounts)",
        )
        if up.borrows:
            markets = B.discover_markets(f, up.borrows, block)
            states = B.read_borrows(f, markets, user, block)
            for mid, m in markets.items():
                st = states[mid]
                node = _market(g, f, m, block)
                held[mid] = m
                hf = st.hf(m.lltv)
                g.edge(
                    pos,
                    node,
                    "borrows from",
                    st.debt / 10**m.loan_decimals,
                    m.loan_symbol,
                    collateral=f"{st.collateral / 10**m.collateral_decimals:,.2f} {m.collateral_symbol}",
                    health_factor=None if hf is None else round(hf, 4),
                    liquidation_at=None if hf in (None, math.inf) else f"-{1 - 1 / hf:.2%} oracle fall",
                )
                _suppliers(g, f, m, block)
        vaults += [v for v in up.vaults if v not in vaults]
    for va in vaults:
        view = discover_vault(f, va, block)
        st = read_state(f, view, block, user if user else None)
        unit = 10**view.decimals
        vid = g.node(
            va,
            "Actor",
            f"Vault {view.name}",
            address=va,
            actor_type="Vault V2 (capital provider)",
            total_assets=f"{st.total_assets / unit:,.0f} {view.asset_symbol}",
            total_assets_value=st.total_assets / unit,
            idle=f"{st.idle / unit:,.0f} {view.asset_symbol}",
            plain_withdrawal_capacity=f"{st.withdrawable / unit:,.0f} {view.asset_symbol}",
            adapters=", ".join(f"{a.address} ({a.kind})" for a in view.adapters),
            source="Vault V2 getters on-chain",
        )
        g.edge(vid, _asset(g, f, view.asset, block, view.asset_symbol), "denominated in")
        if user and st.depositor_shares:
            g.edge(f"user:{user}", vid, "deposits in", st.depositor_assets / unit, view.asset_symbol)
        read = B.discover_markets(f, view.market_ids, block)  # decimals included, for the curves
        for a in view.adapters:
            for mp in a.markets.values():
                ms = st.markets[mp.id]
                m = read.get(mp.id) or B.BorrowMarket(
                    mp.id,
                    mp.loan_token,
                    mp.collateral_token,
                    mp.oracle,
                    mp.irm,
                    int(round(mp.lltv * 1e18)),
                    view.asset_symbol,
                    mp.collateral_symbol,
                    view.decimals,
                )
                node = _market(g, f, m, block)
                held[mp.id] = m
                g.edge(
                    vid,
                    node,
                    "supplies",
                    ms.vault_assets / unit,
                    view.asset_symbol,
                    share_of_vault=f"{ms.vault_assets / st.total_assets:.1%}" if st.total_assets else None,
                    share_of_market=f"{ms.vault_assets / ms.total_supply_assets:.1%}"
                    if ms.total_supply_assets
                    else None,
                    through_adapter=a.address,
                    utilization=f"{ms.utilization:.1%}",
                )
        # admins: owner and curator on-chain; allocators and sentinels listed by the API, each confirmed on-chain
        owner, curator = (
            ("0x" + r[-40:]).lower() if r else None
            for r in S.rpc_batch(f, [_call(va, "owner()"), _call(va, "curator()")], block)
        )
        roles: dict[str, list[str]] = {}
        for addr, role in ((owner, "owner"), (curator, "curator")):
            if addr:
                roles.setdefault(addr, []).append(role)
        try:
            d = S.morpho(
                f,
                """query($a:String!){ vaultV2ByAddress(address:$a, chainId:1){
                    allocators{ allocator{address} } sentinels{ sentinel{address} } } }""",
                {"a": va},
            )["vaultV2ByAddress"]
            cand = [(x["allocator"]["address"].lower(), "allocator") for x in d["allocators"]] + [
                (x["sentinel"]["address"].lower(), "sentinel") for x in d["sentinels"]
            ]
            checks = S.rpc_batch(
                f,
                [
                    _call(va, "isAllocator(address)" if r == "allocator" else "isSentinel(address)", ["address"], [a])
                    for a, r in cand
                ],
                block,
            )
            for (addr, role), ok in zip(cand, checks):
                if _uint(ok):
                    roles.setdefault(addr, []).append(role)
        except (S.SourceError, S.CacheMiss, KeyError, TypeError):
            pass
        verb = {
            "owner": "owns (sets curator, sentinels)",
            "curator": "curates (timelocked changes)",
            "allocator": "allocates (immediate, within caps)",
            "sentinel": "can de-risk (lower caps, revoke)",
        }
        for addr, rs in roles.items():
            nid = g.node(
                f"admin:{addr}",
                "Admin",
                f"{' + '.join(rs)} {_short(addr)}",
                address=addr,
                source="owner()/curator() on-chain; allocators and sentinels from the Morpho API, "
                "confirmed with isAllocator()/isSentinel()",
            )
            for r in rs:
                g.edge(nid, vid, verb[r])
    found, und = _siblings(g, f, held, block) if siblings and held else ({}, {})
    _wraps(g, f, und, block)
    _tracks(g)
    _market_state(g, f, {**held, **found}, block)
    return g


def build_all(f: S.Fetcher, block: int, users: list[str], vaults: list[str], siblings: bool = True) -> Graph:
    """One graph for several addresses and vaults: the vaults are built with the first address."""
    g = None
    for i, u in enumerate(users or [None]):
        part = build(f, block, u, vaults if i == 0 else [], siblings)
        if g is None:
            g = part
            continue
        for n in part.nodes.values():
            g.node(n["id"], n["kind"], n["label"], **n["details"])
        for e in part.edges:
            g.edge(e["source"], e["target"], e["rel"], e["amount"], e["unit"], **e["details"])
    return g


def load(
    users: list[str], vaults: list[str], siblings: bool, mode: str, replay_dir: Path
) -> tuple[Graph, int, list[str], list[str], bool]:
    """Build a graph live (`direct`), live while saving every response (`record`), or from a recording (`replay`,
    whose meta.json fixes the targets, the block and siblings). Returns (graph, block, users, vaults, siblings)."""
    meta = replay_dir / "meta.json"
    if mode == "replay":
        if not meta.exists():
            raise FileNotFoundError(f"no recorded graph in {replay_dir}")
        m = json.loads(meta.read_text())
        users, vaults, block, siblings = m["users"], m["vaults"], m["block"], m["siblings"]
        clock.set_as_of(m.get("as_of"))  # days to a PT's maturity count from the recording, not from today
        f = S.Fetcher("offline", replay_dir)
    else:
        # a direct run gets no directory: the Fetcher would create an empty one under fixtures/
        f = S.Fetcher("refresh", replay_dir) if mode == "record" else S.Fetcher("direct")
        block = int(S.rpc(f, "eth_blockNumber", []), 16) - 2
    g = build_all(f, block, users, vaults, siblings)
    if mode == "record":
        meta.write_text(
            json.dumps(
                {"users": users, "vaults": vaults, "block": block, "siblings": siblings, "as_of": clock.now()}, indent=1
            )
        )
    return g, block, users, vaults, siblings


def annotate_zama(g: Graph) -> int:
    """D175: for each vault of the graph entered through Zama's Confidential Vault protocol, the hidden layer a
    confidential depositor depends on: the cShare pool that holds its shares, the deposit and redeem batchers (daily),
    the confidential asset, Zama's decryption (KMS and coprocessors) that every exit needs, and the wrapper registry
    that can pause the wrappers. From the registry's verified addresses; no read. Returns the number of vaults."""
    from . import zama as ZM

    n = 0
    for vid in [i for i, x in g.nodes.items() if x["kind"] == "Actor"]:
        e = ZM.entry(vid)
        if e is None:
            continue
        n += 1
        kms = g.node(
            "zama:protocol",
            "External",
            "Zama Protocol (KMS, coprocessors)",
            role="decrypts every batch aggregate and every unwrap: if it halts, no confidential exit completes",
            source="docs/external/docs.zama.org-protocol-docs (D175)",
        )
        reg = g.node(
            ZM.Z["wrapper_registry"],
            "Admin",
            "Zama token wrapper registry",
            address=ZM.Z["wrapper_registry"],
            role="its governance can pause a wrapper",
        )
        cs = g.node(
            e["cshare"],
            "Asset",
            "cShare (confidential vault shares)",
            address=e["cshare"],
            zama_vault=e["name"],
            pool=True,
            role="holds the vault shares of every confidential depositor: one pool, not one holder",
        )
        ca = g.node(e["casset"], "Asset", "cAsset (confidential underlying)", address=e["casset"])
        g.edge(cs, vid, "wraps")
        if e["underlying"] in g.nodes:
            g.edge(ca, e["underlying"], "wraps")
        rb = g.node(
            e["redeem_batcher"],
            "Pool",
            "Zama redeem batcher (daily)",
            address=e["redeem_batcher"],
            role="the confidential exit: one batch a day, settled after a decryption",
        )
        db = g.node(e["deposit_batcher"], "Pool", "Zama deposit batcher (daily)", address=e["deposit_batcher"])
        g.edge(rb, vid, "redeems from")
        g.edge(db, vid, "deposits into")
        g.edge(rb, cs, "takes")
        g.edge(db, ca, "takes")
        for x in (cs, ca, rb, db):
            g.edge(x, kms, "decrypted by")
        for x in (cs, ca):
            g.edge(x, reg, "can be paused by")
        if e.get("deposit_gate"):
            g.edge(vid, db, "accepts deposits only from", gate=e["deposit_gate"])
    return n


def annotate_tvl(g: Graph, protocols: list[dict]) -> int:
    """D160: each Blue market, PT and issuer token of the graph points to the DefiLlama protocol it belongs to, an
    External node carrying that protocol's TVL, its share of DeFi and of its category, and whether that is a
    concentration (`tvl` in the registry). Returns the number of protocols drawn."""
    from . import tvl as TV

    drawn = {}
    for nid, n in list(g.nodes.items()):
        slug = TV.slug_of(n)
        if slug is None:
            continue
        if slug not in drawn:
            c = TV.concentration(protocols, slug)
            if c is None:
                continue
            drawn[slug] = g.node(
                f"protocol:{slug}",
                "External",
                c.name,
                tvl_usd=round(c.tvl_usd),
                category=c.category,
                share_of_defi=round(c.share_defi, 5),
                share_of_category=round(c.share_category, 4),
                rank_in_category=c.rank,
                concentrated=c.concentrated,
                concentration=c.text,
                source="DefiLlama /protocols (D158–D160)",
            )
        g.edge(nid, drawn[slug], "runs on" if n["kind"] == "Pool" else "issued by")
    return len(drawn)


def annotate_pharos(g: Graph, snap) -> int:
    """D136, D137: Pharos on the graph, keyless. Each asset Pharos covers gets its grade; what backs it off-chain
    becomes a `backed by (Pharos)` edge, to the asset already in the graph or to an External node; a narrow common-mode
    group (one mint key, upgrade admin, reserve issuer or redemption rail) shared by two assets of the graph becomes an
    External node they both `share`. Returns the number of assets graded."""
    from . import pharos as PH

    pids = {}
    for nid, n in list(g.nodes.items()):
        if n["kind"] != "Asset":
            continue
        pid = PH.resolve(snap, nid, n["label"])
        if pid is None:
            continue
        pids[pid] = nid
        g.node(nid, "Asset", n["label"], pharos_id=pid, pharos_grade=snap.grade(pid), pharos_as_of=snap.as_of)
    for pid, nid in list(pids.items()):
        for up, w, role in snap.backing.get(pid, []):
            if w < PH.P["min_exposure"]:
                continue
            target = pids.get(up) or g.node(
                f"pharos:{up}", "External", PH.name(up), pharos_id=up, pharos_grade=snap.grade(up), source="Pharos"
            )
            g.edge(nid, target, "backed by (Pharos)", share=round(w, 4), role=role, source=f"Pharos {snap.as_of}")
    seen = set()
    for pid, nid in pids.items():
        for kind, key, members in snap.groups.get(pid, []):
            inside = [pids[m] for m in members if m in pids]
            if len(inside) < 2 or (kind, key) in seen:
                continue
            seen.add((kind, key))
            gid = g.node(
                f"pharos-group:{kind}:{key}", "External", f"{kind.replace('-', ' ')}: {key[:24]}", source="Pharos"
            )
            for a in inside:
                g.edge(a, gid, "shares (Pharos)", kind=kind, members=len(members))
    return len(pids)


CSS = """
:root{--bg:#ffffff;--fg:#1f2328;--muted:#59636e;--panel:#f6f8fa;--line:#d1d9e0;
--Actor:#0072B2;--Pool:#009E73;--Asset:#E69F00;--Oracle:#CC79A7;--Admin:#D55E00;--External:#999999;--edge:#8c959f}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;
--panel:#151b23;--line:#3d444d;--edge:#6e7681}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--panel:#151b23;--line:#3d444d;--edge:#6e7681}
*{box-sizing:border-box}html,body{margin:0;height:100%;background:var(--bg);color:var(--fg);
font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
.app{display:grid;grid-template-columns:320px 1fr;height:100vh}
aside{background:var(--panel);border-right:1px solid var(--line);padding:16px;overflow:auto}
h1{font-size:1.05rem;margin:0 0 4px}h2{font-size:.85rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:18px 0 6px}
.muted{color:var(--muted);font-size:.85rem}#cy{width:100%;height:100%}
.legend label{display:flex;align-items:center;gap:8px;margin:3px 0;cursor:pointer}
.sw{width:14px;height:14px;border-radius:3px;display:inline-block;border:1px solid var(--line)}
.sw.round{border-radius:50%}.sw.diamond{transform:rotate(45deg) scale(.8)}
input[type=search]{width:100%;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
table{border-collapse:collapse;width:100%;font-size:.82rem}td{border-bottom:1px solid var(--line);padding:4px 2px;vertical-align:top;word-break:break-word}
td{white-space:pre-line}td:first-child{color:var(--muted);width:38%}button{padding:5px 10px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
@media (max-width:760px){.app{grid-template-columns:1fr;grid-template-rows:auto 70vh;height:auto}aside{border-right:0;border-bottom:1px solid var(--line)}}
"""

SHAPES = {
    "Actor": "round-rectangle",
    "Pool": "ellipse",
    "Asset": "round-tag",
    "Oracle": "diamond",
    "Admin": "triangle",
    "External": "rectangle",
}
DESCR = {
    "Actor": "whose capital is at stake: an address, a Vault V2",
    "Pool": "where liquidity sits: Blue market (dashed: sibling), Pendle pool",
    "Asset": "token: loan, collateral, yield source, reused vault share",
    "Oracle": "market oracle and the feeds it reads",
    "Admin": "decides for a vault: owner, curator, allocator, sentinel",
    "External": "off-chain dependency (registry.json; Pharos backing and common-mode groups)",
}


def to_html(g: Graph, title: str, subtitle: str) -> str:
    data = {"nodes": list(g.nodes.values()), "edges": g.edges}
    counts = {k: sum(1 for n in g.nodes.values() if n["kind"] == k) for k in SHAPES}
    legend = "".join(
        f'<label><input type="checkbox" checked data-kind="{k}"> <span class="sw" style="background:var(--{k})"></span>'
        f'<b>{k}</b> <span class="muted">({counts[k]}) {html.escape(DESCR[k])}</span></label>'
        for k in SHAPES
        if counts[k]
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Morpho Dependency Graph</title>
<style>{CSS}</style></head><body><div class="app"><aside>
<h1>{html.escape(title)}</h1><p class="muted">{html.escape(subtitle)}</p>
<h2>Node types</h2><div class="legend">{legend}</div>
<p class="muted">Shapes repeat the colour: rounded box Actor, ellipse Pool, tag Asset, diamond Oracle, triangle Admin, square External.
A dashed, paler Pool is a sibling market: no actor of the graph holds it, and it joins a held market through the asset, oracle or feed they share.
Edge width grows with the amount carried (log scale, in the token of the edge). Zoom in to read asset, oracle and off-chain labels; click a node to isolate its neighbours.</p>
<h2>Find</h2><input type="search" id="q" placeholder="symbol, address, market id…">
<p><button id="fit">Fit</button> <button id="lay">Re-layout</button></p>
<h2>Selection</h2><div id="info" class="muted">Click a node or an edge.</div>
</aside><div id="cy" role="img" aria-label="Interactive dependency graph"></div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js"></script>
<script>
const DATA={json.dumps(data, default=str)};
const SHAPES={json.dumps(SHAPES)};
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const fmt=x=>x==null?"":(Math.abs(x)>=1e6?(x/1e6).toFixed(2)+"M":Math.abs(x)>=1e3?(x/1e3).toFixed(1)+"k":x.toFixed(2));
const els=[...DATA.nodes.map(n=>({{data:{{id:n.id,label:n.label,kind:n.kind,details:n.details,sibling:n.details.sibling?1:0}}}})),
 ...DATA.edges.map((e,i)=>({{data:{{id:"e"+i,source:e.source,target:e.target,rel:e.rel,amount:e.amount,unit:e.unit,details:e.details,
   w:e.amount?Math.min(10,1+Math.log10(1+e.amount)/1.2):1,label:e.amount>=1?fmt(e.amount)+" "+(e.unit||""):""}}}}))];
const cy=cytoscape({{container:document.getElementById("cy"),elements:els,wheelSensitivity:0.2,
 style:[{{selector:"node",style:{{"background-color":e=>css("--"+e.data("kind")),"shape":e=>SHAPES[e.data("kind")]||"ellipse",
   "label":"data(label)","font-size":10,"color":css("--fg"),"text-valign":"bottom","text-margin-y":4,"width":26,"height":26,
   "text-wrap":"wrap","text-max-width":120,"border-width":1,"border-color":css("--line")}}}},
  {{selector:'node[kind="Actor"]',style:{{"width":44,"height":30,"font-weight":"bold","font-size":11,"text-max-width":90}}}},
  {{selector:'node[kind="Asset"],node[kind="Oracle"],node[kind="External"]',style:{{"min-zoomed-font-size":9}}}},
  {{selector:"node[sibling = 1]",style:{{"border-style":"dashed","border-width":2,"border-color":css("--fg"),"background-opacity":0.55}}}},
  {{selector:"edge",style:{{"width":"data(w)","line-color":css("--edge"),"target-arrow-color":css("--edge"),
   "target-arrow-shape":"triangle","curve-style":"bezier","opacity":0.75,"label":"data(label)","font-size":8,
   "color":css("--muted"),"text-rotation":"autorotate","text-background-color":css("--bg"),"text-background-opacity":0.8}}}},
  {{selector:".faded",style:{{"opacity":0.08}}}},{{selector:":selected",style:{{"border-width":3,"border-color":css("--fg"),"line-color":css("--fg")}}}}],
 layout:{{name:"preset"}}}});
// roots passed as a collection: ids such as "0x6dc5…" start with a digit and make a CSS selector fail
// sibling markets are roots too: no actor of the graph points at them, they hang from the shared nodes below
const roots=()=>cy.nodes().filter(n=>n.data("kind")==="Actor"||n.data("kind")==="Admin"||n.data("sibling")===1);
const relayout=()=>cy.layout({{name:"breadthfirst",directed:true,spacingFactor:1.5,roots:roots()}}).run();
relayout();
const num=x=>typeof x==="number"?x.toLocaleString("en-US",{{maximumFractionDigits:Math.abs(x)<1?4:2}}):String(x);
const val=v=>Array.isArray(v)?v.map(o=>o&&typeof o==="object"?Object.entries(o).map(([a,b])=>a.replace(/_/g," ")+" "+num(b)).join(", "):num(o)).join("\\n"):num(v);
function row(k,v){{if(v==null||v==="")return"";const s=val(v);const link=/^0x[0-9a-f]{{40}}$/.test(s)?
 `<a href="https://etherscan.io/address/${{s}}" target="_blank" rel="noopener">${{s}}</a>`:s.replace(/[&<>]/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;"}}[c]));
 return `<tr><td>${{k.replace(/_/g," ")}}</td><td>${{link}}</td></tr>`}}
cy.on("tap","node",ev=>{{const d=ev.target.data();const nb=ev.target.closedNeighborhood();cy.elements().addClass("faded");nb.removeClass("faded");
 let h=`<b>${{d.label}}</b> <span class="muted">${{d.kind}}</span><table>`+Object.entries(d.details).filter(([k])=>!k.startsWith("_")).map(([k,v])=>row(k,v)).join("");
 const out=ev.target.outgoers("edge").map(e=>row("→ "+e.data("rel"),cy.getElementById(e.data("target")).data("label")+(e.data("amount")?" · "+fmt(e.data("amount"))+" "+(e.data("unit")||""):""))).join("");
 const inc=ev.target.incomers("edge").map(e=>row("← "+e.data("rel"),cy.getElementById(e.data("source")).data("label")+(e.data("amount")?" · "+fmt(e.data("amount"))+" "+(e.data("unit")||""):""))).join("");
 document.getElementById("info").innerHTML=h+out+inc+"</table>"}});
cy.on("tap","edge",ev=>{{const d=ev.target.data();cy.elements().addClass("faded");ev.target.removeClass("faded");ev.target.connectedNodes().removeClass("faded");
 document.getElementById("info").innerHTML=`<b>${{cy.getElementById(d.source).data("label")}}</b> → ${{d.rel}} → <b>${{cy.getElementById(d.target).data("label")}}</b><table>`+
 row("amount",d.amount?fmt(d.amount)+" "+(d.unit||""):"")+Object.entries(d.details||{{}}).map(([k,v])=>row(k,v)).join("")+"</table>"}});
cy.on("tap",ev=>{{if(ev.target===cy){{cy.elements().removeClass("faded");document.getElementById("info").textContent="Click a node or an edge."}}}});
document.querySelectorAll("[data-kind]").forEach(cb=>cb.addEventListener("change",()=>{{
 cy.nodes(`[kind="${{cb.dataset.kind}}"]`).style("display",cb.checked?"element":"none")}}));
document.getElementById("q").addEventListener("input",e=>{{const q=e.target.value.toLowerCase();cy.elements().removeClass("faded");if(!q)return;
 const hit=cy.nodes().filter(n=>(n.data("label")+" "+n.id()+" "+JSON.stringify(n.data("details"))).toLowerCase().includes(q));
 cy.elements().addClass("faded");hit.closedNeighborhood().removeClass("faded")}});
document.getElementById("fit").onclick=()=>cy.fit(undefined,30);
document.getElementById("lay").onclick=relayout;
</script></body></html>"""


def to_dict(g: Graph, title: str, subtitle: str) -> dict:
    """The graph as plain JSON-ready data. `write` persists this; the API serves it."""
    return {"title": title, "subtitle": subtitle, "nodes": list(g.nodes.values()), "edges": g.edges}


def write(g: Graph, out_html: Path, title: str, subtitle: str) -> tuple[Path, Path]:
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(to_html(g, title, subtitle))
    out_json = out_html.with_suffix(".json")
    out_json.write_text(json.dumps(to_dict(g, title, subtitle), indent=1, default=str))
    return out_html, out_json


def subtitle_for(block: int) -> str:
    return (
        f"Ethereum mainnet, read at block {block:,} "
        f"({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}). "
        "Positions found with the Morpho API; amounts, parameters, oracles and roles read on-chain."
    )
