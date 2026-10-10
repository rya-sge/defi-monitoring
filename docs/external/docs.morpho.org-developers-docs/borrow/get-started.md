# Morpho Variable Rate Markets for Borrow products

> Source: https://docs.morpho.org/developers/borrow/get-started

---

# Morpho Variable Rate Markets for Borrow products

Integrating Morpho Variable Rate Markets (Borrow) into your application means implementing the infrastructure that allows users to supply collateral and borrow assets directly from isolated lending markets.

Users will pay a borrow rate on their borrowed assets and may receive incentives (rewards). A critical part of a borrow integration is facilitating the monitoring of position health to help users avoid **liquidation**, where their collateral can be seized to repay their debt.

Note:
Borrowers will see interests accruing in their debt position, while the collateral remains idle, and do not yield.

## [Key Components of Borrow Integration](#key-components-of-borrow-integration)

When building borrow products with Morpho Markets, you need to integrate three main components:

1. **Market Operations**: Supplying collateral, borrowing, repaying, and withdrawing collateral.
2. **Position Health Management**: Real-time tracking of Loan-to-Value (LTV), Health Factor, and liquidation risk.
3. **Rewards Integration**: Discovery and claiming of incentives for supplying collateral or borrowing.

Integrating Borrow gives users access to:

1. **Isolated Risk**: Each market's risk is contained. A problem in one market (e.g., a volatile collateral asset) does not affect the solvency of any other market.
2. **Capital Efficiency**: The underlying interest rate models are designed for high utilization, which translates to better rates for both borrowers and lenders.
3. **Deep Liquidity via Public Allocator**: While markets are isolated, the [Vault V2 Public Allocator](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/) enables liquidity to flow between them on demand, ensuring borrowers can access deep liquidity from a single market. Read [Shared Liquidity](https://docs.morpho.org/developers/borrow/concepts/shared-liquidity/) before following the SDK tutorial.

## [Technical Components](#technical-components)

From a technical standpoint, integrating Borrow involves:

1. **Market Discovery and Display**: Implementing systems to discover available markets and display their key parameters (Collateral/Loan Asset, APYs, TVL, LLTV, Oracle, IRM).
2. **Transaction Handling**: Building the interface and backend support, including asset approvals, transaction monitoring, and position updates. Here are the four core market operations:

  - `supplyCollateral`
  - `borrow`
  - `repay`
  - `withdrawCollateral`
3. **Position Management**: Creating interfaces for users to:

  - View their current collateral and debt balances.
  - Clearly track their **Health Factor** and current LTV.
  - Perform any of the four core market operations.
  - Claim any available rewards.
4. **Liquidation Risk Transparency**: Building clear and prominent displays that communicate:

  - The user's current Health Factor.
  - The market's Liquidation Loan-to-Value (LLTV), which is the LTV at which liquidation can occur.
  - Visual warnings when a user's position health is declining.

## [Rewards Considerations](#rewards-considerations)

A complete Borrow integration should include rewards functionality. Many markets offer incentives for both borrowers and collateral suppliers through reward campaigns.

Key aspects to integrate:

- **Rewards Discovery**: Identify available reward programs for borrowers and collateral suppliers
- **Rewards Tracking**: Display accruing and claimable rewards in real-time
- **Claiming Process**: Implement claim functionality using Merkle-proof based distribution via Merkl
- **Multi-Token Support**: Handle various reward tokens from different incentive programs
- **Program Awareness**: Display active campaigns and their respective parameters

For detailed implementation guidance, see the [Rewards integration guide](https://docs.morpho.org/developers/rewards/get-started/).

## [Assets Flow - Borrow](#assets-flow---borrow)

Understanding the complete flow of assets is crucial for a proper integration:

### [1. Supply Collateral](#1-supply-collateral)

- A user selects a market (e.g., wstETH/WETH).
- They supply a collateral asset (wstETH) to the market. This collateral secures their future debt.

### [2. Borrow](#2-borrow)

- The user borrows the loan asset (WETH) from the same market.
- The amount they can borrow is limited by the value of their collateral and the market's Liquidation Loan-to-Value (LLTV).
- The user's **Health Factor** is established, representing their position's safety from liquidation.

### [3. Repay](#3-repay)

- The user repays the loan asset (WETH), either partially or in full.
- Repaying debt reduces their LTV and increases their Health Factor, making their position safer.
- Interest continuously accrues on the outstanding debt, which must also be repaid.

### [4. Withdraw Collateral](#4-withdraw-collateral)

- After repaying debt, the user can withdraw their collateral.
- They can only withdraw collateral if their position remains healthy (i.e., their Health Factor stays above 1). If the user has fully repaid their debt, they can withdraw all of their collateral.

## [Functional Integration Requirements](#functional-integration-requirements)

For a complete Borrow integration, your system needs to implement:

1. **Read Operations**:

  - Query market parameters (LLTV, oracle, irm, etc.).
  - Fetch real-time market state (APYs, total supply/borrow, utilization).
  - Display user-specific position data (collateral, debt, **Health Factor**).
  - Present available liquidity, including reallocatable liquidity from the Public Allocator; read [Shared Liquidity](https://docs.morpho.org/developers/borrow/concepts/shared-liquidity/) and use the [SDK tutorial](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/) to integrate it.
2. **Write Operations**:

  - Handle token approvals for supplying collateral and repaying debt.
  - Execute `supplyCollateral`, `borrow`, `repay`, and `withdrawCollateral`.
  - Facilitate claiming any associated rewards.
3. **Monitoring Capabilities**:

  - Track position Health Factor changes in real-time.
  - Alert users when their position approaches the liquidation threshold.
  - Update market data and interest rates dynamically.

## [Risk Considerations](#risk-considerations)

A responsible Borrow integration must clearly communicate the following risks to the user:

1. **Liquidation Risk**: This is the primary risk for borrowers. If a position's Health Factor drops below 1, their collateral can be seized by liquidators, resulting in a loss of assets.
2. **Oracle Risk**: Inaccurate or manipulated price feeds from the market's oracle can lead to premature liquidations or prevent timely ones, causing bad debt.
3. **Smart Contract Risk**: Exposure to vulnerabilities in the Morpho core contracts.
4. **Market Liquidity Risk**: Low liquidity in a market can prevent users from borrowing or impact interest rates significantly.
5. **Counterparty Risk**: The risk associated with the assets themselves (e.g., de-pegging of a stablecoin or centralization risk of a token).

By properly integrating these components and transparently communicating risks, your application can offer users direct access to Morpho's efficient and secure lending markets.

## [UX Requirements](#ux-requirements)

When building a Borrow product on Morpho, you must follow these UX requirements to help users understand what they're interacting with and ensure a transparent experience.

### [Attribution](#attribution)

You must include a "Powered by Morpho" mention in your interface, for example in the footer or near the borrow product section. This helps users identify the underlying protocol and builds trust in the infrastructure behind your product. See [Brand Assets](https://brand.morpho.org/) for official logos and usage guidelines.

### [User Disclaimer](#user-disclaimer)

You must display the following notice to end users at least the first time they interact with the protocol through your app, ideally with a checkbox confirmation before they proceed.

Replace **[Your App]** with your application's name before displaying this notice:

> Accessing the Morpho Protocol through this app is governed by **[Your App]**'s Terms of Use and [Morpho's Disclaimer](https://morpho.org/disclaimers/). By using it, you acknowledge that you have read and understood these terms and the risks involved.

[Resources

Previous Page

](https://docs.morpho.org/developers/earn/resources/all/)[Market Mechanics

Next Page

](https://docs.morpho.org/developers/borrow/concepts/market-mechanics/)