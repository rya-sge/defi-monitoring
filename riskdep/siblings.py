"""Sibling markets: Blue markets no actor of the graph holds that can move the price of a held market's collateral or
share its price inputs (plan 2026-10-10-sibling-markets, D76–D79).

A candidate is a sibling of a seed (a held market) through any of:
  same collateral      it takes the seed's collateral
  same underlying      its collateral and the seed's are linked: a PT and its Pendle underlying, an ERC-4626 share and
                       its asset(), either way round, or two tokens with the same underlying
  shared price input   its oracle is the seed's, or reads on its base side a feed or vault the seed's reads on its base
                       side; quote-side feeds (USDC / USD under most oracles) never count
  lends a linked asset its loan token is the seed's collateral or that collateral's underlying: an exploit of its own
                       collateral would borrow that asset and dump it
The registry's stablecoins (USDC, USDT) are terminal and never link markets by token. The Morpho API finds the
candidates; the graph then re-reads each retained one on-chain (D78).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eth_abi import decode

from . import sources as S
from .discover import REGISTRY
from .vault import _call

G = REGISTRY["graph"]
TERMINAL = frozenset(REGISTRY["stables"])
PAGE = 500
CHUNK = 200

SAME_COLLATERAL = "same collateral"
SAME_UNDERLYING = "same underlying"
SHARED_INPUT = "shared price input"
LENDS_LINKED = "lends a linked asset"

CANDIDATES_QUERY = """query($skip:Int!, $min:Float!){ markets(first:500, skip:$skip,
  where:{chainId_in:[1], supplyAssetsUsd_gte:$min}){ pageInfo{ countTotal } items{ marketId oracleAddress
  collateralAsset{ address symbol } loanAsset{ address symbol }
  oracle{ data{
    ... on MorphoChainlinkOracleV2Data{ baseFeedOne{address} baseFeedTwo{address} baseOracleVault{address} }
    ... on MorphoChainlinkOracleData{ baseFeedOne{address} baseFeedTwo{address} baseOracleVault{address} } } }
  state{ borrowAssetsUsd supplyAssetsUsd } } } }"""


@dataclass
class Market:
    """A seed or a candidate, as the matcher sees it; addresses lowercase."""

    id: str
    collateral: str
    loan: str
    oracle: str
    base_inputs: frozenset[str] = frozenset()
    borrow_usd: float = 0.0
    label: str = ""
    tvl_usd: float = 0.0  # supplied assets in USD, the size floor (D79)


@dataclass
class Sibling:
    id: str
    label: str
    borrow_usd: float
    links: list[tuple[str, str]] = field(default_factory=list)  # (seed market id, relation)


def family(token: str, underlying: dict[str, str]) -> set[str]:
    """Tokens whose price moves with `token`: itself, its underlying, and every token with either as underlying. A
    terminal underlying is not followed: every USDC vault share would otherwise be family of syrupUSDC."""
    core = {token} | ({underlying[token]} if underlying.get(token) not in (None, *TERMINAL) else set())
    return core | {t for t, u in underlying.items() if u in core}


def relations(seed: Market, cand: Market, underlying: dict[str, str]) -> list[str]:
    """Pure: why `cand` is a sibling of `seed`, empty when it is not."""
    out = []
    c = seed.collateral
    linked = c not in TERMINAL
    if linked and cand.collateral == c:
        out.append(SAME_COLLATERAL)
    elif linked and cand.collateral not in TERMINAL and cand.collateral in family(c, underlying):
        out.append(SAME_UNDERLYING)
    if cand.oracle == seed.oracle or cand.base_inputs & seed.base_inputs:
        out.append(SHARED_INPUT)
    if linked and cand.loan not in TERMINAL and cand.loan in {c, underlying.get(c)}:
        out.append(LENDS_LINKED)
    return out


def match(
    seeds: list[Market],
    candidates: list[Market],
    underlying: dict[str, str],
    min_tvl_usd: float = G["sibling_min_tvl_usd"],
    max_per_seed: int = G["sibling_max_per_seed"],
) -> list[Sibling]:
    """Pure: the siblings of every seed, one hop only (D76), with at least `min_tvl_usd` supplied and at most
    `max_per_seed` per seed, largest borrow first (D79): borrow is what liquidations sell. A market related to several
    seeds is one sibling with every link. Seeds are never filtered by size: a small held market can sit next to a
    large sibling (PRIME/USDC, $1.8M, next to PRIME/PYUSD, $189M)."""
    held = {s.id for s in seeds}
    found: dict[str, Sibling] = {}
    for seed in seeds:
        rows = []
        for cand in candidates:
            if cand.id in held or cand.tvl_usd < min_tvl_usd:
                continue
            rel = relations(seed, cand, underlying)
            if rel:
                rows.append((cand, rel))
        rows.sort(key=lambda r: -r[0].borrow_usd)
        for cand, rel in rows[:max_per_seed]:
            sib = found.setdefault(cand.id, Sibling(cand.id, cand.label, cand.borrow_usd))
            sib.links += [(seed.id, r) for r in rel]
    return sorted(found.values(), key=lambda s: -s.borrow_usd)


# --- I/O


def candidates(f: S.Fetcher, min_tvl_usd: float = G["sibling_min_tvl_usd"]) -> list[Market]:
    """Every Ethereum Blue market with at least `min_tvl_usd` supplied, from the Morpho API, paged."""
    out, skip = [], 0
    while True:
        d = S.morpho(f, CANDIDATES_QUERY, {"skip": skip, "min": float(min_tvl_usd)})["markets"]
        for m in d["items"]:
            if not m.get("collateralAsset") or not m.get("loanAsset"):
                continue  # an idle market (no collateral) cannot be a sibling
            data, state = (m.get("oracle") or {}).get("data") or {}, m.get("state") or {}
            inputs = {
                data[k]["address"].lower()
                for k in ("baseFeedOne", "baseFeedTwo", "baseOracleVault")
                if data.get(k) and data[k].get("address")
            }
            out.append(
                Market(
                    m["marketId"].lower(),
                    m["collateralAsset"]["address"].lower(),
                    m["loanAsset"]["address"].lower(),
                    (m.get("oracleAddress") or "").lower(),
                    frozenset(inputs),
                    float(state.get("borrowAssetsUsd") or 0.0),
                    f"{m['collateralAsset']['symbol']}/{m['loanAsset']['symbol']}",
                    float(state.get("supplyAssetsUsd") or 0.0),
                )
            )
        skip += PAGE
        if not d["items"] or skip >= d["pageInfo"]["countTotal"]:
            return out


def underlyings(f: S.Fetcher, tokens: set[str], block) -> dict[str, tuple[str, str]]:
    """token → (underlying, how): 'pendle' for a PT (Pendle markets' underlyingAsset), 'erc4626' for a share that
    answers asset() with another token. One Pendle list per status (cached, as `discover` reads them) and one
    asset() batch per 200 tokens."""
    tokens = {t.lower() for t in tokens}
    out: dict[str, tuple[str, str]] = {}
    for status in ("active", "inactive"):
        try:
            markets = f.get_json(f"{S.PENDLE}/v1/1/markets/{status}")["markets"]
        except (S.SourceError, S.CacheMiss, KeyError, TypeError):
            continue
        for m in markets:
            pt = m["pt"].split("-", 1)[-1].lower()
            if pt in tokens and pt not in out:
                out[pt] = (m["underlyingAsset"].split("-", 1)[-1].lower(), "pendle")
    rest = sorted(t for t in tokens if t not in out)
    res = []
    for i in range(0, len(rest), CHUNK):
        res += S.rpc_batch(f, [_call(t, "asset()") for t in rest[i : i + CHUNK]], block)
    for t, raw in zip(rest, res):
        if raw and len(raw) == 66:
            try:
                a = decode(["address"], bytes.fromhex(raw[2:]))[0].lower()
            except Exception:
                continue
            if int(a, 16) and a != t:
                out[t] = (a, "erc4626")
    return out
