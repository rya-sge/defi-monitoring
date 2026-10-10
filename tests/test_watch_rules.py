"""Every rule of plan §3 fires on a synthetic event (US6)."""

import pytest
from eth_abi import encode

from riskdep.abi import SELECTORS, Event, describe_call, selector
from riskdep.rules import Ctx, assess_batch, startup_findings
from riskdep.vault import AdapterView, MarketParams, MarketState, VaultState, VaultView, cap_ids

E18 = 10**18
ADAPTER = "0x" + "aa" * 20
VAULT = "0x" + "bb" * 20
DEP = "0x" + "dd" * 20
M1 = "0x" + "11" * 32
M2 = "0x" + "22" * 32


def view():
    mp1 = MarketParams(M1, "0x" + "01" * 20, "0x" + "02" * 20, "0x" + "03" * 20, "0x" + "04" * 20, 0.86, "kBTC")
    mp2 = MarketParams(M2, "0x" + "01" * 20, "0x" + "05" * 20, "0x" + "06" * 20, "0x" + "04" * 20, 0.915, "USDe")
    return VaultView(
        VAULT, "0x" + "01" * 20, "RLUSD", 18, "Test vault", [AdapterView(ADAPTER, "market", {M1: mp1, M2: mp2})], None
    )


def state(
    block=100,
    ta=1000,
    m1=(600, 1000, 900),
    m2=(300, 1000, 500),
    price1=10**36,
    idle=100,
    dep=200,
    caps=None,
    liq=M2,
    stored=None,
    send=True,
    recv=True,
    penalty=10**14,
):
    """m = (vault supply assets, market total supply assets, total borrow), in whole tokens."""

    def ms(mid, m, price):
        va, tsa, tba = (x * E18 for x in m)
        return MarketState(mid, va * 10**6, tsa, tsa * 10**6, tba, va, price)

    return VaultState(
        block,
        ta * E18,
        ta * E18,
        idle * E18,
        {ADAPTER: 900 * E18},
        {M1: ms(M1, m1, price1), M2: ms(M2, m2, 10**36)},
        caps or {},
        0,
        0,
        DEP,
        dep * E18,
        (stored if stored is not None else ta) * E18,
        liq,
        {ADAPTER: penalty},
        send,
        recv,
    )


def ev(name, contract, **args):
    return Event(name, contract, ADAPTER if contract == "adapter" else VAULT, 101, "0x" + "ee" * 32, 0, args)


def run(events, before=None, after=None, dep=DEP):
    v = view()
    return assess_batch(events, Ctx(v, before or state(), after or state(block=101)), dep, 101)


def test_bad_debt_is_critical_and_shared_pro_rata():
    al = run(
        [
            ev(
                "Liquidate",
                "blue",
                id=M1,
                repaidAssets=0,
                repaidShares=0,
                seizedAssets=0,
                badDebtAssets=100 * E18,
                badDebtShares=0,
            )
        ]
    )
    assert al[0].level == "critical"
    # vault holds 600/1000 of the market, depositor 200/1000 of the vault: 100 * 0.6 * 0.2 = 12
    assert al[0].depositor_impact == pytest.approx(-12.0)


def test_liquidation_without_bad_debt_is_info():
    al = run(
        [
            ev(
                "Liquidate",
                "blue",
                id=M1,
                repaidAssets=5 * E18,
                repaidShares=0,
                seizedAssets=0,
                badDebtAssets=0,
                badDebtShares=0,
            )
        ]
    )
    assert al[0].level == "info"


def test_events_of_markets_not_held_are_ignored():
    assert (
        run(
            [
                ev(
                    "Liquidate",
                    "blue",
                    id="0x" + "99" * 32,
                    repaidAssets=0,
                    repaidShares=0,
                    seizedAssets=0,
                    badDebtAssets=E18,
                    badDebtShares=0,
                )
            ]
        )
        == []
    )


def test_share_price_fall_is_critical():
    al = run(
        [
            ev(
                "AccrueInterest",
                "vault",
                previousTotalAssets=1000 * E18,
                newTotalAssets=990 * E18,
                performanceFeeShares=0,
                managementFeeShares=0,
            )
        ]
    )
    assert al[0].level == "critical" and al[0].depositor_impact == pytest.approx(-2.0)


def test_normal_interest_is_silent():
    assert (
        run(
            [
                ev(
                    "AccrueInterest",
                    "vault",
                    previousTotalAssets=1000 * E18,
                    newTotalAssets=1001 * E18,
                    performanceFeeShares=0,
                    managementFeeShares=0,
                )
            ]
        )
        == []
    )


def test_submit_decodes_the_pending_change_and_its_date():
    data = "0x" + selector("setPerformanceFee(uint256)") + encode(["uint256"], [5 * 10**16]).hex()
    al = run(
        [
            ev(
                "Submit",
                "vault",
                selector="0x" + selector("setPerformanceFee(uint256)"),
                data=data,
                executableAt=1_800_000_000,
            )
        ]
    )
    assert al[0].level == "warn" and "setPerformanceFee" in al[0].title and "2027" in al[0].detail


