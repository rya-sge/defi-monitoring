"""Upshift: the Tori Ecosystem Vault behind etrUSD, its NAV and its exits (plan 2026-10-11-gapv3, D253–D255;
GAPV3 §2).

etrUSD is the share of an Upshift `TokenizedVault` holding trUSD (Tori). Almost all of it is off the chain: the
operator reports it (`updateTotalAssets(externalAssets)`), and the vault checks the change against a cap that grows
with the time since the last report (`getMaxAllowedChange() = maxChangePercent × seconds / 86400`, in 1/10,000; a
change is |new / old − 1|, `getChangePercentage`). A loss therefore reaches etrUSD's NAV, and the "fundamental" oracle
that reads it, only as fast as the cap allows, unless the owner raises the cap, a call scheduled through a timelock.
Exits: a redemption request is claimable after `lagDuration`, or at once for `instantRedemptionFee` (1/10,000);
`globalLiabilityShares` are the shares already queued. Read on-chain at a block from the pinned vault
(`registry.json` `upshift`), keyless; recorded under fixtures/replay/upshift/.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import roles as RL
from . import sources as S
from .discover import REGISTRY
from .vault import _call, _uint

K = REGISTRY["upshift"]


@dataclass
class Snapshot:
    block: int
    total: float  # getTotalAssets, trUSD
    external: float  # externalAssets: reported by the operator
    share_price: float
    updated_on: int  # assetsUpdatedOn, seconds
    cap_bps_day: float  # maxChangePercent: the NAV moves at most this much per day since the last report
    lag_s: int  # lagDuration: a redemption request waits this long
    instant_fee: float  # instantRedemptionFee, a fraction
    queued: float  # globalLiabilityShares: shares waiting to be redeemed
    supply: float  # etrUSD
    timelock_s: int  # the scheduled-call timelock that raising the cap goes through
    holders: list = field(default_factory=list)  # roles.Holder: owner, operator

    def lines(self) -> list[str]:
        return [
            f"etrUSD is the share of Upshift's Tori Ecosystem Vault (block {self.block:,}): {self.total / 1e6:,.2f}M "
            f"trUSD, {self.external / self.total:.2%} reported off-chain by the operator; its NAV can move "
            f"{self.cap_bps_day / 1e4:.2%} a day at most, unless the owner raises the cap ({self.timelock_s / 3600:g} h "
            "timelock)",
            f"exits: a request waits {self.lag_s / 86400:g} days, or leaves at once for {self.instant_fee:.0%}; "
            f"{self.queued / 1e6:,.2f}M of the {self.supply / 1e6:,.2f}M etrUSD ({self.queued / self.supply:.0%}) "
            "are queued already",
        ] + [f"{', '.join(h.roles)}: {h.label}" for h in self.holders]


def days_to_report(snap: Snapshot, fall: float) -> float:
    """D254, pure: the days of cap a NAV fall of `fall` needs, |new / old − 1| = 1 / (1 − fall) − 1, in 1/10,000."""
    if fall <= 0:
        return 0.0
    if fall >= 1 or not snap.cap_bps_day:
        return math.inf
    return (1 / (1 - fall) - 1) * 1e4 / snap.cap_bps_day


def markdown(snap: Snapshot, loss: float) -> dict:
    """D254, pure: a loss of the vault's off-chain assets as etrUSD's markdown, and how fast it can be reported."""
    m = loss * snap.external / snap.total if snap.total else 0.0
    days = days_to_report(snap, m)
    pace = (
        f"the cap lets it reach the NAV only over {days:,.0f} days, or after the owner raises the cap through its "
        f"{snap.timelock_s / 3600:g} h timelock; until then etrUSD's oracle reads it high, and the gap invites a drain"
        if days > 1
        else "the cap lets it reach the NAV at the next report"
    )
    return {
        "markdown": m,
        "days": days,
        "text": f"Upshift's Tori vault loses {loss:.1%} of its off-chain assets: etrUSD falls {m:.2%}; {pace}",
    }


def parse(items: list[str] | None) -> tuple[list[str], list[float]]:
    """D254, pure: split `upshift=<loss of its off-chain assets>` from the other shocks."""
    rest, out = [], []
    for it in items or []:
        name, _, value = it.partition("=")
        if name.strip() != "upshift":
            rest.append(it)
            continue
        try:
            v = float(value)
        except ValueError:
            v = -1.0
        if not 0 < v <= 1:
            raise ValueError(f"'{it}': write upshift=<loss of its off-chain assets, between 0 and 1>")
        out.append(v)
    return rest, out


# --- I/O


def load(f: S.Fetcher, block: int) -> Snapshot | None:
    """D253: the vault's assets, NAV cap, exits and roles at `block`; None when not readable."""
    v = K["vault"]
    names = (
        "getTotalAssets()",
        "externalAssets()",
        "getSharePrice()",
        "assetsUpdatedOn()",
        "maxChangePercent()",
        "lagDuration()",
        "instantRedemptionFee()",
        "globalLiabilityShares()",
        "lpTokenAddress()",
        "owner()",
        "operatorAddress()",
        "scheduledCallerAddress()",
    )
    try:
        r = S.rpc_batch(f, [_call(v, s) for s in names], block)
        lp, owner, operator, sched = ("0x" + x[-40:] for x in r[8:12])
        x = S.rpc_batch(f, [_call(lp, "totalSupply()"), _call(sched, "TIMELOCK_DURATION()")], block)
        holders = RL.read(f, {owner: ["owner"], operator: ["operator (reports the NAV)"]}, block)
    except (S.SourceError, S.CacheMiss):
        return None
    u = [_uint(y) or 0 for y in r[:8]]
    return Snapshot(
        block,
        u[0] / 1e18,
        u[1] / 1e18,
        u[2] / 1e18,
        u[3],
        float(u[4]),
        u[5],
        u[6] / 1e4,
        u[7] / 1e18,
        (_uint(x[0]) or 0) / 1e18,
        _uint(x[1]) or 0,
        holders,
    )
