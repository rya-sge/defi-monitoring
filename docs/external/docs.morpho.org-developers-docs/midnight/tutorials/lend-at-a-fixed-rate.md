# Lend at a fixed rate

> Source: https://docs.morpho.org/developers/midnight/tutorials/lend-at-a-fixed-rate

---

# Lend at a fixed rate

Snippets assume a [viem wallet client](https://viem.sh/docs/clients/wallet) `walletClient` for your account on Base, and `taker` set to your wallet address.

## [**Browse markets**](#browse-markets)

Fetch the list of books filtered by chain and loan token. Each book represents one market with its top ask/bid price levels:

```
GET https://api.morpho.org/v0/midnight/books
  ?chain_ids=8453                                         // Base
  &loan_tokens=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 // USDC on Base
  &sort=maturity

// Response (each book is one market with its top ask/bid levels)
{
  "cursor": "eyJzb3J0Ijpb...",                            // null when there is no next page
  "data": [
    {
      "market_id": "0xd92de5e7fbb...7614",                 // use this ID in the next step
      "chain_id": 8453,
      "midnight": "0x2F7a3AA739ba5792Ce1b4eA046117f2C0095BCA6",
      "loan_token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      "collaterals": [
        {
          "token": "0x4200000000000000000000000000000000000006", // WETH on Base
          "lltv": "770000000000000000",                          // 77% LTV
          "liquidation_cursor": "250000000000000000",
          "oracle": "0xD09048c8B568Dbf5f189302beA26c9edABFC4858"
        }
      ],
      "maturity": 1798761600,                                     // January 1, 2027
      "rcf_threshold": "0",
      "enter_gate": "0x0000000000000000000000000000000000000000",
      "liquidator_gate": "0x0000000000000000000000000000000000000000",

      // ┌─────────────────────────────────────────────────────────┐
      // │  FOR LENDING → read the ASKS                            │
      // │  Asks = makers selling units = borrowers seeking loans  │
      // │  You (the lender) take these asks = buy their units     │
      // │  The ask price is what you pay per unit → your rate     │
      // └─────────────────────────────────────────────────────────┘
      "asks": [
        { "tick": 42, "price": "952380952380952380", "units": "10000000000", "assets": "9523809523", "count": 3 },
        { "tick": 43, "price": "948000000000000000", "units": "18500000000", "assets": "17538000000", "count": 5 }
      ],

      // (bids = lenders' buy-offers, read these for borrowing)
      "bids": [
        { "tick": 41, "price": "956937000000000000", "units": "8000000000", "assets": "7655497000", "count": 2 }
      ]
    }
  ]
}
```

## [**Select market & estimate lend rate**](#select-market--estimate-lend-rate)

The best ask is the cheapest unit price. Convert the price into an annualized rate:

```
// Select book data
const book = response.data[0];

// Obtain best ask price (scaled by 1e18)
const bestAskPrice = Number(book.asks[0].price) / 1e18;  // ≈ 0.9524

// Calculate time to maturity (ttm) in seconds
const ttm = book.maturity - Date.now() / 1000;

// Calculate fixed lend APR
// Note: This assumes the entire lend size fits within that first tick's available units.
// If lend size is higher than the assets at that tick, the effective blended rate would be lower.
// The Morpho router (next step) returns the accurate blended price stemming from all takeable offers available.
const lendAPR = (1 / bestAskPrice - 1) * (365 * 86400) / ttm; // ≈ 5.2%

console.log(`Lend APR: ${(lendAPR * 100).toFixed(2)}%`);

// If the rate looks good, save the market ID for the next step
const marketId = book.market_id;   // "0xd92de5e7fbb...7614"
```

## [**Get a quote for your offer**](#get-a-quote-for-your-offer)

### [REST API](#rest-api)

#### [Step 1: Get a quote](#step-1-get-a-quote)

Specify the amount of USDC you want to lend to a market with slippage. The Morpho router (via the quote API shown below) returns executable takeable offers with fallback liquidity (i.e. additional offers returned in case offers are partially consumed). This way, during execution, the bundle can skip stale offers and still take offers for the lender's request.

```
GET https://api.morpho.org/v0/midnight/books/{marketId}/asks/quote
  ?assets=10000000000  // 10,000 USDC (6 decimals)
  &slippage=0.5       // 0.5% slippage guard
  &limit=10000        // max offers walked/returned; default and maximum 10,000

// Response: the router's execution plan:
{
  "data": {
    "average_best_price": "947619047619047619", // realized target fill using onchain per-offer rounding, rounded against the taker
    "average_worst_price": "952300000000000000", // conservative adverse-placement bound across returned caps; not the slippage-derived guard
    "available_assets": "15000000000", // max assets in this returned limit window
    "available_units": "15750000000", // max units in this returned limit window
    "takeable_offers": [
      {
        "market_id": "0x56b822d7d8be6bded8e1782277989fe5dc4e5b0a4f7f9d349482bc933bd5436c",
        "units": "5250000000", // maximum this offer may contribute, not an exact allocation
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
                "oracle": "0xD09048c8B568Dbf5f189302beA26c9edABFC4858"
              }
            ],
            "maturity": 1786147200,
            "rcf_threshold": "0",
            "enter_gate": "0x0000000000000000000000000000000000000000",
            "liquidator_gate": "0x0000000000000000000000000000000000000000"
          },
          "buy": false, // sell offer (ask): the maker is borrowing
          "maker": "0x7b093658BE7f90B63D7c359e8f408e503c2D9401",
          "max_units": "0",
          "start": 1761922790,
          "expiry": 1786147200,
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
        "ratifier_data": "0x4a8b...f201"
      }
      // Additional complete offers follow in best-price order as fallback excess.
      // A grouped offer's full cap is not guaranteed: sibling fills may consume
      // group capacity before execution, which is why the router returns fallbacks.
    ]
  }
}

// Interpreting the quote
const quote = response.data;
const avgPrice = Number(quote.average_best_price) / 1e18;      // ≈ 0.9476
const impliedRate = (1 / avgPrice - 1) * (365 * 86400) / ttm;
const targetUnits = BigInt(Math.ceil(10_000e6 / avgPrice));     // target fill; available_units is fallback-window capacity
```

#### [Step 2: Convert takeable offers to ABI-encoded data](#step-2-convert-takeable-offers-to-abi-encoded-data)

The API returns snake_case JSON, whereas the onchain ABI expects camelCase tuples. The `apiOfferToAbi` helper converts the API offer to an ABI struct.

```
function apiOfferToAbi(apiOffer: any) {
  return {
    market: {
      chainId:        BigInt(apiOffer.market.chain_id),
      midnight:       apiOffer.market.midnight,
      loanToken:      apiOffer.market.loan_token,
      collateralParams: apiOffer.market.collaterals.map((c: any) => ({
        token:  c.token,
        lltv:   BigInt(c.lltv),
        liquidationCursor: BigInt(c.liquidation_cursor),
        oracle: c.oracle,
      })),
      maturity:       BigInt(apiOffer.market.maturity),
      rcfThreshold:   BigInt(apiOffer.market.rcf_threshold),
      enterGate:      apiOffer.market.enter_gate,
      liquidatorGate: apiOffer.market.liquidator_gate,
    },
    buy:                       apiOffer.buy,
    maker:                     apiOffer.maker,
    maxUnits:                  BigInt(apiOffer.max_units),
    maxAssets:                 BigInt(apiOffer.max_assets),
    start:                     BigInt(apiOffer.start),
    expiry:                    BigInt(apiOffer.expiry),
    tick:                      BigInt(apiOffer.tick),
    group:                     apiOffer.group,
    callback:                  apiOffer.callback,
    callbackData:              apiOffer.callback_data,
    receiverIfMakerIsSeller:   apiOffer.receiver_if_maker_is_seller,
    ratifier:                  apiOffer.ratifier,
    reduceOnly:                apiOffer.reduce_only,
    continuousFeeCap:          BigInt(apiOffer.continuous_fee_cap),
  };
}

// Takeable offers from quote API
const takeableOffers = quote.takeable_offers;

// Map offers to ABI-ready structs via helper
const takes = takeableOffers.map((t) => ({
  offer: apiOfferToAbi(t.offer),
  ratifierData: t.ratifier_data,
  units: BigInt(t.units),
}));
```

### [SDK](#sdk)

`MidnightApi.fetchBookQuote` wraps the quote endpoint as part of the Morpho SDK's Midnight API helpers and returns ABI-ready take objects

#### [Step 1: Install dependencies](#step-1-install-dependencies)

```
npm install @morpho-org/morpho-sdk viem
```

#### [Step 2: Get ABI-ready takeable offers](#step-2-get-abi-ready-takeable-offers)

```
import { MidnightApi, type MidnightApiTake } from "@morpho-org/morpho-sdk/midnight-api";
import { parseUnits } from "viem";

const marketId = "0xd92de5e7fbb...7614";   // from the "Browse markets" step

// SDK wraps the quote endpoint and maps the response into ABI-ready take objects (uses Morpho's router by default, no config needed)
const quote = await MidnightApi.fetchBookQuote({
  marketId,
  side:     "asks",                        // lender takes asks (not bids)
  assets:   parseUnits("10000", 6),        // 10,000 USDC to lend
  slippage: "0.5",                         // 0.5% slippage guard
});

// quote.data contains:
//   .averageBestPrice   (BigInt)
//   .averageWorstPrice  (BigInt)
//   .availableAssets    (BigInt)
//   .availableUnits     (BigInt)
//   .takeableOffers     (MidnightApiTake[], ABI-ready)

// ABI-ready takes
const takes: MidnightApiTake[] = quote.data.takeableOffers;
```

## [**Execute the lend**](#execute-the-lend)

The recommended path is the [Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/): it derives the USDC approval and the one-time `MidnightBundles` authorization for you, applies your price guard, and builds the bundle transaction that takes offers toward your target while skipping stale offers. The raw contract call below it is the manual equivalent.

### [Morpho SDK](#morpho-sdk)

Extend `walletClient` and hand the flow the quote from the previous step (SDK tab):

```
import { parseUnits, publicActions } from "viem";
import { morphoViemExtension } from "@morpho-org/morpho-sdk";

// Extend the wallet client with the `morpho` namespace and the public reads
// the flow needs (getBlock / waitForTransactionReceipt).
const client = walletClient.extend(morphoViemExtension()).extend(publicActions);
const midnight = client.morpho.midnight(8453);

// Fresh, same-block market snapshot.
const block = await client.getBlock();
const marketData = await midnight.getMarketData(marketId, {
  blockNumber: block.number,
});

// Price guard: cap the minimum units you'll accept for your 10,000 USDC -
// if the average fill price rises above 0.96, the bundle reverts.
const worstAcceptablePrice = 0.96;
const minUnits = BigInt(Math.ceil(10_000e6 / worstAcceptablePrice));

// Deadline: the transaction reverts if not included before this timestamp
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600); // 1 hour from now

// takeLend spends `assets` of USDC for at least `minUnits` of credit units.
const takeLend = midnight.takeLend({
  accountAddress: taker,
  marketData,
  assets: parseUnits("10000", 6),
  minUnits,
  takeableOffers: quote.data.takeableOffers,
  deadline,
});

// Requirements are plain transactions - the USDC approval to MidnightBundles
// plus the one-time MidnightBundles authorization. The SDK returns only the
// ones that are still missing; send each and wait for its receipt.
for (const requirement of await takeLend.getRequirements()) {
  const hash = await client.sendTransaction(requirement);
  await client.waitForTransactionReceipt({ hash });
}

const hash = await client.sendTransaction(takeLend.buildTx());
console.log("Lend tx:", hash);
```

See [Taker flows](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/#taker-flows) for the full surface, including `takeBorrow` and `supplyCollateralTakeBorrow`.

### [Raw contract call](#raw-contract-call)

Working below the SDK? Call the `MidnightBundles` contract directly - it takes offers toward your target in one transaction, skipping stale offers automatically, but you handle the approvals and authorization yourself.

**Prerequisites**

1. Approve `MidnightBundles` contract to pull loan token (i.e. USDC)
2. Authorize `MidnightBundles` on the Midnight contract.

#### [Authorizations & Approvals](#authorizations--approvals)

Pick between Path 1, Path 2, or Path 3 depending on your UX and signing needs.

```
import {
  erc20Abi, maxUint256, createPublicClient, encodeAbiParameters, parseAbiParameters, parseSignature, parseUnits, http,
} from "viem";
import { base } from "viem/chains";

const MIDNIGHT_BUNDLES = "0x091183d729BE9f808c212b475E387A12E67850A7";   // MidnightBundles on Base (from the @morpho-org/morpho-ts address registry)
const USDC            = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913";    // USDC on Base
const MIDNIGHT         = "0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A";   // Midnight on Base (from the registry)

// Path 1: approve()
// 1. Let MidnightBundles pull USDC during the buy
// 2. maxUint256 = standing allowance
await walletClient.writeContract({
  account: taker,
  address: USDC,
  abi: erc20Abi,
  functionName: "approve",
  args: [MIDNIGHT_BUNDLES, maxUint256],
});

// Variable to set the loanTokenPermit variable to (bundler argument) in the Execute step that follows
const tokenPermitNone   = { kind: 0, data: "0x" } as const;

// --------------------------------------------------------------

// Path 2: EIP-2612 (Permit)
// Authorize exactly the USDC you'll spend buying units
const permitValue = parseUnits("10000", 6);                              // = targetBuyerAssets (10,000 USDC)
const deadline    = BigInt(Math.floor(Date.now() / 1000) + 3600);        // 1 hour expiry

const publicClient = createPublicClient({ chain: base, transport: http() });

// Read the taker's current EIP-2612 nonce from the USDC contract
const nonce = await publicClient.readContract({
  address: USDC,
  abi: [{ name: "nonces", type: "function", stateMutability: "view",
          inputs: [{ name: "owner", type: "address" }],
          outputs: [{ type: "uint256" }] }],
  functionName: "nonces",
  args: [taker],
});

// Offchain signature (no transaction, no gas)
const sig = await walletClient.signTypedData({
  account: taker,
  domain: { name: "USD Coin", version: "2", chainId: 8453, verifyingContract: USDC },
  types: { Permit: [
    { name: "owner",    type: "address" },
    { name: "spender",  type: "address" },
    { name: "value",    type: "uint256" },
    { name: "nonce",    type: "uint256" },
    { name: "deadline", type: "uint256" },
  ] },
  primaryType: "Permit",
  message: { owner: taker, spender: MIDNIGHT_BUNDLES,
             value: permitValue, nonce, deadline },
});

const { r, s, v } = parseSignature(sig);

// Variable to set the loanTokenPermit variable to (bundler argument) in the Execute step that follows
const loanTokenPermitERC2612 = {
  kind: 1,                                                             // 1 = ERC-2612
  data: encodeAbiParameters(
    parseAbiParameters("uint256 deadline, uint8 v, bytes32 r, bytes32 s"),
    [deadline, Number(v), r, s],
  ),
} as const;

// --------------------------------------------------------------

// Path 3: Permit2
// One-time setup (once per token, ever): approve Permit2 on USDC
const PERMIT2 = "0x000000000022D473030F116dDEE9F6B43aC78BA3";          // canonical, same on every chain
const permitValue = parseUnits("10000", 6);                            // = targetBuyerAssets (10,000 USDC)

// One-time setup (once per token, ever): approve Permit2 on USDC. After this, every future authorization is just a signature
await walletClient.writeContract({
  account: taker, address: USDC, abi: erc20Abi,
  functionName: "approve", args: [PERMIT2, maxUint256],
});

// Per-take: sign a Permit2 SignatureTransfer (offchain, no gas).
const nonce    = BigInt(Date.now());                                   // unordered nonce (Permit2 uses a bitmap)
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

const sig = await walletClient.signTypedData({
  account: taker,
  domain: { name: "Permit2", chainId: 8453, verifyingContract: PERMIT2 },
  types: {
    PermitTransferFrom: [
      { name: "permitted", type: "TokenPermissions" },
      { name: "spender",   type: "address" },
      { name: "nonce",     type: "uint256" },
      { name: "deadline",  type: "uint256" },
    ],
    TokenPermissions: [
      { name: "token",  type: "address" },
      { name: "amount", type: "uint256" },
    ],
  },
  primaryType: "PermitTransferFrom",
  message: {
    permitted: { token: USDC, amount: permitValue },
    spender: MIDNIGHT_BUNDLES,                                           // contract pulls via Permit2
    nonce,
    deadline,
  },
});

// Variable to set the loanTokenPermit variable to (bundler argument) in the Execute step that follows
const loanTokenPermit2 = {
  kind: 2,                                                               // 2 = Permit2
  data: encodeAbiParameters(
    parseAbiParameters("uint256 nonce, uint256 deadline, bytes signature"),
    [nonce, deadline, sig],
  ),
} as const;

// --------------------------------------------------------------

// Authorize MidnightBundles to act on your position (one-time boolean, persists across future actions)
await walletClient.writeContract({
  account: taker,
  address: MIDNIGHT,
  abi: midnightAbi,
  functionName: "setIsAuthorized",
  args: [MIDNIGHT_BUNDLES, true, taker],
});
```

#### [Execute onchain](#execute-onchain)

Specify the target amount of assets you want to buy (i.e. lend), a price guard, and the bundler's arguments.

```
import { createWalletClient, http, parseUnits, zeroAddress, maxUint256 } from "viem";
import { base } from "viem/chains";
import { midnightBundlesAbi } from "@morpho-org/morpho-sdk/abis";

const MIDNIGHT_BUNDLES = "0x091183d729BE9f808c212b475E387A12E67850A7";      // MidnightBundles on Base (from the @morpho-org/morpho-ts address registry)

const targetBuyerAssets = parseUnits("10000", 6);  // 10,000 USDC

// Set your own price guard (caps the minimum units you'll receive, preventing you from getting a worse yield than expected)
// For example, if avg fill price rises above 0.96 → fewer units → bundle reverts
const worstAcceptablePrice = 0.96;
const minUnits = BigInt(Math.ceil(10_000e6 / worstAcceptablePrice));

// Deadline: the transaction reverts if not included before this timestamp
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600); // 1 hour from now

// The bundle's 5th argument (loanTokenPermit), a TokenPermit { kind, data }, is how you tell the bundle to move your USDC.
// The possible values are outlined in "Authorizations & Approvals" step.
const hash = await walletClient.writeContract({
  account: taker,
  address: MIDNIGHT_BUNDLES,
  abi: midnightBundlesAbi,
  functionName: "midnightBundlesV1BuyWithAssetsTargetAndWithdrawCollateral",
  args: [
    targetBuyerAssets,   // how much USDC to spend
    minUnits,            // revert if fewer units returned (yield protection)
    taker,               // taker (the lender's address where the bought units are credited to)
    false,               // reduceOnly (false for a new lend position)
    tokenPermitNone,     // loan-token permit (none = pre-approved)
    takes,               // the takeable offers from the quote (ABI-encoded)
    [],                  // collateralWithdrawals (empty for lend)
    taker,               // collateralReceiver (unused - no withdrawals)
    0n,                  // referralFeePct (0 = none)
    zeroAddress,         // referralFeeRecipient (none)
    maxUint256,          // maxContinuousFee (type(uint256).max disables the check)
    deadline             // deadline (reverts if tx is included after this timestamp)
  ],
});

console.log("Lend tx:", hash);
```

[Fees

Previous Page

](https://docs.morpho.org/developers/midnight/concepts/fees/)[Borrow at a fixed rate

Next Page

](https://docs.morpho.org/developers/midnight/tutorials/borrow-at-a-fixed-rate/)