"""Zama confidential vaults: a Morpho Vault V2 entered through Zama's Confidential Vault protocol (plan
2026-10-11-zama, D171–D176; docs/analysis/ZAMA-VAULT.md).

The vault stays public; what changes is who holds it. Every confidential depositor's shares sit in one cShare
wrapper, so on-chain the cShare is one holder with the whole confidential part of the vault. It is a **pool**: not "the
depositor", and not a fast holder ahead of anyone in a run. A confidential depositor has two exits:
  - the batch: join the redeem batcher, which dispatches once its batch reaches its minimum age (about daily), then
    settles after a Zama decryption, at the share price of that moment, with no slippage bound;
  - the instant exit: unwrap the cShare to public vault shares (one decryption, minutes) and redeem them, which reveals
    the amount.
Both need Zama's decryption: if it halts, neither works.

`registry.json` `zama` lists every mainnet vault (checked on-chain). Pure helpers, and `read` for the live state.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import sources as S
from .discover import REGISTRY
from .vault import _call, _uint

Z = REGISTRY["zama"]
POOLS = {v["cshare"]: vault for vault, v in Z["vaults"].items()}


@dataclass
class ZamaState:
    name: str
    cshare: str
    confidential_share: float  # of the vault's shares, held by the cShare pool
    now: int  # the block's timestamp
    redeem_next: int | None  # when the pending redeem batch can be dispatched (unix seconds)
    deposit_next: int | None
    redeem_batch: int | None
    paused: bool
    gated: bool  # deposits only through the deposit batcher

    @property
    def redeem_in_h(self) -> float | None:
        return max(0.0, (self.redeem_next - self.now) / 3600) if self.redeem_next else None


def entry(vault: str) -> dict | None:
    return Z["vaults"].get(vault.lower())


def is_pool(address: str | None) -> bool:
    """D172, pure: is this holder a Zama cShare, a pool of confidential depositors?"""
    return bool(address) and address.lower() in POOLS


def exits(z: ZamaState, lands_at_once: bool) -> list[str]:
    """D174, pure: a confidential depositor's two exits, against how the incident lands."""
    out = [
        f"{z.confidential_share:.1%} of the vault is held confidentially through Zama (cShare {z.cshare[:10]}…, "
        f"one pool of depositors, not one holder)" + ("; batching is paused" if z.paused else "")
    ]
    h = z.redeem_in_h
    batch = (
        f"the confidential exit joins redeem batch {z.redeem_batch}, dispatched in {h:.1f} h at the earliest, then "
        "settled after a Zama decryption at the share price of that moment"
        if h is not None
        else "the confidential exit's next batch time could not be read"
    )
    if lands_at_once and h is not None:
        batch += ": it does not beat an incident that lands at once"
    out.append(batch)
    out.append(
        f"the instant exit unwraps the cShare to public vault shares and redeems them (about "
        f"{Z['instant_exit_minutes']} min, one Zama decryption); it is first in line, but the amount becomes public"
    )
    out.append("both exits need Zama's decryption: if it halts, neither works until it resumes")
    return out


# --- I/O


def read(f: S.Fetcher, vault: str, block) -> ZamaState | None:
    """D173: the confidential share and the batchers' state at `block`; None for a vault that is not a Zama vault."""
    e = entry(vault)
    if e is None:
        return None
    rb, db = e["redeem_batcher"], e["deposit_batcher"]
    ids = S.rpc_batch(
        f,
        [
            _call(vault, "balanceOf(address)", ["address"], [e["cshare"]]),
            _call(vault, "totalSupply()"),
            _call(rb, "currentBatchId()"),
            _call(db, "currentBatchId()"),
            _call(rb, "paused()"),
        ],
        block,
    )
    held, supply, rid, did, paused = (_uint(x) for x in ids)
    calls = []
    for b, i in ((rb, rid), (db, did)):
        calls += [
            _call(b, "batchCreatedAt(uint256)", ["uint256"], [i or 0]),
            _call(b, "batchMinBatchAge(uint256)", ["uint256"], [i or 0]),
        ]
    r_created, r_age, d_created, d_age = (_uint(x) for x in S.rpc_batch(f, calls, block))
    head = S.rpc(f, "eth_getBlockByNumber", [hex(block) if isinstance(block, int) else block, False]) or {}
    now = int(head.get("timestamp", "0x0"), 16)
    return ZamaState(
        e["name"],
        e["cshare"],
        held / supply if supply and held is not None else 0.0,
        now,
        r_created + r_age if r_created and r_age is not None else None,
        d_created + d_age if d_created and d_age is not None else None,
        rid,
        bool(paused),
        "deposit_gate" in e,
    )
