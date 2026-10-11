"""Event and function signatures of Morpho Blue, Vault V2 and its adapters (D19, D29).

Signatures come from EventsLib.sol / the adapter interfaces on the `main` branch of
morpho-org/morpho-blue and morpho-org/vault-v2, read 2026-10-10.
"""

from __future__ import annotations

from dataclasses import dataclass

from eth_abi import decode, encode
from eth_utils import keccak

MORPHO_BLUE = "0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb"


def selector(signature: str) -> str:
    return keccak(text=signature)[:4].hex()


def topic(signature: str) -> str:
    return "0x" + keccak(text=signature).hex()


@dataclass(frozen=True)
class EventSpec:
    contract: str  # "blue" | "vault" | "adapter"
    name: str
    params: tuple[tuple[str, str, bool], ...]  # (name, type, indexed)

    @property
    def signature(self) -> str:
        return f"{self.name}({','.join(t for _, t, _ in self.params)})"

    @property
    def topic0(self) -> str:
        return topic(self.signature)


def _ev(contract: str, name: str, *params: str) -> EventSpec:
    """params as 'type name' or 'type indexed name'."""
    out = []
    for p in params:
        parts = p.split()
        out.append((parts[-1], parts[0], "indexed" in parts))
    return EventSpec(contract, name, tuple(out))


