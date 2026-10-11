"""One analyse, from a position to a verdict, with no I/O of its own beyond the fetcher.

This is the orchestration the `analyze` subcommand used to carry inline. It lives here so the
CLI and the HTTP API run the *same* sequence: discover, cross-check, price the layers, simulate,
decide, then re-run under the other oracle behaviour. Callers choose what to do with the result —
`report.write` to disk for the CLI, `report.to_dict` over the wire for the API.

Raises `sources.CacheMiss` (offline snapshot incomplete) and `sources.SourceError` (upstream
failure) for the caller to turn into an exit code or an HTTP status.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import clock, crosscheck, decide, discover, pendle_amm, priors, scenario, simulate, vault_book, vault_incident
from . import sources as S
from .decide import Decision
from .discover import Position
from .priors import Prior
from .scenario import IncidentResult
from .simulate import SimResult

REPLAY_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "replay"
DEMO_MARKET = "0x5613b170ded221c588b6e9637b910f49e5508680ceede207f44aa72e5c46cb05"
DEMO_USER = "0xdf81987465681D0515058fe0A47A3bD174012730"


@dataclass
class AnalyzeResult:
    position: Position
    priors: list[Prior]
    simulation: SimResult
    decision: Decision
    quote: dict
    checks: list[crosscheck.Check] = field(default_factory=list)
    oracle_alt: dict | None = None
    incident: IncidentResult | None = None
    discovery: dict = field(default_factory=dict)  # D199: the layers the position's recorded graph adds


def analyze(
    f: S.Fetcher,
    *,
    market: str | None = None,
    user: str | None = None,
    pendle_market: str | None = None,
    pt_amount: float | None = None,
    horizon: float = 30.0,
    paths: int = 20000,
    shocks: dict[str, float] | None = None,
    venue: dict | None = None,
) -> AnalyzeResult:
    """Analyse one position. With no market and no pendle_market, analyse the demo position.

    `shocks` (from `scenario.parse_shocks`) adds incident mode: a known incident's impact and verdict."""
    if market:
        pos = discover.discover_morpho_position(f, market, user)
    elif pendle_market:
        if pt_amount is None:
            raise ValueError("pendle_market needs pt_amount")
        pos = discover.discover_pt_holding(f, pendle_market, pt_amount)
    else:
        pos = discover.discover_morpho_position(f, DEMO_MARKET, DEMO_USER)

    # D96: the oracle mode from the oracle's structure when it decides, instead of the price inference
    oracle = next((n.split(":", 1)[1] for n, a in pos.graph.nodes(data=True) if a.get("kind") == "oracle"), None)
    profile = scenario.oracle_profile(f, oracle) if oracle else None
    decided = scenario.ex_ante_mode(profile, max(1.0, min(horizon, pos.days_to_maturity or horizon)))
    if decided:
        mode0, why = decided
        if mode0 != pos.oracle_mode or pos.oracle_ambiguous:
            was = pos.oracle_mode + (", ambiguous" if pos.oracle_ambiguous else "")
            pos.notes.append(f"Oracle mode {mode0}: {why} (the price inference said {was}).")
        pos.oracle_mode, pos.oracle_ambiguous = mode0, False
        pos.graph.nodes[f"oracle:{oracle}"]["mode"] = mode0

    checks = [crosscheck.second_rpc(f)]
    if pos.morpho_market:
        checks.append(
            crosscheck.morpho_position(
                f,
                pos.morpho_market,
                pos.borrower,
                pos.collateral_decimals,
                pos.loan_decimals,
                pos.collateral_units,
                pos.debt_raw,
            )
        )
    pos.notes += [c.line for c in checks]

    prs = priors.layer_priors(f, pos)
    horizon = max(1.0, min(horizon, pos.days_to_maturity or horizon))
    sim = simulate.run(pos, prs, horizon, n=paths)
    quote = discover.exit_quote(f, pos)
    depeg = next((p.mean_severity for p in prs if p.event == "issuer_depeg"), None)
    dec = decide.verdict(
        pos,
        sim,
        quote,
        depeg,
        resimulate=lambda q: simulate.run(q, prs, horizon, n=paths),
        quote_for=lambda q, fr: discover.partial_exit_quote(f, q, fr),
    )

    alt = None
    if pos.oracle_mode != "none":
        # the same position under the other oracle behaviour: how much the verdict rests on the inference
        other = copy.copy(pos)
        other.oracle_mode = "fundamental" if pos.oracle_mode == "market-tracking" else "market-tracking"
        s2 = simulate.run(other, prs, horizon, n=paths)
        d2 = decide.verdict(other, s2, quote, depeg)
        alt = {
            "oracle_mode": other.oracle_mode,
            "verdict": d2.verdict,
            "expected_loss_usd": s2.expected_loss_usd,
            "cvar99_usd": s2.cvar99_usd,
            "p_liquidation": s2.p_liquidation,
        }
        same = d2.verdict == dec.verdict
        dec.reasons.append(
            f"Oracle sensitivity{' (inference ambiguous)' if pos.oracle_ambiguous else ''}: if the oracle were "
            f"{other.oracle_mode}, expected loss ${s2.expected_loss_usd:,.0f} (vs ${sim.expected_loss_usd:,.0f}), "
            f"P(liquidation) {s2.p_liquidation:.2%} (vs {sim.p_liquidation:.2%}), verdict {d2.verdict}"
            + (" — the same." if same else " — the verdict depends on the oracle; check its source before acting.")
        )
    if pos.days_to_maturity and pos.days_to_maturity > horizon:
        # D196 (K12): a PT redeems at par at maturity: holding it there against leaving now, over the whole period
        days = pos.days_to_maturity
        sm = simulate.run(pos, prs, days, n=paths)
        carry_m, exit_c = decide.carry_usd(pos, days), decide.exit_cost_usd(pos, quote)
        cheaper = sm.expected_loss_usd < carry_m + exit_c
        dec.reasons.append(
            f"Held to maturity ({days:.0f} days), the PT redeems at par: expected loss ${sm.expected_loss_usd:,.0f} "
            f"against ${carry_m:,.0f} of carry, while leaving now costs ${exit_c:,.0f} once"
            + (" — holding to maturity is the cheaper path." if cheaper else " — leaving now is the cheaper path.")
        )

    depth = position_depth(pos, profile)
    incident = None
    if shocks:
        # D220: a venue's loss of backing is permanent: nothing of the markdown is recovered
        recovery = 0.0 if venue else next((p.recovery for p in prs if p.event == "issuer_depeg"), 0.0)
        moved = None
        if "pool_move" in shocks:
            shocks, moved = pool_move_shocks(f, pos, shocks)
        incident = scenario.assess(
            pos,
            shocks,
            recovery,
            quote,
            profile,
            quote_for=lambda q, fr: discover.partial_exit_quote(f, q, fr),
            horizon_days=horizon,
            stressed=lambda drop, now: stressed_exit(f, pos, depth.get("market_curve"), drop, now),
        )
        if moved:
            incident.pool_move = moved
            incident.notes.insert(0, moved["text"])
        if venue:
            incident.notes.insert(0, venue["text"])

    # a failed cross-check leads the reasons: the numbers below it are suspect
    bad = [c for c in checks if c.ok is False]
    if bad:
        dec.reasons.insert(0, "DATA CHECK FAILED — " + "; ".join(c.detail for c in bad))

    if incident and depth.get("siblings"):
        # D202: the same incident reaches the markets that sell the same collateral or read the same price
        s = depth["siblings"][:3]
        incident.notes.append(
            f"{len(depth['siblings'])} sibling market(s) take the same collateral or read the same price: their "
            f"liquidations at a {depth['sibling_fall']:.0%} fall ("
            + ", ".join(f"{x['label']} {x['liquidatable_at_fall']:,.0f} {x['unit']}" for x in s)
            + ") sell into the same market and can deepen the fall"
        )
    return AnalyzeResult(
        position=pos,
        priors=prs,
        simulation=sim,
        decision=dec,
        quote=quote,
        checks=checks,
        oracle_alt=alt,
        incident=incident,
        discovery=depth,
    )


