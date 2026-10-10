"""What an address holds on Morpho (D31, D32).

The Morpho API is used only to find the positions; everything monitored is read on-chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import sources as S

QUERY = """query($a:String!){ userByAddress(address:$a, chainId:1){
  marketPositions{ market{ marketId } state{ borrowAssets collateral } }
  vaultV2Positions{ vault{ address name } shares } } }"""


@dataclass
class UserPositions:
    address: str
    borrows: list[str] = field(default_factory=list)  # Blue market ids with debt > 0
    vaults: list[str] = field(default_factory=list)  # Vault V2 addresses with shares > 0
    api_state: dict[str, dict] = field(default_factory=dict)  # market id -> API collateral / borrowAssets
    collateral_only: int = 0  # markets with collateral but no debt (not watched)


def discover_user(f: S.Fetcher, address: str) -> UserPositions:
    data = S.morpho(f, QUERY, {"a": address})["userByAddress"]
    out = UserPositions(address.lower())
    if not data:
        return out
    for p in data.get("marketPositions") or []:
        mid = p["market"]["marketId"].lower()
        st = p.get("state") or {}
        debt = int(st.get("borrowAssets") or 0)
        if debt > 0:
            out.borrows.append(mid)
            out.api_state[mid] = {"borrowAssets": debt, "collateral": int(st.get("collateral") or 0)}
        elif int(st.get("collateral") or 0) > 0:
            out.collateral_only += 1
    for v in data.get("vaultV2Positions") or []:
        if int(v.get("shares") or 0) > 0:
            out.vaults.append(v["vault"]["address"].lower())
    return out
