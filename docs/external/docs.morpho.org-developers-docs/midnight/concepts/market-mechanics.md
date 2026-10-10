# Market Mechanics

> Source: https://docs.morpho.org/developers/midnight/concepts/market-mechanics

---

# Market Mechanics

## [Markets & Units](#markets--units)

Every Midnight market is defined at creation by an immutable set of parameters: a **chain ID**, **loan token**, **maturity date**, accepted **collateral assets** (with oracles and LLTVs), and optional **gates**. Once created, these parameters never change. Markets are permissionless, which means anyone can create one. Understanding how a market is defined is essential before reading balances or constructing offers.

### [Market immutable configuration](#market-immutable-configuration)

`GET /v0/midnight/markets/{market-id}`

```
GET /v0/midnight/markets/{marketId}

// Response excerpt (other fields omitted; values are illustrative)
{
  "data": {
    "chain_id":       8453,
    "market_id":      "0xd92de5e7fbb...7614",
    "loan_token":     "0x8335...2913",                 // USDC
    "maturity":       1798761600,                    // Dec 31, 2026
    "collaterals": [
      {
        "token":   "0x4200...0006",                    // wETH
        "lltv":    "860000000000000000",               // 0.86 → 86% LLTV
        "liquidation_cursor": "250000000000000000",
        "oracle":  "0x1234...abcd"
      },
      {
        "token":   "0xcbBT...1234",                    // cbBTC
        "lltv":    "770000000000000000",               // 0.77 → 77% LLTV
        "liquidation_cursor": "340000000000000000",
        "oracle":  "0x5678...ef01"
      },
      {
        "token":   "0xwstE...5678",                    // wstETH
        "lltv":    "860000000000000000",               // 0.86 → 86% LLTV
        "liquidation_cursor": "240000000000000000",
        "oracle":  "0x9abc...2345"
      }
    ],
    "enter_gate":      "0x0000...0000",                // no enter gate
    "liquidator_gate": "0x0000...0000"                 // no liquidator gate
  }
}
```

### [Market live state](#market-live-state)

To fetch the market’s current state (i.e. settlement fee, total units), use the following endpoint:

`GET /v0/midnight/markets/{market-id}/state`

```
GET /v0/midnight/markets/{marketId}/state

// Response excerpt (other fields omitted; values are illustrative)
{
  "data": {
    "chain_id":         8453,
    "market_id":        "0xd92de5e7fbb...7614",
    "total_units":      "85000000000",                 // total units outstanding
    "tick_granularity":  1,                            // valid ticks must be multiples of this

    "settlement_fee_schedule": [                       // settlement fee by time-to-maturity
      { "time_to_maturity_days": 0,   "fee_cbp": "0" },
      { "time_to_maturity_days": 1,   "fee_cbp": "50" },
      { "time_to_maturity_days": 7,   "fee_cbp": "150" },
      { "time_to_maturity_days": 30,  "fee_cbp": "400" },
      { "time_to_maturity_days": 90,  "fee_cbp": "800" },
      { "time_to_maturity_days": 180, "fee_cbp": "1200" },
      { "time_to_maturity_days": 360, "fee_cbp": "2000" }
    ],
    "current_settlement_fee_cbp": "743.5",             // interpolated for current TTM
    "current_settlement_fee_wad": "7435000000000",     // same, WAD-scaled
    "continuous_fee_rate":        "158549000",         // per-second ongoing fee (WAD)

    "last_indexed_block": "47457420"
  }
}
```

## [Credit and debt units](#credit-and-debt-units)

Within a market, all positions are denominated in **units**. These units have a fixed payoff structure analogous to that of zero-coupon obligations, representing credit for lenders and debt for borrowers.

- 1 credit unit = a claim on 1 loan token at maturity (held by lenders)

  - You buy units → your credit increases → Withdraw 1:1 once loan tokens are available: at or after maturity, or earlier after repayments or liquidations
- 1 debt unit = an obligation to repay 1 loan token (held by borrowers)

  - You sell units → your debt increases → Before maturity, repay to close

To list a user's position in a market use the following endpoint:
`GET /v0/midnight/users/{user-address}/positions`

