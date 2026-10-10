# Exit borrow early

> Source: https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-early

---

# Exit borrow early

A borrower doesn't have to wait for maturity to close a position. Before maturity, the borrower can buy units from resting **sell offers** (asks): the units retire debt directly, at the ask price - less than face value - instead of repaying in full at maturity.

The exit runs through `MidnightBundlesV1` with `reduceOnly = true`. Reduce-only is a check, not a cap: every take is checked onchain against the taker's outstanding debt, and a take that would exceed it reverts the whole transaction rather than being clamped - an exit can never turn surplus units into a new lend position. These calls go to `MidnightBundlesV1`, the Bundles contract at the Morpho SDK's `midnightBundles` address, which markets.morpho.org also uses. Its functions are prefixed `midnightBundlesV1`; don't mix them with another Bundles version's address or authorization.

Unlike [exiting a lend early](https://docs.morpho.org/developers/midnight/tutorials/exit-lend-early/), where `MidnightBundlesV1` pays the lender and no token approval is needed, `MidnightBundlesV1` **pulls** loan tokens from the borrower up front to pay for the units. This flow therefore needs a loan-token ERC-20 approval (or permit) to `MidnightBundlesV1`, on top of the `MidnightBundlesV1` authorization. Collateral can be released in the same call.

The Morpho SDK taker flows hard-code `reduceOnly = false` and don't expose a reduce-only exit at this version, so this tutorial uses the raw `MidnightBundlesV1` calls - with the SDK still used for quoting. See [Taker flows](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/#taker-flows) for the SDK surface.

Snippets assume a [viem wallet client](https://viem.sh/docs/clients/wallet) `walletClient` for your account on Base, and `taker` set to your wallet address.

## [**Read the position**](#read-the-position)

The REST API is the quickest way to inspect the position. It returns the stored, indexed values and can lag a few blocks. To size the transaction, run the SDK read or the direct contract read: they return the live, accrued values that the next steps use.

### [REST API](#rest-api)

Fetch the borrower's position to get its outstanding debt and locked collateral:

```
GET https://api.morpho.org/v0/midnight/markets
  /{marketId}/users/{userAddress}/position

// Response
{
  "data": {
    "chain_id":           8453,
    "market_id":          "0xd92de5e7fbb...7614",               // market the borrower borrowed from
    "user_address":       "0xYourWalletAddress",
    "last_indexed_block": "47457420",
    "loan_token":         "0x8335...2913",                      // USDC
    "maturity":           "1798761600",
    "type":               "borrow",                             // "lend" | "borrow" | "collateral_only"
    "credit":             "0",
    "debt":               "10527000000",                        // debt units to retire
    "pending_fee":        "0",
    "last_loss_factor":   "0",
    "loss_factor":        "0",
    "collaterals": [                                            // each entry is { token, amount }
      {
        "token":  "0x4200000000000000000000000000000000000006", // WETH - withdrawable in the same call
        "amount": "5000000000000000000"                         // 5 WETH (18 dec)
      }
    ]
  }
}

// Inspection only - size the transaction from the SDK or direct contract read below.
```

### [SDK](#sdk)

The SDK reads the same position through `midnight.getPositionData`, accrued to the latest block:

```
import { publicActions } from "viem";
import { morphoViemExtension } from "@morpho-org/morpho-sdk";
import { midnightAbi } from "@morpho-org/morpho-sdk/abis";

// Extend the wallet client with the `morpho` namespace and the public reads
// the SDK needs.
const client = walletClient.extend(morphoViemExtension()).extend(publicActions);
const midnight = client.morpho.midnight(8453); // Midnight entity for Base
const MIDNIGHT = "0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A"; // Midnight on Base (from the @morpho-org/morpho-ts address registry)

// The extended client doubles as the public client the execute snippet reads with.
const publicClient = client;

const block = await client.getBlock();
const positionData = (
  await midnight.getPositionData({
    marketId,
    accountAddress: taker,
    parameters: { blockNumber: block.number },
  })
).accrueInterest(block.timestamp);

// Full-exit units target: the accrued outstanding debt.
const targetUnits = positionData.debt;

// positionData.collateral[i] is the live collateral amount at index i of
// market.collateralParams - the same value the execute snippet reads with
// `collateral(marketId, taker, i)`.
```

### [Onchain (direct contract read)](#onchain-direct-contract-read)

A full exit must be sized to the exact outstanding debt right now - read the raw `debt` getter. Debt carries no loss factor and accrues no pending fee, so unlike the lend side the raw getter is the value the bundle's `reduceOnly` check enforces against:

```
import { createPublicClient, http } from "viem";
import { base } from "viem/chains";
import { midnightAbi } from "@morpho-org/morpho-sdk/abis";

const MIDNIGHT = "0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A"; // Midnight on Base (from the @morpho-org/morpho-ts address registry)

const publicClient = createPublicClient({ chain: base, transport: http() });

// No market struct needed - unlike updatePositionView (which the lend exit
// uses because credit accrues), debt is read raw.
const targetUnits = await publicClient.readContract({
  address: MIDNIGHT,
  abi: midnightAbi,
  functionName: "debt",
  args: [marketId, taker],
});
```

## [**Get a quote**](#get-a-quote)

A borrow exit takes **asks** - makers selling units. Quote against the ask side: `units` for a full exit (retire all debt), `assets` for a partial one (spend down to a loan-token amount).

### [REST API](#rest-api-1)

```
GET https://api.morpho.org/v0/midnight/books/{marketId}/asks/quote
  ?units=10527000000   // outstanding debt units (full exit); use assets= for a partial
  &slippage=0.5        // 0.5% slippage guard
  &limit=10000         // max offers walked/returned; default and maximum 10,000

// Response: the router's execution plan
{
  "data": {
    "average_best_price": "947619047619047619",  // realized target take using onchain per-offer rounding, rounded against the taker
    "average_worst_price": "952300000000000000", // conservative adverse-placement bound across returned caps - above best for asks, the buying side's worst case; not the slippage-derived guard
    "available_assets": "9990000000",            // max loan-token cost in this returned limit window (includes fallback excess, so it exceeds the target cost)
    "available_units": "10527000000",            // max units in this returned limit window
    "takeable_offers": [
      {
        "market_id": "0x56b822d7d8be6bded8e1782277989fe5dc4e5b0a4f7f9d349482bc933bd5436c",
        "units": "5250000000",  // maximum this offer may contribute, not an exact allocation
        "offer": { /* … sell offer (ask): the maker is borrowing … */ },
        "ratifier_data": "0x4a8b...f201"
      }
      // Additional complete offers follow in best-price order as fallback excess.
    ]
  }
}

// Interpreting the quote
const quote = response.data;
const avgPrice = Number(quote.average_best_price) / 1e18;   // ≈ 0.9476 per unit
const expectedCost = BigInt(Math.floor(10_527e6 * avgPrice)); // ≈ 9,975 USDC spent (available_assets covers the target plus fallback)
// Price guard: a buyer's cap sits above the quote - maxBuyerAssets
// uses the same units × worst-acceptable-price formula as the exit call
const maxBuyerAssets = BigInt(Math.ceil(10_527e6 * 0.96));
// NOTE: a full exit targets the *available* debt - units already backing
// your own resting reduce-only buy offers are committed elsewhere.
```

### [SDK](#sdk-1)

`MidnightApi.fetchBookQuote` wraps the quote endpoint and returns ABI-ready take objects:

```
import { MidnightApi, type MidnightApiTake } from "@morpho-org/morpho-sdk/midnight-api";

// SDK wraps the quote endpoint and maps the response into ABI-ready take
// objects (uses Morpho's router by default, no config needed)
const quote = await MidnightApi.fetchBookQuote({
  marketId,
  side:     "asks",               // exiting borrower takes asks (not bids)
  units:    targetUnits,          // outstanding debt units
  slippage: "0.5",                // 0.5% slippage guard
});

// ABI-ready takes
const takes: MidnightApiTake[] = quote.data.takeableOffers;
```

There is no onchain quote: offers are signed and published offchain, not stored in the Midnight contract.

## [**Approve & authorize**](#approve--authorize)

The bundler pulls loan tokens from the borrower to pay for the units, then withdraws collateral. The borrower must:

1. Approve `MidnightBundlesV1` to pull the loan token (USDC) - sized to `targetBuyerAssets` for a partial exit, or `maxBuyerAssets` for a full one (the units-target call refunds the unused part).
2. Authorize `MidnightBundlesV1` on the Midnight contract (one-time).

```
import { erc20Abi, parseUnits } from "viem";
import { midnightAbi } from "@morpho-org/morpho-sdk/abis";

const MIDNIGHT_BUNDLES = "0x091183d729BE9f808c212b475E387A12E67850A7";   // MidnightBundlesV1 on Base (from the @morpho-org/morpho-ts address registry)
const MIDNIGHT         = "0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A";   // Midnight on Base (from the registry)
const USDC             = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913";   // USDC on Base

// Pulled amounts (reused by the execute snippets below):
// a full exit pulls maxBuyerAssets up front and refunds the unused part;
// a partial exit pulls exactly targetBuyerAssets
const worstAcceptablePrice = 0.96;
const maxBuyerAssets = BigInt(Math.ceil(Number(targetUnits) * worstAcceptablePrice));
const targetBuyerAssets = parseUnits("5000", 6);   // example partial exit: 5,000 USDC

// Approve the pulled amount for the exit you're running
// Wait for the approval to confirm before authorizing the bundle below.
const approveHash = await walletClient.writeContract({
  account: taker,
  address: USDC,
  abi: erc20Abi,
  functionName: "approve",
  args: [MIDNIGHT_BUNDLES, maxBuyerAssets],   // use targetBuyerAssets for a partial exit
});
const approveReceipt = await publicClient.waitForTransactionReceipt({ hash: approveHash });
if (approveReceipt.status !== "success") throw new Error("USDC approval failed");

// A TokenPermit { kind, data } argument on the bundle call can carry an
// EIP-2612 or Permit2 signature instead - { kind: 0, data: "0x" } is the
// pre-approved variant used below.

// Authorize MidnightBundlesV1 to act on your position (one-time boolean, persists across future actions)
// Wait for the authorization to confirm before the exit call below.
const authHash = await walletClient.writeContract({
  account: taker,
  address: MIDNIGHT,
  abi: midnightAbi,
  functionName: "setIsAuthorized",
  args: [MIDNIGHT_BUNDLES, true, taker],
});
const authReceipt = await publicClient.waitForTransactionReceipt({ hash: authHash });
if (authReceipt.status !== "success") throw new Error("MidnightBundlesV1 authorization failed");
```

## [**Execute the exit**](#execute-the-exit)

Pick a full exit (retire all debt, sized in units) or a partial exit (spend down to a loan-token amount). Both calls can release collateral in the same transaction: `collateralWithdrawals` lists what to withdraw and `collateralReceiver` where it goes - an empty list and the zero address withdraw nothing. Withdrawal is bounded by the debt left after the take: Midnight re-checks the position against its LLTV at withdrawal and reverts if it would go unhealthy.

### [Full exit: retire all debt](#full-exit-retire-all-debt)

`targetUnits` is the outstanding debt from the onchain read. `maxBuyerAssets` is the price guard: the most loan tokens you'll pay - the bundle pulls that amount up front and refunds the unused part, reverting if the take would cost more.

```
import { midnightBundlesAbi } from "@morpho-org/morpho-sdk/abis";
import { maxUint256, zeroAddress } from "viem";

// market = the Market struct built from the API market payload (as in the
// lend/borrow tutorials) - collateralParams is what withdrawals index into.
// Release collateral in the same call: iterate the market's collateral
// indexes and read the live onchain balance per index - API amounts can lag.
const collateralWithdrawals = (
  await Promise.all(
    market.collateralParams.map(async (_: any, index: number) => ({
      collateralIndex: BigInt(index),
      assets: await publicClient.readContract({
        address: MIDNIGHT,
        abi: midnightAbi,
        functionName: "collateral",
        args: [marketId, taker, BigInt(index)],
      }),
    }))
  )
).filter((c: any) => c.assets > 0n);

// Withdrawing everything is only safe when targetUnits retires the full
// debt - sized below it (e.g. units committed to your own resting offers),
// pass [] / zeroAddress or a withdrawal the remaining debt's LLTV allows,
// or this reverts `UnhealthyBorrower`.

// Deadline: the transaction reverts if not included before this timestamp
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600); // 1 hour from now

const hash = await walletClient.writeContract({
  account: taker,
  address: MIDNIGHT_BUNDLES,
  abi: midnightBundlesAbi,
  functionName: "midnightBundlesV1BuyWithUnitsTargetAndWithdrawCollateral",
  args: [
    targetUnits,           // debt units to retire - from the debt() read
    maxBuyerAssets,        // revert if the take costs more (price guard)
    taker,                 // taker (the exiting borrower)
    true,                  // reduceOnly (true - this is an exit, never buy past the debt)
    { kind: 0, data: "0x" }, // loanTokenPermit (pre-approved - see Approve & authorize)
    takes,                 // the takeable offers from the quote (ABI-encoded)
    collateralWithdrawals, // CollateralWithdrawal[] - or [] to withdraw nothing
    taker,                 // collateralReceiver (zeroAddress when withdrawing nothing)
    0n,                    // referralFeePct (0 = none)
    zeroAddress,           // referralFeeRecipient (none)
    maxUint256,            // maxContinuousFee (type(uint256).max disables the check)
    deadline               // deadline (reverts if tx is included after this timestamp)
  ],
});

// Units backing your own resting reduce-only buy offers are already
// committed - size targetUnits to the available debt (or cancel those
// offers first), or they revert when taken.

console.log("Exit tx:", hash);
```

### [Partial exit: spend down to an amount](#partial-exit-spend-down-to-an-amount)

`targetBuyerAssets` is how many loan tokens to spend - the bundler pulls exactly that. `minUnits` is the price guard: the fewest debt units the take must retire - derive it from a worst-acceptable price (units = loan tokens / price, rounded down), and the bundle reverts if it would retire less.

```
import { midnightBundlesAbi } from "@morpho-org/morpho-sdk/abis";
import { maxUint256, zeroAddress } from "viem";

// Price guard: the fewest debt units the take must retire for the
// targetBuyerAssets pulled (from Approve & authorize) -
// reverts if the take happens above the 0.96 worst-acceptable price
const minUnits = BigInt(Math.floor(Number(targetBuyerAssets) / worstAcceptablePrice));

// Deadline: the transaction reverts if not included before this timestamp
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600); // 1 hour from now

const hash = await walletClient.writeContract({
  account: taker,
  address: MIDNIGHT_BUNDLES,
  abi: midnightBundlesAbi,
  functionName: "midnightBundlesV1BuyWithAssetsTargetAndWithdrawCollateral",
  args: [
    targetBuyerAssets,     // loan tokens to spend (the amount pulled)
    minUnits,              // revert if fewer debt units retired (price guard)
    taker,                 // taker
    true,                  // reduceOnly
    { kind: 0, data: "0x" }, // loanTokenPermit (pre-approved)
    takes,                 // takeable offers from the quote
    [],                    // collateralWithdrawals (empty - or bounded by remaining debt's LLTV)
    zeroAddress,           // collateralReceiver (none)
    0n,                    // referralFeePct
    zeroAddress,           // referralFeeRecipient
    maxUint256,            // maxContinuousFee
    deadline               // deadline
  ],
});

console.log("Partial exit tx:", hash);
```

## [**Exit at a chosen price**](#exit-at-a-chosen-price)

Instead of taking asks now, a borrower can publish a resting **reduce-only buy offer** at a chosen tick: it stays published until it is taken, cancelled or expires, and retires debt only when another user takes it at that price. A buy offer pulls loan tokens from the maker when taken, so it also needs a loan-token approval to the `Midnight` contract (`buy: true`, `reduceOnly: true`).

On the SDK, buy-side maker offers are posted through `makeLend` (the flow validates `buy: true` offers and returns the Midnight loan-token approval as a requirement):

```
import { addresses } from "@morpho-org/morpho-ts";
import { Offer } from "@morpho-org/midnight-sdk";
import { parseUnits } from "viem";

const chainId = 8453;
const ecrecoverRatifier = addresses[chainId].ecrecoverRatifier!; // EcrecoverRatifier on Base (from the registry)
// `midnight` = the MorphoMidnight entity built in the SDK page's Maker flows section

// Resting buy offer: retires debt only when taken at this tick's price
const exitOffer = Offer.create({
  market,                       // market params (as on the SDK page)
  maker: taker,
  buy: true,                    // maker buys units
  reduceOnly: true,             // can only consume outstanding debt - pure exit
  tick: 5_000n,                 // chosen price tick
  maxUnits: targetUnits,        // debt units this offer may retire
  // now + 7 days, capped at the market's maturity
  expiry: BigInt(Math.min(Number(market.maturity), Math.floor(Date.now() / 1000) + 604_800)),
  ratifier: ecrecoverRatifier,
});

// loanAssets sizes the Midnight loan-token approval the flow returns
const make = await midnight.makeLend({
  accountAddress: taker,
  offers: [exitOffer],
  loanToken: USDC,
  loanAssets: parseUnits("10000", 6),
});
// …dispatch make.getRequirements() (loan-token approval + ratifier), then buildTx()

// Debt units committed to this offer are excluded from a full taker
// exit's available amount - take or cancel first if you need both.
```

See [Maker flows](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/#maker-flows) for the full pipeline (grouping, tree, ratification, mempool publication).

[Exit lend early

Previous Page

](https://docs.morpho.org/developers/midnight/tutorials/exit-lend-early/)[Display positions

Next Page

](https://docs.morpho.org/developers/midnight/tutorials/display-positions/)