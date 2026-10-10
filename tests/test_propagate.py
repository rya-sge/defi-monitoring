import pytest

from riskdep.propagate import loss


def test_no_shock_no_loss():
    r = loss(100.0, 80.0, 0.9, 1.03, "market-tracking", {})
    assert r.loss_usd == 0 and not r.liquidated


def test_holder_loses_the_markdown():
    r = loss(100.0, 0.0, None, None, "none", {"issuer_hack": 0.2})
    assert r.loss_usd == pytest.approx(20.0)


def test_depeg_recovery_for_unlevered_holder():
    r = loss(100.0, 0.0, None, None, "none", {"issuer_depeg": 0.10}, recovery=0.75)
    assert r.loss_usd == pytest.approx(2.5)


def test_market_tracking_oracle_turns_a_depeg_into_liquidation():
    # equity 10, liquidation at 1 - 90 / (100 * 0.915) = 1.6% oracle drop
    fixed = loss(100.0, 90.0, 0.915, 1.026, "fundamental", {"issuer_depeg": 0.04}, recovery=0.75)
    tracking = loss(100.0, 90.0, 0.915, 1.026, "market-tracking", {"issuer_depeg": 0.04}, recovery=0.75)
    assert not fixed.liquidated and fixed.loss_usd == pytest.approx(1.0)
    assert tracking.liquidated and tracking.loss_usd > fixed.loss_usd


def test_oracle_misprint_liquidates_without_real_loss_of_value():
    r = loss(100.0, 90.0, 0.915, 1.026, "market-tracking", {"oracle": 0.05})
    assert r.liquidated and r.true_value_usd == 100.0
    seized = 90.0 * 1.026 / 95.0
    assert r.loss_usd == pytest.approx(10.0 - 100.0 * (1 - seized))


def test_limited_liability_caps_loss_at_equity():
    r = loss(100.0, 90.0, 0.915, 1.026, "fundamental", {"lending": 0.5})
    assert not r.liquidated and r.loss_usd == pytest.approx(10.0)
