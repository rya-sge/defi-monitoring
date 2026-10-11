# Risk and impact monitoring: analysis

Design note for monitoring the risk of positions on the [Morpho](https://morpho.org/) protocol (Morpho Blue markets and Vault V2), and the state of this repository against it. It has four parts: the model (a dependency graph), how the impact of an incident is measured, what has to be monitored, and how a response could be executed. A final section lists the gaps of the current implementation.

Status column used throughout: **done** (implemented and tested), **partial**, **missing**.

## Contents

- [1. Dependency graph](#1-dependency-graph)
- [2. Impact](#2-impact)
- [3. Monitoring](#3-monitoring)
- [4. Execution](#4-execution)
- [5. Gaps in this project](#5-gaps-in-this-project)

## 1. Dependency graph

A position is modelled as a graph. Nodes are the things that can fail; edges say who depends on whom, and are derived from on-chain attributes and addresses, not drawn by hand.

### Node types

The types separate **who** holds capital, **where** the capital sits, **what** it is held in, **how** it is priced, and **who decides**:

| Type | What it is | Morpho examples | Read from |
|---|---|---|---|
| **Actor** | whose capital is at stake: it supplies, borrows or deposits, and can move | an address with positions; a Vault V2 (with its adapters folded in); a Vault V1 (MetaMorpho) supplying a market | the user's positions, `parentVault()` of an adapter, `MORPHO()` and `withdrawQueueLength()` for a V1 vault |
| **Pool** | where liquidity sits and is priced; it never moves on its own | Morpho Blue market, Pendle PT/SY pool | market id, Pendle API |
| **Asset** | a token | loan token, collateral token, the yield source behind a PT; a vault's share token **only** when another protocol reuses it (as collateral, or in an oracle's conversion) | `MarketParams.loanToken` / `collateralToken`, Pendle `underlyingAsset`, an oracle's `BASE_VAULT()` |
| **Oracle** | how a market prices its collateral | the market's oracle and the price feeds it reads | `MarketParams.oracle`, then the oracle's own getters |
| **Admin** | who decides for an actor, without their own capital at stake | vault owner, curator, allocators, sentinels; Blue owner; oracle and token admins | `owner()`, `curator()`, `isAllocator`, `isSentinel`, role events |

A vault is an **Actor** rather than a Pool because it behaves like a large lender: its allocators move its capital between markets without a timelock, and it can leave a market. Seen from a market's borrowers, a vault's withdrawal raises utilisation and the borrow rate, and stops other lenders from leaving. Its share token is a separate **Asset** node, and only when something else depends on it.

### Edges

An edge exists because an attribute of one node names another node:

| Edge | Derived from |
|---|---|
| actor (vault) → market: *supplies*, with the amount and its share of the market | `marketIds(i)` on the vault's `MorphoMarketV1AdapterV2`, `position(id, adapter)` |
| actor (lender) → market: *supplies* | the market's main suppliers (Morpho API), amounts from `position(id, supplier)`; an adapter is resolved to its vault with `parentVault()` |
| actor (address) → market: *borrows from*, with debt, collateral and health factor | the user's `position(id, user)` |
| actor (address) → vault: *deposits in* | vault shares, `balanceOf(user)` |
| market → loan asset, collateral asset, oracle | the five `MarketParams` of the market id; *takes as collateral* carries the collateral of the market's borrowers |
| sibling market → the shared asset, oracle or feed | a Blue market no actor holds, found because it shares a held market's collateral, underlying or collateral-side price input, or lends that collateral (Morpho API `markets`, then `idToMarketParams` on-chain); it has no edge to the held market itself |
| asset → asset: *wraps* | an ERC-4626 share's `asset()` |
| oracle → feed: *reads*; oracle → vault share: *converts through* | the oracle's configuration (`BASE_FEED_1()`, `BASE_VAULT()` on a Morpho `ChainlinkOracleV2`) |
| collateral PT → Pendle pool → yield source | Pendle market data |
| admin → vault: *owns*, *curates*, *allocates*, *can de-risk* | the role getters and their change events (`SetCurator`, `SetIsAllocator`, …) |

### State in this repository

| Element | Status | Where |
|---|---|---|
| Graph for one PT borrow, with typed nodes (chain, issuer, asset, amm, oracle, lending, stable, off-chain) and the source of each node | done | `riskdep/discover.py` |
| Vault → adapters → markets → collateral / oracle / LLTV, read on-chain | done, as data structures rather than a graph object | `riskdep/vault.py` |
| A user's positions: Blue borrows and Vault V2 deposits | done | `riskdep/positions.py`, `riskdep/borrower.py` |
| Vaults and lenders as actors; the main suppliers of a borrower's markets (≥ 5 % of supply, up to 5 per market), vaults resolved through their adapter | done, in the `graph` command | `riskdep/graph.py` |
| Admin nodes: owner and curator on-chain, allocators and sentinels from the Morpho API, each confirmed with `isAllocator` / `isSentinel` | done, in the `graph` command | `riskdep/graph.py` |
| Oracle decomposed into feeds (Morpho `ChainlinkOracleV2` getters, feed `description()`) | done, in the `graph` command; custom oracles stay one node | `riskdep/graph.py` |
| Sibling markets: the Blue markets that share a held market's collateral, underlying or collateral-side price input, or lend that collateral, joined through the shared node | done, in the `graph` command (plan `2026-10-10-sibling-markets`); Blue only, one hop | `riskdep/siblings.py`, `riskdep/graph.py` |
| Oracle class on every market oracle and input: `price-tracking`, `constant-price` or `not classified`, with its basis | done, in the `graph` command | `riskdep/oracle_class.py` |
| Every Blue market node, held or sibling, with supply, borrow, the collateral of its borrowers and its liquidation curve | done, in the `graph` command | `riskdep/graph.py` (`market_risk`) |
| One graph shared by `analyze` and `watch` | missing: the `graph` command draws the graph, the rules still work on their own structures | — |

### Example

`docs/examples/graph-example.html` is an interactive rendering of a real graph, generated by `python3 -m riskdep graph --example` at block 26,162,421 (`docs/examples/graph-example.json` holds the same data). It has 100 nodes and 134 edges:

- the demo borrower `0xdf81…2730` with its 6 Blue borrows, and the main lenders of each of those markets;
- Sentora RLUSD Main with its largest depositor, its 10 markets and its five role holders.

Click a node to isolate its neighbours and read its details; edge width follows the amount carried.

Three dependencies are visible in it that no single-position view shows:

- **One lender under a borrow.** The borrower's PT-sUSDE-26NOV2026/USDC market (3.41M USDC of debt) is funded entirely by one Vault V2, Pendle Ecosystem USDC, through its adapter (7.76M USDC, 100 % of the supply). PT-fxSAVE-29OCT2026/USDC is 89 % funded by one vault. If that vault's allocator moves the liquidity elsewhere, which needs no timelock, the market's utilisation and borrow rate jump.
- **One feed under a whole vault.** The oracles of all 10 Sentora markets read the same `RLUSD / USD` feed. A fault in that feed misprices every market of the vault at once.
- **One feed under two borrows.** The borrower's PT-reUSD/USDC (3.67M USDC) and PT-reUSD/USDT (1.20M USDT) markets both read the same Ojo PT feed, so one feed decides the liquidation of 4.9M of debt.

Any address or vault can be drawn the same way: `python3 -m riskdep graph --user <address> --vault <vault> --out out/graph.html`.

## 2. Impact

The question is "if this node fails, how much does each position lose?". Four ingredients:

### Exposure (TVL on edges)

Every edge carries the value that flows along it: a vault's supplied assets in each market, a borrower's collateral and debt, a vault's share of a market's supply. The loss carried to a position is the shock times its share of each edge on the path, for example a vault's share of a bad debt = bad debt × the vault's supply shares ÷ the market's total supply shares.

Status: **done** for the paths the tool follows (vault → market, borrower → market). It is computed per position, not stored on a shared graph.

### Liquidations per price change

For a market, the amount of collateral that becomes liquidatable for each oracle fall of 1 %, 2 %, … 20 % is the market's liquidation curve. It needs every borrower's position in the market, not only the user's. It says how much collateral would be sold into the market at once, and therefore how much price impact and bad debt a fall would cause.

Status: **done** for the watched markets (`riskdep/market_risk.py`): every borrower is listed, and each batch computes the debt liquidatable after a 2, 5, 10 and 20 % fall, with the bad debt it would leave. The `graph` command computes the same curve, with the collateral that would be sold, for every held and sibling market. The price impact of the cascade itself is not simulated.

### DEX liquidity and slippage

The cost of leaving, for the user or for liquidators, depends on how much collateral the market can absorb.

Status: **partial**. Real Pendle quotes for PT collateral, including a re-quote for a partial de-lever. The shock engine models the liquidators' side for PTs: two quote ladders per PT (into its pool, then the underlying for dollars), with the capacity beyond which liquidations cannot complete. Collateral that is not a PT, or the underlying of one, has no quote, so its sales move no price.

### Limiting the propagation

Following every edge of every node makes the graph explode, since every market touches USDC and Ethereum. Propagation stops by criteria:

- **Exposure floor:** do not follow an edge carrying less than a share of the position, e.g. 1 %.
- **Depth:** at most N hops from the position.
- **Severity floor:** stop when the shock carried falls below a threshold.
- **Shared terminal nodes:** the settlement chain and the main stablecoins are modelled once, as their own events, not expanded.

Status: **partial**. `analyze` uses a fixed set of layers per position, which acts as a depth limit. There is no general rule, because there is no general graph yet.

## 3. Monitoring

### Re-query every value?

No. Querying everything every block costs too much and gives no reason for a change. The tool combines two mechanisms:

- **Events say *that* something changed and *why*.** One `eth_getLogs` per batch, filtered by addresses and by market id as `topic1`.
- **One batched state read per batch says *what* the values are now,** at a single block, so they are consistent with each other. For one vault that is 104 `eth_call`s in a single JSON-RPC request.

Some values change without any event: oracle prices, accrued interest, the vault's `totalAssets()`. They are re-read every batch. Status: **done** (`riskdep/poller.py`, `vault.read_state`, `borrower.read_borrows`). Details: `docs/watch/how-a-block-is-analysed.md`.

### Token prices against the oracle

A market liquidates on its oracle's price, not on the market price. A gap between the two is either a lagging or broken oracle, or a market dislocation the oracle smooths.

| Check | Status |
|---|---|
| Oracle vs PT market price at analysis time, to infer whether the oracle follows the market | done (`analyze`), flagged ambiguous near par |
| Oracle moves between two reads (≥ 5 %) | done (`watch`) |
| Oracle that stops answering (`price()` reverts) | done (`watch --user`) |
| Oracle vs an independent market price (DefiLlama), at start and every 300 blocks | done (`riskdep/admin.py`), warn from a 3 % gap |
| Oracle class from its structure and its feeds' round history: does a market fall reach the price? | done in `graph` (`riskdep/oracle_class.py`); `analyze` still infers it from the price, `drain.py` does not use it (D70) |

### Positions and holders

| Check | Status |
|---|---|
| The user's borrows: HF, liquidation distance, rate, actions on their behalf | done (`watch --user`) |
| The user's vault deposits: exit capacity, losses, gates | done (`watch --vault`, `watch --user`) |
| Every borrower of the markets a vault holds: underwater positions, i.e. bad debt not yet written off | done: unrealised bad debt computed each batch, with the vault's and the depositor's share |
| **Large holders of a vault**: whose exit would drain its liquidity | missing |

### Admins: transactions, key variables, delayed execution

| Check | Status |
|---|---|
| Vault V2 timelocked changes: `Submit` decoded (function, target, value) with `executableAt`; `Accept`, `Revoke` | done |
| Vault V2 immediate changes: liquidity adapter, `maxRate`, caps lowered, allocators, fees, gates | done, as events |
| Market adapter timelocked calls (`burnShares`, skim recipient) | done |
| Timelock length and abdication of each function, which give the real warning time | done: read at start for every vault and market adapter; risk-increasing functions with no notice are flagged, and a `Submit` for one is critical |
| Morpho Blue owner actions (`SetOwner`, `EnableIrm`, `EnableLltv`, `SetFeeRecipient`) | done |
| Oracle admin: upgradeable oracles and feeds, Chainlink aggregator changes, ownership | done, from standard events and storage slots; a custom setter that emits no standard event is caught only if it changes a slot, owner or aggregator |
| Collateral and issuer admin: upgrade, pause, admin roles, outsized mints of the collateral and yield tokens, Pendle SY upgrades | done (`riskdep/admin.py`) |

## 4. Execution

Monitoring tells the user when to act. Acting quickly and safely needs several actions to land **atomically**, all or nothing, **under a condition** checked on-chain at execution time.

- **Atomic de-lever.** Morpho's Bundles execute a fixed chain of calls in one transaction against the caller's own position. `BlueBundlesV1RepayAndWithdrawCollateral` repays debt and withdraws collateral in one step, bounded by a `maxLtv` check, and the Bundle's entrypoints accept a signed Morpho authorisation so the Bundle can be authorised in the same transaction.
- **Batched admin actions.** Vault V2 exposes a `multicall` for batching admin calls from an externally owned account.
- **Conditional execution.** The action reverts unless its condition still holds when it is mined: the `maxLtv` bound of the repay-and-withdraw entrypoint is one such condition, and a Bundle's deadline bounds when it can land. A condition the Bundles do not offer, such as acting only while the health factor is below a level, needs a contract of the user's own, since Bundles act on `msg.sender`'s position and are not meant to be called by other contracts.
- **Simulation before sending.** The free RPC used here answers `eth_simulateV1` (verified on 2026-10-10), which returns the status and the logs of a call against the latest state. That is enough to check that a de-lever transaction would succeed and what it would emit, before signing it.

Status: **missing**. The tool alerts and never acts. Executing needs a signing key, which changes the security model of the tool: key storage, limits on what may be signed, and a human approval step. It belongs to a separate increment with its own design.

## 5. Gaps in this project

Gaps found while building and testing the tool, ranked by how much they limit the protection it gives. Effort: **S** about a day, **M** a few days, **L** more.

### Coverage

| # | Gap | Impact | Effort |
|---|---|---|---|
| C1 | ~~Underwater borrowers are not followed.~~ Done (plan `2026-10-10-market-borrowers`): unrealised bad debt in every held market, warn from 0.01 % of the vault, critical from 0.1 %. | — | done |
| C2 | `analyze` supports only Pendle PT collateral; other collateral is refused. | high | M |
| C3 | Direct Blue supply and Vault V1 deposits are not watched by `watch --user`. A V1 vault held through `MorphoVaultV1Adapter` is an opaque layer. | medium | M (supply S, V1 M) |
| C4 | Adapters other than `MorphoMarketV1AdapterV2` (for example the `MidnightAdapter` in the vault-v2 repository) are listed as opaque. | medium | M |
| C5 | Ethereum mainnet only; no other chain where Morpho is deployed. | medium | M |

### Early warning and governance

| # | Gap | Impact | Effort |
|---|---|---|---|
| G1 | ~~Timelock lengths and abdications are not read.~~ Done (plan `2026-10-10-lenders-and-timelocks`): read at start, zero timelocks flagged, `Submit` with no notice critical. | — | done |
| G2 | ~~No liquidation curve.~~ Done (plan `2026-10-10-market-borrowers`): curve at −2/−5/−10/−20 % for every watched market, warn when a 5 % fall liquidates ≥ 25 % of the debt. | — | done |
| G3 | ~~Admin actions are not watched.~~ Done (plan `2026-10-10-admin-surface`): upgrades, admin and owner changes, feed changes, pauses, roles, outsized mints, Blue owner actions. Custom admin functions without standard events are seen only through slot changes. | — | done |
| G4 | ~~No oracle vs independent price.~~ Done: DefiLlama price, every 300 blocks, warn from 3 %. | — | done |
| G5 | Pending transactions are not watched. The free node streams them and `eth_simulateV1` can simulate them, but liquidations and large exits often use private relays. | low | M |
| G6 | Morpho's opt-in pre-liquidation contracts are not read; only the authorisation they require is alerted. | low | S |

### Impact model (`analyze`)

| # | Gap | Impact | Effort |
|---|---|---|---|
| M1 | Incident probabilities are base rates from DefiLlama's hack record by size and category, not assessments of the specific protocols. | medium | — (by design; document per use) |
| M2 | Layers fail independently, except an issuer exploit, which comes with a depeg. A depeg, a draining Pendle pool and a lagging oracle tend to happen together. | medium | M |
| M3 | Exit cost is quoted only for PT collateral, and the liquidators' selling pressure is not modelled. | medium | M |
| M4 | The liquidation distance and the starting oracle value use the PT market price, not the oracle's reading (0.08 % apart on the demo). | low | S |
| M5 | Carry assumes today's yield and borrow rate over the horizon. | low | S |
| M6 | One position at a time: two positions sharing a layer are not combined into one exposure. | medium | M |
| M7 | `registry.json` covers 4 yield issuers by hand; others get a conservative default. | low | S per issuer |

### Graph

| # | Gap | Impact | Effort |
|---|---|---|---|
| R1 | The `graph` command builds and draws the graph (with admins and oracle feeds), but `analyze` and `watch` do not use it: their rules work on their own structures, and exposure is computed per position. *Partial:* `riskdep shock` propagates a failure through the graph with a rule-driven engine (plan `2026-10-10-propagation-engine`); the watches and `analyze` still do not use it. | medium | L |
| R3 | Shared nodes are drawn but not measured: no alert says that one feed (for example `RLUSD / USD` under all 10 Sentora markets) carries several positions at once. | medium | S after R1 |
| R4 | ~~Lender concentration is not watched.~~ Done (plan `2026-10-10-lenders-and-timelocks`): `watch --user` lists each borrowed market's main lenders, warns when one funds ≥ 50 %, and when a main lender withdraws ≥ 5 % of the supply. | — | done |
| R2 | No general propagation limits (exposure floor, depth, severity floor). *Partial:* the shock engine stops when no input moves by more than ε or its evaluation budget is spent, and a rule can stop an effect on any criterion; there is no exposure floor by default. | low | S |
| R5 | Sibling markets are found on Morpho Blue only: the same collateral borrowed on Euler, Aave, Silo or Fluid, or sold through another pool, is not in the graph. | medium | M per venue |
| R6 | Sibling markets are drawn, not watched: `watch` does not follow their liquidations, oracle moves or bad debt, and the curves in the graph are read once. | medium | M |
| R7 | Oracle classes are binary and per input: a meta-oracle that switches source after a deviation (`MetaOracleDeviationTimelock`) and an input known only by name without the Etherscan key stay `not classified`. | low | S per oracle type |

### Data and infrastructure

| # | Gap | Impact | Effort |
|---|---|---|---|
| D1 | The free RPC serves state only about 90 to 126 blocks back and refuses old log ranges: no backfill after a long stop, only a reported gap. It also accepts at most 9 addresses per log filter (worked around by splitting) and intermittently refuses recent ranges as "archive" (worked around by retrying). | medium | S with a paid RPC |
| D2 | Position discovery depends on the Morpho API; `--market` is the fallback for borrows, but vault deposits have none. | low | S |
| D3 | Reorgs deeper than 2 blocks are not handled. | low | S |
| D4 | Alert memory is in-process: after a restart, standing conditions such as an HF below a level are alerted again. | low | S |
| D5 | Alerts go to the terminal and a JSONL file only; no push notification. | medium | S |

### Execution

| # | Gap | Impact | Effort |
|---|---|---|---|
| X1 | No execution: no Bundle construction, no simulation of a de-lever, no conditional transaction (section 4). | high for a user who cannot react in time | L, with a key-management design |

### Testing and documentation

| # | Gap | Impact | Effort |
|---|---|---|---|
| T1 | Tests replay small recorded ranges (300 to 1,000 blocks); no run against a forked chain with a forced liquidation or bad debt. | medium | M |
| T2 | No continuous integration. | low | S |
| T3 | ~~Missing documents.~~ Done: `docs/reference/alert-runbook.md` (what each alert means and what to do), `docs/reference/glossary.md`, `docs/reference/registry-reference.md`. | — | done |
| T4 | A frozen copy of an earlier version, with an old date bug, remains in `../projet/`. | low | S |

### Suggested order

1. **C2 and M3:** extend `analyze` beyond PT collateral, with a generic exit quote.
2. **D5, then X1:** push alerts first, then execution with its own security design.
