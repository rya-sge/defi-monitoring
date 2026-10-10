"""Oracle classes, one test per rule of D83 (plan 2026-10-10-sibling-markets, US19)."""

import pytest

from riskdep.oracle_class import (
    CONSTANT_PRICE,
    NOT_CLASSIFIED,
    PRICE_TRACKING,
    Probe,
    classify_input,
    classify_oracle,
)

A = "0x" + "aa" * 20


def feed(**kw) -> Probe:
    return Probe(A, **kw)


def test_base_vault_is_an_exchange_rate():
    assert classify_input(feed(vault=True))[0] == CONSTANT_PRICE


def test_twap_getter_tracks_and_linear_discount_does_not():
    assert classify_input(feed(getters={"twapDuration()": 900}))[0] == PRICE_TRACKING
    assert classify_input(feed(getters={"twapDuration()": 0}))[0] == NOT_CLASSIFIED
    assert classify_input(feed(getters={"baseDiscountPerYear()": 0}))[0] == CONSTANT_PRICE


def test_composite_tracks_when_one_child_tracks():
    """Ojo PT feed: min(Pendle TWAP, timestamp adapter → linear discount)."""
    twap = feed(getters={"twapDuration()": 900})
    linear = feed(children=[feed(getters={"baseDiscountPerYear()": 235 * 10**15})])
    cls, basis = classify_input(feed(description="Ojo PT Feed", children=[twap, linear]))
    assert cls == PRICE_TRACKING and "twapDuration" in basis
    assert classify_input(feed(children=[linear, feed(vault=True)]))[0] == CONSTANT_PRICE
    assert classify_input(feed(children=[linear, feed()]))[0] == NOT_CLASSIFIED


@pytest.mark.parametrize(
    "history,cls",
    [
        ([100, 101, 99, 102, 100, 101, 98], PRICE_TRACKING),  # moves both ways: a market price
        ([100, 101, 102, 103, 104, 105, 106], CONSTANT_PRICE),  # only rises: an accrual rate
        ([100] * 7, CONSTANT_PRICE),  # never changes
        ([100, 101, 102, 103, 104, 105, 106, 107, 108, 107], CONSTANT_PRICE),  # 1 fall in 9 changes, below 20 %
    ],
)
def test_round_history(history, cls):
    assert classify_input(feed(history=history, answer=history[-1], decimals=8))[0] == cls


def test_short_history_falls_through_to_the_next_rules():
    assert classify_input(feed(history=[1, 2, 1], answer=1, decimals=8))[0] == NOT_CLASSIFIED


def test_exactly_one_without_history_is_pegged():
    assert classify_input(feed(answer=10**8, decimals=8, history=[10**8]))[0] == CONSTANT_PRICE
    assert classify_input(feed(answer=10**8 + 1, decimals=8, history=[10**8 + 1]))[0] == NOT_CLASSIFIED


def test_patterns_match_description_or_contract_name():
    assert classify_input(feed(description="RedStone Price Feed for strUSD_FUNDAMENTAL", answer=103))[0] == (
        CONSTANT_PRICE
    )
    assert classify_input(feed(name="PendleChainlinkOracle", answer=98))[0] == PRICE_TRACKING
    assert classify_input(feed(description="Some feed", answer=98))[0] == NOT_CLASSIFIED


def test_history_decides_before_a_misleading_name():
    """An 'exchange rate' feed that moves both ways is classified by its behaviour."""
    p = feed(description="X Exchange Rate", history=[100, 99, 101, 98, 102, 97, 103], answer=103, decimals=8)
    assert classify_input(p)[0] == PRICE_TRACKING


def test_oracle_class_from_base_inputs():
    tracking, rate = feed(history=[1, 2, 1, 2, 1, 2, 1], answer=1, decimals=8), feed(vault=True)
    assert classify_oracle([rate, tracking], standard=True)[0] == PRICE_TRACKING
    assert classify_oracle([rate], standard=True)[0] == CONSTANT_PRICE
    assert classify_oracle([rate, feed()], standard=True)[0] == NOT_CLASSIFIED
    assert classify_oracle([], standard=True)[0] == CONSTANT_PRICE  # only the scale factor
    assert classify_oracle([feed()], standard=False)[0] == NOT_CLASSIFIED  # a custom oracle, read as one input
