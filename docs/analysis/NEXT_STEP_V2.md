# Next steps, version 2

This file proposes what to build next, ordered by what moves the challenge's score most. It replaces the order of `NEXT_STEP.md` (version 1, written before the exit queue, the drain threshold and the gap review), whose steps it keeps where they still apply.

It draws on three sources:
- **The brief**, `docs/hackaton_instruction/Hackathon_DeFi-Risk-Dependency-Challenge_EN_v1.pdf`, summarised in `docs/hackaton_instruction/GOAL.md`.
- **The gap review**, `GAP.md`: gaps K1–K25 and its recommended order (§11).
- **The teammates' feedback**: `teammate/team1.md`, `teammate/team2.md`, compared in `comparison_team.md`.

**Update 2026-10-10, after the merge of plan `2026-10-10-sibling-markets`.** A colleague extended the `graph` command, which changes several steps below:
- **Sibling markets** (`siblings.py`): the Blue markets that share a held market's collateral, underlying or collateral-side price input, or lend that collateral, above $1M of supply, joined through the shared asset, oracle or feed node.
- **Oracle classes** (`oracle_class.py`): every oracle input is `price-tracking`, `constant-price` or `not classified`, decided from its structure (base vault, composites, wrappers, Pendle getters), its feeds' round history, then its name.
- **Market state on every market node**, held or sibling: supply, borrow, the collateral of its borrowers, and its liquidation curve with the collateral seized.
- **`wraps` edges**: an ERC-4626 share to its `asset()`.
- **An optional eRPC proxy** (`erpc.yaml`, `docs/erpc.md`) behind `RISKDEP_RPC_URL`, and retries on rate-limited replies.

All of it lives in `graph`; `analyze` and the watches are unchanged. Steps B4, C2, E1, E2 and E3 now build on these modules instead of starting from nothing, and three new gaps from that work (R5–R7 in `ANALYSIS_MONITORING.md`) are placed in E1, E2 and F2.

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
| Dependency discovery: depth and correctness (30 %) | The brief's own five layers for a Pendle PT; vault → adapters → markets → borrowers and lenders; the admin surface (oracles, feeds, tokens, Pendle SY, Blue owner); oracle source verified on Etherscan; in `graph`, sibling Blue markets, `wraps` edges and an oracle class per input | `analyze` stops at the issuer and uses neither the admin surface nor the siblings; siblings are Blue only (R5); feed quality, TVL concentration, external venues and other chains are not covered | K19, K23, K25, K24, C5 |
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
| A1 | Incident mode: `--shock layer=size`, the impact and the verdict with that incident certain **done** (plan `2026-10-10-incident-mode`) | K20 | impact, decision | S | `propagate.loss`, `decide` |
| A2 | Time to impact and time to exit, per scenario **done**, time to exit still "one block" | K22 | decision | S | oracle type, Pendle quote |
| A3 | A book: pockets with weights, the breakeven probability p\*, one headline number | K21, M6 | decision, demo | S–M | `analyze` per position |
| B1 | Borrow-rate channel from the AdaptiveCurveIRM | K10 | impact | S | IRM docs, utilisation already read |
| B2 | PT implied-yield channel | K11 | impact | S | Pendle market data |
| B3 | Horizon to maturity, exit cost under stress | K12 | decision | S | Pendle quote at several sizes |
| B4 | Oracle structure instead of a binary, and liquidation by a pool move | K7, K8, R7 | impact | S–M | `oracle_class.py`, Etherscan source |
| B5 | Prior recalibration: decayed window, survivorship, double count, two-part depeg, off-chain prior, protocol multiplier | K17, K1, K3, K5, K2, K18 | impact | S–M | `priors.py`, `admin.py`, one keyless Nexus call |
| C1 | Named scenarios and a common-shock factor | K6 | impact, decision | M | A1 |
| C2 | Liquidation cascade with slippage (M3 part 2) | K9 | impact | M | the curves and seized collateral of every held and sibling market (`graph`), Pendle quotes |
| C3 | Tail-aware verdict and uncertainty ranges | K13, K14 | decision | S–M | `simulate`, `decide` |
| D1 | `analyze --vault`: a depositor's loss under a scenario, existing loans revalued at the market price, d\* as a loss channel | K16 | impact, decision | M | `market_risk`, `exit_queue`, `drain` |
| E1 | Discovery depth in `analyze`: admin surface, siblings and one look-through level; siblings on other venues | K19, R5, R6 | discovery | M | `admin.py`, `siblings.py`, `graph.py` |
| E2 | Feed quality: heartbeat, staleness, shared feeds, meta-oracle state | K23, R3 | discovery | S–M | `oracle_class.py` (round history), `graph` feed nodes, local Chainlink docs |
| E3 | TVL concentration per layer | K25 | discovery | S | DefiLlama `/protocols` (cached), collateral held per market (`graph`) |
| F1 | External venue node (perp, CEX) and a funding-rate scenario | K24 | discovery, impact | M–L | registry |
| F2 | Other chains, Vault V1 | C5, C4 | discovery | M–L | `metamorpho-v1.1` submodule |

