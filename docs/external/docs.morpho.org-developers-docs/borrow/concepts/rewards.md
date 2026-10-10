# Rewards for Borrowers

> Source: https://docs.morpho.org/developers/borrow/concepts/rewards

---

# Rewards for Borrowers

Borrowers on Morpho Markets can earn rewards that offset borrowing costs or even generate net positive yields. These incentives are designed to bootstrap markets, attract liquidity, and encourage specific borrowing behaviors.

## [Overview](#overview)

As a borrower on Morpho, you can earn rewards for borrowing an asset from a market.

**Net Cost Calculation:**

```
Net Borrow APY = Borrow APY - Borrow Rewards APR
```

It is also possible to incentivize a simple collateral deposit (without the borrow action required).

In favorable conditions, rewards can exceed borrow costs, resulting in **negative net APY** (borrowers earn while borrowing).

Rewards are claimable on the side via the Merkl distribution system and do not impact user LTV. Even though the Net Borrow APY can be negative, user loan will increase and so its LTV.

**Borrow Rewards:**

- Incentives for borrowing an asset
- Accrue based on outstanding borrow balance
- Offset borrowing costs directly

### [Net Cost Display Priority](#net-cost-display-priority)

For borrow products, users care most about **net cost after all rewards**:

- Display net APY prominently
- Highlight when borrowing becomes profitable (negative net APY)
- Show breakdown: borrow cost - borrow rewards

## [Distribution System](#distribution-system)

All Morpho rewards are distributed through **Merkl**, which updates every 8 hours and handles all active programs.

If you have unclaimed rewards from historical Morpho programs (pre-Merkl migration), claim them via [rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/).

The claiming process is **identical** for all Morpho users, regardless of whether they're depositors, borrowers, or collateral suppliers.

**For complete details on distribution systems, see:**

- [Distribution System](https://docs.morpho.org/developers/rewards/concepts/distribution-system/)
- [Reward Campaigns](https://docs.morpho.org/developers/rewards/concepts/reward-campaigns/)

## [Learn More](#learn-more)

For comprehensive information about integrating rewards:

- **[Rewards Integration Guide](https://docs.morpho.org/developers/rewards/get-started/)**: Complete overview and integration paths
- **[Fetch Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/)**: Complete API queries and calculations
- **[Claim Rewards](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/)**: Claim implementation via Merkl
- **[Integrate Display](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/)**: UI/UX best practices

## [Implementation](#implementation)

For practical implementation guidance specific to borrow products, see:

- [Integrate Rewards for Borrow Products](https://docs.morpho.org/developers/borrow/tutorials/rewards/)

[Liquidation

Previous Page

](https://docs.morpho.org/developers/borrow/concepts/liquidation/)[Supply Collateral, Borrow, Repay & Withdraw Collateral

Next Page

](https://docs.morpho.org/developers/borrow/tutorials/assets-flow/)