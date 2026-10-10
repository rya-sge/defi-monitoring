"""Drain threshold of a market whose oracle does not follow the market (plan 2026-10-10-drain-threshold, D69–D74).

When the collateral trades at a discount δ below its oracle price, anyone can buy it, post it and borrow LLTV × the
oracle value: per unit of debt the collateral costs (1 − δ)(1 + c) / LLTV, with c the cost of buying at size. That
pays as soon as

  δ > d* = 1 − LLTV / (1 + c)                        (Team 2: d* ≈ 1 − LLTV + c)

and the arbitrage then borrows every unit the market can lend in one block. A market-tracking oracle keeps δ near 0
(the depeg liquidates borrowers instead); an exchange-rate, linear-discount or fixed oracle lets δ grow with the
depeg. δ is measured, whatever the oracle: oracle price against DefiLlama's collateral ÷ loan price (D58).

  drainable    the market's free liquidity + what the Vault V2 Public Allocator can move into it (D71)
  bad debt     drained × max(0, 1 − (1 − δ) / LLTV)  once the collateral is worth less than the debt
"""

from __future__ import annotations

from dataclasses import dataclass

from . import sources as S
from .discover import REGISTRY
from .rules import Alert
from .vault import WAD, _call, _uint, cap_ids

W = REGISTRY["watch"]
PUBLIC_ALLOCATOR = (
    "0x00b8e1509398ed692c3f326cbaf1694f9a881e27"  # BluePublicAllocator, Ethereum (Morpho docs, addresses)
)


@dataclass
class PaConfig:
    """The vault's Public Allocator settings (D71); `enabled` is False when the allocator has no role on the vault."""

    enabled: bool = False
    known: bool = False  # False when the settings could not be read (then no inflow is counted)
    can_pull_idle: bool = False
    active_adapters: set[str] | None = None
    cap: dict[str, int] | None = None  # market id -> absoluteCap of the Public Allocator
    can_pull: dict[str, bool] | None = None  # market id -> can be a source


@dataclass
class MarketDrain:
    id: str
    label: str
    lltv: float
    d_star: float
    discount: float | None  # δ, None when no independent price
    liquidity: int  # the market's free liquidity
    pa_inflow: int  # what the Public Allocator can add
    vault_share: float  # the vault's share of the market's supply
    is_liquidity_market: bool = False

    @property
    def drainable(self) -> int:
        return self.liquidity + self.pa_inflow

    @property
    def margin(self) -> float | None:
        return None if self.discount is None else self.d_star - self.discount

    @property
    def open(self) -> bool:
        return self.discount is not None and self.discount >= self.d_star

    def bad_debt(self, discount: float | None = None) -> int:
        d = self.discount if discount is None else discount
        if d is None:
            return 0
        return int(self.drainable * max(0.0, 1 - (1 - d) / self.lltv))


# --- pure


def d_star(lltv: float, cost: float) -> float:
    return 1 - lltv / (1 + cost)


def discount(divergence: float | None) -> float | None:
    """δ from the oracle's divergence g = oracle ÷ market − 1: the market trades δ = g / (1 + g) below the oracle."""
    return None if divergence is None else divergence / (1 + divergence)


