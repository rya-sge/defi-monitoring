# `registry.json` reference

`riskdep/registry.json` holds every fact, assumption and threshold the tool uses that is not read from a live source. Each probability and severity carries a `basis` field saying where it comes from, and the `analyze` report prints those bases. This page explains each key: its unit, which code reads it, and what changing it does.

Rules for editing:

- **Keep the `basis` honest.** A changed number gets a changed basis: a source, a date, or "judgement" and why.
- **Run the tests after any change:** `python3 -m pytest -q tests`. They run offline; a change that breaks a threshold test shows up there.
- **Addresses are lowercase** Ethereum mainnet addresses.
- **Probabilities are per year** and fractions between 0 and 1; severities are Beta distributions `{"a": …, "b": …}` whose mean is a / (a + b).

## Contents

- [`chain`](#chain)
- [`issuers`](#issuers)
- [`stables`](#stables)
- [`protocols`](#protocols)
- [`oracle`](#oracle)
- [`frequency`](#frequency)
- [`unknown_issuer`](#unknown_issuer)
- [Top-level parameters of `analyze`](#top-level-parameters-of-analyze)
- [`watch`](#watch)
- [`graph`](#graph)
- [`engine`](#engine)
- [`exit_liquidity`](#exit_liquidity)
- [`pharos`](#pharos)
- [`nexus`](#nexus)
- [`feeds`](#feeds)
- [`tvl`](#tvl)
- [`backtest`](#backtest)
- [`conditional`](#conditional)
- [`notify`](#notify)
- [How to add a yield issuer](#how-to-add-a-yield-issuer)

## `chain`

The settlement chain as a layer of the `analyze` model. One entry, `ethereum`.

| Key | Unit | Meaning |
|---|---|---|
| `label` | text | the name shown in the report |
| `p_year` | probability per year | chance of an incident (today 1 %) |
| `severity` | Beta | loss of value if it happens (mean 0.5 %) |
| `basis` | text | justification |

Read by `discover.py` (graph node) and `priors.py` (the `chain` event).

## `issuers`

One entry per yield-bearing token that can sit behind a Pendle PT, keyed by the token's address. Today: sUSDe, USDe, wstETH, sUSDS.

| Key | Unit | Meaning |
|---|---|---|
| `symbol`, `issuer` | text | shown in the report and the graph |
| `llama_slug` | DefiLlama slug | finds the protocol in DefiLlama's list, for its size, category and listing date |
| `category` | DefiLlama category | used when the slug is not found |
| `kind` | text | descriptive only |
| `dependencies` | list of text | off-chain dependencies, drawn as External nodes |
| `depeg.p_year` | probability per year | chance of a depeg |
| `depeg.severity` | Beta | size of the depeg |
| `depeg.recovery` | fraction | share of the depeg recovered by the horizon; the rest is a permanent loss |
| `depeg.basis` | text | justification |
| `hack.severity`, `hack.basis` | Beta, text | loss of backing if the issuer is exploited; the exploit's probability is computed from the hack record (see `frequency`) |

Read by `discover.py`, `priors.py` and `graph.py`. A token not listed here falls back to `unknown_issuer`, and the report says so.

## `stables`

The loan tokens' issuers, keyed by address (USDC, USDT): `symbol`, `issuer`, `basis`. Descriptive only: for a borrower, a depeg of the loan token lowers the debt, so the model has no loss channel for it. Read by `discover.py` and `graph.py`. `siblings.py` treats these tokens as terminal: they never link two markets as sibling markets (D77).

## `protocols`

The two protocols whose exploits the model includes: `pendle` and `morpho-blue`.

| Key | Unit | Meaning |
|---|---|---|
| `label` | text | shown in the report |
| `llama_slug`, `category` | DefiLlama | locate the protocol for the frequency estimate |
| `severity` | Beta | loss if exploited (Pendle mean 14 %, Morpho Blue mean 9 %) |
| `basis` | text | justification |

Read by `priors.py`.

## `oracle`

The oracle-failure event of `analyze`.

| Key | Unit | Meaning |
|---|---|---|
| `techniques` | list | DefiLlama hack techniques counted as oracle failures (misconfigured, stale, predictable); spot-price manipulation is excluded |
| `unverified_factor` | multiplier | applied when the oracle's source is not verified on Etherscan, or when that cannot be checked (no key, no cached answer); a verified oracle gets 1 (D68). Today 2 |
| `p_year_floor` | probability per year | minimum (today 1 %) |
| `severity` | Beta | how far the oracle misreports downwards (mean 10 %) |

Read by `priors.py`.

## `frequency`

How an exploit probability is derived from DefiLlama's hack record (details in `docs/how-risk-is-computed.md`, section 3).

| Key | Unit | Meaning |
|---|---|---|
| `years` | years | look-back window of the hack record (5) |
| `min_tvl_usd` | USD | protocols below this size are ignored in the counts |
| `tiers_usd` | USD | size bands: under 10M, 10M to 100M, over 100M |
| `category_multiplier_clip` | [min, max] | bounds of the category adjustment (0.5 to 2) |
| `age_factor` | multipliers | 2 for a protocol listed less than a year ago, 1 between one and three years, 0.7 beyond |
| `floor`, `cap` | probability per year | the result is kept between 0.5 % and 15 % |

Read by `priors.py`.

## `unknown_issuer`

The conservative default for a yield token not in `issuers`: a 15 % yearly depeg chance with 60 % recovery, and a heavy exploit severity (mean 33 %). Same fields as an `issuers` entry, plus `category` (`Yield`). Read by `priors.py`.

## Top-level parameters of `analyze`

| Key | Unit | Meaning | Read by |
|---|---|---|---|
| `pt_stress_extra_discount` | multiplier | during a depeg, an oracle that follows the PT market sees the depeg × (1 + this), because the PT trades below its backing as the Pendle pool drains (0.5) | `propagate.py`, `simulate.py`, `decide.py` |
| `gas_exit_usd` | USD | gas cost added to every exit and de-lever estimate (25) | `decide.py` |
| `tail_budget` | fraction of equity | REDUCE when CVaR 99 % exceeds this share of the equity (0.5) | `decide.py` |
| `incident.exit_min_gain` | fraction of the loss | vault incident mode: EXIT only when leaving first cuts the depositor's loss by at least this share (0.05) | `vault_incident.py` |
| `incident.breakeven_basis` | text | the breakeven probability p\* of vault and book incidents: yield forgone on what can leave over `--horizon`, divided by the loss leaving first saves (D142–D144) | `vault_incident.py`, `vault_book.py` |
| `incident.reduce_margin` | fraction | incident mode: the partial sale puts liquidation this far beyond the incident's oracle drop (0.01) | `scenario.py` |

## `watch`

The thresholds of `watch --vault` and `watch --user`. Changing them changes when alerts fire; `docs/alert-runbook.md` describes each alert.

| Key | Unit | Default | Alert or behaviour it controls |
|---|---|---|---|
| `poll_seconds` | seconds | 12 | delay between two polls |
| `confirmations` | blocks | 2 | how far behind the newest block the watcher stays |
| `max_range` | blocks | 500 | largest block range read in one batch |
| `state_window_blocks` | blocks | 64 | how far back state is read; older ranges use the oldest servable block |
| `full_state_every_blocks` | blocks | 25 | a live batch with no event reads only oracle prices, `totalAssets`, `realAssets`, idle cash and the depositor's gates; the full state read runs on any event and at least this often (D61) |
| `crosscheck_every_blocks` | blocks | 300 | cadence of cross-checks, lender refresh, exit quotes, position rediscovery, the full refresh of every market's borrowers, and the admin-surface state and oracle-divergence checks |
| `market_share_warn` | fraction of the vault | 0.25 | `Exposure` at start, and `Adapter.Allocate` raised to warn when a market crosses it |
| `utilization_warn` | fraction | 0.99 | utilisation alerts, for vaults and borrows |
| `utilization_min_share` | fraction of the vault | 0.10 | a vault market's utilisation is alerted only if it holds at least this share |
| `oracle_move_warn` | fraction | 0.05 | `Oracle` moved alerts |
| `large_flow_info` | fraction of the vault | 0.01 | someone else's deposit or withdrawal is reported above this size |
| `lender_min_share` | fraction of supply | 0.05 | who counts as a main lender of a borrowed market |
| `lender_max` | count | 5 | main lenders kept per market |
| `lender_concentration_warn` | fraction of supply | 0.5 | `Lender` concentration warning at start |
| `lender_withdraw_min_share` | fraction of supply | 0.05 | `Lender` withdrawal warning |
| `unrealised_bad_debt_warn` | fraction of the vault | 0.0001 | `UnrealisedBadDebt` warn: the vault's share of a market's unrealised bad debt, from 0.01 % of its total assets |
| `unrealised_bad_debt_critical` | fraction of the vault | 0.001 | `UnrealisedBadDebt` critical, from 0.1 % |
| `curve_drop` | fraction | 0.05 | the oracle fall at which the liquidation curve is tested |
| `curve_warn_share` | fraction of the market's borrows | 0.25 | `LiquidationCurve` warning: the debt liquidatable at `curve_drop` reaches this share |
| `mint_share_critical` | fraction of the supply | 0.05 | `Admin.Mint` critical: one transaction minting this share of a collateral or yield token |
| `oracle_divergence_warn` | fraction | 0.03 | `OracleDivergence` warning: oracle price vs DefiLlama's collateral ÷ loan price |
| `divergence_check_every_blocks` | blocks | 25 | `OracleDivergence` between full refreshes: the batch's oracle prices against DefiLlama prices at most this old (D97) |
| `feed_band_report_floor` | fraction | 0.5 | `FeedBand` at start-up: a custom feed whose `minAnswer` lies within this fraction below its latest answer is reported, with the timelock any upgrade must pass (D183). `feed_band_basis` holds the reason |
| `drain_buy_cost` | fraction | 0.005 | the cost c of buying the collateral at the drain's size, in d\* = 1 − LLTV / (1 + c); low on purpose, so the threshold is early |
| `drain_margin` | fraction (points of discount) | 0.02 | `DrainWindow` warn: the collateral's discount to its oracle within this distance of d\*; critical at d\* |
| `drain_check_every_blocks` | blocks | 25 | how often DefiLlama's prices are re-read for the drain threshold; oracle prices come with every state read |
| `exit_queue_phi` | fraction of the other depositors' assets | 0.5 | the "behind φ of others" queue position of the exit-queue table; it also stands in for the contract holders in `ExitQueue` when the holder list is unavailable |
| `concentration_top1_warn` | fraction of the market's debt | 0.5 | `BorrowerConcentration` warn: the largest borrower of a vault market holds at least this share (D129) |
| `concentration_min_borrowers` | count | 5 | `BorrowerConcentration` warn: a vault market with fewer borrowers |
| `concentration_basis` | text | — | why |
| `exit_queue_stuck_warn` | fraction of the position | 0.5 | `ExitQueue` warn: the share of the position stuck if every contract holder withdrew first; critical when the vault also carries unrealised bad debt |

The health-factor levels of `watch --user` are not here: they are a command-line option, `--hf` (default `1.10,1.05,1.02`).

## `graph`

The sibling-market search and the oracle classification of the `graph` command (plan `2026-10-10-sibling-markets`, D79, D83, D84). Read by `siblings.py` and `oracle_class.py`. Changing them changes which markets appear and how oracles are labelled; no alert depends on them.

| Key | Unit | Default | What it controls |
|---|---|---|---|
| `sibling_min_tvl_usd` | USD | 1,000,000 | a market with less supplied (its TVL) is never a sibling; it is also the floor of the Morpho API `markets` query. Held markets are never filtered. Lower it to see small markets, at the cost of a longer run |
| `sibling_max_per_seed` | markets | 10 | the most siblings kept for one held market, the largest borrow first (borrow is what liquidations sell) |
| `sibling_basis` | text | — | why |
| `oracle_history_rounds` | rounds | 24 | how many past rounds of a feed are read with `getRoundData` |
| `oracle_history_min` | rounds | 6 | below this many readable past rounds, history does not decide and the next rules apply |
| `oracle_fall_share` | fraction | 0.2 | a feed whose answer fell in at least this share of its changes is `price-tracking`; below it, `constant-price` (an accrual or exchange rate) |
| `oracle_children_getters` | signatures | `FEED_1()`, `FEED_2()`, `innerOracle()` | getters of a composite or wrapper input; its class comes from the inputs they return, `price-tracking` if one is |
| `oracle_getters` | list | `twapDuration()` → price-tracking when nonzero; `baseDiscountPerYear()` → constant-price when it answers | structural getters that classify an input, each with `when` (`nonzero` or `answers`), `class` and `basis` |
| `oracle_patterns` | list | contract names (`PendleChainlinkOracle`, `PendleSparkLinearDiscountOracle`, `LossAdjustedPTFeed`, `CustomAggregator` for Midas's issuer-published NAV feeds, …) and description fragments (`FUNDAMENTAL`, `exchange rate`, `net asset value`, `discount`) | the last rule: a case-insensitive `match` in the input's `description()` or verified contract name (Etherscan, optional) gives its `class`; each entry has a `basis` |
| `oracle_basis` | text | — | the rules in order, and the 2026-10-10 probe behind the history thresholds |

**Adding a pattern.** When a graph shows an input `not classified`, read its verified source, decide whether a market move reaches its answer, and add `{"match": "<contract name or description fragment>", "class": "price-tracking" | "constant-price", "basis": "<what it computes, source, date>"}`. Prefer a structural getter in `oracle_getters` when the contract exposes one: it needs no Etherscan key.

## `engine`

The shock engine's propagation rules and settings (plan `2026-10-10-propagation-engine`, D104–D111). Read by `engine.py`; the rule format, every criterion and transmission, and worked examples are in `docs/shock-engine.md`.

| Key | Unit | Default | What it controls |
|---|---|---|---|
| `eps` | fraction | 10⁻⁶ | an input that changes by less than this (relative) is not sent on again: the propagation has settled |
| `max_evaluations` | node evaluations | 20,000 | budget of one run; when spent, the report warns that the numbers are not final |
| `depth_usd` | USD by asset address | empty | a pool depth for the `constant_product` comparison model only |
| `quote_sizes_x_liquidity` | multiples of a pool's liquidity | 0.05 … 5 (nine sizes) | the sizes of the two Pendle quote ladders the graph records per PT (PT → underlying, PT → loan token); the sale-impact curves come from them |
| `quote_max_usd` | USD | 99,000,000 | the largest size quoted: Pendle refuses above 100M USD |
| `capacity_min_ratio` | fraction of spot | 0.5 | a ladder's capacity: where the marginal price falls under this share of spot, or the amount received stops growing; a size Pendle cannot route also ends the ladder there |
| `edge_rules` | ordered list | 32 rules | how each effect crosses each edge: `id`, `effect`, `rel`, `direction`, `when`, `apply`, `params`, `basis`. The first match wins, and no match stops the effect |
| `node_rules` | ordered list | `blue-market`, `oracle-input`, `asset`, `default` | each node's model: a Blue market evaluates its borrowers (`slippage`, `buy_cost`); an oracle or feed drops its readings when frozen; an asset prices what is offered into its market (`impact`: `quotes` or `constant_product`, `floor`, `stress_yield` 0.5); anything else combines its inputs |
| `basis` | text | — | why |

**Changing a rule.** Prefer a `--rules` file for a study: the registry's rules are the defaults everyone gets. A change here keeps its `basis` honest and is followed by `python3 -m pytest -q tests/test_engine.py`. The drain threshold uses `watch.drain_buy_cost`.

## `exit_liquidity`

How easily a collateral token can be sold on DEXs, per token address (plan `2026-10-11-borrower-concentration`, D131). Read by `vault_incident.py`: a markdown hit on a market whose collateral has `route` `none` or `thin` reports the loss if nobody liquidates, and the liquidity left locked; a hit token without an entry is named in a note. Measured once, by hand, so it ages: re-measure before relying on it.

| Key | Unit | Default | What it controls |
|---|---|---|---|
| `basis` | text | — | the source (KyberSwap quotes into USDC on Ethereum, 2026-10-11, `docs/analysis/ROCK-VAULT-DEP.md` §7) and the route rule |
| `thin_impact` | fraction | 0.05 | above this price impact at 1M USD, the route is `thin` |
| `tokens.<address>` | object | PST, AUTO, mGLOeuro, fxSAVE, etrUSD, strUSD, PRIME | `symbol`; `route` (`none`: no route at 0.1M USD; `thin`; `deep`); `impact` by sale size in USD (negative = loss; `null`: no route); optional `note` |

**Adding a token.** Quote a sale of the token into the vault's asset at 0.1M, 1M and 5M USD on an aggregator, and add `"<address in lower case>": {"symbol": …, "route": …, "impact": {…}, "note": "<date, source>"}`.

## `pharos`

How Pharos's keyless dependency graph is read (plan `2026-10-11-pharos`, D133–D138; `docs/risk-assessment/outside-providers.md`). Read by `pharos.py`, `vault_incident.py` and `graph.py`. No alert depends on it.

| Key | Unit | Default | What it controls |
|---|---|---|---|
| `basis` | text | — | the source, its methodology version, and that grades are shown, never used as numbers |
| `ids` | address → `{id, symbol}` | 12 tokens: USDC, USDT, EURCV, steakEURCV, trUSD, strUSD, fxUSD, fxSAVE, iUSD, reUSD, USDe, sUSDe | maps a token address to its Pharos id; needed when the symbol is ambiguous (three iUSD, two reUSD); the symbol names the token in the output |
| `ids_basis` | text | — | how each entry was checked (on-chain `symbol()`, 2026-10-11) |
| `min_exposure` | fraction | 0.01 | a market reached through Pharos's off-chain backing is ignored below this share; also the smallest backing edge drawn in `graph` |
| `common_mode_kinds` | list | `mint-control`, `upgrade-control`, `reserve-issuer`, `redemption-rail` | the group kinds that mean "fails together" |
| `max_group_members` | count | 12 | wider groups (a chain, a DEX, LayerZero) are dropped |
| `groups_basis` | text | — | why |

## `nexus`

Nexus Mutual's cover prices as an outside view next to the breakeven p\* (plan `2026-10-11-breakeven`, D145–D146; `docs/risk-assessment/outside-providers.md` §2). Read by `nexus.py` and `vault_incident.py`. Shown, never used in a verdict.

| Key | Unit | Default | What it controls |
|---|---|---|---|
| `basis` | text | — | the source and what the products pay on |
| `loading` | [low, high] | [2, 5] | the implied yearly probability is price ÷ (loading × severity), given for this range |
| `loading_basis` | text | — | why 2–5 |
| `products` | address → `{product, kind, token}` | trUSD, strUSD, etrUSD (Tori 446), fxSAVE (f(x) 137), fxUSD (depeg 311), iUSD, siUSD (infiniFi 308), mGLOeuro (Midas 356) | which Nexus product covers a collateral's protocol; `kind` is `protocol` (pays on an exploit) or `depeg` |

**Adding a product.** Find the product id in `https://api.nexusmutual.io/v2/products`, read its wording (the IPFS annex in its metadata) to set `kind`, and add `"<token address>": {"product": <id>, "kind": "protocol" | "depeg", "token": "<symbol>"}`.

## `feeds`

When an oracle input is stale (plan `2026-10-11-feed-quality`, D155–D157). Read by `feeds.py` for `graph` and vault incidents; no alert depends on it yet.

| Key | Unit | Default | What it controls |
|---|---|---|---|
| `stale_factor` | × cadence | 3 | stale when the last update is older than this many median update intervals, read from the feed's past rounds… |
| `stale_min_hours` | hours | 25 | …and older than this (a daily heartbeat plus an hour) |
| `no_history_max_days` | days | 7 | with fewer than `graph.oracle_history_min` rounds, stale past this age |
| `basis` | text | — | why |

## `tvl`

TVL concentration of the protocols in a graph (plan `2026-10-11-feed-quality`, D158–D160). Read by `tvl.py` for `graph`.

| Key | Unit | Default | What it controls |
|---|---|---|---|
| `warn_share_defi` | fraction of all DeFi TVL | 0.02 | a protocol at or above it is a concentration |
| `warn_share_category` | fraction of its category | 0.25 | …or at or above this share of its DefiLlama category… |
| `warn_category_min_usd` | USD | 1,000,000,000 | …when the category is at least this large |
| `blue_markets` | slug | `morpho-blue` | the protocol of every Blue market |
| `pt_assets` | slug | `pendle-v2` | the protocol of every Pendle PT |
| `tokens` | address → slug | Re, Tori, infiniFi, Hastra, NUVA, Midas, Lido, Huma, AUTOfinance, f(x), Steakhouse | the protocol issuing a token; add a token by its address and the slug in `https://api.llama.fi/protocols` |
| `basis`, `warn_basis` | text | — | why |

## `backtest`

Past incidents replayed (plan `2026-10-11-backtest`, D161–D164). Read by `backtest.py`.

| Key | Unit | Default | What it controls |
|---|---|---|---|
| `lead_blocks` | blocks | 60 | the state before is read this long before the first liquidation (12 minutes) |
| `episodes.<name>` | object | `pt-reusd-2026-08-25` | `title`, `markets` (Blue market ids), `window` (first and last block to search for liquidations), `source` |
| `basis` | text | — | the method |

**Adding an episode.** Find the markets and a block window around the event, add it, run `backtest --episode <name> --record` once (archive RPC and Etherscan key in `keys.ini`), commit `fixtures/replay/backtest-<name>/`, and pin the result in `tests/test_backtest.py`.

## `conditional`

The conditional Monte Carlo of vault and book incidents (plan `2026-10-11-conditional`, D165–D168), `--conditional`. A stated judgement, to calibrate on past markdowns before relying on the tails.

| Key | Unit | Default | What it controls |
|---|---|---|---|
| `paths`, `seed` | count, integer | 10,000, 7 | the number of paths and the generator's seed (runs are reproducible) |
| `grid` | multiples of the fall | 0.25 … 2 | where the real incident is run to measure the loss curve |
| `recover_prob` | probability | 0.3 | the markdown is partly reversed: m uniform on 0–1 |
| `deepen_sigma` | σ of ln m | 0.35 | otherwise m is lognormal with median 1 |
| `no_liquidator_prob` | probability by exit route | none 0.5, thin 0.25, unknown 0.2, deep 0.05 | nobody liquidates: the loss is the shortfall, the liquidity locked |
| `basis` | text | — | why |

## `notify`

Telegram delivery of the watch alerts (`riskdep/notify.py`, `TELEGRAM_BOT.md`). Nothing is sent unless there is an alert at or above `level`.

| Key | Unit | Default | What it controls |
|---|---|---|---|
| `level` | info / warn / critical | warn | the lowest level posted; `--level` overrides it |
| `dedup_blocks` | blocks | 1800 (about 6 h) | a standing finding (no transaction) is posted again only after this many blocks, since every watch restart prints it again |
| `min_gap_seconds` | seconds | 3 | the spacing between two messages when several alerts arrive together; no effect when nothing is sent |
| `burst_max` | messages | 10 | past this many messages in one pass, the rest goes as one digest |
| `poll_seconds` | seconds | 2 | how often the alert files are read |
| `max_retries` | count | 5 | waits on Telegram's 429 before giving up until the next pass |
| `basis` | text | — | why |

## How to add a yield issuer

When a PT's underlying is not in `issuers`, `analyze` uses `unknown_issuer` and says so in the report's notes. To add it:

1. **Find the token address** of the underlying: it is the `underlyingAsset` of the Pendle market, or the `issuer` node of the graph.
2. **Find its DefiLlama slug and category** at `https://api.llama.fi/protocols` (the `slug` and `category` fields).
3. **Collect its depeg history:** the worst prices it traded at, when, and how quickly it recovered. The tool also prints its worst one-year drawdown.
4. **Add the entry**, with each number justified in its `basis`:

```json
"0x<token address, lowercase>": {
  "symbol": "TOKEN", "issuer": "Protocol name", "llama_slug": "protocol-slug", "category": "Category",
  "kind": "synthetic-dollar",
  "dependencies": ["What it relies on off-chain"],
  "depeg": {"p_year": 0.10, "severity": {"a": 1.5, "b": 15.0}, "recovery": 0.7,
            "basis": "Worst observed depeg and date; why this frequency and recovery."},
  "hack": {"severity": {"a": 1.0, "b": 4.0}, "basis": "What an exploit would take, and any backstop."}
}
```

5. **Run it on your position:** `python3 -m riskdep analyze --live --morpho-market <id> --user <address>`. Do not `--refresh` the demo snapshot: it rewrites the snapshot and its date, which the offline tests rely on.
6. **Run the tests.**

A severity's mean is a / (a + b): `{"a": 1.5, "b": 15.0}` averages 9 %. Raising `a` relative to `b` makes larger losses more likely.