def stressed_exit(f: S.Fetcher, pos, curve, drop: float, cost_now: float) -> dict | None:
    """D206: the exit cost after the incident's own liquidations sell first: what the market's other borrowers are
    liquidated for at the incident's oracle fall (the borrower's recorded graph), then real Pendle quotes (the
    aggregator into the loan token, as `discover.exit_quote`) for the position's sale on top of theirs. None when the
    incident liquidates no one else, or the graph is not recorded."""
    if not curve or not pos.pendle_market or not pos.collateral_units:
        return None
    ahead = round(scenario.sold_ahead(curve, drop, pos.liquidation_drop, pos.debt_usd, pos.lltv), -3)
    if ahead <= 0:
        return None
    x = round(pos.collateral_usd, -3)
    small = min(10_000.0, round(x / 100, -3) or 1_000.0)
    sizes = sorted({small, x, ahead, *(round(ahead + k * x, -3) for k in (0.1, 0.25, 0.5, 0.75)), ahead + x})
    try:
        ladder, refused = discover.quote_ladder(
            f,
            pos.pendle_market,
            pos.collateral_address,
            pos.loan_address or pos.underlying_address,
            pos.collateral_decimals,
            pos.collateral_usd / pos.collateral_units,
            True,
            sizes,
        )
    except S.CacheMiss:
        return None
    return scenario.stressed_exit(cost_now, dict(ladder), small, ahead, x, refused)