EVENTS: list[EventSpec] = [
    # Morpho Blue
    _ev(
        "blue",
        "Supply",
        "bytes32 indexed id",
        "address indexed caller",
        "address indexed onBehalf",
        "uint256 assets",
        "uint256 shares",
    ),
    _ev(
        "blue",
        "Withdraw",
        "bytes32 indexed id",
        "address caller",
        "address indexed onBehalf",
        "address indexed receiver",
        "uint256 assets",
        "uint256 shares",
    ),
    _ev(
        "blue",
        "Borrow",
        "bytes32 indexed id",
        "address caller",
        "address indexed onBehalf",
        "address indexed receiver",
        "uint256 assets",
        "uint256 shares",
    ),
    _ev(
        "blue",
        "Repay",
        "bytes32 indexed id",
        "address indexed caller",
        "address indexed onBehalf",
        "uint256 assets",
        "uint256 shares",
    ),
    _ev(
        "blue",
        "SupplyCollateral",
        "bytes32 indexed id",
        "address indexed caller",
        "address indexed onBehalf",
        "uint256 assets",
    ),
    _ev(
        "blue",
        "WithdrawCollateral",
        "bytes32 indexed id",
        "address caller",
        "address indexed onBehalf",
        "address indexed receiver",
        "uint256 assets",
    ),
    _ev(
        "blue",
        "Liquidate",
        "bytes32 indexed id",
        "address indexed caller",
        "address indexed borrower",
        "uint256 repaidAssets",
        "uint256 repaidShares",
        "uint256 seizedAssets",
        "uint256 badDebtAssets",
        "uint256 badDebtShares",
    ),
    _ev(
        "blue",
        "AccrueInterest",
        "bytes32 indexed id",
        "uint256 prevBorrowRate",
        "uint256 interest",
        "uint256 feeShares",
    ),
    _ev("blue", "SetFee", "bytes32 indexed id", "uint256 newFee"),
    # Morpho Blue owner actions (D57): no market id in topic1, fetched with their own filter
    _ev("blue", "SetOwner", "address indexed newOwner"),
    _ev("blue", "EnableIrm", "address indexed irm"),
    _ev("blue", "EnableLltv", "uint256 lltv"),
    _ev("blue", "SetFeeRecipient", "address indexed newFeeRecipient"),
    # not about a market: topic1 is the caller, so the poller fetches it with its own filter
    _ev(
        "blue",
        "SetAuthorization",
        "address indexed caller",
        "address indexed authorizer",
        "address indexed authorized",
        "bool newIsAuthorized",
    ),
    # Vault V2
    _ev("vault", "Deposit", "address indexed sender", "address indexed onBehalf", "uint256 assets", "uint256 shares"),
    _ev(
        "vault",
        "Withdraw",
        "address indexed sender",
        "address indexed receiver",
        "address indexed onBehalf",
        "uint256 assets",
        "uint256 shares",
    ),
    _ev("vault", "Transfer", "address indexed from", "address indexed to", "uint256 shares"),
    _ev("vault", "Approval", "address indexed owner", "address indexed spender", "uint256 shares"),
    _ev(
        "vault", "AllowanceUpdatedByTransferFrom", "address indexed owner", "address indexed spender", "uint256 shares"
    ),
    _ev(
        "vault",
        "Permit",
        "address indexed owner",
        "address indexed spender",
        "uint256 shares",
        "uint256 nonce",
        "uint256 deadline",
    ),
    _ev("vault", "Constructor", "address indexed owner", "address indexed asset"),
    _ev(
        "vault",
        "Allocate",
        "address indexed sender",
        "address indexed adapter",
        "uint256 assets",
        "bytes32[] ids",
        "int256 change",
    ),
    _ev(
        "vault",
        "Deallocate",
        "address indexed sender",
        "address indexed adapter",
        "uint256 assets",
        "bytes32[] ids",
        "int256 change",
    ),
    _ev(
        "vault",
        "ForceDeallocate",
        "address indexed sender",
        "address adapter",
        "uint256 assets",
        "address indexed onBehalf",
        "bytes32[] ids",
        "uint256 penaltyAssets",
    ),
    _ev(
        "vault",
        "AccrueInterest",
        "uint256 previousTotalAssets",
        "uint256 newTotalAssets",
        "uint256 performanceFeeShares",
        "uint256 managementFeeShares",
    ),
    _ev("vault", "Submit", "bytes4 indexed selector", "bytes data", "uint256 executableAt"),
    _ev("vault", "Accept", "bytes4 indexed selector", "bytes data"),
    _ev("vault", "Revoke", "address indexed sender", "bytes4 indexed selector", "bytes data"),
    _ev("vault", "SetOwner", "address indexed newOwner"),
    _ev("vault", "SetCurator", "address indexed newCurator"),
    _ev("vault", "SetIsSentinel", "address indexed account", "bool newIsSentinel"),
    _ev("vault", "SetIsAllocator", "address indexed account", "bool newIsAllocator"),
    _ev("vault", "SetReceiveSharesGate", "address indexed newReceiveSharesGate"),
    _ev("vault", "SetSendSharesGate", "address indexed newSendSharesGate"),
    _ev("vault", "SetReceiveAssetsGate", "address indexed newReceiveAssetsGate"),
    _ev("vault", "SetSendAssetsGate", "address indexed newSendAssetsGate"),
    _ev("vault", "SetAdapterRegistry", "address indexed newAdapterRegistry"),
    _ev("vault", "AddAdapter", "address indexed account"),
    _ev("vault", "RemoveAdapter", "address indexed account"),
    _ev("vault", "DecreaseTimelock", "bytes4 indexed selector", "uint256 newDuration"),
    _ev("vault", "IncreaseTimelock", "bytes4 indexed selector", "uint256 newDuration"),
    _ev("vault", "Abdicate", "bytes4 indexed selector"),
    _ev(
        "vault",
        "SetLiquidityAdapterAndData",
        "address indexed sender",
        "address indexed newLiquidityAdapter",
        "bytes indexed newLiquidityData",
    ),
    _ev("vault", "SetPerformanceFee", "uint256 newPerformanceFee"),
    _ev("vault", "SetPerformanceFeeRecipient", "address indexed newPerformanceFeeRecipient"),
    _ev("vault", "SetManagementFee", "uint256 newManagementFee"),
    _ev("vault", "SetManagementFeeRecipient", "address indexed newManagementFeeRecipient"),
    _ev(
        "vault",
        "DecreaseAbsoluteCap",
        "address indexed sender",
        "bytes32 indexed id",
        "bytes idData",
        "uint256 newAbsoluteCap",
    ),
    _ev("vault", "IncreaseAbsoluteCap", "bytes32 indexed id", "bytes idData", "uint256 newAbsoluteCap"),
    _ev(
        "vault",
        "DecreaseRelativeCap",
        "address indexed sender",
        "bytes32 indexed id",
        "bytes idData",
        "uint256 newRelativeCap",
    ),
    _ev("vault", "IncreaseRelativeCap", "bytes32 indexed id", "bytes idData", "uint256 newRelativeCap"),
    _ev("vault", "SetMaxRate", "uint256 newMaxRate"),
    _ev("vault", "SetForceDeallocatePenalty", "address indexed adapter", "uint256 forceDeallocatePenalty"),
    # standard admin events of the contracts a market depends on (D54): oracles, feeds, tokens
    _ev("admin", "Upgraded", "address indexed implementation"),
    _ev("admin", "AdminChanged", "address previousAdmin", "address newAdmin"),
    _ev("admin", "BeaconUpgraded", "address indexed beacon"),
    _ev("admin", "OwnershipTransferred", "address indexed previousOwner", "address indexed newOwner"),
    _ev("admin", "AggregatorProposed", "address indexed current", "address indexed proposed"),
    _ev("admin", "AggregatorConfirmed", "address indexed previous", "address indexed latest"),
    _ev("admin", "Paused", "address account"),
    _ev("admin", "Unpaused", "address account"),
    _ev("admin", "RoleGranted", "bytes32 indexed role", "address indexed account", "address indexed sender"),
    _ev("admin", "RoleRevoked", "bytes32 indexed role", "address indexed account", "address indexed sender"),
    _ev("admin", "Transfer", "address indexed from", "address indexed to", "uint256 value"),
    # OpenZeppelin TimelockController queue, on the timelocks that control a watched contract (D182)
    _ev(
        "admin",
        "CallScheduled",
        "bytes32 indexed id",
        "uint256 indexed index",
        "address target",
        "uint256 value",
        "bytes data",
        "bytes32 predecessor",
        "uint256 delay",
    ),
    _ev(
        "admin",
        "CallExecuted",
        "bytes32 indexed id",
        "uint256 indexed index",
        "address target",
        "uint256 value",
        "bytes data",
    ),
    _ev("admin", "Cancelled", "bytes32 indexed id"),
    # MorphoMarketV1AdapterV2 (Submit / Revoke / Accept / Abdicate / timelock events share
    # their signatures with the vault's and are told apart by the emitting address)
    _ev("adapter", "Allocate", "bytes32 indexed marketId", "uint256 newAllocation", "uint256 mintedShares"),
    _ev("adapter", "Deallocate", "bytes32 indexed marketId", "uint256 newAllocation", "uint256 burnedShares"),
    _ev("adapter", "BurnShares", "bytes32 indexed marketId", "uint256 supplyShares"),
    _ev("adapter", "SetSkimRecipient", "address indexed newSkimRecipient"),
    _ev("adapter", "Skim", "address indexed token", "uint256 assets"),
    # Zama Confidential Vault: batchers and confidential wrappers (plan 2026-10-11-zama-alerts, D190; ABI of the verified
    # RedeemVaultBatcherConfidential and the cShare implementation, read from Etherscan 2026-10-11)
    _ev("zama", "BatchFinalized", "uint256 indexed batchId", "uint64 exchangeRate"),
    _ev("zama", "BatchCanceled", "uint256 indexed batchId"),
    _ev("zama", "BatchDispatched", "uint256 indexed batchId"),
    _ev(
        "zama",
        "UnwrapFinalized",
        "address indexed receiver",
        "bytes32 indexed unwrapRequestId",
        "bytes32 encryptedAmount",
        "uint64 cleartextAmount",
    ),
    _ev("zama", "Paused", "address account"),
    _ev("zama", "Unpaused", "address account"),
    _ev("zama", "OwnershipTransferred", "address indexed previousOwner", "address indexed newOwner"),
    _ev("zama", "Upgraded", "address indexed implementation"),
    _ev("zama", "UserBlocked", "address indexed user"),
]

