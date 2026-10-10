"""Monte Carlo over layer incidents for one horizon (D12)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .discover import REGISTRY, Position
from .priors import Prior
from .propagate import loss


@dataclass
class LayerResult:
    event: str
    layer: str
    node: str
    p_horizon: float
    mean_severity: float
    standalone_loss_usd: float  # E[loss | only this layer hits]
    contribution_usd: float  # p_horizon × standalone
    liquidation_rate: float  # P(liquidated | only this layer hits)
    example_path: list[str]
    basis: str


@dataclass
class SimResult:
    horizon_days: float
    n: int
    expected_loss_usd: float
    var95_usd: float
    cvar95_usd: float
    var99_usd: float
    cvar99_usd: float
    p_any_loss: float
    p_liquidation: float
    layers: list[LayerResult]
    interaction_usd: float
    loss_samples: np.ndarray = field(repr=False, default=None)


def _p_horizon(p_year: float, days: float) -> float:
    return 1 - (1 - p_year) ** (days / 365)


def _tail(losses: np.ndarray, q: float) -> tuple[float, float]:
    """(VaR, CVaR) at level q; CVaR is the mean of the worst (1 − q) share of outcomes."""
    k = max(1, int(round(len(losses) * (1 - q))))
    worst = np.sort(losses)[-k:]
    return float(np.quantile(losses, q)), float(worst.mean())


def _loss(pos: Position, shocks: dict, recovery: float):
    return loss(
        pos.collateral_usd,
        pos.debt_usd,
        pos.lltv,
        pos.lif,
        pos.oracle_mode,
        shocks,
        recovery=recovery,
        pt_stress_extra=REGISTRY["pt_stress_extra_discount"],
    )


def run(pos: Position, priors: list[Prior], horizon_days: float, n: int = 20000, seed: int = 7) -> SimResult:
    rng = np.random.default_rng(seed)
    recovery = next((p.recovery for p in priors if p.event == "issuer_depeg"), 0.0)
    ph = {p.event: _p_horizon(p.p_year, horizon_days) for p in priors}

    hits = {p.event: rng.random(n) < ph[p.event] for p in priors}
    sev = {p.event: rng.beta(p.a, p.b, n) for p in priors}
    # D12: an exploit of the issuer comes with a depeg at least as deep.
    if "issuer_hack" in hits and "issuer_depeg" in hits:
        both = hits["issuer_hack"]
        hits["issuer_depeg"] = hits["issuer_depeg"] | both
        sev["issuer_depeg"] = np.where(both, np.maximum(sev["issuer_depeg"], sev["issuer_hack"]), sev["issuer_depeg"])

    losses = np.zeros(n)
    liq = np.zeros(n, dtype=bool)
    any_hit = np.zeros(n, dtype=bool)
    for h in hits.values():
        any_hit |= h
    for i in np.flatnonzero(any_hit):
        shocks = {e: float(sev[e][i]) for e in hits if hits[e][i]}
        r = _loss(pos, shocks, recovery)
        losses[i], liq[i] = r.loss_usd, r.liquidated

    layers = []
    m = 4000
    for p in priors:
        s = rng.beta(p.a, p.b, m)
        rs = [_loss(pos, {p.event: float(x)}, recovery) for x in s]
        standalone = float(np.mean([r.loss_usd for r in rs]))
        median = rs[int(np.argsort([r.loss_usd for r in rs])[m // 2])]
        worst = max(rs, key=lambda r: r.loss_usd)
        example = median.path if median.loss_usd > 0 else worst.path
        layers.append(
            LayerResult(
                p.event,
                p.layer,
                p.node,
                ph[p.event],
                p.mean_severity,
                standalone,
                ph[p.event] * standalone,
                float(np.mean([r.liquidated for r in rs])),
                example,
                p.basis,
            )
        )

    el = float(losses.mean())
    return SimResult(
        horizon_days,
        n,
        el,
        *_tail(losses, 0.95),
        *_tail(losses, 0.99),
        float((losses > 0).mean()),
        float(liq.mean()),
        sorted(layers, key=lambda ly: -ly.contribution_usd),
        el - sum(ly.contribution_usd for ly in layers),
        losses,
    )
