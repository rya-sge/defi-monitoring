"""Sky's backing: where the debt behind USDS and DAI sits, and what a loss on one source does to them (plan
2026-10-11-sky, D223–D226; GAP K19).

Read on-chain at one block, keyless, from Sky's ChainLog (the registry of its core addresses):

  every collateral type (ilk) of the IlkRegistry   its debt in the Vat: Art × rate
  the LitePSM                                      the USDC it holds (its `pocket`)
  the Vow                                          the surplus, Vat.dai(vow), and the system's bad debt, Vat.sin(vow)
  sUSDS, USDS, DAI, SKY                            the savings rate, the supplies, SKY's supply (its price: DefiLlama)

The debt is grouped into sources: the peg module, each allocator (Spark, Bloom, Obex, Grove…), crypto vaults, RWA
vaults. A loss on a source is absorbed, in Sky's own order (developers.skyeco.com, the Vow): the net surplus first,
then debt auctions that mint and sell SKY, up to `sky.debt_auction_share` of SKY's market value; what remains marks
USDS, DAI and sUSDS down, over the USDS and DAI in circulation. Recorded under fixtures/replay/sky/.
"""

from __future__ import annotations

from dataclasses import dataclass

from eth_abi import decode

from . import sources as S
from .discover import REGISTRY
from .vault import _call, _uint

K = REGISTRY["sky"]
CHAINLOG = "0xda0ab1e0017debcd72be8599041a2aa3ba7e740f"
KEYS = ("MCD_VAT", "MCD_VOW", "ILK_REGISTRY", "USDS", "SUSDS", "MCD_DAI", "MCD_LITE_PSM_USDC_A", "SKY")


@dataclass
class Snapshot:
    block: int
    debt: dict[str, float]  # source → debt in USD (DAI and USDS are 1:1)
    ilks: dict[str, float]  # collateral type → debt
    psm_usdc: float  # the USDC the LitePSM holds
    surplus: float  # Vat.dai(vow)
    bad_debt: float  # Vat.sin(vow)
    ssr: float  # the sUSDS savings rate, a year
    usds: float
    dai: float
    susds: float  # USDS held in sUSDS
    sky_value: float | None  # SKY's market value, USD

    @property
    def total(self) -> float:
        return sum(self.debt.values())

    @property
    def net_surplus(self) -> float:
        return self.surplus - self.bad_debt

    @property
    def auction_capacity(self) -> float:
        return (self.sky_value or 0.0) * K["debt_auction_share"]

    def lines(self) -> list[str]:
        on = sorted(self.debt.items(), key=lambda x: -x[1])
        out = [
            f"USDS and DAI's backing (Sky, block {self.block:,}, {self.total / 1e9:,.2f}B of debt): "
            + ", ".join(f"{k} {v / self.total:.1%}" for k, v in on if v / self.total >= 0.001)
            + f"; the peg module holds {self.psm_usdc / 1e9:,.2f}B USDC"
        ]
        out.append(
            f"Sky's surplus: {self.surplus / 1e6:,.1f}M against {self.bad_debt / 1e6:,.1f}M of system bad debt, net "
            f"{self.net_surplus / 1e6:+,.1f}M"
            + (": no buffer, a loss goes straight to debt auctions" if self.net_surplus <= 0 else "")
            + (
                f"; debt auctions can raise about {self.auction_capacity / 1e6:,.0f}M by minting SKY "
                f"({K['debt_auction_share']:.0%} of its {self.sky_value / 1e9:,.2f}B market value)"
                if self.sky_value
                else ""
            )
        )
        out.append(f"sUSDS: {self.susds / 1e9:,.2f}B at a savings rate of {self.ssr:.2%}")
        return out


def source_of(ilk: str) -> str:
    """D224, pure: the source a collateral type belongs to, by its name (`sky.sources`)."""
    for prefix, name in K["sources"].items():
        if ilk.startswith(prefix):
            return name if name != "*" else ilk.split("-")[1].capitalize()
    return "crypto vaults"


