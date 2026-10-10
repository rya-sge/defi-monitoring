# Mempool & Router

> Source: https://docs.morpho.org/developers/midnight/concepts/mempool-router

---

# Mempool & Router

## [Mempool](#mempool)

Everything so far describes a position you already hold: how its health is measured and what happens if it deteriorates. But a position only exists once a borrower and a lender have traded units. Midnight has no order book matching them: instead, makers broadcast signed offers onchain through the mempool, a minimal contract that simply logs each offer as an event (no storage or mapping is performed by the mempool).

The mempool is not a single canonical place. Offers exist entirely offchain so different participants might see different subsets of offers. The competition to find and fill the best offers is the province of **routers.**

**Key difference from an order book**

On a CLOB (central limit order book), placing an order locks capital and establishes price-time priority. In Midnight, an offer locks nothing and has no protocol-enforced priority. Best-price ordering is instead handled offchain by the Morpho router, explained in the section that follows.

## [Router](#router)

Because offers float offchain with no canonical queue and no protocol-enforced priority, a taker looking for the best rate faces a genuine **search problem**. The process of discovering, evaluating, and selecting which offers to take is called **routing**.

Because routing is permissionless, anyone can run one. **Morpho operates its own router**, which aggregates offers and surfaces executable offers so integrators don't have to build discovery infrastructure themselves.

### [Validating offers](#validating-offers)

The Morpho router only indexes offers that pass its rules. Each rule constrains one dimension of an offer. If any rule is violated, Morpho's router ignores the offer.

| Rule group | What the validation endpoint checks |
| --- | --- |
| Payload format | Version, framing, compression, ABI decoding, duplicate offers, and the offer count. |
| Chain and market support | Chain and deployment identity, supported maturities, loan tokens, collateral tokens, oracles, market combinations, LLTVs, liquidation settings, and collateral count. |
| Offer size and price | Amount constraints, tick range and spacing, duration, and ratifier support. |
| Batch consistency | Shared maker and ratifier, group identity, compatible group terms, and non-overlapping active windows. |
| Callbacks | Empty-callback policy and the content and registration checks for supported Blue buy callbacks. |

The validation endpoint is a pre-flight check: "will the router index this offer?" If validation returns issues, the offer can still exist in the mempool, but the router ignores it.

`POST /v0/midnight/mempool/validate`

```
// Check if the router will index your offers
POST /v0/midnight/mempool/validate
{
  "chain_id": 8453,
  "payload": "0x01..."
}

// Response excerpt (other fields omitted; values are illustrative)
{
  "data": {
    "issues": []
  }
}

// Response excerpt (other fields omitted; values are illustrative)
{
  "data": {
    "issues": [
      {
        "rule": "loan_token"
      },
      {
        "rule": "maturity"
      },
      {
        "rule": "tick_spacing"
      }
    ]
  }
}
```

Validation checks the declared ratifier against the router's policy. It does not authenticate signatures or Merkle proofs in `ratifierData`; those checks happen later during indexing or onchain execution.

### [The order book](#the-order-book)

The router aggregates all signed & active offers from the mempool that pass its rules in the form of a book (a bid/ask market view). It groups them by tick and sums the units and assets at each tick into a price level (price level = one tick).

**Why "asks" and "bids"?**

Make/take describes what a *participant does.* "I make an offer," "someone takes it." Ask/bid describes the *aggregated state of the market:* "there are asks at this price, bids at that." Both sides of the book are made up of makers' offers; the taker is the person reading the book and deciding what to hit.

An **ask** is a sell-unit offer (the maker wants to borrow). A **bid** is a buy-unit offer (the maker wants to lend). If you want to lend, you *take asks*. If you want to borrow, you *take bids*.

To fetch a single book's state run the following query:
`GET /v0/midnight/books`

```
GET /v0/midnight/books?chain_ids=8453&limit=1

// Response excerpt (other fields omitted; values are illustrative)
{
  "cursor": null,
  "data": [
    {
      "market_id": "0x52b0f65ac6906080cb2100a2ffbef8f81c6c40ec65ebca6b5fc6ad4412ad77cf",
      "chain_id": 8453,
      "midnight": "0x2f7a3aa739ba5792ce1b4ea046117f2c0095bca6",
      "loan_token": "0x4200000000000000000000000000000000000006",
      "collaterals": [
        {
          "token": "0xcbb7...33bf",
          "lltv": "860000000000000000",
          "liquidation_cursor": "250000000000000000",
          "oracle": "0x10b95702a0ce895972c91e432c4f7e19811d320e"
        }
      ],
      "maturity": 1783090800,
      "rcf_threshold": "0",
      "enter_gate": "0x0000000000000000000000000000000000000000",
      "liquidator_gate": "0x0000000000000000000000000000000000000000",
      "asks": [
        {
          "tick": 4736,
          "price": "998890800000000000",
          "units": "666666666666666",
          "assets": "665927200000000",
          "count": 2
        },
        {
          "tick": 4740,
          "price": "998912700000000000",
          "units": "1333333333333334",
          "assets": "1331883600000002",
          "count": 2
        },
        {
          "tick": 4744,
          "price": "998934100000000000",
          "units": "2000000000000000",
          "assets": "1997868200000000",
          "count": 2
        }
      ],
      "bids": [
        {
          "tick": 4732,
          "price": "998868400000000000",
          "units": "667421921312824",
          "assets": "666666666666666",
          "count": 2
        },
        {
          "tick": 4728,
          "price": "998845700000000000",
          "units": "1334874178597690",
          "assets": "1333333333333334",
          "count": 2
        },
        {
          "tick": 4724,
          "price": "998822400000000000",
          "units": "2002357976753426",
          "assets": "2000000000000000",
          "count": 2
        }
      ]
    }
  ]
}
```

