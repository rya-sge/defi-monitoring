"""The `shock` command: build or replay a dependency graph, apply shocks with the propagation engine, and print what
each market, each vault and a depositor lose, with the path the loss took (plan 2026-10-10-propagation-engine, D104).
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
            part = (
                f", {dd['absorbed_usd'] / dd['sold_usd']:.0%} absorbed" if dd["absorbed_usd"] < dd["sold_usd"] else ""
            )
            floor = f", floor {dd['floor']:.4f}" if dd.get("floor") and dd["impact"] == dd["floor"] else ""
            line(
                f"  sold into {nodes[nid]['label']}'s market: {_fmt(dd['sold_usd'])} offered (at today's price){part}: "
                f"impact × {dd['impact']:.4f}{floor}, price × {st.out.get('price', 1.0):.4f}"
                + (" (no quotes: no impact)" if dd["impact"] == 1.0 and not floor else "")
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


TRACE_FORMAT = "riskdep.shock-trace/1"
FACTORS = ("misreport", "reading", "price", "value")


def _unit(eff: str, node: dict, edges_of: dict) -> str | None:
    if eff in FACTORS:
        return "factor"
    if eff in ("sale", "onward"):
        return "USD"
    if eff == "exit":
        return "share"
    if eff == "loss":
        if node["details"].get("loan_unit"):
            return node["details"]["loan_unit"]
        return next((t for rel, t in edges_of.get(node["id"], []) if rel == "denominated in"), None)
    return None


def _display(eff: str, val, unit: str | None) -> str:
    if eff in FACTORS:
        return f"{eff} ×{val:.4f} ({val - 1:+.2%})"
    if eff == "frozen":
        return "frozen" if val else "not frozen"
    if eff == "collateral":
        follows = ", the oracle follows" if val.get("follows") else ""
        return f"collateral {val.get('kind', 'price')} ×{val['factor']:.4f} ({val['factor'] - 1:+.2%}){follows}"
    if eff in ("sale", "onward"):
        return f"{_fmt(val)} USD {'offered for sale' if eff == 'sale' else 'of underlying sold on'}"
    if eff == "exit":
        return f"{val:.0%} of the offer absorbed"
    if eff == "loss":
        return f"loss {_fmt(val)}" + (f" {unit}" if unit else "")
    return f"{eff} {val}"


def _change(eff: str, val):
    """The move a step carries, signed, in the effect's unit: a factor's change, an amount, a share not absorbed."""
    if eff in FACTORS:
        return val - 1
    if eff == "collateral":
        return val["factor"] - 1
    if eff == "exit":
        return val - 1
    if eff in ("sale", "onward", "loss"):
        return val
    return None


def _moved(out: dict) -> dict:
    """The effects of a node's output that differ from neutral."""
    keep = {}
    for eff, v in out.items():
        n = EN.NEUTRAL.get(eff)
        if n is None or (isinstance(n, bool) and bool(v) != n) or (not isinstance(n, bool) and abs(v - n) > 1e-12):
            keep[eff] = v
    return keep


def _headline(n: dict, st: EN.NodeState, unit: str | None, shocked: list[EN.Shock]) -> str:
    """One short line for a node's final state, for a label or a tooltip."""
    parts = [s.label.split(" ", 1)[1] for s in shocked]
    d, out = st.detail or {}, _moved(st.out)
    if st.model == "blue_market" and d:
        u = f" {d.get('loan_unit')}" if d.get("loan_unit") else ""
        if d.get("positions_liquidated"):
            executed = d.get("executed", 1.0)
            parts.append(
                f"{d['positions_liquidated']} positions liquidatable"
                + (f", only {executed:.0%} of their collateral sells" if executed < 1.0 else "")
                + f": {_fmt(d['liquidated_debt'])}{u} repaid, lenders lose {_fmt(d['lender_loss'])}{u}"
            )
        elif d.get("lender_loss"):
            parts.append(
                f"no liquidation, lenders lose {_fmt(d['lender_loss'])}{u}"
                + (f" (drained {_fmt(d['drained'])}{u})" if d.get("drained") else "")
            )
        else:
            parts.append(f"oracle ×{d['oracle_factor']:.4f}, market ×{d['market_factor']:.4f}, no liquidation")
        return "; ".join(parts)
    if st.model == "asset_price" and d:
        parts.append(f"{_fmt(d['sold_usd'])} USD offered, {d['absorbed_usd'] / d['sold_usd']:.0%} absorbed")
    for eff in ("misreport", "reading", "frozen", "price", "value"):
        if eff in out and not (eff == "misreport" and shocked):
            parts.append(_display(eff, out[eff], unit))
    if "loss" in out:
        total = n["details"].get("total_assets_value")
        parts.append(
            f"loses {_fmt(out['loss'])}"
            + (f" {unit}" if unit else "")
            + (f" ({out['loss'] / total:.3%} of its {_fmt(total)})" if total else "")
        )
    return "; ".join(parts) or "reached, nothing moves"


def _status(st: EN.NodeState, shocked: bool) -> str:
    out = _moved(st.out)
    if shocked:
        return "shocked"
    if out.get("loss"):
        return "loss"
    d = st.detail or {}
    if d.get("liquidated_debt"):
        return "liquidations"
    if st.model == "blue_market" and d:
        return "moved" if abs(d["oracle_factor"] - 1) > 1e-12 or abs(d["market_factor"] - 1) > 1e-12 else "reached"
    return "moved" if out else "reached"


