"""Borrower maths, rules and discovery (plan 2026-10-10-morpho-user-watcher, US7–US9)."""

import math

import pytest

from riskdep import positions
from riskdep.abi import Event
from riskdep.borrower import BorrowMarket, BorrowState, Supplier
from riskdep.borrower_rules import assess_events, assess_states, lenders_startup, startup, zone

USER = "0x" + "dd" * 20
OTHER = "0x" + "ee" * 20
M = "0x" + "11" * 32
LEVELS = (1.10, 1.05, 1.02)
E18 = 10**18


def market():
    return BorrowMarket(
        M, "0x" + "01" * 20, "0x" + "02" * 20, "0x" + "03" * 20, "0x" + "04" * 20, int(0.9 * E18), "USDC", "WETH", 6, 18
    )


def state(hf=1.2, price=10**36, rate=10**9, util=(1000, 800)):
    """Collateral 100 tokens at price 1 (in loan units), LLTV 90 %: debt sized to give the HF."""
    collateral = 100 * E18
    value = collateral * price // 10**36 if price else collateral
    debt = int(value * 0.9 / hf)
    return BorrowState(M, collateral, debt, debt, price, util[0], util[1], rate)


def ev(name, **args):
    return Event(name, "blue", "0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb", 10, "0x" + "ab" * 32, 0, args)


def run(before, after, start_apy=None):
    return assess_states(
        {M: before} if before else {}, {M: after}, {M: market()}, LEVELS, start_apy or {M: after.apy}, 10
    )


def test_hf_liquidation_distance_and_apy():
    st = state(hf=1.25)
    assert st.hf(0.9) == pytest.approx(1.25, rel=1e-9)
    assert st.liquidation_drop(0.9) == pytest.approx(0.2)
    assert st.apy == pytest.approx(math.expm1(10**9 * 365 * 86400 / E18))
    assert BorrowState(M, 1, 0, 0, 10**36, 1, 0, 0).hf(0.9) == math.inf


def test_zones():
    assert [zone(h, LEVELS) for h in (1.2, 1.08, 1.03, 1.01, None)] == [0, 1, 2, 3, 0]


@pytest.mark.parametrize("hf,level", [(1.08, "info"), (1.04, "warn"), (1.015, "critical")])
def test_crossing_a_level_alerts_at_its_severity(hf, level):
    al = run(state(1.2), state(hf))
    assert len(al) == 1 and al[0].level == level and al[0].event == "HealthFactor"


def test_staying_in_a_zone_is_silent_and_recovery_alerts_once():
    assert run(state(1.04), state(1.03)) == []
    al = run(state(1.04), state(1.15))
    assert al[0].level == "info" and "back above" in al[0].title


def test_liquidatable():
    al = run(state(1.03), state(0.98))
    assert al[0].level == "critical" and "Liquidatable" in al[0].title


def test_startup_reports_a_position_already_below_a_level():
    al = startup({M: state(1.04)}, {M: market()}, LEVELS, 10)
    assert al[0].level == "warn" and "HF 1.0400" in al[0].detail


def test_oracle_unreadable_warns():
    al = run(state(1.2), state(1.2, price=None))
    assert al[0].event == "Oracle" and al[0].level == "warn"


def test_oracle_move_warns():
    al = run(state(1.2), state(1.2, price=int(0.93 * 10**36)))
    assert any(a.event == "Oracle" and "-7.0%" in a.title for a in al)


def test_rate_jump_warns_once():
    al = run(state(rate=10**9), state(rate=2 * 10**9), start_apy={M: state(rate=10**9).apy})
    assert any(a.event == "Rate" for a in al)
    al = run(state(rate=2 * 10**9), state(rate=2 * 10**9), start_apy={M: state(rate=10**9).apy})
    assert not any(a.event == "Rate" for a in al)


def test_utilisation_crossing_99_percent_warns():
    al = run(state(util=(1000, 900)), state(util=(1000, 995)))
    assert any(a.event == "Utilisation" for a in al)


def test_liquidation_of_the_user_is_critical():
    al = assess_events(
        [
            ev(
                "Liquidate",
                id=M,
                caller=OTHER,
                borrower=USER,
                repaidAssets=5 * 10**6,
                repaidShares=0,
                seizedAssets=E18,
                badDebtAssets=0,
                badDebtShares=0,
            )
        ],
        USER,
        {M: market()},
    )
    assert al[0].level == "critical" and "liquidated" in al[0].title


