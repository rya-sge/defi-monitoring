# Rewards for Lenders

> Source: https://docs.morpho.org/developers/earn/concepts/rewards

---

# Rewards for Lenders

Vault depositors on Morpho can earn additional rewards beyond base lending yield through incentive campaigns. These rewards significantly enhance total returns and are a key feature of competitive earn products.

## [Overview](#overview)

When you deposit into a Morpho Vault, you can earn rewards from **two distinct sources**:

1. **Direct Vault Campaigns**: Rewards distributed directly to vault depositors. Morpho Vault V2 can also surface rewards forwarded from its underlying allocations when campaigns are configured to flow through to end users (see [reward forwarding](https://docs.morpho.org/developers/rewards/concepts/reward-campaigns/#reward-forwarding)).
2. **Forwarded Market Campaigns**: Rewards earned from underlying markets where the vault allocates liquidity

The total yield a depositor may earn combines the native lending APY with reward APR from both sources:

```
Net APY = Native Vault APY + Vault Campaign APR + Forwarded Market Campaign APR - Performance Fee - Management Fee
```

## [What Makes Vault Rewards Unique](#what-makes-vault-rewards-unique)

### [Reward Forwarding](#reward-forwarding)

This is the key differentiator for vault depositors. When a vault allocates liquidity to underlying variable rate markets that have active supply campaigns, those market-level rewards are **automatically forwarded** to vault depositors.

**How it works:**

1. A market has an active supply campaign
2. Your vault allocates liquidity to that market as a supplier
3. The vault contract earns those market rewards
4. Rewards are attributed to individual vault depositors by Merkl's offchain computation
5. You claim these forwarded rewards directly

**Why this matters:**

- You benefit from active campaigns across the markets your vault uses
- Vault curators optimize allocations, and you receive rewards automatically
- More capital-efficient than directly supplying to individual markets

### [Complete APY Components](#complete-apy-components)

The net APY shown to users combines multiple components:

```
Net APY = Native Vault APY + Rewards APR - Performance Fee - Management Fee
```

Where:

- **Native Vault APY**: Native vault yield before fees and rewards
- **Rewards APR**: Vault rewards + weighted market rewards
- **Performance Fee**: Applied only to base APY
- **Management Fee**: Applied to total assets deposited in the vault

## [Distribution System](#distribution-system)

Rewards distribution has migrated from the Morpho URD system to Merkl. All campaigns from July 2025 onwards use Merkl exclusively. For unclaimed historical rewards, visit [rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/).

The claiming process is **identical** for all Morpho users, regardless of whether they're depositors or borrowers.

**For complete details on distribution systems, see:**

- [Reward Campaigns](https://docs.morpho.org/developers/rewards/concepts/reward-campaigns/)
- [Distribution System](https://docs.morpho.org/developers/rewards/concepts/distribution-system/)

## [Learn More](#learn-more)

For comprehensive information about integrating rewards:

- **[Rewards Integration Guide](https://docs.morpho.org/developers/rewards/get-started/)**: Complete overview and integration paths
- **[Fetch Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/)**: Complete API queries and calculations
- **[Claim Rewards](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/)**: Claim implementation via Merkl
- **[Integrate Display](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/)**: UI/UX best practices

## [Implementation](#implementation)

For practical implementation guidance specific to earn products, see:

- [Integrate Rewards for Earn Products](https://docs.morpho.org/developers/earn/tutorials/rewards/)

[Yield & Fees

Previous Page

](https://docs.morpho.org/developers/earn/concepts/yield-fees/)[How can distributors generate revenue on Morpho?

Next Page

](https://docs.morpho.org/developers/earn/concepts/generate-revenue/)