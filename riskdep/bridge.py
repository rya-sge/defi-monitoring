"""Bridges: how many unbacked tokens a bridge can mint on Ethereum, and the markdown they cause (plan
2026-10-11-bridges, D250–D252; GAP C6).

A token bridged by burn-and-mint is minted on Ethereum when a message from another chain says it was burnt there. A
forged message, or a compromised bridge, mints tokens with nothing behind them: they dilute every holder, and an
attacker can post them as collateral at the oracle's price and borrow what the markets can lend. What bounds it:

  CCIP (Chainlink)   each pool accepts messages only from the remote pools it lists, through an inbound rate limit
                     per chain: a bucket of `capacity` tokens refilled at `rate` per second (`TokenPool`,
                     `RateLimiter`). Within `hours`, at most tokens + rate × hours × 3600 per open lane.
  LayerZero (OFT)    an app accepts messages only from the peer it set for a chain (`OAppCore.peers`); no peer, no lane.

The markdown is the dilution, minted / (supply + minted), against the Ethereum supply only: the backing also covers
the tokens on the other chains, so the figure is an upper bound. Read on-chain at a block from the pinned tokens and
pools (`registry.json` `bridge`), keyless; recorded under fixtures/replay/bridge/.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eth_abi import decode

from . import roles as RL
from . import sources as S
from .discover import REGISTRY
from .vault import _call, _uint

K = REGISTRY["bridge"]


@dataclass
class Lane:
    pool: str  # the CCIP pool, or the LayerZero app
    version: str
    chain: str
    open: bool  # a remote pool or a peer is set: messages from that chain are accepted
    limited: bool = False
    tokens: float = 0.0  # what the inbound bucket allows at once
    capacity: float = 0.0
    rate: float = 0.0  # refill, tokens per second


@dataclass
class Route:
    symbol: str
    kind: str  # ccip | layerzero
    token: str
    supply: float  # on Ethereum
    lanes: list[Lane]
    holders: list = field(default_factory=list)  # roles.Holder: who can open a lane or lift a limit

    def open_lanes(self) -> list[Lane]:
        return [x for x in self.lanes if x.open]

    def lines(self) -> list[str]:
        name = "CCIP" if self.kind == "ccip" else "LayerZero"
        lanes = self.open_lanes()
        out = [
            f"{self.symbol} is bridged by {name} ({self.supply / 1e6:,.1f}M on Ethereum): "
            + (
                "; ".join(
                    f"from {x.chain}, "
                    + (f"{x.tokens / 1e6:,.2f}M at once, then {x.rate:,.0f} a second" if x.limited else "no rate limit")
                    for x in lanes
                )
                if lanes
                else "no lane open today"
            )
        ]
        out += [f"{', '.join(h.roles)}: {h.label}" for h in self.holders]
        return out


def minted(route: Route, hours: float) -> float | None:
    """D251, pure: the most the open lanes can mint within `hours`; None when one has no rate limit (unbounded)."""
    lanes = route.open_lanes()
    if any(not x.limited for x in lanes):
        return None
    return sum(x.tokens + x.rate * hours * 3600 for x in lanes)


def markdown(route: Route, hours: float) -> dict:
    """D251, pure: the dilution of the unbacked mint within `hours`, with its words; 0 when no lane is open."""
    lanes = route.open_lanes()
    if not lanes:
        who = "; ".join(f"its {', '.join(h.roles)}, {h.label}" for h in route.holders)
        return {
            "minted": 0.0,
            "markdown": 0.0,
            "text": f"{route.symbol}: no bridge lane is open, nothing can be minted through it today"
            + (f" ({who}, can open one at once)" if who else ""),
        }
    m = minted(route, hours)
    if m is None:
        return {
            "minted": None,
            "markdown": 0.99,
            "text": f"{route.symbol}'s bridge has a lane with no rate limit: what it can mint is unbounded",
        }
    d = m / (route.supply + m) if route.supply + m else 0.0
    return {
        "minted": m,
        "markdown": d,
        "text": f"a forged bridge message mints {m / 1e6:,.1f}M unbacked {route.symbol} within {hours:g} h "
        f"(the rate limits of the lanes from {', '.join(x.chain for x in lanes)}); posted at the oracle's price, they "
        f"borrow the free liquidity of every {route.symbol} market, a loss for the lenders once the issuer refuses "
        f"them; if it honoured them instead, every holder would be diluted {d:.2%} (against the "
        f"{route.supply / 1e6:,.1f}M on Ethereum, an upper bound)",
    }


def parse(items: list[str] | None) -> tuple[list[str], list[tuple[str, float]]]:
    """D251, pure: split `bridge=<symbol>[:<hours>]` from the other shocks."""
    rest, out = [], []
    for it in items or []:
        name, _, value = it.partition("=")
        if name.strip() != "bridge":
            rest.append(it)
            continue
        sym, _, h = value.partition(":")
        try:
            hours = float(h) if h else float(K["response_hours"])
        except ValueError:
            raise ValueError(f"'{it}': write bridge=<token>[:<hours>]") from None
        if sym not in K["tokens"] or hours <= 0:
            raise ValueError(f"'{it}': write bridge=<{'|'.join(K['tokens'])}>[:<hours>], hours above 0")
        out.append((sym, hours))
    return rest, out


# --- I/O


def _bucket(raw: bytes, decimals: int) -> tuple[bool, float, float, float]:
    tokens, _, enabled, capacity, rate = decode(["uint128", "uint32", "bool", "uint128", "uint128"], raw[:160])
    return enabled, tokens / 10**decimals, capacity / 10**decimals, rate / 10**decimals


def _ccip(f: S.Fetcher, sym: str, t: dict, block: int) -> Route:
    """D250: each pool's version, remote chains, remote pools and inbound bucket; its owner and rate-limit admin."""
    dec, lanes, admins = t["decimals"], [], {}
    for pool in t["pools"]:
        r = S.rpc_batch(f, [_call(pool, s) for s in ("typeAndVersion()", "getSupportedChains()", "owner()")], block)
        version = decode(["string"], bytes.fromhex(r[0][2:]))[0]
        v2 = version.split()[-1].startswith("2.")
        chains = decode(["uint64[]"], bytes.fromhex(r[1][2:]))[0]
        admins.setdefault("0x" + r[2][-40:], []).append("pool owner")
        a = S.rpc_batch(f, [_call(pool, "getDynamicConfig()" if v2 else "getRateLimitAdmin()")], block)[0]
        rl = "0x" + (a[2 + 64 : 2 + 128] if v2 else a[2:])[-40:]
        if int(rl, 16):
            admins.setdefault(rl, []).append("rate-limit admin")
        for c in chains:
            limit = (
                _call(pool, "getCurrentRateLimiterState(uint64,bool)", ["uint64", "bool"], [c, False])
                if v2
                else _call(pool, "getCurrentInboundRateLimiterState(uint64)", ["uint64"], [c])
            )
            q = S.rpc_batch(f, [_call(pool, "getRemotePools(uint64)", ["uint64"], [c]), limit], block)
            remote = decode(["bytes[]"], bytes.fromhex(q[0][2:]))[0]
            raw = bytes.fromhex(q[1][2:])
            enabled, tokens, capacity, rate = _bucket(raw[160:] if v2 else raw, dec)  # v2: (outbound, inbound)
            lanes.append(
                Lane(pool, version, t["chains"].get(str(c), str(c)), bool(remote), enabled, tokens, capacity, rate)
            )
    supply = (_uint(S.rpc_batch(f, [_call(t["token"], "totalSupply()")], block)[0]) or 0) / 10**dec
    holders = sorted(RL.read(f, {a: list(dict.fromkeys(rs)) for a, rs in admins.items()}, block), key=lambda h: h.roles)
    return Route(sym, "ccip", t["token"], supply, lanes, holders)


def _layerzero(f: S.Fetcher, sym: str, t: dict, block: int) -> Route:
    """D250: the app's peer for each chain listed; its owner, who sets a peer at once (`OAppCore.setPeer`)."""
    eids = list(t["eids"])
    r = S.rpc_batch(
        f,
        [_call(t["token"], "peers(uint32)", ["uint32"], [int(e)]) for e in eids]
        + [_call(t["token"], s) for s in ("totalSupply()", "owner()")],
        block,
    )
    lanes = [Lane(t["token"], "OApp", t["eids"][e], bool(_uint(p))) for e, p in zip(eids, r)]
    supply = (_uint(r[-2]) or 0) / 10 ** t["decimals"]
    holders = RL.read(f, {"0x" + r[-1][-40:]: ["owner"]}, block)
    return Route(sym, "layerzero", t["token"], supply, lanes, holders)


def load(f: S.Fetcher, block: int) -> dict[str, Route] | None:
    """D250: every pinned bridged token's lanes at `block`; None when not readable."""
    try:
        return {sym: (_ccip if t["kind"] == "ccip" else _layerzero)(f, sym, t, block) for sym, t in K["tokens"].items()}
    except (S.SourceError, S.CacheMiss):
        return None
