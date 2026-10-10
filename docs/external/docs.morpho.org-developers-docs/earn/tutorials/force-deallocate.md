# Support forceDeallocate withdrawals

> Source: https://docs.morpho.org/developers/earn/tutorials/force-deallocate

---

# Support forceDeallocate withdrawals

A Morpho Vault V2 serves a withdrawal from two sources only: its idle balance and its liquidity adapter (an underlying market). Assets allocated to any other market of the adapter are not reachable by a plain `withdraw()` or `redeem()`, even when that market has liquidity. `forceDeallocate` is the permissionless function that moves those assets back into the idle balance, so a withdrawal can be served in the same transaction.

Integrations that do not support `forceDeallocate` can show a smaller withdrawable amount than integrations that do, for the same vault and the same user. This guide explains the liquidity flow behind that gap and how to close it.

This page and its examples assume a Vault V2 that uses a single `MorphoMarketV1AdapterV2` adapter, holding positions in one or more Morpho markets.

This page covers exits into the vault's underlying asset. When the underlying markets themselves lack liquidity (all assets are borrowed), no `forceDeallocate` can help. Use [in-kind redemption](https://docs.morpho.org/developers/earn/tutorials/in-kind-redemption/) instead, which transfers the user's position from the vault to the underlying market.

## [How Vault V2 liquidity flows](#how-vault-v2-liquidity-flows)

Every Vault V2 has an optional `liquidityAdapter` and `liquidityData` pair set by the allocator. Together they name one adapter and one position inside it (for a `MorphoMarketV1AdapterV2`, one Morpho market). The vault routes entries and exits through this pair.

