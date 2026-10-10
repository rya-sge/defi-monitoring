"""Propagation engine: a deterministic shock through the dependency graph, driven by rules (plan
2026-10-10-propagation-engine, D89–D96).

The graph is graph.py's form: nodes with `id`, `kind`, `label`, `details`; edges with `source`, `target`, `rel`,
`amount`, `unit`, `details`. An edge points from a node to what it depends on (a market → its oracle), so a shock
travels against the edges, from a dependency to what depends on it, unless a rule sends it along an edge (a market's
liquidation sales → its collateral).

Effects a node can carry (D90), each input stored per (effect, source node, rule) so that a later round replaces it:
  misreport  factor m on an oracle or feed: it reads m × what it should      combine: product
  frozen     the oracle or feed no longer moves                               combine: any
  price      factor f on an asset or a Pendle pool: market value × f          combine: product, × squeeze impact
  sale       USD of collateral sold into an asset's pool by liquidations      combine: sum
  loss       what lenders, a vault or a depositor lose, in the loan token     combine: sum
  collateral (internal) the collateral's price factor and whether the market's oracle follows it

Rules are data (registry.json `engine`, D91): for each edge, effect and direction the first matching edge rule names
the transmission; for each node the first matching node rule names its model. Nothing here knows Morpho beyond the
`blue_market` model; a new behaviour a rule cannot express is a new function in TRANSMISSIONS or NODE_MODELS.
"""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field

from .discover import REGISTRY, morpho_lif
from .drain import d_star

E = REGISTRY["engine"]
NEUTRAL = {"misreport": 1.0, "frozen": False, "price": 1.0, "sale": 0.0, "loss": 0.0}
MODES = ("reads-low", "reads-high", "frozen", "price")


# --- shocks


@dataclass(frozen=True)
class Shock:
    node: str
    mode: str  # reads-low | reads-high | frozen | price
    size: float = 0.0  # a fraction; for price, the signed change (-0.3 = a 30 % fall)

    def effect(self) -> tuple[str, object]:
        if self.mode == "reads-low":
            return "misreport", 1 - self.size
        if self.mode == "reads-high":
            return "misreport", 1 + self.size
        if self.mode == "frozen":
            return "frozen", True
        if self.mode == "price":
            return "price", 1 + self.size
        raise ValueError(f"unknown shock mode {self.mode!r}; one of {', '.join(MODES)}")

    @property
    def label(self) -> str:
        if self.mode == "frozen":
            return f"{self.node} frozen"
        return (
            f"{self.node} {self.mode} {self.size:+.0%}"
            if self.mode == "price"
            else f"{self.node} {self.mode} {self.size:.0%}"
        )


def parse_size(text: str) -> float:
    t = text.strip()
    return float(t[:-1]) / 100 if t.endswith("%") else float(t)


def parse_shock(spec: str) -> Shock:
    """`<node>:<mode>[:<size>]`, e.g. `0xf17c…:frozen`, `0x77ee…:reads-low:10%`, `0x19eb…:price:-30%`."""
    parts = spec.split(":")
    if len(parts) < 2 or parts[1] not in MODES:
        raise ValueError(f"shock {spec!r}: expected <node>:<mode>[:<size>] with a mode in {', '.join(MODES)}")
    node, mode = parts[0].strip().lower(), parts[1]
    if mode == "frozen":
        return Shock(node, mode)
    if len(parts) < 3:
        raise ValueError(f"shock {spec!r}: {mode} needs a size, e.g. {mode}:10%")
    size = parse_size(parts[2])
    if mode == "price" and not parts[2].strip().startswith(("-", "+")):
        size = -abs(size)  # "price:30%" reads as a fall
    return Shock(node, mode, size)


# --- rules


@dataclass
class Rule:
    id: str
    apply: str
    effect: str | None = None  # edge rules: the effect carried
    rel: str | None = None
    direction: str = "dependents"  # dependents: against the edge; dependencies: along it
    when: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    basis: str = ""


