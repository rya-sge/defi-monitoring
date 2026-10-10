# Blue Public Allocator

> Source: https://docs.morpho.org/developers/contracts/blue-public-allocator

---

# Blue Public Allocator

[Vault v2 repository](https://github.com/morpho-org/vault-v2/tree/main/src/periphery/blue-public-allocator)

## [Introduction](#introduction)

The `BluePublicAllocator` lets anyone move Vault V2 assets between eligible Morpho Blue markets or allocate idle vault assets to an eligible market. The vault remains the owner of the assets throughout the operation. The caller only triggers the reallocation.

The vault's allocator role configures which adapters and markets can participate, whether idle assets can be used, the destination allocation caps, and the penalty. The penalty can be zero. If it is non-zero, the caller pays it in the vault's asset.

For a non-zero penalty, the caller first grants the `BluePublicAllocator` an allowance. During execution, the contract uses `transferFrom` to send the payment from the caller to the vault. The Public Allocator never holds the payment, and the vault does not mint shares for it. The payment increases the assets backing existing vault shares.

The `BluePublicAllocator` must be an allocator of the Vault V2. Each active adapter must be a `MorphoMarketV1AdapterV2` registered on that vault, and its immutable `parentVault` must be that vault. Using another adapter can break the Public Allocator cap system or cause the penalty to use an arbitrary token.

For the liquidity model and integration flow, see the [Public Allocator concept page](https://docs.morpho.org/learn/concepts/public-allocator/) and [Public Allocator tutorial](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/).

## [Allocation IDs and caps](#allocation-ids-and-caps)

The Public Allocator identifies an adapter and Morpho Blue market pair with this allocation ID:

```
keccak256(abi.encode("this/marketParams", adapter, marketParams))
```

`setAbsoluteCap` stores a Public Allocator cap for this ID. During `reallocate` and `allocateFromIdle`, the contract allocates the requested assets and then reads the vault's resulting allocation for the destination ID. The full transaction reverts if that allocation exceeds the configured Public Allocator cap.

The Public Allocator cap is an additional limit for calls through this contract. Vault V2 caps still apply. Direct allocations by other vault allocators and allocations caused by deposits do not use the Public Allocator cap.

## [Structs](#structs)

### [`VaultData`](#vaultdata)

```
struct VaultData {
    bool canPullFromIdle;
    uint64 penalty;
}
```

The contract stores one `VaultData` value for each Vault V2 address. Pass the vault address to `vaultData(vault)` to read the two fields below.

| Name | Type | Description |
| --- | --- | --- |
| `canPullFromIdle` | bool | Whether public calls can allocate the vault's idle assets. |
| `penalty` | uint64 | The WAD-scaled penalty paid by the caller. `0` means no penalty and `1e18` means 100%. |

## [Allocator functions](#allocator-functions)

### [`setIsActiveAdapter`](#setisactiveadapter)

```
function setIsActiveAdapter(address vault, address adapter, bool newIsActiveAdapter) external
```

Allows or prevents an adapter from participating in public reallocations for `vault`.

**Callable by:** An allocator of `vault`

#### [Parameters:](#parameters)

| Name | Type | Description |
| --- | --- | --- |
| `vault` | address | The Vault V2 to configure. |
| `adapter` | address | The `MorphoMarketV1AdapterV2` adapter to configure. |
| `newIsActiveAdapter` | bool | Whether the adapter can participate. |

---

### [`setAbsoluteCap`](#setabsolutecap)

```
function setAbsoluteCap(
    address vault,
    address adapter,
    MarketParams calldata marketParams,
    uint256 newAbsoluteCap
) external
```

Sets the maximum resulting vault allocation for an adapter and Morpho Blue market pair. Public allocations to this destination require a non-zero cap. After the allocation, the contract reads the vault's allocation for the destination ID and reverts the full transaction if it exceeds `newAbsoluteCap`.

**Callable by:** An allocator of `vault`

#### [Parameters:](#parameters-1)

| Name | Type | Description |
| --- | --- | --- |
| `vault` | address | The Vault V2 to configure. |
| `adapter` | address | The destination `MorphoMarketV1AdapterV2` adapter. |
| `marketParams` | MarketParams | The destination Morpho Blue market parameters. |
| `newAbsoluteCap` | uint256 | The maximum resulting allocation in vault asset units. Set to `0` to disable public allocations to this destination. |

---

### [`setCanPullFromMarket`](#setcanpullfrommarket)

```
function setCanPullFromMarket(
    address vault,
    address adapter,
    MarketParams calldata marketParams,
    bool newCanPullFromMarket
) external
```

Allows or prevents public reallocations from using an adapter and Morpho Blue market pair as a source.

**Callable by:** An allocator of `vault`

#### [Parameters:](#parameters-2)

| Name | Type | Description |
| --- | --- | --- |
| `vault` | address | The Vault V2 to configure. |
| `adapter` | address | The source `MorphoMarketV1AdapterV2` adapter. |
| `marketParams` | MarketParams | The source Morpho Blue market parameters. |
| `newCanPullFromMarket` | bool | Whether public reallocations can pull assets from this market. |

---

### [`setCanPullFromIdle`](#setcanpullfromidle)

```
function setCanPullFromIdle(address vault, bool newCanPullFromIdle) external
```

Allows or prevents public calls from allocating assets held idle by the vault.

**Callable by:** An allocator of `vault`

#### [Parameters:](#parameters-3)

| Name | Type | Description |
| --- | --- | --- |
| `vault` | address | The Vault V2 to configure. |
| `newCanPullFromIdle` | bool | Whether public calls can allocate idle assets. |

---

### [`setPenalty`](#setpenalty)

```
function setPenalty(address vault, uint64 newPenalty) external
```

Sets the optional penalty for `reallocate` and `allocateFromIdle`. The contract rounds the payment up with `MathLib.mulDivUp(assets, newPenalty, 1e18)`. It transfers a non-zero payment from the caller directly to the vault.

**Callable by:** An allocator of `vault`

#### [Parameters:](#parameters-4)

| Name | Type | Description |
| --- | --- | --- |
| `vault` | address | The Vault V2 to configure. |
| `newPenalty` | uint64 | The WAD-scaled penalty. Must be at most `1e18`. Set to `0` for no penalty. |

## [Public functions](#public-functions)

### [`reallocate`](#reallocate)

```
function reallocate(
    address vault,
    address deallocateAdapter,
    MarketParams calldata deallocateMarketParams,
    address allocateAdapter,
    MarketParams calldata allocateMarketParams,
    uint128 assets,
    uint64 penalty
) external
```

Moves `assets` from one eligible Morpho Blue market to another. The source and destination adapters must be active, and the source market must allow public withdrawals. The destination must have a non-zero Public Allocator cap. The resulting allocation must remain within both the Public Allocator cap and the Vault V2 caps.

The `penalty` argument must equal the current configured penalty. This check protects the caller from a penalty change between transaction signing and execution. If the configured penalty is non-zero, the caller must approve the `BluePublicAllocator` to spend the vault asset.

**Callable by:** Anyone

#### [Parameters:](#parameters-5)

| Name | Type | Description |
| --- | --- | --- |
| `vault` | address | The Vault V2 whose assets are reallocated. |
| `deallocateAdapter` | address | The active adapter that supplies the source market. |
| `deallocateMarketParams` | MarketParams | The source Morpho Blue market parameters. |
| `allocateAdapter` | address | The active adapter that supplies the destination market. |
| `allocateMarketParams` | MarketParams | The destination Morpho Blue market parameters. |
| `assets` | uint128 | The amount of vault assets to move. |
| `penalty` | uint64 | The expected WAD-scaled penalty. Must equal the configured value. |

---

### [`allocateFromIdle`](#allocatefromidle)

```
function allocateFromIdle(
    address vault,
    address adapter,
    MarketParams calldata marketParams,
    uint128 assets,
    uint64 penalty
) external
```

Moves `assets` from the vault's idle balance into an eligible Morpho Blue market. Pulling from idle must be enabled, the destination adapter must be active, and the destination must have a non-zero Public Allocator cap. The resulting allocation must remain within both the Public Allocator cap and the Vault V2 caps.

The `penalty` argument must equal the current configured penalty. If the configured penalty is non-zero, the caller must approve the `BluePublicAllocator` to spend the vault asset.

**Callable by:** Anyone

#### [Parameters:](#parameters-6)

| Name | Type | Description |
| --- | --- | --- |
| `vault` | address | The Vault V2 whose idle assets are allocated. |
| `adapter` | address | The active destination `MorphoMarketV1AdapterV2` adapter. |
| `marketParams` | MarketParams | The destination Morpho Blue market parameters. |
| `assets` | uint128 | The amount of idle vault assets to allocate. |
| `penalty` | uint64 | The expected WAD-scaled penalty. Must equal the configured value. |

A public allocation can revert if another transaction uses the source liquidity or destination cap first. Integrations should read fresh state before they build and submit the transaction.

## [Other functions](#other-functions)

### [`multicall`](#multicall)

```
function multicall(bytes[] calldata data) external
```

Executes multiple Public Allocator calls in one transaction with `delegatecall`. Each call keeps its own authorization and configuration checks. If one call reverts, the full multicall reverts with the same error.

**Callable by:** Anyone

#### [Parameters:](#parameters-7)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes[] | The ABI-encoded Public Allocator calls to execute. |

## [View functions](#view-functions)

### [`vaultV2Factory`](#vaultv2factory)

```
function vaultV2Factory() external view returns (address)
```

Returns the Vault V2 factory used to verify vaults in configuration calls.

#### [Return values:](#return-values)

| Name | Type | Description |
| --- | --- | --- |
| `vaultV2Factory` | address | The Vault V2 factory address. |

---

### [`absoluteCap`](#absolutecap)

```
function absoluteCap(address vault, bytes32 id) external view returns (uint256)
```

Returns the Public Allocator cap for a vault allocation ID.

#### [Parameters:](#parameters-8)

| Name | Type | Description |
| --- | --- | --- |
| `vault` | address | The Vault V2 to query. |
| `id` | bytes32 | The adapter and Morpho Blue market allocation ID. |

#### [Return values:](#return-values-1)

| Name | Type | Description |
| --- | --- | --- |
| `absoluteCap` | uint256 | The maximum resulting allocation for public calls. |

---

### [`canPullFromMarket`](#canpullfrommarket)

```
function canPullFromMarket(address vault, bytes32 id) external view returns (bool)
```

Returns whether public reallocations can pull assets from a vault allocation ID.

#### [Parameters:](#parameters-9)

| Name | Type | Description |
| --- | --- | --- |
| `vault` | address | The Vault V2 to query. |
| `id` | bytes32 | The adapter and Morpho Blue market allocation ID. |

#### [Return values:](#return-values-2)

| Name | Type | Description |
| --- | --- | --- |
| `canPullFromMarket` | bool | Whether public reallocations can use the market as a source. |

---

### [`isActiveAdapter`](#isactiveadapter)

```
function isActiveAdapter(address vault, address adapter) external view returns (bool)
```

Returns whether an adapter can participate in public allocations for a vault.

#### [Parameters:](#parameters-10)

| Name | Type | Description |
| --- | --- | --- |
| `vault` | address | The Vault V2 to query. |
| `adapter` | address | The adapter to query. |

#### [Return values:](#return-values-3)

| Name | Type | Description |
| --- | --- | --- |
| `isActiveAdapter` | bool | Whether the adapter is active. |

---

### [`vaultData`](#vaultdata-1)

```
function vaultData(address vault) external view returns (bool canPullFromIdle, uint64 penalty)
```

Returns the idle-allocation permission and configured penalty for a vault.

#### [Parameters:](#parameters-11)

| Name | Type | Description |
| --- | --- | --- |
| `vault` | address | The Vault V2 to query. |

#### [Return values:](#return-values-4)

| Name | Type | Description |
| --- | --- | --- |
| `canPullFromIdle` | bool | Whether public calls can allocate idle assets. |
| `penalty` | uint64 | The WAD-scaled penalty paid by public callers. |

## [Events](#events)

| Event | Description |
| --- | --- |
| `SetAbsoluteCap` | Emitted when a vault allocator changes a destination cap. |
| `SetCanPullFromMarket` | Emitted when a vault allocator changes a source-market permission. |
| `SetCanPullFromIdle` | Emitted when a vault allocator changes the idle-assets permission. |
| `SetIsActiveAdapter` | Emitted when a vault allocator activates or deactivates an adapter. |
| `SetPenalty` | Emitted when a vault allocator changes the penalty. |
| `Reallocate` | Emitted after assets move between two Morpho Blue markets. Includes the paid penalty assets. |
| `AllocateFromIdle` | Emitted after idle assets move into a Morpho Blue market. Includes the paid penalty assets. |

## [Errors](#errors)

| Error | Condition |
| --- | --- |
| `Unauthorized` | The caller of a configuration function is not an allocator of the vault. |
| `AbsoluteCapExceeded` | The destination allocation exceeds its Public Allocator cap. |
| `ZeroAbsoluteCap` | The destination has no Public Allocator cap. |
| `CannotPullFromMarket` | The source market does not allow public withdrawals. |
| `CannotPullFromIdle` | The vault does not allow public allocations from idle assets. |
| `InactiveAdapter` | A source or destination adapter is not active. |
| `PenaltyTooHigh` | The configured penalty is greater than `1e18`. |
| `IncorrectPenalty` | The caller's expected penalty does not equal the configured penalty. |
| `NotVaultV2` | A configuration call targets an address that the factory does not recognize as a Vault V2. |

[MorphoMarketV1AdapterV2

Previous Page

](https://docs.morpho.org/developers/contracts/morpho-market-v1-adapter-v2/)[Oracles

Next Page

](https://docs.morpho.org/developers/contracts/oracles/)