If time allows only one phase, do **A**. If two, **A then B1–B3**. Those five to six steps change what a judge sees in the demo and fix the largest error in the number.

## 4. Phase A: answer the brief's question as asked

Each step below has a **why** (what the brief or the review asks), a **how** (modules, functions, formulas, data), the **output** a user sees, and the **tests**. Names in `code` that do not exist yet are proposals.

### A1. Incident mode (K20)

**Status: done on 2026-10-10** (plan `2026-10-10-incident-mode`, D89–D95), with a link from `OracleDivergence` alerts in `watch --user`. The design below is kept as written; `NEXT_TASK.md` task 1 records what was built.

**Why.** The brief's worked example marks layer 3, the oracle, as "incident", and its task is the impact "when one of them is affected". Today every input is a yearly probability.

**How.**
- **CLI.** `analyze --shock <event>=<severity>`, repeatable. The events are the ones `propagate.loss` already understands: `chain`, `issuer_hack`, `issuer_depeg`, `amm`, `oracle`, `lending`. Severity is a fraction: `--shock oracle=0.10` means the oracle reads 10 % low.
- **Computation.** A new pure function `scenario.impact(pos, shocks, recovery)` in a new module `riskdep/scenario.py`. It calls `propagate.loss(...)` once with the given shocks and returns a `ScenarioResult`:
  - the loss in USD and as a share of equity;
  - whether the position is liquidated;
  - the path text `propagate.loss` already builds ("oracle misreports −10.0 %", "liquidated: 92 % of collateral seized…");
  - the exit cost now, from `decide.exit_cost_usd` and today's Pendle quote.
- **Verdict with the incident certain.** In `decide.py`, a new `verdict_given(pos, result, quote)`:
  - EXIT if the loss of staying exceeds the exit cost (no probability involved: the incident has happened);
  - REDUCE if a partial de-lever (the existing `sale_to_reach`) avoids the liquidation for less than the loss;
  - STAY otherwise.
- **Watches.** On a critical alert whose event maps to a layer (`OracleDivergence`, `Admin.Upgraded` on an oracle, `DrainWindow`, a depeg seen by `admin.read_divergence`), `watch --user` calls `scenario.impact` with the observed size, and adds the loss to the alert's `depositor_impact` and detail.

**Output.** A "Scenario" block at the top of `report.html` and a `scenario` key in `report.json`:

```
Incident: oracle −10.0 %
  liquidated: yes (HF 1.053 → 0.95); loss $27,400 (5.3 % of equity)
  exit now costs $78,946 (1.99 % impact + fees)
  verdict given the incident: REDUCE: selling $1.29M (33 %) avoids the liquidation for $1,023
```
(Figures illustrative, to be computed.)

**Tests.** `tests/test_scenario.py`: an oracle shock just below and just above the liquidation distance (5.16 % on the demo) flips `liquidated`; a shock of 0 gives no loss; the CLI parses repeated `--shock`.

**Size.** S. Everything it needs exists; the work is the CLI, the result type and the report block.

