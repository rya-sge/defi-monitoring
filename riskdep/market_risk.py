"""Every borrower of the watched markets (plan 2026-10-10-market-borrowers, D45–D50).

For one position with collateral value v at the oracle price and debt D, at an oracle fall d:
  liquidatable   v (1 − d) × LLTV < D
  bad debt       max(0, D − v (1 − d) / LIF)   a liquidator repays at most the collateral's value / LIF
Unrealised bad debt is the bad debt at d = 0: debt Blue still counts as owed although the collateral
no longer covers it, written off only when the position is liquidated.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eth_abi import decode

from . import sources as S
from .abi import MORPHO_BLUE, Event
from .discover import REGISTRY, morpho_lif
from .rules import Alert
from .vault import _call

W = REGISTRY["watch"]
CURVE_DROPS = (0.02, 0.05, 0.10, 0.20, 0.30, 0.50)  # D50, widened by D98: issuer NAV cuts create bad debt past 20 %
CHUNK = 200
TOUCHING = ("Borrow", "Repay", "SupplyCollateral", "WithdrawCollateral", "Liquidate")


@dataclass
class MarketInfo:
    id: str
    lltv: float
    loan_decimals: int
    loan_symbol: str
    label: str

    @property
    def lif(self) -> float:
        return morpho_lif(self.lltv)


@dataclass
class CurvePoint:
    drop: float
    liquidatable_debt: int  # loan-token units (raw)
    positions: int
    bad_debt: int
    collateral: int = 0  # collateral-token units (raw) of the liquidatable positions: what liquidators can sell


@dataclass
class MarketRisk:
    id: str
    borrowers: int
    total_borrow: int
    liquidatable_now: int  # debt of positions with HF ≤ 1
    unrealised_bad_debt: int
    curve: list[CurvePoint] = field(default_factory=list)

    def point(self, drop: float) -> CurvePoint | None:
        return next((p for p in self.curve if abs(p.drop - drop) < 1e-9), None)


def list_borrowers(f: S.Fetcher, market_id: str) -> list[str]:
    """All addresses with borrow shares in the market, from the Morpho API (D45)."""
    out, skip = [], 0
    while True:
        try:
            d = S.morpho(
                f,
                """query($id:String!, $skip:Int!){ marketPositions(first:1000, skip:$skip,
                  where:{marketUniqueKey_in:[$id], chainId_in:[1], borrowShares_gte:"1"}){
                  pageInfo{ countTotal } items{ user{ address } } } }""",
                {"id": market_id, "skip": skip},
            )["marketPositions"]
        except (S.SourceError, S.CacheMiss, KeyError, TypeError):
            return out
        out += [i["user"]["address"].lower() for i in d["items"]]
        skip += 1000
        if skip >= d["pageInfo"]["countTotal"] or not d["items"]:
            return out


def value(
    positions: dict[str, tuple[int, int]], totals: tuple[int, int], price: int | None, m: MarketInfo
) -> MarketRisk:
    """Pure: positions {borrower: (collateral, borrowShares)}, totals (totalBorrowAssets, totalBorrowShares)."""
    tba, tbs = totals
    debts = []
    for coll, bshares in positions.values():
        if not bshares:
            continue
        debt = bshares * (tba + 1) // (tbs + 10**6)
        cv = coll * price // 10**36 if price is not None else None
        debts.append((debt, cv, coll))
    risk = MarketRisk(m.id, len(debts), tba, 0, 0)
    if price is None:
        return risk
    for debt, cv, _ in debts:
        if cv * m.lltv <= debt:
            risk.liquidatable_now += debt
        risk.unrealised_bad_debt += max(0, debt - int(cv / m.lif))
    for d in CURVE_DROPS:
        pt = CurvePoint(d, 0, 0, 0)
        for debt, cv, coll in debts:
            v = cv * (1 - d)
            if v * m.lltv < debt:
                pt.liquidatable_debt += debt
                pt.positions += 1
                pt.collateral += coll
            pt.bad_debt += max(0, debt - int(v / m.lif))
        risk.curve.append(pt)
    return risk


class Tracker:
    """Positions of every borrower of a set of markets, kept current between full refreshes (D46)."""

    def __init__(self, markets: dict[str, MarketInfo], exclude: set[str] | None = None):
        self.markets = markets
        self.exclude = {a.lower() for a in (exclude or set())}  # e.g. the watched borrower itself
        self.borrowers: dict[str, set[str]] = {}
        self.positions: dict[str, dict[str, tuple[int, int]]] = {}
        self.totals: dict[str, tuple[int, int]] = {}

    def _read(self, f: S.Fetcher, pairs: list[tuple[str, str]], block) -> None:
        ids = sorted({mid for mid, _ in pairs})
        calls = [_call(MORPHO_BLUE, "market(bytes32)", ["bytes32"], [bytes.fromhex(mid[2:])]) for mid in ids]
        calls += [
            _call(MORPHO_BLUE, "position(bytes32,address)", ["bytes32", "address"], [bytes.fromhex(mid[2:]), u])
            for mid, u in pairs
        ]
        res = []
        for i in range(0, len(calls), CHUNK):
            res += S.rpc_batch(f, calls[i : i + CHUNK], block)
        for mid, raw in zip(ids, res[: len(ids)]):
            if raw:
                mk = decode(["uint128"] * 6, bytes.fromhex(raw[2:]))
                self.totals[mid] = (mk[2], mk[3])
        for (mid, u), raw in zip(pairs, res[len(ids) :]):
            if raw:
                _, bshares, coll = decode(["uint256", "uint128", "uint128"], bytes.fromhex(raw[2:]))
                self.positions.setdefault(mid, {})[u] = (coll, bshares)

    def refresh(self, f: S.Fetcher, block) -> None:
        for mid in self.markets:
            self.borrowers[mid] = set(list_borrowers(f, mid))
        self.positions = {mid: {} for mid in self.markets}
        self._read(f, [(mid, u) for mid in self.markets for u in sorted(self.borrowers[mid])], block)

    def update(self, f: S.Fetcher, events: list[Event], block) -> int:
        """Re-read the positions this batch's Blue events touched; returns how many."""
        pairs = set()
        for e in events:
            if e.contract != "blue" or e.removed or e.name not in TOUCHING:
                continue
            mid = e.args.get("id")
            if mid not in self.markets:
                continue
            who = e.args.get("borrower") if e.name == "Liquidate" else e.args.get("onBehalf")
            if who:
                pairs.add((mid, who))
                self.borrowers.setdefault(mid, set()).add(who)
        if pairs:
            self._read(f, sorted(pairs), block)
        return len(pairs)

    def compute(self, prices: dict[str, int | None]) -> dict[str, MarketRisk]:
        out = {}
        for mid, m in self.markets.items():
            pos = {u: p for u, p in self.positions.get(mid, {}).items() if u not in self.exclude}
            out[mid] = value(pos, self.totals.get(mid, (0, 0)), prices.get(mid), m)
        return out


