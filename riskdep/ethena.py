"""Ethena's backing venues: where the collateral behind USDe sits, and what a venue failure does to it (plan
2026-10-11-venues, D218–D221; GAP K24, `NEXT_STEP.md` C4).

USDe is a delta-neutral position: collateral held by off-exchange settlement providers (Copper, Ceffu) and delegated
to exchanges as margin for short perpetuals, plus liquid stablecoins. Ethena's transparency dashboard serves, keyless:

  /api/positions/current/collateral         the backing by asset and by venue (an exchange, or "Unallocated")
  /api/solvency/reserve-fund                the reserve fund's value over time, which absorbs a loss first
  /api/yields/protocol-and-staking-yield    the protocol's and sUSDe's yields

A venue incident `venue=<venue>:<loss>` loses that share of what sits there; the reserve fund absorbs it first; the
rest is a markdown of USDe, and of sUSDe, its staked claim, by the same fraction. Recorded under
fixtures/replay/ethena/ like the other outside providers; offline by default.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import sources as S
from .discover import REGISTRY

E = REGISTRY["ethena"]
API = "https://app.ethena.fi/api"


@dataclass
class Snapshot:
    as_of: int  # the positions' timestamp
    total_usd: float
    venues: dict[str, float]  # venue → USD of backing there ("Unallocated": not delegated to an exchange)
    assets: dict[str, float]  # asset → USD
    reserve_usd: float | None
    protocol_yield: float | None  # % a year, 30-day average
    susde_yield: float | None

    def share(self, venue: str) -> float:
        return self.venues.get(venue, 0.0) / self.total_usd if self.total_usd else 0.0

    def lines(self) -> list[str]:
        """The backing in words, largest venue first."""
        on = sorted(((v, u) for v, u in self.venues.items() if v != "Unallocated" and u > 0), key=lambda x: -x[1])
        out = [
            f"USDe's backing (Ethena, {self.total_usd / 1e6:,.0f}M USD): {self.share('Unallocated'):.1%} not on an "
            "exchange (liquid stablecoins, held with off-exchange settlement providers such as Copper and Ceffu); "
            "margin on exchanges: " + ", ".join(f"{v} {u / self.total_usd:.1%}" for v, u in on)
        ]
        if self.reserve_usd is not None:
            out.append(
                f"Ethena's reserve fund: {self.reserve_usd / 1e6:,.1f}M USD, "
                f"{self.reserve_usd / self.total_usd:.2%} of the backing, absorbs a loss before USDe holders"
            )
        if self.protocol_yield is not None and self.susde_yield is not None:
            out.append(
                f"yields (30-day average): protocol {self.protocol_yield:.2f} %, sUSDe {self.susde_yield:.2f} %; "
                "negative funding on the hedges is paid from the reserve fund"
            )
        hedged = sum(u for v, u in self.venues.items() if v != "Unallocated")
        rate = E["funding_stress"]
        if self.reserve_usd and hedged and rate < 0:
            daily = hedged * -rate / 365
            out.append(
                f"funding at {rate:.0%}/yr on the {hedged / 1e6:,.0f}M hedged costs {daily / 1e3:,.0f}k USD a day: the "
                f"reserve fund covers {self.reserve_usd / daily:,.0f} days, then the loss reaches USDe holders"
            )
        return out


def venue_loss(snap: Snapshot, venue: str, loss: float) -> dict:
    """D219, pure: a venue losing `loss` of the backing that sits there: what is lost, what the reserve fund absorbs,
    and the markdown of USDe (and sUSDe) that remains. Raises ValueError for a venue the snapshot does not know."""
    name = next((v for v in snap.venues if v.lower() == venue.lower()), None)
    if name is None:
        raise ValueError(f"unknown Ethena venue {venue!r}: one of {', '.join(sorted(snap.venues))}")
    exposed = snap.venues[name]
    lost = exposed * loss
    absorbed = min(lost, snap.reserve_usd or 0.0)
    markdown = (lost - absorbed) / snap.total_usd if snap.total_usd else 0.0
    return {
        "venue": name,
        "exposed_usd": exposed,
        "share": exposed / snap.total_usd if snap.total_usd else 0.0,
        "lost_usd": lost,
        "absorbed_usd": absorbed,
        "markdown": markdown,
        "text": (
            f"{name} holds {exposed / 1e6:,.0f}M USD of USDe's backing ({exposed / snap.total_usd:.1%}); losing "
            f"{loss:.0%} of it is {lost / 1e6:,.1f}M"
            + (
                f", of which the reserve fund absorbs {absorbed / 1e6:,.1f}M: USDe and sUSDe are marked down "
                f"{markdown:.2%}"
                if markdown > 0
                else f", within the reserve fund ({(snap.reserve_usd or 0) / 1e6:,.1f}M): no markdown of USDe"
            )
            + "; the hedges held there are lost too, leaving that collateral unhedged until they are reopened "
            "elsewhere"
        ),
    }


def parse_venue(items: list[str] | None) -> tuple[list[str], list[tuple[str, float]]]:
    """D220, pure: split `venue=<venue>:<loss>` from the other shocks: (the others, [(venue, loss)])."""
    rest, venues = [], []
    for it in items or []:
        name, _, value = it.partition("=")
        if name.strip() != "venue":
            rest.append(it)
            continue
        venue, _, loss = value.rpartition(":")
        try:
            v = float(loss)
        except ValueError:
            raise ValueError(f"'{it}': write venue=<exchange>:<loss>, e.g. venue=Binance:0.5") from None
        if not venue or not 0 < v <= 1:
            raise ValueError(f"'{it}': write venue=<exchange>:<loss>, the loss between 0 and 1")
        venues.append((venue, v))
    return rest, venues


# --- I/O


def _last(r: dict) -> dict:
    """The reserve fund's series runs hourly since 2024: keep its last point."""
    y = (((r or {}).get("queryIndex") or [{}])[0].get("yields")) or []
    return {"last": y[-1] if y else None}


def _yields(r: dict) -> dict:
    return {k: (r or {}).get(k) for k in ("avg30dProtocolYield", "avg30dSusdeYield")}


def load(f: S.Fetcher) -> Snapshot | None:
    """D218: the three reads; None when the positions cannot be read (optional provider)."""
    try:
        rows = f.get_json(f"{API}/positions/current/collateral")["collateral"]
    except (S.SourceError, S.CacheMiss, KeyError, TypeError):
        return None
    venues, assets = {}, {}
    for r in rows:
        venues[r["exchange"]] = venues.get(r["exchange"], 0.0) + float(r["usdAmount"] or 0)
        assets[r["asset"]] = assets.get(r["asset"], 0.0) + float(r["usdAmount"] or 0)
    try:
        last = f.get_json(f"{API}/solvency/reserve-fund", transform=_last)["last"]
        reserve = float(last["value"]) if last else None
    except (S.SourceError, S.CacheMiss, KeyError, TypeError):
        reserve = None
    try:
        y = f.get_json(f"{API}/yields/protocol-and-staking-yield", transform=_yields)
        py, sy = (y.get(k, {}) or {} for k in ("avg30dProtocolYield", "avg30dSusdeYield"))
        protocol, staking = py.get("value"), sy.get("value")
    except (S.SourceError, S.CacheMiss, KeyError, TypeError, AttributeError):
        protocol = staking = None
    return Snapshot(
        max((int(r.get("timestamp") or 0) for r in rows), default=0),
        sum(venues.values()),
        venues,
        assets,
        reserve,
        protocol,
        staking,
    )