### A2. How fast (K22)

**Status: done on 2026-10-10** for the time to impact, from `oracle_class` and the meta-oracle's getters; the time to exit remains "one block at today's quote".

**Why.** The brief asks what an incident does to the book "and how fast". USR fell 97 % in 17 minutes; PT-reUSD's oracle moved in 9.

**How.**
- **Time to impact**, from the oracle type that B4 identifies (until then, from the current `oracle_mode`):

| Oracle type | Time from the incident to the liquidation |
|---|---|
| market feed (Chainlink-style) | the feed's next update: within its heartbeat, or at once past its deviation threshold |
| Pendle TWAP | about the TWAP window (15 min for the common setting) |
| meta-oracle with a deviation timelock (the demo) | `challengeTimelockDuration`, read on-chain from the verified contract |
| linear discount or fixed | never: no liquidation, lenders take the loss |

- **Time to exit:** one block through the Pendle pool, at the depth left. The exit is "possible in time" when time to exit < time to impact, and the quote at the stressed depth (B3) is still above the debt.
- A new field `time_to_impact_s` (or `None` for "never") in `ScenarioResult`.

**Output.** One line per scenario: "liquidation in ≈ 15 min (TWAP); exit takes one block: exit before the TWAP catches up".

**Tests.** The mapping per oracle type; the demo oracle's timelock read from a cached `eth_call`.

**Size.** S once A1 exists.

### A3. A book, the breakeven and one number (K21, M6)

**Why.** The brief's example is a book of ten 10 % pockets, one affected, unwinding at 11 %, and it asks the system to make "expensive and certain against cheap and uncertain" explicit. Team 2 proposed the breakeven probability for exactly this. `docs/scenarios-and-breakeven.md` worked it out; the tool does not compute it.

**How.**
- **Book file.** `book.json`, a list of pockets:
  ```json
  {"name": "Book A", "value_usd": 40000000, "pockets": [
    {"name": "PT loop", "weight": 0.10, "kind": "borrow", "market": "0x…", "user": "0x…"},
    {"name": "RLUSD vault", "weight": 0.10, "kind": "vault", "vault": "0x6dc5…", "user": "0x…"},
    {"name": "sUSDS", "weight": 0.10, "kind": "hold", "token": "0x…"}]}
  ```
  `analyze --book book.json` builds a `Position` per pocket with the existing discovery and scales its amounts to `weight × value_usd`.
- **Shared layers (M6).** Every pocket's graph gives node ids (issuer, oracle, feed, Morpho market, Pendle pool). A new `book.shared_layers(positions)` lists the nodes that appear in more than one pocket. In the Monte Carlo, a shared node is drawn **once** per path and applied to every pocket that holds it, instead of once per pocket.
- **Breakeven probability.** For each scenario s from A1 or C1, with L(s) the loss of the pocket if s happens over the horizon:

  $$p^\star(s) = \frac{\text{exit cost} + \text{carry}}{L(s)}$$

  Exit pays when one believes P(s) > p\*. No base rate is needed. A new pure `decide.breakeven(exit_cost, carry, loss_if)`.
- **Headline.** A new `report.headline(book_result)`: the largest book loss among the scenarios, as a share of the book, the pocket it comes from, its exit cost as a share of the book, its p\*, and the verdict.
- **The brief's example as a test.** Ten pockets of 10 %, one wiped out by a scenario, an exit cost of 11 % of the pocket: the book loses 10 %, exiting costs 1.1 % of the book, p\* = 11 %.

**Output.**
```
Book A ($40M, 3 pockets)
  worst scenario: USDe depeg −20 %: book −1.2 % (PT loop liquidated)
  exiting the PT loop costs 0.20 % of the book; exit pays if P(depeg) > 16 % this month
  shared layers: USDe (PT loop, RLUSD vault), RLUSD/USD feed (RLUSD vault, 7 markets)
```
(Illustrative.)

**Tests.** `tests/test_book.py`: the brief's example; a shared node drawn once (two pockets on one issuer lose together in the same paths); weights that do not sum to 1 are rejected.

