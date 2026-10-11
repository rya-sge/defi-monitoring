# Next steps

Where the project goes next, in recommended order, and what each step needs. It follows the reading of the brief in the 2026-10-10 assessment (`docs/archive/ANALYSIS_CURRENT.md`, now archived; where each criterion stands is in `GOAL.md`): **an incident is known; the tool must detect it, compute its impact on the book, say how fast it lands, and decide stay or exit**. Built steps are listed once, in §2, with their plan; the rest of the file holds only what remains.

Sources: the brief (`docs/hackaton_instruction/GOAL.md` and its PDF), the gap review `GAP.md` (K ids), `IMPROVEMENT.md` (a judge's reading, 2026-10-11), the gap list of `ANALYSIS_MONITORING.md` (C, D, M, R, T, X ids), and the RockawayX and Belem findings (`ROCK-VAULT.md`, `ROCK-VAULT-DEP.md`).

Sizes: **S** about a day, **M** a few days, **L** more.

## Contents

- [1. Where the project stands](#1-where-the-project-stands)
- [2. What has been built](#2-what-has-been-built)
- [3. What remains, in order](#3-what-remains-in-order)
- [4. Phase A: the brief's chain, the rest](#4-phase-a-the-briefs-chain-the-rest)
- [5. Phase B: the numbers, the rest](#5-phase-b-the-numbers-the-rest)
- [6. Phase C: discovery depth and the brief's scope items](#6-phase-c-discovery-depth-and-the-briefs-scope-items)
- [7. Phase D: operations](#7-phase-d-operations)
- [8. The demo](#8-the-demo)
- [9. What is needed from you](#9-what-is-needed-from-you)

## 1. Where the project stands

| Criterion (weight) | Strong now | Still weak | Main gaps |
|---|---|---|---|
| Dependency discovery (30 %) | vault → adapters → markets → borrowers and lenders; the admin surface (feed band, timelock queue, exit gates); siblings, `wraps` edges, oracle classes; Pharos off-chain backing and common-mode groups; feed freshness; protocol TVL concentration | `analyze` (the PT position) does not use the graph; Morpho and Ethereum only; external venues | K19, K24, C5 |
| Impact estimation (30 %) | one number from `analyze` and `shock` (the engine, with the squeeze and sibling markets); wrapped collateral; borrower default; no-liquidator branch; the PT's yield and rate channels; **backtested** on the 2026-08-25 PT-reUSD liquidations (the same 20 borrowers, debt and incentive within 0.8 %) | the squeeze at a past date; liquidity returned by liquidations; biased exploit priors | K9, K1, K17 |
| Decision usefulness (25 %) | a verdict given the incident, with its reason; time to impact; breakeven p\*; the conditional distribution of staying against the certain cost of leaving; the brief's ten pockets with an 11 % unwind; Nexus as an outside view | two verdict code paths (a borrow, a vault); no borrow or PT pockets in a book; detection → impact only for borrowers | K21, K20 |
| Working demo (15 %) | a five-minute path at the top of the README; everything offline from mainnet recordings; an HTTP API (`POST /api/incident`); a web incident demo; the fork crisis demo (`scripts/fork/`); Telegram alerts | live detector times and a matching incident propagation trace in the web app | — |

## 2. What has been built

Frontend incident decisions: `/incident` displays an active-alert demo using the recorded PST −30% impact, one vault selector, clickable vault rows and a right-hand action/chart panel. The real detector's event times and a matching propagation trace remain to be connected; the existing Impact example is a different shock. Nexus needs structured cover terms and policy ownership to become an actionable coverage card. See `FRONT_NEXT.md` and `plan/2026-10-11-front-incident.plan.md`.

| Step | Built | Plan |
|---|---|---|
| Admin surface (v1 step 3) | upgrades, owners, feeds, pauses, mints, Blue owner, oracle divergence | `2026-10-10-admin-surface` |
| Exit queue, drain threshold | `ExitQueue`; d\*, `DrainWindow`, Public Allocator inflow | `2026-10-10-exit-queue`, `2026-10-10-drain-threshold` |
| Sibling markets, oracle classes | in `graph`; `wraps` edges; curves on every market | `2026-10-10-sibling-markets` |
| Incident mode for a position; how fast | `analyze --shock`; time to impact by oracle class, meta-oracle switch; `OracleDivergence` with its impact | `2026-10-10-incident-mode` |
| Shock engine | `shock`: rules in the registry, Pendle quotes, a trace for the front end | `2026-10-10-propagation-engine` |
| Vault incident, book | `analyze --vault` / `--book` with `--shock token=…`; books in USD, any vault, `--record` | `2026-10-11-vault-incident`, `2026-10-11-vault-book` |
| Wrapped collateral (A1) | a token reaches the markets whose collateral wraps it; hidden shortfall | `2026-10-11-wrapped-collateral` |
| Borrower concentration and default; exit liquidity | `BorrowerConcentration`; `--shock borrower=…`; the no-liquidator loss | `2026-10-11-borrower-concentration` |
| Pharos, keyless | grades, off-chain backing in incidents, common-mode groups | `2026-10-11-pharos` |
| One incident, one number (A0) | vault and book incidents run through the engine on recorded graphs | `2026-10-11-one-number` |
| Breakeven p\*, Nexus (most of A2) | p\* per vault and for the book, "act first on" by lowest p\*; Nexus cover prices as an outside view | `2026-10-11-breakeven` |
| Incidents over HTTP (part of A5) | `POST /api/incident`, `GET /api/books` | `2026-10-11-incident-api` |
| Shocks and backtests over HTTP (part of A5) | `POST /api/shock`, `/api/shock/graphs`, `/api/shock/targets`, `/api/shock/sweep`, `GET /api/backtests`, `/api/backtest/{episode}`; `web/` client wrappers with fixtures | — |
| The judge path (`IMPROVEMENT.md` 1.1–2.2) | the brief's ten pockets (`pocket` weighting, `--exit-cost`); README path; a reason on every verdict; the expected loss's sampling interval | `2026-10-11-judge-path` |
| Fork crisis demo (D3; part of C6) | `scripts/fork/`: the Belem crisis on an anvil fork, alternative crises; `RISKDEP_FORK`; the timelock queue, the feed band and the exit gates in `admin.py`; `test_fork_replay.py` | `2026-10-11-fork-demo` |
| Feed quality, TVL concentration (most of C2, C3) | each feed's freshness against its own rhythm; each protocol's share of DeFi and of its category | `2026-10-11-feed-quality` |
| Second backtest: the 2025-10-10 crash (B9+) | `backtest --episode crash-2025-10-10`: six markets, no missed borrower, every over-prediction accounted for | `2026-10-11-backtest-crash` |
| Backtest (B9) | `backtest`: the 2026-08-25 PT-reUSD liquidations, through an archive RPC, recorded keyless | `2026-10-11-backtest` |
| Conditional Monte Carlo (A4) | `--conditional`: the loss of staying given the incident, drawn from real incident runs, against the certain cost of leaving | `2026-10-11-conditional` |
| PT yield and rate channels (B1, B2 as incidents) | `--shock pt_yield=…`, `--shock borrow_rate=…` | `2026-10-11-pt-channels` |
| Detection → impact for vaults (A3) | `OracleImpact` in both watches: the vault's and the depositor's loss and the verdict when an oracle falls; the fork crisis's act 6 states 215,003 EURCV when the price lands, 1.1 % from the loss realised | `2026-10-11-detect` |
| The brief's book with its PT loop (most of A6) | a borrow pocket in a book (`kind: borrow`), the same verdict rule as a vault pocket; `examples/brief-mixed-book.json` | `2026-10-11-mixed-book` |
| Zama confidential vaults (Z1–Z3 of `ZAMA-VAULT.md`) | 16 vaults verified; the cShare as a pool; a confidential depositor's two exits in incidents; the hidden layer in `graph` | `2026-10-11-zama` |
| FeedStale, Zama batcher alerts (Z4), the PT verdict's horizon and tail (K12, K13: B7, part of B3) | `FeedStale`; the day's confidential outflow, instant exits, pauses; EXIT when de-levering leaves the tail unsurvivable; the hold-to-maturity path | `2026-10-11-alerts-and-verdict` |
| Discovery depth for the PT position (C1) | `analyze` reports the meta-oracle's structure, who can change the tokens, sibling markets, issuer grade and backing, protocol concentration; the incident names the sibling contagion | `2026-10-11-depth` |
| Push alerts (part of D2) | Telegram (`riskdep notify`, `TELEGRAM_BOT.md`) | — |
| CI | lint, tests, the OpenAPI contract, the web build | — |

## 3. What remains, in order

| # | Step | Gaps | Size | Builds on |
|---|---|---|---|---|
| **A6** | ~~Books mixing borrow and vault pockets, one rule~~ **done** (plan `2026-10-11-mixed-book`); K12 and K13 **done** (plan `2026-10-11-alerts-and-verdict`); the conditional distribution for a borrow **done** (D203); PT holdings without a borrow **done** (D222) | K21, M6 | M | `decide.py`, `vault_book.py`, `conditional.py` |
| **A5** | Connect the incident page to live detector times and a matching propagation trace; structured Nexus cover terms and policy ownership | demo | S | `web/`, `POST /api/incident` |
| B4 | ~~Oracle structure, the rest~~ **done**: the pool move (plan `2026-10-11-pool-move`), constant-price split by kind and drain by class through the engine (plan `2026-10-11-oracle-kinds`) | K7, K8 | M | `oracle_class.py`, `engine.py` |
| B5 | *Secondary: the priors feed only `analyze --demo`'s ex-ante view; no known-incident answer uses them.* Priors: decayed window, survivorship, two-part depeg, protocol multiplier, the RockawayX issuers; calibrate the conditional draw | K1–K5, K17, K18 | M | `priors.py`, `registry.json` |
| B6 | ~~The pool at a past date~~ **done** (plan `2026-10-11-pendle-pool`: the pool rebuilt from its state, the sale behind the backtest's fall, the squeeze); left: the engine's squeeze on the rebuilt pool, returned liquidity in vault incidents | K9, K27 | M | `engine.py`, `backtest.py` |
| B3 | ~~Stressed exit cost~~ **done** (plan `2026-10-11-stressed-exit`: the exit after the incident's own liquidations; the hold-to-maturity path in `2026-10-11-alerts-and-verdict`) | K12 | S | Pendle quotes at several sizes |
| B1+, B2+ | The rate and yield channels as Monte Carlo layers, with Pendle's and Morpho's history | K10, K11 | S | `simulate.py` |
| B8 | Loans at the market price; the drain as a loss channel | K16 | S–M | `market_risk.py`, `drain.py` |
| C2+ | ~~`FeedStale` in the watches; one feed under several markets~~ **done** (plan `2026-10-11-shared-and-supply`) | K23 | S | `feeds.py` |
| C3+ | ~~A collateral's share of its supply held in Morpho~~ **done** (plan `2026-10-11-shared-and-supply`) | K25 | S | `graph.py` |
| C6 | Bridges as graph nodes, issuer and oracle registry entries, PT expiry in incidents | K19, K23 | M | `graph.py`, registry |
| C4, C5 | ~~External venues~~ **done for USDe** (plan `2026-10-11-venues`); left: non-Morpho Vault V2 adapters; Vault V1, other chains | K24, C5 | M–L | registry, `metamorpho-v1.1` |
| D | Validate on your positions; Slack/Discord/email alerts; infrastructure; execution | — | — | — |

Sky's backing behind USDS, DAI and sUSDS is read on-chain (plan `2026-10-11-sky`). Exit liquidity is now quoted live on KyberSwap (plan `2026-10-11-exit-liquidity`). If time is short before the judging: the demo pass; then B6's rest (the engine's squeeze on the rebuilt pool). B6's pool at a past block is done: the backtest's oracle fall traces to a 5.4M PT sale, and from that sale alone the model predicts the same liquidated borrowers. B4 and A6's conditional draw for a borrow are done (PT holdings without a borrow are left). C1 is done. `IMPROVEMENT.md` advises against more documentation and against phase D.

## 4. Phase A: the brief's chain, the rest

### A3. Detection → impact for vaults (K20, K22)

**Why.** For the sponsor's vault the incident is an issuer NAV update, published by a transaction, with no market move before it. The watches see the oracle move, and the fork demo's `admin.py` sees the feed's band and its timelock, but no vault alert carries the vault's loss.

**How.** In `watch --vault` (and for vault deposits in `watch --user`): a new round on a constant-price feed, a stale feed (`feeds.freshness`), or a queued feed upgrade calls `vault_incident` with `token=<collateral>:<fall>` (the observed fall, or the band's floor for a queued upgrade). The alert carries the vault's and the depositor's loss, the timing and the verdict, as `OracleDivergence` does for a borrower. After the fork demo's `admin.py` and `watch.py` work is committed.

### A6. One verdict engine; mixed books (K21, M6)

**Why.** A borrow (`decide.py`) and a vault (`vault_incident`, `vault_book`) reach STAY / REDUCE / EXIT by different code and wording, and a book holds vaults only. The brief's book of pockets can hold a borrow or a PT.

**Done:** borrow pockets in a book, by the vault pocket's rule (plan `2026-10-11-mixed-book`). **Left, how:** the PT verdict's horizon to maturity (hold to maturity against exit now, K12) and a tail budget (K13); then one `verdict_given(stay, leave, cost, …)` used by `decide.py` too; book pockets of kind `borrow` and `pt` through `scenario.assess`; p\* and the conditional distribution for a borrow; each shared (event, node) drawn once per path in a book's ex-ante simulation (M6). Agree first with the shock engine's author: its planned step 2 is a verdict too, and there should be one.

### A5. The web page for incidents

`POST /api/incident` serves the vault and book incident (losses, verdict, p\*, the conditional distribution); `/incident` displays the recorded PST demo, and live detector times and a matching propagation trace remain to be connected. `POST /api/shock` serves the engine's trace (the Impact page calls it outside mock mode, on the committed example by default) and `GET /api/backtest/{episode}` the backtests; no page offers a shock picker or a backtest view yet. See `FRONT_NEXT.md`.

## 5. Phase B: the numbers, the rest

- **B4. The pool-move event (K8).** *Done for the PT position* (plan `2026-10-11-pool-move`: `--shock pool_move=<x>`, real pool quotes, the liquidating sale); the pool at a past block is B6. The backtest replays a known oracle fall; the fall itself came from a trade into a thin Pendle pool moving a TWAP. A `pool_move` event: a trade's impact from Pendle quotes, through the oracle's TWAP window, into the engine. Also: split constant-price (exchange rate, linear discount, issuer-published); `drain.py` by class. *Done* (plan `2026-10-11-oracle-kinds`): four kinds; a markdown reaches only the kinds that move; the engine drains where the oracle keeps reading.
- **B5. Priors (K1–K5, K17, K18).** Weight hacks by age and tier them by their TVL at the hack date; a two-part depeg for synthetic dollars; a bounded protocol multiplier (admin powers, Nexus prices); registry entries for the RockawayX issuers; calibrate `conditional` on past markdowns (Pharos depeg events, the hack corpus).
- **B6. Returned liquidity and the squeeze at a past date (K9, K27).** *Done in part* (plan `2026-10-11-pendle-pool`): the Pendle pool rebuilt at any block from its state; in the backtest, the sale behind the fall, the pool's capacity against what the liquidations seized, the repaid debt as returned liquidity. The debt liquidators repay comes back as free liquidity, which changes what can leave; the Pendle pool's curve rebuilt from its reserves at a block, so the backtest can include the squeeze.
- **B3. Stressed exit cost (K12).** *Done* (plan `2026-10-11-stressed-exit`): the exit priced after the incident's own liquidations sell first, from real quotes; when Pendle stops routing, the part that can still leave. Left: other holders' sales, vault pockets.
- **B9+. A second episode.** USDe −8 % on 2025-10-10, through the same `backtest` (an episode is registry data).
- **B1+, B2+.** The rate and yield channels drawn in the ex-ante Monte Carlo.
- **B8. Loans at the market price (K16).** A second valuation at DefiLlama's price for markets whose oracle does not follow; the drain as a loss channel.

## 6. Phase C: discovery depth and the brief's scope items

- **C1. Depth in `analyze` (K19).** The PT report reuses the graph: siblings, the admin surface, Pharos backing, feed freshness, TVL concentration. **M.**
- **C2+. `FeedStale` (K23).** The freshness rule as a watch alert, with a runbook row; one feed under several markets. After the fork demo's `admin.py`. **S.**
- **C3+. Supply share (K25).** A collateral's share of its supply held in Morpho markets (`totalSupply` at the recorded block). **S.**
- **C6. The rest of `ROCK-VAULT-DEP.md` §11.** Done by the fork demo: the exit-gate standing finding, the feed band, the timelock queue. Left: bridges as graph nodes (CCIP for PST, LayerZero for etrUSD); registry entries for issuers, RedStone, Ojo, CCIP; PT expiry in incidents (`alt-fxsave-expiry.sh` scripts it on the fork). **M.**
- **C4. External venues (K24).** *Done for USDe* (plan `2026-10-11-venues`): the exchanges and custodians behind it, the reserve fund, `venue=<exchange>:<loss>`, the funding stress. Left: Vault V2 adapters into non-Morpho venues. **M–L.**
- **C5. Vault V1, other chains.** A Vault V1 reader; the chain as a parameter. **M–L.**

## 7. Phase D: operations

- **D1. Validate on your own positions.**
- **D2. Push alerts.** Telegram done; Slack, Discord, ntfy and email left.
- **D3. Tests on a forked chain.** Done by the fork demo (`scripts/fork/`, `test_fork_replay.py`).
- **D4. Infrastructure.** Backfill after a stop, a WebSocket trigger, deeper reorgs; an archive RPC is now in `keys.ini` (`[alchemy]`).
- **D5. Execution through Bundles.** A security design first. **L.**
- **D6. Housekeeping.** Remove `LLAMA_YIELDS`; decide on `../projet/`; a `CHANGELOG.md`.

## 8. The demo

The README opens with it (§ "The answer in five minutes"):

1. **Discovery:** `graph --vault 0xE018…1965 --replay`: siblings, oracle classes, Pharos grades and backing, feed freshness, protocol concentration.
2. **Impact and decision:** `analyze --vault 0x2cA2…a423 --shock token=fxSAVE:0.30`: the engine's figures, the timing, the verdict, p\*, the outside view.
3. **The brief's trade-off:** `analyze --book examples/brief-ten-pockets.json --shock token=mGLOeuro:0.30 --exit-cost 0.11 --conditional`: 110,000 certain against a staying loss of 52,067 on average and 246,211 at the 95th percentile.
4. **Is it defensible:** `backtest`: the 2026-08-25 liquidations predicted, the same 20 borrowers.
5. **The crisis live:** the fork demo (`docs/analysis/FORK-PRESENTATION.md`, `scripts/fork/`).

**Checked on 2026-10-11** (a judge's pass): every command above runs offline and prints what the README quotes; `tests/test_readme.py` runs the README's commands and fails when a quoted fragment is no longer printed. Figures that moved since they were written (trUSD −30 % now 2.03M, fxSAVE −30 % 1.81M, through the shock engine) are updated where quoted, with the earlier figure kept in dated findings.

## 9. What is needed from you

- [ ] **Decisions:** who owns the single verdict (A6) with the shock engine's author; the borrow and PT pockets of the demo book; the calibration incidents for the conditional draw (B5).
- [ ] **Documents:** the issuers' documentation for B5 (Huma, f(x), Tori, Re, Midas, Hastra, Nuva, infiniFi).
- [x] Etherscan key. [x] Archive RPC (`[alchemy]`).
- [ ] Credentials for Slack, Discord or email alerts (D2), if wanted.
