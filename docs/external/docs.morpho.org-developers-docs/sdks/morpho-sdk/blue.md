# Variable Rate Market - Blue

> Source: https://docs.morpho.org/developers/sdks/morpho-sdk/blue

---

# Variable Rate Market - Blue

## [Introduction](#introduction)

**Variable Rate - Blue Market** (Morpho Blue) is Morpho's shared, variable-rate lending market: lenders supply the loan asset, borrowers post collateral and borrow against it, and rates float with utilization.

The [**Morpho SDK**](https://docs.morpho.org/developers/sdks/morpho-sdk/) builds every market transaction - supply, supply collateral, borrow, repay, withdraw, Blue-to-Blue refinance, their atomic combinations, and shared-liquidity reallocations - through the same [`getRequirements` / `buildTx` flow](https://docs.morpho.org/developers/sdks/morpho-sdk/#the-getrequirements-flow) as every other Morpho surface, via `client.morpho.blue(marketParams, chainId)`.

## [Setup](#setup)

Build the extended client once, as shown in the Morpho SDK [Setup](https://docs.morpho.org/developers/sdks/morpho-sdk/#setup), then construct the market entity below. Every flow on this page reuses `client`, the `market` entity, and `userAddress` - the client's connected account, per the [Builder = signer](https://docs.morpho.org/developers/sdks/morpho-sdk/#builder--signer) invariant. Dispatch requirements with the loop from [The `getRequirements` flow](https://docs.morpho.org/developers/sdks/morpho-sdk/#the-getrequirements-flow), whose `publicClient` also serves the block reads below.

```
import { type Address, parseUnits } from "viem";
import { mainnet } from "viem/chains";
import { MarketParams } from "@morpho-org/morpho-sdk/entities";

// `client` is the extended wallet client from the Morpho SDK Setup;
// `userAddress` is its connected account.
const userAddress = USER_ADDRESS;

// Every Blue write takes a required execution deadline (Unix seconds).
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3_600);
```

## [Build a market entity & fetch data](#build-a-market-entity--fetch-data)

```
// Construct a Blue Market entity from its `MarketParams`.
// The unique market id is derivable from these five fields.
const market = client.morpho.blue(
  new MarketParams({
    loanToken: "0xLoanToken00000000000000000000000000000000",
    collateralToken: "0xCollateralToken00000000000000000000000000",
    oracle: "0xOracle0000000000000000000000000000000000",
    irm: "0xIrm00000000000000000000000000000000000000",
    lltv: 860000000000000000n, // 86%
  }),
  mainnet.id,
);

// On-chain reads with accrued interest:
const marketData = await market.getMarketData();
const positionData = await market.getPositionData(userAddress);
//   positionData: AccrualPosition with health metrics
//     { borrowAssets, collateral, supplyShares, borrowShares,
//       maxBorrowAssets, ltv, isHealthy, market, ... }
```

## [Supply (loan asset)](#supply-loan-asset)

```
// Lend the loan asset to the market. Routed through a direct BlueBundlesV1
// call; Blue write calls expose no share-price bound or `slippageTolerance`.
//
// `getRequirements()` returns the ERC-20 approval (or Permit / Permit2 signature)
// for the loan token to BlueBundlesV1 - no Morpho authorization is needed.
const supply = market.supply({
  assets: parseUnits("1000", 6), // 1,000 USDC, for example
  userAddress,
  deadline, // Unix seconds; required on every Blue write
  // nativeAmount: parseUnits("1", 18), // when the loan token is wNative
});

const supplyLoanReqs = await supply.getRequirements();
const supplyLoanTx = supply.buildTx(/* [requirementSignature] */);
```

Supplying the loan asset credits your supply position on the market (tracked as `supplyShares` on `AccrualPosition`). Native-token funding is supported when the loan token is the chain's wNative - BlueBundlesV1 wraps the native `nativeAmount` atomically, and it must equal `assets`. Blue write calls accept no `slippageTolerance`; the WAD-scaled convention documented on [vault deposits](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/#deposit) only applies to vault operations.

## [Supply collateral](#supply-collateral)

```
// Routed through a direct BlueBundlesV1 call.
// `getRequirements()` returns the ERC-20 approval (or Permit / Permit2 signature)
// for the collateral token to BlueBundlesV1.
const supplyCollateral = market.supplyCollateral({
  collateralAssets: parseUnits("1", 18),
  userAddress,
  deadline,
  // nativeAmount: parseUnits("1", 18) // when collateral is wNative
});

const supplyReqs = await supplyCollateral.getRequirements();
const supplyTx = supplyCollateral.buildTx(/* [requirementSignature] */);
```

## [Borrow](#borrow)

```
// Routed through a direct BlueBundlesV1 call. Requires BlueBundlesV1 to be
// authorized on Morpho - `getRequirements()` returns the `setAuthorization`
// transaction (or a signable authorization) if it has not been done yet.
//
// Always pass a **fresh** `positionData` - stale data may cause unexpected
// health-check failures.
const borrow = market.borrow({
  borrowAssets: parseUnits("500", 6), // 500 USDC, for example
  userAddress,
  positionData,
  deadline,
});

const borrowReqs = await borrow.getRequirements();
const borrowTx = borrow.buildTx();
```

The SDK validates an LLTV buffer against your `positionData` before building, so you cannot accidentally build a transaction that lands on the wrong side of the liquidation threshold the moment it includes. The buffer is hardcoded at `DEFAULT_LLTV_BUFFER` = `5000000000000000n` (WAD-scaled, i.e. 0.5% below the market's LLTV) and is not user-configurable; a borrow beyond it throws `BorrowExceedsSafeLtvError`. `getRequirements()` returns `setAuthorization(blueBundlesV1, true)` if it has not been done yet for the user.

## [Supply collateral & borrow (atomic)](#supply-collateral--borrow-atomic)

```
// Atomic supply-then-borrow in a single BlueBundlesV1 call. Validates the
// hardcoded 0.5% LLTV buffer so a fresh position is not instantly liquidatable.
//
// `getRequirements()` returns IN PARALLEL:
//   - ERC-20 approval / Permit / Permit2 for the collateral token to BlueBundlesV1
//   - `morpho.setAuthorization(blueBundlesV1, true)` if not yet authorized
const supplyCollateralBorrow = market.supplyCollateralBorrow({
  collateralAssets: parseUnits("1", 18),
  borrowAssets: parseUnits("500", 6),
  userAddress,
  positionData,
  deadline,
});

const supplyBorrowReqs = await supplyCollateralBorrow.getRequirements();
const supplyBorrowTx = supplyCollateralBorrow.buildTx(/* [requirementSignature] */);
```

## [Repay](#repay)

Two modes - exactly one of `repayAssets` or `repayShares`:

- **`repayAssets`** - partial repay by exact ERC-20 asset amount. When the loan token is the chain's wNative, the repayment can instead be funded entirely in native token via `nativeAmount`, which must cover the full derived repayment cap; native and ERC-20 funding are exclusive, not additive.
- **`repayShares`** - repay by exact share count - `maxUint256` requests the saturated full close, immune to interest accrued between quote and inclusion (recommended for "close position" flows).

```
// Two modes - exactly one of `repayAssets` / `repayShares`:
//   - `repayAssets`: partial repay by exact asset amount.
//   - `repayShares`: full repay by exact share count - `maxUint256` requests
//                    the saturated full close, immune to interest accrued
//                    between quote and inclusion (recommended for "close position").
//
// Repay does NOT require Morpho authorization - only an ERC-20 approval (or
// permit) on the loan token to BlueBundlesV1.

import { maxUint256 } from "viem";

// Partial repay by assets
const partialRepay = market.repay({
  repayAssets: parseUnits("100", 6),
  userAddress,
  positionData,
  deadline,
});
const partialRepayTx = partialRepay.buildTx(/* [requirementSignature] */);

// Full repay by shares (saturated)
const fullRepay = market.repay({
  repayShares: maxUint256,
  userAddress,
  positionData,
  deadline,
});

const repayReqs = await fullRepay.getRequirements();
const fullRepayTx = fullRepay.buildTx(/* [requirementSignature] */);
```

`repay` does **not** require Morpho authorization - only an ERC-20 approval (or permit) on the loan token to BlueBundlesV1. Share-mode deadlines cannot exceed the SDK's two-hour funding quote horizon.

## [Withdraw (loan asset)](#withdraw-loan-asset)

Two modes - exactly one of `assets` or `shares`:

- **`assets`** - withdraw an exact loan-asset amount.
- **`shares`** - burn an exact supply-share count, immune to interest accrued between quote and inclusion (recommended for "close position" flows).

```
// Withdraw your supplied loan assets. Routed through a direct BlueBundlesV1
// call; Blue write calls expose no share-price bound or `slippageTolerance`.
//
// Requires BlueBundlesV1 to be authorized on Morpho - `getRequirements()`
// returns the `setAuthorization` transaction (or, with `supportSignature: true`,
// a signable authorization requirement folded into the call) if it is missing.
//
// Always pass a **fresh** `positionData` - stale data may cause unexpected
// supply-share calculations.

// Partial withdraw by assets
const withdrawSupply = market.withdraw({
  assets: parseUnits("500", 6),
  userAddress,
  positionData,
  deadline,
});

const withdrawSupplyReqs = await withdrawSupply.getRequirements();
const withdrawSupplyTx = withdrawSupply.buildTx();

// Full close by shares
const closeSupply = market.withdraw({
  shares: positionData.supplyShares,
  userAddress,
  positionData,
  deadline,
});
const closeSupplyTx = closeSupply.buildTx();
```

Like `borrow`, loan-asset `withdraw` accepts an optional `reallocations` array to pull shared liquidity into the market before withdrawing - see [Shared liquidity (reallocations)](#shared-liquidity-reallocations). BlueBundlesV1 pays the withdrawn assets to the transaction sender.

## [Withdraw collateral](#withdraw-collateral)

```
// Routed through a direct BlueBundlesV1 call - it is the collateral-only form
// of `repayWithdrawCollateral`, so it requires BlueBundlesV1 to be authorized
// on Morpho: `getRequirements()` returns the `setAuthorization` transaction
// (or a signable authorization) if it is missing.
// The SDK validates the resulting position health using the LLTV buffer.
const withdrawCollateral = market.withdrawCollateral({
  collateralAssets: parseUnits("0.25", 18),
  userAddress,
  positionData,
  deadline,
});
const withdrawCollateralSignatures = [];
for (const req of await withdrawCollateral.getRequirements()) {
  if ("sign" in req) {
    withdrawCollateralSignatures.push(await req.sign(client, userAddress));
  } else {
    await client.sendTransaction(req); // morpho.setAuthorization(blueBundlesV1, true)
  }
}
const withdrawCollateralTx = withdrawCollateral.buildTx(withdrawCollateralSignatures);
```

Routed through BlueBundlesV1, so `withdrawCollateral` now requires `morpho.setAuthorization(blueBundlesV1, true)` like every other collateral-withdrawing flow. The SDK validates position health after the withdrawal against the LLTV buffer.

## [Repay & withdraw collateral (atomic)](#repay--withdraw-collateral-atomic)

```
// Atomic repay → withdraw collateral via BlueBundlesV1.
// Order is critical: repay FIRST, then withdraw.
//
// `getRequirements()` returns IN PARALLEL:
//   - ERC-20 approval / Permit / Permit2 for the loan token (for repay)
//   - `morpho.setAuthorization(blueBundlesV1, true)` if not yet authorized (for withdraw)
//
// The SDK simulates the repay before validating that the resulting position
// can sustain the requested collateral withdrawal.
const repayWithdrawCollateral = market.repayWithdrawCollateral({
  repayAssets: parseUnits("100", 6), // or { repayShares: ... }
  collateralAssets: parseUnits("0.25", 18),
  userAddress,
  positionData,
  deadline,
});

const repayWithdrawReqs = await repayWithdrawCollateral.getRequirements();
const repayWithdrawTx = repayWithdrawCollateral.buildTx(/* [requirementSignature] */);
```

The order is critical and is encoded for you: **repay first, then withdraw**. The SDK simulates the repay before validating that the resulting position can sustain the requested collateral withdrawal.

## [Refinance to another Morpho Blue market](#refinance-to-another-morpho-blue-market)

`refinance` atomically migrates the caller's full borrower position from a source Morpho Blue market to a destination Morpho Blue market that uses the same `loanToken` and `collateralToken`.

The destination market may differ by oracle, IRM, or LLTV. The SDK validates both markets and builds one direct BlueBundlesV1 call that migrates the entire `msg.sender` position - partial and collateral-only migration are not supported, and `userAddress` must be the account that sends the transaction. `getRequirements()` only returns the Morpho authorization for BlueBundlesV1 when the user has not authorized it yet.

```
const sourceMarketParams = new MarketParams({
  loanToken: "0xLoanToken00000000000000000000000000000000",
  collateralToken: "0xCollateralToken00000000000000000000000000",
  oracle: "0xSourceOracle0000000000000000000000000000",
  irm: "0xIrm00000000000000000000000000000000000000",
  lltv: 860000000000000000n,
});

const targetMarketParams = new MarketParams({
  loanToken: "0xLoanToken00000000000000000000000000000000",
  collateralToken: "0xCollateralToken00000000000000000000000000",
  oracle: "0xTargetOracle0000000000000000000000000000",
  irm: "0xIrm00000000000000000000000000000000000000",
  lltv: 915000000000000000n,
});

const sourceMarket = client.morpho.blue(sourceMarketParams, mainnet.id);
const targetMarket = client.morpho.blue(targetMarketParams, mainnet.id);

const sourcePosition = await sourceMarket.getPositionData(userAddress);
const targetPosition = await targetMarket.getPositionData(userAddress);

const refinance = sourceMarket.refinance({
  userAddress,
  positionData: sourcePosition,
  destination: {
    marketParams: targetMarketParams,
    positionData: targetPosition,
  },
  deadline,
});

const refinanceRequirements = await refinance.getRequirements();

// Only the Morpho authorization can come back here. Dispatch it like any other
// requirement: a transaction to send, or - with `supportSignature: true` - a
// signable requirement whose signature is folded into the bundle.
const refinanceSignatures: RequirementSignature[] = [];

for (const requirement of refinanceRequirements) {
  if (isRequirementSignature(requirement)) {
    refinanceSignatures.push(await requirement.sign(client, userAddress));
  } else {
    const hash = await client.sendTransaction(requirement);
    await publicClient.waitForTransactionReceipt({ hash });
  }
}

const refinanceTx = refinance.buildTx(refinanceSignatures);
await client.sendTransaction(refinanceTx);
```

`refinance` always migrates the complete position: the source market's live debt and collateral are read at execution, referral fees and Vault V2 reallocation penalties increase the destination debt, and the SDK validates the complete destination position against the LLTV buffer. `refinance` requires Morpho authorization for BlueBundlesV1. It does not need ERC-20 approvals because the migrated collateral and debt move through BlueBundlesV1, not from the user wallet.

## [Shared liquidity (reallocations)](#shared-liquidity-reallocations)

When a borrowed market needs more liquidity, use the Vault V2 Public Allocator to source eligible liquidity from Vault V2. Follow the [Vault V2 Public Allocator guide](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/) for discovery, planning, and transaction examples.

Use `getVaultV2BlueReallocationData` to fetch the snapshot and `getVaultV2BlueReallocations` to compute plans containing the vault, source market adapter or idle source, target adapter, asset amount, and WAD-scaled penalty.

[Vault V2

Previous Page

](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/)[Fixed Rate Market - Midnight

Next Page

](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/)