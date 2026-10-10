# Next steps, version 2

This file proposes what to build next, ordered by what moves the challenge's score most. It replaces the order of `NEXT_STEP.md` (version 1, written before the exit queue, the drain threshold and the gap review), whose steps it keeps where they still apply.

It draws on three sources:
- **The brief**, `docs/hackaton_instruction/Hackathon_DeFi-Risk-Dependency-Challenge_EN_v1.pdf`, summarised in `docs/hackaton_instruction/GOAL.md`.
- **The gap review**, `GAP.md`: gaps K1–K25 and its recommended order (§11).
- **The teammates' feedback**: `teammate/team1.md`, `teammate/team2.md`, compared in `comparison_team.md`.

## Contents

- [1. Where the project stands against the brief](#1-where-the-project-stands-against-the-brief)
- [2. How the steps are ordered](#2-how-the-steps-are-ordered)
- [3. Summary](#3-summary)
- [4. Phase A: answer the brief's question as asked](#4-phase-a-answer-the-briefs-question-as-asked)
- [5. Phase B: make the PT-loop number defensible](#5-phase-b-make-the-pt-loop-number-defensible)
- [6. Phase C: correlation, cascade and the tail](#6-phase-c-correlation-cascade-and-the-tail)
- [7. Phase D: the vault depositor](#7-phase-d-the-vault-depositor)
- [8. Phase E: discovery depth and the brief's scope items](#8-phase-e-discovery-depth-and-the-briefs-scope-items)
- [9. Phase F: external venues and other chains](#9-phase-f-external-venues-and-other-chains)
- [10. The demo](#10-the-demo)
- [11. What carries over from version 1](#11-what-carries-over-from-version-1)
- [12. Decisions needed](#12-decisions-needed)

## 1. Where the project stands against the brief

| Criterion (weight) | Strong today | Weak today | Main gaps |
|---|---|---|---|
| Dependency discovery: depth and correctness (30 %) | The brief's own five layers for a Pendle PT; vault → adapters → markets → borrowers and lenders; the admin surface (oracles, feeds, tokens, Pendle SY, Blue owner); oracle source verified on Etherscan | `analyze` stops at the issuer and does not use the admin surface; feed quality, TVL concentration, external venues and other chains are not covered | K19, K23, K25, K24, C5 |
| Impact estimation: is the number defensible (30 %) | Every number has a basis; unrealised bad debt, liquidation curves, the exit queue and the drain threshold for depositors | The `analyze` model prices incidents only: the rate and implied-yield channels that actually cost PT loops in 2025–2026 are missing; layers are independent; oracles are binary; the exploit priors are biased (survivorship, stale window) | K10, K11, K7, K8, K6, K1, K17, K5 |
| Decision usefulness: stay or exit, and why (25 %) | STAY / REDUCE / EXIT with carry, a real exit quote and a de-lever size; block-by-block alerts with a runbook | No "this component is hit now" mode; no book; no breakeven probability; no single headline number; no time to impact; the verdict compares a one-off exit cost with a 30-day loss | K20, K21, K22, K12, K13 |
| Working demo on real data (15 %) | Live and offline runs on mainnet positions, recorded replays, 133 offline tests, CI | The demo shows one PT borrower and one vault; it does not reproduce the brief's book example | K21 |

The brief's question is conditional and set on a book: *a component is hit, what does it do to the book, how fast, and is exiting worth its certain cost?* The tool answers an unconditional, single-position question (expected loss over 30 days from yearly probabilities). Closing that difference is the first priority. It reuses code that exists, and it moves both of the criteria worth 30 % and 25 %.

## 2. How the steps are ordered

1. **The brief's question first.** A step that lets the tool answer the question as the brief asks it comes before any refinement of the model.
2. **Then the largest error in the number.** For the demo's 7.6× PT loop, a +10 pp borrow-rate shock for 30 days costs $28,060, 4.5× the whole modelled expected loss ($6,265). That channel comes before recalibrating hack priors that move the result by tens of percent.
3. **Then the teammates' points that are still open.** Team 1: scenarios before the Monte Carlo, gap shocks, then slippage as a parameter. Team 2: the breakeven probability, the queue (done), the drain (done), the cascade, the depositor's loss.
4. **Cheap before expensive** within a phase; steps marked S reuse existing functions.
5. **Each step ends with something the demo can show.**

## 3. Summary

| # | Step | Gaps | Criteria moved | Size | Builds on |
|---|---|---|---|---|---|
| A1 | Incident mode: `--shock layer=size`, the impact and the verdict with that incident certain | K20 | impact, decision | S | `propagate.loss`, `decide` |
| A2 | Time to impact and time to exit, per scenario | K22 | decision | S | oracle type, Pendle quote |
| A3 | A book: pockets with weights, the breakeven probability p\*, one headline number | K21, M6 | decision, demo | S–M | `analyze` per position |
| B1 | Borrow-rate channel from the AdaptiveCurveIRM | K10 | impact | S | IRM docs, utilisation already read |
| B2 | PT implied-yield channel | K11 | impact | S | Pendle market data |
| B3 | Horizon to maturity, exit cost under stress | K12 | decision | S | Pendle quote at several sizes |
| B4 | Oracle structure instead of a binary, and liquidation by a pool move | K7, K8 | impact | M | `morpho-blue-oracles`, Etherscan source |
| B5 | Prior recalibration: decayed window, survivorship, double count, two-part depeg, off-chain prior, protocol multiplier | K17, K1, K3, K5, K2, K18 | impact | S–M | `priors.py`, `admin.py`, one keyless Nexus call |
| C1 | Named scenarios and a common-shock factor | K6 | impact, decision | M | A1 |
| C2 | Liquidation cascade with slippage (M3 part 2) | K9 | impact | M | `market_risk` curves, Pendle quotes |
| C3 | Tail-aware verdict and uncertainty ranges | K13, K14 | decision | S–M | `simulate`, `decide` |
| D1 | `analyze --vault`: a depositor's loss under a scenario, existing loans revalued at the market price, d\* as a loss channel | K16 | impact, decision | M | `market_risk`, `exit_queue`, `drain` |
| E1 | Discovery depth in `analyze`: admin surface as layers, one look-through level | K19 | discovery | M | `admin.py`, `graph.py` |
| E2 | Feed quality: heartbeat, staleness, shared feeds, meta-oracle state | K23 | discovery | S–M | `admin.py`, local Chainlink docs |
| E3 | TVL concentration per layer | K25 | discovery | S | DefiLlama `/protocols` (cached) |
| F1 | External venue node (perp, CEX) and a funding-rate scenario | K24 | discovery, impact | M–L | registry |
| F2 | Other chains, Vault V1 | C5, C4 | discovery | M–L | `metamorpho-v1.1` submodule |

If time allows only one phase, do **A**. If two, **A then B1–B3**. Those five to six steps change what a judge sees in the demo and fix the largest error in the number.

## 4. Phase A: answer the brief's question as asked

### A1. Incident mode (K20)

**Why.** The brief's worked example marks layer 3, the oracle, as "incident", and its task is the impact "when one of them is affected". Today every input is a yearly probability.

**What.**
- `analyze --shock oracle=-0.10`, `--shock issuer_depeg=0.08`, `--shock pool=-0.03`, combinable.
- With the shock certain: the loss in USD and as a share of equity, whether the position is liquidated, and the verdict.
- The same function behind a critical alert in the watches, so an alert carries an impact number.

**Builds on.** `propagate.loss()` already computes the loss of a given shock; `decide` already gives the verdict.

**Proof.** The brief's example run on the demo position: "the oracle drops 10 %: liquidated, loss X, exit now costs Y".

### A2. How fast (K22)

**Why.** The brief asks what an incident does to the book "and how fast". USR fell 97 % in 17 minutes, and PT-reUSD's oracle moved in 9.

**What.** Per scenario, the time from the incident to liquidation next to the time to exit:

| Oracle type | Time to liquidation |
|---|---|
| TWAP | about the TWAP window |
| meta-oracle with a timelock | the challenge timelock |
| linear discount or fixed | never: lenders take the loss |

Time to exit is one block through the Pendle pool, at the depth left.

**Builds on.** A1, B4 for the oracle type; the demo oracle's `challengeTimelockDuration` is readable now that its source is verified.

### A3. A book, the breakeven and one number (K21, M6)

**Why.** The brief's example is a book of ten 10 % pockets, one affected, unwinding at 11 %, and it asks the system to make "expensive and certain against cheap and uncertain" explicit. Team 2 proposed the breakeven probability for exactly this. `docs/scenarios-and-breakeven.md` worked it out; it is not in the tool.

**What.**
- **A book file:** a list of positions, each an address and market or vault, with its weight. `analyze --book book.json` runs every position. Positions that share a layer (an issuer, an oracle, a feed) are combined, which is M6.
- **The breakeven probability** p\* = (exit cost + carry) / L(scenario), per scenario. It does not depend on a base rate. On the brief's own numbers (11 % exit cost, a total loss of the pocket), p\* = 11 %.
- **One headline line** above the verdict, for example: "Book loss if the oracle fails: 0.9 % of the book. Exiting pocket 3 costs 0.11 % of the book and pays if you believe P(failure) > 11 % this month. Verdict: REDUCE pocket 3."
- **A reproduction of the brief's example** as a test.

**Builds on.** `analyze` per position, A1 for the scenario losses.

## 5. Phase B: make the PT-loop number defensible

### B1. The borrow rate (K10)

The AdaptiveCurveIRM sets the rate at 100 % utilisation to 4× the rate at target, and the rate at target doubles in 5 days while utilisation stays there (`docs/external/morpho/docs.morpho.org-developers-docs/contracts/irm.md`). For a 7.6× loop, the carry is a thin spread (5.01 % − 3.74 % on the demo). **What:** draw a utilisation path, apply the IRM rule, and subtract its cost from the carry in each simulated month. No new data source is needed: the watches already read utilisation.

### B2. The PT's implied yield (K11)

A PT's price before maturity moves with its implied yield: +20 pp costs 2.2 % on the demo and +40 pp liquidates it under a market-tracking oracle. **What:** draw the implied-yield move from the Pendle market's history, price the PT from it, and pass the price to the oracle according to its type (B4).

### B3. Horizon and stressed exit cost (K12)

The rule compares a one-off exit cost with a 30-day loss, while the PT redeems at par in 46.6 days. **What:**
- set the horizon to the PT's maturity;
- compare three choices: exit now, hold to maturity, de-lever;
- report the exit cost under stress (the quote at the pool depth of the stress scenario), not only today's calm quote.

### B4. Oracle structure, and liquidation without an incident (K7, K8)

**Why.** The oracle decides which channel a shock takes, and "conservative" depends on the side: market-tracking is worst for a borrower, linear discount for a lender. The demo oracle is a `MetaOracleDeviationTimelock`, which is neither. On 2026-08-25 a $320k trade moved a TWAP oracle and liquidated 33 PT-reUSD positions at the demo's LLTV.

**What.**
- Read the oracle's structure (`MorphoChainlinkOracleV2` feeds and vaults, the meta-oracle's primary, backup and timelocks) and map each known type to its rule. Fall back to price inference only for unknown types.
- Add a "pool move" event for TWAP-based oracles. Its size comes from Pendle's quote at several sizes (already available); its cost is the liquidation incentive on the repaid debt.

**Builds on.** `docs/external/morpho/lib/morpho-blue-oracles`, the verified source on Etherscan (D68), `admin.py`'s feed discovery.

### B5. The priors (K17, K1, K3, K5, K2, K18)

All in `priors.py` and `registry.json`, each with a stated basis:
- **K17, K1:** weight hacks by age (a half-life of 1–2 years) and tier protocols by their TVL at the hack date, not today's. Use the result as a category base rate only.
- **K3:** stop counting oracle hacks in both the lending layer and the oracle layer.
- **K5:** a two-part depeg severity for synthetic dollars (frequent shallow, rare near-total), fitted to on-chain prices.
- **K2:** an operational prior for off-chain issuers (custodian, CEX, fund manager, keys).
- **K18:** a bounded protocol multiplier (for example 0.25×–4×) from what `admin.py` already reads (admin powers, upgrades since the last audit) and one keyless Nexus Mutual price call. The report shows both factors, so a reader can dispute one without rejecting the number.

## 6. Phase C: correlation, cascade and the tail

### C1. Named scenarios and a common shock (K6)

Both teams asked for scenarios: Team 1 before any Monte Carlo, Team 2 as the basis of the breakeven. Every large loss in GAP.md's incident list was a chain of layers. **What:** a scenario library in `registry.json`, each run through A1:
- a replay of the Nov 2025 contagion (xUSD → deUSD → USDX);
- a replay of Resolv;
- a PT yield spike with a pool drain;
- a CEX-only wick.

Then add a common-shock factor that raises every layer's probability in the same Monte Carlo draw.

### C2. Liquidation cascade with slippage (K9, M3 part 2)

LlamaRisk measured PT supply on lending markets at 12.8× to 30× the Pendle AMM's depth. **What:** the loop proposed in `comparison_team.md`. Collateral seized at a drop goes to Pendle's price impact for that size, which gives a new drop, until stable. It uses the per-market curves `market_risk.py` already computes. For collateral other than PT, start with Team 1's parametric k·√volume and calibrate k from quotes when one is available (the KyberSwap probe showed keyless quotes exist).

### C3. A verdict that sees the tail (K13, K14)

The demo's CVaR 99 % is 98 % of equity, yet the verdict is REDUCE, because EXIT depends on the mean only. **What:**
- sample the priors themselves and report ranges;
- compare carry with the upper bound of the expected loss;
- let a CVaR beyond a second, higher budget give EXIT;
- report P(loss > x % of equity).

## 7. Phase D: the vault depositor

### D1. `analyze --vault` (K16)

**Why.** The brief's setter runs curated vaults, and `comparison_team.md` §4.3 calls the depositor's loss the largest gap against the impact criterion. The watches now have the exit queue and the drain threshold. What is missing is a loss number under a scenario.

**What.**
- **Loss:** for each scenario, the depositor's loss = their share of the vault × Σ over markets of the vault's share of supply × the market's bad debt at that drop (`market_risk.value`). That is the table worked out by hand in `docs/vault-depositor-scenarios.md`.
- **Loans revalued at the market price:** existing loans in a market whose oracle does not follow the market get valued at the market price too. `docs/drain-threshold.md` shows why: 45.7M already lent against USDe stays invisible today.
- **Drain as a loss channel:** d\* becomes a loss channel, with the probability of crossing it taken from the depeg prior.
- **Version rule:** bad debt is realised differently by vault version (V1.0, V1.1, V2).

**Proof.** The Sentora table of `docs/vault-depositor-scenarios.md` produced by the tool.

## 8. Phase E: discovery depth and the brief's scope items

Discovery is 30 % of the score, judged on "depth and correctness".

- **E1, depth (K19).** Put the admin surface the watches already discover into `analyze`'s graph as layers with their own priors (B5's multiplier). Look through one level where it is on-chain: sUSDS → USDS → PSM → USDC, or the ERC-4626 vault behind an exchange-rate oracle. Draw the off-chain part (custodians, CEX hedges) as typed registry nodes, so the depth is visible even where it is not computed.
- **E2, feed quality (K23), named in the brief's scope.** Heartbeat and deviation threshold, the age of the last update against the heartbeat (the Morpho oracle does not check staleness), the number of sources, one feed carrying several markets (R3), and which source a meta-oracle is using. Documentation is local: `docs/external/chainlink/docs.chain.link-data-feeds-docs/`.
- **E3, TVL concentration (K25), named in the brief's scope.** Per layer: the protocol's share of the chain's category TVL, the position's or market's share of the PT supply and of the pool depth. DefiLlama `/protocols` is already cached. A high share means both a systemic node and a slow exit.

## 9. Phase F: external venues and other chains

- **F1, external venues (K24), named in the brief's scope.** The setter runs market-neutral strategies, so its positions have a hedge leg on a perp venue; USDe has the same structure inside. Start with a typed "external venue" node (venue, custody, withdrawal delay, funding-rate exposure), a prior with a basis, and a funding-rate scenario. A full perp-venue model is a separate project.
- **F2, other chains and Vault V1 (C5, C4).** Morpho is deployed on many EVM chains, and the setter has SOL mandates. EVM chains mostly need an RPC per chain and the address table already in the Morpho docs. Solana is a new stack. Vault V1 deposits (step 4 of version 1) can now read `docs/external/morpho/lib/metamorpho-v1.1`.

## 10. The demo

What a judge should see in five minutes, once phase A is done:

1. **A book of pockets** close to the setter's: a PT loop, a vault deposit, a stablecoin pocket.
2. **The dependency graph** of one pocket (`graph`), five layers deep plus the admin surface.
3. **An incident:** `--shock oracle=-0.10` on the PT pocket. Liquidated or not, the loss as a share of the book, the time to impact, the exit cost, p\*, and the verdict.
4. **The live view:** the vault watch on the same book, with its exit queue and drain threshold, and an alert that carries an impact number.
5. **The defence:** each number's basis in the report, and the brief's own example (ten pockets, 11 % unwind) reproduced by a test.

## 11. What carries over from version 1

| Version 1 step | Status | In version 2 |
|---|---|---|
| 0. Validate on your own positions | still open | needed for A3's book |
| 1. Push alerts | blocked on a channel in `keys.ini` | unchanged, independent |
| 2. `analyze` for any collateral | open | within C2 (slippage) and E1 (look-through) |
| 3. Admin surface | done (refinement open) | E1 brings it into `analyze`; B5 uses it for the protocol multiplier |
| 4. Vault V1, other adapters | open | F2 |
| 5. Fork tests | open | still useful to test B4 and C2 against a forced liquidation |
| 6. Archive RPC, WebSocket | open | unchanged, needed for history-based priors (B2, C1 replays) |
| 7. Other chains | open | F2 |
| 8. Better risk model | split | B1–B5, C1–C3 |
| 9. Execution through Bundles | open | after A and B: a verdict must be right before it is executed |
| 10. Housekeeping | partly done (CI) | unchanged |

## 12. Decisions needed

- **The book for the demo:** which positions and weights, ideally close to the setter's mandates (stablecoin, ETH, BTC, SOL; fund deposits and curated vaults).
- **The horizon rule:** maturity for PTs, and what for open-ended positions (B3).
- **Tail budgets:** the second CVaR budget that turns REDUCE into EXIT, tied to the mandate (C3).
- **Scenario sizes:** which historical moves to cite for each named scenario (C1).
- **Scope of phase F:** whether any of it fits before the event, or stays as a stated limit.
