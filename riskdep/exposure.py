"""Worst-case exposure up to the caps (plan 2026-10-11-gapv2-fixes, D243; GAPV2 G1).

Exposure was measured from today's allocation. In a Vault V2 an allocator can move capital into any enabled market up
to its caps at once, with no timelock (`VaultV2.allocate`). A market's most is the smallest of its three cap ids
(`vault.cap_ids`: adapter, collateral, market), each min(absoluteCap, relativeCap × totalAssets), a relative cap of
WAD meaning none. Over several markets the shared ids bind too: every market on one collateral shares the collateral
id, every market of an adapter the adapter id, so a sum caps each group by its shared id, and the total by the vault's
assets. Pure: the caps are `VaultState.caps`.
"""

from __future__ import annotations

from .vault import WAD

KEYS = ("adapter", "collateral", "market")


def limit(cap: tuple[int, int, int] | None, total: int) -> int:
    """One cap id's limit: min(absolute, relative × total); an id never set allows nothing."""
    if cap is None:
        return 0
    _, absolute, relative = cap
    return absolute if relative >= WAD else min(absolute, relative * total // WAD)


def market_limit(ids: dict[str, str], caps: dict, total: int) -> int:
    """The most the vault can hold in one market: the smallest of its three ids' limits."""
    return min(limit(caps.get(ids[k]), total) for k in KEYS)


def group_limit(markets: list[dict[str, str]], caps: dict, total: int) -> int:
    """The most the vault can hold across `markets` (each its cap ids): per-market limits, each collateral group
    capped by its collateral id, each adapter group by its adapter id, and the whole by the vault's assets."""
    by_adapter: dict[str, dict[str, int]] = {}
    for ids in markets:
        coll = by_adapter.setdefault(ids["adapter"], {})
        coll[ids["collateral"]] = coll.get(ids["collateral"], 0) + market_limit(ids, caps, total)
    out = 0
    for adapter, colls in by_adapter.items():
        within = sum(min(v, limit(caps.get(c), total)) for c, v in colls.items())
        out += min(within, limit(caps.get(adapter), total))
    return min(out, total)
