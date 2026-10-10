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

TERMINAL = frozenset(REGISTRY["stables"])


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
    via: str = ""  # D110: empty for the collateral itself; else the wrapping path, e.g. "PT-trUSD → trUSD"
    seen: bool = True  # D111: False when the oracle does not follow a markdown of what the collateral wraps


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
        shock = ", ".join(f"{k} −{v:.0%}" for k, v in self.shocks.items()) or "no market of the vault holds it"
        out = [f"INCIDENT  {shock}  ·  {self.name} ({self.vault}), block {self.block}"]
        for h in self.hits:
            out.append(
                f"  {h.label}: {h.liquidatable_debt:,.0f} of {h.total_borrow:,.0f} {s} of debt liquidatable "
                f"({h.borrowers} borrowers); bad debt {h.bad_debt:,.0f}; the vault supplies {h.vault_share:.0%} → "
                f"its loss {h.vault_loss:,.0f}"
            )
            if h.via:
                out.append(
                    f"    reached through what its collateral wraps: {h.via}"
                    + (
                        ""
                        if h.seen
                        else "; the oracle does not follow it: no liquidation, the lenders' shortfall "
                        "if the markdown persists is counted as the loss (hidden)"
                    )
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


def match_token(collateral: str, chain: list[str], symbols: dict[str, str], tok: str) -> tuple[str, str] | None:
    """D110, pure: does the shocked token `tok` (an address or a symbol, lower case) reach this collateral? Returns
    (via, the token's symbol): via is empty for the collateral itself, else the path "PT-trUSD → strUSD → trUSD"."""
    path = [collateral] + chain
    for i, t in enumerate(path):
        if tok in (t, symbols.get(t, "").lower()):
            via = " → ".join(symbols.get(x, x[:10]) for x in path[: i + 1]) if i else ""
            return via, symbols.get(t, t)
    return None


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


def hidden_shortfall(positions: dict[str, tuple[int, int]], totals: tuple[int, int], price: int, drop: float) -> int:
    """D111, pure: Σ max(0, debt − collateral value × (1 − drop)), raw loan units: what lenders lose if the collateral
    is worth `drop` less while the oracle, which does not follow, liquidates nobody."""
    tba, tbs = totals
    out = 0
    for coll, bshares in positions.values():
        if bshares:
            debt = bshares * (tba + 1) // (tbs + 10**6)
            out += max(0, debt - int(coll * price // 10**36 * (1 - drop)))
    return out


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
    via: str = "",
) -> MarketHit:
    """D99, pure: one market's liquidations and bad debt at the shocked oracle price, and the vault's part. D111: when
    the market is reached through what its collateral wraps (`via`) and its oracle does not track a market, the oracle
    does not move; the loss is the hidden shortfall, with nothing liquidated."""
    seen = not via or (profile is not None and profile.kind == OC.PRICE_TRACKING)
    unit = 10**info.loan_decimals
    if seen:
        shocked = int(price * (1 - drop)) if price is not None else None
        r = MR.value(positions, totals, shocked, info)
        liquidatable, bad = r.liquidatable_now / unit, r.unrealised_bad_debt / unit
    else:
        r = MR.value(positions, totals, price, info)
        liquidatable = 0.0
        bad = hidden_shortfall(positions, totals, price, drop) / unit if price is not None else 0.0
    return MarketHit(
        mid,
        info.label,
        drop,
        r.borrowers,
        r.total_borrow / unit,
        liquidatable,
        bad,
        vault_share,
        bad * vault_share,
        profile.kind if profile else OC.NOT_CLASSIFIED,
        nav_timing(profile)
        if seen
        else "the oracle does not move; the loss lands when the collateral is repriced or sold",
        exposure,
        via,
        seen,
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

    # resolve each shocked token, given by address or by symbol, to the markets whose collateral is it or wraps it
    params = {mp.id: mp for a in view.adapters for mp in a.markets.values()}
    chains, symbols = collateral_chains(f, {mp.collateral_token for mp in params.values()}, block)
    for mp in params.values():
        symbols.setdefault(mp.collateral_token, mp.collateral_symbol)
    drops: dict[str, float] = {}
    vias: dict[str, str] = {}
    names: dict[str, str] = {}
    for tok, v in token_shocks:
        for mid, mp in params.items():
            found = match_token(mp.collateral_token, chains.get(mp.collateral_token, []), symbols, tok)
            if found is None or v <= drops.get(mid, 0.0):
                continue
            drops[mid], vias[mid] = v, found[0]
            names[tok] = found[1]

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
            vias.get(mid, ""),
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
        {names.get(tok, tok): v for tok, v in token_shocks if tok in names},
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


def collateral_chains(
    f: S.Fetcher, tokens: set[str], block, depth: int = 4
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """D110: what each collateral wraps, level by level: a PT's Pendle underlying, an ERC-4626 share's asset()
    (`siblings.underlyings`); and the symbols of every token met. A vault of vaults that answers neither stays opaque.
    The registry's stablecoins (USDC, USDT) end a chain, as in `siblings.family`: they are the loan assets."""
    from .siblings import underlyings
    from .vault import _symbol

    step: dict[str, str] = {}
    level = {t.lower() for t in tokens}
    for _ in range(depth):
        try:
            found = underlyings(f, level, block)
        except (S.SourceError, S.CacheMiss):
            break
        step.update({t: u for t, (u, _how) in found.items()})
        level = {u for u, _how in found.values() if u not in step and u not in tokens and u not in TERMINAL}
        if not level:
            break
    chains: dict[str, list[str]] = {}
    for t in tokens:
        chain, x = [], t.lower()
        while x in step and step[x] not in chain and step[x] not in TERMINAL and len(chain) < depth:
            x = step[x]
            chain.append(x)
        chains[t.lower()] = chain
    symbols: dict[str, str] = {}
    for t in {x for c in chains.values() for x in c}:
        try:
            symbols[t] = _symbol(f, t, block)
        except (S.SourceError, S.CacheMiss):
            symbols[t] = t[:10]
    return chains, symbols


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
