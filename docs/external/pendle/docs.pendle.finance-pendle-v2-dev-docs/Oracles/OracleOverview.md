# Pendle Oracle Overview

> Source: https://docs.pendle.finance/pendle-v2-dev/Oracles/OracleOverview

---

- [](https://docs.pendle.finance/)
- Oracles
- Oracle Overview

On this page
# Pendle Oracle Overview

Pendle offers two oracle types for pricing PT and LP tokens. For most new integrations, **the Linear Discount Oracle is the recommended choice** — it has been widely adopted by top Aave and Morpho curators including Gauntlet and Steakhouse due to its manipulation-resistant design and alignment with PT's guaranteed 1:1 redemption to underlying at maturity. The TWAP oracle remains available for integrations that require a market-derived price.

## Which oracle should I use?[​](#which-oracle-should-i-use)

| Oracle type | Status | Best for | Docs |
| --- | --- | --- | --- |
| **Deterministic (Linear Discount)** | ✅ **Recommended** | Money markets, lending protocols, collateral pricing | [LinearDiscountOracle](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/LinearDiscountOracle) · [LP variant](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/LPLinearDiscountOracle) · [Choosing params](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/ChoosingLinearDiscountParams) |
| TWAP PT/LP Oracle | Available | Integrations requiring a live market-derived price | [HowToIntegratePtAndLpOracle](https://docs.pendle.finance/pendle-v2-dev/Oracles/HowToIntegratePtAndLpOracle) |

## Why the Linear Discount Oracle is recommended[​](#why-the-linear-discount-oracle-is-recommended)

PT is **guaranteed to redeem 1:1 to its underlying asset at maturity**. This hard floor means a linear discount model — which prices PT as a fraction that converges to 1.0 at expiry — is fundamentally sound and tightly tracks fair value. In contrast, TWAP oracles derive price from AMM activity, which introduces AMM manipulation surface and requires careful initialization and liquidity depth assessment.

The Linear Discount Oracle has no external dependencies during reads (`block.timestamp` only), making it liveness-risk-free and manipulation-resistant. This is why it has become the oracle of choice for top risk curators integrating PT across Aave and Morpho markets.

## About the PT Oracle[​](#about-the-pt-oracle)

In the Pendle system, PTPTPT can be freely traded from and to SYSYSY utilizing our AMM. With the built-in TWAP oracle library, the geometric mean price of PTPTPT in terms of SY or asset can be derived from our `PendleMarket` contracts fully on-chain. Please refer to the [StandardizedYield doc](https://docs.pendle.finance/pendle-v2-dev/Contracts/StandardizedYield) for more details of SY & asset.

### Oracle design[​](#oracle-design)

Pendle's oracle implementation is inspired by the idea of the UniswapV3 Oracle (see [here](https://docs.uniswap.org/concepts/protocol/oracle)) with a slight difference in how we define the cumulative rate. In short, our oracle stores the cumulative logarithm of implied APY (the interest rate implied by PT/assetPT/assetPT/asset pricing). From the cumulative logarithm of Implied APY, we can calculate the geometric mean of Implied APY, which will be used to derive the mean PTPTPT price.

In a way, the Pendle AMM contract has a built-in oracle of interest rate, which can be used to derive PTPTPT prices.

### Formulas[​](#formulas)

Our oracle storage is in the following form:

```
struct Observation {    // the block timestamp of the observation    uint32 blockTimestamp;    // the tick logarithm accumulator, i.e., ln(impliedRate) * time elapsed since the pool was first initialized    uint216 lnImpliedRateCumulative;    // whether or not the observation is initialized    bool initialized;}
```

The geometric mean price of PTPTPT for the time interval of [t0,t1][t_0, t_1][t0​,t1​] is:

lnImpliedRate=lnImpliedRateCumulative1−lnImpliedRateCumulative0t1−t0lnImpliedRate = \frac{lnImpliedRateCumulative_1 - lnImpliedRateCumulative_0}{t_1 - t_0}lnImpliedRate=t1​−t0​lnImpliedRateCumulative1​−lnImpliedRateCumulative0​​
impliedRate=elnImpliedRateimpliedRate = e^{lnImpliedRate}impliedRate=elnImpliedRate
assetToPtPrice=impliedRatetimeToMaturityoneYearassetToPtPrice = impliedRate^{\frac{timeToMaturity}{oneYear}}assetToPtPrice=impliedRateoneYeartimeToMaturity​
ptToAssetPrice=1/assetToPtPriceptToAssetPrice = 1 / assetToPtPriceptToAssetPrice=1/assetToPtPrice
See [How to Integrate](https://docs.pendle.finance/pendle-v2-dev/Oracles/HowToIntegratePtAndLpOracle) for a step-by-step guide.

## About the LP Oracle[​](#about-the-lp-oracle)

Pendle's LP token represents a user's share in Pendle AMM which pairs up PT and SY.

SY is the interest-bearing token wrapper which enables depositing from and redeeming from underlying asset with no additional fee or price impact. PT can be traded to and from SY/underlying asset using our AMM, with a built-in geometric mean pricing module.

LP oracle returns the estimated TWAP exchange rate between LP token and underlying asset. Our approach for LP pricing is to simulate a hypothetical trade on the AMM so that its PT spot price (and the implied rate) matches PT price (and the implied rate) from PT oracle before using market state to calculate LP price.

For example:

- The 1hr TWAP PT price is 0.90 asset.
- The current state of the market is (x PT, y SY), where PT price is 0.92 asset
- We calculate a hypothetical, zero-fee swap that brings PT price to 0.90 asset, to reach a state of (x' PT, y' SY)
- We calculate the estimated TWAP LP token price based on the hypothetical state (x' PT, y' SY) and PT price of 0.90 asset

Detailed documentation on the math for this approach can be found [here](https://github.com/pendle-finance/pendle-v2-resources/blob/main/docs/LP_Oracle_Doc.pdf).

See [How to Integrate](https://docs.pendle.finance/pendle-v2-dev/Oracles/HowToIntegratePtAndLpOracle) for a step-by-step guide.

## Recommended reading order[​](#recommended-reading-order)

### If using the Linear Discount Oracle (recommended)[​](#if-using-the-linear-discount-oracle-recommended)

1. This page — understand which oracle type fits your use case
2. [Linear Discount Oracle](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/LinearDiscountOracle) — how the oracle works and how to deploy it
3. [Choosing Linear Discount Parameters](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/ChoosingLinearDiscountParams) — how to select the right discount rate
4. If pricing LP tokens: [LP Linear Discount Oracle](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/LPLinearDiscountOracle)
5. If using as collateral: [PT as Collateral](https://docs.pendle.finance/pendle-v2-dev/Oracles/PTAsCollateral) or [LP as Collateral](https://docs.pendle.finance/pendle-v2-dev/Oracles/LPAsCollateral)

### If using the TWAP Oracle[​](#if-using-the-twap-oracle)

1. This page — understand which oracle type fits your use case
2. [How to Integrate PT and LP Oracle](https://docs.pendle.finance/pendle-v2-dev/Oracles/HowToIntegratePtAndLpOracle) — hands-on TWAP integration with code
3. [PT Sanity Checks](https://docs.pendle.finance/pendle-v2-dev/Oracles/PTSanityChecks) — validate your integration before going live
4. If using as collateral: [PT as Collateral](https://docs.pendle.finance/pendle-v2-dev/Oracles/PTAsCollateral) or [LP as Collateral](https://docs.pendle.finance/pendle-v2-dev/Oracles/LPAsCollateral)