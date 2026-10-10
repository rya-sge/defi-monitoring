# Exit borrow at maturity

> Source: https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-by-repaying-in-full-at-maturity

---

# Exit borrow at maturity

Snippets assume a [viem wallet client](https://viem.sh/docs/clients/wallet) `walletClient` for your account on Base, and `borrower` set to your wallet address.

## [**Read outstanding debt & collateral**](#read-outstanding-debt--collateral)

In order to exit your position at maturity, repay your debt in full. Collateral can only be released in full once the debt is fully repaid. To fetch a user's outstanding debt and locked collateral, use the following query:

```
GET https://api.morpho.org/v0/midnight/markets
  /{marketId}/users/{userAddress}/position

// Response
{
  "data": {
    "chain_id":           8453,
    "market_id":          "0xd92de5e7fbb...7614",                // market the borrower borrowed from
    "user_address":       "0xYourWalletAddress",
    "last_indexed_block": "47457420",
    "loan_token":         "0x8335...2913",                       // USDC
    "maturity":           "1798761600",
    "type":               "borrow",                              // "lend" | "borrow" | "collateral_only"
    "credit":             "0",                                   // lender side (0 for a borrower)
    "debt":               "10527000000",                         // outstanding debt to clear
    "pending_fee":        "0",                                   // lender-side fee (0 for a borrower; not part of the debt)
    "last_loss_factor":   "0",
    "loss_factor":        "0",
    "collaterals": [                                             // each entry is { token, amount }
      {
        "token":  "0x4200000000000000000000000000000000000006",  // WETH
        "amount": "5000000000000000000"                          // 5 WETH (18 dec)
      }
    ]
  }
}
```

Positions with zero credit and debt but non-empty collaterals are returned as `type`: "collateral_only".

## [Repay & withdraw collateral](#repay--withdraw-collateral)

A full collateral withdrawal only succeeds once the position's debt is zero. If accrual leaves even 1 unit unpaid, the withdrawal of the corresponding collateral reverts (it would push the position under its LLTV). Over-approving slightly plus a small repay buffer is what makes the at-maturity exit reliably clean.

The recommended path is the [Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/): it derives the USDC approval and the one-time `MidnightBundles` authorization for you and builds the atomic repay + withdraw bundle. The raw contract call below it is the manual equivalent.

### [**Morpho SDK**](#morpho-sdk)

Extend `walletClient` and reuse the position read from the previous step:

```
import { parseUnits, publicActions } from "viem";
import { morphoViemExtension } from "@morpho-org/morpho-sdk";

// Extend the wallet client with the `morpho` namespace and the public reads
// the flow needs (getBlock / waitForTransactionReceipt).
const client = walletClient.extend(morphoViemExtension()).extend(publicActions);
const midnight = client.morpho.midnight(8453);

const marketId = position.market_id; // from "Read outstanding debt & collateral"

// Fresh, same-block market snapshot.
const block = await client.getBlock();
const marketData = await midnight.getMarketData(marketId, {
  blockNumber: block.number,
});

// Full obligation = debt. `pending_fee` is lender-side and isn't repaid by a borrower.
const repayAssets = BigInt(position.debt);

// Release the full WETH balance. `collateralIndex` defaults to 0n - the
// market's first configured collateral.
const withdrawCollateralAssets = BigInt(position.collaterals[0].amount);

// Deadline: the transaction reverts if not included before this timestamp
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600); // 1 hour from now

// Repay and withdraw atomically in one MidnightBundles bundle.
const repayWithdrawCollateral = midnight.repayWithdrawCollateral({
  accountAddress: borrower,
  marketData,
  repayAssets,
  withdrawCollateralAssets,
  deadline,
});

// Requirements are plain transactions - the USDC approval to MidnightBundles
// (returned only while repayAssets > 0) plus the one-time MidnightBundles
// authorization. Send each and wait for its receipt.
for (const requirement of await repayWithdrawCollateral.getRequirements()) {
  const hash = await client.sendTransaction(requirement);
  await client.waitForTransactionReceipt({ hash });
}

const hash = await client.sendTransaction(repayWithdrawCollateral.buildTx());
console.log("Repay + withdraw tx:", hash);
```

See [Position maintenance](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/#position-maintenance) for the full surface, including `redeem` and `cancelOffer`.

### [**Raw contract call: Authorizations & Approvals**](#raw-contract-call-authorizations--approvals)

**Prerequisites**

The borrower must have:

1. Authorized `MidnightBundles` on the Midnight contract (so it can act on the positio on their behalf).
2. Approved `MidnightBundles` to pull the loan token

Pick between Path 1, Path 2, or Path 3 depending on your UX and signing needs.

```
import {
  erc20Abi, createPublicClient, encodeAbiParameters, parseAbiParameters, parseSignature, parseUnits, http,
} from "viem";
import { base } from "viem/chains";

const MIDNIGHT_BUNDLES = "0x091183d729BE9f808c212b475E387A12E67850A7";   // MidnightBundles on Base (from the @morpho-org/morpho-ts address registry)
const MIDNIGHT         = "0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A";   // Midnight on Base (from the registry)
const USDC            = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913";    // USDC on Base

// Full obligation = debt (`pending_fee` is lender-side)
const debtAssets = BigInt(position.debt);

// Approve a bit more than the debtAssets. Any accrual between reading and executing could leave dust that blocks full collateral release.
const approveAmount = debtAssets + parseUnits("1", 6);

// Path 1: approve()
// 1. Let MidnightBundles pull USDC 
// 2. Set limit based on approveAmount computed above
await walletClient.writeContract({
  account: borrower, address: USDC, abi: erc20Abi,
  functionName: "approve", args: [MIDNIGHT_BUNDLES, approveAmount],
});

// Variable to set loanTokenPermit later in bundler argument
const tokenPermitNone = { kind: 0, data: "0x" } as const;

// --------------------------------------------------------------

// Path 2: EIP-2612
// Authorize exactly the USDC you'll spend buying units
const publicClient = createPublicClient({ chain: base, transport: http() });

// Ceiling you authorize via the permit: debt plus a small buffer
// Same as "approveAmount" defined above for the approval flow
const permitValue = BigInt(position.debt) + parseUnits("1", 6);
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

// Read the owner's current EIP-2612 nonce from the token.
const nonce = await publicClient.readContract({
  address: USDC,
  abi: [{ name: "nonces", type: "function", stateMutability: "view",
          inputs: [{ name: "owner", type: "address" }],
          outputs: [{ type: "uint256" }] }],
  functionName: "nonces",
  args: [borrower],
});

// Offchain signature (no transaction, no gas)
const sig = await walletClient.signTypedData({
  account: borrower,
  domain: { name: "USD Coin", version: "2", chainId: 8453, verifyingContract: USDC },
  types: { Permit: [
    { name: "owner",    type: "address" },
    { name: "spender",  type: "address" },
    { name: "value",    type: "uint256" },
    { name: "nonce",    type: "uint256" },
    { name: "deadline", type: "uint256" },
  ] },
  primaryType: "Permit",
  message: { owner: borrower, spender: MIDNIGHT_BUNDLES,
             value: permitValue, nonce, deadline },
});

const { r, s, v } = parseSignature(sig);

// Variable to set the loanTokenPermit variable to (bundler argument) in the Execute step that follows 
const loanTokenPermitEIP2612 = {
  kind: 1,                                                                 // 1 = ERC2612
  data: encodeAbiParameters(
    parseAbiParameters("uint256 deadline, uint8 v, bytes32 r, bytes32 s"),
    [deadline, Number(v), r, s],
  ),
} as const;

// --------------------------------------------------------------

// Path 3: Permit2
// One-time setup (once per token, ever): approve Permit2 on USDC
const PERMIT2 = "0x000000000022D473030F116dDEE9F6B43aC78BA3";              // canonical, same on every chain
const repayCeiling = BigInt(position.debt) + parseUnits("1", 6);

// One-time setup (once per token, ever): approve Permit2 on USDC.
await walletClient.writeContract({
  account: borrower, address: USDC, abi: erc20Abi,
  functionName: "approve", args: [PERMIT2, maxUint256],
});

// Per-repay: sign a Permit2 SignatureTransfer (offchain, no gas).
const nonce    = BigInt(Date.now());                                       // unordered nonce (Permit2 uses a bitmap)
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);

const sig = await walletClient.signTypedData({
  account: borrower,
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
    permitted: { token: USDC, amount: repayCeiling },
    spender: MIDNIGHT_BUNDLES,
    nonce,
    deadline,
  },
});

// Variable to set the loanTokenPermit variable to (bundler argument) in the Execute step that follows 
const loanTokenPermit2 = {
  kind: 2,                                                                 // 2 = Permit2
  data: encodeAbiParameters(
    parseAbiParameters("uint256 nonce, uint256 deadline, bytes signature"),
    [nonce, deadline, sig],
  ),
} as const;

// --------------------------------------------------------------

// Authorize MidnightBundles to act on your position (one-time boolean, persists across future actions)
await walletClient.writeContract({
  account: borrower,
  address: MIDNIGHT,
  abi: midnightAbi,
  functionName: "setIsAuthorized",
  args: [MIDNIGHT_BUNDLES, true, borrower],
});
```

### [**Raw contract call: Execute onchain**](#raw-contract-call-execute-onchain)

```
import { midnightBundlesAbi } from "@morpho-org/morpho-sdk/abis";
import { zeroAddress } from "viem";

// Release the full balance of each collateral:
// The position lists collateral by { token, amount } and the contract wants an INDEX into market.collateralParams[], so resolve token → index here.
const collateralWithdrawals = position.collaterals.map((c: any) => ({
  collateralIndex: BigInt(
    market.collateralParams.findIndex(
      (cp: any) => cp.token.toLowerCase() === c.token.toLowerCase()
    )
  ),
  assets: BigInt(c.amount),
}));

const repayAssets = BigInt(position.debt);

// Deadline: the transaction reverts if not included before this timestamp
const deadline = BigInt(Math.floor(Date.now() / 1000) + 3600);               // 1 hour from now

const hash = await walletClient.writeContract({
  account: borrower,
  address: MIDNIGHT_BUNDLES,
  abi: midnightBundlesAbi,
  functionName: "midnightBundlesV1RepayAndWithdrawCollateral",
  args: [
    market,                 // Market struct (fetch via GET /v0/midnight/markets/{marketId} or reuse from browsing)
    repayAssets,            // loan tokens to repay (full debt)
    borrower,               // onBehalf - whose position is repaid
    tokenPermitNone,        // if Permit EIP-2612 or Permit2 is used use loanTokenPermitEIP2612 or loanTokenPermit2, respectively
    collateralWithdrawals,  // CollateralWithdrawal[] (release all collateral)
    borrower,               // collateralReceiver (where the WETH is sent)
    0n,                     // referralFeePct (0 = none)
    zeroAddress,            // referralFeeRecipient (none)
    deadline               // deadline (reverts if tx is included after this timestamp)
  ],
});

console.log("Repay + withdraw tx:", hash);
```

[Redeem lend at maturity

Previous Page

](https://docs.morpho.org/developers/midnight/tutorials/redeem-lend-at-maturity/)[Exit lend early

Next Page

](https://docs.morpho.org/developers/midnight/tutorials/exit-lend-early/)