def pool_move_shocks(f: S.Fetcher, pos, shocks: dict[str, float]) -> tuple[dict[str, float], dict]:
    """D204, D211: a sale into the PT's Pendle pool, priced by the pool's math on its state at the position's block
    (`pendle_amm`; recorded through the archive route), turned into the implied-yield rise the `pt_yield` channel
    prices."""
    if not pos.pendle_market or not pos.amm_liquidity_usd:
        raise ValueError("pool_move needs a Pendle PT position with a known pool liquidity")
    block = int(S.rpc(f, "eth_blockNumber", []), 16)
    rise, moved = scenario.pool_move(pos, pendle_amm.read(f, pos.pendle_market, block), shocks["pool_move"])
    rest = {k: v for k, v in shocks.items() if k != "pool_move"}
    rest["pt_yield"] = rest.get("pt_yield", 0.0) + rise
    moved["implied_yield_rise"] = rise
    return rest, moved


def position_share(pos, market: dict) -> list[str]:
    """D217: the position's share of its market (collateral and debt, from the borrower's recorded graph) and the PT the
    market holds as collateral against its Pendle pool's PT reserves (the pool at the snapshot's block): how much of
    the market leaves if the position does, and how many times the pool's depth the market's liquidations would sell."""
    out = []
    coll, debt = float(market.get("collateral_of_borrowers") or 0), float(market.get("total_borrow") or 0)
    if coll and debt and pos.collateral_units:
        out.append(
            f"the position is {pos.collateral_units / coll:.0%} of its market's collateral and "
            f"{pos.debt_usd / debt:.0%} of its debt"
        )
    if coll and pos.pendle_market:
        try:
            f = S.Fetcher("offline")
            pool = pendle_amm.read(f, pos.pendle_market, int(S.rpc(f, "eth_blockNumber", []), 16))
        except S.CacheMiss:
            return out
        out.append(
            f"the market holds {coll:,.0f} PT as collateral, {coll / pool.total_pt:.1f}× the PT in its Pendle pool "
            f"({pool.total_pt:,.0f}); the pool accepts at most {pendle_amm.max_sale(pool):,.0f} more"
        )
    return out


def position_depth(pos, profile=None) -> dict:
    """D199–D202: the borrow position's extra layers, from its borrower's recorded graph (`graph --user <borrower>
    --record`) and its market's admin surface read at that block; {} when the graph is not recorded. Offline only:
    the graph is a recording, so the layers carry its block and date."""
    from . import admin as AD
    from . import depth as DP
    from . import graph as GR

    if not pos.morpho_market or not pos.borrower:
        return {}
    rdir = REPLAY_DIR / f"graph-{pos.borrower.lower()}"
    if not (rdir / "meta.json").exists():
        return {}
    as_of = clock.as_of()
    try:
        g, block, *_ = GR.load([], [], True, "replay", rdir)
    except S.CacheMiss:
        return {}
    finally:
        clock.set_as_of(as_of)
    ph, protocols = pharos_snapshot("offline"), llama_protocols("offline")
    if ph:
        GR.annotate_pharos(g, ph)
    if protocols:
        GR.annotate_tvl(g, protocols)
    GR.annotate_shared(g)
    GR.annotate_supply(g, S.Fetcher("offline", rdir), block)
    eth = ethena_snapshot("offline")
    try:
        aw = AD.AdminWatch(S.Fetcher("offline", rdir), [pos.morpho_market], block)
        admin = DP.admin_rows(aw.contracts, aw.timelock_over)
    except S.CacheMiss:
        admin = []
    tokens = [x.lower() for x in (pos.collateral_address, pos.underlying_address) if x]
    gd = {"nodes": list(g.nodes.values()), "edges": g.edges}
    d = DP.position_depth(gd, pos.morpho_market, tokens, admin)
    if d:
        d["position_share"] = position_share(pos, g.nodes.get(pos.morpho_market, {}).get("details", {}))
        on_usde = any(b["backed_by"] == "USDe" for b in d["backing"]) or any("usde" in t for t in d["grades"].keys())
        d["venues"] = eth.lines() if eth and on_usde else []  # D221
    if d and profile is not None:
        d["oracle_profile"] = DP.profile_text(profile)  # D200: what the graph cannot see inside a meta-oracle
    if d:
        d["graph_block"] = block
        d["lines"] = DP.lines(d)
    return d


# --- a known incident on a vault or a book of vaults (plans 2026-10-11-vault-incident … 2026-10-11-breakeven)

MODES = ("offline", "live", "refresh", "record")


