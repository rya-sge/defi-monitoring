"""Per-layer incident priors.

Frequency of exploits: DefiLlama hack record, per DefiLlama category (D9).
Severity and market (non-exploit) events: registry.json, each with its basis (D10).
"""

from __future__ import annotations

from dataclasses import dataclass

from . import clock
from . import sources as S
from .discover import REGISTRY, Position


@dataclass
class Prior:
    event: str  # id of the event, e.g. "issuer_depeg"
    node: str  # graph node it hits
    layer: str  # human label
    p_year: float
    a: float  # Beta severity
    b: float
    basis: str
    recovery: float = 0.0

    @property
    def mean_severity(self) -> float:
        return self.a / (self.a + self.b)


def _tier(tvl: float | None) -> int:
    t = REGISTRY["frequency"]["tiers_usd"]
    tvl = tvl or 0
    return 0 if tvl < t[0] else 1 if tvl < t[1] else 2


TIER_LABEL = {0: "< $10M", 1: "$10M–$100M", 2: "≥ $100M"}


def hack_stats(f: S.Fetcher) -> dict:
    """Counts behind the frequency model: per category (≥ $1M) and per TVL tier."""
    cfg = REGISTRY["frequency"]
    protocols = S.llama_protocols(f)
    since = clock.now() - cfg["years"] * 365 * 86400
    hacks = [h for h in S.llama_hacks(f) if h.get("date", 0) >= since]
    by_id = {str(p.get("id")): p for p in protocols}
    cat_n: dict[str, int] = {}
    tier_n = {0: 0, 1: 0, 2: 0}
    for p in protocols:
        tvl = p.get("tvl") or 0
        if tvl >= cfg["min_tvl_usd"]:
            if p.get("category"):
                cat_n[p["category"]] = cat_n.get(p["category"], 0) + 1
            tier_n[_tier(tvl)] += 1
    cat_h: dict[str, int] = {}
    tier_h = {0: 0, 1: 0, 2: 0}
    for h in hacks:
        p = by_id.get(str(h.get("defillamaId")))
        if not p or (p.get("tvl") or 0) < cfg["min_tvl_usd"]:
            continue
        if p.get("category"):
            cat_h[p["category"]] = cat_h.get(p["category"], 0) + 1
        tier_h[_tier(p.get("tvl"))] += 1
    yrs = cfg["years"]
    overall = sum(cat_h.values()) / (sum(cat_n.values()) * yrs)
    return {
        "years": yrs,
        "hacks": hacks,
        "protocols": protocols,
        "cat_n": cat_n,
        "cat_h": cat_h,
        "tier_n": tier_n,
        "tier_h": tier_h,
        "overall": overall,
        "tier_rate": {t: tier_h[t] / (tier_n[t] * yrs) if tier_n[t] else overall for t in tier_n},
        "cat_rate": {c: cat_h.get(c, 0) / (n * yrs) for c, n in cat_n.items()},
    }


def _protocol(st: dict, slug: str) -> dict | None:
    for p in st["protocols"]:
        if p.get("slug") == slug:
            return p
    return None


def _age_factor(listed_at: int | None) -> tuple[float, str]:
    af = REGISTRY["frequency"]["age_factor"]
    if not listed_at:
        return af["gt_3y"], "listed before DefiLlama recorded dates"
    years = (clock.now() - listed_at) / (365 * 86400)
    if years < 1:
        return af["lt_1y"], f"listed {years:.1f}y ago"
    if years < 3:
        return af["1y_3y"], f"listed {years:.1f}y ago"
    return af["gt_3y"], f"listed {years:.1f}y ago"


def exploit_p_year(st: dict, slug: str | None, category: str) -> tuple[float, str]:
    cfg = REGISTRY["frequency"]
    proto = _protocol(st, slug) if slug else None
    if proto and proto.get("category"):
        category = proto["category"]
    tier = _tier(proto.get("tvl") if proto else 0)
    base = st["tier_rate"][tier]
    lo, hi = cfg["category_multiplier_clip"]
    cat_rate = st["cat_rate"].get(category)
    mult = 1.0 if cat_rate is None else min(hi, max(lo, cat_rate / st["overall"]))
    factor, age = _age_factor(proto.get("listedAt") if proto else None)
    p = min(cfg["cap"], max(cfg["floor"], base * mult * factor))
    note = (
        f"tier {TIER_LABEL[tier]}: {st['tier_h'][tier]} hacks / {st['tier_n'][tier]} protocols / {st['years']}y "
        f"= {base:.2%}/yr; × category '{category}' {mult:.2f} "
        f"({st['cat_h'].get(category, 0)} hacks / {st['cat_n'].get(category, 0)} protocols); "
        f"× age {factor} ({age}) → {p:.2%}/yr"
    )
    if not proto:
        note = f"protocol '{slug}' not found on DefiLlama, smallest tier assumed; " + note
    return p, note


