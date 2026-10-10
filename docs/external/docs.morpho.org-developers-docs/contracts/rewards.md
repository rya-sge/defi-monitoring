# Universal Rewards Distributors (Deprecated)

> Source: https://docs.morpho.org/developers/contracts/rewards

---

# Universal Rewards Distributors (Deprecated)

Universal Rewards Distributors has been **deprecated**.

[Universal Rewards Distributors repository](https://github.com/morpho-org/universal-rewards-distributor/tree/main)

## [Contract Overview](#contract-overview)

The [`UniversalRewardsDistributor`](https://github.com/morpho-org/universal-rewards-distributor/tree/main) contract facilitates the distribution of various reward tokens to multiple accounts using different Merkle trees. It is designed to operate in a permissionless manner and is inspired by Morpho's current rewards distributor.

The contract enables the dynamic update of distribution parameters, management of reward claims, and ensures the integrity of the distribution through the use of Merkle proofs.

## [Functions](#functions)

### [submitRoot](#submitroot)

```
function submitRoot(bytes32 newRoot, bytes32 newIpfsHash) external onlyUpdaterRole;
```

Submits a new merkle root for the distribution of rewards.

- Can only be called by an address with updater role.
- Emits a `PendingRootSet` event.

#### [Parameters:](#parameters)

| Name | Type | Description |
| --- | --- | --- |
| `newRoot` | bytes32 | The new merkle root. |
| `newIpfsHash` | bytes32 | The optional ipfs hash containing metadata about the root. |

### [acceptRoot](#acceptroot)

```
function acceptRoot() external;
```

Accepts and sets the current pending merkle root after the timelock has expired.

- Can be called by any address.
- Reverts if no pending root is set or if the timelock has not expired.
- Emits a `RootSet` event upon successful execution.

### [revokePendingRoot](#revokependingroot)

```
function revokePendingRoot() external onlyUpdaterRole;
```

Revokes the current pending merkle root.

- Can only be called by an address with updater role.
- Reverts if no pending root is set.
- Emits a `PendingRootRevoked` event.

### [claim](#claim)

```
function claim(address account, address reward, uint256 claimable, bytes32[] calldata proof) external returns (uint256 amount);
```

Claims rewards for a specific account.

- Reverts if the root is not set, if the proof is invalid, or if the claimable amount is less than the amount already claimed.
- Emits a `Claimed` event upon successful execution.

#### [Parameters:](#parameters-1)

| Name | Type | Description |
| --- | --- | --- |
| `account` | address | The address to claim rewards for. |
| `reward` | address | The address of the reward token. |
| `claimable` | uint256 | The overall claimable amount of token rewards. |
| `proof` | bytes32[] | The merkle proof that validates this claim. |

#### [Return values:](#return-values)

| Name | Type | Description |
| --- | --- | --- |
| `amount` | uint256 | The amount of reward token claimed. |

### [setRoot](#setroot)

```
function setRoot(bytes32 newRoot, bytes32 newIpfsHash) external onlyUpdaterRole;
```

Forces update of the distribution's merkle root, bypassing the timelock.

- Can only be called by the owner of the distribution or by updaters if there is no timelock.
- Reverts if the new root is the same as the current root and if the caller is unauthorized to change the root.
- Emits a `RootSet` event upon successful execution.

#### [Parameters:](#parameters-2)

| Name | Type | Description |
| --- | --- | --- |
| `newRoot` | bytes32 | The new merkle root. |
| `newIpfsHash` | bytes32 | The optional ipfs hash containing metadata about the root. |

### [setTimelock](#settimelock)

```
function setTimelock(uint256 newTimelock) external onlyOwner;
```

Sets a new timelock for the distribution.

- Can only be called by the owner of the distribution.
- Reverts if the new timelock is the same as the current timelock.
- Emits a `TimelockSet` event upon successful execution.

#### [Parameters:](#parameters-3)

| Name | Type | Description |
| --- | --- | --- |
| `newTimelock` | uint256 | The new timelock. |

### [setRootUpdater](#setrootupdater)

```
function setRootUpdater(address updater, bool active) external onlyOwner;
```

Sets or unsets an address as a root updater.

#### [Parameters:](#parameters-4)

| Name | Type | Description |
| --- | --- | --- |
| `updater` | address | The address of the root updater. |
| `active` | bool | Whether the root updater should be active or not. |

- Can only be called by the owner of the distribution.
- Reverts if the updater status is already set as specified.
- Emits a `RootUpdaterSet` event upon successful execution.

### [setOwner](#setowner)

```
function setOwner(address newOwner) external onlyOwner;
```

Transfers ownership of the distribution to a new address.

- Can only be called by the current owner.
- Reverts if the new owner is the same as the current owner.
- Emits an `OwnerSet` event upon successful execution.

#### [Parameters:](#parameters-5)

| Name | Type | Description |
| --- | --- | --- |
| `newOwner` | address | The address of the new owner. |

## [Events](#events)

The contract emits events to signify important actions and state changes. Here are the events associated with the `UniversalRewardsDistributor` contract:

- `PendingRootSet`: Emitted when a new pending root is submitted.
- `PendingRootRevoked`: Emitted when a pending root is revoked.
- `RootSet`: Emitted when a new root is accepted and set.
- `Claimed`: Emitted when rewards are successfully claimed.
- `RootUpdaterSet`: Emitted when a root updater's status is changed.
- `OwnerSet`: Emitted when a new owner is set for the distribution.
- `TimelockSet`: Emitted when the timelock is updated.

## [Roles](#roles)

There are only 2 roles:

- **Owner**: owner of the contract that has access to the updater's functions and [`setTimelock`](#settimelock), [`setRootUpdater`](#setrootupdater), and [`setOwner`](#setowner) functions.
- **Updater**: addresses that can trigger the [`submitRoot`](#submitroot), [`setRoot`](#setroot), and [`revokePendingRoot`](#revokependingroot) functions.

[Bundles

Previous Page

](https://docs.morpho.org/developers/contracts/bundles/)[Morpho Optimizers (Deprecated)

Next Page

](https://docs.morpho.org/developers/contracts/morpho-v0/)