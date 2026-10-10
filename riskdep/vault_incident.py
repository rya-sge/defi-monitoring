"""Incident mode for a vault depositor: a collateral's price, as the oracle sees it, falls by x % (plan
2026-10-11-vault-incident, D98–D103).

The incident that threatens a vault lending against issuer-priced collateral (RWA, credit, yield tokens) is a NAV
markdown: the issuer publishes a lower value, the oracle passes it on at once, and the market's borrowers become
liquidatable or underwater. For each market of the vault holding that collateral:

  liquidatable   the debt of positions whose collateral × (1 − x) × LLTV < debt          (market_risk.value)
  bad debt       Σ max(0, debt − collateral × (1 − x) / LIF)                               (market_risk.value)
  vault loss     Σ the vault's share of each market's supply × its bad debt
  depositor      staying: the share of the vault × the vault loss (bad debt is shared pro rata once written off);
                 leaving first: the exit queue's loss on what cannot leave (exit_queue.py)

Bad debt is written off only when the positions are liquidated; until then the share price stays at par, and the
depositors who leave first leave the loss to those who stay.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import exit_queue as EQ
from . import market_risk as MR
from . import oracle_class as OC
from . import scenario
from . import sources as S
from .discover import REGISTRY
from .vault import discover_vault, largest_depositor, read_state


@dataclass
class MarketHit:
    market_id: str
    label: str
    drop: float
    borrowers: int
    total_borrow: float
    liquidatable_debt: float
    bad_debt: float
    vault_share: float  # the vault's share of the market's supply
    vault_loss: float
    oracle_class: str
    timing: str
    vault_exposure: float = 0.0  # the vault's assets in this market: what the incident puts at risk


@dataclass
class VaultIncident:
    vault: str
    name: str
    symbol: str
    block: int
    depositor: str | None
    shocks: dict[str, float]  # collateral token → fall of its oracle price
    hits: list[MarketHit]
    vault_total: float
    vault_loss: float
    depositor_assets: float
    loss_if_stay: float
    can_leave_now: float
    stuck: float
    loss_if_exit_first: float
    verdict: str
    reason: str
    notes: list[str] = field(default_factory=list)
    asset: str = ""  # the vault's asset address
    asset_usd: float | None = None  # its USD price (DefiLlama), to add vaults in different assets into one book

    def lines(self) -> list[str]:
        s = self.symbol
        shock = (
            ", ".join(f"{h.label.split('/')[0]} −{h.drop:.0%}" for h in self.hits) or "no market of the vault holds it"
        )
        out = [f"INCIDENT  {shock}  ·  {self.name} ({self.vault}), block {self.block}"]
        for h in self.hits:
            out.append(
                f"  {h.label}: {h.liquidatable_debt:,.0f} of {h.total_borrow:,.0f} {s} of debt liquidatable "
                f"({h.borrowers} borrowers); bad debt {h.bad_debt:,.0f}; the vault supplies {h.vault_share:.0%} → "
                f"its loss {h.vault_loss:,.0f}"
            )
            out.append(f"    oracle {h.oracle_class}; how fast: {h.timing}")
        out.append(
            f"  vault loss {self.vault_loss:,.0f} {s} ({self.vault_loss / self.vault_total:.2%} of {self.vault_total:,.0f})"
            if self.vault_total
            else "  empty vault"
        )
        if self.depositor:
            out.append(
                f"  depositor {self.depositor}: {self.depositor_assets:,.0f} {s}; staying loses {self.loss_if_stay:,.0f}; "
                f"leaving first recovers {self.can_leave_now:,.0f} at par, {self.stuck:,.0f} stays, loss {self.loss_if_exit_first:,.0f}"
            )
        out.append(f"  verdict given the incident: {self.verdict}: {self.reason}")
        out += [f"  note: {n}" for n in self.notes]
        return out

    def to_json(self) -> dict:
        return asdict(self)


# --- pure


def parse_token_shocks(items: list[str] | None) -> list[tuple[str, float]]:
    """`["token=0xabc…:0.30", "token=mGLOeuro:0.2"]` → `[("0xabc…", 0.3), ("mgloeuro", 0.2)]`: a collateral, by address
    or symbol, and the fall of its oracle price (a fraction)."""
    out = []
    for it in items or []:
        name, sep, rest = it.partition("=")
        if name.strip() != "token" or not sep:
            raise ValueError(
                f"'{it}': a vault incident is token=<collateral address or symbol>:<fall>, e.g. token=mGLOeuro:0.30"
            )
        tok, sep2, value = rest.rpartition(":")
        if not sep2 or not tok:
            raise ValueError(f"'{it}': give the fall after a colon, e.g. token={rest}:0.30")
        try:
            v = float(value)
        except ValueError:
            raise ValueError(f"'{it}': the fall must be a number between 0 and 1") from None
        if not 0 < v <= 1:
            raise ValueError(f"'{it}': the fall must be above 0 and at most 1 (0.30 for 30 %)")
        out.append((tok.strip().lower(), v))
    return out


def nav_timing(profile: scenario.OracleProfile | None) -> str:
    """D100: how fast a fall of the collateral's oracle price reaches the market."""
    if profile is None or profile.kind == OC.NOT_CLASSIFIED:
        return "unknown: the oracle could not be classified"
    if profile.kind == OC.CONSTANT_PRICE:
        return (
            "at once when the issuer publishes the new value: the oracle is the issuer's rate or NAV, so no market "
            "move announces it, and liquidations can start in the same block"
        )
    if profile.kind == OC.PRICE_TRACKING:
        return f"as the market falls, through the feed ({'TWAP ' + str(profile.twap_s) + ' s' if profile.twap_s else 'its next update'})"
    return "through a meta-oracle: " + scenario.time_to_impact(profile, {"issuer_depeg": 0.5}).text


