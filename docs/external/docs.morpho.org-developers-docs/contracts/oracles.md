# Oracles

> Source: https://docs.morpho.org/developers/contracts/oracles

---

# Oracles

[Morpho Chainlink Oracle V2](https://github.com/morpho-org/morpho-blue-oracles/tree/main/src/morpho-chainlink)

## [Basics](#basics)

Oracles are contracts that can be used as oracles for markets on Morpho. The oracles implement the IOracle interface defined in [IOracle.sol](https://github.com/morpho-org/morpho-blue/blob/main/src/interfaces/IOracle.sol).

They return the price of 1 asset of collateral token quoted in 1 asset of loan token.

## [price](#price)

```
function price() external view returns (uint256);
```

Returns the price of 1 asset of collateral token quoted in 1 asset of loan token, scaled by 1e36.

- It corresponds to the price of 10**(collateral token decimals) assets of collateral token quoted in 10 **(loan token decimals) assets of loan token with `36 + loan token decimals - collateral token decimals` decimals of precision.

### [Return values:](#return-values)

| Name | Type | Description |
| --- | --- | --- |
| `price` | uint256 | The price rate of 1 asset of collateral token quoted in 1 asset of loan token (scaled by 1e36). |

## [MorphoChainlinkOracleV2](#morphochainlinkoraclev2)

This is an oracle that uses Chainlink-interface-compliant feeds to provide price data.

This oracle handles the following cases among others (let's say that our pair is A/B):

- A/B is a feed (typically, stETH/ETH).
- B/A is a feed (typically, ETH/USDC).
- A/C and B/C are feeds (typically, stETH/ETH and USDC/ETH).
- A/C, C/D and B/D are feeds (typically, WBTC/BTC, BTC/USD, USDC/USD).
- A/D, and B/C, C/D are feeds (typically, USDC/USD, WBTC/BTC, BTC/USD).
- A/C, C/D and B/E, E/D are feeds.
- A/C and C/B are feeds (typically, WBTC/BTC and BTC/ETH).
- A'/C and B/C are feeds, and there is an exchange rate between A and A'. (typically A=sDAI and A'=DAI).

## [WstETH/stETH Exchange Rate Adapter](#wstethsteth-exchange-rate-adapter)

A specific implementation, the `WstEthStEthExchangeRateChainlinkAdapter`, provides the exchange rate between wstETH and stETH as a Chainlink-interface-compliant feed.

This adapter is deployed on Ethereum Mainnet at the address [0x905b7dAbCD3Ce6B792D874e303D336424Cdb1421](https://etherscan.io/address/0x905b7dabcd3ce6b792d874e303d336424cdb1421#code).

## [MorphoChainlinkOracleV2Factory](#morphochainlinkoraclev2factory)

This factory deploys `MorphoChainlinkOracleV2` instances.

The factory facilitates the creation and indexing of MorphoChainlinkOracleV2 oracles. This factory contract streamlines the process of deploying new oracles, catering to various market pairs without the need to deploy individual contracts manually for each pair.

## [Implementation](#implementation)

> [Morpho Chainlink Oracle V2 Github repository](https://github.com/morpho-org/morpho-blue-oracles/tree/main/src/morpho-chainlink)

The contract implements the [Oracle interface](https://github.com/morpho-org/morpho-blue/blob/main/src/interfaces/IOracle.sol) to fit Morpho specifications:

## [Immutables](#immutables)

- `BASE_VAULT`: baseVault. Pass address zero to omit this parameter.
- `BASE_VAULT_CONVERSION_SAMPLE`: Base vault conversion sample.
- `BASE_FEED_1`: First base feed. Pass address zero if the price = 1.
- `BASE_FEED_2`: Second base feed. Pass address zero if the price = 1.
- `BASE_TOKEN_DECIMALS`: Base token decimals.
- `QUOTE_VAULT`: Quote vault. Pass address zero to omit this parameter.
- `QUOTE_VAULT_CONVERSION_SAMPLE`: The sample amount of quote vault shares used to convert to underlying. Pass 1 if the quote asset is not a vault. Should be chosen such that converting `quoteVaultConversionSample` to assets has enough precision.
- `QUOTE_FEED_1`: First quote feed. Pass address zero if the price = 1.
- `QUOTE_FEED_2`: Second quote feed. Pass address zero if the price = 1.
- `QUOTE_TOKEN_DECIMALS`: Quote token decimals.

## [Assumptions](#assumptions)

Here is the list of assumptions that guarantees the oracle behaves as expected:

- The vaults, if set, are ERC4626-compliant.
- The feeds, if set, are Chainlink-interface-compliant.
- Decimals passed as argument are correct.
- The base vaults's sample shares quoted as assets and the base feed prices don't overflow when multiplied.
- The quote vault's sample shares quoted as assets and the quote feed prices don't overflow when multiplied.

[Blue Public Allocator

Previous Page

](https://docs.morpho.org/developers/contracts/blue-public-allocator/)[Interest Rate Models

Next Page

](https://docs.morpho.org/developers/contracts/irm/)