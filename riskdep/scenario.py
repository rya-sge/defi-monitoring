"""Incident mode: a known incident, what it does to one position, how fast, and what to do
(plan 2026-10-10-incident-mode, D89–D95).

The Monte Carlo answers an unconditional question (what to expect over a horizon, from yearly probabilities). The brief
asks a conditional one: a component *is* hit. Here the incident is given, so no probability enters:

  impact      `propagate.loss` with the observed shocks, the same rule the simulation uses on each path
  how fast    the time before the oracle passes the shock to the position, from the oracle's type (D91)
  decision    staying loses the impact; leaving costs the exit quote; a partial sale may cost less (D90)

The watches call `alert_impact` when an alert carries a measured incident (D93), so an alert says what it costs.
"""

from __future__ import annotations

import copy
import math
from dataclasses import asdict, dataclass, field

from . import decide
from . import oracle_class as OC
from . import pendle_amm as PA
from . import sources as S
from .discover import REGISTRY, Position, morpho_lif
from .propagate import LossBreakdown, loss
from .vault import _call

EVENTS = ("chain", "issuer_hack", "issuer_depeg", "amm", "oracle", "lending", "pt_yield", "borrow_rate", "pool_move")
POOL_MOVE_MAX = 5.0  # pool_move is a sale in multiples of the pool's liquidity, up to the quote ladder's largest
META_ORACLE = "MetaOracleDeviationTimelock"
META_GETTERS = [
    "challengeTimelockDuration()",
    "healingTimelockDuration()",
    "deviationThreshold()",
    "currentOracle()",
    "primaryOracle()",
    "isChallenged()",
    "backupOracle()",
]
INCIDENT = REGISTRY["incident"]


@dataclass
class OracleProfile:
    """What decides how fast a shock reaches the price (D91)."""

    kind: str  # meta-oracle | price-tracking | constant-price | not classified
    basis: str
    name: str | None = None  # verified contract name (Etherscan), if known
    twap_s: int | None = None  # a Pendle TWAP input's window
    timelock_s: int | None = None  # a meta-oracle's challenge timelock
    deviation_threshold: float | None = None
    on_primary: bool | None = None  # a meta-oracle reading its primary source
    challenged: bool | None = None
    constant_kind: str | None = None  # D205: a constant-price oracle's kind (`oracle_class.KINDS`)
    live: OracleProfile | None = None  # a meta-oracle's source in use, classified like any oracle
    other: OracleProfile | None = None  # the source it would switch to


@dataclass
class Timing:
    seconds: float | None  # None: never, or unknown (see `never`)
    never: bool
    text: str


@dataclass
class IncidentResult:
    shocks: dict[str, float]
    loss_usd: float
    loss_share_of_equity: float
    liquidated: bool
    oracle_drop: float  # how far the oracle's value of the collateral falls under the shocks
    path: list[str]
    timing: Timing
    exit_cost_usd: float
    exit_source: str
    verdict: str
    reason: str
    reduction: dict | None = None
    notes: list[str] = field(default_factory=list)
    after_switch: dict | None = None  # a meta-oracle: the impact once it switches to the source that follows the market
    pool_move: dict | None = None  # D204: the sale into the PT's pool, the price it leaves, the sale that liquidates
    stressed_exit: dict | None = None  # D206: the exit cost after the incident's own liquidations sell first

    def lines(self) -> list[str]:
        shock = ", ".join(f"{k} {v:.1%}" for k, v in self.shocks.items())
        out = [
            f"INCIDENT  {shock}",
            f"  {'liquidated' if self.liquidated else 'not liquidated'}; loss ${self.loss_usd:,.0f} "
            f"({self.loss_share_of_equity:.1%} of equity)",
            f"  how fast: {self.timing.text}",
            f"  exit now: ${self.exit_cost_usd:,.0f} ({self.exit_source})",
            *([f"  {self.stressed_exit['text']}"] if self.stressed_exit else []),
            f"  verdict given the incident: {self.verdict}: {self.reason}",
        ]
        if self.after_switch:
            a = self.after_switch
            out.insert(
                2,
                f"  after the oracle switches ({a['after']}): {'liquidated' if a['liquidated'] else 'not liquidated'}; "
                f"loss ${a['loss_usd']:,.0f} ({a['loss_share_of_equity']:.1%} of equity)",
            )
        out += [f"    · {p}" for p in self.path]
        out += [f"  note: {n}" for n in self.notes]
        return out

    def to_json(self) -> dict:
        return asdict(self)


