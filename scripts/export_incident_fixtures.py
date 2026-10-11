"""Regenerate the frontend's exact-request incident fixtures from offline recordings.

Run from the repository root: uv run python scripts/export_incident_fixtures.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from riskdep import clock  # noqa: E402
from riskdep.api.routes.incident import get_books, post_incident  # noqa: E402
from riskdep.api.schemas import BookSummary, IncidentRequest, IncidentResponse  # noqa: E402


def main():
    clock.set_as_of(json.loads(Path("fixtures/snapshot/as_of.json").read_text())["as_of"])
    books = [BookSummary.model_validate(b).model_dump() for b in get_books()]
    cases = []
    for book in books:
        scopes = [{"example": book["name"]}] + [{"vaults": [v["address"]]} for v in book["vaults"]]
        for scope in scopes:
            for shock in ("token=PST:0.3", "token=fxSAVE:0.3", "borrower=all:0.5:1"):
                request = {**scope, "shocks": [shock], "horizon": 30}
                response = IncidentResponse.model_validate(post_incident(IncidentRequest(**request)))
                cases.append({"request": request, "response": response.model_dump()})
    dest = Path("web/src/mocks")
    for name, data in (("books", books), ("incidents", cases)):
        (dest / f"{name}.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    print(f"Exported {len(books)} book(s), {len(cases)} incident responses, offline.")


if __name__ == "__main__":
    main()
