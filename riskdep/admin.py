"""Admin surface of the watched markets (plan 2026-10-10-admin-surface, D52–D58).

For every watched market: the oracle, the feeds and vault shares it reads, the collateral and loan
tokens, and for a Pendle PT its SY and yield token. For each contract: is it upgradeable, who is its
admin and owner, which aggregator a Chainlink proxy points to. Read from standard storage slots and
getters, watched through standard events; no API key and no contract source needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eth_abi import decode
from eth_utils import keccak

from . import borrower as B
from . import discover
from . import sources as S
from .abi import MORPHO_BLUE, Event, selector, topic
from .discover import REGISTRY
from .rules import Alert
from .vault import _call, _symbol, _uint

W = REGISTRY["watch"]
ZERO = "0x" + "0" * 40


def _slot(label: str, minus_one: bool = True) -> str:
    h = int.from_bytes(keccak(text=label), "big") - (1 if minus_one else 0)
    return hex(h)


SLOTS = {
    "impl": _slot("eip1967.proxy.implementation"),  # EIP-1967
    "admin": _slot("eip1967.proxy.admin"),
    "beacon": _slot("eip1967.proxy.beacon"),
    "zos_impl": _slot("org.zeppelinos.proxy.implementation", False),  # ZeppelinOS (USDC's proxy)
    "zos_admin": _slot("org.zeppelinos.proxy.admin", False),
}
ORACLE_GETTERS = ["BASE_FEED_1()", "BASE_FEED_2()", "QUOTE_FEED_1()", "QUOTE_FEED_2()", "BASE_VAULT()", "QUOTE_VAULT()"]
ADMIN_EVENTS = [
    "Upgraded(address)",
    "AdminChanged(address,address)",
    "BeaconUpgraded(address)",
    "OwnershipTransferred(address,address)",
    "AggregatorProposed(address,address)",
    "AggregatorConfirmed(address,address)",
    "Paused(address)",
    "Unpaused(address)",
    "RoleGranted(bytes32,address,address)",
    "RoleRevoked(bytes32,address,address)",
]
# the queue of an OpenZeppelin TimelockController that controls a watched contract (fork-demo D3)
TIMELOCK_EVENTS = [
    "CallScheduled(bytes32,uint256,address,uint256,bytes,bytes32,uint256)",
    "CallExecuted(bytes32,uint256,address,uint256,bytes)",
    "Cancelled(bytes32)",
]
# calls that replace a contract's code: on a ProxyAdmin (the proxy is the first argument) or on the proxy (UUPS)
UPGRADE_CALLS = {
    selector(sig): sig
    for sig in (
        "upgrade(address,address)",
        "upgradeAndCall(address,address,bytes)",
        "upgradeTo(address)",
        "upgradeToAndCall(address,bytes)",
        "changeProxyAdmin(address,address)",
        "transferOwnership(address)",
    )
}
BLUE_OWNER = ["SetOwner(address)", "EnableIrm(address)", "EnableLltv(uint256)", "SetFeeRecipient(address)"]
TRANSFER = topic("Transfer(address,address,uint256)")
DEFAULT_ADMIN_ROLE = "0x" + "00" * 32


@dataclass
class Contract:
    address: str
    roles: list[str] = field(default_factory=list)  # "collateral X/Y", "oracle of …", "feed ETH / USD", …
    mint_watch: bool = False  # collateral and yield tokens (D55)
    is_collateral: bool = False
    symbol: str = ""
    # state, read at start and every refresh
    impl: str | None = None
    admin: str | None = None
    beacon: str | None = None
    owner: str | None = None
    aggregator: str | None = None
    clone_of: str | None = None
    total_supply: int | None = None
    # fork-demo D3–D4: a timelock or proxy admin found above a watched contract, and a custom feed's fixed band
    timelock_delay: int | None = None  # seconds, when this contract is an OpenZeppelin TimelockController
    controls: list[str] = field(default_factory=list)  # addresses of the watched contracts it can change
    band: tuple[int, int, int, int] | None = None  # (minAnswer, maxAnswer, decimals, latest answer)

    @property
    def upgradeable(self) -> bool:
        return bool(self.impl or self.beacon)

    @property
    def label(self) -> str:
        return f"{self.symbol or self.address[:10] + '…'} ({'; '.join(self.roles[:2])}{'…' if len(self.roles) > 2 else ''})"


def _word(raw: str | None, signed: bool = False) -> int | None:
    """One 32-byte return word as an int; None for an empty or reverted answer."""
    if not raw or len(raw) < 66:
        return None
    return int.from_bytes(bytes.fromhex(raw[2:66]), "big", signed=signed)


def _addr(word: str | None) -> str | None:
    if not word or word in ("0x", "0x0"):
        return None
    a = "0x" + word[-40:].lower()
    return None if a == ZERO else a


class AdminWatch:
    def __init__(self, f: S.Fetcher, market_ids: list[str], block: int):
        self.contracts: dict[str, Contract] = {}
        self.markets = B.discover_markets(f, sorted(set(market_ids)), block) if market_ids else {}
        self.divergence: dict[str, float | None] = {}
        self.llama: dict | None = None
        self.llama_block = 0
        for m in self.markets.values():
            self._discover_market(f, m, block)
        self.read_state(f, block)
        self.controllers_checked = self._discover_controllers(f, block)
        self.bands_checked = self._read_bands(f, block)
        self.divergence = self.read_divergence(f, block)

    # --- discovery
    def _add(self, addr: str, role: str, symbol: str = "", **flags) -> Contract:
        c = self.contracts.setdefault(addr.lower(), Contract(addr.lower()))
        if role not in c.roles:
            c.roles.append(role)
        c.symbol = c.symbol or symbol
        for k, v in flags.items():
            setattr(c, k, getattr(c, k) or v)
        return c

    def _discover_market(self, f: S.Fetcher, m: B.BorrowMarket, block: int) -> None:
        tag = f"{m.collateral_symbol}/{m.loan_symbol}"
        self._add(m.collateral_token, f"collateral of {tag}", m.collateral_symbol, mint_watch=True, is_collateral=True)
        self._add(m.loan_token, f"loan of {tag}", m.loan_symbol)
        self._add(m.oracle, f"oracle of {tag}", "oracle")
        res = S.rpc_batch(f, [_call(m.oracle, g) for g in ORACLE_GETTERS], block)
        for g, r in zip(ORACLE_GETTERS, res):
            a = _addr(r)
            if not a:
                continue
            if "VAULT" in g:
                self._add(a, f"vault share in the oracle of {tag}", _symbol(f, a, block))
            else:
                desc = S.rpc_batch(f, [_call(a, "description()")], block)[0]
                name = g[:-2]
                try:
                    name = decode(["string"], bytes.fromhex(desc[2:]))[0] if desc else name
                except Exception:
                    pass
                self._add(a, f"feed of the oracle of {tag}", name)
        if m.collateral_symbol.upper().startswith("PT-"):
            try:
                pm = discover.find_pendle_market(f, m.collateral_token)
            except (S.SourceError, S.CacheMiss):
                return
            sy = pm["sy"].split("-", 1)[-1].lower()
            und = pm["underlyingAsset"].split("-", 1)[-1].lower()
            self._add(sy, f"Pendle SY of {m.collateral_symbol}", f"SY-{pm['name']}")
            self._add(und, f"yield token of {m.collateral_symbol}", _symbol(f, und, block), mint_watch=True)

    def _discover_controllers(self, f: S.Fetcher, block: int) -> bool:
        """D3: who can change a watched contract, one level up. The proxy admin of each proxy, the owner of that
        proxy admin, and each contract's owner; any of them answering `getMinDelay()` is an OpenZeppelin
        TimelockController, whose queue is then watched: an upgrade is seen when it is scheduled, a full delay before
        it can land. False when it could not be read (a replay recorded before this check): the watch goes on."""
        cands: dict[str, list[tuple[str, Contract]]] = {}
        for c in list(self.contracts.values()):
            if c.admin:
                cands.setdefault(c.admin, []).append(("proxy admin", c))
            if c.owner:
                cands.setdefault(c.owner, []).append(("owner", c))
        if not cands:
            return True
        try:
            pas = sorted(a for a, rs in cands.items() if any(r == "proxy admin" for r, _ in rs))
            for a, r in zip(pas, S.rpc_batch(f, [_call(a, "owner()") for a in pas], block)):
                o = _addr(r)
                if o:
                    for _, c in list(cands[a]):
                        cands.setdefault(o, []).append(("owner of its proxy admin", c))
            addrs = sorted(cands)
            delays = S.rpc_batch(f, [_call(a, "getMinDelay()") for a in addrs], block)
        except (S.SourceError, S.CacheMiss):
            return False
        for a, d in zip(addrs, delays):
            delay = _word(d)
            proxy_admin = any(r == "proxy admin" for r, _ in cands[a])
            if delay is None and not proxy_admin:
                continue
            for r, c in cands[a]:
                kind = f"timelock ({delay / 3600:g} h)" if delay is not None else "proxy admin"
                t = self._add(a, f"{kind}, {r} of {c.symbol or c.address[:10]}")
                t.timelock_delay = delay
                if c.address not in t.controls:
                    t.controls.append(c.address)
        return True

    def _read_bands(self, f: S.Fetcher, block: int) -> bool:
        """D4: the fixed band of a custom feed (`minAnswer`/`maxAnswer` readable on the feed itself, e.g. Midas
        CustomAggregatorV3CompatibleFeed). Below `minAnswer` the feed cannot report without new code, so a loss
        beyond the band reaches the oracle only through an upgrade. Chainlink proxies expose no band: skipped."""
        feeds = sorted(a for a, c in self.contracts.items() if any(r.startswith("feed of") for r in c.roles))
        if not feeds:
            return True
        calls = []
        for a in feeds:
            calls += [
                _call(a, "minAnswer()"),
                _call(a, "maxAnswer()"),
                _call(a, "decimals()"),
                _call(a, "latestRoundData()"),
            ]
        try:
            res = S.rpc_batch(f, calls, block)
        except (S.SourceError, S.CacheMiss):
            return False
        for i, a in enumerate(feeds):
            lo, hi, dec, rd = res[4 * i : 4 * i + 4]
            lo, hi, dec = _word(lo, True), _word(hi, True), _word(dec)
            ans = _word("0x" + rd[66:130], True) if rd and len(rd) >= 130 else None
            if lo is not None and hi is not None and dec is not None and ans and 0 < lo < hi:
                self.contracts[a].band = (lo, hi, dec, ans)
        return True

    def timelock_over(self, address: str) -> Contract | None:
        """The timelock controlling a watched contract, directly or through its proxy admin."""
        for c in self.contracts.values():
            if c.timelock_delay is not None and address in c.controls:
                return c
        return None

    # --- state
    def read_state(self, f: S.Fetcher, block: int) -> None:
        addrs = sorted(self.contracts)
        tag = hex(block)
        raw = S.rpc_batch_methods(
            f,
            [("eth_getStorageAt", [a, slot, tag]) for a in addrs for slot in SLOTS.values()]
            + [("eth_getCode", [a, tag]) for a in addrs],
        )
        n = len(SLOTS)
        calls = (
            [_call(a, "owner()") for a in addrs]
            + [_call(a, "aggregator()") for a in addrs]
            + [_call(a, "totalSupply()") for a in addrs]
        )
        res = S.rpc_batch(f, calls, block)
        for i, a in enumerate(addrs):
            c = self.contracts[a]
            words = dict(zip(SLOTS, raw[i * n : (i + 1) * n]))
            c.impl = _addr(words["impl"]) or _addr(words["zos_impl"])
            c.admin = _addr(words["admin"]) or _addr(words["zos_admin"])
            c.beacon = _addr(words["beacon"])
            code = raw[len(addrs) * n + i] or ""
            c.clone_of = "0x" + code[22:62] if code.startswith("0x363d3d373d3d3d363d73") else None
            c.owner = _addr(res[i])
            c.aggregator = _addr(res[len(addrs) + i])
            c.total_supply = _uint(res[2 * len(addrs) + i]) if c.mint_watch else None

    def snapshot(self) -> dict[str, tuple]:
        return {a: (c.impl, c.admin, c.beacon, c.owner, c.aggregator) for a, c in self.contracts.items()}

    def read_divergence(self, f: S.Fetcher, block: int) -> dict[str, float | None]:
        """D58: oracle price against DefiLlama's collateral ÷ loan price, per market."""
        ms = list(self.markets.values())
        prices = S.rpc_batch(f, [_call(m.oracle, "price()") for m in ms], block)
        return self.divergence_at({m.id: _uint(raw) for m, raw in zip(ms, prices)}, self.fresh_prices(f, block, 0))

    def fresh_prices(self, f: S.Fetcher, block: int, every: int) -> dict:
        """DefiLlama's prices of the markets' tokens, re-fetched once `every` blocks have passed (0: always)."""
        if self.llama is None or block - self.llama_block >= every:
            ms = self.markets.values()
            try:
                self.llama = S.coin_prices(f, sorted({m.collateral_token for m in ms} | {m.loan_token for m in ms}))
                self.llama_block = block
            except (S.SourceError, S.CacheMiss):
                self.llama = self.llama or {}
        return self.llama

    def divergence_at(self, oracle_raw: dict[str, int | None], llama: dict) -> dict[str, float | None]:
        """Pure: oracle ÷ (collateral ÷ loan price) − 1 per market, from raw `price()` values."""
        out = {}
        for mid, p in oracle_raw.items():
            m = self.markets.get(mid)
            if m is None:
                continue
            pc = llama.get(f"ethereum:{m.collateral_token}", {}).get("price")
            pl = llama.get(f"ethereum:{m.loan_token}", {}).get("price")
            if not (pc and pl and p):
                out[mid] = None
                continue
            oracle = p / 10 ** (36 + m.loan_decimals - m.collateral_decimals)
            out[mid] = oracle / (pc / pl) - 1
        return out

    # --- poller
    def kinds(self) -> dict[str, str]:
        return {a: "admin" for a in self.contracts}

    def filters(self) -> list[dict]:
        out = []
        if self.contracts:
            out.append(
                {"address": sorted(self.contracts), "topics": [[topic(e) for e in ADMIN_EVENTS]], "_optional": True}
            )
        mint = sorted(a for a, c in self.contracts.items() if c.mint_watch)
        if mint:
            out.append({"address": mint, "topics": [TRANSFER, "0x" + "0" * 64], "_optional": True})
        out.append({"address": MORPHO_BLUE, "topics": [[topic(e) for e in BLUE_OWNER]], "_optional": True})
        tls = sorted(a for a, c in self.contracts.items() if c.timelock_delay is not None)
        if tls:
            out.append({"address": tls, "topics": [[topic(e) for e in TIMELOCK_EVENTS]], "_optional": True})
        return out

    # --- per batch
    def step(self, f: S.Fetcher, events: list[Event], block: int, refresh: bool) -> list[Alert]:
        alerts = assess_events(events, self.contracts, block)
        apply_events(events, self.contracts)
        if refresh:
            before = self.snapshot()
            self.read_state(f, block)
            alerts += assess_changes(before, self.snapshot(), self.contracts, block)
            div = self.read_divergence(f, block)
            alerts += assess_divergence(self.divergence, div, self.markets, block)
            self.divergence = div
        return alerts

    def check_divergence(self, f: S.Fetcher, block: int, oracle_raw: dict[str, int | None]) -> list[Alert]:
        """D97: the oracle-versus-market check between full refreshes, every `divergence_check_every_blocks`, from the
        oracle prices the watch already read at this batch and DefiLlama's prices (shared with the drain check)."""
        prices = self.fresh_prices(f, block, W["divergence_check_every_blocks"])
        div = self.divergence_at({m: r for m, r in oracle_raw.items() if m in self.markets}, prices)
        alerts = assess_divergence(self.divergence, div, self.markets, block)
        self.divergence = {**self.divergence, **div}
        return alerts

    def startup(self, block: int) -> list[Alert]:
        up = [c for c in self.contracts.values() if c.upgradeable]
        out = []
        if up:
            out.append(
                Alert(
                    "info",
                    block,
                    None,
                    "AdminSurface",
                    f"{len(up)} of {len(self.contracts)} contracts your markets depend on are upgradeable",
                    "; ".join(
                        f"{c.label}: "
                        + (f"admin {c.admin}" if c.admin else "upgrade right in the implementation (UUPS)")
                        for c in up[:8]
                    )
                    + ("…" if len(up) > 8 else ""),
                    None,
                    {"upgradeable": [c.address for c in up]},
                )
            )
        out += band_findings(self.contracts, self.timelock_over, block)
        tls = [c for c in self.contracts.values() if c.timelock_delay is not None]
        if tls:
            out.append(
                Alert(
                    "info",
                    block,
                    None,
                    "AdminSurface",
                    f"{len(tls)} timelock(s) control contracts your markets depend on; their queue is watched",
                    "; ".join(
                        f"{c.address[:10]}… ({c.timelock_delay / 3600:g} h) over "
                        + ", ".join(self.contracts[x].symbol or x[:10] for x in c.controls)
                        for c in tls
                    )
                    + ". An upgrade is alerted when it is scheduled, not when it lands",
                    None,
                    {"timelocks": [c.address for c in tls]},
                )
            )
        out += assess_divergence({}, self.divergence, self.markets, block)
        return out

    def table(self, line) -> None:
        line(f"  admin surface: {len(self.contracts)} contracts behind the watched markets")
        line(f"    {'contract':<34} {'upgradeable':<12} {'admin / owner':<44} role")
        for c in sorted(self.contracts.values(), key=lambda c: (not c.upgradeable, c.symbol)):
            up = "yes" if c.upgradeable else ("clone" if c.clone_of else "no")
            who = c.admin or c.owner or ("UUPS: right in the code" if c.upgradeable else "")
            if c.aggregator:
                who = (who + " · feed " + c.aggregator[:10] + "…").strip(" ·")
            line(
                f"    {(c.symbol or '')[:20] + ' ' + c.address[:10] + '…':<34} {up:<12} {who[:44]:<44} {c.roles[0]}"
                + (f" (+{len(c.roles) - 1})" if len(c.roles) > 1 else "")
            )
        for c in self.contracts.values():
            if c.band:
                lo, hi, dec, ans = c.band
                line(
                    f"  feed band {c.symbol} {c.address[:10]}…: {lo / 10**dec:,.4g} – {hi / 10**dec:,.4g}, "
                    f"now {ans / 10**dec:,.6g} ({lo / ans - 1:+.1%} to the floor)"
                )
        if not (self.controllers_checked and self.bands_checked):
            line("  timelocks and feed bands: not checked (not in this recording)")
        div = [
            f"{self.markets[m].collateral_symbol}/{self.markets[m].loan_symbol} {d:+.2%}"
            for m, d in self.divergence.items()
            if d is not None
        ]
        if div:
            line("  oracle vs DefiLlama: " + ", ".join(div))


