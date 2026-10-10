"""Drain threshold (plan 2026-10-10-drain-threshold): d*, the Public Allocator inflow, the alert, the recorded vault."""

import json

import pytest

from riskdep import drain as DR
from riskdep import exit_queue as EQ
from riskdep import market_risk as MR
from riskdep import sources as S
from riskdep import vault as V
from riskdep.cli import DEMO_VAULT, REPLAY_DIR, main

M = 10**18
LOAN = "0x" + "10" * 20
WAD = 10**18


def test_d_star_matches_team2():
    assert DR.d_star(0.915, 0.0) == pytest.approx(0.085)
    assert DR.d_star(0.86, 0.0) == pytest.approx(0.14)
    assert DR.d_star(0.86, 0.005) > DR.d_star(0.86, 0.0)  # buying costs push the threshold out


def test_discount_from_divergence():
    assert DR.discount(0.25) == pytest.approx(0.20)  # oracle 25 % above the market: market 20 % below the oracle
    assert DR.discount(None) is None


def test_headroom_uses_absolute_and_relative_caps():
    assert DR.headroom((10, 100, WAD), 1_000) == 90  # relative WAD: no limit
    assert DR.headroom((10, 100, WAD // 20), 1_000) == 40  # 5 % of 1,000 = 50
    assert DR.headroom((60, 100, WAD // 20), 1_000) == 0
    assert DR.headroom(None, 1_000) == 0


def _vault():
    """Two markets on one adapter: A (the drain target) and B (a source)."""
    mp = {
        k: V.MarketParams(
            f"0x{k * 64}",
            LOAN,
            "0x" + ("c1" if k == "a" else "c2") * 20,
            "0x" + "0e" * 20,
            "0x" + "1e" * 20,
            0.86,
            k.upper(),
        )
        for k in ("a", "b")
    }
    ad = V.AdapterView("0x" + "ad" * 20, "market", {m.id: m for m in mp.values()})
    view = V.VaultView("0x" + "fa" * 20, LOAN, "USDC", 18, "Vault", [ad], None)
    markets = {
        mp["a"].id: V.MarketState(mp["a"].id, 1, 100 * M, 1, 90 * M, 50 * M, None),  # 10 free
        mp["b"].id: V.MarketState(mp["b"].id, 1, 100 * M, 1, 60 * M, 50 * M, None),  # 40 free, vault can take 40
    }
    caps = {cid: (0, 2**128 - 1, WAD) for m in mp.values() for cid in V.cap_ids(ad.address, m).values()}
    st = V.VaultState(1, 120 * M, 120 * M, 20 * M, {}, markets, caps, 0, 0)
    return view, st, mp, ad


def test_public_allocator_inflow_is_bounded_by_cap_and_sources():
    view, st, mp, ad = _vault()
    a, b = mp["a"].id, mp["b"].id
    pa = DR.PaConfig(True, True, True, {ad.address}, {a: 80 * M}, {b: True})
    assert DR.pa_inflow(view, st, pa, a) == 30 * M  # PA cap 80 − allocation 50
    pa.cap[a] = 200 * M
    assert DR.pa_inflow(view, st, pa, a) == 60 * M  # sources: idle 20 + B's withdrawable 40
    pa.can_pull_idle = False
    assert DR.pa_inflow(view, st, pa, a) == 40 * M
    assert DR.pa_inflow(view, st, DR.PaConfig(False, True), a) == 0  # not an allocator of the vault
    pa.active_adapters = set()
    assert DR.pa_inflow(view, st, pa, a) == 0


def _drain(discount, lltv=0.86):
    return DR.MarketDrain("m", "X/USDC", lltv, DR.d_star(lltv, DR.W["drain_buy_cost"]), discount, 10 * M, 0, 1.0)


def test_alert_warns_near_then_critical_at_threshold_once():
    near, open_ = _drain(DR.d_star(0.86, DR.W["drain_buy_cost"]) - 0.01), _drain(0.20)
    args = ("Vault", M, "USDC", 1)
    assert DR.assess({}, {"m": _drain(0.01)}, *args) == []
    warn = DR.assess({}, {"m": near}, *args)
    assert [a.level for a in warn] == ["warn"] and warn[0].event == "DrainWindow"
    assert DR.assess({"m": near}, {"m": near}, *args) == []
    crit = DR.assess({"m": near}, {"m": open_}, *args)
    assert [a.level for a in crit] == ["critical"] and crit[0].depositor_impact == pytest.approx(-10)
    assert DR.assess({}, {"m": _drain(None)}, *args) == []


def test_bad_debt_appears_only_past_the_lltv_buffer():
    assert _drain(0.10).bad_debt() == 0  # (1 − 0.10) / 0.86 > 1: the collateral still covers the debt
    assert _drain(0.30).bad_debt() == int(10 * M * (1 - 0.70 / 0.86))


def test_drained_liquidity_comes_out_of_the_exit_queue():
    view, st, mp, _ = _vault()
    st.depositor_shares, st.depositor = 60 * M, "0xme"
    ds = {mp["a"].id: _drain(0.20)}
    ds[mp["a"].id].id = mp["a"].id
    drained = DR.drained_vault_liquidity(view, st, ds)
    assert drained == 10 * M  # market A's withdrawable part
    full, cut = EQ.liquidity(st), EQ.liquidity(st, drained)
    assert full.available - cut.available == drained


def test_recorded_vault_is_far_from_every_threshold(tmp_path, capsys):
    rdir = REPLAY_DIR / DEMO_VAULT
    meta = json.loads((rdir / "start.json").read_text())
    f = S.Fetcher("offline", rdir)
    block = meta["head"] - 2 - 64
    view = V.discover_vault(f, DEMO_VAULT, block)
    st = V.read_state(f, view, block, meta["depositor"])
    markets = MR.vault_markets(view, st)
    ds = DR.drains(view, st, markets, {}, DR.PaConfig())
    assert ds and all(m.discount is None and not m.open for m in ds.values())
    usde = next(mid for mid, m in markets.items() if m.label.startswith("USDe"))
    hit = DR.drains(view, st, markets, {usde: 0.12}, DR.PaConfig())[usde]  # USDe 10.7 % below the oracle
    assert hit.open and hit.drainable == st.markets[usde].liquidity
    assert main(["watch", "--replay", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "drain threshold (" in out and "settings not read" in out
    kinds = [json.loads(x)["event"] for x in (tmp_path / f"watch-{DEMO_VAULT}.jsonl").read_text().splitlines()]
    assert "DrainWindow" not in kinds
