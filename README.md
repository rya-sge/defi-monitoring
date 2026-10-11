# defi-monitoring

Risk tooling for DeFi positions on Ethereum, built with the charrette loop: design and decisions first (`plan/`), then code. Five modes:

- **`analyze`**: batch risk report for a Pendle-PT position on Morpho Blue. It discovers the dependency stack, simulates incidents on each layer and ends with STAY / REDUCE / EXIT. Plan: `plan/2026-10-10-defi-risk-dependency.plan.md`.
- **`watch`**: follows a **Morpho Vault V2** block by block and alerts on every transaction that changes a depositor's exposure, losses or ability to exit. Plan: `plan/2026-10-10-morpho-vault-v2-watcher.plan.md`.
- **`watch --user`**: finds every Morpho Blue borrow and Vault V2 deposit of an address and follows them together: health factor, liquidation, actions on your behalf, borrow rate. Plan: `plan/2026-10-10-morpho-user-watcher.plan.md`.
- **`graph`**: draws the dependency graph of a vault or an address, with the sibling markets around it. Plan: `plan/2026-10-10-sibling-markets.plan.md`.
- **`shock`**: applies a failure to a node of that graph (an oracle reading low or high, a frozen feed, a collateral falling) and propagates it to every market, vault and depositor, by rules you can change. Plan: `plan/2026-10-10-propagation-engine.plan.md`.

## The answer in five minutes

The brief asks: a dependency of a position is hit; how much is lost, how fast, and should you stay or exit despite what exiting costs (`docs/hackaton_instruction/GOAL.md`). Three commands answer it, offline, on mainnet recordings of the sponsor's vault and its curator's book (`uv sync` first):

```bash
# 1. Dependency discovery (30 %): what RockawayX USDC Yield depends on, siblings, oracle classes, issuer grades
uv run python -m riskdep graph --vault 0xE0181090c22579B6A217f1522cbf8c9f1F0C1965 --replay        # → out/graph.html

# 2. Impact and decision (30 % + 25 %): fxSAVE marked down 30 %, for the f(x) vault and its largest depositor
uv run python -m riskdep analyze --vault 0x2cA22cb25558fa2018ecb1CE4eD8AF92Ee7ea423 --shock token=fxSAVE:0.30

# 3. The brief's own trade-off: ten 1M pockets, one hit, an 11 % cost to unwind it
uv run python -m riskdep analyze --book examples/brief-ten-pockets.json --shock token=mGLOeuro:0.30 --exit-cost 0.11 --conditional
```

What to read in the output:

| Output line | Answers |
|---|---|
| `fxSAVE/USDC …: 1,494,648 of 25,324,668 USDC of debt liquidatable (19 borrowers); bad debt 2,284,812 …` | the impact, market by market, from the shock engine over the recorded graph |
| `oracle constant-price; how fast: at its next published round, by a transaction …` | how fast it lands |
| `verdict given the incident: EXIT: withdraw the 2,500,571 that can leave now …` | stay or exit, if the incident happens |
| `if the incident is not certain: … it pays if the incident's probability over 30 days is above 7.92%` | the breakeven: exiting is certain and costly, staying is uncertain |
| `outside view: Nexus f(x) Protocol cover …` | an outside price to compare that probability with |
| `Leaving Belem RWA EURCV costs 110,000 USD for sure, against 53,445 saved if the incident comes: stay.` | the brief's ten-pocket example, made explicit |
| `given the incident, drawn: staying loses 52,067 USD on average (median 11,164, 95 % 246,211, 99 % 352,195); leaving now costs 110,000 …; staying is worse in 18% of 10,000 paths` | "exiting is expensive and certain, staying is cheap and uncertain": the uncertain side as a distribution (`--conditional`) |

**Is the number defensible: a backtest.** `uv run python -m riskdep backtest` replays the PT-reUSD liquidations of 2026-08-25 (a Pendle yield spike moved a min(TWAP, linear) oracle; `GAP.md` K8). It reads the state 60 blocks before them, applies the oracle's observed fall, and compares the prediction with the 33 `Liquidate` events:

| Market | Oracle | Positions (pred. / real) | Debt liquidatable / repaid | Liquidation incentive (pred. / real) | Bad debt |
|---|---|---|---|---|---|
| PT-reUSD/USDC | −2.45 % | 13 / 13, the same borrowers | 35.46M / 35.19M USDC (−0.8 %) | 927,975 / 920,781 | 0 / 0 |
| PT-reUSD/USDT | −2.76 % | 7 / 7, the same borrowers | 1.89M / 0.96M USDT (liquidators repaid about half) | 49,378 / 25,015 | 0 / 0 |

A second episode tests a different mechanism, price-tracking oracles in a market-wide crash: `backtest --episode crash-2025-10-10`, the main wave of the 2025-10-10 crash on the six Morpho markets with the most liquidations (Mog, PEPE, SPX, WBTC, wstETH). No liquidated borrower is missed in any of them; WBTC/USDC's debt and incentive are within 2 %. The model over-predicts by count in a fast crash, and the backtest accounts for each case: 36 of Mog's 52 extra positions were liquidated later that night, a few were defended by their borrowers, and the rest owe little (under 3 % of the debt repaid, much of it dust no liquidator takes). The bad debt predicted at the low over-states the realised one (Mog: 403k against 22.7k), because liquidators reached many positions after the wick.

