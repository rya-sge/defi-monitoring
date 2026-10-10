"""Run / queue model (plan 2026-10-10-exit-queue): formulas on Team 2's example, alert levels, the recorded vault."""

import json

import pytest

from riskdep import exit_queue as EQ
from riskdep import sources as S
from riskdep.cli import DEMO_VAULT, REPLAY_DIR, main
from riskdep.market_risk import CurvePoint, MarketRisk

M = 10**6  # amounts in millions, unit 1


def team2() -> tuple[EQ.Liquidity, EQ.LossCase]:
    """Team 2's example: vault 100M, 15M in a market with a 30 % depeg (4.5M loss), 20M liquid elsewhere."""
    return EQ.Liquidity(total=100 * M, position=1 * M, plain=20 * M, forced=0, penalty=0.0), EQ.LossCase(
        "depeg", 4_500_000, 15 * M
    )


def test_team2_example_loss_by_queue_position():
    liq, case = team2()
    assert EQ.pro_rata_loss(liq, case) / liq.position == pytest.approx(0.045)
    assert EQ.depositor_loss(liq, EQ.exit_at(liq, 0), case) == 0  # first out
    behind = EQ.depositor_loss(liq, EQ.exit_at(liq, 20 * M), case)  # after the first 20M left
    assert behind / liq.position == pytest.approx(4.5 / 80)
    assert EQ.last_out_loss(liq, case) / liq.position == pytest.approx(0.30)


def test_par_recovery_splits_plain_and_forced_and_charges_the_penalty():
    liq = EQ.Liquidity(total=100 * M, position=30 * M, plain=10 * M, forced=20 * M, penalty=0.01)
    ex = EQ.exit_at(liq, 5 * M)  # 5M of plain left, then forced
    assert (ex.par, ex.forced, ex.stuck) == (25 * M, 20 * M, 5 * M)
    assert ex.penalty == 200_000
    late = EQ.exit_at(liq, 40 * M)
    assert (late.par, late.stuck, late.penalty) == (0, 30 * M, 0)


def test_loss_rate_is_capped_and_zero_without_loss():
    liq = EQ.Liquidity(total=100 * M, position=10 * M, plain=95 * M, forced=0, penalty=0.0)
    assert EQ.loss_rate(liq, 50 * M) == 1.0
    assert EQ.loss_rate(liq, 0) == 0.0


def test_queue_points_use_contract_holders_except_the_depositor():
    liq = EQ.Liquidity(total=100 * M, position=10 * M, plain=20 * M, forced=0, penalty=0.0)
    hs = [EQ.Holder("0xme", 10 * M, True), EQ.Holder("0xfund", 30 * M, True), EQ.Holder("0xeoa", 60 * M, False)]
    pts = dict(EQ.queue_points(liq, hs, "0xme"))
    assert pts["first out"] == 0 and pts["behind contracts"] == 30 * M and pts["last of the run"] == 90 * M
    assert "behind contracts" not in dict(EQ.queue_points(liq, [], "0xme"))
    assert EQ.alert_point(liq, [], "0xme")[0].endswith("of others")


def test_a_7702_delegated_wallet_is_not_a_contract():
    assert EQ._is_contract("0x6080604052") is True
    assert EQ._is_contract("0xef0100" + "ab" * 20) is False
    assert EQ._is_contract("0x") is False and EQ._is_contract(None) is None


def test_loss_cases_take_the_vault_share_of_each_market():
    r = MarketRisk("m1", 3, 100, 0, 10, [CurvePoint(d, 0, 0, 40 if d >= 0.1 else 0) for d in (0.02, 0.05, 0.1, 0.2)])
    cases = EQ.loss_cases({"m1": r}, {"m1": 0.5}, {"m1": 60})
    assert [(c.loss, c.exposure) for c in cases] == [(5, 60), (0, 0), (0, 0), (20, 60), (20, 60)]


def test_alert_warns_then_turns_critical_once_on_crossing():
    W = EQ.W["exit_queue_stuck_warn"]
    args = ("behind contracts", "Vault", 1, "USDC", 1)
    assert EQ.assess(None, (W - 0.01, 0), *args) == []
    warn = EQ.assess(None, (W, 0), *args)
    assert [a.level for a in warn] == ["warn"] and warn[0].event == "ExitQueue"
    assert EQ.assess((W, 0), (W + 0.1, 0), *args) == []  # same level: no repeat
    crit = EQ.assess((W, 0), (W, 5), *args)
    assert [a.level for a in crit] == ["critical"] and "not written off" in crit[0].detail


def test_recorded_vault_holders_and_startup(tmp_path, capsys):
    f = S.Fetcher("offline", REPLAY_DIR / DEMO_VAULT)
    hs, count = EQ.holders(f, DEMO_VAULT, 10**18, 10**18)
    assert len(hs) == 100 and count >= 100 and any(h.fast for h in hs) and all(h.fast is not None for h in hs)
    assert main(["watch", "--replay", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "exit queue (100 of" in out and "behind contracts" in out
    kinds = [json.loads(x)["event"] for x in (tmp_path / f"watch-{DEMO_VAULT}.jsonl").read_text().splitlines()]
    assert "ExitQueue" in kinds
