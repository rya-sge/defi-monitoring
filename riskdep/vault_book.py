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

from .vault_incident import VaultIncident, describe

WEIGHTINGS = ("vault", "depositor")
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@dataclass
class BookVault:
    address: str
    label: str | None = None
    depositor: str | None = None


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
    exit_cost_usd: float = 0.0  # the yield forgone by leaving now
    saved_usd: float = 0.0  # what leaving first saves if the incident comes


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

    def text(self) -> list[str]:
        shock = "; ".join(self.shocks)
        out = [f"BOOK  {self.name}  ·  incident: {shock}  ·  weighting: {self.weighting}", f"  {self.headline}"]
        out.append(
            f"    {'vault':<44} {'in the book':>14} {'in hit mkts':>14} {'loss':>12} {'loss %':>7} {'p*/yr':>7}  verdict"
        )
        for ln in sorted(self.lines, key=lambda x: (-x.loss_usd, -x.exposure_usd)):
            pct = ln.loss_usd / ln.value_usd if ln.value_usd else 0.0
            out.append(
                f"    {ln.name[:44]:<44} {ln.value_usd:>14,.0f} {ln.exposure_usd:>14,.0f} {ln.loss_usd:>12,.0f} "
                f"{pct:>7.2%} {(f'{ln.p_star_year:.1%}' if ln.p_star_year is not None else '—'):>7}  "
                f"{ln.verdict if ln.hit_markets else '—'}"
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
        a = str(v.get("address", "")).lower()
        if not (a.startswith("0x") and len(a) == 42):
            raise ValueError(f'{where}: vault #{i + 1} has no valid "address"')
        if a in seen:
            raise ValueError(f"{where}: vault {a} is listed twice")
        seen.add(a)
        dep = v.get("depositor")
        vaults.append(BookVault(a, v.get("label"), dep.lower() if dep else None))
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


def line(inc: VaultIncident, label: str | None, weighting: str) -> VaultLine:
    """D122, pure: one vault's line in USD, in the book's weighting."""
    usd = inc.asset_usd if inc.asset_usd else 1.0
    p_ok = inc.p_star is not None and inc.p_star < 1
    exposure = sum(h.vault_exposure for h in inc.hits)
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
        max(0.0, inc.loss_if_stay - inc.loss_if_exit_first) * usd,
    )


def aggregate(book: Book, shocks: list[tuple], incidents: list[VaultIncident]) -> BookIncident:
    """D123, pure: add the vaults up, and write the headline. `shocks` as `vault_incident.parse_shocks` gives them."""
    labels = {v.address: v.label for v in book.vaults}
    names = {k.lower(): k for i in incidents for k in i.shocks}  # the symbol as the vaults' markets name it
    for i in incidents:
        names.update(i.labels)
    shocks = [describe(s, names) for s in shocks]
    lines = [line(i, labels.get(i.vault), book.weighting) for i in incidents]
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
            f"{shock}: the book loses {loss:,.0f} USD ({loss / value:.2%} of {value:,.0f}) in {len(hit)} vault(s); "
            f"largest in {worst.name} ({worst.loss_usd:,.0f}). "
            + (
                f"Act first on {first.name}: leaving it now pays if the incident's probability over {days:g} days "
                f"is above {first.p_star:.2%} ({first.p_star_year:.1%}/yr)."
                if first
                else "No vault's loss falls enough by leaving first to pay for the yield given up: stay."
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
