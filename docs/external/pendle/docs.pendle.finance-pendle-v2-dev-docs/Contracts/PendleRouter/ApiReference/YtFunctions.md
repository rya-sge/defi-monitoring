# Yield Token (YT) Trading Functions

> Source: https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/YtFunctions

---

- [](https://docs.pendle.finance/)
- Contracts
- PendleRouter
- API Reference
- YT Functions

On this page
# Yield Token (YT) Trading Functions

This document covers all functions for trading Yield Tokens (YT) in Pendle markets. YT tokens represent the yield portion of yield-bearing assets and can be traded against other tokens or SY tokens.

## Token to YT Trading[​](#token-to-yt-trading)

Since the AMM only supports swaps by exact YT, to swap exact tokens for YT requires binary search approximation to find the correct amount of SY needed to achieve the desired YT output. For best usage, use the [SDK](https://docs.pendle.finance/pendle-v2-dev/Backend/HostedSdk#features) for better approximation since running binary search on-chain is costly.

### swapExactTokenForYt[​](#swapexacttokenforyt)

Swaps an exact amount of any supported token for YT tokens.

```
function swapExactTokenForYt(    address receiver,    address market,    uint256 minYtOut,    ApproxParams calldata guessYtOut,    TokenInput calldata input,    LimitOrderData calldata limit) external payable returns (uint256 netYtOut, uint256 netSyFee, uint256 netSyInterm)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive YT tokens |
| market | `address` | Pendle market address |
| minYtOut | `uint256` | Minimum YT tokens to receive |
| guessYtOut | [`ApproxParams`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#approxparams) | Approximation parameters |
| input | [`TokenInput`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#tokeninput) | Token input configuration |
| limit | [`LimitOrderData`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#limitorderdata) | Limit order configuration |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netYtOut | `uint256` | YT tokens received |
| netSyFee | `uint256` | Trading fees paid in SY |
| netSyInterm | `uint256` | SY tokens generated from input token |

**Use Case**
Most common function for buying YT tokens with any supported token. The function converts your token to SY and then swaps SY for YT, first filling available limit orders, then using the AMM for any remaining amount.

**Simple Version Available**
For basic operations without custom parameters, use [`swapExactTokenForYtSimple`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/SimpleFunctions#swapexacttokenforytsimple) which automatically handles approximation and skips limit order functionality.

### swapExactSyForYt[​](#swapexactsyforyt)

Swaps an exact amount of SY tokens for YT tokens.

```
function swapExactSyForYt(    address receiver,    address market,    uint256 exactSyIn,    uint256 minYtOut,    ApproxParams calldata guessYtOut,    LimitOrderData calldata limit) external returns (uint256 netYtOut, uint256 netSyFee)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive YT tokens |
| market | `address` | Pendle market address |
| exactSyIn | `uint256` | Exact amount of SY tokens to swap |
| minYtOut | `uint256` | Minimum YT tokens to receive |
| guessYtOut | [`ApproxParams`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#approxparams) | Approximation parameters |
| limit | [`LimitOrderData`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#limitorderdata) | Limit order configuration |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netYtOut | `uint256` | YT tokens received |
| netSyFee | `uint256` | Trading fees paid in SY |

**Use Case**
Direct and efficient method when you already have SY tokens and want to buy YT tokens.

**Simple Version Available**
For basic operations without custom parameters, use [`swapExactSyForYtSimple`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/SimpleFunctions#swapexactsyforytsimple) which automatically handles approximation and skips limit order functionality.

## YT to Token Trading[​](#yt-to-token-trading)

### swapExactYtForToken[​](#swapexactytfortoken)

Swaps an exact amount of YT tokens for any supported token.

```
function swapExactYtForToken(    address receiver,    address market,    uint256 exactYtIn,    TokenOutput calldata output,    LimitOrderData calldata limit) external returns (uint256 netTokenOut, uint256 netSyFee, uint256 netSyInterm)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive tokens |
| market | `address` | Pendle market address |
| exactYtIn | `uint256` | Exact amount of YT tokens to swap |
| output | [`TokenOutput`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#tokenoutput) | Token output configuration |
| limit | [`LimitOrderData`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#limitorderdata) | Limit order configuration |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netTokenOut | `uint256` | Amount of tokens received |
| netSyFee | `uint256` | Trading fees paid in SY |
| netSyInterm | `uint256` | SY tokens before conversion |

**Use Case**
Most common function for selling YT tokens to receive tokens. The function swaps YT for SY (first filling available limit orders, then using the AMM), then converts SY to your desired token.

### swapExactYtForSy[​](#swapexactytforsy)

Swaps an exact amount of YT tokens for SY tokens.

```
function swapExactYtForSy(    address receiver,    address market,    uint256 exactYtIn,    uint256 minSyOut,    LimitOrderData calldata limit) external returns (uint256 netSyOut, uint256 netSyFee)
```

**Input Parameters**

| Name | Type | Description |
| --- | --- | --- |
| receiver | `address` | Address to receive SY tokens |
| market | `address` | Pendle market address |
| exactYtIn | `uint256` | Exact amount of YT tokens to swap |
| minSyOut | `uint256` | Minimum SY tokens to receive |
| limit | [`LimitOrderData`](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ApiReference/Types#limitorderdata) | Limit order configuration |

**Return Values**

| Name | Type | Description |
| --- | --- | --- |
| netSyOut | `uint256` | SY tokens received |
| netSyFee | `uint256` | Trading fees paid in SY |

**Use Case**
Direct and efficient method for selling YT tokens to receive SY tokens.

## Integration Examples[​](#integration-examples)

### Buying YT-sUSDe with USDe[​](#buying-yt-susde-with-usde)

```
// Swap 1000 USDe for YT-sUSDe tokensrouter.swapExactTokenForYt(    msg.sender,    PT_SUSDE_MARKET_ADDRESS,    minYtOut,    createDefaultApproxParams(),    createTokenInputSimple(USDE_ADDRESS, 1000e18),    createEmptyLimitOrderData());
```

### Selling YT-sUSDe for USDe[​](#selling-yt-susde-for-usde)

```
// Swap YT-sUSDe tokens for USDerouter.swapExactYtForToken(    msg.sender,    PT_SUSDE_MARKET_ADDRESS,    ytAmount,    createTokenOutputSimple(USDE_ADDRESS, minUsdeOut),    createEmptyLimitOrderData());
```

### Direct SY to YT Trading[​](#direct-sy-to-yt-trading)

```
// Swap SY tokens directly for YT tokensrouter.swapExactSyForYt(    msg.sender,    MARKET_ADDRESS,    syAmount,    minYtOut,    createDefaultApproxParams(),    createEmptyLimitOrderData());
```