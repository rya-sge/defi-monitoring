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
from dataclasses import asdict, dataclass, field

from . import decide
from . import oracle_class as OC
from . import sources as S
from .discover import REGISTRY, Position, morpho_lif
from .propagate import LossBreakdown, loss
from .vault import _call

EVENTS = ("chain", "issuer_hack", "issuer_depeg", "amm", "oracle", "lending")
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

    def lines(self) -> list[str]:
        shock = ", ".join(f"{k} {v:.1%}" for k, v in self.shocks.items())
        out = [
            f"INCIDENT  {shock}",
            f"  {'liquidated' if self.liquidated else 'not liquidated'}; loss ${self.loss_usd:,.0f} "
            f"({self.loss_share_of_equity:.1%} of equity)",
            f"  how fast: {self.timing.text}",
            f"  exit now: ${self.exit_cost_usd:,.0f} ({self.exit_source})",
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
        if not 0 <= v <= 1:
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
        return Timing(
            None,
            True,
            "never: the oracle does not follow the market, so nobody is liquidated; the loss stays with the lenders",
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
        cls, basis, base, _, _ = OC.classify_market_oracle(f, oracle, block)
        return OracleProfile(cls, basis, name, twap_s=_twap(base))
    except (S.SourceError, S.CacheMiss, ValueError) as e:
        return OracleProfile(OC.NOT_CLASSIFIED, f"not read: {str(e)[:80]}")


def assess(
    pos: Position,
    shocks: dict[str, float],
    recovery: float,
    quote: dict,
    profile: OracleProfile | None,
    quote_for=None,
) -> IncidentResult:
    """The impact of a given incident on an `analyze` position, its timing and the verdict (D89, D90)."""
    mode = oracle_mode_for(profile, pos.oracle_mode)
    extra = REGISTRY["pt_stress_extra_discount"]

    def run(p: Position) -> LossBreakdown:
        return loss(p.collateral_usd, p.debt_usd, p.lltv, p.lif, mode, shocks, recovery=recovery, pt_stress_extra=extra)

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
        and shocks.get("issuer_depeg", 0) > (profile.deviation_threshold or 0)
    ):
        # the depeg opens a challenge; once accepted, the oracle reads the source that follows the market
        sw = loss(pos.collateral_usd, pos.debt_usd, pos.lltv, pos.lif, "market-tracking", shocks, recovery, extra)
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
    timing = time_to_impact(profile, shocks)
    notes = []
    if verdict != "STAY" and timing.seconds == 0:
        notes.append("the impact is immediate: leaving only helps if it is done before the liquidation lands")
    if quote.get("source"):
        notes.append("the exit cost is today's quote; in the incident the pool may be thinner (docs/analysis/GAP.md K12)")
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
        quote.get("source", "?"),
        verdict,
        reason,
        reduction,
        notes,
        after_switch,
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