def layer_priors(f: S.Fetcher, pos: Position) -> list[Prior]:
    st = hack_stats(f)
    g = pos.graph
    out: list[Prior] = []

    ch = REGISTRY["chain"]["ethereum"]
    out.append(
        Prior(
            "chain",
            "chain:ethereum",
            "Ethereum (settlement)",
            ch["p_year"],
            ch["severity"]["a"],
            ch["severity"]["b"],
            ch["basis"],
        )
    )

    und = pos.underlying_address
    reg = REGISTRY["issuers"].get(und) or REGISTRY["unknown_issuer"]
    name = f"{pos.underlying_symbol} issuer" + (f" ({reg['issuer']})" if "issuer" in reg else "")
    dp = reg["depeg"]
    out.append(
        Prior(
            "issuer_depeg",
            f"issuer:{und}",
            f"{name}: depeg",
            dp["p_year"],
            dp["severity"]["a"],
            dp["severity"]["b"],
            dp["basis"],
            recovery=dp["recovery"],
        )
    )
    p, note = exploit_p_year(st, reg.get("llama_slug"), reg.get("category", "Yield"))
    out.append(
        Prior(
            "issuer_hack",
            f"issuer:{und}",
            f"{name}: exploit / loss of backing",
            p,
            reg["hack"]["severity"]["a"],
            reg["hack"]["severity"]["b"],
            f"{note}. Severity: {reg['hack']['basis']}",
        )
    )

    pr = REGISTRY["protocols"]["pendle"]
    p, note = exploit_p_year(st, pr["llama_slug"], pr["category"])
    out.append(
        Prior(
            "amm",
            f"amm:{pos.pendle_market}",
            "Pendle market / SY adapter exploit",
            p,
            pr["severity"]["a"],
            pr["severity"]["b"],
            f"{note}. Severity: {pr['basis']}",
        )
    )

    lend = [n for n, a in g.nodes(data=True) if a["kind"] == "lending"]
    orc = [n for n, a in g.nodes(data=True) if a["kind"] == "oracle"]
    if lend:
        mr = REGISTRY["protocols"]["morpho-blue"]
        p, note = exploit_p_year(st, mr["llama_slug"], mr["category"])
        out.append(
            Prior(
                "lending",
                lend[0],
                "Morpho Blue exploit",
                p,
                mr["severity"]["a"],
                mr["severity"]["b"],
                f"{note}. Severity: {mr['basis']}",
            )
        )
    if orc:
        out.append(oracle_prior(orc[0], g.nodes[orc[0]].get("verified"), st))
    return out


def oracle_prior(node: str, verified: bool | None, st: dict) -> Prior:
    """Pure: the oracle layer's prior. `verified` comes from Etherscan (D68): True, False, or None when it could not
    be checked, which is treated as unverified (conservative)."""
    o = REGISTRY["oracle"]
    n_oracle = sum(1 for h in st["hacks"] if h.get("technique") in o["techniques"])
    users = st["cat_n"].get("Lending", 0) + st["cat_n"].get("CDP", 0)
    base = n_oracle / (max(1, users) * st["years"])
    factor = 1.0 if verified is True else o["unverified_factor"]
    status = {True: "verified", False: "implementation unverified", None: "verification not checked"}[verified]
    p = min(REGISTRY["frequency"]["cap"], max(o["p_year_floor"], base * factor))
    return Prior(
        "oracle",
        node,
        "Oracle misprice / misconfiguration",
        p,
        o["severity"]["a"],
        o["severity"]["b"],
        f"{n_oracle} misconfigured/stale-oracle hacks / {users} Lending+CDP protocols / {st['years']}y "
        f"= {base:.2%}/yr; × {factor} ({status} on Etherscan) → {p:.2%}/yr. Severity: {o['basis']}",
    )
