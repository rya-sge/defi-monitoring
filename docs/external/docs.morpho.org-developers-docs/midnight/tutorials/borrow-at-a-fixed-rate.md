# Borrow at a fixed rate

> Source: https://docs.morpho.org/developers/midnight/tutorials/borrow-at-a-fixed-rate

---

# Borrow at a fixed rate

Snippets assume a [viem wallet client](https://viem.sh/docs/clients/wallet) `walletClient` for your account on Base, and `taker` set to your wallet address.

## [**Browse markets**](#browse-markets)

Fetch the list of books filtered by chain and loan token. Each book represents one market with its top ask/bid price levels:

```
GET https://api.morpho.org/v0/midnight/books
  ?chain_ids=8453                                                // Base
  &loan_tokens=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913        // USDC on Base
  &sort=maturity

// Response (each book is one market with its top ask/bid levels)
{
  "cursor": "eyJzb3J0Ijpb...",                                  // null when there is no next page
  "data": [
    {
      "market_id": "0xd92de5e7fbb...7614",                       // use this ID in the next step
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
      "maturity": 1798761600,                                    // January 1, 2027
      "rcf_threshold": "0",
      "enter_gate": "0x0000000000000000000000000000000000000000",
      "liquidator_gate": "0x0000000000000000000000000000000000000000",

      "asks": [
        { "tick": 4990, "price": "957900000000000000", "units": "5000000000", "assets": "4789500000", "count": 1 }
      ], // lending side; ignore for borrowing

      // ┌──────────────────────────────────────────────────────────────┐
      // │  FOR BORROWING → read the BIDS                               │
      // │  Bids = lenders buying units = offering to lend you money    │
      // │  You (the borrower) take these bids = sell your units        │
      // │  The bid price is what you receive per unit → your cost      │
      // └──────────────────────────────────────────────────────────────┘
      "bids": [
        {
          "tick": 4988,
          "price": "956937000000000000",                         // ≈ 0.9569 per unit
          "units": "8000000000",
          "assets": "7655497000",                               // ≈ 7,655 USDC on the bid
          "count": 2
        },
        {
          "tick": 4976,
          "price": "951000000000000000",                         // ≈ 0.9510 (worse for borrower)
          "units": "12000000000",
          "assets": "11412000000",
          "count": 4
        }
      ]
    }
  ]
}
```

## [**Select market & estimate borrow rate**](#select-market--estimate-borrow-rate)

The best bid is the highest price. Higher means you receive more per unit sold, so lower borrowing cost.

```
// Select book data
const book = response.data[0];

// Obtain best bid price (highest = cheapest to borrow)
const bestBidPrice = Number(book.bids[0].price) / 1e18;          // ≈ 0.9569

// Calculate time to maturity (ttm) in seconds
const ttm = book.maturity - Date.now() / 1000;

// Calculate fixed borrow APR
const borrowAPR = (1 / bestBidPrice - 1) * (365 * 86400) / ttm;

console.log(`Borrow APR: ${(borrowAPR * 100).toFixed(2)}%`);

// If the rate looks good, save the market ID for the next step
const marketId = book.market_id;                                 // "0xd92de5e7fbb...7614"
```

## [**Get a quote for your offer**](#get-a-quote-for-your-offer)

### [REST API](#rest-api)

#### [Step 1: Get a quote](#step-1-get-a-quote)

Specify the amount of USDC you want to borrow from a market with slippage. Morpho's router returns executable takeable offers (quotes against the bids) with fallback liquidity. The total may exceed your target so the bundle can skip stale offers and still take offers.

```
GET https://api.morpho.org/v0/midnight/books/{marketId}/bids/quote
  ?assets=10000000000                             // 10,000 USDC (6 decimals)
  &slippage=0.5                                   // 0.5% slippage guard
  &limit=10000                                    // max offers walked/returned; default and maximum 10,000

// Response - the Router's execution plan:
{
  "data": {
    "average_best_price": "956937000000000000", // realized target fill using onchain per-offer rounding, rounded against the taker
    "average_worst_price": "952200000000000000", // conservative adverse-placement bound across returned caps; not the slippage-derived guard
    "available_assets": "14000000000", // max assets in this returned limit window
    "available_units": "14630000000", // max units in this returned limit window
    "takeable_offers": [
      {
        "market_id": "0x56b822d7d8be6bded8e1782277989fe5dc4e5b0a4f7f9d349482bc933bd5436c",
        "units": "8000000000", // maximum this offer may contribute, not an exact allocation
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
          "buy": true, // buy offer (bid): the maker is lending
          "maker": "0x7b093658BE7f90B63D7c359e8f408e503c2D9401",
          "max_units": "8000000000",
          "start": 1761922790,
          "expiry": 1786147200,
          "tick": 4988,
          "group": "0x000000000000000000000000000000000000000000000000000000000008b8f4",
          "callback": "0x0000000000000000000000000000000000000000",
          "callback_data": "0x",
          "receiver_if_maker_is_seller": "0x7b093658BE7f90B63D7c359e8f408e503c2D9401",
          "ratifier": "0x0000000000000000000000000000000000000002",
          "reduce_only": false,
          "max_assets": "0",
          "continuous_fee_cap": "115792089237316195423570985008687907853269984665640564039457584007913129639935"
        },
        "ratifier_data": "0x7c1e...d402"
      }
      // Additional complete offers follow in best-price order as fallback excess.
    ]
  }
}

// Interpreting the quote
const quote = response.data;
const avgPrice = Number(quote.average_best_price) / 1e18; // 0.9569
const borrowAPR = (1 / avgPrice - 1) * (365 * 86400) / ttm;

// To borrow 10,000 USDC at price ≈ 0.9569 you sell ≈ 10,450 units
// At maturity you repay 10,450 USDC → net cost ≈ 450 USDC
const unitsToSell = Math.ceil(10000e6 / avgPrice);
```

#### [Step 2: Convert takeable offers to ABI-encoded data](#step-2-convert-takeable-offers-to-abi-encoded-data)

The quote API returns snake_case JSON, whereas the onchain ABI expects camelCase tuples. The `apiOfferToAbi` helper converts the API offer to an ABI struct.

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

const takeableOffers = quote.takeable_offers;

// Map API offers → ABI-ready structs via helper
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

const marketId = "0xd92de5e7fbb...7614";   // from browsing books in Step 1

// SDK wraps the quote endpoint and maps the response into ABI-ready take objects (uses Morpho's router by default, no config needed)
const quote = await MidnightApi.fetchBookQuote({
  marketId,
  side:     "bids",                        // borrower takes bids
  assets:   parseUnits("10000", 6),        // 10,000 USDC to borrow
  slippage: "0.5",                         // 0.5% slippage guard
});

// quote.data contains:
//   .averageBestPrice  (BigInt)
//   .averageWorstPrice (BigInt)
//   .availableAssets   (BigInt)
//   .availableUnits    (BigInt)
//   .takeableOffers    (MidnightApiTake[], ABI-ready)

// ABI-ready takes
const takes: MidnightApiTake[] = quote.data.takeableOffers;

// Compute your borrowing cost
const avgPrice = Number(quote.data.averageBestPrice) / 1e18;
const borrowAPR = (1 / avgPrice - 1) * (365 * 86400) / ttm;
```

## [**Execute the borrow**](#execute-the-borrow)

The recommended path is the [Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/): it derives the collateral (WETH) approval and the one-time `MidnightBundles` authorization for you, applies your rate guard, and builds the atomic supply + borrow bundle. The raw contract call below it is the manual equivalent. Either way, hold sufficient collateral to cover the position at the market's LLTV.

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

// Rate guard: cap the units (debt at maturity) you're willing to sell for
// 10,000 USDC - if the price drops below 0.95, the bundle reverts.
const worstAcceptablePrice = 0.95;
const maxUnits = BigInt(Math.ceil(10_000e6 / worstAcceptablePrice));

// Deadline: the transaction reverts if not included before this timestamp
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600); // 1 hour from now

// Supply 5 WETH collateral and borrow 10,000 USDC atomically. `collateralIndex`
// defaults to 0n - the market's first configured collateral (WETH here).
const supplyCollateralTakeBorrow = midnight.supplyCollateralTakeBorrow({
  accountAddress: taker,
  marketData,
  collateralAssets: parseUnits("5", 18),
  loanAssets: parseUnits("10000", 6),
  maxUnits,
  takeableOffers: quote.data.takeableOffers,
  deadline,
});

// Requirements are plain transactions - the WETH approval to MidnightBundles
// plus the one-time MidnightBundles authorization. The SDK returns only the
// ones that are still missing; send each and wait for its receipt.
for (const requirement of await supplyCollateralTakeBorrow.getRequirements()) {
  const hash = await client.sendTransaction(requirement);
  await client.waitForTransactionReceipt({ hash });
}

const hash = await client.sendTransaction(supplyCollateralTakeBorrow.buildTx());
console.log("Borrow tx:", hash);
```

See [Taker flows](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/#taker-flows) for the full surface, including the borrow-only `takeBorrow`.

### [Raw contract call](#raw-contract-call)

Working below the SDK? Call the `MidnightBundles` contract directly - it takes offers toward your target in one transaction, skipping stale offers automatically, but you handle the approvals and authorization yourself.

**Prerequisites**

The taker must:

1. Authorize `MidnightBundles` on the Midnight contract.
2. Approve `MidnightBundles` to pull the **collateral token** (e.g. WETH).
3. Hold sufficient collateral to cover the position at the market's LLTV.

#### [Authorizations & Approvals](#authorizations--approvals)

Pick between Path 1, Path 2, or Path 3 depending on your UX and signing needs.

```
import {
  erc20Abi, maxUint256, createPublicClient, encodeAbiParameters, parseAbiParameters, parseSignature, parseUnits, http,
} from "viem";
import { base } from "viem/chains";

const MIDNIGHT_BUNDLES = "0x091183d729BE9f808c212b475E387A12E67850A7";   // MidnightBundles on Base (from the @morpho-org/morpho-ts address registry)
const USDC             = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913";   // USDC on Base
const WETH             = "0x4200000000000000000000000000000000000006";   // WETH on Base
const MIDNIGHT         = "0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A";   // Midnight on Base (from the registry)

// Path 1: approve()
// 1. Let MidnightBundles pull WETH during the buy
// 2. maxUint256 = standing allowance
await walletClient.writeContract({
  account: taker, address: WETH, abi: erc20Abi,
  functionName: "approve", args: [MIDNIGHT_BUNDLES, maxUint256],
});

// Variable to set the loanTokenPermit variable to (bundler argument) in the Execute step that follows
const collateralPermitNone   = { kind: 0, data: "0x" } as const;

// --------------------------------------------------------------

// Path 2: EIP-2612
// For a permit-capable COLLATERAL token only (WETH has no permit() but example assumes COLLATERAL of choise has permit())
const COLLATERAL = "0x...";                                               // a permit-capable collateral token
const collateralAmount = parseUnits("1", 18);                             // 1 unit of collateral
const publicClient = createPublicClient({ chain: base, transport: http() });

const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

// Read the taker's current EIP-2612 nonce from the USDC contract
const nonce = await publicClient.readContract({
  address: COLLATERAL,
  abi: [{ name: "nonces", type: "function", stateMutability: "view",
          inputs: [{ name: "owner", type: "address" }],
          outputs: [{ type: "uint256" }] }],
  functionName: "nonces",
  args: [taker],
});

const sig = await walletClient.signTypedData({
  account: taker,
  // TODO: Replace token name and version based on the COLLATERAL choice
  domain: { name: "<Token Name>", version: "<v>", chainId: 8453, verifyingContract: COLLATERAL },
  types: { Permit: [
    { name: "owner",    type: "address" },
    { name: "spender",  type: "address" },
    { name: "value",    type: "uint256" },
    { name: "nonce",    type: "uint256" },
    { name: "deadline", type: "uint256" },
  ] },
  primaryType: "Permit",
  message: { owner: taker, spender: MIDNIGHT_BUNDLES,
             value: collateralAmount, nonce, deadline },
});

const { r, s, v } = parseSignature(sig);

// Variable to set the loanTokenPermit variable to (bundler argument) in the Execute step that follows
const collateralPermitERC2612 = {
  kind: 1,                                                                  // 1 = ERC2612
  data: encodeAbiParameters(
    parseAbiParameters("uint256 deadline, uint8 v, bytes32 r, bytes32 s"),
    [deadline, Number(v), r, s],
  ),
} as const;

// --------------------------------------------------------------

// Path 3: Permit2
// One-time setup (once per token, ever): approve Permit2 on collateral asset (i.e. WETH)
const PERMIT2 = "0x000000000022D473030F116dDEE9F6B43aC78BA3";

// One-time setup: approve Permit2 on WETH. After this, every future authorization is just a signature
await walletClient.writeContract({
  account: taker, address: WETH, abi: erc20Abi,
  functionName: "approve", args: [PERMIT2, maxUint256],
});

// Per-borrow: sign a Permit2 SignatureTransfer (offchain, no gas)
const nonce    = BigInt(Date.now());                                        // unordered nonce (Permit2 uses a bitmap)
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
    permitted: { token: WETH, amount: collateralAmount },
    spender: MIDNIGHT_BUNDLES,
    nonce,
    deadline,
  },
});

// Variable to set the loanTokenPermit variable to (bundler argument) in the Execute step that follows
const collateralPermit2 = {
  kind: 2,                                                                   // 2 = Permit2
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

Specify the target amount of assets you want to sell (i.e. borrow), a price guard, the collateral you want to post, and the bundler's arguments.

```
import { createWalletClient, http, parseUnits, zeroAddress, maxUint256 } from "viem";
import { base } from "viem/chains";
import { midnightBundlesAbi } from "@morpho-org/morpho-sdk/abis";

const MIDNIGHT_BUNDLES = "0x091183d729BE9f808c212b475E387A12E67850A7";        // MidnightBundles on Base (from the @morpho-org/morpho-ts address registry)
const WETH = "0x4200000000000000000000000000000000000006";                    // WETH contract address

// Borrower sells units to receive USDC, depositing WETH as collateral
const targetSellerAssets = parseUnits("10000", 6);                            // want 10,000 USDC

const worstAcceptablePrice = 0.95;                                            // worst price per unit you'll accept

// Calculate maxUnits to set your own price guard (cap your debt obligation by specifying the maximum number of units you're willing to sell) from worst acceptable borrow rate
// If price drops below 0.95, you'd need to sell more units than this so the bundle reverts instead of giving you a worse rate
const maxUnits = BigInt(Math.ceil(10_000e6 / worstAcceptablePrice));

// Calculate collateral needed for the debt you want to take using the market's LLTV, and the oracle price of the collateral asset:
// 1. Retrieve the collateral's LLTV from the "Browse markets" step: collaterals[0].lltv = "770000000000000000" → 77% (WETH's LLTV for this market)
// 2. Fetch your desireable debt at maturity (maxUnits ≈ 10,527 USDC)
// 3. Estimate the minimum collateral value needed for this configuration (debt / LLTV = 10,527 / 0.77 ≈ 13,671 USDC)
// 4. At WETH ≈ $3,000, minimum debt for this position is ≈ 4.56 WETH (at the liquidation boundary)
// 5. Add a safety buffer (i.e. ~10% headroom above minimum) on that to get to 5 WETH
const collateralAmount   = parseUnits("5", 18);                               // 5 WETH collateral

// Deadline: the transaction reverts if not included before this timestamp
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);               // 1 hour from now

// Collateral is referenced by index into the market's collateralParams[] NOT by token address.
// Here collateralIndex 0 = collateralParams[0] = WETH.
// See Authorizations section for different permit inputs (i.e. collateralPermitNone, collateralPermitERC2612, collateralPermit2)
// The permit is per collateral asset and per-supply action; { kind: 0 } means "already approved on the bundle".
const collateralSupplies = [
  { collateralIndex: 0n, assets: collateralAmount, permit: collateralPermitNone },
];

const hash = await walletClient.writeContract({
  account: taker,
  address: MIDNIGHT_BUNDLES,
  abi: midnightBundlesAbi,
  functionName: "midnightBundlesV1SupplyCollateralAndSellWithAssetsTarget",
  args: [
    targetSellerAssets,  // USDC to receive
    maxUnits,            // revert if more units sold than this (rate protection)
    taker,               // taker - the borrower's address
    false,               // reduceOnly (false for a new borrow position)
    taker,               // receiver (where the borrowed USDC is sent)
    collateralSupplies,  // CollateralSupply[] - WETH to deposit as collateral
    takes,               // takes (takeable offers from the quote)
    0n,                  // referralFeePct (0 = none)
    zeroAddress,         // referralFeeRecipient (none)
    maxUint256,          // maxContinuousFee (type(uint256).max disables the check)
    deadline             // deadline (reverts if tx is included after this timestamp)
  ],
});

console.log("Borrow tx:", hash);
```

[Lend at a fixed rate

Previous Page

](https://docs.morpho.org/developers/midnight/tutorials/lend-at-a-fixed-rate/)[Redeem lend at maturity

Next Page

](https://docs.morpho.org/developers/midnight/tutorials/redeem-lend-at-maturity/)