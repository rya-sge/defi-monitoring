# Reward Campaigns on Morpho

> Source: https://docs.morpho.org/developers/rewards/concepts/reward-campaigns

---

# Reward Campaigns on Morpho

Reward campaigns are incentive strategies created via [Merkl](https://merkl.xyz/) to encourage specific user behaviors within the Morpho protocol. Understanding how these campaigns work and the different distribution strategies available is essential for integrators who want to accurately display and calculate reward rates for their users.

## [What Are Reward Campaigns?](#what-are-reward-campaigns)

Merkl allows protocols, DAOs, and token issuers to **reward users for providing active liquidity** on Morpho. Campaigns incentivize users who hold supply, borrow, or collateral balances on the protocol. Rewards are distributed automatically based on users' positions over time.

When creating a campaign through Merkl's interface, you select:

- The lending market or vault you want to incentivize
- The reward token to distribute
- The campaign duration and reward budget
- The specific user behavior to reward (supply, borrow, or collateral deposit)

It is also possible to incentivize a simple collateral deposit (without the borrow action required).

## [Distribution Strategies](#distribution-strategies)

Merkl offers two main categories of reward distribution for Morpho:

1. **Vault-Level Incentives** - Target deposits into specific Morpho Vaults
2. **Market-Level Incentives** - Target activity within Morpho Markets

### [Vault-Level Incentives](#vault-level-incentives)

**Strategy: Supply to a Morpho Vault**

This strategy incentivizes users who deposit assets into a specific Morpho Vault. It's the simplest distribution method, rewarding vault depositors proportionally based on their share of total vault deposits over time.

**How it works:**

- Rewards are distributed linearly over the campaign duration
- Users earn rewards based on their vault deposit amount and duration
- All depositors into the targeted vault are eligible
- Only one reward rate applies (vault supply rewards)

**Use cases:**

- Bootstrap a new vault to attract initial liquidity
- Increase deposits into an established vault
- Provide additional yield to vault depositors beyond base APY

### [Market-Level Incentives](#market-level-incentives)

**Strategy: Incentivize Activity in Morpho Variable Rate Markets**

Market-level strategies provide more granular control, allowing you to target specific behaviors within Morpho Variable Rate Markets. You can incentivize:

- **Supply**: Reward users who lend assets to a market
- **Borrow**: Reward users who borrow assets from a market
- **Collateral**: Reward users who deposit collateral in a market, without requiring them to borrow

Additionally, you can choose between:

- **Specific market targeting**: Incentivize activity in one particular market
- **Token-based targeting**: Incentivize use of a specific token across all markets

**Distribution Options:**

1. **Supply to a specific market**: Rewards users who supply assets to a particular Morpho Variable Rate Market.
2. **Supply a token to any market**: Rewards users who supply a specific token across all Morpho variable rate markets (e.g., all markets where USDC is the loan asset).
3. **Borrow from a specific market**: Rewards users who borrow assets from a particular Morpho Variable Rate Market.
4. **Borrow a token from any market**: Rewards users who borrow a specific token across all Morpho Variable Rate Markets.
5. **Deposit collateral in a specific market**: Rewards users who deposit collateral in a particular Morpho Variable Rate Market, without requiring a borrow position.
6. **Deposit a token as collateral in any market**: Rewards users who deposit a specific token as collateral across all Morpho Variable Rate Markets, without requiring a borrow position.

**How it works:**

- Campaigns distribute rewards linearly over a defined period
- Each campaign can have separate rates for supply, borrow, and collateral deposits
- Users earn rewards based on their position size and duration
- Rates are expressed as annualized amounts per token

**Use cases:**

- Bootstrap a new market by incentivizing early suppliers or borrowers
- Encourage borrowing to increase market utilization
- Reward specific collateral types to diversify market risk
- Create token-wide incentives across the entire Morpho ecosystem

## [Combining Multiple Campaigns](#combining-multiple-campaigns)

Merkl API provides an APR for each campaign (vault and market ones).

Vault depositors may be eligible for rewards from **multiple campaigns simultaneously**:

1. **Direct vault-level rewards**: From campaigns directly targeting the vault
2. **Forwarded market-level rewards**: From campaigns targeting markets where the vault allocates liquidity

**Net Vault APY:**

```
Net APY = Native Vault APY + Vault Campaign APR + Σ(Forwarded Market Campaign APR) - Performance Fee - Management Fee
```

Where:

- **Native Vault APY**: Native lending yield from the vault's market allocations
- **Vault Campaign APR**: Direct vault-level incentives
- **Forwarded Market Campaign APR**: Sum of all market-level rewards from allocated markets
- **Performance Fee**: Applied only to base APY
- **Management Fee**: Applied to total assets deposited in the vault

## [Reward Forwarding](#reward-forwarding)

One of the most important features of Morpho's reward system is **automatic reward forwarding** for vault depositors.

### [How Forwarding Works](#how-forwarding-works)

When a Morpho Vault allocates liquidity to a market with an active supply campaign, the vault itself technically earns those rewards (since it's the direct supplier to the market). However, these rewards are **automatically forwarded to individual vault depositors** proportionally to their vault shares.

**The forwarding mechanism:**

1. Market-level supply campaigns distribute rewards to suppliers
2. Vaults that supply to these markets earn rewards at the vault contract level
3. Merkl's offchain computation attributes these rewards to individual vault depositors
4. Vault depositors can claim these market-level rewards directly

This happens transparently in the background, ensuring that:

- Vault depositors benefit from all market-level campaigns
- No manual intervention is required
- Rewards are distributed fairly based on deposit amounts and duration

Forwarding works for Morpho Vault V2 when its underlying allocations are connected to eligible reward campaigns. See [Forwarded vault rewards](https://docs.morpho.org/developers/rewards/tutorials/create-program/#forwarded-vault-rewards) for the allocations the Morpho API forwards.

### [Integration Considerations](#integration-considerations)

As an integrator, you should display:

- **Direct vault campaigns**: Campaigns explicitly targeting the vault
- **Forwarded market campaigns**: Campaigns targeting markets where the vault allocates, with rewards forwarded to depositors
- **Combined APR**: Total reward APR from both sources

Users expect to see the full picture of their potential earnings, including both direct and forwarded rewards.

## [Blacklisting](#blacklisting)

Campaign creators can **blacklist specific addresses** from earning rewards. This is commonly used to:

- Prevent self-incentivization when protocols bootstrap their own markets
- Exclude treasury addresses that provide initial liquidity
- Remove addresses that don't align with campaign goals

**Example:**
If a protocol creates a market and deposits its treasury to provide initial liquidity, it can blacklist its treasury address. This ensures:

- Reward budget goes entirely to external users
- No circular incentive flow
- Fair distribution among community participants

Blacklisting is configured when creating the campaign and is enforced during rewards computation. It's transparent-anyone can verify which addresses are excluded from a campaign.

## [Historical Context: Legacy Reward Systems](#historical-context-legacy-reward-systems)

**Historical Note**

Prior to July 2025, Morpho used a native rewards distribution system (the Universal Rewards Distributor or URD) with different program types called "Market Programs" and "Vault Programs."

The `rewards.morpho.org` API has been deprecated. Users with unclaimed legacy rewards can look them up and claim via [rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/).

## [Querying Active Campaigns](#querying-active-campaigns)

You can see how to retrieve campaigns data in the [Fetch Rewards Data section](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/).

The Morpho API returns only campaigns that meet the [conditions for display on Morpho](https://docs.morpho.org/developers/rewards/tutorials/create-program/#campaigns-displayed-by-morpho).

## [Next Steps](#next-steps)

- **Create campaigns**: Follow the [Create a Rewards Program tutorial](https://docs.morpho.org/developers/rewards/tutorials/create-program/)
- **Understand distribution**: Read about [Distribution System](https://docs.morpho.org/developers/rewards/concepts/distribution-system/)
- **Fetch data**: Follow the [Fetch Rewards Data tutorial](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/)
- **Display rewards**: See the [Integrate Display tutorial](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/)

[Get Started

Previous Page

](https://docs.morpho.org/developers/rewards/get-started/)[Merkl Distribution System

Next Page

](https://docs.morpho.org/developers/rewards/concepts/distribution-system/)