# --- rules (pure)


def apply_events(events: list[Event], contracts: dict[str, Contract]) -> None:
    """Keep the snapshot current, so a change already alerted by its event is not alerted again at refresh."""
    for e in events:
        c = contracts.get(e.address)
        if c is None or e.removed:
            continue
        a = e.args
        if e.name == "Upgraded":
            c.impl = a["implementation"]
        elif e.name == "BeaconUpgraded":
            c.beacon = a["beacon"]
        elif e.name == "AdminChanged":
            c.admin = a["newAdmin"]
        elif e.name == "OwnershipTransferred":
            c.owner = a["newOwner"]
        elif e.name == "AggregatorConfirmed":
            c.aggregator = a["latest"]


def assess_events(events: list[Event], contracts: dict[str, Contract], block: int) -> list[Alert]:
    out = []
    for e in events:
        if e.removed:
            continue
        a = e.args
        if e.contract == "blue" and e.name in ("SetOwner", "EnableIrm", "EnableLltv", "SetFeeRecipient"):
            lvl = "warn" if e.name == "SetOwner" else "info"
            out.append(
                Alert(
                    lvl,
                    e.block,
                    e.tx,
                    f"Blue.{e.name}",
                    f"Morpho Blue owner action: {e.name}",
                    ", ".join(f"{k}={v}" for k, v in a.items())
                    + ". Blue is immutable; this does not change existing markets",
                    None,
                    {},
                )
            )
            continue
        c = contracts.get(e.address)
        if c is None or e.contract != "admin":
            continue
        name, label = e.name, c.label
        if name in ("Upgraded", "BeaconUpgraded"):
            out.append(
                Alert(
                    "critical",
                    e.block,
                    e.tx,
                    f"Admin.{name}",
                    f"{label} was upgraded",
                    f"new {'implementation' if name == 'Upgraded' else 'beacon'} "
                    f"{a.get('implementation') or a.get('beacon')}: its code, and so its behaviour, changed",
                    None,
                    {"contract": c.address},
                )
            )
        elif name == "AdminChanged":
            out.append(
                Alert(
                    "warn",
                    e.block,
                    e.tx,
                    "Admin.AdminChanged",
                    f"Proxy admin of {label} changed",
                    f"{a['previousAdmin']} → {a['newAdmin']}: the new admin can upgrade it",
                    None,
                    {"contract": c.address},
                )
            )
        elif name == "OwnershipTransferred":
            out.append(
                Alert(
                    "warn",
                    e.block,
                    e.tx,
                    "Admin.OwnershipTransferred",
                    f"Owner of {label} changed",
                    f"{a['previousOwner']} → {a['newOwner']}",
                    None,
                    {"contract": c.address},
                )
            )
        elif name in ("AggregatorProposed", "AggregatorConfirmed"):
            out.append(
                Alert(
                    "warn",
                    e.block,
                    e.tx,
                    f"Admin.{name}",
                    f"Price feed {'change proposed' if name == 'AggregatorProposed' else 'changed'}: {label}",
                    f"{a.get('current') or a.get('previous')} → {a.get('proposed') or a.get('latest')}; "
                    "the oracle's price now comes from a different aggregator"
                    if name == "AggregatorConfirmed"
                    else f"{a['current']} → {a['proposed']}, not yet confirmed",
                    None,
                    {"contract": c.address},
                )
            )
        elif name == "Paused":
            lvl = "critical" if c.is_collateral else "warn"
            out.append(
                Alert(
                    lvl,
                    e.block,
                    e.tx,
                    "Admin.Paused",
                    f"{label} was paused",
                    "a paused collateral token cannot be transferred: liquidations can fail and leave bad debt"
                    if c.is_collateral
                    else "transfers or operations of this contract are suspended",
                    None,
                    {"contract": c.address},
                )
            )
        elif name == "Unpaused":
            out.append(
                Alert(
                    "info", e.block, e.tx, "Admin.Unpaused", f"{label} was unpaused", "", None, {"contract": c.address}
                )
            )
        elif name in ("RoleGranted", "RoleRevoked"):
            admin_role = a["role"] == DEFAULT_ADMIN_ROLE
            lvl = "warn" if (name == "RoleGranted" and admin_role) else "info"
            out.append(
                Alert(
                    lvl,
                    e.block,
                    e.tx,
                    f"Admin.{name}",
                    f"{'Admin role' if admin_role else 'Role'} {'granted' if name == 'RoleGranted' else 'revoked'} on {label}",
                    f"role {a['role'][:10]}… account {a['account']}",
                    None,
                    {"contract": c.address},
                )
            )
        elif name in ("CallScheduled", "CallExecuted", "Cancelled"):
            out += _timelock_alert(e, c, contracts)
        elif name == "Transfer" and a.get("from") == ZERO and c.mint_watch and c.total_supply:
            share = a["value"] / c.total_supply
            if share >= W["mint_share_critical"]:
                out.append(
                    Alert(
                        "critical",
                        e.block,
                        e.tx,
                        "Admin.Mint",
                        f"Large mint of {label}",
                        f"{share:.1%} of the supply minted in one transaction to {a['to']}. Unbacked minting "
                        "is how Resolv's USR depegged in March 2026 and left bad debt in Morpho markets",
                        None,
                        {"contract": c.address, "share": share},
                    )
                )
    return out


