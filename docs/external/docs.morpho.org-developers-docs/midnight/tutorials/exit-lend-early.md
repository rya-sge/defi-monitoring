# Exit lend early

> Source: https://docs.morpho.org/developers/midnight/tutorials/exit-lend-early

---

# Exit lend early

A lender doesn't have to wait for maturity to exit. Before maturity, credit units can be sold to resting **buy offers** (bids): the lender takes those offers, gives up the units, and receives loan tokens now at the bid price instead of face value at maturity.

The exit runs through `MidnightBundlesV1` with `reduceOnly = true`. Reduce-only is a check, not a cap: every take is checked onchain against the taker's remaining credit, and a take that would exceed it reverts the whole transaction rather than being clamped - an exit can never turn surplus units into new debt. These calls go to `MidnightBundlesV1`, the Bundles contract at the Morpho SDK's `midnightBundles` address, which markets.morpho.org also uses. Its functions are prefixed `midnightBundlesV1`; don't mix them with another Bundles version's address or authorization.

The Morpho SDK taker flows hard-code `reduceOnly = false` and don't expose a reduce-only exit at this version, so this tutorial uses the raw `MidnightBundlesV1` calls - with the SDK still used for quoting. See [Taker flows](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/#taker-flows) for the SDK surface.

Snippets assume a [viem wallet client](https://viem.sh/docs/clients/wallet) `walletClient` for your account on Base, and `taker` set to your wallet address.

## [**Read the position**](#read-the-position)

The REST API is the quickest way to inspect the position. It returns the stored, indexed values and can lag a few blocks. To size the transaction, run the SDK read or the direct contract read: they return the live, accrued values that the next steps use.

### [REST API](#rest-api)

Fetch the lender's position to get its credit and pending fee:

```
GET https://api.morpho.org/v0/midnight/markets
  /{marketId}/users/{userAddress}/position

// Response
{
  "data": {
    "chain_id":           8453,
    "market_id":          "0xd92de5e7fbb...7614",               // market the lender lent into
    "user_address":       "0xYourWalletAddress",
    "last_indexed_block": "47457420",
    "loan_token":         "0x8335...2913",                      // USDC
    "maturity":           "1798761600",
    "type":               "lend",                               // "lend" | "borrow" | "collateral_only"
    "credit":             "10500000000",                        // credit units held - what the exit sells
    "debt":               "0",
    "pending_fee":        "12000",                              // continuous fee accrued, not yet deducted from credit
    "last_loss_factor":   "0",
    "loss_factor":        "0",
    "collaterals":        []                                    // lenders post no collateral
  }
}

// Inspection only - size the transaction from the SDK or direct contract read below.
```

### [SDK](#sdk)

The SDK reads the same position through `midnight.getPositionData`, accrued to the latest block:

```
import { publicActions } from "viem";
import { morphoViemExtension } from "@morpho-org/morpho-sdk";

// Extend the wallet client with the `morpho` namespace and the public reads
// the SDK needs.
const client = walletClient.extend(morphoViemExtension()).extend(publicActions);
const midnight = client.morpho.midnight(8453); // Midnight entity for Base

// The extended client doubles as the public client the execute snippet reads with.
const publicClient = client;

// Accrued position at the latest block - positionData.credit and
// positionData.pendingFee are the same values updatePositionView returns as
// newCredit / newPendingFee in the direct contract read below.
const block = await client.getBlock();
const positionData = (
  await midnight.getPositionData({
    marketId,
    accountAddress: taker,
    parameters: { blockNumber: block.number },
  })
).accrueInterest(block.timestamp);

// market = the Market struct - from GET /v0/midnight/markets/{marketId} or a prior browse step

// Deadline for the exit transaction - the fee buffer below is sized to it
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600); // 1 hour from now
const now = block.timestamp;

// Pending fee accrues linearly until maturity, so credit shrinks between this
// read and execution - buffer the target by the fee accrued before the
// deadline, or the take reverts `NotReduceOnly`. The buffer is measured from
// the snapshot block, so it also covers the fee accrued between the read and
// now. Fee accrual stops at maturity, so the projection end is capped there.
const accrualEnd = deadline < BigInt(market.maturity) ? deadline : BigInt(market.maturity);
const feeBuffer =
  positionData.pendingFee === 0n || BigInt(market.maturity) <= now
    ? 0n
    : (positionData.pendingFee * (accrualEnd - now) + BigInt(market.maturity) - now - 1n) /
      (BigInt(market.maturity) - now); // ceil(pendingFee x (accrualEnd-now) / (maturity-now)), capped at maturity

// Full-exit units target: accrued credit minus the fee buffer. The buffer
// leaves a small remainder - exit it with the partial exit below or redeem it
// at maturity.
const targetUnits = positionData.credit - feeBuffer;
if (targetUnits <= 0n) throw new Error("nothing to sell after the fee buffer");
```

### [Onchain (direct contract read)](#onchain-direct-contract-read)

A full exit must be sized to the exact sellable credit right now - and slightly below it: the pending fee accrues linearly until maturity, so the read is stale by the time the transaction lands and the target must be buffered for the fee that accrues before its deadline. The sell-side bundle enforces `reduceOnly` against `updatePositionView`'s post-accrual `newCredit`, not the raw `credit` getter - the stored value is stale relative to loss-factor application and pending fee accrual, and targeting it would revert `NotReduceOnly`.

```
import { createPublicClient, http } from "viem";
import { base } from "viem/chains";
import { midnightAbi } from "@morpho-org/morpho-sdk/abis";

const MIDNIGHT = "0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A"; // Midnight on Base (from the @morpho-org/morpho-ts address registry)

const publicClient = createPublicClient({ chain: base, transport: http() });

// market = the Market struct - from GET /v0/midnight/markets/{marketId} or a prior browse step
const block = await publicClient.getBlock();
const [newCredit, newPendingFee, accruedFee] = await publicClient.readContract({
  address: MIDNIGHT,
  abi: midnightAbi,
  functionName: "updatePositionView",
  args: [market, marketId, taker],
  blockNumber: block.number,
});

// Deadline for the exit transaction - the fee buffer below is sized to it
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600); // 1 hour from now
const now = block.timestamp;

// Pending fee accrues linearly until maturity, so newCredit shrinks between
// this read and execution - buffer the target by the fee accrued before
// the deadline, or the take reverts `NotReduceOnly`. The buffer is measured
// from the snapshot block, so it also covers the fee accrued between the
// read and now. Fee accrual stops at maturity, so the projection end is
// capped there.
const accrualEnd = deadline < BigInt(market.maturity) ? deadline : BigInt(market.maturity);
const feeBuffer =
  newPendingFee === 0n || BigInt(market.maturity) <= now
    ? 0n
    : (newPendingFee * (accrualEnd - now) + BigInt(market.maturity) - now - 1n) /
      (BigInt(market.maturity) - now); // ceil(newPendingFee x (accrualEnd-now) / (maturity-now)), capped at maturity

// Full-exit units target: post-accrual credit minus the fee buffer. The raw
// `credit` getter is stale for this purpose (loss factor / pending fee).
// The buffer leaves a small remainder - exit it with the partial exit
// below or redeem it at maturity.
const targetUnits = newCredit - feeBuffer;
if (targetUnits <= 0n) throw new Error("nothing to sell after the fee buffer");
```

## [**Get a quote**](#get-a-quote)

A lend exit takes **bids** - makers buying units. Quote against the bid side: `units` for a full exit (sell all available credit), `assets` for a partial one (sell down to a loan-token amount).

### [REST API](#rest-api-1)

```
GET https://api.morpho.org/v0/midnight/books/{marketId}/bids/quote
  ?units=10500000000   // sellable credit units (full exit); use assets= for a partial
  &slippage=0.5        // 0.5% slippage guard
  &limit=10000         // max offers walked/returned; default and maximum 10,000

// Response: the router's execution plan
{
  "data": {
    "average_best_price": "947619047619047619",  // realized target take using onchain per-offer rounding, rounded against the taker
    "average_worst_price": "943000000000000000", // conservative adverse-placement bound across returned caps - below best for bids and inside the 0.5% slippage guard
    "available_assets": "9969975000",            // max loan-token payout in this returned limit window (includes fallback excess, so it exceeds the target payout)
    "available_units": "10500000000",            // max units in this returned limit window
    "takeable_offers": [
      {
        "market_id": "0x56b822d7d8be6bded8e1782277989fe5dc4e5b0a4f7f9d349482bc933bd5436c",
        "units": "5250000000",  // maximum this offer may contribute, not an exact allocation
        "offer": { /* … buy offer (bid): the maker is lending … */ },
        "ratifier_data": "0x4a8b...f201"
      }
      // Additional complete offers follow in best-price order as fallback excess.
    ]
  }
}

// Interpreting the quote
const quote = response.data;
const avgPrice = Number(quote.average_best_price) / 1e18;   // ≈ 0.9476 per unit
const expectedPayout = BigInt(Math.floor(10_500e6 * avgPrice)); // ≈ 9,950 USDC received
// Price guard: a seller's floor sits below the quote - minSellerAssets
// uses the same units × worst-acceptable-price formula as the exit call
const minSellerAssets = BigInt(Math.floor(10_500e6 * 0.94));
// NOTE: a full exit targets the *available* credit - units already backing
// your own resting reduce-only sell offers are committed elsewhere.
```

### [SDK](#sdk-1)

`MidnightApi.fetchBookQuote` wraps the quote endpoint and returns ABI-ready take objects:

```
import { MidnightApi, type MidnightApiTake } from "@morpho-org/morpho-sdk/midnight-api";

// SDK wraps the quote endpoint and maps the response into ABI-ready take
// objects (uses Morpho's router by default, no config needed)
const quote = await MidnightApi.fetchBookQuote({
  marketId,
  side:     "bids",               // exiting lender takes bids (not asks)
  units:    targetUnits,          // sellable credit units
  slippage: "0.5",                // 0.5% slippage guard
});

// ABI-ready takes
const takes: MidnightApiTake[] = quote.data.takeableOffers;
```

There is no onchain quote: offers are signed and published offchain, not stored in the Midnight contract.

## [**Authorize MidnightBundlesV1**](#authorize-midnightbundlesv1)

The bundle pays the lender rather than pulling tokens from them, so no ERC-20 approval is needed - only the one-time `MidnightBundlesV1` authorization on the Midnight contract:

```
import { midnightAbi } from "@morpho-org/morpho-sdk/abis";

const MIDNIGHT_BUNDLES = "0x091183d729BE9f808c212b475E387A12E67850A7";   // MidnightBundlesV1 on Base (from the @morpho-org/morpho-ts address registry)
const MIDNIGHT         = "0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A";   // Midnight on Base (from the registry)

// Authorize MidnightBundlesV1 to act on your position (one-time boolean, persists across future actions)
// Wait for the transaction to confirm before the exit call below.
const hash = await walletClient.writeContract({
  account: taker,
  address: MIDNIGHT,
  abi: midnightAbi,
  functionName: "setIsAuthorized",
  args: [MIDNIGHT_BUNDLES, true, taker],
});
const receipt = await publicClient.waitForTransactionReceipt({ hash });
if (receipt.status !== "success") throw new Error("MidnightBundlesV1 authorization failed");
```

## [**Execute the exit**](#execute-the-exit)

Pick a full exit (sell all available credit, sized in units) or a partial exit (sell down to a loan-token amount). Both calls take the quote's offers in one transaction, skipping stale offers.

### [Full exit: sell all credit](#full-exit-sell-all-credit)

`targetUnits` is the position's sellable credit from the onchain read. `minSellerAssets` is the price guard: the fewest loan tokens you'll accept for those units - derive it from a worst-acceptable price below the quote's average, and the bundle reverts if the take would pay less.

```
import { midnightBundlesAbi } from "@morpho-org/morpho-sdk/abis";
import { maxUint256, zeroAddress } from "viem";

const MIDNIGHT_BUNDLES = "0x091183d729BE9f808c212b475E387A12E67850A7";   // MidnightBundlesV1 on Base (from the registry)

// Price guard: the fewest loan tokens accepted for targetUnits -
// reverts if the take pays below a 0.94 average price
const worstAcceptablePrice = 0.94;
const minSellerAssets = BigInt(Math.floor(Number(targetUnits) * worstAcceptablePrice));

// deadline comes from the position read above - the transaction reverts
// if not included before it
const hash = await walletClient.writeContract({
  account: taker,
  address: MIDNIGHT_BUNDLES,
  abi: midnightBundlesAbi,
  functionName: "midnightBundlesV1SupplyCollateralAndSellWithUnitsTarget",
  args: [
    targetUnits,         // credit units to sell - from the updatePositionView read
    minSellerAssets,     // revert if fewer loan tokens returned (price guard)
    taker,               // taker (the exiting lender)
    true,                // reduceOnly (true - this is an exit, never sell past held credit)
    taker,               // receiver (loan tokens go back to the lender)
    [],                  // collateralSupplies (empty - exits supply none)
    takes,               // the takeable offers from the quote (ABI-encoded)
    0n,                  // referralFeePct (0 = none)
    zeroAddress,         // referralFeeRecipient (none)
    maxUint256,          // maxContinuousFee (type(uint256).max disables the check)
    deadline             // deadline (reverts if tx is included after this timestamp)
  ],
});

// Units backing your own resting reduce-only sell offers are already
// committed - size targetUnits to the available credit (or cancel those
// offers first), or they revert when taken.

console.log("Exit tx:", hash);
```

### [Partial exit: sell down to an amount](#partial-exit-sell-down-to-an-amount)

`targetSellerAssets` is how many loan tokens to receive. `maxUnits` is the price guard: the most credit units you'll give up for them - derive it from a worst-acceptable price (units = loan tokens / price, rounded up), and the bundle reverts if the take would cost more units.

```
import { midnightBundlesAbi } from "@morpho-org/morpho-sdk/abis";
import { maxUint256, parseUnits, zeroAddress } from "viem";

const MIDNIGHT_BUNDLES = "0x091183d729BE9f808c212b475E387A12E67850A7";   // MidnightBundlesV1 on Base (from the registry)

const targetSellerAssets = parseUnits("5000", 6);   // 5,000 USDC to receive

// Price guard: the most credit units given up for the payout -
// reverts if the take happens below a 0.94 average price
const worstAcceptablePrice = 0.94;
const maxUnits = BigInt(Math.ceil(5_000e6 / worstAcceptablePrice));

const hash = await walletClient.writeContract({
  account: taker,
  address: MIDNIGHT_BUNDLES,
  abi: midnightBundlesAbi,
  functionName: "midnightBundlesV1SupplyCollateralAndSellWithAssetsTarget",
  args: [
    targetSellerAssets,  // loan tokens to receive
    maxUnits,            // revert if more units would be sold (price guard)
    taker,               // taker (the exiting lender)
    true,                // reduceOnly
    taker,               // receiver
    [],                  // collateralSupplies
    takes,               // takeable offers from the quote
    0n,                  // referralFeePct
    zeroAddress,         // referralFeeRecipient
    maxUint256,          // maxContinuousFee
    deadline             // deadline
  ],
});

console.log("Partial exit tx:", hash);
```

## [**Exit at a chosen price**](#exit-at-a-chosen-price)

Instead of taking bids now, a lender can publish a resting **reduce-only sell offer** at a chosen tick: it stays published until it is taken, cancelled or expires, and closes credit only when another user takes it at that price. Reduce-only keeps the offer from ever borrowing beyond the credit it backs.

On the SDK, sell-side maker offers are posted through `makeBorrow` (the flow validates `buy: false` offers):

```
import { addresses } from "@morpho-org/morpho-ts";
import { Offer } from "@morpho-org/midnight-sdk";
import { parseUnits } from "viem";

const chainId = 8453;
const ecrecoverRatifier = addresses[chainId].ecrecoverRatifier!; // EcrecoverRatifier on Base (from the registry)
// `midnight` = the MorphoMidnight entity built in the SDK page's Maker flows section

// Resting sell offer: closes credit only when taken at this tick's price
const exitOffer = Offer.create({
  market,                       // market params (as on the SDK page)
  maker: taker,
  buy: false,                   // maker sells units
  reduceOnly: true,             // can only consume held credit - pure exit
  tick: 5_000n,                 // chosen price tick
  maxUnits: targetUnits,        // credit units this offer may sell
  // now + 7 days, capped at the market's maturity
  expiry: BigInt(Math.min(Number(market.maturity), Math.floor(Date.now() / 1000) + 604_800)),
  ratifier: ecrecoverRatifier,
});

const make = await midnight.makeBorrow({
  accountAddress: taker,
  offers: [exitOffer],
});
// …dispatch make.getRequirements() (ratifier signing / root approval), then buildTx()

// Credit units committed to this offer are excluded from a full taker
// exit's available amount - take or cancel first if you need both.
```

See [Maker flows](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/#maker-flows) for the full pipeline (grouping, tree, ratification, mempool publication).

[Exit borrow at maturity

Previous Page

](https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-by-repaying-in-full-at-maturity/)[Exit borrow early

Next Page

](https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-early/)