# Collateral, Health, Liquidations

> Source: https://docs.morpho.org/developers/midnight/concepts/collateral-health-liquidations

---

# Collateral, Health, Liquidations

## [Multiple accepted collaterals](#multiple-accepted-collaterals)

A Midnight market is comprised of *one* loan token + *one* maturity + a **fixed list of accepted collaterals.** Any borrower in that market can back their single debt with any mix of those listed collaterals (up to 128 per market and up to 16 per position).

Each accepted collateral has its own locked LLTV, which determines how much debt that collateral can support. The total amount a borrower can take on is their **maxDebt** (the sum of each posted collateral's value multiplied by its respective LLTV):

```
maxDebt = Σ (collateral value × LLTV)
```

Take a **USDC · Dec-2026** market created to accept three collaterals, each with its own locked LLTV: WETH (86%), cbBTC (77%), wstETH (86%). Two different borrowers show up:

**Borrower A** posts only 2 WETH (at 3,000 USDC):

- collateral value = 6,000
- maxDebt = 6,000 × 0.86 = **5,160 USDC** of borrowing capacity

**Borrower B** posts 2 WETH (at 3,000 USDC) *and* 0.1 cbBTC (at 90,000 USDC):

- WETH: 6,000 × 0.86 = 5,160 (max debt against WETH collateral)
- cbBTC: 9,000 × 0.77 = 6,930 (max debt against cbBTC collateral)
- maxDebt = **12,090 USDC**

Same market, same maturity, the debt units they create are fully fungible with each other and with every lender's credit, but their maxDebt differs because each borrower chooses a different collateral mix.

The set *of accepted* collateral (i.e. WETH, cbBTC, wstETH) is fixed at creation and can never change. Supporting a new collateral means deploying a new market. Within the listed set, though, borrowers compose freely.

One lender-side implication worth flagging: borrowers can change their collateral composition at any point (adding, removing, or swapping between accepted collaterals as long as they stay within their maxDebt). This means lending into a multi-collateral market gives you exposure to *all* of its accepted collaterals' risk, not just whatever borrowers happen to be posting today. If a lender only wants WETH-backed exposure, they lend into a market whose accepted set is just WETH.

To see each collateral's configuration, use the following endpoint:
`GET /v0/midnight/markets/{market-id}`

```
GET /v0/midnight/markets/{market-id}

// Response excerpt (other fields omitted; values are illustrative)
"collaterals": [
  {
    "token":   "0x4200...0006",         // WETH
    "lltv":    "860000000000000000",    // 86% — high LLTV, considered lower risk
    "liquidation_cursor": "250000000000000000",
    "oracle":  "0x1234...abcd"          // price feed for this collateral
  },
  {
    "token":   "0xcbBT...1234",         // cbBTC
    "lltv":    "770000000000000000",    // 77% — lower LLTV, considered higher risk
    "liquidation_cursor": "340000000000000000",
    "oracle":  "0x5678...ef01"
  }
]
```

## [Position Health](#position-health)

Health answers one question: **can a position's collateral still cover what it owes?** A position is healthy as long as its maximum debt capacity is at least its debt: `maxDebt ≥ debt`. After maturity, any outstanding debt makes a position liquidatable regardless of its health.

```
// Pre-maturity health check:
maxDebt ≥ debt   →  healthy
debt > maxDebt   →  liquidatable

// Post-maturity:
// ANY position with debt > 0 is liquidatable, regardless of health
```

Continuing Borrower B from above (`maxDebt` = 12,090), assuming `debt` = 9,000 units:

```
maxDebt (12,090) ≥ debt (9,000)  →  healthy
```

The gap between `maxDebt` and `debt` tells you how much room remains before the position becomes liquidatable. Here, the position can absorb a reduction in `maxDebt` of up to 3,090 units (≈ 25% drop in total collateral value, if both collaterals move together, from 15,000 to ~11,166) before `debt` exceeds `maxDebt`.

To fetch a position's state (debt and collateral) for health computation call the following endpoint:
`GET /v0/midnight/markets/{market-id}/users/{user-address}/position`

```
GET /v0/midnight/markets/{id}/users/{addr}/position

// Response excerpt (other fields omitted; values are illustrative)
{
  "data": {
    "chain_id":          8453,
    "market_id":         "0xd92de5e7fbb...7614",
    "user_address":      "0xBorrowerB...",
    "loan_token":        "0x8335...2913",               // USDC
    "maturity":          1798761600,
    "type":              "borrow",
    "credit":            "0",
    "debt":              "9000000000",                  // 9,000 USDC debt units
    "pending_fee":       "0",
    "loss_factor":       "0",
    "last_loss_factor":  "0",
    "collaterals": [
      { "token": "0x4200...0006", "amount": "2000000000000000000" },  // 2.0 WETH
      { "token": "0xcbBT...1234", "amount": "10000000000000000" }     // 0.1 cbBTC
    ],
    "last_indexed_block": "47457420"
  }
}
```

To check whether the position is healthy:

1. For each collateral, read its oracle address from `GET /v0/midnight/markets/{market-id}` (`collaterals[].oracle`) and query the oracle contract onchain for the price
2. Calculate `collateralValue = amount × oraclePrice`
3. Calculate maxDebt contribution as `collateralValue × lltv` from `GET /v0/midnight/markets/{market-id}`
4. Calculate the position's `maxDebt` as the sum of all contributions from the previous step
5. Position is healthy if `maxDebt ≥ debt`

Health is a property of the whole basket and a liquidator restoring health draws against that combined collateral. Which collateral they seize is an economic choice covered in the Liquidation section that follows.

## [Liquidation](#liquidation)

### [Maturity](#maturity)

A position can be liquidated pre or post maturity.

**Pre-maturity (health-factor based):** if a borrower's position becomes unhealthy (their debt exceeds their maxDebt) a liquidator can step in to repay some of the debt and seize collateral of their choosing, in whatever mix they want. The protocol checks that the seize is valued correctly and that they don't exceed the recovery close factor cap. How much can be liquidated depends on position size (see RCF below).

**Post-maturity:** once a market's maturity date has passed, any borrower who hasn't fully repaid can be liquidated for the entirety of their debt in a single call. There's no partial liquidation and the position is liquidated, because the grace period is over and lenders need access to their funds.

The Recovery Close Factor (RCF) caps how much debt a liquidator can repay in a single liquidation on the **unhealthy path** (pre-maturity). The idea is: if a position is only slightly underwater, the liquidator should only liquidate *enough to restore it to health,* not seize everything.

The RCF caps the liquidator's repayment at the amount needed to bring `maxDebt ≥ debt` back into balance, restoring the position to health rather than closing it out entirely. A per-collateral exception applies: if a liquidation would leave less than `rcfThreshold` worth of a given collateral, the liquidator can seize all of that collateral to avoid leaving a residual too small to liquidate profitably.

The **post-maturity path** has no RCF cap. After maturity, if a borrower hasn't repaid, the full debt can be liquidated in one call because the grace period is over and lenders need access to their assets.

### [Liquidation Incentive Factor (LIF)](#liquidation-incentive-factor-lif)

How the liquidator picks is an economic question, not a protocol rule. The dominant driver is that **the liquidation incentive is per-collateral:** each collateral's `max_lif` comes from its own LLTV and cursor γ, via `LIF = 1/(1 − γ(1 − LLTV))`. Lower-LLTV collateral pays a *bigger* bonus. In your two-collateral position (assuming γ = 0.25 on both):

- WETH, LLTV 86% → `LIF = 1/(1 − 0.25·0.14) ≈ 1.036` → ~3.6% bonus
- cbBTC, LLTV 77% → `LIF = 1/(1 − 0.25·0.23) ≈ 1.061` → ~6.1% bonus

The Morpho API returns all the fields you need to calculate the `max_lif` in the market’s definition endpoint:

`GET /v0/midnight/markets/{market-id}`

```
GET /v0/midnight/markets/{marketId}

// Response excerpt (other fields omitted; values are illustrative)
"collaterals": [
  { "token": "0x4200...0006", "lltv": "860000000000000000", "liquidation_cursor": "250000000000000000", ...},
  { "token": "0xcbBT...1234", "lltv": "770000000000000000", "liquidation_cursor": "250000000000000000", ... }
]
```

**LLTV is a risk signal.** A market gets a low LLTV for an asset precisely because that asset is considered riskier to hold and unwind (more volatile, thinner liquidity, more slippage to sell).

If a liquidator repays 1,000 USDC of debt:

- Take cbBTC → they receive 1,000 × 1.061 = **1,061 USDC** of cbBTC
- Take WETH → they receive 1,000 × 1.036 = **1,036 USDC** of WETH

So cbBTC is the more profitable grab here, purely on the incentive. But the bonus isn't the only input. A rational liquidator nets it against **execution cost**: how liquid the asset is, slippage to swap it back to the loan token, and gas. If cbBTC were thin and WETH deep, they might take WETH despite the smaller headline bonus, or split across both. The protocol is indifferent; profit-maximization decides.

Borrowers can't assume their "preferred" collateral is safe. Liquidators gravitate toward whatever maximizes their return.

What’s more, **lenders’ exposure to loss** doesn’t change based on the liquidator’s choice. Because Midnight realizes excess debt as bad debt immediately the haircut to lender credit is computed from the position's shortfall, not from what the liquidator claimed.

### [Liquidation queries](#liquidation-queries)

Track liquidation events in a market:

`GET /v0/midnight/markets/{market-id}/transactions`

```
GET /v0/midnight/markets/{id}/transactions
  ?event_types=partial_liquidation,full_liquidation

// Each liquidation event includes:
//   borrower           → whose position was liquidated
//   collateral         → which collateral token was seized
//   seized_assets      → amount of collateral taken
//   repaid_units       → debt units repaid by the liquidator
//   post_maturity_mode → false = unhealthy path, true = post-maturity path
//   bad_debt           → any unrealized shortfall socialized to lenders
//   latest_loss_factor → updated market loss factor after this liquidation
```

Check if your position has been liquidated:

`GET /v0/midnight/users/{user-address}/transactions`

```
GET /v0/midnight/users/{addr}/transactions
  ?event_types=partial_liquidation,full_liquidation

// If post_maturity_mode is true → liquidation happened after maturity
// If post_maturity_mode is false → position went unhealthy before maturity
```

Find all borrowing positions in a market to assess liquidation risk:

`GET /v0/midnight/markets/{market-id}/positions`

`GET /v0/midnight/markets/{market-id}`

```
GET /v0/midnight/markets/{marketId}/positions?types=borrow

// For each position, compute maxDebt from their collateral:
//
//   1. Get the market's collateral config (lltv per collateral):
//      GET /v0/midnight/markets/{marketId}
//
//   2. For each collateral in the position:
//      collateralValue = amount × oraclePrice
//      maxDebtContribution = collateralValue × lltv
//
//   3. Sum across all collaterals:
//      maxDebt = Σ maxDebtContribution
//
//   4. Compare:
//      maxDebt ≥ debt  → healthy, not liquidatable
//      maxDebt < debt  → unhealthy, liquidatable via pre-maturity path
//
//   5. Post-maturity check (separate from health):
//      block.timestamp > maturity && debt > 0 → liquidatable via post-maturity path
//      regardless of whether maxDebt ≥ debt
```

[Market Mechanics

Previous Page

](https://docs.morpho.org/developers/midnight/concepts/market-mechanics/)[Mempool & Router

Next Page

](https://docs.morpho.org/developers/midnight/concepts/mempool-router/)