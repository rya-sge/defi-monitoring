"""The Pendle pool rebuilt from its on-chain state (plan 2026-10-11-pendle-pool, D207–D209)."""

import json

import pytest

from riskdep import cli, pipeline
from riskdep import pendle_amm as PA
from riskdep import sources as S

DEMO_POOL = "0x47ad2cd1dd15739a7a035b9d3b7828d916fef77e"


def test_the_pool_math_matches_pendles_quotes():
    """The demo's PT-sUSDE pool read at a block, against Pendle's quotes taken at the same moment (pool only)."""
    rdir = pipeline.REPLAY_DIR / f"pendle-pool-{DEMO_POOL}"
    meta = json.loads((rdir / "meta.json").read_text())
    f = S.Fetcher("offline", rdir)
    pool = PA.read(f, DEMO_POOL, meta["block"])
    assert pool.implied_apy == pytest.approx(0.0501, abs=1e-4) and pool.decimals == 18
    for q, tol in ((1000, 1e-8), (10000, 1e-4)):  # beyond the smallest size the router also fills limit orders
        url = (
            f"{S.PENDLE}/v2/sdk/1/markets/{DEMO_POOL}/swap?receiver=0x1111111111111111111111111111111111111111"
            f"&slippage=0.01&enableAggregator=false&tokenIn={meta['pt']}&tokenOut={meta['sy']}&amountIn={q * 10**18}"
        )
        api = int(f.get_json(url)["data"]["amountOut"]) / 1e18
        assert PA.sell_pt(pool, q)[0] / pool.index == pytest.approx(api, rel=tol)


def test_sale_for_apy_inverts_sell_pt():
    pool = PA.Pool("m", 1, 0, 1_000_000.0, 2_000_000.0, 50.0, 365 * 86_400 // 4, 0.001, 80.0, 0.05, 1.0)
    s = PA.sale_for_apy(pool, 0.08)
    assert PA.sell_pt(pool, s)[1] == pytest.approx(0.0769610411, rel=1e-6)  # ln(1.08)
    assert PA.sale_for_apy(pool, 0.04) == 0 and PA.sell_pt(pool, PA.max_sale(pool) * 1.01) is None


def test_the_reusd_pool_behind_the_oracle(tmp_path, capsys):
    """From the pool's state 60 blocks before the first liquidation, the pool's math needs a sale of 5.52M PT to reach
    the 20.37 % APY of the first liquidation; the pool took 5.43M. It then accepted only 309k more PT, against 38.6M
    seized by the liquidations."""
    assert cli.main(["backtest", "--out", str(tmp_path)]) == 0
    p = json.loads((tmp_path / "backtest-pt-reusd-2026-08-25.json").read_text())["pool"]
    assert p["apy_before"] == pytest.approx(0.1058, abs=1e-4) and p["apy_at_first"] == pytest.approx(0.2037, abs=1e-4)
    assert p["model_sale"] / p["pt_sold"] == pytest.approx(1, abs=0.03)
    assert p["model_asset_out"] / p["asset_out"] == pytest.approx(1, abs=0.01)
    assert p["capacity_at_first"] < 0.01 * p["seized_pt"]
    # D210: from the sale alone, the oracle falls 2.36 % and the same borrowers are liquidated, none missed
    assert p["sale_fall"] == pytest.approx(0.0236, abs=5e-4)
    for m in json.loads((tmp_path / "backtest-pt-reusd-2026-08-25.json").read_text())["markets"]:
        s = m["from_sale"]
        assert s["positions"] == m["realised_positions"] and s["missed"] == 0 and s["extra"] == 0
    assert "came back to the markets as free liquidity" in capsys.readouterr().out


def test_the_cascade_stops_at_the_pools_cap(tmp_path):
    """D238 (K9): from the 2.36 % of the sale alone, the liquidations seize 40.5M PT; the pool takes only 98k more
    before its 96 % cap, so the fall stops at 2.46 % (observed 2.45 % and 2.76 %), with the same borrowers."""
    assert cli.main(["backtest", "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / "backtest-pt-reusd-2026-08-25.json").read_text())
    c = r["pool"]["cascade"]
    assert c["capped"] and c["fall"] == pytest.approx(0.0246, abs=3e-4) and c["unsold_pt"] > 0.99 * c["seized_pt"]
    for m in r["markets"]:
        s = m["from_cascade"]
        assert s["positions"] == m["realised_positions"] and s["missed"] == 0 and s["extra"] == 0


def test_cascade_pure():
    pool = PA.Pool("m", 1, 0, 1_000_000.0, 2_000_000.0, 20.0, PA.YEAR, 0.0, 0.0, 0.05, 1.0)
    none = PA.cascade(pool, 100_000.0, lambda fall: 0.0)
    assert none["sold_pt"] == 0 and len(none["steps"]) == 1
    grow = PA.cascade(pool, 100_000.0, lambda fall: 2_000_000.0 * fall)  # seizes more the deeper it falls
    assert grow["fall"] > none["fall"] and len(grow["steps"]) > 1
