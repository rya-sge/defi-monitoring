# Morpho SDKs

> Source: https://docs.morpho.org/developers/sdks/get-started

---

# Morpho SDKs

The Morpho Software Development Kits (SDKs) are a suite of TypeScript packages for building on the Morpho protocol - from a full-featured DeFi application to a liquidation bot, an indexer, or a simple data dashboard.

The entrypoint is the **[Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/)** - the default abstraction layer that produces ready-to-send transactions for **[VaultV2](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/)**, **[Variable Rate - Blue Market](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/)** (Morpho Blue), and **[Fixed Rate - Midnight Market](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/)** in a single, consistent surface. When you need raw entity classes, low-level fetchers, or custom calldata composition, the Morpho SDK ships those primitives as subpath exports and dependencies, so you never have to reach past it.

**New here?** Go straight to the [Morpho SDK](https://docs.morpho.org/developers/sdks/morpho-sdk/) - it's what powers Morpho's own consumer surfaces and is the SDK you almost certainly want.

## [The Morpho SDK](#the-morpho-sdk)

[**`@morpho-org/morpho-sdk`**](https://docs.morpho.org/developers/sdks/morpho-sdk/) - the **default and recommended SDK** for application integrators. It is the abstraction layer that simplifies the Morpho protocol:

- One consistent abstraction layer across **[VaultV2](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/)**, **[Variable Rate - Blue Market](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/)** (Morpho Blue), and **[Fixed Rate - Midnight Market](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/)**, with VaultV1 (MetaMorpho) supported under the hood for migrations / liquidity reallocation
- Builds final, deep-frozen `viem` `Transaction` objects - no calldata wrangling
- Handles ERC-20 approvals, **Permit / Permit2** signatures, and **Morpho `setAuthorization`** for BlueBundlesV1 via a unified `getRequirements()` flow
- Routes every Blue and Vault write through **Morpho Bundles** (`BlueBundlesV1`, `VaultBundlesV1`, `VaultExitBundlesV1`) for you - atomic supply+borrow, repay+withdraw, Blue-to-Blue refinance, V1→V2 migration
- Slippage-protected where it applies: vault deposits are share-price protected (`maxSharePrice`), and Blue borrow, collateral-withdrawal, and refinance legs enforce an LLTV buffer
- Optional **shared-liquidity reallocations** through the Vault V2 `BluePublicAllocator` for borrow, withdraw, supply+borrow, and refinance flows - see the [Vault V2 Public Allocator guide](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/)
- **Midnight fixed-rate flows** - take offers, publish maker offers, and maintain positions on Morpho's fixed-rate, fixed-term orderbook
- Strict TypeScript, no `any`, dedicated error classes for every failure mode

```
pnpm add @morpho-org/morpho-sdk viem
```

→ [Read the Morpho SDK guide](https://docs.morpho.org/developers/sdks/morpho-sdk/) · [Source on GitHub](https://github.com/morpho-org/sdks/tree/main/packages/morpho-sdk) · [Package on npm](https://www.npmjs.com/package/@morpho-org/morpho-sdk)

## [Fixed rate (Midnight)](#fixed-rate-midnight)

Midnight - fixed-rate, fixed-term lending through signed maker offers matched in an onchain orderbook - is a surface **of the Morpho SDK**, not a separate SDK: the [Midnight page](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/) covers taker, maker, and position-maintenance transactions through the same `getRequirements` / `buildTx` flow.

Underneath, the Morpho SDK ships the low-level Midnight toolkit (the formerly standalone Midnight SDK, now folded in) and re-exports most of its surface on its own subpaths - `/midnight-api`, `/abis`, `/constants`, `/utils`, and `/errors`. Reach for the toolkit directly when you need offer construction, ratification, books and quotes, or tick math:

→ [Read the Midnight toolkit guide](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/) · [Source on GitHub](https://github.com/morpho-org/sdks/tree/main/packages/midnight-sdk)

## [Reaching below the abstraction layer](#reaching-below-the-abstraction-layer)

When you need to reach below the abstraction layer - for raw entity classes, low-level on-chain fetchers, custom calldata composition, or simulation pipelines - the Morpho SDK ships those primitives as subpath exports, so you never need a separate package:

- **`@morpho-org/morpho-sdk/entities`** - Core entity classes (`Market`, `Vault`, `Position`) and offchain computations. The foundation of the rest of the stack.
- **`@morpho-org/morpho-sdk/fetch`** - Viem-based fetchers for live on-chain data.
- **`@morpho-org/morpho-sdk/abis`**, **`/addresses`**, **`/constants`**, **`/errors`**, **`/types`** - ABIs, deployment addresses, protocol constants, typed error classes, and shared types.
- **`@morpho-org/morpho-sdk/midnight-api`** - The Midnight HTTP API helpers (books, quotes, takeable offers, mempool validation).

See the [Morpho SDK guide](https://docs.morpho.org/developers/sdks/morpho-sdk/) for the full surface.

## [Where next](#where-next)

- **Recommended starting point:** [Morpho SDK guide](https://docs.morpho.org/developers/sdks/morpho-sdk/)
- **Vault deposits & withdrawals:** [Vault guide](https://docs.morpho.org/developers/sdks/morpho-sdk/vault/)
- **Variable-rate lending & borrowing:** [Blue guide](https://docs.morpho.org/developers/sdks/morpho-sdk/blue/)
- **Fixed-term lending:** [Midnight toolkit guide](https://docs.morpho.org/developers/sdks/morpho-sdk/midnight/)
- **Source code:** [`morpho-org/sdks`](https://github.com/morpho-org/sdks) - the SDK monorepo containing [`@morpho-org/morpho-sdk`](https://github.com/morpho-org/sdks/tree/main/packages/morpho-sdk) and the [Midnight toolkit](https://github.com/morpho-org/sdks/tree/main/packages/midnight-sdk)
- **Need help?** Reach out via the chat on **[help.morpho.org](https://help.morpho.org)**.

[Changelog

Previous Page

](https://docs.morpho.org/developers/api/changelog/)[Morpho SDK

Next Page

](https://docs.morpho.org/developers/sdks/morpho-sdk/)