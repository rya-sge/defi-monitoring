"""watch --user: every Blue borrow and Vault V2 deposit of one address, in one run (plan
2026-10-10-morpho-user-watcher). Borrows are one target; each vault is a target of its own,
watched with the vault rules on its own events only."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import borrower as B
from . import borrower_rules as BR
from . import crosscheck, discover
from . import sources as S
from .abi import MORPHO_BLUE, topic
from .discover import REGISTRY
from .poller import Poller
from .positions import discover_user
from .rules import Alert, Ctx, assess_batch, startup_findings
from .vault import discover_vault, read_state
from .watch import Printer, _fetcher, exposure_table

W = REGISTRY["watch"]
DEFAULT_LEVELS = (1.10, 1.05, 1.02)
SET_AUTH = topic("SetAuthorization(address,address,address,bool)")


@dataclass
class UserOptions:
    user: str
    out_dir: Path
    levels: tuple[float, ...] = DEFAULT_LEVELS
    markets: list[str] = field(default_factory=list)     # --market: borrows given by hand, no API
    mode: str = "direct"
    replay_dir: Path | None = None
    blocks: int | None = None
    min_level: str = "info"
    color: bool = True
    poll_seconds: float = W["poll_seconds"]
    max_polls: int | None = None


@dataclass
class VaultTarget:
    view: object
    state: object

    @property
    def addresses(self) -> set[str]:
        return set(self.view.kinds) - {MORPHO_BLUE}


def _pt_quote(f: S.Fetcher, m: B.BorrowMarket, st: B.BorrowState) -> str:
    """Real Pendle exit quote for PT collateral (D34); everything else is not quoted."""
    if not m.collateral_symbol.upper().startswith("PT-") or not st.collateral:
        return "not quoted"
    try:
        pm = discover.find_pendle_market(f, m.collateral_token)
    except (S.SourceError, S.CacheMiss):
        return "not quoted (no Pendle market)"
    pos = discover.Position(label="", collateral_units=st.collateral / 10 ** m.collateral_decimals,
                            collateral_symbol=m.collateral_symbol, collateral_address=m.collateral_token,
                            pt_price_usd=0.0, collateral_decimals=m.collateral_decimals,
                            loan_address=m.loan_token, pendle_market=pm["address"])
    q = discover.exit_quote(f, pos)
    if q.get("estimated"):
        return "not quoted (Pendle quote failed)"
    return f"{q['price_impact']:.2%} impact + {q['fee_usd']:,.0f} USD fee"


def borrow_table(p: Printer, f: S.Fetcher, markets: dict, states: dict, levels, block: int, quotes: dict) -> None:
    p.line(f"  borrows at block {block} (alert levels HF {' / '.join(f'{x:.2f}' for x in levels)}):")
    p.line(f"    {'market':<42} {'debt':>16} {'HF':>8} {'liq. at':>8} {'APY':>7} {'util':>6}  exit")
    for mid in sorted(markets, key=lambda i: (states[i].hf(markets[i].lltv) or 0)):
        m, st = markets[mid], states[mid]
        hf, drop = st.hf(m.lltv), st.liquidation_drop(m.lltv)
        p.line(f"    {m.label:<42} {st.debt / 10 ** m.loan_decimals:>12,.0f} {m.loan_symbol:<4}"
               f"{BR._hf_text(hf):>8} {('−' + format(drop, '.1%')) if drop is not None and not math.isinf(drop) else 'n/a':>8}"
               f" {(format(st.apy, '.2%') if st.apy is not None else 'n/a'):>7} {st.utilization:>6.1%}  {quotes.get(mid, '')}")


def lender_table(p: Printer, markets: dict, lenders: dict) -> None:
    p.line("  main lenders of each borrowed market (≥ 5 % of supply):")
    for mid, sps in lenders.items():
        m = markets[mid]
        names = ", ".join(f"{sp.label} {sp.share:.0%}" for sp in sorted(sps, key=lambda x: -x.share)) or "none above 5 %"
        p.line(f"    {m.label:<42} {names}")


def _by_address(lenders: dict) -> dict:
    return {mid: {sp.address: sp for sp in sps} for mid, sps in lenders.items()}


def run_user(opts: UserOptions) -> int:
    f = _fetcher(opts)
    user = opts.user.lower()
    state_dir = opts.replay_dir if opts.mode in ("record", "replay") else opts.out_dir
    meta_path = state_dir / "start.json" if state_dir else None
    if opts.mode == "replay":
        meta = json.loads(meta_path.read_text())
        pinned, start_cursor = meta["head"], meta["cursor"]
    else:
        head = int(S.rpc(f, "eth_blockNumber", []), 16)
        pinned = head if opts.blocks else None
        start_cursor = (head - W["confirmations"] - opts.blocks) if opts.blocks else None
        if opts.mode == "record":
            state_dir.mkdir(parents=True, exist_ok=True)
            meta_path.write_text(json.dumps({"user": user, "head": pinned, "cursor": start_cursor}))

    safe0 = (pinned or int(S.rpc(f, "eth_blockNumber", []), 16)) - W["confirmations"]
    first_block = start_cursor if start_cursor is not None else safe0
    state0 = max(first_block, safe0 - W["state_window_blocks"])
    p = Printer(opts, f"user-{user}")
    p.line(f"Morpho positions of {user}")

    # --- what the address holds (D32)
    if opts.markets:
        borrow_ids, vault_addrs, api_state = [m.lower() for m in opts.markets], [], {}
        p.line(f"  borrows given by hand: {len(borrow_ids)} market(s); vault deposits not looked up")
    else:
        up = discover_user(f, user)
        borrow_ids, vault_addrs, api_state = up.borrows, up.vaults, up.api_state
        p.line(f"  found {len(borrow_ids)} borrow(s) and {len(vault_addrs)} Vault V2 deposit(s)"
               + (f"; {up.collateral_only} market(s) with collateral and no debt are not watched" if up.collateral_only else ""))
    if not borrow_ids and not vault_addrs:
        p.line("  nothing to watch: no borrow and no Vault V2 deposit")
        return 0

    markets = B.discover_markets(f, borrow_ids, state0) if borrow_ids else {}
    before_b = B.read_borrows(f, markets, user, state0) if markets else {}
    start_apy = {mid: st.apy for mid, st in before_b.items()}
    quotes = {mid: _pt_quote(f, markets[mid], before_b[mid]) for mid in markets}
    vaults = []
    for va in vault_addrs:
        view = discover_vault(f, va, state0)
        vaults.append(VaultTarget(view, read_state(f, view, state0, user)))

    lenders = {mid: B.top_suppliers(f, markets[mid], state0) for mid in markets}
    if markets:
        borrow_table(p, f, markets, before_b, opts.levels, state0, quotes)
        lender_table(p, markets, lenders)
        for al in BR.startup(before_b, markets, opts.levels, state0) + BR.lenders_startup(lenders, markets, state0):
            p.alert(al)
        for mid in markets:
            if mid in api_state:
                c = crosscheck.morpho_position(f, mid, user, markets[mid].collateral_decimals, markets[mid].loan_decimals,
                                               api_state[mid]["collateral"] / 10 ** markets[mid].collateral_decimals,
                                               api_state[mid]["borrowAssets"])
                if c.ok is False:
                    p.alert(Alert("warn", state0, None, "CrossCheck", f"Data sources disagree on {markets[mid].label}", c.detail))
    for vt in vaults:
        exposure_table(vt.view, vt.state, p)
        for al in startup_findings(vt.view, vt.state):
            p.alert(al)
    c = crosscheck.second_rpc(f, state0)
    if c.ok is False:
        p.alert(Alert("critical", state0, None, "CrossCheck", "Data sources disagree: second RPC", c.detail))
    else:
        p.line(f"  {c.line}")
    if state0 != first_block:
        p.line(f"  note: events are checked from block {first_block + 1}; state-based rules start at block {state0}")

    # --- the poller: vaults and adapters, Blue on every watched market, and the user's authorisations
    def kinds_and_ids():
        kinds = {MORPHO_BLUE: "blue"}
        ids = set(markets)
        for vt in vaults:
            kinds.update(vt.view.kinds)
            ids |= set(vt.view.market_ids)
        return kinds, sorted(ids)

    user_topic = "0x" + user[2:].rjust(64, "0")
    cursor_path = (state_dir / "replay.cursor") if opts.mode in ("record", "replay") else opts.out_dir / f"watch-user-{user}.cursor"
    if opts.mode in ("record", "replay") or opts.blocks:
        cursor_path.unlink(missing_ok=True)
    kinds, ids = kinds_and_ids()
    poller = Poller(f, kinds, ids, cursor_path, W["confirmations"], W["max_range"],
                    extra_filters=[{"address": MORPHO_BLUE, "topics": [SET_AUTH, None, user_topic]}])
    if start_cursor is not None:
        poller.cursor = start_cursor
    elif poller.cursor is None:
        poller.cursor = first_block
    else:
        p.line(f"resuming after block {poller.cursor}")
    if pinned is not None:
        poller.head = lambda: pinned

    polls, last_check, backoff = 0, state0, opts.poll_seconds
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
        if batch.gap:
            p.alert(Alert("warn", batch.from_block, None, "Gap", f"Blocks {batch.gap[0]}–{batch.gap[1]} could not be read",
                          "too old for the free RPC; events in them were not checked"))
        safe = batch.head - W["confirmations"]
        state_block = max(batch.to_block, safe - W["state_window_blocks"])

        # a borrow opened in a market not yet watched: add it
        new = {e.args["id"] for e in batch.events if e.contract == "blue" and e.name == "Borrow"
               and e.args.get("onBehalf") == user and e.args.get("id") not in markets}
        if new:
            markets.update(B.discover_markets(f, sorted(new), state_block))
            for mid in new:
                if mid in markets:
                    lenders[mid] = B.top_suppliers(f, markets[mid], state_block)
            p.line(f"new borrow market(s) found: {', '.join(markets[i].label for i in new if i in markets)}")

        after_b = B.read_borrows(f, markets, user, state_block) if markets else {}
        for mid in after_b:
            start_apy.setdefault(mid, after_b[mid].apy)
        alerts = BR.assess_events(batch.events, user, markets, _by_address(lenders), before_b)
        alerts += BR.assess_states(before_b, after_b, markets, opts.levels, start_apy, batch.to_block)
        for vt in vaults:
            own = vt.addresses
            evs = [e for e in batch.events if e.address in own or (e.contract == "blue" and e.name != "SetAuthorization")]
            after_v = read_state(f, vt.view, state_block, user)
            alerts += assess_batch(evs, Ctx(vt.view, vt.state, after_v), user, batch.to_block)
            vt.state = after_v
        for al in alerts:
            p.alert(al)
        poller.save(batch.to_block)
        hfs = [st.hf(markets[mid].lltv) for mid, st in after_b.items() if st.debt]
        lowest = min((h for h in hfs if h is not None), default=None)
        p.line(f"·        #{batch.from_block}–{batch.to_block}: {len(batch.events)} events"
               + (f", {batch.unknown} undecoded" if batch.unknown else "")
               + (f" · lowest HF {lowest:.4f}" if lowest is not None else "")
               + (f" · {len(vaults)} vault(s)" if vaults else ""))
        before_b = after_b

        if batch.to_block - last_check >= W["crosscheck_every_blocks"]:
            last_check = batch.to_block
            c = crosscheck.second_rpc(f, batch.to_block)
            if c.ok is False:
                p.alert(Alert("critical", batch.to_block, None, "CrossCheck", "Data sources disagree: second RPC", c.detail))
            quotes = {mid: _pt_quote(f, markets[mid], after_b[mid]) for mid in markets}
            lenders = {mid: B.top_suppliers(f, markets[mid], batch.to_block) for mid in markets}
            if not opts.markets and opts.mode == "direct":
                try:
                    up = discover_user(f, user)
                    missing = [i for i in up.borrows if i not in markets]
                    if missing:
                        markets.update(B.discover_markets(f, missing, state_block))
                        p.line(f"new borrow market(s) found: {', '.join(markets[i].label for i in missing if i in markets)}")
                    for va in up.vaults:
                        if va not in {vt.view.address for vt in vaults}:
                            view = discover_vault(f, va, state_block)
                            vaults.append(VaultTarget(view, read_state(f, view, state_block, user)))
                            p.line(f"new Vault V2 deposit found: {view.name}")
                except (S.SourceError, S.CacheMiss) as e:
                    p.line(f"WARN     position rediscovery failed ({str(e)[:80]}); watching the positions already found")
            poller.kinds, poller.market_ids = kinds_and_ids()

    p.line(f"done: {p.count['critical']} critical, {p.count['warn']} warn, {p.count['info']} info · alerts in {p.path}")
    return 0
