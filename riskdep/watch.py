"""The watch loop: discover, read state, poll, assess, alert, save the cursor last."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from . import admin as AD
from . import crosscheck
from . import detect as DT
from . import drain as DR
from . import exit_queue as EQ
from . import feeds as FD
from . import market_risk as MR
from . import roles as RL
from . import sources as S
from . import zama as ZM
from .discover import REGISTRY
from .poller import Poller
from .rules import LEVELS, Alert, Ctx, assess_batch, startup_findings
from .vault import VaultView, discover_vault, largest_depositor, read_light, read_state

W = REGISTRY["watch"]
COLOR = {"info": "\033[36m", "warn": "\033[33m", "critical": "\033[1;31m"}
RESET = "\033[0m"


@dataclass
class Options:
    vault: str
    depositor: str | None
    out_dir: Path
    mode: str = "direct"  # direct | record | replay
    replay_dir: Path | None = None
    blocks: int | None = None  # process the last N blocks then stop
    min_level: str = "info"
    color: bool = True
    poll_seconds: float = W["poll_seconds"]
    step: int | None = None  # blocks per batch (default watch.max_range); 1 replays a fork crisis act by act (D185)
    max_polls: int | None = None


class Printer:
    def __init__(self, opts, name: str):
        self.opts = opts
        self.path = opts.out_dir / f"watch-{name}.jsonl"
        opts.out_dir.mkdir(parents=True, exist_ok=True)
        self.count = {"info": 0, "warn": 0, "critical": 0}

    def line(self, text: str) -> None:
        print(text, flush=True)

    def alert(self, al: Alert) -> None:
        self.count[al.level] += 1
        with self.path.open("a") as fh:
            fh.write(json.dumps(al.to_json(), default=str) + "\n")
        if LEVELS[al.level] < LEVELS[self.opts.min_level]:
            return
        tag = al.level.upper().ljust(8)
        if self.opts.color and sys.stdout.isatty():
            tag = COLOR[al.level] + tag + RESET
        tx = f" tx {al.tx[:12]}…" if al.tx else ""
        impact = f" [you: {al.depositor_impact:+,.2f}]" if al.depositor_impact else ""
        self.line(f"{tag} #{al.block}{tx} {al.title}{impact}" + (f" — {al.detail}" if al.detail else ""))


def light_read(batch, live: bool, refresh: bool, last_full: int) -> bool:
    """D61: a live batch with no event reads only the values that move without one, until the last full read is
    `full_state_every_blocks` old. Anything on the watched filters, undecoded logs included, a gap, a refresh or a
    recorded or one-shot run (whose replays hold full reads) gets a full read."""
    return (
        live
        and not refresh
        and not batch.events
        and not batch.unknown
        and batch.gap is None
        and batch.to_block - last_full < W["full_state_every_blocks"]
    )


def _fetcher(opts: Options) -> S.Fetcher:
    if opts.mode == "replay":
        return S.Fetcher("offline", opts.replay_dir)
    if opts.mode == "record":
        return S.Fetcher("refresh", opts.replay_dir)
    return S.Fetcher("direct")


def exposure_table(view: VaultView, st, p: Printer) -> None:
    unit = 10**view.decimals
    p.line(f"{view.name} ({view.address}) · {view.asset_symbol} · block {st.block}")
    p.line(
        f"  total assets {st.total_assets / unit:,.0f} · idle {st.idle / unit:,.0f} · share price {st.share_price:.6f}"
    )
    p.line(
        f"  plain withdrawal can pay {st.withdrawable / unit:,.0f} "
        f"({'idle + liquidity market ' + str(view.liquidity_market)[:10] + '…' if view.liquidity_market else 'idle only: no liquidity adapter'})"
        f" · {st.force_withdrawable / unit:,.0f} more via forceDeallocate"
    )
    if st.depositor:
        p.line(
            f"  depositor {st.depositor}: {st.depositor_assets / unit:,.0f} {view.asset_symbol} "
            f"({st.depositor_shares / st.total_supply:.2%} of the vault)"
            if st.total_supply
            else ""
        )
    if view.timelocks:

        def fmt(t, ab):
            return "abdicated" if ab else ("0" if t == 0 else f"{t / 86400:g}d")

        p.line(
            "  timelocks: "
            + ", ".join(
                f"{sig.split('(')[0]}{'' if c == view.address else ' (adapter)'} {fmt(t, ab)}"
                for (c, sig), (t, ab) in view.timelocks.items()
            )
        )
    for a in view.adapters:
        p.line(f"  adapter {a.address} [{a.kind}] real assets {st.real_assets.get(a.address, 0) / unit:,.0f}")
        rows = sorted(a.markets.values(), key=lambda m: -st.markets[m.id].vault_assets)
        for mp in rows:
            m = st.markets[mp.id]
            share = m.vault_assets / st.total_assets if st.total_assets else 0
            tag = " [liquidity]" if mp.id == view.liquidity_market else ""
            p.line(
                f"    {(mp.collateral_symbol + tag):<22} LLTV {mp.lltv:6.1%}  {m.vault_assets / unit:>16,.0f}  {share:6.1%}"
                f"  util {m.utilization:6.1%}  withdrawable {m.withdrawable / unit:>14,.0f}"
            )


def _cross_check(f: S.Fetcher, p: Printer, view: VaultView, st, block: int) -> None:
    """Main RPC vs an independent one, and the Morpho API vs the chain (crosscheck.py)."""
    checks = [
        crosscheck.second_rpc(f, block),
        crosscheck.vault_total_assets(f, view.address, st.total_assets, view.decimals),
    ]
    for c in checks:
        if c.ok is False:
            level = "critical" if c.name == "second RPC" else "warn"
            p.alert(Alert(level, block, None, "CrossCheck", f"Data sources disagree: {c.name}", c.detail))
        else:
            p.line(f"  {c.line}")


def run(opts: Options) -> int:
    f = _fetcher(opts)
    state_dir = opts.replay_dir if opts.mode in ("record", "replay") else opts.out_dir
    meta_path = state_dir / "start.json" if state_dir else None

    if opts.mode == "replay":
        meta = json.loads(meta_path.read_text())
        pinned, start_cursor, dep = meta["head"], meta["cursor"], meta["depositor"]
        S.FORK = meta.get("fork", False)  # a range recorded on a local fork replays as one (D180)
        opts.step = meta.get("step") or opts.step  # the same batches as the recording, or its requests do not match
    else:
        pinned = None
        head = int(S.rpc(f, "eth_blockNumber", []), 16)
        if opts.blocks:
            pinned = head
        start_cursor = (head - W["confirmations"] - opts.blocks) if opts.blocks else None
        dep = opts.depositor.lower() if opts.depositor else largest_depositor(f, opts.vault)
        if opts.mode == "record":
            state_dir.mkdir(parents=True, exist_ok=True)
            meta_path.write_text(
                json.dumps(
                    {
                        "vault": opts.vault,
                        "head": pinned,
                        "cursor": start_cursor,
                        "depositor": dep,
                        "fork": S.FORK,
                        "step": opts.step,
                    }
                )
            )

    safe0 = (pinned or int(S.rpc(f, "eth_blockNumber", []), 16)) - W["confirmations"]
    first_block = start_cursor if start_cursor is not None else safe0
    # the free node serves state only ~126 blocks back (D28): older starts read the oldest servable block
    state0 = max(first_block, safe0 - W["state_window_blocks"])
    view = discover_vault(f, opts.vault, state0)
    before = read_state(f, view, state0, dep)

    p = Printer(opts, view.address)
    exposure_table(view, before, p)
    if state0 != first_block:
        p.line(
            f"  note: events are checked from block {first_block + 1}; state older than block {state0} "
            "is not served by the free RPC, so state-based rules start there"
        )
    vrisk = MR.VaultRisk(f, view, before, state0)
    MR.curve_table(p.line, vrisk.risks, vrisk.markets)
    aw = AD.AdminWatch(f, list(vrisk.markets), state0)
    vd = DR.VaultDrain(f, view, state0)
    drain_alerts = vd.startup(p.line, f, before, vrisk.markets, aw, state0)
    vx = EQ.VaultExit(f, view, before)
    exit_alerts = vx.startup(p.line, before, EQ.vault_cases(vrisk, before), state0, drained=vd.drained(before))
    aw.table(p.line)
    fw = FD.FeedWatch(f, aw, state0)  # D193: each feed's freshness
    try:
        # D245 (GAPV2 G2): what holds each role; a recording made before this read has none of it
        role_alerts = RL.findings(RL.read(f, RL.discover(f, view.address, state0), state0), state0)
    except (S.CacheMiss, S.SourceError):
        role_alerts = []
        p.line("  role holders: not checked (not in this recording)")
    for al in (
        startup_findings(view, before)
        + role_alerts
        + vrisk.startup(before, state0)
        + drain_alerts
        + exit_alerts
        + aw.startup(state0)
        + fw.startup(p.line, state0)
    ):
        p.alert(al)
    _cross_check(f, p, view, before, state0)

    cursor_path = (
        (state_dir / "replay.cursor")
        if opts.mode in ("record", "replay")
        else opts.out_dir / f"watch-{view.address}.cursor"
    )
    if opts.mode in ("record", "replay") or opts.blocks:
        cursor_path.unlink(missing_ok=True)
    # D190: a Zama confidential vault: its batchers and wrappers join the watched contracts
    ze = ZM.entry(view.address)
    zkinds, zfilters, zrate = (ZM.kinds(ze), ZM.filters(ze), ZM.share_rate(f, ze, state0)) if ze else ({}, [], 0)
    poller = Poller(
        f,
        {**aw.kinds(), **view.kinds, **zkinds},
        view.market_ids,
        cursor_path,
        W["confirmations"],
        opts.step or W["max_range"],
        extra_filters=aw.filters() + zfilters,
    )
    if start_cursor is not None:
        poller.cursor = start_cursor
    elif poller.cursor is None:
        poller.cursor = first_block
    else:
        p.line(f"resuming after block {poller.cursor}")
    if pinned is not None:
        poller.head = lambda: pinned

    polls = 0
    known = DT.last_prices({}, before)  # D187: each oracle's last answer
    last_check = last_full = state0
    live = opts.mode == "direct" and pinned is None
    backoff = opts.poll_seconds
    while True:
        try:
            batch = poller.next_batch()
        except S.SourceError as e:
            if opts.mode == "replay" or opts.blocks:
                raise
            p.line(f"WARN     RPC: {e}; retrying in {backoff:.0f}s")
            time.sleep(backoff)
            backoff = min(60, backoff * 2)
            continue
        backoff = opts.poll_seconds
        if batch is None:
            if pinned is not None:
                break
            polls += 1
            if opts.max_polls and polls >= opts.max_polls:
                break
            time.sleep(opts.poll_seconds)
            continue

        for w_ in poller.warnings:
            p.line(f"WARN     {w_}")
        if batch.gap:
            p.alert(
                Alert(
                    "warn",
                    batch.from_block,
                    None,
                    "Gap",
                    f"Blocks {batch.gap[0]}–{batch.gap[1]} could not be read",
                    "too old for the free RPC; events in them were not checked",
                )
            )
        safe = batch.head - W["confirmations"]
        state_block = max(batch.to_block, safe - W["state_window_blocks"])
        if any(e.name in ("AddAdapter", "RemoveAdapter") for e in batch.events) or any(
            e.contract == "adapter" and e.name == "Allocate" and e.args["marketId"] not in view.market_ids
            for e in batch.events
        ):
            view = discover_vault(f, opts.vault, state_block)
            poller.kinds, poller.market_ids = {**view.kinds, **zkinds}, view.market_ids
            p.line(f"structure changed: rediscovered at block {state_block}")
        refresh = batch.to_block - last_check >= W["crosscheck_every_blocks"]
        if light_read(batch, live, refresh, last_full):
            after = read_light(f, view, state_block, before)
        else:
            after = read_state(f, view, state_block, dep)
            last_full = batch.to_block
        if set(MR.vault_markets(view, after)) != set(vrisk.markets):
            vrisk = MR.VaultRisk(f, view, after, state_block)
            aw = AD.AdminWatch(f, list(vrisk.markets), state_block)
            vd = DR.VaultDrain(f, view, state_block)
            poller.kinds, poller.extra_filters = {**aw.kinds(), **view.kinds, **zkinds}, aw.filters() + zfilters
        for al in (
            assess_batch(batch.events, Ctx(view, before, after), dep, batch.to_block)
            + vrisk.step(f, batch.events, after, state_block, batch.to_block, refresh)
            + vd.step(f, after, vrisk.markets, aw, batch.to_block, refresh)
            + vx.step(
                after, EQ.vault_cases(vrisk, after), batch.to_block, f if refresh else None, drained=vd.drained(after)
            )
            + aw.step(f, batch.events, state_block, refresh)
            + aw.check_divergence(f, batch.to_block, {mid: m.oracle_price for mid, m in after.markets.items()})
            # D188: after vrisk.step, whose risks are now at the batch's prices
            + DT.impact_alerts(known, after, vrisk.risks, vrisk.markets, view.decimals, batch.to_block)
            + (ZM.assess_events(batch.events, ze, after.total_supply, zrate, batch.to_block) if ze else [])
            + (fw.step(f, state_block) if refresh else [])
        ):
            p.alert(al)
        known = DT.last_prices(known, after)
        poller.save(batch.to_block)
        unit = 10**view.decimals
        p.line(
            f"·        #{batch.from_block}–{batch.to_block}: {len(batch.events)} events"
            + (f", {batch.unknown} undecoded" if batch.unknown else "")
            + f" · share price {after.share_price:.6f} · plain withdrawal {after.withdrawable / unit:,.0f}"
        )
        before = after
        if batch.to_block - last_check >= W["crosscheck_every_blocks"]:
            _cross_check(f, p, view, after, batch.to_block)
            last_check = batch.to_block

    p.line(f"done: {p.count['critical']} critical, {p.count['warn']} warn, {p.count['info']} info · alerts in {p.path}")
    return 0