# topic0 -> specs; the same topic can exist on several contracts (Withdraw on Blue and on the
# vault have different signatures, so different topics; Submit is shared by vault and adapter).
BY_TOPIC: dict[str, list[EventSpec]] = {}
for _e in EVENTS:
    BY_TOPIC.setdefault(_e.topic0, []).append(_e)


@dataclass
class Event:
    name: str
    contract: str  # blue | vault | adapter
    address: str
    block: int
    tx: str
    log_index: int
    args: dict
    removed: bool = False


def decode_log(log: dict, kinds: dict[str, str]) -> Event | None:
    """`kinds` maps a lowercase address to 'blue' | 'vault' | 'adapter'. None if unknown."""
    addr = log["address"].lower()
    kind = kinds.get(addr)
    specs = [
        s
        for s in BY_TOPIC.get(log["topics"][0], [])
        if s.contract == kind or (kind == "adapter" and s.contract == "vault" and s.name in ADAPTER_SHARED)
    ]
    if not specs:
        return None
    spec = specs[0]
    indexed = [p for p in spec.params if p[2]]
    plain = [p for p in spec.params if not p[2]]
    args = {}
    for (name, typ, _), raw in zip(indexed, log["topics"][1:]):
        b = bytes.fromhex(raw[2:])
        if typ in ("bytes", "string") or typ.endswith("[]"):
            args[name] = "0x" + b.hex()  # indexed dynamic types are only their hash
        else:
            args[name] = decode([typ], b)[0]
    data = bytes.fromhex(log["data"][2:])
    if plain:
        for (name, _, _), val in zip(plain, decode([t for _, t, _ in plain], data)):
            args[name] = val
    for k, v in list(args.items()):
        if isinstance(v, bytes):
            args[k] = "0x" + v.hex()
        elif isinstance(v, tuple):
            args[k] = ["0x" + x.hex() if isinstance(x, bytes) else x for x in v]
        elif isinstance(v, str) and v.startswith("0x") and len(v) == 42:
            args[k] = v.lower()
    return Event(
        spec.name,
        spec.contract if spec.contract == kind else kind,
        addr,
        int(log["blockNumber"], 16),
        log["transactionHash"],
        int(log["logIndex"], 16),
        args,
        bool(log.get("removed", False)),
    )