# --- pure


def parse_shocks(items: list[str] | None) -> dict[str, float]:
    """`["oracle=0.10", "issuer_depeg=0.08"]` → `{"oracle": 0.1, "issuer_depeg": 0.08}`; a severity is a fraction."""
    out: dict[str, float] = {}
    for it in items or []:
        name, sep, value = it.partition("=")
        name = name.strip()
        if name not in EVENTS:
            raise ValueError(f"unknown event '{name}': use one of {', '.join(EVENTS)}")
        if not sep:
            raise ValueError(f"'{it}': give a severity, e.g. {name}=0.10")
        try:
            v = float(value)
        except ValueError:
            raise ValueError(f"'{it}': the severity must be a number between 0 and 1") from None
        if name == "pool_move" and not 0 < v <= POOL_MOVE_MAX:
            raise ValueError(f"'{it}': pool_move is a sale as a multiple of the pool's liquidity, above 0, at most 5")
        if name != "pool_move" and not 0 <= v <= 1:
            raise ValueError(f"'{it}': the severity must be between 0 and 1 (0.10 for 10 %)")
        out[name] = v
    return out


def oracle_mode_for(profile: OracleProfile | None, fallback: str) -> str:
    """The propagation mode an incident uses: from the oracle's class when it decides (D92), else the inference.
    A meta-oracle is read through the source it uses now."""
    if profile and profile.kind == "meta-oracle":
        return oracle_mode_for(profile.live, fallback)
    if profile and profile.kind == OC.PRICE_TRACKING:
        return "market-tracking"
    if profile and profile.kind == OC.CONSTANT_PRICE:
        return "fundamental"
    return fallback


def ex_ante_mode(profile: OracleProfile | None, horizon_days: float) -> tuple[str, str] | None:
    """D96, pure: the oracle mode the ex-ante simulation should use, from the oracle's structure; None when the
    structure does not decide (then `analyze` keeps its price inference). The simulation has no time axis, so a
    meta-oracle that switches to a source following the market within the horizon is treated as following it."""
    if profile is None or profile.kind == OC.NOT_CLASSIFIED:
        return None
    if profile.kind == OC.PRICE_TRACKING:
        return "market-tracking", f"from its structure: {profile.basis}"
    if profile.kind == OC.CONSTANT_PRICE:
        return "fundamental", f"from its structure: {profile.basis}"
    live, other = profile.live, profile.other
    if not live or live.kind == OC.NOT_CLASSIFIED:
        return None
    if live.kind == OC.PRICE_TRACKING:
        return "market-tracking", "a meta-oracle whose live source follows the market"
    lock = profile.timelock_s
    if other and other.kind == OC.PRICE_TRACKING and lock is not None:
        if lock / 86400 <= horizon_days:
            return (
                "market-tracking",
                f"a meta-oracle whose live source does not follow the market, but whose backup does and takes over "
                f"after {lock / 3600:g} h, within the {horizon_days:.0f}-day horizon",
            )
        return (
            "fundamental",
            f"a meta-oracle whose switch ({lock / 3600:g} h) falls after the {horizon_days:.0f}-day horizon",
        )
    return "fundamental", "a meta-oracle with no source that follows the market"


