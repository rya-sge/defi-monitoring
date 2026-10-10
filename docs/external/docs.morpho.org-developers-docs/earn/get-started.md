# Morpho Vaults for Earn products

> Source: https://docs.morpho.org/developers/earn/get-started

---

# Morpho Vaults for Earn products

Integrating Morpho Vaults (Earn) into your application means implementing the infrastructure that allows users to deposit assets into vaults built on top of Morpho's lending protocol.

For new Earn integrations on Morpho, [Morpho Vault V2](https://docs.morpho.org/learn/concepts/vault-v2/) is the recommended vault surface.

Users may receive variable yield from borrower-paid interest on their deposited assets, alongside incentives (rewards) from different rewards providers.

## [Key Components of Earn Integration](#key-components-of-earn-integration)

When building earn products with Morpho Vaults, you need to integrate three main components:

1. **Vault Operations**: Deposit, withdraw, and position management
2. **Yield Tracking**: Vault APY calculation and performance monitoring
3. **Rewards Integration**: Discovery, tracking, and claiming of additional incentives

Here is a quick visual for better understanding:

 
![Slide 1](https://docs.morpho.org/img/earn/Developers_Earn_MorphoVaultsforEarnPorducts_1_light.png)![Slide 2](https://docs.morpho.org/img/earn/Developers_Earn_MorphoVaultsforEarnPorducts_2_light.png)![Slide 3](https://docs.morpho.org/img/earn/Developers_Earn_MorphoVaultsforEarnPorducts_3_light.png)
Integrating Earn gives users access to:

1. **Configurable Risk Parameters**: Unlike traditional lending platforms where users are exposed to all assets in the pool, Morpho Vaults allow selective exposure to specific collateral types based on risk preferences.
2. **Permissionless Infrastructure**: Any entity (individual, DAO, protocol) can create and manage vaults with different risk parameters and allocation strategies.
3. **Non-Custodial Architecture**: All positions remain fully controlled by the user with transparent onchain verification of allocations and immutable vault logic.

## [Technical Components](#technical-components)

From a technical standpoint, integrating Earn involves:

1. **Vault Discovery and Display**: Implementing systems to discover available vaults, display their key metrics (APY, TVL, allocation breakdown), and present risk profiles to users.
2. **Transaction Handling**: Building the interface and backend support for deposit and withdrawal operations, including:

  - Asset approval workflows
  - Transaction status monitoring
  - Receipt confirmation and position updates
  - Rewards tracking updates
3. **Position Management**: Creating interfaces for users to:

  - View their current vault positions
  - Track historical performance
  - Monitor yield accrual
  - Perform deposits & withdrawals
  - Claim rewards
4. **Risk Transparency**: Building displays that clearly communicate:

  - Which Morpho markets the vault allocates to
  - Collateral types users are exposed to
  - Current utilization ratios
  - Current allocation strategy and any pending changes

## [Rewards Considerations](#rewards-considerations)

A complete Earn integration should include rewards functionality as one of the core components. Many Morpho Vaults earn additional incentives beyond base lending yield through reward campaigns.

Key aspects to integrate:

- **Rewards Discovery**: Identify available reward programs for vault depositors
- **Rewards Tracking**: Display accruing and claimable rewards in real-time
- **Claiming Process**: Implement claim functionality using Merkle-proof based distribution via Merkl
- **Multi-Token Support**: Handle various reward tokens from different reward providers
- **Program Awareness**: Display active campaigns and their respective parameters

For detailed implementation guidance, see the [Rewards integration guide](https://docs.morpho.org/developers/rewards/get-started/).

## [Assets Flow - Earn](#assets-flow---earn)

Understanding the complete flow of assets is crucial for proper integration:

![Vault V2 liquidity flow: deposits allocate to the liquidity adapter, withdrawals are served from idle then the liquidity adapter, forceDeallocate moves assets from other markets back to idle](https://docs.morpho.org/img/earn/vault-v2-liquidity-flow.png)

### [1. Deposit](#1-deposit)

- User deposits an asset (e.g., USDC, ETH) into a Morpho Vault
- User receives receipt tokens (ERC4626 tokens) representing their proportional ownership
- Vault V2 allocates the whole deposit to its configured **liquidity adapter** (an underlying market). The allocator then rebalances across the adapter's other markets, or other approved adapters, over time
- Today, the most common underlying yield source is Morpho market exposure routed through Morpho Vault V2 adapters
- These markets are permissionless pools containing a loan token (what was deposited) and a collateral token
- A deposit reverts when the liquidity adapter is at its cap. Read the vault's deposit ceiling with the SDK's `maxDeposit` rather than assuming deposits always succeed
- When no liquidity adapter is set, deposits stay in the vault's idle balance and are not subject to an allocation cap

### [2. Yield Generation](#2-yield-generation)

- Borrowers deposit collateral into Morpho Markets and borrow the loan token
- Borrowers pay interest on borrowed amounts
- This interest accrues to suppliers (the vault, in this case)
- The vault's receipt token price increases as interest accumulates, representing yield for depositors

### [3. Withdrawal Process](#3-withdrawal-process)

- Users can redeem their vault receipt tokens for the underlying asset at any time
- Vault V2 pays from idle assets first, then deallocates from its liquidity adapter. Those two sources are the only ones a plain `withdraw` or `redeem` can reach. When no liquidity adapter is set, idle is the only source
- Assets in other markets or adapters become withdrawable only after someone calls the permissionless `forceDeallocate`, which moves them back to idle and may burn a per-adapter penalty from the user. Integrations that batch `forceDeallocate` with the withdrawal can show a higher withdrawable maximum than those that do not. See [Support forceDeallocate withdrawals](https://docs.morpho.org/developers/earn/tutorials/force-deallocate/)
- Users receive their original deposit plus accrued yield (minus any performance or management fee)

## [Functional Integration Requirements](#functional-integration-requirements)

For a complete Earn integration, your system needs to implement:

1. **Read Operations**:

  - Query vault metadata (name, symbol, asset, curator, fees)
  - Fetch current APY and historical performance
  - Display current allocation across markets
  - Show user-specific position data
  - Present risk parameters of underlying markets
2. **Write Operations**:

  - Handle asset approvals
  - Execute deposits & withdrawals
  - Facilitate claiming any associated rewards
3. **Monitoring Capabilities**:

  - Track position changes
  - Alert users to significant vault parameter changes
  - Update yield information in real-time

## [Risk Considerations](#risk-considerations)

A complete Earn integration should help users understand:

1. **Smart Contract Risk**: Exposure to both Morpho and Vault contracts
2. **Market Risk**: Exposure to specific collateral types and their volatility
3. **Curator Risk**: Dependence on curator's technical configuration and ongoing parameter updates
4. **Liquidity Risk**: Potential for withdrawal delays during high utilization
5. **Oracle Risk**: Vulnerability to incorrect price feeds affecting underlying markets

By properly integrating these components, your application can offer users access to Morpho's capital-efficient lending infrastructure through a curated, simplified experience that abstracts away much of the complexity while maintaining transparency about underlying risks and operations.

[Resources

Previous Page

](https://docs.morpho.org/developers/midnight/resources/all/)[Vaults & ERC4626 Mechanics

Next Page

](https://docs.morpho.org/developers/earn/concepts/vault-mechanics/)