ADAPTER_SHARED = {"Submit", "Revoke", "Accept", "Abdicate", "IncreaseTimelock", "DecreaseTimelock"}

# Timelocked functions (Submit / Accept data): selector -> (signature, what it changes for a depositor)
TIMELOCKED = {
    "setAdapterRegistry(address)": "the registry that decides which adapters are allowed",
    "abdicate(bytes4)": "a function is given up for good",
    "setReceiveSharesGate(address)": "who may receive vault shares (can block transfers to you)",
    "setSendSharesGate(address)": "who may send vault shares (can block your exit)",
    "setReceiveAssetsGate(address)": "who may receive assets on withdraw (can block your exit)",
    "setSendAssetsGate(address)": "who may deposit",
    "addAdapter(address)": "a new adapter: a new place your money can go",
    "removeAdapter(address)": "an adapter is removed",
    "increaseAbsoluteCap(bytes,uint256)": "more money may go to a market / collateral / adapter",
    "increaseRelativeCap(bytes,uint256)": "a larger share of the vault may go to a market / collateral / adapter",
    "setForceDeallocatePenalty(address,uint256)": "the penalty for forcing liquidity out of an adapter",
    "setIsAllocator(address,bool)": "who may move the money",
    "setPerformanceFee(uint256)": "the performance fee",
    "setManagementFee(uint256)": "the management fee",
    "setPerformanceFeeRecipient(address)": "who receives the performance fee",
    "setManagementFeeRecipient(address)": "who receives the management fee",
    "increaseTimelock(bytes4,uint256)": "a longer notice period",
    "decreaseTimelock(bytes4,uint256)": "a SHORTER notice period: less warning next time",
    # adapter-side
    "setSkimRecipient(address)": "who may skim stray tokens from the adapter",
    "burnShares(bytes32)": "the adapter writes off its supply shares in a market (a realised loss)",
}
SELECTORS = {selector(sig): (sig, what) for sig, what in TIMELOCKED.items()}


def describe_call(data_hex: str) -> tuple[str, list, str]:
    """Decode the calldata carried by Submit / Accept / Revoke: (signature, args, meaning)."""
    raw = bytes.fromhex(data_hex[2:] if data_hex.startswith("0x") else data_hex)
    sel = raw[:4].hex()
    if sel not in SELECTORS:
        return f"unknown 0x{sel}", [], "unknown timelocked call"
    sig, what = SELECTORS[sel]
    types = sig[sig.index("(") + 1 : -1].split(",") if not sig.endswith("()") else []
    try:
        vals = list(decode(types, raw[4:])) if types else []
    except Exception:
        vals = []
    vals = ["0x" + v.hex() if isinstance(v, bytes) else v for v in vals]
    return sig, vals, what


def encode_args(types: list[str], values: list) -> str:
    return encode(types, values).hex()


# D44: the timelocked functions whose zero timelock removes a depositor's warning
RISK_INCREASING_VAULT = [
    "addAdapter(address)",
    "increaseAbsoluteCap(bytes,uint256)",
    "increaseRelativeCap(bytes,uint256)",
    "setReceiveSharesGate(address)",
    "setSendSharesGate(address)",
    "setReceiveAssetsGate(address)",
    "setSendAssetsGate(address)",
    "setAdapterRegistry(address)",
    "setPerformanceFee(uint256)",
    "setManagementFee(uint256)",
    "setPerformanceFeeRecipient(address)",
    "setManagementFeeRecipient(address)",
    "setIsAllocator(address,bool)",
    "setForceDeallocatePenalty(address,uint256)",
]
RISK_INCREASING_ADAPTER = ["burnShares(bytes32)", "setSkimRecipient(address)"]
# read for display only: their delay is not a warning period (removeAdapter reduces risk; decreaseTimelock
# uses the timelock of the function it decreases)
OTHER_VAULT_TIMELOCKED = ["removeAdapter(address)", "abdicate(bytes4)", "increaseTimelock(bytes4,uint256)"]
