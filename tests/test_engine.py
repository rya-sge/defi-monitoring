"""The propagation engine: each transmission and node model on a small graph with numbers worked by hand, the rule
criteria, and scenarios on the recorded RockawayX USDC Yield graph (plan 2026-10-10-propagation-engine, US20, US21)."""

import json
from pathlib import Path

import pytest

from riskdep import clock, shock
from riskdep import engine as EN
from riskdep import graph as GR
from riskdep.discover import marginal_curve, morpho_lif

F, ORC, M, C, L, V, U = "0xf", "0xo", "0xm", "0xc", "0xl", "0xv", "user:0xu"
LIF = morpho_lif(0.86)  # 1.04384
D_STAR = 1 - 0.86 / 1.005  # 0.1443, with the registry's drain_buy_cost


def e(s, t, rel, amount=None, **details):
    return {"source": s, "target": t, "rel": rel, "amount": amount, "unit": None, "details": details}


def graph(cls="constant-price", positions=((100.0, 80.0),), free=100.0, role="BASE_FEED_1"):
    """A feed → oracle → market taking C and lending USDC; a vault holds half the market, a depositor 30 % of it."""
    return {
        "nodes": [
            {"id": F, "kind": "Oracle", "label": "feed", "details": {}},
            {"id": ORC, "kind": "Oracle", "label": "oracle", "details": {"oracle_class": cls}},
            {
                "id": M,
                "kind": "Pool",
                "label": "Blue C/USDC",
                "details": {
                    "market_id": M,
                    "oracle_class": cls,
                    "lltv_value": 0.86,
                    "_positions": [list(p) for p in positions],
                    "free_liquidity": free,
                    "total_supply": 1000.0,
                    "loan_usd": 1.0,
                    "loan_unit": "USDC",
                },
            },
            {"id": C, "kind": "Asset", "label": "C", "details": {}},
            {"id": L, "kind": "Asset", "label": "USDC", "details": {}},
            {"id": V, "kind": "Actor", "label": "Vault", "details": {"total_assets_value": 2000.0}},
            {"id": U, "kind": "Actor", "label": "Depositor", "details": {}},
        ],
        "edges": [
            e(ORC, F, "reads", role=role),
            e(M, ORC, "priced by"),
            e(M, C, "takes as collateral"),
            e(M, L, "lends"),
            e(V, M, "supplies", 500.0),
            e(U, V, "deposits in", 600.0),
        ],
    }


def market(res):
    return res.markets()[M]


def test_a_base_feed_reading_high_opens_the_drain():
    res = EN.run(graph(), [EN.Shock(F, "reads-high", 0.2)])
    d = market(res)
    delta = 1 - 1 / 1.2
    assert delta > D_STAR and d["positions_liquidated"] == 0 and d["insolvent"] == 0
    assert d["drain_loss"] == pytest.approx(100 * (1 - (1 - delta) / 0.86))  # 3.10
    assert res.loss(V) == pytest.approx(d["lender_loss"] / 2) and res.loss(U) == pytest.approx(res.loss(V) * 0.3)


def test_a_quote_feed_reading_high_lowers_the_price_and_liquidates():
    res = EN.run(graph(role="QUOTE_FEED_1"), [EN.Shock(F, "reads-high", 0.2)])
    d = market(res)
    assert d["oracle_factor"] == pytest.approx(1 / 1.2) and d["positions_liquidated"] == 1 and d["drained"] == 0
    # the collateral is really worth 100, but Blue seizes it all at 83.3 and writes off what is left
    assert d["bad_debt"] == pytest.approx(80 - 100 / 1.2 / LIF)


@pytest.mark.parametrize(
    "cls,shocks,expected",
    [
        ("price-tracking", [EN.Shock(C, "price", -0.3)], 80 - 70 / LIF),  # liquidated, Blue's write-off
        ("constant-price", [EN.Shock(C, "price", -0.3)], 10 + 100 * (1 - 0.7 / 0.86)),  # insolvent + drain
        ("price-tracking", [EN.Shock(C, "price", -0.3), EN.Shock(F, "frozen")], 10 + 100 * (1 - 0.7 / 0.86)),
        ("not classified", [EN.Shock(C, "price", -0.3)], 10 + 100 * (1 - 0.7 / 0.86)),  # D108
    ],
)
def test_a_collateral_fall_depends_on_the_oracle(cls, shocks, expected):
    res = EN.run(graph(cls), shocks)
    assert market(res)["lender_loss"] == pytest.approx(expected)


