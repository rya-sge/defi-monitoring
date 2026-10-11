"""infiniFi: how a loss of its backing reaches siUSD and iUSD, and the loss pending before it is booked (plan
2026-10-11-issuer-stacks, D246–D247; GAPV2 G18).

infiniFi's YieldSharingV3 books a loss in a fixed order (`_handleNegativeYield`, `YieldSharingV3.sol:343-376`):

  1. the safety buffer (iUSD held by YieldSharing), only if it covers the whole loss; otherwise it is skipped
  2. liUSD, the locked iUSD (`LockingController.totalBalance()`), up to its balance
  3. siUSD holders (the iUSD staked in siUSD), whose rate falls
  4. every iUSD holder: the iUSD price is cut

`unaccruedYield() < 0` is a loss the protocol knows and has not booked yet; siUSD exits close until it is. Read on-chain
at a block from siUSD alone (siUSD → `yieldSharing()` → the rest), keyless; recorded under fixtures/replay/infinifi/.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import sources as S
from .discover import REGISTRY
from .vault import _call, _uint

K = REGISTRY["infinifi"]


@dataclass
class Snapshot:
    block: int
    backing_usd: float  # Accounting.totalAssetsValue()
    buffer: float  # iUSD held by YieldSharing
    locked: float  # liUSD: LockingController.totalBalance()
    staked: float  # iUSD held by siUSD
    supply: float  # iUSD in circulation
    unaccrued: float  # unaccruedYield(), iUSD: negative is a loss pending

    def lines(self) -> list[str]:
        out = [
            f"siUSD's loss waterfall (infiniFi, block {self.block:,}, {self.backing_usd / 1e6:,.2f}M USD of backing): a "
            f"loss goes to the safety buffer ({self.buffer / 1e6:,.3f}M, only if it covers it all), then liUSD "
            f"({self.locked / 1e6:,.2f}M), then siUSD ({self.staked / 1e6:,.2f}M), then every iUSD holder "
            f"({self.supply / 1e6:,.2f}M)"
        ]
        if self.unaccrued < 0:
            out.append(
                f"a loss of {-self.unaccrued:,.0f} iUSD is pending (unaccruedYield < 0): siUSD exits are closed until "
                "it is booked"
            )
        return out


def waterfall(snap: Snapshot, loss: float) -> dict:
    """D246, pure: a loss of backing (iUSD) through the order of `_handleNegativeYield`; the siUSD and iUSD markdowns."""
    if loss <= snap.buffer:
        return {"buffer": loss, "locked": 0.0, "staked": 0.0, "iusd": 0.0, "siusd_markdown": 0.0, "iusd_markdown": 0.0}
    locked = min(loss, snap.locked)
    staked = min(loss - locked, snap.staked)
    rest = loss - locked - staked
    return {
        "buffer": 0.0,
        "locked": locked,
        "staked": staked,
        "iusd": rest,
        "siusd_markdown": staked / snap.staked if snap.staked else 0.0,
        "iusd_markdown": rest / snap.supply if snap.supply else 0.0,
    }


def describe(snap: Snapshot, share: float, w: dict) -> str:
    loss = share * snap.backing_usd
    return f"infiniFi loses {share:.0%} of its backing, {loss / 1e6:,.1f}M: " + (
        "the safety buffer covers it"
        if w["buffer"]
        else f"liUSD absorbs it all ({w['locked'] / 1e6:,.1f}M of {snap.locked / 1e6:,.1f}M)"
        if not w["staked"]
        else f"liUSD absorbs {w['locked'] / 1e6:,.1f}M, siUSD {w['staked'] / 1e6:,.1f}M "
        f"(−{w['siusd_markdown']:.2%})"
        + (f", every iUSD holder {w['iusd'] / 1e6:,.1f}M (−{w['iusd_markdown']:.2%})" if w["iusd"] else "")
    )


def pending_alert(snap: Snapshot, block: int):
    """D247, pure: a loss pending in infiniFi, warn, critical once it would reach siUSD (above liUSD and the buffer)."""
    from .rules import Alert

    if snap.unaccrued >= 0:
        return None
    loss = -snap.unaccrued
    reaches = loss > snap.locked and loss > snap.buffer
    return Alert(
        "critical" if reaches else "warn",
        block,
        None,
        "InfiniFi.PendingLoss",
        f"infiniFi has a loss of {loss:,.0f} iUSD pending, not yet booked",
        "unaccruedYield() is negative: the backing is worth less than the iUSD in circulation; siUSD exits are closed "
        "until the loss is booked"
        + ("; it is larger than liUSD and will reach siUSD holders" if reaches else "; liUSD absorbs it first"),
        None,
        {"pending": loss, "locked": snap.locked},
    )


# --- I/O


def load(f: S.Fetcher, block: int) -> Snapshot | None:
    """D246: from siUSD: its yield-sharing contract, the accounting, iUSD, liUSD; None when not readable."""
    siusd = K["siusd"]
    try:
        ys = "0x" + S.rpc_batch(f, [_call(siusd, "yieldSharing()")], block)[0][-40:]
        r = S.rpc_batch(f, [_call(ys, s) for s in ("accounting()", "receiptToken()", "lockingModule()")], block)
        acc, iusd, lock = ("0x" + x[-40:] for x in r)
        v = S.rpc_batch(
            f,
            [
                _call(acc, "totalAssetsValue()"),
                _call(iusd, "balanceOf(address)", ["address"], [ys]),
                _call(lock, "totalBalance()"),
                _call(iusd, "balanceOf(address)", ["address"], [siusd]),
                _call(iusd, "totalSupply()"),
                _call(ys, "unaccruedYield()"),
            ],
            block,
        )
    except (S.SourceError, S.CacheMiss):
        return None
    raw = int(v[5], 16) if v[5] and v[5] != "0x" else 0
    unaccrued = raw - 2**256 if raw >= 2**255 else raw
    backing, buffer, locked, staked, supply = ((_uint(x) or 0) / 1e18 for x in v[:5])
    return Snapshot(block, backing, buffer, locked, staked, supply, unaccrued / 1e18)