def test_submit_on_a_cap_names_the_market():
    v = view()
    ids = cap_ids(ADAPTER, v.market(M2))
    from eth_abi import encode as enc

    params = (
        v.market(M2).loan_token,
        v.market(M2).collateral_token,
        v.market(M2).oracle,
        v.market(M2).irm,
        int(0.915 * E18),
    )
    id_data = enc(
        ["string", "address", "(address,address,address,address,uint256)"], ["this/marketParams", ADAPTER, params]
    )
    data = "0x" + selector("increaseAbsoluteCap(bytes,uint256)") + enc(["bytes", "uint256"], [id_data, 500 * E18]).hex()
    al = run([ev("Submit", "vault", selector="0x", data=data, executableAt=1_800_000_000)])
    assert "USDe" in al[0].title and ids["market"]


def test_accept_and_revoke():
    data = "0x" + selector("addAdapter(address)") + encode(["address"], ["0x" + "cc" * 20]).hex()
    assert run([ev("Accept", "vault", selector="0x", data=data)])[0].level == "warn"
    assert run([ev("Revoke", "vault", sender=VAULT, selector="0x", data=data)])[0].level == "info"


def test_adapter_submit_is_labelled_as_the_adapter():
    data = "0x" + selector("burnShares(bytes32)") + encode(["bytes32"], [bytes.fromhex(M1[2:])]).hex()
    al = run([ev("Submit", "adapter", selector="0x", data=data, executableAt=1_800_000_000)])
    assert al[0].event == "Adapter.Submit" and "burnShares" in al[0].title


def test_burn_shares_is_critical():
    al = run([ev("BurnShares", "adapter", marketId=M1, supplyShares=50 * E18 * 10**6)])
    assert al[0].level == "critical" and al[0].depositor_impact == pytest.approx(-10.0)


def test_allocation_crossing_the_concentration_threshold_warns():
    al = run(
        [ev("Allocate", "adapter", marketId=M2, newAllocation=400 * E18, mintedShares=0)],
        before=state(m2=(200, 1000, 500)),
        after=state(block=101, m2=(400, 1000, 500)),
    )
    assert al[0].level == "warn"
    al = run(
        [ev("Allocate", "adapter", marketId=M2, newAllocation=210 * E18, mintedShares=0)],
        before=state(m2=(200, 1000, 500)),
        after=state(block=101, m2=(210, 1000, 500)),
    )
    assert al[0].level == "info"


def test_allocation_to_an_unknown_market_warns():
    al = run([ev("Allocate", "adapter", marketId="0x" + "77" * 32, newAllocation=E18, mintedShares=0)])
    assert al[0].level == "warn" and al[0].title.startswith("New market")


def test_force_deallocate_and_liquidity_adapter_warn():
    assert (
        run(
            [
                ev(
                    "ForceDeallocate",
                    "vault",
                    sender=DEP,
                    adapter=ADAPTER,
                    assets=E18,
                    onBehalf=DEP,
                    ids=[],
                    penaltyAssets=0,
                )
            ]
        )[0].level
        == "warn"
    )
    assert (
        run(
            [
                ev(
                    "SetLiquidityAdapterAndData",
                    "vault",
                    sender=VAULT,
                    newLiquidityAdapter=ADAPTER,
                    newLiquidityData="0x",
                )
            ]
        )[0].level
        == "warn"
    )


def test_utilization_crossing_99_percent_warns_once():
    before, after = state(), state(block=101, m1=(600, 1000, 995))
    al = run([ev("Borrow", "blue", id=M1, caller=DEP, onBehalf=DEP, receiver=DEP, assets=E18, shares=0)], before, after)
    assert al[0].level == "warn" and "99.5%" in al[0].title
    al = run([ev("Borrow", "blue", id=M1, caller=DEP, onBehalf=DEP, receiver=DEP, assets=E18, shares=0)], after, after)
    assert al == []


def test_oracle_move_warns():
    al = run([], before=state(), after=state(block=101, price1=int(0.93 * 10**36)))
    assert al[0].event == "Oracle" and al[0].level == "warn"


def test_plain_withdrawal_counts_only_idle_and_the_liquidity_market():
    st = state()
    # idle 100 + liquidity market M2: min(300 supplied, 1000 - 500 free) = 400; M1 (min(600, 100)) only via forceDeallocate
    assert st.withdrawable == 400 * E18 and st.force_withdrawable == 100 * E18
    assert state(liq=None).withdrawable == 100 * E18


def test_losing_the_ability_to_exit_warns():
    # before: 200 needed, 400 payable; after: the liquidity market is fully borrowed and idle fell
    al = run([], before=state(), after=state(block=101, m2=(300, 1000, 1000), idle=50))
    assert any(a.event == "Liquidity" for a in al)


