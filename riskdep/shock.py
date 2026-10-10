"""The `shock` command: build or replay a dependency graph, apply shocks with the propagation engine, and print what
each market, each vault and a depositor lose, with the path the loss took (plan 2026-10-10-propagation-engine, D89).
"""

from __future__ import annotations

import json
from pathlib import Path

from . import engine as EN


def resolve(nodes: dict, text: str) -> str:
    """A node id (address or market id), or a fragment of a label that matches one node only (case-insensitive)."""
    key = text.strip().lower()
    if key in nodes:
        return key
    hits = [nid for nid, n in nodes.items() if key in n["label"].lower()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise ValueError(f"no node matches {text!r}; `shock --list` shows the candidates")
    names = "; ".join(f"{nodes[h]['label']} ({h})" for h in hits[:8])
    raise ValueError(f"{text!r} matches {len(hits)} nodes: {names}; give the address")


def resolve_shocks(nodes: dict, specs: list[str]) -> list[EN.Shock]:
    out = []
    for spec in specs:
        head, _, rest = spec.partition(":")
        # a label fragment may contain spaces but no colon; the mode follows the first colon
        sh = EN.parse_shock(f"0x:{rest}")
        out.append(EN.Shock(resolve(nodes, head), sh.mode, sh.size))
    return out


def _graph_dict(g) -> dict:
    return {"nodes": list(g.nodes.values()), "edges": g.edges}


def _markets_of(gd: dict) -> dict[str, dict]:
    return {n["id"]: n for n in gd["nodes"] if "market_id" in n["details"]}


def dependents(gd: dict) -> dict[str, list[str]]:
    """For every oracle, feed and asset: the Blue markets whose price it enters (structure only, for --list)."""
    priced_by, reads, takes, wraps = {}, {}, {}, {}
    for e in gd["edges"]:
        if e["rel"] == "priced by":
            priced_by.setdefault(e["target"], []).append(e["source"])
        elif e["rel"] in ("reads", "converts through"):
            reads.setdefault(e["target"], []).append(e["source"])
        elif e["rel"] == "takes as collateral":
            takes.setdefault(e["target"], []).append(e["source"])
        elif e["rel"] == "wraps":
            wraps.setdefault(e["target"], []).append(e["source"])
    out = {}
    for n in gd["nodes"]:
        nid = n["id"]
        if n["kind"] == "Oracle":
            ms = list(priced_by.get(nid, []))
            for o in reads.get(nid, []):
                ms += priced_by.get(o, [])
        elif n["kind"] == "Asset":
            ms = list(takes.get(nid, []))
            for w in wraps.get(nid, []):
                ms += takes.get(w, [])
        else:
            continue
        if ms:
            out[nid] = sorted(set(ms))
    return out


def list_targets(gd: dict, line=print) -> None:
    nodes, markets, deps = {n["id"]: n for n in gd["nodes"]}, _markets_of(gd), dependents(gd)
    line(f"  {'node':<46} {'kind':<7} {'class':<15} {'held':>4} {'sibl.':>5}  id")
    rows = []
    for nid, ms in deps.items():
        held = sum(1 for m in ms if not markets[m]["details"].get("sibling"))
        rows.append((-held, -len(ms), nodes[nid]["label"], nid, held, len(ms) - held))
    for _, _, label, nid, held, sib in sorted(rows):
        n = nodes[nid]
        line(
            f"  {label[:46]:<46} {n['kind']:<7} {str(n['details'].get('oracle_class') or ''):<15} {held:>4} {sib:>5}  {nid}"
        )


def _fmt(x: float) -> str:
    if abs(x) >= 1e6:
        return f"{x / 1e6:,.2f}M"
    if abs(x) >= 1e3:
        return f"{x / 1e3:,.1f}k"
    return f"{x:,.0f}"


def actors(gd: dict) -> dict[str, dict]:
    return {n["id"]: n for n in gd["nodes"] if n["kind"] == "Actor"}


def report(gd: dict, res: EN.Result, line=print, max_path: int = 30) -> dict:
    nodes = {n["id"]: n for n in gd["nodes"]}
    line(
        "  shocks: "
        + "; ".join(f"{nodes[s.node]['label']} ({s.node[:10]}…) {s.label.split(' ', 1)[1]}" for s in res.shocks)
    )
    mk = res.markets()
    line(
        f"  {'market':<34} {'':<4} {'oracle class':<15} {'oracle':>7} {'market':>7} {'liquidated':>11} {'pos':>4} "
        f"{'write-off':>10} {'insolvent':>10} {'drained':>9} {'lenders lose':>13} {'sold $':>9}"
    )
    for mid, d in sorted(
        mk.items(), key=lambda kv: (bool(nodes[kv[0]]["details"].get("sibling")), -kv[1].get("lender_loss", 0))
    ):
        n = nodes[mid]
        tag = "sib" if n["details"].get("sibling") else "held"
        line(
            f"  {n['label'].removeprefix('Blue ')[:34]:<34} {tag:<4} {str(n['details'].get('oracle_class')):<15} "
            f"{d['oracle_factor']:>7.3f} {d['market_factor']:>7.3f} {_fmt(d['liquidated_debt']):>11} "
            f"{d['positions_liquidated']:>4} {_fmt(d['bad_debt']):>10} {_fmt(d['insolvent']):>10} {_fmt(d['drained']):>9} "
            f"{_fmt(d['lender_loss']) + ' ' + str(d.get('loan_unit') or ''):>13} {_fmt(d['collateral_sold_usd']):>9}"
        )
    for nid, st in res.states.items():
        if st.model == "asset_price" and st.detail:
            dd = st.detail
            depth = (
                f"a {_fmt(dd['depth_usd'])} pool" if dd["depth_usd"] else "a pool of unknown depth (no price impact)"
            )
            line(
                f"  squeeze: {_fmt(dd['sold_usd'])} of {nodes[nid]['label']} (at today's price) sold into {depth}: "
                f"impact × {dd['impact']:.4f}"
                + (f", floor {dd['floor']:.4f}" if dd.get("floor") else "")
                + f", price × {st.out.get('price', 1.0):.4f}"
            )
    losses = {}
    for aid, a in actors(gd).items():
        loss = res.loss(aid)
        if loss:
            total = a["details"].get("total_assets_value")
            pct = f" ({loss / total:.3%} of its {_fmt(total)})" if total else ""
            line(f"  {a['label']} loses {_fmt(loss)}{pct}")
            losses[aid] = loss
    if not losses:
        line("  no actor of the graph loses anything under this shock")
    for aid in losses:
        if a := nodes.get(aid):
            if "total_assets_value" in a["details"]:
                line(f"  path to {a['label']}:")
                for ln in EN.path(res, aid)[:max_path]:
                    line(f"    {_label_path(ln, nodes)}")
    line(f"  {res.evaluations} node evaluations, {len(res.trace)} propagation steps")
    if not res.converged:
        line("  WARNING: the evaluation budget ran out before the propagation settled; the numbers are not final")
    return {
        "shocks": [s.__dict__ for s in res.shocks],
        "markets": {mid: {k: v for k, v in d.items() if k != "before"} for mid, d in mk.items()},
        "losses": losses,
        "converged": res.converged,
        "trace": [st.__dict__ for st in res.trace],
    }


def _label_path(text: str, nodes: dict) -> str:
    for nid, n in nodes.items():
        if nid in text:
            text = text.replace(nid, n["label"])
    return text


def run_sweep(gd: dict, mode: str, size: float, extra: dict | None, top: int, line=print) -> list[dict]:
    """Every oracle and feed (or every asset, for a price shock) in turn; ranked by the vaults' total loss."""
    kinds = ("Asset",) if mode == "price" else ("Oracle",)
    vaults = [aid for aid, a in actors(gd).items() if "total_assets_value" in a["details"]]
    nodes = {n["id"]: n for n in gd["nodes"]}
    deps = dependents(gd)
    rows = []
    for nid, res in EN.sweep(gd, mode, size, kinds, extra, only=list(deps)):
        vloss = sum(res.loss(v) for v in vaults)
        mk = res.markets()
        worst = max(mk.items(), key=lambda kv: kv[1].get("lender_loss", 0), default=(None, {}))
        rows.append(
            {
                "node": nid,
                "label": nodes[nid]["label"],
                "kind": nodes[nid]["kind"],
                "vault_loss": vloss,
                "markets_hit": sum(1 for d in mk.values() if d.get("lender_loss") or d.get("liquidated_debt")),
                "worst_market": nodes[worst[0]]["label"] if worst[0] else None,
                "worst_market_loss": worst[1].get("lender_loss", 0.0),
            }
        )
    rows.sort(key=lambda r: (-r["vault_loss"], -r["worst_market_loss"]))
    total = sum(nodes[v]["details"]["total_assets_value"] for v in vaults) if vaults else 0
    line(
        f"  {'node':<46} {'kind':<7} {'vault loss':>11} {'% vault':>8} {'markets':>7}  worst market (its lenders lose)"
    )
    for r in rows[:top]:
        pct = f"{r['vault_loss'] / total:.3%}" if total else ""
        line(
            f"  {r['label'][:46]:<46} {r['kind']:<7} {_fmt(r['vault_loss']):>11} {pct:>8} {r['markets_hit']:>7}  "
            f"{(r['worst_market'] or '').removeprefix('Blue ')} ({_fmt(r['worst_market_loss'])})"
        )
    return rows


def load_rules(path: str | None) -> dict | None:
    if not path:
        return None
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict) or not ({"edge_rules", "node_rules"} & set(data)):
        raise ValueError(f"{path}: expected an object with edge_rules and/or node_rules lists")
    EN.rules_from(data)  # fails early on an unknown field
    unknown = {r.get("apply") for r in data.get("edge_rules", [])} - set(EN.TRANSMISSIONS)
    unknown |= {r.get("apply") for r in data.get("node_rules", [])} - set(EN.NODE_MODELS)
    if unknown:
        raise ValueError(
            f"{path}: unknown transmission(s) {sorted(unknown)}; known: {sorted(EN.TRANSMISSIONS) + sorted(EN.NODE_MODELS)}"
        )
    return data