def test_liquidation_sales_are_valued_at_todays_price():
    d = market(EN.run(graph("price-tracking"), [EN.Shock(C, "price", -0.3)]))
    assert d["collateral_sold_usd"] == pytest.approx(100.0)  # all the collateral, whatever its price after the fall


def test_debt_already_underwater_is_not_counted_as_the_shock():
    res = EN.run(graph(positions=((50.0, 80.0),), free=0.0), [EN.Shock(C, "price", -0.3)])
    # before: liquidatable and worth liquidating, so Blue's write-off; after: not worth liquidating, so insolvent
    assert market(res)["lender_loss"] == pytest.approx((80 - 35) - (80 - 50 / LIF))


def test_a_rules_file_overrides_and_stops():
    follow = {
        "edge_rules": [
            {
                "id": "mine",
                "effect": "price",
                "rel": "takes as collateral",
                "when": {"to.oracle_class": "not classified"},
                "apply": "collateral_price",
                "params": {"follows": True},
            }
        ]
    }
    res = EN.run(graph("not classified"), [EN.Shock(C, "price", -0.3)], follow)
    assert market(res)["lender_loss"] == pytest.approx(80 - 70 / LIF)
    assert any(s.rule == "mine" for s in res.trace)
    stop = {
        "edge_rules": [{"id": "cut", "effect": "misreport", "rel": "reads", "when": {"from.id": F}, "apply": "stop"}]
    }
    assert EN.run(graph(), [EN.Shock(F, "reads-high", 0.2)], stop).loss(V) == 0


def test_a_move_of_the_underlying_reaches_wrappers_and_pts():
    g = graph("price-tracking")
    g["nodes"] += [{"id": "0xu2", "kind": "Asset", "label": "U", "details": {}}]
    g["edges"] += [e(C, "0xu2", "wraps")]
    assert market(EN.run(g, [EN.Shock("0xu2", "price", -0.3)]))["market_factor"] == pytest.approx(0.7)
    g = graph("price-tracking")
    g["nodes"] += [
        {"id": "pendle:0xc", "kind": "Pool", "label": "Pendle pool", "details": {}},
        {"id": "0xy", "kind": "Asset", "label": "yield token", "details": {}},
    ]
    g["edges"] += [e(C, "pendle:0xc", "trades in / redeems through"), e("pendle:0xc", "0xy", "yield source")]
    assert market(EN.run(g, [EN.Shock("0xy", "price", -0.3)]))["market_factor"] == pytest.approx(0.7)


def pt_graph(pt_curve=None, pt_capacity=None, und_curve=None, und_capacity=None):
    """C is a PT whose pool trades against the yield token Y; the market's oracle reads C's pool through the feed F
    (a `tracks` edge), as a Pendle TWAP oracle does. Ten positions at HF 1.049: a 5 % fall liquidates them all."""
    g = graph("price-tracking", positions=[(100.0, 82.0)] * 10, free=0.0)
    for n in g["nodes"]:
        if n["id"] == M:
            n["details"]["oracle_tracks_bound"] = True
        if n["id"] == C:
            n["details"].update({"impact_curve": pt_curve or [], "capacity_usd": pt_capacity})
    g["nodes"] += [
        {
            "id": "pendle:0xc",
            "kind": "Pool",
            "label": "Pendle pool",
            "details": {"implied_apy": 0.1, "days_to_maturity": 365},
        },
        {
            "id": "0xy",
            "kind": "Asset",
            "label": "Y",
            "details": {"impact_curve": und_curve or [], "capacity_usd": und_capacity},
        },
    ]
    g["edges"] += [
        e(C, "pendle:0xc", "trades in / redeems through"),
        e("pendle:0xc", "0xy", "yield source"),
        e(F, C, "tracks"),
    ]
    return g


def test_the_oracle_follows_its_tracked_pool_once():
    """A sale lowers the PT's pool price; the oracle reads it through its feed, not twice through the collateral."""
    res = EN.run(pt_graph(pt_curve=[[100, 1.0], [1000, 0.9], [1e9, 0.8]]), [EN.Shock(C, "price", -0.05)])
    d = market(res)
    assert res.converged and d["positions_liquidated"] == 10
    assert d["oracle_factor"] == pytest.approx(0.95 * 0.9) and d["market_factor"] == pytest.approx(0.95 * 0.9)


def test_the_pt_floor_bounds_the_impact():
    res = EN.run(pt_graph(pt_curve=[[100, 1.0], [1e9, 0.1]]), [EN.Shock(C, "price", -0.05)])
    assert res.states[C].out["price"] == pytest.approx(0.95 * 1.1 / 1.5)  # a year to maturity, 10 % → 50 % APY