def trace(
    gd: dict, res: EN.Result, block: int | None = None, as_of: str | None = None, extra: dict | None = None
) -> dict:
    """The propagation as data for a front end (D119): the graph with stable edge ids (`e<i>`, the position in its edge
    list, as graph.html numbers them), each step over an edge in order and by wave, each evaluation, every touched
    node's final state with a headline and the steps that hold its inputs, and the steps behind each loss."""
    nodes = {n["id"]: n for n in gd["nodes"]}
    edges_of: dict[str, list] = {}
    for e in gd["edges"]:
        edges_of.setdefault(e["source"], []).append((e["rel"], nodes[e["target"]]["label"]))
    loss_unit = {nid: _unit("loss", nodes[nid], edges_of) for nid in res.states}
    holder: dict[tuple, int] = {}
    steps = []
    for s in res.trace:
        unit = _unit(s.effect, nodes[s.target], edges_of)
        holder[(s.target, s.effect, s.source, s.rule)] = s.seq
        steps.append(
            {
                "seq": s.seq,
                "wave": s.wave,
                "edge": f"e{s.edge}" if s.edge is not None else None,
                "source": s.source,
                "target": s.target,
                "direction": s.direction,
                "effect": s.effect,
                "value": s.value,
                "change": _change(s.effect, s.value),
                "unit": unit,
                "display": _display(s.effect, s.value, unit),
                "rule": s.rule,
                "replaces": s.replaces,
            }
        )
    by_node: dict[str, list[EN.Shock]] = {}
    for sh in res.shocks:
        by_node.setdefault(sh.node, []).append(sh)

    def inputs(nid: str) -> list[int]:
        st = res.states.get(nid)
        return sorted(holder[(nid, e, src, r)] for (e, src, r) in st.inputs if src != "shock") if st else []

    def behind(nid: str) -> list[int]:
        seen, todo, out = set(), [nid], set()
        while todo:
            x = todo.pop()
            if x in seen:
                continue
            seen.add(x)
            for q in inputs(x):
                out.add(q)
                todo.append(res.trace[q - 1].source)
        return sorted(out)

    def evaluation(ev: EN.Evaluation) -> dict:
        """The node's state right after this evaluation: what a front end shows from this wave on."""
        st = EN.NodeState(out=ev.out, detail=ev.detail, model=ev.model)
        return {
            "seq": ev.seq,
            "wave": ev.wave,
            "node": ev.node,
            "model": ev.model,
            "status": _status(st, ev.node in by_node),
            "headline": _headline(nodes[ev.node], st, loss_unit[ev.node], by_node.get(ev.node, [])),
            "effects": _moved(ev.out),
            "detail": {k: v for k, v in ev.detail.items() if k != "before"},
        }

    first_wave = {}
    for ev in res.log:
        first_wave.setdefault(ev.node, ev.wave)
    final = {}
    for nid, st in res.states.items():
        final[nid] = {
            "status": _status(st, nid in by_node),
            "headline": _headline(nodes[nid], st, loss_unit[nid], by_node.get(nid, [])),
            "model": st.model or None,
            "effects": _moved(st.out),
            "loss_unit": loss_unit[nid] if "loss" in st.out else None,
            "detail": st.detail or {},
            "inputs": inputs(nid),
            "first_wave": first_wave.get(nid),
        }
    waves = []
    for w in sorted({ev.wave for ev in res.log} | {s.wave for s in res.trace}):
        waves.append(
            {
                "wave": w,
                "evaluated": list(dict.fromkeys(ev.node for ev in res.log if ev.wave == w)),
                "steps": [s.seq for s in res.trace if s.wave == w],
            }
        )
    used, rules = {s.rule for s in res.trace}, {}
    for r in EN.rules_from(extra)[0] + EN.DEFAULT_EDGE_RULES:  # a rules file's rule comes first, as in the run
        if r.id in used:
            rules.setdefault(r.id, {"apply": r.apply, "effect": r.effect, "rel": r.rel, "basis": r.basis})
    return {
        "format": TRACE_FORMAT,
        "block": block,
        "as_of": as_of,
        "note": "Waves are rounds of a fixed-point iteration, not time: a value can overshoot in an early wave and settle "
        "lower. Only the final state (`nodes`) is the answer; `evaluations_log` shows how the loop got there.",
        "shocks": [
            {
                "node": s.node,
                "mode": s.mode,
                "size": s.size,
                "label": f"{nodes[s.node]['label']} {s.label.split(' ', 1)[1]}",
            }
            for s in res.shocks
        ],
        "converged": res.converged,
        "evaluations": res.evaluations,
        "graph": {
            "nodes": [
                {**n, "details": {k: v for k, v in n["details"].items() if not k.startswith("_")}} for n in gd["nodes"]
            ],
            "edges": [{"id": f"e{i}", **e} for i, e in enumerate(gd["edges"])],
        },
        "rules": rules,
        "steps": steps,
        "evaluations_log": [evaluation(ev) for ev in res.log],
        "waves": waves,
        "nodes": final,
        "paths": {nid: behind(nid) for nid, f in final.items() if f["status"] == "loss"},
    }


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
