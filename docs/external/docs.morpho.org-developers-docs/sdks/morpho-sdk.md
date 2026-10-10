# Morpho SDK

> Source: https://docs.morpho.org/developers/sdks/morpho-sdk

---

# Morpho SDK

## [Introduction](#introduction)

The [**Morpho SDK**](https://github.com/morpho-org/sdks/tree/main/packages/morpho-sdk) (`@morpho-org/morpho-sdk`) is the **default and recommended SDK** for building applications on top of Morpho.

It is the abstraction layer that simplifies the Morpho protocol: it produces ready-to-send `viem` transactions for **[VaultV2](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/)** and **[Variable Rate - Blue Market](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/)** (Morpho Blue) on every EVM-compatible chain Morpho is deployed on - plus **[Fixed Rate - Midnight Market](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/)** through the same flow - while taking care of the Morpho Bundles routing (BlueBundlesV1, VaultBundlesV1, VaultExitBundlesV1), ERC-20 approvals, Permit / Permit2 signatures, Morpho authorizations, native-token wrapping, vault share-price protection, Blue-to-Blue refinance, and Vault V2 shared-liquidity reallocations for you.

The SDK also supports **[refinance](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/#refinance-to-another-morpho-blue-market)**: atomically moving a borrower's collateral and debt from one Morpho Blue market to another market that shares the same loan token and collateral token, optionally using shared liquidity through the Vault V2 Blue Public Allocator.

For shared-liquidity implementation, use the [Vault V2 Public Allocator guide](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/).

If you are integrating Morpho into a wallet, dApp, partner app, agent, or backend service, this is the SDK you want.

Source: [morpho-org/sdks · packages/morpho-sdk](https://github.com/morpho-org/sdks/tree/main/packages/morpho-sdk) · Package: [`@morpho-org/morpho-sdk` on npm](https://www.npmjs.com/package/@morpho-org/morpho-sdk)

## [Choose your product](#choose-your-product)

Each Morpho product surface has its own subpage. Find the product you are shipping and go straight there - every subpage reuses the same client [Setup](#setup) and [`getRequirements` / `buildTx` flow](#the-getrequirements-flow) documented on this page, so adding a second product later is only a new entity factory call.

| You are building | Morpho product | Go to |
| --- | --- | --- |
| An earn product: users deposit an asset and accrue yield | VaultV2 (curated vaults) | [Vault V2](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/) |
| Variable-rate borrowing against collateral, with no fixed term | Morpho Blue markets | [Variable Rate - Blue Market](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/) |
| Fixed-rate, fixed-term lending or borrowing on an onchain orderbook | Midnight | [Fixed Rate - Midnight Market](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/) |

## [Actions overview](#actions-overview)

Every action the SDK builds, per entity - with the route each transaction takes and why:

| Entity | Action | Route | Why |
| --- | --- | --- | --- |
| **VaultV2** | `deposit` | a direct VaultBundlesV1 call | Enforces `maxSharePrice` against ERC-4626 share-price inflation and supports native-token funding. |
|  | `withdraw` | a direct VaultBundlesV1 call | Withdraws an exact asset amount, burning the sender's shares under an exact share allowance. |
|  | `redeem` | a direct VaultBundlesV1 call | Redeems an exact share amount under an exact share allowance. |
|  | `inKindRedeem` | a direct VaultExitBundlesV1 call | Burns vault shares, returns idle assets first, and transfers ordered Morpho Blue supply positions for the illiquid remainder. |
|  | `forceWithdraw` | a direct VaultExitBundlesV1 call | Force-withdraws into the underlying asset through the vault's sole adapter, bounding the realized exit share price. |
|  | `forceRedeem` | a vault multicall | Runs caller-supplied `forceDeallocate` calls before one `redeem` in a single vault transaction. |
| **VaultV1** | `deposit` | a direct VaultBundlesV1 call | Enforces `maxSharePrice` against ERC-4626 share-price inflation and supports native-token funding. |
|  | `withdraw` | a direct VaultBundlesV1 call | Withdraws an exact asset amount, burning the sender's shares under an exact share allowance. |
|  | `redeem` | a direct VaultBundlesV1 call | Redeems an exact share amount under an exact share allowance. |
|  | `inKindRedeem` | a direct VaultExitBundlesV1 call | Burns MetaMorpho shares and transfers ordered Morpho Blue supply positions to the user when an asset withdrawal is illiquid. |
|  | `migrateToV2` | a direct VaultBundlesV1 call | Atomically redeems V1 shares and deposits the assets into V2 with share-price bounds on both legs. |
| **Blue Market** | `supplyCollateral` | a direct BlueBundlesV1 call | Pulls collateral into Morpho and supports native funding when collateral is wNative. |
|  | `supply` | a direct BlueBundlesV1 call | Supplies the loan asset, with optional native funding. |
|  | `withdraw` | a direct BlueBundlesV1 call | Withdraws supplied assets with Morpho authorization and optional shared-liquidity reallocations. |
|  | `borrow` | a direct BlueBundlesV1 call | Borrows with LLTV-buffer validation, Morpho authorization, and optional reallocations. |
|  | `repay` | a direct BlueBundlesV1 call | Repays by `repayAssets` or `repayShares` (with a saturated full-close mode), plus optional native funding. |
|  | `withdrawCollateral` | a direct BlueBundlesV1 call | Withdraws collateral with Morpho authorization after validating the resulting position health. |
|  | `repayWithdrawCollateral` | a direct BlueBundlesV1 call | Repays before withdrawing collateral in one call, then validates the combined post-state. |
|  | `supplyCollateralBorrow` | a direct BlueBundlesV1 call | Supplies collateral then borrows atomically with LLTV-buffer validation and optional reallocations. |
|  | `refinance` | a direct BlueBundlesV1 call | Migrates the full `msg.sender` collateral and debt position between compatible Blue markets atomically, with optional reallocations. |
| **Midnight** | `takeLend` | MidnightBundles bundle | Takes borrow-side offers for a lender with a deadline, token approval, and MidnightBundles authorization. |
|  | `takeBorrow` | MidnightBundles bundle | Takes lend-side offers for a borrower with a deadline and MidnightBundles authorization. |
|  | `supplyCollateralTakeBorrow` | MidnightBundles bundle | Supplies collateral and takes lend-side offers atomically with a deadline. |
|  | `supplyCollateral` | Direct Midnight call | Supplies configured collateral directly to the selected Midnight market. |
|  | `makeLend` | Midnight mempool submission | Validates and submits lend-side maker offers after reserve and ratifier requirements are satisfied. |
|  | `makeBorrow` | Midnight mempool submission | Validates and submits borrow-side maker offers after ratifier requirements are satisfied. |
|  | `supplyCollateralMakeBorrow` | Midnight mempool submission | Supplies collateral as a requirement, then submits validated borrow-side maker offers. |
|  | `redeem` | Direct Midnight call | Redeems accrued fixed-rate credit directly to the selected receiver. |
|  | `repayWithdrawCollateral` | MidnightBundles bundle | Repays debt, withdraws collateral, or does both through one deadline-bound bundle. |
|  | `cancelOffer` | Direct Midnight call | Fully consumes a maker offer group directly on Midnight. |

This page documents the shared client setup and the `getRequirements` / `buildTx` flow; the [VaultV2](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/), [Blue Market](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/), and fixed-rate [Midnight](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/) surfaces are each documented on their own subpage. VaultV1 (MetaMorpho) mirrors the VaultV2 vault surface and adds a V1→V2 migration.

## [Installation](#installation)

```
pnpm add @morpho-org/morpho-sdk@6.0.0 viem@^2.0.0
# or
yarn add @morpho-org/morpho-sdk@6.0.0 viem@^2.0.0
# or
npm install @morpho-org/morpho-sdk@6.0.0 viem@^2.0.0
```

`viem` is a peer dependency (`^2.0.0`) and must be installed alongside the SDK.

`@morpho-org/morpho-sdk@6.0.0` is the first release that routes every Blue and Vault write through Morpho Bundles. It is currently published under the `next` npm dist-tag, so pin the version explicitly (`@morpho-org/morpho-sdk@6.0.0`) or install `@morpho-org/morpho-sdk@next`. Releases up to 5.x route Blue writes and vault deposits through the deprecated Bundler3 (vault withdrawals and redemptions were direct vault calls, and in-kind redemptions already used VaultExitBundlesV1).

## [Setup](#setup)

```
import "dotenv/config";
import { type Address, createWalletClient, http } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { mainnet } from "viem/chains";
import { morphoViemExtension } from "@morpho-org/morpho-sdk";

// Private-key account: this is the connected account the SDK enforces as the signer.
const account = privateKeyToAccount(process.env.PRIVATE_KEY as Address);

// This is the account the builders must be told about (see the invariant below).
const USER_ADDRESS = account.address;

// Extend a viem wallet client with the Morpho namespace. `client.morpho` exposes
// four stateless entity factories: `vaultV1`, `vaultV2`, `blue`, and `midnight`.
const client = createWalletClient({
  account,
  chain: mainnet,
  transport: http(process.env.RPC_URL),
}).extend(
  morphoViemExtension({
    // Collect EIP-712 permit / permit2 signatures instead of only on-chain ERC-20
    // approvals; defaults to `false` (classic approvals only).
    supportSignature: true,
    // Analytics metadata stamped onto every transaction the namespace builds.
    // `timestamp` is optional; `origin` is required when `metadata` is passed.
    // `origin` is hexadecimal calldata (at most 8 hex chars / 4 bytes, even
    // length, optional 0x prefix), NOT a clear-text name - an invalid origin
    // is dropped with only a console warning.
    metadata: { origin: "0xbeef01", timestamp: true },
    // Allow entity fetchers to use deployless multicall for on-chain reads.
    supportDeployless: true,
  }),
);

// Builder = signer invariant:
// The `userAddress` you pass to any builder MUST equal the account connected to THIS
// extended client, and the SAME client MUST sign and send the resulting transaction.
// Signature requirements enforce it when `sign(client, userAddress)` is called, via
// `validateUserAddress` - throwing `MissingClientPropertyError` when the client has
// no connected account, or `AddressMismatchError` when the connected account does
// not match `userAddress`. Transaction builders do not re-validate at build time.
```

Extend your `viem` client with `morphoViemExtension()` to add the `client.morpho` namespace. That namespace exposes four entity factories:

```
import { MarketParams } from "@morpho-org/morpho-sdk/entities";

// chainId is mandatory (validated against the viem client).
const vaultV2 = client.morpho.vaultV2(
  "0xVaultV2Address0000000000000000000000000000" as Address,
  mainnet.id,
);

// `blue()` derives and validates the market id from these params, so construct a
// `MarketParams` instance - a raw object literal has no id and throws MarketIdMismatchError.
const market = client.morpho.blue(
  new MarketParams({
    loanToken: "0xLoanToken00000000000000000000000000000000" as Address,
    collateralToken: "0xCollateralToken00000000000000000000000000" as Address,
    oracle: "0xOracle0000000000000000000000000000000000" as Address,
    irm: "0xIrm00000000000000000000000000000000000000" as Address,
    lltv: 945000000000000000n, // 94.5%
  }),
  mainnet.id,
);
```

`client.morpho.midnight(chainId)` returns the fixed-rate Midnight market surface bound to the same viem client; see the [Midnight](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/) subpage.

### [Extension options](#extension-options)

Pass these options to `morphoViemExtension(...)`:

| Option | Default | Effect |
| --- | --- | --- |
| `supportSignature` | `false` | Lets the SDK return EIP-712 Permit, Permit2, and Morpho authorization signature requirements instead of relying only on approval and authorization transactions. |
| `supportDeployless` | `undefined` | Lets entity fetchers use deployless multicall reads; when unset, fetchers use their default behavior. |
| `metadata` | `undefined` | Appends analytics metadata to every built transaction. `origin` must be a hexadecimal byte string of at most 8 hex characters (4 bytes), with even length and an optional `0x` prefix; invalid origin text is dropped with a console warning. |

`metadata.origin` is **hexadecimal**, not a clear-text app name. It is appended verbatim to every transaction's calldata as an analytics tag, so it must be a hex string of at most 8 hex characters (4 bytes), with an even number of characters, with or without the `0x` prefix - e.g. `"0xbeef01"`. An invalid origin (such as `"my-app"`) does not throw: the SDK logs a console warning and omits the tag from the calldata.

## [The `getRequirements` flow](#the-getrequirements-flow)

Every action that touches a user's tokens or positions returns the same shape:

- `buildTx(signatures?)` - returns the final, deep-frozen `viem` `Transaction` (`{ to, value, data, action }`). Collected requirement signatures are passed as an array.
- `getRequirements()` - returns the on-chain pre-requisites that must be satisfied first.

A requirement is one of:

- An **ERC-20 approval** transaction the user must send first (approving the bundles contract - or Morpho - to pull tokens).
- A **Permit / Permit2** signature request - a signable `Requirement`: call `requirement.sign(client, userAddress)` to collect the EIP-712 `RequirementSignature`, then pass it back into `buildTx([signature])` as an array. Enabled with `morphoViemExtension({ supportSignature: true })`.
- A **Morpho authorization** - `morpho.setAuthorization(blueBundlesV1, true)`. Required once per user for `borrow`, `supplyCollateralBorrow`, `withdrawCollateral`, `repayWithdrawCollateral`, loan-asset `withdraw`, and `refinance`. The SDK only returns it if it is missing. With `supportSignature: true` it comes back as a signable `Requirement` instead of a transaction, and the signed authorization is folded into the BlueBundlesV1 call - no standalone transaction needed.

The canonical end-to-end flow - the same dispatch loop works for **every** vault, market, and Midnight *taker* action. Midnight *maker* flows are the exception: they submit signed offers to the Midnight mempool instead of returning a `viem` `Transaction` you send yourself - see the [Midnight](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/#maker-flows) subpage.

```
import { parseUnits, publicActions } from "viem";
import {
  isRequirementSignature,
  type RequirementSignature,
} from "@morpho-org/morpho-sdk";

// `client` is the extended wallet client from Setup; viem's `publicActions`
// adds `waitForTransactionReceipt` / `getBlock` for the requirement flow.
const publicClient = client.extend(publicActions);

const vaultData = await vaultV2.getData();

const deposit = vaultV2.deposit({
  amount: parseUnits("1", 18), // the vault asset has 18 decimals here
  userAddress: USER_ADDRESS,
  vaultData,
});

// 1. Resolve the on-chain pre-requisites.
const requirements = await deposit.getRequirements();

// 2. Dispatch every requirement: sign the signable ones (off-chain), send the
//    rest as transactions (on-chain) and wait for inclusion.
const signatures: RequirementSignature[] = [];

for (const requirement of requirements) {
  if (isRequirementSignature(requirement)) {
    // Permit / Permit2 / Morpho authorization signature request. `sign` runs
    // the EIP-712 signing flow and enforces builder = signer: it throws
    // `AddressMismatchError` unless the client's connected account equals
    // `USER_ADDRESS` (or `MissingClientPropertyError` when none is connected).
    signatures.push(await requirement.sign(client, USER_ADDRESS));
  } else {
    // ERC-20 approval or Morpho `setAuthorization` transaction. It must be
    // mined before the final transaction can execute.
    const hash = await client.sendTransaction(requirement);
    await publicClient.waitForTransactionReceipt({ hash });
  }
}

// 3. Build the final transaction, passing the collected signatures.
const tx = deposit.buildTx(signatures);
// `tx` is a deep-frozen `{ to, value, data, action }`.

// 4. Send it with the SAME client that built it.
await client.sendTransaction(tx);
```

`isRequirementSignature` splits the off-chain signature requests from the on-chain transactions. When you need finer-grained dispatch - for example different wallet-prompt copy per requirement - the SDK also exports `isRequirementApproval` and `isRequirementBlueAuthorization`:

```
import {
  isRequirementApproval,
  isRequirementBlueAuthorization,
  isRequirementSignature,
} from "@morpho-org/morpho-sdk";

for (const requirement of requirements) {
  if (isRequirementApproval(requirement)) {
    // ERC-20 approval transaction - `requirement.action.args` is { spender, amount }.
  } else if (isRequirementBlueAuthorization(requirement)) {
    // `morpho.setAuthorization(blueBundlesV1, true)` transaction.
  } else if (isRequirementSignature(requirement)) {
    // Signable requirement - `requirement.action.type` is "permit", "permit2",
    // or "authorization".
  }
}
```

## [Builder = signer](#builder--signer)

> **`userAddress` MUST equal the connected account on the `viem` client used to build the transaction, and the SAME client MUST sign and send it.**

Transaction builders do **not** re-validate this at build time - you must keep `userAddress` aligned with the signing account yourself. The invariant is enforced when a signature requirement is signed: `sign(client, userAddress)` runs `validateUserAddress`, which throws `MissingClientPropertyError` (no connected account) or `AddressMismatchError` (account mismatch).

This invariant exists because some bundles - particularly `repayWithdrawCollateral` - mix **explicit** `onBehalf = userAddress` (repay) with **implicit** `msg.sender` (transfer-from + withdraw). Splitting the builder and the signer would atomically repay one user's debt while withdrawing another user's collateral.

This is a build-time guard against accidental mixed-account calls for honest integrators, **not** a defense against a malicious builder. The signer remains responsible for reviewing what they sign. See [`ARCHITECTURE.md`](https://github.com/morpho-org/sdks/blob/%40morpho-org%2Fmorpho-sdk-v6.0.0/packages/morpho-sdk/ARCHITECTURE.md) for the deeper Morpho Bundles context.

## [Fetching state](#fetching-state)

Each entity exposes thin wrappers over the canonical viem fetchers (re-exported from [`@morpho-org/morpho-sdk/fetch`](https://github.com/morpho-org/sdks/tree/main/packages/morpho-sdk)), so you always pass **fresh, accrued** data into the builders:

| Entity | Method | Returns |
| --- | --- | --- |
| `vaultV2` | `vault.getData(parameters?)` | `AccrualVaultV2` - total assets, total supply, asset address, share/asset conversion, curated allocations, adapters used by `forceWithdraw` / `forceRedeem`. |
| `blue` | `market.getMarketData(parameters?)` | `Market` - total supply / borrow assets and shares, utilization, liquidity, oracle price, rate-at-target. |
| `blue` | `market.getPositionData(user, parameters?)` | `AccrualPosition` - `borrowAssets`, `collateral`, `supplyShares`, `borrowShares`, `maxBorrowAssets`, `ltv`, `isHealthy`, plus the parent `Market`. |

These data objects are the canonical entity classes re-exported from [`@morpho-org/morpho-sdk/entities`](https://github.com/morpho-org/sdks/tree/main/packages/morpho-sdk). Refer to that module for the full type surface, accrual math, and helpers.

## [Errors and invariants](#errors-and-invariants)

The SDK uses dedicated error classes (no generic `Error`s) so you can branch on failure modes deterministically. A few highlights:

| Error | When it triggers |
| --- | --- |
| `NegativeInputError` | A scalar input that must be non-negative is negative; exposes the invalid `field` and `value`. |
| `NonPositiveInputError` | A scalar input that must be positive is zero or negative; exposes the invalid `field` and `value`. |
| `InputExceedsMaxError` | An input exceeds a protocol upper bound such as `uint128` reallocation assets or a WAD-scaled `uint64` penalty; exposes `field`, `value`, and `max`. |
| `EmptyMarketParamsListError` | An in-kind redemption omits the ordered Morpho Blue market parameters needed to cover the exit. |
| `ExpiredDeadlineError` | An operation deadline is not later than the timestamp used when the action or its requirements are prepared. |
| `VaultV2SingleAdapterRequiredError` | A Vault V2 exit (in-kind redemption or `forceWithdraw`) snapshot contains anything other than one adapter. |
| `AdapterNotPartOfVaultError` | A requested Vault V2 exit adapter is not the vault snapshot's sole configured adapter. |
| `VaultV2UnsupportedExitAdapterError` | A Vault V2 exit adapter is not a supported `MorphoMarketV1AdapterV2`. |
| `VaultV2UnsupportedLiquidityAdapterError` | A Vault V2 `forceWithdraw` vault's liquidity adapter is not supported by VaultExitBundlesV1. |
| `VaultV2UndecodableLiquidityDataError` | A Vault V2 `forceWithdraw` vault's liquidity-adapter data cannot be decoded. |
| `VaultV2ForceWithdrawCoverageError` | The computed force-withdraw deallocation plan cannot cover the requested `exitAssets`; exposes `required`, `covered`, and `maxExitAssets`. |
| `VaultV2ForceWithdrawZeroWithdrawalError` | A Vault V2 `forceWithdraw` plan would withdraw zero assets after the penalty. |
| `VaultV2ForceWithdrawZeroSharePriceError` | A Vault V2 `forceWithdraw` computes a zero exit share price. |
| `VaultV2ForceWithdrawSharePriceBelowFloorError` | The projected Vault V2 `forceWithdraw` exit share price falls below the `minSharePriceE27` floor. |
| `VaultV2ForceWithdrawFeeSharesExceedBurnError` | The projected Vault V2 `forceWithdraw` fee shares exceed the shares the exit would burn. |
| `InKindRedeemZeroDeallocationError` | A Vault V2 exit has no idle assets and its penalty-adjusted amount rounds to zero deallocated assets. |
| `InKindRedeemCoverageError` | The supplied markets, plus any Vault V2 idle assets, cannot cover the requested in-kind redemption amount. |
| `InsufficientBlueBalanceForInKindRedeemError` | Morpho Blue's current loan-token balance cannot fund the flash loan or largest callback required by an in-kind redemption. |
| `VaultMorphoMismatchError` | A Vault V1 in-kind redemption targets a MetaMorpho vault connected to a different Morpho deployment. |
| `VaultIsBlueFeeRecipientError` | A Vault V1 is Morpho Blue's fee recipient, whose accrued protocol fee shares VaultExitBundlesV1 cannot safely account for. |
| `BundlesPermitMismatchError` | A bundles call receives a vault-share or token permit whose kind, spender, amount, deadline, or asset does not match the requirement. |
| `BundlesRequirementSignatureMismatchError` | A bundles requirement signature's field or encoding does not match the fixed bundles call; exposes `field`, `expected`, and `actual`. |
| `Permit2SignatureTransferNonceAlreadyUsedError` | The selected Permit2 signature-transfer nonce is already consumed onchain. |
| `NoUnusedPermit2NonceError` | No unused Permit2 signature-transfer nonce is available for the requirement. |
| `NativeFundingAmountMismatchError` | A native-funded call's `nativeAmount` differs from the gross amount the BlueBundlesV1 entrypoint funds. |
| `ReferralFeeRecipientMissingError` | A positive `referralFeePct` is supplied without `referralFeeRecipient`. |
| `ReferralFeePctExceededError` | A referral fee percentage is outside the contract's `[0, WAD)` range; extends `InputExceedsMaxError`. |
| `MixedBundlesFundingError` | A bundles call supplies both `amount` and `nativeAmount`; the two funding modes are exclusive. |
| `AmountAndSharesExclusiveError` | A vault migration specifies both `assets` and `shares`, or neither. |
| `SameVaultMigrationError` | A vault migration selects the same source and destination vault. |
| `ReallocationLoanTokenMismatchError` | A BlueBundlesV1 reallocation source uses a loan token different from the target market's. |
| `UnsupportedAuthorizationOperatorError` | A Blue authorization targets an operator other than the chain's registered BlueBundlesV1 contract. |
| `ReallocationsRequireBorrowError` | Reallocations are attached to a combined call with no borrow leg. |
| `MaxRepayAssetsBelowRepayAssetsError` | The derived `maxRepayAssets` funding cap cannot cover the requested `repayAssets` plus referral fee. |
| `AmbiguousRequirementSignaturesError` | `buildTx` receives more than one requirement signature of the same accepted kind. |
| `UnexpectedRequirementSignatureError` | `buildTx` receives a requirement signature kind that the operation does not consume. |
| `UnsupportedRequirementSignatureError` | `buildTx` receives a requirement signature with an unsupported action type. |
| `AddressMismatchError` | The connected viem account differs from the address required by a signing flow. |
| `ChainIdMismatchError` | The viem client chain differs from the chain expected by the entity or action. |
| `CryptoUnavailableError` | A flow needs a runtime cryptography API that is unavailable. |
| `MissingClientPropertyError` | The viem client lacks a required property such as `account.address`. |
| `ApprovalAmountLessThanSpendAmountError` | An ERC-20 approval amount is smaller than the amount the action must spend. |
| `UnsupportedErc20ApprovalSpenderError` | A requirement targets a spender outside the chain registry slots the flow supports. |
| `UnsupportedMidnightAuthorizationTargetError` | A Midnight authorization targets neither MidnightBundles nor the chain's Ecrecover or Setter ratifier. |
| `MissingAccrualPositionError` | An action that requires accrued position data receives no position snapshot. |
| `ExcessiveSlippageToleranceError` | A supplied slippage tolerance exceeds `MAX_SLIPPAGE_TOLERANCE` (10%). |
| `EmptyDeallocationsError` | VaultV2 `forceRedeem` receives no deallocations. |
| `DepositAmountMismatchError` | A deposit amount differs from the amount covered by its permit or Permit2 signature. |
| `DepositAssetMismatchError` | A deposit asset differs from the asset covered by its permit or Permit2 signature. |
| `DepositOwnerMismatchError` | A deposit owner differs from the owner covered by its permit or Permit2 signature. |
| `DepositSpenderMismatchError` | A deposit spender differs from the spender covered by its permit or Permit2 signature. |
| `NativeAmountOnNonWNativeVaultError` | A vault deposit uses `nativeAmount` when the vault asset is not the chain's wrapped native token. |
| `ChainWNativeMissingError` | A flow uses `nativeAmount` on a chain with no configured wrapped native token. |
| `VaultAddressMismatchError` | A vault entity address differs from the address in the supplied vault data. |
| `NativeAmountOnNonWNativeAssetError` | An action uses `nativeAmount` when its target asset is not the chain's wrapped native token. |
| `BorrowExceedsSafeLtvError` | A Blue borrow exceeds the LLTV-buffered safe maximum for the position. |
| `MissingMarketPriceError` | A Blue market has no oracle price, so position health cannot be validated. |
| `MarketIdMismatchError` | Supplied market data or parameters resolve to a market id different from the expected id. |
| `AccrualPositionUserMismatchError` | An accrued position belongs to a user other than the account the action targets. |
| `ReallocationWithdrawalOnTargetMarketError` | A reallocation tries to withdraw from the same market it targets. |
| `InvalidVaultV2BlueReallocationShapeError` | A reallocation entry passed to a high-level Blue write is not a valid Vault V2 reallocation. |
| `InvalidReallocationAddressError` | A reallocation has a malformed BluePublicAllocator vault or adapter address. |
| `InvalidReallocationSourceTypeError` | A reallocation source is absent, incomplete, or not a supported BluePublicAllocator source type. |
| `InconsistentReallocationPenaltyError` | Two reallocation entries for one vault carry conflicting penalties. |
| `MutuallyExclusiveRepayAmountsError` | A Blue repay supplies both `repayAssets` and `repayShares` modes. |
| `WithdrawExceedsCollateralError` | A collateral withdrawal exceeds the position's available collateral. |
| `WithdrawMakesPositionUnhealthyError` | A collateral withdrawal would leave the position above the LLTV-buffered safe maximum. |
| `RepayExceedsDebtError` | An assets-mode Blue repay exceeds the borrower's outstanding debt. |
| `InvalidSignatureError` | EIP-712 signature verification does not recover the expected signer. |
| `RepaySharesExceedDebtError` | A shares-mode Blue repay supplies more borrow shares than the borrower owes. |
| `InsufficientSharedLiquidityError` | Computed shared liquidity cannot cover the target market's absolute operation shortfall. |
| `UnknownReallocationMarketError` | Reallocation state does not contain the requested market. |
| `UnknownReallocationVaultError` | Reallocation state does not contain the requested vault. |
| `UnknownReallocationAllocationError` | Reallocation state does not contain the requested vault allocation. |
| `UnknownReallocationPublicAllocatorConfigError` | Reallocation state does not contain the requested vault's PublicAllocator configuration. |
| `UnknownReallocationActiveAdaptersError` | Reallocation state does not contain the requested vault's active adapters. |
| `UnknownReallocationMarketPublicAllocatorConfigError` | Reallocation state does not contain the requested market's PublicAllocator configuration. |
| `UnknownReallocationAdapterError` | Reallocation state does not contain the requested adapter. |
| `ReallocationAllocationUnderflowError` | A simulated reallocation underflows the vault's allocation accounting. |
| `ReallocationAdapterSupplySharesUnderflowError` | A simulated reallocation underflows the source adapter's supply shares. |
| `MidnightAmountExceedsMaxOfferCapError` | A Midnight offer or cancellation amount exceeds the onchain maximum offer-cap value. |
| `EmptyMidnightTakeableOffersError` | A Midnight take flow receives no takeable offers. |
| `MidnightOfferSideMismatchError` | A Midnight offer has the wrong maker side for the selected lend or borrow flow. |
| `MidnightOfferMakerMismatchError` | A prepared maker offer belongs to an account other than the active maker. |
| `MidnightOfferMarketChainMismatchError` | A maker offer targets a chain other than the selected Midnight entity chain. |
| `MidnightOfferMarketAddressMismatchError` | A maker offer targets a Midnight deployment other than the selected chain deployment. |
| `MidnightMarketAddressMismatchError` | Hydrated Midnight market data targets a deployment other than the selected chain deployment. |
| `MidnightOfferMarketLoanTokenMismatchError` | A make-lend offer uses a loan token different from the approved reserve token. |
| `MidnightTakeableOfferMarketMismatchError` | A quoted takeable offer belongs to a market other than the requested market. |
| `UnknownMidnightRatifierError` | A maker offer tree uses neither the chain's Ecrecover ratifier nor its Setter ratifier. |
| `MissingMidnightOfferRootSignatureError` | An Ecrecover maker flow builds its submission before an offer-root signature is attached. |
| `MidnightOfferRootMismatchError` | An attached Midnight offer-root signature references a root different from the prepared tree. |
| `MidnightOfferRootOwnerMismatchError` | An attached Midnight offer-root signature was produced by a different maker. |
| `MidnightOfferRootRatifierMismatchError` | An attached Midnight offer-root signature targets a different ratifier. |
| `MidnightOfferRootOfferCountMismatchError` | An attached Midnight offer-root signature covers a different number of offers. |
| `UnpreparedMidnightOfferRootSignatureError` | A Midnight offer-root signature was not prepared and recorded by the current maker flow. |
| `NoMidnightCreditToRedeemError` | A Midnight redeem flow finds no positive credit units to redeem. |
| `MidnightRedeemExceedsCreditError` | A Midnight redemption requests more units than the accrued position credit. |
| `InsufficientMidnightWithdrawableLiquidityError` | A Midnight redemption exceeds the market's currently withdrawable liquidity. |
| `MutuallyExclusiveWithdrawAmountsError` | A Blue loan-asset withdraw supplies both assets and shares modes. |
| `WithdrawExceedsSupplyError` | An assets-mode Blue loan-asset withdraw exceeds the user's supplied assets. |
| `WithdrawSharesExceedSupplyError` | A shares-mode Blue loan-asset withdraw exceeds the user's supply shares. |
| `ReallocationWithdrawExceedsMarketSupplyError` | A withdraw reallocation is requested for more than the target market's total supplied assets. |
| `VaultAssetMismatchError` | A VaultV1-to-VaultV2 migration uses source and target vaults with different assets. |
| `RefinanceSameMarketError` | A refinance uses the same Blue market as source and destination. |
| `RefinanceTokenMismatchError` | A refinance source and destination do not share both loan and collateral tokens. |

The full list lives in [`src/types/error.ts`](https://github.com/morpho-org/sdks/blob/%40morpho-org%2Fmorpho-sdk-v6.0.0/packages/morpho-sdk/src/types/error.ts).

## [Key invariants](#key-invariants)

- **Builder = signer.** The `viem` client used to build a transaction MUST be the one used to sign and send it.
- **`Transaction` objects are deep-frozen.** They cannot be mutated after `buildTx`.
- **No `any`.** Strict TypeScript across the entire surface, with discriminated unions for every action type.
- **Chain id is mandatory.** Every entity is constructed against a specific chain id, validated against the viem client.
- **Morpho Bundles are the route** for every Blue and Vault write that touches a user's tokens or position: Blue writes call BlueBundlesV1, vault deposits/withdrawals/redemptions call VaultBundlesV1, and in-kind exits and Vault V2 force withdrawals call VaultExitBundlesV1. The exception is VaultV2 `forceRedeem`, a plain vault multicall that needs no Bundle allowance; Midnight actions route through `MidnightBundlesV1` - see the [Actions overview](#actions-overview).
- **Vault deposits are share-price protected.** `maxSharePrice` is computed from fresh on-chain state and your `slippageTolerance`; the LLTV buffer additionally protects Blue borrow, collateral-withdrawal, and refinance legs. Blue write calls accept no share-price bounds or `slippageTolerance` input.
- **Refinance markets must be compatible.** Source and destination markets must be different and must share `loanToken` and `collateralToken`.
- **Refinance migrates the full position.** It always moves the entire `msg.sender` position and validates the complete destination position against the LLTV buffer. Always pass fresh source and destination `positionData`.
- **Refinance is `msg.sender`-only.** There is no on-behalf migration, and no partial or collateral-only mode.

## [Resources](#resources)

- **Repository:** [morpho-org/sdks · packages/morpho-sdk](https://github.com/morpho-org/sdks/tree/main/packages/morpho-sdk)
- **Package:** [`@morpho-org/morpho-sdk` on npm](https://www.npmjs.com/package/@morpho-org/morpho-sdk)
- **Architecture:** [`ARCHITECTURE.md`](https://github.com/morpho-org/sdks/blob/%40morpho-org%2Fmorpho-sdk-v6.0.0/packages/morpho-sdk/ARCHITECTURE.md)
- **v5 → v6 migration guide:** [`MIGRATION-v5-to-v6.md`](https://github.com/morpho-org/sdks/blob/%40morpho-org%2Fmorpho-sdk-v6.0.0/packages/morpho-sdk/MIGRATION-v5-to-v6.md)
- **Examples:** [`examples/example.ts`](https://github.com/morpho-org/sdks/blob/%40morpho-org%2Fmorpho-sdk-v6.0.0/packages/morpho-sdk/examples/example.ts)
- **Contributing:** [`CONTRIBUTING.md`](https://github.com/morpho-org/sdks/blob/main/CONTRIBUTING.md)
- **Security:** [`SECURITY.md`](https://github.com/morpho-org/sdks/blob/main/SECURITY.md)
- **Lower-level primitives:** [`@morpho-org/morpho-sdk/entities`](https://github.com/morpho-org/sdks/tree/main/packages/morpho-sdk) · [`@morpho-org/morpho-sdk/fetch`](https://github.com/morpho-org/sdks/tree/main/packages/morpho-sdk)

[Get Started

Previous Page

](https://docs.morpho.org/developers/sdks/get-started/)[Vault V2

Next Page

](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/)