@dataclass
class VaultIncidentResult:
    book: vault_book.Book
    incidents: list[vault_incident.VaultIncident]
    result: vault_book.BookIncident


def vault_source(vault: str, mode: str = "offline") -> tuple[S.Fetcher, int, bool]:
    """D121: where a vault is read. `record`: live at the head, every response saved under incident-<vault>/;
    `live` and `refresh`: live, nothing saved; `offline`: the incident recording if there is one, else the watch
    recording at its state block. Returns (fetcher, block, read every oracle). FileNotFoundError without a recording."""
    w = discover.REGISTRY["watch"]
    if mode == "record":
        rdir = REPLAY_DIR / f"incident-{vault}"
        f = S.Fetcher("refresh", rdir)
        block = int(S.rpc(S.Fetcher("direct"), "eth_blockNumber", []), 16) - w["confirmations"]
        (rdir / "meta.json").write_text(json.dumps({"vault": vault, "block": block}, indent=1))
        return f, block, True
    if mode in ("live", "refresh"):
        f = S.Fetcher("direct")
        return f, int(S.rpc(f, "eth_blockNumber", []), 16) - w["confirmations"], False
    inc_dir, watch_dir = REPLAY_DIR / f"incident-{vault}", REPLAY_DIR / vault
    if (inc_dir / "meta.json").exists():
        return S.Fetcher("offline", inc_dir), json.loads((inc_dir / "meta.json").read_text())["block"], False
    if (watch_dir / "start.json").exists():
        head = json.loads((watch_dir / "start.json").read_text())["head"]
        return S.Fetcher("offline", watch_dir), head - w["confirmations"] - w["state_window_blocks"], False
    raise FileNotFoundError(
        f"no recording for {vault}: record it with analyze --vault {vault} --record --shock …, or run live"
    )


def _outside_fetcher(name: str, mode: str) -> S.Fetcher:
    """D138, D145: an optional outside provider's recording under fixtures/replay/<name>/: offline by default;
    `record` and `refresh` re-read and save it; `live` reads it without saving."""
    if mode == "live":
        return S.Fetcher("direct")
    return S.Fetcher("refresh" if mode in ("record", "refresh") else "offline", REPLAY_DIR / name)


def pharos_snapshot(mode: str = "offline"):
    from . import pharos

    return pharos.load(_outside_fetcher("pharos", mode))


def ethena_snapshot(mode: str = "offline"):
    from . import ethena

    return ethena.load(_outside_fetcher("ethena", mode))


def sky_snapshot(mode: str = "offline"):
    """D223: Sky's core at the recorded block (fixtures/replay/sky/meta.json) offline; at the head, saved, in `record`
    and `refresh`; at the head, not saved, `live`."""
    from . import sky

    rdir = REPLAY_DIR / "sky"
    if mode in ("record", "refresh"):
        f = S.Fetcher("refresh", rdir)
        block = int(S.rpc(S.Fetcher("direct"), "eth_blockNumber", []), 16) - 2
        rdir.mkdir(parents=True, exist_ok=True)
        (rdir / "meta.json").write_text(json.dumps({"block": block}, indent=1))
    elif mode == "live":
        f = S.Fetcher("direct")
        block = int(S.rpc(f, "eth_blockNumber", []), 16) - 2
    else:
        if not (rdir / "meta.json").exists():
            return None
        f, block = S.Fetcher("offline", rdir), json.loads((rdir / "meta.json").read_text())["block"]
    return sky.load(f, block)


def incident_words(info: dict) -> str:
    """D227: a venue or Sky incident in a few words, with the markdown it becomes."""
    if info.get("words") and not info["losses"]:
        return info["words"]
    parts = []
    for x in info["losses"]:
        share = x["lost_usd"] / x["exposed_usd"] if x["exposed_usd"] else 0.0
        if "venue" in x:
            parts.append(f"{x['venue']} loses {share:.0%} of USDe's backing there")
        else:
            parts.append(f"Sky's {x['source']} loses {share:.0%}")
    tokens = "USDe and sUSDe" if any("venue" in x for x in info["losses"]) else "USDS, DAI and sUSDS"
    return f"{'; '.join(parts)} → {tokens} −{info['markdown']:.2%}"