def test_others_liquidated_are_ignored():
    assert (
        assess_events(
            [
                ev(
                    "Liquidate",
                    id=M,
                    caller=OTHER,
                    borrower=OTHER,
                    repaidAssets=1,
                    repaidShares=0,
                    seizedAssets=1,
                    badDebtAssets=0,
                    badDebtShares=0,
                )
            ],
            USER,
            {M: market()},
        )
        == []
    )


def test_action_on_behalf_by_another_address_warns_own_action_is_info():
    al = assess_events(
        [ev("WithdrawCollateral", id=M, caller=OTHER, onBehalf=USER, receiver=OTHER, assets=E18)], USER, {M: market()}
    )
    assert al[0].level == "warn" and "on your behalf" in al[0].title
    al = assess_events(
        [ev("Borrow", id=M, caller=USER, onBehalf=USER, receiver=USER, assets=10**6, shares=0)], USER, {M: market()}
    )
    assert al[0].level == "info"


def test_new_authorisation_warns():
    al = assess_events(
        [ev("SetAuthorization", caller=USER, authorizer=USER, authorized=OTHER, newIsAuthorized=True)],
        USER,
        {M: market()},
    )
    assert al[0].level == "warn" and OTHER in al[0].title


class FakeF:
    def __init__(self, data):
        self.data = data

    def post_json(self, url, body):
        return {"data": self.data}


def test_discovery_keeps_debt_and_non_empty_vaults():
    data = {
        "userByAddress": {
            "marketPositions": [
                {"market": {"marketId": M}, "state": {"borrowAssets": "5", "collateral": "9"}},
                {"market": {"marketId": "0x" + "22" * 32}, "state": {"borrowAssets": "0", "collateral": "9"}},
                {"market": {"marketId": "0x" + "33" * 32}, "state": {"borrowAssets": None, "collateral": "0"}},
            ],
            "vaultV2Positions": [
                {"vault": {"address": "0xAA"}, "shares": "10"},
                {"vault": {"address": "0xBB"}, "shares": 0},
            ],
        }
    }
    up = positions.discover_user(FakeF(data), USER)
    assert up.borrows == [M] and up.vaults == ["0xaa"] and up.collateral_only == 1


# --- main lenders (plan 2026-10-10-lenders-and-timelocks, US10)

LENDER = "0x" + "aa" * 20
VAULT = "0x" + "bb" * 20


def test_one_dominant_lender_warns_at_start():
    sp = Supplier(LENDER, VAULT, "Vault X", "Vault V2", 900 * 10**6, 0.9)
    al = lenders_startup({M: [sp]}, {M: market()}, 10)
    assert al[0].level == "warn" and "90%" in al[0].title and LENDER in al[0].detail
    small = Supplier(LENDER, LENDER, "Lender", "lender", 100, 0.3)
    assert lenders_startup({M: [small]}, {M: market()}, 10) == []


def test_main_lender_withdrawal_warns_small_one_is_silent():
    sp = Supplier(LENDER, VAULT, "Vault X", "Vault V2", 900 * E18, 0.9)
    before = {M: state(util=(1000 * E18, 800 * E18))}
    big = ev("Withdraw", id=M, caller=LENDER, onBehalf=LENDER, receiver=LENDER, assets=100 * E18, shares=0)
    al = assess_events([big], USER, {M: market()}, {M: {LENDER: sp}}, before)
    assert al[0].event == "Lender" and "10.0%" in al[0].detail
    sp2 = Supplier(LENDER, VAULT, "Vault X", "Vault V2", 900 * E18, 0.9)
    tiny = ev("Withdraw", id=M, caller=LENDER, onBehalf=LENDER, receiver=LENDER, assets=10 * E18, shares=0)
    assert assess_events([tiny], USER, {M: market()}, {M: {LENDER: sp2}}, before) == []
    other = ev("Withdraw", id=M, caller=OTHER, onBehalf=OTHER, receiver=OTHER, assets=500 * E18, shares=0)
    assert assess_events([other], USER, {M: market()}, {M: {LENDER: sp2}}, before) == []


def test_repay_or_collateral_added_by_another_address_is_info():
    al = assess_events([ev("Repay", id=M, caller=OTHER, onBehalf=USER, assets=10**6, shares=0)], USER, {M: market()})
    assert al[0].level == "info"
    al = assess_events([ev("SupplyCollateral", id=M, caller=OTHER, onBehalf=USER, assets=E18)], USER, {M: market()})
    assert al[0].level == "info"
