"""The conditional Monte Carlo: given the incident, how bad can staying get, against the certain cost of leaving
(plan 2026-10-11-conditional, D165–D168; `IMPROVEMENT.md` 2.4, `NEXT_STEP.md` A4).

The incident is fixed; what is drawn is how it evolves:
  - its size: a multiple m of the fall given (`conditional.recover_prob`: partly reversed, m uniform on 0–1;
    otherwise held or deepened, m lognormal with median 1 and σ `conditional.deepen_sigma`);
  - whether liquidators act: with `conditional.no_liquidator_prob` by the hit collateral's worst exit route, nobody
    liquidates and the vault's loss is the shortfall (`MarketHit.no_liquidator_shortfall`) with the liquidity locked.
Losses at m are read off curves measured by running the real incident at `conditional.grid` multiples (the engine
included), not re-modelled here. A book's vaults share each path's m: one incident reaches them together.

Pure: the curves are passed in.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .discover import REGISTRY

C = REGISTRY["conditional"]
ROUTES = ("none", "thin", "unknown", "deep")  # worst first


@dataclass
class Curve:
    """One vault, in USD: at each multiple of the fall, the loss if the depositor stays, if it leaves first, and the
    no-liquidator loss as a share of the liquidated one; plus the certain cost of leaving and the liquidator risk."""

    name: str
    multiples: list[float]
    stay: list[float]
    leave: list[float]
    no_liq_ratio: list[float]
    exit_cost: float
    no_liquidator_prob: float


@dataclass
class Distribution:
    paths: int
    stay_mean: float
    stay_p50: float
    stay_p95: float
    stay_p99: float
    leave_mean: float  # loss left after leaving first, plus the certain cost of leaving
    p_stay_worse: float  # share of paths where staying costs more than leaving
    no_liquidator_share: float  # share of paths where nobody liquidates (for a book: in at least one vault)

    def text(self, unit: str = "USD") -> str:
        return (
            f"staying loses {self.stay_mean:,.0f} {unit} on average (median {self.stay_p50:,.0f}, 95 % "
            f"{self.stay_p95:,.0f}, 99 % {self.stay_p99:,.0f}); leaving now costs {self.leave_mean:,.0f} on average, "
            f"cost included; staying is worse in {self.p_stay_worse:.0%} of {self.paths:,} paths"
        )


def worst_route(routes: list[str | None]) -> str:
    """D167, pure: the worst exit route among a vault's liquidatable hits."""
    seen = {r or "unknown" for r in routes}
    return next((r for r in ROUTES if r in seen), "deep")


def draw_multiples(rng: np.random.Generator, n: int) -> np.ndarray:
    """D166, pure given the generator."""
    recover = rng.random(n) < C["recover_prob"]
    m = np.exp(rng.normal(0.0, C["deepen_sigma"], n))
    m[recover] = rng.random(int(recover.sum()))
    return m


def simulate(curves: list[Curve], fall: float, n: int | None = None, seed: int | None = None) -> Distribution:
    """D165–D168, pure: the book's (or one vault's) loss if it stays, path by path, against leaving first."""
    n = n or C["paths"]
    rng = np.random.default_rng(C["seed"] if seed is None else seed)
    m = np.minimum(draw_multiples(rng, n), 0.99 / fall if fall > 0 else 1.0)
    stay, leave, any_noliq = np.zeros(n), np.zeros(n), np.zeros(n, dtype=bool)
    for c in curves:
        s = np.interp(m, c.multiples, c.stay)
        lv = np.interp(m, c.multiples, c.leave)
        noliq = rng.random(n) < c.no_liquidator_prob
        r = np.where(noliq, np.interp(m, c.multiples, c.no_liq_ratio), 1.0)
        stay += s * r
        leave += lv * r + c.exit_cost
        any_noliq |= noliq
    return Distribution(
        n,
        float(stay.mean()),
        float(np.quantile(stay, 0.5)),
        float(np.quantile(stay, 0.95)),
        float(np.quantile(stay, 0.99)),
        float(leave.mean()),
        float((stay > leave).mean()),
        float(any_noliq.mean()),
    )
