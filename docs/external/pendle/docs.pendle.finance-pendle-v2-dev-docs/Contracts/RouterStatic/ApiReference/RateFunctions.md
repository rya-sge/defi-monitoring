# Market Rates & State Functions

> Source: https://docs.pendle.finance/pendle-v2-dev/Contracts/RouterStatic/ApiReference/RateFunctions

---

- [](https://docs.pendle.finance/)
- Contracts
- RouterStatic
- API Reference
- Rate Functions

On this page
# Market Rates & State Functions

These functions come from the `IPActionMarketAuxStatic` facet. They cover spot prices, market state, price impact calculations, and `ApproxParams` generation helpers.

---

## Spot Rates[​](#spot-rates)

All spot rates are returned as 18-decimal fixed-point numbers.

### getLpToSyRate[​](#getlptosyrate)

Returns the **spot** price of 1 LP token denominated in the market's SY token.

```
function getLpToSyRate(address market) external view returns (uint256)
```

**Parameters**

| Name | Type | Description |
| --- | --- | --- |
| market | `address` | Pendle market address |

**Return Values**

| Type | Description |
| --- | --- |
| `uint256` | Spot LP price in SY units (18 decimals) |

---

### getLpToAssetRate[​](#getlptoassetrate)

Returns the **spot** price of 1 LP token denominated in the SY's underlying asset.

```
function getLpToAssetRate(address market) external view returns (uint256)
```

**Parameters**

| Name | Type | Description |
| --- | --- | --- |
| market | `address` | Pendle market address |

**Return Values**

| Type | Description |
| --- | --- |
| `uint256` | Spot LP price in underlying asset units (18 decimals) |

---

### getPtToSyRate[​](#getpttosyrate)

Returns the **spot** price of 1 PT token denominated in SY.

```
function getPtToSyRate(address market) external view returns (uint256)
```

**Parameters**

| Name | Type | Description |
| --- | --- | --- |
| market | `address` | Pendle market address |

**Return Values**

| Type | Description |
| --- | --- |
| `uint256` | Spot PT price in SY units (18 decimals) |

---

### getPtToAssetRate[​](#getpttoassetrate)

Returns the **spot** price of 1 PT token denominated in the SY's underlying asset.

```
function getPtToAssetRate(address market) external view returns (uint256)
```

---

### getYtToSyRate[​](#getyttosyrate)

Returns the **spot** price of 1 YT token denominated in SY.

```
function getYtToSyRate(address market) external view returns (uint256)
```

---

### getYtToAssetRate[​](#getyttoassetrate)

Returns the **spot** price of 1 YT token denominated in the SY's underlying asset.

```
function getYtToAssetRate(address market) external view returns (uint256)
```

---

## Market State[​](#market-state)

### getMarketState[​](#getmarketstate)

Returns the full market state along with derived metrics.

```
function getMarketState(address market)    external    view    returns (        address pt,        address yt,        address sy,        int256 impliedYield,        uint256 marketExchangeRateExcludeFee,        MarketState memory state    )
```

**Parameters**

| Name | Type | Description |
| --- | --- | --- |
| market | `address` | Pendle market address |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| pt | `address` | Principal Token address |
| yt | `address` | Yield Token address |
| sy | `address` | SY token address |
| impliedYield | `int256` | Current implied yield rate (18 decimals) |
| marketExchangeRateExcludeFee | `uint256` | Current PT/SY exchange rate (fees excluded) |
| state | `MarketState` | Full low-level AMM state struct |

---

### getTradeExchangeRateExcludeFee[​](#gettradeexchangerateexcludefee)

Returns the current trade exchange rate from a given market state, excluding fees.

```
function getTradeExchangeRateExcludeFee(address market, MarketState memory state)    external    view    returns (uint256)
```

**Parameters**

| Name | Type | Description |
| --- | --- | --- |
| market | `address` | Pendle market address |
| state | `MarketState` | Market state (e.g. from `getMarketState`) |

**Return Values**

| Type | Description |
| --- | --- |
| `uint256` | Exchange rate excluding fees (18 decimals) |

---

### getTradeExchangeRateIncludeFee[​](#gettradeexchangerateincludefee)

Returns the effective exchange rate for a specific trade size, including fees.

```
function getTradeExchangeRateIncludeFee(address market, int256 netPtOut)    external    view    returns (uint256)
```

**Parameters**

| Name | Type | Description |
| --- | --- | --- |
| market | `address` | Pendle market address |
| netPtOut | `int256` | Signed PT delta for the trade (positive = PT leaving pool, negative = PT entering pool) |

**Return Values**

| Type | Description |
| --- | --- |
| `uint256` | Effective exchange rate including fees (18 decimals) |

---

## Price Impact[​](#price-impact)

All price impact values are returned as 18-decimal fixed-point numbers (e.g. `1e16` = 1%).

### calcPriceImpactPt[​](#calcpriceimpactpt)

Calculates the price impact of a PT trade.

```
function calcPriceImpactPt(address market, int256 netPtOut)    external    view    returns (uint256)
```

**Parameters**

| Name | Type | Description |
| --- | --- | --- |
| market | `address` | Pendle market address |
| netPtOut | `int256` | Signed PT amount (positive = buy PT, negative = sell PT) |

**Return Values**

| Type | Description |
| --- | --- |
| `uint256` | Price impact as a fraction (18 decimals) |

---

### calcPriceImpactYt[​](#calcpriceimpactyt)

Calculates the price impact of a YT trade, expressed in PT terms.

```
function calcPriceImpactYt(address market, int256 netPtOut)    external    view    returns (uint256)
```

---

### calcPriceImpactPY[​](#calcpriceimpactpy)

Calculates the combined price impact of a simultaneous PT+YT trade.

```
function calcPriceImpactPY(address market, int256 netPtOut)    external    view    returns (uint256)
```

---

## Yield Token / PT / YT Conversion Rates[​](#yield-token--pt--yt-conversion-rates)

### getYieldTokenAndPtRate[​](#getyieldtokenandptrate)

Returns how many yield tokens are equivalent to 1 PT at current rates.

```
function getYieldTokenAndPtRate(address market)    external    view    returns (address yieldToken, uint256 netPtOut, uint256 netYieldTokenOut)
```

**Parameters**

| Name | Type | Description |
| --- | --- | --- |
| market | `address` | Pendle market address |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| yieldToken | `address` | The market's underlying yield-bearing token |
| netPtOut | `uint256` | Normalised PT amount used as the basis (typically 1e18) |
| netYieldTokenOut | `uint256` | Equivalent yield token amount |

---

### getYieldTokenAndYtRate[​](#getyieldtokenandytrate)

Returns how many yield tokens are equivalent to 1 YT at current rates.

```
function getYieldTokenAndYtRate(address market)    external    view    returns (address yieldToken, uint256 netYtOut, uint256 netYieldTokenOut)
```

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| yieldToken | `address` | The market's underlying yield-bearing token |
| netYtOut | `uint256` | Normalised YT amount used as the basis (typically 1e18) |
| netYieldTokenOut | `uint256` | Equivalent yield token amount |

---

## ApproxParams Helpers[​](#approxparams-helpers)

These functions combine a swap simulation with automatic `ApproxParams` generation. Pass the returned `approxParams` directly to the corresponding Router function.

### swapExactSyForPtStaticAndGenerateApproxParams[​](#swapexactsyforptstaticandgenerateapproxparams)

Simulates swapping exact SY for PT and returns a ready-to-use `ApproxParams`.

```
function swapExactSyForPtStaticAndGenerateApproxParams(    address market,    uint256 exactSyIn,    uint256 slippage)    external    view    returns (        uint256 netPtOut,        uint256 netSyFee,        uint256 priceImpact,        uint256 exchangeRateAfter,        ApproxParams memory approxParams    )
```

**Parameters**

| Name | Type | Description |
| --- | --- | --- |
| market | `address` | Pendle market address |
| exactSyIn | `uint256` | Exact SY amount to swap in |
| slippage | `uint256` | Maximum acceptable slippage (18-decimal fraction, e.g. `5e15` = 0.5%) |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netPtOut | `uint256` | Expected PT output |
| netSyFee | `uint256` | Fee paid in SY |
| priceImpact | `uint256` | Price impact of the trade (18 decimals) |
| exchangeRateAfter | `uint256` | Exchange rate after the trade (18 decimals) |
| approxParams | [`ApproxParams`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#approxparams) | Pre-filled approximation parameters for the Router call |

---

### swapExactTokenForPtStaticAndGenerateApproxParams[​](#swapexacttokenforptstaticandgenerateapproxparams)

Simulates swapping exact tokens for PT and returns a ready-to-use `ApproxParams`.

```
function swapExactTokenForPtStaticAndGenerateApproxParams(    address market,    address tokenIn,    uint256 amountTokenIn,    uint256 slippage)    external    view    returns (        uint256 netPtOut,        uint256 netSyMinted,        uint256 netSyFee,        uint256 priceImpact,        uint256 exchangeRateAfter,        ApproxParams memory approxParams    )
```

**Parameters**

| Name | Type | Description |
| --- | --- | --- |
| market | `address` | Pendle market address |
| tokenIn | `address` | Input token address |
| amountTokenIn | `uint256` | Exact token amount to swap in |
| slippage | `uint256` | Maximum acceptable slippage (18-decimal fraction) |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netPtOut | `uint256` | Expected PT output |
| netSyMinted | `uint256` | SY minted from the input token |
| netSyFee | `uint256` | Fee paid in SY |
| priceImpact | `uint256` | Price impact of the trade (18 decimals) |
| exchangeRateAfter | `uint256` | Exchange rate after the trade (18 decimals) |
| approxParams | [`ApproxParams`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#approxparams) | Pre-filled approximation parameters for the Router call |

**Use Case**
This is the recommended way to populate `ApproxParams` for `swapExactTokenForPt`. It avoids the need to tune approximation parameters manually.

---

## Examples[​](#examples)

Recommended: Use the Pendle APIThe examples below show direct RouterStatic usage. For most integrations, the [Pendle Hosted SDK / API](https://docs.pendle.finance/pendle-v2-dev/Backend/HostedSdk) is the better choice — it handles approximation, limit-order filling, and zap routing automatically.

### Display LP / PT / YT spot prices[​](#display-lp--pt--yt-spot-prices)

```
const [lpToAsset, ptToAsset, ytToAsset] = await Promise.all([    routerStatic.getLpToAssetRate(MARKET_ADDRESS),    routerStatic.getPtToAssetRate(MARKET_ADDRESS),    routerStatic.getYtToAssetRate(MARKET_ADDRESS),]);// All values are 18-decimal fractions of the underlying assetconsole.log(`1 LP  = ${ethers.formatEther(lpToAsset)} underlying`);console.log(`1 PT  = ${ethers.formatEther(ptToAsset)} underlying`);console.log(`1 YT  = ${ethers.formatEther(ytToAsset)} underlying`);
```

### Read market state and implied yield[​](#read-market-state-and-implied-yield)

```
const [pt, yt, sy, impliedYield, exchangeRateExcludeFee, state] =    await routerStatic.getMarketState(MARKET_ADDRESS);// impliedYield is a signed 18-decimal annualised rateconst impliedYieldPct = Number(ethers.formatEther(impliedYield)) * 100;console.log(`Implied yield: ${impliedYieldPct.toFixed(2)}%`);console.log(`PT: ${pt}, YT: ${yt}, SY: ${sy}`);
```

### Gate a trade on price impact[​](#gate-a-trade-on-price-impact)

```
const netPtOut_amount = ethers.parseEther("500");const priceImpact = await routerStatic.calcPriceImpactPt(MARKET_ADDRESS, netPtOut_amount);const impactPct = Number(ethers.formatEther(priceImpact)) * 100;if (impactPct > 1.0) {    throw new Error(`Price impact ${impactPct.toFixed(2)}% exceeds 1% threshold — reduce size`);}
```

### Buy PT with token using generated ApproxParams[​](#buy-pt-with-token-using-generated-approxparams)

```
const tokenIn  = WSTETH_ADDRESS;const amountIn = ethers.parseEther("1");const SLIPPAGE = ethers.parseEther("0.005"); // 0.5%// 1. Get simulation + ready-to-use ApproxParams in a single callconst [netPtOut, netSyMinted, netSyFee, priceImpact, exchangeRateAfter, approxParams] =    await routerStatic.swapExactTokenForPtStaticAndGenerateApproxParams(        MARKET_ADDRESS,        tokenIn,        amountIn,        SLIPPAGE    );console.log(`PT out: ${ethers.formatEther(netPtOut)}`);console.log(`Fee:    ${ethers.formatEther(netSyFee)} SY`);console.log(`Impact: ${ethers.formatEther(priceImpact * 100n)}%`);// 2. Execute — pass approxParams directly, no manual tuning neededawait IERC20(tokenIn).approve(ROUTER_ADDRESS, amountIn);await router.swapExactTokenForPt(    signer.address,    MARKET_ADDRESS,    (netPtOut * 995n) / 1000n,  // minPtOut    approxParams,               // generated by RouterStatic    createTokenInputStruct(tokenIn, amountIn),    emptyLimitOrderData);
```