def test_pending_loss_is_critical_before_realisation():
    # stored total 1000, totalAssets() already 990: a loss sits in the adapters, not yet accrued
    al = run([], before=state(), after=state(block=101, ta=990, stored=1000))
    pend = [a for a in al if a.event == "PendingLoss"]
    assert pend and pend[0].level == "critical" and pend[0].depositor_impact < 0


def test_gate_closing_on_the_depositor_warns():
    al = run([], before=state(), after=state(block=101, send=False))
    assert any(a.event == "Gate" for a in al)


def test_zero_force_deallocate_penalty_is_flagged_at_start():
    al = startup_findings(view(), state(penalty=0))
    assert any("forceDeallocate is free" in a.title for a in al)


def test_own_and_large_flows_are_info_small_ones_silent():
    assert (
        run([ev("Withdraw", "vault", sender=DEP, receiver=DEP, onBehalf=DEP, assets=E18, shares=E18)])[0].title
        == "Your withdraw"
    )
    assert (
        run([ev("Deposit", "vault", sender=VAULT, onBehalf=VAULT, assets=50 * E18, shares=0)])[0].title
        == "Large deposit"
    )
    assert run([ev("Deposit", "vault", sender=VAULT, onBehalf=VAULT, assets=E18 // 10, shares=0)]) == []


def test_config_and_caps():
    assert (
        run([ev("IncreaseAbsoluteCap", "vault", id="0x" + "00" * 32, idData="0x", newAbsoluteCap=E18)])[0].level
        == "warn"
    )
    assert (
        run(
            [
                ev(
                    "DecreaseRelativeCap",
                    "vault",
                    sender=VAULT,
                    id="0x" + "00" * 32,
                    idData="0x",
                    newRelativeCap=E18 // 2,
                )
            ]
        )[0].level
        == "info"
    )
    assert run([ev("AddAdapter", "vault", account=ADAPTER)])[0].level == "warn"
    assert run([ev("SetPerformanceFee", "vault", newPerformanceFee=E18 // 10)])[0].level == "warn"
    assert run([ev("DecreaseTimelock", "vault", selector="0x00000000", newDuration=0)])[0].level == "warn"


def test_removed_logs_are_ignored():
    e = ev(
        "Liquidate", "blue", id=M1, repaidAssets=0, repaidShares=0, seizedAssets=0, badDebtAssets=E18, badDebtShares=0
    )
    e.removed = True
    assert run([e]) == []


def test_startup_flags_concentration_and_exit():
    v = view()
    al = startup_findings(v, state(dep=900))
    kinds = {a.event for a in al}
    assert "Exposure" in kinds and "Liquidity" in kinds


def test_every_timelocked_selector_decodes():
    for sel, (sig, _) in SELECTORS.items():
        types = sig[sig.index("(") + 1 : -1].split(",")
        vals = [
            {
                "address": "0x" + "ab" * 20,
                "uint256": 1,
                "bool": True,
                "bytes4": b"\x00" * 4,
                "bytes32": b"\x00" * 32,
                "bytes": b"\x01",
            }[t]
            for t in types
        ]
        assert describe_call("0x" + sel + encode(types, vals).hex())[0] == sig


# --- timelock lengths (plan 2026-10-10-lenders-and-timelocks, US11)


def view_with_timelocks(t_fee=0, t_cap=3 * 86400, abdicated_fee=False):
    v = view()
    v.timelocks = {
        (VAULT, "setPerformanceFee(uint256)"): (t_fee, abdicated_fee),
        (VAULT, "increaseAbsoluteCap(bytes,uint256)"): (t_cap, False),
        (VAULT, "removeAdapter(address)"): (0, False),
    }
    return v


def run_view(v, events):
    return assess_batch(events, Ctx(v, state(), state(block=101)), DEP, 101)


def test_zero_timelock_on_a_risk_increasing_function_warns_at_start():
    al = startup_findings(view_with_timelocks(), state())
    t = [a for a in al if a.event == "Timelock"]
    assert t and "setPerformanceFee" in t[0].detail and "removeAdapter" not in t[0].detail
    assert not [a for a in startup_findings(view_with_timelocks(abdicated_fee=True), state()) if a.event == "Timelock"]


def test_submit_with_no_notice_is_critical_with_notice_is_warn():
    fee = "0x" + selector("setPerformanceFee(uint256)") + encode(["uint256"], [10**17]).hex()
    al = run_view(view_with_timelocks(), [ev("Submit", "vault", selector="0x", data=fee, executableAt=1_800_000_000)])
    assert al[0].level == "critical" and "no notice" in al[0].title
    al = run_view(
        view_with_timelocks(t_fee=86400), [ev("Submit", "vault", selector="0x", data=fee, executableAt=1_800_000_000)]
    )
    assert al[0].level == "warn" and "timelock 1 days" in al[0].detail
