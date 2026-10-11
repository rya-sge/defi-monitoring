"""Backtest (plan 2026-10-11-backtest): the 2026-08-25 PT-reUSD liquidations replayed offline from the recording made
through an archive RPC. If a change to the liquidation model moves the prediction away from what happened, this fails."""

import json

import pytest

from riskdep import backtest as BK
from riskdep import cli
from riskdep import market_risk as MR

INFO = MR.MarketInfo("m", 0.915, 6, "USDC", "PT/USDC (LLTV 91.5%)")


def test_compare_counts_liquidatable_positions_and_the_incentive():
    pos = {"a": (100 * 10**6, 90 * 10**12), "b": (100 * 10**6, 80 * 10**12)}  # debts 90 and 80 (shares 1e6 per unit)
    totals = (170 * 10**6, 170 * 10**12)
    price0 = 10**36
    events = [(2, "a", 90 * 10**6, 93 * 10**6, 0)]  # a liquidated in full, 93 collateral seized
    m = BK.compare(INFO, 10**6, pos, totals, price0, {2: int(price0 * 0.97)}, events)
    assert m.oracle_fall == pytest.approx(0.03) and m.predicted_positions == 1 and m.extra == [] and m.missed == []
    assert m.predicted_debt == pytest.approx(90, rel=1e-3) and m.realised_repaid == 90
    assert m.predicted_bonus == pytest.approx(90 * (INFO.lif - 1), rel=1e-3)
    assert m.realised_bonus == pytest.approx(93 * 0.97 - 90, rel=1e-3)


def test_the_reusd_episode_replays_offline(tmp_path, capsys):
    assert cli.main(["backtest", "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / "backtest-pt-reusd-2026-08-25.json").read_text())
    usdc, usdt = r["markets"]
    # the same 13 and 7 borrowers predicted as were liquidated, none missed, none extra
    assert (usdc["predicted_positions"], usdc["realised_positions"]) == (13, 13) and not usdc["missed"] + usdc["extra"]
    assert (usdt["predicted_positions"], usdt["realised_positions"]) == (7, 7) and not usdt["missed"] + usdt["extra"]
    # the debt and the incentive within 1 % where liquidators repaid in full (USDC)
    assert usdc["predicted_debt"] == pytest.approx(usdc["realised_repaid"], rel=0.01)
    assert usdc["predicted_bonus"] == pytest.approx(usdc["realised_bonus"], rel=0.01)
    assert usdc["realised_bad_debt"] == usdc["predicted_bad_debt"] == 0
    assert 940_000 < usdc["realised_bonus"] + usdt["realised_bonus"] < 950_000  # the cited $946k
    assert "13 / 13" in capsys.readouterr().out


def test_the_2025_10_10_crash_replays_offline(tmp_path):
    """A second mechanism: price-tracking oracles in a market-wide crash (memecoins, WBTC, wstETH). No liquidated
    borrower is missed in any of the six markets; every one predicted but not liquidated in the wave is accounted for
    (liquidated later that night, defended by its borrower, or left liquidatable with little debt, much of it dust)."""
    assert cli.main(["backtest", "--episode", "crash-2025-10-10", "--out", str(tmp_path)]) == 0
    ms = json.loads((tmp_path / "backtest-crash-2025-10-10.json").read_text())["markets"]
    assert len(ms) == 6 and all(not m["missed"] for m in ms)
    wbtc = next(m for m in ms if m["label"].startswith("WBTC/USDC"))
    assert wbtc["predicted_debt"] == pytest.approx(wbtc["realised_repaid"], rel=0.02)
    assert wbtc["predicted_bonus"] == pytest.approx(wbtc["realised_bonus"], rel=0.02)
    mog = next(m for m in ms if m["label"].startswith("Mog/"))
    assert len(mog["extra_later"]) == 36 and len(mog["extra_defended"]) == 3
    left = sum(m["left_debt"] for m in ms)
    assert left < 0.03 * sum(m["realised_repaid"] for m in ms)  # what no liquidator took: small next to what was repaid
