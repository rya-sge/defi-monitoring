# Shared Liquidity

> Source: https://docs.morpho.org/developers/borrow/concepts/shared-liquidity

---

# Shared Liquidity

Show and use liquidity that the Public Allocator can move into a Morpho Blue market.

Available liquidity can include both assets already in a Morpho Blue market and assets that the Public Allocator can reallocate from participating Vault V2s. This can support a larger borrow, or a larger loan-asset withdrawal by a lender in that market, without combining the markets' risk.

## [What liquidity is available](#what-liquidity-is-available)

For a target market, distinguish liquidity already in the market from liquidity that can be moved into it:

| Source | Meaning |
| --- | --- |
| Market liquidity | Loan assets currently available in the market. |
| Reallocatable liquidity | Loan assets that the Public Allocator V2 can move from participating vaults, subject to each vault's settings and caps. |

Both values are denominated in the market's loan-token native units. Neither amount is reserved. Other borrows, withdrawals, or reallocations, and changes to permissions or caps, can reduce either one before your transaction executes.

Borrowing and withdrawing loan assets from a market can benefit from reallocation. The API also reports `borrow_amount_to_target_utilization`, which is the additional borrow capacity to the target utilization, including reallocation. Treat that field as a separate utilization-based measure, not another amount to add to market liquidity.

## [Read the liquidity API](#read-the-liquidity-api)

Use `GET /v0/blue/markets/{market-selector}/liquidity` with a market selector formatted as `<chain_id>:<market_id>`. See the [Get market liquidity](https://docs.morpho.org/api/markets/get-market-liquidity/) API reference.

The `MarketLiquidityResponse` wraps the values in a `data` object:

| Field | Meaning |
| --- | --- |
| `market_liquidity` | Current market liquidity in loan-token native units. |
| `reallocatable_liquidity` | Liquidity available through Public Allocator V2 in loan-token native units. |
| `borrow_amount_to_target_utilization` | Additional borrow capacity to target utilization, including reallocations, in loan-token native units. |
| `last_indexed_block` | Indexer tip block number when the response was served. |

The amount and block fields are JSON strings. Parse the three liquidity amounts as integer values in native units; apply token decimals only for display. Do not parse them as floating-point numbers.

```
{
  "data": {
    "market_liquidity": "...",
    "reallocatable_liquidity": "...",
    "borrow_amount_to_target_utilization": "...",
    "last_indexed_block": "..."
  }
}
```

Use `market_liquidity` and `reallocatable_liquidity` to show the available liquidity split. `borrow_amount_to_target_utilization` can help explain how much additional borrowing fits before the target utilization, including eligible reallocations.

## [Plan and price a reallocation](#plan-and-price-a-reallocation)

Reallocatable liquidity is potential liquidity, not a reservation for your user. When presenting an amount for a borrow or withdrawal, make clear whether it relies on a reallocation.

A single move connects one source to one target market. If liquidity must come from several sources, the bundle includes one move per source. Each move can charge a penalty in the loan asset, paid by the caller to the vault, where it accrues to depositors. Show the total penalty before submission and set a maximum penalty the user accepts.

## [Execute atomically](#execute-atomically)

Build the reallocation and the borrow or withdrawal in one bundled transaction so both succeed or neither does. Bundles provide atomic execution; see [Bundles](https://docs.morpho.org/learn/concepts/bundles/) and the [Public Allocator SDK tutorial](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/).

## [Refresh before submission](#refresh-before-submission)

`last_indexed_block` reports the indexer tip when it served the response; it is a freshness hint, not a reservation. Liquidity can change after the API read and before execution.

Rebuild the plan from fresh data immediately before submission, and simulate the final transaction. If the source or destination no longer has enough liquidity or a cap has changed, discard the old plan and rebuild it. The displayed amount is not guaranteed to remain available.

## [Integrate it](#integrate-it)

Use the [Public Allocator SDK tutorial](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/) to build and submit reallocation plans.

[Interest Rates

Previous Page

](https://docs.morpho.org/developers/borrow/concepts/interest-rates/)[Liquidation

Next Page

](https://docs.morpho.org/developers/borrow/concepts/liquidation/)