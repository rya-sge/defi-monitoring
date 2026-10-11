"""A book of vaults under one incident (plan 2026-10-11-vault-book, D120–D125).

A book is any list of Morpho Vault V2 vaults, in a JSON file or given on the command line, so a curator, a
depositor or an analyst can define their own:

    {
      "name": "RockawayX, Morpho Vault V2 on Ethereum",
      "weighting": "vault",                       # "vault": each vault at its total assets (a curator's book)
                                                  # "depositor": each vault at the depositor's position in it
      "vaults": [
        {"address": "0xd6d4…", "label": "Belem RWA EURCV", "depositor": "0x…"},   # label and depositor optional
        {"address": "0xc207…"}
      ]
    }

The incident (`token=<collateral>:<fall>` or `borrower=<target>:<recovery>[:<n>]`, as for one vault) is applied in
every vault it reaches; the book adds the losses in USD, so vaults lending different assets can share a book, and says
where the issuer or the borrower sits.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import exit_queue as EQ
from .vault_incident import VaultIncident, breakeven, describe

WEIGHTINGS = ("vault", "depositor", "pocket")
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@dataclass
class BookVault:
    address: str
    label: str | None = None
    depositor: str | None = None
    amount: float | None = None  # D152: `pocket` weighting: the book's position in this vault, in USD
    kind: str = "vault"  # D177, D222: "vault" (a Vault V2 deposit), "pt" (a PT held) or "borrow" (a Morpho Blue borrow: `address` is the market)


@dataclass
class Book:
    name: str
    weighting: str
    vaults: list[BookVault]


@dataclass
class VaultLine:
    vault: str
    name: str
    value_usd: float  # the vault in the book: its total, or the depositor's position (weighting)
    loss_usd: float
    exposure_usd: float  # what sits in the hit markets
    verdict: str
    hit_markets: list[str]
    priced: bool  # False: the asset's USD price was not available, 1 was assumed
    p_star: float | None = None  # D144: the depositor's breakeven probability over the horizon (vault_incident D143)
    p_star_year: float | None = None
    exit_cost_usd: float = 0.0  # the cost of leaving now: the yield forgone, or a flat share of what leaves
    saved_usd: float = 0.0  # what leaving first saves if the incident comes
    reason: str = ""  # D153: why the verdict, in one clause


@dataclass
class BookIncident:
    name: str
    weighting: str
    shocks: list[str]  # each shock in words
    lines: list[VaultLine]
    value_usd: float
    loss_usd: float
    exposure_usd: float
    headline: str
    notes: list[str] = field(default_factory=list)
    p_star: float | None = None  # D144: the book's breakeven: Σ yield forgone ÷ Σ loss saved, over the horizon
    p_star_year: float | None = None
    horizon_days: float = 30.0
    conditional: dict | None = None  # D165: the book's loss of staying given the incident, drawn, against leaving
    value_at_risk: dict | None = None  # D227: what the incident puts at risk, in one block

    def text(self) -> list[str]:
        shock = "; ".join(self.shocks)
        out = [f"BOOK  {self.name}  ·  incident: {shock}  ·  weighting: {self.weighting}", f"  {self.headline}"]
        if self.conditional:
            out.append(f"  given the incident, drawn: {self.conditional['text']}")
        if self.value_at_risk:
            out += self.value_at_risk["lines"]
        out.append(
            f"    {'vault':<44} {'in the book':>14} {'in hit mkts':>14} {'loss':>12} {'loss %':>7} {'p*/yr':>7}  verdict"
        )
        for ln in sorted(self.lines, key=lambda x: (-x.loss_usd, -x.exposure_usd)):
            pct = ln.loss_usd / ln.value_usd if ln.value_usd else 0.0
            out.append(
                f"    {ln.name[:44]:<44} {ln.value_usd:>14,.0f} {ln.exposure_usd:>14,.0f} {ln.loss_usd:>12,.0f} "
                f"{pct:>7.2%} {(f'{ln.p_star_year:.1%}' if ln.p_star_year is not None else 'n/a' if ln.hit_markets else '—'):>7}  "
                f"{ln.verdict if ln.hit_markets else '—'}" + (f"  {ln.reason}" if ln.reason else "")
            )
        out.append(
            f"    {'book (USD)':<44} {self.value_usd:>14,.0f} {self.exposure_usd:>14,.0f} {self.loss_usd:>12,.0f} "
            f"{(self.loss_usd / self.value_usd if self.value_usd else 0):>7.2%}"
        )
        out += [f"  note: {n}" for n in self.notes]
        return out

    def to_json(self) -> dict:
        return asdict(self)


# --- pure


def load(path: Path) -> Book:
    """D120: read and check a book file."""
    try:
        d = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"cannot read the book {path}: {e}") from None
    return parse(d, str(path))


def parse(d: dict, where: str = "book") -> Book:
    if not isinstance(d, dict) or not isinstance(d.get("vaults"), list) or not d["vaults"]:
        raise ValueError(f'{where}: a book needs a non-empty "vaults" list')
    weighting = d.get("weighting", "vault")
    if weighting not in WEIGHTINGS:
        raise ValueError(f'{where}: "weighting" must be one of {", ".join(WEIGHTINGS)}')
    vaults, seen = [], set()
    for i, v in enumerate(d["vaults"]):
        v = {"address": v} if isinstance(v, str) else v
        kind = v.get("kind", "vault")
        if kind not in ("vault", "borrow", "pt"):
            raise ValueError(f'{where}: pocket #{i + 1}: "kind" is "vault", "borrow" or "pt"')
        if kind == "borrow":
            # D177: a Morpho Blue borrow, e.g. the brief's PT loop: the market id, and the borrower as "depositor"
            a = str(v.get("market") or v.get("address") or "").lower()
            if not (a.startswith("0x") and len(a) == 66):
                raise ValueError(f'{where}: pocket #{i + 1} (borrow) needs the Blue "market" id')
            v = {**v, "depositor": v.get("user") or v.get("depositor")}
        elif kind == "pt":
            # D222: a PT held without a borrow: its Pendle market, and the pocket's amount in USD
            a = str(v.get("market") or v.get("address") or "").lower()
            if not (a.startswith("0x") and len(a) == 42):
                raise ValueError(f'{where}: pocket #{i + 1} (pt) needs the Pendle "market" address')
            if not (isinstance(v.get("amount"), (int, float)) and v["amount"] > 0):
                raise ValueError(f'{where}: pocket #{i + 1} (pt) needs a positive "amount" (USD)')
        else:
            a = str(v.get("address", "")).lower()
            if not (a.startswith("0x") and len(a) == 42):
                raise ValueError(f'{where}: vault #{i + 1} has no valid "address"')
        if a in seen:
            raise ValueError(f"{where}: vault {a} is listed twice")
        seen.add(a)
        dep, amount = v.get("depositor"), v.get("amount")
        if weighting == "pocket" and not (isinstance(amount, (int, float)) and amount > 0):
            raise ValueError(f'{where}: vault #{i + 1} needs a positive "amount" (USD) in the "pocket" weighting')
        # a borrower keeps its spelling: the Morpho API request, and so its recording, is keyed by it
        dep = (dep if kind == "borrow" else dep.lower()) if dep else None
        vaults.append(BookVault(a, v.get("label"), dep, amount, kind))
    return Book(d.get("name") or f"{len(vaults)} vault(s)", weighting, vaults)


def examples() -> dict[str, Book]:
    """The books shipped in `examples/`, by file name without `.json`."""
    return {p.stem: load(p) for p in sorted(EXAMPLES.glob("*.json"))}


def from_addresses(addresses: list[str], depositor: str | None = None) -> Book:
    """An ad hoc book from `--vault A --vault B`; with one `--user`, the depositor's view in every vault."""
    return parse(
        {
            "name": f"{len(addresses)} vault(s) given on the command line",
            "weighting": "depositor" if depositor else "vault",
            "vaults": [{"address": a, "depositor": depositor} for a in addresses],
        },
        "command line",
    )