def _timelock_alert(e: Event, tl: Contract, contracts: dict[str, Contract]) -> list[Alert]:
    """D3: a call queued, executed or cancelled on a timelock that controls a watched contract. An upgrade (or a
    change of the proxy's admin or owner) of a watched contract is a warn when scheduled: the depositor has the
    timelock's delay to act. Its execution is followed by the contract's own Upgraded event (critical)."""
    a = e.args
    if e.name == "Cancelled":
        return [
            Alert(
                "info",
                e.block,
                e.tx,
                "Admin.Cancelled",
                f"Queued call cancelled on timelock {tl.address[:10]}…",
                f"id {a['id'][:12]}…",
                None,
                {"contract": tl.address},
            )
        ]
    data = a.get("data") or "0x"
    sig = UPGRADE_CALLS.get(data[2:10])
    target = a["target"].lower()
    victim = target
    if sig and sig.split("(")[0] in ("upgrade", "upgradeAndCall", "changeProxyAdmin") and len(data) >= 10 + 64:
        victim = "0x" + data[10 + 24 : 10 + 64].lower()
    watched = contracts.get(victim)
    what = (
        f"{sig.split('(')[0]} of {watched.label}"
        if sig and watched
        else f"call {data[:10]} on {contracts[target].label if target in contracts else target}"
    )
    if e.name == "CallScheduled":
        delay = int(a["delay"])
        lvl = "warn" if sig and watched else "info"
        return [
            Alert(
                lvl,
                e.block,
                e.tx,
                "Admin.CallScheduled",
                f"Scheduled on timelock {tl.address[:10]}…: {what}, executable in {delay / 3600:g} h",
                (
                    "its code can change once the delay has passed; this is the window to reduce or exit before "
                    "the new code (and any new price) applies"
                    if sig and watched
                    else "a governance call is queued on a timelock above your markets"
                ),
                None,
                {"contract": tl.address, "target": target, "victim": victim, "delay": delay, "id": a["id"]},
            )
        ]
    return [
        Alert(
            "warn" if sig and watched else "info",
            e.block,
            e.tx,
            "Admin.CallExecuted",
            f"Executed on timelock {tl.address[:10]}…: {what}",
            "the queued change has landed",
            None,
            {"contract": tl.address, "target": target, "victim": victim, "id": a["id"]},
        )
    ]


