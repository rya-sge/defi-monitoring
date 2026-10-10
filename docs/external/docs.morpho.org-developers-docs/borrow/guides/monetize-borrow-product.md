# Guide: How to Monetize Your Borrow Product

> Source: https://docs.morpho.org/developers/borrow/guides/monetize-borrow-product

---

# Guide: How to Monetize Your Borrow Product

Borrow products can monetize the integration layer around Morpho Markets while keeping the underlying protocol permissionless. The first pattern to consider is a **borrow origination fee**: a one-time fee paid in the loan token when a borrower opens or increases a borrow position.

This guide explains how the pattern works, where it can be implemented, and what builders must disclose, simulate, and secure before using it in production.

The referenced contracts in [`morpho-org/morpho-snippets`](https://github.com/morpho-org/morpho-snippets/tree/main/src/morpho-blue) are educational examples and have not been audited. Treat them as implementation references, not production-ready contracts.

## [What is a borrow origination fee?](#what-is-a-borrow-origination-fee)

A borrow origination fee is charged once, at borrow time. The borrower receives the requested net amount, while the fee recipient receives an additional amount of the same loan token.

For example, if a user wants to receive `1,000 USDC` and the origination fee is `200 bps`:

- `feeAmount = 1,000 USDC * 200 / 10,000 = 20 USDC`
- `totalBorrowed = 1,000 USDC + 20 USDC = 1,020 USDC`
- the borrower receives `1,000 USDC`
- the fee recipient receives `20 USDC`
- the borrower's Morpho debt is `1,020 USDC`, and interest accrues on `1,020 USDC`

This distinction is critical for UX: the fee is not separate from the debt. It consumes borrow capacity, changes the resulting LTV and health factor, and increases the amount that must later be repaid.

## [Where the fee lives](#where-the-fee-lives)

Morpho Blue does not enforce an application-level origination fee. The fee is implemented by the builder's transaction path around `Morpho.borrow`.

The core mechanics are:

```
uint256 feeAmount = userAssets * feeBps / 10_000;
uint256 totalBorrowed = userAssets + feeAmount;

morpho.borrow(marketParams, totalBorrowed, 0, onBehalf, receiver);
```

The two important `borrow` parameters are:

- `onBehalf`: the address whose borrow position increases.
- `receiver`: the address that receives the borrowed loan tokens.

A fee-charging integration borrows the gross amount, sends the net amount to the borrower, and routes the fee amount to the fee recipient.

## [Recommended: use the Bundles referral fee](#recommended-use-the-bundles-referral-fee)

The simplest way to charge an origination fee is to route the borrow through [Bundles](https://docs.morpho.org/developers/contracts/bundles/). `BlueBundlesV1` entrypoints such as `blueBundlesV1SupplyCollateralAndBorrow` take a `referralFeePct` (WAD-scaled) and a `referralFeeRecipient`: the Bundle borrows the gross amount on behalf of the user, sends `fee = (borrowAssets - penalties) * referralFeePct / WAD` to the recipient and the remainder to the borrower, atomically. No custom router or delegation contract is needed, and the user only authorizes the audited Bundle contract.

To deliver a net amount `W` to the borrower, pass `borrowAssets = penalties + floor(W * WAD / (WAD - referralFeePct))`, where `penalties` is the sum of public allocator penalties for the reallocations included in the call (zero when none).

Because `floor(W * WAD / (WAD - referralFeePct))` rounds down and the fee `floor((borrowAssets - penalties) * referralFeePct / WAD)` also rounds down, the two roundings cancel and the borrower receives exactly `W` in token units. Note that `referralFeePct` is a share of the gross post-penalty proceeds, not a markup on the net amount like `feeBps` in the example above, so the same nominal rate yields a slightly larger fee. Worked example with `W = 1,000 USDC` (`1_000_000_000` units), `referralFeePct = 0.02e18` (2%, i.e. 200 bps of gross) and no penalties:

- `borrowAssets = floor(1_000_000_000 * 1e18 / 0.98e18) = 1_020_408_163` (1,020.408163 USDC)
- `fee = floor(1_020_408_163 * 0.02e18 / 1e18) = 20_408_163` (20.408163 USDC)
- the borrower receives `1_020_408_163 - 20_408_163 = 1_000_000_000` (exactly 1,000 USDC)

To reproduce the additive `feeBps` convention (fee = `net * feeBps / 10_000`), use `referralFeePct = feeBps * WAD / (10_000 + feeBps)`.

The [Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/) exposes the same two parameters (`referralFeePct`, `referralFeeRecipient`) on every market write, so a fee can be added to an existing SDK integration by setting them. The same fields are available on repay, supply, borrow-position migration, and vault deposit, withdraw and migration entrypoints, so a product can monetize those flows too.

## [Implementation patterns](#implementation-patterns)

When Bundles do not fit your product (for example a smart-account flow that must control execution itself), there are two other ways to implement the pattern.

| Pattern | Use when | How it works | Main risk to manage |
| --- | --- | --- | --- |
| Account-level execution, such as a smart wallet or EIP-7702 delegated EOA | Your product controls the user's account execution flow | The user account executes an atomic call that borrows the gross amount, keeps the net amount, and transfers the fee | The account policy or delegation must tightly restrict `feeBps`, `feeRecipient`, market, amount, and calldata |
| EOA plus authorized router | The user uses a regular EOA and cannot execute custom account logic | The user authorizes a router with `morpho.setAuthorization(router, true)`. The router borrows on behalf of the user, receives the loan token, then transfers net amount and fee | The authorized router can increase the user's borrow position while authorization remains active, so authorization should be as short-lived as possible and the router must be minimal, audited, and easy to revoke |

The educational snippets illustrate both approaches:

- [`OriginationFeeExecutor.sol`](https://github.com/morpho-org/morpho-snippets/blob/main/src/morpho-blue/OriginationFeeExecutor.sol) shows an account-level EIP-7702 delegation target. The delegated EOA is the borrower and the receiver of the net borrowed assets.
- [`OriginationFeeSnippets.sol`](https://github.com/morpho-org/morpho-snippets/blob/main/src/morpho-blue/OriginationFeeSnippets.sol) shows an owner-managed router. The EOA must authorize the router on Morpho before borrowing through it.

## [Production checklist](#production-checklist)

Before shipping a borrow origination fee, make the fee explicit and verifiable.

### [User disclosure](#user-disclosure)

Show the user, before signature:

- net amount received by the borrower;
- origination fee amount and recipient;
- gross debt opened on Morpho;
- resulting LTV or health factor after the fee;
- estimated liquidation price or liquidation risk, if your product shows it;
- repayment implication: interest accrues on the gross debt, not only the net amount received.

Do not present the requested amount as the full debt if the transaction borrows `requested amount + fee`.

### [Simulation and risk checks](#simulation-and-risk-checks)

The transaction should be simulated with the gross borrow amount. Check that:

- the market has enough liquidity for `totalBorrowed`;
- the borrower has enough collateral for `totalBorrowed`, not only `userAssets`;
- the position remains healthy after the fee;
- the fee calculation handles token decimals and rounding consistently;
- the fee recipient can receive and handle the loan token, including any follow-up transfer or recovery flow your product requires;
- repayment and position displays use the actual borrow shares and accrued debt.

### [Contract controls](#contract-controls)

If fees are enforced by a contract, keep the trust surface small:

- cap `feeBps` in the contract;
- reject zero fee recipients and invalid fee values;
- emit an event with borrower, market id, net amount, and fee amount;
- use `SafeERC20` or equivalent checked wrappers for ERC-20 transfers;
- avoid unnecessary upgradeability and mutable configuration;
- protect fee configuration with a multisig, timelock, or immutable deployment, depending on your trust model;
- test interest accrual on the gross debt, insufficient-collateral reverts, zero-amount behavior, and authorization revocation.

### [Authorization safety](#authorization-safety)

For the router pattern, `morpho.setAuthorization(router, true)` is powerful. The router can act on behalf of the user for Morpho actions while it remains authorized.

A production router should therefore:

- expose only the methods needed by your product;
- keep fee parameters bounded and transparent;
- never borrow to an arbitrary receiver controlled by an attacker;
- for `setAuthorizationWithSig` or any other signature-based permission, bind the signature or policy to the intended chain ID and use the shortest practical deadline;
- keep router authorization active only for as long as necessary, and make revocation clear in the UI;
- be audited before handling user positions.

For smart-wallet or EIP-7702 flows, apply the same principle to session keys, account policies, and delegation payloads. The signed permission should be as narrow as possible: exact action, market, amount, fee cap, recipient, deadline, and chain ID.

## [Important limitations](#important-limitations)

An origination fee at the integration layer does not make the underlying Morpho market permissioned. Users can still interact with Morpho directly or through another integration and bypass your fee. This pattern monetizes your product flow, not the protocol itself.

Use it only when the user receives clear value from your borrow product, such as distribution, onboarding, risk tooling, account abstraction, sponsored gas, or portfolio management.

[Integrate Rewards for Borrow Products

Previous Page

](https://docs.morpho.org/developers/borrow/tutorials/rewards/)[Resources

Next Page

](https://docs.morpho.org/developers/borrow/resources/all/)