def test_beyond_capacity_liquidations_cannot_finish():
    res = EN.run(pt_graph(pt_curve=[[1e9, 1.0]], pt_capacity=300.0), [EN.Shock(C, "price", -0.05)])
    d = market(res)
    assert d["executed"] == pytest.approx(300 / res.states[C].detail["sold_usd"])
    full = market(EN.run(pt_graph(pt_curve=[[1e9, 1.0]]), [EN.Shock(C, "price", -0.05)]))
    assert d["liquidated_debt"] == pytest.approx(full["liquidated_debt"] * d["executed"])


def test_a_pt_sale_goes_on_to_the_underlyings_exit_and_lowers_the_pts_worth_only():
    res = EN.run(pt_graph(pt_curve=[[1e9, 1.0]], und_curve=[[100, 1.0], [1e9, 0.8]]), [EN.Shock(C, "price", -0.05)])
    assert res.states["0xy"].detail["sold_usd"] > 100  # what liquidators got for the PT, sold for dollars
    d = market(res)
    assert d["oracle_factor"] == pytest.approx(0.95)  # the pool price, which the oracle reads, did not move
    assert d["market_factor"] == pytest.approx(0.95 * 0.8)  # the PT's worth follows the underlying's exit


def test_an_underlying_move_reaches_the_pts_worth_not_its_oracle():
    """A PT_TO_ASSET oracle prices the PT against its underlying: a depeg of the underlying liquidates nobody."""
    d = market(EN.run(pt_graph(), [EN.Shock("0xy", "price", -0.3)]))
    assert d["oracle_factor"] == pytest.approx(1.0) and d["market_factor"] == pytest.approx(0.7)
    assert d["positions_liquidated"] == 0 and d["insolvent"] == pytest.approx(10 * (82 - 70))


def test_a_loan_token_move_read_by_a_quote_feed_changes_nothing():
    g = graph("price-tracking", role="QUOTE_FEED_1")
    g["edges"] += [e(F, L, "tracks")]
    res = EN.run(g, [EN.Shock(L, "price", -0.1)])
    assert M not in res.markets() and res.loss(V) == 0


def test_the_constant_product_model_is_kept_for_comparison():
    g = pt_graph()
    g["nodes"][-2]["details"]["liquidity_usd"] = 200.0
    cp = {
        "node_rules": [
            {
                "id": "cp",
                "when": {"node.kind": "Asset"},
                "apply": "asset_price",
                "params": {"impact": "constant_product", "depth": "pendle_pool"},
            }
        ]
    }
    res = EN.run(g, [EN.Shock(C, "price", -0.05)], cp)
    assert res.states[C].detail["model"] == "constant_product" and res.states[C].out["price"] < 0.95


def test_marginal_curves_from_quote_ladders():
    curve, cap = marginal_curve([(1, 1.0), (3, 2.99), (6, 5.9), (10, 7.0)], 0.5)
    assert cap == 6 and curve == [[1, 1.0], [3, pytest.approx(0.995)], [6, pytest.approx(0.97)]]
    assert marginal_curve([(1, 1.0)], 0.5) == ([], None)
    assert EN.curve_factor(curve, 0.5) == 1.0 and EN.curve_factor(curve, 4) == pytest.approx(0.97)
    assert EN.curve_factor(curve, 100) == pytest.approx(0.97)  # past the last point: its factor


@pytest.mark.parametrize(
    "when,ok",
    [
        ({"rel": "reads"}, True),
        ({"edge.role__in": ["BASE_FEED_1", "BASE_FEED_2"]}, True),
        ({"edge.role__not_in": ["BASE_FEED_1"]}, False),
        ({"to.oracle_class__ne": "constant-price"}, True),
        ({"from.label__contains": "FEE"}, True),
        ({"to.missing__exists": False, "from.kind": "Oracle"}, True),
        ({"value__lt": 1.0}, True),
        ({"value__gte": 1.0}, False),
        ({"value__gt": 0.5, "value__lte": 0.9}, True),
    ],
)
def test_rule_criteria(when, ok):
    scope = {
        "rel": "reads",
        "edge": e(ORC, F, "reads", role="BASE_FEED_1"),
        "from": {"id": F, "kind": "Oracle", "label": "feed", "details": {}},
        "to": {"id": ORC, "kind": "Oracle", "label": "oracle", "details": {"oracle_class": "price-tracking"}},
        "value": 0.9,
    }
    assert EN.matches(when, scope) is ok