**Size.** S–M: the book loop and the report are S; drawing shared nodes once in `simulate.run` is the M part.

## 5. Phase B: make the PT-loop number defensible

### B1. The borrow rate (K10)

**Why.** For a 7.6× loop the carry is a thin spread (5.01 % − 3.74 % on the demo); a +10 pp borrow rate for 30 days costs $28,060, 4.5× the whole modelled expected loss.

**How.**
- **The rule,** from `docs/external/morpho/docs.morpho.org-developers-docs/contracts/irm.md` (AdaptiveCurveIRM): target utilisation 90 %, `CURVE_STEEPNESS` 4, `ADJUSTMENT_SPEED` 50 per year. With u the utilisation and e its normalised distance to the target:
  - the borrow rate is `rateAtTarget × curve(e)`, where the curve reaches 4× at 100 % utilisation and 1/4 at 0 %;
  - `rateAtTarget` grows as exp(50 × e × t), t in years: at 100 % utilisation it doubles in about 5 days (exp(50 × 5/365) ≈ 1.98).
- **Data.** `rateAtTarget(id)` is a public mapping on the IRM contract (address in the market parameters); utilisation is already read. A new `irm.py` with pure `borrow_rate(rate_at_target, u)` and `step(rate_at_target, u, dt)`.
- **Utilisation path.** Per Monte Carlo path, draw a utilisation path over the horizon: a two-state model (normal around its current level, stressed at 100 %), the entry probability into the stressed state and its length set in `registry.json` with a basis, later fitted from the market's history (archive RPC, version 1 step 6) or Morpho's API.
- **In the model.** `simulate.run` subtracts, per path, the extra interest (rate path − current rate) × debt × time from the carry. The rate also raises the debt, which lowers the HF: if the HF crosses 1 on a path, the position is liquidated with the existing rule.
- **A rate scenario for A1:** `--shock borrow_rate=+0.10` (10 pp for the horizon).

**Output.** A "rates" layer in the attribution table ("borrow rate: $X of expected loss") and the rate scenario in the scenario table.

**Tests.** The IRM formulas against the doc's constants (4× at 100 %, doubling in ≈ 5 days); the demo's +10 pp for 30 days gives $28,060.

**Size.** S.

### B2. The PT's implied yield (K11)

**Why.** A PT's price before maturity moves with its implied yield. On the demo (46.6 days left), +20 pp costs 2.2 % and +40 pp liquidates it under a market-tracking oracle. PT-reUSD's implied yield went from about 11 % to more than 20 % in nine minutes.

**How.**
- **Price.** PT price in the underlying = (1 + y)^(−T), T the time to maturity in years. A move Δy gives the new price; it is pure, in `pricing.py`.
- **Distribution.** From Pendle's `GET /v3/{chainId}/markets/{address}/historical-data` (fields `timestamp`, `impliedApy`), keyless, cached like the other Pendle calls: the distribution of the largest implied-yield rise over a window of the horizon's length. With little history, a registry default with a basis.
- **In the model.** A new event `pt_yield` with probability 1 per path and a drawn Δy. The price change goes to the collateral's market value, and to the oracle according to its type (B4): a market-tracking or TWAP oracle sees it; a linear-discount oracle does not.
- **Scenario:** `--shock pt_yield=+0.20` (20 pp).

**Tests.** The price table of `GAP.md` K11 (+5 pp → −0.59 %, … +40 pp → −4.04 %); the liquidation of the demo at +40 pp under a market-tracking oracle.

**Size.** S. One new cached Pendle call (`PROVIDERS.md` updated).

### B3. Horizon and stressed exit cost (K12)

**Why.** The rule compares a one-off exit cost ($78,946) with a 30-day loss, while the PT redeems at par in 46.6 days.

**How.**
- **Horizon.** For a PT, the default horizon becomes the time to maturity (`--horizon` still overrides). For open-ended positions it stays 30 days, and the exit cost is spread over the expected holding period, a registry parameter.
- **Three choices** compared in `decide.verdict`, each over the same horizon:
  - exit now: − exit cost;
  - hold to maturity: carry − expected loss;
  - de-lever: the existing `Reduction`.
