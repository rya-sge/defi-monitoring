"""f(x): what fxSAVE's NAV is made of, and the markdown each component's loss causes (plan 2026-10-11-issuer-stacks,
D248–D249; GAPV2 G13).

fxSAVE wraps fxSP (FxUSDBasePool), whose NAV per share is (fxUSD held × fxUSD's price + USDC held × USDC's price) /
supply (`FxUSDBasePool.nav()`); the USDC is partly idle in fxSP and partly lent on Aave through its strategy. fxSAVE's
value follows fxSP's NAV, so a loss on one component marks fxSAVE down by that component's share of fxSP's value × the
loss:

  fx=fxusd:<depeg>   fxUSD's price falls
  fx=usdc:<depeg>    USDC's price falls (idle and lent)
  fx=aave:<loss>     the USDC lent on Aave is lost in part

Read on-chain at a block from the pinned addresses (`registry.json` `fx`), keyless; recorded under
fixtures/replay/fx/.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import sources as S
from .discover import REGISTRY
from .vault import _call, _uint

K = REGISTRY["fx"]
COMPONENTS = ("fxusd", "usdc", "aave")


@dataclass
class Snapshot:
    block: int
    fxusd: float  # fxUSD held by fxSP, in USD at its price
    usdc_idle: float  # USDC idle in fxSP, in USD
    usdc_lent: float  # USDC lent on Aave through the strategy, in USD
    fxusd_price: float
    usdc_price: float
    cooldown_s: int | None = None  # fxSP's redeem cool-down (an issuer exit, GAPV2 G14)
    instant_fee: float | None = None

    @property
    def total(self) -> float:
        return self.fxusd + self.usdc_idle + self.usdc_lent

    def share(self, component: str) -> float:
        part = {"fxusd": self.fxusd, "usdc": self.usdc_idle + self.usdc_lent, "aave": self.usdc_lent}[component]
        return part / self.total if self.total else 0.0

    def lines(self) -> list[str]:
        out = [
            f"fxSAVE's NAV (f(x), block {self.block:,}, {self.total / 1e6:,.2f}M USD in fxSP): fxUSD "
            f"{self.share('fxusd'):.1%} (at {self.fxusd_price:.4f}), USDC {self.share('usdc'):.1%}, of which "
            f"{self.share('aave'):.1%} lent on Aave"
        ]
        if self.cooldown_s is not None:
            out.append(
                f"redeeming fxSP: a cool-down of {self.cooldown_s / 3600:g} h, or at once for a fee of "
                f"{(self.instant_fee or 0):.2%}"
            )
        return out


def markdown(snap: Snapshot, component: str, loss: float) -> dict:
    """D249, pure: fxSAVE's markdown from a loss on one component of fxSP's value."""
    if component not in COMPONENTS:
        raise ValueError(f"unknown f(x) component {component!r}: one of {', '.join(COMPONENTS)}")
    share = snap.share(component)
    words = {"fxusd": "fxUSD depegs", "usdc": "USDC depegs", "aave": "the USDC lent on Aave loses"}[component]
    return {
        "component": component,
        "share": share,
        "markdown": share * loss,
        "text": f"{words} {loss:.0%}: it is {share:.1%} of fxSP's value, so fxSAVE falls {share * loss:.2%}",
    }


def parse(items: list[str] | None) -> tuple[list[str], list[tuple[str, str, float]]]:
    """D249, pure: split `fx=<component>:<loss>` and `infinifi=<share>` from the other shocks."""
    rest, out = [], []
    for it in items or []:
        name, _, value = it.partition("=")
        name = name.strip()
        if name not in ("fx", "infinifi"):
            rest.append(it)
            continue
        comp, _, loss = value.rpartition(":") if name == "fx" else ("", "", value)
        try:
            v = float(loss)
        except ValueError:
            raise ValueError(f"'{it}': write fx=<fxusd|usdc|aave>:<loss> or infinifi=<share of its backing>") from None
        if not 0 < v <= 1 or (name == "fx" and comp not in COMPONENTS):
            raise ValueError(f"'{it}': write fx=<fxusd|usdc|aave>:<loss> or infinifi=<share>, the loss between 0 and 1")
        out.append((name, comp, v))
    return rest, out


# --- I/O


def load(f: S.Fetcher, block: int) -> Snapshot | None:
    """D248: fxSP's holdings, its prices and its strategy's lent USDC; None when not readable."""
    fxsp, usdc = K["fxsp"], K["usdc"]
    try:
        # the strategy fxSP lends its USDC through, read live: the README's pinned one is no longer in use
        alloc = S.rpc_batch(f, [_call(fxsp, "allocations(address)", ["address"], [usdc])], block)[0]
        strategy = "0x" + alloc[26:66] if alloc and len(alloc) >= 66 else K["fxsp"]
        r = S.rpc_batch(
            f,
            [
                _call(fxsp, "totalYieldToken()"),
                _call(fxsp, "fxUSDPriceOracle()"),
                _call(usdc, "balanceOf(address)", ["address"], [fxsp]),
                _call(strategy, "totalSupply()"),
                _call(fxsp, "redeemCoolDownPeriod()"),
                _call(fxsp, "instantRedeemFeeRatio()"),
            ],
            block,
        )
        oracle = "0x" + r[1][-40:]
        p = S.rpc_batch(f, [_call(oracle, "getPrice()"), _call(oracle, "getUSDCPrice()")], block)
    except (S.SourceError, S.CacheMiss):
        return None
    fx_price = (int(p[0][66:130], 16) if p[0] and len(p[0]) >= 130 else 10**18) / 1e18
    usdc_price = (_uint(p[1]) or 10**18) / 1e18
    held, idle, lent = (_uint(r[0]) or 0) / 1e18, (_uint(r[2]) or 0) / 1e6, (_uint(r[3]) or 0) / 1e6
    return Snapshot(
        block,
        held * fx_price,
        idle * usdc_price,
        lent * usdc_price,
        fx_price,
        usdc_price,
        _uint(r[4]),
        (_uint(r[5]) or 0) / 1e18 if r[5] else None,  # FxUSDBasePool.PRECISION
    )
