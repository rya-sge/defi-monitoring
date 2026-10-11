# Improvements against the brief

Review of the project against the DeFi Risk Dependency Challenge (`docs/hackaton_instruction/GOAL.md` and the PDF next to it), on 2026-10-11, read the way a judge would read it. It checks what runs today (`pytest`: 268 passed; `analyze --demo`; `analyze --book examples/rockawayx-ethereum.json --shock token=PST:0.30`), not what the plans promise. `docs/analysis/NEXT_STEP.md` keeps the full backlog; this file says which items matter most for the score, and adds the ones it misses.

> **Status, 2026-10-11 (updated).** Priorities 1 and 2 are done: every item below carries its status and the plan that built it. Left: priority 3 except feed quality and TVL concentration, and priority 4. The order of the remaining work is in `docs/analysis/NEXT_STEP.md` §3. The review below is kept as written.

## Verdict

The engineering is well above what a hackathon usually shows: real mainnet data, recorded and replayable, a shock engine with rules in a registry, incident mode, time to impact, a book of vaults with breakeven p\*, cross-checks, 268 offline tests, CI and a web UI. The risk is not missing depth: it is that **a judge cannot find the answer to the brief's question in under five minutes**, and that **two numbers in the demo are not yet defensible** (a verdict reason inside the sampling noise, a STAY next to a 12 % loss with no reason given).

| Criterion (weight) | Estimate | Strongest point | Main weakness |
|---|---|---|---|
| Dependency discovery (30 %) | strong | vault → adapters → markets → borrowers/lenders, oracle classes, admin surface, siblings, wrapped collateral | `analyze` (the PT position, the brief's own example) uses neither siblings nor the admin surface; Ethereum and Morpho only; feed quality and TVL concentration (two of the brief's scope items) not measured |
| Impact estimation (30 %) | good, not yet proven | deterministic impact of a known incident, the same number from `analyze` and `shock` | never backtested on a real incident; rate and implied-yield channels and the liquidation cascade missing; exploit priors from a biased hack history |
| Decision usefulness (25 %) | good on vaults, uneven | STAY / REDUCE / EXIT, de-lever size, p\*, "act first on" | the brief's 10 × 10 % / 11 % trade-off is not a runnable command; some verdicts come without their reason; two verdict code paths (`decide.py` for a borrow, `vault_incident.py` for a vault) |
| Working demo (15 %) | strong | everything runs offline from mainnet recordings | five CLI modes, a 31 KB README and a 40 KB agent guide: no single entry path; no HTML for vault and book incidents |

## Priority 1: make the answer findable (hours, high score impact)

### 1.1 One demo command for the brief's own example

**Problem.** The brief's central trade-off, a book of ten 10 % pockets, one hit, 11 % slippage to unwind, is discussed in `GAP.md` and `NEXT_STEP.md` but no command reproduces it. A judge will look for it first.

**Status: done** (plan `2026-10-11-judge-path`): `analyze --book examples/brief-ten-pockets.json --shock token=mGLOeuro:0.30 --exit-cost 0.11` prints "Leaving Belem RWA EURCV costs 110,000 USD for sure, against 53,445 saved if the incident comes: stay"; the `pocket` weighting and `--exit-cost` are in the CLI and the API. The web Impact page is left to the front end.

**How.** Add `examples/brief-ten-pockets.json` (ten recorded vaults or positions, `weighting: depositor`, equal weights) and a `--exit-cost 0.11` override on `analyze --book`, so the run prints, for the hit pocket: certain cost of leaving (11 % of 10 % = 1.1 % of the book), the loss of staying given the incident, p\*, and the verdict. Then add the same scenario as the first item of the web Impact page. Size: S.

### 1.2 A one-page judge path

**Problem.** The README opens with five modes and the eRPC proxy; the answer to "stay or exit, and why" appears around line 150.

**Status: done** (plan `2026-10-11-judge-path`): "The answer in five minutes" opens the README, with three commands and a table of the output lines that answer each criterion; the backtest's result table follows it.

**How.** Put at the top of `README.md` (or in `DEMO.md`, linked from line 1) three commands and their expected output, in this order: the dependency graph of one position (`graph --replay`), a known incident on it (`analyze --demo --shock oracle=0.10`), and the book (`analyze --book … --shock …`). Map each to the criterion it answers, reusing the table in `GOAL.md`. Move eRPC, cross-checks and the alert tables below. Size: S.

