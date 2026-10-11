"""Feed quality: how fresh each oracle input is, against its own update rhythm (plan 2026-10-11-feed-quality,
D155–D157; the brief's "oracle dependency and feed-quality analysis").

Everything comes from the reads the oracle classification already makes (`oracle_class.probe`): the latest round's
`updatedAt` and up to `graph.oracle_history_rounds` past ones. No extra call, so a recorded graph has it. The
cadence is the median gap between those rounds; a feed is stale when its last update is older than
`feeds.stale_factor` × that cadence and `feeds.stale_min_hours`, or, with fewer than `graph.oracle_history_min` rounds
to learn a cadence from, older than `feeds.no_history_max_days`. A Chainlink heartbeat or deviation threshold is not readable on-chain, so the observed
rhythm stands in for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .discover import REGISTRY

F = REGISTRY["feeds"]
MIN_ROUNDS = REGISTRY["graph"]["oracle_history_min"]  # fewer rounds than the classification trusts: no rhythm


@dataclass
class Freshness:
    age_h: float  # hours since the last update
    cadence_h: float | None  # median hours between updates, None without history
    stale: bool
    text: str


def freshness(updated_at: int | None, times: list[int], now: float) -> Freshness | None:
    """D155–D156, pure: `updated_at` and `times` are unix seconds (`times` oldest first), `now` the reading time."""
    if not updated_at:
        return None
    age = max(0.0, (now - updated_at) / 3600)
    gaps = [(b - a) / 3600 for a, b in zip(times, times[1:]) if b > a]
    cadence = median(gaps) if len(gaps) + 1 >= MIN_ROUNDS else None
    if cadence is not None:
        limit = max(F["stale_factor"] * cadence, F["stale_min_hours"])
        stale = age > limit
        text = f"updated {_dur(age)} ago; usually every {_dur(cadence)} ({len(gaps) + 1} rounds)"
    else:
        limit = F["no_history_max_days"] * 24
        stale = age > limit
        text = f"updated {_dur(age)} ago; " + (
            f"{len(gaps) + 1} rounds, too few to learn its rhythm" if gaps else "no round history to learn its rhythm"
        )
    return Freshness(age, cadence, stale, text + (f": STALE, past {_dur(limit)}" if stale else ""))


def _dur(hours: float) -> str:
    if hours < 1:
        return f"{hours * 60:.0f} min"
    if hours < 48:
        return f"{hours:.1f} h"
    return f"{hours / 24:.1f} days"
