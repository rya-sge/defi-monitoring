# Display positions

> Source: https://docs.morpho.org/developers/midnight/tutorials/display-positions

---

# Display positions

Midnight state is spread across three places a portfolio view has to read separately:

| What the user sees | Where it lives | How to read it |
| --- | --- | --- |
| Lend, borrow and collateral positions | Midnight positions | Positions API endpoints, or the SDK for a same-block read |
| Offers waiting to be taken | Offer groups | `GET /v0/midnight/users/{userAddress}/offer-groups` |
| Assets deposited behind a callback-backed buy offer | A Morpho Blue supply position owned by the callback contract | Offer group `callback` metadata + a Morpho Blue position read |

This tutorial walks through each one and the values you can show for it.

## [**Choose the value to display**](#choose-the-value-to-display)

A Midnight position has two values. Each answers a different question.

| Value | Lender | Borrower | Meaning |
| --- | --- | --- | --- |
| **At maturity** | `credit - pending_fee` | `debt` | What the lender receives, or the borrower owes, at maturity. Deterministic from position state. |
| **Exit now** | Bids quote for available `credit` units | Asks quote for available `debt` units | What the user would receive (lender) or pay (borrower) to close the position now, on the current offer book. Available units leave out units already promised to the user's own resting exit offers. |

The maturity value needs no price: one unit is worth one loan-token unit at maturity, so it does not move with the book. The exit-now value changes with liquidity and can be unavailable. A lender exit sells all available `credit` units, not `credit - pending_fee`: each sold unit takes its share of `pending_fee` with it, so quoting fewer units would leave a residual position. Units promised to resting exit offers close at those offers' prices when they are taken, so you can show them as open exit offers next to the quote ([Quote an early exit](#quote-an-early-exit)).

### [If users can act on their positions](#if-users-can-act-on-their-positions)

If you integrate the whole stack and let users exit or repay from your app, you can display both values:

