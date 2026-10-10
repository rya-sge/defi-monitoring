"""Morpho Vault V2: structure (vault → adapters → Blue markets) and state at a block.

Everything is read on-chain (D24); the Morpho API is only used to find a default depositor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from eth_abi import decode, encode

from . import sources as S
from .abi import MORPHO_BLUE, OTHER_VAULT_TIMELOCKED, RISK_INCREASING_ADAPTER, RISK_INCREASING_VAULT, selector

WAD = 10 ** 18


def _call(to: str, sig: str, types: list[str] | None = None, values: list | None = None) -> tuple[str, str]:
    data = "0x" + selector(sig) + (encode(types, values).hex() if types else "")
    return to, data


def _uint(raw: str | None) -> int | None:
    return int(raw, 16) if raw else None


def _addr(raw: str | None) -> str | None:
    return ("0x" + raw[-40:]).lower() if raw else None


@dataclass
class MarketParams:
    id: str
    loan_token: str
    collateral_token: str
    oracle: str
    irm: str
    lltv: float
    collateral_symbol: str = "?"


@dataclass
class AdapterView:
    address: str
    kind: str                         # market | vault_v1 | unknown
    markets: dict[str, MarketParams] = field(default_factory=dict)
    v1_vault: str | None = None


@dataclass
class VaultView:
    address: str
    asset: str
    asset_symbol: str
    decimals: int
    name: str
    adapters: list[AdapterView]
    liquidity_adapter: str | None
    liquidity_market: str | None = None   # the market a plain withdrawal can draw on (liquidityData)
    # (contract, function signature) -> (timelock in seconds, abdicated), read at discovery (D44)
    timelocks: dict[tuple[str, str], tuple[int, bool]] = field(default_factory=dict)

    def timelock_of(self, contract: str, sel_hex: str) -> tuple[str, int, bool] | None:
        """(signature, seconds, abdicated) for a selector submitted on `contract`, if read."""
        for (c, sig), (t, ab) in self.timelocks.items():
            if c == contract and selector(sig) == sel_hex.removeprefix("0x"):
                return sig, t, ab
        return None

    @property
    def kinds(self) -> dict[str, str]:
        k = {self.address: "vault", MORPHO_BLUE: "blue"}
        for a in self.adapters:
            k[a.address] = "adapter"
        return k

    @property
    def market_ids(self) -> list[str]:
        return [m for a in self.adapters for m in a.markets]

    def market(self, market_id: str) -> MarketParams | None:
        for a in self.adapters:
            if market_id in a.markets:
                return a.markets[market_id]
        return None


@dataclass
class MarketState:
    id: str
    supply_shares: int                # held by the adapter
    total_supply_assets: int
    total_supply_shares: int
    total_borrow_assets: int
    vault_assets: int                 # the adapter's supply, in assets
    oracle_price: int | None

    @property
    def utilization(self) -> float:
        return self.total_borrow_assets / self.total_supply_assets if self.total_supply_assets else 0.0

    @property
    def liquidity(self) -> int:
        return max(0, self.total_supply_assets - self.total_borrow_assets)

    @property
    def withdrawable(self) -> int:
        return min(self.vault_assets, self.liquidity)


@dataclass
class VaultState:
    block: int
    total_assets: int
    total_supply: int
    idle: int                         # vault's own balance of the asset
    real_assets: dict[str, int]       # adapter -> realAssets
    markets: dict[str, MarketState]
    caps: dict[str, tuple[int, int, int]]   # id -> (allocation, absoluteCap, relativeCap)
    performance_fee: int
    management_fee: int
    depositor: str | None = None
    depositor_shares: int = 0
    stored_total_assets: int | None = None      # `_totalAssets`, updated only by accrueInterest
    liquidity_market: str | None = None
    penalties: dict[str, int] = field(default_factory=dict)   # adapter -> forceDeallocatePenalty (WAD)
    can_send_shares: bool | None = None         # gates, for the depositor
    can_receive_assets: bool | None = None

    @property
    def share_price(self) -> float:
        return self.total_assets / self.total_supply if self.total_supply else 0.0

    @property
    def depositor_assets(self) -> int:
        return self.depositor_shares * self.total_assets // self.total_supply if self.total_supply else 0

    @property
    def withdrawable(self) -> int:
        """What a plain withdraw/redeem can pay now: idle assets plus what the liquidity adapter can
        pull from the one market in `liquidityData` (Morpho docs, "Compute deposit and withdrawal limits")."""
        liq = self.markets.get(self.liquidity_market) if self.liquidity_market else None
        return self.idle + (liq.withdrawable if liq else 0)

    @property
    def force_withdrawable(self) -> int:
        """Further assets only `forceDeallocate` can reach: the other markets' withdrawable part."""
        return sum(m.withdrawable for mid, m in self.markets.items() if mid != self.liquidity_market)

    @property
    def pending_loss(self) -> int:
        """Loss already in `totalAssets()` (computed as if accrued now) but not yet in the stored `_totalAssets`.
        Every entry point accrues before pricing, so this is a detection signal, not an exit window: the
        window in which early exits shift a loss lies before Blue writes off the bad debt."""
        if self.stored_total_assets is None:
            return 0
        return max(0, self.stored_total_assets - self.total_assets)


