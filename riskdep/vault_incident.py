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

from . import engine as EN
from . import exit_liquidity as XL
from . import exit_queue as EQ
from . import market_risk as MR
from . import nexus as NX
from . import oracle_class as OC
from . import pharos as PH
from . import scenario
from . import sources as S
from . import zama as ZM
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
    via: str = ""  # D126: empty for the collateral itself; else the wrapping path, e.g. "PT-trUSD → trUSD"
    seen: bool = True  # D127: False when the oracle does not follow a markdown of what the collateral wraps
    event: str = "markdown"  # "markdown" (a token shock) or "default" (borrowers stop repaying, D130)
    defaulters: list[str] = field(default_factory=list)
    defaulted_debt: float = 0.0  # D130: the defaulters' debt
    exit_route: str | None = None  # D131, D213: the collateral's exit liquidity: none, thin, deep
    exit_impact: float | None = None  # D213: the slippage against the oracle at the size the liquidations seize
    exit_capacity: float | None = None  # D213: the largest size the aggregator routes, loan units
    exit_source: str = ""  # D214: "KyberSwap" (quoted live), "registry" (measured by hand on 2026-10-11) or ""
    exit_text: str = ""
    no_liquidator_shortfall: float = 0.0  # D131: the loss if nobody liquidates (liquidity then stays locked)
    top1_share: float = 0.0  # D128: the largest borrower's share of the market's debt, before the incident
    top3_share: float = 0.0
    grade: str | None = None  # D136: the Pharos grade of the collateral, or of the first graded token it wraps
    pharos_exposure: float = 0.0  # D135: > 0 when the market is reached through Pharos's off-chain backing edges
    source: str = "incident"  # D139: "engine" when the shock engine's propagation gave the figures
    engine: str = ""  # D139: what the engine saw: oracle and collateral market factors, liquidated, insolvent
    feeds: list[str] = field(default_factory=list)  # D157: each base feed of the market's oracle and its freshness
    returned: float = 0.0  # D239: what the vault can withdraw more from this market once liquidators repaid
    band: dict | None = None  # D241: the feed's floor holds the oracle back; the stage now, the rest after an upgrade
    stale_feed: bool = False


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
    pharos: str | None = None  # D138: the Pharos publication date used, None when Pharos was not read
    common_mode: list[str] = field(default_factory=list)  # D137: collateral failing with the shocked token (Pharos)
    engine_block: int | None = None  # D139: the block of the graph the shock engine ran on; None when it did not run
    sibling_losses: list[tuple[str, str, float, str]] = field(default_factory=list)  # D141: (id, market, loss, unit)
    apy: float | None = None  # D142: the vault's net yield (Morpho API), what a depositor gives up by leaving
    horizon_days: float = 30.0
    exit_cost: float = 0.0  # D142: the yield forgone over the horizon on what can leave now
    p_star: float | None = None  # D143: the incident probability over the horizon above which leaving now pays
    p_star_year: float | None = None
    outside: list[str] = field(default_factory=list)  # D145: Nexus cover prices on the hit collateral's protocols
    liquidity: tuple[float, float, float] = (0.0, 0.0, 0.0)  # D150: plain, forced (asset units), forced penalty
    exit_cost_rate: float | None = None  # D151: a flat cost of leaving, as a share of what leaves (else the yield)
    conditional: dict | None = None  # D165: the loss of staying given the incident, drawn (USD, depositor's terms)
    zama: list[str] = field(default_factory=list)  # D174: a confidential depositor's two exits, for a Zama vault
    returned_liquidity: float = 0.0  # D239: Σ hits' `returned`: freed once the liquidations have repaid their debt

    def lines(self) -> list[str]:
        s = self.symbol
        shock = "; ".join(self.events) or ", ".join(f"{k} −{v:.0%}" for k, v in self.shocks.items())
        shock = shock or "no market of the vault matches the incident"  # D130: unmatched shocks are not described
        out = [f"INCIDENT  {shock}  ·  {self.name} ({self.vault}), block {self.block}"]
        for h in self.hits:
            out.append(
                f"  {h.label}: {h.liquidatable_debt:,.0f} of {h.total_borrow:,.0f} {s} of debt liquidatable "
                f"({h.borrowers} borrowers); bad debt {h.bad_debt:,.0f}; the vault supplies {h.vault_share:.0%} → "
                f"its loss {h.vault_loss:,.0f}"
            )
            if h.source == "engine":
                out.append(f"    shock engine: {h.engine}")
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
            if h.exit_text:
                out.append(f"    exit liquidity: {h.exit_text}")
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
            out += [f"    feed {x}" for x in h.feeds]
            out.append(f"    oracle {h.oracle_class}; how fast: {h.timing}")
            if h.band:
                b = h.band
                out.append(
                    f"    now, held at the feed's floor: {b['now_liquidatable']:,.0f} {s} liquidatable, bad debt "
                    f"{b['now_bad_debt']:,.0f}, the vault's loss {b['now_vault_loss']:,.0f}; the figures above once "
                    f"the feed is upgraded" + (f", {b['timelock_h']:g} h at the earliest" if b["timelock_h"] else "")
                )
        out.append(
            f"  vault loss {self.vault_loss:,.0f} {s} ({self.vault_loss / self.vault_total:.2%} of {self.vault_total:,.0f})"
            + (
                f"; if liquidators act, the debt they repay frees {self.returned_liquidity:,.0f} more for the vault to "
                f"withdraw once they have (now {sum(self.liquidity[:2]):,.0f}; the market's other lenders can draw on it "
                "too); if nobody liquidates, it stays locked"
                if self.returned_liquidity > 0
                else ""
            )
            if self.vault_total
            else "  empty vault"
        )
        if self.depositor:
            out.append(
                f"  depositor {self.depositor}: {self.depositor_assets:,.0f} {s}; staying loses {self.loss_if_stay:,.0f}; "
                f"leaving first recovers {self.can_leave_now:,.0f} at par, {self.stuck:,.0f} stays, loss {self.loss_if_exit_first:,.0f}"
            )
        out.append(f"  verdict given the incident: {self.verdict}: {self.reason}")
        if self.hits and self.depositor:
            out.append(f"  if the incident is not certain: {self.breakeven_text()}")
        if self.conditional:
            out.append(f"  given the incident, drawn: {self.conditional['text']}")
        out += [f"  confidential (Zama): {z}" for z in self.zama]
        out += [f"  outside view: {o}" for o in self.outside]
        out += [f"  note: {n}" for n in self.notes]
        return out

    def breakeven_text(self) -> str:
        h = f"{self.horizon_days:g} days"
        if self.apy is None and self.exit_cost_rate is None:
            return "the vault's yield could not be read: the breakeven probability is not computed"
        if self.p_star is None:
            return (
                "leaving first does not lower the loss: exiting does not pay against this incident, whatever its odds"
            )
        cost = (
            f"leaving now costs {self.exit_cost:,.0f} {self.symbol} ({self.exit_cost_rate:.0%} of what leaves)"
            if self.exit_cost_rate is not None
            else f"leaving now forgoes {self.exit_cost:,.0f} {self.symbol} of yield over {h} ({self.apy:.2%}/yr)"
        )
        if self.p_star >= 1:
            return f"{cost}, more than leaving first saves: stay even if the incident is certain"
        return (
            f"{cost}; it pays if the incident's probability over {h} is above {self.p_star:.2%} "
            f"({self.p_star_year:.1%}/yr)"
        )

    def to_json(self) -> dict:
        return asdict(self)


