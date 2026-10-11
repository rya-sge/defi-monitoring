"""Discovery depth for a borrow position: the layers the dependency graph knows beyond the PT report's five (plan
2026-10-11-depth, D199–D202; `NEXT_STEP.md` C1, `IMPROVEMENT.md` priority 3).

From the position's recorded graph (`graph --user <borrower> --record`, annotated with Pharos and TVL) and the admin
surface of its market (`admin.AdminWatch`): the oracle and each feed it reads, with its class and freshness; who can
change them, and how fast; the sibling markets that sell the same collateral or read the same price, with what a fall
would liquidate there; the collateral's off-chain backing and grade (Pharos); and the protocols' share of DeFi TVL.
Pure: the graph and the admin rows are passed in.
"""

from __future__ import annotations

FALL = 0.10  # the fall at which the siblings' liquidations are shown


def _curve_at(curve, fall: float) -> tuple[float, float]:
    """(debt liquidatable, bad debt) of a market's liquidation curve at `fall`, the nearest point at or above it."""
    pts = sorted((p for p in curve or [] if p.get("oracle_fall", 0) >= fall - 1e-9), key=lambda p: p["oracle_fall"])
    return (pts[0]["liquidatable_debt"], pts[0]["bad_debt"]) if pts else (0.0, 0.0)


