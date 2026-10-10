"""HTTP API over `riskdep`, for the browser UI in `web/`.

Responsibilities, and only these: address the artifacts, validate the inputs, serve JSON.
No risk logic lives here — `pipeline.analyze` computes, `report.to_dict` and `graph.to_dict`
shape, this module routes. Adding a rule or a threshold here would be a mistake.

The watcher is deliberately **not** hosted: `python -m riskdep watch` runs as its own process
and appends to `out/watch-*.jsonl`; `GET /api/alerts` reads those files with a block cursor.
That keeps one poll loop per target however many browsers are open, and lets either side
restart without the other.

Run it with:  uv run uvicorn riskdep.api:app --reload
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .. import clock
from .. import sources as S
from .routes import alerts, dashboard, graph, report
from .schemas import Health

meta = APIRouter(tags=["meta"])


@meta.get("/api/health", response_model=Health)
def health() -> Health:
    return Health(mode="offline", data_as_of=clock.now_dt().strftime("%Y-%m-%d %H:%M UTC"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Offline runs read "now" from the snapshot, so every response speaks of the same instant."""
    as_of = S.SNAPSHOT_DIR / "as_of.json"
    if as_of.exists():
        clock.set_as_of(json.loads(as_of.read_text())["as_of"])
    yield


app = FastAPI(
    lifespan=lifespan,
    title="riskdep",
    version="0.1.0",
    summary="Risk of DeFi positions on Ethereum, centred on Morpho.",
    description=__doc__,
)

# the Vite dev server; a deployed UI is served from the same origin and needs no entry here
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

for r in (meta, graph.router, report.router, alerts.router, dashboard.router):
    app.include_router(r)