def rules_from(data: dict | None) -> tuple[list[Rule], list[Rule]]:
    data = data or {}
    keys = {"id", "apply", "effect", "rel", "direction", "when", "params", "basis"}

    def mk(lst):
        return [Rule(**{k: v for k, v in r.items() if k in keys}) for r in lst or []]

    return mk(data.get("edge_rules")), mk(data.get("node_rules"))


DEFAULT_EDGE_RULES, DEFAULT_NODE_RULES = rules_from(E)

OPS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    "gt": lambda a, b: a is not None and a > b,
    "gte": lambda a, b: a is not None and a >= b,
    "lt": lambda a, b: a is not None and a < b,
    "lte": lambda a, b: a is not None and a <= b,
    "contains": lambda a, b: a is not None and str(b).lower() in str(a).lower(),
    "exists": lambda a, b: (a is not None) == bool(b),
}


def _node_field(node: dict, name: str):
    if name in ("id", "kind", "label"):
        return node.get(name)
    return (node.get("details") or {}).get(name)


def _lookup(key: str, scope: dict):
    """Value of a criterion key: rel, value, edge.<f>, from.<f>, to.<f>, node.<f>."""
    if key in ("rel", "value"):
        return scope.get(key)
    head, _, name = key.partition(".")
    if head == "edge":
        e = scope["edge"]
        return (
            e.get(name) if name in ("rel", "amount", "unit", "source", "target") else (e.get("details") or {}).get(name)
        )
    if head in ("from", "to", "node"):
        return _node_field(scope[head], name)
    raise KeyError(f"unknown criterion {key!r}")


def matches(when: dict, scope: dict) -> bool:
    """Pure: every criterion holds. A key ends with __<op> for an operator other than equality."""
    for key, want in when.items():
        name, op = key, "eq"
        m = re.match(r"^(.*)__(\w+)$", key)
        if m and m.group(2) in OPS:
            name, op = m.group(1), m.group(2)
        try:
            if not OPS[op](_lookup(name, scope), want):
                return False
        except TypeError:
            return False
    return True


# --- the graph


class _Graph:
    def __init__(self, graph):
        if hasattr(graph, "nodes") and isinstance(graph.nodes, dict):
            graph = {"nodes": list(graph.nodes.values()), "edges": graph.edges}
        self.nodes = {n["id"]: n for n in graph["nodes"]}
        self.incoming: dict[str, list[dict]] = {}
        self.outgoing: dict[str, list[dict]] = {}
        for e in graph["edges"]:
            self.outgoing.setdefault(e["source"], []).append(e)
            self.incoming.setdefault(e["target"], []).append(e)


@dataclass
class NodeState:
    inputs: dict = field(default_factory=dict)  # (effect, source, rule id) -> value
    out: dict = field(default_factory=dict)  # effective effects after the node model
    detail: dict = field(default_factory=dict)  # what the node model computed (a market's outcome)
    model: str = ""


@dataclass
class Step:
    source: str
    target: str
    effect: str
    value: object
    rule: str
    basis: str


@dataclass
class Result:
    states: dict[str, NodeState]
    trace: list[Step]
    evaluations: int
    shocks: list[Shock]
    converged: bool = True

    def loss(self, node: str) -> float:
        st = self.states.get(node)
        return float(st.out.get("loss", 0.0)) if st else 0.0

    def markets(self) -> dict[str, dict]:
        return {nid: st.detail for nid, st in self.states.items() if st.model == "blue_market" and st.detail}


# --- node models


def _combine(inputs: dict) -> dict:
    out: dict = {}
    for (eff, _src, _rule), v in inputs.items():
        if eff in ("misreport", "price"):
            out[eff] = out.get(eff, 1.0) * v
        elif eff == "frozen":
            out[eff] = out.get(eff, False) or bool(v)
        elif eff in ("sale", "loss"):
            out[eff] = out.get(eff, 0.0) + v
    return out


