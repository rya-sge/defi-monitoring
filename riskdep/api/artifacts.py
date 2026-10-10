"""Where the API reads from, and the one lock it takes.

The CLI writes `out/report.json`, `out/graph.json` and `out/watch-*.jsonl`; this module is the
only place that knows those names and turns a missing file into an HTTP 404 that says which
command would produce it. Routes never touch the filesystem themselves.

`OUT` is read at call time, not captured at import, so a test can point it at a tmp_path.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from fastapi import HTTPException

OUT = Path("out")

# data/snapshot writes are not concurrency-safe, and the free RPC rate-limits anyway:
# one fetching request at a time.
fetch_lock = threading.Lock()


def read_artifact(name: str) -> dict:
    """A JSON artifact from `out/`, or a 404 naming the command that writes it."""
    path = OUT / name
    if not path.exists():
        command = "graph --example" if "graph" in name else "analyze --demo"
        raise HTTPException(
            status_code=404,
            detail=f"{path} not found — run `uv run python -m riskdep {command}` first",
        )
    return json.loads(path.read_text())


def alert_files() -> dict[str, Path]:
    """Watch target -> its alert log. The target is the file name without `watch-`."""
    return {p.stem.removeprefix("watch-"): p for p in sorted(OUT.glob("watch-*.jsonl"))}


def read_alerts(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
