# Exit an illiquid vault in kind

> Source: https://docs.morpho.org/developers/earn/tutorials/in-kind-redemption

---

# Exit an illiquid vault in kind

[In-kind redemption](https://docs.morpho.org/curate/concepts/liquidity/#in-kind-redemption) is the fallback exit for the part of a vault position that cannot be returned through a normal withdrawal because the underlying liquidity is borrowed. It transfers the vault's exposure instead of manufacturing liquidity.

In-kind redemption has called the VaultExitBundlesV1 contract directly since `@morpho-org/morpho-sdk@5.5.0`. Version `6.0.0` routes every Blue and Vault write through Morpho Bundles - use it for new integrations.

VaultExitBundlesV1 is registered on Ethereum, Base, Polygon, Arbitrum, Optimism, World Chain, Unichain, Katana, HyperEVM, Monad, Stable, Tempo, Arc, and Robinhood Chain. Custom deployments remain supported; see the [SDK registration example](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/#in-kind-redemption).

Prefer a normal `withdraw` or `redeem` while the vault can return the underlying asset. Use this flow only for an illiquid remainder, and show the user the assets and market positions they will receive before requesting a signature.

## [Before you begin](#before-you-begin)

| Vault | User receives | Amount | Required shape |
| --- | --- | --- | --- |
| Vault V1 | Ordered Morpho Blue supply positions. | Asset-denominated exit amount. | A caller-ordered list of enabled vault markets consumed greedily. |
| Vault V2 | Available idle assets first, then ordered Morpho Blue supply positions net of the force-deallocation penalty. | Penalty-inclusive, asset-denominated exit amount. | Exactly one `MorphoMarketV1AdapterV2`; ordered markets are consumed after idle assets. |

The SDK does not validate the user's share balance. For Vault V1, size `amount` against the vault contract's `previewRedeem(sharesHeld)`; for Vault V2, keep `amount + BigInt(marketParamsList.length) <= previewRedeem(sharesHeld)` because each market needs a one-asset withdrawal-rounding buffer. `getRequirements()` produces a bounded vault-share authorization: V1 accounts for pending performance-fee shares, while V2 covers the per-market rounding buffer plus separately rounded idle, penalty, and main burns with accrual through the deadline. Simulate the final transaction after authorization because Vault V2 gates and snapshot drift are not fully preflighted.

The examples assume a private-key signer for a backend integration. In a frontend, construct the wallet client from the connected provider but keep the same invariant: the account that builds the action signs its requirements and submits the final transaction.

### [Step 1: Set up the clients](#step-1-set-up-the-clients)

```
import "dotenv/config";
import {
  createWalletClient,
  http,
  parseAbi,
  publicActions,
  type Address,
} from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { mainnet } from "viem/chains";
import { morphoViemExtension } from "@morpho-org/morpho-sdk";

const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`);
const client = createWalletClient({
  account,
  chain: mainnet,
  transport: http(process.env.RPC_URL),
})
  .extend(publicActions)
  .extend(morphoViemExtension({ supportSignature: true }));
const publicClient = client;

const userAddress = account.address;
const vaultV1Address = process.env.VAULT_V1_ADDRESS as Address;
const vaultV2Address = process.env.VAULT_V2_ADDRESS as Address;
const vaultReadAbi = parseAbi([
  "function balanceOf(address account) view returns (uint256)",
  "function previewRedeem(uint256 shares) view returns (uint256)",
]);
```

### [Step 2: Preview a Vault V2 exit](#step-2-preview-a-vault-v2-exit)

```
import { previewVaultV2InKindRedeem } from "@morpho-org/morpho-sdk";

const vaultV2 = client.morpho.vaultV2(vaultV2Address, mainnet.id);
const [vaultV2Data, latestBlock, sharesHeld] = await Promise.all([
  vaultV2.getData(),
  publicClient.getBlock(),
  publicClient.readContract({
    address: vaultV2Address,
    abi: vaultReadAbi,
    functionName: "balanceOf",
    args: [userAddress],
  }),
]);
const maximumRedeemAssets = await publicClient.readContract({
  address: vaultV2Address,
  abi: vaultReadAbi,
  functionName: "previewRedeem",
  args: [sharesHeld],
});
// This example passes one market, so reserve the one-asset V2 rounding buffer.
const marketRoundingBuffer = 1n;
if (maximumRedeemAssets <= marketRoundingBuffer) {
  throw new Error("Vault V2 position is too small for in-kind redemption");
}
const requestedExitAssets = maximumRedeemAssets - marketRoundingBuffer;
const [marketChoice] = previewVaultV2InKindRedeem(vaultV2Data, {
  requestedExitAssets,
  timestamp: latestBlock.timestamp,
});

if (marketChoice == null) {
  throw new Error("No supported Vault V2 in-kind redemption choice");
}

console.log({
  marketParams: marketChoice.marketParams,
  maxExitAssets: marketChoice.maxExitAssets,
  exitAssets: marketChoice.exitAssets,
  remainingExitAssets: marketChoice.remainingExitAssets,
  idleAssets: marketChoice.idleAssets,
  netAssets: marketChoice.netAssets,
  feeAssets: marketChoice.feeAssets,
});
// This example executes one market choice. Rebuild from fresh state for any
// remainingExitAssets after the transaction confirms.
```

### [Step 3: Build and authorize the Vault V2 exit](#step-3-build-and-authorize-the-vault-v2-exit)

```
import {
  isRequirementSignature,
  type RequirementSignature,
} from "@morpho-org/morpho-sdk";

const vaultV2Exit = vaultV2.inKindRedeem({
  amount: marketChoice.exitAssets,
  marketParamsList: [marketChoice.marketParams],
  vaultData: vaultV2Data,
  userAddress,
});
const vaultV2Signatures: RequirementSignature[] = [];

// Requirements authorize only the bounded shares needed for the per-market
// rounding buffer and separately rounded idle, penalty, and main burns through deadline.
for (const requirement of await vaultV2Exit.getRequirements()) {
  if (isRequirementSignature(requirement)) {
    vaultV2Signatures.push(await requirement.sign(client, userAddress));
  } else {
    const hash = await client.sendTransaction(requirement);
    await publicClient.waitForTransactionReceipt({ hash });
  }
}

const vaultV2Tx = vaultV2Exit.buildTx(vaultV2Signatures);
// Simulate after authorization to check gates and post-snapshot state.
await publicClient.call({
  account: userAddress,
  to: vaultV2Tx.to,
  data: vaultV2Tx.data,
  value: vaultV2Tx.value,
});
const vaultV2Hash = await client.sendTransaction(vaultV2Tx);
await publicClient.waitForTransactionReceipt({ hash: vaultV2Hash });
console.log("Vault V2 in-kind redemption confirmed:", vaultV2Hash);
```

If the preview reports a non-zero remainder, do not append another preview row to the same call: each row is an alternative single-market choice. Complete the selected partial exit, fetch a new vault snapshot, and preview the remainder again—or build an ordered multi-market list only if your integration independently validates the combined coverage.

## [Vault V1 variant](#vault-v1-variant)

Vault V1 has no single-market preview helper. Build its ordered market list from the fresh vault snapshot, then let the entity validate coverage before resolving requirements.

### [Step 1: Prepare the Vault V1 action](#step-1-prepare-the-vault-v1-action)

```
const vaultV1 = client.morpho.vaultV1(vaultV1Address, mainnet.id);
const [vaultV1Data, vaultV1SharesHeld] = await Promise.all([
  vaultV1.getData(),
  publicClient.readContract({
    address: vaultV1Address,
    abi: vaultReadAbi,
    functionName: "balanceOf",
    args: [userAddress],
  }),
]);
const vaultV1ExitAssets = await publicClient.readContract({
  address: vaultV1Address,
  abi: vaultReadAbi,
  functionName: "previewRedeem",
  args: [vaultV1SharesHeld],
});
const marketParamsList = [...vaultV1Data.allocations.values()]
  .filter(
    ({ config, position }) =>
      config.enabled && position.supplyShares > 0n,
  )
  .map(({ position }) => position.market.params);

// The allocations Map is unique by market id. Repeated entries cannot spend
// the same vault position twice.
const vaultV1Exit = vaultV1.inKindRedeem({
  amount: vaultV1ExitAssets,
  marketParamsList,
  vaultData: vaultV1Data,
  userAddress,
});
```

### [Step 2: Authorize, simulate, and submit](#step-2-authorize-simulate-and-submit)

```
import {
  isRequirementSignature,
  type RequirementSignature,
} from "@morpho-org/morpho-sdk";

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
await publicClient.call({
  account: userAddress,
  to: vaultV1Tx.to,
  data: vaultV1Tx.data,
  value: vaultV1Tx.value,
});
const vaultV1Hash = await client.sendTransaction(vaultV1Tx);
await publicClient.waitForTransactionReceipt({ hash: vaultV1Hash });
console.log("Vault V1 in-kind redemption confirmed:", vaultV1Hash);
```

## [Recover from rejected previews or transactions](#recover-from-rejected-previews-or-transactions)

| Error | Meaning | Recovery |
| --- | --- | --- |
| `VaultV2SingleAdapterRequiredError` | The Vault V2 snapshot does not contain exactly one adapter. | Use another exit path; in-kind redemption supports one `MorphoMarketV1AdapterV2`. |
| `InKindRedeemZeroDeallocationError` | With no idle assets, the penalty-adjusted exit rounds to zero deallocated assets. | Increase the amount or use another exit path. |
| `EmptyMarketParamsListError` | Markets are required but the ordered list is empty. | Supply enough current vault markets to cover the non-idle exit. |
| `InKindRedeemCoverageError` | The ordered markets cannot cover the requested exit without exceeding a vault position. | Reduce the amount to the error's `maxExitAssets` or rebuild with sufficient current markets. |
| `ExpiredDeadlineError` | The deadline has passed at action creation or requirement resolution. | Rebuild the action and resolve its requirements again. |
| `InsufficientBlueBalanceForInKindRedeemError` | Morpho Blue cannot fund the required flash loan or largest callback. | Reduce the amount or wait for Blue liquidity. |
| `UnknownAddressError` | VaultExitBundlesV1 is not registered for the selected chain. | Register a custom deployment or use a chain with a canonical deployment. |
| `VaultIsBlueFeeRecipientError` | A Vault V1 is Morpho Blue's fee recipient, whose accrued fee shares cannot be safely accounted for. | Use another exit path. |
| `BundlesPermitMismatchError` | The supplied permit has the wrong kind, asset, or signature encoding. | Rebuild the action and sign its new vault-exit permit. |

RPC or multicall failures surface as `viem.BaseError`; after any quote-time or submission failure, fetch a fresh snapshot and rebuild the action instead of reusing the old transaction.

For the complete mechanics, parameter table, and error surface, see the [Morpho SDK vault reference](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/#in-kind-redemption).

[Support forceDeallocate withdrawals

Previous Page

](https://docs.morpho.org/developers/earn/tutorials/force-deallocate/)[Get Data

Next Page

](https://docs.morpho.org/developers/earn/tutorials/get-data/)