def headroom(cap: tuple[int, int, int] | None, total_assets: int) -> int:
    """How much more a Vault V2 cap id can take: min(absolute, relative × total) − allocation; WAD means no limit."""
    if cap is None:
        return 0
    alloc, absolute, relative = cap
    limit = absolute if relative >= WAD else min(absolute, relative * total_assets // WAD)
    return max(0, limit - alloc)


def pa_inflow(view, st, pa: PaConfig, market_id: str) -> int:
    """D71: what anyone can move into `market_id` through the Public Allocator: bounded by the allocator's cap, the
    vault's three cap ids, and the sources it may pull (idle if allowed, other markets' withdrawable part)."""
    if not pa.enabled:
        return 0
    dest = next(((a, mp) for a in view.adapters for mp in a.markets.values() if mp.id == market_id), None)
    if dest is None or dest[0].address not in (pa.active_adapters or set()):
        return 0
    adapter, mp = dest
    ms = st.markets.get(market_id)
    alloc = ms.vault_assets if ms else 0
    room = max(0, (pa.cap or {}).get(market_id, 0) - alloc)
    for cid in cap_ids(adapter.address, mp).values():
        room = min(room, headroom(st.caps.get(cid), st.total_assets))
    sources = st.idle if pa.can_pull_idle else 0
    for a in view.adapters:
        if a.address not in (pa.active_adapters or set()):
            continue
        for other in a.markets.values():
            if other.id != market_id and (pa.can_pull or {}).get(other.id) and other.id in st.markets:
                sources += st.markets[other.id].withdrawable
    return min(room, sources)


def assess(
    before: dict[str, MarketDrain], after: dict[str, MarketDrain], vault: str, unit: int, symbol: str, block: int
) -> list[Alert]:
    """D72: warn when a market's discount comes within `drain_margin` of d*; critical when it reaches d*. On
    crossing, per market."""
    margin = W["drain_margin"]

    def level(m: MarketDrain | None) -> int:
        if m is None or m.discount is None:
            return 0
        return 2 if m.open else (1 if m.margin <= margin else 0)

    out = []
    for mid, m in after.items():
        l1 = level(m)
        if l1 <= level(before.get(mid)):
            continue
        mine = int(m.drainable * m.vault_share)
        detail = (
            f"the collateral trades {m.discount:.2%} below the oracle; the drain pays from {m.d_star:.2%} "
            f"(LLTV {m.lltv:.1%}, buying cost {W['drain_buy_cost']:.1%}). An arbitrageur would buy it, post it and "
            f"borrow {m.drainable / unit:,.0f} {symbol}, the market's free liquidity"
            + (f" plus {m.pa_inflow / unit:,.0f} the Public Allocator can move in" if m.pa_inflow else "")
            + f"; the vault supplies {m.vault_share:.0%} of it, so about {mine / unit:,.0f} {symbol} of the vault "
            "would leave as loans that are never repaid"
        )
        if m.open and m.bad_debt():
            detail += f", with {m.bad_debt() / unit:,.0f} {symbol} of bad debt at today's discount"
        out.append(
            Alert(
                "critical" if l1 == 2 else "warn",
                block,
                None,
                "DrainWindow",
                (f"Drain of {m.label} pays now" if l1 == 2 else f"{m.label} is {m.margin:.2%} from the drain threshold")
                + f" ({vault})",
                detail
                + (
                    ". Exit before it happens: once drained, the market's liquidity is gone"
                    if l1 == 1
                    else ". The market's liquidity can be taken in one block"
                ),
                -mine / unit if l1 == 2 else None,
                {"market": mid, "discount": m.discount, "d_star": m.d_star, "drainable": m.drainable},
            )
        )
    return out


def table(lines, drains: dict[str, MarketDrain], unit: int, symbol: str, pa: PaConfig) -> None:
    lines(
        "  drain threshold (oracle above the market price: a fixed or exchange-rate oracle lets the gap grow"
        + (
            "; Public Allocator enabled"
            if pa.enabled
            else "; Public Allocator not enabled on this vault"
            if pa.known
            else "; Public Allocator settings not read: its inflow is not counted"
        )
        + "):"
    )
    lines(f"    {'market':<42} {'below oracle':>12} {'d*':>7} {'margin':>8} {'drainable':>16} {'vault share':>11}")
    rows = sorted(drains.values(), key=lambda m: (m.margin is None, m.margin if m.margin is not None else 0))
    for m in rows:
        below = "n/a" if m.discount is None else f"{m.discount:+.2%}"
        margin = "n/a" if m.margin is None else f"{m.margin:.2%}"
        tag = " [liquidity]" if m.is_liquidity_market else ""
        lines(
            f"    {(m.label + tag)[:42]:<42} {below:>12} {m.d_star:>7.2%} {margin:>8} "
            f"{m.drainable / unit:>12,.0f} {symbol:<3} {m.vault_share:>11.0%}"
        )


# --- I/O


def read_pa(f: S.Fetcher, view, block) -> PaConfig:
    """The Public Allocator's settings for a Vault V2 (D71), read on-chain."""
    v, pa = view.address, PUBLIC_ALLOCATOR
    mlist = [(a, mp) for a in view.adapters if a.kind == "market" for mp in a.markets.values()]
    calls = [_call(v, "isAllocator(address)", ["address"], [pa]), _call(pa, "vaultData(address)", ["address"], [v])]
    calls += [
        _call(pa, "isActiveAdapter(address,address)", ["address", "address"], [v, a.address]) for a in view.adapters
    ]
    for a, mp in mlist:
        cid = bytes.fromhex(cap_ids(a.address, mp)["market"][2:])
        calls += [
            _call(pa, "absoluteCap(address,bytes32)", ["address", "bytes32"], [v, cid]),
            _call(pa, "canPullFromMarket(address,bytes32)", ["address", "bytes32"], [v, cid]),
        ]
    try:
        res = S.rpc_batch(f, calls, block)
    except (S.SourceError, S.CacheMiss):
        return PaConfig()  # unknown: e.g. a replay older than the free RPC's state window
    it = iter(res)
    is_alloc, data = _uint(next(it)), next(it)
    active = {a.address for a in view.adapters if _uint(next(it))}
    cap, pull = {}, {}
    for _, mp in mlist:
        cap[mp.id], pull[mp.id] = _uint(next(it)) or 0, bool(_uint(next(it)))
    can_idle = bool(int(data[2:66], 16)) if data and len(data) >= 66 else False
    return PaConfig(bool(is_alloc), True, can_idle, active, cap, pull)


def drains(view, st, markets: dict, divergence: dict[str, float | None], pa: PaConfig) -> dict[str, MarketDrain]:
    """Pure once `pa` is read: one MarketDrain per watched market of the vault (`market_risk.vault_markets`)."""
    cost = W["drain_buy_cost"]
    out = {}
    for mid, info in markets.items():
        ms = st.markets.get(mid)
        if ms is None:
            continue
        share = ms.vault_assets / ms.total_supply_assets if ms.total_supply_assets else 0.0
        out[mid] = MarketDrain(
            mid,
            info.label,
            info.lltv,
            d_star(info.lltv, cost),
            discount(divergence.get(mid)),
            ms.liquidity,
            pa_inflow(view, st, pa, mid),
            share,
            mid == view.liquidity_market,
        )
    return out


def drained_vault_liquidity(view, st, ds: dict[str, MarketDrain]) -> int:
    """What a drain of the open markets removes from the vault's exit capacity: their withdrawable part and what the
    Public Allocator would pull into them (D73)."""
    return sum(st.markets[mid].withdrawable + m.pa_inflow for mid, m in ds.items() if m.open and mid in st.markets)


class VaultDrain:
    """Drain thresholds of one vault's markets, used by both watches. Discounts come from the oracle prices of each
    state read and DefiLlama's prices, re-read every `drain_check_every_blocks` (an `admin.AdminWatch` holds them)."""

    def __init__(self, f, view, block):
        self.view = view
        self.pa = read_pa(f, view, block)
        self.state: dict[str, MarketDrain] = {}

    def compute(self, f, st, markets, aw, block) -> dict[str, MarketDrain]:
        raw = {mid: st.markets[mid].oracle_price for mid in markets if mid in st.markets}
        div = aw.divergence_at(raw, aw.fresh_prices(f, block, W["drain_check_every_blocks"]))
        return drains(self.view, st, markets, div, self.pa)

    def startup(self, lines, f, st, markets, aw, block) -> list[Alert]:
        ds = self.compute(f, st, markets, aw, block)
        table(lines, ds, 10**self.view.decimals, self.view.asset_symbol, self.pa)
        return self._assess(ds, block)

    def step(self, f, st, markets, aw, block, refresh: bool) -> list[Alert]:
        if refresh:
            self.pa = read_pa(f, self.view, st.block)
        return self._assess(self.compute(f, st, markets, aw, block), block)

    def _assess(self, ds, block) -> list[Alert]:
        alerts = assess(self.state, ds, self.view.name, 10**self.view.decimals, self.view.asset_symbol, block)
        self.state = ds
        return alerts

    def drained(self, st) -> int:
        return drained_vault_liquidity(self.view, st, self.state)
