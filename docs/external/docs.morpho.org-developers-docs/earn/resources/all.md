# Earn: Developer Resources

> Source: https://docs.morpho.org/developers/earn/resources/all

---

# Earn: Developer Resources

This page is your central hub for all the tools, links, and data sources you need to build on Morpho's Earn product (Morpho Vaults).

## [Onchain Data & Contracts](#onchain-data--contracts)

These resources are for interacting directly with the blockchain.

- **Vault Addresses**: While you can find the factory (the main address used to deploy all vaults) list of all core contracts on the main [Addresses page](https://docs.morpho.org/get-started/resources/addresses/), the best way to dynamically fetch all deployed Morpho vaults is via the [Morpho API](https://docs.morpho.org/developers/earn/tutorials/get-data/).
- **Contract Specifications**: For detailed function signatures, events, and errors, refer to the canonical [Morpho Vault V2 Contract Specs](https://docs.morpho.org/get-started/resources/contracts/morpho-vaults-v2/).
- **GitHub Repositories**:

  - [`vault-v2`](https://github.com/morpho-org/vault-v2): The canonical Morpho Vault V2 implementation.

## [Offchain Data & Tools](#offchain-data--tools)

These tools provide easier access to onchain data for frontends, backends, and analytics.

- **Morpho API (Recommended)**: The simplest way to fetch comprehensive data about vaults, their states, APYs, and user positions.

  - **API Playground**: [api.morpho.org/graphql](https://api.morpho.org/graphql)
  - **Tutorial**: [Using the API for Vaults](https://docs.morpho.org/developers/earn/tutorials/get-data/)
- **SDKs**: A suite of TypeScript libraries to accelerate your development.

  - **`@morpho-org/morpho-sdk`**: The default abstraction layer - ready-to-send transactions, plus core entity classes for Vaults and Markets (`@morpho-org/morpho-sdk/entities`) and Viem-based fetchers (`@morpho-org/morpho-sdk/fetch`).
  - **`@morpho-org/simulation-sdk`**: Simulates user interactions to predict outcomes before sending a transaction.
  - **Learn more**: [Introduction to Morpho SDKs](https://docs.morpho.org/developers/sdks/get-started/)

## [Code & Examples](#code--examples)

- **Solidity Snippets**: The [`morpho-snippets`](https://github.com/morpho-org/morpho-snippets) repository contains simple, educational Solidity contracts for common vault interactions.

[Best Practices for Vault Integrators

Previous Page

](https://docs.morpho.org/developers/earn/vault-ux/best-practices/)[Get Started

Next Page

](https://docs.morpho.org/developers/borrow/get-started/)