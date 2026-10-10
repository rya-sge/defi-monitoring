# Borrow: Developer Resources

> Source: https://docs.morpho.org/developers/borrow/resources/all

---

# Borrow: Developer Resources

This page is your central hub for all the tools, links, and data sources you need to build on Morpho's Borrow product (Morpho Markets).

## [Onchain Data & Contracts](#onchain-data--contracts)

These resources are for interacting directly with the blockchain.

- **Market Parameters**: Every Morpho Market is defined by 5 immutable parameters. The easiest way to fetch these for all markets is via the [Morpho API](https://docs.morpho.org/developers/borrow/tutorials/get-data/#get-data).
- **Contract Specifications**: For detailed function signatures, events, and errors, refer to the canonical contract specs:

  - [Morpho Core Contract](https://docs.morpho.org/get-started/resources/contracts/morpho/)
  - [Bundles](https://docs.morpho.org/developers/contracts/bundles/)
- **GitHub Repositories**:

  - [`morpho-blue`](https://github.com/morpho-org/morpho-blue): The core protocol contracts.

## [Offchain Data & Tools](#offchain-data--tools)

These tools provide easier access to onchain data for frontends, backends, and analytics.

- **Morpho API (Recommended)**: The simplest way to fetch comprehensive data about markets, their states, APYs, and user positions.

  - **API Playground**: [api.morpho.org/graphql](https://api.morpho.org/graphql)
  - **Tutorial**: [Using the API for Markets](https://docs.morpho.org/developers/borrow/tutorials/get-data/#get-data)
- **SDKs**: A suite of TypeScript libraries to accelerate your development.

  - **`@morpho-org/morpho-sdk`**: The default abstraction layer - ready-to-send transactions, plus core entity classes (`@morpho-org/morpho-sdk/entities`) and Viem-based fetchers (`@morpho-org/morpho-sdk/fetch`) for easy onchain data retrieval.
  - **Vault V2 Public Allocator**: Use the [`@morpho-org/morpho-sdk`](https://www.npmjs.com/package/@morpho-org/morpho-sdk), the [Vault V2 guide](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/), and the [Blue Public Allocator source](https://github.com/morpho-org/vault-v2/tree/main/src/periphery/blue-public-allocator).
  - **Learn more**: [Introduction to Morpho SDKs](https://docs.morpho.org/developers/sdks/get-started/)

## [Code & Examples](#code--examples)

- **Solidity Snippets**: The [`morpho-snippets`](https://github.com/morpho-org/morpho-snippets) repository contains simple, educational Solidity contracts for common market interactions.
- **Liquidation Bots**: For advanced developers, the community has provided open-source liquidation bot examples.
- **Learn more**: [Community Liquidations Resources](https://docs.morpho.org/developers/ecosystem/bots-and-automations/#community-implementations)

[Guide: How to Monetize Your Borrow Product

Previous Page

](https://docs.morpho.org/developers/borrow/guides/monetize-borrow-product/)[Get Started

Next Page

](https://docs.morpho.org/developers/rewards/get-started/)