def _cap_ids(adapter: str, mp: MarketParams) -> dict[str, str]:
    """The 3 ids a MorphoMarketV1AdapterV2 registers for a market (docs: `ids`)."""
    from eth_utils import keccak
    params = (mp.loan_token, mp.collateral_token, mp.oracle, mp.irm, int(round(mp.lltv * WAD)))
    return {
        "adapter": "0x" + keccak(encode(["string", "address"], ["this", adapter])).hex(),
        "collateral": "0x" + keccak(encode(["string", "address"], ["collateralToken", mp.collateral_token])).hex(),
        "market": "0x" + keccak(encode(["string", "address", "(address,address,address,address,uint256)"],
                                       ["this/marketParams", adapter, params])).hex(),
    }


def _symbol(f: S.Fetcher, token: str, block) -> str:
    raw = S.rpc_batch(f, [_call(token, "symbol()")], block)[0]
    if not raw:
        return token[:10]
    try:
        return decode(["string"], bytes.fromhex(raw[2:]))[0]
    except Exception:
        b = bytes.fromhex(raw[2:66]).rstrip(b"\0")
        return b.decode(errors="ignore") or token[:10]


def discover_vault(f: S.Fetcher, address: str, block: int | str = "latest") -> VaultView:
    v = address.lower()
    asset, n, liq, name_raw = S.rpc_batch(f, [_call(v, "asset()"), _call(v, "adaptersLength()"),
                                                _call(v, "liquidityAdapter()"), _call(v, "name()")], block)
    if asset is None or n is None:
        raise S.SourceError(f"{address} does not answer asset()/adaptersLength(): not a Morpho Vault V2")
    asset = _addr(asset)
    dec = _uint(S.rpc_batch(f, [_call(asset, "decimals()")], block)[0]) or 18
    name = decode(["string"], bytes.fromhex(name_raw[2:]))[0] if name_raw else v
    adapters = [_addr(r) for r in S.rpc_batch(f, [_call(v, "adapters(uint256)", ["uint256"], [i]) for i in range(_uint(n))], block)]

    views = []
    for a in adapters:
        n_m, v1 = S.rpc_batch(f, [_call(a, "marketIdsLength()"), _call(a, "morphoVaultV1()")], block)
        if n_m is not None:
            ids = S.rpc_batch(f, [_call(a, "marketIds(uint256)", ["uint256"], [i]) for i in range(_uint(n_m))], block)
            params = S.rpc_batch(f, [_call(MORPHO_BLUE, "idToMarketParams(bytes32)", ["bytes32"], [bytes.fromhex(i[2:])])
                                     for i in ids], block)
            av = AdapterView(a, "market")
            for mid, raw in zip(ids, params):
                loan, coll, orc, irm, lltv = decode(["address"] * 4 + ["uint256"], bytes.fromhex(raw[2:]))
                av.markets[mid] = MarketParams(mid, loan.lower(), coll.lower(), orc.lower(), irm.lower(), lltv / WAD)
            for mp in av.markets.values():
                mp.collateral_symbol = _symbol(f, mp.collateral_token, block)
            views.append(av)
        elif v1 is not None:
            views.append(AdapterView(a, "vault_v1", v1_vault=_addr(v1)))
        else:
            views.append(AdapterView(a, "unknown"))
    liq_adapter = _addr(liq) if liq and int(liq, 16) else None
    liq_market = None
    if liq_adapter and any(a.address == liq_adapter and a.kind == "market" for a in views):
        raw = S.rpc_batch(f, [_call(v, "liquidityData()")], block)[0]
        try:
            data = decode(["bytes"], bytes.fromhex(raw[2:]))[0] if raw else b""
            if data:
                from eth_utils import keccak
                liq_market = "0x" + keccak(data).hex()   # Blue's market id = keccak256(abi.encode(marketParams))
        except Exception:
            liq_market = None
    view = VaultView(v, asset, _symbol(f, asset, block), dec, name, views, liq_adapter, liq_market)
    view.timelocks = read_timelocks(f, view, block)
    return view