def test_shock_specs():
    assert EN.parse_shock("0xAB:reads-high:10%") == EN.Shock("0xab", "reads-high", pytest.approx(0.1))
    assert EN.parse_shock("0xab:price:30%").size == pytest.approx(-0.3)  # a price shock without a sign is a fall
    assert EN.parse_shock("0xab:frozen") == EN.Shock("0xab", "frozen")
    with pytest.raises(ValueError):
        EN.parse_shock("0xab:melts:5%")


def test_the_path_names_every_hop_and_rule():
    lines = EN.path(EN.run(graph(), [EN.Shock(F, "reads-high", 0.2)]), V)
    assert [r for r in ("supplier", "oracle-misreport", "base-feed") if not any(f"[{r}]" in ln for ln in lines)] == []


def test_the_trace_ties_every_step_to_an_edge_a_wave_and_the_final_state():
    gd = graph()
    res = EN.run(gd, [EN.Shock(F, "reads-high", 0.2)])
    t = json.loads(json.dumps(shock.trace(gd, res, 1, "2026-10-10T00:00:00Z")))  # JSON as written, no Python types
    edges = {x["id"]: x for x in t["graph"]["edges"]}
    assert [s["seq"] for s in t["steps"]] == list(range(1, len(t["steps"]) + 1))
    assert [s["wave"] for s in t["steps"]] == sorted(s["wave"] for s in t["steps"]) and t["steps"][0]["wave"] == 0
    for s in t["steps"]:
        x = edges[s["edge"]]
        ends = (x["target"], x["source"]) if s["direction"] == "dependents" else (x["source"], x["target"])
        assert ends == (s["source"], s["target"])
    last = {ev["node"]: ev for ev in t["evaluations_log"]}
    assert all(t["nodes"][n]["effects"] == ev["effects"] for n, ev in last.items())
    assert t["nodes"][F]["status"] == "shocked" and t["nodes"][V]["status"] == "loss"
    assert t["nodes"][V]["headline"].startswith("loses ")
    chain = [t["steps"][q - 1] for q in t["paths"][V]]
    assert chain[0]["source"] == F and {s["rule"] for s in chain} >= {"base-feed", "oracle-misreport", "supplier"}
    assert set(t["rules"]) == {s["rule"] for s in t["steps"]}


# --- the recorded RockawayX USDC Yield graph

ROCKAWAYX = (
    Path(__file__).resolve().parent.parent / "fixtures" / "replay" / "graph-0xe0181090c22579b6a217f1522cbf8c9f1f0c1965"
)
VAULT = "0xe0181090c22579b6a217f1522cbf8c9f1f0c1965"
PRIME, PRIME_FEED = "0x19ebb35279a16207ec4ba82799cc64715065f7f6", "0xf17c0edcaa28371e9c8012d7699bf40ecf0f58d1"
OJO = "0x77ee147391eac11c92817e771860ff4aad265d89"


@pytest.fixture(scope="module")
def rockawayx():
    g = GR.load([], [], True, "replay", ROCKAWAYX)[0]
    yield shock._graph_dict(g)
    clock.set_as_of(None)


def by_label(gd, res):
    labels = {n["id"]: n["label"].removeprefix("Blue ") for n in gd["nodes"]}
    return {labels[mid]: d for mid, d in res.markets().items()}


def test_prime_feed_stuck_while_prime_falls(rockawayx):
    res = EN.run(rockawayx, [EN.Shock(PRIME_FEED, "frozen"), EN.Shock(PRIME, "price", -0.3)])
    m = by_label(rockawayx, res)
    assert all(d["positions_liquidated"] == 0 for d in m.values())  # constant-price: nobody is liquidated
    assert m["PRIME/USDC"]["drained"] > 0 and m["PRIME/USDC"]["insolvent"] > 0
    assert m["PRIME/PYUSD"]["lender_loss"] > 20e6  # the $189M sibling on the same feed
    pool = next(n for n in rockawayx["nodes"] if n["label"] == "Blue PRIME/USDC")
    edge = next(x for x in rockawayx["edges"] if x["source"] == VAULT and x["target"] == pool["id"])
    share = edge["amount"] / pool["details"]["total_supply"]
    assert res.loss(VAULT) == pytest.approx(m["PRIME/USDC"]["lender_loss"] * share)


def node_id(gd, label):
    return next(n["id"] for n in gd["nodes"] if n["label"] == label)


