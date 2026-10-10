# Redeem lend at maturity

> Source: https://docs.morpho.org/developers/midnight/tutorials/redeem-lend-at-maturity

---

# Redeem lend at maturity

At maturity, credit units settle 1:1 with the loan token: each unit redeems for exactly one loan token, net of fees and losses the market accrued. Redemption is a direct `Midnight` call - no offers, no bundle, no approvals.

Snippets assume a [viem wallet client](https://viem.sh/docs/clients/wallet) `walletClient` for your account on Base, and `lender` set to your wallet address.

## [**Read the position**](#read-the-position)

The REST API is the quickest way to inspect the position. It returns the stored, indexed values and can lag a few blocks. To size the transaction, run the SDK read or the direct contract read: they return the live, accrued values that the next steps use.

### [REST API](#rest-api)

Fetch the lender's position to get the credit available to redeem:

```
GET https://api.morpho.org/v0/midnight/markets
  /{marketId}/users/{userAddress}/position

// Response
{
  "data": {
    "chain_id":           8453,
    "market_id":          "0xd92de5e7fbb...7614",               // market the lender lent into
    "user_address":       "0xYourWalletAddress",
    "last_indexed_block": "47457420",
    "loan_token":         "0x8335...2913",                      // USDC
    "maturity":           "1798761600",
    "type":               "lend",                               // "lend" | "borrow" | "collateral_only"
    "credit":             "10500000000",                        // stored credit - the redeemable amount comes from the accrued onchain read below
    "debt":               "0",
    "pending_fee":        "12000",                              // accrued fee, nets out of the payout
    "last_loss_factor":   "0",                                  // loss factor already applied to this position
    "loss_factor":        "0",                                  // current market loss factor (applies to credit on bad debt)
    "collaterals":        []                                    // lenders post no collateral
  }
}

// Inspection only - size the transaction from the SDK or direct contract read below.
```

### [SDK](#sdk)

The SDK reads the accrued position through `midnight.getPositionData`:

```
import { publicActions } from "viem";
import { morphoViemExtension } from "@morpho-org/morpho-sdk";

// Extend the wallet client with the `morpho` namespace and the public reads
// the flow needs (getBlock / waitForTransactionReceipt).
const client = walletClient.extend(morphoViemExtension()).extend(publicActions);
const midnight = client.morpho.midnight(8453); // Midnight entity for Base

// marketId = the market's id - from the REST API read above or the markets endpoint

// Fetch the position and accrue it to the current block's timestamp.
const block = await client.getBlock();
const positionData = (
  await midnight.getPositionData({
    marketId,
    accountAddress: lender,
    parameters: { blockNumber: block.number },
  })
).accrueInterest(block.timestamp);
// positionData.faceValue = accrued credit net of accrued pending fee - the
// full-redemption units the redeem flow defaults to (same as newCredit minus
// newPendingFee in the direct contract read below).

// Redemption is bounded by the market's withdrawable liquidity - the bound
// the redeem flow checks. Cap the full redemption at it.
const units =
  positionData.faceValue < positionData.market.withdrawable
    ? positionData.faceValue
    : positionData.market.withdrawable;
if (units === 0n) throw new Error("no withdrawable liquidity yet, retry later");
```

### [Onchain (direct contract read)](#onchain-direct-contract-read)

```
import { createPublicClient, http } from "viem";
import { base } from "viem/chains";
import { midnightAbi } from "@morpho-org/morpho-sdk/abis";

const MIDNIGHT = "0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A";   // Midnight on Base (from the @morpho-org/morpho-ts address registry)

const publicClient = createPublicClient({ chain: base, transport: http() });

// market = the Market struct - from GET /v0/midnight/markets/{marketId} or a prior browse step

// A full redemption uses the accrued redeemable credit - the same value the
// SDK redeems by default (positionData.faceValue): newCredit minus the accrued
// pending fee.
const [newCredit, newPendingFee] = await publicClient.readContract({
  address: MIDNIGHT,
  abi: midnightAbi,
  functionName: "updatePositionView",
  args: [market, marketId, lender],
});

// The market's withdrawable liquidity in units - the bound Midnight.withdraw
// enforces (the same value the SDK's redeem flow checks).
const withdrawable = await publicClient.readContract({
  address: MIDNIGHT,
  abi: midnightAbi,
  functionName: "withdrawable",
  args: [marketId],
});
const units =
  newCredit - newPendingFee < withdrawable ? newCredit - newPendingFee : withdrawable;
if (units === 0n) throw new Error("no withdrawable liquidity yet, retry later");
```

## [**Redeem**](#redeem)

You can redeem with the [Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/): its `redeem` flow checks the accrued position for you and builds a direct `Midnight.withdraw` transaction - no bundle and no requirements. Redemption is bounded by the market's `withdrawable` liquidity - the SDK throws `InsufficientMidnightWithdrawableLiquidityError` above it. A partial redemption leaves the rest redeemable later. The raw contract call below it is the manual equivalent.

### [**Morpho SDK**](#morpho-sdk)

Hand the flow the accrued `positionData` from the SDK position read above:

```
// `client`, `midnight`, `positionData` and `units` come from the SDK
// position read above - `units` is already capped at withdrawable liquidity.
const redeem = midnight.redeem({
  accountAddress: lender,
  positionData,
  receiver: lender,
  units,
});

// `redeem` returns no requirements and checks the accrued credit plus the
// market's withdrawable liquidity; `receiver` defaults to the owner and
// `units` is passed explicitly, already capped at withdrawable.
// The built transaction is a direct Midnight.withdraw call.
const hash = await client.sendTransaction(redeem.buildTx());
console.log("Redeem tx:", hash);
```

See [Position maintenance](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/#position-maintenance) for the full surface.

### [**Raw contract call**](#raw-contract-call)

Call `Midnight.withdraw` directly:

```
// `midnightAbi`, `MIDNIGHT`, `market` and `units` come from the onchain
// position read above.
const hash = await walletClient.writeContract({
  account: lender,
  address: MIDNIGHT,
  abi: midnightAbi,
  functionName: "withdraw",
  args: [
    market,   // Market struct
    units,    // credit units to redeem
    lender,   // onBehalf - whose credit is reduced
    lender,   // receiver - where the loan tokens go
  ],
});

// The call debits credit and the market's withdrawable liquidity - not
// gated on maturity; pre-maturity it succeeds only up to withdrawable -
// and redeems 1:1 net of accrued fees and losses.
console.log("Redeem tx:", hash);
```

[Borrow at a fixed rate

Previous Page

](https://docs.morpho.org/developers/midnight/tutorials/borrow-at-a-fixed-rate/)[Exit borrow at maturity

Next Page

](https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-by-repaying-in-full-at-maturity/)