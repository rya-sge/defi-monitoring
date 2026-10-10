"""How a shock on one layer reaches the position. Pure functions, no I/O.

Shocks are severities in [0, 1] keyed by event id:
  chain         liveness / settlement loss          value × (1 − s)
  issuer_hack   backing lost, SY exchange rate falls value × (1 − s), every oracle sees it
  issuer_depeg  market price of the underlying falls trough × (1 − s), (1 − recovery) of it stays;
                a market-tracking oracle sees the trough amplified by the PT stress discount
  amm           Pendle core / SY adapter exploit     value × (1 − s), every oracle sees it
  oracle        the oracle misreports downward       oracle reading × (1 − s), no real loss
  lending       collateral stolen from the market    value × (1 − s), no liquidation needed

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


def loss(
    collateral_usd: float,
    debt_usd: float,
    lltv: float | None,
    lif: float | None,
    oracle_mode: str,
    shocks: dict[str, float],
    recovery: float = 0.0,
    pt_stress_extra: float = 0.5,
) -> LossBreakdown:
    v_true = collateral_usd
    v_oracle = collateral_usd
    path: list[str] = []

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
            trough = min(0.99, s * (1 + pt_stress_extra))
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

    equity0 = collateral_usd - debt_usd
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