def pocket(inc: VaultIncident, amount_usd: float):
    """D152, pure: a position of `amount_usd` in the vault, first in the exit queue: (value, loss if it stays, loss if
    it leaves first, what leaves at par, cost of leaving, p*, p* per year, verdict given the incident), asset units."""
    usd = inc.asset_usd if inc.asset_usd else 1.0
    a = amount_usd / usd
    plain, forced, penalty = inc.liquidity
    liq = EQ.Liquidity(inc.vault_total, a, plain, forced, penalty)
    stay = a * inc.vault_loss / inc.vault_total if inc.vault_total else 0.0
    first = EQ.exit_at(liq, 0)
    leave = EQ.depositor_loss(liq, first, EQ.LossCase("incident", inc.vault_loss, 0))
    cost, p, py = breakeven(stay, leave, first.par, inc.apy, inc.horizon_days, inc.exit_cost_rate)
    verdict = "EXIT" if stay - leave > cost and stay > 0 else "STAY"
    return a, stay, leave, first.par, cost, p, py, verdict


def reason(hit: bool, loss: float, saved: float, cost: float, p: float | None, days: float, share: float | None) -> str:
    """D153, pure: why a vault line reads STAY or EXIT, in one clause."""
    if not hit:
        return ""
    if loss <= 0:
        return "no bad debt reaches the vault"
    if saved <= 0:
        return "nothing to save by leaving first" + (
            f": the depositor is {share:.0%} of the vault" if share is not None and share >= 0.5 else ""
        )
    if p is None or p >= 1:
        return f"leaving costs {cost:,.0f} USD, more than the {saved:,.0f} it saves"
    return f"leaving pays above a {p:.1%} chance over {days:g} days"


