"""`GET /api/targets` and `GET /api/alerts` — what the watcher has recorded.

The watcher is a separate process; these routes only read its logs. Nothing here polls the
chain, so however many browsers are open there is still one poll loop per target.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..artifacts import alert_files, read_alerts
from ..schemas import AlertLevel, AlertPage, Target

router = APIRouter(tags=["alerts"])

# info < warn < critical: `level` is a floor, not an equality
ORDER = {"info": 0, "warn": 1, "critical": 2}


@router.get("/api/targets", response_model=list[Target])
def get_targets() -> list[Target]:
    """What the watcher has written so far: one entry per `out/watch-*.jsonl`."""
    out = []
    for name, path in alert_files().items():
        rows = read_alerts(path)
        out.append(Target(target=name, alerts=len(rows), last_block=rows[-1]["block"] if rows else None))
    return out


@router.get("/api/alerts", response_model=AlertPage)
def get_alerts(
    target: str | None = Query(default=None, description="From /api/targets. Omitted: the first one."),
    since: int = Query(default=0, ge=0, description="Only alerts strictly after this block."),
    level: AlertLevel | None = Query(default=None, description="Minimum level to return."),
    limit: int = Query(default=200, ge=1, le=2000),
) -> AlertPage:
    """Alerts the watcher has recorded, after a block cursor.

    Poll this: pass the previous `cursor` back as `since`. The cursor is a block number, the
    same unit the watcher resumes from, so moving to a push transport later changes the
    delivery and not the contract.
    """
    files = alert_files()
    if not files:
        raise HTTPException(status_code=404, detail="no watch output in out/ — run `uv run python -m riskdep watch`")
    name = target or next(iter(files))
    if name not in files:
        raise HTTPException(status_code=404, detail=f"unknown target {name!r}; see GET /api/targets")

    floor = ORDER[level] if level else 0
    rows = [a for a in read_alerts(files[name]) if a["block"] > since and ORDER[a["level"]] >= floor]
    rows = rows[-limit:]
    counts = {lv: sum(1 for a in rows if a["level"] == lv) for lv in ORDER}
    cursor = max((a["block"] for a in rows), default=since)
    return AlertPage(target=name, cursor=cursor, counts=counts, alerts=rows)
