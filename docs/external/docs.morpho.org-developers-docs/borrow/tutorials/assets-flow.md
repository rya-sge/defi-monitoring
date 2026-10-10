# Supply Collateral, Borrow, Repay & Withdraw Collateral

> Source: https://docs.morpho.org/developers/borrow/tutorials/assets-flow

---

# Supply Collateral, Borrow, Repay & Withdraw Collateral

This tutorial provides a comprehensive guide for developers on how to integrate the core functionalities of Morpho Markets: supplying collateral, borrowing, repaying debt, and withdrawing collateral.

Unlike ERC4626 vaults, Morpho Markets have a unique interface defined by the core `Morpho` contract. Understanding these functions is essential for building any application with borrowing capabilities.

The recommended integration path is the [**Morpho SDK**](https://docs.morpho.org/developers/sdks/morpho-sdk/) ([`@morpho-org/morpho-sdk`](https://github.com/morpho-org/sdks/tree/main/packages/morpho-sdk)) - a thin abstraction layer over Morpho Blue. It produces ready-to-send `viem` transactions (atomic supply+borrow, atomic repay+withdraw, partial vs full repay by shares, BlueBundlesV1 authorization, the LLTV buffer) so you don't have to wire `writeContract` calls by hand.

## [Key Concepts: Assets vs. Shares](#key-concepts-assets-vs-shares)

The core accounting system in Morpho Markets revolves around the concepts of `assets` and `shares`. This applies to the `borrow` positions (the loanable asset), but **not** to the collateral.

| Concept | Functions Affected | Description |
| --- | --- | --- |
| **Assets** | `borrow`, `repay` | The actual underlying token (e.g., USDC, WETH) that a user wants to lend or borrow. |
| **Shares** | `borrow`, `repay` | Internal accounting units representing a proportional claim on the market's total supply or debt. |

**Best Practice:**

- For `borrow`, specifying an exact asset amount is the most common and intuitive approach for users.
- For **full repayments**, repaying by shares with `maxUint256` (saturated full close) is highly recommended: it clears the exact live borrow-share balance, avoiding "dust" amounts left over from rounding.
- Collateral (`supplyCollateral` and `withdrawCollateral`) is always handled in `assets`.

## [Prerequisites](#prerequisites)

Before you begin, you will need:

- The `MarketParams` for the market you want to interact with. You can find active markets using the [Morpho API](https://docs.morpho.org/developers/borrow/tutorials/get-data/#markets-parameters).
- An account with a balance of the collateral asset (e.g., wstETH) and the loan asset (e.g., WETH for repayments).

## [Integrate with the Morpho SDK](#integrate-with-the-morpho-sdk)

For an end-to-end walkthrough of every market action this SDK exposes (supply collateral, borrow, atomic supply+borrow, repay by assets vs shares, withdraw collateral, atomic repay+withdraw, shared-liquidity reallocations) see the [**Blue subpage**](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/); the [Morpho SDK page](https://docs.morpho.org/developers/sdks/morpho-sdk/) covers the `getRequirements` flow, the builder = signer invariant, and error classes. For shared-liquidity implementation, use the [Vault V2 Public Allocator guide](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/).

### [Step 1: Install and set up the client](#step-1-install-and-set-up-the-client)

```
npm install @morpho-org/morpho-sdk@6.0.0 viem@^2.0.0
# or
pnpm add @morpho-org/morpho-sdk@6.0.0 viem@^2.0.0
# or
yarn add @morpho-org/morpho-sdk@6.0.0 viem@^2.0.0
```

```
import { createWalletClient, http, parseUnits } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { mainnet } from "viem/chains";
import { morphoViemExtension } from "@morpho-org/morpho-sdk";
import { MarketParams } from "@morpho-org/morpho-sdk/entities";

const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`);

const client = createWalletClient({
  account,
  chain: mainnet,
  transport: http(process.env.RPC_URL_MAINNET),
}).extend(morphoViemExtension({ supportSignature: true }));

const market = client.morpho.blue(
  new MarketParams({
    loanToken: "0xLoanToken...",
    collateralToken: "0xCollateralToken...",
    oracle: "0xOracle...",
    irm: "0xIrm...",
    lltv: 860000000000000000n, // 86%
  }),
  mainnet.id,
);
```

### [Step 2: Supply collateral & borrow (atomic)](#step-2-supply-collateral--borrow-atomic)

The SDK builds an atomic BlueBundlesV1 call that supplies collateral, then borrows, with an LLTV buffer that prevents the new position from being instantly liquidatable. `getRequirements()` returns the ERC-20 approval (or Permit/Permit2 signature) for the collateral token, plus the one-time `morpho.setAuthorization(blueBundlesV1, true)` if it has not been done yet.

```
const positionData = await market.getPositionData(account.address);

const supplyCollateralBorrow = market.supplyCollateralBorrow({
  collateralAssets: parseUnits("1.0", 18), // 1 wstETH
  borrowAssets: parseUnits("2000", 18),    // 2000 WETH
  userAddress: account.address,
  positionData,
  deadline: BigInt(Math.floor(Date.now() / 1000) + 3_600), // Unix seconds, now + 1 hour
});

const signatures = [];
for (const req of await supplyCollateralBorrow.getRequirements()) {
  if ("sign" in req) {
    signatures.push(await req.sign(client, account.address));
  } else {
    await client.sendTransaction(req); // approval / setAuthorization
  }
}

const txHash = await client.sendTransaction(supplyCollateralBorrow.buildTx(signatures));
console.log("Supply + borrow:", txHash);
```

### [Step 3: Repay & withdraw collateral (atomic)](#step-3-repay--withdraw-collateral-atomic)

For full repayments, pass `maxUint256` as the shares-mode repay input (`repayShares`): the contract replaces it with the position's live borrow shares, so the full debt is cleared regardless of interest accrued between quote and inclusion (no dust). Passing the position's freshly fetched `borrowShares` also works when the data is fresh. The operation order is encoded for you: repay first, then withdraw.

```
import { maxUint256 } from "viem";

const fresh = await market.getPositionData(account.address);

const repayWithdrawCollateral = market.repayWithdrawCollateral({
  repayShares: maxUint256,                   // full repay (saturated close; use { repayAssets } for partial)
  collateralAssets: parseUnits("1.0", 18),   // 1 wstETH
  userAddress: account.address,
  positionData: fresh,
  deadline: BigInt(Math.floor(Date.now() / 1000) + 3_600),
});

const signatures = [];
for (const req of await repayWithdrawCollateral.getRequirements()) {
  if ("sign" in req) {
    signatures.push(await req.sign(client, account.address));
  } else {
    await client.sendTransaction(req); // loan-token approval / setAuthorization
  }
}

const txHash = await client.sendTransaction(repayWithdrawCollateral.buildTx(signatures));
console.log("Repay + withdraw:", txHash);
```

Need to move an existing borrower from one Morpho Blue market to another with the same loan and collateral tokens? Use [`refinance()`](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/#refinance-to-another-morpho-blue-market) to migrate the full collateral and debt atomically, with optional shared liquidity from the [Vault V2 Public Allocator](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/) on the destination market.

For separate, non-atomic flows (e.g. `supplyCollateral` only, `borrow` only, `repay` only, `withdrawCollateral` only), see the equivalent action documented on the Morpho SDK's [Blue](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/) subpage.

[Rewards for Borrowers

Previous Page

](https://docs.morpho.org/developers/borrow/concepts/rewards/)[Get Data

Next Page

](https://docs.morpho.org/developers/borrow/tutorials/get-data/)