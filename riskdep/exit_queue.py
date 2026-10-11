"""Run / queue model for a Vault V2 depositor's exit (plan 2026-10-10-exit-queue, D62–D67).

Liquidity is first come, first served, and a loss Blue has not written off yet is not in the share price, so in a
crisis exiting early is rational and the loss lands on whoever is still in the vault (Team 2, "Run / queue model").
With A the depositor's assets, T the vault's total, W = W_plain + W_forced what can leave now and q the other
depositors' assets that leave before the depositor:

  recovered at par   R(q) = min(A, max(0, W − q))      forced part pays the adapter's penalty
  stuck              S(q) = A − R(q)
  loss rate          ρ = min(1, L / (T − W))            the run drains W before the write-off (D63)
  depositor's loss   S(q) · ρ + penalty                 against A · L / T if the loss were shared pro rata
  last out, later    min(A, X) · L / X                  once healthy markets repay, the last holders keep only
                                                        the X assets of the markets that carry the loss L
"""

from __future__ import annotations

from dataclasses import dataclass

from . import sources as S
from .discover import REGISTRY
from .market_risk import CURVE_DROPS, MarketRisk, vault_supply_shares
from .rules import Alert

W = REGISTRY["watch"]


@dataclass
class Holder:
    address: str
    assets: int
    fast: bool | None  # a contract (vault, fund, multisig) reacts fast, a plain wallet slowly; None: unknown


@dataclass
class Liquidity:
    total: int  # T, the vault's total assets
    position: int  # A, the depositor's assets
    plain: int  # W_plain: idle + liquidity market
    forced: int  # W_forced: the other markets' unborrowed part, via forceDeallocate
    penalty: float  # forceDeallocate penalty on the forced part (fraction)

    @property
    def available(self) -> int:
        return self.plain + self.forced


@dataclass
class Exit:
    queue: int  # q, other depositors' assets ahead
    par: int  # R, recovered at par
    forced: int  # of which via forceDeallocate
    penalty: int
    stuck: int


@dataclass
class LossCase:
    name: str
    loss: int  # L, the vault's share of the bad debt
    exposure: int  # X, the vault's assets in the markets that carry it


# --- pure


def exit_at(liq: Liquidity, q: int) -> Exit:
    """What the depositor gets with q of other depositors' assets ahead in the queue (plain liquidity goes first)."""
    q = max(0, q)
    par = min(liq.position, max(0, liq.available - q))
    forced = max(0, min(q + par, liq.available) - max(q, liq.plain))
    pen = int(forced * liq.penalty)
    return Exit(q, par, forced, pen, liq.position - par)


def loss_rate(liq: Liquidity, loss: int) -> float:
    """ρ: the loss per unit left in the vault once the run has drained what can leave (D63)."""
    left = liq.total - liq.available
    if loss <= 0:
        return 0.0
    return 1.0 if left <= 0 else min(1.0, loss / left)


def depositor_loss(liq: Liquidity, ex: Exit, case: LossCase) -> int:
    return int(ex.stuck * loss_rate(liq, case.loss)) + ex.penalty


def pro_rata_loss(liq: Liquidity, case: LossCase) -> int:
    return int(liq.position * case.loss / liq.total) if liq.total else 0


def last_out_loss(liq: Liquidity, case: LossCase) -> int:
    """Upper bound: healthy markets repay over time, everyone else leaves, the last holders keep the toxic part."""
    if case.loss <= 0 or case.exposure <= 0:
        return 0
    return min(case.loss, int(min(liq.position, case.exposure) * case.loss / case.exposure))


def queue_points(liq: Liquidity, holders: list[Holder], depositor: str | None) -> list[tuple[str, int]]:
    """Named queue positions (D64): first out, behind the fast holders, behind a share φ of the others, last."""
    others = max(0, liq.total - liq.position)
    fast = sum(h.assets for h in holders if h.fast and h.address != depositor)
    phi = W["exit_queue_phi"]
    pts = [("first out", 0)]
    if holders:
        pts.append(("behind contracts", min(fast, others)))
    pts += [(f"behind {phi:.0%} of others", int(phi * others)), ("last of the run", others)]
    return pts


