"""`GET /api/graph` — the dependency graph, from `out/` or read live."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ... import graph as GR
from ... import sources as S
from ..artifacts import fetch_lock, read_artifact
from ..schemas import GraphResponse

router = APIRouter(tags=["graph"])


@router.get("/api/graph", response_model=GraphResponse)
def get_graph(
    user: list[str] = Query(default=[], description="Address whose positions to include; repeatable."),
    vault: list[str] = Query(default=[], description="Vault V2 address to include; repeatable."),
    block: int | None = Query(default=None, description="Block to read at. Omitted: 2 behind the head."),
) -> Any:
    """The dependency graph. With no user and no vault, the last graph written to `out/`.

    The whole graph is returned in one payload: selecting a node and walking its dependencies
    is the client's job, not an endpoint — 100 nodes fit in the browser and Cytoscape traverses
    them better than a round trip would.
    """
    if not user and not vault:
        return read_artifact("graph.json")
    with fetch_lock:
        f = S.Fetcher("direct")
        try:
            at = block if block is not None else int(S.rpc(f, "eth_blockNumber", []), 16) - 2
            g = None
            for i, u in enumerate(user or [None]):
                part = GR.build(f, at, u, vault if i == 0 else [])
                if g is None:
                    g = part
                else:
                    for n in part.nodes.values():
                        g.node(n["id"], n["kind"], n["label"], **n["details"])
                    for e in part.edges:
                        g.edge(e["source"], e["target"], e["rel"], e["amount"], e["unit"], **e["details"])
        except S.CacheMiss as e:
            raise HTTPException(status_code=503, detail=f"offline snapshot incomplete: {e}") from e
        except S.SourceError as e:
            raise HTTPException(status_code=502, detail=f"data source error: {e}") from e
    title = "Morpho dependency graph: " + ", ".join([u[:10] + "…" for u in user] + [v[:10] + "…" for v in vault])
    return GR.to_dict(g, title, GR.subtitle_for(at))
