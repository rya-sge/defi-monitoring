# Integrating Morpho Rewards

> Source: https://docs.morpho.org/developers/rewards/get-started

---

# Integrating Morpho Rewards

Morpho's rewards system allows protocols, DAOs, and token issuers to incentivize specific behaviors on the Morpho protocol—such as supplying assets to vaults, supplying or borrowing loan assets in markets, or depositing collateral in markets. As an integrator, your role is to help users discover, track, and claim these rewards through your application.

## [Understanding the Rewards Ecosystem](#understanding-the-rewards-ecosystem)

Rewards on Morpho are distributed through **Merkl**.

**Migration Complete**

The rewards distribution has been fully migrated from the Morpho rewards stack (URD) to the Merkl stack following [MIP 111](https://snapshot.box/#/s:morpho.eth/proposal/0xadf3862d97cf4e8bb84a4b3d5117abe1a9db774e92ad97c65bde22214c0b76c9).

All new MORPHO rewards and third-party rewards are distributed via Merkl. For unclaimed historical rewards, users can visit [rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/).

**Important: Non-Claimable Addresses**

If you're interacting with Morpho through a smart contract or address that cannot claim rewards, please contact Merkl before depositing to have your rewards redirected.

Rewards allocated to addresses that cannot claim aren't recoverable or redirectable after the fact and will stay permanently unclaimable.

## [Merkl: The Current Standard](#merkl-the-current-standard)

[Merkl](https://merkl.xyz/) is a third-party rewards distribution platform that now handles Morpho ecosystem rewards. It offers:

- **Flexible distribution**: Rewards updated every 8 hours
- **Multi-protocol support**: Used across DeFi, not just Morpho
- **Automated calculations**: Offchain computation of eligible rewards
- **Standardized claiming**: Consistent API and claiming process

**When to use Merkl:**

- All new reward programs (July 2025 onwards)
- Third-party incentive programs
- Current MORPHO token distributions

## [Legacy Rewards (Pre-Merkl)](#legacy-rewards-pre-merkl)

The Universal Rewards Distributor (URD) was Morpho's previous rewards system. The `rewards.morpho.org` API has been deprecated.

Users with unclaimed historical rewards can look them up and claim via [rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/).

## [Who Should Integrate Rewards?](#who-should-integrate-rewards)

You should integrate rewards if you're building:

- **Earn Products**: Display additional APR from rewards alongside base vault yield
- **Borrow Products**: Show borrowers incentives for taking loans
- **Portfolio Dashboards**: Provide users with a complete view of their Morpho earnings
- **Aggregators**: Compare total yields (base + rewards) across protocols
- **Reward Platforms**: Create specialized UIs for rewards discovery and claiming

## [What You'll Need to Integrate](#what-youll-need-to-integrate)

A complete rewards integration involves three main components:

### [1. Rewards Discovery & Display](#1-rewards-discovery--display)

Fetch and display available rewards for vaults and markets:

- Query reward rates from Merkl API or Morpho API
- Calculate total APY (base yield + reward APR)
- Show reward token types and amounts
- Display program timelines and eligibility

### [2. User Balance Tracking](#2-user-balance-tracking)

Show users their accrued and claimable rewards:

- Fetch user-specific reward balances
- Display rewards by token and program
- Calculate USD values of rewards
- Update balances in real-time

### [3. Claiming Interface](#3-claiming-interface)

Enable users to claim their rewards:

- Support Merkl claim flow
- Handle transaction signing and confirmation
- Provide claim status feedback

## [Integration Paths](#integration-paths)

First, [Understand Reward Programs](https://docs.morpho.org/developers/rewards/concepts/reward-campaigns/) and learn the different program types.

Choose your integration approach based on your needs:

### [Quick Start (Display Only)](#quick-start-display-only)

Just want to show rewards APR alongside base yield? Start here:

1. [Fetch Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/) - Learn to query both APIs
2. [Integrate Display](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/) - Show rewards in your UI

### [Full Integration (Display + Claiming)](#full-integration-display--claiming)

Building a complete product? Follow this path:

1. [Merkl Distribution System](https://docs.morpho.org/developers/rewards/concepts/distribution-system/) - Understand Distribution
2. [Fetch Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/) - Query rewards information
3. [Claim Rewards](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/) - Implement claiming via Merkl

### [Creating Rewards (Issuers)](#creating-rewards-issuers)

Are you a protocol or DAO looking to create a rewards program?

1. [Create a Program](https://docs.morpho.org/developers/rewards/tutorials/create-program/) - Step-by-step program creation

## [Need Help?](#need-help)

- **Technical Support**: Visit [help.morpho.org](https://help.morpho.org)
- **Merkl Support**: Reach out via [Merkl's documentation](https://docs.merkl.xyz/)

[Resources

Previous Page

](https://docs.morpho.org/developers/borrow/resources/all/)[Reward Campaigns on Morpho

Next Page

](https://docs.morpho.org/developers/rewards/concepts/reward-campaigns/)