def block_snapshot(name: str, mode: str = "offline"):
    """D246, D248, D250: an issuer's or a bridge's state read on-chain at one block (`infinifi`, `fx`, `bridge`), recorded under fixtures/replay/<name>/
    with its block offline; at the head, saved, in `record` and `refresh`; at the head, not saved, `live`."""
    import importlib

    mod = importlib.import_module(f"riskdep.{name}")
    rdir = REPLAY_DIR / name
    if mode in ("record", "refresh"):
        block = int(S.rpc(S.Fetcher("direct"), "eth_blockNumber", []), 16) - 2
        rdir.mkdir(parents=True, exist_ok=True)
        (rdir / "meta.json").write_text(json.dumps({"block": block}, indent=1))
        return mod.load(S.Fetcher("refresh", rdir), block)
    if mode == "live":
        f = S.Fetcher("direct")
        return mod.load(f, int(S.rpc(f, "eth_blockNumber", []), 16) - 2)
    if not (rdir / "meta.json").exists():
        return None
    return mod.load(S.Fetcher("offline", rdir), json.loads((rdir / "meta.json").read_text())["block"])


def issuer_shocks(items: list[str] | None, mode: str, target: str) -> tuple[list[str], list[str]]:
    """D247, D249, D251: `infinifi=<share of its backing>` through infiniFi's loss waterfall, `fx=<fxusd|usdc|aave>:<loss>`
    through fxSAVE's NAV components, `bridge=<token>[:<hours>]` through the bridge's rate limits, each as the `token=`
    markdowns they cause, with their words."""
    from . import bridge as BR
    from . import fx as FX
    from . import infinifi as IF

    rest, bridges = BR.parse(items)
    rest, found = FX.parse(rest)
    if not found and not bridges:
        return rest, []
    if target == "position":
        raise ValueError(
            "infinifi=, fx= and bridge= apply with --vault or --book: the analyze position is not on siUSD, fxSAVE, "
            "PST or etrUSD"
        )
    words = []
    if bridges:
        # D251: the unbacked mint a bridge allows within the stop time, as the token's dilution
        routes = block_snapshot("bridge", mode)
        if routes is None:
            raise ValueError("a bridge incident needs its lanes: no recording under fixtures/replay/bridge/")
        for sym, hours in bridges:
            m = BR.markdown(routes[sym], hours)
            words.append(m["text"])
            if m["markdown"] > 0:
                # D252: the issuer refuses the forged tokens, so holders stay whole and the markets they borrow from lose
                minted = m["minted"] if m["minted"] is not None else 1e18
                rest.append(f"drain={sym}:{minted}:{BR.K['tokens'][sym]['decimals']}")
    for name, comp, v in found:
        snap = block_snapshot(name, mode)
        if snap is None:
            raise ValueError(f"an {name} incident needs its state: no recording under fixtures/replay/{name}/")
        if name == "infinifi":
            w = IF.waterfall(snap, v * snap.backing_usd)
            words.append(IF.describe(snap, v, w))
            if w["siusd_markdown"] > 0:
                rest.append(f"token=siUSD:{min(0.99, w['siusd_markdown'])}")
            if w["iusd_markdown"] > 0:
                rest.append(f"token=iUSD:{min(0.99, w['iusd_markdown'])}")
        else:
            m = FX.markdown(snap, comp, v)
            words.append(m["text"])
            if m["markdown"] > 0:
                rest.append(f"token=fxSAVE:{min(0.99, m['markdown'])}")
    if not any(x.startswith("token=") for x in rest) and not any(
        x.split("=")[0] in ("sky", "venue", "borrower", "drain") for x in rest
    ):
        raise ValueError("; ".join(words) + ": nothing reaches the markets")
    return rest, words


def venue_shocks(items: list[str] | None, mode: str, target: str) -> tuple[list[str], dict | None]:
    """D220: `venue=<exchange>:<loss>` replaced by the USDe markdown it leaves once the reserve fund absorbed what it
    can: `issuer_depeg=<markdown>` for `analyze` (`target` "position"), `token=` markdowns of USDe and sUSDe for a
    vault or a book. Returns (the shocks, the venue loss or None). Raises ValueError (unknown venue, no Ethena data)."""
    from . import ethena as ET
    from . import sky as SK

    items, issuer_words = issuer_shocks(items, mode, target)
    rest, skies = SK.parse_sky(items)
    if skies:
        # D226: a loss on one of Sky's sources, after its surplus and its debt auctions, marks USDS, DAI and sUSDS down
        if target == "position":
            raise ValueError("sky=<source>:<loss> applies with --vault or --book: the analyze position is not on USDS")
        snap = sky_snapshot(mode)
        if snap is None:
            raise ValueError("a Sky incident needs Sky's core: no recording under fixtures/replay/sky/")
        losses = [SK.sky_loss(snap, s, v) for s, v in skies]
        m = min(0.99, sum(x["markdown"] for x in losses))
        info = {"losses": losses, "markdown": m, "text": "; ".join(x["text"] for x in losses)}
        if m <= 0:
            raise ValueError(info["text"])
        rest += [f"token=USDS:{m}", f"token=sUSDS:{m}", f"token=DAI:{m}"]
        items = rest
        sky_info = info
    else:
        sky_info = None
    rest, venues = ET.parse_venue(items)
    if not venues:
        if issuer_words:
            words = "; ".join(issuer_words)
            sky_info = (
                {**sky_info, "text": f"{sky_info['text']}; {words}"}
                if sky_info
                else {"losses": [], "markdown": 0.0, "text": words, "words": words}
            )
        return list(items or []), sky_info
    snap = ethena_snapshot(mode)
    if snap is None:
        raise ValueError("a venue incident needs Ethena's backing: no recording under fixtures/replay/ethena/")
    losses = [ET.venue_loss(snap, v, loss) for v, loss in venues]
    m = min(0.99, sum(x["markdown"] for x in losses))
    info = {"losses": losses, "markdown": m, "text": "; ".join(x["text"] for x in losses)}
    if target == "position":
        rest = [x for x in rest if not x.startswith("issuer_depeg=")] + [f"issuer_depeg={m}"]
    elif m > 0:
        rest += [f"token=USDe:{m}", f"token=sUSDe:{m}"]
    else:
        raise ValueError(info["text"])
    if sky_info:
        info["text"] = sky_info["text"] + "; " + info["text"]
    return rest, info


