"""A borrower's Morpho Blue positions, read on-chain the way Blue computes them (D37).

debt  = borrowShares × (totalBorrowAssets + 1) / (totalBorrowShares + 10^6)
HF    = collateral × oracle price / 10^36 × LLTV / debt
drop  = 1 − 1 / HF, the oracle fall that brings HF to 1
APY   = e^(rate per second × seconds per year) − 1, rate from the market's IRM borrowRateView
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from eth_abi import decode

from . import sources as S
from .abi import MORPHO_BLUE
from .discover import REGISTRY
from .vault import _call, _symbol, _uint

WAD = 10**18
YEAR = 365 * 86400
PARAMS_T = "(address,address,address,address,uint256)"
MARKET_T = "(uint128,uint128,uint128,uint128,uint128,uint128)"


@dataclass
class BorrowMarket:
    id: str
    loan_token: str
    collateral_token: str
    oracle: str
    irm: str
    lltv_raw: int
    loan_symbol: str = "?"
    collateral_symbol: str = "?"
    loan_decimals: int = 18
    collateral_decimals: int = 18

    @property
    def lltv(self) -> float:
        return self.lltv_raw / WAD

    @property
    def label(self) -> str:
        return f"{self.collateral_symbol}/{self.loan_symbol} (LLTV {self.lltv:.1%})"

    @property
    def params(self) -> tuple:
        return (self.loan_token, self.collateral_token, self.oracle, self.irm, self.lltv_raw)


@dataclass
class BorrowState:
    id: str
    collateral: int  # collateral token units (raw)
    borrow_shares: int
    debt: int  # loan token units (raw)
    price: int | None  # oracle price, scaled 10^36 × loan / collateral decimals
    total_supply_assets: int
    total_borrow_assets: int
    rate_per_second: int | None  # WAD

    @property
    def collateral_value(self) -> int | None:
        """Collateral valued by the oracle, in loan-token units (raw)."""
        return self.collateral * self.price // 10**36 if self.price is not None else None

    def hf(self, lltv: float) -> float | None:
        if self.debt == 0:
            return math.inf
        if self.price is None:
            return None
        return self.collateral_value * lltv / self.debt

    def liquidation_drop(self, lltv: float) -> float | None:
        h = self.hf(lltv)
        if h is None or math.isinf(h):
            return h
        return max(0.0, 1 - 1 / h)

    @property
    def utilization(self) -> float:
        return self.total_borrow_assets / self.total_supply_assets if self.total_supply_assets else 0.0

    @property
    def apy(self) -> float | None:
        return math.expm1(self.rate_per_second * YEAR / WAD) if self.rate_per_second is not None else None


def _decimals(f: S.Fetcher, token: str, block) -> int:
    return _uint(S.rpc_batch(f, [_call(token, "decimals()")], block)[0]) or 18


def discover_markets(f: S.Fetcher, ids: list[str], block) -> dict[str, BorrowMarket]:
    raws = S.rpc_batch(
        f, [_call(MORPHO_BLUE, "idToMarketParams(bytes32)", ["bytes32"], [bytes.fromhex(i[2:])]) for i in ids], block
    )
    out = {}
    for mid, raw in zip(ids, raws):
        if not raw:
            continue
        loan, coll, orc, irm, lltv = decode(["address"] * 4 + ["uint256"], bytes.fromhex(raw[2:]))
        m = BorrowMarket(mid, loan.lower(), coll.lower(), orc.lower(), irm.lower(), lltv)
        m.loan_symbol, m.collateral_symbol = _symbol(f, m.loan_token, block), _symbol(f, m.collateral_token, block)
        m.loan_decimals, m.collateral_decimals = (
            _decimals(f, m.loan_token, block),
            _decimals(f, m.collateral_token, block),
        )
        out[mid] = m
    return out


def read_borrows(f: S.Fetcher, markets: dict[str, BorrowMarket], user: str, block) -> dict[str, BorrowState]:
    ids = list(markets)
    calls = []
    for mid in ids:
        b = bytes.fromhex(mid[2:])
        calls += [
            _call(MORPHO_BLUE, "position(bytes32,address)", ["bytes32", "address"], [b, user]),
            _call(MORPHO_BLUE, "market(bytes32)", ["bytes32"], [b]),
            _call(markets[mid].oracle, "price()"),
        ]
    res = S.rpc_batch(f, calls, block)
    raw_markets, out = {}, {}
    for i, mid in enumerate(ids):
        pos, mk, price = res[3 * i : 3 * i + 3]
        _, bshares, coll = decode(["uint256", "uint128", "uint128"], bytes.fromhex(pos[2:])) if pos else (0, 0, 0)
        mw = decode(["uint128"] * 6, bytes.fromhex(mk[2:])) if mk else (0,) * 6
        raw_markets[mid] = mw
        debt = bshares * (mw[2] + 1) // (mw[3] + 10**6) if bshares else 0
        out[mid] = BorrowState(mid, coll, bshares, debt, _uint(price), mw[0], mw[2], None)
    rates = S.rpc_batch(
        f,
        [
            _call(
                markets[mid].irm,
                f"borrowRateView({PARAMS_T},{MARKET_T})",
                [PARAMS_T, MARKET_T],
                [markets[mid].params, raw_markets[mid]],
            )
            for mid in ids
        ],
        block,
    )
    for mid, r in zip(ids, rates):
        out[mid].rate_per_second = _uint(r)
    return out


@dataclass
class Supplier:
    address: str  # the supplier of the market: an EOA, a Vault V1, or a Vault V2's adapter
    actor: str  # who owns the capital: the address itself, or the adapter's parent vault
    label: str
    kind: str  # "Vault V2" | "Vault V1" | "lender"
    assets: int  # loan-token units (raw)
    share: float  # of the market's supply


def _name(f: S.Fetcher, addr: str, block) -> str | None:
    raw = S.rpc_batch(f, [_call(addr, "name()")], block)[0]
    try:
        return decode(["string"], bytes.fromhex(raw[2:]))[0] if raw else None
    except Exception:
        return None


def top_suppliers(
    f: S.Fetcher, m: BorrowMarket, block, min_share: float | None = None, limit: int | None = None
) -> list[Supplier]:
    """A market's main lenders (D41): the top suppliers by shares from the Morpho API, amounts on-chain;
    a Vault V2 supplies through its adapter (resolved with parentVault()), a Vault V1 is identified by
    MORPHO() and withdrawQueueLength()."""
    w = REGISTRY["watch"]
    min_share = w["lender_min_share"] if min_share is None else min_share
    limit = w["lender_max"] if limit is None else limit
    try:
        # The query text is part of the request cache key, so it is concatenated rather
        # than interpolated: the string must stay byte for byte what the snapshots recorded.
        q = (
            """query($id:String!){ marketPositions(first:"""
            + str(limit)
            + """, where:{marketUniqueKey_in:[$id], chainId_in:[1]},
              orderBy: SupplyShares, orderDirection: Desc){ items{ user{ address } } } }"""
        )
        items = S.morpho(f, q, {"id": m.id})["marketPositions"]["items"]
    except (S.SourceError, S.CacheMiss, KeyError, TypeError):
        return []
    addrs = [i["user"]["address"].lower() for i in items]
    if not addrs:
        return []
    mid = bytes.fromhex(m.id[2:])
    res = S.rpc_batch(
        f,
        [_call(MORPHO_BLUE, "market(bytes32)", ["bytes32"], [mid])]
        + [_call(MORPHO_BLUE, "position(bytes32,address)", ["bytes32", "address"], [mid, a]) for a in addrs]
        + [_call(a, "parentVault()") for a in addrs],
        block,
    )
    tsa, tss = decode(["uint128"] * 6, bytes.fromhex(res[0][2:]))[:2]
    out = []
    for i, a in enumerate(addrs):
        pos, parent = res[1 + i], res[1 + len(addrs) + i]
        shares = decode(["uint256", "uint128", "uint128"], bytes.fromhex(pos[2:]))[0] if pos else 0
        assets = shares * (tsa + 1) // (tss + 10**6)
        share = assets / tsa if tsa else 0.0
        if share < min_share:
            continue
        if parent and int(parent, 16):
            vault = ("0x" + parent[-40:]).lower()
            nm = _name(f, vault, block)
            out.append(Supplier(a, vault, f"Vault {nm}" if nm else f"Vault {vault[:10]}…", "Vault V2", assets, share))
            continue
        nm = _name(f, a, block)
        morpho, wq = S.rpc_batch(f, [_call(a, "MORPHO()"), _call(a, "withdrawQueueLength()")], block)
        is_v1 = bool(morpho and ("0x" + morpho[-40:]).lower() == MORPHO_BLUE and wq)
        label = (f"Vault {nm}" if is_v1 and nm else nm) or f"Lender {a[:6]}…{a[-4:]}"
        out.append(Supplier(a, a, label, "Vault V1" if is_v1 else "lender", assets, share))
    return out