def band_findings(contracts: dict[str, Contract], timelock_over, block: int) -> list[Alert]:
    """D4: a custom feed whose floor is close to its answer caps how far the oracle can fall: a larger loss stays
    invisible to the market (no liquidation, hidden bad debt) until new code is installed."""
    out = []
    for c in contracts.values():
        if not c.band:
            continue
        lo, hi, dec, ans = c.band
        room = lo / ans - 1
        if room < -W["feed_band_report_floor"]:
            continue
        tl = timelock_over(c.address)
        via = f"an upgrade through timelock {tl.address[:10]}… ({tl.timelock_delay / 3600:g} h)" if tl else "an upgrade"
        out.append(
            Alert(
                "warn",
                block,
                None,
                "FeedBand",
                f"{c.symbol or c.address[:10]} cannot report below {lo / 10**dec:,.6g} ({room:+.1%}) without {via}",
                f"its band is {lo / 10**dec:,.6g} – {hi / 10**dec:,.6g}, now {ans / 10**dec:,.6g}. A loss larger than "
                f"{-room:.1%} reaches the oracle only after the upgrade: until then the market prices the collateral "
                "at the floor, liquidations stop there and the shortfall is bad debt nobody sees",
                None,
                {"contract": c.address, "floor": lo / 10**dec, "answer": ans / 10**dec, "room": room},
            )
        )
    return out


