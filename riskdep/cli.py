"""python -m riskdep analyze ..."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

from . import clock, crosscheck, decide, discover, priors, report, scenario, simulate, vault_incident
from . import sources as S

# D14: largest borrower of Morpho market PT-sUSDE-26NOV2026 / USDC, cached in fixtures/snapshot.
DEMO_MARKET = "0x5613b170ded221c588b6e9637b910f49e5508680ceede207f44aa72e5c46cb05"
DEMO_USER = "0xdf81987465681D0515058fe0A47A3bD174012730"
DEMO_VAULT = "0x6dc58a0fdfc8d694e571dc59b9a52eeea780e6bf"  # Sentora RLUSD Main, largest Vault V2 on 2026-10-10
DEMO_BORROWER = "0xdf81987465681d0515058fe0a47a3bd174012730"  # 6 Blue borrows on 2026-10-10
REPLAY_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "replay"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="riskdep", description="Dependency discovery and stay/exit risk signal for a Pendle PT position."
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="analyse one position and write out/report.html + report.json")
    a.add_argument("--demo", action="store_true", help="the cached demo position (offline unless --live)")
    a.add_argument("--morpho-market", help="Morpho Blue market uniqueKey (PT collateral)")
    a.add_argument("--user", help="borrower address; default: the market's largest borrower")
    a.add_argument("--pendle-market", help="Pendle market address, for a plain PT holding")
    a.add_argument("--pt-amount", type=float, help="PT units held, with --pendle-market")
    a.add_argument("--horizon", type=float, default=30, help="days (capped at maturity), default 30")
    a.add_argument("--paths", type=int, default=20000, help="Monte Carlo paths")
    a.add_argument("--live", action="store_true", help="fetch on cache miss")
    a.add_argument("--refresh", action="store_true", help="always fetch and rewrite the cache")
    a.add_argument(
        "--vault",
        help="incident mode for a Vault V2 depositor (with --shock token=<collateral>:<fall>, and --user for the "
        "depositor); offline it reads fixtures/replay/<vault>/",
    )
    a.add_argument(
        "--shock",
        action="append",
        metavar="EVENT=SEVERITY",
        help="incident mode: a known incident, e.g. oracle=0.10 or issuer_depeg=0.08 (repeatable); events: "
        + ", ".join(scenario.EVENTS),
    )
    a.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "out"))

    w = sub.add_parser("watch", help="follow a Morpho Vault V2 block by block and alert on what affects a depositor")
    w.add_argument(
        "--vault",
        help="Vault V2 address; with --user, the depositor to follow in it "
        "(default with neither: Sentora RLUSD Main and its largest holder)",
    )
    w.add_argument(
        "--user",
        help="alone: watch every Blue borrow and Vault V2 deposit of this address; "
        "with --vault: the depositor in that vault",
    )
    w.add_argument("--hf", default="1.10,1.05,1.02", help="health-factor alert levels (info,warn,critical) for --user")
    w.add_argument(
        "--market",
        action="append",
        default=[],
        help="with --user: a Blue market id to watch as a borrow, skipping the Morpho API lookup (repeatable)",
    )
    w.add_argument("--blocks", type=int, help="check the last N blocks, then stop")
    w.add_argument(
        "--record", action="store_true", help="with --blocks: save every response under fixtures/replay/<vault>"
    )
    w.add_argument("--replay", action="store_true", help="re-run a recorded range offline")
    w.add_argument("--level", choices=["info", "warn", "critical"], default="info", help="lowest level printed")
    w.add_argument("--max-polls", type=int, help="stop after N empty polls (live mode)")
    w.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "out"))
    gr = sub.add_parser(
        "graph", help="write the dependency graph of an address's positions and of vaults as HTML + JSON"
    )
    gr.add_argument(
        "--user",
        action="append",
        default=[],
        help="address whose borrows and Vault V2 deposits to include (repeatable)",
    )
    gr.add_argument("--vault", action="append", default=[], help="Vault V2 to include (repeatable)")
    gr.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "out" / "graph.html"))
    gr.add_argument(
        "--example",
        action="store_true",
        help="the documented example: the demo borrower, and Sentora RLUSD Main with its largest depositor",
    )
    gr.add_argument(
        "--no-siblings",
        action="store_true",
        help="leave out the sibling markets: other Blue markets sharing a held market's collateral, underlying or "
        "price input, or lending that collateral",
    )
    gr.add_argument("--record", action="store_true", help="save every response under fixtures/replay/graph-<target>")
    gr.add_argument("--replay", action="store_true", help="rebuild a recorded graph offline")
    args = ap.parse_args(argv)

    if args.cmd == "graph":
        from . import graph as GR

        users, vaults = list(args.user), list(args.vault)
        if args.example or (not users and not vaults):
            users, vaults = [DEMO_BORROWER, "0xb03d620e49b6a21ea9d02142831c3f61c2fcbabc"], [DEMO_VAULT]
        rdir = REPLAY_DIR / f"graph-{(vaults or users)[0].lower()}"
        siblings = not args.no_siblings
        if args.replay:
            if not (rdir / "meta.json").exists():
                print(f"no recorded graph in {rdir}", file=sys.stderr)
                return 2
            meta = json.loads((rdir / "meta.json").read_text())
            users, vaults, block, siblings = meta["users"], meta["vaults"], meta["block"], meta["siblings"]
        # a direct run gets no directory: the Fetcher would create an empty one under fixtures/
        f = (
            S.Fetcher("offline", rdir)
            if args.replay
            else S.Fetcher("refresh", rdir)
            if args.record
            else S.Fetcher("direct")
        )
        try:
            if not args.replay:
                block = int(S.rpc(f, "eth_blockNumber", []), 16) - 2
            g = GR.build_all(f, block, users, vaults, siblings)
        except S.CacheMiss as e:
            print(f"replay data incomplete: {e}", file=sys.stderr)
            return 2
        except S.SourceError as e:
            print(f"data source error: {e}", file=sys.stderr)
            return 3
        if args.record:
            meta = {"users": users, "vaults": vaults, "block": block, "siblings": siblings}
            (rdir / "meta.json").write_text(json.dumps(meta, indent=1))
        title = "Morpho dependency graph: " + ", ".join([u[:10] + "…" for u in users] + [v[:10] + "…" for v in vaults])
        hp, jp = GR.write(g, Path(args.out), title, GR.subtitle_for(block))
        kinds = {}
        for n in g.nodes.values():
            kinds[n["kind"]] = kinds.get(n["kind"], 0) + 1
        print(f"{len(g.nodes)} nodes ({', '.join(f'{v} {k}' for k, v in kinds.items())}), {len(g.edges)} edges")
        print(f"html: {hp}\njson: {jp}")
        return 0

    if args.cmd == "watch" and args.user and not args.vault:
        from .watch_user import UserOptions, run_user

        try:
            levels = tuple(sorted((float(x) for x in args.hf.split(",")), reverse=True))
        except ValueError:
            ap.error("--hf takes comma-separated numbers, e.g. 1.10,1.05,1.02")
        if not levels or len(levels) > 3 or min(levels) <= 1:
            ap.error("--hf takes one to three levels, all above 1")
        if args.record and not args.blocks:
            ap.error("--record needs --blocks")
        rdir = REPLAY_DIR / f"user-{args.user.lower()}"
        uopts = UserOptions(
            args.user.lower(),
            Path(args.out),
            levels,
            args.market,
            mode="replay" if args.replay else "record" if args.record else "direct",
            replay_dir=rdir if (args.replay or args.record) else None,
            blocks=args.blocks,
            min_level=args.level,
            max_polls=args.max_polls,
        )
        try:
            return run_user(uopts)
        except S.CacheMiss as e:
            print(f"replay data incomplete: {e}", file=sys.stderr)
            return 2
        except S.SourceError as e:
            print(f"data source error: {e}", file=sys.stderr)
            return 3
        except KeyboardInterrupt:
            print("stopped; the cursor points at the last fully processed block", file=sys.stderr)
            return 0

    if args.cmd == "watch":
        from .watch import Options, run

        args.vault = args.vault or DEMO_VAULT
        rdir = REPLAY_DIR / args.vault.lower()
        if args.record and not args.blocks:
            ap.error("--record needs --blocks")
        opts = Options(
            args.vault.lower(),
            args.user,
            Path(args.out),
            mode="replay" if args.replay else "record" if args.record else "direct",
            replay_dir=rdir if (args.replay or args.record) else None,
            blocks=args.blocks,
            min_level=args.level,
            max_polls=args.max_polls,
        )
        try:
            return run(opts)
        except S.CacheMiss as e:
            print(f"replay data incomplete: {e}", file=sys.stderr)
            return 2
        except S.SourceError as e:
            print(f"data source error: {e}", file=sys.stderr)
            return 3
        except KeyboardInterrupt:
            print("stopped; the cursor points at the last fully processed block", file=sys.stderr)
            return 0

    if args.vault:
        return _vault_incident(ap, args)
    try:
        shocks = scenario.parse_shocks(args.shock)
    except ValueError as e:
        ap.error(str(e))
    mode = "refresh" if args.refresh else "live" if args.live else "offline"
    f = S.Fetcher(mode)
    as_of_path = S.SNAPSHOT_DIR / "as_of.json"
    if mode == "offline" and as_of_path.exists():
        clock.set_as_of(json.loads(as_of_path.read_text())["as_of"])
    run_started = clock.now()
    try:
        if args.demo or (not args.morpho_market and not args.pendle_market):
            pos = discover.discover_morpho_position(f, DEMO_MARKET, DEMO_USER)
        elif args.morpho_market:
            pos = discover.discover_morpho_position(f, args.morpho_market, args.user)
        else:
            if args.pt_amount is None:
                ap.error("--pendle-market needs --pt-amount")
            pos = discover.discover_pt_holding(f, args.pendle_market, args.pt_amount)

        # D96: the oracle mode from the oracle's structure when it decides, instead of the price inference
        oracle = next((n.split(":", 1)[1] for n, a in pos.graph.nodes(data=True) if a.get("kind") == "oracle"), None)
        profile = scenario.oracle_profile(f, oracle) if oracle else None
        decided = scenario.ex_ante_mode(profile, max(1.0, min(args.horizon, pos.days_to_maturity or args.horizon)))
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
        horizon = max(1.0, min(args.horizon, pos.days_to_maturity or args.horizon))
        sim = simulate.run(pos, prs, horizon, n=args.paths)
        quote = discover.exit_quote(f, pos)
        depeg = next((p.mean_severity for p in prs if p.event == "issuer_depeg"), None)
        dec = decide.verdict(
            pos,
            sim,
            quote,
            depeg,
            resimulate=lambda q: simulate.run(q, prs, horizon, n=args.paths),
            quote_for=lambda q, fr: discover.partial_exit_quote(f, q, fr),
        )
        alt = None
        if pos.oracle_mode != "none":
            # the same position under the other oracle behaviour: how much the verdict rests on the inference
            other = copy.copy(pos)
            other.oracle_mode = "fundamental" if pos.oracle_mode == "market-tracking" else "market-tracking"
            s2 = simulate.run(other, prs, horizon, n=args.paths)
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
    except S.CacheMiss as e:
        print(f"offline snapshot incomplete: {e}", file=sys.stderr)
        return 2
    except S.SourceError as e:
        print(f"data source error: {e}", file=sys.stderr)
        return 3

    if mode == "refresh":
        # a full refetch: this run's start becomes the snapshot's as-of date for later offline runs
        as_of_path.write_text(
            json.dumps(
                {
                    "as_of": run_started,
                    "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(run_started)),
                    "_doc": "Time the analyze snapshot was taken; offline runs use it as 'now'.",
                },
                indent=2,
            )
        )
    bad = [c for c in checks if c.ok is False]
    if bad:
        dec.reasons.insert(0, "DATA CHECK FAILED — " + "; ".join(c.detail for c in bad))
    hp, jp = report.write(pos, prs, sim, dec, quote, Path(args.out), mode, alt, incident)
    if incident:
        for line in incident.lines():
            print(line)
        print("EX ANTE (Monte Carlo, before any incident):")
    print(dec.headline)
    for r in dec.reasons:
        print(f"  - {r}")
    for c in checks:
        print(f"  {c.line}")
    print(f"report: {hp}\njson:   {jp}\nnetwork calls: {f.network_calls}")
    return 0


def _vault_incident(ap, args) -> int:
    """`analyze --vault`: a known incident on a vault's collateral, for a depositor (plan 2026-10-11-vault-incident)."""
    try:
        token_shocks = vault_incident.parse_token_shocks(args.shock)
    except ValueError as e:
        ap.error(str(e))
    if not token_shocks:
        ap.error("--vault needs --shock token=<collateral address or symbol>:<fall>, e.g. token=mGLOeuro:0.30")
    vault = args.vault.lower()
    w = discover.REGISTRY["watch"]
    rdir = REPLAY_DIR / vault
    try:
        if args.live or args.refresh:
            f = S.Fetcher("direct")
            block = int(S.rpc(f, "eth_blockNumber", []), 16) - w["confirmations"]
        else:
            if not (rdir / "start.json").exists():
                ap.error(
                    f"no recording for {vault} in {rdir}: run with --live, or record it with watch --blocks --record"
                )
            f = S.Fetcher("offline", rdir)
            block = (
                json.loads((rdir / "start.json").read_text())["head"] - w["confirmations"] - w["state_window_blocks"]
            )
        inc = vault_incident.run(f, vault, block, args.user, token_shocks)
    except S.CacheMiss as e:
        print(f"recording incomplete: {e}", file=sys.stderr)
        return 2
    except S.SourceError as e:
        print(f"data source error: {e}", file=sys.stderr)
        return 3
    for line in inc.lines():
        print(line)
    print(f"json:   {vault_incident.write(inc, Path(args.out))}")
    return 0