To fetch a book with a specific depth (max price levels per side), run the following query:
`GET /v0/midnight/books/{market-id}`

```
GET /v0/midnight/books/{market-id}?depth=50
```

To only fetch the book's ask side, run the following query:
`GET /v0/midnight/books/{market-id}/{side}`

```
GET /v0/midnight/books/{market-id}/asks

// Response excerpt (other fields omitted; values are illustrative)
{
  "data": [
    {
      "tick": 4736,
      "price": "998890800000000000",
      "units": "666666666666666",
      "assets": "665927200000000",
      "count": 2
    },
    {
      "tick": 4740,
      "price": "998912700000000000",
      "units": "1333333333333334",
      "assets": "1331883600000002",
      "count": 2
    },
    {
      "tick": 4744,
      "price": "998934100000000000",
      "units": "2000000000000000",
      "assets": "1997868200000000",
      "count": 2
    }
  ]
}
```

### [Takeable offers](#takeable-offers)

The book endpoint returns only aggregated summaries. A price level tells you "10,000 units are available at price 0.9524". To execute, you need the full `Offer` struct plus the `ratifierData`.

That's what a **takeable offer** is: an individual offer that is currently executable, packaged with everything needed to call the Midnight contract onchain. The quote endpoint returns these individual offers complete with `Offer` structs and `ratifierData` ready for onchain submission. You tell it how much you want to trade, a market, a side, a target size, and optional slippage and it searches the mempool, ranks offers by price, and returns a bundle-ready execution plan.

A note on fallback excess returned by the quote:

1. When you request a quote for 10,000 units, the router returns more than 10,000 (say 15,000 across four offers, sorted best price first, then earliest first within the same tick). This excess is intentional.
2. Between the moment you receive the quote and the moment your transaction lands onchain, other takers may have partially consumed some of those same offers.
3. If offer A originally had 5,000 units but someone else took 3,800 of them in the meantime, only 1,200 remain when your transaction executes.
4. Your bundler skips what it can't fill from A and moves to offers B and C to reach your 10,000 target. The fallback offers absorb the impact of this concurrency.
5. You may get a slightly worse average price (since later offers sit at deeper ticks), but you still fill your slippage target / price tolerance.

For example, if you want to lend 10,000 USDC and take asks you run the following query:
`GET /v0/midnight/books/{market-id}/{side}/quote`

```
GET /v0/midnight/books/{market-id}/asks/quote
  ?assets=10000000000
  &slippage=0.5

// Response excerpt (other fields omitted; values are illustrative)
{
  "data": {
    "average_best_price": "998890800000000000",
    "average_worst_price": "1003885254000000000",
    "available_assets": "14983800",
    "available_units": "15000000",
    "takeable_offers": [
      {
        "market_id": "0xa249f0b3ffe8891c96ec93fd9c7d00e479da04e4ffe2f2502ea0e5db8eabc75d",
        "units": "833333",
        "offer": {
          "buy": false,
          "maker": "0x6ba008e3f6ec55dc6412e459ac67949c6d1620c5",
          "max_units": "833333",
          "max_assets": "0",
          "tick": 4736,
          "start": 1782484425,
          "expiry": 1783090799,
          "group": "0x6c544af73868898482d1802005d87e7a4d1100d4e1a6e099a978f6bd2e6cba17",
          "ratifier": "0x1db7b555ce19e85e625428b0e1047da3198211ea"
        },
        "ratifier_data": "0x0000000000000000000000000000000000000000..."
      },
      // more offers
      {...}
    ]
  }
}
```

[Collateral, Health, Liquidations

Previous Page

](https://docs.morpho.org/developers/midnight/concepts/collateral-health-liquidations/)[Callbacks

Next Page

](https://docs.morpho.org/developers/midnight/concepts/callbacks/)