### 1.3 Fix stale numbers in the docs

`README.md:23` says 257 tests, `NEXT_STEP.md:30` says 188; the suite has 268. A judge who runs the tests sees the mismatch. Either drop the count or update it in one place. Size: S.

**Status: done:** the count is kept in `CLAUDE.md` only.

## Priority 2: make every number defensible (days, impact estimation 30 %)

### 2.1 Say why a verdict is STAY when the loss is large

**Problem.** In the PST −30 % book run, *RockawayX Confidential RWA USDC* loses 3.27M USD (12.4 %) and reads `STAY` with p\* `—`; *Huma USDC Main* loses less and reads `EXIT`. The JSON shows why (`saved_usd: 0`: leaving first saves nothing, presumably because the loss is already realised or shared pro rata), but the output does not say it. To a reader it looks like a bug.

**Status: done** (plan `2026-10-11-judge-path`): every book line says why, "n/a" replaces "—", and a vault's no-saving reason names its cause. The 99 % holder behind Confidential RWA's STAY turned out to be the Zama cShare, a pool of confidential depositors (plan `2026-10-11-zama`): the line now reads for its largest public holder, "leaving pays above a 6.6 % chance over 30 days".

**How.** Give every vault line a one-clause reason, from the fields already computed: "leaving saves nothing: the loss is socialised at once", "exit blocked: no idle liquidity", "p\* above the outside view". Show "n/a (nothing to save)" instead of `—`. Size: S.

### 2.2 Do not state a reason the simulation does not establish

**Problem.** `analyze --demo` opens with "the carry ($5,697) does not cover the expected loss ($6,265)". `ANALYSIS_CURRENT.md` §5 already shows the expected loss is 6,265 ± 380 USD, so the carry is inside its 95 % interval. The verdict holds on its two other reasons, but a judge testing "is the number defensible" will find this.

