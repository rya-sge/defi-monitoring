# Morpho Midnight

> Source: https://docs.morpho.org/developers/api/morpho-midnight

---

# Morpho Midnight

## [How to query Morpho Midnight data with the API?](#how-to-query-morpho-midnight-data-with-the-api)

Morpho Midnight can be accessed through Morpho's REST API currently under version `v0`. This API is still evolving, and changes to routes and responses may occur as development progresses.

Enterprise API accessFor enterprise access, send requests to `https://private.api.morpho.org` with your API key in the `x-api-key` header. [Request an API key](https://docs.morpho.org/request-api-key/).

## [Discovery & listing](#discovery--listing)

### [List all markets](#list-all-markets)

Returns all Midnight markets, optionally filtered by chain, loan token, or collateral. Supported `chain_ids`: `1`, `8453`.

`GET /v0/midnight/markets`

**All markets:**

```
# All markets on Ethereum mainnet
curl "https://api.morpho.org/v0/midnight/markets?chain_ids=1"
```

**Filtered by token:**

```
# USDC markets on Base with wETH as collateral
curl "https://api.morpho.org/v0/midnight/markets\
  ?chain_ids=8453\
  &loan_assets=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913\
  &collateral_assets=0x4200000000000000000000000000000000000006"
```

### [Get market detail](#get-market-detail)

Immutable configuration for a single market: market family, loan token, maturity, collaterals (with LLTV, liquidation cursor, oracle), and gates. Does **not** include fees or total units (those live on the state endpoint).

`GET /v0/midnight/markets/{market-id}`

Each entry in the response's `collaterals` list carries exactly these fields:

`token`, `lltv`, `liquidation_cursor`, `oracle`

```
curl "https://api.morpho.org/v0/midnight/markets/0xcc9418ea594c6e658650aedd205ce4544b266b69493f56fd2adc65c14bd06738"

// Response - immutable market definition:
{
  "data": {
    "chain_id": 8453,
    "market_id": "0xcc9418ea594c6e658650aedd205ce4544b266b69493f56fd2adc65c14bd06738",
    "market_family_id": "0x9a6ece688006fb810141501154acfd1aa29ae7ac3753452f4931a092f2653f1f",
    "loan_token": "0x4200000000000000000000000000000000000006", // WETH on Base
    "maturity": 1784300400, // July 17, 2026 at 15:00 UTC
    "rcf_threshold": "0",
    "enter_gate": "0x0000000000000000000000000000000000000000",
    "liquidator_gate": "0x0000000000000000000000000000000000000000",
    "collaterals": [
      {
        "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "lltv": "860000000000000000",
        "liquidation_cursor": "300000000000000000",
        "oracle": "0xD09048c8B568Dbf5f189302beA26c9edABFC4858"
      }
    ]
  }
}
```

## [Market state & metrics](#market-state--metrics)

### [Get market state](#get-market-state)

Live market state: total units outstanding, fee configuration, and tick granularity. Separated from the market definition because these values change over time.

`GET /v0/midnight/markets/{market-id}/state`

```
curl "https://api.morpho.org/v0/midnight/markets/0xcc9418ea594c6e658650aedd205ce4544b266b69493f56fd2adc65c14bd06738/state"

// Response:
{
  "data": {
    "chain_id": 8453,
    "market_id": "0xcc9418ea594c6e658650aedd205ce4544b266b69493f56fd2adc65c14bd06738",
    "market_family_id": "0x9a6ece688006fb810141501154acfd1aa29ae7ac3753452f4931a092f2653f1f",
    "last_indexed_block": "48408699",
    "total_units": "1481439992020013", // total units outstanding
    "tick_granularity": 4, // valid ticks must be multiples of this
    "settlement_fee_schedule": [
      { "time_to_maturity_days": 0, "fee_cbp": "0" },
      { "time_to_maturity_days": 1, "fee_cbp": "0" },
      { "time_to_maturity_days": 7, "fee_cbp": "0" },
      { "time_to_maturity_days": 30, "fee_cbp": "0" },
      { "time_to_maturity_days": 90, "fee_cbp": "0" },
      { "time_to_maturity_days": 180, "fee_cbp": "0" },
      { "time_to_maturity_days": 360, "fee_cbp": "0" }
    ],
    "current_settlement_fee_wad": "0",
    "current_settlement_fee_cbp": "0", // interpolated for current TTM
    "continuous_fee_rate": "0" // per-second, WAD-scaled
  }
}
```

## [Order books & rates](#order-books--rates)

### [List policy-admitted books](#list-policy-admitted-books)

The endpoint returns only active maturities admitted by the current policy. Unlisted and past maturities stay excluded even when requested with `ids`; if a maturity leaves the policy, its books disappear immediately, including books with existing offers.

Each book includes the top 3 ask and bid levels. Sorting: Sort by comma-separated fields (`id`, `ask`, `bid`, `maturity`). Prefix a field with `-` for descending. Max 3 fields.

`GET /v0/midnight/books`

**By maturity:**

```
curl "https://api.morpho.org/v0/midnight/books\
  ?chain_ids=8453\
  &loan_tokens=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913\
  &sort=maturity"
```

**By best lend rate:**

```
# Sort by best ask (lowest price = highest lend rate)
curl "https://api.morpho.org/v0/midnight/books\
  ?chain_ids=8453\
  &loan_tokens=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913\
  &sort=ask"
```

### [Get full book for a market](#get-full-book-for-a-market)

Each level sums all offers at that tick. Levels returned per side: Maximum levels returned per side. Default: 100. Maximum: 5821.

`GET /v0/midnight/books/{market-id}`

Each price level carries exactly these fields:

`tick`, `price`, `units`, `assets`, `count`

```
curl "https://api.morpho.org/v0/midnight/books/0xcc9418ea594c6e658650aedd205ce4544b266b69493f56fd2adc65c14bd06738?depth=50"

// Response:
{
  "data": {
    "market_id": "0xcc9418ea594c6e658650aedd205ce4544b266b69493f56fd2adc65c14bd06738",
    "chain_id": 8453,
    "midnight": "0x2F7a3AA739ba5792Ce1b4eA046117f2C0095BCA6",
    "loan_token": "0x4200000000000000000000000000000000000006",
    "collaterals": [
      {
        "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "lltv": "860000000000000000",
        "liquidation_cursor": "300000000000000000",
        "oracle": "0xD09048c8B568Dbf5f189302beA26c9edABFC4858"
      }
    ],
    "maturity": 1784300400,
    "rcf_threshold": "0",
    "enter_gate": "0x0000000000000000000000000000000000000000",
    "liquidator_gate": "0x0000000000000000000000000000000000000000",
    "asks": [
      { "tick": 42, "price": "952380952380952380", "units": "10000000000", "assets": "9523809523", "count": 3 },
      { "tick": 43, "price": "948000000000000000", "units": "18500000000", "assets": "17538000000", "count": 5 }
    ],
    "bids": [
      { "tick": 41, "price": "956937000000000000", "units": "8000000000", "assets": "7655497000", "count": 2 }
    ]
  }
}
```

Compute rates from prices (TTM = seconds to maturity):

```
// lend rate (from asks):   (1 / (price / 1e18) - 1) × 365×86400 / TTM
// borrow rate (from bids): (1 / (price / 1e18) - 1) × 365×86400 / TTM
```

### [Get one side of the book](#get-one-side-of-the-book)

`{side}` is one of `asks`, `bids`.

`GET /v0/midnight/books/{market-id}/{side}`

```
# Just the asks (lender opportunities)
curl "https://api.morpho.org/v0/midnight/books/0xd92d...7614/asks?depth=100"

# Just the bids (borrower opportunities)
curl "https://api.morpho.org/v0/midnight/books/0xd92d...7614/bids?depth=100"
```

## [Quotes & execution](#quotes--execution)

### [Get a quote (execution plan)](#get-a-quote-execution-plan)

Given a target amount (in assets or units) and a side, the Router returns execution-ready takeable offers sorted by best price with fallback excess.

`GET /v0/midnight/books/{market-id}/{side}/quote`

Each takeable offer's `offer` struct carries exactly these fields:

`market`, `buy`, `maker`, `max_units`, `start`, `expiry`, `tick`, `group`, `callback`, `callback_data`, `receiver_if_maker_is_seller`, `ratifier`, `reduce_only`, `max_assets`, `continuous_fee_cap`

**Lend (take asks):**

```
// "I want to lend 10,000 USDC" → take asks
curl "https://api.morpho.org/v0/midnight/books/0xd92d...7614/asks/quote\
  ?assets=10000000000\
  &slippage=0.5\
  &limit=10000"

// Response:
{
  "data": {
    "average_best_price": "947619047619047619", // realized target fill, using onchain per-offer rounding and rounded against the taker
    "average_worst_price": "952300000000000000", // conservative adverse-placement bound across returned caps; not the caller's guard
    "available_assets": "15000000000",
    "available_units": "15750000000",
    "takeable_offers": [
      {
        "market_id": "0xd92d...7614",
        "units": "5000000000",
        "offer": {
          "market": {
            "chain_id": 8453,
            "midnight": "0x2F7a3AA739ba5792Ce1b4eA046117f2C0095BCA6",
            "loan_token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "collaterals": [
              {
                "token": "0x4200000000000000000000000000000000000006",
                "lltv": "860000000000000000",
                "liquidation_cursor": "300000000000000000",
                "oracle": "0x45093658BE7f90B63D7c359e8f408e503c2D9401"
              }
            ],
            "maturity": 1798761600,
            "rcf_threshold": "0",
            "enter_gate": "0x0000000000000000000000000000000000000000",
            "liquidator_gate": "0x0000000000000000000000000000000000000000"
          },
          "buy": false,
          "maker": "0x7b093658BE7f90B63D7c359e8f408e503c2D9401",
          "max_units": "0",
          "start": 1761922790,
          "expiry": 1798761600,
          "tick": 42,
          "group": "0x000000000000000000000000000000000000000000000000000000000008b8f4",
          "callback": "0x0000000000000000000000000000000000000000",
          "callback_data": "0x",
          "receiver_if_maker_is_seller": "0x7b093658BE7f90B63D7c359e8f408e503c2D9401",
          "ratifier": "0x0000000000000000000000000000000000000002",
          "reduce_only": false,
          "max_assets": "5000000000",
          "continuous_fee_cap": "115792089237316195423570985008687907853269984665640564039457584007913129639935"
        },
        "ratifier_data": "0x4a8b...f201",
        "warning": null
      }
    ]
  }
}
```

**Borrow (take bids):**

```
# "I want to borrow 5,000 USDC" → take bids
curl "https://api.morpho.org/v0/midnight/books/0xd92d...7614/bids/quote\
  ?assets=5000000000\
  &slippage=0.5\
  &limit=10000"

# Same response shape - but offers have buy=true (lenders' buy-offers)
```

**By units:**

```
# Quote by units instead of assets
curl "https://api.morpho.org/v0/midnight/books/0xd92d...7614/asks/quote\
  ?units=10500000000"
```

### [List takeable offers (raw)](#list-takeable-offers-raw)

Individual executable offers with the full offer struct and ratifier data. Use when building custom routing or analysis.

By market side:

`GET /v0/midnight/books/{market-id}/{side}/takeable-offers`

Across markets, by maker:

`GET /v0/midnight/takeable-offers`

**By market side:**

```
curl "https://api.morpho.org/v0/midnight/books/0xd92d...7614/asks/takeable-offers"
```

**By maker:**

```
# All active offers from a specific maker
curl "https://api.morpho.org/v0/midnight/takeable-offers\
  ?maker=0xMakerAddress...\
  &limit=100"
```

## [Position tracking](#position-tracking)

### [List user positions](#list-user-positions)

Returns all positions for a user across markets. Includes `cost_basis` and `effective_rate_wad` inline. Position `types`: `lend`, `borrow`, `collateral_only`.

`GET /v0/midnight/users/{user-address}/positions`

**All positions:**

```
curl "https://api.morpho.org/v0/midnight/users/0xAlice.../positions"

// Response:
{
  "cursor": null,
  "data": [
    {
      "chain_id": 8453,
      "market_id": "0xd92d...7614",
      "user_address": "0xAlice...",
      "loan_token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      "maturity": 1798761600,
      "credit": "10500000000",
      "pending_fee": "12000",
      "last_loss_factor": "0",
      "loss_factor": "0",
      "debt": "0",
      "cost_basis": "952380952380952380",
      "effective_rate_wad": "52000000000000000",
      "collaterals": [],
      "created_at": 1761922790,
      "type": "lend"
    }
  ]
}
```

**Lend only:**

```
curl "https://api.morpho.org/v0/midnight/users/0xAlice.../positions?types=lend"
```

**Borrow only:**

```
curl "https://api.morpho.org/v0/midnight/users/0xAlice.../positions?types=borrow"
```

### [Get position detail](#get-position-detail)

Raw position state in a specific market. Does **not** include `cost_basis` or `effective_rate_wad` (use the performance endpoint for those).

`GET /v0/midnight/markets/{market-id}/users/{user-address}/position`

```
curl "https://api.morpho.org/v0/midnight/markets/0xd92d...7614/users/0xBob.../position"

// Response (borrow position):
{
  "data": {
    "chain_id": 8453,
    "market_id": "0xd92d...7614",
    "user_address": "0xBob...",
    "loan_token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "maturity": 1798761600,
    "credit": "0",
    "pending_fee": "0",
    "last_loss_factor": "0",
    "loss_factor": "0",
    "debt": "9000000000", // debt to clear
    "collaterals": [
      {
        "token": "0x4200000000000000000000000000000000000006", // WETH on Base
        "amount": "2000000000000000000" // 2 WETH
      },
      {
        "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", // USDC on Base
        "amount": "10000000" // 10 USDC
      }
    ],
    "type": "borrow",
    "last_indexed_block": "47457420"
  }
}
```

### [Get position performance](#get-position-performance)

Cost basis and effective rate for P&L computation. Uses average cost accounting.

`GET /v0/midnight/markets/{market-id}/users/{user-address}/position/performance`

```
curl "https://api.morpho.org/v0/midnight/markets/0xd92d...7614/users/0xAlice.../position/performance"

// Response:
{
  "data": {
    "chain_id": 8453,
    "market_id": "0xd92d...7614",
    "user_address": "0xAlice...",
    "type": "lend",
    "cost_basis": "952380952380952380",
    "effective_rate_wad": "52000000000000000",
    "last_indexed_block": "47457420",
    "accounting_method": "average_cost"
  }
}
```

### [List all positions in a market](#list-all-positions-in-a-market)

Find all borrowers, cross-reference with oracle prices to find unhealthy positions.

`GET /v0/midnight/markets/{market-id}/positions`

```
# All borrowers in a market
curl "https://api.morpho.org/v0/midnight/markets/0xd92d...7614/positions?types=borrow"

# Active positions only (market not yet matured)
curl "https://api.morpho.org/v0/midnight/markets/0xd92d...7614/positions\
  ?types=borrow\
  &active_only=true"
```

## [Transaction history](#transaction-history)

### [User transactions](#user-transactions)

All onchain events for a user. Filter by `event_types` to focus on specific actions. Valid values:

`borrow`, `lend`, `exit_lend_primary`, `exit_lend_secondary`, `exit_borrow_primary`, `exit_borrow_secondary`, `partial_liquidation`, `full_liquidation`, `withdraw_collateral`, `supply_collateral`

- `lend` - entered a lending position (bought units)
- `exit_lend_primary` - redeemed credit (1:1 withdrawal)
- `exit_lend_secondary` - sold credit units early
- `borrow` - entered a borrowing position (sold units)
- `exit_borrow_primary` - repaid debt
- `exit_borrow_secondary` - bought units to close debt early
- `supply_collateral` - deposited collateral
- `withdraw_collateral` - withdrew collateral
- `partial_liquidation` / `full_liquidation` - liquidations; events include the borrower, collateral, seized assets, repaid units, post-maturity mode, bad debt, and latest loss factor

`GET /v0/midnight/users/{user-address}/transactions`

**Lending activity:**

```
curl "https://api.morpho.org/v0/midnight/users/0xAlice.../transactions\
  ?event_types=lend,exit_lend_primary,exit_lend_secondary"
```

**Borrowing activity:**

```
curl "https://api.morpho.org/v0/midnight/users/0xBob.../transactions\
  ?event_types=borrow,exit_borrow_primary,exit_borrow_secondary,supply_collateral,withdraw_collateral"
```

### [Market transactions](#market-transactions)

`GET /v0/midnight/markets/{market-id}/transactions`

```
# All activity in a market since a specific time
curl "https://api.morpho.org/v0/midnight/markets/0xd92d...7614/transactions?created_at_gte=1719000000"
```

## [Offer management](#offer-management)

### [List offer groups](#list-offer-groups)

Track a maker's consumption groups and which offers belong to them. `status` selects the
lifecycle and defaults to `active`; `status=expired` returns groups whose latest offers have
all expired or matured. Groups can also be narrowed to verified Blue callbacks with
`callback_type=blue_buy`, and to Midnight market families with `market_family_ids`.

`GET /v0/midnight/users/{user-address}/offer-groups`

```
# All active offer groups for this maker (default status)
curl "https://api.morpho.org/v0/midnight/users/0xMaker.../offer-groups"

# Active offer groups filtered by market and group
curl "https://api.morpho.org/v0/midnight/users/0xMaker.../offer-groups\
  ?market_ids=0xd92d...7614\
  &groups=0xMyGroupId..."

# Expired offer groups with verified Blue-buy callbacks
curl "https://api.morpho.org/v0/midnight/users/0xMaker.../offer-groups\
  ?status=expired\
  &callback_type=blue_buy"
```

## [Mempool](#mempool)

### [Validate offers before publishing](#validate-offers-before-publishing)

Check whether the Router will index your offers. Payload is `version byte + 4-byte big-endian gzip length + gzip(ABI-encoded (Offer, bytes ratifierData)[])`. Optionally pass a `timestamp` to validate against a specific policy snapshot.

`POST /v0/midnight/mempool/validate`

**Current policy:**

```
curl -X POST "https://api.morpho.org/v0/midnight/mempool/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "chain_id": 8453,
    "payload": "0x01..."
  }'

# Success (Router will index):
{ "data": { "issues": [] } }

# Issues found (Router will ignore):
{ "data": { "issues": [{ "rule": "blue_callback", "details": null }] } }
```

**At a specific time:**

```
# Validate against the policy snapshot active at a specific time
# Uses the latest 15:00 UTC boundary at or before the given timestamp
curl -X POST "https://api.morpho.org/v0/midnight/mempool/validate\
  ?timestamp=2026-06-28T12:00:00Z" \
  -H "Content-Type: application/json" \
  -d '{
    "chain_id": 8453,
    "payload": "0x01..."
  }'
```

## [Pagination & filtering](#pagination--filtering)

List endpoints support cursor-based pagination. The response includes a `cursor` field - pass it as a query parameter to get the next page.

```
# First page
curl "https://api.morpho.org/v0/midnight/markets?chain_ids=8453"

// Response includes:
{ "cursor": "***...", "data": [...] }

# Next page - pass the cursor
curl "https://api.morpho.org/v0/midnight/markets?chain_ids=8453&cursor=***..."

// cursor is null when there are no more pages
```

The markets list carries the richest filter set - other list endpoints follow the same conventions:

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `chain_ids` | query | array | No | Filter by chain ids. Supported chains: Ethereum (1) and Base (8453). Required when any address filter is provided. |
| `market_ids` | query | array | No | Filter by Midnight market ids. These ids are globally unique. |
| `market_family_ids` | query | array | No | Filter by Midnight market family ids. A family contains markets whose immutable parameters differ only by maturity. |
| `loan_assets` | query | array | No | Filter by loan token addresses. Combine with chain_ids; lowercase input is checksummed. |
| `collateral_assets` | query | array | No | Filter by collateral token addresses. Combine with chain_ids; lowercase input is checksummed. |
| `oracle_addresses` | query | array | No | Filter by collateral oracle addresses. Combine with chain_ids; lowercase input is checksummed. |
| `enter_gates` | query | array | No | Filter by enter gate addresses. Combine with chain_ids; lowercase input is checksummed. |
| `liquidator_gates` | query | array | No | Filter by liquidator gate addresses. Combine with chain_ids; lowercase input is checksummed. |
| `maturities` | query | array | No | Filter by exact maturity timestamps, in unix seconds. |
| `active_only` | query | string | No | When true, enforces maturity strictly after the current timestamp. |
| `maturity_gte` | query | anyOf | No | Filter for maturities greater than or equal to this unix timestamp. |
| `maturity_lte` | query | anyOf | No | Filter for maturities less than or equal to this unix timestamp. |
| `total_units_gte` | query | string | No | Filter for total units greater than or equal to this value. |
| `total_units_lte` | query | string | No | Filter for total units less than or equal to this value. |
| `listed` | query | string | No | Filter by listing status. When true, returns only markets surfaced by the app trust layer; when false, only unlisted markets. Omit to return both. |
| `sort_by` | query | string | No | Sort field for cursor pagination. |
| `sort_direction` | query | string | No | Sort direction for cursor pagination. |
| `limit` | query | integer | No | Maximum number of items to return. |
| `cursor` | query | string | No | Opaque cursor from a previous page response. |

[Get Started

Previous Page

](https://docs.morpho.org/developers/api/get-started/)[Morpho Blue

Next Page

](https://docs.morpho.org/developers/api/morpho/)