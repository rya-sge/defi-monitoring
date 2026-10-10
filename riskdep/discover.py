"""Dependency discovery: a position becomes numbers plus a typed layer graph.

Layers (node attribute `kind`): chain, issuer, asset, amm, oracle, lending, stable.
Every node carries `source` (where the fact came from) and `evidence` (what was read).
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import networkx as nx

from . import clock
from . import sources as S

REGISTRY = json.loads((Path(__file__).parent / "registry.json").read_text())

POSITION_QUERY = """query($id:String!, $user:String!){
 marketById(marketId:$id, chainId:1){ marketId lltv oracleAddress irmAddress
  collateralAsset{address symbol decimals priceUsd} loanAsset{address symbol decimals priceUsd}
  state{ borrowApy supplyApy utilization liquidityAssetsUsd supplyAssetsUsd borrowAssetsUsd collateralAssetsUsd } }
 marketPosition(userAddress:$user, marketUniqueKey:$id, chainId:1){
  healthFactor state{ collateral collateralUsd borrowAssets borrowAssetsUsd } }
}"""

MARKET_QUERY = """query($id:String!){
 marketById(marketId:$id, chainId:1){ marketId lltv oracleAddress
  collateralAsset{address symbol decimals priceUsd} loanAsset{address symbol decimals priceUsd}
  state{ borrowApy utilization liquidityAssetsUsd supplyAssetsUsd borrowAssetsUsd collateralAssetsUsd } } }"""

TOP_BORROWER_QUERY = """query($id:String!){
 marketPositions(first:1, where:{marketUniqueKey_in:[$id], chainId_in:[1]}, orderBy: BorrowShares, orderDirection: Desc){
  items { user{address} } } }"""


@dataclass
class Position:
    label: str
    collateral_units: float
    collateral_symbol: str
    collateral_address: str
    pt_price_usd: float  # market price of one PT
    collateral_decimals: int = 18
    debt_usd: float = 0.0
    loan_symbol: str | None = None
    loan_address: str | None = None
    lltv: float | None = None
    lif: float | None = None  # Morpho liquidation incentive factor
    borrow_apy: float = 0.0
    implied_apy: float = 0.0  # PT fixed yield to maturity
    maturity: str | None = None
    days_to_maturity: float = 0.0
    oracle_mode: str = "none"  # market-tracking | fundamental | none
    oracle_ambiguous: bool = False  # the inference could not tell the modes apart
    pt_discount: float | None = None  # 1 − PT price in its accounting asset (Pendle API)
    morpho_market: str | None = None
    borrower: str | None = None
    debt_raw: int = 0  # in loan-token units, as the Morpho API reports it
    loan_decimals: int = 18
    oracle_price: float | None = None  # loan units per PT, as the lending market sees it
    health_factor: float | None = None
    pendle_market: str | None = None
    underlying_address: str | None = None
    underlying_symbol: str | None = None
    underlying_drawdown_1y: float | None = None
    amm_liquidity_usd: float | None = None
    lending_liquidity_usd: float | None = None
    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    notes: list[str] = field(default_factory=list)

    @property
    def collateral_usd(self) -> float:
        return self.collateral_units * self.pt_price_usd

    @property
    def equity_usd(self) -> float:
        return self.collateral_usd - self.debt_usd

    @property
    def liquidation_drop(self) -> float | None:
        """Fall in the oracle price that triggers liquidation."""
        if not self.debt_usd or not self.lltv:
            return None
        return max(0.0, 1 - self.debt_usd / (self.collateral_usd * self.lltv))


def _addr(pendle_id: str) -> str:
    return pendle_id.split("-", 1)[-1].lower()


def morpho_lif(lltv: float) -> float:
    return min(1.15, 1 / (0.3 * lltv + 0.7))


def find_pendle_market(f: S.Fetcher, pt_address: str) -> dict:
    pt = pt_address.lower()
    for status in ("active", "inactive"):
        for m in f.get_json(f"{S.PENDLE}/v1/1/markets/{status}")["markets"]:
            if _addr(m["pt"]) == pt:
                return m
    raise S.SourceError(f"no Pendle market on Ethereum has PT {pt_address}")


def pendle_market_by_address(f: S.Fetcher, market: str) -> dict:
    for status in ("active", "inactive"):
        for m in f.get_json(f"{S.PENDLE}/v1/1/markets/{status}")["markets"]:
            if m["address"].lower() == market.lower():
                return m
    raise S.SourceError(f"{market} is not a Pendle market on Ethereum")


def top_borrower(f: S.Fetcher, market_id: str) -> str:
    items = S.morpho(f, TOP_BORROWER_QUERY, {"id": market_id})["marketPositions"]["items"]
    if not items:
        raise S.SourceError(f"Morpho market {market_id} has no borrowers")
    return items[0]["user"]["address"]


ORACLE_GAP = 0.005  # oracle within 0.5 % of the PT market price → reads as market-tracking


def oracle_verified(f: S.Fetcher, oracle: str, clone_of: str | None) -> tuple[bool | None, str]:
    """Whether the code behind the oracle is verified on Etherscan (D68): the implementation of an EIP-1167 clone or
    of a proxy Etherscan recognises. (None, …) when it cannot be checked: no key and no cached answer."""
    target = clone_of or oracle
    src = S.contract_source(f, target)
    if src is None:
        return None, "source verification not checked (no Etherscan key or answer)"
    if src["verified"] and src["proxy"] and src["implementation"] and src["implementation"] != target:
        impl = S.contract_source(f, src["implementation"])
        if impl is None:
            return None, f"proxy verified on Etherscan, implementation {src['implementation']} not checked"
        src = impl
    if not src["verified"]:
        return False, "source not verified on Etherscan"
    return True, f"source verified on Etherscan ({src['name']})"


def infer_oracle(
    f: S.Fetcher, oracle: str, coll_dec: int, loan_dec: int, pt_market_in_loan: float, pt_discount: float | None = None
) -> tuple[str, float | None, str, bool, bool | None]:
    """Return (mode, oracle price in loan units per PT, evidence, ambiguous, source verified).

    The test compares the oracle with the PT market price. It cannot separate a market
    oracle from a linear-discount or a par oracle when the PT itself trades within
    2 × ORACLE_GAP of par (near maturity): every kind then reads close to the market.
    Such a result is flagged ambiguous and kept market-tracking, the conservative case.
    """
    raw = S.rpc_call(f, oracle, "price()")
    if not raw or raw == "0x":
        return "market-tracking", None, "price() unreadable; assumed market-tracking (conservative)", True, None
    price = int(raw, 16) / 10 ** (36 + loan_dec - coll_dec)
    shape = "Chainlink-v2 adapter" if S.rpc_call(f, oracle, "BASE_FEED_1()") else "custom oracle"
    code = S.rpc(f, "eth_getCode", [oracle, "latest"]) or ""
    clone_of = None
    if code.startswith("0x363d3d373d3d3d363d73"):
        clone_of = "0x" + code[22:62]
        shape += f", EIP-1167 clone of {clone_of}"
    verified, vtext = oracle_verified(f, oracle, clone_of)
    shape += f"; {vtext}"
    gap = price / pt_market_in_loan - 1
    if pt_discount is not None and abs(pt_discount) < 2 * ORACLE_GAP:
        return (
            "market-tracking",
            price,
            (
                f"{shape}; reads {price:.4f} vs PT market {pt_market_in_loan:.4f} ({gap:+.2%}), but the PT trades only "
                f"{pt_discount:.2%} below par: a market, linear-discount or par oracle would all read about the same. "
                "Ambiguous; treated as market-tracking, the conservative case"
            ),
            True,
            verified,
        )
    if abs(gap) <= ORACLE_GAP:
        mode = "market-tracking"
        why = (
            f"{shape}; reads {price:.4f} vs PT market {pt_market_in_loan:.4f} ({gap:+.2%}): "
            "follows the market or a linear discount close to it; treated as market-tracking, the conservative case"
        )
    else:
        mode = "fundamental"
        why = (
            f"{shape}; reads {price:.4f} vs PT market {pt_market_in_loan:.4f} ({gap:+.2%}): "
            "does not follow the market; a market depeg does not trigger liquidation, a loss of backing still does"
        )
    return mode, price, why, False, verified


def _add(g: nx.DiGraph, node: str, kind: str, label: str, source: str, evidence: str, **attrs):
    g.add_node(node, kind=kind, label=label, source=source, evidence=evidence, **attrs)


def _build_pt_layers(f: S.Fetcher, pos: Position, pm: dict) -> None:
    """Shared PT stack: chain, issuer, SY/underlying, Pendle AMM."""
    g = pos.graph
    data = f.get_json(f"{S.PENDLE}/v2/1/markets/{pm['address']}/data")
    pos.pendle_market = pm["address"]
    pos.implied_apy = data.get("impliedApy") or pm["details"].get("impliedApy", 0.0)
    pos.pt_discount = data.get("ptDiscount")
    pos.amm_liquidity_usd = data.get("liquidity", {}).get("usd")
    pos.maturity = pm["expiry"]
    exp = datetime.fromisoformat(pm["expiry"].replace("Z", "+00:00"))
    pos.days_to_maturity = max(0.0, (exp - clock.now_dt()).total_seconds() / 86400)

    und = _addr(pm["underlyingAsset"])
    pos.underlying_address = und
    prices = S.coin_prices(f, [und])
    meta = prices.get(f"ethereum:{und}", {})
    reg = REGISTRY["issuers"].get(und)
    pos.underlying_symbol = (reg or {}).get("symbol") or meta.get("symbol") or und[:10]
    dd = S.coin_drawdown(f, und)
    pos.underlying_drawdown_1y = dd["max_drawdown"] if dd["points"] else None

    _add(
        g,
        "chain:ethereum",
        "chain",
        REGISTRY["chain"]["ethereum"]["label"],
        "registry",
        "settlement for every contract below",
    )
    _add(
        g,
        f"asset:{pos.collateral_address}",
        "asset",
        pos.collateral_symbol,
        "Pendle API /markets",
        f"PT {pos.collateral_address}, matures {pm['expiry'][:10]}, implied APY {pos.implied_apy:.2%}",
    )
    _add(
        g,
        f"amm:{pm['address']}",
        "amm",
        f"Pendle market {pm['name']} (PT/SY AMM + SY adapter)",
        "Pendle API /markets/{m}/data",
        f"liquidity ${pos.amm_liquidity_usd or 0:,.0f}, total TVL ${data.get('totalTvl', {}).get('usd', 0):,.0f}",
        protocol="pendle",
    )
    issuer_label = (
        f"{pos.underlying_symbol} ({reg['issuer']})" if reg else f"{pos.underlying_symbol} (unidentified issuer)"
    )
    _add(
        g,
        f"issuer:{und}",
        "issuer",
        issuer_label,
        "Pendle API underlyingAsset + registry" if reg else "Pendle API underlyingAsset (not in registry)",
        f"price ${meta.get('price', float('nan')):.4f} (DefiLlama coins); 1y max drawdown "
        f"{(pos.underlying_drawdown_1y or 0):.2%} over {dd['points']} daily points",
        registered=bool(reg),
    )
    for i, dep in enumerate((reg or {}).get("dependencies", [])):
        _add(g, f"offchain:{und}:{i}", "offchain", dep, "registry", "off-chain dependency of the issuer")
        g.add_edge(f"issuer:{und}", f"offchain:{und}:{i}", rel="relies on")

    g.add_edge(f"asset:{pos.collateral_address}", f"amm:{pm['address']}", rel="minted by / exits through")
    g.add_edge(f"asset:{pos.collateral_address}", f"issuer:{und}", rel="redeems into")
    g.add_edge(f"amm:{pm['address']}", "chain:ethereum", rel="settles on")
    g.add_edge(f"issuer:{und}", "chain:ethereum", rel="settles on")
    if not reg:
        pos.notes.append(f"Underlying {und} is not in the registry: default (conservative) issuer prior used.")


def discover_morpho_position(f: S.Fetcher, market_id: str, user: str | None = None) -> Position:
    if user is None:
        user = top_borrower(f, market_id)
    d = S.morpho(f, POSITION_QUERY, {"id": market_id, "user": user})
    m, p = d["marketById"], d["marketPosition"]
    if p is None or float(p["state"]["collateral"] or 0) == 0:
        raise S.SourceError(f"{user} has no collateral in Morpho market {market_id}")
    coll, loan = m["collateralAsset"], m["loanAsset"]
    if not coll["symbol"].upper().startswith("PT-"):
        raise S.SourceError(f"collateral {coll['symbol']} is not a Pendle PT; this increment covers PT positions only")
    lltv = int(m["lltv"]) / 1e18
    units = int(p["state"]["collateral"]) / 10 ** coll["decimals"]
    pos = Position(
        label=f"Morpho borrower {user[:8]}…{user[-4:]} · {coll['symbol']} → {loan['symbol']}",
        collateral_units=units,
        collateral_symbol=coll["symbol"],
        collateral_address=coll["address"].lower(),
        pt_price_usd=coll["priceUsd"],
        collateral_decimals=coll["decimals"],
        debt_usd=p["state"]["borrowAssetsUsd"],
        loan_symbol=loan["symbol"],
        loan_address=loan["address"].lower(),
        lltv=lltv,
        lif=morpho_lif(lltv),
        borrow_apy=m["state"]["borrowApy"],
        health_factor=p["healthFactor"],
        lending_liquidity_usd=m["state"]["liquidityAssetsUsd"],
        morpho_market=market_id,
        borrower=user.lower(),
        debt_raw=int(p["state"]["borrowAssets"] or 0),
        loan_decimals=loan["decimals"],
    )
    pm = find_pendle_market(f, coll["address"])
    _build_pt_layers(f, pos, pm)

    pt_in_loan = coll["priceUsd"] / loan["priceUsd"]
    mode, oprice, why, ambiguous, verified = infer_oracle(
        f, m["oracleAddress"], coll["decimals"], loan["decimals"], pt_in_loan, pos.pt_discount
    )
    pos.oracle_mode, pos.oracle_price, pos.oracle_ambiguous = mode, oprice, ambiguous
    if ambiguous:
        pos.notes.append(
            "Oracle behaviour is ambiguous (PT close to par): the report also shows the verdict "
            "if the oracle were fundamental."
        )

    g = pos.graph
    mk = f"lending:{market_id}"
    _add(
        g,
        mk,
        "lending",
        f"Morpho Blue market {coll['symbol']}/{loan['symbol']} (LLTV {lltv:.1%})",
        "Morpho API marketById/marketPosition",
        f"debt ${pos.debt_usd:,.0f}, HF {pos.health_factor:.3f}, utilization {m['state']['utilization']:.1%}, "
        f"idle liquidity ${pos.lending_liquidity_usd:,.0f}, borrow APY {pos.borrow_apy:.2%}",
        protocol="morpho-blue",
    )
    _add(
        g,
        f"oracle:{m['oracleAddress'].lower()}",
        "oracle",
        f"Oracle {m['oracleAddress'][:10]}…",
        "Ethereum RPC eth_call price(), eth_getCode; Etherscan getsourcecode",
        why,
        mode=mode,
        verified=verified,
    )
    sreg = REGISTRY["stables"].get(loan["address"].lower(), {})
    _add(
        g,
        f"stable:{loan['address'].lower()}",
        "stable",
        f"{loan['symbol']} ({sreg.get('issuer', 'loan asset')})",
        "Morpho API loanAsset + registry",
        sreg.get("basis", "loan asset"),
    )
    g.add_node(
        "position",
        kind="position",
        label=pos.label,
        source="Morpho API",
        evidence=f"{units:,.0f} {coll['symbol']} (${pos.collateral_usd:,.0f}) against ${pos.debt_usd:,.0f} {loan['symbol']}",
    )
    g.add_edge("position", mk, rel="borrows on")
    g.add_edge(mk, f"asset:{pos.collateral_address}", rel="collateral")
    g.add_edge(mk, f"oracle:{m['oracleAddress'].lower()}", rel="prices collateral with")
    g.add_edge(mk, f"stable:{loan['address'].lower()}", rel="debt in")
    g.add_edge(
        f"oracle:{m['oracleAddress'].lower()}",
        f"amm:{pm['address']}",
        rel="reads (inferred)" if mode == "market-tracking" else "independent of (inferred)",
    )
    g.add_edge(mk, "chain:ethereum", rel="settles on")
    return pos


def discover_pt_holding(f: S.Fetcher, pendle_market: str, pt_amount: float) -> Position:
    pm = pendle_market_by_address(f, pendle_market)
    pt = _addr(pm["pt"])
    price = S.coin_prices(f, [pt]).get(f"ethereum:{pt}", {})
    if "price" not in price:
        raise S.SourceError(f"no USD price for PT {pt} on DefiLlama")
    sym = price.get("symbol") or f"PT-{pm['name']}"
    pos = Position(
        label=f"PT holding · {pt_amount:,.0f} {sym}",
        collateral_units=pt_amount,
        collateral_symbol=sym,
        collateral_address=pt,
        pt_price_usd=price["price"],
        collateral_decimals=int(price.get("decimals", 18)),
    )
    _build_pt_layers(f, pos, pm)
    pos.graph.add_node(
        "position",
        kind="position",
        label=pos.label,
        source="input",
        evidence=f"{pt_amount:,.0f} PT (${pos.collateral_usd:,.0f})",
    )
    pos.graph.add_edge("position", f"asset:{pt}", rel="holds")
    return pos


def exit_quote(f: S.Fetcher, pos: Position) -> dict:
    """Real Pendle quote to sell the whole PT balance into the loan asset (or the underlying)."""
    token_out = pos.loan_address or pos.underlying_address
    amount_raw = str(int(pos.collateral_units * 10**pos.collateral_decimals))
    url = (
        f"{S.PENDLE}/v2/sdk/1/markets/{pos.pendle_market}/swap?receiver=0x1111111111111111111111111111111111111111"
        f"&slippage=0.01&enableAggregator=true&tokenIn={pos.collateral_address}&tokenOut={token_out}&amountIn={amount_raw}"
    )
    try:
        d = f.get_json(url, transform=lambda r: {"data": r.get("data"), "method": r.get("method")})["data"]
        impact = abs(float(d["priceImpact"]))
        fee = float(d.get("fee", {}).get("usd", 0.0))
        return {
            "source": "Pendle swap quote",
            "price_impact": impact,
            "fee_usd": fee,
            "amount_out_raw": d.get("amountOut"),
            "estimated": False,
        }
    except (S.SourceError, S.CacheMiss, KeyError, TypeError) as e:
        liq = pos.amm_liquidity_usd or 1.0
        impact = min(0.5, pos.collateral_usd / (2 * liq) * 0.01)
        return {
            "source": f"AMM-depth estimate (quote failed: {str(e)[:80]})",
            "price_impact": impact,
            "fee_usd": 0.0,
            "amount_out_raw": None,
            "estimated": True,
        }


def partial_exit_quote(f: S.Fetcher, pos: Position, fraction: float) -> dict:
    part = copy.copy(pos)
    part.collateral_units = pos.collateral_units * fraction
    return exit_quote(f, part)


# --- sale-size ladders for the shock engine's squeeze (plan 2026-10-10-propagation-engine, D97, D98)


def quote_ladder(
    f: S.Fetcher,
    market: str,
    token_in: str,
    token_out: str,
    decimals_in: int,
    usd_per_unit: float,
    aggregator: bool,
    sizes_usd: list[float],
) -> tuple[list[tuple[float, int]], bool]:
    """Real Pendle swap quotes for selling token_in at growing sizes: ([(USD sold at today's price, amount out raw)],
    refused). Stops at the first size Pendle cannot route ("MarketProportionTooHigh. Market liquidity is likely
    insufficient", no route): `refused` then says the market's capacity lies below that size."""
    out: list[tuple[float, int]] = []
    if usd_per_unit <= 0:
        return out, False
    for usd in sizes_usd:
        amount = int(usd / usd_per_unit * 10**decimals_in)
        url = (
            f"{S.PENDLE}/v2/sdk/1/markets/{market}/swap?receiver=0x1111111111111111111111111111111111111111"
            f"&slippage=0.01&enableAggregator={'true' if aggregator else 'false'}&tokenIn={token_in}"
            f"&tokenOut={token_out}&amountIn={amount}"
        )
        try:
            d = f.get_json(url, transform=lambda r: {"data": r.get("data")})["data"]
            out.append((float(usd), int(d["amountOut"])))
        except (S.SourceError, KeyError, TypeError, ValueError):
            return out, True  # a missing cached answer (CacheMiss) is not a refusal: it fails the replay instead
    return out, False


def ladder_sizes(liquidity_usd: float | None) -> list[float]:
    """Sale sizes for a pool: multiples of its liquidity (`engine.quote_sizes_x_liquidity`), at most
    `engine.quote_max_usd` (Pendle refuses quotes above 100M USD)."""
    e = REGISTRY["engine"]
    if not liquidity_usd:
        return []
    return sorted({min(e["quote_max_usd"], round(x * liquidity_usd, -3)) for x in e["quote_sizes_x_liquidity"]})


def marginal_curve(ladder: list[tuple[float, float]], min_ratio: float) -> tuple[list[list[float]], float | None]:
    """Pure. From [(sold, received)] in any units, the marginal price after each step relative to the first step's
    average (the spot): [[sold up to, factor]], and the capacity, where the marginal price falls under `min_ratio` of
    spot or the amount received stops growing (None when the ladder never reaches it)."""
    pts = sorted((s, r) for s, r in ladder if s > 0 and r > 0)
    if len(pts) < 2:
        return [], None
    spot = pts[0][1] / pts[0][0]
    curve, capacity = [[pts[0][0], 1.0]], None
    for (s0, r0), (s1, r1) in zip(pts, pts[1:]):
        factor = max(0.0, (r1 - r0) / (s1 - s0) / spot)
        if factor < min_ratio:
            capacity = s0
            break
        curve.append([s1, min(1.0, factor)])
    return curve, capacity
