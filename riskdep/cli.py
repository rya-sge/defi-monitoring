"""python -m riskdep analyze ..."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

from . import clock, crosscheck, decide, discover, priors, report, simulate
from . import sources as S

# D14: largest borrower of Morpho market PT-sUSDE-26NOV2026 / USDC, cached in data/snapshot.
DEMO_MARKET = "0x5613b170ded221c588b6e9637b910f49e5508680ceede207f44aa72e5c46cb05"
DEMO_USER = "0xdf81987465681D0515058fe0A47A3bD174012730"
DEMO_VAULT = "0x6dc58a0fdfc8d694e571dc59b9a52eeea780e6bf"   # Sentora RLUSD Main, largest Vault V2 on 2026-10-10
DEMO_BORROWER = "0xdf81987465681d0515058fe0a47a3bd174012730"  # 6 Blue borrows on 2026-10-10
REPLAY_DIR = Path(__file__).resolve().parent.parent / "data" / "replay"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="riskdep", description="Dependency discovery and stay/exit risk signal for a Pendle PT position.")
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
    a.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "out"))

    w = sub.add_parser("watch", help="follow a Morpho Vault V2 block by block and alert on what affects a depositor")
    w.add_argument("--vault", help="Vault V2 address; with --user, the depositor to follow in it "
                                     "(default with neither: Sentora RLUSD Main and its largest holder)")
    w.add_argument("--user", help="alone: watch every Blue borrow and Vault V2 deposit of this address; "
                                  "with --vault: the depositor in that vault")
    w.add_argument("--hf", default="1.10,1.05,1.02", help="health-factor alert levels (info,warn,critical) for --user")
    w.add_argument("--market", action="append", default=[],
                   help="with --user: a Blue market id to watch as a borrow, skipping the Morpho API lookup (repeatable)")
    w.add_argument("--blocks", type=int, help="check the last N blocks, then stop")
    w.add_argument("--record", action="store_true", help="with --blocks: save every response under data/replay/<vault>")
    w.add_argument("--replay", action="store_true", help="re-run a recorded range offline")
    w.add_argument("--level", choices=["info", "warn", "critical"], default="info", help="lowest level printed")
    w.add_argument("--max-polls", type=int, help="stop after N empty polls (live mode)")
    w.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "out"))
    args = ap.parse_args(argv)

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
        uopts = UserOptions(args.user.lower(), Path(args.out), levels, args.market,
                            mode="replay" if args.replay else "record" if args.record else "direct",
                            replay_dir=rdir if (args.replay or args.record) else None,
                            blocks=args.blocks, min_level=args.level, max_polls=args.max_polls)
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
        opts = Options(args.vault.lower(), args.user, Path(args.out),
                       mode="replay" if args.replay else "record" if args.record else "direct",
                       replay_dir=rdir if (args.replay or args.record) else None,
                       blocks=args.blocks, min_level=args.level, max_polls=args.max_polls)
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

        checks = [crosscheck.second_rpc(f)]
        if pos.morpho_market:
            checks.append(crosscheck.morpho_position(f, pos.morpho_market, pos.borrower, pos.collateral_decimals,
                                                     pos.loan_decimals, pos.collateral_units, pos.debt_raw))
        pos.notes += [c.line for c in checks]

        prs = priors.layer_priors(f, pos)
        horizon = max(1.0, min(args.horizon, pos.days_to_maturity or args.horizon))
        sim = simulate.run(pos, prs, horizon, n=args.paths)
        quote = discover.exit_quote(f, pos)
        depeg = next((p.mean_severity for p in prs if p.event == "issuer_depeg"), None)
        dec = decide.verdict(pos, sim, quote, depeg,
                             resimulate=lambda q: simulate.run(q, prs, horizon, n=args.paths),
                             quote_for=lambda q, fr: discover.partial_exit_quote(f, q, fr))
        alt = None
        if pos.oracle_mode != "none":
            # the same position under the other oracle behaviour: how much the verdict rests on the inference
            other = copy.copy(pos)
            other.oracle_mode = "fundamental" if pos.oracle_mode == "market-tracking" else "market-tracking"
            s2 = simulate.run(other, prs, horizon, n=args.paths)
            d2 = decide.verdict(other, s2, quote, depeg)
            alt = {"oracle_mode": other.oracle_mode, "verdict": d2.verdict, "expected_loss_usd": s2.expected_loss_usd,
                   "cvar99_usd": s2.cvar99_usd, "p_liquidation": s2.p_liquidation}
            same = d2.verdict == dec.verdict
            dec.reasons.append(
                f"Oracle sensitivity{' (inference ambiguous)' if pos.oracle_ambiguous else ''}: if the oracle were "
                f"{other.oracle_mode}, expected loss ${s2.expected_loss_usd:,.0f} (vs ${sim.expected_loss_usd:,.0f}), "
                f"P(liquidation) {s2.p_liquidation:.2%} (vs {sim.p_liquidation:.2%}), verdict {d2.verdict}"
                + (" — the same." if same else " — the verdict depends on the oracle; check its source before acting."))
    except S.CacheMiss as e:
        print(f"offline snapshot incomplete: {e}", file=sys.stderr)
        return 2
    except S.SourceError as e:
        print(f"data source error: {e}", file=sys.stderr)
        return 3

    if mode == "refresh":
        # a full refetch: this run's start becomes the snapshot's as-of date for later offline runs
        as_of_path.write_text(json.dumps({"as_of": run_started, "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(run_started)),
                                          "_doc": "Time the analyze snapshot was taken; offline runs use it as 'now'."}, indent=2))
    bad = [c for c in checks if c.ok is False]
    if bad:
        dec.reasons.insert(0, "DATA CHECK FAILED — " + "; ".join(c.detail for c in bad))
    hp, jp = report.write(pos, prs, sim, dec, quote, Path(args.out), mode, alt)
    print(dec.headline)
    for r in dec.reasons:
        print(f"  - {r}")
    for c in checks:
        print(f"  {c.line}")
    print(f"report: {hp}\njson:   {jp}\nnetwork calls: {f.network_calls}")
    return 0