def loss_cases(risks: dict[str, MarketRisk], shares: dict[str, float], vault_assets: dict[str, int]) -> list[LossCase]:
    """D65: the bad debt now (unrealised), and if every collateral fell by each curve step at once."""

    def case(name: str, bd: dict[str, int]) -> LossCase:
        loss = sum(int(b * shares.get(mid, 0.0)) for mid, b in bd.items())
        return LossCase(name, loss, sum(vault_assets.get(mid, 0) for mid, b in bd.items() if b > 0))

    out = [case("now", {mid: r.unrealised_bad_debt for mid, r in risks.items()})]
    for d in CURVE_DROPS:
        bd = {mid: p.bad_debt for mid, r in risks.items() if (p := r.point(d))}
        out.append(case(f"all collateral −{d:.0%}", bd))
    return out


def vault_cases(risk, st) -> list[LossCase]:
    """Loss cases for a `market_risk.VaultRisk` and a `vault.VaultState`."""
    return loss_cases(
        risk.risks,
        vault_supply_shares(st, risk.markets),
        {mid: st.markets[mid].vault_assets for mid in risk.markets if mid in st.markets},
    )


def alert_point(liq: Liquidity, holders: list[Holder], depositor: str | None) -> tuple[str, int]:
    """The queue position the alert measures (D66): behind every contract holder, or behind the share φ of the
    other depositors when the holders are unknown."""
    pts = dict(queue_points(liq, holders, depositor))
    name = "behind contracts" if "behind contracts" in pts else f"behind {W['exit_queue_phi']:.0%} of others"
    return name, pts[name]


def assess(
    before: tuple[float, int] | None,
    after: tuple[float, int],
    point: str,
    label: str,
    unit: int,
    symbol: str,
    block: int,
) -> list[Alert]:
    """D66: (stuck share at the alert's queue position, the vault's loss now) → warn when at least
    exit_queue_stuck_warn of the position would be stuck there; critical when, in addition, the vault already carries
    unrealised bad debt for the stuck part to absorb. On crossing."""

    def level(x: tuple[float, int] | None) -> int:
        if x is None:
            return 0
        stuck, loss = x
        return 0 if stuck < W["exit_queue_stuck_warn"] else (2 if loss > 0 else 1)

    l0, l1 = level(before), level(after)
    if l1 <= l0:
        return []
    stuck, loss = after
    who = (
        "every contract holder (vault, fund, multisig)"
        if point == "behind contracts"
        else f"{W['exit_queue_phi']:.0%} of the other depositors (holders unknown)"
    )
    return [
        Alert(
            "critical" if l1 == 2 else "warn",
            block,
            None,
            "ExitQueue",
            f"{stuck:.0%} of your position in {label} would be stuck in a run",
            f"if {who} withdrew before you, what can leave the vault now would not pay out the rest"
            + (
                f"; {loss / unit:,.0f} {symbol} of bad debt is not written off yet and would fall on those "
                "still in the vault"
                if loss
                else ""
            ),
            None,
            {"stuck_share": round(stuck, 4), "queue_position": point, "loss_now": loss},
        )
    ]


def table(
    lines,
    liq: Liquidity,
    holders: list[Holder],
    depositor: str | None,
    cases: list[LossCase],
    unit: int,
    symbol: str,
    coverage: str,
) -> None:
    """Print the exit queue: what the depositor recovers at each queue position, and the loss in each case."""
    pts = queue_points(liq, holders, depositor)
    lines(f"  exit queue ({coverage}):")
    lines(
        f"    position {liq.position / unit:,.0f} {symbol} · can leave now {liq.available / unit:,.0f} "
        f"({liq.plain / unit:,.0f} plain + {liq.forced / unit:,.0f} forced at {liq.penalty:.2%})"
    )
    lines(f"    {'queue position':<24} {'others ahead':>14} {'at par':>14} {'stuck':>14}")
    for name, q in pts:
        ex = exit_at(liq, q)
        lines(f"    {name:<24} {q / unit:>14,.0f} {ex.par / unit:>14,.0f} {ex.stuck / unit:>14,.0f}")
    heads = ["pro rata"] + [n for n, _ in pts] + ["last out, later"]
    lines(f"    {'your loss, ' + symbol:<22}" + " ".join(f"{h:>22}" for h in heads))
    for c in cases:
        vals = [pro_rata_loss(liq, c)] + [depositor_loss(liq, exit_at(liq, q), c) for _, q in pts]
        vals.append(last_out_loss(liq, c))
        lines(f"    {c.name:<22}" + " ".join(f"{v / unit:>22,.0f}" for v in vals))


# --- I/O