# --- helpers for a Vault V2 (D47)


def vault_markets(view, st) -> dict[str, MarketInfo]:
    """Markets where the vault has at least one whole token allocated."""
    out = {}
    for a in view.adapters:
        for mp in a.markets.values():
            ms = st.markets.get(mp.id)
            if ms and ms.vault_assets >= 10**view.decimals:
                out[mp.id] = MarketInfo(
                    mp.id,
                    mp.lltv,
                    view.decimals,
                    view.asset_symbol,
                    f"{mp.collateral_symbol}/{view.asset_symbol} (LLTV {mp.lltv:.1%})",
                )
    return out


def vault_prices(st, markets) -> dict[str, int | None]:
    return {mid: st.markets[mid].oracle_price for mid in markets if mid in st.markets}


def vault_supply_shares(st, markets) -> dict[str, float]:
    return {
        mid: (
            st.markets[mid].vault_assets / st.markets[mid].total_supply_assets
            if st.markets[mid].total_supply_assets
            else 0.0
        )
        for mid in markets
        if mid in st.markets
    }


def vault_eligible(st, markets) -> set[str]:
    """Markets holding at least `utilization_min_share` of the vault, for the curve alert (D49)."""
    return {
        mid
        for mid in markets
        if st.total_assets and st.markets[mid].vault_assets / st.total_assets >= W["utilization_min_share"]
    }


class VaultRisk:
    """Unrealised bad debt and curves for one vault's markets, used by both watches."""

    def __init__(self, f, view, st, block):
        self.view, self.markets = view, vault_markets(view, st)
        self.tracker = Tracker(self.markets)
        self.tracker.refresh(f, block)
        self.risks = self.tracker.compute(vault_prices(st, self.markets))

    def startup(self, st, block) -> list[Alert]:
        dep = st.depositor_shares / st.total_supply if st.total_supply else 0.0
        return assess_vault_bad_debt(
            {}, self.risks, self.markets, vault_supply_shares(st, self.markets), st.total_assets, dep, block
        ) + assess_curves({}, self.risks, self.markets, block, vault_eligible(st, self.markets))

    def step(self, f, events, st, state_block, block, refresh: bool = False) -> list[Alert]:
        if refresh:
            self.tracker.refresh(f, state_block)
        else:
            self.tracker.update(f, events, state_block)
        after = self.tracker.compute(vault_prices(st, self.markets))
        dep = st.depositor_shares / st.total_supply if st.total_supply else 0.0
        alerts = assess_vault_bad_debt(
            self.risks, after, self.markets, vault_supply_shares(st, self.markets), st.total_assets, dep, block
        ) + assess_curves(self.risks, after, self.markets, block, vault_eligible(st, self.markets))
        self.risks = after
        return alerts


