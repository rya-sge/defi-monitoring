"""`GET /api/report` and `POST /api/analyze` — the analyse, served or run."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from ... import pipeline, report
from ... import sources as S
from ..artifacts import fetch_lock, read_artifact
from ..schemas import AnalyzeRequest, Report

router = APIRouter(tags=["report"])


@router.get("/api/report", response_model=Report)
def get_report() -> Any:
    """The last `analyze` report written to `out/`. Use POST /api/analyze to compute a new one."""
    return read_artifact("report.json")


@router.post("/api/analyze", response_model=Report)
def post_analyze(req: AnalyzeRequest = Body(default_factory=AnalyzeRequest)) -> Any:
    """Run one analysis and return its report. Nothing is written to `out/`."""
    with fetch_lock:
        f = S.Fetcher("live" if req.live else "offline")
        try:
            res = pipeline.analyze(
                f,
                market=req.market,
                user=req.user,
                pendle_market=req.pendle_market,
                pt_amount=req.pt_amount,
                horizon=req.horizon,
                paths=req.paths,
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        except S.CacheMiss as e:
            raise HTTPException(
                status_code=503, detail=f"offline snapshot incomplete: {e}; retry with live=true"
            ) from e
        except S.SourceError as e:
            raise HTTPException(status_code=502, detail=f"data source error: {e}") from e
    return report.to_dict(
        res.position,
        res.priors,
        res.simulation,
        res.decision,
        res.quote,
        "live" if req.live else "offline",
        res.oracle_alt,
        discovery=res.discovery,
    )