def nexus_prices(mode: str = "offline"):
    from . import nexus

    return nexus.load(_outside_fetcher("nexus", mode))


def llama_protocols(mode: str = "offline") -> list[dict] | None:
    """D158: DefiLlama's protocol list: the snapshot's copy offline (its as-of date), read live otherwise and not saved."""
    try:
        return S.llama_protocols(S.Fetcher("offline") if mode == "offline" else S.Fetcher("direct"))
    except (S.CacheMiss, S.SourceError):
        return None


def vault_graph(vault: str) -> dict | None:
    """D139: the vault's recorded dependency graph (graph --vault … --record), for the shock engine; None without one.
    Loading a replay moves the clock to the recording's date, so the clock is put back."""
    from . import graph as GR

    rdir = REPLAY_DIR / f"graph-{vault.lower()}"
    if not (rdir / "meta.json").exists():
        return None
    as_of = clock.as_of()
    try:
        g, block, *_ = GR.load([], [], True, "replay", rdir)
    except S.CacheMiss:
        return None
    finally:
        clock.set_as_of(as_of)
    GR.annotate_shared(g)  # D215: a hit's feed read by other markets too
    GR.annotate_roles(g, S.Fetcher("offline", rdir), block)  # D245: what holds each role
    return {"nodes": list(g.nodes.values()), "edges": g.edges, "block": block}


def incident(
    book: vault_book.Book,
    shocks: list[str],
    user: str | None = None,
    horizon: float = 30.0,
    mode: str = "offline",
    exit_cost: float | None = None,
    conditional: bool = False,
) -> VaultIncidentResult:
    """A known incident on every vault of a book, added up (shared by `analyze --vault|--book` and the API).

    `shocks` in the CLI's syntax (`token=<collateral>:<fall>`, `borrower=<target>:<recovery>[:<n>]`). `exit_cost`, a
    share of what leaves, replaces the yield given up as the cost of leaving (the brief's 11 % unwind). `conditional`
    adds the distribution of the loss of staying given the incident, from runs at multiples of the fall (D165–D168).
    Raises ValueError (bad shocks), FileNotFoundError (a vault not recorded, offline), `sources.CacheMiss`,
    `SourceError`."""
    if exit_cost is not None and not 0 <= exit_cost < 1:
        raise ValueError("exit_cost is a share of what leaves, between 0 and 1 (0.11 for 11 %)")
    if mode not in MODES:
        raise ValueError(f"mode must be one of {', '.join(MODES)}")
    shocks, venue = venue_shocks(shocks, mode, "vault")
    parsed = vault_incident.parse_shocks(shocks)
    if not parsed:
        raise ValueError(
            "a vault incident needs a shock: token=<collateral address or symbol>:<fall>, e.g. token=mGLOeuro:0.30, "
            "or borrower=<collateral, market id or all>:<recovery>[:<n>], e.g. borrower=mGLOeuro:0.5"
        )
    if conditional and not any(k == "token" for k, *_ in parsed):
        raise ValueError("the conditional distribution draws the size of a markdown: it needs a token=… shock")
    ph, nx = pharos_snapshot(mode), nexus_prices(mode)
    sources = [(v, *vault_source(v.address, mode), vault_graph(v.address)) for v in book.vaults if v.kind == "vault"]

    def run_all(scaled):
        return [
            vault_incident.run(
                f,
                v.address,
                block,
                v.depositor or user,
                scaled,
                profile_all=all_oracles,
                pharos=ph,
                graph=g,
                horizon_days=horizon,
                nexus=nx,
                exit_cost_rate=exit_cost,
            )
            for v, f, block, all_oracles, g in sources
        ]

    incidents = run_all(parsed)
    borrows, names = [], {}
    pockets = [v for v in book.vaults if v.kind in ("borrow", "pt")]

    def run_borrows(scaled):
        return [borrow_pocket(v, scaled, book.weighting, horizon, mode, exit_cost, venue)[0] for v in pockets]

    for v in pockets:
        ln, n = borrow_pocket(v, parsed, book.weighting, horizon, mode, exit_cost, venue)
        borrows.append(ln)
        names.update(n)
    result = vault_book.aggregate(book, parsed, incidents, borrows, names)
    if venue:
        result.notes.insert(0, venue["text"])
        for inc in incidents:
            inc.notes.insert(0, venue["text"])
    if conditional:
        conditional_distribution(book, parsed, incidents, result, run_all, borrows, run_borrows)
    # D227, after the draw it reports; a venue or Sky incident is named by what it is, with the markdown it becomes
    event = incident_words(venue) if venue else None
    result.value_at_risk = vault_book.value_at_risk(result, incidents, event)
    return VaultIncidentResult(book, incidents, result)


