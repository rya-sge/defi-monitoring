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
from . import pharos as PH
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
    event: str = "markdown"  # "markdown" (a token shock) or "default" (borrowers stop repaying, D114)
    defaulters: list[str] = field(default_factory=list)
    defaulted_debt: float = 0.0  # D114: the defaulters' debt
    exit_route: str | None = None  # D115: the collateral's exit liquidity from the registry: none, thin, deep
    no_liquidator_shortfall: float = 0.0  # D115: the loss if nobody liquidates (liquidity then stays locked)
    top1_share: float = 0.0  # D112: the largest borrower's share of the market's debt, before the incident
    top3_share: float = 0.0
    grade: str | None = None  # D120: the Pharos grade of the collateral, or of the first graded token it wraps
    pharos_exposure: float = 0.0  # D119: > 0 when the market is reached through Pharos's off-chain backing edges


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
    events: list[str] = field(default_factory=list)  # each shock in words, in the order given
    labels: dict[str, str] = field(default_factory=dict)  # each shock's target as given → as the markets name it
    pharos: str | None = None  # D122: the Pharos publication date used, None when Pharos was not read
    common_mode: list[str] = field(default_factory=list)  # D121: collateral failing with the shocked token (Pharos)

    def lines(self) -> list[str]:
        s = self.symbol
        shock = "; ".join(self.events) or ", ".join(f"{k} −{v:.0%}" for k, v in self.shocks.items())
        shock = shock or "no market of the vault matches the incident"  # D114: unmatched shocks are not described
        out = [f"INCIDENT  {shock}  ·  {self.name} ({self.vault}), block {self.block}"]
        for h in self.hits:
            out.append(
                f"  {h.label}: {h.liquidatable_debt:,.0f} of {h.total_borrow:,.0f} {s} of debt liquidatable "
                f"({h.borrowers} borrowers); bad debt {h.bad_debt:,.0f}; the vault supplies {h.vault_share:.0%} → "
                f"its loss {h.vault_loss:,.0f}"
            )
            if h.borrowers:
                out.append(
                    f"    concentration: the largest borrower holds {h.top1_share:.0%} of the debt, the three "
                    f"largest {h.top3_share:.0%}"
                )
            if h.event == "default":
                out.append(
                    f"    default: {len(h.defaulters)} borrower(s) stop repaying {h.defaulted_debt:,.0f} {s} "
                    f"({', '.join(a[:10] + '…' for a in h.defaulters)})"
                )
            if h.exit_route in ("none", "thin") and h.liquidatable_debt > 0 and h.event == "markdown":
                out.append(
                    f"    exit liquidity for the collateral: {h.exit_route}; liquidators may not act: if nobody "
                    f"liquidates, the loss is {h.no_liquidator_shortfall:,.0f} and the market's liquidity stays locked"
                )
            if h.grade:
                out.append(f"    issuer grade (Pharos {self.pharos}): {h.grade}")
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


def parse_shocks(items: list[str] | None) -> list[tuple[str, str, float, int]]:
    """D114: every vault incident shock, as (kind, target, value, n):
    token=<collateral address or symbol>:<fall>              ("token", target, fall, 0)
    borrower=<collateral, market id or all>:<recovery>[:<n>]  ("borrower", target, recovery, n): the n largest
                                                              borrowers of each matching market default, and their
                                                              collateral is recovered at that fraction of its value"""
    out = []
    for it in items or []:
        name = it.partition("=")[0].strip()
        if name == "token":
            tok, v = parse_token_shocks([it])[0]
            out.append(("token", tok, v, 0))
            continue
        if name != "borrower":
            raise ValueError(
                f"'{it}': a vault incident is token=<collateral>:<fall> or borrower=<target>:<recovery>[:<n>]"
            )
        parts = it.partition("=")[2].split(":")
        if len(parts) not in (2, 3) or not parts[0]:
            raise ValueError(
                f"'{it}': write borrower=<collateral, market id or all>:<recovery>[:<n>], e.g. borrower=mGLOeuro:0.5"
            )
        try:
            rec = float(parts[1])
            n = int(parts[2]) if len(parts) == 3 else 1
        except ValueError:
            raise ValueError(f"'{it}': the recovery is a number between 0 and 1, and n a whole number") from None
        if not 0 <= rec <= 1 or n < 1:
            raise ValueError(f"'{it}': the recovery must be between 0 and 1 (0.5 for half), n at least 1")
        out.append(("borrower", parts[0].strip().lower(), rec, n))
    return out


