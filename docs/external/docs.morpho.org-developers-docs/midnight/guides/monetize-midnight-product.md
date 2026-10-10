# Guide: How to Monetize Your Midnight Product

> Source: https://docs.morpho.org/developers/midnight/guides/monetize-midnight-product

---

# Guide: How to Monetize Your Midnight Product

Products built on Midnight can monetize the integration layer around fixed-rate markets while the protocol stays permissionless. The built-in pattern is the **referral fee** of [`MidnightBundlesV1`](https://github.com/morpho-org/bundles/blob/34a12c68c2e638ae872f525a8226dbc92ccd1a30/src/midnight/MidnightBundlesV1.sol): a one-time fee, paid in the loan token to an address you choose, taken in the same transaction as the trade.

This guide explains which fees belong to the protocol and which to your product, how the referral fee is computed on each Bundles entrypoint, and what to disclose, simulate, and guard before shipping it.

Midnight's [settlement and continuous fees](https://docs.morpho.org/developers/midnight/concepts/fees/) are protocol fees. They are set per market within protocol-wide caps, they are paid to the protocol, and an integrator cannot raise them or redirect them. Monetization lives one layer up, in the Bundles call your product builds.

## [Protocol fees versus your fee](#protocol-fees-versus-your-fee)

| Fee | Who sets it | Who pays it | Who receives it |
| --- | --- | --- | --- |
| Settlement fee | Market parameter, capped | The taker, as a spread on the settlement price | The protocol |
| Continuous fee | Market parameter, capped at 1% annualized | Lenders, netted from their credit over time | The protocol |
| Referral fee | Your product, in the Bundles calldata (`referralFeePct`) | The taker or repayer using your product | `referralFeeRecipient`, an address you choose |

The referral fee is on top of the settlement fee. A borrower using your product pays both when both are set. No Midnight market has a settlement or continuous fee activated today, so at the time of writing the referral fee is the only fee a user of your product pays.

## [How the referral fee works](#how-the-referral-fee-works)

The five `MidnightBundlesV1` trade and repay entrypoints listed below take two fee parameters:

- `referralFeePct`: a WAD-scaled percentage (`1e18 = 100%`), strictly below `WAD`. Pass `0` for no fee.
- `referralFeeRecipient`: the address that receives the fee. It is only used when the fee is positive.

Bundles takes the offers, applies the fee to the loan-token leg, transfers the fee to the recipient and the remainder to the user, all in one transaction. No custom router or fee contract is needed. The user authorizes Bundles on Midnight once (`setIsAuthorized`), the same requirement as a fee-free integration.

The fee base depends on the entrypoint. Amount-targeted entrypoints keep the user-facing amount exact and adjust the amount filled on the book. Units-targeted entrypoints keep the units exact and adjust the loan-token amount. In the table, `pct` is `referralFeePct` and `WAD` is `1e18`.

| Flow | Fee formula | Effect on the trade |
| --- | --- | --- |
| **Borrow, exact loan-token amount** `midnightBundlesV1SupplyCollateralAndSellWithAssetsTarget` | `fee = targetSellerAssets * pct / (WAD - pct)` | Bundles fills `targetSellerAssets + fee` on the book. The receiver gets exactly `targetSellerAssets`. More units are sold, so the debt at maturity is higher. |
| **Borrow, exact units** `midnightBundlesV1SupplyCollateralAndSellWithUnitsTarget` | `fee = filledSellerAssets * pct / WAD` | The receiver gets `filledSellerAssets - fee`. `minSellerAssets` is checked on the net amount. |
| **Lend, exact loan-token amount** `midnightBundlesV1BuyWithAssetsTargetAndWithdrawCollateral` | `fee = targetBuyerAssets * pct / WAD` | Bundles pulls `targetBuyerAssets` and fills `targetBuyerAssets - fee` on the book. Fewer units are bought, so `minUnits` must account for the fee. |
| **Lend, exact units** `midnightBundlesV1BuyWithUnitsTargetAndWithdrawCollateral` | `fee = filledBuyerAssets * pct / (WAD - pct)` | The lender pays `filledBuyerAssets + fee`. `maxBuyerAssets` must cover the fee. The unused remainder is refunded. |
| **Repay** `midnightBundlesV1RepayAndWithdrawCollateral` | `fee = assets * pct / WAD` | `assets - fee` units are repaid. To repay a debt `D` in full, pass `assets = floor(D * WAD / (WAD - pct))`. |

All divisions round down to whole token units. On the two amount-targeted take entrypoints the referral fee changes the amount sent to the order book, which may consume more or fewer price levels and change the average taking price. Build the quote from the amount Bundles will actually fill, not from the user-facing amount: `target + fee` for a borrow with an exact loan-token amount, `target - fee` for a lend with an exact loan-token amount.

### [Worked example: borrow an exact loan-token amount](#worked-example-borrow-an-exact-loan-token-amount)

A borrower wants to receive `10,000 USDC` (`10_000_000_000` units of USDC). Your product charges `referralFeePct = 0.02e18` (2%).

- `fee = floor(10_000_000_000 * 0.02e18 / 0.98e18) = 204_081_632` (204.081632 USDC)
- Bundles fills `10_204_081_632` on the book (10,204.081632 USDC)
- the borrower receives exactly `10_000_000_000` (10,000 USDC)
- the recipient receives `204_081_632` (204.081632 USDC)

At an average settlement price of `0.95`, the borrower sells about `10,741` units instead of about `10,526`. The extra `215` units are debt at maturity that finance the fee. `referralFeePct` is a share of the gross amount filled, so `2%` of gross is `2.04%` of the net amount the borrower sees. To charge `feeBps` on the net amount instead, set `referralFeePct = feeBps * WAD / (10_000 + feeBps)`.

## [Implementation](#implementation)

The [Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/) Midnight taker flows (`takeLend`, `takeBorrow`, `supplyCollateralTakeBorrow`, `repayWithdrawCollateral`) encode `referralFeePct = 0` today. To charge a fee, call `MidnightBundlesV1` directly with the ABI exported by the SDK (`midnightBundlesAbi` from `@morpho-org/morpho-sdk/abis`). The [Borrow at a fixed rate](https://docs.morpho.org/developers/midnight/tutorials/borrow-at-a-fixed-rate/) tutorial shows the full flow with `referralFeePct = 0`. The change for a fee-charging product is:

```
import { parseUnits } from "viem";
import { midnightBundlesAbi } from "@morpho-org/morpho-sdk/abis";

const WAD = 10n ** 18n;
const referralFeePct = parseUnits("0.02", 18);                // 2% of the gross amount filled
const referralFeeRecipient = "0xYourFeeRecipient";

const targetSellerAssets = parseUnits("10000", 6);            // what the borrower receives
const fee = (targetSellerAssets * referralFeePct) / (WAD - referralFeePct);
const grossSellerAssets = targetSellerAssets + fee;           // what Bundles fills on the book

// 1. Quote the gross amount, not the net amount: Bundles needs offers for
//    `grossSellerAssets`, and `maxUnits` must be derived from it.
const quote = await MidnightApi.fetchBookQuote({ /* ..., */ assets: grossSellerAssets });
const worstAcceptablePriceWad = parseUnits("0.95", 18);
const maxUnits =
  (grossSellerAssets * WAD + worstAcceptablePriceWad - 1n) / worstAcceptablePriceWad;

// 2. Pass the fee parameters to Bundles.
const hash = await walletClient.writeContract({
  account: taker,
  address: MIDNIGHT_BUNDLES,
  abi: midnightBundlesAbi,
  functionName: "midnightBundlesV1SupplyCollateralAndSellWithAssetsTarget",
  args: [
    targetSellerAssets,     // the borrower receives exactly this amount
    maxUnits,               // rate guard, derived from the gross amount
    taker,
    false,                  // reduceOnly
    taker,                  // receiver
    collateralSupplies,
    takes,                  // takeable offers from the gross quote
    referralFeePct,
    referralFeeRecipient,
    maxUint256,             // maxContinuousFee
    deadline,
  ],
});
```

The same two parameters apply to the lend, units-targeted, and repay entrypoints. Use the fee formula of the entrypoint you call to derive the amount Bundles fills, `minUnits`, `maxUnits`, or `maxBuyerAssets`.

## [Production checklist](#production-checklist)

The fee is plain calldata that the user signs. Make it explicit and verifiable.

Bundles does not cap the referral fee: any `referralFeePct` below `WAD` is accepted, so a malicious or buggy frontend could route most of a user's loan to `referralFeeRecipient`. The user's protection is the calldata they sign: the fee parameters are visible in the transaction, and on units-targeted entrypoints `minSellerAssets` and `maxBuyerAssets` bound what they give up. Show the fee in the preview, keep `referralFeePct` in auditable configuration, and expect wallets and users to check it.

### [User disclosure](#user-disclosure)

Show the user, before signature:

- the net loan-token amount they receive (borrow) or spend (lend);
- the referral fee amount and its recipient;
- the units sold or bought, which is the debt or credit at maturity, after the fee;
- the effective fixed rate after the referral fee and the protocol settlement fee, not the headline offer rate;
- the resulting LTV or health after the fee, for a borrow;
- the exact repayment amount at maturity, including the repay-side fee if you charge one.

Do not present the net amount as the debt. On a borrow, the debt is the units sold, and the fee increases them.

### [Simulation and guards](#simulation-and-guards)

- Quote and simulate with the amount Bundles fills on amount-targeted entrypoints: `target + fee` for a borrow, `target - fee` for a lend.
- Derive `maxUnits` (borrow) or `minUnits` (lend) from that filled amount, so the rate guard still holds with the fee.
- On `midnightBundlesV1BuyWithUnitsTargetAndWithdrawCollateral`, set `maxBuyerAssets` to at least `filledBuyerAssets + fee`, or Bundles reverts.
- Check collateral health against the gross debt, not the net amount received.
- Handle rounding in token units. All fee divisions round down.
- Make sure the fee recipient can receive and handle the loan token.
- Keep `maxContinuousFee` and `deadline` as tight as your product allows. They are unrelated to the referral fee but ship in the same call.

### [Fee parameters and authorization](#fee-parameters-and-authorization)

The fee parameters are chosen by your frontend or backend, not enforced on-chain. Keep them auditable:

- pin `referralFeePct` and `referralFeeRecipient` in your product configuration and show them in the transaction preview;
- reject a `referralFeePct` above your published cap before building the call;
- `MidnightBundlesV1` requires `taker == msg.sender` or a Midnight authorization from the taker. `setIsAuthorized` grants persistent authority across Midnight, including the ability to authorize other accounts; it cannot be limited to a market, action, amount, fee, or deadline. For onchain scope, authorize a smart contract that enforces those limits. Otherwise, disclose the full scope and provide a clear revocation path.

## [Important limitations](#important-limitations)

A referral fee at the integration layer does not make the market permissioned. Users can call Midnight or `MidnightBundlesV1` directly, or use another integration, and bypass your fee. This pattern monetizes your product flow, not the protocol.

Use it when the user receives clear value from your product, such as distribution, onboarding, rate discovery, risk tooling, account abstraction, sponsored gas, or portfolio management.

[Display positions

Previous Page

](https://docs.morpho.org/developers/midnight/tutorials/display-positions/)[Resources

Next Page

](https://docs.morpho.org/developers/midnight/resources/all/)