def test_ojo_reading_low_liquidates_what_the_reusd_exit_can_absorb(rockawayx):
    res = EN.run(rockawayx, [EN.Shock(OJO, "reads-low", 0.1)])
    m = by_label(rockawayx, res)
    assert res.converged
    held, sib = m["PT-reUSD-10DEC2026/USDC"], m["PT-reUSD-10DEC2026/USDT"]
    assert held["positions_liquidated"] > 0 and sib["positions_liquidated"] > 0
    pt, reusd = res.states[node_id(rockawayx, "PT-reUSD-10DEC2026")], res.states[node_id(rockawayx, "reUSD")]
    assert pt.detail["impact"] > 0.98  # the Pendle pool is deep: under 2 % at this size (quotes of 2026-10-10)
    assert reusd.detail["absorbed_usd"] < reusd.detail["sold_usd"]  # selling the reUSD for dollars hits its capacity
    assert 0 < held["executed"] < 1
    assert 0 < res.loss(VAULT) < 18.5e6


def test_a_reusd_depeg_liquidates_nobody_in_the_pt_markets(rockawayx):
    """The PT oracle (Pendle PT_TO_ASSET) never sees reUSD's market price: the loss is insolvent debt and a drain."""
    res = EN.run(rockawayx, [EN.Shock(node_id(rockawayx, "reUSD"), "price", -0.3)])
    d = by_label(rockawayx, res)["PT-reUSD-10DEC2026/USDC"]
    assert d["positions_liquidated"] == 0 and d["oracle_factor"] == pytest.approx(1.0)
    assert d["market_factor"] == pytest.approx(0.7) and d["drained"] > 0 and d["insolvent"] > 0


def test_a_sibling_oracle_failure_reaches_our_pt_through_the_reusd_exit(rockawayx):
    """The reUSD/USD feed of the sibling reUSD markets reads low: their liquidators sell reUSD, which lowers reUSD and
    so our PT's worth, while our oracle stays put: no liquidation here, a thinner buffer."""
    res = EN.run(rockawayx, [EN.Shock(node_id(rockawayx, "reUSD/USD exchange rate"), "reads-low", 0.15)])
    m = by_label(rockawayx, res)
    assert m["reUSD/USDC"]["positions_liquidated"] > 0
    ours = m["PT-reUSD-10DEC2026/USDC"]
    assert ours["market_factor"] < 1.0 and ours["oracle_factor"] == pytest.approx(1.0)
    assert ours["positions_liquidated"] == 0


def test_sweep_ranks_the_pt_oracle_first_for_a_reading_too_high(rockawayx):
    rows = shock.run_sweep(rockawayx, "reads-high", 0.2, None, top=3, line=lambda s: None)
    assert {rows[0]["label"], rows[1]["label"]} == {
        "Oracle 0x217d…51f0",
        "Ojo PT Feed Pendle Chainlink-compatible Oracle",
    }
    assert rows[0]["vault_loss"] > 0


EXAMPLE = Path(__file__).resolve().parent.parent / "docs" / "shock-trace-example.json"


def test_the_trace_of_the_ojo_shock_leads_from_the_feed_to_the_vault(rockawayx):
    res = EN.run(rockawayx, [EN.Shock(OJO, "reads-low", 0.1)])
    t = shock.trace(rockawayx, res)
    chain = [t["steps"][q - 1] for q in t["paths"][VAULT]]
    assert chain[0]["source"] == OJO and chain[-1]["target"] == VAULT
    assert {"tracks", "liquidation-sale", "pt-onward", "supplier"} <= {s["rule"] for s in chain}
    replaced = [s for s in t["steps"] if s["replaces"]]
    assert replaced  # the loop revises what it sent: the vault's loss, the sales
    for s in replaced:
        old = t["steps"][s["replaces"] - 1]
        assert old["seq"] < s["seq"] and all(old[k] == s[k] for k in ("source", "target", "effect", "rule"))
    assert t["nodes"][VAULT]["status"] == "loss" and "USDC" in t["nodes"][VAULT]["headline"]


def test_the_committed_trace_example_is_current(rockawayx):
    """docs/shock-trace-example.json is what `shock --replay --shock "Ojo PT:reads-low:10%"` writes today."""
    ex = json.loads(EXAMPLE.read_text())
    res = EN.run(rockawayx, [EN.Shock(OJO, "reads-low", 0.1)])
    now = json.loads(json.dumps(shock.trace(rockawayx, res, ex["block"], ex["as_of"]), default=str))
    assert now == ex, "regenerate docs/shock-trace-example.json (docs/shock-trace.md says how)"
