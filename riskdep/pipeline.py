"""One analyse, from a position to a verdict, with no I/O of its own beyond the fetcher.

This is the orchestration the `analyze` subcommand used to carry inline. It lives here so the
CLI and the HTTP API run the *same* sequence: discover, cross-check, price the layers, simulate,
decide, then re-run under the other oracle behaviour. Callers choose what to do with the result —
`report.write` to disk for the CLI, `report.to_dict` over the wire for the API.

Raises `sources.CacheMiss` (offline snapshot incomplete) and `sources.SourceError` (upstream
failure) for the caller to turn into an exit code or an HTTP status.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from . import crosscheck, decide, discover, priors, simulate
from . import sources as S
from .decide import Decision
from .discover import Position
from .priors import Prior
from .simulate import SimResult

DEMO_MARKET = "0x5613b170ded221c588b6e9637b910f49e5508680ceede207f44aa72e5c46cb05"
DEMO_USER = "0xdf81987465681D0515058fe0A47A3bD174012730"


@dataclass
class AnalyzeResult:
    position: Position
    priors: list[Prior]
    simulation: SimResult
    decision: Decision
    quote: dict
    checks: list[crosscheck.Check] = field(default_factory=list)
    oracle_alt: dict | None = None


def analyze(
    f: S.Fetcher,
    *,
    market: str | None = None,
    user: str | None = None,
    pendle_market: str | None = None,
    pt_amount: float | None = None,
    horizon: float = 30.0,
    paths: int = 20000,
) -> AnalyzeResult:
    """Analyse one position. With no market and no pendle_market, analyse the demo position."""
    if pendle_market:
        if pt_amount is None:
            raise ValueError("pendle_market needs pt_amount")
        pos = discover.discover_pt_holding(f, pendle_market, pt_amount)
    elif market:
        pos = discover.discover_morpho_position(f, market, user)
    else:
        pos = discover.discover_morpho_position(f, DEMO_MARKET, DEMO_USER)

    checks = [crosscheck.second_rpc(f)]
    if pos.morpho_market:
        checks.append(
            crosscheck.morpho_position(
                f,
                pos.morpho_market,
                pos.borrower,
                pos.collateral_decimals,
                pos.loan_decimals,
                pos.collateral_units,
                pos.debt_raw,
            )
        )
    pos.notes += [c.line for c in checks]

    prs = priors.layer_priors(f, pos)
    horizon = max(1.0, min(horizon, pos.days_to_maturity or horizon))
    sim = simulate.run(pos, prs, horizon, n=paths)
    quote = discover.exit_quote(f, pos)
    depeg = next((p.mean_severity for p in prs if p.event == "issuer_depeg"), None)
    dec = decide.verdict(
        pos,
        sim,
        quote,
        depeg,
        resimulate=lambda q: simulate.run(q, prs, horizon, n=paths),
        quote_for=lambda q, fr: discover.partial_exit_quote(f, q, fr),
    )

    alt = None
    if pos.oracle_mode != "none":
        # the same position under the other oracle behaviour: how much the verdict rests on the inference
        other = copy.copy(pos)
        other.oracle_mode = "fundamental" if pos.oracle_mode == "market-tracking" else "market-tracking"
        s2 = simulate.run(other, prs, horizon, n=paths)
        d2 = decide.verdict(other, s2, quote, depeg)
        alt = {
            "oracle_mode": other.oracle_mode,
            "verdict": d2.verdict,
            "expected_loss_usd": s2.expected_loss_usd,
            "cvar99_usd": s2.cvar99_usd,
            "p_liquidation": s2.p_liquidation,
        }
        same = d2.verdict == dec.verdict
        dec.reasons.append(
            f"Oracle sensitivity{' (inference ambiguous)' if pos.oracle_ambiguous else ''}: if the oracle were "
            f"{other.oracle_mode}, expected loss ${s2.expected_loss_usd:,.0f} (vs ${sim.expected_loss_usd:,.0f}), "
            f"P(liquidation) {s2.p_liquidation:.2%} (vs {sim.p_liquidation:.2%}), verdict {d2.verdict}"
            + (" — the same." if same else " — the verdict depends on the oracle; check its source before acting.")
        )

    # a failed cross-check leads the reasons: the numbers below it are suspect
    bad = [c for c in checks if c.ok is False]
    if bad:
        dec.reasons.insert(0, "DATA CHECK FAILED — " + "; ".join(c.detail for c in bad))

    return AnalyzeResult(
        position=pos, priors=prs, simulation=sim, decision=dec, quote=quote, checks=checks, oracle_alt=alt
    )
