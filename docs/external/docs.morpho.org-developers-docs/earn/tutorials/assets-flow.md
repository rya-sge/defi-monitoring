# Depositing & Withdrawing from Vaults

> Source: https://docs.morpho.org/developers/earn/tutorials/assets-flow

---

# Depositing & Withdrawing from Vaults

**Morpho Vault V2** follows the standard [ERC‑4626](https://eips.ethereum.org/EIPS/eip-4626) interface for deposit and withdrawal operations. That means `deposit()`, `withdraw()`, `mint()`, and `redeem()` behave like familiar tokenized vault flows for new Earn integrations on Morpho.

**Morpho Vault V2** has a non-conventional behavior on max functions (`maxDeposit`, `maxMint`, `maxWithdraw`, `maxRedeem`): they always return zero. See the [Morpho Vaults V2 reference](https://docs.morpho.org/developers/contracts/morpho-vaults-v2/#maxdeposit) for the reason, and [Compute deposit and withdrawal limits](#compute-deposit-and-withdrawal-limits) for what to use instead.

Before integrating with any ERC4626 vault, verify that adequate inflation attack protection is in place. See [Inflation Attack Protection](https://docs.morpho.org/developers/earn/concepts/vault-mechanics/#inflation-attack-protection).

For background on ERC4626 mechanics and vault architecture, see [Vaults & ERC4626 Mechanics](https://docs.morpho.org/developers/earn/concepts/vault-mechanics/).

This guide shows the recommended integration path for Morpho Vault deposits and withdrawals: the [**Morpho SDK**](https://docs.morpho.org/developers/sdks/morpho-sdk/) ([`@morpho-org/morpho-sdk`](https://github.com/morpho-org/sdks/tree/main/packages/morpho-sdk)). It builds final, ready-to-send `viem` transactions and resolves all on-chain pre-requisites for you - ERC-20 approvals, Permit / Permit2 signatures, native-token wrapping, slippage protection, and `VaultBundlesV1` routing - whether you're building a dApp frontend or a backend service.

## [Key Concepts: Assets vs. Shares](#key-concepts-assets-vs-shares)

When interacting with ERC4626 vaults, you have two approaches for deposits and withdrawals: an **asset-first** approach or a **shares-first** approach. Understanding the difference is key to a robust integration.

| Approach | Deposit Function | Withdrawal Function | Description |
| --- | --- | --- | --- |
| **Asset-First** | `deposit(assets, ...)` | `withdraw(assets, ...)` | You specify the exact amount of the underlying token (e.g., USDC, WETH) you want to deposit or withdraw. |
| **Shares-First** | `mint(shares, ...)` | `redeem(shares, ...)` | You specify the exact number of vault shares you want to mint or redeem. |

**Best Practice:**

- For **deposits**, `deposit()` is the most common and intuitive function.
- For **full withdrawals**, `redeem()` is recommended. Redeeming all of a user's shares ensures their balance goes to zero and avoids leaving behind small, unusable amounts of "dust."
- For **partial withdrawals** where a user needs a specific amount of the underlying asset, `withdraw()` is appropriate.

## [Integrate with the Morpho SDK](#integrate-with-the-morpho-sdk)

For an end-to-end walkthrough of every vault action this SDK exposes (deposit, withdraw, redeem, force-withdraw) see the [**Vault subpage**](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/); the [Morpho SDK page](https://docs.morpho.org/developers/sdks/morpho-sdk/) covers the `getRequirements` flow, the builder = signer invariant, and error classes.

### [Step 1: Install and set up the client](#step-1-install-and-set-up-the-client-toc)

```
npm install @morpho-org/morpho-sdk@6.0.0 viem@^2.0.0
# or
pnpm add @morpho-org/morpho-sdk@6.0.0 viem@^2.0.0
# or
yarn add @morpho-org/morpho-sdk@6.0.0 viem@^2.0.0
```

```
import { createWalletClient, http } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { mainnet } from "viem/chains";
import { morphoViemExtension } from "@morpho-org/morpho-sdk";

const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`);

const client = createWalletClient({
  account,
  chain: mainnet,
  transport: http(process.env.RPC_URL_MAINNET),
}).extend(
  morphoViemExtension({
    // Enables Permit / Permit2 in getRequirements() so users skip the extra approve tx.
    supportSignature: true,
  }),
);

const vault = client.morpho.vaultV2("0xVaultAddress...", mainnet.id);
```

### [Step 2: Deposit](#step-2-deposit-toc)

```
import { parseUnits } from "viem";

const vaultData = await vault.getData(); // fresh on-chain state with accrued interest

const deposit = vault.deposit({
  amount: parseUnits("1.0", 18), // 1 underlying token
  userAddress: account.address,
  vaultData,
});

// 1. Resolve approvals / permits before sending the deposit
const requirements = await deposit.getRequirements();
const signatures = [];
for (const req of requirements) {
  if ("sign" in req) {
    // Permit / Permit2: capture the off-chain signature
    signatures.push(await req.sign(client, account.address));
  } else {
    // ERC-20 approval: send the approval transaction
    await client.sendTransaction(req);
  }
}

// 2. Build and send the deposit tx (same client that built it - "builder = signer").
//    buildTx takes the collected requirement signatures as an array.
const depositTx = deposit.buildTx(signatures);
const depositTxHash = await client.sendTransaction(depositTx);
console.log("Deposit successful:", depositTxHash);
```

### [Step 3: Withdraw / redeem](#step-3-withdraw--redeem-toc)

```
// Redeem all of a user's shares (recommended for full exits - leaves no dust)
const userShares = vaultData.toShares(parseUnits("1.0", 18));

const redeem = vault.redeem({
  shares: userShares,
  userAddress: account.address,
});

// VaultBundlesV1 burns the sender's shares, so redeem needs an exact
// vault-share approval or ERC-2612 permit first.
const redeemSignatures = [];
for (const req of await redeem.getRequirements()) {
  if ("sign" in req) {
    redeemSignatures.push(await req.sign(client, account.address));
  } else {
    await client.sendTransaction(req);
  }
}

const redeemTxHash = await client.sendTransaction(redeem.buildTx(redeemSignatures));
console.log("Withdrawal successful:", redeemTxHash);
```

For partial withdrawals by exact asset amount, use `vault.withdraw({ amount, userAddress, vaultData })` instead of `redeem` - `withdraw` additionally requires the fetched `vaultData`.

If borrowed liquidity prevents a normal exit, follow [Exit an illiquid vault in kind](https://docs.morpho.org/developers/earn/tutorials/in-kind-redemption/) to preview and transfer the vault's positions.

## [Compute deposit and withdrawal limits](#compute-deposit-and-withdrawal-limits)

Vault V2's `maxDeposit`, `maxMint`, `maxWithdraw` and `maxRedeem` views always return zero, so you can't use them to size a "Max" button or to decide whether a vault accepts funds. Compute the limits from vault state instead. A transaction above its limit reverts onchain.

Three things bound a transaction:

- **Withdrawal liquidity.** A withdrawal is paid from the vault's idle assets first, then from the liquidity adapter. Assets the vault has allocated through other adapters aren't available to a plain withdrawal. A user can still move them back to idle with [`forceDeallocate`](https://docs.morpho.org/developers/earn/tutorials/force-deallocate/), which the limits below don't include.
- **Deposit caps.** When the vault has a liquidity adapter, a deposit is allocated to it and reverts with `AbsoluteCapExceeded` or `RelativeCapExceeded` if it would push an allocation above the curator's caps.
- **Gates.** A gate can refuse the user or the contract that calls the vault. Capacity calculations don't account for gates; [check them separately](#check-gates-before-sending).

### [With the Morpho SDK](#with-the-morpho-sdk)

The vault data returned by `getData()` computes both limits from fresh onchain state. The deposit, withdraw and redeem builders don't check these limits, so check them before you build the transaction.

```
import { CapacityLimitReason } from "@morpho-org/morpho-sdk/utils";
import { erc20Abi } from "viem";
import { readContract } from "viem/actions";

const vaultData = await vault.getData(); // fresh on-chain state with accrued interest

const [walletAssets, userShares] = await Promise.all([
  readContract(client, {
    address: vaultData.asset,
    abi: erc20Abi,
    functionName: "balanceOf",
    args: [account.address],
  }),
  readContract(client, {
    address: vaultData.address,
    abi: erc20Abi,
    functionName: "balanceOf",
    args: [account.address],
  }),
]);

const depositLimit = vaultData.maxDeposit(walletAssets);
const withdrawLimit = vaultData.maxWithdraw(userShares);
console.log("Max deposit:", depositLimit.value, depositLimit.limiter);
console.log("Max withdraw:", withdrawLimit.value, withdrawLimit.limiter);

// "Max" deposit: already bounded by the wallet balance passed in.
const maxDepositAmount = depositLimit.value;

// "Max" withdraw: redeem every share when liquidity covers the position (no dust),
// otherwise withdraw the available amount with vault.withdraw.
const canExitFully = withdrawLimit.limiter === CapacityLimitReason.balance;
```

Both methods return a `CapacityLimit`: `value` is the amount in underlying asset units, and `limiter` says what bounds it.

- `"Balance"` (`CapacityLimitReason.balance`): the amount you passed in fits. For a withdrawal, the user can exit their whole position.
- `"Liquidity"` (`CapacityLimitReason.liquidity`): withdrawals only. Idle assets plus the liquidity adapter's available liquidity are below the user's position; show the reduced amount as currently withdrawable.
- `"VaultV2_AbsoluteCap"` / `"VaultV2_RelativeCap"` (`CapacityLimitReason.vaultV2_absoluteCap` / `vaultV2_relativeCap`): deposits only. An absolute or relative allocation cap on the liquidity adapter leaves less room than requested; show the vault as near capacity.
- `"Cap"` (`CapacityLimitReason.cap`): deposits only, when the liquidity adapter is a `MorphoVaultV1Adapter`. The underlying Morpho Vault V1's market supply caps leave less room than requested.

Before you rely on these limits:

- `maxWithdraw` takes a share amount, not a user. Pass the user's share balance.
- Neither method checks gates.
- `maxDeposit` throws `VaultV2Errors.UnsupportedLiquidityAdapter` when the vault's liquidity adapter is the non-V2 `MorphoMarketV1Adapter`, because the SDK doesn't load allocation caps for it.
- The withdrawal limit covers idle assets plus liquidity adapter capacity only, not assets allocated through other adapters.

### [With the Morpho API](#with-the-morpho-api)

A read-only integration, such as analytics, a backend, or a UI without the SDK, gets the assets a plain withdrawal can pay now by adding `idle_assets` and `liquidity_adapter_available_assets` from the [withdrawal options endpoint](https://docs.morpho.org/api/vaults-v2/get-v2-vault-withdrawal-options/).

A user's withdrawal limit is the lower of that sum and the `assets` of their [position](https://docs.morpho.org/api/vaults-v2/user-v2-vault-position/). The same response lists each adapter's `force_deallocatable_assets` and `penalty_rate_wad`, which only a [force deallocation](https://docs.morpho.org/developers/earn/tutorials/force-deallocate/) can use.

The API returns no deposit limit; compute it with the SDK. Indexed data can lag the chain, so recheck with fresh onchain state before sending a transaction.

### [Onchain integrations](#onchain-integrations)

A contract such as an ERC-4626 router can't call the SDK. It can recompute the withdrawal limit with view calls: the vault's idle balance of its asset plus what the liquidity adapter can withdraw from the market encoded in the vault's `liquidityData`, capped by the owner's assets (`previewRedeem` of their shares).

The [`VaultV2LiquidityLens` in morpho-snippets](https://github.com/morpho-org/morpho-snippets#vaultv2-liquidity-lib-alternative-view-for-maxwithdraw--maxredeem) shows this computation. It is an unaudited example, it only reads `MorphoMarketV1AdapterV2` and `MorphoVaultV1Adapter` liquidity adapters (any other adapter counts as zero), it doesn't compute a deposit limit, and it doesn't check gates.

### [Check gates before sending](#check-gates-before-sending)

A gate set to the zero address allows everyone. The vault exposes the gate result as view functions, so you can check an address without reading the gate contracts:

| Operation | Checks |
| --- | --- |
| Deposit or mint | `canReceiveShares(onBehalf)` and `canSendAssets(caller)` |
| Withdraw or redeem | `canSendShares(owner)` and `canReceiveAssets(receiver)` |
| Share transfer | `canSendShares(from)` and `canReceiveShares(to)` |

Here `caller` is the account that calls the vault. When you deposit or withdraw through `VaultBundlesV1`, as the Morpho SDK does, the bundle is the `caller` of a deposit and the `receiver` of a withdrawal, so the gates must allow the bundle as well as the user.

A gate can read the bundle's initiator from `VaultBundlesV1`'s transient storage, so a view call on the bundle address can disagree with the real transaction. Simulate the whole bundle with `eth_call` instead.

See [Gates](https://docs.morpho.org/curate/concepts/gates/) for how each gate works.

### [Withdrawing more than the liquidity limit](#withdrawing-more-than-the-liquidity-limit)

When a user needs more than the withdrawal limit, they can [force-deallocate](https://docs.morpho.org/developers/earn/tutorials/force-deallocate/) from the vault's other adapters, which costs a penalty if the curator set one, or [exit in kind](https://docs.morpho.org/developers/earn/tutorials/in-kind-redemption/) when borrowed liquidity blocks a normal exit.

## [Slippage for User Experience](#slippage-for-user-experience)

Vault deposits convert assets into shares. Between quote and execution, the vault share price can move because interest accrues or vault state changes. Slippage tolerance lets the transaction revert if the user would receive materially fewer shares than expected.

The SDK computes the `maxSharePrice` guard from fresh vault data and your `slippageTolerance`, then routes the deposit through `VaultBundlesV1`.

The SDK default is `0.03%`; the maximum accepted value is `10%`. A tighter value gives stronger price protection but can cause more reverts when vault state changes before inclusion.

### [Step 1: Set the deposit inputs](#step-1-set-the-deposit-inputs-toc)

Choose the asset amount and maximum tolerated movement before building the SDK transaction. Slippage is expressed in WAD units: `parseUnits("0.01", 18)` means 1%.

```
import { parseUnits, type Address } from "viem";
import { mainnet } from "viem/chains";
import {
  isRequirementSignature,
  type RequirementSignature,
} from "@morpho-org/morpho-sdk";

// Assumes `client` is a viem wallet client extended with `morphoViemExtension()`
// and `account` is the connected signer.
const vaultAddress = "0xVaultAddress..." as Address;
const userAddress = account.address;
const amount = parseUnits("1.0", 18); // replace 18 with the underlying asset decimals
const slippageTolerance = parseUnits("0.01", 18); // 1% in WAD units

const vault = client.morpho.vaultV2(vaultAddress, mainnet.id);
const vaultData = await vault.getData(); // fresh on-chain state with accrued interest
```

### [Step 2: Build the protected deposit transaction](#step-2-build-the-protected-deposit-transaction-toc)

Pass `vaultData` and `slippageTolerance` to the deposit builder so the SDK can build the onchain share-price guard.

```
const deposit = vault.deposit({
  amount,
  userAddress,
  vaultData,
  slippageTolerance,
});
```

### [Step 3: Resolve approvals and permits](#step-3-resolve-approvals-and-permits-toc)

`getRequirements()` returns approval transactions plus an optional Permit / Permit2 signature. Resolve them before sending the final deposit.

```
const requirements = await deposit.getRequirements();
const requirementSignatures: RequirementSignature[] = [];

for (const requirement of requirements) {
  if (isRequirementSignature(requirement)) {
    requirementSignatures.push(await requirement.sign(client, userAddress));
  } else {
    await client.sendTransaction(requirement);
  }
}
```

### [Step 4: Send the protected deposit](#step-4-send-the-protected-deposit-toc)

Build the final transaction with the optional signature, then send it with the same client that built the transaction.

```
const depositTxHash = await client.sendTransaction(deposit.buildTx(requirementSignatures));
console.log("Deposit sent:", depositTxHash);
```

See also [Vault Mechanics: Slippage Considerations](https://docs.morpho.org/developers/earn/concepts/vault-mechanics/#additional-considerations-slippage) for more context.

[Wallet Structures

Previous Page

](https://docs.morpho.org/developers/earn/concepts/wallet-structures/)[Support forceDeallocate withdrawals

Next Page

](https://docs.morpho.org/developers/earn/tutorials/force-deallocate/)