# How to Integrate PT and LP Oracle

> Source: https://docs.pendle.finance/pendle-v2-dev/Oracles/HowToIntegratePtAndLpOracle

---

- [](https://docs.pendle.finance/)
- Oracles
- How to Integrate PT & LP Oracle

On this page
# How to Integrate PT and LP Oracle

Looking for the recommended oracle?For most new integrations, Pendle now recommends the **[Linear Discount Oracle](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/LinearDiscountOracle)** — adopted by top Aave and Morpho curators (Gauntlet, Steakhouse) for its manipulation-resistant, AMM-independent design. This page covers the TWAP oracle, which remains fully supported for integrations that require a market-derived price.

Integrating PT and LP oracles into your system can be accomplished in the following steps. This document provides detailed instructions along with runnable examples.

If you need personalized assistance, don't hesitate to contact us via our Developers channel on [Pendle Discord](https://pendle.finance/discord).

## Prerequisite[​](#prerequisite)

### Understand SY, PT, LP[​](#understand-sy-pt-lp)

- Read [High Level Architecture](https://docs.pendle.finance/pendle-v2-dev/HighLevelArchitecture) and [StandardizedYield docs](https://docs.pendle.finance/pendle-v2-dev/Contracts/StandardizedYield) to understand the Pendle system.
- Refer to the examples in the following repository for further understanding:

  - [https://github.com/pendle-finance/pendle-examples/tree/main/test](https://github.com/pendle-finance/pendle-examples/tree/main/test)
  - [https://github.com/pendle-finance/pendle-core-v2-public/tree/main/contracts/oracles](https://github.com/pendle-finance/pendle-core-v2-public/tree/main/contracts/oracles)

### Follow security advisories[​](#follow-security-advisories)

As Pendle becomes more permissionless, certain security assumptions of SY will
change in the future, and the Pendle team will verify for all teams currently
integrating the LP Oracle that their integration meets the new **security
assumptions** of SY. Please reach out to us on [Pendle Discord](https://pendle.finance/discord) if you have any
questions.

## Choose a Market[​](#choose-a-market)

The *Using Pendle Oracle* and *Using Pendle Library* tabs use EtherFi's [weETH market](https://arbiscan.io/address/0x952083cde7aaa11AB8449057F7de23A970AA8472) on Arbitrum (70M USD liquidity at block 192 001 277). The *Using ChainLink oracle* tab demonstrates with an LBTC market to show how `PendleChainlinkOracleWithQuote` works with external price feeds.

We recommend choosing a market with high trading activities & deep liquidity.
For a detailed guide on assessing the risk, depth of liquidity & twap
duration, refer to the corresponding risk assessment docs.

- [For using PT as collateral](https://docs.pendle.finance/pendle-v2-dev/Oracles/PTAsCollateral#risk-analysis-for-pt-as-a-collateral)
- [For using LP as collateral](https://docs.pendle.finance/pendle-v2-dev/Oracles/LPAsCollateral#risk-analysis-for-lp-as-a-collateral)

## TWAP Duration and Oracle Initialization[​](#twap-duration-and-oracle-initialization)

By default, markets' oracles are **NOT initialized**. The oracle's status can be checked using the `_test_oracle_ready` function ([source](https://github.com/pendle-finance/pendle-examples-public/blob/642b1ab2784b3015691d6c26a2684cd5f7585b0d/test/OracleSample.sol#L75-L91)).

- The passed in `duration` is the TWAP duration (in seconds) you want to use.

  - The recommended TWAP duration is 900 seconds (15 minutes) for most markets or 1800 seconds (30 minutes).

```
function _test_oracle_ready(address marketToCheck, uint32 duration) public view {    (bool increaseCardinalityRequired, , bool oldestObservationSatisfied) =        oracle.getOracleState(marketToCheck, duration);    if (increaseCardinalityRequired) {        // <=============== (1) - Oracle needs to be initialized    }    if (!oldestObservationSatisfied) {        // <=============== (2) - Need to wait for data to be available    }    // <=============== (3) - Oracle is ready    assert(!increaseCardinalityRequired);    assert(oldestObservationSatisfied);}
```

### Point (1) - Oracle needs to be initialized[​](#point-1---oracle-needs-to-be-initialized)

At this point, the oracle needs to be initialized. This can be done by calling the following yourself:

```
IPMarket(market).increaseObservationsCardinalityNext(cardinalityRequired)
```

Here are possible values for `cardinalityRequired`:

| `duration` (seconds) | `900` | `1800` |
| --- | --- | --- |
| For Ethereum | 85 | 165 |
| For Arbitrum | 900 | 1800 |

So on Ethereum, for `duration` of 900 seconds, `cardinalityRequired` can be 85.

Calculate `cardinalityRequired`In general, it can be calculated like this

cardinalityRequired≈durationmax⁡{chain block time,1}\mathtt{cardinalityRequired} \approx
    \frac
        {\mathtt{duration}}
        {\max\{\mathrm{\text{chain block time}}, 1\}}cardinalityRequired≈max{chain block time,1}duration​
After that, you need **to wait** for `duration` seconds for the first data to be available.

### Point (2) - Need to wait for data to be available[​](#point-2---need-to-wait-for-data-to-be-available)

Similar to the previous point, you need **to wait** for `duration` seconds for the first data to be available.

### Point (3) - Oracle is ready[​](#point-3---oracle-is-ready)

Now you can call functions to get the observed price!

## Price Retrieval[​](#price-retrieval)

We have provided a few ways to obtain the price. Select one of the following
tabs to choose the one that best suits your needs.

- Using ChainLink oracle
- Using Pendle Oracle
- Using Pendle Library

We have provided a way to get the price, with the same interface as ChainLink oracles.

The source code of the whole example can be found here:

- [https://github.com/pendle-finance/pendle-examples-public/blob/main/test/ChainlinkOracleSample.sol](https://github.com/pendle-finance/pendle-examples-public/blob/main/test/ChainlinkOracleSample.sol)

### Step 1. Deploy the oracle (if not already deployed)[​](#step-1-deploy-the-oracle-if-not-already-deployed)

If the oracle is not already deployed, you can self-deploy it via the [Pendle Public DApp](https://dapp-public.pendle.finance/deploy-oracle), or deploy it yourself the same as this `setUp` function ([source](https://github.com/pendle-finance/pendle-examples-public/blob/642b1ab2784b3015691d6c26a2684cd5f7585b0d/test/ChainlinkOracleSample.sol#L30-L41)).

code fragment of setUp function
```
factory = new PendleChainlinkOracleFactory(0x5542be50420E88dd7D5B4a3D488FA6ED82F6DAc2);PT_LBTC_oracle = PendleChainlinkOracle(    factory.createOracle(address(market), twapDuration, PendleOracleType.PT_TO_SY));PT_USD_oracle = PendleChainlinkOracleWithQuote(    factory.createOracleWithQuote(address(market), twapDuration, PendleOracleType.PT_TO_SY, address(LBTC_USD_feed)));
```

Parameters summary
- `market` is the market address you want to observe the price.
- `twapDuration` is the TWAP duration you want to use, chosen in the previous section.
- `0x5542be50420E88dd7D5B4a3D488FA6ED82F6DAc2` is the address of the deployed Pendle Oracle.

  - It was deployed to have the same address on all networks.
  - Refer to [Deployments on GitHub](https://github.com/pendle-finance/pendle-core-v2-public/tree/main/deployments) section for the full list of addresses.
  - The deployed ChainLink oracles **wrap** this oracle.
  - Please refer to the *Using Pendle Oracle* way if you want to use it directly.

When deploying the oracle, you need to specify the type:

- `PendleOracleType.PT_TO_SY` - to get the price of PT in SY.
- `PendleOracleType.PT_TO_ASSET` - to get the price of PT in the underlying asset.

We support 2 contracts for obtaining the price:

- `PendleChainlinkOracle` - to get the price of PT in SY/asset.
- `PendleChainlinkOracleWithQuote` - to get the price of PT in a different token if you have the ChainLink oracle of that token with the underlying asset.

### Step 2. Call the oracle[​](#step-2-call-the-oracle)

Price can be obtained simply by calling the `getLatestRoundData` function ([source](https://github.com/pendle-finance/pendle-examples-public/blob/642b1ab2784b3015691d6c26a2684cd5f7585b0d/test/ChainlinkOracleSample.sol#L43-L54)).

```
function test_get_prices_in_SY() external view {    (uint80 roundId, int256 answer, , uint256 updatedAt, uint80 answeredInRound) = PT_LBTC_oracle.latestRoundData();    console.log("PT LBTC to SY-LBTC");    console.log(uint256(roundId), uint256(answer), updatedAt, uint256(answeredInRound));    // answer = 992893819205953801, meaning 1 PT = 0.992893819205953801 SY-LBTC}function test_get_prices_in_quote() external view {    (uint80 roundId, int256 answer, , uint256 updatedAt, uint80 answeredInRound) = PT_USD_oracle.latestRoundData();    console.log("PT LBTC to BTC");    console.log(uint256(roundId), uint256(answer), updatedAt, uint256(answeredInRound));    // answer = 990999427443599801, meaning 1 PT = 0.9909994274435997 BTC}
```

The source code of the whole example can be found here:

- [https://github.com/pendle-finance/pendle-examples-public/blob/main/test/OracleSample.sol](https://github.com/pendle-finance/pendle-examples-public/blob/main/test/OracleSample.sol)

We have deployed a contract that helps obtain the price of PT/YT/LP token in SY or asset.

The contract is at address `0x5542be50420E88dd7D5B4a3D488FA6ED82F6DAc2`.

- It was deployed to have the same address on all networks.
- Refer to [Deployments on GitHub](https://github.com/pendle-finance/pendle-core-v2-public/tree/main/deployments) section for the full list of addresses.

Getting the price can be done simply by calling the corresponding function ([source](https://github.com/pendle-finance/pendle-examples-public/blob/642b1ab2784b3015691d6c26a2684cd5f7585b0d/test/OracleSample.sol#L38-L46)).

```
function test_get_price_LRT_in_underlying() external view {    uint256 ptRateInWeEth = oracle.getPtToSyRate(address(market), twapDuration);    uint256 ytRateInWeEth = oracle.getYtToSyRate(address(market), twapDuration);    uint256 lpRateInWeEth = oracle.getLpToSyRate(address(market), twapDuration);    console.log("1 PT = %s Wrapped eEth (base 1e18)", ptRateInWeEth);    console.log("1 YT = %s Wrapped eEth (base 1e18)", ytRateInWeEth);    console.log("1 LP = %s Wrapped eEth (base 1e18)", lpRateInWeEth);}
```

### Optional: Convert the price to a different asset[​](#optional-convert-the-price-to-a-different-asset)

Additionally, if you have an on-chain feed for the price of the underlying asset with a different token, you can **convert** the price using multiplication.

```
function test_get_price_LRT_with_external_oracle() external view {    uint256 ptRateInWeEth = oracle.getPtToSyRate(address(market), twapDuration); // 1 SY-weETH = 1 weETH    uint256 ptRateInEth = (ptRateInWeEth * uint256(weETH_ETH_feed.latestAnswer())) / (10 ** weETH_ETH_feed.decimals());    console.log("1 PT = %s ETH (base 1e18)", ptRateInEth); // 1 PT = 0.980103943942239852 ETH    uint256 ptRateInUsd = (ptRateInEth * uint256(ETH_USD_feed.latestAnswer())) / (10 ** ETH_USD_feed.decimals());    console.log("1 PT = %s USD (base 1e18)", ptRateInUsd); // 1 PT = 3714.1302603652102 USD}
```

The source code of the whole example can be found here:

- [https://github.com/pendle-finance/pendle-examples-public/blob/main/test/OracleSample.sol](https://github.com/pendle-finance/pendle-examples-public/blob/main/test/OracleSample.sol)

This library is used in the Pendle Oracle (refer to *Using Pendle Oracle* section). But it can also be used directly in your contract source code. This can help save **about 4k gas**!

Before using it, import it as follows:

```
import {    PendlePYOracleLib,    PendleLpOracleLib} from "@pendle/core-v2/contracts/oracles/PtYtLpOracle/PendlePYLpOracle.sol";contract YourContract {    using PendlePYOracleLib for IPMarket;    using PendleLpOracleLib for IPMarket;    // ...}
```

Then you can call the functions directly on the market address.

```
function test_get_price_LRT_in_underlying_with_lib() external view {    uint256 ptRateInWeEth = market.getPtToSyRate(twapDuration);    uint256 ytRateInWeEth = market.getYtToSyRate(twapDuration);    uint256 lpRateInWeEth = market.getLpToSyRate(twapDuration);    console.log("1 PT = %s Wrapped eEth (base 1e18)", ptRateInWeEth);    console.log("1 YT = %s Wrapped eEth (base 1e18)", ytRateInWeEth);    console.log("1 LP = %s Wrapped eEth (base 1e18)", lpRateInWeEth);}
```

Refer to [StandardizedYield docs](https://docs.pendle.finance/pendle-v2-dev/Contracts/StandardizedYield) to call the correct function.

### Optional: Convert the price to a different asset[​](#optional-convert-the-price-to-a-different-asset-1)

Additionally, if you have an on-chain feed for the price of the underlying asset with a different token, you can **convert** the price using multiplication.

```
function test_get_price_LRT_with_external_oracle_with_lib() external view {    uint256 ptRateInWeEth = market.getPtToSyRate(twapDuration); // 1 SY-weETH = 1 weETH    uint256 ptRateInEth = (ptRateInWeEth * uint256(weETH_ETH_feed.latestAnswer())) / (10 ** weETH_ETH_feed.decimals());    console.log("1 PT = %s ETH (base 1e18)", ptRateInEth); // 1 PT = 0.980103943942239852 ETH    uint256 ptRateInUsd = (ptRateInEth * uint256(ETH_USD_feed.latestAnswer())) / (10 ** ETH_USD_feed.decimals());    console.log("1 PT = %s USD (base 1e18)", ptRateInUsd); // 1 PT = 3714.1302603652102 USD}
```

We recommend pricing PT to SY instead of asset.For SY to any other units, the integrator can choose an appropriate method
based on whether the asset can be directly redeemed from the SY or if there is
a slashing risk, etc. Pendle can not provide a perfect PT to Asset price because
Asset price is not well defined.

Pendle can not provide a perfect PT to asset priceLet's take a look at the example of PT-sUSDe/SY-sUSDe with asset being USDe.

Pendle can guarantee 1 PT-sUSDe can be traded to XXX SY-sUSDe = XXX sUSDe. PT to SY price **exists natively**.

On the other hand, Pendle **can not** guarantee sUSDe is redeemable to some amount of USDe. Which now traced back to: SY-sUSDe’s asset is not USDe, but USDe staked in Ethena, hence the price of this is not **well defined**.

---

Because of this, in case when sUSDe depegged from USDe, the conversion rate between PT-sUSDe to sUSDe is still correct, because the conversion rate is based on `SY.exchangeRate()`, which is provided by the underlying contract.

About unit and decimalsAs the `decimals` is a token metadata, and only be used to show the amount to
the users, Pendle contract does **not** operate with decimals. See the documentation about [unit and decimals](https://docs.pendle.finance/pendle-v2-dev/Contracts/UnitAndDecimals) for more info.

Let's say you want to know how much XXX LP is worth in SY.

First, we convert XXX into the **raw** format so that the contract can understand.

rawX=X×10LP.decimals\mathtt{rawX} = X \times 10^{\mathtt{LP}.\mathtt{decimals}}rawX=X×10LP.decimalsAfter obtaining the `lpToSyRate`, we convert `rawX` to the **raw** form of SY as follows:

rawY=rawX×lpToSyRate/1018\mathtt{rawY} = \mathtt{rawX} \times \mathtt{lpToSyRate} / 10^{18}rawY=rawX×lpToSyRate/1018
> Note that 101810^{18}1018 is a fixed number in the formula, and does not depend on any `decimals` data.

Finally, we can convert `rawY` to the human-readable format:

Y=rawY/10SY.decimalsY = \mathtt{rawY} / 10^{\mathtt{SY}.\mathtt{decimals}}Y=rawY/10SY.decimalsConversion between PT/YT and SY is done similarly.

As Pendle supports a wide variety of assets, each with a different `decimals`,
this fact is important to remember.

## Handle liquidation & LP's rewards[​](#handle-liquidation--lps-rewards)

### For PT liquidation[​](#for-pt-liquidation)

- When a liquidation with PTPTPT as collateral occurs, commonly, the liquidator will have to sell PTPTPT into common asset to pay their debt.
- In Pendle's system, we support converting PTPTPT back to SYSYSY by selling PTPTPT on our AMM (before maturity) or redeeming directly from `PendleYieldToken` contract (post maturity). This will then allow the liquidator to redeem their SYSYSY into one of the output tokens of SYSYSY.
- For reference, we have written the [`BoringPtSeller`](https://github.com/pendle-finance/pendle-core-v2-public/blob/main/contracts/oracles/samples/BoringPtSeller.sol) contract to sell PTPTPT into one of the output token.
- You can extend this abstract contract to use in a liquidation system.

### For LP liquidation[​](#for-lp-liquidation)

- When a liquidation with LPLPLP as collateral occurs, commonly, the liquidator will have to sell LPLPLP into common asset to pay their debt.
- In Pendle's system, we support converting LPLPLP back to SYSYSY by removing liquidity single-sided into SYSYSY on our AMM (before maturity) or redeeming PTPTPT + SYSYSY and redeeming PTPTPT to SYSYSY directly from `PendleYieldToken` contract (post maturity). This will then allow the liquidator to redeem their SYSYSY into one of the output tokens of SYSYSY.
- For reference, we have written the [`BoringLpSeller`](https://github.com/pendle-finance/pendle-core-v2-public/blob/main/contracts/oracles/samples/BoringLpSeller.sol) contract to sell LPLPLP into one of SY's output tokens.
- You can extend this abstract contract to use in a liquidation system.

### Handling of Pendle LP's rewards:[​](#handling-of-pendle-lps-rewards)

- Holding Pendle LP tokens will generate PENDLE incentives and potential reward tokens (like WETH for LP for GLP pool)
- The money market contracts will need to redeem these rewards by calling the `redeemRewards` function and implement logic to distribute these rewards to their users