def line(inc: VaultIncident, label: str | None, weighting: str, amount: float | None = None) -> VaultLine:
    """D122, pure: one vault's line in USD, in the book's weighting."""
    usd = inc.asset_usd if inc.asset_usd else 1.0
    exposure = sum(h.vault_exposure for h in inc.hits)
    hit = bool(inc.hits)
    if weighting == "pocket":
        a, stay, leave, _, cost, p, py, verdict = pocket(inc, amount or 0.0)
        frac = a / inc.vault_total if inc.vault_total else 0.0
        saved = max(0.0, stay - leave)
        p_ok = p is not None and p < 1
        return VaultLine(
            inc.vault,
            label or inc.name,
            a * usd,
            stay * usd,
            exposure * frac * usd,
            verdict,
            [h.label for h in inc.hits],
            inc.asset_usd is not None,
            p if p_ok else None,
            py if p_ok else None,
            cost * usd,
            saved * usd,
            reason(hit, stay, saved * usd, cost * usd, p, inc.horizon_days, None),
        )
    p_ok = inc.p_star is not None and inc.p_star < 1
    saved = max(0.0, inc.loss_if_stay - inc.loss_if_exit_first)
    why = reason(
        hit,
        inc.vault_loss,
        saved * usd,
        inc.exit_cost * usd,
        inc.p_star,
        inc.horizon_days,
        inc.depositor_assets / inc.vault_total if inc.vault_total else None,
    )
    if weighting == "depositor":
        frac = inc.depositor_assets / inc.vault_total if inc.vault_total else 0.0
        value, loss, exposure = inc.depositor_assets, inc.loss_if_stay, exposure * frac
    else:
        value, loss = inc.vault_total, inc.vault_loss
    return VaultLine(
        inc.vault,
        label or inc.name,
        value * usd,
        loss * usd,
        exposure * usd,
        inc.verdict,
        [h.label for h in inc.hits],
        inc.asset_usd is not None,
        inc.p_star if p_ok else None,
        inc.p_star_year if p_ok else None,
        inc.exit_cost * usd,
        saved * usd,
        why,
    )


def borrow_line(
    label: str,
    weighting: str,
    amount: float | None,
    equity_usd: float,
    loss_usd: float,
    exit_cost_usd: float,
    rate: float | None,
    days: float,
    hit: bool,
) -> VaultLine:
    """D178, pure: a borrow pocket (the brief's PT loop) under the book's incident, by the same rule as a vault pocket:
    staying loses the incident's loss; leaving now avoids it and costs the exit (its swap quote, or `rate` × what
    leaves); EXIT when the loss avoided exceeds that certain cost; p* = cost / loss avoided. In the `pocket` weighting
    the position is scaled to the pocket's amount."""
    k = (amount / equity_usd) if weighting == "pocket" and amount and equity_usd else 1.0
    value, stay = equity_usd * k, loss_usd * k
    cost = rate * value if rate is not None else exit_cost_usd * k
    p = cost / stay if stay > 0 else None
    verdict = "EXIT" if hit and stay > cost else "STAY"
    return VaultLine(
        label,
        label,
        value,
        stay,
        value if hit else 0.0,
        verdict,
        [label] if hit else [],
        True,
        p if p is not None and p < 1 else None,
        (1 - (1 - p) ** (365 / days)) if p is not None and p < 1 else None,
        cost,
        stay,
        reason(hit, stay, stay, cost, p, days, None),
    )


