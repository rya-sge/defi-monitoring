# Integrate Rewards for Earn Products

> Source: https://docs.morpho.org/developers/earn/tutorials/rewards

---

# Integrate Rewards for Earn Products

Vault depositors on Morpho can earn rewards beyond base lending yield. Integrating rewards display and claiming is essential for providing competitive APY and maximizing user returns.

## [What's Unique for Earn Products](#whats-unique-for-earn-products)

When building earn products, understand that vault depositors earn rewards from **two sources**:

1. **Direct Vault Campaigns**: Rewards distributed directly to vault depositors
2. **Forwarded Market Campaigns**: Rewards from underlying markets where the vault allocates liquidity

**Critical integration requirement:**

```
Net APY = Native Vault APY + Vault Campaign APR + Forwarded Market Campaign APR - Performance Fee - Management Fee
```

## [Integration Steps](#integration-steps)

Follow the centralized rewards tutorials with vault-specific considerations:

### [Step 1: Fetch Vault Rewards Data](#step-1-fetch-vault-rewards-data)

**Follow:** [Fetch Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/)

**Vault-specific notes:**

- Query both `state.allRewards` and `state.allocation[].market.state.rewards`
- Calculate weighted average for market rewards based on allocation
- Use `supplyAssetsUsd` to determine weights
- Alternatively, use `netApy` convenience field for simple total APY

### [Step 2: Display Rewards in Your UI](#step-2-display-rewards-in-your-ui)

**Follow:** [Integrate Rewards Display](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/)

**Vault-specific notes:**

- Prominently display Net APY (native + all rewards)
- Show breakdown: base yield vs. rewards
- List reward tokens with their respective APRs
- Optionally show which markets contribute to forwarded rewards

### [Step 3: Enable Reward Claiming](#step-3-enable-reward-claiming)

**Follow:** [Claim Rewards](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/)

**Important:** The claiming process is **identical** for all Morpho users (vault depositors, borrowers, market suppliers). Merkl handles all reward claims.

## [Quick Reference](#quick-reference)

| Task | Main Tutorial | Vault-Specific Consideration |
| --- | --- | --- |
| **Understanding rewards** | [Reward Campaigns](https://docs.morpho.org/developers/rewards/concepts/reward-campaigns/) | Understand forwarding mechanism |
| **Distribution system** | [Distribution Systems](https://docs.morpho.org/developers/rewards/concepts/distribution-system/) | Merkl for all users |
| **Fetch rewards** | [Fetch Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/) | Query two API locations, manual aggregation |
| **Display rewards** | [Integrate Display](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/) | Show total APY breakdown |
| **Claim rewards** | [Claim Rewards](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/) | Same process for all users |

## [Need Help?](#need-help)

- **Conceptual questions**: [Rewards for Lenders Concept](https://docs.morpho.org/developers/earn/concepts/rewards/)
- **Main rewards guide**: [Rewards Integration Guide](https://docs.morpho.org/developers/rewards/get-started/)
- **Technical support**: [help.morpho.org](https://help.morpho.org)

[Get Data

Previous Page

](https://docs.morpho.org/developers/earn/tutorials/get-data/)[UX Requirements

Next Page

](https://docs.morpho.org/developers/earn/vault-ux/ux-requirement/)