def normalise(shocks) -> list[tuple[str, str, float, int]]:
    """Accept the token-only pairs of `parse_token_shocks` as well as `parse_shocks`' tuples."""
    return [("token", s[0], s[1], 0) if len(s) == 2 else tuple(s) for s in shocks or []]


def describe(shock: tuple, labels: dict[str, str] | None = None) -> str:
    """One shock in words, e.g. "PST −30%" or "the largest borrower of mGLOeuro defaults, 50% recovered"."""
    kind, target, v, n = normalise([shock])[0]
    name = (labels or {}).get(target, target)
    if kind == "token":
        return f"{name} −{v:.0%}"
    who = "the largest borrower" if n == 1 else f"the {n} largest borrowers"
    where = "every market" if target == "all" else name
    return f"{who} of {where} default{'s' if n == 1 else ''}, collateral recovered at {v:.0%}"


def exit_route(collateral: str) -> str | None:
    """D115: the collateral's exit liquidity on DEXs, from the registry (none, thin, deep), or None if not measured."""
    e = REGISTRY["exit_liquidity"]["tokens"].get(collateral.lower())
    return e["route"] if e else None


def borrower_default(
    positions: dict[str, tuple[int, int]], totals: tuple[int, int], price: int, recovery: float, n: int
) -> tuple[int, int, list[str]]:
    """D114, pure: the n largest borrowers stop repaying; their collateral is recovered at `recovery` of its oracle value.
    Returns (debt defaulted, bad debt Σ max(0, debt − collateral value × recovery), the borrowers), raw loan units."""
    tba, tbs = totals
    ranked = sorted(((bs * (tba + 1) // (tbs + 10**6), u, c) for u, (c, bs) in positions.items() if bs), reverse=True)[
        :n
    ]
    debt = sum(d for d, _, _ in ranked)
    bad = sum(max(0, d - int(c * price // 10**36 * recovery)) for d, _, c in ranked)
    return debt, bad, [u for _, u, _ in ranked]


def match_token(collateral: str, chain: list[str], symbols: dict[str, str], tok: str) -> tuple[str, str] | None:
    """D110, pure: does the shocked token `tok` (an address or a symbol, lower case) reach this collateral? Returns
    (via, the token's symbol): via is empty for the collateral itself, else the path "PT-trUSD → strUSD → trUSD"."""
    path = [collateral] + chain
    for i, t in enumerate(path):
        if tok in (t, symbols.get(t, "").lower()):
            via = " → ".join(symbols.get(x, x[:10]) for x in path[: i + 1]) if i else ""
            return via, symbols.get(t, t)
    return None


def pharos_reach(
    snap: PH.Snapshot, collateral: str, chain: list[str], symbols: dict[str, str], tok: str
) -> tuple[tuple[str, str] | None, float]:
    """D119, pure: does the shocked token reach this collateral through Pharos's off-chain backing? For the outermost
    token of the collateral's on-chain path that Pharos knows, the share of its backing that is the shocked token.
    Returns ((via, the shocked token's name), share), or (None, 0) below `pharos.min_exposure`."""
    target = PH.resolve(snap, tok)
    if target is None:
        return None, 0.0
    path = [collateral] + chain
    for i, t in enumerate(path):
        pid = PH.resolve(snap, t, symbols.get(t))
        if pid is None or pid == target:
            continue
        share, ppath = PH.exposure(snap, pid, target)
        if share < PH.P["min_exposure"]:
            continue
        name = PH.name(target)
        onchain = " → ".join(symbols.get(x, x[:10]) for x in path[: i + 1])
        via = f"{onchain} ⇒ Pharos: {' → '.join(ppath)} ({share:.1%} of its backing)"
        return (via, name), share
    return None, 0.0


def graded(snap: PH.Snapshot, collateral: str, chain: list[str], symbols: dict[str, str]) -> str | None:
    """D120, pure: 'fxSAVE F 36' for the collateral or the first token of its path Pharos grades."""
    for t in [collateral] + chain:
        g = snap.grade(PH.resolve(snap, t, symbols.get(t)))
        if g:
            return f"{symbols.get(t, t[:10])} {g}"
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
    token_shocks: list[tuple],
    profile_all: bool = False,
    pharos: PH.Snapshot | None = None,
) -> VaultIncident:
    """Read the vault and every borrower of its markets at `block`, then apply the incident (D98). `token_shocks` is
    `parse_shocks`' list (token markdowns and borrower defaults, D114) or `parse_token_shocks`' pairs. `profile_all`
    reads every market's oracle, not only the hit ones, so a recording serves any later shock (D105). `pharos`, when
    given, adds grades, the off-chain backing a token shock also reaches, and common-mode groups (D117–D122)."""
    shocks = normalise(token_shocks)
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
    pexps: dict[str, float] = {}  # market → share of its collateral's backing the shocked token is (Pharos, D119)
    defaults: dict[str, tuple[float, int]] = {}  # market → (recovery, n), the harshest when several apply
    for kind, tok, v, n in shocks:
        for mid, mp in params.items():
            if kind == "borrower" and tok in ("all", mid):
                found = ("", "every market" if tok == "all" else mp.collateral_symbol)
            else:
                found = match_token(mp.collateral_token, chains.get(mp.collateral_token, []), symbols, tok)
            pexp = 0.0
            if found is None and kind == "token" and pharos is not None:
                found, pexp = pharos_reach(
                    pharos, mp.collateral_token, chains.get(mp.collateral_token, []), symbols, tok
                )
            if found is None:
                continue
            if pexp:
                names.setdefault(tok, found[1])  # an on-chain match names the token better
            else:
                names[tok] = found[1]
            if kind == "borrower":
                r0, n0 = defaults.get(mid, (1.0, 0))
                defaults[mid] = (min(r0, v), max(n0, n))
                vias.setdefault(mid, found[0])
            elif v * (pexp or 1.0) > drops.get(mid, 0.0):
                drops[mid], vias[mid] = v * (pexp or 1.0), found[0]
                pexps[mid] = pexp

    profiles = (
        {mid: scenario.oracle_profile(f, params[mid].oracle, "latest") for mid in risk.markets} if profile_all else {}
    )
    hits, loss_raw, exposure_raw = [], 0, 0
    for mid in sorted(set(drops) | set(defaults), key=list(params).index):
        if mid not in risk.markets:
            continue  # below one whole token allocated: not followed (D47)
        profile = profiles.get(mid) or scenario.oracle_profile(f, params[mid].oracle, "latest")
        positions = risk.tracker.positions.get(mid, {})
        totals = risk.tracker.totals.get(mid, (0, 0))
        price = st.markets[mid].oracle_price
        d = drops.get(mid, 0.0)
        who: list[str] = []
        if mid in defaults and price is not None:
            # D114: the defaulters leave the market's normal valuation; the others are valued as for a markdown
            recovery, n = defaults[mid]
            worth = int(price * (1 - d)) if d else price  # the collateral's value after a markdown, if any
            ddebt, dbad, who = borrower_default(positions, totals, worth, recovery, n)
            positions = {u: p for u, p in positions.items() if u not in who}
        h = market_hit(
            mid,
            risk.markets[mid],
            positions,
            totals,
            price,
            d,
            shares.get(mid, 0.0),
            profile,
            st.markets[mid].vault_assets / unit,
            vias.get(mid, "") if d else "",
        )
        lu = 10 ** risk.markets[mid].loan_decimals
        if who:
            h.event, h.defaulters, h.defaulted_debt = "default", who, ddebt / lu
            h.borrowers += len(who)
            h.bad_debt += dbad / lu
            h.vault_loss = h.bad_debt * h.vault_share
            h.via = h.via or vias.get(mid, "")
            if not d:
                h.timing = (
                    "the oracle does not move: the loss lands when the defaulted collateral is seized and sold or "
                    "redeemed; until then the debt keeps accruing and the market's liquidity stays locked"
                )
        conc = MR.value(risk.tracker.positions.get(mid, {}), totals, price, risk.markets[mid])
        h.top1_share, h.top3_share = conc.top1_share, conc.top3_share
        h.exit_route = exit_route(params[mid].collateral_token)
        h.pharos_exposure = pexps.get(mid, 0.0)
        if pharos is not None:
            h.grade = graded(
                pharos, params[mid].collateral_token, chains.get(params[mid].collateral_token, []), symbols
            )
        if d and price is not None and h.liquidatable_debt > 0:
            # D115: nobody liquidates (no exit route): the lenders carry debt − collateral value, and wait
            h.no_liquidator_shortfall = (
                hidden_shortfall(positions, totals, price, d) / lu + (dbad / lu if who else 0.0)
            ) * h.vault_share
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
    if any(h.event == "default" for h in hits):
        notes.append(
            "a default on Morpho Blue has no due date: the defaulted debt keeps accruing until the collateral is "
            "seized; the recovery is the share of the collateral's oracle value actually realised"
        )
    if any(h.oracle_class == OC.CONSTANT_PRICE and h.liquidatable_debt > 0 for h in hits):
        notes.append(
            "liquidating issuer-priced collateral needs a buyer of the issuer's token; if no liquidator acts, the bad "
            "debt stays unrealised and the market's liquidity stays locked"
        )
    unmeasured = sorted({symbols.get(params[h.market_id].collateral_token, "?") for h in hits if h.exit_route is None})
    if unmeasured:
        notes.append(
            f"exit liquidity not measured for {', '.join(unmeasured)}: add it to the registry's exit_liquidity"
        )
    if st.liquidity_market and st.liquidity_market in {h.market_id for h in hits}:
        notes.append(
            "the hit market is the vault's liquidity market: plain withdrawals draw on its free liquidity only"
        )
    mates: list[str] = []
    if pharos is None:
        notes.append("Pharos: not checked (no grades, off-chain backing or common-mode groups)")
    else:
        among = {}
        for c in params.values():
            for tkn in [c.collateral_token] + chains.get(c.collateral_token, []):
                pid = PH.resolve(pharos, tkn, symbols.get(tkn))
                if pid:
                    among.setdefault(pid, symbols.get(tkn, pid))
        for kind, tok, _, _ in shocks:
            pid = PH.resolve(pharos, tok) if kind == "token" else None
            for m in PH.common_mode(pharos, pid, among) if pid else []:
                mates.append(f"{names.get(tok, PH.name(pid))} with {m}")
        if mates:
            notes.append(
                "Pharos common-mode groups: " + "; ".join(mates) + ": one failure of that key, admin or issuer "
                "reaches both, so a second shock on them is not independent"
            )
        if any(h.pharos_exposure for h in hits):
            notes.append(
                "some markets are reached through Pharos's off-chain backing (reserve shares): their fall is the "
                "shock × that share, on the assumption that a loss in the reserve passes to the token pro rata"
            )
    if dep and st.total_supply:
        notes.append(f"the depositor holds {st.depositor_shares / st.total_supply:.2%} of the vault")
    return VaultIncident(
        view.address,
        view.name,
        view.asset_symbol,
        block,
        dep,
        {names.get(tok, tok): v for kind, tok, v, _ in shocks if kind == "token" and tok in names},
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
        [describe(s, names) for s in shocks if s[1] in names],
        names,
        pharos.as_of if pharos is not None else None,
        mates,
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