def read_timelocks(f: S.Fetcher, view: "VaultView", block) -> dict:
    targets = [(view.address, sig) for sig in RISK_INCREASING_VAULT + OTHER_VAULT_TIMELOCKED]
    targets += [(a.address, sig) for a in view.adapters if a.kind == "market" for sig in RISK_INCREASING_ADAPTER]
    calls = []
    for c, sig in targets:
        b4 = bytes.fromhex(selector(sig))
        calls += [_call(c, "timelock(bytes4)", ["bytes4"], [b4]), _call(c, "abdicated(bytes4)", ["bytes4"], [b4])]
    res = S.rpc_batch(f, calls, block)
    out = {}
    for i, key in enumerate(targets):
        t, ab = res[2 * i], res[2 * i + 1]
        if t is not None:
            out[key] = (_uint(t), bool(_uint(ab)))
    return out


def read_state(f: S.Fetcher, view: VaultView, block: int, depositor: str | None = None) -> VaultState:
    v = view.address
    calls = [_call(v, "totalAssets()"), _call(v, "totalSupply()"), _call(view.asset, "balanceOf(address)", ["address"], [v]),
             _call(v, "performanceFee()"), _call(v, "managementFee()")]
    if depositor:
        calls += [_call(v, "balanceOf(address)", ["address"], [depositor]),
                  _call(v, "canSendShares(address)", ["address"], [depositor]),
                  _call(v, "canReceiveAssets(address)", ["address"], [depositor])]
    calls.append(_call(v, "_totalAssets()"))
    for a in view.adapters:
        calls += [_call(a.address, "realAssets()"), _call(v, "forceDeallocatePenalty(address)", ["address"], [a.address])]
    mlist = [(a, m) for a in view.adapters for m in a.markets.values()]
    for a, m in mlist:
        mid = bytes.fromhex(m.id[2:])
        calls += [_call(a.address, "supplyShares(bytes32)", ["bytes32"], [mid]),
                  _call(MORPHO_BLUE, "market(bytes32)", ["bytes32"], [mid]),
                  _call(m.oracle, "price()")]
    cap_keys = []
    for a, m in mlist:
        for kind, cid in _cap_ids(a.address, m).items():
            if cid in cap_keys:
                continue
            cap_keys.append(cid)
            b = bytes.fromhex(cid[2:])
            calls += [_call(v, "allocation(bytes32)", ["bytes32"], [b]), _call(v, "absoluteCap(bytes32)", ["bytes32"], [b]),
                      _call(v, "relativeCap(bytes32)", ["bytes32"], [b])]
    res = S.rpc_batch(f, calls, block)
    it = iter(res)
    ta, ts, idle, pf, mf = (_uint(next(it)) or 0 for _ in range(5))
    dshares, can_send, can_recv = 0, None, None
    if depositor:
        dshares = _uint(next(it)) or 0
        cs, cr = next(it), next(it)
        can_send = bool(_uint(cs)) if cs else None
        can_recv = bool(_uint(cr)) if cr else None
    stored = _uint(next(it))
    real, penalties = {}, {}
    for a in view.adapters:
        real[a.address] = _uint(next(it)) or 0
        penalties[a.address] = _uint(next(it)) or 0
    markets = {}
    for a, m in mlist:
        ss = _uint(next(it)) or 0
        mk = next(it)
        price = _uint(next(it))
        tsa, tss, tba = (int(mk[2 + 64 * i: 2 + 64 * (i + 1)], 16) for i in range(3)) if mk else (0, 0, 0)
        assets = ss * (tsa + 1) // (tss + 10 ** 6) if ss else 0     # Blue's virtual shares / assets
        markets[m.id] = MarketState(m.id, ss, tsa, tss, tba, assets, price)
    caps = {cid: tuple(_uint(next(it)) or 0 for _ in range(3)) for cid in cap_keys}
    return VaultState(block, ta, ts, idle, real, markets, caps, pf, mf, depositor, dshares,
                      stored, view.liquidity_market, penalties, can_send, can_recv)


def largest_depositor(f: S.Fetcher, vault: str) -> str | None:
    """Default depositor via the Morpho API (D24): the largest share holder."""
    try:
        d = S.morpho(f, """query($a:String!){ vaultV2ByAddress(address:$a, chainId:1){
              positions(first:100){ items{ user{ address } shares } } } }""", {"a": vault})
        items = d["vaultV2ByAddress"]["positions"]["items"]
        top = max(items, key=lambda i: int(i["shares"] or 0), default=None)
        return top["user"]["address"].lower() if top else None
    except (S.SourceError, S.CacheMiss, KeyError, TypeError):
        return None


def cap_ids(adapter: str, mp: MarketParams) -> dict[str, str]:
    return _cap_ids(adapter, mp)