def sky_loss(snap: Snapshot, source: str, loss: float) -> dict:
    """D225, pure: a source losing `loss` of what backs it (the peg module: of its USDC); the net surplus absorbs first,
    then debt auctions up to their capacity; the rest marks USDS, DAI and sUSDS down. ValueError for an unknown
    source."""
    name = next((s for s in snap.debt if s.lower() == source.lower()), None)
    if name is None:
        raise ValueError(f"unknown Sky source {source!r}: one of {', '.join(sorted(snap.debt))}")
    exposed = snap.psm_usdc if name == "peg module" else snap.debt[name]
    lost = exposed * loss
    surplus = min(lost, max(0.0, snap.net_surplus))
    auctions = min(lost - surplus, snap.auction_capacity)
    rest = lost - surplus - auctions
    markdown = rest / (snap.usds + snap.dai) if snap.usds + snap.dai else 0.0
    return {
        "source": name,
        "exposed_usd": exposed,
        "lost_usd": lost,
        "surplus_usd": surplus,
        "auctions_usd": auctions,
        "markdown": markdown,
        "text": (
            f"Sky's {name}: {exposed / 1e6:,.0f}M of USDS's backing; losing {loss:.0%} of it is {lost / 1e6:,.1f}M: "
            f"{surplus / 1e6:,.1f}M from the surplus, {auctions / 1e6:,.1f}M from debt auctions (SKY minted)"
            + (
                f", the remaining {rest / 1e6:,.1f}M marks USDS, DAI and sUSDS down {markdown:.2%}"
                if markdown > 0
                else ": no markdown of USDS"
            )
        ),
    }


def parse_sky(items: list[str] | None) -> tuple[list[str], list[tuple[str, float]]]:
    """D226, pure: split `sky=<source>:<loss>` from the other shocks."""
    rest, out = [], []
    for it in items or []:
        name, _, value = it.partition("=")
        if name.strip() != "sky":
            rest.append(it)
            continue
        source, _, loss = value.rpartition(":")
        try:
            v = float(loss)
        except ValueError:
            raise ValueError(f"'{it}': write sky=<source>:<loss>, e.g. sky=spark:0.2") from None
        if not source or not 0 < v <= 1:
            raise ValueError(f"'{it}': write sky=<source>:<loss>, the loss between 0 and 1")
        out.append((source, v))
    return rest, out


# --- I/O


def _b32(s: str) -> bytes:
    return s.encode().ljust(32, b"\0")


def load(f: S.Fetcher, block: int) -> Snapshot | None:
    """D223: the reads at `block`; None when the ChainLog cannot be read."""
    try:
        res = S.rpc_batch(f, [_call(CHAINLOG, "getAddress(bytes32)", ["bytes32"], [_b32(k)]) for k in KEYS], block)
        a = {k: "0x" + r[-40:] for k, r in zip(KEYS, res)}
        raw = S.rpc_batch(f, [_call(a["ILK_REGISTRY"], "list()")], block)[0]
        ilks = decode(["bytes32[]"], bytes.fromhex(raw[2:]))[0]
        rows = S.rpc_batch(f, [_call(a["MCD_VAT"], "ilks(bytes32)", ["bytes32"], [i]) for i in ilks], block)
        vow = a["MCD_VOW"]
        g = S.rpc_batch(
            f,
            [
                _call(a["MCD_VAT"], "dai(address)", ["address"], [vow]),
                _call(a["MCD_VAT"], "sin(address)", ["address"], [vow]),
                _call(a["SUSDS"], "ssr()"),
                _call(a["SUSDS"], "totalAssets()"),
                _call(a["USDS"], "totalSupply()"),
                _call(a["MCD_DAI"], "totalSupply()"),
                _call(a["MCD_LITE_PSM_USDC_A"], "pocket()"),
                _call(a["MCD_LITE_PSM_USDC_A"], "gem()"),
                _call(a["SKY"], "totalSupply()"),
            ],
            block,
        )
    except (S.SourceError, S.CacheMiss):
        return None
    dai_vow, sin_vow, ssr, susds, usds, dai, pocket, gem, sky_supply = (_uint(x) or 0 for x in g)
    per_ilk, debt = {}, {}
    for i, r in zip(ilks, rows):
        art, rate = decode(["uint256"] * 5, bytes.fromhex(r[2:]))[:2]
        name, d = i.rstrip(b"\0").decode(errors="replace"), art * rate / 1e45
        if d >= 1:
            per_ilk[name] = d
            debt[source_of(name)] = debt.get(source_of(name), 0.0) + d
    pocket_a, gem_a = "0x" + hex(pocket)[2:].rjust(40, "0"), "0x" + hex(gem)[2:].rjust(40, "0")
    try:
        held = _uint(S.rpc_batch(f, [_call(gem_a, "balanceOf(address)", ["address"], [pocket_a])], block)[0]) or 0
        price = S.coin_prices(f, [a["SKY"]]).get(f"ethereum:{a['SKY']}", {}).get("price")
    except (S.SourceError, S.CacheMiss):
        held, price = 0, None
    return Snapshot(
        block,
        debt,
        per_ilk,
        held / 1e6,
        dai_vow / 1e45,
        sin_vow / 1e45,
        (ssr / 1e27) ** (365 * 86_400) - 1 if ssr else 0.0,
        usds / 1e18,
        dai / 1e18,
        susds / 1e18,
        sky_supply / 1e18 * price if price else None,
    )