def after_incident(
    vault: str,
    since: int,
    at: int | None,
    shocks: list[str],
    user: str | None = None,
    mode: str = "offline",
    exit_cost: float | None = None,
    horizon: float = 30.0,
):
    """D230: a vault after an incident that began at block `since`: landed, unrealised, pending, and the verdict on
    what is still at risk (`after.run`). Offline from `fixtures/replay/after-<vault>-<since>-<at>/`, or, when `at` is
    `since`, from the vault's incident recording at that block; `record` reads through the archive route and saves;
    `live` reads now. Raises ValueError (bad shocks), FileNotFoundError (no recording), `sources.CacheMiss`."""
    from . import after

    shocks, _ = venue_shocks(shocks, mode, "vault")
    parsed = vault_incident.parse_shocks(shocks)
    if any(k != "token" for k, *_ in parsed):
        raise ValueError("after an incident, give the markdown as token=<collateral>:<fall> (a default has no price)")
    v = vault.lower()
    if mode == "offline":
        inc = REPLAY_DIR / f"incident-{v}"
        if at is None or at == since:
            if not (inc / "meta.json").exists():
                raise FileNotFoundError(f"no recording of {vault}: record it with --since {since} --record")
            block = json.loads((inc / "meta.json").read_text())["block"]
            if since != block:
                raise FileNotFoundError(
                    f"no recording of {vault} at block {since} (its incident recording is at {block})"
                )
            return after.run(S.Fetcher("offline", inc), v, since, since, user, parsed, exit_cost, horizon)
        rdir = REPLAY_DIR / f"after-{v}-{since}-{at}"
        if not rdir.exists():
            raise FileNotFoundError(f"no recording in {rdir.name}: run once with --record")
        return after.run(S.Fetcher("offline", rdir), v, since, at, user, parsed, exit_cost, horizon)
    direct = S.Fetcher("direct")
    at = at or int(S.rpc(direct, "eth_blockNumber", []), 16) - discover.REGISTRY["watch"]["confirmations"]
    f = S.Fetcher("refresh", REPLAY_DIR / f"after-{v}-{since}-{at}") if mode == "record" else direct
    with S.routed_rpc(S.archive_url()):  # the block `since` is past what the free RPCs serve
        return after.run(f, v, since, at, user, parsed, exit_cost, horizon)


