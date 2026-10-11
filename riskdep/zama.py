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


def share_rate(f: S.Fetcher, e: dict, block) -> int:
    """The cShare's `rate()`: vault-share units per cShare unit (10^12 for 18-decimal shares wrapped at 6); 0 when it
    cannot be read, which silences the share-of-vault figures rather than inventing them."""
    try:
        return _uint(S.rpc_batch(f, [_call(e["cshare"], "rate()")], block)[0]) or 0
    except (S.CacheMiss, S.SourceError):
        return 0


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


# --- watch (Z4): the batchers' and wrappers' events (plan 2026-10-11-zama-alerts, D190–D192)

ZAMA_EVENTS = (
    "BatchFinalized",
    "BatchCanceled",
    "BatchDispatched",
    "UnwrapFinalized",
    "Paused",
    "Unpaused",
    "OwnershipTransferred",
    "Upgraded",
    "UserBlocked",
)


def contracts(e: dict) -> dict[str, str]:
    """The vault's Zama contracts, by role."""
    return {
        e["redeem_batcher"]: "redeem batcher",
        e["deposit_batcher"]: "deposit batcher",
        e["cshare"]: "cShare",
        e["casset"]: "cAsset",
    }


def kinds(e: dict) -> dict[str, str]:
    """D190: the addresses the poller decodes as `zama` events."""
    return {a: "zama" for a in contracts(e)}


def filters(e: dict) -> list[dict]:
    """D190: one optional log filter for the vault's Zama contracts and their events (a refusal is a warning)."""
    from .abi import EVENTS

    topics = sorted({s.topic0 for s in EVENTS if s.contract == "zama"})
    return [{"address": sorted(contracts(e)), "topics": [topics], "_optional": True}]


def assess_events(events, e: dict, total_supply: int, share_rate: int, block: int) -> list:
    """D191–D192, pure: alerts from a batch's Zama events. `share_rate` is the cShare's `rate()`: vault-share units per
    cShare unit; `total_supply` the vault's shares. A cShare unwrap to the redeem batcher is the day's confidential
    redemption, in public; to anyone else, an instant exit with its amount revealed."""
    from .rules import Alert

    W = REGISTRY["watch"]
    role = contracts(e)
    out = []
    # an empty day: the batch's aggregate decrypts to zero and the batch cancels; routine, not an alert
    empty = {
        ev.tx
        for ev in events
        if ev.name == "UnwrapFinalized"
        and ev.args.get("receiver") in (e["redeem_batcher"], e["deposit_batcher"])
        and not ev.args.get("cleartextAmount")
    }
    for ev in events:
        if ev.contract != "zama" or ev.removed or ev.address not in role:
            continue
        who = role[ev.address]
        a = ev.args
        if ev.name == "UnwrapFinalized" and who == "cShare" and a["cleartextAmount"]:
            share = a["cleartextAmount"] * share_rate / total_supply if total_supply else 0.0
            batch = a["receiver"] == e["redeem_batcher"]
            if batch:
                level = (
                    "critical"
                    if share >= W["zama_redeem_critical"]
                    else "warn"
                    if share >= W["zama_redeem_warn"]
                    else "info"
                )
                title = f"Zama redeem batch: {share:.2%} of the vault leaving confidentially today"
                detail = (
                    "the redeem batcher's aggregate, made public by its decryption: the confidential depositors' daily "
                    "outflow" + ("; a confidential run may be forming" if level == "critical" else "")
                )
            else:
                level = "warn" if share >= W["zama_instant_warn"] else "info"
                title = (
                    f"Zama instant exit: {share:.2%} of the vault unwrapped to public shares by {a['receiver'][:10]}…"
                )
                detail = "a confidential holder left fast, revealing the amount: an informed exit is worth watching"
            out.append(
                Alert(
                    level,
                    block,
                    ev.tx,
                    "Zama.Unwrap",
                    title,
                    detail,
                    None,
                    {"share_of_vault": share, "batch": batch, "receiver": a["receiver"]},
                )
            )
        elif ev.name == "BatchCanceled" and ev.tx not in empty:
            out.append(
                Alert(
                    "warn",
                    block,
                    ev.tx,
                    "Zama.BatchCanceled",
                    f"Zama {who}: batch {a['batchId']} canceled",
                    "the batch did not settle (zero aggregate, a take-back, or its 12 h deadline passed with the "
                    "decryption pending): its depositors get their input back and must join again",
                    None,
                    {"batch": a["batchId"], "contract": who},
                )
            )
        elif ev.name in ("Paused", "Upgraded"):
            out.append(
                Alert(
                    "critical",
                    block,
                    ev.tx,
                    f"Zama.{ev.name}",
                    f"Zama {who} {'paused' if ev.name == 'Paused' else 'upgraded'}",
                    "the confidential exit is blocked until it is unpaused"
                    if ev.name == "Paused"
                    else f"new implementation {a['implementation']}: its code, and so its behaviour, changed",
                    None,
                    {"contract": who},
                )
            )
        elif ev.name == "OwnershipTransferred":
            out.append(
                Alert(
                    "warn",
                    block,
                    ev.tx,
                    "Zama.OwnershipTransferred",
                    f"Zama {who}: owner changed to {a['newOwner'][:10]}…",
                    "the owner can pause joins and dispatch",
                    None,
                    {"contract": who, "owner": a["newOwner"]},
                )
            )
        elif ev.name in ("Unpaused", "UserBlocked"):
            out.append(Alert("info", block, ev.tx, f"Zama.{ev.name}", f"Zama {who}: {ev.name}", "", None, {}))
    return out