# --- pure


def breakeven(stay: float, leave: float, par: float, apy: float | None, days: float, rate: float | None = None):
    """D142–D143, pure: (cost of leaving now, p* over the horizon, p* per year). Leaving now costs the vault's net
    yield on what can leave, or `rate` × what leaves when a flat exit cost is given (D151: the brief's 11 % unwind); it
    saves stay − leave if the incident comes. p* = cost / saving; None when leaving saves nothing; ≥ 1 when the cost
    exceeds the saving even for a certain incident."""
    if apy is None and rate is None:
        return 0.0, None, None
    cost = par * rate if rate is not None else par * apy * days / 365
    saved = stay - leave
    if saved <= 0:
        return cost, None, None
    p = cost / saved
    return cost, p, (1 - (1 - p) ** (365 / days) if p < 1 else 1.0)


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
    """D130: every vault incident shock, as (kind, target, value, n):
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


def returned_liquidity(h: MarketHit, vault_assets: float, free: float) -> float:
    """D239, pure: when liquidators act, the debt they repay (what the seized collateral covers) is the market's free
    liquidity again, so the vault can withdraw more from it, up to what it still has there after its loss; nothing when
    nobody can liquidate (no exit route) or for a default (nothing is repaid). Asset units."""
    if h.event != "markdown" or h.liquidatable_debt <= 0 or h.exit_route == "none":
        return 0.0
    # the shock engine's figure is the debt liquidators repaid (D139); this module's is the liquidatable positions'
    # whole debt, of which the part their collateral does not cover is not repaid
    repaid = h.liquidatable_debt if h.source == "engine" else max(0.0, h.liquidatable_debt - h.bad_debt)
    now = min(vault_assets, free)
    after = min(max(0.0, vault_assets - h.vault_loss), free + repaid)
    return max(0.0, after - now)


def feed_bands(f: S.Fetcher, graph: dict | None, market_ids: list[str], block: int) -> dict[str, dict] | None:
    """D241 (GAPV2 G11): each market's feed with a fixed band (a Midas custom feed: below `minAnswer` it cannot report
    without new code) and the timelock above it, read through the admin surface at `block`; None when not readable
    (not in the recording)."""
    from . import admin as AD

    if graph is None or not market_ids:
        return {}
    try:
        aw = AD.AdminWatch(f, market_ids, block)
    except (S.CacheMiss, S.SourceError):
        return None
    oracles = {e["source"]: e["target"] for e in graph["edges"] if e["rel"] == "priced by"}
    out = {}
    for mid in market_ids:
        for e in graph["edges"]:
            c = aw.contracts.get(e["target"]) if e["rel"] == "reads" and e["source"] == oracles.get(mid) else None
            if c is not None and c.band:
                lo, hi, dec, ans = c.band
                tl = aw.timelock_over(c.address)
                out[mid] = {
                    "feed": c.symbol or c.address[:10],
                    "floor_fall": max(0.0, 1 - lo / ans),
                    "floor": lo / 10**dec,
                    "timelock_h": tl.timelock_delay / 3600 if tl and tl.timelock_delay else None,
                }
    return out


def live_exit(f: S.Fetcher, h: MarketHit, mp, price: int | None, info) -> None:
    """D213–D214: the hit's exit liquidity quoted live on KyberSwap at the size its liquidations seize (debt × LIF),
    in place of the registry's; the registry's stays when no quote is available."""
    if h.event != "markdown" or h.liquidatable_debt <= 0 or not price:
        return
    try:
        q = XL.ladder(f, mp.collateral_token, mp.loan_token, price, info.loan_decimals)
    except (S.CacheMiss, S.SourceError):
        h.exit_source = "registry" if h.exit_route else ""
        return
    size = h.liquidatable_debt * info.lif
    h.exit_route, h.exit_impact, h.exit_capacity = XL.at(q, size)
    h.exit_source = "KyberSwap"
    h.exit_text = XL.text(h.exit_route, h.exit_impact, h.exit_capacity, size, info.loan_symbol, "KyberSwap")


def exit_route(collateral: str) -> str | None:
    """D131: the collateral's exit liquidity on DEXs, from the registry (none, thin, deep), or None if not measured."""
    e = REGISTRY["exit_liquidity"]["tokens"].get(collateral.lower())
    return e["route"] if e else None