```
GET /v0/midnight/users/{addr}/positions?market_ids=0xd92de5e7fbb...7614

// Response excerpt (other fields omitted; values are illustrative)
{
  "data": [
    {
      "chain_id":          8453,
      "market_id":         "0xd92de5e7fbb...7614",
      "user_address":      "0xYourAddress...",
      "loan_token":        "0x8335...2913",               // USDC
      "maturity":          1798761600,                  // Dec 31, 2026
      "type":              "lend",                        // lend | borrow | collateral_only

      // Position state
      "credit":            "10500000000",                 // 10,500 units → 10,500 USDC at maturity
      "debt":              "0",                           // no debt (this is a lend position)
      "pending_fee":       "12000",                       // continuous fee accrued but not yet deducted from credit
      "loss_factor":       "0",                           // current market loss factor (bad debt)
      "last_loss_factor":  "0",                           // loss_factor already applied to this returned position
      "collaterals":       [],                            // lenders don't post collateral

      // Performance is inline on this list; detail has a separate performance endpoint
      "cost_basis":        "10000000000000000000000",       // cost basis in loan-token units (WAD-scaled)
      "effective_rate_wad": "52000000000000000"           // 5.2% annualized
    }
  ]
}
```

## [How rate emerges from price](#how-rate-emerges-from-price)

Units always settle at 1:1 with the loan token at maturity. If you buy a unit for price `P` (where P<1), you earn the difference. The implied simple rate over the remaining term is `1 / P - 1`.

Example: Buy a unit at P = 0.95 with 6 months to maturity:

```
rate = 1 / P − 1
     = 1 / 0.95 − 1
     = 0.0526  // → 5.26% over the remaining term
     // → ~10.5% annualized (simple)
```

You pay less than face value today and at maturity, you receive face value. The discount is your return.

In **Morpho Blue**, when you lend 1,000 USDC, you receive supply shares. The number of shares depends on the current exchange rate. As borrowers pay interest, the exchange rate grows, i.e. each share becomes worth *more* USDC over time (unless bad debt is socialized). Your share count stays the same, but the value per share floats upward. The rate is baked into the continuously changing exchange rate. All lenders in the same market earn the same rate, and that rate changes every block.

In **Morpho Midnight**, when you lend 1,000 USDC, you *buy* credit units at a specific price (say 0.9524 per unit). You get ~1,050 units. Each unit is always worth exactly 1 USDC at maturity. Your return is the gap between what you paid (1,000 USDC) and what you'll receive (1,050 USDC). The rate isn't embedded in the accounting, it was determined by the price you entered at. Two lenders in the same market can have different rates because they entered at different prices.

## [Fungibility and early exits](#fungibility-and-early-exits)

Positions within a market are **fully fungible**. Because all positions within a market share the same maturity date, units created from different takes at different times are interchangeable.

This fungibility enables early exits through the same offer mechanism as entries. A lender doesn't need to wait until maturity: they can sell their credit units by taking resting buy offers (see [Exit lend early](https://docs.morpho.org/developers/midnight/tutorials/exit-lend-early/)). A borrower can close out debt early by buying units from resting sell offers (see [Exit borrow early](https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-early/)). The same market serves both entries and exits.

To track a user’s entries and exits in a market use the following endpoint:

`GET /v0/midnight/users/{user-address}/transactions`

```
GET /v0/midnight/users/{addr}/transactions

// Response excerpt (other fields omitted; values are illustrative)
//    lend                  → bought credit units (entered a lending position)
//    exit_lend_primary     → redeemed credit (1:1 withdrawal)
//    exit_lend_secondary   → sold credit units before maturity (early exit)
//    supply_collateral     → deposited collateral into a market
//    borrow                → took an offer / sold credit units (created debt)
//    exit_borrow_primary   → repaid debt
//    exit_borrow_secondary → bought units to close debt (early close)
//    withdraw_collateral   → withdrew collateral from a market
//    partial_liquidation   → position partially liquidated (pre-maturity, RCF-capped)
//    full_liquidation      → position fully liquidated

// Event fields depend on event_type; inspect the matching transaction schema.
```

You can also choose to filter specific transactions (i.e. lending) and get a subset of event types in the response:
`GET /v0/midnight/users/{user-address}/transactions`

```
GET /v0/midnight/users/{addr}/transactions
  ?event_types=lend,exit_lend_primary,exit_lend_secondary
```

[Get Started

Previous Page

](https://docs.morpho.org/developers/midnight/get-started/)[Collateral, Health, Liquidations

Next Page

](https://docs.morpho.org/developers/midnight/concepts/collateral-health-liquidations/)