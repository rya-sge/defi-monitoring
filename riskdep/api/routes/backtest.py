"""`GET /api/backtests` and `GET /api/backtest/{episode}` — a past incident replayed: the prediction against the
Liquidate events, as `riskdep backtest` does. Offline only, from `fixtures/replay/backtest-<episode>/`: reading the
past needs an archive RPC key, which the API never holds."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ... import backtest as BK
from ... import pipeline
from ... import sources as S
from ..artifacts import fetch_lock
from ..schemas import Backtest, BacktestSummary

router = APIRouter(tags=["backtest"])


def _dir(episode: str):
    return pipeline.REPLAY_DIR / f"backtest-{episode}"


@router.get("/api/backtests", response_model=list[BacktestSummary])
def get_backtests() -> Any:
    """The episodes of `registry.json` `backtest.episodes`, and whether each is recorded (servable)."""
    return [
        {"episode": k, "title": ep["title"], "markets": len(ep["markets"]), "recorded": _dir(k).is_dir()}
        for k, ep in BK.BT["episodes"].items()
    ]


@router.get("/api/backtest/{episode}", response_model=Backtest)
def get_backtest(episode: str) -> Any:
    """One episode replayed from its recording: per market, predicted against realised positions, debt, incentive and
    bad debt."""
    if episode not in BK.BT["episodes"]:
        raise HTTPException(status_code=404, detail=f"unknown episode {episode!r}: see GET /api/backtests")
    with fetch_lock:
        try:
            res = BK.run(S.Fetcher("offline", _dir(episode)), episode)
        except S.CacheMiss as e:
            raise HTTPException(
                status_code=404, detail=f"no recording of {episode}: {e}; run `backtest --record` first"
            ) from e
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
    return {**res.to_json(), "lines": res.lines()}
