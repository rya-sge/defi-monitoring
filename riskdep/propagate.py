"""How a shock on one layer reaches the position. Pure functions, no I/O.

Shocks are severities in [0, 1] keyed by event id:
  chain         liveness / settlement loss          value × (1 − s)
  issuer_hack   backing lost, SY exchange rate falls value × (1 − s), every oracle sees it
  issuer_depeg  market price of the underlying falls trough × (1 − s), (1 − recovery) of it stays;
                a market-tracking oracle sees the trough amplified by the PT stress discount
  amm           Pendle core / SY adapter exploit     value × (1 − s), every oracle sees it
  oracle        the oracle misreports downward       oracle reading × (1 − s), no real loss
  lending       collateral stolen from the market    value × (1 − s), no liquidation needed
  pt_yield      the PT's implied yield rises by s    market price × ((1 + y) / (1 + y + s))^T, T years to maturity;
                (D169)                               a market-tracking oracle sees it, a linear one does not; held to
                                                     maturity the PT still redeems at par, so the loss is realised
                                                     only through a liquidation at the depressed price
  borrow_rate   the borrow APY is s over the horizon debt grows by (s − today's APY) × the horizon; it can cross the
                (D170)                               liquidation threshold

A borrower is liquidated when the oracle-seen collateral × LLTV < debt; the liquidator repays
the debt and seizes debt × LIF worth of collateral at the oracle price. Without liquidation the
borrower keeps max(0, value − debt) (limited liability).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LossBreakdown:
    loss_usd: float
    liquidated: bool
    true_value_usd: float
    oracle_value_usd: float
    path: list[str] = field(default_factory=list)


def pt_stress(implied_apy: float, pt_years: float, spike: float) -> float:
    """D236, pure: the PT's extra fall in a depeg, from a spike of its implied yield as LPs and holders leave the
    pool: 1 − ((1 + y) / (1 + y + spike))^T; none at maturity."""
    return 1 - ((1 + implied_apy) / (1 + implied_apy + spike)) ** pt_years if pt_years > 0 else 0.0


def loss(
    collateral_usd: float,
    debt_usd: float,
    lltv: float | None,
    lif: float | None,
    oracle_mode: str,
    shocks: dict[str, float],
    recovery: float = 0.0,
    pt_stress_spike: float = 0.098,
    pt_years: float = 0.0,
    implied_apy: float = 0.0,
    borrow_apy: float = 0.0,
    horizon_years: float = 0.0,
) -> LossBreakdown:
    v_true = collateral_usd
    v_oracle = collateral_usd
    path: list[str] = []
    equity0 = collateral_usd - debt_usd

    s = shocks.get("borrow_rate", 0.0)
    if s and debt_usd and horizon_years:
        extra = debt_usd * (s - borrow_apy) * horizon_years
        debt_usd += extra
        path.append(f"borrow rate {s:.1%} instead of {borrow_apy:.1%}: debt +${extra:,.0f} over the horizon")

    s = shocks.get("pt_yield", 0.0)
    if s and pt_years > 0:
        f = ((1 + implied_apy) / (1 + implied_apy + s)) ** pt_years
        if oracle_mode == "market-tracking":
            v_oracle *= f
            path.append(
                f"implied yield +{s:.1%} pts: PT price −{1 - f:.2%} ({pt_years:.2f} years to maturity), seen by the "
                "oracle; held to maturity the PT still redeems at par"
            )
        else:
            path.append(f"implied yield +{s:.1%} pts: PT price −{1 - f:.2%}, not seen by the oracle; no liquidation")

    for ev in ("chain", "issuer_hack", "amm"):
        s = shocks.get(ev, 0.0)
        if s:
            v_true *= 1 - s
            v_oracle *= 1 - s
            path.append(f"{ev}: value −{s:.1%}")

    s = shocks.get("issuer_depeg", 0.0)
    if s:
        v_true *= 1 - s * (1 - recovery)
        if oracle_mode == "market-tracking":
            trough = min(0.99, 1 - (1 - s) * (1 - pt_stress(implied_apy, pt_years, pt_stress_spike)))
            v_oracle *= 1 - trough
            path.append(f"depeg −{s:.1%}, PT market trough −{trough:.1%} seen by the oracle, {recovery:.0%} recovers")
        else:
            path.append(f"depeg −{s:.1%}, oracle does not follow the market, {recovery:.0%} recovers")

    s = shocks.get("oracle", 0.0)
    if s:
        v_oracle *= 1 - s
        path.append(f"oracle misreports −{s:.1%}")

    s = shocks.get("lending", 0.0)
    if s:
        v_true *= 1 - s
        path.append(f"lending market exploit: −{s:.1%} of collateral stolen")

    liquidated = bool(debt_usd and lltv and v_oracle * lltv < debt_usd)
    if liquidated:
        seized_frac = min(1.0, debt_usd * (lif or 1.0) / v_oracle)
        equity1 = v_true * (1 - seized_frac)
        path.append(f"liquidated: {seized_frac:.1%} of collateral seized at the oracle price")
    else:
        equity1 = max(0.0, v_true - debt_usd)
        if debt_usd and v_true < debt_usd:
            path.append("collateral below debt: equity wiped, lenders take bad debt")
    return LossBreakdown(max(0.0, equity0 - equity1), liquidated, v_true, v_oracle, path)