def model_combine(g, nid, st, params) -> tuple[dict, dict]:
    out = _combine(st.inputs)
    out.pop("sale", None)  # only an asset's pool absorbs sales
    return out, {}


def _depth(g, nid, params) -> float | None:
    if nid in (params.get("depth_usd") or E.get("depth_usd") or {}):
        return float((params.get("depth_usd") or E["depth_usd"])[nid])
    if params.get("depth") == "pendle_pool":
        for e in g.outgoing.get(nid, []):
            if e["rel"] == "trades in / redeems through":
                liq = _node_field(g.nodes.get(e["target"], {}), "liquidity_usd")
                if liq:
                    return float(liq)
    return None


def _floor(g, nid, params) -> float:
    """Lowest factor the sales alone can push the price to. `pendle_maturity`: a PT redeems at par at maturity, so a
    buyer holding it there stops the fall where it yields `stress_yield`: ((1 + implied) / (1 + stress))^(days / 365)."""
    if params.get("floor") != "pendle_maturity":
        return float(params.get("floor") or 0.0)
    for e in g.outgoing.get(nid, []):
        if e["rel"] == "trades in / redeems through":
            pool = g.nodes.get(e["target"], {})
            days, implied = _node_field(pool, "days_to_maturity"), _node_field(pool, "implied_apy")
            if days is not None and implied is not None:
                stress = float(params.get("stress_yield", 0.5))
                return ((1 + implied) / (1 + stress)) ** (max(0.0, days) / 365) if stress > implied else 1.0
    return 0.0


def model_asset_price(g, nid, st, params) -> tuple[dict, dict]:
    """The asset's price: shocks and moves from what it wraps, times the impact of the collateral sold into its pool,
    a constant-product pool with reserves depth / 2 on each side, bounded below by a floor (D94). No depth: the sale
    moves nothing. Sales are valued at today's price, so the impact only grows as liquidations do."""
    out = _combine(st.inputs)
    sold = out.pop("sale", 0.0)
    depth = _depth(g, nid, params)
    impact, floor = 1.0, _floor(g, nid, params)
    if sold > 0 and depth:
        r = depth / 2
        impact = max(floor, (r / (r + sold)) ** 2)
    if impact != 1.0:
        out["price"] = out.get("price", 1.0) * impact
    detail = {"sold_usd": sold, "depth_usd": depth, "impact": impact, "floor": floor} if sold else {}
    return out, detail


def _evaluate(positions, fo: float, fm: float, lltv: float, slip: float) -> dict:
    """Pure: Blue's outcome for every position at oracle factor fo and market factor fm (D92)."""
    lif = morpho_lif(lltv)
    pays = fo > 0 and (fm / fo) * (1 - slip) >= 1 / lif
    o = {"liquidated_debt": 0.0, "positions_liquidated": 0, "bad_debt": 0.0, "insolvent": 0.0, "sold": 0.0}
    for value, debt in positions:
        if debt <= 0:
            continue
        vo, vm = value * fo, value * fm
        if vo * lltv < debt and pays:
            repaid = min(debt, vo / lif)
            o["liquidated_debt"] += repaid
            o["positions_liquidated"] += 1
            o["bad_debt"] += max(0.0, debt - vo / lif)
            o["sold"] += repaid * lif / fo  # the seized collateral, valued at today's price: a quantity, not a price
        else:
            o["insolvent"] += max(0.0, debt - vm * (1 - slip))
    return o


