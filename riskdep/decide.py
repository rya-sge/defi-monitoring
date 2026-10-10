"""Stay / reduce / exit (D13)."""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, field

from .discover import REGISTRY, Position
from .simulate import SimResult


@dataclass
class Reduction:
    sell_usd: float  # PT sold, proceeds repay debt
    new_health_factor: float
    new_liquidation_drop: float
    cost_usd: float  # price impact + fee + gas on the partial sale
    expected_loss_usd: float  # after the reduction
    cvar99_usd: float
    carry_usd: float
    source: str


@dataclass
class Decision:
    verdict: str  # STAY | REDUCE | EXIT
    headline: str
    carry_usd: float
    exit_cost_usd: float
    expected_loss_usd: float
    net_stay_usd: float  # carry − expected loss
    risk_multiple_to_exit: float  # how many times riskier the world must be before exit pays
    liquidation_drop: float | None
    stress_drop: float | None  # the oracle drop the position should survive
    reduction: Reduction | None = None
    reasons: list[str] = field(default_factory=list)


def carry_usd(pos: Position, days: float) -> float:
    h = days / 365
    return pos.collateral_usd * pos.implied_apy * h - pos.debt_usd * pos.borrow_apy * h


def exit_cost_usd(pos: Position, quote: dict) -> float:
    return pos.collateral_usd * quote["price_impact"] + quote["fee_usd"] + REGISTRY["gas_exit_usd"]


def stress_drop(pos: Position, depeg_mean: float | None) -> float:
    """The oracle fall a leveraged PT position should survive: the larger of twice the
    underlying's worst 1-year drawdown and the mean depeg as the oracle would see it."""
    dd = 2 * (pos.underlying_drawdown_1y or 0)
    seen = (depeg_mean or 0) * (
        (1 + REGISTRY["pt_stress_extra_discount"]) if pos.oracle_mode == "market-tracking" else 0
    )
    return max(dd, seen, 0.05)


def sale_to_reach(pos: Position, target_drop: float) -> float:
    """USD of PT to sell (proceeds repay debt) so a `target_drop` oracle fall no longer liquidates."""
    v, d, lt = pos.collateral_usd, pos.debt_usd, pos.lltv
    k = (1 - target_drop) * lt
    return max(0.0, min(d, (d - k * v) / (1 - k)))


def verdict(
    pos: Position,
    sim: SimResult,
    quote: dict,
    depeg_mean: float | None = None,
    resimulate: Callable[[Position], SimResult] | None = None,
    quote_for: Callable[[Position, float], dict] | None = None,
) -> Decision:
    carry = carry_usd(pos, sim.horizon_days)
    exit_cost = exit_cost_usd(pos, quote)
    el = sim.expected_loss_usd
    net_stay = carry - el
    mult = (carry + exit_cost) / el if el > 0 else float("inf")
    equity = max(pos.equity_usd, 1.0)

    reasons = [
        f"Over {sim.horizon_days:.0f} days: expected loss ${el:,.0f} vs carry ${carry:,.0f} "
        f"(net ${net_stay:+,.0f}); leaving now costs ${exit_cost:,.0f} "
        f"({quote['price_impact']:.2%} price impact + fees, {quote['source']})."
    ]
    reasons += [
        f"Driver: {ly.layer}: ${ly.contribution_usd:,.0f} of expected loss "
        f"({ly.p_horizon:.2%} chance over the horizon, ${ly.standalone_loss_usd:,.0f} if it happens"
        + (f", liquidates {ly.liquidation_rate:.0%} of the time" if ly.liquidation_rate else "")
        + ")."
        for ly in sim.layers[:2]
        if ly.contribution_usd > 0
    ]

    ld = pos.liquidation_drop
    stress = None
    if ld is not None:
        stress = stress_drop(pos, depeg_mean)
        dd = pos.underlying_drawdown_1y
        reasons.append(
            f"A {ld:.2%} fall in the oracle price liquidates the position (HF {pos.health_factor:.3f}); "
            f"the stress it should survive is {stress:.1%}"
            + (f" (underlying's worst 1-year drawdown {dd:.2%})." if dd is not None else ".")
        )
        if pos.oracle_mode == "market-tracking":
            reasons.append(
                (
                    "The oracle is treated as following the PT market (not confirmed: see the oracle sensitivity line)"
                    if pos.oracle_ambiguous
                    else "The oracle follows the PT market"
                )
                + ", so a temporary depeg turns into a realised loss through liquidation."
            )

    tail_bad = sim.cvar99_usd > REGISTRY["tail_budget"] * equity
    reduction = None
    if el > carry + exit_cost:
        v = "EXIT"
        head = "EXIT: the expected loss exceeds the carry plus the cost of leaving."
    elif net_stay < 0 or tail_bad or (ld is not None and ld < (stress or 0)):
        v = "REDUCE"
        why = []
        if net_stay < 0:
            why.append(f"the carry (${carry:,.0f}) does not cover the expected loss (${el:,.0f})")
        if tail_bad:
            why.append(
                f"in the worst 1% of outcomes it loses ${sim.cvar99_usd:,.0f} on average "
                f"({sim.cvar99_usd / equity:.0%} of equity)"
            )
        if ld is not None and ld < (stress or 0):
            why.append(f"a {ld:.1%} oracle drop liquidates it, less than the {stress:.1%} stress")
        head = "REDUCE: a full exit costs more than it saves, but " + "; ".join(why) + "."
        if ld is not None and resimulate and stress:
            sell = sale_to_reach(pos, stress)
            if sell > 0:
                smaller = copy.copy(pos)
                frac = sell / pos.collateral_usd
                smaller.collateral_units = pos.collateral_units * (1 - frac)
                smaller.debt_usd = pos.debt_usd - sell
                smaller.health_factor = (
                    (smaller.collateral_usd * pos.lltv / smaller.debt_usd) if smaller.debt_usd else float("inf")
                )
                q = (
                    quote_for(pos, frac)
                    if quote_for
                    else {
                        "price_impact": quote["price_impact"] * frac,
                        "fee_usd": quote["fee_usd"] * frac,
                        "source": "scaled from the full quote",
                    }
                )
                cost = sell * q["price_impact"] + q["fee_usd"] + REGISTRY["gas_exit_usd"]
                s2 = resimulate(smaller)
                reduction = Reduction(
                    sell,
                    smaller.health_factor,
                    smaller.liquidation_drop or 0.0,
                    cost,
                    s2.expected_loss_usd,
                    s2.cvar99_usd,
                    carry_usd(smaller, sim.horizon_days),
                    q["source"],
                )
                reasons.append(
                    f"De-lever: sell ${sell:,.0f} of PT ({frac:.0%}) and repay debt → HF {smaller.health_factor:.3f}, "
                    f"liquidation at −{reduction.new_liquidation_drop:.1%}; costs ${cost:,.0f}; expected loss "
                    f"${el:,.0f} → ${s2.expected_loss_usd:,.0f}, CVaR99 ${sim.cvar99_usd:,.0f} → ${s2.cvar99_usd:,.0f}, "
                    f"carry ${carry:,.0f} → ${reduction.carry_usd:,.0f}."
                )
    else:
        v = "STAY"
        head = "STAY: the carry covers the expected loss, and the tail fits the budget."
    reasons.append(
        f"A full exit would only pay if incident probabilities were {mult:.1f}× the estimates."
        if mult != float("inf")
        else "No modelled loss."
    )
    return Decision(v, head, carry, exit_cost, el, net_stay, mult, ld, stress, reduction, reasons)
