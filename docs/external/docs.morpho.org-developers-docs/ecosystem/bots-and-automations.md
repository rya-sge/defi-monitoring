# Bots and Automations

> Source: https://docs.morpho.org/developers/ecosystem/bots-and-automations

---

# Bots and Automations

Bots and automations built by Morpho and the community for liquidations, quoting, and vault reallocation.

New to Morpho liquidations? Start with the [Liquidation concept section](https://docs.morpho.org/learn/concepts/liquidation/).

## [Maintained by Morpho](#maintained-by-morpho)

These bots are provided as-is, without any warranty. The Morpho Association is not responsible for any potential loss of assets resulting from the use of these bots, including (but not limited to) gas fees, failed transactions, liquidations or reallocations on malicious or misconfigured markets.

### [Blue liquidation bot](#morpho-blue-liquidation-bot)

TypeScript & Solidity · by [Morpho Association](https://github.com/morpho-org)

An ecosystem-backstop liquidation bot for Morpho Blue. Discovers borrowers through the Morpho GraphQL API, reads current on-chain state, and simulates liquidation transactions before submission. See the repository for supported chains, configuration, and limitations.

[morpho-org/morpho-bots (Blue liquidation)](https://github.com/morpho-org/morpho-bots/tree/main/bots/blue-liquidation)

### [Midnight liquidation bot](#midnight-liquidation-bot)

TypeScript & Solidity · by [Morpho Association](https://github.com/morpho-org)

An off-chain liquidation bot for Morpho Midnight. Monitors candidate borrowers, checks their current state, and simulates liquidation transactions before submission. See the repository for supported chains, configuration, and limitations.

[morpho-org/morpho-bots (Midnight liquidation)](https://github.com/morpho-org/morpho-bots/tree/main/bots/midnight-liquidation)

### [Midnight Quoter bot](#midnight-quoter-bot)

TypeScript · by [Morpho Association](https://github.com/morpho-org)

A reference bot for Midnight makers. It validates setup, bootstraps lending positions, and maintains two-sided rate ladders around a reference rate. Start in read-only mode to inspect intended actions before enabling signing. See the repository for configuration and operating limits.

The CLI is available as [`@morpho-org/quoter`](https://www.npmjs.com/package/@morpho-org/quoter).

[morpho-org/morpho-bots (Midnight Quoter)](https://github.com/morpho-org/morpho-bots/tree/main/bots/quoter-bot)

### [Vault V2 Reallocation bot](#vault-v2-reallocation-bot)

TypeScript · by [Morpho Association](https://github.com/morpho-org)

Automates Morpho Vault V2 reallocations using RPC calls and the Morpho API. Supports configurable strategies for balancing utilization across markets. Check the repository's vault and adapter assumptions, supported chains, configuration, and limitations before deployment.

[morpho-org/vault-v2-reallocation-bot](https://github.com/morpho-org/vault-v2-reallocation-bot)

## [Liquidator: community implementations](#community-implementations)

The content provided in this document is contributed by the community and is shared as examples. Morpho Association nor author of the repository cannot be held responsible for any losses or damages that may result from the use of this information. Users are advised to conduct their own research and exercise caution when applying any strategies or methods described herein.

### [Blue liquidator in Rust](#rust-liquidator)

Rust & Solidity · by [etherhood](https://github.com/etherhood/)

This contribution presents a detailed strategy for liquidations using Rust and Solidity.

[etherhood/Liquidator-Morpho](https://github.com/etherhood/Liquidator-Morpho)

### [Blue liquidator in Go](#go-liquidator)

Go & Solidity · by [zach030](https://github.com/zach030/)

This contribution presents a detailed strategy for liquidations using Go and Solidity.

[zach030/morpho-liquidator-bot](https://github.com/zach030/morpho-liquidator-bot)

## [Get listed](#get-listed)

If you want to be displayed here, please reach out via the chatbox on **[help.morpho.org](https://help.morpho.org)**.

[Community Oracles

Previous Page

](https://docs.morpho.org/developers/ecosystem/oracles/)[Data Dashboards

Next Page

](https://docs.morpho.org/developers/ecosystem/data-dashboards/)