def borrow_pocket(v, parsed, weighting: str, horizon: float, mode: str, exit_cost: float | None, venue=None):
    """D177–D178: a Morpho Blue borrow in a book (the brief's PT loop), or D222 a PT held without a borrow (`kind`
    "pt": its Pendle market, sized to the pocket's amount at the PT's price). A token shock that names its collateral
    or the collateral's underlying is, for the position, a loss of backing every oracle sees (`issuer_hack`); the
    incident module of `analyze --shock` gives its loss and its exit cost. Offline from the analyze snapshot."""
    f = S.Fetcher("offline") if mode == "offline" else S.Fetcher("direct")
    as_of = clock.as_of()
    if mode == "offline":
        clock.set_as_of(json.loads((S.SNAPSHOT_DIR / "as_of.json").read_text())["as_of"])
    try:
        if v.kind == "pt":
            price = discover.discover_pt_holding(f, v.address, 1.0).pt_price_usd
            units = v.amount / price if price else 0.0
            pos = discover.discover_pt_holding(f, v.address, units)
            where = {"pendle_market": v.address, "pt_amount": units}
        else:
            pos = discover.discover_morpho_position(f, v.address, v.depositor)
            where = {"market": v.address, "user": v.depositor}
        names = {
            x.lower()
            for x in (pos.collateral_symbol, pos.collateral_address, pos.underlying_symbol, pos.underlying_address)
            if x
        }
        fall = max((s for k, t, s, _ in parsed if k == "token" and t in names), default=0.0)
        label = v.label or pos.label
        shown = {
            t: (
                pos.underlying_symbol
                if t in {(pos.underlying_symbol or "").lower(), pos.underlying_address}
                else pos.collateral_symbol
            )
            for k, t, _, _ in parsed
            if k == "token" and t in names
        }
        if not fall:
            line = vault_book.borrow_line(label, weighting, v.amount, pos.equity_usd, 0.0, 0.0, None, horizon, False)
            return line, shown
        # D220: a venue's loss of USDe backing is a depeg the oracle's class decides on, as in `analyze`
        event = "issuer_depeg" if venue else "issuer_hack"
        res = analyze(f, **where, horizon=horizon, paths=2000, shocks={event: fall}, venue=venue)
        inc = res.incident
        line = vault_book.borrow_line(
            label, weighting, v.amount, pos.equity_usd, inc.loss_usd, inc.exit_cost_usd, exit_cost, horizon, True
        )
        return line, shown
    finally:
        clock.set_as_of(as_of)


def conditional_distribution(book, parsed, incidents, result, run_all, borrows=(), run_borrows=None) -> None:
    """D165–D168: run the incident at each multiple of `conditional.grid`, build each vault's loss curve in its
    depositor's terms (the book's pocket when it has one), and draw the distribution for each vault and the book.
    D203: a borrow pocket hit by the incident gets its curve the same way, from `borrow_pocket` at each multiple:
    leaving now avoids the loss and costs the exit; no liquidator branch, the borrower's own loss is the position's."""
    from dataclasses import asdict

    from . import conditional as CD

    grid = [m for m in CD.C["grid"] if m != 1.0]
    runs, bruns = {1.0: incidents}, {1.0: list(borrows)}
    hit_borrows = any(ln.hit_markets for ln in borrows)
    for m in grid:
        scaled = [(k, t, min(0.99, v * m), n) if k == "token" else (k, t, v, n) for k, t, v, n in parsed]
        runs[m] = run_all(scaled)
        if hit_borrows:
            bruns[m] = run_borrows(scaled)
    mults = [0.0] + sorted(runs)
    amounts = {v.address: v.amount for v in book.vaults}
    curves = []
    for i, inc in enumerate(incidents):
        stay, leave, ratio = [0.0], [0.0], [1.0]
        for m in mults[1:]:
            x = runs[m][i]
            usd = x.asset_usd or 1.0
            if book.weighting == "pocket":
                ln = vault_book.line(x, None, "pocket", amounts.get(x.vault))
                s, lv = ln.loss_usd, ln.loss_usd - ln.saved_usd
            else:
                s, lv = x.loss_if_stay * usd, x.loss_if_exit_first * usd
            noliq = sum(
                h.no_liquidator_shortfall if h.event == "markdown" and h.liquidatable_debt > 0 else h.vault_loss
                for h in x.hits
            )
            stay.append(s)
            leave.append(lv)
            ratio.append(noliq / x.vault_loss if x.vault_loss > 0 else 1.0)
        line = next(ln for ln in result.lines if ln.vault == inc.vault)
        cost = line.exit_cost_usd if book.weighting == "pocket" else inc.exit_cost * (inc.asset_usd or 1.0)
        liquidatable = [h.exit_route for h in inc.hits if h.liquidatable_debt > 0]
        p_noliq = CD.C["no_liquidator_prob"][CD.worst_route(liquidatable)] if liquidatable else 0.0
        curves.append(CD.Curve(line.name, mults, stay, leave, ratio, cost, p_noliq))
    fall = max(v for k, _, v, _ in parsed if k == "token")
    for inc, c in zip(incidents, curves):
        if inc.hits:
            d = CD.simulate([c], fall)
            inc.conditional = {**asdict(d), "text": d.text()}
    hit = [c for inc, c in zip(incidents, curves) if inc.hits]
    for i, ln in enumerate(borrows):
        if not ln.hit_markets:
            continue
        c = CD.Curve(
            ln.name,
            mults,
            [0.0] + [bruns[m][i].loss_usd for m in mults[1:]],
            [0.0] * len(mults),
            [1.0] * len(mults),
            ln.exit_cost_usd,
            0.0,
        )
        hit.append(c)
        d = CD.simulate([c], fall)
        result.notes.append(f"{ln.name}, given the incident: {d.text()}")
    if hit:
        d = CD.simulate(hit, fall)
        result.conditional = {**asdict(d), "text": d.text()}
