"""Cross-checks of the data sources against each other.

Everything else trusts one RPC and the Morpho/Pendle APIs. These checks compare:
  - the main RPC with a second, independent keyless RPC (same block, same hash);
  - the Morpho API with the chain (position, vault total assets).
A check that cannot run (offline snapshot without it, endpoint down) says "not checked"; it
never stops the analysis.
"""

from __future__ import annotations

from dataclasses import dataclass

from eth_abi import encode

from . import sources as S
from .abi import MORPHO_BLUE, selector

SECOND_RPCS = ["https://eth.drpc.org", "https://1rpc.io/eth"]
TOLERANCE = 0.005


@dataclass
class Check:
    name: str
    ok: bool | None  # None = not checked
    detail: str

    @property
    def line(self) -> str:
        tag = {True: "ok", False: "MISMATCH", None: "not checked"}[self.ok]
        return f"cross-check {self.name}: {tag} — {self.detail}"


def _rpc_at(f: S.Fetcher, url: str, method: str, params: list):
    r = f.post_json(url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    return r.get("result") if isinstance(r, dict) else None


def second_rpc(f: S.Fetcher, block: int | None = None) -> Check:
    """Same block hash from the main RPC and an independent one (default: head − 5)."""
    try:
        if block is None:
            block = int(_rpc_at(f, S.RPC, "eth_blockNumber", []), 16) - 5
        main = (_rpc_at(f, S.RPC, "eth_getBlockByNumber", [hex(block), False]) or {}).get("hash")
    except (S.SourceError, S.CacheMiss, TypeError, ValueError) as e:
        return Check("second RPC", None, f"main RPC block unavailable ({str(e)[:60]})")
    for url in SECOND_RPCS:
        try:
            other = (_rpc_at(f, url, "eth_getBlockByNumber", [hex(block), False]) or {}).get("hash")
        except (S.SourceError, S.CacheMiss):
            continue
        if other:
            if other == main:
                return Check("second RPC", True, f"block {block} hash {main[:12]}… identical on {url}")
            return Check(
                "second RPC",
                False,
                f"block {block}: main RPC {str(main)[:12]}… vs {url} {other[:12]}… — "
                "one source is on another fork or wrong; do not act on its data",
            )
    return Check("second RPC", None, "no second RPC answered")


def morpho_position(
    f: S.Fetcher,
    market_id: str,
    user: str,
    coll_decimals: int,
    loan_decimals: int,
    api_collateral_units: float,
    api_borrow_raw: int,
) -> Check:
    """Morpho API position vs Morpho Blue `position(id, user)` and `market(id)` on-chain."""
    mid = bytes.fromhex(market_id[2:])
    calls = [
        (MORPHO_BLUE, "0x" + selector("position(bytes32,address)") + encode(["bytes32", "address"], [mid, user]).hex()),
        (MORPHO_BLUE, "0x" + selector("market(bytes32)") + encode(["bytes32"], [mid]).hex()),
    ]
    try:
        pos, mk = S.rpc_batch(f, calls, "latest")
    except (S.SourceError, S.CacheMiss) as e:
        return Check("Morpho API vs chain", None, f"on-chain position unavailable ({str(e)[:60]})")
    if not pos or not mk:
        return Check("Morpho API vs chain", None, "on-chain read reverted")
    w = [int(pos[2 + 64 * i : 2 + 64 * (i + 1)], 16) for i in range(3)]  # supplyShares, borrowShares, collateral
    m = [int(mk[2 + 64 * i : 2 + 64 * (i + 1)], 16) for i in range(4)]  # tsa, tss, tba, tbs
    coll = w[2] / 10**coll_decimals
    debt = w[1] * (m[2] + 1) // (m[3] + 10**6)
    dc = abs(coll / api_collateral_units - 1) if api_collateral_units else 1.0
    dd = abs(debt / api_borrow_raw - 1) if api_borrow_raw else (0.0 if debt == 0 else 1.0)
    detail = (
        f"collateral {coll:,.2f} on-chain vs {api_collateral_units:,.2f} API ({dc:.3%}); "
        f"debt {debt / 10**loan_decimals:,.2f} vs {api_borrow_raw / 10**loan_decimals:,.2f} ({dd:.3%})"
    )
    ok = dc <= TOLERANCE and dd <= TOLERANCE
    return Check(
        "Morpho API vs chain", ok, detail + ("" if ok else " — the API is stale or wrong; the chain is authoritative")
    )


def vault_total_assets(f: S.Fetcher, vault: str, chain_total: int, decimals: int) -> Check:
    try:
        d = S.morpho(f, "query($a:String!){ vaultV2ByAddress(address:$a, chainId:1){ totalAssets } }", {"a": vault})
        api = int(d["vaultV2ByAddress"]["totalAssets"])
    except (S.SourceError, S.CacheMiss, KeyError, TypeError) as e:
        return Check("Morpho API vs chain", None, f"API total assets unavailable ({str(e)[:60]})")
    diff = abs(chain_total / api - 1) if api else 1.0
    ok = diff <= TOLERANCE
    return Check(
        "Morpho API vs chain",
        ok,
        f"vault total assets {chain_total / 10**decimals:,.0f} on-chain vs {api / 10**decimals:,.0f} API ({diff:.3%})",
    )
