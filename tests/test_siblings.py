"""Sibling-market matching, pure (plan 2026-10-10-sibling-markets, US18)."""

from riskdep.siblings import (
    LENDS_LINKED,
    SAME_COLLATERAL,
    SAME_UNDERLYING,
    SHARED_INPUT,
    Market,
    family,
    match,
    relations,
)

USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
PT, RE, PT2, WRAP = ("0x" + c * 40 for c in "1234")  # PT-reUSD, reUSD, another PT-reUSD maturity, a reUSD wrapper
FEED, OTHER = "0x" + "f" * 40, "0x" + "e" * 40
UND = {PT: RE, PT2: RE, WRAP: RE}

SEED = Market("seed", PT, USDC, "0xorc", frozenset({FEED}), 50e6, "PT-reUSD/USDC")


def cand(mid, coll, loan=USDC, oracle="0xo2", inputs=(), borrow=1e6, tvl=None):
    return Market(mid, coll, loan, oracle, frozenset(inputs), borrow, mid, tvl if tvl is not None else borrow * 1.2)


def test_family_follows_the_underlying_both_ways():
    assert family(PT, UND) == {PT, RE, PT2, WRAP}
    assert family(RE, UND) == {RE, PT, PT2, WRAP}


def test_family_stops_at_a_terminal_underlying():
    und = {"0xsyrup": USDC, "0xsteak": USDC}
    assert family("0xsyrup", und) == {"0xsyrup"}


def test_each_relation():
    assert relations(SEED, cand("a", PT, USDT), UND) == [SAME_COLLATERAL]
    assert relations(SEED, cand("b", RE), UND) == [SAME_UNDERLYING]
    assert relations(SEED, cand("c", PT2), UND) == [SAME_UNDERLYING]
    assert relations(SEED, cand("d", OTHER, inputs=[FEED]), UND) == [SHARED_INPUT]
    assert relations(SEED, cand("e", OTHER, oracle="0xorc"), UND) == [SHARED_INPUT]
    assert relations(SEED, cand("f", OTHER, loan=RE), UND) == [LENDS_LINKED]
    assert relations(SEED, cand("g", OTHER), UND) == []


def test_several_relations_are_kept():
    assert relations(SEED, cand("a", PT, USDT, inputs=[FEED]), UND) == [SAME_COLLATERAL, SHARED_INPUT]


def test_stablecoins_never_link_by_token():
    usdc_seed = Market("s2", USDC, USDT, "0xo3")
    assert relations(usdc_seed, cand("a", USDC, USDT), {}) == []
    assert relations(usdc_seed, cand("b", OTHER, loan=USDC), {}) == []


def test_match_floor_cap_held_and_merge():
    seed2 = Market("seed2", RE, USDC, "0xo4", frozenset(), 5e6)
    cands = [
        cand("seed2", RE, borrow=5e6),  # held: never a sibling
        cand("small", PT, USDT, borrow=500_000, tvl=800_000),  # TVL below the floor
        cand("big", PT, USDT, borrow=9e6),
        cand("mid", RE, USDT, borrow=2e6),
        cand("low", PT2, borrow=1e6),
    ]
    sibs = match([SEED, seed2], cands, UND, min_tvl_usd=1_000_000, max_per_seed=2)
    # each seed keeps its 2 largest (big, mid): low is cut by the cap, small by the floor, seed2 is held
    assert [s.id for s in sibs] == ["big", "mid"]
    assert sibs[0].links == [("seed", SAME_COLLATERAL), ("seed2", SAME_UNDERLYING)]
    assert sibs[1].links == [("seed", SAME_UNDERLYING), ("seed2", SAME_COLLATERAL)]
    assert [s.id for s in match([SEED, seed2], cands, UND, min_tvl_usd=1_000_000, max_per_seed=3)][-1] == "low"
    assert "small" in {s.id for s in match([SEED], cands, UND, min_tvl_usd=500_000, max_per_seed=10)}
