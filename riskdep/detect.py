"""Detection → impact for a vault (plan 2026-10-11-detect, D187–D189; `NEXT_STEP.md` A3).

When a vault market's oracle falls within a batch (an issuer marking its NAV down, a feed rewritten, a market fall
the oracle follows), the incident has landed: the watch already holds the new prices and every borrower revalued at
them (`market_risk.VaultRisk`). This module turns that into the brief's answer, in the alert itself: what the vault
loses now, what is liquidatable, what the depositor loses if it stays or leaves first, and the verdict, with the same
rule as `analyze --vault` (`vault_incident.decide`). Pure: the watch passes its states.
"""

from __future__ import annotations

from . import exit_queue as EQ
from . import market_risk as MR
from .discover import REGISTRY
from .rules import Alert
from .vault_incident import decide

W = REGISTRY["watch"]


def last_prices(known: dict[str, int], st) -> dict[str, int]:
    """D187, pure: the last price each market's oracle answered; an oracle that stops answering for a while (a feed
    being upgraded) keeps its last answer, so the fall is measured across the gap."""
    return {**known, **{mid: m.oracle_price for mid, m in st.markets.items() if m.oracle_price}}


def oracle_falls(known: dict[str, int], after, markets: dict) -> dict[str, float]:
    """D187, pure: the vault markets whose oracle fell at least `watch.impact_oracle_fall` since its last answer."""
    out = {}
    for mid in markets:
        a = after.markets.get(mid)
        p0, p1 = known.get(mid), (a.oracle_price if a else None)
        if p0 and p1 is not None and p1 < p0 and 1 - p1 / p0 >= W["impact_oracle_fall"]:
            out[mid] = 1 - p1 / p0
    return out


def impact_alerts(known: dict[str, int], after, risks: dict, markets: dict, decimals: int, block: int) -> list[Alert]:
    """D188, pure: one alert per batch in which a vault market's oracle fell: the impact, already landed, and the
    verdict. `known` are the oracles' last answers before this batch (`last_prices`); `risks` the markets' valuations
    at the new prices (`VaultRisk.risks` after its step)."""
    falls = oracle_falls(known, after, markets)
    if not falls:
        return []
    unit = 10**decimals
    shares = MR.vault_supply_shares(after, markets)
    loss_raw = sum(int(r.unrealised_bad_debt * shares.get(mid, 0.0)) for mid, r in risks.items())
    exposure_raw = sum(after.markets[mid].vault_assets for mid, r in risks.items() if r.unrealised_bad_debt > 0)
    liquidatable = {
        markets[mid].label: risks[mid].liquidatable_now / 10 ** markets[mid].loan_decimals
        for mid in falls
        if mid in risks and risks[mid].liquidatable_now
    }
    stay, par, stuck, leave, verdict, reason = decide(EQ.liquidity(after), loss_raw, exposure_raw, unit)
    moved = ", ".join(f"{markets[mid].label} −{f:.1%}" for mid, f in sorted(falls.items(), key=lambda kv: -kv[1]))
    total = after.total_assets / unit if after.total_assets else 0.0
    loss = loss_raw / unit
    return [
        Alert(
            "critical" if loss_raw > 0 else "warn",
            block,
            None,
            "OracleImpact",
            f"Oracle fell: {moved}; the vault's loss is now {loss:,.0f} ({loss / total:.2%} of the vault)"
            if total
            else f"Oracle fell: {moved}",
            (
                "liquidatable now: " + ", ".join(f"{k} {v:,.0f}" for k, v in liquidatable.items()) + "; "
                if liquidatable
                else "nothing liquidatable yet; "
            )
            + "the oracle already reads the new price, so the impact has landed. "
            + (
                f"Depositor: staying loses {stay:,.0f}; leaving first recovers {par:,.0f} at par, {stuck:,.0f} "
                f"stays, loss {leave:,.0f}. "
                if after.depositor_assets
                else ""
            )
            + f"Verdict given the incident: {verdict}: {reason}",
            -stay if after.depositor_assets else None,
            {
                "falls": falls,
                "vault_loss": loss,
                "liquidatable": liquidatable,
                "loss_if_stay": stay,
                "loss_if_exit_first": leave,
                "can_leave_now": par,
                "verdict": verdict,
            },
        )
    ]
