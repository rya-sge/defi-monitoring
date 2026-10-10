# Fixed Rate Market - Midnight

> Source: https://docs.morpho.org/developers/sdks/morpho-sdk/midnight

---

# Fixed Rate Market - Midnight

## [Introduction](#introduction)

**Morpho Midnight** is Morpho's fixed-rate, fixed-term market: lenders and borrowers take signed maker offers that settle credit units onchain at a fixed discount.

The [**Morpho SDK**](https://docs.morpho.org/developers/sdks/morpho-sdk/) is the primary entrypoint for integrating Midnight. [Transaction flows](#transaction-flows) below builds ready-to-send transactions - taker flows, maker publications, and position maintenance - through the same `getRequirements` / `buildTx` flow as every other Morpho surface, via `client.morpho.midnight(chainId)`.

The rest of the page documents the layer **underneath** those flows: the **Midnight toolkit**, which ships inside the Morpho SDK. Reach for it when you need to go below the transaction flows:

- **Make side** - construct offers locally, group offers that share a consumption cap, commit them to a Merkle tree, validate the tree against the Midnight API's mempool policy, sign or approve it through a ratifier, and publish the encoded payload onchain.
- **Take side** - query books, price levels, and quotes from the Midnight API, and execute the returned ABI-ready takes against the `Midnight` contract.

It also ships viem fetch helpers for onchain market and position state, entity classes with local accrual math, TypeScript ports of the protocol's tick math, protocol constants, contract ABIs, and dedicated error classes.

The formerly standalone **Midnight SDK** is no longer a separate integration entrypoint - it has been folded into the [Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/), which ships the toolkit as a dependency and re-exports most of its surface on its own subpaths. Start from the Morpho SDK; use this page when you need the primitives it is built on.

Source: [morpho-org/sdks · packages/midnight-sdk](https://github.com/morpho-org/sdks/tree/main/packages/midnight-sdk)

For protocol theory - how ticks discretize prices, how the mempool and router work, how collateral and liquidations behave - see the [Midnight docs](https://docs.morpho.org/developers/midnight/get-started/), in particular [Tick structure](https://docs.morpho.org/developers/midnight/concepts/tick-structure/), [Market mechanics](https://docs.morpho.org/developers/midnight/concepts/market-mechanics/), and [Mempool & router](https://docs.morpho.org/developers/midnight/concepts/mempool-router/).

## [Installation](#installation)

Everything on this page ships with the [Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/#installation):

```
pnpm add @morpho-org/morpho-sdk@5.8.0 viem@^2.0.0
```

Examples that import primitives directly from `@morpho-org/midnight-sdk` or `@morpho-org/morpho-ts` need those packages declared in your own `dependencies` as well - both ship with the Morpho SDK.

## [Transaction flows](#transaction-flows)

Midnight is Morpho's **fixed-rate, fixed-term** market surface. Instead of the shared, variable-rate [Blue](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/) pool, lenders and borrowers settle credit units at a fixed discount through signed, ratified offers: a **maker** publishes an offer to the Midnight mempool, and a **taker** takes it onchain. Each take locks in the fixed economics encoded by its offer.

The Morpho SDK exposes Midnight through the same `getRequirements` / `buildTx` flow as every other Morpho surface - so you build Midnight transactions with the client, requirement dispatch, and error-handling patterns you already know. The lower-level offer / tree / ratifier toolkit (constructing offers, querying books and quotes, tick math) is documented in the sections that follow.

`client.morpho.midnight(chainId)` returns a `MorphoMidnight` bound to the extended client, keeping reads - market, position, and offer state - separate from transaction construction: the returned `buildTx` callback is synchronous and only consumes data you already passed in. You build for three kinds of flow: **taker** flows take existing offers onchain, **maker** flows publish signed offers to the Midnight mempool, and **position maintenance** covers supplying collateral, redeeming accrued credit, repaying or withdrawing, and cancelling offers.

Midnight is deployed only on Base, so its flows need a client built on that chain - a mainnet client (like the one built in the Morpho SDK page's [Setup](https://docs.morpho.org/developers/sdks/morpho-sdk/#setup)) fails the SDK's chain check. The Midnight deployment lives at chain id `8453` (`ChainId.BaseMainnet`).

### [Setup](#setup)

Midnight lives only on Base, so build a Base wallet client, extend it with `morphoViemExtension()`, and add viem `publicActions` for the block reads the accrual and requirement flows need. Reuse this `midnight` entity across every flow below.

```
import "dotenv/config";
import { type Address, createWalletClient, http, publicActions } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { base } from "viem/chains";
import { morphoViemExtension } from "@morpho-org/morpho-sdk";

const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`);

// Midnight lives on Base, so build the client on `base` (chain id 8453) - not a
// mainnet client. `publicActions` adds the `getBlock` and
// `waitForTransactionReceipt` reads the accrual and requirement flows use.
const client = createWalletClient({
  account,
  chain: base,
  transport: http(process.env.BASE_RPC_URL),
})
  .extend(morphoViemExtension())
  .extend(publicActions);

// Every entity is chain-validated against the client. Reuse `midnight` across
// all Midnight flows below.
const midnight = client.morpho.midnight(base.id);

const user: Address = account.address;
const marketId = "0xMidnightMarketId..." as `0x${string}`;
```

### [Fetch state](#fetch-state)

Read fresh, same-block state and pass it into the builders. Fetch a block once, forward its number to `getMarketData` / `getPositionData`, then accrue the position to that block's timestamp.

| Method | Returns |
| --- | --- |
| `getMarketData(marketId, parameters?)` | A hydrated Midnight `Market` - market params plus current onchain state. |
| `getPositionData({ marketId, accountAddress, parameters? })` | An `AccrualPosition` for the account, paired with its hydrated market. |
| `getOffersData({ accountAddress, offers, validation? })` | Validated maker-offer data: the offer tree, its groups, the ratifier type and address, and any setter payload. |

### [Taker flows](#taker-flows)

A taker takes maker offers surfaced by the Midnight API. Fetch a quote with [the API client](#the-midnight-api-client) (or the API directly), then hand its takeable offers to a taker flow. Each returns the standard `getRequirements` / `buildTx` handles and takes a `deadline`.

The taker flows hard-code `reduceOnly = false` and don't offer a reduce-only early exit at this version - early exits call `MidnightBundles` directly, as covered in the [Exit lend early](https://docs.morpho.org/developers/midnight/tutorials/exit-lend-early/) and [Exit borrow early](https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-early/) tutorials.

```
import { maxUint256, parseUnits } from "viem";

// `quote` comes from `MidnightApi.fetchBookQuote(...)` (see The Midnight API
// client below); it carries the fillable offers and the fill amounts. Pass a
// fresh, same-block market snapshot into the builder.
const block = await client.getBlock();
const marketData = await midnight.getMarketData(marketId, {
  blockNumber: block.number,
});

// Lend side: spend `assets` of the loan token for at least `minUnits` of credit.
// Routes through a MidnightBundles bundle. `deadline` bounds bundle execution -
// pass `maxUint256` for no expiry.
const takeLend = midnight.takeLend({
  accountAddress: user,
  marketData,
  assets: BigInt(quote.data.availableAssets),
  minUnits: BigInt(quote.data.availableUnits),
  takeableOffers: quote.data.takeableOffers,
  deadline: maxUint256,
});

// Midnight requirements are plain transactions - an ERC-20 approval for the spent
// token to the MidnightBundles contract, plus a one-time MidnightBundles
// authorization. Midnight approvals are never Permit / Permit2, and no taker
// requirement is signable, so send each and wait for its receipt.
for (const requirement of await takeLend.getRequirements()) {
  const hash = await client.sendTransaction(requirement);
  await client.waitForTransactionReceipt({ hash });
}

const takeLendTx = takeLend.buildTx();
await client.sendTransaction(takeLendTx);

// Borrow side: receive `loanAssets` for at most `maxUnits` of debt. Also a
// MidnightBundles bundle; its only requirement is the MidnightBundles
// authorization (no token is pulled from the borrower at take time).
const takeBorrow = midnight.takeBorrow({
  accountAddress: user,
  marketData,
  loanAssets: BigInt(quote.data.availableAssets),
  maxUnits: BigInt(quote.data.availableUnits),
  takeableOffers: quote.data.takeableOffers,
  deadline: maxUint256,
});
const takeBorrowTx = takeBorrow.buildTx();

// Supply collateral and borrow atomically in one MidnightBundles bundle.
// `collateralIndex` defaults to 0n (the market's first configured collateral);
// requirements are the collateral approval plus the MidnightBundles authorization.
const supplyCollateralTakeBorrow = midnight.supplyCollateralTakeBorrow({
  accountAddress: user,
  marketData,
  collateralAssets: parseUnits("2", 18),
  loanAssets: BigInt(quote.data.availableAssets),
  maxUnits: BigInt(quote.data.availableUnits),
  takeableOffers: quote.data.takeableOffers,
  deadline: maxUint256,
});
const supplyCollateralTakeBorrowTx = supplyCollateralTakeBorrow.buildTx();
```

### [Maker flows](#maker-flows)

A maker publishes signed offers to the Midnight mempool rather than sending an onchain take. These flows are **async** - they validate the offer tree against the mempool API up front - and return the offer `groups`, the tree `root`, the `ratifierType`, plus the `getRequirements` / `buildTx` handles.

```
import { parseUnits } from "viem";
import { isRequirementSignature } from "@morpho-org/morpho-sdk";
import { Offer } from "@morpho-org/midnight-sdk";

// Offers, groups, and trees are built with the Midnight toolkit - see Making
// offers below for the full model. `market` is the Midnight market description
// and `ecrecoverRatifier` the ratifier address for the chain.
const lendOffer = Offer.create({
  market,
  maker: user,
  buy: true, // maker buys units = lends
  tick: 5_000n,
  maxAssets: parseUnits("250000", 6),
  // now + 7 days, capped at the market's maturity
  expiry: BigInt(Math.min(Number(market.maturity), Math.floor(Date.now() / 1000) + 604_800)),
  ratifier: ecrecoverRatifier,
});

// makeLend is async: it validates the offer tree against the mempool API, then
// resolves to the tree `root`, its `groups`, the `ratifierType`, and the flow
// handles. `loanAssets` is the group's loan reserve.
const makeLend = await midnight.makeLend({
  accountAddress: user,
  offers: [lendOffer],
  loanToken: market.loanToken,
  loanAssets: parseUnits("250000", 6),
});

// makeLend first returns a loan-token ERC-20 approval to the Midnight contract,
// then the ratifier requirements. The ratifier path depends on `ratifierType`:
//   - "ecrecover": a signable requirement - sign it and pass the signature to buildTx.
//   - "setter":    a root-approval transaction to send; buildTx then needs no signature.
const signatures = [];
for (const requirement of await makeLend.getRequirements()) {
  if (isRequirementSignature(requirement)) {
    signatures.push(await requirement.sign(client, user));
  } else {
    const hash = await client.sendTransaction(requirement);
    await client.waitForTransactionReceipt({ hash });
  }
}

// Publishes the encoded, ratified offer payload to the Midnight mempool.
const makeLendTx = makeLend.buildTx(signatures);
await client.sendTransaction(makeLendTx);

// Borrow-side maker offers need no loan reserve - only the ratifier requirements.
// `borrowOffer` is a borrow-side `Offer.create({ ..., buy: false })`.
const makeBorrow = await midnight.makeBorrow({
  accountAddress: user,
  offers: [borrowOffer],
});
const makeBorrowRequirements = await makeBorrow.getRequirements();
const makeBorrowTx = makeBorrow.buildTx(/* [signature] on the ecrecover route */);

// Supply collateral and publish borrow-side offers together. Its requirements are
// the collateral approval, the collateral supply, and the ratifier requirements.
const supplyCollateralMakeBorrow = await midnight.supplyCollateralMakeBorrow({
  accountAddress: user,
  market,
  collateralAssets: parseUnits("2", 18),
  offers: [borrowOffer],
});
const supplyCollateralMakeBorrowTx = supplyCollateralMakeBorrow.buildTx();
```

### [Position maintenance](#position-maintenance)

```
import { maxUint256, parseUnits } from "viem";

const block = await client.getBlock();
const marketData = await midnight.getMarketData(marketId, {
  blockNumber: block.number,
});

// Supply collateral directly to the Midnight contract (no bundle). Its only
// requirement is a collateral ERC-20 approval to the Midnight contract.
const supplyCollateral = midnight.supplyCollateral({
  accountAddress: user,
  marketData,
  collateralAssets: parseUnits("2", 18),
});
for (const requirement of await supplyCollateral.getRequirements()) {
  const hash = await client.sendTransaction(requirement);
  await client.waitForTransactionReceipt({ hash });
}
const supplyCollateralTx = supplyCollateral.buildTx();

// Redeem accrued fixed-rate credit - a direct Midnight `withdraw` call with no
// requirements. `units` defaults to the position's face value and `receiver`
// defaults to `accountAddress`. Pass a fresh, accrued position snapshot.
const positionData = (
  await midnight.getPositionData({
    marketId,
    accountAddress: user,
    parameters: { blockNumber: block.number },
  })
).accrueInterest(block.timestamp);

const redeem = midnight.redeem({
  accountAddress: user,
  positionData,
});
const redeemTx = redeem.buildTx();
await client.sendTransaction(redeemTx);

// Repay debt and/or withdraw collateral in one MidnightBundles bundle. Repay-only
// and withdraw-only are both valid, but both amounts zero throws. Requirements are
// a loan-token approval (only when repayAssets > 0) plus a MidnightBundles
// authorization.
const repayWithdrawCollateral = midnight.repayWithdrawCollateral({
  accountAddress: user,
  marketData,
  repayAssets: parseUnits("1000", 6),
  withdrawCollateralAssets: parseUnits("2", 18),
  deadline: maxUint256,
});
const repayWithdrawCollateralTx = repayWithdrawCollateral.buildTx();

// Cancel a maker group - a direct Midnight `setConsumed` call with no
// requirements. Pass a `group` id from a maker output's `groups`.
const cancelOffer = midnight.cancelOffer({
  group,
  accountAddress: user,
});
const cancelOfferTx = cancelOffer.buildTx();
```

See the [Actions overview](https://docs.morpho.org/developers/sdks/morpho-sdk/#actions-overview) on the Morpho SDK page for the full route table and its [Errors and invariants](https://docs.morpho.org/developers/sdks/morpho-sdk/#errors-and-invariants) for the Midnight error classes.

The rest of this page is the lower-level toolkit: there is no `getRequirements` / `buildTx` flow and no bundler composition. You construct protocol objects, sign typed data, and send transactions with your own `viem` client.

## [Core concepts](#core-concepts)

How the toolkit's types map onto the protocol:

- **Markets.** A Midnight market is fully described by its immutable params - `loanToken`, `collateralParams` (one `{ token, lltv, liquidationCursor, oracle }` entry per accepted collateral), `maturity`, `rcfThreshold`, `enterGate` / `liquidatorGate` - plus the `chainId` and `midnight` contract address. The SDK models them as `MarketParams`, and a hydrated `Market` adds mutable state. Onchain reads address markets by their `marketId` hash.
- **Ticks and prices.** Offer prices live on a discrete tick grid: each tick indexes a WAD-scaled price ≤ 1 (the discount paid today per unit redeemed at maturity), so a tick is equivalently a fixed rate. Ticks must be aligned to the market's tick spacing. `TickLib` converts tick ↔ price ↔ rate ↔ APR - see [Tick math](#tick-math).
- **Units and assets.** Offer consumption is capped either in **units** (the protocol's normalized quantity dimension) or in **assets** (loan-token amounts). Exactly one of `maxUnits` / `maxAssets` must be non-zero on an offer; `TakeAmountsLib` converts between the two at a given tick.
- **Offers.** A maker offer commits to a market, a side (`buy: true` - the maker buys units, i.e. lends; `buy: false` - the maker sells units, i.e. borrows), a `tick`, a consumption cap, a `start` / `expiry` window, and a `ratifier`. Optional fields (`reduceOnly`, `continuousFeeCap`, maker callback, …) default to protocol-sensible values in `Offer.create`.
- **Ratifiers.** Offers are not individual transactions - makers commit a whole tree of offers at once, and a **ratifier** contract proves maker intent when an offer is taken. Two routes ship with the protocol: the **EcrecoverRatifier** (an EOA - or authorized signer - signs the tree root as typed data) and the **SetterRatifier** (a contract maker approves the tree root onchain). `fetchRatifierInfo` inspects the maker's bytecode and tells you which route to use. See [Ratification](#ratification) for what the ratifier data proves, why the design pays off, and how to cancel or customize it.
- **Mempool.** Encoded offer payloads are published as calldata to the Midnight mempool contract, where the offchain router and API index them into books. See [Mempool & router](https://docs.morpho.org/developers/midnight/concepts/mempool-router/).

## [Making offers](#making-offers)

The make side is a pipeline: build offers → group the ones that should share a cap → commit everything to a tree → validate → sign or approve through the ratifier → encode → publish.

The [maker flows](#maker-flows) above run this pipeline for you - they take `Offer` objects, validate the tree, dispatch the ratifier requirements, and build the mempool submission. Run the steps below yourself when you need control the flows don't expose.

### [1. Define the market and create offers](#1-define-the-market-and-create-offers)

```
import { addresses } from "@morpho-org/morpho-ts";
import { Offer } from "@morpho-org/midnight-sdk";
import { parseUnits, zeroAddress, type Address } from "viem";

const chainId = 8453;
const usdc = addresses[chainId].usdc!;
const cbBtc = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf" as Address;   // cbBTC on Base
const midnightAddress = addresses[chainId].midnight!;
const ecrecoverRatifier = addresses[chainId].ecrecoverRatifier!;

const maker = "0xMaker00000000000000000000000000000000000" as Address;
const usdcOracle = "0x4429112b3C00b40Cf295db81cfcdE39d7d5ADC1d" as Address;    // from the live market's collateralParams
const cbBtcOracle = "0x663BECd10daE6C4A3Dcd89F1d76c1174199639B9" as Address;   // from the live market's collateralParams

// Immutable market description, copied verbatim from a live Base market
// (0xf5564b5322b8...3fc5, GET /v0/midnight/markets?chain_id=8453) so its
// maturity is in the future. Onchain reads address the market by its id hash.
const market = {
  chainId,
  midnight: midnightAddress,
  loanToken: usdc,
  collateralParams: [
    {
      token: usdc,
      lltv: 980_000_000_000_000_000n,
      liquidationCursor: 300_000_000_000_000_000n,
      oracle: usdcOracle,
    },
    {
      token: cbBtc,
      lltv: 860_000_000_000_000_000n,
      liquidationCursor: 300_000_000_000_000_000n,
      oracle: cbBtcOracle,
    },
  ],
  maturity: 1_806_073_200n, // 2027-03-26 15:00:00 UTC.
  rcfThreshold: 3_000000000n,
  enterGate: zeroAddress,
  liquidatorGate: zeroAddress,
};

// Offer expiry - now + 7 days, capped at the market's maturity
const offerExpiry = BigInt(Math.min(Number(market.maturity), Math.floor(Date.now() / 1000) + 604_800));

const commonOffer = {
  market,
  maker,
  expiry: offerExpiry,
  ratifier: ecrecoverRatifier,
};

// Maker buys units = lends. `maxAssets` caps consumption in loan-token terms.
const lend250kUsdc = Offer.create({
  ...commonOffer,
  buy: true,
  tick: 5_000n,
  maxAssets: parseUnits("250000", 6),
});

// Maker sells units = borrows. `maxUnits` caps consumption in units.
const borrow50Units = Offer.create({
  ...commonOffer,
  buy: false,
  tick: 5_024n,
  maxUnits: parseUnits("50", 18),
});
```

Fields you omit get protocol defaults: `start` defaults to zero (immediately takeable), `continuousFeeCap` to the protocol maximum, `callback` / `callbackData` to none, and `receiverIfMakerIsSeller` to the maker on sell offers. Exactly one of `maxUnits` / `maxAssets` must be non-zero.

### [2. Group offers that share a consumption cap (optional)](#2-group-offers-that-share-a-consumption-cap-optional)

`Group.create` puts several offers behind **one shared consumption budget** - Midnight tracks a single consumed scalar per maker and group. Offers in a group must share maker, side, loan token, and cap mode and value; the group id is derived by hashing the offers, and each offer is copied with that id.

```
import { Group } from "@morpho-org/midnight-sdk";

// One 250k USDC budget posted at two ticks - a fill on either tick
// consumes the same shared cap.
const lendLadder = Group.create([
  Offer.create({ ...commonOffer, buy: true, tick: 5_000n, maxAssets: parseUnits("250000", 6) }),
  Offer.create({ ...commonOffer, buy: true, tick: 5_012n, maxAssets: parseUnits("250000", 6) }),
]);
```

Group creation is resource-intensive compared to offer construction - build offers first, group once.

For makers quoting a fixed rate across a longer window, the `OfferChainUtils` namespace builds **offer chains** - adjacent grouped offers whose expiries tile the window so the maker's displayed fixed rate stays stable across it. `OfferChainUtils.buildLendFixedRateOfferChain` and `OfferChainUtils.buildBorrowFixedRateOfferChain` construct the chains, and `OfferChainUtils.getMaxFixedRateOfferChainEndTimestamp` bounds a chain's end timestamp.

### [3. Commit to a tree](#3-commit-to-a-tree)

`Tree.create` accepts a mix of standalone offers and groups and commits them into one Merkle tree - the unit that ratifiers sign or approve.

```
import { Tree } from "@morpho-org/midnight-sdk";

const tree = Tree.create([lendLadder, borrow50Units]);
// tree.root         - Merkle root the ratifier signs or approves.
// tree.offers       - non-padding offers in leaf order.
// tree.paddedOffers - ABI-compatible offers including protocol-zero padding.
// tree.leaves, tree.height
```

### [4. Validate against the mempool policy](#4-validate-against-the-mempool-policy)

```
// Ratification data is optional pre-signature - validating early catches API
// policy issues before asking the maker to sign.
await tree.mempoolValidate({ chainId });
```

`mempoolValidate` throws `MidnightMempoolValidationError` - carrying the API's `issues` - when policy validation fails. Pass `apiUrl` to target a custom Midnight API deployment.

### [5. Sign and ratify (EOA makers)](#5-sign-and-ratify-eoa-makers)

```
import { EcrecoverRatifierUtils } from "@morpho-org/morpho-sdk/utils";

// Derives the verifying contract from `offer.ratifier` and rejects
// mixed-ratifier trees. `account` may be the maker or an authorized signer
// for every maker in the tree.
const signature = await EcrecoverRatifierUtils.sign({
  tree,
  client: walletClient,
  account: maker,
});

// Optional: re-validate the final payload shape with real ratification data.
await tree.mempoolValidate({
  chainId,
  ratification: { type: "ecrecover", account: maker, signature },
});

const items = await EcrecoverRatifierUtils.ratify({
  tree,
  account: maker,
  signature,
});
```

Signing throws `ChainIdMismatchError` when the client's chain does not match the offer market's chain, and `InvalidTypedDataSignatureError` when the signature does not recover to the expected signer.

When the maker is a **contract**, use `SetterRatifierUtils` instead: build the `Tree`, validate it, submit the root approval transaction for every maker in the tree, then call `SetterRatifierUtils.ratify({ tree })` before encoding. The `setterRatifierAbi` export covers the approval call.

### [6. Encode and publish](#6-encode-and-publish)

```
import { Payload } from "@morpho-org/morpho-sdk/utils";
import { addresses } from "@morpho-org/morpho-ts";

const payload = await Payload.encode(items);

const transactionHash = await walletClient.sendTransaction({
  account: maker,
  to: addresses[chainId].midnightMempool!,
  data: payload,
});
```

`Payload.encode` turns ratified items into wire bytes for mempool publication; `Payload.decode` inspects published maker offers, ratifier data, or attribution-tagged payloads.

## [Ratification](#ratification)

Publishing a payload stores nothing onchain per offer - the mempool payload is calldata. **Ratification** is what makes those offchain offers binding: when a taker calls `Midnight.take(offer, ratifierData, ...)`, the contract runs two checks before moving any funds.

1. **The maker trusts the ratifier.** `offer.ratifier` must be authorized by the maker in Midnight's authorization mapping, or the take reverts with `RatifierUnauthorized`. Authorizing a ratifier is a one-time `Midnight.setIsAuthorized(ratifier, true, maker)` transaction per maker (the `midnightAbi` export covers it) - until it has happened, published offers sit in the mempool but cannot be taken.
2. **The ratifier vouches for the offer.** Midnight calls `isRatified(offer, ratifierData)` on the ratifier contract and reverts with `RatifierFailed` unless it returns the protocol's success value. The `ratifierData` bytes are the proof material for that call: each ratifier defines its own format, and the core protocol never interprets them.

### [What the ratifier data contains](#what-the-ratifier-data-contains)

Both shipped ratifiers verify the same claim - *this offer is a leaf of a tree the maker committed to* - and differ only in how the commitment was made:

| Route | `ratifierData` decodes to | Commitment it proves |
| --- | --- | --- |
| **EcrecoverRatifier** | `(signature (v, r, s), root, leafIndex, proof)` | The maker - or a signer the maker authorized on Midnight - signed the tree root as EIP-712 typed data |
| **SetterRatifier** | `(root, leafIndex, proof)` | The maker - or an authorized account - approved the root onchain via `setIsRootRatified` |

In [step 5](#5-sign-and-ratify-eoa-makers), the signature covers only the tree **root** - one signature for the whole tree. `EcrecoverRatifierUtils.ratify` expands it into one `Payload.Item` (`{ offer, ratifierData }`) per offer: each item embeds the shared signature and root plus that offer's own `leafIndex` and Merkle `proof`, which is how the onchain ratifier re-links a single leaf to the signed root. The three offers in the example tree publish with the same signature and three different proofs.

The take side sees the same bytes coming back: every take object returned by the [API](#the-midnight-api-client) carries the `ratifierData` that was published with the offer, and the [take loop](#taking-offers) forwards it verbatim as the second argument of `Midnight.take`. Takers never build or parse ratifier data - the SDK treats it as opaque bytes end to end. To inspect it anyway (diagnostics, decoding published payloads), use the scheme's decoder:

```
import { EcrecoverRatifierUtils } from "@morpho-org/morpho-sdk/utils";

const { signature, root, leafIndex, proof } =
  EcrecoverRatifierUtils.decodeRatifierData(items[0]!.ratifierData);
```

`SetterRatifierUtils.decodeRatifierData` is the Setter-route equivalent.

### [Why offers are ratified instead of sent](#why-offers-are-ratified-instead-of-sent)

- **One commitment covers the whole tree.** Quoting many ticks and markets costs one signature (or one root-approval transaction) however many offers the tree holds - heights up to 20 are supported, over a million leaves. Requoting is a new tree and a new signature, not per-offer transactions. See [Multi-market offers](https://docs.morpho.org/developers/midnight/concepts/multi-market-offers/) for how this composes with consumption groups.
- **Stale quotes cost nothing.** Nothing is written to contract storage at publication, and offers retire themselves at `expiry` - abandoning a tree is free.
- **Signing can be delegated.** Both routes accept commitments from any account the maker authorized on Midnight, not just the maker key - an operational bot key can quote on behalf of a treasury maker. This is why `EcrecoverRatifierUtils.sign` and `ratify` take an `account` distinct from the maker. A tree may even mix makers: the signer must then be authorized by each of them (on the Setter route, each maker approves the same root once).
- **Contract makers still work.** Accounts that cannot produce ECDSA signatures (multisigs, contract vaults) commit through the Setter route; EIP-7702 accounts keep signing through Ecrecover. `fetchRatifierInfo` picks the route from the maker's bytecode.

### [Cancelling ratified offers](#cancelling-ratified-offers)

A signature cannot be un-signed, so cancellation is onchain state that the take-time checks consult:

| Lever | Scope | Notes |
| --- | --- | --- |
| `EcrecoverRatifier.cancelRoot(maker, root)` | Every offer in one tree | Irreversible. Callable by the maker or an account authorized on Midnight; pass `tree.root`. The `ecrecoverRatifierAbi` export covers the call |
| `SetterRatifier.setIsRootRatified(maker, root, false)` | Every offer in one tree | Reversible - the same call with `true` re-arms the root |
| `Midnight.setConsumed(group, maxUint256, maker)` | Every offer sharing one group id | Consumption can only increase, so maxing it out permanently exhausts the budget. Standalone offers derive their own group id - read it from `offer.group` |
| `Midnight.setIsAuthorized(ratifier, false, maker)` | Every offer naming that ratifier | The `RatifierUnauthorized` check fails before the ratifier is even called |

### [Custom ratifiers](#custom-ratifiers)

`offer.ratifier` is just an address, and the two take-time checks above are the entire protocol contract - any contract that implements the protocol's `IRatifier` interface (a single view function, `isRatified(Offer offer, bytes ratifierData) returns (bytes32)`) can serve as a ratifier by returning the protocol success value only when its policy holds. Because it receives the full offer plus a byte blob whose format you define, a custom ratifier can gate takeability on offer fields, chain state, or extra proof material. The SDK stays out of the way: build `Payload.Item`s with your own `ratifierData` bytes, and `Payload.encode` / `Payload.decode` carry them unchanged - takers forward them to `take` like any other offer.

Authorization is binding: once a maker calls `setIsAuthorized` for a ratifier, every offer that ratifier accepts is takeable against the maker's position. Audit under which conditions a ratifier returns success before authorizing it - a ratifier that unconditionally succeeds lets anyone fabricate offers on the maker's behalf.

One practical limit: the hosted Midnight API only indexes offers whose ratifier is on its per-chain allowlist, because the router replicates ratifier logic offchain before booking an offer (see [Mempool & router](https://docs.morpho.org/developers/midnight/concepts/mempool-router/#validating-offers)). Custom-ratified offers fail `tree.mempoolValidate` with a `ratifier` issue and never appear in books or quotes - they remain takeable onchain, but you distribute them to takers yourself. `fetchRatifierInfo` and the ratifier utils cover only the two shipped routes.

## [Taking offers](#taking-offers)

The take side starts from API responses: book, quote, and takeable-offer endpoints return ABI-ready take objects - each with `offer`, `ratifierData`, and `units` for `Midnight.take`, plus `marketId` metadata. The `ratifierData` bytes are the maker's [ratification](#ratification) proof - forward them to `take` untouched. Book **asks** are maker sell offers; book **bids** are maker buy offers.

For production takes, prefer the [taker flows](#taker-flows) above - they wrap a quote's takeable offers in a bundled transaction with requirement handling. The raw loop below is the manual equivalent:

```
import { midnightAbi } from "@morpho-org/morpho-sdk/abis";
import { MidnightApi } from "@morpho-org/morpho-sdk/midnight-api";
import { addresses } from "@morpho-org/morpho-ts";
import { parseUnits, zeroAddress, type Address, type Hash } from "viem";

const chainId = 8453;
const midnightAddress = addresses[chainId].midnight!;

const marketId = "0xMarketId..." as Hash;
const taker = "0xTaker00000000000000000000000000000000000" as Address;
const receiverIfTakerIsSeller = taker;

// Quote how to fill 50 units from the ask side, tolerating 0.5% slippage.
const quote = await MidnightApi.fetchBookQuote({
  marketId,
  side: "asks",
  units: parseUnits("50", 18),
  slippage: "0.5",
});

// A quote can span several offers: execute the returned takes IN ORDER and
// clamp each take to the remaining target instead of submitting every
// returned cap blindly.
let remainingUnits = parseUnits("50", 18);

for (const take of quote.data.takeableOffers) {
  if (remainingUnits === 0n) break;

  const units = take.units < remainingUnits ? take.units : remainingUnits;
  if (units === 0n) continue;

  await walletClient.writeContract({
    account: taker,
    address: midnightAddress,
    abi: midnightAbi,
    functionName: "take",
    args: [
      take.offer,
      take.ratifierData,
      units,
      taker,
      receiverIfTakerIsSeller,
      zeroAddress, // no taker callback
      "0x",
    ],
  });
  remainingUnits -= units;
}
```

## [The Midnight API client](#the-midnight-api-client)

`MidnightApi` (from `@morpho-org/morpho-sdk/midnight-api`) is both a static helper surface and an instantiable client. Static methods target `https://api.morpho.org/v0/midnight` by default and accept per-call configuration; instantiate the class when an integration makes repeated calls or needs shared request options (`baseUrl`, a custom `fetch` implementation, and `request` options such as headers, credentials, and abort signals). The SDK owns endpoint paths, HTTP methods, request bodies, and response normalization; caller inputs and successful JSON output shapes are trusted at runtime.

The Midnight API helpers (`@morpho-org/morpho-sdk/midnight-api`) are **not a stable import surface** and may not respect semver versioning. Pin your SDK version if you depend on them.

```
import { MidnightApi } from "@morpho-org/morpho-sdk/midnight-api";

// One-off static call:
const books = await MidnightApi.fetchBooks({ chainIds: [8453], limit: 10 });

// Shared configuration for repeated calls:
const api = new MidnightApi({ baseUrl: "https://api.morpho.org/v0/midnight" });
const book = await api.fetchBook({ marketId });
```

| Method | Reads | Returns |
| --- | --- | --- |
| `fetchBooks` | `GET /books` | Paginated active books with market metadata and top price levels, mapped to SDK camelCase fields. |
| `fetchBook` | `GET /books/{marketId}` | A single book snapshot with market metadata and both sides. |
| `fetchBookPriceLevels` | `GET /books/{marketId}/{side}` | One side of a book grouped by price level. |
| `fetchBookTakeableOffers` | `GET /books/{marketId}/{side}/takeable-offers` | ABI-ready take objects for one side of a book. |
| `fetchBookQuote` | `GET /books/{marketId}/{side}/quote` | A quote (average best/worst price, available assets and units) plus signed ABI-ready take caps for one side. |
| `fetchTakeableOffers` | `GET /takeable-offers` | Paginated ABI-ready take objects for one maker's unexpired, unmatured offers. |
| `validateMempoolPayload` | `POST /mempool/validate` | The API's validation `issues` and a `valid` summary for already-encoded payload bytes. |
| `validateMempoolItems` | `POST /mempool/validate` | The API's validation `issues` and a `valid` summary after encoding the given SDK-native payload items. |

Every method throws `MidnightApiError` on a non-2xx response and `InvalidMidnightApiResponseError` on a malformed success body. `validateMempoolPayload` is the raw, **non-throwing** validation surface for already-encoded payload bytes - in normal make-side flows prefer `tree.mempoolValidate(...)`, which throws `MidnightMempoolValidationError` with the API's issues.

The same endpoints are documented in the [Midnight API reference](https://docs.morpho.org/api/midnight/books/list-books/).

## [Reading onchain state](#reading-onchain-state)

The fetch helpers are plain viem functions imported from the toolkit package: they resolve the Midnight contract address for the client's chain from the `@morpho-org/morpho-ts` address registry, and accept optional `account`, `blockNumber`, `blockTag`, and `stateOverride` call parameters. (For typical reads, [Fetch state](#fetch-state) covers the same ground at a higher level.)

| Fetcher | Reads | Returns |
| --- | --- | --- |
| `fetchMarketParams(client, { marketId })` | `Midnight.toMarket` | `MarketParams` - the market's immutable params |
| `fetchMarket(client, { marketId })` | `Midnight.toMarket` + `Midnight.marketState` | `Market` - params hydrated with mutable state |
| `fetchPosition(client, { marketId, user })` | Deployless `GetPosition` query (fallback: `Midnight.position` + up to 128 collateral slots) | `Position` - credit, pending fee, debt, collateral balances |
| `fetchAccrualPosition(client, { marketId, user })` | `fetchPosition` + `fetchMarket` in parallel | `AccrualPosition` - the position bound to its market |
| `fetchRatifierInfo(client, { maker })` | The maker's bytecode | `RatifierInfo` - which ratifier route to use, and its address |

`fetchPosition` defaults to a deployless multicall-style query with a per-slot fallback; pass `deployless: "force"` to disable the fallback or `deployless: false` to skip it entirely.

`AccrualPosition.accrueInterest(timestamp)` reproduces Midnight's `updatePositionView` locally - it returns a new accrued position without an RPC round-trip. It validates its inputs and throws `InvalidPositionAccrualTimestampError`, `InvalidPositionLossFactorError`, or `InvalidPositionAccrualStateError` on inconsistent snapshots - fetch the market and position at the same block. Related helpers: `getCollateralBalanceByIndex` / `getCollateralBalanceByToken`, `getSettlementFee(timestamp)`, and the accrued position's `withdrawable` getter - the maximum credit units currently withdrawable, capped by both the accrued credit and the market's currently withdrawable liquidity.

## [Tick math](#tick-math)

`TickLib` is a TypeScript port of the onchain `TickLib`; `TakeAmountsLib` converts between units and assets when preparing takes. Both are importable from `@morpho-org/morpho-sdk/utils`. Everything is `bigint` / WAD math - no floats.

| Function | Converts | Notes |
| --- | --- | --- |
| `TickLib.divHalfDownUnchecked(x, d)` | dividend → quotient | Divides with half-down rounding without validating the denominator. |
| `TickLib.assertTickInRange(tick)` | tick → validated `bigint` | Asserts the tick is non-negative and at most `MAX_TICK`; throws `NegativeValueError` or `TickOutOfRangeError`. |
| `TickLib.wExp(x)` | WAD exponent → WAD exponential | The WAD-scaled exponential approximation underpinning tick pricing; inverts for negative `x`. |
| `TickLib.tickToPrice(tick)` | tick → WAD price | Rounds the result to `PRICE_ROUNDING_STEP`; validates the tick range. |
| `TickLib.priceToTick(price, spacing?)` | WAD price → tick | Returns the lowest spacing-aligned tick whose price is at least `price`; `spacing` defaults to `DEFAULT_TICK_SPACING`; throws `PriceGreaterThanOneError` above WAD and `InvalidTickSpacingError` on bad spacing. |
| `TickLib.snapPriceToTick(price, spacing?)` | WAD price → WAD price | SDK-only convenience that snaps a price to the price of the lowest aligned tick at or above it. |
| `TickLib.rateToPrice(rate)` | WAD fixed rate → WAD price | SDK-only rate conversion; rounds down. |
| `TickLib.tickToRate(tick)` | tick → WAD fixed rate | SDK-only rate conversion; rounds up and throws `DivisionByZeroError` when the tick price is zero. |
| `TickLib.tickToApr(tick, timeToMaturity)` | tick → WAD simple APR | SDK-only display convenience; annualizes `tickToRate` over `timeToMaturity` seconds, rounds up, throws `DivisionByZeroError` when maturity or price is zero. |
| `TickLib.assertTickAlignedToSpacing(tick, spacing?)` | tick → validated `bigint` | SDK-only assertion that the tick is in range and aligned to `spacing`; throws `InvalidTickSpacingError` when misaligned. |
| `TakeAmountsLib.prices({ offer, settlementFee })` | offer + fee → buyer/seller prices | Derives `buyerPrice` and `sellerPrice` from the offer tick; throws `SettlementFeeExceedsPriceError` when the fee exceeds a buy offer's price. |
| `TakeAmountsLib.buyerAssetsToUnits({ offer, targetBuyerAssets, settlementFee })` | buyer assets → units | Rounds up for buy offers and down otherwise; throws `DivisionByZeroError`, `PriceGreaterThanOneError`, or `SettlementFeeExceedsPriceError`. |
| `TakeAmountsLib.sellerAssetsToUnits({ offer, targetSellerAssets, settlementFee })` | seller assets → units | Rounds up for buy offers and down otherwise; throws `DivisionByZeroError` when the seller price is zero. |
| `TakeAmountsLib.toUnits({ assets, price, rounding })` | assets → units | SDK-only generic conversion at an explicit WAD price with a caller-supplied `rounding`; throws `DivisionByZeroError` when price is zero. |
| `TakeAmountsLib.toUnitsAtTick({ assets, tick, rounding })` | assets → units | SDK-only conversion at a tick price via `tickToPrice`, then `toUnits`. |

## [Protocol constants](#protocol-constants)

The SDK re-exports the protocol's deployed constants so your code never hardcodes them:

| Constant | Value | Meaning |
| --- | --- | --- |
| `CBP` | `1_000000000000n` | Centibip scale used by settlement fees. |
| `SETTLEMENT_FEE_BREAKPOINTS` | 7 `bigint` seconds, `0n` → `31_104_000n` (0, 1, 7, 30, 90, 180, 360 days) | Settlement-fee time-to-maturity breakpoints across which Midnight linearly interpolates each market's seven settlement-fee cbp buckets. |
| `MAX_TICK` | `6744n` | Maximum Midnight tick. |
| `PRICE_ROUNDING_STEP` | `100_000000000n` | WAD price quantum used by Midnight tick prices. |
| `DEFAULT_TICK_SPACING` | `4n` | Default Midnight tick spacing. |
| `MAX_COLLATERALS` | `128n` | Maximum collateral entries in a Midnight market. |
| `MAX_COLLATERALS_PER_BORROWER` | `16n` | Maximum active collateral entries per borrower. |
| `MAX_SETTLEMENT_FEES` | 7 `bigint`, `14000000000000n` → `5000000000000000n` | Maximum settlement-fee values by Midnight fee index. |
| `MAX_CONTINUOUS_FEE` | `317097919n` | Maximum continuous fee per second. |
| `MAX_OFFER_CAP` | `maxUint128` | Maximum value accepted by the uint128 offer cap fields. |
| `TIME_TO_MAX_LIF` | `3600n` | Seconds after maturity over which post-maturity LIF reaches the computed maximum liquidation incentive factor. |
| `COLLATERAL_PARAMS_TYPEHASH` | `0x39ed3f92…85b841` | HashLib EIP-712 typehash for the collateral params struct. |
| `MARKET_TYPEHASH` | `0x510b3862…20391a` | HashLib EIP-712 typehash for the market struct. |
| `OFFER_TYPEHASH` | `0x99052142…9d8906` | HashLib EIP-712 typehash for the offer struct. |
| `EIP712_DOMAIN_TYPEHASH` | `0x47e79534…469218` | EcrecoverRatifier EIP-712 domain typehash. |

All of these are importable from `@morpho-org/morpho-sdk/constants`; `MAX_OFFER_CAP` and `TIME_TO_MAX_LIF` come from the toolkit package directly, while the Morpho SDK re-exports them as `MIDNIGHT_MAX_OFFER_CAP` and `MIDNIGHT_TIME_TO_MAX_LIF`.

## [Errors](#errors)

The SDK throws dedicated error classes (no generic `Error`s) so you can branch on failure modes deterministically - one row per class exported from `src/errors.ts`:

| Error | When it triggers |
| --- | --- |
| `TickOutOfRangeError` | A tick exceeds the deployed `TickLib` maximum during tick or offer construction. |
| `PriceGreaterThanOneError` | A price is above the maximum WAD price (1) accepted by `TickLib`. |
| `InvalidTickSpacingError` | The tick spacing is not a positive divisor of the maximum tick, or a tick is not aligned to the market's spacing. |
| `SettlementFeeExceedsPriceError` | A buy offer's settlement fee exceeds its tick price. |
| `InvalidOfferParameterError` | An offer builder receives a parameter that cannot satisfy Midnight protocol rules (carries the offending `parameter` and `value`). |
| `InvalidMarketParameterError` | A market parameter cannot satisfy Midnight protocol rules (carries the offending `parameter` and `value`). |
| `UnknownCollateralIndexError` | A market collateral index is queried that the market does not configure (carries `market` and `collateralIndex`). |
| `InvalidOfferGroupError` | Offers grouped together violate group mechanics - they must share maker, side, loan token, and cap mode and value. |
| `InvalidTreeHeightError` | A tree height exceeds the ratifier typehash table. |
| `InvalidTreeError` | A tree cannot be represented by the ratifiers, for example when it is empty. |
| `ChainIdMismatchError` | The viem client's chain id does not match the offer market's chain id required by a signing flow (carries `clientChainId` and `expectedChainId`). |
| `InvalidTypedDataSignatureError` | A typed-data signature does not recover to the expected signer (carries the expected `signer`). |
| `InvalidEcrecoverSignatureVError` | Decoded Ecrecover ratifier data contains a non-canonical signature `v` value - canonical Ethereum `v` is 27 or 28 (carries the invalid `v`). |
| `PayloadDecodeError` | Mempool payload bytes cannot be encoded or decoded (carries a machine-readable `reason`). |
| `MidnightApiError` | The Midnight API returns a non-2xx response (carries `status`, and `code` / `details` / `requestId` when present). |
| `InvalidMidnightApiResponseError` | The Midnight API returns a 2xx response whose body is malformed or missing expected data. |
| `MidnightMempoolValidationError` | The Midnight API rejects a tree during mempool policy validation (carries the API's `issues`). |
| `InvalidPositionAccrualTimestampError` | A local position accrual is requested for a timestamp before the position's last accrual (carries `timestamp` and `lastAccrual`). |
| `InvalidPositionLossFactorError` | A local accrual sees a market loss factor below the position's, meaning the market and position were fetched at inconsistent blocks. |
| `InvalidPositionAccrualStateError` | Local accrual inputs violate Midnight accounting invariants, such as a pending fee exceeding credit. |

All of these are importable from `@morpho-org/morpho-sdk/errors`; `InvalidMarketParameterError`, `ChainIdMismatchError`, `InvalidTypedDataSignatureError`, `InvalidEcrecoverSignatureVError`, and `PayloadDecodeError` come from the toolkit package directly, while the Morpho SDK re-exports them as `InvalidMidnightMarketParameterError`, `MidnightChainIdMismatchError`, `InvalidMidnightTypedDataSignatureError`, `InvalidMidnightEcrecoverSignatureVError`, and `MidnightPayloadDecodeError` - and note the Morpho SDK's root export ships its own, distinct `ChainIdMismatchError` for client validation, so don't conflate the two classes.

`MidnightApiError` and `InvalidMidnightApiResponseError` are also re-exported from `@morpho-org/morpho-sdk/midnight-api` alongside the client. The fetch helpers can additionally throw `UnsupportedChainIdError` / `UnknownAddressError` from `@morpho-org/morpho-ts` when the client's chain has no Midnight registry entry.

## [Resources](#resources)

- **Repository:** [morpho-org/sdks · packages/midnight-sdk](https://github.com/morpho-org/sdks/tree/main/packages/midnight-sdk)
- **Protocol docs:** [Get started with Midnight](https://docs.morpho.org/developers/midnight/get-started/) · [Tick structure](https://docs.morpho.org/developers/midnight/concepts/tick-structure/) · [Mempool & router](https://docs.morpho.org/developers/midnight/concepts/mempool-router/)
- **Tutorials:** [Lend at a fixed rate](https://docs.morpho.org/developers/midnight/tutorials/lend-at-a-fixed-rate/) · [Borrow at a fixed rate](https://docs.morpho.org/developers/midnight/tutorials/borrow-at-a-fixed-rate/) · [Redeem lend at maturity](https://docs.morpho.org/developers/midnight/tutorials/redeem-lend-at-maturity/) · [Exit borrow at maturity](https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-by-repaying-in-full-at-maturity/) · [Exit lend early](https://docs.morpho.org/developers/midnight/tutorials/exit-lend-early/) · [Exit borrow early](https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-early/)
- **API reference:** [Midnight API](https://docs.morpho.org/api/midnight/books/list-books/)
- **Contributing:** [`CONTRIBUTING.md`](https://github.com/morpho-org/sdks/blob/main/CONTRIBUTING.md)
- **Security:** [`SECURITY.md`](https://github.com/morpho-org/sdks/blob/main/SECURITY.md)

[Variable Rate Market - Blue

Previous Page

](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/)[Morpho Contracts

Next Page

](https://docs.morpho.org/developers/contracts/)