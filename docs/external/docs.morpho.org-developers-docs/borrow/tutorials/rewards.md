# Integrate Rewards for Borrow Products

> Source: https://docs.morpho.org/developers/borrow/tutorials/rewards

---

# Integrate Rewards for Borrow Products

Borrowers on Morpho Markets can earn rewards that offset borrowing costs or even generate net positive yields. Integrating rewards display and claiming is essential for showing users their true cost of borrowing.

## [What's Unique for Borrow Products](#whats-unique-for-borrow-products)

When building borrow products, understand that borrowers earn rewards for borrowing an asset from a market

**Critical integration requirement:**

```
Net Borrow APY = Borrow APY - Borrow Rewards APR
```

It is also possible to incentivize a simple collateral deposit (without the borrow action required).

When rewards exceed costs, net APY becomes negative (profitable borrowing).

Rewards are claimable on the side via the Merkl distribution system and do not impact user LTV. Even though the Net Borrow APY can be negative, user loan will increase and so its LTV.

## [Integration Steps](#integration-steps)

Follow the centralized rewards tutorials with borrow-specific considerations:

### [Step 1: Fetch Market Rewards Data](#step-1-fetch-market-rewards-data)

**Follow:** [Fetch Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/)

**Borrow-specific notes:**

- Query `state.rewards` on market object
- Look for `borrowApr` (rewards for borrowing)
- No weighted averaging needed (unlike vaults)

### [Step 2: Display Rewards in Your UI](#step-2-display-rewards-in-your-ui)

**Follow:** [Integrate Rewards Display](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/)

**Borrow-specific notes:**

- Show **net cost** prominently (borrow cost - all rewards)
- Highlight when borrowing becomes profitable (negative net APY)
- Break down: borrow cost, borrow rewards
- List reward tokens with their respective APRs
- Calculate per-position rewards based on user amounts

### [Step 3: Enable Reward Claiming](#step-3-enable-reward-claiming)

**Follow:** [Claim Rewards](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/)

**Important:** The claiming process is **identical** for all Morpho users (borrowers, vault depositors, market suppliers).

## [Quick Reference](#quick-reference)

| Task | Main Tutorial | Borrow-Specific Consideration |
| --- | --- | --- |
| **Understanding rewards** | [Reward Campaigns](https://docs.morpho.org/developers/rewards/concepts/reward-campaigns/) | Understand dual eligibility |
| **Distribution system** | [Distribution System](https://docs.morpho.org/developers/rewards/concepts/distribution-system/) | Same for all users |
| **Fetch rewards** | [Fetch Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/) | Query single location, no aggregation |
| **Display rewards** | [Integrate Display](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/) | Show net cost after rewards |
| **Claim rewards** | [Claim Rewards](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/) | Same process for all users |

## [Need Help?](#need-help)

- **Conceptual questions**: [Rewards for Borrowers Concept](https://docs.morpho.org/developers/borrow/concepts/rewards/)
- **Main rewards guide**: [Rewards Integration Guide](https://docs.morpho.org/developers/rewards/get-started/)
- **Technical support**: [help.morpho.org](https://help.morpho.org)

[Vault V2 Public Allocator

Build a Vault V2 reallocation snapshot, plan shared liquidity, and attach it to a Morpho Blue action.

](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/)[Guide: How to Monetize Your Borrow Product

Next Page

](https://docs.morpho.org/developers/borrow/guides/monetize-borrow-product/)