# Merkl Distribution System

> Source: https://docs.morpho.org/developers/rewards/concepts/distribution-system

---

# Merkl Distribution System

[Merkl](https://merkl.xyz/) is a third-party rewards distribution platform that has become the standard for Morpho rewards following [MIP 111](https://snapshot.box/#/s:morpho.eth/proposal/0xadf3862d97cf4e8bb84a4b3d5117abe1a9db774e92ad97c65bde22214c0b76c9).

## [How Merkl Works](#how-merkl-works)

### [Offchain Computation](#offchain-computation)

Merkl's infrastructure continuously monitors onchain activity and calculates earned rewards:

- Monitors onchain activity directly via RPC nodes
- Proprietary indexing infrastructure
- Real-time event processing

This is necessary because:

1. **Complex logic**: Reward calculations involve historical data, forwarding, and blacklisting
2. **Gas efficiency**: Computing onchain would be prohibitively expensive
3. **Flexibility**: Allows for sophisticated distribution strategies

### [Merkle Tree Generation & Onchain Distribution](#merkle-tree-generation--onchain-distribution)

Every 8 hours, Merkl generates a new Merkle tree containing all claimable rewards. The Merkle root is posted onchain, making rewards claimable.

- Rewards are recalculated every 8 hours
- Users see their accruing rewards in near real-time

### [User Claims](#user-claims)

Users can claim their rewards by submitting a transaction with their Merkle proof.

- Low waiting period between earning and claiming

## [Key Characteristics](#key-characteristics)

**Standardized Integration**

- Consistent API across all protocols using Merkl
- Well-documented claiming process
- Community-supported SDKs and tools

**Multi-Protocol Support**

- Same infrastructure used by many DeFi protocols
- Familiar UX for users who've claimed rewards elsewhere
- Centralized infrastructure for reward discovery

## [When to Use](#when-to-use)

Integrate Merkl for:

- All new reward programs (July 2025 onwards)
- Current MORPHO token distributions
- Third-party incentive programs
- Real-time reward tracking

## [Integration Points](#integration-points)

**For Claiming Rewards:** head to the [Integrate Rewards Claim](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/) section.

**For Displaying Rewards:** head to the [Integrate Rewards Display](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/) section.

[Reward Campaigns on Morpho

Previous Page

](https://docs.morpho.org/developers/rewards/concepts/reward-campaigns/)[Create a Rewards Program

Next Page

](https://docs.morpho.org/developers/rewards/tutorials/create-program/)