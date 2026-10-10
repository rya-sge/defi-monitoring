"""Impact rules: decoded events + state before/after → alerts for a Vault V2 depositor.

Pure functions, no I/O. The rule table is §3 of plan 2026-10-10-morpho-vault-v2-watcher.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from .abi import RISK_INCREASING_ADAPTER, RISK_INCREASING_VAULT, Event, describe_call
from .discover import REGISTRY
from .vault import VaultState, VaultView, cap_ids

W = REGISTRY["watch"]
LEVELS = {"info": 0, "warn": 1, "critical": 2}


@dataclass
class Alert:
    level: str  # info | warn | critical
    block: int
    tx: str | None
    event: str
    title: str
    detail: str = ""
    depositor_impact: float | None = None  # in the vault's asset, negative = loss
    data: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return asdict(self)


class Ctx:
    """What the rules need to phrase amounts and find markets."""

    def __init__(self, view: VaultView, before: VaultState, after: VaultState):
        self.view, self.before, self.after = view, before, after
        self.unit = 10**view.decimals

    def amt(self, raw: int | float) -> str:
        return f"{raw / self.unit:,.0f} {self.view.asset_symbol}"

    def label(self, market_id: str) -> str:
        mp = self.view.market(market_id)
        return (
            f"{mp.collateral_symbol}/{self.view.asset_symbol} (LLTV {mp.lltv:.1%})"
            if mp
            else f"market {market_id[:10]}…"
        )

    def dep_fraction(self, st: VaultState | None = None) -> float:
        st = st or self.before
        return st.depositor_shares / st.total_supply if st.total_supply else 0.0

    def market_share(self, st: VaultState, market_id: str) -> float:
        m = st.markets.get(market_id)
        return m.vault_assets / st.total_assets if m and st.total_assets else 0.0

    def id_label(self, cid: str) -> str:
        for a in self.view.adapters:
            for mp in a.markets.values():
                for kind, x in cap_ids(a.address, mp).items():
                    if x == cid:
                        return {
                            "adapter": f"adapter {a.address[:10]}…",
                            "collateral": f"collateral {mp.collateral_symbol}",
                            "market": f"market {self.label(mp.id)}",
                        }[kind]
        return f"id {cid[:10]}…"


def _when(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _timelocked_text(ctx: Ctx, data_hex: str) -> tuple[str, str]:
    sig, args, what = describe_call(data_hex)
    name = sig.split("(")[0]
    if name.startswith(("increaseAbsoluteCap", "increaseRelativeCap")) and args:
        from eth_utils import keccak

        cid = "0x" + keccak(bytes.fromhex(args[0][2:])).hex()
        val = args[1]
        shown = f"{val / 1e18:.1%}" if "Relative" in name else ctx.amt(val)
        return f"{name} on {ctx.id_label(cid)} to {shown}", what
    if args:
        shown = ", ".join(str(a) if not isinstance(a, int) or a < 10**6 else f"{a:,}" for a in args)
        return f"{name}({shown})", what
    return name, what


def assess_event(e: Event, ctx: Ctx, held: set[str], dep: str | None) -> Alert | None:
    a = e.args
    tx = e.tx
    # ---- Morpho Blue, in a market the vault holds
    if e.contract == "blue":
        mid = a.get("id")
        if mid not in held:
            return None
        if e.name == "Liquidate":
            bad = a["badDebtAssets"]
            m = ctx.before.markets.get(mid)
            if bad and m and m.total_supply_shares:
                vault_loss = bad * m.supply_shares / m.total_supply_shares
                dep_loss = vault_loss * ctx.dep_fraction()
                return Alert(
                    "critical",
                    e.block,
                    tx,
                    "Blue.Liquidate",
                    f"Bad debt in {ctx.label(mid)}",
                    f"{ctx.amt(bad)} of bad debt realised; the vault's share {ctx.amt(vault_loss)}"
                    + (f", yours {ctx.amt(dep_loss)}" if dep else ""),
                    -dep_loss / ctx.unit if dep else None,
                    {"market": mid, "badDebtAssets": bad, "vault_loss": vault_loss},
                )
            return Alert(
                "info",
                e.block,
                tx,
                "Blue.Liquidate",
                f"Liquidation in {ctx.label(mid)}",
                f"{ctx.amt(a['repaidAssets'])} repaid, no bad debt",
                None,
                {"market": mid},
            )
        if e.name in ("Withdraw", "Borrow"):
            b, af = ctx.before.markets.get(mid), ctx.after.markets.get(mid)
            share = ctx.market_share(ctx.after, mid)
            if (
                af
                and af.utilization >= W["utilization_warn"]
                and (not b or b.utilization < W["utilization_warn"])
                and share >= W["utilization_min_share"]
            ):
                return Alert(
                    "warn",
                    e.block,
                    tx,
                    f"Blue.{e.name}",
                    f"{ctx.label(mid)} is {af.utilization:.1%} utilised",
                    f"holds {share:.0%} of the vault; only {ctx.amt(af.liquidity)} can leave this market now",
                    None,
                    {"market": mid, "utilization": af.utilization},
                )
            return None
        if e.name == "SetFee":
            return Alert(
                "info",
                e.block,
                tx,
                "Blue.SetFee",
                f"Protocol fee changed on {ctx.label(mid)}",
                f"new fee {a['newFee'] / 1e18:.1%} of interest",
                None,
                {"market": mid},
            )
        return None

    # ---- the vault's MorphoMarketV1AdapterV2
    if e.contract == "adapter":
        if e.name in ("Allocate", "Deallocate"):
            mid = a["marketId"]
            new = a["newAllocation"]
            share = new / ctx.after.total_assets if ctx.after.total_assets else 0
            before_share = ctx.market_share(ctx.before, mid)
            level = "warn" if share > W["market_share_warn"] >= before_share else "info"
            title = ("New market: " if mid not in held else "") + f"{e.name} {ctx.label(mid)}"
            return Alert(
                level if mid in held else "warn",
                e.block,
                tx,
                f"Adapter.{e.name}",
                title,
                f"allocation now {ctx.amt(new)} ({share:.0%} of the vault, was {before_share:.0%})",
                None,
                {"market": mid, "newAllocation": new, "share": share},
            )
        if e.name == "BurnShares":
            mid = a["marketId"]
            m = ctx.before.markets.get(mid)
            lost = (
                a["supplyShares"] * m.total_supply_assets / m.total_supply_shares if m and m.total_supply_shares else 0
            )
            return Alert(
                "critical",
                e.block,
                tx,
                "Adapter.BurnShares",
                f"Supply shares written off in {ctx.label(mid)}",
                f"about {ctx.amt(lost)} removed from the vault's assets",
                -lost * ctx.dep_fraction() / ctx.unit if dep else None,
                {"market": mid, "supplyShares": a["supplyShares"]},
            )
        # shared timelock events fall through to the vault branch, labelled as the adapter's

    # ---- the vault (and the adapter's timelock)
    who = "Adapter" if e.contract == "adapter" else "Vault"
    if e.name == "AccrueInterest" and e.contract == "vault":
        prev, new = a["previousTotalAssets"], a["newTotalAssets"]
        if new < prev:
            loss = (prev - new) * ctx.dep_fraction()
            return Alert(
                "critical",
                e.block,
                tx,
                "Vault.AccrueInterest",
                "Vault total assets fell",
                f"{ctx.amt(prev)} → {ctx.amt(new)} ({(new - prev) / prev:+.3%})"
                + (f"; yours −{ctx.amt(loss)}" if dep else ""),
                -loss / ctx.unit if dep else None,
                {"previous": prev, "new": new},
            )
        return None
    if e.name == "Submit":
        what, why = _timelocked_text(ctx, a["data"])
        tl = ctx.view.timelock_of(e.address, a["data"][2:10])
        no_notice = bool(tl and tl[1] == 0 and tl[0] in RISK_INCREASING_VAULT + RISK_INCREASING_ADAPTER)
        return Alert(
            "critical" if no_notice else "warn",
            e.block,
            tx,
            f"{who}.Submit",
            ("Pending change with no notice: " if no_notice else "Pending change: ") + what,
            f"{why}; executable from {_when(a['executableAt'])}"
            + (
                " (timelock 0: it can be executed in the same block)"
                if no_notice
                else f" (timelock {tl[1] / 86400:g} days)"
                if tl
                else ""
            ),
            None,
            {"data": a["data"], "executableAt": a["executableAt"], "timelock": tl[1] if tl else None},
        )
    if e.name == "Accept":
        what, why = _timelocked_text(ctx, a["data"])
        return Alert("warn", e.block, tx, f"{who}.Accept", f"Change now live: {what}", why, None, {"data": a["data"]})
    if e.name == "Revoke":
        what, _ = _timelocked_text(ctx, a["data"])
        return Alert(
            "info", e.block, tx, f"{who}.Revoke", f"Pending change cancelled: {what}", "", None, {"data": a["data"]}
        )
    if e.name == "ForceDeallocate":
        return Alert(
            "warn",
            e.block,
            tx,
            "Vault.ForceDeallocate",
            "Liquidity forced out of an adapter",
            f"{ctx.amt(a['assets'])} pulled from {a['adapter'][:10]}…, penalty {ctx.amt(a['penaltyAssets'])}",
            None,
            {"assets": a["assets"], "penalty": a["penaltyAssets"]},
        )
    if e.name in ("Allocate", "Deallocate"):
        known = any(x.address == a["adapter"] and x.kind == "market" for x in ctx.view.adapters)
        if known:
            return None  # the adapter's own event says which market
        return Alert(
            "info",
            e.block,
            tx,
            f"Vault.{e.name}",
            f"{e.name} through adapter {a['adapter'][:10]}…",
            f"{ctx.amt(a['assets'])} (opaque adapter: its markets are not expanded, D23)",
            None,
            {"adapter": a["adapter"]},
        )
    if e.name == "SetLiquidityAdapterAndData":
        return Alert(
            "warn",
            e.block,
            tx,
            "Vault.SetLiquidityAdapterAndData",
            "Deposits and withdrawals now go through another adapter",
            f"new liquidity adapter {a['newLiquidityAdapter']}",
            None,
            {"adapter": a["newLiquidityAdapter"]},
        )
    if e.name in ("Deposit", "Withdraw", "Transfer"):
        mine = dep and dep in (a.get("onBehalf"), a.get("receiver"), a.get("from"), a.get("to"))
        if e.name == "Transfer":
            return (
                None
                if not mine
                else Alert(
                    "info",
                    e.block,
                    tx,
                    "Vault.Transfer",
                    "Your vault shares moved",
                    f"{a['shares'] / 10**18:,.4f} shares {a['from'][:10]}… → {a['to'][:10]}…",
                    None,
                    {},
                )
            )
        size = a["assets"] / ctx.before.total_assets if ctx.before.total_assets else 0
        if mine or size >= W["large_flow_info"]:
            return Alert(
                "info",
                e.block,
                tx,
                f"Vault.{e.name}",
                ("Your " if mine else "Large ") + e.name.lower(),
                f"{ctx.amt(a['assets'])} ({size:.1%} of the vault)",
                None,
                {"assets": a["assets"]},
            )
        return None
    if e.name in ("DecreaseAbsoluteCap", "DecreaseRelativeCap"):
        v = a.get("newAbsoluteCap", a.get("newRelativeCap"))
        shown = ctx.amt(v) if "Absolute" in e.name else f"{v / 1e18:.1%}"
        return Alert(
            "info",
            e.block,
            tx,
            f"Vault.{e.name}",
            f"Cap lowered on {ctx.id_label(a['id'])}",
            f"to {shown}",
            None,
            {"id": a["id"]},
        )
    if e.name in ("IncreaseAbsoluteCap", "IncreaseRelativeCap"):
        v = a.get("newAbsoluteCap", a.get("newRelativeCap"))
        shown = ctx.amt(v) if "Absolute" in e.name else f"{v / 1e18:.1%}"
        return Alert(
            "warn",
            e.block,
            tx,
            f"Vault.{e.name}",
            f"Cap raised on {ctx.id_label(a['id'])}",
            f"to {shown}",
            None,
            {"id": a["id"]},
        )
    if e.name in ("AddAdapter", "RemoveAdapter"):
        lvl = "warn" if e.name == "AddAdapter" else "info"
        return Alert(
            lvl,
            e.block,
            tx,
            f"Vault.{e.name}",
            f"{'New' if lvl == 'warn' else 'Removed'} adapter {a['account']}",
            "",
            None,
            {},
        )
    if e.name in ("SetPerformanceFee", "SetManagementFee"):
        v = a.get("newPerformanceFee", a.get("newManagementFee"))
        return Alert(
            "warn",
            e.block,
            tx,
            f"Vault.{e.name}",
            f"{e.name[3:]} set to {v / 1e18:.2%}" + (" per year" if "Management" in e.name else ""),
            "",
            None,
            {},
        )
    if e.name in (
        "SetReceiveSharesGate",
        "SetSendSharesGate",
        "SetReceiveAssetsGate",
        "SetSendAssetsGate",
        "SetAdapterRegistry",
        "SetCurator",
        "SetOwner",
        "SetIsAllocator",
        "SetIsSentinel",
        "DecreaseTimelock",
        "IncreaseTimelock",
        "Abdicate",
        "SetForceDeallocatePenalty",
        "SetMaxRate",
    ):
        detail = ", ".join(f"{k}={v}" for k, v in a.items())
        lvl = "info" if e.name in ("IncreaseTimelock", "Abdicate", "SetIsSentinel", "SetMaxRate") else "warn"
        return Alert(lvl, e.block, tx, f"{who}.{e.name}", f"Vault configuration: {e.name}", detail, None, {})
    return None


def assess_state(ctx: Ctx, dep: str | None, block: int) -> list[Alert]:
    """Rules that compare two state reads, independent of any one event."""
    out = []
    b, af = ctx.before, ctx.after
    for mid, m in af.markets.items():
        p0 = b.markets.get(mid).oracle_price if mid in b.markets else None
        if p0 and m.oracle_price and m.vault_assets:
            move = m.oracle_price / p0 - 1
            if abs(move) >= W["oracle_move_warn"]:
                out.append(
                    Alert(
                        "warn",
                        block,
                        None,
                        "Oracle",
                        f"Oracle of {ctx.label(mid)} moved {move:+.1%}",
                        f"the vault has {ctx.amt(m.vault_assets)} lent against this collateral",
                        None,
                        {"market": mid, "move": move},
                    )
                )
    if af.pending_loss and not b.pending_loss:
        dep_loss = af.pending_loss * ctx.dep_fraction(af)
        out.append(
            Alert(
                "critical",
                block,
                None,
                "PendingLoss",
                "Loss recorded by an adapter, not yet accrued",
                f"totalAssets() is {ctx.amt(af.pending_loss)} below the stored total; every deposit and withdrawal "
                "accrues it first, so it is already in the price they use"
                + (f"; your share {ctx.amt(dep_loss)}" if dep else ""),
                -dep_loss / ctx.unit if dep else None,
                {"pending_loss": af.pending_loss},
            )
        )
    if dep:
        need, can = af.depositor_assets, af.withdrawable
        if need > can and b.depositor_assets <= b.withdrawable:
            out.append(
                Alert(
                    "warn",
                    block,
                    None,
                    "Liquidity",
                    "You can no longer exit in full with a plain withdrawal",
                    _exit_detail(ctx, af),
                    None,
                    {"need": need, "withdrawable": can},
                )
            )
        for attr, what in (
            ("can_send_shares", "send your shares (withdraw, redeem, transfer)"),
            ("can_receive_assets", "receive assets on withdraw"),
        ):
            if getattr(af, attr) is False and getattr(b, attr) is not False:
                out.append(
                    Alert(
                        "warn",
                        block,
                        None,
                        "Gate",
                        f"A gate now blocks you: you cannot {what}",
                        "check the vault's gates (canSendShares / canReceiveAssets)",
                        None,
                        {},
                    )
                )
    return out


def _exit_detail(ctx: Ctx, st: VaultState) -> str:
    pens = {p for p in st.penalties.values()}
    pen = f"{max(pens) / 1e18:.2%}" if pens else "n/a"
    return (
        f"your {ctx.amt(st.depositor_assets)} vs {ctx.amt(st.withdrawable)} payable by a plain withdrawal "
        f"(idle{' + liquidity market' if st.liquidity_market else ', no liquidity adapter'}); "
        f"{ctx.amt(st.force_withdrawable)} more reachable only through forceDeallocate, penalty up to {pen}"
    )


def assess_batch(events: list[Event], ctx: Ctx, dep: str | None, block: int) -> list[Alert]:
    held = set(ctx.view.market_ids)
    out = [x for e in events if not e.removed for x in [assess_event(e, ctx, held, dep)] if x]
    out += assess_state(ctx, dep, block)
    return out


def startup_findings(view: VaultView, st: VaultState) -> list[Alert]:
    """Standing conditions worth a line when the watch starts."""
    ctx = Ctx(view, st, st)
    out = []
    for mid, m in st.markets.items():
        share = ctx.market_share(st, mid)
        if share > W["market_share_warn"]:
            out.append(
                Alert(
                    "warn",
                    st.block,
                    None,
                    "Exposure",
                    f"{share:.0%} of the vault is in {ctx.label(mid)}",
                    f"{ctx.amt(m.vault_assets)}; a bad debt there is shared by every depositor",
                    None,
                    {"market": mid},
                )
            )
    for a in view.adapters:
        for mp in a.markets.values():
            alloc, abs_cap, rel_cap = st.caps.get(cap_ids(a.address, mp)["market"], (0, 0, 0))
            if alloc >= ctx.unit and abs_cap == 0:
                out.append(
                    Alert(
                        "info",
                        st.block,
                        None,
                        "Caps",
                        f"{ctx.label(mp.id)} is being wound down",
                        f"its cap is 0 but {ctx.amt(alloc)} is still allocated",
                        None,
                        {"market": mp.id},
                    )
                )
        if a.kind != "market":
            out.append(
                Alert(
                    "info",
                    st.block,
                    None,
                    "Structure",
                    f"Adapter {a.address[:10]}… is {a.kind}",
                    "watched as one opaque layer (D23)",
                    None,
                    {"adapter": a.address},
                )
            )
    if st.depositor and st.depositor_assets > st.withdrawable:
        out.append(
            Alert(
                "warn",
                st.block,
                None,
                "Liquidity",
                "You cannot exit in full with a plain withdrawal",
                _exit_detail(ctx, st),
                None,
                {},
            )
        )
    if st.depositor and (st.can_send_shares is False or st.can_receive_assets is False):
        out.append(
            Alert(
                "warn",
                st.block,
                None,
                "Gate",
                "A gate blocks your exit",
                f"canSendShares={st.can_send_shares}, canReceiveAssets={st.can_receive_assets}",
                None,
                {},
            )
        )
    if st.pending_loss:
        out.append(
            Alert(
                "critical",
                st.block,
                None,
                "PendingLoss",
                "Loss recorded by an adapter, not yet accrued",
                f"totalAssets() is {ctx.amt(st.pending_loss)} below the stored total",
                None,
                {},
            )
        )
    no_notice = [
        sig.split("(")[0] + ("" if c == view.address else " (adapter)")
        for (c, sig), (t, ab) in view.timelocks.items()
        if t == 0 and not ab and sig in RISK_INCREASING_VAULT + RISK_INCREASING_ADAPTER
    ]
    if no_notice:
        out.append(
            Alert(
                "warn",
                st.block,
                None,
                "Timelock",
                f"{len(no_notice)} risk-increasing change(s) can be made with no notice",
                "timelock 0, not abdicated: "
                + ", ".join(no_notice)
                + ". A Submit for one of them gives no warning period",
                None,
                {"functions": no_notice},
            )
        )
    zero_pen = [a for a, p in st.penalties.items() if p == 0]
    if zero_pen:
        out.append(
            Alert(
                "info",
                st.block,
                None,
                "Structure",
                "forceDeallocate is free on some adapters",
                "a zero penalty lets anyone pull those positions back to idle at no cost (griefing, yield loss): "
                + ", ".join(a[:10] + "…" for a in zero_pen),
                None,
                {},
            )
        )
    return out
