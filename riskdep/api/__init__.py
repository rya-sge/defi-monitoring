"""The HTTP API package.

- `main.py` assembles the FastAPI app and serves `/api/health`
- `schemas.py` is the published contract, mirrored by `openapi.json`
- `artifacts.py` is the only reader of `out/`, and holds the fetch lock
- `routes/` has one module per resource: graph, report, alerts

`uvicorn riskdep.api:app` resolves `app` through this re-export.
"""

from .main import app

__all__ = ["app"]