def time_to_impact(profile: OracleProfile | None, shocks: dict[str, float]) -> Timing:
    """D91: how long before the shocks reach the position's liquidation check."""
    if shocks.get("oracle"):
        return Timing(
            0.0, False, "now: the oracle already reports the shocked price; a liquidation can follow in the next block"
        )
    if any(shocks.get(e) for e in ("chain", "issuer_hack", "amm")):
        return Timing(
            0.0, False, "now: the loss of value reaches every oracle at once (exchange rates and backing fall together)"
        )
    if shocks.get("lending"):
        return Timing(0.0, False, "now: collateral taken from the market; no liquidation is involved")
    if shocks.get("pt_yield") and not shocks.get("issuer_depeg"):
        # D169: a rise of the implied yield moves the PT's market price, which reaches the oracle as a depeg would
        t = time_to_impact(profile, {"issuer_depeg": shocks["pt_yield"]})
        return Timing(t.seconds, t.never, "the PT's market price falls with the yield: " + t.text)
    if shocks.get("borrow_rate") and not shocks.get("issuer_depeg"):
        irm = REGISTRY["irm"]
        days = math.log(2) / irm["adjustment_speed_per_year"] * 365
        return Timing(
            None,
            False,
            f"gradual: the interest accrues every block; at 100 % utilisation Morpho's AdaptiveCurveIRM charges "
            f"{irm['curve_steepness']}× its rate at target, which then doubles about every {days:.0f} days",
        )
    if not shocks.get("issuer_depeg"):
        return Timing(None, False, "no shock")
    p = profile
    if p is None or p.kind == OC.NOT_CLASSIFIED:
        return Timing(None, False, "unknown: the oracle could not be classified")
    if p.kind == "meta-oracle":
        lock = f"{p.timelock_s / 3600:g} h" if p.timelock_s is not None else "its challenge timelock"
        thr = f"more than {p.deviation_threshold:.2%}" if p.deviation_threshold is not None else "past its threshold"
        side = "primary" if p.on_primary else "backup" if p.on_primary is False else "current"
        switch = f"if the two sources diverge by {thr}, a challenge can switch it to the other one after {lock}"
        live = time_to_impact(p.live, shocks) if p.live else None
        if live is None or p.live.kind == OC.NOT_CLASSIFIED:
            return Timing(None, False, f"unknown: the meta-oracle's {side} source could not be classified; {switch}")
        if live.never:
            other = p.other.kind if p.other else "unknown"
            return Timing(
                float(p.timelock_s) if p.timelock_s is not None else None,
                False,
                f"not before {lock}: the {side} source does not follow the market; {switch} "
                f"(the other source is {other})",
            )
        return Timing(live.seconds, False, f"{live.text} (through the {side} source); {switch}")
    if p.kind == OC.CONSTANT_PRICE:
        loss = f"; a loss the issuer records reaches it {OC.MOVES[p.constant_kind]}" if p.constant_kind else ""
        return Timing(
            None,
            True,
            "never: the oracle does not follow the market, so nobody is liquidated; the loss stays with the lenders"
            + (f" ({p.constant_kind}{loss})" if p.constant_kind else ""),
        )
    if p.twap_s:
        return Timing(
            float(p.twap_s), False, f"about {p.twap_s / 60:g} min: the oracle averages the pool over that window"
        )
    return Timing(None, False, "at the feed's next update (its heartbeat, or at once past its deviation threshold)")


def _twap(probes: list[OC.Probe]) -> int | None:
    for p in probes:
        v = p.getters.get("twapDuration()")
        if v:
            return v
        kid = _twap(p.children)
        if kid:
            return kid
    return None


# --- I/O


