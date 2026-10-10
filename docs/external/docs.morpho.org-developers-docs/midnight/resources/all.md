# Midnight: Developer Resources

> Source: https://docs.morpho.org/developers/midnight/resources/all

---

# Midnight: Developer Resources

This page is your central hub for all the tools, links, and data sources you need to build on Morpho Midnight.

## [Data & Contracts](#data--contracts)

These resources are for interacting directly with the blockchain.

- **Contract Specifications**: For detailed function signatures, events, and errors, refer to the canonical contract specs:

  - [**Midnight Core Contract**](https://github.com/morpho-org/midnight/blob/main/src/Midnight.sol): immutable fixed-rate lending primitive via isolated permissionless markets
  - [**Midnight Bundles**](https://github.com/morpho-org/bundles/blob/main/src/midnight/MidnightBundlesV1.sol): atomic multi-step transactions (e.g., supply collateral + take in one call)
- **GitHub Repositories**:

  - [**Midnight**](https://github.com/morpho-org/midnight): The core protocol contracts (Midnight.sol, interfaces, libraries).

## [Integration Methods](#integration-methods)

These tools provide easier access to onchain data for frontends, backends, and analytics.

- **Midnight REST API**: Indexed onchain state (markets, positions, transactions, offer groups, and performance data).

  - **API Reference**: [Morpho Midnight API examples](https://docs.morpho.org/developers/api/morpho-midnight/)
  - **Base URL**: `https://api.morpho.org/v0/midnight/`
  - **Tutorials:**

    - [Lend at a fixed rate](https://docs.morpho.org/developers/midnight/tutorials/lend-at-a-fixed-rate/)
    - [Borrow at a fixed rate](https://docs.morpho.org/developers/midnight/tutorials/borrow-at-a-fixed-rate/)
    - [Redeem lend at maturity](https://docs.morpho.org/developers/midnight/tutorials/redeem-lend-at-maturity/)
    - [Exit borrow at maturity](https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-by-repaying-in-full-at-maturity/)
    - [Exit lend early](https://docs.morpho.org/developers/midnight/tutorials/exit-lend-early/)
    - [Exit borrow early](https://docs.morpho.org/developers/midnight/tutorials/exit-borrow-early/)
  - **Guides:**

    - [Monetize your Midnight product](https://docs.morpho.org/developers/midnight/guides/monetize-midnight-product/)
- [**Morpho SDK - Midnight**](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/): ready-to-send Midnight taker, maker, and position-maintenance transactions, plus the low-level toolkit for constructing offers, computing ticks, and encoding payloads.
- [**Midnight Quoter bot**](https://docs.morpho.org/developers/ecosystem/bots-and-automations/#midnight-quoter-bot): see the canonical bot overview, source code, CLI, and setup references.

## [Other](#other)

- **Validation Rules Reference**: Full table of Router [mempool rules](https://docs.morpho.org/developers/midnight/concepts/mempool-router/#validating-offers) (what the Router checks before indexing an offer)

[Guide: How to Monetize Your Midnight Product

Previous Page

](https://docs.morpho.org/developers/midnight/guides/monetize-midnight-product/)[Get Started

Next Page

](https://docs.morpho.org/developers/earn/get-started/)