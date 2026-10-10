# Morpho Vaults V2

> Source: https://docs.morpho.org/developers/contracts/morpho-vaults-v2

---

# Morpho Vaults V2

[Vault v2 repository](https://github.com/morpho-org/vault-v2)

## [Introduction to principles](#introduction-to-principles)

By design, Morpho Vault V2 has a non-conventional behaviour on max functions (`maxDeposit`, `maxMint`, `maxWithdraw`, `maxRedeem`): they always return zero. To compute deposit and withdrawal limits, see [Compute deposit and withdrawal limits](https://docs.morpho.org/developers/earn/tutorials/assets-flow/#compute-deposit-and-withdrawal-limits).

### [Caps structure](#caps-structure)

```
struct Caps {
    uint256 allocation;
    uint128 absoluteCap;
    uint128 relativeCap;
}
```

| Name | Type | Description |
| --- | --- | --- |
| `allocation` | uint256 | The current amount of assets allocated to this `id`. |
| `absoluteCap` | uint128 | The maximum amount of assets that can be allocated to this `id`. |
| `relativeCap` | uint128 | The maximum percentage of total assets that can be allocated to this `id`, scaled by 1e18. |

---

### [`id`, `idData`, and `data`](#id-iddata-and-data)

Allocation targets are identified by an `id` computed as `keccak256(idData)`, where `idData` is adapter-defined bytes. When allocating or setting caps, you pass the raw `data` bytes. When querying allocations or caps, you must compute and pass the `id` hash. The vault does not provide a helper function to compute `id` - you must calculate it off-chain or in your contract. Refer to each adapter's documentation for the exact `data` encoding and the list of `id`s it registers.

Throughout the vault contract, you'll encounter three related concepts for identifying allocation targets:

#### [`data` / `idData`](#data--iddata)

- **Raw bytes**: Protocol-specific data that identifies where assets are allocated
- **Encoding varies by adapter**: Each adapter defines what `data` encodes and how many `id`s it registers per allocation (an adapter may register multiple ids, e.g. for per-collateral or per-market caps). Refer to the adapter's documentation for the exact encoding.

#### [`id`](#id)

- **Computed hash**: `id = keccak256(idData)`
- **Purpose**: Used as the unique key in the vault's storage mappings to track allocations and caps
- **Type**: `bytes32`

#### [Function usage patterns](#function-usage-patterns)

- **Setting caps**: Functions like `increaseAbsoluteCap` take `idData` (raw bytes) as input
- **Allocating**: Functions like `allocate` take `data` (raw bytes) as input
- **Querying**: Functions like `allocation`, `absoluteCap`, `relativeCap` take `id` (keccak256 hash) as input

This design allows the vault to work with any adapter and allocation target, as long as they can be identified by bytes-encoded data.

---

### [Function Selectors](#function-selectors)

A **function selector** is a `bytes4` value that uniquely identifies a function in a smart contract. It's the first 4 bytes of the `keccak256` hash of the function's signature.

**What are they used for in the vault?** Selectors are used for timelock management. The curator can configure different timelock durations for different functions, or permanently abdicate the ability to call specific functions. Functions like `timelock(bytes4 selector)`, `abdicated(bytes4 selector)`, `increaseTimelock(bytes4 selector, ...)`, and `decreaseTimelock(bytes4 selector, ...)` use selectors to identify which function's settings to modify.

**Important notes:**

- The function signature must include parameter types but not parameter names or return types
- Example: `"setPerformanceFee(uint256)"` not `"setPerformanceFee(uint256 newFee)"`
- Selectors are always exactly 4 bytes (shown as 10 characters in hex: `0x` + 8 hex digits)

#### [Timelocked Functions and Selectors](#timelocked-functions-and-selectors)

| Function Name | Selector |
| --- | --- |
| `setAdapterRegistry` | `0x5b34b823` |
| `abdicate` | `0xb2e32848` |
| `setReceiveSharesGate` | `0x2cb19f98` |
| `setSendSharesGate` | `0xc21ad028` |
| `setReceiveAssetsGate` | `0x04dbf0ce` |
| `addAdapter` | `0x60d54d41` |
| `increaseAbsoluteCap` | `0xf6f98fd5` |
| `increaseRelativeCap` | `0x2438525b` |
| `setForceDeallocatePenalty` | `0x3e9d2ac7` |
| `setIsAllocator` | `0xb192a84a` |
| `setSendAssetsGate` | `0x871c979c` |
| `setPerformanceFee` | `0x70897b23` |
| `setManagementFee` | `0xfe56e232` |
| `setPerformanceFeeRecipient` | `0x6a5f1aa2` |
| `setManagementFeeRecipient` | `0x9faae464` |
| `removeAdapter` | `0x585cd34b` |
| `increaseTimelock` | `0x47966291` |
| `decreaseTimelock` | `0x5c1a1a4f` |

## [External Functions](#external-functions)

### [`deposit`](#deposit)

```
function deposit(uint256 assets, address onBehalf) external returns (uint256)
```

Deposits `assets` of the underlying token to mint vault shares for `onBehalf`.

**Callable by:** Anyone

#### [Parameters:](#parameters)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The amount of the underlying asset to deposit. |
| `onBehalf` | address | The recipient of the minted vault shares. |

#### [Return Values:](#return-values)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The amount of vault shares minted. |

---

### [`mint`](#mint)

```
function mint(uint256 shares, address onBehalf) external returns (uint256)
```

Mints exactly `shares` vault shares for `onBehalf` by depositing the required amount of the underlying token.

**Callable by:** Anyone

#### [Parameters:](#parameters-1)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The exact amount of shares to mint. |
| `onBehalf` | address | The recipient of the minted vault shares. |

#### [Return Values:](#return-values-1)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The amount of the underlying asset deposited. |

---

### [`withdraw`](#withdraw)

```
function withdraw(uint256 assets, address receiver, address onBehalf) public returns (uint256)
```

Withdraws `assets` of the underlying token by burning shares from `onBehalf` and sends them to `receiver`.

**Callable by:** `onBehalf` or approved address

#### [Parameters:](#parameters-2)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The amount of the underlying asset to withdraw. |
| `receiver` | address | The recipient of the withdrawn assets. |
| `onBehalf` | address | The owner of the shares to be burned. `msg.sender` must be approved. |

#### [Return Values:](#return-values-2)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The amount of vault shares burned. |

---

### [`redeem`](#redeem)

```
function redeem(uint256 shares, address receiver, address onBehalf) external returns (uint256)
```

Burns exactly `shares` vault shares from `onBehalf` and sends the corresponding amount of underlying assets to `receiver`.

**Callable by:** `onBehalf` or approved address

#### [Parameters:](#parameters-3)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The exact amount of shares to burn. |
| `receiver` | address | The recipient of the withdrawn assets. |
| `onBehalf` | address | The owner of the shares to be burned. `msg.sender` must be approved. |

#### [Return Values:](#return-values-3)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The amount of the underlying asset withdrawn. |

---

### [`forceDeallocate`](#forcedeallocate)

```
function forceDeallocate(address adapter, bytes memory data, uint256 assets, address onBehalf) external returns (uint256)
```

Moves `assets` from the selected `adapter` back to the vault's idle balance. The caller does not provide or receive those assets.

If a penalty is configured, the vault burns the corresponding value of vault shares from `onBehalf`. The penalty is denominated in the vault's underlying asset, and the underlying assets remain in the vault. They are not paid to the caller, curator, or an external fee recipient.

This permissionless function can be used as part of an in-kind redemption.

**Callable by:** Anyone

With a `forceDeallocatePenalty` of 0, no shares are burned. Anyone can then move available assets from the adapter into the vault's idle balance, provided the `onBehalf` account is permitted by the share-sending gate. This does not transfer assets to the caller, but it can make vault assets idle at times unintended by the curator.

#### [Parameters:](#parameters-4)

| Name | Type | Description |
| --- | --- | --- |
| `adapter` | address | The adapter to deallocate from. |
| `data` | bytes | The protocol-specific data for the deallocation. |
| `assets` | uint256 | The amount of the underlying asset moved from the adapter to the vault's idle balance. |
| `onBehalf` | address | The account whose vault shares pay the penalty. If the caller acts for another account, sufficient vault-share allowance is required. |

#### [Return Values:](#return-values-4)

| Name | Type | Description |
| --- | --- | --- |
| `withdrawnShares` | uint256 | The amount of vault shares burned from `onBehalf` to pay the penalty. |

---

### [`accrueInterest`](#accrueinterest)

```
function accrueInterest() public
```

Accrues interest for the vault by querying adapters for their current assets and updating `totalAssets`. This function is called by most state-changing functions.

**Callable by:** Anyone

---

### [`accrueInterestView`](#accrueinterestview)

```
function accrueInterestView() public view returns (uint256, uint256, uint256)
```

Returns the view version of interest accrual without updating state.

#### [Return Values:](#return-values-5)

| Name | Type | Description |
| --- | --- | --- |
| `newTotalAssets` | uint256 | The updated total assets after interest accrual. |
| `performanceFeeShares` | uint256 | The amount of shares that would be minted as performance fee. |
| `managementFeeShares` | uint256 | The amount of shares that would be minted as management fee. |

---

### [`previewDeposit`](#previewdeposit)

```
function previewDeposit(uint256 assets) public view returns (uint256)
```

Returns previewed minted shares for a given asset amount.

#### [Parameters:](#parameters-5)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The amount of assets to preview deposit for. |

#### [Return Values:](#return-values-6)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The amount of shares that would be minted. |

---

### [`previewMint`](#previewmint)

```
function previewMint(uint256 shares) public view returns (uint256)
```

Returns previewed deposited assets for a given share amount.

#### [Parameters:](#parameters-6)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The amount of shares to preview mint for. |

#### [Return Values:](#return-values-7)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The amount of assets that would be deposited. |

---

### [`previewWithdraw`](#previewwithdraw)

```
function previewWithdraw(uint256 assets) public view returns (uint256)
```

Returns previewed redeemed shares for a given asset amount.

#### [Parameters:](#parameters-7)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The amount of assets to preview withdrawal for. |

#### [Return Values:](#return-values-8)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The amount of shares that would be burned. |

---

### [`previewRedeem`](#previewredeem)

```
function previewRedeem(uint256 shares) public view returns (uint256)
```

Returns previewed withdrawn assets for a given share amount.

#### [Parameters:](#parameters-8)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The amount of shares to preview redemption for. |

#### [Return Values:](#return-values-9)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The amount of assets that would be withdrawn. |

---

### [`convertToShares`](#converttoshares)

```
function convertToShares(uint256 assets) external view returns (uint256)
```

Returns corresponding shares (rounded down) for a given asset amount. Takes into account performance and management fees.

#### [Parameters:](#parameters-9)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The amount of assets to convert. |

#### [Return Values:](#return-values-10)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The corresponding amount of shares. |

---

### [`convertToAssets`](#converttoassets)

```
function convertToAssets(uint256 shares) external view returns (uint256)
```

Returns corresponding assets (rounded down) for a given share amount. Takes into account performance and management fees.

#### [Parameters:](#parameters-10)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The amount of shares to convert. |

#### [Return Values:](#return-values-11)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The corresponding amount of assets. |

---

### [`maxDeposit`](#maxdeposit)

```
function maxDeposit(address) external pure returns (uint256)
```

Returns the maximum amount of assets that can be deposited.

Always returns 0 as a conservative underestimate. Morpho Vault V2 can use external gate contracts for access control; because gate behavior cannot be guaranteed to be revert-free, computing a reliable maximum is not possible.

---

### [`maxMint`](#maxmint)

```
function maxMint(address) external pure returns (uint256)
```

Returns the maximum amount of shares that can be minted.

Always returns 0 as a conservative underestimate. Morpho Vault V2 can use external gate contracts for access control; because gate behavior cannot be guaranteed to be revert-free, computing a reliable maximum is not possible.

---

### [`maxWithdraw`](#maxwithdraw)

```
function maxWithdraw(address) external pure returns (uint256)
```

Returns the maximum amount of assets that can be withdrawn.

Always returns 0 as a conservative underestimate. Morpho Vault V2 can use external gate contracts for access control; because gate behavior cannot be guaranteed to be revert-free, computing a reliable maximum is not possible.

---

### [`maxRedeem`](#maxredeem)

```
function maxRedeem(address) external pure returns (uint256)
```

Returns the maximum amount of shares that can be redeemed.

Always returns 0 as a conservative underestimate. Morpho Vault V2 can use external gate contracts for access control; because gate behavior cannot be guaranteed to be revert-free, computing a reliable maximum is not possible.

---

### [`multicall`](#multicall)

```
function multicall(bytes[] calldata data) external
```

Useful for EOAs to batch admin calls. Does not return anything, because accounts who would use the return data would be contracts, which can do the multicall themselves.

**Callable by:** Anyone

#### [Parameters:](#parameters-11)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes[] | Array of encoded function calls to execute. |

---

As a reminder, there are four distinct [roles](https://docs.morpho.org/curate/concepts/roles/#morpho-vaults-v2-roles) in Morpho Vaults V2:

1. **Owner**: Manages role assignments.
2. **Curator**: The chief risk curator and strategist.
3. **Allocator**: The active portfolio curator.
4. **Sentinel**: A safety-oriented role for reactive risk mitigation.

## [Owner Functions](#owner-functions)

---

### [`setOwner`](#setowner)

```
function setOwner(address newOwner) external
```

Transfers ownership of the vault to `newOwner`.

**Callable by:** `Owner`

---

### [`setCurator`](#setcurator)

```
function setCurator(address newCurator) external
```

Sets the vault's `Curator`.

**Callable by:** `Owner`

---

### [`setIsSentinel`](#setissentinel)

```
function setIsSentinel(address account, bool newIsSentinel) external
```

Grants or revokes the `Sentinel` role for an `account`.

**Callable by:** `Owner`

---

### [`setName`](#setname)

```
function setName(string memory newName) external
```

Sets the vault's name.

**Callable by:** `Owner`

---

### [`setSymbol`](#setsymbol)

```
function setSymbol(string memory newSymbol) external
```

Sets the vault's symbol.

**Callable by:** `Owner`

## [Curator Functions](#curator-functions)

The following functions are only callable by the `Curator`. Some are subject to a **timelock** while others are **instant**. The timelock process is:

1. `Curator` calls `submit(bytes calldata data)` with the ABI-encoded function call.
2. After the timelock expires, anyone can execute the function directly.

---

### [`abdicate`](#abdicate)

```
function abdicate(bytes4 selector) external
```

Irreversibly disables the ability to execute a specific type of action.

This action is irreversible. Existing pending operations submitted before abdicating cannot be executed.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0xb2e32848`

#### [Parameters:](#parameters-12)

| Name | Type | Description |
| --- | --- | --- |
| `selector` | bytes4 | The function selector to abdicate. |

---

### [`addAdapter`](#addadapter)

```
function addAdapter(address account) external
```

Adds a new adapter to the vault.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x60d54d41`

#### [Parameters:](#parameters-13)

| Name | Type | Description |
| --- | --- | --- |
| `account` | address | The adapter address to add. |

---

### [`decreaseAbsoluteCap`](#decreaseabsolutecap)

```
function decreaseAbsoluteCap(bytes memory idData, uint256 newAbsoluteCap) external
```

Decreases the absolute cap for an allocation target. The `id` is computed as `keccak256(idData)` where `idData` is the market-specific data identifying the allocation target.

**Callable by:** `Curator`, `Sentinel`

#### [Parameters:](#parameters-14)

| Name | Type | Description |
| --- | --- | --- |
| `idData` | bytes | Market-specific data identifying the allocation target (e.g., market ID for Morpho markets). The hash of this data (`keccak256(idData)`) is used as the unique identifier. |
| `newAbsoluteCap` | uint256 | The new absolute cap value. |

---

### [`decreaseRelativeCap`](#decreaserelativecap)

```
function decreaseRelativeCap(bytes memory idData, uint256 newRelativeCap) external
```

Decreases the relative cap for an allocation target. The `id` is computed as `keccak256(idData)` where `idData` is the market-specific data identifying the allocation target.

**Callable by:** `Curator`, `Sentinel`

#### [Parameters:](#parameters-15)

| Name | Type | Description |
| --- | --- | --- |
| `idData` | bytes | Market-specific data identifying the allocation target (e.g., market ID for Morpho markets). The hash of this data (`keccak256(idData)`) is used as the unique identifier. |
| `newRelativeCap` | uint256 | The new relative cap value (scaled by 1e18). |

---

### [`decreaseTimelock`](#decreasetimelock)

```
function decreaseTimelock(bytes4 selector, uint256 newDuration) external
```

Decreases a function's timelock duration. This action's timelock equals the current timelock of the function being decreased.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x5c1a1a4f`

#### [Parameters:](#parameters-16)

| Name | Type | Description |
| --- | --- | --- |
| `selector` | bytes4 | The function selector. |
| `newDuration` | uint256 | The new timelock duration. |

---

### [`increaseAbsoluteCap`](#increaseabsolutecap)

```
function increaseAbsoluteCap(bytes memory idData, uint256 newAbsoluteCap) external
```

Increases the absolute cap for an allocation target. The `id` is computed as `keccak256(idData)` where `idData` is the market-specific data identifying the allocation target.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0xf6f98fd5`

#### [Parameters:](#parameters-17)

| Name | Type | Description |
| --- | --- | --- |
| `idData` | bytes | Market-specific data identifying the allocation target (e.g., market ID for Morpho markets). The hash of this data (`keccak256(idData)`) is used as the unique identifier. |
| `newAbsoluteCap` | uint256 | The new absolute cap value. |

---

### [`increaseRelativeCap`](#increaserelativecap)

```
function increaseRelativeCap(bytes memory idData, uint256 newRelativeCap) external
```

Increases the relative cap for an allocation target. The `id` is computed as `keccak256(idData)` where `idData` is the market-specific data identifying the allocation target.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x2438525b`

#### [Parameters:](#parameters-18)

| Name | Type | Description |
| --- | --- | --- |
| `idData` | bytes | Market-specific data identifying the allocation target (e.g., market ID for Morpho markets). The hash of this data (`keccak256(idData)`) is used as the unique identifier. |
| `newRelativeCap` | uint256 | The new relative cap value (scaled by 1e18). |

---

### [`increaseTimelock`](#increasetimelock)

```
function increaseTimelock(bytes4 selector, uint256 newDuration) external
```

Increases a function's timelock duration.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x47966291`

#### [Parameters:](#parameters-19)

| Name | Type | Description |
| --- | --- | --- |
| `selector` | bytes4 | The function selector. |
| `newDuration` | uint256 | The new timelock duration. |

---

### [`removeAdapter`](#removeadapter)

```
function removeAdapter(address account) external
```

Removes an adapter from the vault.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x585cd34b`

#### [Parameters:](#parameters-20)

| Name | Type | Description |
| --- | --- | --- |
| `account` | address | The adapter address to remove. |

---

### [`revoke`](#revoke)

```
function revoke(bytes calldata data) external
```

Revokes a pending timelocked action.

**Callable by:** `Curator`, `Sentinel`

#### [Parameters:](#parameters-21)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes | The ABI-encoded function call data to revoke. |

---

### [`setAdapterRegistry`](#setadapterregistry)

```
function setAdapterRegistry(address newAdapterRegistry) external
```

Sets the adapter registry contract. The function validates that the new registry approves all currently added adapters.
If the new registry returns false for any existing adapter, the transaction will revert.
This ensures that changing the registry doesn't invalidate adapters that are already in use.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x5b34b823`

#### [Parameters:](#parameters-22)

| Name | Type | Description |
| --- | --- | --- |
| `newAdapterRegistry` | address | The new adapter registry contract. |

---

### [`setForceDeallocatePenalty`](#setforcedeallocatepenalty)

```
function setForceDeallocatePenalty(address adapter, uint256 newForceDeallocatePenalty) external
```

Sets the penalty for using [`forceDeallocate`](https://docs.morpho.org/get-started/resources/contracts/morpho-vaults-v2/#forcedeallocate) on a specific adapter. The value is a fraction scaled by `1e18` and cannot exceed 2% (`0.02e18`).

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x3e9d2ac7`

#### [Parameters:](#parameters-23)

| Name | Type | Description |
| --- | --- | --- |
| `adapter` | address | The adapter to set penalty for. |
| `newForceDeallocatePenalty` | uint256 | The new penalty value, scaled by `1e18` and capped at 2% (`0.02e18`). |

---

### [`setIsAllocator`](#setisallocator)

```
function setIsAllocator(address account, bool newIsAllocator) external
```

Grants or revokes the `Allocator` role for an account.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0xb192a84a`

#### [Parameters:](#parameters-24)

| Name | Type | Description |
| --- | --- | --- |
| `account` | address | The account to modify. |
| `newIsAllocator` | bool | Whether the account should be an allocator. |

---

### [`setManagementFee`](#setmanagementfee)

```
function setManagementFee(uint256 newManagementFee) external
```

Sets the vault's management fee.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0xfe56e232`

#### [Parameters:](#parameters-25)

| Name | Type | Description |
| --- | --- | --- |
| `newManagementFee` | uint256 | The new management fee (scaled by 1e18). |

---

### [`setManagementFeeRecipient`](#setmanagementfeerecipient)

```
function setManagementFeeRecipient(address newManagementFeeRecipient) external
```

Sets the management fee recipient.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x9faae464`

#### [Parameters:](#parameters-26)

| Name | Type | Description |
| --- | --- | --- |
| `newManagementFeeRecipient` | address | The new management fee recipient. |

Fees are minted as shares. To receive the underlying asset, the fee recipient must call `redeem()` at some point, either directly, or by granting allowance to another address that redeems on their behalf. **The fee recipient must be an address capable of interacting with the vault** (EOA, smart wallet, multisig, etc.). A fully passive address that never interacts with the chain won't be able to actually receive the fee in the underlying asset.

---

### [`setPerformanceFee`](#setperformancefee)

```
function setPerformanceFee(uint256 newPerformanceFee) external
```

Sets the vault's performance fee.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x70897b23`

#### [Parameters:](#parameters-27)

| Name | Type | Description |
| --- | --- | --- |
| `newPerformanceFee` | uint256 | The new performance fee (scaled by 1e18). |

---

### [`setPerformanceFeeRecipient`](#setperformancefeerecipient)

```
function setPerformanceFeeRecipient(address newPerformanceFeeRecipient) external
```

Sets the performance fee recipient.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x6a5f1aa2`

#### [Parameters:](#parameters-28)

| Name | Type | Description |
| --- | --- | --- |
| `newPerformanceFeeRecipient` | address | The new performance fee recipient. |

Fees are minted as shares. To receive the underlying asset, the fee recipient must call `redeem()` at some point, either directly, or by granting allowance to another address that redeems on their behalf. **The fee recipient must be an address capable of interacting with the vault** (EOA, smart wallet, multisig, etc.). A fully passive address that never interacts with the chain won't be able to actually receive the fee in the underlying asset.

---

### [`setReceiveAssetsGate`](#setreceiveassetsgate)

```
function setReceiveAssetsGate(address newReceiveAssetsGate) external
```

Sets the contract for gating asset receipts.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x04dbf0ce`

#### [Parameters:](#parameters-29)

| Name | Type | Description |
| --- | --- | --- |
| `newReceiveAssetsGate` | address | The new receive assets gate contract. |

---

### [`setReceiveSharesGate`](#setreceivesharesgate)

```
function setReceiveSharesGate(address newReceiveSharesGate) external
```

Sets the contract for gating share receipts.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x2cb19f98`

#### [Parameters:](#parameters-30)

| Name | Type | Description |
| --- | --- | --- |
| `newReceiveSharesGate` | address | The new receive shares gate contract. |

---

### [`setSendAssetsGate`](#setsendassetsgate)

```
function setSendAssetsGate(address newSendAssetsGate) external
```

Sets the contract for gating asset sends.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0x871c979c`

#### [Parameters:](#parameters-31)

| Name | Type | Description |
| --- | --- | --- |
| `newSendAssetsGate` | address | The new send assets gate contract. |

---

### [`setSendSharesGate`](#setsendsharesgate)

```
function setSendSharesGate(address newSendSharesGate) external
```

Sets the contract for gating share sends.

**Callable by:** `Curator` (timelocked - submit first, then anyone can execute after delay)

Selector: `0xc21ad028`

#### [Parameters:](#parameters-32)

| Name | Type | Description |
| --- | --- | --- |
| `newSendSharesGate` | address | The new send shares gate contract. |

---

### [`submit`](#submit)

```
function submit(bytes calldata data) external
```

Submits a timelocked action for execution after the timelock period expires.

**Callable by:** `Curator`

#### [Parameters:](#parameters-33)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes | The ABI-encoded function call data. |

## [Allocator Functions](#allocator-functions)

### [`allocate`](#allocate)

```
function allocate(address adapter, bytes memory data, uint256 assets) external
```

Allocates `assets` from the vault's idle pool to a specific `adapter`. The allocation is subject to the caps configured for the target market.

**Callable by:** `Allocator`

#### [Parameters:](#parameters-34)

| Name | Type | Description |
| --- | --- | --- |
| `adapter` | address | The adapter to allocate assets to. |
| `data` | bytes | Market-specific data encoding passed to the adapter (e.g., market ID for Morpho markets). The hash of this data (`keccak256(data)`) identifies the allocation target for cap enforcement. |
| `assets` | uint256 | The amount of assets to allocate. |

---

### [`deallocate`](#deallocate)

```
function deallocate(address adapter, bytes memory data, uint256 assets) external
```

Deallocates `assets` from an `adapter` back to the vault's idle pool.

**Callable by:** `Allocator`, `Sentinel`

#### [Parameters:](#parameters-35)

| Name | Type | Description |
| --- | --- | --- |
| `adapter` | address | The adapter to deallocate assets from. |
| `data` | bytes | Market-specific data encoding passed to the adapter (e.g., market ID for Morpho markets). Must match the data used when allocating. |
| `assets` | uint256 | The amount of assets to deallocate. |

---

### [`setLiquidityAdapterAndData`](#setliquidityadapteranddata)

```
function setLiquidityAdapterAndData(address newLiquidityAdapter, bytes memory newLiquidityData) external
```

Sets the default adapter for handling user deposits and withdrawals.

**Callable by:** `Allocator`

#### [Parameters:](#parameters-36)

| Name | Type | Description |
| --- | --- | --- |
| `newLiquidityAdapter` | address | The new liquidity adapter address. |
| `newLiquidityData` | bytes | The new liquidity data for the adapter. |

---

### [`setMaxRate`](#setmaxrate)

```
function setMaxRate(uint256 newMaxRate) external
```

Sets the maximum rate at which `totalAssets` can grow. An allocator-controlled parameter that caps how quickly totalAssets can grow, useful for implementing fixed-rate distributions or preventing unrealistic yield spikes.
`maxRate` is capped at 200% APR (see `MAX_MAX_RATE` constant [here](https://github.com/morpho-org/vault-v2/blob/00881eb5f5c8031252c7fcdb7cd7e026bb21cfa4/src/libraries/ConstantsLib.sol#L9))

**Callable by:** `Allocator`

If `maxRate` is 0, yield does not accrue to vault's suppliers.

#### [Parameters:](#parameters-37)

| Name | Type | Description |
| --- | --- | --- |
| `newMaxRate` | uint256 | The new maximum rate per second (scaled by 1e18). |

## [Gating Functions](#gating-functions)

Gates are optional external smart contracts that implement access control for the vault.
The vault supports four independent gates: `receiveSharesGate`, `sendSharesGate`, `receiveAssetsGate`, and `sendAssetsGate`.

Gates are separate smart contracts that you (or the curator) must deploy independently.
They are not part of the vault contract itself. The curator configures them using functions like `setReceiveSharesGate`, `setSendSharesGate`, etc.

Each gate contract must implement a function that returns `bool` to indicate whether an account is allowed to perform the action.
The vault calls these gates during transfers and deposits/withdrawals to enforce access control.

---

### [`canReceiveShares`](#canreceiveshares)

```
function canReceiveShares(address account) public view returns (bool)
```

Checks if an account can receive shares based on the receive shares gate.

#### [Parameters:](#parameters-38)

| Name | Type | Description |
| --- | --- | --- |
| `account` | address | The account to check. |

#### [Return Values:](#return-values-12)

| Name | Type | Description |
| --- | --- | --- |
| `allowed` | bool | Whether the account can receive shares. |

---

### [`canSendShares`](#cansendshares)

```
function canSendShares(address account) public view returns (bool)
```

Checks if an account can send shares based on the send shares gate.

#### [Parameters:](#parameters-39)

| Name | Type | Description |
| --- | --- | --- |
| `account` | address | The account to check. |

#### [Return Values:](#return-values-13)

| Name | Type | Description |
| --- | --- | --- |
| `allowed` | bool | Whether the account can send shares. |

---

### [`canReceiveAssets`](#canreceiveassets)

```
function canReceiveAssets(address account) public view returns (bool)
```

Checks if an account can receive assets based on the receive assets gate. The vault itself is always allowed.

#### [Parameters:](#parameters-40)

| Name | Type | Description |
| --- | --- | --- |
| `account` | address | The account to check. |

#### [Return Values:](#return-values-14)

| Name | Type | Description |
| --- | --- | --- |
| `allowed` | bool | Whether the account can receive assets. |

---

### [`canSendAssets`](#cansendassets)

```
function canSendAssets(address account) public view returns (bool)
```

Checks if an account can send assets based on the send assets gate.

#### [Parameters:](#parameters-41)

| Name | Type | Description |
| --- | --- | --- |
| `account` | address | The account to check. |

#### [Return Values:](#return-values-15)

| Name | Type | Description |
| --- | --- | --- |
| `allowed` | bool | Whether the account can send assets. |

## [View Functions](#view-functions)

### [`totalAssets`](#totalassets)

```
function totalAssets() external view returns (uint256)
```

Returns the total amount of underlying assets held by the vault, including both idle assets and assets allocated to adapters.

#### [Return Values:](#return-values-16)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The total assets in the vault. |

---

### [`adaptersLength`](#adapterslength)

```
function adaptersLength() external view returns (uint256)
```

Returns the number of adapters currently added to the vault.

#### [Return Values:](#return-values-17)

| Name | Type | Description |
| --- | --- | --- |
| `length` | uint256 | The number of adapters. |

---

### [`absoluteCap`](#absolutecap)

```
function absoluteCap(bytes32 id) external view returns (uint256)
```

Returns the absolute cap for a given allocation `id`. The `id` is computed as `keccak256(idData)` where `idData` is the market-specific data identifying the allocation target.

#### [Parameters:](#parameters-42)

| Name | Type | Description |
| --- | --- | --- |
| `id` | bytes32 | The allocation identifier (keccak256 hash of idData). |

#### [Return Values:](#return-values-18)

| Name | Type | Description |
| --- | --- | --- |
| `cap` | uint256 | The absolute cap value. |

---

### [`relativeCap`](#relativecap)

```
function relativeCap(bytes32 id) external view returns (uint256)
```

Returns the relative cap for a given allocation `id`. The `id` is computed as `keccak256(idData)` where `idData` is the market-specific data identifying the allocation target.

#### [Parameters:](#parameters-43)

| Name | Type | Description |
| --- | --- | --- |
| `id` | bytes32 | The allocation identifier (keccak256 hash of idData). |

#### [Return Values:](#return-values-19)

| Name | Type | Description |
| --- | --- | --- |
| `cap` | uint256 | The relative cap value (scaled by 1e18). |

---

### [`allocation`](#allocation)

```
function allocation(bytes32 id) external view returns (uint256)
```

Returns the current allocation amount for a given `id`. The `id` is computed as `keccak256(idData)` where `idData` is the market-specific data identifying the allocation target.

#### [Parameters:](#parameters-44)

| Name | Type | Description |
| --- | --- | --- |
| `id` | bytes32 | The allocation identifier (keccak256 hash of idData). |

#### [Return Values:](#return-values-20)

| Name | Type | Description |
| --- | --- | --- |
| `amount` | uint256 | The current allocation amount. |

---

### [`owner`](#owner)

```
function owner() external view returns (address)
```

Returns the current owner address of the vault.

#### [Return Values:](#return-values-21)

| Name | Type | Description |
| --- | --- | --- |
| `owner` | address | The owner address. |

---

### [`curator`](#curator)

```
function curator() external view returns (address)
```

Returns the current curator address of the vault.

#### [Return Values:](#return-values-22)

| Name | Type | Description |
| --- | --- | --- |
| `curator` | address | The curator address. |

---

### [`isSentinel`](#issentinel)

```
function isSentinel(address account) external view returns (bool)
```

Checks if an account has the Sentinel role.

#### [Parameters:](#parameters-45)

| Name | Type | Description |
| --- | --- | --- |
| `account` | address | The account to check. |

#### [Return Values:](#return-values-23)

| Name | Type | Description |
| --- | --- | --- |
| `isSentinel` | bool | Whether the account is a sentinel. |

---

### [`isAllocator`](#isallocator)

```
function isAllocator(address account) external view returns (bool)
```

Checks if an account has the Allocator role.

#### [Parameters:](#parameters-46)

| Name | Type | Description |
| --- | --- | --- |
| `account` | address | The account to check. |

#### [Return Values:](#return-values-24)

| Name | Type | Description |
| --- | --- | --- |
| `isAllocator` | bool | Whether the account is an allocator. |

---

### [`receiveSharesGate`](#receivesharesgate)

```
function receiveSharesGate() external view returns (address)
```

Returns the address of the receive shares gate contract.

#### [Return Values:](#return-values-25)

| Name | Type | Description |
| --- | --- | --- |
| `gate` | address | The receive shares gate address. |

---

### [`sendSharesGate`](#sendsharesgate)

```
function sendSharesGate() external view returns (address)
```

Returns the address of the send shares gate contract.

#### [Return Values:](#return-values-26)

| Name | Type | Description |
| --- | --- | --- |
| `gate` | address | The send shares gate address. |

---

### [`receiveAssetsGate`](#receiveassetsgate)

```
function receiveAssetsGate() external view returns (address)
```

Returns the address of the receive assets gate contract.

#### [Return Values:](#return-values-27)

| Name | Type | Description |
| --- | --- | --- |
| `gate` | address | The receive assets gate address. |

---

### [`sendAssetsGate`](#sendassetsgate)

```
function sendAssetsGate() external view returns (address)
```

Returns the address of the send assets gate contract.

#### [Return Values:](#return-values-28)

| Name | Type | Description |
| --- | --- | --- |
| `gate` | address | The send assets gate address. |

---

### [`adapterRegistry`](#adapterregistry)

```
function adapterRegistry() external view returns (address)
```

Returns the address of the adapter registry contract.

#### [Return Values:](#return-values-29)

| Name | Type | Description |
| --- | --- | --- |
| `registry` | address | The adapter registry address. |

---

### [`adapters`](#adapters)

```
function adapters(uint256 index) external view returns (address)
```

Returns the adapter address at a specific index (index list retrievable via the [`adaptersLength`](https://docs.morpho.org/get-started/resources/contracts/morpho-vaults-v2/#adapterslength) function).

#### [Parameters:](#parameters-47)

| Name | Type | Description |
| --- | --- | --- |
| `index` | uint256 | The index in the adapters array. |

#### [Return Values:](#return-values-30)

| Name | Type | Description |
| --- | --- | --- |
| `adapter` | address | The adapter address at the given index. |

---

### [`isAdapter`](#isadapter)

```
function isAdapter(address account) external view returns (bool)
```

Checks if an account is a registered adapter.

#### [Parameters:](#parameters-48)

| Name | Type | Description |
| --- | --- | --- |
| `account` | address | The account to check. |

#### [Return Values:](#return-values-31)

| Name | Type | Description |
| --- | --- | --- |
| `isAdapter` | bool | Whether the account is an adapter. |

---

### [`liquidityAdapter`](#liquidityadapter)

```
function liquidityAdapter() external view returns (address)
```

Returns the default adapter used for handling user deposits and withdrawals.

#### [Return Values:](#return-values-32)

| Name | Type | Description |
| --- | --- | --- |
| `adapter` | address | The liquidity adapter address. |

---

### [`liquidityData`](#liquiditydata)

```
function liquidityData() external view returns (bytes memory)
```

Returns the data associated with the liquidity adapter.

#### [Return Values:](#return-values-33)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes | The liquidity adapter data. |

---

### [`forceDeallocatePenalty`](#forcedeallocatepenalty)

```
function forceDeallocatePenalty(address adapter) external view returns (uint256)
```

Returns the penalty for using `forceDeallocate` on a specific adapter.

#### [Parameters:](#parameters-49)

| Name | Type | Description |
| --- | --- | --- |
| `adapter` | address | The adapter to check. |

#### [Return Values:](#return-values-34)

| Name | Type | Description |
| --- | --- | --- |
| `penalty` | uint256 | The force deallocate penalty (scaled by 1e18). |

---

### [`virtualShares`](#virtualshares)

```
function virtualShares() external view returns (uint256)
```

Returns the virtual shares used for avoiding initial share inflation attacks.

#### [Return Values:](#return-values-35)

| Name | Type | Description |
| --- | --- | --- |
| `shares` | uint256 | The virtual shares amount. |

---

### [`firstTotalAssets`](#firsttotalassets)

```
function firstTotalAssets() external view returns (uint256)
```

Returns the total assets after the first interest accrual of the current transaction. Used to prevent bypassing relative caps with flashloans.

#### [Return Values:](#return-values-36)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The total assets after the first interest accrual of the transaction. |

---

### [`_totalAssets`](#_totalassets)

```
function _totalAssets() external view returns (uint128)
```

Returns the internal cached total assets value.

#### [Return Values:](#return-values-37)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint128 | The cached total assets. |

---

### [`lastUpdate`](#lastupdate)

```
function lastUpdate() external view returns (uint64)
```

Returns the timestamp of the last interest accrual.

#### [Return Values:](#return-values-38)

| Name | Type | Description |
| --- | --- | --- |
| `timestamp` | uint64 | The last update timestamp. |

---

### [`maxRate`](#maxrate)

```
function maxRate() external view returns (uint64)
```

Returns the maximum rate at which `totalAssets` can grow.

#### [Return Values:](#return-values-39)

| Name | Type | Description |
| --- | --- | --- |
| `rate` | uint64 | The maximum rate per second (scaled by 1e18). |

---

### [`performanceFee`](#performancefee)

```
function performanceFee() external view returns (uint96)
```

Returns the current performance fee.

#### [Return Values:](#return-values-40)

| Name | Type | Description |
| --- | --- | --- |
| `fee` | uint96 | The performance fee (scaled by 1e18). |

---

### [`performanceFeeRecipient`](#performancefeerecipient)

```
function performanceFeeRecipient() external view returns (address)
```

Returns the recipient address of performance fees.

#### [Return Values:](#return-values-41)

| Name | Type | Description |
| --- | --- | --- |
| `recipient` | address | The performance fee recipient address. |

---

### [`managementFee`](#managementfee)

```
function managementFee() external view returns (uint96)
```

Returns the current management fee.

#### [Return Values:](#return-values-42)

| Name | Type | Description |
| --- | --- | --- |
| `fee` | uint96 | The management fee (scaled by 1e18). |

---

### [`managementFeeRecipient`](#managementfeerecipient)

```
function managementFeeRecipient() external view returns (address)
```

Returns the recipient address of management fees.

#### [Return Values:](#return-values-43)

| Name | Type | Description |
| --- | --- | --- |
| `recipient` | address | The management fee recipient address. |

---

### [`timelock`](#timelock)

```
function timelock(bytes4 selector) external view returns (uint256)
```

Returns the timelock duration for a specific function selector.

#### [Parameters:](#parameters-50)

| Name | Type | Description |
| --- | --- | --- |
| `selector` | bytes4 | The function selector. |

#### [Return Values:](#return-values-44)

| Name | Type | Description |
| --- | --- | --- |
| `duration` | uint256 | The timelock duration in seconds. |

---

### [`abdicated`](#abdicated)

```
function abdicated(bytes4 selector) external view returns (bool)
```

Checks if the curator has abdicated the ability to execute a specific action.

#### [Parameters:](#parameters-51)

| Name | Type | Description |
| --- | --- | --- |
| `selector` | bytes4 | The function selector. |

#### [Return Values:](#return-values-45)

| Name | Type | Description |
| --- | --- | --- |
| `abdicated` | bool | Whether the action has been abdicated. |

---

### [`executableAt`](#executableat)

```
function executableAt(bytes memory data) external view returns (uint256)
```

Returns the timestamp when a submitted timelocked action becomes executable.

#### [Parameters:](#parameters-52)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes | The ABI-encoded function call data. |

#### [Return Values:](#return-values-46)

| Name | Type | Description |
| --- | --- | --- |
| `timestamp` | uint256 | The timestamp when the action becomes executable. |

---

### [`DOMAIN_SEPARATOR`](#domain_separator)

```
function DOMAIN_SEPARATOR() external view returns (bytes32)
```

Returns the EIP-712 domain separator used for permit signatures.

#### [Return Values:](#return-values-47)

| Name | Type | Description |
| --- | --- | --- |
| `separator` | bytes32 | The domain separator. |

[Blue

Previous Page

](https://docs.morpho.org/developers/contracts/blue/)[MorphoMarketV1AdapterV2

Next Page

](https://docs.morpho.org/developers/contracts/morpho-market-v1-adapter-v2/)