# --- rules (pure)


def _fmt(raw: int, m: MarketInfo) -> str:
    return f"{raw / 10**m.loan_decimals:,.0f} {m.loan_symbol}"


def assess_vault_bad_debt(
    before: dict[str, MarketRisk],
    after: dict[str, MarketRisk],
    markets: dict[str, MarketInfo],
    vault_share: dict[str, float],
    vault_total: int,
    depositor_fraction: float,
    block: int,
) -> list[Alert]:
    """D48: the vault's share of unrealised bad debt, as a fraction of its total assets, alerted on crossing."""
    out = []
    warn, crit = W["unrealised_bad_debt_warn"], W["unrealised_bad_debt_critical"]

    def level(r: MarketRisk | None, mid: str) -> tuple[int, int]:
        if r is None or not vault_total:
            return 0, 0
        exposure = int(r.unrealised_bad_debt * vault_share.get(mid, 0.0))
        frac = exposure / vault_total
        return (2 if frac >= crit else 1 if frac >= warn else 0), exposure

    for mid, r in after.items():
        l0, _ = level(before.get(mid), mid)
        l1, exposure = level(r, mid)
        if l1 > l0:
            m = markets[mid]
            mine = exposure * depositor_fraction
            out.append(
                Alert(
                    "critical" if l1 == 2 else "warn",
                    block,
                    None,
                    "UnrealisedBadDebt",
                    f"Unrealised bad debt in {m.label}",
                    f"{_fmt(r.unrealised_bad_debt, m)} of debt is no longer covered by its collateral and not yet "
                    f"written off; the vault's share {_fmt(exposure, m)} ({exposure / vault_total:.3%} of the vault)"
                    + (f", yours {_fmt(int(mine), m)}" if depositor_fraction else "")
                    + ". Depositors who exit before the liquidation leave it to those who stay",
                    -mine / 10**m.loan_decimals if depositor_fraction else None,
                    {"market": mid, "unrealised_bad_debt": r.unrealised_bad_debt, "vault_exposure": exposure},
                )
            )
    return out


def assess_curves(
    before: dict[str, MarketRisk],
    after: dict[str, MarketRisk],
    markets: dict[str, MarketInfo],
    block: int,
    eligible: set[str] | None = None,
) -> list[Alert]:
    """D49: a steep liquidation curve, alerted on crossing."""
    out = []
    drop, share = W["curve_drop"], W["curve_warn_share"]

    def steep(r: MarketRisk | None) -> bool:
        p = r.point(drop) if r else None
        return bool(p and r.total_borrow and p.liquidatable_debt / r.total_borrow >= share)

    for mid, r in after.items():
        if eligible is not None and mid not in eligible:
            continue
        if steep(r) and not steep(before.get(mid)):
            m, p = markets[mid], r.point(drop)
            out.append(
                Alert(
                    "warn",
                    block,
                    None,
                    "LiquidationCurve",
                    f"A {drop:.0%} fall would liquidate {p.liquidatable_debt / r.total_borrow:.0%} of {m.label}",
                    f"{p.positions} position(s), {_fmt(p.liquidatable_debt, m)} of debt; their collateral would be "
                    f"sold into the market at once"
                    + (f", leaving {_fmt(p.bad_debt, m)} of bad debt" if p.bad_debt else ""),
                    None,
                    {"market": mid, "drop": drop, "liquidatable_debt": p.liquidatable_debt},
                )
            )
    return out


def curve_table(lines, risks: dict[str, MarketRisk], markets: dict[str, MarketInfo]) -> None:
    """Print one row per market: borrowers, liquidatable now, unrealised bad debt, the curve."""
    lines("  liquidation curves (debt liquidatable at an oracle fall of, % of the market's borrows):")
    lines(
        f"    {'market':<42} {'borrowers':>9} {'now':>6} {'bad debt':>14} "
        + " ".join(f"{'-' + format(d, '.0%'):>7}" for d in CURVE_DROPS)
    )
    for mid, r in sorted(
        risks.items(),
        key=lambda kv: (
            -(kv[1].point(0.05).liquidatable_debt / kv[1].total_borrow if kv[1].total_borrow and kv[1].curve else 0)
        ),
    ):
        m = markets[mid]
        tb = r.total_borrow or 1
        lines(
            f"    {m.label:<42} {r.borrowers:>9} {r.liquidatable_now / tb:>6.1%} "
            f"{r.unrealised_bad_debt / 10**m.loan_decimals:>10,.0f} {m.loan_symbol:<4}"
            + " ".join(f"{p.liquidatable_debt / tb:>7.1%}" for p in r.curve)
        )
