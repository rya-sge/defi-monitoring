"""A Pendle V2 pool rebuilt from its on-chain state at any block (plan 2026-10-11-pendle-pool, D207–D209).

The quote API answers for now only; the pool's own math answers for any block an archive RPC can read. From
`MarketMathCore.sol` (pendle-core-v2-public): the pool holds PT and SY; with t the time to expiry,

  rate scalar   scalarRoot × 365 days / t
  anchor        e^(lastLnImpliedRate × t / 365 days) − ln(p / (1 − p)) / rate scalar, p = PT / (PT + asset)
  exchange      ln(p' / (1 − p')) / rate scalar + anchor, p' the proportion after the trade (refused above 96 %)
  a PT sale     pays PT / exchange in asset, divided by the fee rate e^(lnFeeRateRoot × t / 365 days)
  implied rate  ln(exchange at the new totals) × 365 days / t, the rate the oracle's TWAP averages

`asset` is SY × the PY index (max of the SY's exchange rate and the YT's stored index). Floating point, not the
contract's fixed point: within a part in a billion of it. Pure, except `read`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from eth_abi import decode

from . import sources as S
from .vault import _call, _uint

YEAR = 365 * 86_400
MAX_PROPORTION = 0.96
ROUTER = "0x888888888889758f76e7103c6cbf23abbf58f946"  # Pendle RouterV4: the fee config readState is asked for
STATE_T = ["int256", "int256", "int256", "address", "int256", "uint256", "uint256", "uint256", "uint256"]


@dataclass
class Pool:
    """A Pendle market's state at one block, in token units (PT, SY and the asset share their decimals)."""

    market: str
    block: int
    now: int  # the block's timestamp
    total_pt: float
    total_sy: float
    scalar_root: float
    expiry: int
    ln_fee_rate_root: float
    reserve_fee_percent: float
    last_ln_rate: float
    index: float  # asset per SY, in the asset's units
    decimals: int = 18  # the PT's (and the asset's)

    @property
    def t(self) -> float:
        return self.expiry - self.now

    @property
    def total_asset(self) -> float:
        return self.total_sy * self.index

    @property
    def rate_scalar(self) -> float:
        return self.scalar_root * YEAR / self.t

    @property
    def anchor(self) -> float:
        p = self.total_pt / (self.total_pt + self.total_asset)
        return math.exp(self.last_ln_rate * self.t / YEAR) - math.log(p / (1 - p)) / self.rate_scalar

    @property
    def implied_apy(self) -> float:
        return math.exp(self.last_ln_rate) - 1

    @property
    def pt_price(self) -> float:
        """Asset per PT at the pool's last implied rate."""
        return math.exp(-self.last_ln_rate * self.t / YEAR)


def _exchange(pool: Pool, total_pt: float, total_asset: float, anchor: float) -> float | None:
    p = total_pt / (pool.total_pt + pool.total_asset)  # the denominator is the pre-trade total, as in the contract
    if p > MAX_PROPORTION or p <= 0:
        return None
    e = math.log(p / (1 - p)) / pool.rate_scalar + anchor
    return e if e >= 1 else None


def sell_pt(pool: Pool, pt_in: float) -> tuple[float, float] | None:
    """D207, pure: (asset to the seller, the pool's new ln implied rate) for a sale of `pt_in` PT into the pool; None
    when the pool refuses it (proportion above 96 %, or an exchange rate below one)."""
    anchor = pool.anchor
    pre = _exchange(pool, pool.total_pt + pt_in, pool.total_asset, anchor)
    if pre is None:
        return None
    fee_rate = math.exp(pool.ln_fee_rate_root * pool.t / YEAR)
    gross = pt_in / pre
    fee = gross * (fee_rate - 1) / fee_rate
    out = gross - fee
    reserve = fee * pool.reserve_fee_percent / 100
    pt, asset = pool.total_pt + pt_in, pool.total_asset - out - reserve
    # the new implied rate: the exchange rate at the new totals, same anchor, proportion over the new total
    p = pt / (pt + asset)
    if not 0 < p < 1:
        return None
    e = math.log(p / (1 - p)) / pool.rate_scalar + anchor
    return out, (math.log(e) * YEAR / pool.t if e > 1 else 0.0)


def max_sale(pool: Pool) -> float:
    """D207, pure: the largest PT sale the pool accepts (its proportion reaches 96 %)."""
    return MAX_PROPORTION * (pool.total_pt + pool.total_asset) - pool.total_pt


def sale_for_apy(pool: Pool, apy: float) -> float | None:
    """D208, pure: the PT sale that lifts the pool's implied APY to `apy`, by bisection; None above what the pool
    accepts, 0 when it is already there."""
    target = math.log(1 + apy)
    if target <= pool.last_ln_rate:
        return 0.0
    hi = max_sale(pool) * (1 - 1e-9)
    top = sell_pt(pool, hi)
    if top is None or top[1] < target:
        return None
    lo = 0.0
    for _ in range(100):
        mid = (lo + hi) / 2
        r = sell_pt(pool, mid)
        if r is not None and r[1] >= target:
            hi = mid
        else:
            lo = mid
    return hi


# --- I/O


def read(f: S.Fetcher, market: str, block: int) -> Pool:
    """D209: the market's state at `block`: `readState`, its tokens, the SY's exchange rate, the YT's stored index and
    the block's timestamp. Needs an archive RPC for an old block."""
    market = market.lower()
    st, toks = S.rpc_batch(
        f, [_call(market, "readState(address)", ["address"], [ROUTER]), _call(market, "readTokens()")], block
    )
    pt, sy, lp, _, scalar, expiry, fee, reserve, last = decode(STATE_T, bytes.fromhex(st[2:]))
    sy_addr, pt_addr, yt_addr = ("0x" + toks[2 + 64 * i + 24 : 2 + 64 * (i + 1)] for i in range(3))
    rate, stored, dec = (
        _uint(x)
        for x in S.rpc_batch(
            f,
            [_call(sy_addr, "exchangeRate()"), _call(yt_addr, "pyIndexStored()"), _call(pt_addr, "decimals()")],
            block,
        )
    )
    unit = 10 ** (dec or 18)  # PT and the asset share these decimals; SY has 18, its rate converts
    head = S.rpc(f, "eth_getBlockByNumber", [hex(block), False]) or {}
    return Pool(
        market,
        block,
        int(head.get("timestamp", "0x0"), 16),
        pt / unit,
        sy / 1e18,
        scalar / 1e18,
        expiry,
        fee / 1e18,
        float(reserve),
        last / 1e18,
        max(rate or 0, stored or 0) / unit,
        dec or 18,
    )