def value_at_risk(book: BookIncident, incidents: list[VaultIncident], incident: str | None = None) -> dict:
    """D227, pure: what the incident puts at risk, gathered from figures already computed: the money in the hit
    markets, the expected loss if it happens and its worst pocket, the worst cases given the incident (when the
    conditional draw ran), the cost of leaving the hit pockets against what it saves, and the losses beyond the book:
    the lenders of the other markets the incident reaches (sibling markets, each counted once, in its loan unit)."""
    hit = [ln for ln in book.lines if ln.hit_markets]
    worst = max(hit, key=lambda ln: ln.loss_usd, default=None)
    own = {h.market_id for inc in incidents for h in inc.hits}
    beyond: dict[str, tuple[str, float, str]] = {}
    for inc in incidents:
        for mid, label, loss, unit in inc.sibling_losses:
            if mid not in own and loss > beyond.get(mid, ("", 0.0, ""))[1]:
                beyond[mid] = (label, loss, unit)
    per_unit: dict[str, float] = {}
    for _, loss, unit in beyond.values():
        per_unit[unit or "?"] = per_unit.get(unit or "?", 0.0) + loss
    c = book.conditional
    leave = sum(ln.exit_cost_usd for ln in hit)
    saved = sum(ln.saved_usd for ln in hit)
    share = book.loss_usd / book.value_usd if book.value_usd else 0.0
    # the "vault" weighting counts each vault whole (all its depositors); the draw, the cost of leaving and what it
    # saves are the followed depositor's: say whose figures each line gives
    whole = book.weighting == "vault"
    them = " for the depositors followed" if whole else ""
    event = incident or "; ".join(book.shocks)
    lines = [
        f"  VALUE AT RISK, given: {event}",
        f"    at risk: {book.exposure_usd:,.0f} USD in the hit markets, {len(hit)} of {len(book.lines)} pocket(s) hit",
        f"    loss if it happens, at that size: {book.loss_usd:,.0f} USD ({share:.2%} of the book"
        + ("; the vaults whole, all their depositors)" if whole else ")")
        + (f"; worst pocket: {worst.name} ({worst.loss_usd:,.0f})" if worst and worst.loss_usd > 0 else ""),
        (
            f"    worst cases if it happens{them}, its size and the liquidators drawn over {c['paths']:,} paths: "
            f"95 % {c['stay_p95']:,.0f}, 99 % {c['stay_p99']:,.0f} USD"
            if c
            else "    worst cases if it happens: run with --conditional to draw its size and the liquidators"
        ),
        f"    leaving the hit pockets now{them}: costs {leave:,.0f} USD for sure, saves {saved:,.0f} if it happens",
    ]
    if per_unit:
        lines.append(
            f"    beyond the book: the lenders of {len(beyond)} other market(s) the incident reaches lose "
            + ", ".join(f"{v:,.0f} {u}" for u, v in sorted(per_unit.items(), key=lambda x: -x[1]))
        )
    return {
        "incident": event,
        "exposure_usd": book.exposure_usd,
        "loss_usd": book.loss_usd,
        "loss_share": share,
        "pockets_hit": len(hit),
        "pockets": len(book.lines),
        "worst_pocket": worst.name if worst and worst.loss_usd > 0 else None,
        "worst_pocket_loss_usd": worst.loss_usd if worst else 0.0,
        "p95_usd": c["stay_p95"] if c else None,
        "p99_usd": c["stay_p99"] if c else None,
        "leave_cost_usd": leave,
        "saved_usd": saved,
        "beyond_markets": len(beyond),
        "beyond_by_unit": per_unit,
        "loss_is_whole_vaults": whole,
        "lines": lines,
    }


