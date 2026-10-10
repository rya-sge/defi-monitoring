# Vault V2

> Source: https://docs.morpho.org/developers/sdks/morpho-sdk/vault

---

# Vault V2

## [Introduction](#introduction)

**VaultV2** is Morpho's curated vault: depositors supply the vault's asset and receive shares, while the vault allocates the liquidity across markets through adapters.

The [**Morpho SDK**](https://docs.morpho.org/developers/sdks/morpho-sdk/) builds every vault transaction - deposit (with native-token wrapping), withdraw, redeem, and the force-withdraw / force-redeem escape hatches - through the same [`getRequirements` / `buildTx` flow](https://docs.morpho.org/developers/sdks/morpho-sdk/#the-getrequirements-flow) as every other Morpho surface, via `client.morpho.vaultV2(address, chainId)`.

VaultV1 (MetaMorpho) mirrors this vault surface and adds a V1→V2 migration - see the [Actions overview](https://docs.morpho.org/developers/sdks/morpho-sdk/#actions-overview) for its route table.

## [Setup](#setup)

Build the extended client once, as shown in the Morpho SDK [Setup](https://docs.morpho.org/developers/sdks/morpho-sdk/#setup), then construct the vault entity. Every flow below reuses `client`, the `vault` entity, and `userAddress` - the client's connected account, per the [Builder = signer](https://docs.morpho.org/developers/sdks/morpho-sdk/#builder--signer) invariant. Dispatch requirements with the loop from [The `getRequirements` flow](https://docs.morpho.org/developers/sdks/morpho-sdk/#the-getrequirements-flow), whose `publicClient` also serves the block reads and receipt waits below.

```
import { type Address, parseUnits } from "viem";
import { mainnet } from "viem/chains";

// `client` is the extended wallet client from the Morpho SDK Setup;
// `userAddress` is its connected account.
const userAddress = USER_ADDRESS;

// chainId is mandatory (validated against the viem client).
const vault = client.morpho.vaultV2(
  "0xVaultV2Address0000000000000000000000000000" as Address,
  mainnet.id,
);
```

## [Fetch vault state](#fetch-vault-state)

```
// Fetches on-chain vault state with accrued interest.
// Returns an `AccrualVaultV2` with: address, asset, totalAssets, totalSupply,
// share/asset conversion helpers (`toShares`, `toAssets`), curated allocations,
// and adapters used by `forceWithdraw` / `forceRedeem`.
const vaultData = await vault.getData();
```

## [Deposit](#deposit)

```
// Routed through a direct VaultBundlesV1 call - enforces `maxSharePrice`
// (ERC-4626 inflation-attack guard) and supports native-token wrapping.
const deposit = vault.deposit({
  amount: parseUnits("1", 18),
  userAddress,
  vaultData,
  // slippageTolerance is a WAD-scaled bigint: 1e18 = 100%. It defaults to
  // DEFAULT_SLIPPAGE_TOLERANCE = 300000000000000n (0.03%) and is capped at 10%.
  // e.g. 0.1%: parseUnits("0.001", 18) = 1000000000000000n
  // slippageTolerance: parseUnits("0.001", 18),
});

const requirements = await deposit.getRequirements();
// e.g. [erc20Approval tx for VaultBundlesV1] OR [Permit / Permit2 signature requirement]

const depositTx = deposit.buildTx(/* [requirementSignature] */);
```

Routed through a direct VaultBundlesV1 call - the SDK enforces a `maxSharePrice` derived from `accrualVault` and `slippageTolerance`, preventing ERC-4626 inflation-attack share-price drift.

`slippageTolerance` is a **WAD-scaled `bigint`** - `1e18` (`parseUnits("1", 18)`) means 100%. It defaults to `DEFAULT_SLIPPAGE_TOLERANCE` = `300000000000000n` (`3e14`, i.e. 0.03%) and is capped at `MAX_SLIPPAGE_TOLERANCE` = `100000000000000000n` (`1e17`, i.e. 10%) - a larger value throws `ExcessiveSlippageToleranceError`, a negative one `NegativeInputError`. So to pass 0.1%, use `parseUnits("0.001", 18)` (= `1000000000000000n`) - **not** `0.1`, `0.001`, or `1n`. The same convention applies to every `slippageTolerance` parameter across the SDK.

### [Deposit with native-token wrapping](#deposit-with-native-token-wrapping)

```
// For vaults whose underlying asset is the chain's wNative token (WETH on mainnet),
// you can deposit native ETH that VaultBundlesV1 atomically wraps before depositing.
// `amount` and `nativeAmount` are mutually exclusive - passing both throws
// `MixedBundlesFundingError`.
const nativeDeposit = vault.deposit({
  nativeAmount: parseUnits("1", 18), // 1 ETH wrapped → WETH → deposited
  userAddress,
  vaultData,
});
const nativeDepositTx = nativeDeposit.buildTx();
```

VaultBundlesV1 atomically transfers the native token, wraps it to the chain's wNative (e.g. WETH), and deposits it. The transaction's `value` is set to `nativeAmount`. Throws `NativeAmountOnNonWNativeVaultError` if the vault asset is not the chain's wNative.

## [Withdraw](#withdraw)

```
// Routed through a direct VaultBundlesV1 call - burns the sender's vault shares.
// `vaultData` is required: the SDK derives an exact vault-share allowance from
// it (plus `deadline` and `slippageTolerance`), and `getRequirements()` returns
// a share approval or ERC-2612 permit requirement to VaultBundlesV1 when the
// live allowance is insufficient - an oversized allowance is always reset with
// an onchain approval.
const withdraw = vault.withdraw({
  amount: parseUnits("0.5", 18),
  userAddress,
  vaultData,
});
const withdrawSignatures = [];
for (const req of await withdraw.getRequirements()) {
  if ("sign" in req) {
    withdrawSignatures.push(await req.sign(client, userAddress));
  } else {
    await client.sendTransaction(req); // vault-share approval to VaultBundlesV1
  }
}
const withdrawTx = withdraw.buildTx(withdrawSignatures);
```

## [Redeem](#redeem)

```
// Direct VaultBundlesV1 call - same as withdraw but specifies an exact share
// amount, so it is immune to share-price drift between quoting and execution.
// `getRequirements()` resolves the exact vault-share allowance (approval or
// ERC-2612 permit) for the submitted shares.
const redeem = vault.redeem({
  shares: parseUnits("1", 18),
  userAddress,
});

const redeemRequirements = await redeem.getRequirements();
const redeemTx = redeem.buildTx(/* [requirementSignature] */);
```

## [In-kind redemption](#in-kind-redemption)

[In-kind redemption](https://docs.morpho.org/curate/concepts/liquidity/#in-kind-redemption) is the illiquid-vault exit path: it burns vault shares and transfers vault-held assets instead of requiring underlying liquidity from markets. Vault V1 transfers ordered Morpho Blue supply positions; Vault V2 returns available idle assets first, then transfers ordered Blue supply positions for the remainder. Both `client.morpho.vaultV1(...)` and `client.morpho.vaultV2(...)` expose `inKindRedeem`, and each action calls `VaultExitBundlesV1` directly.

This complements `withdraw`, `redeem`, and the Vault V2 force-deallocation flows. Use it when the underlying markets cannot release enough assets; for the illiquid remainder, the user takes ownership of the market positions and can withdraw from them later as liquidity returns.

> **Availability:** VaultExitBundlesV1 is registered on Ethereum, Base, Polygon, Arbitrum, Optimism, World Chain, Unichain, Katana, HyperEVM, Monad, Stable, Tempo, Arc, and Robinhood Chain. Custom deployments remain supported through `registerCustomAddresses`; constructing an exit on a chain without a registered address throws `UnknownAddressError`.

```
import { registerCustomAddresses } from "@morpho-org/morpho-sdk/addresses";

// A new chain entry must include the required Morpho Blue registry fields.
registerCustomAddresses({
  addresses: {
    [chainId]: {
      blue,
      adaptiveCurveIrm,
      bundles: { vaultExitBundlesV1 },
    },
  },
});
```

### [Vault V1](#vault-v1)

`vaultV1.inKindRedeem` prepares an illiquid Vault V1 exit into the vault's Morpho Blue supply positions. You control the greedy market order and must call `getRequirements()` before `buildTx()` so the RPC-backed Blue-balance and Morpho-deployment checks run, including the check that the vault is not Morpho Blue's fee recipient. The SDK validates that the ordered markets cover `amount` without assigning the same vault position twice when a market is repeated, but it does not validate the user's share balance: size the asset-denominated amount against `previewRedeem(sharesHeld)`. For the bounded share permit or approval, it first accrues pending performance-fee shares and then uses the current rounded-up burn; future interest can only reduce the required burn. The deadline is checked again when requirements resolve, and a later reallocation can still leave the on-chain loop under-covered after the snapshot was validated.

![Sequence diagram of Vault V1 in-kind redemption](https://docs.morpho.org/img/morpho-sdk/in-kind-redemption-vault-v1.png)
*Vault V1 contract flow: the Blue flash loan bridges the asset transfer while the user receives the vault's Blue supply positions.*

```
import {
  isRequirementSignature,
  type RequirementSignature,
} from "@morpho-org/morpho-sdk";

// `vaultV1Address` and `marketParamsList` are supplied by the integration.
const vaultV1 = client.morpho.vaultV1(vaultV1Address, mainnet.id);
const vaultV1Data = await vaultV1.getData();

const vaultV1Exit = vaultV1.inKindRedeem({
  amount: 1_000_000n,
  marketParamsList,
  vaultData: vaultV1Data,
  userAddress,
});

const vaultV1Signatures: RequirementSignature[] = [];
for (const requirement of await vaultV1Exit.getRequirements()) {
  if (isRequirementSignature(requirement)) {
    vaultV1Signatures.push(await requirement.sign(client, userAddress));
  } else {
    const hash = await client.sendTransaction(requirement);
    await publicClient.waitForTransactionReceipt({ hash });
  }
}

const vaultV1Tx = vaultV1Exit.buildTx(vaultV1Signatures);
// `vaultV1Tx` satisfies Readonly<Transaction<VaultV1InKindRedeemAction>>.
```

### [Vault V2](#vault-v2)

`vaultV2.inKindRedeem` prepares an illiquid Vault V2 exit into idle assets and its adapter's Morpho Blue supply positions. The vault must have exactly one `MorphoMarketV1AdapterV2`; `amount` is penalty-inclusive, and the action consumes idle assets before using your greedy market order for the remainder. Call `getRequirements()` before `buildTx()` so Blue balance, allowance, nonce, and the still-live deadline are checked on-chain. Vault gates are enforced by the final transaction rather than preflighted: receive gates may depend on VaultExitBundlesV1's transient initiator, while arbitrary send-share gates can observe intermediate state across multiple share burns. The SDK does not validate the user's share balance, so keep `amount + BigInt(marketParamsList.length) <= previewRedeem(sharesHeld)`; the per-market term covers V2 withdrawal rounding. Its bounded share allowance includes that buffer, separately rounded idle, penalty, and main burns, and accrual through the bundle deadline. An exit with no idle assets that rounds to zero after the penalty is rejected. Idle balance, penalty, or adapter-position drift after the snapshot can still cause an on-chain under-coverage panic.

![Sequence diagram of Vault V2 in-kind redemption](https://docs.morpho.org/img/morpho-sdk/in-kind-redemption-vault-v2.png)
*Vault V2 adapter leg when no idle assets are available: Morpho Blue's supply callback provides just-in-time liquidity through the vault's sole supported adapter; no flash loan is used. The contract consumes idle assets before this flow.*

```
import {
  isRequirementSignature,
  previewVaultV2InKindRedeem,
  type RequirementSignature,
} from "@morpho-org/morpho-sdk";

const vaultV2Data = await vault.getData();
const requestedExitAssets = 1_000_000n;
const latestBlock = await publicClient.getBlock();
const marketChoices = previewVaultV2InKindRedeem(vaultV2Data, {
  requestedExitAssets,
  timestamp: latestBlock.timestamp,
});
const marketChoice = marketChoices[0];

if (marketChoice == null) {
  throw new Error("This vault has no supported in-kind redemption market");
}

// Each row is one single-market choice. It also reports `idleAssets`,
// `netAssets`, `feeAssets`, and `remainingExitAssets` for the requested amount.
const vaultV2Exit = vault.inKindRedeem({
  amount: marketChoice.exitAssets,
  marketParamsList: [marketChoice.marketParams],
  vaultData: vaultV2Data,
  userAddress,
});

const vaultV2Signatures: RequirementSignature[] = [];
for (const requirement of await vaultV2Exit.getRequirements()) {
  if (isRequirementSignature(requirement)) {
    vaultV2Signatures.push(await requirement.sign(client, userAddress));
  } else {
    const hash = await client.sendTransaction(requirement);
    await publicClient.waitForTransactionReceipt({ hash });
  }
}

const vaultV2Tx = vaultV2Exit.buildTx(vaultV2Signatures);
// `vaultV2Tx` satisfies Readonly<Transaction<VaultV2InKindRedeemAction>>.
```

### [Parameters and validation](#parameters-and-validation)

| Parameter or behavior | Vault V1 | Vault V2 |
| --- | --- | --- |
| `amount` | Asset-denominated amount to exit. | Penalty-inclusive, asset-denominated amount to exit; the idle portion is returned directly. |
| `marketParamsList` | Ordered vault markets consumed greedily; repeated entries cannot draw from the same position twice. | Ordered adapter markets consumed greedily after idle assets; may be empty when idle balance covers `amount`, and its length sets the share-sufficiency rounding buffer. |
| `vaultData` | Pre-fetched `AccrualVault` snapshot for this Vault V1. | Pre-fetched `AccrualVaultV2` snapshot for this Vault V2. |
| `userAddress` | Account that signs and submits the exit. | Account that signs and submits the exit. |
| `adapter` | Not accepted. | Optional override that defaults to the vault's sole adapter. |
| `deadline` | Optional shared permit/bundle deadline; defaults to two hours from handle creation and is rechecked during requirement resolution. | Optional shared permit/bundle deadline; defaults to two hours from handle creation and is rechecked during requirement resolution. |
| Return value | Lazy prerequisite resolution plus a synchronous `buildTx(signatures?)`. | Lazy prerequisite resolution plus a synchronous `buildTx(signatures?)`. |
| `getRequirements()` | Checks Blue balance, Morpho deployment, and Blue fee recipient; resolves a bounded share authorization after pending performance-fee accrual. | Checks Blue balance, allowance, and nonce on-chain; resolves a bounded authorization for the market-count buffer and separately rounded idle, penalty, and main burns with accrual through the deadline. |
| Vault gates | Not applicable. | Enforced by the final transaction, not preflighted; simulate the authorized transaction when compatibility must be checked before submission. |
| User share balance | Not checked; size `amount` in asset terms against `previewRedeem(sharesHeld)`. | Not checked; keep `amount + BigInt(marketParamsList.length) <= previewRedeem(sharesHeld)`. |
| Share authorization | Bounded to the current rounded-up burn after pending performance-fee accrual. | Bounded across the market-count buffer and separately rounded idle, penalty, and main burns at the current and deadline-accrued states. |
| Snapshot drift | A later reallocation can make the on-chain loop under-cover. | Idle balance, penalty, and adapter-position drift can cause an on-chain under-coverage panic. |

Always await `getRequirements()` and dispatch its results through [The `getRequirements` flow](https://docs.morpho.org/developers/sdks/morpho-sdk/#the-getrequirements-flow) before calling `buildTx()`.

### [Errors](#errors)

| Error | Vault | Trigger |
| --- | --- | --- |
| `ChainIdMismatchError` | V1 and V2 | The viem client and entity target different chains. |
| `VaultAddressMismatchError` | V1 and V2 | `vaultData` belongs to another vault. |
| `NonPositiveInputError` | V1 and V2 | `amount` is not positive. |
| `InKindRedeemZeroDeallocationError` | V2 | The vault has no idle assets and the penalty-adjusted amount rounds to zero deallocated assets. |
| `EmptyMarketParamsListError` | V1 and V2 | The V1 list is empty, or V2 must deallocate assets and its list is empty. |
| `ExpiredDeadlineError` | V1 and V2 | `deadline` has passed at handle creation or requirement resolution. |
| `InKindRedeemCoverageError` | V1 and V2 | The V1 list cannot cover the exit without overspending a repeated market, or the V2 idle balance plus deduplicated list cannot cover it. |
| `UnsupportedChainIdError` | V1 and V2 | No address registry exists for the target chain. |
| `UnknownAddressError` | V1 and V2 | VaultExitBundlesV1 is not registered on the target chain. |
| `viem.BaseError` | V1 and V2 | An RPC or multicall contract read fails during `getRequirements()`. |
| `InsufficientBlueBalanceForInKindRedeemError` | V1 and V2 | Blue cannot fund the V1 flash loan or the V2 largest callback. |
| `AmbiguousRequirementSignaturesError` | V1 and V2 | `buildTx()` receives more than one permit signature. |
| `UnexpectedRequirementSignatureError` | V1 and V2 | `buildTx()` receives a non-permit signature. |
| `BundlesPermitMismatchError` | V1 and V2 | The requirement has the wrong permit kind, asset, or signature encoding. |
| `VaultMorphoMismatchError` | V1 | `getRequirements()` finds that the vault uses another Morpho deployment. |
| `VaultIsBlueFeeRecipientError` | V1 | `getRequirements()` finds that Morpho Blue accrues protocol fees to the vault. |
| `VaultV2SingleAdapterRequiredError` | V2 | The vault does not have exactly one adapter. |
| `AdapterNotPartOfVaultError` | V2 | The selected adapter is not the vault's adapter. |
| `VaultV2UnsupportedExitAdapterError` | V2 | The adapter is not a `MorphoMarketV1AdapterV2`. |

For a complete integration from preview through simulation and submission, follow [Exit an illiquid vault in kind](https://docs.morpho.org/developers/earn/tutorials/in-kind-redemption/).

## [Force withdraw / force redeem](#force-withdraw--force-redeem)

For VaultV2, `forceWithdraw` exits an illiquid vault position into the underlying asset through a direct VaultExitBundlesV1 call: the contract computes its own deallocations from the vault's adapter, so the caller supplies no deallocation list. The vault must resolve to exactly one supported adapter (or the explicit `adapter` override), and `getRequirements()` resolves the exact vault-share allowance (approval or ERC-2612 permit) for the computed burn.

```
// Direct VaultExitBundlesV1 call - the contract force-withdraws `exitAssets`
// from the vault's sole adapter, bounding the realized exit share price with an
// SDK-computed `minSharePriceE27` (overridable, never zero).
const forceWithdraw = vault.forceWithdraw({
  exitAssets: parseUnits("0.5", 18),
  vaultData,
  userAddress,
  // adapter: "0xAdapter0000000000000000000000000000000000", // explicit override
  // slippageTolerance / deadline / referralFeePct / referralFeeRecipient optional
});

const forceWithdrawRequirements = await forceWithdraw.getRequirements();
const forceWithdrawTx = forceWithdraw.buildTx(/* [requirementSignature] */);
```

For manual deallocation, `forceRedeem` still encodes a caller-supplied `forceDeallocate` chain followed by a single `redeem` inside the vault's native `multicall`.

```
// Share-based counterpart to forceWithdraw. The deallocated total must be
// >= the asset-equivalent of the redeemed shares; apply a buffer for share-price drift.
const forceRedeem = vault.forceRedeem({
  deallocations: [
    {
      adapter: "0xAdapter0000000000000000000000000000000000",
      amount: parseUnits("1.01", 18), // small buffer over target assets
    },
  ],
  redeem: { shares: parseUnits("1", 18) },
  userAddress,
});
const forceRedeemTx = forceRedeem.buildTx();
```

See the [Actions overview](https://docs.morpho.org/developers/sdks/morpho-sdk/#actions-overview) on the Morpho SDK page for the full route table and its [Errors and invariants](https://docs.morpho.org/developers/sdks/morpho-sdk/#errors-and-invariants) for the vault error classes.

[Morpho SDK

Previous Page

](https://docs.morpho.org/developers/sdks/morpho-sdk/)[Variable Rate Market - Blue

Next Page

](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/)