# MorphoMarketV1AdapterV2

> Source: https://docs.morpho.org/developers/contracts/morpho-market-v1-adapter-v2

---

# MorphoMarketV1AdapterV2

[Vault v2 repository](https://github.com/morpho-org/vault-v2)

## [Introduction](#introduction)

`MorphoMarketV1AdapterV2` is an adapter that connects a Morpho Vault V2 to a variable rate market. It manages supply positions across multiple markets and implements its own timelock system using the same submit/execute pattern as Morpho Vault V2, with its own distinct set of timelocked functions.

This adapter must be used with variable rate markets that are protected against inflation attacks with an initial supply. See [OpenZeppelin ERC4626 inflation attack](https://docs.openzeppelin.com/contracts/5.x/erc4626#inflation-attack) and Inflation Front-Running Attack Protection section [here](https://docs.morpho.org/curate/concepts/security-considerations/#inflation-front-running-attack-protection).

This adapter can only be used for markets with the AdaptiveCurveIRM.

Markets are removed from `marketIds` when the allocation is zero, but this does not mean that the adapter has zero shares on that market.

---

### [Function Selectors](#function-selectors)

#### [Timelocked Functions and Selectors](#timelocked-functions-and-selectors)

| Function Name | Selector |
| --- | --- |
| `increaseTimelock` | `0x47966291` |
| `decreaseTimelock` | `0x5c1a1a4f` |
| `abdicate` | `0xb2e32848` |
| `setSkimRecipient` | `0x2b30997b` |
| `burnShares` | `0x3b2de5ac` |

## [Immutables](#immutables)

| Name | Type | Description |
| --- | --- | --- |
| `factory` | address | The factory contract that deployed this adapter. |
| `parentVault` | address | The Morpho Vault V2 that this adapter belongs to. |
| `asset` | address | The underlying asset of the parent vault (must match the loan token of all managed markets). |
| `morpho` | address | The Morpho (Morpho Blue) contract address. |
| `adapterId` | bytes32 | Unique identifier for this adapter instance, computed as `keccak256(abi.encode("this", address(this)))`. |
| `adaptiveCurveIrm` | address | The AdaptiveCurveIRM address. All managed markets must use this IRM. |

## [Timelock System](#timelock-system)

The timelock system works identically to the one in Morpho Vault V2. The curator must `submit` a timelocked action, wait for the timelock to expire, then anyone can call the function directly.

---

### [`submit`](#submit)

```
function submit(bytes calldata data) external
```

Submits a timelocked action for later execution.

**Callable by:** `Curator`

#### [Parameters:](#parameters)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes | The ABI-encoded function call data. |

---

### [`revoke`](#revoke)

```
function revoke(bytes calldata data) external
```

Cancels a pending timelocked action.

**Callable by:** `Curator`, `Sentinel`

#### [Parameters:](#parameters-1)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes | The ABI-encoded function call data to revoke. |

---

### [`increaseTimelock`](#increasetimelock)

```
function increaseTimelock(bytes4 selector, uint256 newDuration) external
```

Increases the timelock duration for a specific function selector.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x47966291`

#### [Parameters:](#parameters-2)

| Name | Type | Description |
| --- | --- | --- |
| `selector` | bytes4 | The function selector whose timelock to increase. |
| `newDuration` | uint256 | The new timelock duration in seconds. Must be greater than or equal to the current duration. |

---

### [`decreaseTimelock`](#decreasetimelock)

```
function decreaseTimelock(bytes4 selector, uint256 newDuration) external
```

Decreases the timelock duration for a specific function selector. This action's own timelock equals the current timelock of the function being decreased.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x5c1a1a4f`

#### [Parameters:](#parameters-3)

| Name | Type | Description |
| --- | --- | --- |
| `selector` | bytes4 | The function selector whose timelock to decrease. |
| `newDuration` | uint256 | The new timelock duration in seconds. Must be less than or equal to the current duration. |

---

### [`abdicate`](#abdicate)

```
function abdicate(bytes4 selector) external
```

Irreversibly disables the ability to execute a specific type of action.

This action is irreversible. Existing pending operations submitted before abdicating cannot be executed.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0xb2e32848`

#### [Parameters:](#parameters-4)

| Name | Type | Description |
| --- | --- | --- |
| `selector` | bytes4 | The function selector to permanently abdicate. |

## [Curator Functions](#curator-functions)

### [`setSkimRecipient`](#setskimrecipient)

```
function setSkimRecipient(address newSkimRecipient) external
```

Sets the address that receives skimmed token balances (e.g., reward tokens earned by the adapter).

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x2b30997b`

#### [Parameters:](#parameters-5)

| Name | Type | Description |
| --- | --- | --- |
| `newSkimRecipient` | address | The new skim recipient address. |

---

### [`burnShares`](#burnshares)

```
function burnShares(bytes32 marketId) external
```

Burns the adapter's tracked supply shares for a market, setting `supplyShares[marketId]` to zero.

Burnt shares are lost forever and cannot be recovered.

When submitting `burnShares`, it is recommended to set the caps of the market to zero first to avoid losing more assets.

After burning shares, call `deallocate` on the parent vault with this adapter's address, the market's data encoding, and `0` assets to sync the vault's recorded allocation.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x3b2de5ac`

#### [Parameters:](#parameters-6)

| Name | Type | Description |
| --- | --- | --- |
| `marketId` | bytes32 | The market ID whose shares to burn. |

## [Other Functions](#other-functions)

### [`skim`](#skim)

```
function skim(address token) external
```

Transfers the adapter's entire balance of `token` to `skimRecipient`.

**Callable by:** `skimRecipient`

If `skimRecipient` is not set (`address(0)`), this function will always revert.

#### [Parameters:](#parameters-7)

| Name | Type | Description |
| --- | --- | --- |
| `token` | address | The token to skim. |

---

### [`allocate`](#allocate)

```
function allocate(bytes memory data, uint256 assets, bytes4, address) external returns (bytes32[] memory, int256)
```

Supplies `assets` into the specified variable rate market.

**Callable by:** `parentVault`

#### [Parameters:](#parameters-8)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes | ABI-encoded `MarketParams` struct identifying the target market. |
| `assets` | uint256 | The amount of assets to supply. |

The `bytes4` and `address` parameters are part of the shared adapter interface but unused by this implementation.

#### [Return Values:](#return-values)

| Name | Type | Description |
| --- | --- | --- |
| `ids` | bytes32[] | The allocation IDs affected by this operation. |
| `delta` | int256 | The change in allocation (new allocation minus old allocation). Positive for `allocate`, negative for `deallocate`. |

---

### [`deallocate`](#deallocate)

```
function deallocate(bytes memory data, uint256 assets, bytes4, address) external returns (bytes32[] memory, int256)
```

Withdraws `assets` from the specified variable rate market back to the parent vault.

**Callable by:** `parentVault`

#### [Parameters:](#parameters-9)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes | ABI-encoded `MarketParams` struct identifying the target market. |
| `assets` | uint256 | The amount of assets to withdraw. |

The `bytes4` and `address` parameters are part of the shared adapter interface but unused by this implementation.

#### [Return Values:](#return-values-1)

| Name | Type | Description |
| --- | --- | --- |
| `ids` | bytes32[] | The allocation IDs affected by this operation. |
| `delta` | int256 | The change in allocation (new allocation minus old allocation). Positive for `allocate`, negative for `deallocate`. |

## [View Functions](#view-functions)

### [`realAssets`](#realassets)

```
function realAssets() external view returns (uint256)
```

Returns the total expected supply assets across all managed markets, used by the parent vault during interest accrual.

#### [Return Values:](#return-values-2)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The total assets across all markets in `marketIds`. |

---

### [`expectedSupplyAssets`](#expectedsupplyassets)

```
function expectedSupplyAssets(bytes32 marketId) public view returns (uint256)
```

Returns the expected supply assets for a specific market, accounting for the adapter's internal share balance.

#### [Parameters:](#parameters-10)

| Name | Type | Description |
| --- | --- | --- |
| `marketId` | bytes32 | The market ID to query. |

#### [Return Values:](#return-values-3)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The expected supply assets for the given market. |

---

### [`allocation`](#allocation)

```
function allocation(MarketParams memory marketParams) public view returns (uint256)
```

Returns the vault's current allocation for this market, as recorded in the parent vault.

#### [Parameters:](#parameters-11)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | MarketParams | The market parameters struct. |

#### [Return Values:](#return-values-4)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The current allocation amount in the parent vault. |

---

### [`ids`](#ids)

```
function ids(MarketParams memory marketParams) public view returns (bytes32[] memory)
```

Returns the three allocation IDs used by this adapter for a given market.

#### [Parameters:](#parameters-12)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | MarketParams | The market parameters struct. |

#### [Return Values:](#return-values-5)

| Name | Type | Description |
| --- | --- | --- |
| `ids_` | bytes32[] | Array of 3 IDs: `adapterId`, `keccak256(abi.encode("collateralToken", collateralToken))`, and `keccak256(abi.encode("this/marketParams", address(this), marketParams))`. |

---

### [`marketIdsLength`](#marketidslength)

```
function marketIdsLength() external view returns (uint256)
```

Returns the number of markets currently tracked by this adapter. Use this as the upper bound when iterating over [`marketIds`](#marketids).

#### [Return Values:](#return-values-6)

| Name | Type | Description |
| --- | --- | --- |
| `length` | uint256 | The number of market IDs in `marketIds`. |

---

### [`marketIds`](#marketids)

```
bytes32[] public marketIds
```

Returns the market ID at the given position in the list of markets with non-zero allocation currently managed by this adapter.

#### [Parameters:](#parameters-13)

| Name | Type | Description |
| --- | --- | --- |
| `index` | uint256 | The position in the array. Must be less than [`marketIdsLength()`](#marketidslength). |

#### [Return Values:](#return-values-7)

| Name | Type | Description |
| --- | --- | --- |
| `marketId` | bytes32 | The market ID at the given index. |

---

### [`timelock`](#timelock)

```
mapping(bytes4 selector => uint256) public timelock
```

Returns the timelock duration (in seconds) for a given function selector.

#### [Parameters:](#parameters-14)

| Name | Type | Description |
| --- | --- | --- |
| `selector` | bytes4 | The function selector to query. |

#### [Return Values:](#return-values-8)

| Name | Type | Description |
| --- | --- | --- |
| `duration` | uint256 | The timelock duration in seconds for the given selector. |

---

### [`abdicated`](#abdicated)

```
mapping(bytes4 selector => bool) public abdicated
```

Returns whether the curator has permanently abdicated the ability to execute a specific action.

#### [Parameters:](#parameters-15)

| Name | Type | Description |
| --- | --- | --- |
| `selector` | bytes4 | The function selector to query. |

#### [Return Values:](#return-values-9)

| Name | Type | Description |
| --- | --- | --- |
| `isAbdicated` | bool | `true` if the curator has abdicated the given selector, `false` otherwise. |

---

### [`executableAt`](#executableat)

```
function executableAt(bytes memory data) external view returns (uint256)
```

Returns the Unix timestamp (seconds) at which a submitted timelocked action becomes executable.

#### [Parameters:](#parameters-16)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes | The ABI-encoded function call data of the pending action. |

#### [Return Values:](#return-values-10)

| Value | Meaning |
| --- | --- |
| `0` | No pending action (never submitted, already executed, or revoked) |
| `<= block.timestamp` | Action is currently executable (timelock has elapsed) |
| `> block.timestamp` | Not yet executable - equals `submissionTimestamp + timelock[selector]` |

---

### [`supplyShares`](#supplyshares)

```
mapping(bytes32 marketId => uint256) public supplyShares
```

Returns the adapter's tracked supply shares for a given market.

#### [Parameters:](#parameters-17)

| Name | Type | Description |
| --- | --- | --- |
| `marketId` | bytes32 | The market ID to query. |

#### [Return Values:](#return-values-11)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The adapter's tracked supply shares for the given market. |

---

### [`skimRecipient`](#skimrecipient)

```
address public skimRecipient
```

Returns the address that receives skimmed token balances.

---

[Morpho Vaults V2

Previous Page

](https://docs.morpho.org/developers/contracts/morpho-vaults-v2/)[Blue Public Allocator

Next Page

](https://docs.morpho.org/developers/contracts/blue-public-allocator/)