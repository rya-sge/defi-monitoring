"""Exit liquidity live from KyberSwap (plan 2026-10-11-exit-liquidity, D212–D214)."""

import pytest

from riskdep import exit_liquidity as XL
from riskdep import sources as S


def test_route_at_the_incidents_size():
    q = {100_000.0: 0.001, 1_000_000.0: 0.02, 5_000_000.0: 0.12, 20_000_000.0: None}
    assert XL.at(q, 500_000) == ("deep", pytest.approx(0.001 + 0.019 * 4 / 9), 5_000_000)
    assert XL.at(q, 3_000_000)[0] == "thin"  # 7 % slippage, above the 5 % threshold
    assert XL.at(q, 8_000_000)[0] == "thin"  # beyond what the aggregator routes
    assert XL.at({100_000.0: None}, 50_000) == ("none", None, 0.0)
    assert XL.at({100_000.0: 0.0, 1_000_000.0: 0.0, 5_000_000.0: 0.0, 20_000_000.0: 0.0}, 50_000_000)[0] == "deep"


class _Kyber:
    """Answers like KyberSwap: a 1 % slippage up to 1M of the loan token, then no route."""

    def get_json(self, url, transform=None):
        amount = int(url.rsplit("amountIn=", 1)[1])
        if amount > 10**6 * 10**18:  # 1M collateral units at a price of 1
            return transform({"code": 4008, "message": "route not found"})
        return transform({"code": 0, "data": {"routeSummary": {"amountOut": str(amount // 10**12 * 99 // 100)}}})


def test_ladder_stops_at_the_first_size_with_no_route():
    q = XL.ladder(_Kyber(), "0xc", "0xl", 10**24, 6)  # 18-decimal collateral, 6-decimal loan, price 1
    assert q == {100_000.0: pytest.approx(0.01), 1_000_000.0: pytest.approx(0.01), 5_000_000.0: None}
    with pytest.raises(S.CacheMiss):
        XL.ladder(S.Fetcher("offline", S.SNAPSHOT_DIR / "nowhere"), "0xc", "0xl", 10**24, 6)


def test_belem_markdown_quotes_its_collateral_live(tmp_path, capsys):
    """D214: the recorded incident carries KyberSwap's ladder: mGLOeuro has no route into EURCV."""
    import json

    from riskdep import cli

    belem = "0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec"
    assert cli.main(["analyze", "--vault", belem, "--shock", "token=mGLOeuro:0.50", "--out", str(tmp_path)]) == 0
    inc = json.loads((tmp_path / f"vault-incident-{belem.lower()}.json").read_text())
    (hit,) = inc["hits"]
    assert hit["exit_source"] == "KyberSwap" and hit["exit_route"] == "none" and hit["liquidatable_debt"] > 0
    assert "no route for the collateral on KyberSwap" in capsys.readouterr().out