**Status: done** (plan `2026-10-11-judge-path`): "expected loss $6,265 ± $745 (95 %, 20,000 paths)"; the carry gap reads "about equal" and is no longer a reason to REDUCE on its own (the demo's REDUCE stands on its tail and liquidation reasons).

**How.** Print the expected loss with its standard error, and phrase a reason that rests on a difference inside the interval as "about equal" (`NEXT_STEP.md` B7). Size: S.

### 2.3 Backtest on a real incident

**Problem.** Nothing shows the engine's numbers against what actually happened. This is the single strongest argument for "is the number defensible", and the repository already names the case: the PT-reUSD liquidations of 2026-08-25 (`NEXT_STEP.md` B9). USDe at −8 % on 2025-10-10 is a second one.

**Status: done** (plan `2026-10-11-backtest`): `riskdep backtest` replays the PT-reUSD liquidations of 2026-08-25 through an archive RPC, recorded keyless: the same 13 + 7 borrowers predicted as liquidated, none missed; in the USDC market debt and incentive within 0.8 %; no bad debt, as observed. The table is in the README. Left: the squeeze at that date. A second episode is done (plan `2026-10-11-backtest-crash`): the 2025-10-10 crash on six markets, no liquidated borrower missed; USDe itself barely reached Morpho that night.

**How.** Record the graph at the block before the incident (an archive RPC is needed; one free archive endpoint or a one-day paid key is enough), apply the observed shock, and compare predicted against realised liquidations and bad debt from `Liquidate` events. Report the error in a table in the README, even if it is large: a measured error is more credible than an unmeasured one. Size: M.

### 2.4 Conditional Monte Carlo around the known incident

**Problem.** The Monte Carlo draws incidents from yearly priors (an ex-ante view); the brief asks about a known incident. `ANALYSIS_CURRENT.md` §6 explains this well, but it is not built (`NEXT_STEP.md` A4).

**Status: done for vaults and books** (plan `2026-10-11-conditional`): `--conditional` draws the incident's size and whether liquidators act, reads the losses off real incident runs, and gives the loss of staying (mean, median, 95th, 99th percentile) against the certain cost of leaving; on the ten pockets, 52,067 on average against 110,000, but 246,211 at the 95th percentile. Left: a borrow position's, common-mode second failures, calibration.

**How.** As planned: force the observed layer in every path, draw its evolution (recover or deepen) from past incidents of the same kind, draw the other layers given it. Output: the loss distribution of staying against the certain exit cost, which is exactly the brief's "exiting is expensive and certain, staying is cheap and uncertain". Size: M.

### 2.5 The missing loss channels of the brief's PT example

**Status: done as incidents** (plan `2026-10-11-pt-channels`): `--shock pt_yield=…` and `--shock borrow_rate=…`, with their timing (and the meta-oracle switch on a PT fall); not yet Monte Carlo layers. The cascade (B6) is partly in the shock engine's squeeze; the returned liquidity is not.

The PT-on-Morpho loop loses money without any incident through the borrow rate (AdaptiveCurveIRM up to 4× at full utilisation) and through the PT implied yield (`NEXT_STEP.md` B1, B2). Both are small and use data already read. Then the liquidation cascade with slippage (B6). Size: S each, M for B6.

## Priority 3: discovery depth on the brief's scope items (dependency discovery 30 %)

| Item | Why it counts | How | Size |
|---|---|---|---|
| Discovery depth in `analyze` — *done* (plan `2026-10-11-depth`: the meta-oracle, admins and timelocks, siblings, grade and backing, concentration in the PT report) | the brief's worked example is the PT position, and it is the mode with the shallowest discovery | reuse `siblings.py` and `admin.py` in `discover.py`, so the PT report lists the same layers as `graph` | M |
| Feed quality — *done in part* (plan `2026-10-11-feed-quality`: freshness against each feed's rhythm, in `graph` and vault incidents; the fork demo reads the band and the timelock; `FeedStale` alert left) | named in the brief ("oracle dependency and feed-quality analysis") | per feed: heartbeat, deviation threshold, last update age, number of transmitters, admin; from `oracle_class.py` and Chainlink's aggregator (`NEXT_STEP.md` C2) | S–M |
| TVL concentration — *done in part* (plan `2026-10-11-feed-quality`: each protocol's share of DeFi and of its category in `graph`; supply share left) | named in the brief ("protocols concentrating a large share of on-chain TVL") | per protocol node in `graph`: its share of the chain's TVL (DefiLlama, already a source), flagged above a registry threshold (C3) | S |
| External venues — *open (C4)* | named in the brief ("vaults that deploy into an external venue, for instance a perp exchange") | at least one off-chain venue as a graph node with a registry prior and an exit delay; Ethena's CEX custody is the obvious first one, since `sUSDe` is already the demo's main driver (C4) | M |
| Second ecosystem — *open (C5)* | "any ecosystem" is allowed, not required | lowest priority for the score; Vault V1 (MetaMorpho) on Ethereum widens coverage more cheaply than a second chain (C5) | M–L |

## Priority 4: coherence of the product

- **One verdict engine.** *Open (NEXT_STEP A6).* A borrow position (`decide.py`) and a vault (`vault_incident.py`, `vault_book.py`) reach STAY / REDUCE / EXIT by different code and different wording. A mixed book (borrow + vault + PT pockets, `NEXT_STEP.md` A2) needs one; build it before adding a third path.
- **HTML for vault and book incidents** (A5). *The API is done (`POST /api/incident`, plan `2026-10-11-incident-api`); the page is the front end's.* The PT report has HTML; the book, which is the closest answer to the brief, prints only to the terminal and JSON. The web Impact page reads a committed example trace (`api.shockTrace()`), not a live run; wiring it to `POST /api/incident` (in progress in the working tree) closes that.
- **Detection → impact for vaults** (A3). *Open: after the fork demo's `admin.py` lands.* Only `OracleDivergence` in `watch --user` carries an impact; a vault depositor's critical alert should carry its loss, time to impact and verdict too.

## What not to spend time on before the judging

- Push alerts, Bundles execution, forked-chain tests, reliable infrastructure (`NEXT_STEP.md` phase D): they do not move any criterion.
- More documentation. There are already some forty Markdown documents; the gain now is in pointing to the right three, not in writing a fourth.
- Refining the unconditional priors (B5) before the conditional simulation exists: they answer the secondary question.

## Recommended order

*Steps 1 to 4 are done (except the alert for feed quality); step 5 remains, as `NEXT_STEP.md` A3, A6 and C1.*

1. 1.1 ten-pocket example, 1.2 judge path, 1.3 stale counts, 2.1 STAY reasons, 2.2 sampling error: one day together, the largest score gain per hour.
2. 2.3 backtest: the strongest defensibility argument.
3. Feed quality and TVL concentration: two brief scope items at size S.
4. 2.4 conditional Monte Carlo, then 2.5 rate and implied-yield channels.
5. Discovery depth in `analyze`, one verdict engine, HTML for books.