- **[Maturity value](#fetch-positions-and-maturity-values):** the headline figure ("Loan at maturity": principal plus interest).
- **[Exit-now value](#quote-an-early-exit):** priced against the book inside the exit flow, next to the maturity value, when the user can act on it.

### [If you only display positions](#if-you-only-display-positions)

A wallet or portfolio tracker can show the [maturity value](#fetch-positions-and-maturity-values) alone. In that case, say so next to the figure, for example: *"Value at maturity. Closing before maturity depends on offer book liquidity and can return less."*

### [Matured positions](#matured-positions)

Once maturity has passed there is nothing left to price. A lender redeems units 1:1 for loan tokens, as liquidity allows, and a borrower repays `debt`. Only the maturity value applies.

### [Open offers](#open-offers)

Open offers are not positions yet, so they have neither value. You can list them next to positions as open offers, with their remaining size (see [Fetch open offers](#fetch-open-offers)). Keep them out of the position total: a plain offer's funds are still in the maker's wallet, and a callback-backed offer's funds are a Morpho Blue supply position of the callback contract (see [Show callback-backed offers](#show-callback-backed-offers)). Adding the offer size on top would count the same funds twice.

## [**Fetch positions and maturity values**](#fetch-positions-and-maturity-values)

Read position state from the Midnight API or onchain with the SDK. The balances give the maturity value directly and collateral as-is; the exit-now value needs a quote ([next section](#quote-an-early-exit)).

### [With the API](#with-the-api)

List every Midnight position for a wallet. The endpoint already leaves out closed positions with no credit, no debt and no collateral left. Leave `active_only` off to keep matured positions: `active_only=true` drops every position whose market has matured.

`GET /v0/midnight/users/{user-address}/positions`

```
GET https://api.morpho.org/v0/midnight/users/{userAddress}/positions
  ?chain_ids=8453

// Response (one entry per market the user holds)
{
  "cursor": null,              // pass back as ?cursor= to read the next page
  "data": [
    {
      "chain_id": 8453,
      "market_id": "0x2569…",
      "user_address": "0x7b09…",
      "loan_token": "0x8335…",   // USDC on Base
      "maturity": 1793491199,    // unix seconds
      "type": "lend",            // "lend" | "borrow" | "collateral_only"
      "credit": "1012000000",    // gross lender credit, in loan-token units
      "pending_fee": "2000000",  // continuous fee not yet accrued, still inside credit
      "debt": "0",               // borrower debt, in loan-token units
      "collaterals": [],         // [{ token, amount }] for borrowers
      "cost_basis": "…",         // WAD-scaled, null when unavailable
      "effective_rate_wad": "…", // annualized, WAD-scaled, null when unavailable
      "last_loss_factor": "0",
      "loss_factor": "0",
      "created_at": 1790000000
    }
  ]
}
```

- For a single market, [`GET /v0/midnight/markets/{marketId}/users/{userAddress}/position`](https://docs.morpho.org/api/midnight/positions/get-position/) returns the same balances plus `last_indexed_block`, the latest block the API had indexed when it computed the payload.
- For cost basis and effective rate history, use [`GET /v0/midnight/markets/{marketId}/users/{userAddress}/position/performance`](https://docs.morpho.org/api/midnight/positions/get-midnight-position-performance/).
- To compute a lender's maturity value, use `credit - pending_fee`, not raw `credit`. `credit` still contains the continuous fee that can accrue to the protocol before maturity, so showing it overstates the position. If the API returns a `loss_factor` higher than `last_loss_factor`, the market has absorbed bad debt since the position was last updated and the indexed `credit` is not yet reduced: use the [SDK read](#with-the-sdk), whose accrual applies the loss and reduces `pending_fee` in proportion.

See [List positions](https://docs.morpho.org/api/midnight/positions/list-positions/) for the full response schema, and the [Midnight API overview](https://docs.morpho.org/developers/api/morpho-midnight/#position-tracking) for how positions fit with the other endpoints.

### [With the SDK](#with-the-sdk)

If the screen must match the chain at a given block (for example right before building a transaction), read the position with the SDK and accrue it to that block's timestamp:

```
import { type Address, createPublicClient, http } from "viem";
import { base } from "viem/chains";
import { morphoViemExtension } from "@morpho-org/morpho-sdk";

// A read-only client is enough: nothing is signed here.
const client = createPublicClient({
  chain: base,
  transport: http(process.env.BASE_RPC_URL),
}).extend(morphoViemExtension());

const midnight = client.morpho.midnight(base.id);

const block = await client.getBlock();

// Read at one block, then accrue to that block's timestamp: accrual applies any
// market loss and moves the accrued part of the pending fee out of credit.
const position = (
  await midnight.getPositionData({
    marketId,
    accountAddress: user,
    parameters: { blockNumber: block.number },
  })
).accrueInterest(block.timestamp);

position.faceValue; // credit - pendingFee: what a lender receives at maturity
position.debt;      // what a borrower owes at maturity
```

See [Morpho SDK: Midnight](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/#reading-onchain-state) for the other onchain reads.

### [Collateral](#collateral)

Borrow positions and `collateral_only` positions list their collateral as `collaterals: [{ token, amount }]`. Show each entry as its own row next to the debt. A `collateral_only` position has no maturity value or exit-now value: it is collateral deposited in a market with no outstanding debt.

## [**Quote an early exit**](#quote-an-early-exit)

Before maturity, price the whole position against the side of the book that closes it:

- A lender sells units, which takes **bids** (buy offers).
- A borrower buys back units to cancel debt, which takes **asks** (sell offers).

Quote by `units`. A full exit closes the units not already promised to the user's own resting exit offers: `credit` (lender) or `debt` (borrower), minus what can still be taken from those offers (see [Fetch open offers](#fetch-open-offers)). Selling the promised units too would make those offers revert when a taker reaches them. The API's `credit` is the balance at the position's last update; for an exact unit count, use the accrued `position.credit` from the [SDK read](#with-the-sdk).

```
import { MidnightApi } from "@morpho-org/morpho-sdk/midnight-api";

const WAD = 10n ** 18n;

// Lender: sell every credit unit into the bids. Borrower: buy back `debt` units
// from the asks.
const side = position.type === "lend" ? "bids" : "asks";
const positionUnits =
  position.type === "lend"
    ? BigInt(position.credit) // pending_fee leaves with the sold units
    : BigInt(position.debt);
// `reservedUnits`: units that can still be taken from the user's own resting exit offers on this market.
const units = positionUnits > reservedUnits ? positionUnits - reservedUnits : 0n;

try {
  // GET /v0/midnight/books/{marketId}/{side}/quote?units=…
  const quote = await MidnightApi.fetchBookQuote({ marketId, side, units });

  // Value of `units` at the realized average price, rounded against the user:
  // down for what a lender receives, up for what a borrower pays.
  const price = BigInt(quote.data.averageBestPrice);
  const exitNowAssets =
    side === "bids" ? (units * price) / WAD : (units * price + WAD - 1n) / WAD;
} catch (error) {
  // A 422 means the book can't take the whole position right now (see below).
}
```

Read the result carefully:

- `units × average_best_price / 1e18`, rounded against the user, is the value of the requested units. Use it as the exit-now value. `average_best_price` is itself rounded, so the actual amount taken can differ by a few base units; for the exact amount, sum the amounts taken from the returned takeable offers.
- Don't use `available_assets` as the position's value. It is the total liquidity in the returned offers, which can exceed the target so a bundle has fallback liquidity.
- A `422` means the book cannot take the whole position right now. You can show the exit-now value as unavailable, or show what the book can absorb: quote a smaller `units` target and show the quoted value next to the units left unquoted. That side's price levels from [`GET /v0/midnight/books/{marketId}/{side}`](https://docs.morpho.org/api/midnight/books/list-book-price-levels/) give a starting size, but they can list more than the quote endpoint can execute, so the smaller quote can also return a `422`. Either way, don't present part of the position as if it were all of it.
- A quote is a snapshot. Refresh it on an interval while it's on screen, and get a fresh one before submitting an exit.

To execute the exit, pass the quote's takeable offers to a target-aware bundle. If you call `Midnight.take` directly, clamp each offer to your remaining target. This tutorial doesn't cover executing an exit.

## [**Fetch open offers**](#fetch-open-offers)

An offer that hasn't been taken yet is not a position: it doesn't appear in the positions endpoints until a taker takes it. List a user's resting offers from their offer groups:

`GET /v0/midnight/users/{user-address}/offer-groups`

```
GET https://api.morpho.org/v0/midnight/users/{userAddress}/offer-groups
  ?chain_ids=8453
  &status=active        // default; "expired" lists groups whose offers have all expired or matured

// Response (one entry per offer group)
{
  "cursor": null,
  "data": [
    {
      "id": "0x…08b8f4",
      "chain_id": 8453,
      "expiry": 1793400000,      // latest expiry among the group's live offers
      "max_units": "0",          // the group's cap is in units when max_assets is 0...
      "max_assets": "5000000000", // ...and in assets otherwise
      "consumed": "1000000000",  // taken so far, shared by every offer in the group
      "callback": null,          // verified callback metadata (see next section)
      "offers": [
        {
          "market_id": "0x2569…",
          "buy": true,           // true: lend / repay side, false: borrow / exit side
          "tick": 495
          // …full signed offer fields
        }
      ]
    }
  ]
}
```

Show each group as an open offer, not as a position:

- **Remaining size:** the group's cap minus `consumed`. Use `max_assets` when it is non-zero, otherwise `max_units`. A group is one budget shared across all its offers, so don't add the offers' sizes together. A cap of `2^128 - 1` (the `uint128` maximum) means no stated limit: the size is then whatever backs the offer (the wallet balance and allowance, or the callback's Blue supply), not the cap minus `consumed`. See [Multi-market offers](https://docs.morpho.org/developers/midnight/concepts/multi-market-offers/).
- **Price and maturity:** from each offer's `tick` and its market.
- **Funds:** a plain buy offer (its `callback` is the zero address) leaves the loan tokens in the maker's wallet until it is taken. They already appear in the wallet balance, so don't add them to the portfolio total a second time.

When an offer is taken, the maker gets a Midnight position and it appears in the positions endpoints.

## [**Show callback-backed offers**](#show-callback-backed-offers)

A buy offer can be funded by a callback instead of the maker's wallet. With the `blue_buy` callback, the maker's loan tokens sit in a Morpho Blue market and earn the variable rate until a taker takes the offer. At settlement the callback withdraws exactly the amount taken from Blue and hands it to Midnight. See [Callbacks](https://docs.morpho.org/developers/midnight/concepts/callbacks/).

A `BlueBuyCallback` contract belongs to one maker, and that contract owns the Morpho Blue supply position. The factory creates a callback the first time a maker uses a given salt and returns the same one afterwards, so the maker's choice of salt decides how offers share callbacks. The contracts allow one callback to back several of the maker's buy offers, and each offer names the Blue market it withdraws from. The Morpho fixed-rate app derives the salt from the offer group, so it creates one callback per offer group: all offers of one offer group share a callback, and a new group gets a new one. A view that reads Morpho Blue positions by the user's address therefore misses these funds. Two rules keep the portfolio correct:

1. **Before the offer is taken**, the funds are a Morpho Blue supply position owned by the callback contract. Show them under the maker as funds backing an open Midnight offer, not as a Midnight position.
2. **After the offer is taken**, the Midnight position belongs to the maker, not to the callback. The callback only supplies the funds, so the resulting position appears in the maker's positions like any other lend.

Find callback-backed groups with `callback_type=blue_buy`. The API fills in `callback` only for verified callbacks: canonical Blue market params and a callback registered to the maker in the official [factory](https://docs.morpho.org/developers/contracts/addresses/#morpho-midnight) (`BlueBuyCallback Factory`) at or before the offer was created. `callback: null` means no *verified* callback, not no callback. A group is a plain, wallet-funded offer only when its offers' own `callback` field is the zero address. When an offer names an unverified callback, the API can't tell where its funds are, so don't count them in the wallet or in a Blue position.

```
GET https://api.morpho.org/v0/midnight/users/{userAddress}/offer-groups
  ?chain_ids=8453&callback_type=blue_buy

// The `callback` object on each returned group
"callback": {
  "type": "blue_buy",
  "callback_address": "0x…",   // the maker's BlueBuyCallback: owner of the Blue position
  "market_id": "0x…",          // the Morpho Blue market holding the funds
  "market_params": {
    "loan_token": "0x…",
    "collateral_token": "0x…",
    "oracle_address": "0x…",
    "irm_address": "0x…",
    "lltv_wad": "…"
  }
}
```

Read the callback's Blue supply to show how much is deposited:

```
import { fetchAccrualPosition } from "@morpho-org/morpho-sdk/blue/fetch";

// The Blue position is keyed by the callback contract, not by the maker.
const bluePosition = (
  await fetchAccrualPosition(
    group.callback.callback_address,
    group.callback.market_id,
    client,
  )
).accrueInterest(BigInt(Math.floor(Date.now() / 1000)));

const depositedAssets = bluePosition.supplyAssets; // loan tokens earning the Blue rate
```

What can actually be taken from the offer is the smaller of the group's remaining size and the callback's Blue supply, further limited by Blue's withdrawable liquidity at settlement. When the remaining size is in units (`max_units`), convert it to assets at the offer price (`units × price / 1e18`) before comparing. Show both numbers when they differ, and hide groups whose Blue supply has dropped to zero, since nothing backs them anymore. Funds stay in the callback's Blue position after the offer expires or is cancelled until the maker withdraws them, so also query `status=expired` callback groups to find balances still deposited. Three kinds of group appear in neither list, though their callback can still hold supply: groups whose offers haven't started yet (until one starts), groups fully taken before they expire (until their offers expire), and groups hard-cancelled with `SetConsumed(maxUint128)`. To keep tracking those, store the callback address when the offer is created, or read it from the factory with `callbackOf(maker, salt)` or its `CreateBlueBuyCallback` events.

## [**Putting it together**](#putting-it-together)

| Situation | Source | Show |
| --- | --- | --- |
| Lend, before maturity | Positions | Maturity value `credit - pending_fee` Optional exit-now (bids quote) |
| Borrow, before maturity | Positions | Debt at maturity `debt`, collateral Optional repay-now (asks quote) |
| Matured | Positions | Maturity value only |
| Collateral only | Positions | Collateral balances |
| Open offer | Offer groups with `status=active` | Remaining size, price, maturity, expiry Not a position |
| Callback offer, open | Offer groups with `callback_type=blue_buy`, plus the Blue position of `callback_address` | Deposited Blue supply under the maker Takeable size |
| Callback offer, taken | Positions | Regular lend position of the maker |

[Exit borrow early

Previous Page

](https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-early/)[Guide: How to Monetize Your Midnight Product

Next Page

](https://docs.morpho.org/developers/midnight/guides/monetize-midnight-product/)