def model_blue_market(g, nid, st, params) -> tuple[dict, dict]:
    """A Morpho Blue market: liquidations, write-offs, insolvent debt and the drain, net of the state before the shock."""
    d = g.nodes[nid].get("details") or {}
    ins = st.inputs
    m = 1.0
    frozen = False
    f, follows = 1.0, False
    for (eff, _src, _rule), v in ins.items():
        if eff == "misreport":
            m *= v
        elif eff == "frozen":
            frozen = frozen or bool(v)
        elif eff == "collateral":
            f *= v["factor"]
            follows = follows or bool(v["follows"])
    fo = m * (f if follows and not frozen else 1.0)
    fm = f
    lltv = float(d.get("lltv_value") or 0.0)
    positions = d.get("_positions") or []
    slip = float(params.get("slippage", 0.0))
    if not lltv:
        return {}, {"error": "no LLTV on the node"}
    now, after = _evaluate(positions, 1.0, 1.0, lltv, slip), _evaluate(positions, fo, fm, lltv, slip)
    delta = 1 - fm / fo if fo > 0 else 0.0
    threshold = d_star(lltv, float(params.get("buy_cost", REGISTRY["watch"]["drain_buy_cost"])))
    drained = float(d.get("free_liquidity") or 0.0) if delta > threshold else 0.0
    drain_loss = drained * max(0.0, 1 - (1 - delta) / lltv)
    net = {k: after[k] - now[k] for k in after}
    loss = max(0.0, net["bad_debt"] + net["insolvent"]) + drain_loss
    usd = d.get("loan_usd")
    sold_usd = net["sold"] * usd if usd else 0.0
    detail = {
        "oracle_factor": fo,
        "market_factor": fm,
        "oracle_misreport": m,
        "oracle_frozen": frozen,
        "oracle_follows": follows,
        "liquidated_debt": net["liquidated_debt"],
        "positions_liquidated": net["positions_liquidated"],
        "bad_debt": net["bad_debt"],
        "insolvent": net["insolvent"],
        "discount": delta,
        "drain_threshold": threshold,
        "drained": drained,
        "drain_loss": drain_loss,
        "lender_loss": loss,
        "collateral_sold_usd": sold_usd,  # valued at today's price
        "collateral_sold": net["sold"],
        "loan_unit": d.get("loan_unit"),
        "before": now,
    }
    return {"loss": loss, "sale": sold_usd}, detail


NODE_MODELS = {"combine": model_combine, "asset_price": model_asset_price, "blue_market": model_blue_market}


# --- edge transmissions: (graph, edge, from id, to id, effect, value, params, states) -> [(node, effect, value)]


def t_stop(g, e, frm, to, eff, val, p, states):
    return []


def t_pass(g, e, frm, to, eff, val, p, states):
    if eff == "frozen":
        return [(to, "frozen", bool(val))]
    return [(to, p.get("as", eff), val ** p.get("exponent", 1))]


def t_collateral_price(g, e, frm, to, eff, val, p, states):
    return [(to, "collateral", {"factor": val, "follows": bool(p.get("follows"))})]


def t_liquidation_sale(g, e, frm, to, eff, val, p, states):
    return [(to, "sale", val)] if val > 0 else []


def t_supplier_loss(g, e, frm, to, eff, val, p, states):
    """market → its supplier: the supplier's share of the market's supply (edge amount ÷ total supply)."""
    total = _node_field(g.nodes[frm], "total_supply")
    share = min(1.0, (e.get("amount") or 0.0) / total) if total else 0.0
    return [(to, "loss", val * share)] if share else []


def t_depositor_loss(g, e, frm, to, eff, val, p, states):
    """vault → a depositor: the depositor's share of the vault's total assets."""
    total = _node_field(g.nodes[frm], "total_assets_value")
    share = min(1.0, (e.get("amount") or 0.0) / total) if total else 0.0
    return [(to, "loss", val * share)] if share else []


TRANSMISSIONS = {
    "stop": t_stop,
    "pass": t_pass,
    "collateral_price": t_collateral_price,
    "liquidation_sale": t_liquidation_sale,
    "supplier_loss": t_supplier_loss,
    "depositor_loss": t_depositor_loss,
}


# --- the run


def _changed(a, b, eps: float) -> bool:
    if isinstance(a, dict) or isinstance(b, dict):
        return a != b
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None:
        return a != b
    return abs(a - b) > eps * max(1.0, abs(a), abs(b))


