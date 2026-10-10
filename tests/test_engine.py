"""The propagation engine: each transmission and node model on a small graph with numbers worked by hand, the rule
criteria, and scenarios on the recorded RockawayX USDC Yield graph (plan 2026-10-10-propagation-engine, US20, US21)."""

from pathlib import Path

import pytest

from riskdep import clock, shock
from riskdep import engine as EN
from riskdep import graph as GR
from riskdep.discover import morpho_lif

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
        ("not classified", [EN.Shock(C, "price", -0.3)], 10 + 100 * (1 - 0.7 / 0.86)),  # D93
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


def squeeze_graph(liquidity):
    g = graph("price-tracking", positions=[(100.0, 82.0)] * 10, free=0.0)  # HF 1.049: a 5 % fall liquidates all
    g["nodes"] += [
        {
            "id": "pendle:0xc",
            "kind": "Pool",
            "label": "Pendle pool",
            "details": {"liquidity_usd": liquidity, "implied_apy": 0.1, "days_to_maturity": 365},
        }
    ]
    g["edges"] += [e(C, "pendle:0xc", "trades in / redeems through")]
    return g


def test_the_squeeze_deepens_the_fall_down_to_the_pt_floor():
    floor = 1.1 / 1.5  # a buyer holding a year to maturity at 50 % APY instead of 10 %
    res = EN.run(squeeze_graph(200.0), [EN.Shock(C, "price", -0.05)])
    assert res.converged
    assert res.states[C].out["price"] == pytest.approx(0.95 * floor)
    assert res.states[C].detail["sold_usd"] == pytest.approx(1000.0)  # the ten positions, at today's price
    no_depth = EN.run(squeeze_graph(None), [EN.Shock(C, "price", -0.05)])
    assert no_depth.states[C].out["price"] == pytest.approx(0.95)


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


def test_ojo_feed_reading_low_liquidates_both_pt_markets_and_squeezes(rockawayx):
    res = EN.run(rockawayx, [EN.Shock(OJO, "reads-low", 0.1)])
    m = by_label(rockawayx, res)
    assert res.converged
    assert (
        m["PT-reUSD-10DEC2026/USDC"]["positions_liquidated"] > 0
        and m["PT-reUSD-10DEC2026/USDT"]["positions_liquidated"] > 0
    )
    pt = next(n["id"] for n in rockawayx["nodes"] if n["label"] == "PT-reUSD-10DEC2026")
    assert res.states[pt].detail["floor"] == pytest.approx(res.states[pt].detail["impact"])  # the floor binds
    assert 0 < res.loss(VAULT) < 18.5e6


def test_sweep_ranks_the_pt_oracle_first_for_a_reading_too_high(rockawayx):
    rows = shock.run_sweep(rockawayx, "reads-high", 0.2, None, top=3, line=lambda s: None)
    assert {rows[0]["label"], rows[1]["label"]} == {
        "Oracle 0x217d…51f0",
        "Ojo PT Feed Pendle Chainlink-compatible Oracle",
    }
    assert rows[0]["vault_loss"] > 0
