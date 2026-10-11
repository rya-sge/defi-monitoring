"""Who holds each role of a Vault V2: one key, a Safe, a timelock (plan 2026-10-11-admin-impact, D245; GAPV2 G2).

In a Vault V2 the owner sets the curator and the sentinels at once (`setCurator`, `setIsSentinel`: owner only, not
timelocked); allocators move money within the caps at once; only the curator's changes wait for their timelocks. So a
role held by a single key is a dependency on that key: an owner that is one key can hand the vault to a new curator in
one transaction. Each holder is read at a block:

  no code, or an EIP-7702 delegation (0xef0100 + address)   one key
  getMinDelay() answers                                     a timelock (OpenZeppelin TimelockController)
  getThreshold() and getOwners() answer                     a Safe, n of m
  anything else                                             a contract (unknown)
"""

from __future__ import annotations

from dataclasses import dataclass

from . import sources as S
from .rules import Alert
from .vault import _call, _uint


@dataclass
class Holder:
    address: str
    roles: list[str]
    kind: str  # EOA | Safe | timelock | contract
    label: str
    threshold: int | None = None
    owners: int | None = None
    delay_s: int | None = None

    @property
    def one_key(self) -> bool:
        return self.kind == "EOA" or (self.kind == "Safe" and self.threshold == 1)


def classify(code: str | None, threshold: int | None, owners: int | None, delay: int | None) -> tuple[str, str]:
    """D245, pure: (kind, label) of a role holder from its code and what it answers."""
    if code in (None, "0x", ""):
        return "EOA", "an EOA (one key)"
    if code.startswith("0xef0100"):
        return "EOA", "an EIP-7702 wallet (one key)"
    if delay is not None:
        return "timelock", f"a timelock ({delay / 3600:g} h)"
    if threshold:
        return "Safe", f"a Safe {threshold}/{owners}" + (" (one key)" if threshold == 1 else "")
    return "contract", "a contract (unknown)"


def findings(holders: list[Holder], block: int) -> list[Alert]:
    """D245, pure: an owner held by one key is critical (it can replace the curator and the sentinels at once); an
    allocator held by one key a warn (it can move the vault's money within the caps at once); the rest info."""
    out = []
    for h in holders:
        if "owner" in h.roles and h.one_key:
            level, why = "critical", "it can replace the curator and the sentinels at once, with no timelock"
        elif "allocator" in h.roles and h.one_key:
            level, why = "warn", "it can move the vault's money between markets within the caps at once"
        else:
            level, why = "info", ""
        out.append(
            Alert(
                level,
                block,
                None,
                "RoleHolder",
                f"{' + '.join(h.roles)} {h.address[:10]}… is {h.label}",
                why,
                None,
                {"address": h.address, "roles": h.roles, "kind": h.kind, "threshold": h.threshold},
            )
        )
    return out


# --- I/O


def read(f: S.Fetcher, roles: dict[str, list[str]], block: int) -> list[Holder]:
    """D245: each holder's code, and for a contract `getThreshold()`, `getOwners()` and `getMinDelay()` in one batch."""
    codes = {a: S.rpc(f, "eth_getCode", [a, hex(block)]) for a in roles}
    contracts = [a for a, c in codes.items() if c not in (None, "0x", "") and not c.startswith("0xef0100")]
    calls = [_call(a, s) for a in contracts for s in ("getThreshold()", "getOwners()", "getMinDelay()")]
    res = S.rpc_batch(f, calls, block) if calls else []
    got = {}
    for i, a in enumerate(contracts):
        thr, owners_raw, delay = res[3 * i : 3 * i + 3]
        n = _uint("0x" + owners_raw[66:130]) if owners_raw and len(owners_raw) >= 130 else None
        got[a] = (_uint(thr) if thr and thr != "0x" else None, n, _uint(delay) if delay and delay != "0x" else None)
    out = []
    for a, rs in roles.items():
        thr, n, delay = got.get(a, (None, None, None))
        kind, label = classify(codes[a], thr, n, delay)
        out.append(Holder(a, rs, kind, label, thr, n, delay))
    return out


def discover(f: S.Fetcher, vault: str, block: int) -> dict[str, list[str]]:
    """The vault's role holders: owner and curator on-chain; allocators and sentinels listed by the Morpho API, each
    confirmed on-chain (as `graph` reads them)."""
    va = vault.lower()
    owner, curator = (
        ("0x" + r[-40:]).lower() if r else None
        for r in S.rpc_batch(f, [_call(va, "owner()"), _call(va, "curator()")], block)
    )
    roles: dict[str, list[str]] = {}
    for addr, role in ((owner, "owner"), (curator, "curator")):
        if addr:
            roles.setdefault(addr, []).append(role)
    try:
        d = S.morpho(
            f,
            """query($a:String!){ vaultV2ByAddress(address:$a, chainId:1){
                allocators{ allocator{address} } sentinels{ sentinel{address} } } }""",
            {"a": va},
        )["vaultV2ByAddress"]
        cand = [(x["allocator"]["address"].lower(), "allocator") for x in d["allocators"]] + [
            (x["sentinel"]["address"].lower(), "sentinel") for x in d["sentinels"]
        ]
        checks = S.rpc_batch(
            f,
            [
                _call(va, "isAllocator(address)" if r == "allocator" else "isSentinel(address)", ["address"], [a])
                for a, r in cand
            ],
            block,
        )
        for (addr, role), ok in zip(cand, checks):
            if _uint(ok):
                roles.setdefault(addr, []).append(role)
    except (S.SourceError, S.CacheMiss, KeyError, TypeError):
        pass
    return roles
