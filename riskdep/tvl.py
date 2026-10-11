"""TVL concentration: how much of DeFi, and of its category, each protocol in a dependency graph holds (plan
2026-10-11-feed-quality, D158–D160; the brief's "protocols concentrating a large share of on-chain TVL").

DefiLlama's `/protocols`, already read for the incident base rates, gives each protocol's TVL and category. Which
protocol a graph node belongs to is data: `registry.json` `tvl.tokens` maps issuer tokens to DefiLlama slugs; every
Morpho Blue market is `tvl.blue_markets`, every Pendle PT `tvl.pt_assets`. Pure functions; the list is passed in.
"""

from __future__ import annotations

from dataclasses import dataclass

from .discover import REGISTRY

T = REGISTRY["tvl"]


@dataclass
class Concentration:
    slug: str
    name: str
    category: str
    tvl_usd: float
    share_defi: float
    share_category: float
    rank: int  # in its category, 1 = largest
    concentrated: bool

    @property
    def text(self) -> str:
        if not self.tvl_usd:
            return f"{self.name}: no TVL reported by DefiLlama"
        flag = ": CONCENTRATED" if self.concentrated else ""
        return (
            f"{self.name}: {self.tvl_usd / 1e6:,.0f}M USD, {self.share_defi:.2%} of DeFi, {self.share_category:.1%} of "
            f"{self.category} (#{self.rank}){flag}"
        )


def concentration(protocols: list[dict], slug: str) -> Concentration | None:
    """D159, pure: one protocol's TVL against all of DeFi and its category; None when DefiLlama does not list it."""
    p = next((x for x in protocols if x.get("slug") == slug), None)
    if p is None:
        return None
    total = sum(x.get("tvl") or 0 for x in protocols)
    peers = sorted((x.get("tvl") or 0 for x in protocols if x.get("category") == p.get("category")), reverse=True)
    tvl = p.get("tvl") or 0
    share, cat = (tvl / total if total else 0.0), (tvl / sum(peers) if sum(peers) else 0.0)
    return Concentration(
        slug,
        p.get("name") or slug,
        p.get("category") or "?",
        tvl,
        share,
        cat,
        peers.index(tvl) + 1 if tvl in peers else len(peers),
        share >= T["warn_share_defi"] or (cat >= T["warn_share_category"] and sum(peers) >= T["warn_category_min_usd"]),
    )


def slug_of(node: dict) -> str | None:
    """D158, pure: the DefiLlama slug a graph node belongs to, if any."""
    if node["kind"] == "Pool" and node["details"].get("market_id"):
        return T["blue_markets"]
    if node["kind"] == "Asset":
        if node["label"].startswith("PT-"):
            return T["pt_assets"]
        return T["tokens"].get(node["id"])
    return None
