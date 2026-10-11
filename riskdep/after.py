"""After the incident: what has already landed, what is still at risk, and whether leaving now still pays (plan
2026-10-11-after, D228–D231).

The incident mode answers before: if this happens, what is lost. Once it has happened, part of the loss has landed
and only the rest can still be avoided. A vault is read at the incident's first block (`since`) and now (`at`):

  landed     the share price's fall since: the depositor's loss on what it still holds (bad debt already written off
             by liquidations is in it), with the liquidations in the vault's markets meanwhile
  unrealised the bad debt the markets carry now, at the oracle's current price, not yet written off: whoever leaves
             first at par leaves it to those who stay
  pending    what the oracle has not passed on yet: the incident's price is the price at `since` × (1 − fall); only
             the gap between it and the oracle's price now is applied, so a fall the oracle already took is not counted
             twice (a price-tracking oracle that has fallen leaves nothing pending, a NAV feed not yet updated all of it)

The verdict weighs only what is still at risk against the cost of leaving now: the landed part is sunk.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from . import exit_queue as EQ
from . import market_risk as MR
from . import sources as S
from . import vault_incident as VI
from . import zama as ZM
from .abi import MORPHO_BLUE
from .vault import discover_vault, largest_depositor, read_state


@dataclass
class AfterMarket:
    market_id: str
    label: str
    oracle_seen: float  # the oracle's fall since `since`, as read
    pending_drop: float  # the fall still to come before the oracle reaches the incident's price
    unrealised: float  # bad debt now, loan units, the whole market
    at_full: float  # bad debt once the oracle reaches the incident's price
    vault_share: float
    liquidations: int = 0
    repaid: float = 0.0
    written_off: float = 0.0  # bad debt realised by those liquidations, the whole market

    @property
    def pending(self) -> float:
        return max(0.0, self.at_full - self.unrealised)


@dataclass
class After:
    vault: str
    name: str
    since: int
    at: int
    depositor: str
    unit_symbol: str
    share_price_since: float
    share_price_at: float
    landed: float  # the depositor's loss since, on the shares it holds now, asset units
    landed_vault: float  # the same for the whole vault
    unrealised: float  # the vault's part, asset units
    pending: float
    stay: float  # the depositor's loss from what is still at risk if it stays
    leave: float  # … if it leaves first
    par: float
    stuck: float
    verdict: str
    reason: str
    exit_cost: float
    markets: list[AfterMarket] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def at_risk(self) -> float:
        return self.unrealised + self.pending

    def lines(self) -> list[str]:
        u = self.unit_symbol
        drop = 1 - self.share_price_at / self.share_price_since if self.share_price_since else 0.0
        liq = [m for m in self.markets if m.liquidations]
        out = [
            f"AFTER THE INCIDENT  {self.name} ({self.vault}), block {self.since:,} → {self.at:,}",
            f"  already landed: the share price {'fell' if drop > 0 else 'moved'} {abs(drop):.2%} since: the depositor "
            f"{self.depositor[:10]}… has lost {self.landed:,.0f} {u} on what it holds (the vault {self.landed_vault:,.0f})"
            + (
                "; "
                + "; ".join(
                    f"{m.label}: {m.liquidations} liquidation(s), {m.repaid:,.0f} repaid, {m.written_off:,.0f} written off"
                    for m in liq
                )
                if liq
                else "; no liquidation in its markets meanwhile"
            ),
            f"  still at risk: {self.at_risk:,.0f} {u} for the vault: {self.unrealised:,.0f} unrealised now (bad debt "
            f"not yet written off) and {self.pending:,.0f} pending (the oracle has not passed the incident on yet)",
        ]
        for m in self.markets:
            if m.pending > 0 or m.unrealised > 0 or m.oracle_seen or m.pending_drop:
                out.append(
                    f"    {m.label}: the oracle fell {m.oracle_seen:.2%} so far, {m.pending_drop:.2%} still to come; "
                    f"unrealised {m.unrealised:,.0f}, pending {m.pending:,.0f} (the vault supplies {m.vault_share:.0%})"
                )
        out += [
            f"  verdict on what is still at risk: {self.verdict}: {self.reason}",
            f"  leaving now costs {self.exit_cost:,.0f} {u} for sure, and saves {max(0.0, self.stay - self.leave):,.0f} "
            "of what is still at risk; what has landed is sunk either way",
        ]
        out += [f"  note: {n}" for n in self.notes]
        return out

    def to_json(self) -> dict:
        d = asdict(self)
        d["at_risk"] = self.at_risk
        for m, x in zip(self.markets, d["markets"]):
            x["pending"] = m.pending
        return d


def remaining_drop(price_since: int | None, price_at: int | None, fall: float) -> tuple[float, float]:
    """D229, pure: (the oracle's fall so far, the fall still to come) for an incident of `fall` from the price at
    `since`: the incident's price is price_since × (1 − fall); what the oracle already took is not applied again."""
    if not price_since or not price_at:
        return 0.0, fall
    seen = 1 - price_at / price_since
    target = price_since * (1 - fall)
    return seen, max(0.0, 1 - target / price_at)


def landed_loss(shares: int, pps_since: float, pps_at: float, unit: int) -> float:
    """D228, pure: the loss on shares still held when the share price fell; 0 when it rose (interest accrued)."""
    return max(0.0, shares * (pps_since - pps_at)) / unit


# --- I/O


def run(
    f: S.Fetcher,
    vault: str,
    since: int,
    at: int,
    depositor: str | None,
    token_shocks: list[tuple],
    exit_cost_rate: float | None = None,
    horizon_days: float = 30.0,
) -> After:
    """Read the vault at `since` and at `at` (an archive RPC for an old block), the liquidations of its markets in
    between, and split the incident into landed, unrealised and pending (D228–D231)."""
    from .backtest import LIQUIDATE, decode_liquidation

    shocks = VI.normalise(token_shocks)
    view = discover_vault(f, vault, at)
    dep = depositor.lower() if depositor else largest_depositor(f, vault, frozenset(ZM.POOLS))
    st0, st1 = read_state(f, view, since, dep), read_state(f, view, at, dep)
    risk = MR.VaultRisk(f, view, st1, at)
    shares = MR.vault_supply_shares(st1, risk.markets)
    shares0 = MR.vault_supply_shares(st0, risk.markets)
    unit = 10**view.decimals
    params = {mp.id: mp for a in view.adapters for mp in a.markets.values()}
    chains, symbols = VI.collateral_chains(f, {mp.collateral_token for mp in params.values()}, at)
    for mp in params.values():
        symbols.setdefault(mp.collateral_token, mp.collateral_symbol)
    falls: dict[str, float] = {}
    for kind, tok, v, _ in shocks:
        for mid, mp in params.items():
            if kind == "token" and VI.match_token(
                mp.collateral_token, chains.get(mp.collateral_token, []), symbols, tok
            ):
                falls[mid] = max(falls.get(mid, 0.0), v)
    markets, notes = [], []
    for mid in risk.markets:
        info, pos, tot = risk.markets[mid], risk.tracker.positions.get(mid, {}), risk.tracker.totals.get(mid, (0, 0))
        p0 = st0.markets[mid].oracle_price if mid in st0.markets else None
        p1 = st1.markets[mid].oracle_price
        lu = 10**info.loan_decimals
        now = MR.value(pos, tot, p1, info).unrealised_bad_debt / lu if p1 else 0.0
        seen, todo = remaining_drop(p0, p1, falls.get(mid, 0.0)) if mid in falls else (0.0, 0.0)
        full = now
        if todo > 0:
            profile = VI.scenario.oracle_profile(f, params[mid].oracle, "latest")
            full = VI.market_hit(mid, info, pos, tot, p1, todo, shares.get(mid, 0.0), profile).bad_debt
        m = AfterMarket(mid, info.label, seen, todo, now, full, shares.get(mid, 0.0))
        try:
            logs = S.etherscan_logs(f, MORPHO_BLUE, LIQUIDATE, mid, since + 1, at) if at > since else []
            events = [decode_liquidation(x) for x in logs]
        except (S.SourceError, S.CacheMiss):
            events = None
        if events is None:
            notes.append(f"{info.label}: the liquidations since were not read (an Etherscan key, or a recording)")
        elif events:
            m.liquidations = len(events)
            m.repaid = sum(e[2] for e in events) / lu
            m.written_off = sum(e[4] for e in events) / lu
        if mid in falls or now > 0 or m.liquidations:
            markets.append(m)
    unrealised = sum(m.unrealised * m.vault_share for m in markets)
    pending = sum(m.pending * m.vault_share for m in markets)
    exposure = sum(st1.markets[m.market_id].vault_assets for m in markets if m.pending > 0 or m.unrealised > 0)
    liq = EQ.liquidity(st1)
    stay, par, stuck, leave, verdict, reason = VI.decide(liq, int((unrealised + pending) * unit), exposure, unit)
    cost, _, _ = VI.breakeven(stay, leave, par, VI.vault_apy(f, vault), horizon_days, exit_cost_rate)
    if verdict == "EXIT" and stay - leave <= cost:
        # D231: the incident has happened, so leaving pays only if what it still saves exceeds its certain cost
        verdict, reason = (
            "STAY",
            f"leaving first would still save {stay - leave:,.0f}, less than the {cost:,.0f} it costs to leave now",
        )
    if any(shares0.get(m.market_id, 0.0) and m.written_off for m in markets):
        notes.append("the bad debt written off since is in the share price's fall: it is counted once, as landed")
    held = st1.depositor_shares
    return After(
        vault.lower(),
        view.name,
        since,
        at,
        dep,
        view.asset_symbol,
        st0.share_price,
        st1.share_price,
        landed_loss(held, st0.share_price, st1.share_price, unit),
        landed_loss(st1.total_supply, st0.share_price, st1.share_price, unit),
        unrealised,
        pending,
        stay,
        leave,
        par,
        stuck,
        verdict,
        reason,
        cost,
        markets,
        notes,
    )