def oracle_profile(f: S.Fetcher, oracle: str, block="latest") -> OracleProfile:
    """Read what decides the timing: a meta-oracle's timelock, or the class of the oracle's inputs (`oracle_class`)."""
    oracle = oracle.lower()
    try:
        code = S.rpc(f, "eth_getCode", [oracle, "latest"]) or ""
        target = "0x" + code[22:62] if code.startswith("0x363d3d373d3d3d363d73") else oracle
        src = S.contract_source(f, target)
        name = src.get("name") if src else None
        if name == META_ORACLE:
            res = S.rpc_batch(f, [_call(oracle, g) for g in META_GETTERS], block)
            w = [int(r, 16) if r and r != "0x" else None for r in res]
            cur = ("0x" + res[3][-40:]).lower() if res[3] else None
            pri = ("0x" + res[4][-40:]).lower() if res[4] else None
            bak = ("0x" + res[6][-40:]).lower() if res[6] else None
            live = oracle_profile(f, cur, block) if cur else None
            other = oracle_profile(f, bak if cur == pri else pri, block) if pri and bak else None
            return OracleProfile(
                "meta-oracle",
                f"{META_ORACLE}: switches between a primary and a backup oracle after a timelocked challenge",
                name,
                timelock_s=w[0],
                deviation_threshold=w[2] / 1e18 if w[2] is not None else None,
                on_primary=(cur == pri) if cur and pri else None,
                challenged=bool(w[5]) if w[5] is not None else None,
                live=live,
                other=other,
            )
        cls, basis, base, _, standard = OC.classify_market_oracle(f, oracle, block)
        return OracleProfile(
            cls, basis, name, twap_s=_twap(base), constant_kind=OC.oracle_constant_kind(base, standard)
        )
    except (S.SourceError, S.CacheMiss, ValueError) as e:
        return OracleProfile(OC.NOT_CLASSIFIED, f"not read: {str(e)[:80]}")


def pt_fall(pos: Position, shocks: dict[str, float]) -> float:
    """D169, pure: the PT's market price fall a rise of its implied yield causes."""
    s, years = shocks.get("pt_yield", 0.0), pos.days_to_maturity / 365
    return 1 - ((1 + pos.implied_apy) / (1 + pos.implied_apy + s)) ** years if s and years > 0 else 0.0


def sold_ahead(curve: list[dict], fall: float, own_drop: float | None, own_debt: float, lltv: float) -> float:
    """D206, pure: what the incident's liquidations sell before the position can, in the loan token: the other
    borrowers' debt liquidatable at `fall` (the market curve's last point at or below it) times the LIF."""
    pts = [p for p in curve or [] if p["oracle_fall"] <= fall + 1e-9]
    if not pts:
        return 0.0
    last = max(pts, key=lambda p: p["oracle_fall"])
    debt = last["liquidatable_debt"] - (own_debt if own_drop is not None and own_drop <= last["oracle_fall"] else 0.0)
    return max(0.0, debt) * morpho_lif(lltv)


def slice_loss(out: dict[float, int], small: float, ahead: float, x: float) -> float | None:
    """D206, pure: the share of `x` (USD at today's price) lost selling it after `ahead` was sold, from quotes `out`
    (USD sold → amount out) at `small`, `ahead`, `x` and `ahead + x`; None when a size was not quoted."""
    if any(s not in out for s in (small, ahead + x)) or (ahead and ahead not in out) or not out[small]:
        return None
    rate = out[small] / small
    return 1 - (out[ahead + x] - (out[ahead] if ahead else 0)) / (x * rate)


def stressed_exit(cost_now: float, out: dict[float, int], small: float, ahead: float, x: float, refused: bool) -> dict:
    """D206, pure: the exit cost once the incident's liquidations sold `ahead` first, as today's cost plus the extra
    slippage of selling the position's `x` after them, both read off one quote ladder (USD sold → amount out). When
    Pendle stops routing before `ahead + x`, only the part it still routes can leave: `cost_usd` is then None."""
    now = slice_loss(out, small, 0.0, x)
    routed = max((s for s in out if s >= ahead), default=0.0) if (ahead in out) else 0.0
    sellable = min(x, max(0.0, routed - ahead))
    base = {"ahead_usd": ahead, "slippage_now": now, "sellable_usd": sellable}
    if now is not None and sellable >= x:
        then = slice_loss(out, small, ahead, x)
        cost = cost_now + max(0.0, then - now) * x
        return {
            **base,
            "cost_usd": cost,
            "slippage_after": then,
            "full_exit": True,
            "text": f"exit after the incident's liquidations sell {ahead:,.0f} first: ${cost:,.0f} "
            f"(slippage {now:.2%} today, {then:.2%} after them)",
        }
    part = slice_loss(out, small, ahead, sellable) if sellable > 0 else None
    return {
        **base,
        "cost_usd": None,
        "slippage_after": part,
        "full_exit": False,
        "text": f"after the incident's liquidations sell {ahead:,.0f} first, Pendle routes "
        + (
            f"only {sellable:,.0f} more ({sellable / x:.0%} of the position, slippage {part:.2%}): a full exit is not "
            "available, the rest waits for the pool to recover or for maturity"
            if sellable > 0 and part is not None
            else "no more of the position: a full exit through Pendle is not available"
            if refused
            else "a size that was not quoted"
        ),
    }


