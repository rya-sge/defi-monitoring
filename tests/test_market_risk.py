"""Unrealised bad debt and liquidation curves (plan 2026-10-10-market-borrowers, US12, US13)."""

import pytest

from riskdep.market_risk import MarketInfo, Tracker, assess_curves, assess_vault_bad_debt, value

E6 = 10 ** 6
M = "0x" + "11" * 32
INFO = MarketInfo(M, 0.9, 6, "USDC", "X/USDC (LLTV 90.0%)")
PRICE = 10 ** 36 // 10 ** 12          # 1 collateral unit (18 decimals) = 1 USDC (6 decimals)
TOTALS = (1_000 * E6, 1_000 * E6 * 10 ** 6)   # borrow assets, borrow shares: 1 share-unit = 1e-6 asset


def pos(collateral_usdc: float, debt_usdc: float) -> tuple[int, int]:
    return int(collateral_usdc * 10 ** 18), int(debt_usdc * E6 * 10 ** 6)


def test_value_counts_liquidatable_and_unrealised_bad_debt():
    positions = {
        "a": pos(100, 80),     # HF 1.125: safe now, liquidatable after a 20 % fall
        "b": pos(100, 95),     # HF 0.947: liquidatable now, covered (100 / LIF ≥ 95)
        "c": pos(90, 100),     # underwater: bad debt 100 − 90 / LIF
    }
    r = value(positions, TOTALS, PRICE, INFO)
    lif = INFO.lif
    assert r.borrowers == 3
    assert r.liquidatable_now == pytest.approx(195 * E6, rel=1e-6)
    assert r.unrealised_bad_debt == pytest.approx((100 - 90 / lif) * E6 + max(0, 95 - 100 / lif) * E6, rel=1e-6)
    p20 = r.point(0.20)
    assert p20.positions == 3 and p20.liquidatable_debt == pytest.approx(275 * E6, rel=1e-6)
    assert r.point(0.02).positions == 2


def test_unreadable_oracle_gives_no_numbers():
    r = value({"a": pos(100, 80)}, TOTALS, None, INFO)
    assert r.borrowers == 1 and r.curve == [] and r.unrealised_bad_debt == 0


def test_tracker_excludes_the_watched_borrower():
    t = Tracker({M: INFO}, exclude={"0xME"})
    t.positions = {M: {"0xme": pos(50, 49), "0xother": pos(100, 50)}}
    t.totals = {M: TOTALS}
    r = t.compute({M: PRICE})[M]
    assert r.borrowers == 1 and r.liquidatable_now == 0


def risk(bad_debt_usdc=0.0, liq5_share=0.0):
    r = value({}, TOTALS, PRICE, INFO)
    r.unrealised_bad_debt = int(bad_debt_usdc * E6)
    for p in r.curve:
        if abs(p.drop - 0.05) < 1e-9:
            p.liquidatable_debt, p.positions = int(liq5_share * TOTALS[0]), 3
    return r


def test_vault_bad_debt_warn_and_critical_on_crossing():
    vault_total = 1_000_000 * E6
    shares = {M: 0.5}
    # vault exposure 0.5 × 400 = 200 USDC = 0.02 % of the vault → warn
    al = assess_vault_bad_debt({M: risk()}, {M: risk(400)}, {M: INFO}, shares, vault_total, 0.1, 10)
    assert al[0].level == "warn" and al[0].depositor_impact == pytest.approx(-20.0)
    # already warned, still warn level → silent; then 0.5 × 4000 = 2000 = 0.2 % → critical
    assert assess_vault_bad_debt({M: risk(400)}, {M: risk(500)}, {M: INFO}, shares, vault_total, 0.1, 10) == []
    al = assess_vault_bad_debt({M: risk(400)}, {M: risk(4000)}, {M: INFO}, shares, vault_total, 0.1, 10)
    assert al[0].level == "critical"


def test_steep_curve_warns_once_and_respects_eligibility():
    al = assess_curves({M: risk(liq5_share=0.1)}, {M: risk(liq5_share=0.3)}, {M: INFO}, 10)
    assert al[0].event == "LiquidationCurve" and "30%" in al[0].title
    assert assess_curves({M: risk(liq5_share=0.3)}, {M: risk(liq5_share=0.4)}, {M: INFO}, 10) == []
    assert assess_curves({}, {M: risk(liq5_share=0.3)}, {M: INFO}, 10, eligible=set()) == []
