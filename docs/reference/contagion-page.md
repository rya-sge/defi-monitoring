# The Contagion page

**Question it answers:** *which single failure would hit the most of my book at once?*

Open it at `/contagion` in the web app: [belem.fuca.ch/contagion](https://belem.fuca.ch/contagion), or `http://localhost:5173/contagion` after `pnpm dev`. Code: `web/src/routes/ContagionPage.tsx`, with the calculation in `web/src/lib/cross.ts` (`crossView`).

A vault page shows one vault's dependencies. This page puts all the vaults of the dependency graph side by side. It keeps only the oracles, feeds, assets, markets, pools, admins and off-chain parties that **two or more vaults** depend on. Those are the points where one failure spreads to several vaults: the contagion channels.

## How it is computed

Everything comes from the dependency graph (`GET /api/graph`, built by `riskdep graph`). The page does no network call of its own and no modelling.

1. **Vaults.** Every Vault V2 in the graph.
2. **What each vault depends on.** Every node reachable from the vault by following the graph's edges: vault → markets it supplies → collateral → oracle → feed → issuer, and so on.
3. **Exposure.** For each dependency, a vault's exposure is what it supplies into the markets that lead to that dependency. The amount is in loan units (USDC, USDT…) counted at par.
4. **Kept:** dependencies with two vaults or more, sorted by total exposure.
5. **Left out by default:** the loan tokens (USDC, USDT…), because every vault lending them depends on them, so they would top every list and hide the signal. Actors (other depositors, borrowers) are always left out.

**This is exposure, not loss.** The page says how much sits on top of each dependency. It doesn't say how likely a failure is or how much would be lost. The **Simulate** button and the Scenario lab answer that.

## Reading the page

**Header:** the number of vaults, the total they supply (the book), and the number of shared dependencies.

**Filters:** *All*, or one kind at a time (Oracles, Feeds, Assets, Markets, Pendle pools, Off-chain, Admins). Tick **Include loan tokens** to bring USDC and the like back in.

**The table, one row per shared dependency:**

| Column | Meaning |
|---|---|
| Dependency | The node, with the graph's icon and colour for its kind |
| Vaults | How many vaults depend on it; the three most exposed are named, then "+N" |
| Exposed | The total that those vaults supply into the markets leading to it |
| Share of vaults | Exposed ÷ everything the vaults supply: the part of the book one failure here would touch |
| Markets | How many distinct markets connect the vaults to it |
| Signals | The warnings already in the graph (below) |
| Simulate | Opens the Scenario lab with this dependency failing |

**Signals:** labels already set on the node by `riskdep graph`. Hover a label for its explanation.

| Signal | Meaning | Colour |
|---|---|---|
| Pharos grade (e.g. `F 38`) | The issuer's stablecoin safety grade from Pharos | red for D or F, amber for C |
| Stale | The feed last updated later than its own update rhythm | red |
| Constant price | The oracle doesn't follow the market (hard-coded or NAV), so a depeg liquidates nobody and the loss lands on the lenders | amber |
| Concentrated | The protocol holds a large share of its category's on-chain TVL (DefiLlama) | amber |
| Shared | An oracle read by several markets: if it fails, they all fail at once | — |
| Supply | A large share of the token's supply is posted as collateral on Morpho | — |

**A row, clicked:** opens the breakdown. Each line is one vault and one market, with the amount supplied and its share of this dependency's exposure. A market's name links to its Market page.

**The selected vault** (the selector in the top bar): rows it depends on carry a dark bar on their left edge, and its chip is outlined. Simulate then uses this vault; otherwise it uses the most exposed vault of the row.

**Simulate, by kind:**

| Kind | Scenario opened |
|---|---|
| Oracle or feed | the oracle reads 10 % low (`trace=<node>:reads-low:10%`) |
| Asset | the token falls 30 % (`shock=token=<asset>:0.3`) |
| Market | the market's largest borrower defaults, 50 % recovered (`shock=borrower=<market>:0.5:1`) |
| Other kinds | no button |

## Example: the public site

The public site runs on the committed fixture graph (`web/src/mocks/graph.json`): 16 Vault V2s, 556.7M supplied, and 35 shared dependencies. Its top rows:

| Dependency | Vaults | Exposed | Share | What it says |
|---|---|---|---|---|
| Morpho Blue | 16 | 556.7M | 100 % | Expected: every vault lends through Blue. A Blue bug hits the whole book |
| reserve issuer: United States Treasury | 16 | 556.7M | 100 % | The reserves behind the loan stablecoins |
| two "mint control" addresses | 12 | 132.9M | 23.9 % | Whoever controls these mints a token that a quarter of the book's markets depend on |
| Pendle V2 | 10 | 88.1M | 15.8 % | Signal *Concentrated* |
| reUSD, PT-reUSD, its Ojo feed and oracle, the Pendle reUSD pool, Re | 8 | 79.1M | 14.2 % | One stack shared by eight vaults; reUSD has a Pharos grade of **F 38** |
| USDe, Ethena USDe | 2 | 57.8M | 10.4 % | Pharos C+; Ethena is *Concentrated* |
| Blue PST/USDC | 3 | 38.0M | 6.8 % | *Constant price*: a PST depeg liquidates nobody |

The reUSD stack is the key point. A curator who looks at one vault at a time sees one PT-reUSD position. This page shows that eight vaults hold the same thing, behind one feed, with 79M exposed and the issuer graded F. One failure there is one loss across eight vaults, not eight separate losses.

## Limits

- **Par, not price:** USDC and USDT exposures are added one-for-one.
- **A whole market counts:** if a market depends on a node, everything the vault supplies into it counts as exposed, even when only part of the market's loss would reach the vault.
- **Only what's in the graph:** a dependency `riskdep graph` didn't discover isn't on the page. The fixture graph is a recorded snapshot, so the public site doesn't move with the chain. The local app with `VITE_USE_MOCKS=false` reads the API's current graph.
- **No joint loss or probability:** for those, use Simulate (the Scenario lab), `riskdep shock`, or `analyze --book`.
