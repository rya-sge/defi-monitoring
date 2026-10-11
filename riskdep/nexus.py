"""Nexus Mutual, keyless: the yearly price of cover on the protocols behind a vault's collateral, as an outside view
next to the breakeven probability (plan 2026-10-11-breakeven, D145–D146; docs/risk-assessment/outside-providers.md).

Two public responses: `GET /v2/products` (names, types) and `GET /v2/capacity` (yearly price range and capacity per
product). `registry.json` `nexus.products` maps a token address to the product that covers its protocol. A price is an
expected payout plus a loading, so it implies a yearly probability of the covered event of price ÷ (loading × severity),
given for the registry's loading range. Shown, never used in a verdict. Optional: None when Nexus cannot be read.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import sources as S
from .discover import REGISTRY

API = "https://api.nexusmutual.io/v2"
N = REGISTRY["nexus"]


@dataclass
class Cover:
    product: int
    name: str
    kind: str  # "protocol": pays on an exploit of the protocol; "depeg": pays when the token loses its peg
    price: tuple[float, float]  # yearly price range, as a fraction of the amount covered
    capacity_usd: float | None  # what can still be covered, in USDC (asset 6), None when not quoted


def _slim_products(d) -> list[dict]:
    return [{"id": p["id"], "name": p["name"], "type": p.get("productType")} for p in d]


def _slim_capacity(d) -> list[dict]:
    out = []
    for c in d:
        usdc = next((a for a in c.get("availableCapacity", []) if a.get("assetId") == 6), None)
        out.append(
            {
                "id": c["productId"],
                "min": float(c.get("minAnnualPrice") or 0),
                "max": float(c.get("maxAnnualPrice") or 0),
                "usdc": int(usdc["amount"]) / 1e6 if usdc else None,
            }
        )
    return out


def covers(products: list[dict], capacity: list[dict], tokens: list[str]) -> list[Cover]:
    """Pure: the products the registry maps to these tokens (addresses, any order), each once, if Nexus sells it now."""
    names = {p["id"]: p["name"] for p in products}
    cap = {c["id"]: c for c in capacity}
    out, seen = [], set()
    for t in tokens:
        e = N["products"].get(t.lower())
        if not e or e["product"] in seen or e["product"] not in cap or not cap[e["product"]]["max"]:
            continue
        seen.add(e["product"])
        c = cap[e["product"]]
        out.append(
            Cover(e["product"], names.get(e["product"], str(e["product"])), e["kind"], (c["min"], c["max"]), c["usdc"])
        )
    return out


def implied(cover: Cover, severity: float) -> tuple[float, float]:
    """D146, pure: the yearly probability of the covered event the price implies, low and high: price ÷ (loading ×
    severity), with the registry's loading range (a price includes capital cost and margin)."""
    lo, hi = N["loading"]
    s = max(severity, 1e-9)
    return min(1.0, cover.price[0] / (hi * s)), min(1.0, cover.price[1] / (lo * s))


def outside_line(cover: Cover, severity: float) -> str:
    lo, hi = implied(cover, severity)
    what = "an exploit of the protocol" if cover.kind == "protocol" else "the token losing its peg"
    price = (
        f"{cover.price[0]:.2%}" if cover.price[0] == cover.price[1] else f"{cover.price[0]:.2%}–{cover.price[1]:.2%}"
    )
    cap = f", capacity {cover.capacity_usd:,.0f} USDC" if cover.capacity_usd is not None else ""
    return f"Nexus {cover.name} cover {price}/yr{cap}: implies {lo:.1%}–{hi:.1%}/yr for {what} at this severity; " + (
        "it pays on that, not on an issuer's markdown or a borrower's default"
        if cover.kind == "protocol"
        else "it pays on a depeg, not on a NAV markdown"
    )


# --- I/O


def load(f: S.Fetcher) -> tuple[list[dict], list[dict]] | None:
    try:
        return f.get_json(f"{API}/products", transform=_slim_products), f.get_json(
            f"{API}/capacity", transform=_slim_capacity
        )
    except (S.CacheMiss, S.SourceError, KeyError, TypeError, ValueError):
        return None
