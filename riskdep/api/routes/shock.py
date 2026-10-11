"""`/api/shock*` — a failure applied to a node of the dependency graph and propagated, as `riskdep shock` does.

Offline from the graphs recorded under `fixtures/replay/graph-<target>/` unless `live`; nothing is written to `out/`.
The propagation is `engine.run`, the shaping `shock.trace` and `shock.run_sweep`: this module only loads the graph.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ... import clock, pipeline
from ... import engine as EN
from ... import graph as GR
from ... import shock as SH
from ... import sources as S
from ..artifacts import fetch_lock
from ..schemas import ShockGraph, ShockRequest, ShockSweep, ShockSweepRequest, ShockTarget, ShockTrace

router = APIRouter(tags=["shock"])


def _quiet(*_: Any) -> None:
    """`shock` prints its tables; a route returns them."""


def _load(vault: list[str], user: list[str], live: bool, siblings: bool) -> tuple[dict, int, str | None]:
    """The graph as `shock` reads it: (graph dict, block, its as-of). The caller holds `fetch_lock`."""
    if not vault and not user:
        raise HTTPException(status_code=422, detail="give at least one vault or user")
    rdir = pipeline.REPLAY_DIR / f"graph-{(vault or user)[0].lower()}"
    kept = clock.as_of()
    try:
        g, block, *_ = GR.load(user, vault, siblings, "direct" if live else "replay", rdir)
        as_of = clock.now_dt().strftime("%Y-%m-%dT%H:%M:%SZ")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"{e}: see GET /api/shock/graphs, or retry with live=true") from e
    except S.CacheMiss as e:
        raise HTTPException(status_code=503, detail=f"recording incomplete: {e}; retry with live=true") from e
    except S.SourceError as e:
        raise HTTPException(status_code=502, detail=f"data source error: {e}") from e
    finally:
        clock.set_as_of(kept)  # a replay moves the clock to its recording; the API keeps the snapshot's
    return SH._graph_dict(g), block, as_of


def _json(data: dict) -> dict:
    # the CLI writes the same dicts with default=str (tuples, sets, numpy scalars)
    return json.loads(json.dumps(data, default=str))


@router.get("/api/shock/graphs", response_model=list[ShockGraph])
def get_graphs() -> Any:
    """The recorded graphs a shock can run on offline: one per `fixtures/replay/graph-<target>/`."""
    out = []
    for meta in sorted(pipeline.REPLAY_DIR.glob("graph-*/meta.json")):
        m = json.loads(meta.read_text())
        out.append(
            {
                "target": meta.parent.name.removeprefix("graph-"),
                "vaults": [v.lower() for v in m["vaults"]],
                "users": [u.lower() for u in m["users"]],
                "block": m["block"],
                "siblings": m["siblings"],
            }
        )
    return out


@router.get("/api/shock/targets", response_model=list[ShockTarget])
def get_targets(
    vault: list[str] = Query(default=[], description="Vault V2 whose markets seed the graph; repeatable."),
    user: list[str] = Query(default=[], description="Address whose borrows seed the graph; repeatable."),
    live: bool = Query(default=False, description="Read the chain instead of the recording."),
) -> Any:
    """The nodes that can be shocked — oracles, feeds and assets — with the markets whose price they enter
    (`shock --list`); held markets first."""
    with fetch_lock:
        gd, _, _ = _load(vault, user, live, True)
    nodes, markets = {n["id"]: n for n in gd["nodes"]}, SH._markets_of(gd)
    rows = []
    for nid, ms in SH.dependents(gd).items():
        n = nodes[nid]
        held = [m for m in ms if not markets[m]["details"].get("sibling")]
        rows.append(
            {
                "node": nid,
                "label": n["label"],
                "kind": n["kind"],
                "oracle_class": n["details"].get("oracle_class"),
                "held": len(held),
                "siblings": len(ms) - len(held),
                "markets": ms,
            }
        )
    return sorted(rows, key=lambda r: (-r["held"], -len(r["markets"]), r["label"]))


@router.post("/api/shock", response_model=ShockTrace)
def post_shock(req: ShockRequest) -> Any:
    """Apply the shocks together and return the propagation trace (`shock --shock`, `docs/model/shock-trace.md`)."""
    with fetch_lock:
        gd, block, as_of = _load(req.vault, req.user, req.live, req.siblings)
        try:
            shocks = SH.resolve_shocks({n["id"]: n for n in gd["nodes"]}, req.shocks)
            res = EN.run(gd, shocks, None)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        return _json(SH.trace(gd, res, block, as_of))


@router.post("/api/shock/sweep", response_model=ShockSweep)
def post_sweep(req: ShockSweepRequest) -> Any:
    """The same failure on every oracle and feed in turn (every asset, for `price`), ranked by the vaults' loss
    (`shock --sweep`)."""
    with fetch_lock:
        gd, block, _ = _load(req.vault, req.user, req.live, req.siblings)
        try:
            shk = EN.parse_shock(f"0x:{req.mode}:{req.size}" if req.size else f"0x:{req.mode}")
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        rows = SH.run_sweep(gd, shk.mode, shk.size, None, req.top, line=_quiet)
    return _json({"block": block, "mode": shk.mode, "size": shk.size, "ranking": rows[: req.top]})