def pool_move(pos: Position, pool: PA.Pool, x: float) -> tuple[float, dict]:
    """D204, D211, pure: a sale of `x` times the pool's liquidity of the PT into its Pendle pool, priced by the pool's
    own math (`pendle_amm`, the rate the oracle's TWAP reads; the router's limit orders left out), as the implied-yield
    rise the `pt_yield` channel prices; with the sale that would liquidate the position through a price-tracking
    oracle, or the largest sale the pool accepts and its fall."""
    usd_per_pt = pos.collateral_usd / pos.collateral_units if pos.collateral_units else 0.0
    liq, cap = pos.amm_liquidity_usd or 0.0, PA.max_sale(pool)
    sold = x * liq
    q = min(sold / usd_per_pt if usd_per_pt else 0.0, cap * (1 - 1e-9))
    ln0, years = pool.last_ln_rate, pool.t / PA.YEAR

    def fall_of(pt: float) -> float:
        r = PA.sell_pt(pool, pt)
        return 1 - math.exp(-(r[1] - ln0) * years) if r else 0.0

    moved = PA.sell_pt(pool, q)
    fall, top = fall_of(q), fall_of(cap * (1 - 1e-9))
    ld = pos.liquidation_drop
    need = PA.sale_for_apy(pool, math.exp(ln0 - math.log(1 - ld) / years) - 1) if ld and years > 0 else None
    liquidating = need * usd_per_pt if need is not None else None
    beyond = sold > cap * usd_per_pt
    return (math.exp(moved[1]) - math.exp(ln0) if moved else 0.0), {
        "sold_usd": sold,
        "pool_liquidity_usd": liq,
        "pool_fall": fall,
        "liquidation_fall": ld,
        "liquidating_sale_usd": liquidating,
        "beyond_pool": beyond,
        "max_sale_usd": cap * usd_per_pt,
        "pool_block": pool.block,
        "text": (
            f"a sale of {sold:,.0f} USD of PT into its Pendle pool ({x:g}× its liquidity) "
            + (
                f"leaves the pool's price {fall:.2%} lower (the pool's math at block {pool.block:,})"
                if not beyond
                else "is more than the pool accepts: counted as its largest sale"
            )
            + (
                f"; a price-tracking oracle liquidates the position after a sale of {liquidating:,.0f} USD"
                if liquidating
                else f"; the largest sale the pool accepts ({cap * usd_per_pt:,.0f} USD, its PT share at 96 %) moves "
                f"it {top:.2%}, short of the {ld:.2%} that liquidates the position"
                if ld
                else ""
            )
            + "; limit orders the router fills first would absorb part of a sale; the move must hold through the "
            "oracle's averaging window, and arbitrage can reverse it first"
        ),
    }


