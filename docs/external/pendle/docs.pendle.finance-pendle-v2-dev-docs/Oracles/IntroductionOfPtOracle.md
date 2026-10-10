# Introduction of PT Oracle

> Source: https://docs.pendle.finance/pendle-v2-dev/Oracles/IntroductionOfPtOracle

---

- [](https://docs.pendle.finance/)
- Oracles
- PT Oracle Introduction

On this page
# Introduction of PT Oracle

In the Pendle system, PTPTPT can be freely traded from and to SYSYSY utilizing our AMM. With the built-in TWAP oracle library, the geometric mean price of PTPTPT in terms of SY or asset can be derived from our `PendleMarket` contracts fully on-chain. Please refer to the [StandardizedYield doc](https://docs.pendle.finance/pendle-v2-dev/Contracts/StandardizedYield) for more details of SY & asset

## Oracle design[​](#oracle-design)

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