def holders(f: S.Fetcher, vault: str, total_assets: int, total_supply: int) -> tuple[list[Holder], int]:
    """The vault's holders from the Morpho API (first 100, D64), in assets at the on-chain share price, each marked
    fast (has code) or slow; returns (holders, the API's holder count). Empty if the API cannot answer."""
    try:
        d = S.morpho(
            f,
            """query($a:String!){ vaultV2ByAddress(address:$a, chainId:1){
              positions(first:100){ pageInfo{ countTotal } items{ user{ address } shares } } } }""",
            {"a": vault},
        )["vaultV2ByAddress"]["positions"]
    except (S.SourceError, S.CacheMiss, KeyError, TypeError):
        return [], 0
    rows = [(i["user"]["address"].lower(), int(i["shares"] or 0)) for i in d["items"]]
    try:
        codes = S.rpc_batch_methods(f, [("eth_getCode", [a, "latest"]) for a, _ in rows])
    except (S.SourceError, S.CacheMiss):
        codes = [None] * len(rows)
    from .zama import is_pool

    out = [
        # D172: a Zama cShare is a contract, but it pools many confidential depositors: not one fast holder ahead
        Holder(a, sh * total_assets // total_supply if total_supply else 0, False if is_pool(a) else _is_contract(c))
        for (a, sh), c in zip(rows, codes)
    ]
    return sorted(out, key=lambda h: -h.assets), int(d["pageInfo"]["countTotal"] or 0)


def _is_contract(code: str | None) -> bool | None:
    """Has code and is not an EIP-7702 delegated wallet (`0xef0100` + address), which a person still signs for."""
    if code is None:
        return None
    return code not in ("0x", "") and not code.startswith("0xef0100")


def liquidity(st, drained: int = 0) -> Liquidity:
    """From a `vault.VaultState`; the penalty is the highest of the adapters' (conservative). `drained` is what a drain
    of the markets past their threshold would take first (drain.py, D73): out of the forced part, then the plain."""
    pen = max(st.penalties.values(), default=0) / 10**18
    forced = max(0, st.force_withdrawable - drained)
    plain = max(0, st.withdrawable - max(0, drained - st.force_withdrawable))
    return Liquidity(st.total_assets, st.depositor_assets, plain, forced, pen)


class VaultExit:
    """The exit queue of one depositor in one vault, used by both watches. Holders are re-read on refresh."""

    def __init__(self, f, view, st):
        self.view = view
        self.holders, self.count = holders(f, view.address, st.total_assets, st.total_supply)
        self.state: tuple[float, int] | None = None

    def coverage(self, liq: Liquidity, depositor: str | None) -> str:
        if not self.holders:
            return "holders unknown: the Morpho API did not answer"
        listed = sum(h.assets for h in self.holders)
        fast = sum(h.assets for h in self.holders if h.fast and h.address != depositor)
        unknown = sum(1 for h in self.holders if h.fast is None)
        return (
            f"{len(self.holders)} of {self.count} holders listed, {listed / liq.total:.1%} of the vault; "
            f"other contracts hold {fast / liq.total:.1%}" + (f"; {unknown} not classified" if unknown else "")
            if liq.total
            else "empty vault"
        )

    def measure(self, st, cases: list[LossCase], drained: int = 0) -> tuple[str, tuple[float, int]]:
        """(the alert's queue position, (stuck share there, the vault's loss not written off yet))."""
        liq = liquidity(st, drained)
        name, q = alert_point(liq, self.holders, st.depositor)
        stuck = exit_at(liq, q).stuck / liq.position if liq.position else 0.0
        return name, (stuck, next((c.loss for c in cases if c.name == "now"), 0))

    def startup(self, lines, st, cases: list[LossCase], block: int, drained: int = 0) -> list[Alert]:
        if not st.depositor or not st.depositor_assets:
            return []
        liq, unit = liquidity(st, drained), 10**self.view.decimals
        if drained:
            lines(
                f"  exit queue: {drained / unit:,.0f} {self.view.asset_symbol} left out, drainable now (drain threshold)"
            )
        table(
            lines,
            liq,
            self.holders,
            st.depositor,
            cases,
            unit,
            self.view.asset_symbol,
            self.coverage(liq, st.depositor),
        )
        return self.step(st, cases, block, drained=drained)

    def step(self, st, cases: list[LossCase], block: int, f=None, drained: int = 0) -> list[Alert]:
        if not st.depositor or not st.depositor_assets:
            return []
        if f is not None:
            self.holders, self.count = holders(f, self.view.address, st.total_assets, st.total_supply)
        point, after = self.measure(st, cases, drained)
        alerts = assess(self.state, after, point, self.view.name, 10**self.view.decimals, self.view.asset_symbol, block)
        self.state = after
        return alerts