def position_depth(graph: dict, market_id: str, tokens: list[str], admin: list[dict] | None = None) -> dict:
    """D199–D202, pure: the position's extra layers. `tokens` are its collateral and what it wraps or redeems into
    (lower-case addresses); `admin` the admin surface's rows for its market."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    out_edges: dict[str, list[dict]] = {}
    for e in graph["edges"]:
        out_edges.setdefault(e["source"], []).append(e)
    held = nodes.get(market_id)
    if held is None:
        return {}
    label = held["label"].removeprefix("Blue ")
    oracle = next((e["target"] for e in out_edges.get(market_id, []) if e["rel"] == "priced by"), None)
    feeds = []
    for e in out_edges.get(oracle, []):
        if e["rel"] in ("reads", "converts through") and e["target"] in nodes:
            d = nodes[e["target"]]["details"]
            feeds.append(
                {
                    "label": nodes[e["target"]]["label"],
                    "address": e["target"],
                    "role": e.get("details", {}).get("role"),
                    "class": d.get("oracle_class"),
                    "kind": d.get("constant_kind"),
                    "freshness": d.get("freshness"),
                    "stale": bool(d.get("stale")),
                    "shared": d.get("shared_text"),
                }
            )
    siblings = []
    for n in nodes.values():
        d = n["details"]
        if not d.get("sibling") or label not in str(d.get("linked_by", "")):
            continue
        liq, bad = _curve_at(d.get("liquidation_curve"), FALL)
        siblings.append(
            {
                "label": n["label"].removeprefix("Blue "),
                "linked_by": d.get("linked_by"),
                "borrow": float(d.get("total_borrow") or 0),
                "unit": d.get("loan_unit"),
                "liquidatable_at_fall": liq,
                "bad_debt_at_fall": bad,
                "oracle_class": d.get("oracle_class"),
            }
        )
    siblings.sort(key=lambda s: -s["liquidatable_at_fall"])
    backing, grades, supply = [], {}, []
    for t in tokens:
        n = nodes.get(t)
        if n is None:
            continue
        if n["details"].get("supply_text"):
            supply.append(f"{n['label']}: {n['details']['supply_text']}")  # D216
        if n["details"].get("pharos_grade"):
            grades[n["label"]] = n["details"]["pharos_grade"]
        for e in out_edges.get(t, []):
            if e["rel"] == "backed by (Pharos)" and e["target"] in nodes:
                backing.append(
                    {
                        "token": n["label"],
                        "backed_by": nodes[e["target"]]["label"],
                        "share": e.get("details", {}).get("share"),
                    }
                )
    protocols = {}
    for src in [market_id, *tokens]:
        for e in out_edges.get(src, []):
            if e["rel"] in ("runs on", "issued by") and e["target"] in nodes:
                p = nodes[e["target"]]
                protocols[p["label"]] = {
                    "concentration": p["details"].get("concentration"),
                    "concentrated": bool(p["details"].get("concentrated")),
                }
    return {
        "market": label,
        "market_curve": held["details"].get("liquidation_curve") or [],  # D206: what the incident liquidates
        "oracle": nodes[oracle]["details"].get("oracle_class") if oracle in nodes else None,
        "oracle_shared": nodes[oracle]["details"].get("shared_text") if oracle in nodes else None,  # D215
        "supply": supply,
        "feeds": feeds,
        "admin": admin or [],
        "siblings": siblings,
        "sibling_fall": FALL,
        "grades": grades,
        "backing": backing,
        "protocols": protocols,
    }


def profile_text(p) -> str:
    """D200, pure: the oracle as `scenario.oracle_profile` read it; for a meta-oracle, its two sources and the switch."""
    if p.kind == "meta-oracle" and p.live is not None:
        lock = f"{p.timelock_s / 3600:g} h" if p.timelock_s else "its challenge timelock"
        thr = f"{p.deviation_threshold:.2%}" if p.deviation_threshold is not None else "its threshold"
        other = p.other.kind if p.other else "unknown"
        return (
            f"a meta-oracle reading its {'primary' if p.on_primary else 'backup' if p.on_primary is False else 'live'} "
            f"source ({p.live.kind}{', ' + p.live.name if p.live.name else ''}); a divergence above {thr} can switch "
            f"it, after {lock}, to the other ({other})"
        )
    return f"{p.kind}" + (f", TWAP {p.twap_s} s" if p.twap_s else "") + (f" ({p.name})" if p.name else "")


def lines(depth: dict) -> list[str]:
    """The extra layers in words, for the terminal and the report."""
    if not depth:
        return []
    out = [f"oracle: {depth['oracle_profile']}"] if depth.get("oracle_profile") else []
    if depth.get("oracle_shared"):
        out.append(f"the oracle is {depth['oracle_shared']}")
    for f in depth["feeds"]:
        out.append(
            f"oracle input {f['label']} ({f['role'] or 'feed'}): {f['class'] or 'not classified'}"
            + (f", {f['kind']}" if f.get("kind") else "")
            + (f"; {f['freshness']}" if f["freshness"] else "")
            + (f"; {f['shared']}" if f.get("shared") else "")
        )
    for a in depth["admin"]:
        out.append(f"who can change it: {a['text']}")
    if depth["siblings"]:
        fall = depth["sibling_fall"]
        out.append(
            f"{len(depth['siblings'])} sibling market(s) sell the same collateral or read the same price; at a "
            f"{fall:.0%} fall: "
            + "; ".join(
                f"{s['label']} {s['liquidatable_at_fall']:,.0f} {s['unit']} liquidatable" for s in depth["siblings"][:4]
            )
        )
    out += [f"concentration: {s}" for s in depth.get("supply", [])]
    out += [f"concentration: {s}" for s in depth.get("position_share", [])]
    for t, g in depth["grades"].items():
        out.append(f"issuer grade (Pharos): {t} {g}")
    for b in depth["backing"]:
        share = f" ({b['share']:.0%})" if isinstance(b["share"], (int, float)) else ""
        out.append(f"off-chain backing (Pharos): {b['token']} backed by {b['backed_by']}{share}")
    for name, p in depth["protocols"].items():
        if p["concentration"]:
            out.append(f"protocol: {p['concentration']}")
    return out


def admin_rows(contracts: dict, timelock_over) -> list[dict]:
    """D201, pure: who can change each contract behind the position's market, and how fast: one row per upgradeable or
    owned contract (the oracle, its feeds, the tokens, Pendle's SY), from `admin.AdminWatch` once it read its state."""
    rows = []
    for c in sorted(contracts.values(), key=lambda c: (not c.upgradeable, c.symbol)):
        who = c.admin or c.owner
        if not (c.upgradeable or who):
            continue
        tl = timelock_over(c.address)
        delay = (
            f"through a {tl.timelock_delay / 3600:g} h timelock"
            if tl and tl.timelock_delay
            else "with no timelock seen"
        )
        what = "upgradeable" if c.upgradeable else "owned"
        rows.append(
            {
                "address": c.address,
                "role": c.roles[0] if c.roles else "",
                "upgradeable": c.upgradeable,
                "admin": who,
                "timelock_h": tl.timelock_delay / 3600 if tl and tl.timelock_delay else None,
                "text": f"{c.symbol or c.address[:10]} ({c.roles[0] if c.roles else 'contract'}): {what}"
                + (f" by {who[:10]}…" if who else "")
                + f", {delay}",
            }
        )
    return rows