def market_hit(
    mid: str,
    info: MR.MarketInfo,
    positions: dict[str, tuple[int, int]],
    totals: tuple[int, int],
    price: int | None,
    drop: float,
    vault_share: float,
    profile: scenario.OracleProfile | None,
    exposure: float = 0.0,
) -> MarketHit:
    """D99, pure: one market's liquidations and bad debt at the shocked oracle price, and the vault's part."""
    shocked = int(price * (1 - drop)) if price is not None else None
    r = MR.value(positions, totals, shocked, info)
    unit = 10**info.loan_decimals
    bad = r.unrealised_bad_debt / unit
    return MarketHit(
        mid,
        info.label,
        drop,
        r.borrowers,
        r.total_borrow / unit,
        r.liquidatable_now / unit,
        bad,
        vault_share,
        bad * vault_share,
        profile.kind if profile else OC.NOT_CLASSIFIED,
        nav_timing(profile),
        exposure,
    )


def decide(
    liq: EQ.Liquidity, vault_loss_raw: int, exposure_raw: int, unit: int
) -> tuple[float, float, float, float, str, str]:
    """D101, pure: (loss if stay, can leave, stuck, loss if exit first, verdict, reason), in asset units."""
    case = EQ.LossCase("incident", vault_loss_raw, exposure_raw)
    stay = EQ.pro_rata_loss(liq, case) / unit
    first = EQ.exit_at(liq, 0)
    leave = EQ.depositor_loss(liq, first, case) / unit
    par, stuck = first.par / unit, first.stuck / unit
    if vault_loss_raw <= 0:
        return (
            stay,
            par,
            stuck,
            leave,
            "STAY",
            "the collateral still covers the debt after the fall: no bad debt reaches the vault",
        )
    gain = stay - leave
    if gain > 1 and gain >= REGISTRY["incident"]["exit_min_gain"] * stay:
        return (
            stay,
            par,
            stuck,
            leave,
            "EXIT",
            f"withdraw the {par:,.0f} that can leave now, before the bad debt is written off: your loss falls from "
            f"{stay:,.0f} to {leave:,.0f}; {stuck:,.0f} cannot leave and carries the rest",
        )
    return (
        stay,
        par,
        stuck,
        leave,
        "STAY",
        f"leaving first saves only {gain:,.0f} ({gain / stay:.1%} of the {stay:,.0f} loss): too little can leave, or the "
        "depositor is most of the vault, so the loss falls on it either way; withdrawing what can leave still cuts "
        f"its exposure to a further cut by {par:,.0f}",
    )


