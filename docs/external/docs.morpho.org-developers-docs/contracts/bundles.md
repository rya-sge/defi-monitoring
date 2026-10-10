# Bundles

> Source: https://docs.morpho.org/developers/contracts/bundles

---

# Bundles

[Bundles repository](https://github.com/morpho-org/bundles)

## [Bundles structure](#bundles-structure)

Bundles are opinionated, end-user-facing entrypoints that execute a fixed
chain of calls against a Morpho protocol in a single transaction. Each
entrypoint performs atomic checks, can receive callbacks (e.g. Morpho
callbacks used to sequence a borrow and a supply), and keeps calldata simple
to verify. Bundles operate on `msg.sender`'s position and are not meant to be
called by other contracts or to hold token balances between transactions.

Most Bundle entrypoints share the same building blocks:

- **Token permits** - each underlying token the Bundle pulls from the caller accepts an optional `TokenPermit`, either an ERC-2612 `permit` or a Permit2 `SignatureTransfer`, so the approval and the operation land in one transaction. An empty permit means the caller granted a standard ERC-20 allowance to the Bundle beforehand.
- **Share permits** - share-based entrypoints (`vaultBundlesV1Withdraw`, `vaultBundlesV1Migrate`, and every `vaultExitBundlesV1*` entrypoint) take an ERC-2612 `Permit` on the vault shares instead, or rely on a prior share allowance to the Bundle. Shares never go through Permit2.
- **Signed authorization** - `BlueBundlesV1` entrypoints that act on the caller's Morpho position (borrow, withdraw, repay-and-withdraw-collateral, migrate) accept an optional Morpho `SignedAuthorization` so the caller can authorize the Bundle in the same transaction. An empty signature means the Bundle is already authorized. Vault entrypoints take share permits, not Morpho authorizations.
- **Public allocations** - entrypoints that consume market liquidity accept a list of Vault V2 [`BluePublicAllocator`](https://docs.morpho.org/developers/contracts/blue-public-allocator/) reallocations executed before the operation.
- **Referral fee** and **deadline** - every entrypoint except the two in-kind redemptions takes a caller-chosen `referralFeePct` (WAD-scaled, strictly below `WAD`) and `referralFeeRecipient`, plus a call deadline after which the transaction reverts. The fee is paid in the loan or vault asset to the recipient within the same transaction, so integrators can use it to monetize their integration without any extra contract. On borrow and withdraw entrypoints (including `vaultExitBundlesV1ForceWithdrawVaultV2`) the fee is taken from the proceeds, after any public allocator penalties; on supply and deposit it is deducted from the supplied amount; on repay it is charged on top of the repaid amount (`fee = repaidAssets * referralFeePct / (WAD - referralFeePct)`). On `blueBundlesV1MigrateBorrowPosition` the fee and any public allocator penalties are borrowed on top of the migrated debt, so they increase the debt on the destination market; on `vaultBundlesV1Migrate` the fee is deducted from the withdrawn assets before the deposit into the destination vault. Pass `0` for no fee. See [How to monetize your borrow product](https://docs.morpho.org/developers/borrow/guides/monetize-borrow-product/).

The deployment addresses of every Bundle are listed in the [addresses page](https://docs.morpho.org/developers/contracts/addresses/#bundles).

### [](#bluebundlesv1)[`BlueBundlesV1`](https://github.com/morpho-org/bundles/blob/main/src/blue/BlueBundlesV1.sol)

Entrypoints for [Variable Rate Markets (Morpho Blue)](https://docs.morpho.org/developers/contracts/blue/):

| Entrypoint | What it does |
| --- | --- |
| `blueBundlesV1Supply` | Supply loan assets to a market. |
| `blueBundlesV1Withdraw` | Withdraw supplied loan assets, by assets or by shares. |
| `blueBundlesV1SupplyCollateralAndBorrow` | Supply collateral and borrow, bounded by a `maxLtv` check. |
| `blueBundlesV1RepayAndWithdrawCollateral` | Repay debt, by assets or by shares, and withdraw collateral, bounded by a `maxLtv` check. |
| `blueBundlesV1MigrateBorrowPosition` | Move a full borrow position (collateral and debt) from one market to another in one transaction - the source debt is repaid atomically with assets borrowed on the destination market, so the caller needs no repay funds. |

`blueBundlesV1SupplyCollateralAndBorrow`, `blueBundlesV1Withdraw` and `blueBundlesV1MigrateBorrowPosition` accept Vault V2 `BluePublicAllocator` reallocations.

### [](#vaultbundlesv1)[`VaultBundlesV1`](https://github.com/morpho-org/bundles/blob/main/src/vault/VaultBundlesV1.sol)

Entrypoints for [Vault V1](https://docs.morpho.org/developers/contracts/morpho-vaults/) and [Vault V2](https://docs.morpho.org/developers/contracts/morpho-vaults-v2/):

| Entrypoint | What it does |
| --- | --- |
| `vaultBundlesV1Deposit` | Deposit assets into a vault. |
| `vaultBundlesV1Withdraw` | Withdraw assets from a vault. |
| `vaultBundlesV1Migrate` | Migrate assets from one vault to another vault. |

### [](#vaultexitbundlesv1)[`VaultExitBundlesV1`](https://github.com/morpho-org/bundles/blob/main/src/vault-exit/VaultExitBundlesV1.sol)

Exit paths for vaults whose liquidity is constrained:

| Entrypoint | What it does |
| --- | --- |
| `vaultExitBundlesV1InKindRedemptionVaultV1` | Redeem in kind from an illiquid Vault V1. |
| `vaultExitBundlesV1InKindRedemptionVaultV2` | Withdraw idle assets and redeem the remainder in kind from an illiquid Vault V2. |
| `vaultExitBundlesV1ForceWithdrawVaultV2` | Force withdraw assets from an illiquid Vault V2 whose underlying markets are liquid, paying the force-deallocate penalty (idle and liquidity-adapter assets are withdrawn penalty-free first). |

### [Midnight Bundles](#midnight-bundles)

Taker entrypoints (`MidnightBundlesV1`) - taking offers by units or assets target, supplying collateral and selling, and repaying and withdrawing collateral - for [Midnight](https://docs.morpho.org/developers/midnight/get-started/) are documented in the [Midnight resources](https://docs.morpho.org/developers/midnight/resources/all/).

## [Permit2](#permit2)

In November 2022, Uniswap Labs introduced [Permit2](https://blog.uniswap.org/permit2-and-universal-router), a robust token approval contract designed to standardize and secure token approvals across various smart contracts. By enabling signature-based approvals and efficient management of token allowances, Permit2 significantly enhances the user experience. It reduces transaction costs and bolsters smart contract security by mitigating risks associated with traditional approval methods.

Bundles accept Permit2 `SignatureTransfer` permits, naming the Bundle as spender, as an alternative to ERC-2612 permits and standard ERC-20 approvals. Discover the full potential of Permit2 and how it revolutionizes token approvals in the [integration guide](https://blog.uniswap.org/permit2-integration-guide).

## [Bundler3 (deprecated)](#bundler3-deprecated)

[Bundler3](https://github.com/morpho-org/bundler3) - the general-purpose
`multicall` dispatcher with `GeneralAdapter1`, `ParaswapAdapter` and the
migration adapters - is deprecated. The Morpho interface and the Morpho SDK
(from v6) route every operation through Bundles, and new integrations should
do the same. Bundler3 deployments remain live and immutable, and their
addresses stay listed in the [addresses page](https://docs.morpho.org/developers/contracts/addresses/)
for existing integrators.

Bundles are protocol-specific by design. Flows that Bundler3 enabled through arbitrary call composition - DEX swaps and leverage via `ParaswapAdapter`, migrations from other lending protocols via the migration adapters, and Vault V1 `PublicAllocator` reallocations - have no Bundle equivalent today.

[Interest Rate Models

Previous Page

](https://docs.morpho.org/developers/contracts/irm/)[Universal Rewards Distributors (Deprecated)

Next Page

](https://docs.morpho.org/developers/contracts/rewards/)