def aggregate(
    book: Book,
    shocks: list[tuple],
    incidents: list[VaultIncident],
    extra: list[VaultLine] | None = None,
    extra_names: dict[str, str] | None = None,
) -> BookIncident:
    """D123, pure: add the vaults up, and write the headline. `shocks` as `vault_incident.parse_shocks` gives them;
    `extra` are the borrow pockets' lines (D178)."""
    labels = {v.address: v.label for v in book.vaults}
    amounts = {v.address: v.amount for v in book.vaults}
    names = {k.lower(): k for i in incidents for k in i.shocks}  # the symbol as the vaults' markets name it
    for i in incidents:
        names.update(i.labels)
    names.update(extra_names or {})
    shocks = [describe(s, names) for s in shocks]
    lines = [line(i, labels.get(i.vault), book.weighting, amounts.get(i.vault)) for i in incidents] + list(extra or [])
    days = incidents[0].horizon_days if incidents else 30.0
    value = sum(ln.value_usd for ln in lines)
    loss = sum(ln.loss_usd for ln in lines)
    exposure = sum(ln.exposure_usd for ln in lines)
    hit = [ln for ln in lines if ln.hit_markets]
    shock = "; ".join(shocks)
    if not hit:
        headline = f"{shock}: no vault of the book is reached (above one token allocated): no impact."
    elif loss <= 0:
        headline = (
            f"{shock}: no bad debt; {exposure:,.0f} USD ({exposure / value:.1%} of the book) sits in {len(hit)} "
            f"vault(s) reached, and the collateral still covers the debt."
        )
    else:
        worst = max(hit, key=lambda x: x.loss_usd)
        act = [ln for ln in hit if ln.p_star is not None]
        first = min(act, key=lambda x: x.p_star) if act else None
        headline = (
            f"{shock}: the book loses {loss:,.0f} USD ({loss / value:.2%} of {value:,.0f}) in {len(hit)} {'pocket(s)' if book.weighting == 'pocket' else 'vault(s)'}; "
            f"largest in {worst.name} ({worst.loss_usd:,.0f}). "
            + (
                f"Act first on {first.name}: leaving it costs {first.exit_cost_usd:,.0f} USD "
                f"({first.exit_cost_usd / value:.2%} of the book) for sure and saves {first.saved_usd:,.0f} if the "
                f"incident comes, so it pays if the incident's probability over {days:g} days is above "
                f"{first.p_star:.2%} ({first.p_star_year:.1%}/yr)."
                if first
                else f"Leaving {worst.name} costs {worst.exit_cost_usd:,.0f} USD for sure, against "
                f"{worst.saved_usd:,.0f} saved if the incident comes: stay."
                if worst.saved_usd > 0
                else "Leaving first saves nothing in any vault reached: the depositors carry the loss either way."
            )
        )
    notes = []
    if any(not ln.priced for ln in lines):
        notes.append("an asset's USD price was not available: its vault is counted at 1 USD per unit")
    if len(hit) > 1:
        notes.append(
            f"the incident reaches {len(hit)} vaults of the book at once: their losses add up, they do not offset"
        )
    held = {h.market_id for i in incidents for h in i.hits}  # a sibling of one vault can be held by another
    sib = {(m, u): v for i in incidents for mid, m, v, u in i.sibling_losses if mid not in held}  # each counted once
    if sib:
        top = sorted(sib.items(), key=lambda kv: -kv[1])[:3]
        notes.append(
            f"contagion beyond the book: the lenders of {len(sib)} sibling market(s) lose "
            + ", ".join(f"{m} {v:,.0f} {u}" for (m, u), v in top)
        )
    mates = list(dict.fromkeys(m for i in incidents for m in i.common_mode))
    if mates:
        notes.append("Pharos common-mode groups across the book: " + "; ".join(mates))
    graded = list(dict.fromkeys(h.grade for i in incidents for h in i.hits if h.grade))
    if graded:
        notes.append(f"issuer grades of the hit collateral (Pharos {incidents[0].pharos}): " + ", ".join(graded))
    if incidents and all(i.pharos is None for i in incidents):
        notes.append("Pharos: not checked")
    notes.append("each vault is read at its own recorded or live block; the vaults' blocks can differ by minutes")
    cost, saved = sum(ln.exit_cost_usd for ln in hit), sum(ln.saved_usd for ln in hit)
    bp = cost / saved if saved > 0 and cost < saved else None
    if bp is not None:
        notes.insert(0, f"the book's breakeven, leaving every vault reached: {bp:.2%} over {days:g} days")
    return BookIncident(
        book.name,
        book.weighting,
        shocks,
        lines,
        value,
        loss,
        exposure,
        headline,
        notes,
        bp,
        (1 - (1 - bp) ** (365 / days)) if bp is not None else None,
        days,
    )


def write(b: BookIncident, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "book-incident.json"
    p.write_text(json.dumps(b.to_json(), indent=2))
    return p
