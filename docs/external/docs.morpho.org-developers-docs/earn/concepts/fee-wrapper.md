# Fee Wrapper

> Source: https://docs.morpho.org/developers/earn/concepts/fee-wrapper

---

# Fee Wrapper

## [What is a Fee Wrapper?](#what-is-a-fee-wrapper)

A **Fee Wrapper** is a Vault V2 configured in a specific, constrained mode that enables distribution channels to add a fee layer on top of an existing Morpho Vault V2.

1. **Main Morpho Vault V2**: Handles actual capital allocation to Morpho Markets (V1, V2, future versions). This is where yield is generated.
2. **Fee Wrapper**: A lightweight **Vault V2** that deposits into the main Morpho Vault V2, with the sole purpose of adding a fee layer per customer/distributor.

![Fee Wrapper Architecture](https://docs.morpho.org/img/build/earn/fee-wrapper.png)
Both Fee Wrapper and Morpho Vault V2 use the same Vault V2 smart contract, but with different configurations:

- **Morpho Vaults V2** lock their adapter registry to the official Morpho Registry
- **Fee Wrappers** lock their adapter list to a single underlying Morpho Vault V2

Fee Wrappers are not listed on app.morpho.org.

## [Key Properties](#key-properties)

| Property | Description |
| --- | --- |
| **ERC-4626 Mostly Compliant** | Mostly compliant, with shares remaining fully ERC-20. See [Vault V2 principles](https://docs.morpho.org/get-started/resources/contracts/morpho-vaults-v2/#introduction-to-principles) |
| **Immutably Bound** | Bound to a single Morpho Vault V2 at deployment. Can **not** be changed |
| **Fee Flexibility** | Owner can configure performance fees (up to 50%) and management fees (up to 5%) |
| **Simplified Configuration** | Risk management functions are abdicated, making operation simpler |
| **Shared Liquidity** | Users share the liquidity of the underlying Morpho Vault V2 |

## [Architecture](#architecture)

A Fee Wrapper is deployed with a carefully designed split between immutable, defaulted, and configurable parameters.

**Fixed at deployment** (`addAdapter` / `removeAdapter` abdicated):

- The single adapter pointing to the underlying Morpho Vault V2
- The adapter registry lock (no new adapters can ever be added)

**Set to recommended defaults:**

- Absolute and relative caps set to maximum values
- Max rate set to maximum
- Force-deallocate penalty set to 2% (MAX_FORCE_DEALLOCATE_PENALTY)
- Liquidity adapter set to the single Morpho Vault V2 adapter
- All roles (Curator, Allocator, Sentinel) default to the owner

**Configurable by the owner:**

- Owner address
- Vault name and symbol
- Performance fee (up to 50%) and management fee (up to 5%)
- Fee recipient address
- Gate abdication mode (`abdicateNonCriticalGates`)

## [Gates & Non-Custodiality](#gates--non-custodiality)

Gates control who can interact with the vault. Each gate is a contract slot that, when set, enforces on-chain rules on a specific action. A Fee Wrapper has four gates:

| Gate | Action it governs | Critical? |
| --- | --- | --- |
| `receiveAssetsGate` | Who can receive assets on withdrawal | Yes - can lock assets |
| `receiveSharesGate` | Who can receive shares | Yes - can lock assets |
| `sendSharesGate` | Who can send/transfer shares | Yes - can lock assets |
| `sendAssetsGate` | Who can deposit assets | No - cannot lock assets |

The three **critical** gates can prevent users from accessing their own assets if misconfigured. The fourth gate (`sendAssetsGate`) only restricts who can deposit and cannot lock assets in the wrapper. The underlying vault's `sendAssetsGate` is a different case, see [Underlying vault gates](#underlying-vault-gates).

By default all four gates are set to `address(0)` (permissionless): anyone can deposit, withdraw, and transfer shares freely.

### [Non-custodial (recommended for DeFi)](#non-custodial-recommended-for-defi)

Permanently abdicate the three critical gate setters at deployment. This locks them to `address(0)` forever - no one can ever restrict user access to assets. This action is **irreversible**.

The non-critical `sendAssetsGate` remains configurable so the curator can still restrict who can deposit post-deployment if needed, without affecting asset safety.

### [Compliance-ready (KYC/AML)](#compliance-ready-kycaml)

Keep all gate setters configurable and set gate contracts post-deployment to enforce on-chain rules (e.g., KYC whitelists). The curator can set or change gate contracts at any time via timelocked actions.

This enables compliance-ready distribution but makes the vault **partially custodial**, because the critical gates could restrict certain users from accessing their assets.

Keeping the critical gate setters configurable affects non-custodial guarantees. Review the implications carefully before choosing this path.

### [Underlying vault gates](#underlying-vault-gates)

The Fee Wrapper's gates only cover the wrapper itself. Its adapter deposits into and withdraws from the underlying Morpho Vault V2 like any depositor, so the underlying vault's gates apply to the adapter address:

| Underlying vault gate | Effect if it blocks the adapter | Effect if it blocks a wrapper depositor |
| --- | --- | --- |
| `receiveSharesGate` | Wrapper deposits revert | In-kind redemption reverts |
| `sendSharesGate` | Wrapper withdrawals beyond its idle assets and `forceDeallocate` revert | - |
| `receiveAssetsGate` | Wrapper withdrawals beyond its idle assets and `forceDeallocate` revert | - |
| `sendAssetsGate` | Wrapper deposits revert | In-kind redemption reverts |

A wrapper depositor's in-kind redemption deposits flash-loaned assets into the underlying vault, so the underlying vault's deposit gates are also checked against the depositor.

Abdicating the wrapper's critical gates does not protect users if the underlying vault's curator can still set a gate that blocks the adapter or the in-kind exit. For a Fee Wrapper, the underlying vault's `sendAssetsGate` is critical too.

A Fee Wrapper is fully non-custodial only when both conditions hold:

- The wrapper's three critical gates are abdicated
- The underlying vault's three critical gates and its `sendAssetsGate` are abdicated, or set to gates that can never block the wrapper's adapter or its depositors

Check the underlying vault's gates and abdications before deploying a Fee Wrapper on it.

For more details on gates, see the [Gates concept page](https://docs.morpho.org/curate/concepts/gates/) and the [Abdicate Gates tutorial](https://docs.morpho.org/curate/tutorials-v2/abdicate-gates/).

## [Use Cases](#use-cases)

- **B2B Distribution**: Distributors can deploy one Fee Wrapper per customer, each with custom fee configurations
- **Revenue Sharing**: Split native yield between the distribution channel and end users (e.g., 50/50 split via fee configuration)
- **White-Label Products**: Distributor can offer Morpho yield under their own brand with their own fee structure

## [Yield and Rewards](#yield-and-rewards)

**Native Yield (Inside ERC-4626 Flow)**

Native yield comes from interest paid by borrowers on underlying Morpho Markets. It accrues automatically to shares over time, requiring no separate claim - shares simply appreciate in value. Users withdraw the same token they deposited (e.g., USDC) plus accrued interest. Performance and management fees are applied to this yield.

**External Rewards (Outside ERC-4626 Flow)**

External rewards (e.g., MORPHO tokens) come from incentives provided by Morpho governance, market creators, or token issuers, and are distributed via Merkl (updated every 8 hours). These rewards require a separate claim action through Merkl and are automatically forwarded to end depositors by default.
It is possible to implement custom distribution. For specific reward routing (e.g., distributor claims rewards instead of users), coordinate with the Merkl team for address remapping configuration.

## [Deployment](#deployment)

**Dead deposit required.** Before any user deposits into the underlying Fee Wrapper, a [dead deposit](https://docs.morpho.org/curate/tutorials-v2/dead-deposit/) must be executed as the very first transaction on the empty Fee Wrapper. This protects against ERC-4626 inflation attacks. If skipped, the attack may be possible.

### [Curator App V2](#curator-app-v2)

Use the [Curator App V2](https://curator.morpho.org/vaults) to deploy and manage Fee Wrappers. To deploy a new Fee Wrapper, open the [Fee Wrapper creation flow](https://curator.morpho.org/fee-wrapper/create).

The Curator App V2 lets you:

- Deploy a new Fee Wrapper
- Check whether a Fee Wrapper is properly configured
- Update fees on an existing Fee Wrapper

Find the factory addresses in the [addresses section](https://docs.morpho.org/get-started/resources/addresses/).

### [Programmatic Deployment](#programmatic-deployment)

For programmatic deployments, use the **FeeWrapperDeployer** periphery contract to create and configure a wrapper in a single transaction.

The FeeWrapperDeployer is documented inline in its source code. Refer to the latest implementation details directly in the repository before wiring deployment automation.

**[FeeWrapperDeployer.sol on GitHub](https://github.com/morpho-org/morpho-snippets/blob/main/src/vault-v2/FeeWrapperDeployer.sol)**

## [Integration Guide](#integration-guide)

Query the Morpho API to compute post-fee APY. No on-chain reads needed - all data comes from the API.

### [1. Query the Morpho API](#1-query-the-morpho-api)

Endpoint: POST [https://api.morpho.org/graphql](https://api.morpho.org/graphql)

Use the fee wrapper address directly (not the underlying Morpho Vault V2 address) along with the chainID.

```
query FeeWrapperAPY {
  feeWrapper: vaultV2ByAddress(
    address: "0x2861ABE7AB28484Fb8375def4A7eb56C8F53fE8F"
    chainId: 8453
  ) {
    avgNetApy
    avgNetApyExcludingRewards
    performanceFee
    managementFee
    name
    symbol
    rewards {
      supplyApr
      asset { address, symbol }
    }
    adapters {
      items {
        type
        address
        ... on MorphoVaultV2Adapter {
          innerVault {
            address
            name
            avgNetApyExcludingRewards
            performanceFee
            managementFee
            rewards {
              supplyApr
              asset { address, symbol }
            }
          }
        }
      }
    }
  }
}
```

### [2. Read Net APY](#2-read-net-apy)

The API response includes pre-computed net APY values that account for the full fee chain (inner vault fees + wrapper fees + rewards):

- **`avgNetApy`** - 6h rolling average net APY, including rewards. This is the recommended value for most integrations.
- **`avgNetApyExcludingRewards`** - Same as above but excluding reward incentives.

These values are ready to use directly - no manual computation needed.

> If rewards are redirected via Merkl address remapping, `avgNetApyExcludingRewards` is the correct value to display (end users do not receive the rewards).

### [3. Advanced: Manual APY Breakdown (Optional)](#3-advanced-manual-apy-breakdown-optional)

For newly deployed fee wrappers, `avgNetApy` may be zero or noisy until sufficient history accumulates. The manual computation below uses `innerVault.avgNetApyExcludingRewards` for consistent results in those cases, and is also useful when a granular per-layer fee breakdown is needed.

```
// innerVault.avgNetApyExcludingRewards already includes inner vault fee deductions
adapterYield = innerVault.avgNetApyExcludingRewards
wrapperPerfFeeDeduction = max(adapterYield, 0) * feeWrapper.performanceFee
nativeYield = adapterYield - wrapperPerfFeeDeduction - feeWrapper.managementFee
rewardsApr = sum(innerVault.rewards[].supplyApr)
netApy = nativeYield + rewardsApr
```

> **Note:** `avgNetApyExcludingRewards` is the 6h rolling average net yield after the inner vault's own performance and management fees, but excluding reward incentives. Rewards are sourced from the inner vault (`innerVault.rewards[]`) and distributed via Merkl based on the inner vault's market positions.

More Fee Wrapper API data can be found [here](https://docs.morpho.org/developers/earn/tutorials/get-data/#fee-wrapper).

## [Roles & Auth Model](#roles--auth-model)

All roles default to the **owner** at deployment:

| Role | Default | Description |
| --- | --- | --- |
| **Owner** | deployer | Top-level permissions. No timelock on ownership actions. |
| **Curator** | owner | Configures vault risk parameters and market allocation strategy. Most actions are timelocked. |
| **Allocator** | owner | Executes liquidity allocation within Curator-approved constraints. No timelock on allocation actions. |
| **Sentinel** | owner | Safety role. Can revoke pending actions and reduce risk. |

**Auth tiers:**

- **Owner-level**: Transfer ownership, set roles - no timelock
- **Curator-level**: Change fees, fee recipients, caps - timelocked
- **Allocator-level**: Allocate/deallocate to the adapter - no timelock

## [Security Considerations](#security-considerations)

**What the Owner CAN Do:**

- Change performance fees (up to 50%, timelocked)
- Change management fees (up to 5%, timelocked)
- Change fee recipients (timelocked)
- Add/remove allocators (timelocked)

**What the Owner CANNOT Do:**

- Change the underlying vault (abdicated)
- Add new adapters (abdicated)
- Remove the existing adapter (abdicated)
- Access user assets directly
- Prevent users from exiting (via forceDeallocate), provided the wrapper's critical gates are abdicated. See [Underlying vault gates](#underlying-vault-gates) for the conditions on the underlying vault.

[How can distributors generate revenue on Morpho?

Previous Page

](https://docs.morpho.org/developers/earn/concepts/generate-revenue/)[Wallet Structures

Next Page

](https://docs.morpho.org/developers/earn/concepts/wallet-structures/)