def borrower_default(
    positions: dict[str, tuple[int, int]], totals: tuple[int, int], price: int, recovery: float, n: int
) -> tuple[int, int, list[str]]:
    """D130, pure: the n largest borrowers stop repaying; their collateral is recovered at `recovery` of its oracle value.
    Returns (debt defaulted, bad debt Σ max(0, debt − collateral value × recovery), the borrowers), raw loan units."""
    tba, tbs = totals
    ranked = sorted(((bs * (tba + 1) // (tbs + 10**6), u, c) for u, (c, bs) in positions.items() if bs), reverse=True)[
        :n
    ]
    debt = sum(d for d, _, _ in ranked)
    bad = sum(max(0, d - int(c * price // 10**36 * recovery)) for d, _, c in ranked)
    return debt, bad, [u for _, u, _ in ranked]


def match_token(collateral: str, chain: list[str], symbols: dict[str, str], tok: str) -> tuple[str, str] | None:
    """D126, pure: does the shocked token `tok` (an address or a symbol, lower case) reach this collateral? Returns
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
    """D135, pure: does the shocked token reach this collateral through Pharos's off-chain backing? For the outermost
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
    """D136, pure: 'fxSAVE F 36' for the collateral or the first token of its path Pharos grades."""
    for t in [collateral] + chain:
        g = snap.grade(PH.resolve(snap, t, symbols.get(t)))
        if g:
            return f"{symbols.get(t, t[:10])} {g}"
    return None


def market_feeds(graph: dict, market_id: str) -> list[tuple[str, str, bool]]:
    """D157, pure: (feed label, freshness, stale) for each input of the market's oracle the graph has a freshness for."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    oracles = {e["target"] for e in graph["edges"] if e["source"] == market_id and e["rel"] == "priced by"}
    out = []
    for e in graph["edges"]:
        d = nodes.get(e["target"], {}).get("details", {})
        if e["rel"] == "reads" and e["source"] in oracles and d.get("freshness"):
            txt = d["freshness"] + (f"; {d['shared_text']}" if d.get("shared_text") else "")  # D215
            out.append((nodes[e["target"]]["label"], txt, bool(d.get("stale"))))
    return out


def engine_shocks(graph: dict, shocks: list[tuple]) -> list[EN.Shock]:
    """D139, pure: a markdown of token T by f, in the engine's terms: T's market price falls by f, and every
    constant-price input (the issuer's rate or NAV feed) of the oracles of markets taking T as collateral reads f low.
    A price-tracking input follows T's price through the graph's `tracks` edges by itself. D205: a linear-discount or
    fixed input does not read the markdown: its market keeps its oracle, liquidates nobody, and its lenders hold the
    shortfall (and the drain the gap opens). D240: an oracle that applies T's own ERC-4626 rate reads it low too."""
    nodes = {n["id"]: n for n in graph["nodes"]}
    out: dict[tuple, EN.Shock] = {}
    for kind, tok, fall, _ in normalise(shocks):
        if kind != "token":
            continue
        assets = [i for i, n in nodes.items() if n["kind"] == "Asset" and tok in (i, n["label"].lower())]
        for a in assets:
            out[(a, "price")] = EN.Shock(a, "price", -fall)
            markets = {e["source"] for e in graph["edges"] if e["rel"] == "takes as collateral" and e["target"] == a}
            oracles = {e["target"] for e in graph["edges"] if e["rel"] == "priced by" and e["source"] in markets}
            seen = set()  # oracles that read the markdown through one of their feeds
            for e in graph["edges"]:
                feed = nodes.get(e["target"], {})
                if (
                    e["rel"] == "reads"
                    and e["source"] in oracles
                    and feed.get("details", {}).get("oracle_class") == (OC.CONSTANT_PRICE)
                    and feed["details"].get("constant_kind") not in (OC.LINEAR_DISCOUNT, OC.FIXED)
                ):
                    out[(feed["id"], "misreport")] = EN.Shock(feed["id"], "reads-low", fall)
                    seen.add(e["source"])
            for e in graph["edges"]:
                # D240 (GAPV2 G19): an oracle that applies the token's own ERC-4626 rate (BASE_VAULT) reads a loss of
                # value the issuer books, as a rate oracle does; not twice when a feed already carries it
                if e["rel"] == "converts through" and e["target"] == a and e["source"] in oracles:
                    if e["source"] not in seen:
                        out[(e["source"], "misreport")] = EN.Shock(e["source"], "reads-low", fall)
    return list(out.values())


def apply_engine(graph: dict, shocks: list[tuple], hits: list[MarketHit], markets: dict, shares: dict, st, unit: int):
    """D139–D141: run the engine on the markdowns; on each market of the vault it moves, its liquidations and lenders'
    loss replace this module's (a hit it reaches only through a default or Pharos keeps this module's figures); a market
    of the vault only the engine reaches becomes a hit. Returns the sibling markets' lenders' losses."""
    sh = engine_shocks(graph, shocks)
    if not sh:
        return []
    res = EN.run(graph, sh)
    nodes = {n["id"]: n for n in graph["nodes"]}
    by_id = {h.market_id: h for h in hits}
    siblings = []
    for mid, d in res.markets().items():
        loss = float(d.get("lender_loss", 0.0))
        if mid not in markets:
            if loss > 0:
                siblings.append((mid, nodes[mid]["label"].removeprefix("Blue "), loss, d.get("loan_unit") or ""))
            continue
        h = by_id.get(mid)
        if h is None:
            if not loss and not d.get("liquidated_debt"):
                continue
            h = MarketHit(mid, markets[mid].label, 0.0, 0, 0.0, 0.0, 0.0, shares.get(mid, 0.0), 0.0, "", "")
            h.via, h.vault_exposure = "the dependency graph (shock engine)", st.markets[mid].vault_assets / unit
            hits.append(h)
        elif h.event == "default" or h.pharos_exposure:
            continue
        h.source = "engine"
        h.engine = (
            f"oracle × {d.get('oracle_factor', 1.0):.3f}, collateral market × {d.get('market_factor', 1.0):.3f} "
            f"after the liquidation sales; {d.get('liquidated_debt', 0.0):,.0f} liquidated, "
            f"{d.get('insolvent', 0.0):,.0f} left insolvent (more collateral than its market absorbs)"
        )
        h.liquidatable_debt = float(d.get("liquidated_debt", 0.0))
        h.bad_debt = loss
        h.vault_loss = loss * h.vault_share
    return siblings


def nav_timing(profile: scenario.OracleProfile | None) -> str:
    """D100: how fast a fall of the collateral's oracle price reaches the market."""
    if profile is None or profile.kind == OC.NOT_CLASSIFIED:
        return "unknown: the oracle could not be classified"
    if profile.kind == OC.CONSTANT_PRICE:
        k = profile.constant_kind
        if k in (OC.LINEAR_DISCOUNT, OC.FIXED):
            return (
                f"never: the oracle is a {k} and does not see the markdown, so nobody is liquidated; the loss stays "
                "with the lenders, hidden until the collateral is sold, and the gap invites a drain"
            )
        return (
            f"{OC.MOVES[k] if k else 'at once when the issuer publishes the new value'}: the oracle is the issuer's "
            "rate or NAV, so no market move announces it, and liquidations can start in the same block"
        )
    if profile.kind == OC.PRICE_TRACKING:
        return f"as the market falls, through the feed ({'TWAP ' + str(profile.twap_s) + ' s' if profile.twap_s else 'its next update'})"
    return "through a meta-oracle: " + scenario.time_to_impact(profile, {"issuer_depeg": 0.5}).text


def hidden_shortfall(positions: dict[str, tuple[int, int]], totals: tuple[int, int], price: int, drop: float) -> int:
    """D127, pure: Σ max(0, debt − collateral value × (1 − drop)), raw loan units: what lenders lose if the collateral
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
    """D99, pure: one market's liquidations and bad debt at the shocked oracle price, and the vault's part. D127: when
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
    share = liq.position / liq.total if liq.total else 0.0
    why = (
        f"the depositor holds {share:.0%} of the vault, so the loss falls on it either way"
        if share >= 0.5
        else f"only {par:,.0f} can leave, and the {stuck:,.0f} left behind carries the loss"
    )
    if gain <= 1:
        pen = (
            f"; the forceDeallocate penalty on the way out ({first.penalty / unit:,.0f}) makes leaving cost "
            f"{-gain:,.0f} more"
            if first.penalty and -gain > 1
            else ""
        )
        return stay, par, stuck, leave, "STAY", f"leaving first does not lower the loss: {why}{pen}"
    if gain >= REGISTRY["incident"]["exit_min_gain"] * stay:
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
        f"leaving first saves only {gain:,.0f} ({gain / stay:.1%} of the {stay:,.0f} loss): {why}; withdrawing what "
        f"can leave still cuts its exposure to a further cut by {par:,.0f}",
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
    graph: dict | None = None,
    horizon_days: float = 30.0,
    nexus: tuple[list[dict], list[dict]] | None = None,
    exit_cost_rate: float | None = None,
) -> VaultIncident:
    """Read the vault and every borrower of its markets at `block`, then apply the incident (D98). `token_shocks` is
    `parse_shocks`' list (token markdowns and borrower defaults, D130) or `parse_token_shocks`' pairs. `profile_all`
    reads every market's oracle, not only the hit ones, so a recording serves any later shock (D121). `pharos`, when
    given, adds grades, the off-chain backing a token shock also reaches, and common-mode groups (D133–D138). `graph`,
    the vault's dependency graph (graph.py's nodes and edges, with its `block`), runs the shock engine on the markdowns:
    its figures replace this module's on the markets it reaches, and it adds the sibling markets (D139–D141).
    `horizon_days` and the vault's yield give the breakeven probability; `nexus` adds cover prices (D142–D146)."""
    shocks = normalise(token_shocks)
    view = discover_vault(f, vault, block)
    dep = depositor.lower() if depositor else largest_depositor(f, vault, frozenset(ZM.POOLS))
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
    pexps: dict[str, float] = {}  # market → share of its collateral's backing the shocked token is (Pharos, D135)
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
    direct = [m for m in drops if m in risk.markets and drops[m] > 0 and not vias.get(m)]
    bands = feed_bands(f, graph, direct, block)  # D241: a feed whose floor holds the markdown back
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
            # D130: the defaulters leave the market's normal valuation; the others are valued as for a markdown
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
            # D131: nobody liquidates (no exit route): the lenders carry debt − collateral value, and wait
            h.no_liquidator_shortfall = (
                hidden_shortfall(positions, totals, price, d) / lu + (dbad / lu if who else 0.0)
            ) * h.vault_share
        b = (bands or {}).get(mid)
        if b and d > b["floor_fall"] and h.event == "markdown" and not h.via:
            # D241: the oracle can fall only to the feed's floor now; the rest waits for an upgrade of the feed
            now = market_hit(mid, risk.markets[mid], positions, totals, price, b["floor_fall"], h.vault_share, profile)
            lock = f" through a {b['timelock_h']:g} h timelock" if b["timelock_h"] else ""
            h.band = {
                **b,
                "now_liquidatable": now.liquidatable_debt,
                "now_bad_debt": now.bad_debt,
                "now_vault_loss": now.vault_loss,
                "held_back": d - b["floor_fall"],
            }
            h.timing = (
                f"the feed's floor ({b['feed']} {b['floor']:,.6g}) holds the oracle at −{b['floor_fall']:.1%} at its "
                f"next round; the rest, −{d - b['floor_fall']:.1%}, reaches it only after the feed is upgraded{lock}"
            )
        hits.append(h)

    for h in hits if graph is not None else []:
        fs = market_feeds(graph, h.market_id)
        h.feeds, h.stale_feed = [f"{lbl}: {txt}" for lbl, txt, _ in fs], any(s for *_, s in fs)
    engine_block, siblings = None, []
    if graph is not None and shocks:
        engine_block = graph.get("block")
        siblings = apply_engine(graph, shocks, hits, risk.markets, shares, st, unit)
    for h in hits:
        live_exit(f, h, params[h.market_id], st.markets[h.market_id].oracle_price, risk.markets[h.market_id])
        m = st.markets[h.market_id]
        h.returned = returned_liquidity(h, m.vault_assets / unit, m.liquidity / unit)  # after live_exit's route
    for h in hits:
        loss_raw += int(h.vault_loss * unit)
        if h.bad_debt > 0:
            exposure_raw += st.markets[h.market_id].vault_assets

    liq = EQ.liquidity(st)
    stay, par, stuck, leave, verdict, reason = decide(liq, loss_raw, exposure_raw, unit)
    apy = vault_apy(f, view.address)
    exit_cost, p_star, p_year = breakeven(stay, leave, par, apy, horizon_days, exit_cost_rate)
    if exit_cost_rate is not None and verdict == "EXIT" and stay - leave <= exit_cost:
        verdict, reason = (
            "STAY",
            (
                f"leaving first would save {stay - leave:,.0f}, but leaving costs {exit_cost:,.0f} "
                f"({exit_cost_rate:.0%} of the {par:,.0f} that leaves): staying is cheaper even if the incident is certain"
            ),
        )
    outside = []
    if nexus is not None and hits:
        tokens = [
            x
            for h in hits
            for x in [params[h.market_id].collateral_token] + chains.get(params[h.market_id].collateral_token, [])
        ]
        severity = max((v if k == "token" else 1 - v) for k, _, v, _ in shocks)
        outside = [NX.outside_line(c, severity) for c in NX.covers(*nexus, tokens)]
    notes = [
        "bad debt is written off only when the positions are liquidated; until then the share price stays at par, "
        "and those who leave first leave the loss to those who stay"
    ]
    if any(h.stale_feed for h in hits):
        notes.append(
            "a hit market's feed is stale: the price the incident starts from may already be out of date, and the "
            "issuer's next update can land the markdown at once"
        )
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
    if any(h.exit_source == "KyberSwap" and h.exit_route != "deep" for h in hits):
        notes.append(
            "exit liquidity is what the DEX aggregator routes; an issuer redemption, a vault share's withdrawal or "
            "Pendle's router may offer another exit, slower or gated"
        )
    unmeasured = sorted(
        {
            symbols.get(params[h.market_id].collateral_token, "?")
            for h in hits
            if h.exit_route is None and h.liquidatable_debt > 0
        }
    )
    if unmeasured:
        notes.append(
            f"exit liquidity not available for {', '.join(unmeasured)}: no KyberSwap quote recorded (run with "
            "--record) and none in the registry's exit_liquidity"
        )
    if st.liquidity_market and st.liquidity_market in {h.market_id for h in hits}:
        notes.append(
            "the hit market is the vault's liquidity market: plain withdrawals draw on its free liquidity only"
        )
    if engine_block is not None:
        notes.append(
            f"the markdowns ran through the shock engine on the vault's graph (block {engine_block:,}): "
            + (
                "its figures are used on the markets it reaches"
                if any(h.source == "engine" for h in hits)
                else "it reached no market of the vault"
            )
            + "; borrower defaults and Pharos-reached markets come from this module alone"
        )
        if siblings:
            top = sorted(siblings, key=lambda s: -s[2])[:3]
            notes.append(
                f"contagion beyond this vault: the same incident costs the lenders of {len(siblings)} sibling "
                "market(s) " + ", ".join(f"{lbl} {v:,.0f} {u}" for _, lbl, v, u in top)
            )
    elif any(k == "token" for k, *_ in shocks):
        notes.append(
            "shock engine: no graph of this vault recorded (graph --vault … --record): sibling markets not seen"
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
    zama_lines = []
    if ZM.entry(view.address):
        try:
            zs = ZM.read(f, view.address, block)
            zama_lines = ZM.exits(zs, any(h.oracle_class == OC.CONSTANT_PRICE and h.vault_loss > 0 for h in hits))
        except (S.CacheMiss, S.SourceError, TypeError):
            zama_lines = ["a Zama confidential vault: its batchers could not be read (record the vault again)"]
    inc = VaultIncident(
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
        engine_block,
        siblings,
        apy,
        horizon_days,
        exit_cost,
        p_star,
        p_year,
        outside,
        (liq.plain / unit, liq.forced / unit, liq.penalty),
        exit_cost_rate,
    )
    inc.zama = zama_lines
    inc.returned_liquidity = sum(h.returned for h in hits)
    return inc


def collateral_chains(
    f: S.Fetcher, tokens: set[str], block, depth: int = 4
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """D126: what each collateral wraps, level by level: a PT's Pendle underlying, an ERC-4626 share's asset()
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


def vault_apy(f: S.Fetcher, vault: str) -> float | None:
    """D142: the vault's average net APY, rewards included (Morpho API); None when it cannot be read."""
    try:
        d = S.morpho(f, "query($a:String!){ vaultV2ByAddress(address:$a, chainId:1){ avgNetApy } }", {"a": vault})
        return float(d["vaultV2ByAddress"]["avgNetApy"])
    except (S.SourceError, S.CacheMiss, KeyError, TypeError):
        return None


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
