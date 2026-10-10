"""Pharos, keyless: issuer grades, off-chain backing and common-mode groups of stablecoins and yield dollars
(plan 2026-10-11-pharos, D117–D122; docs/risk-assessment/outside-providers.md).

One public response, `GET https://api.pharos.watch/api/dependency-graph/v1`, carries everything used here:
  - nodes: a Safety Score (0–100) and letter grade per coin, and its `roles`: what backs it, with a weight
    (`serial-claim` 1 for a wrapper, `basket-exposure` w for a share of the reserve);
  - commonModeGroups: coins that fail together (one mint key, one upgrade admin, one reserve issuer, one bridge).
Pharos ids are not addresses: `registry.json` `pharos.ids` maps token addresses to ids and symbols; a symbol also matches an id
whose first part is that symbol, when only one does ("fxsave" → "fxsave-f-x-protocol"; "iusd" matches three ids,
so iUSD needs its address in the registry).

Pure functions on a `Snapshot`, and one I/O function, `load`, through the cached fetcher. Pharos is optional: when it
cannot be read, the caller says "Pharos: not checked" and carries on.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from . import sources as S
from .discover import REGISTRY

URL = "https://api.pharos.watch/api/dependency-graph/v1"
P = REGISTRY["pharos"]


@dataclass
class Snapshot:
    as_of: str  # the publication date, UTC
    methodology: str
    grades: dict[str, tuple[str, int | None]]  # id → (grade, score); "NR" and None when not rated
    backing: dict[str, list[tuple[str, float, str]]]  # id → [(upstream id, weight, role)]
    groups: dict[str, list[tuple[str, str, list[str]]]] = field(default_factory=dict)  # id → [(kind, key, members)]

    def grade(self, pid: str | None) -> str | None:
        """'F 36', 'NR', or None when the id is not covered."""
        if pid not in self.grades:
            return None
        g, s = self.grades[pid]
        return g if s is None else f"{g} {s}"


def _slim(d: dict) -> dict:
    """Keep what is used: the graph is 0.5 MB, the slim copy about a third of it."""
    return {
        "asOfSec": d.get("asOfSec"),
        "methodologyVersion": d.get("methodologyVersion"),
        "nodes": [
            {
                "id": n["id"],
                "grade": n.get("grade"),
                "score": n.get("score"),
                "roles": [
                    {"up": r["upstreamAssetId"], "w": r.get("weight"), "role": r.get("economicRole")}
                    for r in n.get("roles") or []
                ],
            }
            for n in d.get("nodes", [])
        ],
        "groups": [
            {"kind": c["kind"], "key": c["key"], "members": c["memberAssetIds"]} for c in d.get("commonModeGroups", [])
        ],
    }


def parse(d: dict) -> Snapshot:
    """Pure: the slim response → a Snapshot. Groups wider than `max_group_members` say little and are dropped."""
    grades = {n["id"]: (n.get("grade") or "NR", n.get("score")) for n in d["nodes"]}
    backing = {
        n["id"]: [(r["up"], float(r["w"] if r["w"] is not None else 1.0), r["role"] or "") for r in n["roles"]]
        for n in d["nodes"]
        if n["roles"]
    }
    groups: dict[str, list] = {}
    for c in d["groups"]:
        if c["kind"] in P["common_mode_kinds"] and 1 < len(c["members"]) <= P["max_group_members"]:
            for m in c["members"]:
                groups.setdefault(m, []).append((c["kind"], c["key"], c["members"]))
    as_of = time.strftime("%Y-%m-%d", time.gmtime(d["asOfSec"])) if d.get("asOfSec") else "unknown"
    return Snapshot(as_of, str(d.get("methodologyVersion")), grades, backing, groups)


def resolve(snap: Snapshot, token: str, symbol: str | None = None) -> str | None:
    """D118, pure: a token (address or symbol, any case) → its Pharos id, or None. The registry's address map first,
    then an exact id, then the only id whose first part is the symbol."""
    t = token.lower()
    if t in P["ids"]:
        return P["ids"][t]["id"]
    for s in (t, (symbol or "").lower()):
        if not s:
            continue
        if s in snap.grades:
            return s
        found = [i for i in snap.grades if i.split("-", 1)[0] == s]
        if len(found) == 1:
            return found[0]
    return None


def name(pid: str) -> str:
    """Pure: the token's symbol from the registry's address map, else the id's first part ("mglobal")."""
    return next((e["symbol"] for e in P["ids"].values() if e["id"] == pid), pid.split("-", 1)[0])


def exposure(snap: Snapshot, pid: str, target: str, depth: int = 4) -> tuple[float, list[str]]:
    """D119, pure: the share of `pid`'s backing that is `target`, through Pharos's backing edges (a wrapper counts 1,
    a reserve basket its weight), multiplied along each path and summed over paths. Returns (share, the path of the
    largest contribution)."""
    if pid == target:
        return 1.0, [pid]
    if depth == 0:
        return 0.0, []
    total, best, best_path = 0.0, 0.0, []
    for up, w, _ in snap.backing.get(pid, []):
        e, path = exposure(snap, up, target, depth - 1)
        total += w * e
        if w * e > best:
            best, best_path = w * e, [pid] + path
    return min(total, 1.0), best_path


def common_mode(snap: Snapshot, pid: str, among: dict[str, str]) -> list[str]:
    """D121, pure: the coins in `among` (Pharos id → name) that share a narrow common-mode group with `pid`, in words:
    'strUSD (mint control, upgrade control)'."""
    out: dict[str, list[str]] = {}
    for kind, _, members in snap.groups.get(pid, []):
        for m in members:
            if m != pid and m in among:
                out.setdefault(among[m], [])
                label = kind.replace("-", " ")
                if label not in out[among[m]]:
                    out[among[m]].append(label)
    return [f"{k} ({', '.join(v)})" for k, v in sorted(out.items())]


# --- I/O


def load(f: S.Fetcher) -> Snapshot | None:
    """The dependency graph through the cached fetcher; None when Pharos cannot be read (optional source)."""
    try:
        return parse(f.get_json(URL, transform=_slim))
    except (S.CacheMiss, S.SourceError, KeyError, TypeError):
        return None
