# Liquidity Management Functions

> Source: https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/LiquidityFunctions

---

- [](https://docs.pendle.finance/)
- Contracts
- PendleRouter
- API Reference
- Liquidity Functions

On this page
# Liquidity Management Functions

This document covers all functions for managing liquidity positions in Pendle markets. These functions allow adding and removing liquidity in various token combinations.

## Add Liquidity Functions[​](#add-liquidity-functions)

### addLiquidityDualTokenAndPt[​](#addliquiditydualtokenandpt)

Adds liquidity using a token and PT token in exact amounts.

```
function addLiquidityDualTokenAndPt(    address receiver,    address market,    TokenInput calldata input,    uint256 netPtDesired,    uint256 minLpOut) external payable returns (uint256 netLpOut, uint256 netPtUsed, uint256 netSyInterm)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive LP tokens |
| market | `address` | Pendle market address |
| input | [`TokenInput`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#tokeninput) | Token input configuration |
| netPtDesired | `uint256` | Desired amount of PT tokens to use |
| minLpOut | `uint256` | Minimum LP tokens to receive |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netLpOut | `uint256` | LP tokens received |
| netPtUsed | `uint256` | PT tokens actually used |
| netSyInterm | `uint256` | SY tokens generated from input token |

**Use Case**
When you have both the underlying token and PT tokens and want to add liquidity using exact amounts of both. The function will mint SY from your token input and combine it with your PT tokens.

### addLiquidityDualSyAndPt[​](#addliquiditydualsyandpt)

Adds liquidity using both SY and PT tokens in exact amounts.

```
function addLiquidityDualSyAndPt(    address receiver,    address market,    uint256 netSyDesired,    uint256 netPtDesired,    uint256 minLpOut) external returns (uint256 netLpOut, uint256 netSyUsed, uint256 netPtUsed)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive LP tokens |
| market | `address` | Pendle market address |
| netSyDesired | `uint256` | Desired amount of SY tokens to use |
| netPtDesired | `uint256` | Desired amount of PT tokens to use |
| minLpOut | `uint256` | Minimum LP tokens to receive |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netLpOut | `uint256` | LP tokens received |
| netSyUsed | `uint256` | SY tokens actually used |
| netPtUsed | `uint256` | PT tokens actually used |

**Use Case**
When you already have both SY and PT tokens and want to add liquidity directly.

### addLiquiditySinglePt[​](#addliquiditysinglept)

Adds liquidity using only PT tokens by internally swapping some PT for SY.

```
function addLiquiditySinglePt(    address receiver,    address market,    uint256 netPtIn,    uint256 minLpOut,    ApproxParams calldata guessPtSwapToSy,    LimitOrderData calldata limit) external returns (uint256 netLpOut, uint256 netSyFee)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive LP tokens |
| market | `address` | Pendle market address |
| netPtIn | `uint256` | Amount of PT tokens to use |
| minLpOut | `uint256` | Minimum LP tokens to receive |
| guessPtSwapToSy | [`ApproxParams`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#approxparams) | Approximation parameters |
| limit | [`LimitOrderData`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#limitorderdata) | Limit order configuration |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netLpOut | `uint256` | LP tokens received |
| netSyFee | `uint256` | Trading fees paid in SY |

**Use Case**
When you only have PT tokens and want to add liquidity. The function will automatically determine the optimal amount of PT to swap for SY to achieve balanced liquidity provision.

**Simple Version Available**
For basic operations without custom parameters, use [`addLiquiditySinglePtSimple`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/SimpleFunctions#addliquiditysingleptsimple) which automatically handles approximation and skips limit order functionality.

### addLiquiditySingleToken[​](#addliquiditysingletoken)

Adds liquidity using any supported token by converting it to SY and PT as needed.

```
function addLiquiditySingleToken(    address receiver,    address market,    uint256 minLpOut,    ApproxParams calldata guessPtReceivedFromSy,    TokenInput calldata input,    LimitOrderData calldata limit) external payable returns (uint256 netLpOut, uint256 netSyFee, uint256 netSyInterm)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive LP tokens |
| market | `address` | Pendle market address |
| minLpOut | `uint256` | Minimum LP tokens to receive |
| guessPtReceivedFromSy | [`ApproxParams`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#approxparams) | Approximation parameters |
| input | [`TokenInput`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#tokeninput) | Token input configuration |
| limit | [`LimitOrderData`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#limitorderdata) | Limit order configuration |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netLpOut | `uint256` | LP tokens received |
| netSyFee | `uint256` | Trading fees paid in SY |
| netSyInterm | `uint256` | SY tokens generated from input token |

**Use Case**
Most convenient method when you have any supported token and want to add liquidity. The function handles all necessary conversions and swaps automatically.

**Simple Version Available**
For basic operations without custom parameters, use [`addLiquiditySingleTokenSimple`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/SimpleFunctions#addliquiditysingletokensimple) which automatically handles approximation and skips limit order functionality.

### addLiquiditySingleSy[​](#addliquiditysinglesy)

Adds liquidity using only SY tokens by converting some to PT through market operations.

```
function addLiquiditySingleSy(    address receiver,    address market,    uint256 netSyIn,    uint256 minLpOut,    ApproxParams calldata guessPtReceivedFromSy,    LimitOrderData calldata limit) external returns (uint256 netLpOut, uint256 netSyFee)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive LP tokens |
| market | `address` | Pendle market address |
| netSyIn | `uint256` | Amount of SY tokens to use |
| minLpOut | `uint256` | Minimum LP tokens to receive |
| guessPtReceivedFromSy | [`ApproxParams`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#approxparams) | Approximation parameters |
| limit | [`LimitOrderData`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#limitorderdata) | Limit order configuration |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netLpOut | `uint256` | LP tokens received |
| netSyFee | `uint256` | Trading fees paid in SY |

**Use Case**
When you have SY tokens and want to add liquidity. The function will swap some SY for PT to achieve optimal liquidity provision.

**Simple Version Available**
For basic operations without custom parameters, use [`addLiquiditySingleSySimple`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/SimpleFunctions#addliquiditysinglesysimple) which automatically handles approximation and skips limit order functionality.

### addLiquiditySingleTokenKeepYt[​](#addliquiditysingletokenkeepyt)

Adds liquidity while keeping the generated YT tokens instead of selling them.

```
function addLiquiditySingleTokenKeepYt(    address receiver,    address market,    uint256 minLpOut,    uint256 minYtOut,    TokenInput calldata input) external payable returns (uint256 netLpOut, uint256 netYtOut, uint256 netSyMintPy, uint256 netSyInterm)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive LP and YT tokens |
| market | `address` | Pendle market address |
| minLpOut | `uint256` | Minimum LP tokens to receive |
| minYtOut | `uint256` | Minimum YT tokens to receive |
| input | [`TokenInput`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#tokeninput) | Token input configuration |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netLpOut | `uint256` | LP tokens received |
| netYtOut | `uint256` | YT tokens received |
| netSyMintPy | `uint256` | SY used to mint PT/YT |
| netSyInterm | `uint256` | SY tokens generated from input token |

**Use Case**
When you want to add liquidity and also keep YT tokens for yield farming. This strategy avoids price impact since no swapping occurs - the underlying asset is converted to SY, then PT/YT pairs are minted directly. The PT and remaining SY are used for liquidity provision while YT is returned to you.

### addLiquiditySingleSyKeepYt[​](#addliquiditysinglesykeepyt)

Adds liquidity using SY tokens while keeping the generated YT tokens.

```
function addLiquiditySingleSyKeepYt(    address receiver,    address market,    uint256 netSyIn,    uint256 minLpOut,    uint256 minYtOut) external returns (uint256 netLpOut, uint256 netYtOut, uint256 netSyMintPy)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive LP and YT tokens |
| market | `address` | Pendle market address |
| netSyIn | `uint256` | Amount of SY tokens to use |
| minLpOut | `uint256` | Minimum LP tokens to receive |
| minYtOut | `uint256` | Minimum YT tokens to receive |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netLpOut | `uint256` | LP tokens received |
| netYtOut | `uint256` | YT tokens received |
| netSyMintPy | `uint256` | SY used to mint PT/YT |

**Use Case**
When you have SY tokens and want both LP tokens and YT tokens. This method avoids price impact since no swapping occurs - SY is used to mint PT/YT pairs directly, with PT used for liquidity provision and YT returned to you.

## Remove Liquidity Functions[​](#remove-liquidity-functions)

### removeLiquidityDualTokenAndPt[​](#removeliquiditydualtokenandpt)

Removes liquidity and receives both the underlying token and PT tokens.

```
function removeLiquidityDualTokenAndPt(    address receiver,    address market,    uint256 netLpToRemove,    TokenOutput calldata output,    uint256 minPtOut) external returns (uint256 netTokenOut, uint256 netPtOut, uint256 netSyInterm)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive tokens |
| market | `address` | Pendle market address |
| netLpToRemove | `uint256` | Amount of LP tokens to burn |
| output | [`TokenOutput`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#tokenoutput) | Token output configuration |
| minPtOut | `uint256` | Minimum PT tokens to receive |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netTokenOut | `uint256` | Amount of tokens received |
| netPtOut | `uint256` | PT tokens received |
| netSyInterm | `uint256` | SY tokens converted to underlying |

**Use Case**
When you want to exit a liquidity position and receive both the underlying token and PT tokens separately.

### removeLiquidityDualSyAndPt[​](#removeliquiditydualsyandpt)

Removes liquidity and receives both SY and PT tokens.

```
function removeLiquidityDualSyAndPt(    address receiver,    address market,    uint256 netLpToRemove,    uint256 minSyOut,    uint256 minPtOut) external returns (uint256 netSyOut, uint256 netPtOut)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive tokens |
| market | `address` | Pendle market address |
| netLpToRemove | `uint256` | Amount of LP tokens to burn |
| minSyOut | `uint256` | Minimum SY tokens to receive |
| minPtOut | `uint256` | Minimum PT tokens to receive |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netSyOut | `uint256` | SY tokens received |
| netPtOut | `uint256` | PT tokens received |

**Use Case**
Most efficient method when you want both SY and PT tokens. No additional conversions are performed.

### removeLiquiditySinglePt[​](#removeliquiditysinglept)

Removes liquidity and converts everything to PT tokens.

```
function removeLiquiditySinglePt(    address receiver,    address market,    uint256 netLpToRemove,    uint256 minPtOut,    ApproxParams calldata guessPtReceivedFromSy,    LimitOrderData calldata limit) external returns (uint256 netPtOut, uint256 netSyFee)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive PT tokens |
| market | `address` | Pendle market address |
| netLpToRemove | `uint256` | Amount of LP tokens to burn |
| minPtOut | `uint256` | Minimum PT tokens to receive |
| guessPtReceivedFromSy | [`ApproxParams`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#approxparams) | Approximation parameters |
| limit | [`LimitOrderData`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#limitorderdata) | Limit order configuration |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netPtOut | `uint256` | PT tokens received |
| netSyFee | `uint256` | Trading fees paid in SY |

**Use Case**
When you want to exit liquidity and hold only PT tokens, maximizing your PT position.

**Simple Version Available**
For basic operations without custom parameters, use [`removeLiquiditySinglePtSimple`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/SimpleFunctions#removeliquiditysingleptsimple) which automatically handles approximation and skips limit order functionality.

### removeLiquiditySingleToken[​](#removeliquiditysingletoken)

Removes liquidity and converts everything to a specified underlying token.

```
function removeLiquiditySingleToken(    address receiver,    address market,    uint256 netLpToRemove,    TokenOutput calldata output,    LimitOrderData calldata limit) external returns (uint256 netTokenOut, uint256 netSyFee, uint256 netSyInterm)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive tokens |
| market | `address` | Pendle market address |
| netLpToRemove | `uint256` | Amount of LP tokens to burn |
| output | [`TokenOutput`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#tokenoutput) | Token output configuration |
| limit | [`LimitOrderData`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#limitorderdata) | Limit order configuration |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netTokenOut | `uint256` | Amount of tokens received |
| netSyFee | `uint256` | Trading fees paid in SY |
| netSyInterm | `uint256` | SY tokens before conversion |

**Use Case**
Most convenient exit method when you want to receive a specific underlying token. Handles all necessary conversions automatically.

### removeLiquiditySingleSy[​](#removeliquiditysinglesy)

Removes liquidity and converts everything to SY tokens.

```
function removeLiquiditySingleSy(    address receiver,    address market,    uint256 netLpToRemove,    uint256 minSyOut,    LimitOrderData calldata limit) external returns (uint256 netSyOut, uint256 netSyFee)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive SY tokens |
| market | `address` | Pendle market address |
| netLpToRemove | `uint256` | Amount of LP tokens to burn |
| minSyOut | `uint256` | Minimum SY tokens to receive |
| limit | [`LimitOrderData`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#limitorderdata) | Limit order configuration |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netSyOut | `uint256` | SY tokens received |
| netSyFee | `uint256` | Trading fees paid in SY |

**Use Case**
When you want to exit liquidity and hold SY tokens, useful for further operations within the Pendle ecosystem.

## Integration Examples[​](#integration-examples)

### Basic Liquidity Addition[​](#basic-liquidity-addition)

```
// Add liquidity with USDerouter.addLiquiditySingleToken(    msg.sender,    PT_USDE_MARKET_ADDRESS,    minLpOut,    createDefaultApproxParams(),    createTokenInputSimple(USDE_ADDRESS, 1000e18),    createEmptyLimitOrderData());
```

### Basic Liquidity Removal[​](#basic-liquidity-removal)

```
// Remove liquidity to USDerouter.removeLiquiditySingleToken(    msg.sender,    PT_USDE_MARKET_ADDRESS,    lpAmount,    createTokenOutputSimple(USDE_ADDRESS, minUsdeOut),    createEmptyLimitOrderData());
```