def assess_changes(
    before: dict[str, tuple], after: dict[str, tuple], contracts: dict[str, Contract], block: int
) -> list[Alert]:
    """D56: slot changes seen at a refresh that no event explained."""
    out = []
    fields = ("implementation", "proxy admin", "beacon", "owner", "price feed")
    level = {"implementation": "critical", "beacon": "critical"}
    for a, now in after.items():
        was = before.get(a)
        if was is None:
            continue
        for name, old, new in zip(fields, was, now):
            if old != new:
                out.append(
                    Alert(
                        level.get(name, "warn"),
                        block,
                        None,
                        "AdminState",
                        f"{name.capitalize()} of {contracts[a].label} changed",
                        f"{old} → {new}, seen at a state refresh (no standard event was emitted)",
                        None,
                        {"contract": a, "field": name},
                    )
                )
    return out


def assess_divergence(
    before: dict[str, float | None], after: dict[str, float | None], markets: dict, block: int
) -> list[Alert]:
    """D58: oracle vs independent price, warn on crossing the threshold."""
    out, th = [], W["oracle_divergence_warn"]
    for mid, d in after.items():
        if d is None or abs(d) < th:
            continue
        d0 = before.get(mid)
        if d0 is not None and abs(d0) >= th:
            continue
        m = markets[mid]
        out.append(
            Alert(
                "warn",
                block,
                None,
                "OracleDivergence",
                f"Oracle of {m.label} is {d:+.1%} from the market price",
                "oracle price vs DefiLlama's collateral ÷ loan price. A fixed-rate or linear PT oracle differs by "
                "design; otherwise the oracle is lagging, misconfigured, or the market is dislocated, and "
                "liquidations follow the oracle",
                None,
                {"market": mid, "gap": d},
            )
        )
    return out