# --- I/O


def run(
    f: S.Fetcher,
    vault: str,
    block: int,
    depositor: str | None,
    token_shocks: list[tuple[str, float]],
    profile_all: bool = False,
) -> VaultIncident:
    """Read the vault and every borrower of its markets at `block`, then apply the incident (D98). `profile_all`
    reads every market's oracle, not only the hit ones, so a recording serves any later shock (D105)."""
    view = discover_vault(f, vault, block)
    dep = depositor.lower() if depositor else largest_depositor(f, vault)
    st = read_state(f, view, block, dep)
    risk = MR.VaultRisk(f, view, st, block)
    shares = MR.vault_supply_shares(st, risk.markets)
    unit = 10**view.decimals

    # resolve each shocked token, given by address or by symbol, to the collateral addresses of the vault's markets
    params = {mp.id: mp for a in view.adapters for mp in a.markets.values()}
    drops: dict[str, float] = {}
    for tok, v in token_shocks:
        for mid, mp in params.items():
            if tok in (mp.collateral_token.lower(), mp.collateral_symbol.lower()):
                drops[mid] = max(drops.get(mid, 0.0), v)

    profiles = (
        {mid: scenario.oracle_profile(f, params[mid].oracle, "latest") for mid in risk.markets} if profile_all else {}
    )
    hits, loss_raw, exposure_raw = [], 0, 0
    for mid, d in drops.items():
        if mid not in risk.markets:
            continue  # below one whole token allocated: not followed (D47)
        profile = profiles.get(mid) or scenario.oracle_profile(f, params[mid].oracle, "latest")
        h = market_hit(
            mid,
            risk.markets[mid],
            risk.tracker.positions.get(mid, {}),
            risk.tracker.totals.get(mid, (0, 0)),
            st.markets[mid].oracle_price,
            d,
            shares.get(mid, 0.0),
            profile,
            st.markets[mid].vault_assets / unit,
        )
        hits.append(h)
        loss_raw += int(h.vault_loss * unit)
        if h.bad_debt > 0:
            exposure_raw += st.markets[mid].vault_assets

    liq = EQ.liquidity(st)
    stay, par, stuck, leave, verdict, reason = decide(liq, loss_raw, exposure_raw, unit)
    notes = [
        "bad debt is written off only when the positions are liquidated; until then the share price stays at par, "
        "and those who leave first leave the loss to those who stay"
    ]
    if any(h.oracle_class == OC.CONSTANT_PRICE and h.liquidatable_debt > 0 for h in hits):
        notes.append(
            "liquidating issuer-priced collateral needs a buyer of the issuer's token; if no liquidator acts, the bad "
            "debt stays unrealised and the market's liquidity stays locked"
        )
    if st.liquidity_market and st.liquidity_market in drops:
        notes.append(
            "the hit market is the vault's liquidity market: plain withdrawals draw on its free liquidity only"
        )
    if dep and st.total_supply:
        notes.append(f"the depositor holds {st.depositor_shares / st.total_supply:.2%} of the vault")
    return VaultIncident(
        view.address,
        view.name,
        view.asset_symbol,
        block,
        dep,
        {params[m].collateral_symbol: d for m, d in drops.items()},
        hits,
        st.total_assets / unit,
        loss_raw / unit,
        st.depositor_assets / unit,
        stay,
        par,
        stuck,
        leave,
        verdict,
        reason,
        notes,
        view.asset,
        asset_usd(f, view.asset),
    )


def asset_usd(f: S.Fetcher, asset: str) -> float | None:
    """The vault asset's USD price from DefiLlama; None when it cannot be read (then the book assumes 1, and says so)."""
    try:
        return S.coin_prices(f, [asset]).get(f"ethereum:{asset}", {}).get("price")
    except (S.SourceError, S.CacheMiss):
        return None


def write(inc: VaultIncident, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"vault-incident-{inc.vault}.json"
    p.write_text(json.dumps(inc.to_json(), indent=2))
    return p
