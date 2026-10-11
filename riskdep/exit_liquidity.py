"""Exit liquidity of a collateral, live from KyberSwap (plan 2026-10-11-exit-liquidity, D212–D214; GAP K27).

Will a liquidator act? Only if it can sell what it seizes for at least what it repaid. For each hit market, the
collateral is quoted on KyberSwap's aggregator into the market's loan token on a fixed ladder of sizes
(`exit_liquidity.sizes`, loan units), so a recording serves any shock size. The slippage is measured against the
oracle's price, the one the liquidation is settled at: 1 − amount out ÷ the size. At the size the incident liquidates:

  none   no route at the ladder's smallest size: nobody liquidates
  thin   slippage above `exit_liquidity.thin_impact`, or a size beyond the largest the aggregator routes
  deep   otherwise

The registry's routes measured by hand on 2026-10-11 stay as the fallback when a quote is not available (offline with
no recording, or the API down). Pure, except `ladder`.
"""

from __future__ import annotations

import numpy as np

from . import sources as S
from .discover import REGISTRY

E = REGISTRY["exit_liquidity"]
KYBER = "https://aggregator-api.kyberswap.com/ethereum/api/v1/routes"


def _out(r: dict) -> dict:
    """Keep what the ladder reads: the amount out, or the refusal (a 4xx body with its code and message)."""
    rs = ((r or {}).get("data") or {}).get("routeSummary") or {}
    return {"code": (r or {}).get("code"), "message": (r or {}).get("message"), "amountOut": rs.get("amountOut")}


def ladder(f: S.Fetcher, collateral: str, loan: str, price: int, loan_decimals: int) -> dict[float, float | None]:
    """D212: the slippage of selling the collateral into the loan token at each size of the ladder, against the oracle
    `price` (Morpho's scale: loan raw = collateral raw × price / 1e36); None from the first size with no route.
    Raises `sources.CacheMiss` offline with no recording, `SourceError` when the API does not answer."""
    out: dict[float, float | None] = {}
    for size in E["sizes"]:
        want = int(size * 10**loan_decimals)
        amount = want * 10**36 // price if price else 0
        r = f.get_json(f"{KYBER}?tokenIn={collateral}&tokenOut={loan}&amountIn={amount}", transform=_out)
        got = int(r["amountOut"]) if r.get("amountOut") else 0
        out[float(size)] = 1 - got / want if got else None
        if not got:
            break
    return out


def at(quotes: dict[float, float | None], size: float) -> tuple[str, float | None, float]:
    """D213, pure: (route, slippage, capacity) at `size` loan units: the slippage interpolated between the routed sizes
    (the smallest's below it), the capacity the largest routed size."""
    routed = sorted((s, i) for s, i in quotes.items() if i is not None)
    if not routed:
        return "none", None, 0.0
    sizes, imps = zip(*routed)
    cap = sizes[-1]
    impact = float(np.interp(size, sizes, imps))
    thin = impact > E["thin_impact"] or (size > cap and None in quotes.values())
    return ("thin" if thin else "deep"), impact, cap


def text(route: str, impact: float | None, cap: float, size: float, unit: str, source: str) -> str:
    """The hit's exit-liquidity line."""
    if route == "none":
        return f"no route for the collateral on {source}: liquidators cannot sell what they seize"
    beyond = size > cap
    return (
        f"selling the {size:,.0f} {unit} the liquidations seize costs {impact:.2%} against the oracle on {source}"
        + (f"; the aggregator routes at most {cap:,.0f}" if beyond else "")
    )