def assess(
    pos: Position,
    shocks: dict[str, float],
    recovery: float,
    quote: dict,
    profile: OracleProfile | None,
    quote_for=None,
    horizon_days: float = 30.0,
    stressed=None,
) -> IncidentResult:
    """The impact of a given incident on an `analyze` position, its timing and the verdict (D89, D90)."""
    mode = oracle_mode_for(profile, pos.oracle_mode)
    extra = REGISTRY["pt_stress_extra_discount"]
    kw = {
        "pt_years": pos.days_to_maturity / 365,
        "implied_apy": pos.implied_apy,
        "borrow_apy": pos.borrow_apy,
        "horizon_years": min(horizon_days, pos.days_to_maturity or horizon_days) / 365,
    }

    def run(p: Position) -> LossBreakdown:
        return loss(
            p.collateral_usd, p.debt_usd, p.lltv, p.lif, mode, shocks, recovery=recovery, pt_stress_extra=extra, **kw
        )

    b = run(pos)
    equity = max(pos.equity_usd, 1.0)
    after_switch, staying = None, b
    if (
        profile
        and profile.kind == "meta-oracle"
        and profile.live
        and profile.other
        and mode == "fundamental"
        and profile.other.kind == OC.PRICE_TRACKING
        and max(shocks.get("issuer_depeg", 0), pt_fall(pos, shocks)) > (profile.deviation_threshold or 0)
    ):
        # the depeg opens a challenge; once accepted, the oracle reads the source that follows the market
        sw = loss(pos.collateral_usd, pos.debt_usd, pos.lltv, pos.lif, "market-tracking", shocks, recovery, extra, **kw)
        lock = f"{profile.timelock_s / 3600:g} h" if profile.timelock_s is not None else "the challenge timelock"
        after_switch = {
            "after": lock,
            "loss_usd": sw.loss_usd,
            "loss_share_of_equity": sw.loss_usd / equity,
            "liquidated": sw.liquidated,
            "path": sw.path,
        }
        staying = sw
    oracle_drop = 1 - staying.oracle_value_usd / pos.collateral_usd if pos.collateral_usd else 0.0
    exit_cost = decide.exit_cost_usd(pos, quote)
    timing = time_to_impact(profile, shocks)
    stress = stressed(oracle_drop, exit_cost) if stressed else None
    if stress:
        # D206: an impact sooner than the exit window lets the liquidations sell first, so their price is the exit's
        soon = timing.seconds is None or timing.seconds < INCIDENT["exit_window_s"]
        stress["counted"] = soon and stress["cost_usd"] is not None
        if stress["counted"]:
            exit_cost = stress["cost_usd"]
        stress["text"] += (
            ": counted, the incident lands before a holder can leave"
            if stress["counted"]
            else "; the incident lands at once, so the verdict's exit and sale assume leaving before the liquidations"
            if soon
            else f"; leaving within {(timing.seconds or 0) / 3600:g} h comes before them, at today's quote"
        )
    reduction, red_cost, red_loss = None, None, None
    if staying.liquidated and pos.lltv:
        target = min(0.95, oracle_drop + INCIDENT["reduce_margin"])
        sell = decide.sale_to_reach(pos, target)
        if 0 < sell < pos.collateral_usd:
            frac = sell / pos.collateral_usd
            scaled = {
                "price_impact": quote["price_impact"] * frac,
                "fee_usd": quote["fee_usd"] * frac,
                "source": "scaled from the full quote",
            }
            try:
                q = quote_for(pos, frac) if quote_for else scaled
            except (S.SourceError, S.CacheMiss):
                q = {**scaled, "source": "scaled from the full quote (no quote at this size)"}
            red_cost = sell * q["price_impact"] + q["fee_usd"] + REGISTRY["gas_exit_usd"]
            smaller = copy.copy(pos)
            smaller.collateral_units = pos.collateral_units * (1 - frac)
            smaller.debt_usd = pos.debt_usd - sell
            sm = (
                loss(
                    smaller.collateral_usd,
                    smaller.debt_usd,
                    smaller.lltv,
                    smaller.lif,
                    "market-tracking",
                    shocks,
                    recovery,
                    extra,
                    **kw,
                )
                if after_switch
                else run(smaller)
            )
            red_loss = sm.loss_usd
            reduction = {
                "sell_usd": sell,
                "share": frac,
                "cost_usd": red_cost,
                "loss_after_usd": red_loss,
                "liquidated_after": sm.liquidated,
                "source": q["source"],
            }
    verdict, reason = decide.verdict_given(staying.loss_usd, exit_cost, red_cost, red_loss)
    if after_switch:
        reason += f", counted after the oracle switch, which leaves {after_switch['after']} to act"
    notes = []
    if verdict != "STAY" and timing.seconds == 0:
        notes.append("the impact is immediate: leaving only helps if it is done before the liquidation lands")
    if quote.get("source") and not (stress and stress.get("counted")):
        notes.append(
            "the exit cost is today's quote"
            + ("" if stress else "; in the incident the pool may be thinner (docs/analysis/GAP.md K12)")
        )
    if profile and mode != pos.oracle_mode:
        notes.append(f"oracle mode from its class ({profile.kind}), not from the price inference ({pos.oracle_mode})")
    return IncidentResult(
        shocks,
        b.loss_usd,
        b.loss_usd / equity,
        b.liquidated,
        oracle_drop,
        b.path,
        timing,
        exit_cost,
        "Pendle swap quotes after the incident's liquidations"
        if stress and stress["counted"]
        else quote.get("source", "?"),
        verdict,
        reason,
        reduction,
        notes,
        after_switch,
        stressed_exit=stress,
    )