![Vault V2 liquidity flow: deposits allocate to the liquidity adapter, withdrawals are served from idle then the liquidity adapter, forceDeallocate moves assets from other markets back to idle](https://docs.morpho.org/img/earn/vault-v2-liquidity-flow.png)

| Operation | What the vault does |
| --- | --- |
| `deposit` / `mint` | Transfers the assets in. If a liquidity adapter (an underlying market) is set, allocates the full amount to it; otherwise the assets stay idle. |
| `withdraw` / `redeem` | Pays from the idle balance first. If the amount exceeds idle, deallocates the remainder from the liquidity adapter. With no liquidity adapter set, idle is the only source. |
| `forceDeallocate` | Moves `assets` from any market of the adapter into the idle balance and burns a penalty in shares from `onBehalf`. Does not transfer assets to the caller. |

Two constraints follow from this design:

- **Withdrawal ceiling**: the amount a plain withdrawal can serve is `idle + liquidity available to the vault through the liquidity adapter`. The allocator raises this ceiling by reallocating, but between two reallocations it can sit below what a user is owed.
- **Deposit ceiling**: a deposit allocates its whole amount to the liquidity adapter, so the vault's absolute and relative caps on that adapter's market bound deposits. When the liquidity adapter is at cap, `deposit` reverts with `AbsoluteCapExceeded` or `RelativeCapExceeded`. With no liquidity adapter set, deposits stay idle and no allocation cap applies.

The [Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/) exposes both ceilings on `AccrualVaultV2` from `@morpho-org/blue-sdk`: `maxWithdraw(shares)` returns the assets a plain withdrawal can serve for a share amount, capped by idle plus liquidity-adapter capacity, and `maxDeposit(assets)` applies the liquidity adapter's capacity and every allocation cap. Both return a `CapacityLimit` with a `value` and the `limiter` that binds. Read these instead of the ERC-4626 `maxWithdraw` / `maxDeposit` view functions, which [always return zero](https://docs.morpho.org/developers/contracts/morpho-vaults-v2/#maxdeposit) on Vault V2.

Which adapter and market serve as the liquidity adapter, how often the allocator reallocates, and the per-adapter penalty are all set by the vault's curator and allocator, not by the integrator. This is why the same integration can behave differently from one vault to the next. [Liquidity curation](https://docs.morpho.org/curate/tutorials-v2/liquidity-curation/) describes these choices from the curator's side.

## [What `forceDeallocate` costs](#what-forcedeallocate-costs)

```
function forceDeallocate(address adapter, bytes memory data, uint256 assets, address onBehalf) external returns (uint256)
```

The call deallocates `assets` from `adapter` (identified inside the adapter by `data`, the encoded market params for a Morpho market adapter) into the idle balance. It then withdraws `penaltyAssets = ceil(assets × forceDeallocatePenalty[adapter] / 1e18)` from `onBehalf` back into the vault, which burns the matching shares. The penalty stays in the vault and accrues to the remaining depositors. It is not paid to the caller, curator, or any fee recipient.

| Penalty | Effect for the user |
| --- | --- |
| `0` | No shares burned. Deallocating is free and the full deallocated amount becomes withdrawable. |
| `p > 0` (max `0.02e18`, 2%) | For every `D` assets deallocated, the user loses `ceil(D × p / 1e18)` assets worth of shares. |

The penalty is set **per adapter** by the curator through `setForceDeallocatePenalty` and read with [`forceDeallocatePenalty(adapter)`](https://docs.morpho.org/developers/contracts/morpho-vaults-v2/#forcedeallocatepenalty). With a single adapter, one rate `p` applies to every market. The SDK hydrates it in `AccrualVaultV2.forceDeallocatePenalties`, keyed by adapter address. Read the penalty before every plan: a curator can change it under timelock.

## [Decide whether to support it](#decide-whether-to-support-it)

| Integration | Withdrawable amount shown | Trade-off |
| --- | --- | --- |
| Plain `withdraw` / `redeem` only | `maxWithdraw(userShares)`: idle plus the liquidity adapter | Simple. Users can be blocked from a full exit until the allocator reallocates, even though the vault is solvent and its markets are liquid. |
| Plain withdrawal plus `forceDeallocate` | `maxWithdraw(userShares)` plus the adapter's other markets' available liquidity, minus penalties | Full exit whenever the underlying markets are liquid. Requires a deallocation plan and a penalty disclosure in the UI. |

Support `forceDeallocate` if you show a "max" withdrawal or let users exit their full position. Without it, your maximum disagrees with integrations that support it, and users see their funds as stuck when they are not.

## [Plan the deallocations](#plan-the-deallocations)

Given a requested `inputAmount` of assets and `availableNormalWithdraw = vaultData.maxWithdraw(maxUint256).value`:

1. If `inputAmount <= availableNormalWithdraw`, use a plain [withdrawal](https://docs.morpho.org/developers/earn/tutorials/assets-flow/). Do not force-deallocate: it would charge a penalty nobody owes.
2. Otherwise compute `shortfall = inputAmount - availableNormalWithdraw` and cover it from the adapter's other markets.

If you use the SDK's `forceWithdraw`, `previewVaultV2ForceWithdraw` performs this plan for you. Read on if you build the deallocation list yourself, for example for `forceRedeem` or a raw `multicall`.

### [Step 1: Compute per-market capacity](#step-1-compute-per-market-capacity)

For each market the adapter holds a position in, other than the liquidity market (its available assets are already counted in `availableNormalWithdraw`):

- `capacity = min(vault supply in that market, market liquidity)`.

Each candidate is `{ adapter, marketParams, capacity }`. Read the adapter's penalty `p` once; it applies to every leg.

### [Step 2: Cover the shortfall, largest market first](#step-2-cover-the-shortfall-largest-market-first)

Sort candidates by descending capacity. Walk the list and accumulate coverage until it reaches the shortfall.

A deallocation of `D` covers `D + ceil(D × p / 1e18)` of the shortfall: `D` lands in idle and is withdrawn, and the penalty is value the user no longer needs the vault to pay out. So:

- Take a market's full `capacity` while its coverage does not bridge the remaining gap.
- On the boundary market, take the smallest `D` with `D + ceil(D × p / 1e18) >= remaining`. Start from `D = ceil(remaining × 1e18 / (1e18 + p))` and check whether `D - 1` still satisfies the inequality (at most one step, because both roundings go up).
- For a full exit (share path), add a drift buffer to that boundary leg: `amount = min(D + buffer, capacity)` with `buffer = max(ceil(inputAmount / 10_000), 1)` (0.01% of the exit, at least 1 wei). Interest accrues between the plan and execution, so the shares redeem for slightly more assets than `inputAmount`; without the buffer the vault comes up a few wei short and the whole multicall reverts. If `capacity` clips the buffer, the plan tolerates less drift. The surplus lands in idle and stays in the vault.

If the accumulated coverage never reaches the shortfall, the exit cannot be served in the asset. Offer an [in-kind redemption](https://docs.morpho.org/developers/earn/tutorials/in-kind-redemption/) or a partial withdrawal instead.

The output is a list of `{ adapter, marketParams, amount, penaltyAssets }`, with `penaltyAssets = ceil(amount × p / 1e18)` per leg computed from the `amount` actually submitted (buffer included), plus `totalPenaltyAssets = Σ penaltyAssetsᵢ`.

The contract documents the optimal amount for a fully illiquid vault: to exit `A` assets, force-deallocate `min(market liquidity, A / (1 + penalty))` from the market. The plan above is the multi-market version of that rule.

### [Step 3: Size the final withdrawal](#step-3-size-the-final-withdrawal)

The penalty burns shares from the user, so the assets they can still withdraw shrink by `totalPenaltyAssets`:

- Asset path: `withdraw.amount = inputAmount - totalPenaltyAssets`.
- Share path (full exit): `redeem.shares = userShares - penaltyShares`, where `penaltyShares = Σ previewWithdraw(penaltyAssetsᵢ)` summed per deallocation leg, since the contract rounds each burn up separately. Accrued interest makes each burn cost slightly fewer shares than previewed, so a few wei of shares can remain after the exit.

Show the user three numbers before they sign: the amount they receive, the penalty in assets, and the effective penalty rate.

## [Build the transaction](#build-the-transaction)

The [Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/#force-withdraw--force-redeem) offers two routes: `forceWithdraw`, which goes through the `VaultExitBundlesV1` contract, and `forceRedeem`, which chains `forceDeallocate` calls and one `redeem` inside the vault's native `multicall`. Both execute atomically.

### [Asset-based exit with `forceWithdraw`](#asset-based-exit-with-forcewithdraw)

For a vault with a single adapter, the SDK does the planning for you. `previewVaultV2ForceWithdraw` computes, without any RPC, the largest exit the current state supports and what a given exit delivers; `forceWithdraw` then routes through `VaultExitBundlesV1`, which sizes the deallocations across the adapter's markets itself. `exitAssets` is penalty-inclusive: it is what the user's position is debited; `netAssets` is what they receive.

```
import { previewVaultV2ForceWithdraw } from "@morpho-org/morpho-sdk";

// `client` is a viem wallet client extended with `morphoViemExtension`,
// set up as in the assets-flow tutorial.
const vault = client.morpho.vaultV2(vaultV2Address, chainId);
const vaultData = await vault.getData();

const preview = previewVaultV2ForceWithdraw(vaultData, {
  requestedExitAssets: inputAmount,
  timestamp: BigInt(Math.floor(Date.now() / 1000)),
  userAddress,
});
// preview.maxExitAssets     -> cap for the input field
// preview.penaltyAssets     -> penalty to disclose
// preview.netAssets         -> what the user receives
// preview.remainingExitAssets > 0n -> the requested amount is not fully serviceable

const forceWithdraw = vault.forceWithdraw({
  exitAssets: preview.exitAssets,
  vaultData,
  userAddress,
});

const requirements = await forceWithdraw.getRequirements();
// Resolve approvals and permit signatures exactly as for a plain withdrawal.
const tx = forceWithdraw.buildTx(signatures);
```

`getRequirements()` resolves the vault-share allowance (approval or ERC-2612 permit) for the shares the bundle burns: the exit plus its penalty. Use the current time as `timestamp`, never a future one: market accrual grows the adapter's position, so a forward timestamp reports a `maxExitAssets` the contract will reject.

### [Share-based exit with `forceRedeem`](#share-based-exit-with-forceredeem)

Use `forceRedeem` when you need a share-exact full exit or want to choose which markets are tapped. It takes your plan as-is: a caller-supplied `deallocations` list followed by a single `redeem`, encoded inside the vault's `multicall`. No approval or signature is needed because the user calls the vault directly and `onBehalf` is the user.

```
import { erc20Abi, maxUint256 } from "viem";

// `client` is a viem wallet client extended with `morphoViemExtension`,
// set up as in the assets-flow tutorial.
const vault = client.morpho.vaultV2(vaultV2Address, chainId);
const vaultData = await vault.getData();

const userShares = await client.readContract({
  address: vaultV2Address,
  abi: erc20Abi,
  functionName: "balanceOf",
  args: [userAddress],
});

const availableNormalWithdraw = vaultData.maxWithdraw(maxUint256).value;
const userAssets = vaultData.toAssets(userShares);

if (userAssets <= availableNormalWithdraw) {
  // No shortfall, so no penalty: serve the exit with the plain `vault.redeem`
  // flow from the assets-flow tutorial and skip the rest of this snippet.
  return redeemAllShares(vault, userShares, userAddress);
}

// `planDeallocations` implements the three steps above, including the drift
// buffer on the boundary leg, and returns
// `{ deallocations: { adapter, marketParams, amount, penaltyAssets }[], totalPenaltyAssets }`,
// or `null` when the adapter's other markets cannot cover the shortfall.
const plan = planDeallocations({
  inputAmount: userAssets,
  availableNormalWithdraw,
  vaultData,
});

if (plan === null) {
  throw new Error("Shortfall not coverable with forceDeallocate; offer in-kind redemption");
}

const penaltyShares = plan.deallocations.reduce(
  (acc, d) => acc + vaultData.toShares(d.penaltyAssets, "Up"),
  0n,
);

const forceRedeem = vault.forceRedeem({
  deallocations: plan.deallocations.map(({ adapter, marketParams, amount }) => ({
    adapter,
    marketParams,
    amount,
  })),
  redeem: { shares: userShares - penaltyShares },
  userAddress,
});

const tx = forceRedeem.buildTx();
await client.call({ account: userAddress, ...tx }); // simulate first
const hash = await client.sendTransaction(tx);
```

Points to keep in mind:

- The SDK validates a non-empty list and positive amounts. It does not check that the deallocations cover the redeem, that each amount fits its market's capacity, or that the user holds enough shares for the penalty. Simulate before sending.
- Deallocating more than the withdrawal needs is safe, as long as each leg stays within its market's capacity: the surplus lands in idle, stays in the vault, and the allocator can re-allocate it. It is charged the penalty like any other deallocated amount, so always derive `penaltyAssets` and `penaltyShares` from the amounts you actually submit, buffer included.

### [Without the SDK](#without-the-sdk)

Encode the calls yourself and send them through the vault's `multicall(bytes[])`:

1. For each planned leg, `forceDeallocate(adapter, abi.encode(marketParams), amount, user)`.
2. Then `redeem(shares, user, user)` or `withdraw(assets, user, user)`.

`onBehalf` must be the user for the penalty burn. If a contract calls on the user's behalf, it needs vault-share allowance for the penalty shares.

## [Zero-penalty vaults](#zero-penalty-vaults)

When the adapter's penalty is `0`, the plan degenerates to "deallocate the shortfall, largest market first" (plus the drift buffer on a full exit) and `totalPenaltyAssets` is `0`. Curators who follow the [liquidity curation](https://docs.morpho.org/curate/tutorials-v2/liquidity-curation/) guide set the penalty to zero on the `MorphoMarketV1AdapterV2`, so for those vaults the full underlying liquidity is withdrawable at no cost. Keep the penalty read in your code anyway: the same code path handles a non-zero penalty the day the curator changes it.

## [Display checklist](#display-checklist)

- Compute the withdrawable maximum as `maxWithdraw(userShares).value + Σ coverage of the plan`, capped at the user's position. This is penalty-inclusive, the amount debited from the position (the SDK's `maxExitAssets`). Show it as the user's "max" together with the amount they receive, which is that maximum minus the penalty (`netAssets`).
- When the requested amount exceeds `availableNormalWithdraw`, label the transaction as force-deallocating and show the penalty in assets and as a rate.
- Rebuild the plan from a fresh vault snapshot right before signing. Liquidity in the markets, the penalty, and the liquidity adapter can all change between quote and execution.
- When the plan cannot cover the shortfall, point the user to a partial withdrawal or to [in-kind redemption](https://docs.morpho.org/developers/earn/tutorials/in-kind-redemption/).

[Depositing & Withdrawing from Vaults

Previous Page

](https://docs.morpho.org/developers/earn/tutorials/assets-flow/)[Exit an illiquid vault in kind

Next Page

](https://docs.morpho.org/developers/earn/tutorials/in-kind-redemption/)