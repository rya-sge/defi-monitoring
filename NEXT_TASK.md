# Next task: the two main tasks to implement

This file picks the two tasks to build next from `NEXT_STEP_V2.md` and says how, file by file. Both come from phase A of that file: they make the tool answer the brief's question in the form it is asked (`docs/hackaton_instruction/GOAL.md`).

| # | Task | Gaps (`GAP.md`) | Criteria moved | Size |
|---|---|---|---|---|
| 1 | **Incident mode**: a component is hit, what does it do to the position, and how fast | K20, K22 | impact (30 %), decision (25 %) | S–M |
| 2 | **The book**: several positions as pockets, shared layers, the breakeven probability p\*, one headline | K21, M6 | decision (25 %), demo (15 %) | M |

## Contents

- [Why these two](#why-these-two)
- [Task 1: incident mode](#task-1-incident-mode)
- [Task 2: the book, the breakeven and the headline](#task-2-the-book-the-breakeven-and-the-headline)
- [Order of work](#order-of-work)
- [Decisions to confirm before starting](#decisions-to-confirm-before-starting)

## Why these two

- **The brief's question is conditional.** It asks for "the potential economic impact on that position **when one of them is affected**". `analyze` answers an unconditional question instead: an expected loss over 30 days, from yearly probabilities. Task 1 adds the conditional answer.
- **The brief's example is a book.** Ten pockets of 10 %, one affected, 11 % to unwind, "make that trade-off explicit". `analyze` takes one position, and gives no breakeven probability and no headline. Task 2 adds them.
- **Both reuse what exists.** `propagate.loss` already computes the loss of a given set of shocks, and `simulate`, `decide` and `report` need extensions, not rewrites. No new data provider is needed.
- **The teammates asked for them.** Team 1 wants scenarios before any Monte Carlo; Team 2 wants the breakeven probability, which needs no base rate.

## Task 1: incident mode

### Today, and what is missing

What `analyze` does today (checked 2026-10-10, `analyze --demo`):
- It answers an **unconditional** question: the expected loss over 30 days, drawn from yearly probabilities for six layers, then a STAY / REDUCE / EXIT verdict.
- The report's layer table has a column **"Loss if it happens"**: for each layer, the mean loss when that layer alone fails, at a severity drawn from its prior. That is the closest thing to an impact number.
- It does **not** accept an incident: `analyze --demo --shock oracle=0.10` fails with `unrecognized arguments: --shock`.

What is missing, and why it matters for the brief:
- **The user cannot say what happened.** The brief's task is the impact "when one of them is affected", and its worked example marks the oracle "incident". Today the only input is a probability; nobody can enter "the oracle reads 10 % low" or "USDe is at 0.92".
- **No verdict given the incident.** "Loss if it happens" is a number in a table, not a decision. When the incident is certain, the probabilities no longer matter, and the question becomes "loss of staying against cost of leaving now". Today's verdict always mixes in the 30-day probabilities.
- **No "how fast".** The brief asks what an incident does "and how fast". The report has no time to impact: it does not say whether the oracle will liquidate in one block, after a timelock, or never.
- **The watches cannot price an alert.** A critical alert says what happened, not what it costs the position.

### What the user would get (target output, not available today)

```bash
python -m riskdep analyze --demo --shock oracle=0.10
python -m riskdep analyze --demo --shock issuer_depeg=0.08 --shock amm=0.03
```

The output adds a block before the Monte Carlo result (figures illustrative):

```
INCIDENT  oracle −10.0 %
  liquidated: yes (liquidation from a 5.16 % oracle fall)
  loss: $27,400 (5.3 % of equity)
  how fast: the oracle switches after its challenge timelock (24 h); the exit takes one block
  exit now: $78,946; de-lever $1.29M (33 %) for $1,023 avoids the liquidation
  verdict given the incident: REDUCE
```

### Design

- **Events.** The six events `propagate.loss` already handles: `chain`, `issuer_hack`, `issuer_depeg`, `amm`, `oracle`, `lending`. Each severity is a fraction in [0, 1]. Nothing new in the propagation itself.
- **Verdict given an incident.** The probability is 1, so the rule compares amounts only:
  - **EXIT** if staying loses more than exiting costs: loss(shock) > exit cost;
  - **REDUCE** if a partial sale, sized with the existing `decide.sale_to_reach` to put liquidation beyond the shock, costs less than the loss it avoids;
  - **STAY** otherwise: the shock is absorbed, and leaving costs more.
- **How fast (K22).** A time to impact per oracle type, without waiting for task B4 of `NEXT_STEP_V2.md`:

  | What is known about the oracle | Time to impact reported |
  |---|---|
  | Etherscan name `MetaOracleDeviationTimelock` (the demo) | `challengeTimelockDuration()`, read on-chain: the backup takes over only after it |
  | `oracle_mode == "market-tracking"`, Chainlink-style | "at the feed's next update" |
  | `oracle_mode == "fundamental"` | "never: no liquidation; the loss stays with lenders" |
  | otherwise | "unknown" |

  The time to exit is "one block through the Pendle pool, at today's quote".

### File by file

| File | Change |
|---|---|
| `riskdep/scenario.py` (new) | `@dataclass ScenarioResult` (shocks, `loss_usd`, `loss_share_of_equity`, `liquidated`, `path`, `time_to_impact`, `exit_cost_usd`, `reduction`, `verdict`). Pure `impact(pos, shocks, recovery, pt_stress_extra) -> LossBreakdown` that calls `propagate.loss`. `parse_shocks(["oracle=0.10", …]) -> dict` that rejects unknown events and severities outside [0, 1] |
| `riskdep/decide.py` | Pure `verdict_given(pos, breakdown, quote, quote_for) -> (verdict, reduction)`, reusing `exit_cost_usd` and `sale_to_reach` |
| `riskdep/discover.py` | `oracle_timelock(f, oracle) -> int \| None`: reads `challengeTimelockDuration()` when the verified name is `MetaOracleDeviationTimelock` (already known from `oracle_verified`); keep the Etherscan name on the oracle node (`name=` attribute) |
| `riskdep/cli.py` | `--shock EVENT=SEVERITY`, repeatable, on `analyze`. When present, run the incident block in addition to the normal analysis (the Monte Carlo still runs: the two answers are shown side by side) |
| `riskdep/report.py` | `write(..., incident=None)`: an "Incident" section at the top of `report.html`, an `incident` key in `report.json`; `print` of the block in the terminal |
| `riskdep/registry.json` | nothing required; optional `incident_presets` (named shocks such as `oracle_10`) for the demo |
| `fixtures/snapshot/` | one new cached `eth_call` (`challengeTimelockDuration()` on the demo oracle), recorded with `--live` and committed (see `CLAUDE.md`, fixtures) |

### Tests (`tests/test_scenario.py`)

- An oracle shock just below the demo's liquidation distance (5.16 %) gives `liquidated == False`; just above gives `True`.
- A zero shock gives no loss and STAY.
- `parse_shocks` rejects `foo=0.1`, `oracle=1.5`, and `oracle` without a value.
- `verdict_given` on synthetic positions: EXIT when the loss exceeds the exit cost; REDUCE when the de-lever is cheaper than the loss; STAY otherwise.
- The demo's time to impact comes from the cached `challengeTimelockDuration()`.
- `analyze --demo --shock oracle=0.10` runs offline and writes the `incident` key.

### Done when

- the three example commands run offline on the demo;
- the report shows the incident block above the Monte Carlo;
- `README.md` (the `analyze` section), `docs/how-risk-is-computed.md` (a short section "When a component is hit") and the `CLAUDE.md` / `AGENTS.md` file tree are updated;
- the decisions go in a new plan, `plan/<date>-incident-and-book.plan.md`, from D75.

## Task 2: the book, the breakeven and the headline

### Today, and what is missing

What exists today:
- `analyze` takes **one position**: a Morpho borrow (`--morpho-market`, `--user`) or a PT holding (`--pendle-market`, `--pt-amount`). There is no `--book` option, and no way to analyse several positions together.
- Its headline is a sentence per position, for example "REDUCE: … the carry ($5,697) does not cover the expected loss ($6,265) …", followed by several dollar amounts.
- It ends with one global line, "A full exit would only pay if incident probabilities were 13.5× the estimates" (`risk_multiple_to_exit`). That is a partial answer to Team 2's breakeven argument, but it scales **all** probabilities at once.
- The watches follow several positions of one address, but each one separately; nothing adds them up.

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
- **Shared layers (M6).** Every pocket's graph has node ids (`chain:ethereum`, `issuer:0x…`, `oracle:0x…`, `lending:0x…`, `amm:0x…`). A layer shared by several pockets is the same node id. In the book's Monte Carlo, each **(event, node)** is drawn **once** per path and applied to every pocket that holds that node. Today each position draws its own, which treats one USDe depeg as two independent events.
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
- decisions are recorded in the same plan as task 1.

## Order of work

| Step | Content | Depends on |
|---|---|---|
| 1 | `scenario.py`, `parse_shocks`, `verdict_given`, their tests | — |
| 2 | `--shock` in the CLI, the incident block in the report | 1 |
| 3 | `oracle_timelock` and the time to impact; record the new `eth_call` in `fixtures/` | 1 |
| 4 | `breakeven`, `severe_loss`, the brief's example as a test | — |
| 5 | `book.py` loader and discovery | — |
| 6 | `simulate.run_book` with shared draws, its tests | 5 |
| 7 | `report.write_book`, `--book` in the CLI, the demo book recorded and committed | 4, 6 |
| 8 | `--book` with `--shock` | 2, 7 |
| 9 | docs, plan, guide | all |

Steps 1–3 deliver task 1 on their own; steps 4–8 task 2. Task 1 can ship first.

## Decisions to confirm before starting

- **The demo book.** Which positions: the current PT-sUSDe loop, plus real addresses close to your own pockets (a second PT, a stablecoin holding)? Each needs one `--live` recording.
- **"Severe case"** at the 95th percentile of each layer's severity, or a fixed table of named scenarios (C1 of `NEXT_STEP_V2.md`) from the start?
- **Weights from equity** (real positions as they are), or a target weight per pocket with the amounts scaled (simpler to read, but the exit quote is no longer a real quote at that size)?
- **Verdict given an incident:** is "loss > exit cost → EXIT" the rule you want, or should the residual risk after the incident (the Monte Carlo on the shocked position) also count?
