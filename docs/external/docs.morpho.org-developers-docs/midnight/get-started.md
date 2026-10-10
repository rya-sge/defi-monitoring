# Fixed Rate Markets (Midnight)

> Source: https://docs.morpho.org/developers/midnight/get-started

---

# Fixed Rate Markets (Midnight)

Integrating Morpho Midnight into your application means implementing the infrastructure that allows users to lend at fixed rates and borrow at fixed rates across isolated, fixed-term markets.

Unlike variable rate lending where rates fluctuate every block, Midnight rates are locked at the moment a take settles. Each unit represents a claim on (or obligation to repay) exactly one loan token at maturity. The rate emerges from the price at which units are taken, not from an interest rate model.

## [Key Integration Components](#key-integration-components)

When building fixed-rate earn and borrow products with Morpho Midnight, you need to integrate three main components:

1. **Market discovery and selection**: Let users browse isolated fixed-term markets by chain, loan token, maturity, accepted collaterals, and available bid/ask liquidity.
2. **Quote and execution flows**: Fetch takeable offers, apply price/slippage protections, and execute offers.
3. **Position and risk tracking**: Show users their credit, debt, collateral, maturity, pending fees, liquidation risk, and transaction history.

Integrating Midnight gives users access to:

1. **Fixed-rate lending and borrowing**: Rates are locked at execution because users take offers at a specific price. Lenders know the return they are targeting, and borrowers know the repayment obligation they create.
2. **Isolated fixed-term markets**: Each market is defined by one loan token, one maturity, and a fixed accepted-collateral set. Market parameters are immutable after creation, which makes risk easier to reason about.
3. **Fungible credit and debt units**: Positions are denominated in units. Credit units represent claims on loan tokens at maturity; debt units represent obligations to repay loan tokens.
4. **Early exits**: Lenders can sell credit units before maturity by taking resting buy offers, and borrowers can buy units from resting sell offers to close debt before maturity, depending on available offers.

## [Assets Flow - Lend](#assets-flow---lend)

Understanding the lending flow is essential for a clean Earn integration:

1. **Browse markets**: The user selects a market by chain, loan token, maturity, accepted collateral set, among many other parameters of interest.
2. **Estimate return**: The app converts ask prices for the selected market into implied fixed rates.
3. **Get a quote**: The Router returns executable takeable offers for the requested lend size and slippage, including fallback liquidity in case offers are consumed before execution.
4. **Buy credit units**: The user takes asks and spends loan tokens to buy credit units. Each credit unit is a claim on one loan token at maturity.
5. **Track position**: The user’s position shows credit, pending fees, cost basis, effective rate, and any loss factor.
6. **Exit or redeem**: Before maturity, the user may sell credit units by taking resting buy offers ([exit lend early](https://docs.morpho.org/developers/midnight/tutorials/exit-lend-early/)). Credit can also be redeemed 1:1, net of fees and losses, up to the loan tokens available for withdrawal: at or after maturity once borrowers repay, and before maturity only as far as repayments or liquidations have returned loan tokens to the market ([redeem lend at maturity](https://docs.morpho.org/developers/midnight/tutorials/redeem-lend-at-maturity/)).

## [Assets Flow - Borrow](#assets-flow---borrow)

For borrowing integrations, the flow is symmetric but risk and collateral management are central:

1. **Browse markets**: The user selects a market by chain, loan token, maturity, accepted collateral set, among many other parameters of interest.
2. **Estimate cost**: The app converts bid prices into implied fixed borrow rates. The highest bid is the best available price for the borrower.
3. **Supply collateral**: The borrower deposits accepted collateral. Borrowing capacity depends on the value of each collateral multiplied by its LLTV.
4. **Fetch a quote**: The Router returns executable takeable offers against bids for the requested borrow size.
5. **Sell units**: The borrower takes bids, sells debt units, and receives loan tokens. The debt amount is the number of units owed at maturity.
6. **Monitor health**: The position remains healthy while `maxDebt ≥ debt`. If debt exceeds maxDebt before maturity, the position can be partially liquidated. After maturity, unpaid debt can be partially or fully liquidated.
7. **Repay or exit**: The borrower can repay at maturity or buy units from resting sell offers before maturity to close debt early ([exit borrow early](https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-early/)).

## [Functional Integration Requirements](#functional-integration-requirements)

For a complete Midnight integration, your system needs to implement:

1. **Read Operations**:

  - Query market definitions and live market state.
  - Fetch books, bids, asks, quotes, and takeable offers.
  - Display user positions, transactions, collateral balances, credit, debt, pending fees, and effective rates.
  - Show fees and maturity status.
2. **Write Operations**:

  - Handle token approvals, permits, and Midnight Bundles authorization.
  - Execute lend, borrow, repay, collateral supply, collateral withdrawal, and early-exit flows.
  - For makers, publish signed offers and validate offer payloads before broadcasting.
3. **Monitoring Capabilities**:

  - Track position changes, offer consumption, transaction status, market liquidity, and liquidation events.
  - Alert users to maturity, deteriorating collateral health, failed quotes, exhausted liquidity, or rejected offer payloads.

## [Risk Considerations](#risk-considerations)

A complete Midnight integration should help users understand:

1. **Market isolation risk**: Each market has its own maturity, loan token, and fixed collateral set.
2. **Collateral risk**: Lenders are exposed to the full accepted collateral set of a market, not only the collateral currently posted by borrowers.
3. **Liquidation risk**: Borrowers can be liquidated if debt exceeds maxDebt before maturity, and unpaid debt can be fully liquidated after maturity.
4. **Liquidity risk**: Early exits and quote execution depend on available offers. Offers can be consumed before a transaction lands.
5. **Oracle risk**: Collateral health depends on oracle prices used to value collateral.
6. **Fee risk**: Settlement fees affect taker execution prices, while continuous fees reduce lender credit over time.
7. **Bad debt risk**: If liquidation does not fully cover debt, losses can be socialized to lenders through the market loss factor.

## [UX Requirements](#ux-requirements)

### [What your interface should surface](#what-your-interface-should-surface)

1. **Show both price and rate**: Users take offers at a price, while the app usually presents the result as an implied fixed rate.
2. **Distinguish asks and bids**: Lenders take asks; borrowers take bids. Make this clear in the UI.
3. **Explain maturity**: Users should understand what happens before maturity, at maturity, and after maturity.
4. **Show execution protection**: Display slippage, worst acceptable price, minimum units for lenders, or maximum units for borrowers.
5. **Surface collateral exposure**: For lend products, show the market accepted collateral set. For borrow products, show collateral requirements.
6. **Attribute Morpho**: Include a clear “Powered by Morpho” mention and appropriate protocol disclaimers in the user flow.

### [Brand & attribution](#brand--attribution)

- Surface “Powered by Morpho” on the screens where users actually interact with Morpho functionality. Integrators who get this framing right tend to have cleaner regulatory conversations and clearer user support.
- The official `powered-by-morpho` web component or the official static badge both work. If either does not fit a surface, contact the support team so the asset pack can be adapted rather than rebuilding the mark.
- Matching the badge theme to the UI surface (light on light, dark on dark) tends to read best.
- Somewhere reachable from the badge, users benefit from seeing the short disclaimer. The web component does this via tooltip.

**Reference.** [https://brand.morpho.org](https://brand.morpho.org) / [snippet.js](https://brand.morpho.org/snippet.js)

[Developers

Build on Morpho with product integrations, data tools, and open-source examples.

](https://docs.morpho.org/developers/)[Market Mechanics

Next Page

](https://docs.morpho.org/developers/midnight/concepts/market-mechanics/)