def run(graph, shocks: list[Shock], extra: dict | None = None) -> Result:
    """Apply the shocks and propagate until nothing moves (ε) or the evaluation budget is spent (D94)."""
    g = graph if isinstance(graph, _Graph) else _Graph(graph)
    xe, xn = rules_from(extra)
    edge_rules, node_rules = xe + DEFAULT_EDGE_RULES, xn + DEFAULT_NODE_RULES
    eps, budget = float(E["eps"]), int(E["max_evaluations"])
    states: dict[str, NodeState] = {}
    trace: list[Step] = []
    queue, queued = deque(), set()

    def push(nid):
        if nid not in queued:
            queue.append(nid)
            queued.add(nid)

    for sh in shocks:
        if sh.node not in g.nodes:
            raise KeyError(f"no node {sh.node} in the graph")
        eff, val = sh.effect()
        states.setdefault(sh.node, NodeState()).inputs[(eff, "shock", sh.mode)] = val
        push(sh.node)

    evaluations = 0
    while queue and evaluations < budget:
        nid = queue.popleft()
        queued.discard(nid)
        evaluations += 1
        node, st = g.nodes[nid], states[nid]
        rule = next((r for r in node_rules if matches(r.when, {"node": node})), None)
        model = NODE_MODELS[rule.apply] if rule else model_combine
        out, detail = model(g, nid, st, rule.params if rule else {})
        st.out, st.detail, st.model = out, detail, rule.apply if rule else "combine"
        for eff, val in out.items():
            if eff in NEUTRAL and not _changed(val, NEUTRAL[eff], eps):
                continue
            hops = [(e, e["source"], "dependents") for e in g.incoming.get(nid, [])]
            hops += [(e, e["target"], "dependencies") for e in g.outgoing.get(nid, [])]
            for e, other, direction in hops:
                scope = {"rel": e["rel"], "edge": e, "from": node, "to": g.nodes[other], "value": val}
                r = next(
                    (
                        r
                        for r in edge_rules
                        if r.effect == eff
                        and r.direction == direction
                        and (r.rel is None or r.rel == e["rel"])
                        and matches(r.when, scope)
                    ),
                    None,
                )
                if r is None:
                    continue
                for target, eff2, val2 in TRANSMISSIONS[r.apply](g, e, nid, other, eff, val, r.params, states):
                    tst = states.setdefault(target, NodeState())
                    key = (eff2, nid, r.id)
                    if key not in tst.inputs or _changed(tst.inputs[key], val2, eps):
                        tst.inputs[key] = val2
                        trace.append(Step(nid, target, eff2, val2, r.id, r.basis))
                        push(target)
    return Result(states, trace, evaluations, list(shocks), converged=not queue)


def path(result: Result, node: str, depth: int = 0, seen: frozenset = frozenset()) -> list[str]:
    """How the effects reached `node`, one line per input, indented by hop."""
    st = result.states.get(node)
    if not st or node in seen or depth > 12:
        return []
    lines = []
    for (eff, src, rule), val in st.inputs.items():
        shown = (
            f"{val:.6g}"
            if isinstance(val, float)
            else (f"factor {val['factor']:.6g}, follows {val['follows']}" if isinstance(val, dict) else str(val))
        )
        lines.append(f"{'  ' * depth}{node} ← {eff} {shown} from {src} [{rule}]")
        if src != "shock":
            lines += path(result, src, depth + 1, seen | {node})
    return lines


def sweep(
    graph, mode: str, size: float, kinds: tuple[str, ...], extra: dict | None = None, only: list[str] | None = None
):
    """The same failure on every node of the given kinds, one at a time: [(node id, Result)]."""
    g = graph if isinstance(graph, _Graph) else _Graph(graph)
    out = []
    for nid, n in g.nodes.items():
        if n["kind"] not in kinds or (only is not None and nid not in only):
            continue
        out.append((nid, run(g, [Shock(nid, mode, size)], extra)))
    return out
