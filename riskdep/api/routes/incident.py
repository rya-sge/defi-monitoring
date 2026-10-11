"""`GET /api/books`, `POST /api/incident` and `POST /api/incident/after` — a known incident on a vault or a book of vaults, computed by
`pipeline.incident`, the same run as `analyze --vault` / `--book`."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException

from ... import pipeline, vault_book
from ... import sources as S
from ..artifacts import fetch_lock
from ..schemas import AfterRequest, AfterResponse, BookSummary, IncidentRequest, IncidentResponse

router = APIRouter(tags=["incident"])


@router.get("/api/books", response_model=list[BookSummary])
def get_books() -> Any:
    """The books of vaults shipped in `examples/`, for `POST /api/incident` with `example`."""
    return [
        {"name": k, "title": b.name, "weighting": b.weighting, "vaults": [asdict(v) for v in b.vaults]}
        for k, b in vault_book.examples().items()
    ]


@router.post("/api/incident", response_model=IncidentResponse)
def post_incident(req: IncidentRequest) -> Any:
    """Apply a known incident to every vault of a book, offline from the recordings unless `live`. Nothing is
    written to `out/`; a vault without a recording answers 404 offline."""
    given = [x for x in (req.vaults, req.book, req.example) if x]
    if len(given) != 1:
        raise HTTPException(status_code=422, detail="give exactly one of vaults, book or example")
    try:
        if req.example:
            books = vault_book.examples()
            if req.example not in books:
                raise HTTPException(status_code=404, detail=f"no example book {req.example!r}: see GET /api/books")
            book = books[req.example]
        elif req.book:
            book = vault_book.parse(req.book.model_dump(), "book")
        else:
            book = vault_book.from_addresses(req.vaults, req.user)
        with fetch_lock:
            res = pipeline.incident(
                book,
                req.shocks,
                req.user,
                req.horizon,
                "live" if req.live else "offline",
                req.exit_cost,
                req.conditional,
            )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"{e}; or retry with live=true") from e
    except S.CacheMiss as e:
        raise HTTPException(status_code=503, detail=f"recording incomplete: {e}; retry with live=true") from e
    except S.SourceError as e:
        raise HTTPException(status_code=502, detail=f"data source error: {e}") from e
    return {"book": res.result.to_json(), "vaults": [i.to_json() for i in res.incidents]}


@router.post("/api/incident/after", response_model=AfterResponse)
def post_incident_after(req: AfterRequest) -> Any:
    """A vault after an incident that began at block `since`: what has landed, what is still at risk (unrealised, and
    pending until the oracle passes it on) and the verdict on that part only. Offline from a recording unless `live`."""
    try:
        with fetch_lock:
            res = pipeline.after_incident(
                req.vault,
                req.since,
                req.at,
                req.shocks,
                req.user,
                "live" if req.live else "offline",
                req.exit_cost,
                req.horizon,
            )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"{e}; or retry with live=true") from e
    except S.CacheMiss as e:
        raise HTTPException(status_code=503, detail=f"recording incomplete: {e}; retry with live=true") from e
    except S.SourceError as e:
        raise HTTPException(status_code=502, detail=f"data source error: {e}") from e
    return res.to_json()