The impact given the incident is right to within 1 % where positions were liquidated in full. Not tested: the oracle's fall itself, and the squeeze (the Pendle pool's curve at that date is not served by the quote API). Recorded through an archive RPC (`keys.ini`), it replays offline with no key.

The brief's book with its own worked example, the PT-sUSDe loop on Morpho, as one pocket next to nine vaults: `analyze --book examples/brief-mixed-book.json --shock token=sUSDe:0.08 --exit-cost 0.11` ("leaving it costs 110,000 USD … for sure and saves 776,708 if the incident comes": EXIT).

**The brief's PT example, discovered in depth.** `analyze --demo` now also reports what its dependency graph knows beyond the five layers: the meta-oracle's two sources and its 16 h switch, who can change the tokens and through which timelock (sUSDe: a 24 h timelock; Pendle's SY and USDC: none seen), the three sibling markets on sUSDe (at a 10 % fall, 97M PYUSD liquidatable in sUSDe/PYUSD alone), sUSDe's grade and its backing by USDe, and Ethena's and Pendle's concentration. Its incident names the sibling contagion.

**No hack probability in these answers.** The brief starts from a known incident, so every answer above takes the incident as given; p\* replaces a probability by the threshold above which leaving pays. The hack-history priors (DefiLlama's hack record, `priors.py`) feed only `analyze --demo`'s ex-ante Monte Carlo, a secondary view.

The same runs are served over HTTP (`POST /api/incident`, below). A borrower's view of the brief's PT example: `analyze --demo --shock issuer_depeg=0.08`.

How the system is built (components, data sources, data flow, state, testing): `docs/analysis/ARCHITECTURE.md`.

A browser UI over the same three outputs lives in `web/`.

All data comes from keyless public sources: the publicnode Ethereum RPC, the Morpho and Pendle APIs, and DefiLlama.

> **Note — no browser automation.** Do not work on this project through Claude for Chrome, or any other tool that drives a browser on your behalf. Check the UI the ordinary way: `pnpm dev` and look at it.

## Install

```bash
uv sync                             # Python >= 3.10
uv run pytest -q tests              # offline, from the committed recordings
```

Outside an activated virtualenv, prefix the `python3 -m riskdep …` commands below with `uv run`.

`RISKDEP_RPC_URL` (optional) sends the main RPC's requests to another endpoint, for example a local node, a proxy or a paid endpoint with its key. Cached requests, snapshots and replays keep the public URL, so the offline tests are unaffected and the key is never written to a file. See `docs/analysis/PROVIDERS.md`.

**Faster live runs: eRPC (optional).** The free RPC throttles long runs such as `graph`; riskdep then waits and resends, which is slow but loses nothing. A local eRPC proxy spreads the calls over six free endpoints instead (RockawayX graph: 43 s direct, 20 s through eRPC; the example graph: 8 to 12 min direct, 3 min through eRPC). It takes one binary, the committed `erpc.yaml`, and one variable:

```bash
~/.local/bin/erpc erpc.yaml                                  # in its own terminal; setup in docs/setup/erpc.md
export RISKDEP_RPC_URL=http://127.0.0.1:4000/main/evm/1      # unset it to go direct again
```

Tests and replays never need it. Setup, checks and troubleshooting: `docs/setup/erpc.md`.

## watch: Morpho Vault V2 depositor

```bash
python3 -m riskdep watch                                   # Sentora RLUSD Main, its largest depositor, live
python3 -m riskdep watch --vault <V2 address> --user <addr> --level warn
python3 -m riskdep watch --blocks 1000                     # check the last 1000 blocks, then stop
python3 -m riskdep watch --blocks 1000 --record            # same, saving every response under fixtures/replay/<vault>
python3 -m riskdep watch --replay                          # re-run the recorded range offline
python3 -m riskdep watch --vault <V2> --step 1             # one block per batch: a short crisis is seen act by act
python3 -m riskdep watch --vault <V2> --replay --record-as fork-belem   # a recording kept under its own name
```

At start it reads the vault's structure on-chain (vault → adapters → Blue markets: collateral, LLTV, the vault's share, utilisation, caps, the liquidity market). It reports what a plain withdrawal can pay (idle assets plus the liquidity adapter's market, per the Morpho docs) separately from what only `forceDeallocate` can reach, at the adapter's penalty, and prints standing findings such as concentration or an exit that can't be done in full. It also lists every borrower of the vault's markets (Morpho API, positions read on-chain) and prints each market's liquidation curve and unrealised bad debt; positions are re-read when an event touches them and fully refreshed every 300 blocks. It then prints each market's **drain threshold**: how far the collateral trades below its oracle, the depeg d\* past which the market's free liquidity can be borrowed in one block, and how much that is (`docs/watch/drain-threshold.md`). It then prints the depositor's **exit queue**: what it recovers at par and what stays stuck if it exits first, behind the vault's contract holders, behind half of the other depositors, or last, and its loss in each case for the unrealised bad debt now and for every collateral falling 2 to 20 % at once (`docs/watch/exit-queue.md`). A live batch with no event re-reads only what moves without one (oracle prices, `totalAssets`, `realAssets`, idle cash, the depositor's gates); the full state read runs on any event and at least every 25 blocks (D61). Finally it prints the **admin surface** of those markets: each oracle and the feeds it reads, the collateral and loan tokens, Pendle SY and yield tokens, whether each is upgradeable and who controls it, and each oracle's gap to DefiLlama's price. It then polls every 12 s, 2 blocks behind the head, and prints one line per relevant transaction. Each alert is also appended to `out/watch-<vault>.jsonl`, and the cursor in `out/watch-<vault>.cursor` lets a restart resume where it stopped.

| Level | What triggers it |
|---|---|
| critical | an upgrade of a contract a held market depends on (oracle, feed, collateral or loan token, Pendle SY); a pause of a collateral token; one transaction minting ≥ 5 % of a collateral or yield token's supply; unrealised bad debt in a held market from 0.1 % of the vault (borrowers underwater, not yet liquidated; warn from 0.01 %); a pending change with no notice (`Submit` for a risk-increasing function whose timelock is 0); bad debt in a held market (`Liquidate.badDebtAssets`, your share computed), a loss recorded by an adapter but not yet accrued (`totalAssets()` below the stored `_totalAssets`), vault total assets falling (`AccrueInterest`), the adapter writing off shares (`BurnShares`); at least half of your position stuck behind the vault's contract holders in a run while the vault carries unrealised bad debt; a market's collateral at or past its drain threshold (`DrainWindow`); a vault market's oracle falling ≥ 2 % that leaves bad debt, with the vault's and your loss and the verdict (`OracleImpact`) |
| warn | an oracle ≥ 3 % away from DefiLlama's price; a change of proxy admin, owner or Chainlink aggregator of a dependency; a steep liquidation curve: a 5 % oracle fall would make ≥ 25 % of a held market's debt liquidatable (markets holding ≥ 10 % of the vault); risk-increasing functions that can change with no notice (timelock 0, not abdicated), listed at start; a timelocked change submitted (`Submit`, decoded, with its execution date and timelock) or made live (`Accept`), new adapter, cap raised, fee or gate change, shorter timelock, `ForceDeallocate`, new liquidity adapter, a market crossing 25 % of the vault, ≥ 99 % utilisation on a market holding ≥ 10 %, an oracle moving ≥ 5 %, you no longer able to exit in full with a plain withdrawal, a gate blocking your exit, a block range that could not be read; at least half of your position stuck if the vault's contract holders withdrew before you (`ExitQueue`); a market's collateral within 2 points of its drain threshold (`DrainWindow`); one borrower holding ≥ 50 % of a market's debt, or fewer than 5 borrowers, in a market holding ≥ 10 % of the vault (`BorrowerConcentration`); an upgrade, admin or owner change of a dependency scheduled on a timelock above it, with its delay (`Admin.CallScheduled`, D182); a custom feed that cannot report below a floor within 50 % of its answer without an upgrade (`FeedBand`, D183); an exit gate settable with no notice (`ExitGate`, D184); a vault market's oracle falling ≥ 2 % with no loss yet, with what is liquidatable and the verdict (`OracleImpact`); a feed of a watched oracle turning stale (`FeedStale`); for a Zama confidential vault, a day's confidential outflow ≥ 2 %, an instant exit ≥ 1 %, a batch canceled with money in it (`Zama.*`, critical for ≥ 10 % or a pause or upgrade) |
| info | allocation moves, caps lowered, cancelled changes, liquidations without bad debt, your own and large (≥ 1 %) deposits and withdrawals; both exit gates abdicated (`ExitGate`); a `Submit` for an abdicated function; the timelocks found above the markets, and other calls queued on them |

Thresholds live in `riskdep/registry.json` (`watch`), documented in `docs/reference/registry-reference.md`. What to do about each alert: `docs/reference/alert-runbook.md`. Terms: `docs/reference/glossary.md`.

**Cross-checks** (`riskdep/crosscheck.py`), at start and then every 300 blocks for `watch`, and once per `analyze` run:
- the block hash from the main RPC is compared with an independent one (`eth.drpc.org`, then `1rpc.io`); a difference is a *critical* alert;
- the Morpho API is compared with the chain: the vault's total assets for `watch`, the borrower's collateral and debt for `analyze` (0.5 % tolerance); a difference is a *warn*.

A check that can't run prints "not checked" and never stops the run. Why polling rather than a WebSocket: `docs/watch/websocket-vs-polling.md`.

**Limits.** The free RPC serves state only ~64–90 blocks back, so for older ranges the state-based rules start at the oldest servable block; rules that use the event's own data stay exact. Reorgs deeper than 2 blocks are not handled. Underwater borrowers in the held markets (bad debt Blue has not yet written off, the window in which early exits shift a loss onto others) are not followed. A V1 vault held through `MorphoVaultV1Adapter` is watched as one opaque layer. The mempool is not watched.

**Crisis demo on a mainnet fork** (`scripts/fork/README.md`). `scripts/fork/start-fork.sh` starts an anvil fork; with `RISKDEP_RPC_URL=http://127.0.0.1:8545 RISKDEP_FORK=1`, `watch` follows it and skips the cross-checks that a fork cannot pass. `scripts/fork/crisis-belem.sh` then plays the Belem RWA EURCV crisis through the roles that could cause it: the issuer's −10 % markdown, a liquidation, a run, the curator's (abdicated) gate, a feed upgrade queued 48 h on the Midas timelock, and the bad debt. The start-up shows how far the custom feed can fall without new code (`FeedBand`), the timelocks above the markets and whether the exit gates are abdicated (`ExitGate`); an upgrade is alerted when it is scheduled (`Admin.CallScheduled`), not when it lands. Without a fork: `watch --vault 0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec --replay --record-as fork-belem`.

## watch --user: every Morpho position of an address

```bash
python3 -m riskdep watch --user <address>                      # every Blue borrow and Vault V2 deposit, live
python3 -m riskdep watch --user <address> --hf 1.2,1.1,1.05    # your own health-factor alert levels
python3 -m riskdep watch --user <address> --market <id> --market <id>   # borrows given by hand, no Morpho API lookup
python3 -m riskdep watch --user <address> --blocks 300 --record          # check the last 300 blocks, saving them for --replay
```

The Morpho API (`userByAddress`) finds the positions: Blue markets where the address has debt, and Vault V2 deposits with shares. Everything monitored is then read on-chain. Each borrow's health factor is computed as Blue does: collateral × oracle `price()` × LLTV ÷ debt. Its borrow APY comes from the market's rate model (`borrowRateView`). A real Pendle exit quote is shown when the collateral is a PT. The startup table also lists the main lenders of each borrowed market (≥ 5 % of supply); a Vault V2 is found through its adapter. The lenders are refreshed every 300 blocks. Each Vault V2 deposit is watched with the vault rules above, on its own events only.

| Level | What triggers it, for a borrow |
|---|---|
| critical | the admin-surface criticals of the vault table above (upgrade, collateral pause, large mint), for the borrowed markets; HF below the third level (default 1.02); HF ≤ 1, liquidatable; a `Liquidate` naming the address as borrower |
| warn | HF below the second level (default 1.05); a steep liquidation curve in a borrowed market (≥ 25 % of the other borrowers' debt liquidatable at a 5 % fall); one lender funding ≥ 50 % of a borrowed market, at start; a main lender withdrawing ≥ 5 % of a borrowed market's supply; a borrow or collateral withdrawal made on your behalf by another address; a `SetAuthorization` by the address; the borrow APY 50 % above its value at start; utilisation ≥ 99 %; an oracle move ≥ 5 % or an oracle that stops answering |
| info | HF below the first level (default 1.10), and once when it recovers above it; your own borrows, repays and collateral moves; a repay or added collateral by another address, which lowers your risk |

Alerts go to `out/watch-user-<address>.jsonl`, and a restart resumes from `out/watch-user-<address>.cursor`. Each Vault V2 deposit gets the same tables as `watch --vault`, the drain threshold and the exit queue included. Every 300 blocks the tool looks for new positions and refreshes the exit quotes. A Blue `Borrow` on your behalf in a market not yet watched is picked up at once. Not covered: direct Blue supply, Vault V1 deposits, exit quotes for collateral other than a PT, and Morpho's opt-in pre-liquidation contracts. Authorising one of them still raises the `SetAuthorization` alert. The options behind these choices are in `docs/watch/user-watcher-options.md`.

## graph: draw the dependency graph

```bash
python3 -m riskdep graph --example                                   # writes out/graph.html and out/graph.json
python3 -m riskdep graph --user <address> --vault <vault> --out out/graph.html
python3 -m riskdep graph --vault <vault> --no-siblings               # only what the vault and address hold
python3 -m riskdep graph --vault <vault> --record                    # save every response under fixtures/replay/graph-<vault>
python3 -m riskdep graph --vault 0xE0181090c22579B6A217f1522cbf8c9f1F0C1965 --replay   # RockawayX USDC Yield, offline
```

Builds the graph of `docs/analysis/ANALYSIS_MONITORING.md` §1 from live data. Actors are addresses, vaults, and the main lenders of the borrowed markets. Pools are Blue markets and Pendle pools. It also draws assets, oracles with the feeds they read, and vault admins. The output is an interactive HTML page (Cytoscape.js from cdnjs) plus the same data as JSON. `docs/examples/graph-example.html` is a rendered example, built before sibling markets existed.

**Sibling markets** (plan `2026-10-10-sibling-markets`). For every Blue market an address or vault of the graph holds, `graph` also adds the other Blue markets that can move its collateral's price or share its price inputs, drawn dashed:

| Relation | The sibling… | Example on RockawayX USDC Yield |
|---|---|---|
| same collateral | takes the same collateral token | PT-reUSD-10DEC2026/USDT next to PT-reUSD-10DEC2026/USDC |
| same underlying | takes a token with the same underlying: a PT and its Pendle underlying, an ERC-4626 share and its `asset()` | reUSD/USDC, behind PT-reUSD-10DEC2026 |
| shared price input | has an oracle reading, on its collateral side, a feed or vault the held market's oracle reads | PRIME/PYUSD ($189M) reads the PRIME / WYLDS feed under the vault's PRIME/USDC |
| lends a linked asset | lends the held collateral or its underlying: an exploit of its own collateral would borrow it and dump it | — |

Siblings come from the Morpho API (Ethereum markets with at least $1M supplied, their TVL, and at most 10 per held market, the largest borrow first) and are re-read on-chain. They connect to the held market through the asset, oracle or feed node they share, never through a direct edge. USDC and USDT never link markets. The thresholds are in `registry.json` (`graph`).

**Oracle classes.** Every market oracle is labelled `price-tracking` (a fall of the collateral's market price lowers it: liquidations, possibly a cascade) or `constant-price` (it does not: fixed value, exchange rate, NAV, linear discount; a depeg liquidates nobody and lands on the lenders), or `not classified` when no rule decides. Rules, in order, for each collateral-side input: an ERC-4626 rate; a composite or wrapper takes its inputs' class; Pendle's TWAP (`twapDuration()`) or linear-discount (`baseDiscountPerYear()`) getters; the feed's round history (it falls in at least 20 % of its changes: a market price); an answer of exactly 1.0 with no history; description or verified contract name (Etherscan key optional). Each label carries its basis.

**Feed quality and TVL concentration.** Each base feed of an oracle carries how old its last update is against its own rhythm, read from the rounds the classification already reads (`updated 17.5 days ago; 2 rounds, too few to learn its rhythm: STALE, past 7.0 days` for Belem's mGLOeuro NAV feed); a vault incident lists the feeds of each hit market. Each Blue market, PT and issuer token points to its DefiLlama protocol, with its share of DeFi and of its category, flagged when it is a concentration (`Pendle V2: 1,208M USD, 0.20% of DeFi, 25.3% of Yield (#2): CONCENTRATED`). Thresholds in `registry.json` `feeds` and `tvl`.

**Market state.** Every Blue market node, held or sibling, carries its supply, borrow, the collateral of its borrowers and its liquidation curve at −2/−5/−10/−20 % (debt, positions, bad debt, collateral that would be sold); the `takes as collateral` edge carries the collateral amount, and an ERC-4626 asset has a `wraps` edge to the token it redeems into. That is the data the propagation engine of `docs/model/graph-propagation.md` needs.

## shock: what a vault loses when a node fails

```bash
V=0xE0181090c22579B6A217f1522cbf8c9f1F0C1965                                # RockawayX USDC Yield, recorded graph
python3 -m riskdep shock --vault $V --replay --list                          # what can be shocked
python3 -m riskdep shock --vault $V --replay --shock "Ojo PT:reads-low:10%"  # one failure
python3 -m riskdep shock --vault $V --replay --shock "PRIME / WYLDS:frozen" --shock 0x19ebb35279a16207ec4ba82799cc64715065f7f6:price:-30%
python3 -m riskdep shock --vault $V --replay --sweep reads-high:20%         # every oracle and feed in turn, ranked
python3 -m riskdep shock --vault $V --replay --rules my-rules.json --shock …  # your own propagation rules first
```

A shock is `<node>:<mode>[:<size>]`. The node is an address, a market id or a unique fragment of a label. The mode is `reads-low`, `reads-high` or `frozen` for an oracle or feed, or `price` for an asset's market price. Several shocks apply together.

The engine walks the graph from the shocked node to everything that depends on it:
- feed → oracle → every market it prices, held or sibling;
- collateral → the markets taking it, through wrappers and Pendle pools.

In each Blue market it computes, from every borrower's position:
- the liquidations, and the debt Blue writes off;
- the debt left insolvent when nobody liquidates (a stuck or constant-price oracle);
- the drain once the collateral's discount to its oracle passes d\*.

Liquidated collateral is offered for sale, which lowers its price and reaches every market taking it, until nothing moves (the squeeze). The price impact comes from real Pendle quotes recorded with the graph, two ladders per PT:
- **into its pool,** the price a Pendle TWAP oracle reads;
- **for dollars,** the underlying the pool pays out.

Past a market's capacity the rest cannot be sold, and those liquidations do not complete.

Each oracle moves only with what it actually tracks. PT-reUSD's oracle prices the PT against reUSD, so a reUSD depeg liquidates nobody there: it leaves insolvent debt and a drain.

Losses reach the vault by its share of each market, and a depositor (`--user`) by its share of the vault. The output gives the consequences per market and the path each loss took. `out/shock-<vault>.trace.json` holds the same propagation as data, every step tied to an edge of the graph, for a front end to animate: format in `docs/model/shock-trace.md`, a committed example in `docs/model/shock-trace-example.json`.

How a shock crosses each edge is an ordered list of rules in `registry.json` (`engine`), with criteria on the edge, its two nodes and the effect. Change them, or pass a file with `--rules`, to propagate differently without touching the code. Everything, with worked examples and the rule format: `docs/model/shock-engine.md`.

## analyze: Pendle PT on Morpho Blue

```bash
python3 -m riskdep analyze --demo                 # cached real snapshot, no network
python3 -m riskdep analyze --live --morpho-market <uniqueKey> [--user <addr>]
python3 -m riskdep analyze --live --pendle-market <market> --pt-amount <n>
python3 -m riskdep analyze --demo --shock oracle=0.10            # incident mode: a known incident
python3 -m riskdep analyze --demo --shock issuer_depeg=0.08 --shock amm=0.03
```

Writes `out/report.html` and `out/report.json`.

**Incident mode** (`--shock EVENT=SEVERITY`, events `chain`, `issuer_hack`, `issuer_depeg`, `amm`, `oracle`, `lending`, `pt_yield` (a rise of the PT's implied yield, in points: `pt_yield=0.09`), `borrow_rate` (the borrow APY over the horizon: `borrow_rate=0.40`), `pool_move` (a sale of the PT into its Pendle pool, in multiples of the pool's liquidity: `pool_move=0.5`; from real pool quotes, with the sale that would liquidate the position; on the demo, the largest sale the pool routes moves the PT 0.70 %, short of the 5.16 % that liquidates it)). The brief's question starts from a known incident, so `--shock` gives the incident's impact with no probability: the loss, whether the position is liquidated, how long before the oracle passes the shock on (from the oracle's type; a meta-oracle through its live source, and after its switch), and a verdict with the incident certain (REDUCE if a partial sale is cheapest, EXIT if staying loses more than leaving, STAY otherwise). The ex-ante Monte Carlo verdict follows it. Plan: `plan/2026-10-10-incident-mode.plan.md`.

**Incident mode for a vault depositor** (`--vault`):

```bash
python3 -m riskdep analyze --vault 0xd6d4b804014ef27836dbe9f8f6bf6c71251548ec --shock token=mGLOeuro:0.30
python3 -m riskdep analyze --live --vault <vault> --shock token=<collateral address or symbol>:<fall> [--user <depositor>]
```

The incident is a fall of a collateral's oracle price, such as an issuer marking its NAV down. For each market of the vault holding that collateral, the tool values every borrower at the shocked price, then reports:

- the debt liquidatable and the bad debt, per market;
- the vault's loss, and the depositor's loss if it stays and if it leaves first, with what can leave now;
- how fast the incident lands: at once on publication for an issuer NAV oracle;
- how concentrated each hit market is (the largest borrower's and the three largest's share of its debt);
- the collateral's exit liquidity (from the registry's `exit_liquidity`) and, when it is thin or absent, the loss if nobody liquidates;
- a verdict.

**One number with `shock`.** When the vault's dependency graph is recorded (`graph --vault <vault> --record`; the seven RockawayX vaults are), the markdown also runs through the shock engine: the token's price falls and the issuer's rate or NAV feed reads as much lower. The engine's figures are used on the markets it reaches, so `analyze` and `shock` agree (PRIME −30 % on RockawayX USDC Yield: 131,162 USDC from both). They include the squeeze: when the collateral's market cannot absorb the liquidation sales, positions are left insolvent rather than liquidated. The notes list the sibling markets the same incident reaches. A borrower default and a Pharos-reached market keep the incident's own figures.

**When the incident is not certain: p\*.** The verdict above assumes the incident happens. Each vault and book incident also gives its breakeven probability: leaving now gives up the vault's yield (its net APY from the Morpho API) on what can leave, over `--horizon` days (default 30), and saves what leaving first avoids if the incident comes. Leaving pays when the incident's probability over the horizon is above p\* = yield given up ÷ loss saved (also given per year). The book acts first on the vault with the lowest p\*. Next to it, Nexus Mutual's cover price on the protocol (keyless, `fixtures/replay/nexus/`) gives an outside probability, with what that cover pays on:

```
if the incident is not certain: leaving now forgoes 17,042 USDC of yield over 30 days (8.29%/yr); it pays if the incident's probability over 30 days is above 7.92% (63.3%/yr)
outside view: Nexus f(x) Protocol cover 1.82%–8.20%/yr, capacity 2,539,669 USDC: implies 1.2%–13.7%/yr for an exploit of the protocol at this severity; it pays on that, not on an issuer's markdown or a borrower's default
```

**Zama confidential vaults.** For a vault entered through Zama's Confidential Vault protocol (16 on mainnet, `registry.json` `zama`), the cShare that holds every confidential depositor's shares is treated as a pool, not as the vault's depositor nor a holder ahead in a run; the incident states the confidential share and a confidential depositor's two exits (the daily batch, which does not beat a NAV markdown that lands at once; the instant exit, which does and reveals the amount); `graph` draws the batchers and Zama's decryption every exit needs. See `docs/analysis/ZAMA-VAULT.md`.

**Pharos** (keyless, optional): each hit market shows its collateral's grade from Pharos, a token shock also follows Pharos's off-chain backing (fxSAVE backs 16.4 % of infiniFi's iUSD, so an fxSAVE cut reaches siUSD markets, at 16.4 % of the fall), and the notes name the collateral sharing a mint key, upgrade admin or reserve issuer with the shocked token. `graph` draws the same backing and groups. Offline it reads `fixtures/replay/pharos/`; `--record` re-reads it. See `docs/risk-assessment/outside-providers.md`.

**A borrower's default** (`--shock borrower=<collateral symbol or address, market id, or all>:<recovery>[:<n>]`): in each matching market, the n largest borrowers (1 by default) stop repaying and their collateral is recovered at that fraction of its oracle value. It works on any vault or book, and combines with a markdown (`--shock token=mGLOeuro:0.30 --shock borrower=mGLOeuro:0.5`) without counting a position twice:

```bash
python3 -m riskdep analyze --vault 0xd6d4b804014ef27836dbe9f8f6bf6c71251548ec --shock borrower=mGLOeuro:0.5   # 1.05M EURCV, 22 % of the vault
python3 -m riskdep analyze --book examples/rockawayx-ethereum.json --shock borrower=all:0.5                  # every market's largest borrower
```

Offline it reads the vault's recording; the RockawayX vaults, Belem RWA EURCV among them, are recorded. Output: the terminal and `out/vault-incident-<vault>.json`. Plan: `plan/2026-10-11-vault-incident.plan.md`.

**A book of vaults** (`--book`, or several `--vault`): the same incident in every vault of a book you define, added up in USD.

```bash
python3 -m riskdep analyze --book examples/rockawayx-ethereum.json --shock token=PST:0.30
python3 -m riskdep analyze --vault <A> --vault <B> --user <depositor> --shock token=<collateral>:0.30   # ad hoc book
python3 -m riskdep analyze --book my-book.json --record --shock token=<collateral>:0.30                # record new vaults
```

A book file lists vault addresses, each with an optional `label` and `depositor`, and a `weighting`: `vault` (each vault at its total assets, a curator's view), `depositor` (each vault at the depositor's position) or `pocket` (each vault at the `amount` in USD the file gives it, a position first in the exit queue: the brief's book of pockets, `examples/brief-ten-pockets.json`). `--exit-cost 0.11` makes the cost of leaving a share of what leaves (the brief's 11 % unwind) instead of the vault's yield given up. Each line says why it reads STAY or EXIT. `examples/rockawayx-ethereum.json` is the template. A token also reaches the markets whose collateral wraps it (a PT, an ERC-4626 share, chains of them), and the output shows the path; when such a market's oracle does not track a market, nothing is liquidated and the loss is shown as a hidden shortfall. `--record` reads each vault live and saves it under `fixtures/replay/incident-<vault>/`, with all its oracles and wrapping chains, so any later incident runs offline. Output: the headline, one line per vault, and `out/book-incident.json`. Plan: `plan/2026-10-11-vault-book.plan.md`.

- **Data date.** An offline run uses the snapshot's date, `fixtures/snapshot/as_of.json`, as "now", so the demo gives the same result on any later day. `--refresh` refetches everything and rewrites that date; `--live` fetches only what is missing and uses today's date.
- **Oracle.** Whether the lending market's oracle follows the PT market is read from the oracle's structure when it decides (its inputs' class; a meta-oracle through its live source and its switch within the horizon, D96). Otherwise it is inferred by comparing prices; when the PT trades within 1 % of par (near maturity), that test can't tell, so the report says *ambiguous*. The report always shows the verdict under the other oracle behaviour too.

## notify: alerts to Telegram

```bash
python3 -m riskdep notify --test                         # one test message to the channel
python3 -m riskdep notify                                # follow out/watch-*.jsonl, post warn and critical
python3 -m riskdep notify --level critical --from-start  # only criticals, including what the files already hold
python3 -m riskdep notify --post out/book-incident.json  # the headline of an incident run, as a scenario
```

A separate process next to `watch`: it reads the alert files and posts to a private Telegram channel (`keys.ini` `[alerts] telegram_bot_token`, `telegram_chat_id`). It sends **only when there is an alert** at or above the level, never a heartbeat. Standing findings, printed again at every watch start, are posted once per 1800 blocks. The alerts of one block come as one message: the cause in plain words, the loss and the decision (EXIT or STAY) on top, the details folded underneath, and a "What to do" button to the runbook; only criticals ring the phone. Offsets are saved in `out/notify.state.json` after each send, so a restart neither skips nor resends. Setup and design: `TELEGRAM_BOT.md`; thresholds: `registry.json` `notify`.

## web: the browser UI

A React single-page app in `web/`, one page per CLI mode: **Vault** (the vault picked in the top bar: total assets, liquidity, its Blue markets by allocation, and four candidate charts in tabs, every borrower weighted by the vault's share of its market: the liquidations by collateral price drop — debt per 0.5 % bucket and its running total; the vault's bad debt in % of its assets if every collateral fell together; per market, the fall to the first bad debt beside the collateral's worst 1-year drawdown (DefiLlama); and per market, what the vault can withdraw now against what stays lent), **Market** (one of those markets, opened from the vault's table: supply, borrow, utilization, rate, and the same liquidation chart for its borrowers), **Dependency graph** (the `graph` output in React Flow: shape by role, icon and amount inside each node, arrows; filterable by node kind, searchable, and a selection lights the node's whole upstream and downstream flow and opens a risk panel), **Impact** (a `shock` trace in two tabs — summary tables and the whole graph, reached nodes ringed and the rest greyed out; for now always the committed example, `docs/model/shock-trace-example.json`) and **Alerts** (the `watch` stream, newest first, with level counts and a minimum-level filter).

Tailwind CSS v4 with stock shadcn/ui primitives: a light radius on every control, faint table rules. Colour is reserved for severity — `info`, `warn`, `critical`, `ok` — and is carried by a word, never by a number, so an alert reads the same without it. The one other colour on screen is the dependency graph's six node kinds, which are data and are mirrored from `riskdep/graph.py`. Numbers are set in the UI face with tabular figures; only identifiers (addresses, hashes, market ids) are monospace.

```bash
cd web
pnpm install
pnpm dev          # http://localhost:5173
pnpm build        # tsc -b && vite build -> web/dist
pnpm preview      # serve the build
pnpm lint         # eslint + prettier --check
pnpm format       # prettier --write
```

**It runs with no backend.** `VITE_USE_MOCKS` in `web/.env` defaults to true, and the hooks then resolve fixtures copied from real CLI output (`out/report.json`, `out/graph.json`, `out/watch-*.jsonl`) into `web/src/mocks/`. The alert stream is replayed one entry every 1.5 s, then ends. Two `critical` alerts in that fixture are **fabricated** — no recorded run has one, so their wording is modelled on `docs/reference/alert-runbook.md`; everything else is verbatim recorded output.

**The backend.** `riskdep/api/` is a FastAPI app serving the routes below; Vite proxies `/api` to it. With `VITE_USE_MOCKS=false` the hooks hit it for real.

**Incident (`/incident`).** An active-alert demo: PST −30%, occurred 19 minutes ago and detected 16 minutes ago. The event timing and severity are illustrative metadata in `src/mocks/incident.ts`; losses and liquidity come from the recorded RockawayX example through `/api/incident`. One top-bar vault selector stays in sync with fully clickable vault rows; the selected vault's actions, position-loss chart, withdrawal liquidity and propagation summary appear on the right. There is no scenario form or hit-markets table. The backend verdict determines the action; pre-incident breakeven probabilities and Nexus prose are omitted. Policy ownership and incident coverage remain unverified. Regenerate the impact fixtures and vault list with `uv run python scripts/export_incident_fixtures.py`. A real detector must supply occurrence/detection timestamps; a combined Impact view must use a trace for this same incident, rather than the separate Ojo example.

```bash
uv run uvicorn riskdep.api:app --reload      # http://127.0.0.1:8000, docs at /docs
```

It owns no risk logic: `pipeline.analyze` and `pipeline.incident` compute, `report.to_dict` and `graph.to_dict` shape, the API routes. The watcher is **not** hosted — `python -m riskdep watch` stays its own process and appends to `out/watch-*.jsonl`, which `GET /api/alerts` reads with a block cursor. One poll loop per target however many browsers are open, and either side can restart without the other.

`openapi.json` is committed and is the contract: regenerate it with the command below, and CI fails if it has drifted from the code.

```bash
uv run python -c "import json,riskdep.api as a; print(json.dumps(a.app.openapi(), indent=2))" > openapi.json
```

| Endpoint | Serves |
|---|---|
| `GET /api/health` | `{status, mode, data_as_of}` — the mode chip in the header |
| `GET /api/vault/{address}` | a Vault V2 read live from the Morpho API: its markets by allocation, their borrowers' liquidations and concentration; from the vault's recordings when there are, each market's oracle class and feed freshness and the vault's exit liquidity and holders |
| `GET /api/market/{market_id}` | a Blue market read live from the Morpho API: its state and every borrower's liquidating fall |
| `GET /api/report` | the last `analyze` report written to `out/` |
| `POST /api/analyze` | run `analyze` (market, user, horizon, paths, live) and return the report; writes nothing |
| `GET /api/books` | the books of vaults shipped in `examples/` |
| `POST /api/incident` | a known incident (`shocks` as `analyze --shock`, e.g. `token=PST:0.30`) on `vaults`, an inline `book` or an `example` book: the book's loss, headline and breakeven, and each vault's detail, as `analyze --vault` / `--book` computes them; offline from the recordings unless `live`; writes nothing |
| `GET /api/graph?user=&vault=&block=` | the dependency graph; with no user and no vault, the last one written to `out/` |
| `GET /api/targets` | one entry per `out/watch-*.jsonl`: the watch targets with alerts |
| `GET /api/alerts?target=&since=&level=&limit=` | alerts after a block cursor; pass the returned `cursor` back as `since` |

**Limits.** No wallet or transaction. Incident displays a fixed demo event with recorded impact; its timestamps are illustrative, not live detection. The Vault, Graph and Alerts pages follow the vault selector of the top bar, one vault at a time: it lists every vault of the last graph and the watched addresses, starts on the first watch target, and only watched targets have alerts. `POST /api/analyze` is typed and wired in the client but no page offers it. Dark mode follows the system; the `data-theme` override the palette supports has no toggle yet (the graph reads the colour tokens live, so one would need no re-init). Alerts arrive by polling `/api/alerts` every 3 s with a block cursor, not over a socket; a failed poll is surfaced and retried on the next tick. No frontend tests; CI does build `web/` and checks its formatting (`pnpm lint && pnpm build`).

## Layout

```
plan/        the charrette plans (design, decisions, tracker, interview log)
docs/        README.md (the index) · model/ (risk, probabilities, Monte Carlo, incidents, shock engine) · watch/ (detection,
             monitoring) · reference/ (alert runbook, registry reference, glossary) · setup/ · examples/ · img/
             analysis/ (assessments, architecture, providers, next steps) · external/ (third-party docs) · risk-assessment/
riskdep/     sources · abi · vault · poller · rules · market_risk · drain · exit_queue · admin · watch (watch --vault)
             positions · borrower · borrower_rules · watch_user (watch --user) · graph
             discover · priors · propagate · simulate · decide · report (analyze)
             cli · registry.json (facts, assumptions, thresholds)
fixtures/    snapshot/ (analyze demo), replay/<vault>/ and replay/user-<address>/ (recorded watch ranges); tracked in git, the tests read them
tests/
web/         React SPA: src/api (client, hooks, SSE, types) · src/routes (the three pages)
             src/components · src/lib · src/mocks (fixtures from real CLI output)
```
