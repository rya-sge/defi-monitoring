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

from . import clock, crosscheck, decide, discover, priors, scenario, simulate, vault_book, vault_incident
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

    incident = None
    if shocks:
        recovery = next((p.recovery for p in prs if p.event == "issuer_depeg"), 0.0)
        incident = scenario.assess(
            pos, shocks, recovery, quote, profile, quote_for=lambda q, fr: discover.partial_exit_quote(f, q, fr)
        )

    # a failed cross-check leads the reasons: the numbers below it are suspect
    bad = [c for c in checks if c.ok is False]
    if bad:
        dec.reasons.insert(0, "DATA CHECK FAILED — " + "; ".join(c.detail for c in bad))

    return AnalyzeResult(
        position=pos,
        priors=prs,
        simulation=sim,
        decision=dec,
        quote=quote,
        checks=checks,
        oracle_alt=alt,
        incident=incident,
    )


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


def nexus_prices(mode: str = "offline"):
    from . import nexus

    return nexus.load(_outside_fetcher("nexus", mode))


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
    return {"nodes": list(g.nodes.values()), "edges": g.edges, "block": block}


def incident(
    book: vault_book.Book, shocks: list[str], user: str | None = None, horizon: float = 30.0, mode: str = "offline"
) -> VaultIncidentResult:
    """A known incident on every vault of a book, added up (shared by `analyze --vault|--book` and the API).

    `shocks` in the CLI's syntax (`token=<collateral>:<fall>`, `borrower=<target>:<recovery>[:<n>]`). Raises
    ValueError (bad shocks), FileNotFoundError (a vault not recorded, offline), `sources.CacheMiss`, `SourceError`."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {', '.join(MODES)}")
    parsed = vault_incident.parse_shocks(shocks)
    if not parsed:
        raise ValueError(
            "a vault incident needs a shock: token=<collateral address or symbol>:<fall>, e.g. token=mGLOeuro:0.30, "
            "or borrower=<collateral, market id or all>:<recovery>[:<n>], e.g. borrower=mGLOeuro:0.5"
        )
    ph, nx = pharos_snapshot(mode), nexus_prices(mode)
    incidents = []
    for v in book.vaults:
        f, block, all_oracles = vault_source(v.address, mode)
        incidents.append(
            vault_incident.run(
                f,
                v.address,
                block,
                v.depositor or user,
                parsed,
                profile_all=all_oracles,
                pharos=ph,
                graph=vault_graph(v.address),
                horizon_days=horizon,
                nexus=nx,
            )
        )
    return VaultIncidentResult(book, incidents, vault_book.aggregate(book, parsed, incidents))