def alert_impact(
    gap: float,
    collateral_value: float,
    debt: float,
    lltv: float,
    profile: OracleProfile | None = None,
) -> dict:
    """D93, pure: the impact on a borrow of an oracle-versus-market gap measured by the watches.

    `gap` is oracle ÷ market − 1, `collateral_value` the collateral at the oracle price, `debt` the debt, both in the
    loan token. Oracle above the market (gap > 0): the collateral is worth less than the oracle says; if the gap is
    real, the position's equity at the market price is lower, with no liquidation until the oracle follows.
    Oracle below the market (gap < 0): the oracle under-reports, and a liquidation at that price loses value."""
    lif = morpho_lif(lltv)
    if gap >= 0:
        base, shocks, mode = collateral_value, {"issuer_depeg": gap / (1 + gap)}, "fundamental"
    else:
        base, shocks, mode = collateral_value / (1 + gap), {"oracle": -gap}, "fundamental"
    b = loss(base, debt, lltv, lif, mode, shocks, recovery=0.0)
    equity = max(base - debt, 1e-9)
    timing = time_to_impact(profile, {"issuer_depeg": shocks["issuer_depeg"]} if gap >= 0 else shocks)
    return {
        "gap": gap,
        "loss": b.loss_usd,
        "loss_share_of_equity": b.loss_usd / equity,
        "liquidated": b.liquidated,
        "time_to_impact": timing.text,
        "never_liquidates": timing.never,
    }


def alert_sentence(imp: dict, symbol: str) -> str:
    """One sentence for the alert's detail."""
    if imp["gap"] >= 0:
        head = f"If the market price is right, your collateral is worth {imp['gap'] / (1 + imp['gap']):.1%} less than the oracle says"
    else:
        head = f"The oracle is {-imp['gap']:.1%} below the market"
    what = "liquidated" if imp["liquidated"] else "not liquidated"
    return (
        f"{head}: {what}, a loss of {imp['loss']:,.0f} {symbol} ({imp['loss_share_of_equity']:.1%} of your equity). "
        f"How fast: {imp['time_to_impact']}"
    )


def enrich_divergence(alerts: list, markets: dict, states: dict, profiles: dict) -> None:
    """D93: give every `OracleDivergence` alert on a market the user borrows from the impact on that borrow, in place.
    `markets` and `states` are `borrower.BorrowMarket` / `BorrowState` by market id; `profiles` maps them to an
    `OracleProfile` (missing: timing unknown)."""
    for al in alerts:
        if al.event != "OracleDivergence":
            continue
        mid, gap = al.data.get("market"), al.data.get("gap")
        m, st = markets.get(mid), states.get(mid)
        if m is None or st is None or not st.debt or st.collateral_value is None or gap is None:
            continue
        unit = 10**m.loan_decimals
        imp = alert_impact(gap, st.collateral_value / unit, st.debt / unit, m.lltv, profiles.get(mid))
        al.detail += ". " + alert_sentence(imp, m.loan_symbol)
        al.data["incident"] = imp
        al.depositor_impact = -imp["loss"]
