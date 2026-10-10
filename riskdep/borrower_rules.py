"""Borrower rules (D33, D35, D36). Pure functions, no I/O.

Health factor zones: with levels (1.10, 1.05, 1.02), zone 0 is above 1.10, zone 1 below 1.10, zone 2
below 1.05, zone 3 below 1.02. Crossing into a deeper zone alerts at that zone's level (info, warn,
critical); coming back to zone 0 alerts once. HF ≤ 1 is liquidatable whatever the levels.
"""

from __future__ import annotations

import math

from .abi import Event
from .borrower import BorrowMarket, BorrowState
from .discover import REGISTRY
from .rules import Alert

W = REGISTRY["watch"]
ZONE_LEVEL = {1: "info", 2: "warn", 3: "critical"}
RATE_JUMP = 1.5            # D35: warn when the borrow APY is 50 % above its value at start


def zone(hf: float | None, levels: tuple[float, ...]) -> int:
    if hf is None or math.isinf(hf):
        return 0
    return sum(1 for lv in levels if hf < lv)


def _units(raw: int, decimals: int) -> str:
    return f"{raw / 10 ** decimals:,.2f}"


def _hf_text(hf: float | None) -> str:
    return "unknown" if hf is None else ("∞" if math.isinf(hf) else f"{hf:.4f}")


def assess_events(events: list[Event], user: str, markets: dict[str, BorrowMarket]) -> list[Alert]:
    out = []
    for e in events:
        if e.contract != "blue" or e.removed:
            continue
        a = e.args
        if e.name == "SetAuthorization":
            if a.get("authorizer") == user:
                what = "authorised" if a["newIsAuthorized"] else "removed the authorisation of"
                out.append(Alert("warn", e.block, e.tx, "Blue.SetAuthorization",
                                 f"Your address {what} {a['authorized']}",
                                 "an authorised address can borrow, withdraw collateral and repay on your behalf",
                                 None, {"authorized": a["authorized"], "on": a["newIsAuthorized"]}))
            continue
        m = markets.get(a.get("id"))
        if m is None:
            continue
        if e.name == "Liquidate" and a.get("borrower") == user:
            bad = a["badDebtAssets"]
            out.append(Alert("critical", e.block, e.tx, "Blue.Liquidate", f"You were liquidated on {m.label}",
                             f"{_units(a['repaidAssets'], m.loan_decimals)} {m.loan_symbol} repaid, "
                             f"{_units(a['seizedAssets'], m.collateral_decimals)} {m.collateral_symbol} seized"
                             + (f", {_units(bad, m.loan_decimals)} {m.loan_symbol} of bad debt" if bad else ""),
                             None, {"market": m.id, "repaid": a["repaidAssets"], "seized": a["seizedAssets"], "bad_debt": bad}))
        elif e.name in ("Borrow", "Repay", "SupplyCollateral", "WithdrawCollateral") and a.get("onBehalf") == user:
            token, dec = ((m.collateral_symbol, m.collateral_decimals) if "Collateral" in e.name
                          else (m.loan_symbol, m.loan_decimals))
            own = a.get("caller") == user
            out.append(Alert("info" if own else "warn", e.block, e.tx, f"Blue.{e.name}",
                             (f"Your {e.name}" if own else f"{e.name} on your behalf by {a.get('caller')}") + f" on {m.label}",
                             f"{_units(a['assets'], dec)} {token}", None, {"market": m.id, "caller": a.get("caller")}))
    return out


def assess_states(before: dict[str, BorrowState], after: dict[str, BorrowState], markets: dict[str, BorrowMarket],
                  levels: tuple[float, ...], start_apy: dict[str, float | None], block: int) -> list[Alert]:
    out = []
    for mid, af in after.items():
        m = markets[mid]
        b = before.get(mid)
        h1 = af.hf(m.lltv)
        h0 = b.hf(m.lltv) if b else None
        if af.debt == 0:
            continue
        if h1 is None and (b is None or h0 is not None):
            out.append(Alert("warn", block, None, "Oracle", f"Oracle unreadable on {m.label}",
                             "price() reverts: Blue cannot liquidate, and you cannot withdraw collateral or borrow",
                             None, {"market": mid}))
            continue
        z0, z1 = zone(h0, levels), zone(h1, levels)
        if h1 is not None and h1 <= 1 and (h0 is None or h0 > 1):
            out.append(Alert("critical", block, None, "HealthFactor", f"Liquidatable now on {m.label}",
                             f"HF {_hf_text(h1)} ≤ 1", None, {"market": mid, "hf": h1}))
        elif z1 > z0:
            out.append(Alert(ZONE_LEVEL[z1], block, None, "HealthFactor",
                             f"HF below {levels[z1 - 1]:.2f} on {m.label}",
                             (f"HF {_hf_text(h0)} → {_hf_text(h1)}" if b else f"HF {_hf_text(h1)}")
                             + f"; a {af.liquidation_drop(m.lltv):.2%} oracle fall liquidates",
                             None, {"market": mid, "hf": h1}))
        elif z1 == 0 and z0 > 0:
            out.append(Alert("info", block, None, "HealthFactor", f"HF back above {levels[0]:.2f} on {m.label}",
                             f"HF {_hf_text(h1)}", None, {"market": mid, "hf": h1}))
        if b and b.price and af.price:
            move = af.price / b.price - 1
            if abs(move) >= W["oracle_move_warn"]:
                out.append(Alert("warn", block, None, "Oracle", f"Oracle of {m.label} moved {move:+.1%}",
                                 f"HF now {_hf_text(h1)}", None, {"market": mid, "move": move}))
        a0 = start_apy.get(mid)
        if a0 and af.apy is not None and af.apy >= RATE_JUMP * a0 and (b is None or b.apy is None or b.apy < RATE_JUMP * a0):
            out.append(Alert("warn", block, None, "Rate", f"Borrow rate up on {m.label}",
                             f"{a0:.2%} at start → {af.apy:.2%}", None, {"market": mid, "apy": af.apy}))
        if af.utilization >= W["utilization_warn"] and (b is None or b.utilization < W["utilization_warn"]):
            out.append(Alert("warn", block, None, "Utilisation", f"{m.label} is {af.utilization:.1%} utilised",
                             "the rate model pushes the rate towards 4× its target at 100 %; lenders cannot withdraw",
                             None, {"market": mid, "utilization": af.utilization}))
    return out


def startup(states: dict[str, BorrowState], markets: dict[str, BorrowMarket], levels: tuple[float, ...],
            block: int) -> list[Alert]:
    """Conditions already true when the watch starts: compare with an empty 'before'."""
    return assess_states({}, states, markets, levels, {}, block)
