"""python -m riskdep analyze ..."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import clock, pipeline, report, scenario, vault_book, vault_incident
from . import sources as S

# D14: largest borrower of Morpho market PT-sUSDE-26NOV2026 / USDC, cached in fixtures/snapshot.
DEMO_VAULT = "0x6dc58a0fdfc8d694e571dc59b9a52eeea780e6bf"  # Sentora RLUSD Main, largest Vault V2 on 2026-10-10
DEMO_BORROWER = "0xdf81987465681d0515058fe0a47a3bd174012730"  # 6 Blue borrows on 2026-10-10
REPLAY_DIR = pipeline.REPLAY_DIR


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
        action="append",
        help="incident mode for a Vault V2 (with --shock token=… or borrower=…; --user for the depositor); "
        "repeat it for an ad hoc book of vaults",
    )
    a.add_argument(
        "--book",
        help="a book of vaults in a JSON file (see examples/), each vault with an optional depositor and label",
    )
    a.add_argument(
        "--conditional",
        action="store_true",
        help="with --vault or --book and a token=… shock: the distribution of the loss of staying given the incident "
        "(its size recovering or deepening, liquidators failing to act), against the certain cost of leaving",
    )
    a.add_argument(
        "--exit-cost",
        type=float,
        help="with --vault or --book: the cost of leaving as a share of what leaves (0.11 for the brief's 11 %% "
        "unwind), instead of the vault's yield given up over --horizon",
    )
    a.add_argument(
        "--record",
        action="store_true",
        help="with --vault or --book: read each vault live at the head and save every response under "
        "fixtures/replay/incident-<vault>/, for offline runs",
    )
    a.add_argument(
        "--shock",
        action="append",
        metavar="EVENT=SEVERITY",
        help="incident mode: a known incident, e.g. oracle=0.10 or issuer_depeg=0.08 (repeatable); events: "
        + ", ".join(scenario.EVENTS)
        + "; with --vault or --book: token=<collateral>:<fall> (a markdown) or "
        "borrower=<collateral, market id or all>:<recovery>[:<n>] (the n largest borrowers default)",
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
    w.add_argument(
        "--step",
        type=int,
        metavar="N",
        help="blocks per batch (default watch.max_range); --step 1 reads state at every block, so a short crisis "
        "on a local fork is seen act by act",
    )
    w.add_argument(
        "--poll",
        type=float,
        metavar="SECONDS",
        help="seconds between polls in live mode (default watch.poll_seconds, 12 s, Ethereum's block time); "
        "lower on a local fork, whose blocks come when a script mines them",
    )
    w.add_argument(
        "--record-as",
        metavar="NAME",
        help="with --record or --replay: the recording's folder under fixtures/replay/ instead of the vault address, "
        "e.g. fork-belem for a run on a local fork (scripts/fork/)",
    )
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
    sh = sub.add_parser(
        "shock", help="apply a failure to a node of the dependency graph and propagate it (oracle, feed, collateral)"
    )
    sh.add_argument("--vault", action="append", default=[], help="Vault V2 whose markets seed the graph (repeatable)")
    sh.add_argument("--user", action="append", default=[], help="address: its borrows, and its share of a vault's loss")
    sh.add_argument(
        "--shock",
        action="append",
        default=[],
        help="<node>:<mode>[:<size>], node = address, market id or a unique label fragment; mode = reads-low, "
        "reads-high, frozen or price (repeatable: shocks applied together)",
    )
    sh.add_argument(
        "--sweep", help="<mode>[:<size>]: the same failure on every oracle and feed (assets for price) in turn"
    )
    sh.add_argument("--rules", help="JSON file whose edge_rules / node_rules are tried before the registry's")
    sh.add_argument("--list", action="store_true", help="list the nodes that can be shocked and the markets they price")
    sh.add_argument("--top", type=int, default=15, help="rows of the --sweep ranking")
    sh.add_argument("--no-siblings", action="store_true", help="leave out the sibling markets")
    sh.add_argument("--record", action="store_true", help="save every response under fixtures/replay/graph-<target>")
    sh.add_argument("--replay", action="store_true", help="use a recorded graph, offline")
    sh.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "out"))
    bt = sub.add_parser("backtest", help="replay a past incident: the tool's prediction against the on-chain events")
    bt.add_argument("--episode", default="pt-reusd-2026-08-25", help="an episode of registry.json backtest.episodes")
    bt.add_argument(
        "--record",
        action="store_true",
        help="read the episode through the archive RPC and the Etherscan key of keys.ini, and save every response "
        "under fixtures/replay/backtest-<episode>/ (offline otherwise)",
    )
    bt.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "out"))
    nt = sub.add_parser("notify", help="post the watch alerts to a Telegram channel (keys.ini [alerts])")
    nt.add_argument("--level", choices=["info", "warn", "critical"], help="lowest level posted (registry: warn)")
    nt.add_argument("--from-start", action="store_true", help="post what the alert files already hold, not only new")
    nt.add_argument("--once", action="store_true", help="one pass over the alert files, then stop")
    nt.add_argument("--test", action="store_true", help="send one test message and stop")
    nt.add_argument("--post", metavar="JSON", help="post the headline of an incident run (out/book-incident.json)")
    nt.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "out"))
    args = ap.parse_args(argv)

    if args.cmd == "backtest":
        return _backtest(ap, args)
    if args.cmd == "notify":
        from . import notify

        args.level = args.level or notify.N["level"]
        return notify.run(args)

    if S.FORK:
        # D180–D181: a local fork only; its clock is the fork's, which `anvil_increaseTime` moves ahead of ours
        if S.RPC not in S.ROUTES:
            ap.error("RISKDEP_FORK needs RISKDEP_RPC_URL pointing at the local fork (scripts/fork/start-fork.sh)")
        if not getattr(args, "replay", False):
            try:
                head = S.rpc(S.Fetcher("direct"), "eth_getBlockByNumber", ["latest", False])
                clock.set_as_of(int(head["timestamp"], 16))
            except (S.SourceError, KeyError, TypeError) as e:
                ap.error(f"the local fork does not answer at {S.ROUTES[S.RPC]}: {str(e)[:80]}")

    if args.cmd == "shock":
        from . import engine as EN
        from . import graph as GR
        from . import shock as SH

        if not args.vault and not args.user:
            ap.error("shock needs --vault or --user")
        if not (args.shock or args.sweep or args.list):
            ap.error("shock needs --shock, --sweep or --list")
        rdir = REPLAY_DIR / f"graph-{(args.vault or args.user)[0].lower()}"
        mode = "replay" if args.replay else "record" if args.record else "direct"
        try:
            extra = SH.load_rules(args.rules)
            g, block, users, vaults, _ = GR.load(args.user, args.vault, not args.no_siblings, mode, rdir)
        except (FileNotFoundError, ValueError) as e:
            print(e, file=sys.stderr)
            return 2
        except S.CacheMiss as e:
            print(f"replay data incomplete: {e}", file=sys.stderr)
            return 2
        except S.SourceError as e:
            print(f"data source error: {e}", file=sys.stderr)
            return 3
        gd = SH._graph_dict(g)
        target = (vaults or users)[0].lower()
        print(
            f"graph of {', '.join(v[:10] + '…' for v in vaults + users)} at block {block:,}: {len(gd['nodes'])} nodes"
        )
        if args.list:
            SH.list_targets(gd)
            return 0
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        try:
            if args.sweep:
                m, _, sz = args.sweep.partition(":")
                shk = EN.parse_shock(f"0x:{m}:{sz}" if sz else f"0x:{m}")
                rows = SH.run_sweep(gd, shk.mode, shk.size, extra, args.top)
                path = out / f"shock-sweep-{target}.json"
                path.write_text(
                    json.dumps({"block": block, "mode": shk.mode, "size": shk.size, "ranking": rows}, indent=1)
                )
            else:
                shocks = SH.resolve_shocks({n["id"]: n for n in gd["nodes"]}, args.shock)
                res = EN.run(gd, shocks, extra)
                data = SH.report(gd, res)
                path = out / f"shock-{target}.json"
                path.write_text(json.dumps({"block": block, **data}, indent=1, default=str))
                tpath = out / f"shock-{target}.trace.json"
                tpath.write_text(
                    json.dumps(
                        SH.trace(gd, res, block, clock.now_dt().strftime("%Y-%m-%dT%H:%M:%SZ"), extra),
                        indent=1,
                        default=str,
                    )
                )
                print(f"trace: {tpath}")
        except (ValueError, KeyError) as e:
            print(e, file=sys.stderr)
            return 2
        print(f"json: {path}")
        return 0

    if args.cmd == "graph":
        from . import graph as GR

        users, vaults = list(args.user), list(args.vault)
        if args.example or (not users and not vaults):
            users, vaults = [DEMO_BORROWER, "0xb03d620e49b6a21ea9d02142831c3f61c2fcbabc"], [DEMO_VAULT]
        rdir = REPLAY_DIR / f"graph-{(vaults or users)[0].lower()}"
        mode = "replay" if args.replay else "record" if args.record else "direct"
        try:
            g, block, users, vaults, _ = GR.load(users, vaults, not args.no_siblings, mode, rdir)
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            return 2
        except S.CacheMiss as e:
            print(f"replay data incomplete: {e}", file=sys.stderr)
            return 2
        except S.SourceError as e:
            print(f"data source error: {e}", file=sys.stderr)
            return 3
        ph = pipeline.pharos_snapshot("record" if args.record else "offline" if args.replay else "live")
        graded = GR.annotate_pharos(g, ph) if ph else 0
        protocols = pipeline.llama_protocols("offline" if args.replay else "live")
        drawn = GR.annotate_tvl(g, protocols) if protocols else 0
        title = "Morpho dependency graph: " + ", ".join([u[:10] + "…" for u in users] + [v[:10] + "…" for v in vaults])
        hp, jp = GR.write(g, Path(args.out), title, GR.subtitle_for(block))
        kinds = {}
        for n in g.nodes.values():
            kinds[n["kind"]] = kinds.get(n["kind"], 0) + 1
        print(f"{len(g.nodes)} nodes ({', '.join(f'{v} {k}' for k, v in kinds.items())}), {len(g.edges)} edges")
        print(f"Pharos {ph.as_of}: {graded} asset(s) graded" if ph else "Pharos: not checked")
        print(
            f"TVL concentration: {drawn} protocol(s) from DefiLlama" if protocols else "TVL concentration: not checked"
        )
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
        rdir = REPLAY_DIR / (args.record_as or args.vault.lower())
        if args.record and not args.blocks:
            ap.error("--record needs --blocks")
        if args.record_as and not (args.record or args.replay):
            ap.error("--record-as needs --record or --replay")
        opts = Options(
            args.vault.lower(),
            args.user,
            Path(args.out),
            mode="replay" if args.replay else "record" if args.record else "direct",
            replay_dir=rdir if (args.replay or args.record) else None,
            blocks=args.blocks,
            min_level=args.level,
            max_polls=args.max_polls,
            step=args.step,
            **({"poll_seconds": args.poll} if args.poll else {}),
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

    if args.vault or args.book:
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
        res = pipeline.analyze(
            f,
            market=None if args.demo else args.morpho_market,
            user=args.user,
            pendle_market=None if args.demo else args.pendle_market,
            pt_amount=args.pt_amount,
            horizon=args.horizon,
            paths=args.paths,
            shocks=shocks,
        )
    except ValueError as e:
        ap.error(str(e))
    except S.CacheMiss as e:
        print(f"offline snapshot incomplete: {e}", file=sys.stderr)
        return 2
    except S.SourceError as e:
        print(f"data source error: {e}", file=sys.stderr)
        return 3
    pos, prs, sim, dec = res.position, res.priors, res.simulation, res.decision

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
    incident = res.incident
    hp, jp = report.write(pos, prs, sim, dec, res.quote, Path(args.out), mode, res.oracle_alt, incident)
    if incident:
        for line in incident.lines():
            print(line)
        print("EX ANTE (Monte Carlo, before any incident):")
    print(dec.headline)
    for r in dec.reasons:
        print(f"  - {r}")
    for c in res.checks:
        print(f"  {c.line}")
    print(f"report: {hp}\njson:   {jp}\nnetwork calls: {f.network_calls}")
    return 0


def _backtest(ap, args) -> int:
    """`backtest`: plan 2026-10-11-backtest (D161–D164)."""
    from . import backtest as BK

    if args.episode not in BK.BT["episodes"]:
        ap.error(f"unknown episode {args.episode!r}: one of {', '.join(BK.BT['episodes'])}")
    rdir = REPLAY_DIR / f"backtest-{args.episode}"
    url = S.archive_url() if args.record else None
    if args.record and not url:
        ap.error("--record reads past state: put an archive RPC in keys.ini ([rpc] url or [alchemy])")
    try:
        with S.routed_rpc(url):
            res = BK.run(S.Fetcher("refresh" if args.record else "offline", rdir), args.episode)
    except S.CacheMiss as e:
        print(f"no recording of this episode: {e}; run once with --record", file=sys.stderr)
        return 2
    except S.SourceError as e:
        print(f"data source error: {e}", file=sys.stderr)
        return 3
    for line in res.lines():
        print(line)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    jp = out / f"backtest-{args.episode}.json"
    jp.write_text(json.dumps(res.to_json(), indent=2))
    print(f"json:   {jp}")
    return 0


def _vault_incident(ap, args) -> int:
    """`analyze --vault` / `--book`: a known incident on a collateral, for one vault or a book of vaults
    (plans 2026-10-11-vault-incident and 2026-10-11-vault-book); the work is `pipeline.incident`."""
    mode = "record" if args.record else "refresh" if args.refresh else "live" if args.live else "offline"
    try:
        book = vault_book.load(Path(args.book)) if args.book else vault_book.from_addresses(args.vault, args.user)
        res = pipeline.incident(book, args.shock, args.user, args.horizon, mode, args.exit_cost, args.conditional)
    except (ValueError, FileNotFoundError) as e:
        ap.error(str(e))
    except S.CacheMiss as e:
        print(f"recording incomplete: {e}", file=sys.stderr)
        return 2
    except S.SourceError as e:
        print(f"data source error: {e}", file=sys.stderr)
        return 3
    if len(res.incidents) == 1 and not args.book:
        for line in res.incidents[0].lines():
            print(line)
        print(f"json:   {vault_incident.write(res.incidents[0], Path(args.out))}")
        return 0
    for line in res.result.text():
        print(line)
    print(f"json:   {vault_book.write(res.result, Path(args.out))}")
    return 0
