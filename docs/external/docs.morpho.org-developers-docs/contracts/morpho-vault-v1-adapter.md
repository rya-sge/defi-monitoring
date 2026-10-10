# MorphoVaultV1Adapter

> Source: https://docs.morpho.org/developers/contracts/morpho-vault-v1-adapter

---

# MorphoVaultV1Adapter

[v2.0 repository](https://github.com/morpho-org/vault-v2)

## [Introduction](#introduction)

`MorphoVaultV1Adapter` is an adapter that connects a Morpho Vault V2 to a Morpho Vault V1. It wraps deposits and withdrawals to/from the underlying Vault V1 on behalf of the parent Vault V2.

This adapter must be used with Morpho Vaults V1 that are protected against inflation attacks with an initial supply. See [OpenZeppelin ERC4626 inflation attack](https://docs.openzeppelin.com/contracts/5.x/erc4626#inflation-attack) and Inflation Front-Running Attack Protection section [here](https://docs.morpho.org/curate/concepts/security-considerations/#inflation-front-running-attack-protection).

Must not be used with a Morpho Vault V1 that has a market with an IRM that can re-enter the parent vault or the adapter.

Morpho Vaults V1.1 do not realize bad debt, so a Vault V2 supplying through this adapter will not realize the corresponding bad debt either.

## [Timelock System](#timelock-system)

This adapter has no timelock system. All functions are callable directly by their respective roles with no submit/execute delay.

## [Immutables](#immutables)

| Name | Type | Description |
| --- | --- | --- |
| `factory` | address | The factory contract that deployed this adapter. |
| `parentVault` | address | The Morpho Vault V2 that this adapter belongs to. |
| `morphoVaultV1` | address | The Morpho Vault V1 (MetaMorpho) contract that this adapter deposits into. |
| `adapterId` | bytes32 | Unique identifier for this adapter instance, computed as `keccak256(abi.encode("this", address(this)))`. |

## [Owner Functions](#owner-functions)

### [`setSkimRecipient`](#setskimrecipient)

```
function setSkimRecipient(address newSkimRecipient) external
```

Sets the address that receives skimmed token balances.

**Callable by:** `Owner` of the parent vault (instant - no timelock)

#### [Parameters:](#parameters)

| Name | Type | Description |
| --- | --- | --- |
| `newSkimRecipient` | address | The new skim recipient address. |

## [Other Functions](#other-functions)

### [`skim`](#skim)

```
function skim(address token) external
```

Transfers the adapter's entire balance of `token` to `skimRecipient`.

Shares of the underlying Morpho Vault V1 (`morphoVaultV1`) cannot be skimmed and will revert if passed as `token`.

**Callable by:** `skimRecipient`

If `skimRecipient` is not set (`address(0)`), this function will always revert.

#### [Parameters:](#parameters-1)

| Name | Type | Description |
| --- | --- | --- |
| `token` | address | The token to skim. Must not be the `morphoVaultV1` share token. |

---

### [`allocate`](#allocate)

```
function allocate(bytes memory data, uint256 assets, bytes4, address) external returns (bytes32[] memory, int256)
```

Deposits `assets` into the underlying Morpho Vault V1.

**Callable by:** `parentVault`

#### [Parameters:](#parameters-2)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes | Must be empty (`0x`). |
| `assets` | uint256 | The amount of assets to deposit. |

The `bytes4` and `address` parameters are part of the shared adapter interface but unused by this implementation.

#### [Return Values:](#return-values)

| Name | Type | Description |
| --- | --- | --- |
| `ids` | bytes32[] | The allocation IDs affected (contains `adapterId`). |
| `delta` | int256 | The change in allocation (new allocation minus old allocation). |

---

### [`deallocate`](#deallocate)

```
function deallocate(bytes memory data, uint256 assets, bytes4, address) external returns (bytes32[] memory, int256)
```

Withdraws `assets` from the underlying Morpho Vault V1 back to the parent vault.

**Callable by:** `parentVault`

#### [Parameters:](#parameters-3)

| Name | Type | Description |
| --- | --- | --- |
| `data` | bytes | Must be empty (`0x`). |
| `assets` | uint256 | The amount of assets to withdraw. |

The `bytes4` and `address` parameters are part of the shared adapter interface but unused by this implementation.

#### [Return Values:](#return-values-1)

| Name | Type | Description |
| --- | --- | --- |
| `ids` | bytes32[] | The allocation IDs affected (contains `adapterId`). |
| `delta` | int256 | The change in allocation (new allocation minus old allocation). |

## [View Functions](#view-functions)

### [`realAssets`](#realassets)

```
function realAssets() external view returns (uint256)
```

Returns the current value of the adapter's Vault V1 share balance in underlying assets. Returns `0` if the parent vault has no recorded allocation for this adapter.

#### [Return Values:](#return-values-2)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The current value of held Vault V1 shares, or `0` if allocation is zero. |

---

### [`allocation`](#allocation)

```
function allocation() public view returns (uint256)
```

Returns the vault's current allocation for this adapter, as recorded in the parent vault (keyed by `adapterId`).

#### [Return Values:](#return-values-3)

| Name | Type | Description |
| --- | --- | --- |
| `assets` | uint256 | The current allocation amount in the parent vault. |

---

### [`ids`](#ids)

```
function ids() public view returns (bytes32[] memory)
```

Returns the allocation IDs used by this adapter. Contains a single entry: `adapterId`.

#### [Return Values:](#return-values-4)

| Name | Type | Description |
| --- | --- | --- |
| `ids_` | bytes32[] | Array of 1 ID: `adapterId` (`keccak256(abi.encode("this", address(this)))`). |

---

### [`skimRecipient`](#skimrecipient)

```
address public skimRecipient
```

Returns the address that receives skimmed token balances.

#### [Return Values:](#return-values-5)

| Name | Type | Description |
| --- | --- | --- |
| `recipient` | address | The current skim recipient address. |