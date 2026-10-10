# Next task: the two main tasks to implement

This file picks the two tasks to build next from `NEXT_STEP_V2.md` and says how, file by file. Both come from phase A of that file: they make the tool answer the brief's question in the form it is asked (`docs/hackaton_instruction/GOAL.md`).

| # | Task | Gaps (`GAP.md`) | Criteria moved | Size |
|---|---|---|---|---|
| 1 | ~~**Incident mode**: a component is hit, what does it do to the position, and how fast~~ **done** (plan `2026-10-10-incident-mode`) | K20, K22 | impact (30 %), decision (25 %) | S–M |
| 2 | **The book**: several positions as pockets, shared layers, the breakeven probability p\*, one headline | K21, M6 | decision (25 %), demo (15 %) | M |
| 3 | **Conditional Monte Carlo**: the observed incident forced in every path, its evolution and spread drawn | K6, K14 | impact (30 %), decision (25 %) | M |

## Contents

- [Why these two](#why-these-two)
- [Task 1: incident mode — done](#task-1-incident-mode--done)
- [Task 2: the book, the breakeven and the headline](#task-2-the-book-the-breakeven-and-the-headline)
- [Task 3: conditional Monte Carlo](#task-3-conditional-monte-carlo)
- [Order of work](#order-of-work)
- [Decisions to confirm before starting](#decisions-to-confirm-before-starting)

## Why these two

- **The brief's question is conditional.** It asks for "the potential economic impact on that position **when one of them is affected**". `analyze` answers an unconditional question instead: an expected loss over 30 days, from yearly probabilities. Task 1 adds the conditional answer.
- **The brief's example is a book.** Ten pockets of 10 %, one affected, 11 % to unwind, "make that trade-off explicit". `analyze` takes one position, and gives no breakeven probability and no headline. Task 2 adds them.
- **Both reuse what exists.** `propagate.loss` already computes the loss of a given set of shocks, and `simulate`, `decide` and `report` need extensions, not rewrites. No new data provider is needed.
- **The teammates asked for them.** Team 1 wants scenarios before any Monte Carlo; Team 2 wants the breakeven probability, which needs no base rate.

## Task 1: incident mode — done

**Status: implemented on 2026-10-10** (plan `2026-10-10-incident-mode`, decisions D89–D95), with the detection link of `ANALYSIS_CURRENT.md` §7 step 3 added to it. It covers the brief's chain on one position: detect → impact → how fast → decide.

### What the user gets now

```bash
python -m riskdep analyze --demo --shock oracle=0.10
python -m riskdep analyze --demo --shock issuer_depeg=0.08
```

```
INCIDENT  issuer_depeg 8.0%
  not liquidated; loss $78,684 (15.1% of equity)
  after the oracle switches (16 h): liquidated; loss $520,236 (100.0% of equity)
  how fast: not before 16 h: the primary source does not follow the market; if the two sources diverge by more
            than 0.75%, a challenge can switch it to the other one after 16 h (the other source is price-tracking)
  exit now: $78,946 (Pendle swap quote)
  verdict given the incident: REDUCE: selling part of the collateral costs $1,313 and leaves a loss of $51,016,
            less than staying ($520,236) or exiting ($78,946), counted after the oracle switch, which leaves 16 h to act
EX ANTE (Monte Carlo, before any incident):
REDUCE: ...
```

With `--shock oracle=0.10` the oracle already reports the shocked price: the demo is liquidated now, with a loss of $478,591 or 92 % of equity, and a sale of about a third of the collateral avoids it.

### What was built

| Part | What | Where |
|---|---|---|
| Impact | `propagate.loss` with the given shocks; loss, liquidation, the oracle's drop, the propagation path | `riskdep/scenario.py` (`assess`) |
| Decision | with the incident certain, no probability: REDUCE if a partial sale plus what it still loses is cheapest, else EXIT if staying loses more than exiting, else STAY | `decide.verdict_given` |
| How fast | the oracle's profile: a meta-oracle's timelock, threshold, live and other source, each classified; otherwise the class of its inputs and a Pendle TWAP window (`oracle_class`) | `scenario.oracle_profile`, `scenario.time_to_impact` |
| Meta-oracle | the impact now, through the live source, and after the switch to the other source; the verdict counts the latter, with the timelock as the time left | `scenario.assess` (D94) |
| Detection → impact | an `OracleDivergence` alert on a borrowed market carries the loss on that borrow, the liquidation, and the time to impact; `depositor_impact` is set | `scenario.enrich_divergence`, `watch_user.py` (D93) |
| Report | an "Incident" section above the ex-ante one; `incident` in `report.json` | `report.py` |
| Shared code | the market-oracle classification moved from `graph._oracle` to `oracle_class.classify_market_oracle`, reused by both | `oracle_class.py`, `graph.py` |
| Tests | 9 tests, including the demo's meta-oracle read offline and a synthetic divergence alert | `tests/test_scenario.py` |

### What it found

**The demo oracle does not follow the market today.**

- **Its live source** is a Pendle linear-discount oracle (`baseDiscountPerYear`); its backup reads `USDe / USD`.
- **A USDe depeg** therefore liquidates nothing for 16 hours. If the gap stays above 0.75 % and the challenge is accepted, the switch to the backup then liquidates the position.
- **`analyze`'s price inference** classed the same oracle as market-tracking (ambiguous, near par). *Since D96* the ex-ante simulation takes the mode from the structure: still market-tracking, because the switch falls within the 30-day horizon, but on a stated basis rather than a guess. The 16 h delay is visible only in incident mode, since the simulation has no time axis (`GAP.md` K7).

### Left for later

- **Other alert types** carry no impact yet: an upgrade of the oracle or the collateral token, an oracle move, `DrainWindow` for a vault depositor (which has its own impact already).
- **Detection** was sped up afterwards (D97): the oracle-versus-market check runs every batch with market prices at most 25 blocks old, instead of every 300 blocks.
- **The exit cost is today's quote**: in an incident the pool may be thinner (`GAP.md` K12).

## Task 2: the book, the breakeven and the headline

### Today, and what is missing

What exists today:
- `analyze` takes **one position**: a Morpho borrow (`--morpho-market`, `--user`) or a PT holding (`--pendle-market`, `--pt-amount`). There is no `--book` option, and no way to analyse several positions together.
- Its headline is a sentence per position, for example "REDUCE: … the carry ($5,697) does not cover the expected loss ($6,265) …", followed by several dollar amounts.
- It ends with one global line, "A full exit would only pay if incident probabilities were 13.5× the estimates" (`risk_multiple_to_exit`). That is a partial answer to Team 2's breakeven argument, but it scales **all** probabilities at once.
- The watches follow several positions of one address, but each one separately; nothing adds them up.
- `graph` can draw several users and vaults together (`graph.build_all`), with their shared assets, oracles and feeds, and since the sibling-markets work, the other Blue markets on the same collateral. It draws the book's structure but computes no loss, no weight and no verdict for it.

What is missing, and why it matters for the brief:
- **No book.** The brief's example is a book of ten 10 % pockets, one affected. Its answer depends on the pocket's weight: the same loss is 10 % of the book or 1 %. Today no number is expressed as a share of a book, and the example cannot be entered.
- **Shared layers counted as independent.** Two pockets backed by the same issuer, or priced by the same feed, fail together. Run one by one, each draws its own depeg, so their joint failure looks rarer than it is and the book's tail looks thinner. This is gap M6 in `ANALYSIS_MONITORING.md`.
- **No breakeven per scenario.** The brief asks to make "expensive and certain against cheap and uncertain" explicit. The breakeven probability p\* = (exit cost + carry) / L(scenario) does exactly that, scenario by scenario, without relying on a base rate. `docs/scenarios-and-breakeven.md` explains it; the tool does not compute it. The "13.5×" line is one global multiplier, not a probability a manager can compare with their own view of a given scenario.
- **No single headline.** The brief's subtitle asks for "one number a portfolio manager can act on". Today the reader gets a verdict and several amounts, but no line that says which pocket to act on and above which probability.

### What the user would get (target output, not available today)

```bash
python -m riskdep analyze --book book.json
python -m riskdep analyze --book book.json --shock issuer_depeg=0.20
```

```
BOOK  Book A · 3 pockets · equity $1.9M
  shared layers: Ethereum (3 pockets), USDe issuer (2), Morpho Blue (3)
  expected loss 30 d: $9,800 (0.52 % of the book), CVaR 99 %: $640,000 (34 %)
  worst severe case: USDe depeg (95th percentile, −19 %): book −14 %, pocket "PT-sUSDE loop" liquidated
    exiting that pocket costs $78,946 (4.2 % of the book) and pays if P(depeg) > 22 % this month
  verdict: REDUCE "PT-sUSDE loop"; STAY the others
```
(Figures illustrative.)

### Design

- **A pocket is a real position, not a scaled one.** Each pocket is discovered as `analyze` does today: a Morpho borrow, or a PT holding. Its weight is its equity over the book's total. Scaling a position to an arbitrary weight would need a new exit quote at each size, which is not real data.
- **Book file:**
  ```json
  {
    "name": "Book A",
    "pockets": [
      {"name": "PT-sUSDE loop", "kind": "morpho", "market": "0x…", "user": "0x…"},
      {"name": "PT holding", "kind": "pt", "pendle_market": "0x…", "pt_amount": 250000}
    ]
  }
  ```
  Vault pockets (`"kind": "vault"`) wait for `analyze --vault` (D1 of `NEXT_STEP_V2.md`); the loader rejects them with a clear message.
- **Shared layers (M6).** Every pocket's graph has node ids (`chain:ethereum`, `issuer:0x…`, `oracle:0x…`, `lending:0x…`, `amm:0x…`). A layer shared by several pockets is the same node id. In the book's Monte Carlo, each **(event, node)** is drawn **once** per path and applied to every pocket that holds that node. Today each position draws its own, which treats one USDe depeg as two independent events. Two pockets can also share a layer without sharing an oracle: two oracles that read the same Chainlink feed. `graph` already decomposes oracles into one node per feed (via `oracle_class`), so `book.shared_layers` adds the feed addresses of each pocket's oracle to its node ids, and a shared feed (R3) is drawn once too.
- **Breakeven probability** for each pocket and each layer, as in `docs/scenarios-and-breakeven.md`:

  $$p^\star = \frac{\text{exit cost} + \text{carry}}{L_{\text{severe}}}$$

  - L_severe is the pocket's loss when that layer fails at the **95th percentile** of its severity (the Beta's quantile, from the same prior);
  - exit cost is today's Pendle quote;
  - carry is what staying earns over the horizon;
  - exiting pays if one believes the layer fails with probability above p\* over the horizon. No base rate enters.
- **Headline.** The first line of the report: the worst severe case across pockets, as a share of the book; the pocket it hits; its exit cost as a share of the book; its p\*; then each pocket's verdict.
- **With `--shock`.** Task 1's incident is applied to every pocket holding the affected layer, and the book's loss is summed.

### File by file

| File | Change |
|---|---|
| `riskdep/book.py` (new) | `load(path) -> Book` (validation); `discover(f, book) -> list[Position]` using `discover.discover_morpho_position` / `discover_pt_holding`; pure `shared_layers(positions) -> dict[node, list[pocket]]` |
| `riskdep/simulate.py` | `run_book(positions, priors_per_pocket, horizon, n, seed) -> BookSimResult`. It builds the set of unique (event, node) keys, draws `hits` and `sev` once per key, and computes each pocket's loss with the existing `_loss`. The D12 link (issuer hack → depeg) is kept per issuer node. Book-level expected loss, VaR and CVaR come from the summed losses; each pocket's own figures are still reported |
| `riskdep/decide.py` | Pure `breakeven(exit_cost, carry, loss_if) -> float` (inf when `loss_if` is 0); `severe_loss(pos, prior, q=0.95)` that calls `propagate.loss` at the Beta quantile (`scipy` is not a dependency: use `numpy` draws and `np.quantile`, seeded) |
| `riskdep/report.py` | `write_book(book, positions, book_sim, decisions, …)`: the headline, a pocket table (weight, expected loss, CVaR, liquidation distance, verdict), a shared-layer table, a p\* table (pocket × layer), and one section per pocket reusing today's position section |
| `riskdep/cli.py` | `--book PATH` on `analyze`, exclusive with `--demo` / `--morpho-market` / `--pendle-market` |
| `examples/book-demo.json` (new) | a demo book from positions already in `fixtures/snapshot/` plus one more, recorded with `--live` and committed |
| `riskdep/registry.json` | `severe_quantile: 0.95`, with its basis (Team 2's "severe case") |

### Tests (`tests/test_book.py`)

- **The brief's example.** Ten pockets of 10 %, one wiped out in its severe case, an exit cost of 11 % of the pocket and no carry: the book loses 10 %, exiting costs 1.1 % of the book, and p\* = 11 %. This is a pure test of `breakeven` and the share arithmetic.
- **Shared node drawn once.** Two pockets with the same issuer node: in every path where one has the depeg, so does the other. Two pockets with different issuers: they co-occur at about the product of their probabilities.
- **A single-pocket book** gives the same expected loss as `analyze` on that position (same seed).
- **Loader errors:** an unknown `kind`, a `vault` pocket, an empty book.
- **The demo book** runs offline and writes the headline.

### Done when

- `analyze --book examples/book-demo.json` runs offline, prints the headline and writes `report.html` / `report.json`;
- the brief's example passes as a test;
- `README.md`, `docs/scenarios-and-breakeven.md` (a note that the breakeven is now computed), `ANALYSIS_MONITORING.md` (M6 marked partial or done), `GAP.md` (K21) and the guide's file tree are updated;
- decisions go in a new plan, from D96 (D89–D95 are taken by plan `2026-10-10-incident-mode`).

## Task 3: conditional Monte Carlo

**Why.** Incident mode gives one deterministic answer. Once an incident is known, its evolution is still uncertain: how deep a depeg goes, whether it recovers, whether it spreads to the Pendle pool, other issuers or sibling markets, how the borrow rate reacts. The brief's "staying is cheap and uncertain" is that distribution (`ANALYSIS_CURRENT.md` §6).

**How.**
- In `simulate.run`, an `observed` argument: the observed layers have `hits = True` in every path, and their severity is drawn from "the observed size or worse", with a probability of recovering (registry, with a basis from past incidents of the same kind).
- The other layers' probabilities depend on the incident: a depeg raises the Pendle pool's and the oracle's (the K6 links, now with a purpose).
- The meta-oracle's switch (D94) becomes a draw: the depeg lasts past the timelock or not.
- Output: the loss distribution of staying against the certain exit cost, the breakeven p\* for the bad branch, shown under the deterministic incident block.

**Builds on.** `scenario.assess` (the deterministic case is the special case of a severity that does not move), `simulate.run`.

**Size.** M.

## Order of work

| Step | Content | Depends on |
|---|---|---|
| 1 | ~~`scenario.py`, `parse_shocks`, `verdict_given`, their tests~~ done | — |
| 2 | ~~`--shock` in the CLI, the incident block in the report~~ done | 1 |
| 3 | ~~the oracle profile and the time to impact, recorded in `fixtures/`; the alert link in `watch --user`~~ done | 1 |
| 4 | `breakeven`, `severe_loss`, the brief's example as a test | — |
| 5 | `book.py` loader and discovery | — |
| 6 | `simulate.run_book` with shared draws, its tests | 5 |
| 7 | `report.write_book`, `--book` in the CLI, the demo book recorded and committed | 4, 6 |
| 8 | `--book` with `--shock` | 2, 7 |
| 9 | docs, plan, guide | all |
| 10 | conditional Monte Carlo (task 3) | 1–3 done; 6 for the shared draws |

Steps 1–3 delivered task 1. Next: steps 4–8 (task 2), then step 10 (task 3).

## Decisions to confirm before starting

- **The demo book.** Which positions: the current PT-sUSDe loop, plus real addresses close to your own pockets (a second PT, a stablecoin holding)? Each needs one `--live` recording.
- **"Severe case"** at the 95th percentile of each layer's severity, or a fixed table of named scenarios (C1 of `NEXT_STEP_V2.md`) from the start?
- **Weights from equity** (real positions as they are), or a target weight per pocket with the amounts scaled (simpler to read, but the exit quote is no longer a real quote at that size)?
- **Verdict given an incident (implemented as D90):** REDUCE when a partial sale plus its remaining loss is cheapest, else EXIT when staying loses more than exiting, else STAY. The residual risk after the incident is task 3; confirm the rule before it is extended.
