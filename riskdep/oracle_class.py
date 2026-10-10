"""Oracle classes: does a market move of the collateral reach the oracle's price? (plan 2026-10-10-sibling-markets,
D82–D84).

  price-tracking    a fall of the collateral's market price lowers the oracle: borrowers get liquidated, and the
                    liquidations can cascade through the pool the oracle reads
  constant-price    it does not (fixed value, exchange rate, NAV, linear discount): nobody is liquidated on a depeg,
                    and the loss lands on the lenders once the collateral is worth less than the debt
  not classified    no rule decides; shown, never guessed

A Morpho ChainlinkOracleV2 prices base vault × base feeds ÷ quote vault × quote feeds. Only the base side prices the
collateral; the quote side prices the loan token and is ignored. The oracle is price-tracking if one base input is,
constant-price if all are. Rules for one input, the first that applies wins, are in `classify_input`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eth_abi import decode

from . import sources as S
from .discover import REGISTRY
from .vault import _call

PRICE_TRACKING = "price-tracking"
CONSTANT_PRICE = "constant-price"
NOT_CLASSIFIED = "not classified"
BASE_ROLES = ("BASE_VAULT", "BASE_FEED_1", "BASE_FEED_2")
MAX_DEPTH = 2  # composites inside composites, e.g. Ojo min → timestamp adapter → linear discount

G = REGISTRY["graph"]
ROUND_T = ["uint80", "int256", "uint256", "uint256", "uint80"]


@dataclass
class Probe:
    """What was read of one oracle input."""

    address: str
    vault: bool = False  # an ERC-4626 share whose exchange rate the oracle applies (BASE_VAULT)
    decimals: int | None = None
    description: str | None = None
    answer: int | None = None
    history: list[int] = field(default_factory=list)  # answers of distinct past rounds, oldest first, then the latest
    getters: dict[str, int] = field(default_factory=dict)  # structural getter of `oracle_getters` → its answer
    children: list[Probe] = field(default_factory=list)  # composite or wrapper inputs (`oracle_children_getters`)
    name: str | None = None  # verified contract name (Etherscan), the implementation's for a proxy
    market: str | None = None  # `market()` of a Pendle TWAP input: the pool whose PT price it reads (engine D115)

    def pendle_market(self) -> str | None:
        """The Pendle pool this input, or one of its parts, reads with a TWAP (once `read_pendle_markets` ran)."""
        if self.market:
            return self.market
        return next((m for c in self.children if (m := c.pendle_market())), None)

    @property
    def label(self) -> str:
        return self.description or self.name or f"{self.address[:6]}…{self.address[-4:]}"


def _combine(classes: list[tuple[str, str]], what: str) -> tuple[str, str]:
    """Several inputs priced together (a product, or a min): a market move reaches the result through any one."""
    tracking = [b for c, b in classes if c == PRICE_TRACKING]
    if tracking:
        return PRICE_TRACKING, f"{what}: {tracking[0]}"
    if classes and all(c == CONSTANT_PRICE for c, _ in classes):
        return CONSTANT_PRICE, f"{what}, none follows a market: " + "; ".join(b for _, b in classes)
    unknown = [b for c, b in classes if c == NOT_CLASSIFIED]
    return NOT_CLASSIFIED, f"{what}: " + (unknown[0] if unknown else "no input")


def classify_input(p: Probe, rules: dict = G) -> tuple[str, str]:
    """Pure: (class, basis) of one oracle input."""
    if p.vault:
        return (
            CONSTANT_PRICE,
            f"{p.label}: an ERC-4626 exchange rate, which follows the vault's accounting, not a market",
        )
    if p.children:
        return _combine(
            [classify_input(c, rules) for c in p.children], f"{p.label} combines {len(p.children)} input(s)"
        )
    for g in rules["oracle_getters"]:
        v = p.getters.get(g["getter"])
        if v is not None and (g["when"] == "answers" or v != 0):
            return g["class"], f"{p.label}: {g['getter']} = {v}, {g['basis']}"
    past = len(p.history) - 1
    if past >= rules["oracle_history_min"]:
        steps = list(zip(p.history, p.history[1:]))
        falls = sum(1 for a, b in steps if b < a)
        changes = sum(1 for a, b in steps if b != a)
        if changes and falls / changes >= rules["oracle_fall_share"]:
            return (
                PRICE_TRACKING,
                f"{p.label}: fell {falls} times in {changes} changes over {past} rounds, a market price",
            )
        if not changes:
            return CONSTANT_PRICE, f"{p.label}: the same answer over {past} rounds"
        return CONSTANT_PRICE, f"{p.label}: fell {falls} times in {changes} changes over {past} rounds, an accrual rate"
    if not p.history[:-1] and p.answer is not None and p.decimals is not None and p.answer == 10**p.decimals:
        return CONSTANT_PRICE, f"{p.label}: answers exactly 1.0 with no round history, a pegged or hardcoded value"
    text = f"{p.description or ''} {p.name or ''}".lower()
    for pat in rules["oracle_patterns"]:
        if pat["match"].lower() in text:
            return pat["class"], f"{p.label}: matches '{pat['match']}', {pat['basis']}"
    return NOT_CLASSIFIED, f"{p.label}: no round history, no known structure or name"


def classify_oracle(base: list[Probe], standard: bool, rules: dict = G) -> tuple[str, str]:
    """Pure: (class, basis) of a market oracle from its base-side inputs. `standard` is True for a Morpho
    ChainlinkOracleV2; a custom oracle is passed as one input (itself)."""
    if standard and not base:
        return CONSTANT_PRICE, "no base input: the price is the oracle's fixed scale factor"
    return _combine([classify_input(p, rules) for p in base], "base side")


def _word(raw: str | None) -> int | None:
    return int(raw[2:66], 16) if raw and len(raw) >= 66 else None


def _string(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        return decode(["string"], bytes.fromhex(raw[2:]))[0] or None
    except Exception:
        return None


def _contract_name(f: S.Fetcher, address: str) -> str | None:
    """Verified name from Etherscan (optional key): the implementation's name for a proxy Etherscan recognises."""
    src = S.contract_source(f, address)
    if not src:
        return None
    if src.get("proxy") and src.get("implementation") and src["implementation"] != address.lower():
        impl = S.contract_source(f, src["implementation"])
        if impl and impl.get("name"):
            return impl["name"]
    return src.get("name")


