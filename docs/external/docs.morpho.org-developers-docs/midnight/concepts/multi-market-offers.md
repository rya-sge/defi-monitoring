# Multi-Market Offers

> Source: https://docs.morpho.org/developers/midnight/concepts/multi-market-offers

---

# Multi-Market Offers

## [Liquidity fragmentation](#liquidity-fragmentation)

Isolated markets fragment liquidity. A single fixed-rate market is one loan token, one maturity, and one collateral set, so a lender willing to lend "USDC around 5%" faces a dozen separate books: USDC against wETH, against cbBTC, against wstETH, at the December maturity, the March maturity, and so on. Their willingness to lend is one pool of capital, but the venue splits it into many.

The naïve options are bad and result in less liquidity in the system.

1. **Provision capital to every market:** most of it sits idle as unfilled depth (a real opportunity cost that makers respond to by quoting less)
2. **Pick one/fewer markets:** with this you end up missing every fill that lands elsewhere.
3. **Quote wider spreads:** compensates for the cost of capital when they do get filled

The book is thinner than the lender's actual appetite, and thin books are exactly what stop new collateral configurations and maturities from bootstrapping.

## [Multi-market offers](#multi-market-offers)

A maker signs several offers across different markets and assigns them to a common **consumption group** that shares a single **fill budget**. The budget represents the total takeable liquidity the maker is willing to commit across those offers. Each offer is individually takeable up to the full *remaining* budget. The instant any one offer is filled, the shared budget drops. When the budget reaches zero, no offer in the group can be filled, regardless of how many are still signed and floating.

In other words, a maker can quote across a new 9-month maturity *without locking a single dollar*. They add depth for free, borrowers see a usable book, fills happen, and the market bootstraps. The barrier to launching a new collateral configuration or maturity drops from "convince someone to lock real capital in a market with unproven demand" to "convince someone to sign an offer."

A multi-market offer lets a maker post **one balance across many books simultaneously**. The same dollar is take-able in every linked market, but can only be filled once. Exposure is bounded by the shared balance, not by the sum of all the offers' sizes.

Steps:

1. Sign the basket: One signature over a Merkle root of all offers in the group
2. Distribute: Picked up by Morpho’s router
3. A taker fills one offer: Settlement updates the group's shared consumed; the taker supplies the Merkle proof
4. Update balance: Remaining budget = `budget - consumed`. Every linked offer is now fillable only up to that.

### [Validate before publishing](#validate-before-publishing)

All offers in one batch must share the same maker and ratifier. The router [validates](https://docs.morpho.org/developers/midnight/concepts/mempool-router/#validating-offers) the full payload including group consistency. If “group_identity” or “group_consistency” appears in issues, the group ID doesn't match the content hash of the offers, or the offers disagree on loan token / side / max expression.

`POST /v0/midnight/mempool/validate`

```
POST /v0/midnight/mempool/validate
{
  "chain_id": 8453,
  "payload": "0x01..."   // version + gzip(ABI-encoded (Offer, ratifierData)[])
}
```

### [Monitoring the group](#monitoring-the-group)

After publishing, track the group's fill progress across all markets.

Each offer shows max_assets: "21000000" (the original offer size), but consumed: "10000000" at the group level means only 11 USDC is actually takeable across all three. The budget lives on the group, not the individual offer.

`GET /v0/midnight/users/{user-address}/offer-groups`

```
GET /v0/midnight/users/{makerAddress}/offer-groups?groups={groupId}

// Response excerpt (other fields omitted; values are illustrative)
{
  "data": [
    {
      "id":         "0xGroupId...",
      "chain_id":   8453,
      "max_assets": "21000000",              // 21 USDC budget for the whole group
      "max_units":  "0",                     // budget expressed in assets, not units
      "consumed":   "10000000",              // 10 USDC filled so far (across all markets)
                                             // remaining budget: 21 − 10 = 11 USDC
      "created_at": 1719000000,
      "expiry":     1719604800,              // latest expiry across all offers in the group
      "offers": [
        {
          "market_id": "0xCbBTC-Dec26...",   // cbBTC market — this is where the 10 was filled
          "buy":       true,                 // buy offer = lend side
          "tick":      -42,
          "max_assets": "21000000",          // each offer reads "up to 21" individually
          "maker":     "0xMaker...",
          "start":     1719000000,
          "expiry":    1719604800
        },
        {
          "market_id": "0xWETH-Dec26...",    // wETH market — still live, up to 11 remaining
          "buy":       true,
          "tick":      -43,
          "max_assets": "21000000",
          "maker":     "0xMaker...",
          "start":     1719000000,
          "expiry":    1719604800
        },
        {
          "market_id": "0xWstETH-Dec26...",  // wstETH market — still live, up to 11 remaining
          "buy":       true,
          "tick":      -41,
          "max_assets": "21000000",
          "maker":     "0xMaker...",
          "start":     1719000000,
          "expiry":    1719604800
        }
      ]
    }
  ]
}
```

There is no active "rebalancing service" doing this. Every offer in the group reads the same onchain `consumed` counter, so a fill in one market is simply visible to all the others as less budget left. The offers don't shrink, the shared budget they all draw on does.

**Example**

A maker posts a **21 USDC** budget across three markets (one consumption group). Each offer reads "take-able up to 21." A taker fills **10 USDC** on the cbBTC market. The shared budget is now **11,** so the wETH and wstETH offers immediately read "take-able up to 11," not 21. The books stay firm: the full remaining balance is take-able on any single market until it's gone.

Without the shared budget, quoting 21 USDC on three markets would mean committing 63 USDC of capital (or risk being over-filled). With one consumption group the maker commits 21 and is present in all three books.

Signing a separate offer for every market would not scale (a maker quoting twenty markets would sign twenty times). Instead, a ratifier can ratify a **Merkle root of an offer set**: the maker commits to the entire basket with a single signature or interaction, and each individual offer is taken later by presenting its **Merkle proof** as part of the ratifier data.

So the two mechanics compose:

1. The **Merkle root** makes a large basket cheap to authorize.
2. The **consumption group** makes that basket safe to leave outstanding by capping total fills at the shared budget.

### [Fetch takeable offers](#fetch-takeable-offers)

A taker (or your frontend) can fetch all active offers from a maker, filtered by group. Offers with units: "0" are in the group but currently not executable (budget exhausted, expired, or not yet started).

`GET /v0/midnight/takeable-offers`

```
GET /v0/midnight/takeable-offers?maker={makerAddress}&groups={groupId}

// Response excerpt (other fields omitted; values are illustrative)
{
  "data": [
    {
      "market_id":     "0xWETH-Dec26...",
      "units":         "11550000",           // max takeable units (derived from 11 USDC remaining)
      "ratifier_data": "0xMerkleProof...",   // Merkle proof for this specific offer
      "offer": {
        "buy": true, "tick": -43,
        "maker": "0xMaker...", "ratifier": "0xMerkleRatifier...",
        "group": "0xGroupId...", "max_assets": "21000000",
        // ... full offer struct
      }
    },
    {
      "market_id":     "0xWstETH-Dec26...",
      "units":         "11470000",
      "ratifier_data": "0xMerkleProof...",
      "offer": { "buy": true, "tick": -41, ... }
    }
    // cbBTC offer might show units: "0" if its remaining budget is fully consumed
  ]
}
```

One signature, many markets, bounded exposure.

[Callbacks

Previous Page

](https://docs.morpho.org/developers/midnight/concepts/callbacks/)[Tick Structure

Next Page

](https://docs.morpho.org/developers/midnight/concepts/tick-structure/)