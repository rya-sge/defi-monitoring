"""One clock for the whole analysis.

Live runs use the wall clock. An offline run uses the time its snapshot was taken (the
as-of date), so cache keys built from dates and every "days until" stay what they were
when the snapshot was recorded.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

_as_of: float | None = None


def now() -> float:
    return _as_of if _as_of is not None else time.time()


def now_dt() -> datetime:
    return datetime.fromtimestamp(now(), timezone.utc)


def set_as_of(ts: float | None) -> None:
    global _as_of
    _as_of = ts


def as_of() -> float | None:
    return _as_of