- **Stressed exit cost.** Ask Pendle's swap quote at several sizes (already done for the de-lever), fit price impact against size, and recompute it at the pool depth of the stress scenario: depth × (1 − the share of LPs assumed to leave, a registry parameter).

**Output.** A three-row comparison table in the report; the exit cost shown "today" and "under stress".

**Tests.** The horizon rule; the three-way choice on synthetic numbers.

**Size.** S.

### B4. Oracle structure, and liquidation without an incident (K7, K8)

**Why.** The oracle decides which channel a shock takes, and "conservative" depends on the side: market-tracking is worst for a borrower, linear discount for a lender. The demo oracle is a `MetaOracleDeviationTimelock`, which is neither. On 2026-08-25 a $320k trade moved a TWAP oracle and liquidated 33 PT-reUSD positions at the demo's LLTV.

**How.**
- **Start from `oracle_class.py`** (plan `2026-10-10-sibling-markets`, D82–D84), which already classifies an oracle in `graph`: base vault, composites (`FEED_1`/`FEED_2`), wrappers (`innerOracle`), Pendle's `twapDuration` and `baseDiscountPerYear`, the feeds' round history, then registry name patterns. What B4 adds to it:
  1. **Use it in `analyze`**, in place of the price inference of `discover.infer_oracle`, which stays as the fallback for `not classified`. Then `price-tracking` maps to today's `market-tracking`, `constant-price` to `fundamental`.
  2. **Use it in `drain.py`**, which measures the gap without classifying (D70): a `constant-price` oracle is the case where the gap can grow, which can raise the `DrainWindow` alert's priority.
  3. **A third class for switching oracles (R7):** `MetaOracleDeviationTimelock` stays `not classified` today. Read `primaryOracle()`, `backupOracle()` and `currentOracle()`, classify each with the same code, and report the live one with the timelock before a switch.
  4. **Split `constant-price`** where the rule differs: exchange rate (follows the issuer's redemption rate) against fixed or linear discount (follows nothing), as Credora's Dynamic / Exchange / Fixed classes do (`EXTERNAL_SOURCE.md` §3).
- **Resolve its inputs:**
  - `MorphoChainlinkOracleV2`: price = SCALE × (base vault rate × base feeds) ÷ (quote vault rate × quote feeds), from `docs/external/morpho/lib/morpho-blue-oracles`. Each feed is classified as a market feed or an exchange rate (from its `description()`, already read by `admin.py`).
  - Meta-oracle: the primary and backup oracles (each resolved recursively), the deviation threshold, the challenge and healing timelocks, and which one is live (`currentOracle()`).
- **Map each type to a rule** that `propagate.loss` applies per event: which events the oracle sees (`issuer_depeg`, `pt_yield`, `pool`), with what lag (A2), and with what amplification.
- **Pool-move event.** For TWAP-based oracles, a new event `pool`: a trade of size Q moves the PT price by impact(Q), from Pendle quotes at several sizes. Its frequency comes from the implied-yield history (B2). Its loss is the liquidation incentive on the repaid debt, with no loss of value.

**Output.** The oracle node in the report says what it is, for example "meta-oracle: primary X, backup Y; switches after its challenge timelock once they deviate by more than its threshold" with the values read on-chain, and which shocks it passes.

**Tests.** `analyze --demo` takes its oracle mode from `oracle_class` with the inference as fallback; the meta-oracle's switch rule; a TWAP pool move that liquidates at the demo LLTV.

**Size.** M.

### B5. The priors (K17, K1, K3, K5, K2, K18)

All in `priors.py` and `registry.json`, each change with a stated basis:

| Gap | Change | How |
|---|---|---|
| K17 | Weight hacks by age | weight = 0.5^(age / half-life), half-life 1.5 years in the registry; the tier rate becomes Σ weights ÷ (protocols × effective years) |
| K1 | Tier by TVL at the hack date | DefiLlama `/protocol/{slug}` (keyless) gives each protocol's TVL history; take the TVL on the hack's date; keep hacked protocols now below $1M; show the rate with and without them |
| K3 | No double count | remove the oracle techniques from the hacks counted for the lending layer |
| K5 | Two-part depeg severity | for a synthetic dollar: a shallow Beta at the current frequency, plus a collapse branch with severity near total and its own frequency (from K2) |
| K2 | Off-chain prior | a registry `operational` block per off-chain issuer: custodian, CEX, fund manager, keys, each with a probability, a severity and a source |
| K18 | Protocol multiplier | base rate × m, m clipped to [0.25, 4]; m is a product of factors with a basis: admin powers (upgradeable, timelock, multisig threshold, from `admin.py`), upgrades since the last audit (`Upgraded` events), Nexus Mutual's cover price (`https://api.nexusmutual.io/v2/capacity`, keyless), immutability and formal verification (registry) |

**Output.** The basis line of each prior shows both parts: "category base rate 2.7 %/yr × 0.4 (immutable, formally verified) → 1.1 %/yr".

**Tests.** The decay weights; the survivorship count on the snapshot (305 of 1,070 hacks dropped today); m clipped at its bounds.

**Size.** S–M. Two new keyless calls (DefiLlama protocol history, Nexus Mutual), cached in `fixtures/snapshot/`.

## 6. Phase C: correlation, cascade and the tail

### C1. Named scenarios and a common shock (K6)

**Why.** Both teams asked for scenarios: Team 1 before any Monte Carlo, Team 2 as the basis of the breakeven. Every large loss in GAP.md's incident list was a chain of layers.

**How.**
- **Library.** A `scenarios` block in `registry.json`. Each scenario is a set of shocks with a basis and, where it applies, a time profile:
  ```json
  "usde_depeg_20": {"shocks": {"issuer_depeg": 0.20, "pt_yield": 0.15, "pool": 0.05},
                    "basis": "USDe −35 % on one CEX on 2025-10-10; on-chain pools held near par …"}
  ```
  Initial set: Nov 2025 contagion (issuer → issuer: several issuers depeg together), Resolv (unbacked mint: issuer collapse, the oracle keeps par), PT yield spike with a pool drain, CEX-only wick (no on-chain move: nothing happens, which is itself a check).
- **Run.** `analyze --scenarios` runs every scenario through A1 and prints a table with p\* per row (A3). The report puts this table before the Monte Carlo, as Team 1 asked.
- **Common shock.** In `simulate.run`, a latent "stress month" drawn with a registry probability; in a stress month, every layer's probability is multiplied by a registry factor. This creates the co-movement the independent draws lack.

**Tests.** Each scenario's shocks reach `propagate.loss`; with the common shock on, P(two layers in the same path) exceeds the product of their probabilities.

**Size.** M (the scenario sizes need sourcing).

### C2. Liquidation cascade with slippage (K9, M3 part 2)

**Why.** LlamaRisk measured PT supply on lending markets at 12.8× to 30× the Pendle AMM's depth, and its bad debt rose from $7M to $70M as the PT drop went from $0.12 to $0.21.

**How.**
- **The loop,** in a new pure `cascade.run(drop, curve, impact)`:
  1. at a drop d, the curves give the collateral liquidatable, summed over **every market that holds the collateral**: the held markets and their siblings, which `graph` now builds with the collateral seized at each step (D81);
  2. liquidators sell it: the price impact for that size gives an extra drop Δd;
  3. d ← d + Δd; stop when Δd is below a tolerance or after N rounds.
- **The impact curve:** for a PT, Pendle quotes at several sizes, fitted as impact(Q) = k·√Q; for other collateral, Team 1's parametric k·√Q with k in the registry (calibrated from KyberSwap quotes on on-chain venues only, when one is wanted).
- **Where it is used:** the final drop replaces the initial one in `propagate.loss` for the scenario, and in the watches' bad-debt curve.

**Output.** The scenario table gains "after the cascade: −x %".

**Tests.** No liquidation → no extra drop; a steep curve with a thin pool converges to a deeper drop; the loop stops.

**Size.** M.

### C3. A verdict that sees the tail (K13, K14)

**Why.** The demo's CVaR 99 % is 98 % of equity, yet the verdict is REDUCE, because EXIT depends on the mean only.

**How.**
- **Parameter uncertainty.** In `simulate.run`, draw each prior's probability from a Beta fitted to its counts (n hacks over N protocol-years) before drawing the incidents; repeat over K outer draws. Report the expected loss and CVaR as a 5–95 % range.
- **Rules,** in `decide.verdict`:
  - compare carry with the **upper** end of the expected-loss range;
  - EXIT when CVaR 99 % exceeds a second budget, `tail_budget_exit` (for example 80 % of equity), next to the existing REDUCE budget;
  - report P(loss > x % of equity) for x in a registry list.

**Tests.** A wider prior widens the range; the second budget turns REDUCE into EXIT.

**Size.** S–M.

## 7. Phase D: the vault depositor

### D1. `analyze --vault` (K16)

**Why.** The brief's setter runs curated vaults, and `comparison_team.md` §4.3 calls the depositor's loss the largest gap against the impact criterion. The watches have the exit queue and the drain threshold; a loss number under a scenario is missing.

**How.**
- **CLI.** `analyze --vault <address> [--user <address>]`, and `"kind": "vault"` pockets in a book (A3).
- **State.** `vault.discover_vault`, `vault.read_state` and `market_risk.VaultRisk` give each market, the vault's share of its supply, and every borrower's position.
- **Loss per scenario.** A scenario maps to a drop per collateral (BTC −30 %, USDe −20 %, a shared quote feed misreporting). For each market, `market_risk.value` at that drop gives the bad debt. The vault's loss = Σ share of supply × bad debt; the depositor's = their share of the vault × that. This is the table done by hand in `docs/vault-depositor-scenarios.md`, generated.
- **Market-price revaluation.** In `market_risk.value`, a second valuation of every position at the **market** price (DefiLlama, as the drain uses). For a market whose oracle does not follow the market, the bad debt at the market price is the real exposure, which the oracle-price valuation hides.
- **The drain as a loss channel.** If a scenario takes a market past d\* (`drain.py`), add the drainable amount × (1 − (1 − δ)/LLTV) as bad debt, and remove it from the exit capacity.
- **Exit.** The exit queue (`exit_queue.py`) gives what the depositor recovers at par per queue position; p\* per scenario uses the forgone yield plus the `forceDeallocate` penalty as the exit cost.
- **Version rule.** Vault V2 realises bad debt for every holder through `realAssets()`; for a V1.1 vault (once F2 reads it), the last holders take it.

**Output.** The two tables of `docs/vault-depositor-scenarios.md` §5, produced by the tool, with STAY / REDUCE / EXIT AS FAR AS POSSIBLE.

**Tests.** The Sentora numbers on the recorded replay (`fixtures/replay/0x6dc5…`): BTC −50 % gives about 61M of vault bad debt.

**Size.** M.

## 8. Phase E: discovery depth and the brief's scope items

Discovery is 30 % of the score, judged on "depth and correctness".

### E1. Depth in `analyze` (K19)

**How.**
- **Admin surface as layers.** Build an `admin.AdminWatch` for the position's market in `analyze` (it already runs in the watches). Each upgradeable contract becomes a node "upgrade of X" with a prior: the protocol base rate × B5's admin factor. Draw them in the report's graph and in `graph`.
- **One look-through level, on-chain where possible:**
  - an ERC-4626 vault in the oracle (`BASE_VAULT`): its `asset()`, and that asset's own oracle layers;
  - sUSDS → USDS → the PSM → USDC (addresses and the PSM's balance read on-chain);
  - a Pendle SY → its yield token (already discovered by `admin.py`).
- **Off-chain look-through as typed nodes.** From `registry.json` (custodians, CEX hedges, signing keys for each issuer), drawn as nodes with their source, so the depth shows even where it is not computed.
- **Siblings in `analyze`.** `graph` already finds them (`siblings.match`) and joins them through the shared node. In `analyze`, a sibling with a steep liquidation curve on the same collateral is a channel by which another market's liquidations push the position's collateral down; it enters C2's cascade.
- **Watch the siblings (R6).** `watch` follows only the held markets. Adding the siblings' `Liquidate` events and oracle moves to the poller's filters (the 9-address chunking already handles longer lists) turns them from a drawing into a signal.
- **Siblings on other venues (R5).** Euler, Aave, Silo or Fluid markets on the same collateral; one adapter per venue, M each.

**Tests.** The demo graph gains the admin and look-through nodes; each has a source.

**Size.** M.

### E2. Feed quality (K23)

**How.** `oracle_class.py` already reads each feed's latest round and recent history (`getRoundData`), and `graph` draws one node per feed, shared by the markets that read it. For every Chainlink-style feed:
- `latestRoundData()`: the age of the last update (`now − updatedAt`);
- heartbeat and deviation threshold: from Chainlink's published feed data (to probe; the local docs are `docs/external/chainlink/docs.chain.link-data-feeds-docs/`), otherwise a registry entry;
- `aggregator()` and the number of oracles, where the aggregator exposes it;
- shared feeds: the number of watched markets whose oracle reads the same feed (R3);
- for a meta-oracle: which source is live, and whether a challenge or a healing is running (`isChallenged()`, `isHealing()`).

A new alert `FeedStale` when the age exceeds the heartbeat × a registry margin, with a runbook row.

**Tests.** Staleness against a synthetic heartbeat; the shared-feed count on the Sentora replay (the `RLUSD / USD` feed under 7 markets).

**Size.** S–M.

### E3. TVL concentration (K25)

**How.** From DefiLlama `/protocols` (already cached) and on-chain supplies:
- the protocol's share of its category's TVL on the chain (Morpho in Ethereum lending);
- the market's PT collateral as a share of the PT's supply, and against the Pendle pool's depth (the LlamaRisk measure);
- the vault's share of each market (already computed);
- the collateral held across Blue markets, from `graph`'s market nodes (held and sibling), against the token's supply.

One concentration line per layer in the report; a registry threshold marks a "systemic node" and feeds B3's stressed exit cost.

**Size.** S.

## 9. Phase F: external venues and other chains

### F1. External venues (K24)

**Why.** The setter runs market-neutral strategies, so its positions have a hedge leg on a perp venue; USDe has the same structure inside.

**How.**
- A typed `venue` node in the registry and the graph: the venue (on-chain perp such as Hyperliquid, or a CEX), custody, the withdrawal delay, funding-rate exposure.
- A prior per venue with a basis (exchange failure, withdrawal halt), and a `funding` scenario: a negative funding rate for N days, applied to the hedge's notional.
- A book pocket `"kind": "hedge"` that offsets a spot pocket in A3's book.

**Size.** M for the typed node and scenario; a full perp-venue model is a separate project.

### F2. Other chains, Vault V1 (C5, C4)

**How.**
- **EVM chains:** make the chain a parameter: an RPC per chain in `keys.ini` (`[rpc]`), the Morpho addresses per chain from `docs/external/morpho/docs.morpho.org-developers-docs/contracts/addresses.md`, `chainId` in the Morpho and Pendle API calls, the cache keyed by chain.
- **Vault V1:** a second reader beside `vault.py`, from `docs/external/morpho/lib/metamorpho-v1.1` (withdraw queue, caps, `lostAssets`), plugged into the same rules, exit queue and drain.
- **Solana:** a new stack (accounts and programs instead of contracts and logs); out of scope before the event unless the book requires it.

**Size.** M per EVM chain after the first; Vault V1 M; Solana L.

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
| 6. Archive RPC, WebSocket | open; rate limits eased | an optional eRPC proxy over six free upstreams now absorbs rate limits and fails over (`docs/erpc.md`); its upstreams were chosen for recent blocks (tested 60 blocks behind the head), not for archive reads, so history-based priors (B2, C1 replays) still need an archive RPC |
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
