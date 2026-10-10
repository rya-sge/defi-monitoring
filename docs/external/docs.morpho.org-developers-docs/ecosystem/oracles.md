# Community Oracles

> Source: https://docs.morpho.org/developers/ecosystem/oracles

---

# Community Oracles

Solidity oracle adapters and tools built by the community for use with Morpho markets. Most expose a Chainlink-compatible interface, for use as base or quote feeds with `MorphoChainlinkOracleV2Factory`.

New to Morpho oracles? Start with the [Oracle concept section](https://docs.morpho.org/learn/concepts/oracle/).

The content provided in this document is contributed by the community and is shared as examples. Morpho Association nor author of the repository cannot be held responsible for any losses or damages that may result from the use of this information. Users are advised to conduct their own research and exercise caution when applying any strategies or methods described herein.

## [At a glance](#at-a-glance)

| Integration | Prices | Made by |
| --- | --- | --- |
| [Chainlink](#chainlink) | Oracle evaluation framework | [Chainlink oracle documentation](https://docs.google.com/document/d/1bDVGzmTB0Sg22Jk6JzDliRZDvqcNZKLXoC-y5OloXdQ/edit?tab=t.4e7gxqq73srw) |
| [Pyth](#pyth) | Any Pyth price feed | [aditya520](https://github.com/aditya520) |
| [Pendle PT](#pendle-pt) | Pendle Principal Tokens | [Horace](https://github.com/horacepan) |
| [LST/LRT exchange rates](#lstlrt-exchange-rates) | ezETH, rsETH, swETH, rswETH, weETH | [frontier159](https://github.com/frontier159) |
| [sfrxETH exchange rate](#sfrxeth-exchange-rate) | sfrxETH/frxETH | [Horace](https://github.com/horacepan) |
| [f(x) Protocol](#fx-protocol) | fxUSD, rUSD, btcUSD, fETH, xETH, and more | [chiaki644](https://github.com/chiaki644) |
| [Origami](#origami) | Origami Finance assets | [TempleDAO](https://github.com/TempleDAO) |
| [Wildcat Market](#wildcat-market) | ERC-4626 wrapped Wildcat market tokens | [Wintermute Research](https://github.com/WintermuteResearch) |
| [Oval](#oval) | Wraps any Chainlink feed (OEV recapture) | [Oval](https://github.com/UMAprotocol) |
| [Ojo Yield Risk Engine](#ojo-yield-risk-engine) | Caps yield-asset appreciation | [Ojo](https://github.com/ojo-network) |

## [Oracle networks](#oracle-networks)

### [Chainlink](#chainlink)

by Chainlink Labs

Morpho Oracle evaluation framework documentation by [Chainlink](https://docs.google.com/document/d/1bDVGzmTB0Sg22Jk6JzDliRZDvqcNZKLXoC-y5OloXdQ/edit?tab=t.4e7gxqq73srw).

### [Pyth](#pyth)

by [aditya520](https://github.com/aditya520)

Morpho V1 oracle implementation backed by [Pyth](https://pyth.network) price feeds, created by the Pyth Data Association. Use it to build dedicated market oracles from any Pyth feed.

[pyth-network/pyth-morpho-wrapper](https://github.com/pyth-network/pyth-morpho-wrapper)

## [Yield-bearing & staked assets](#yield-bearing--staked-assets)

### [Pendle PT](#pendle-pt)

by [Horace](https://github.com/horacepan)

Wraps Pendle's PT oracle in Chainlink's `AggregatorV3` interface, plus a factory for deploying the adapter and Pendle's `SparkLinearDiscountOracle`. Usable as base or quote feeds with `MorphoChainlinkOracleV2Factory`.

[horacepan/morpho-blue-oracles @ pendle-adapter-factory](https://github.com/horacepan/morpho-blue-oracles/tree/pendle-adapter-factory)

### [LST/LRT exchange rates](#lstlrt-exchange-rates)

by [frontier159](https://github.com/frontier159)

Exchange-rate adapters against ETH for ezETH (Renzo), rsETH (Kelp), swETH and rswETH (Swell), and weETH (ether.fi).

[frontier159/morpho-blue-oracles @ lrt-oracles](https://github.com/frontier159/morpho-blue-oracles/tree/lrt-oracles)

### [sfrxETH exchange rate](#sfrxeth-exchange-rate)

by [Horace](https://github.com/horacepan)

sfrxETH/frxETH exchange-rate adapter following the wstETH-stETH pattern, using `pricePerShare` instead of `getPooledEthByShares`.

[horacepan/morpho-blue-oracles @ sfrxeth-exchange-rate-adapter](https://github.com/horacepan/morpho-blue-oracles/tree/sfrxeth-exchange-rate-adapter)

## [Protocol-specific adapters](#protocol-specific-adapters)

### [f(x) Protocol](#fx-protocol)

by [chiaki644](https://github.com/chiaki644)

Supports all f(x) protocol tokens: fxUSD, rUSD, btcUSD, fETH, xETH, xstETH, xfrxETH, xezETH, xeETH, xWBTC. Token addresses in the [f(x) deployments list](https://github.com/AladdinDAO/deployments/blob/main/deployments.mainnet.md).

[AladdinDAO/morpho-blue-oracles @ feat/fxusd-adapter](https://github.com/AladdinDAO/morpho-blue-oracles/tree/feat/fxusd-adapter)

### [Origami](#origami)

by [TempleDAO](https://github.com/TempleDAO)

Chainlink-interface-compliant feeds by TempleDAO for Origami Finance assets.

[TempleDAO/origami-oracle-adapters](https://github.com/TempleDAO/origami-oracle-adapters)

### [Wildcat Market](#wildcat-market)

by [Wintermute Research](https://github.com/WintermuteResearch)

Prices ERC-4626 wrapped Wildcat market tokens. Deployers can define derisking parameters as a function of delinquency length, based on expected creditworthiness.

[WintermuteResearch/wildcat-market-oracle](https://github.com/WintermuteResearch/wildcat-market-oracle)

## [Risk & MEV tools](#risk--mev-tools)

### [Oval](#oval)

by [Oval](https://github.com/UMAprotocol)

OEV recapture tool by UMA. Wraps existing oracle feeds and outputs Chainlink-compliant prices; deployable via factory for Morpho markets.

[UMAprotocol/oval-contracts](https://github.com/UMAprotocol/oval-contracts)

### [Ojo Yield Risk Engine](#ojo-yield-risk-engine)

by [Ojo](https://github.com/ojo-network)

Puts a static cap on how much a yield asset can appreciate over time, mitigating ERC-4626 donation/inflation attacks where users artificially increase a vault token's value in order to borrow more against it.

[ojo-network/yield-risk-engine](https://github.com/ojo-network/yield-risk-engine)

## [Get listed](#get-listed)

Built an oracle adapter for Morpho? Reach out via the chatbox on **[help.morpho.org](https://help.morpho.org)**.

[llms.txt

Previous Page

](https://docs.morpho.org/developers/agents/llms/)[Bots and Automations

Next Page

](https://docs.morpho.org/developers/ecosystem/bots-and-automations/)