def probe(f: S.Fetcher, address: str, block, vault: bool = False, depth: int = 0) -> Probe:
    """Read one input: one batch for its answer, description and structure, one for its round history."""
    p = Probe(address.lower(), vault=vault)
    if vault:
        return p
    kids, getters = list(G["oracle_children_getters"]), [g["getter"] for g in G["oracle_getters"]]
    sigs = ["decimals()", "description()", "latestRoundData()"] + kids + getters
    res = S.rpc_batch(f, [_call(p.address, s) for s in sigs], block)
    p.decimals, p.description = _word(res[0]), _string(res[1])
    latest = None
    if res[2]:
        try:
            latest = decode(ROUND_T, bytes.fromhex(res[2][2:]))
            p.answer = latest[1]
        except Exception:
            latest = None
    for sig, raw in zip(getters, res[3 + len(kids) :]):
        if raw and _word(raw) is not None:
            p.getters[sig] = _word(raw)
    children = [("0x" + raw[26:66]).lower() for raw in res[3 : 3 + len(kids)] if raw and _word(raw)]
    if children and depth < MAX_DEPTH:
        p.children = [probe(f, c, block, depth=depth + 1) for c in dict.fromkeys(children)]
        return p
    if latest and latest[0] > 1:
        p.history = _history(f, p.address, latest, block)
    elif p.answer is not None:
        p.history = [p.answer]
    if classify_input(p)[0] == NOT_CLASSIFIED:  # the name is the last resort: it needs the optional Etherscan key
        p.name = _contract_name(f, p.address)
    return p


def read_pendle_markets(f: S.Fetcher, p: Probe, block) -> None:
    """Fill `market` on every Pendle TWAP input (one with a `twapDuration`) of a probe tree, one call each, so that the
    graph can tie the input to its pool (engine D115). Kept out of `probe`'s batch, which the other modes share: the
    batch's cache key stays the one their recordings hold."""
    if p.getters.get("twapDuration()"):
        raw = S.rpc_batch(f, [_call(p.address, "market()")], block)[0]
        if raw and _word(raw):
            p.market = ("0x" + raw[26:66]).lower()
    for c in p.children:
        read_pendle_markets(f, c, block)


def _history(f: S.Fetcher, address: str, latest: tuple, block) -> list[int]:
    """Answers of the last `oracle_history_rounds` rounds with a distinct, older timestamp, oldest first."""
    rid, k = latest[0], G["oracle_history_rounds"]
    ids = [rid - i for i in range(1, k + 1) if rid - i > 0]
    res = S.rpc_batch(f, [_call(address, "getRoundData(uint80)", ["uint80"], [i]) for i in ids], block)
    points = [(latest[3], latest[1])]
    for raw in res:
        if not raw:
            break
        try:
            r = decode(ROUND_T, bytes.fromhex(raw[2:]))
        except Exception:
            break
        if not r[3] or r[3] >= points[-1][0]:
            break  # a feed without real rounds returns its latest answer for any id
        points.append((r[3], r[1]))
    return [a for _, a in reversed(points)]


MORPHO_ORACLE_GETTERS = [
    "BASE_VAULT()",
    "BASE_FEED_1()",
    "BASE_FEED_2()",
    "QUOTE_VAULT()",
    "QUOTE_FEED_1()",
    "QUOTE_FEED_2()",
]


def classify_market_oracle(
    f: S.Fetcher, oracle: str, block
) -> tuple[str, str, list[Probe], list[tuple[str, str]], bool]:
    """(class, basis, base-side probes, (role, address) of each non-zero getter, is a Morpho ChainlinkOracleV2) of a
    market oracle. A custom oracle (no ChainlinkOracleV2 getters) is read as one input (D83)."""
    res = S.rpc_batch(f, [_call(oracle, s) for s in MORPHO_ORACLE_GETTERS], block)
    feeds = [(name[:-2], "0x" + r[-40:]) for name, r in zip(MORPHO_ORACLE_GETTERS, res) if r and int(r, 16)]
    standard = any(r is not None for r in res)
    base = [probe(f, a, block, vault="VAULT" in n) for n, a in feeds if n in BASE_ROLES]
    if not standard:
        base = [probe(f, oracle, block)]
    cls, basis = classify_oracle(base, standard)
    return cls, basis, base, feeds, standard
