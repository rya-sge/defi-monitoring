# defi-monitoring

Risk tooling for DeFi positions on Ethereum, built with the charrette loop: design and decisions first (`plan/`), then code. Five modes:

- **`analyze`**: batch risk report for a Pendle-PT position on Morpho Blue. It discovers the dependency stack, simulates incidents on each layer and ends with STAY / REDUCE / EXIT. Plan: `plan/2026-10-10-defi-risk-dependency.plan.md`.
- **`watch`**: follows a **Morpho Vault V2** block by block and alerts on every transaction that changes a depositor's exposure, losses or ability to exit. Plan: `plan/2026-10-10-morpho-vault-v2-watcher.plan.md`.
- **`watch --user`**: finds every Morpho Blue borrow and Vault V2 deposit of an address and follows them together: health factor, liquidation, actions on your behalf, borrow rate. Plan: `plan/2026-10-10-morpho-user-watcher.plan.md`.
- **`graph`**: draws the dependency graph of a vault or an address, with the sibling markets around it. Plan: `plan/2026-10-10-sibling-markets.plan.md`.
- **`shock`**: applies a failure to a node of that graph (an oracle reading low or high, a frozen feed, a collateral falling) and propagates it to every market, vault and depositor, by rules you can change. Plan: `plan/2026-10-10-propagation-engine.plan.md`.

How the system is built (components, data sources, data flow, state, testing): `ARCHITECTURE.md`.

All data comes from keyless public sources: the publicnode Ethereum RPC, the Morpho and Pendle APIs, and DefiLlama.

## Install

```bash
uv sync                             # Python >= 3.10
uv run pytest -q tests              # 196 tests, offline
```

Outside an activated virtualenv, prefix the `python3 -m riskdep …` commands below with `uv run`.

`RISKDEP_RPC_URL` (optional) sends the main RPC's requests to another endpoint, for example a local node, a proxy or a paid endpoint with its key. Cached requests, snapshots and replays keep the public URL, so the offline tests are unaffected and the key is never written to a file. See `PROVIDERS.md`.

**Faster live runs: eRPC (optional).** The free RPC throttles long runs such as `graph`; riskdep then waits and resends, which is slow but loses nothing. A local eRPC proxy spreads the calls over six free endpoints instead (RockawayX graph: 43 s direct, 20 s through eRPC; the example graph: 8 to 12 min direct, 3 min through eRPC). It takes one binary, the committed `erpc.yaml`, and one variable:

```bash
~/.local/bin/erpc erpc.yaml                                  # in its own terminal; setup in docs/erpc.md
export RISKDEP_RPC_URL=http://127.0.0.1:4000/main/evm/1      # unset it to go direct again
```

Tests and replays never need it. Setup, checks and troubleshooting: `docs/erpc.md`.

## watch: Morpho Vault V2 depositor

```bash
python3 -m riskdep watch                                   # Sentora RLUSD Main, its largest depositor, live
python3 -m riskdep watch --vault <V2 address> --user <addr> --level warn
python3 -m riskdep watch --blocks 1000                     # check the last 1000 blocks, then stop
python3 -m riskdep watch --blocks 1000 --record            # same, saving every response under fixtures/replay/<vault>
python3 -m riskdep watch --replay                          # re-run the recorded range offline
```

At start it reads the vault's structure on-chain (vault → adapters → Blue markets: collateral, LLTV, the vault's share, utilisation, caps, the liquidity market). It reports what a plain withdrawal can pay (idle assets plus the liquidity adapter's market, per the Morpho docs) separately from what only `forceDeallocate` can reach, at the adapter's penalty, and prints standing findings such as concentration or an exit that can't be done in full. It also lists every borrower of the vault's markets (Morpho API, positions read on-chain) and prints each market's liquidation curve and unrealised bad debt; positions are re-read when an event touches them and fully refreshed every 300 blocks. It then prints each market's **drain threshold**: how far the collateral trades below its oracle, the depeg d\* past which the market's free liquidity can be borrowed in one block, and how much that is (`docs/drain-threshold.md`). It then prints the depositor's **exit queue**: what it recovers at par and what stays stuck if it exits first, behind the vault's contract holders, behind half of the other depositors, or last, and its loss in each case for the unrealised bad debt now and for every collateral falling 2 to 20 % at once (`docs/exit-queue.md`). A live batch with no event re-reads only what moves without one (oracle prices, `totalAssets`, `realAssets`, idle cash, the depositor's gates); the full state read runs on any event and at least every 25 blocks (D61). Finally it prints the **admin surface** of those markets: each oracle and the feeds it reads, the collateral and loan tokens, Pendle SY and yield tokens, whether each is upgradeable and who controls it, and each oracle's gap to DefiLlama's price. It then polls every 12 s, 2 blocks behind the head, and prints one line per relevant transaction. Each alert is also appended to `out/watch-<vault>.jsonl`, and the cursor in `out/watch-<vault>.cursor` lets a restart resume where it stopped.

| Level | What triggers it |
|---|---|
| critical | an upgrade of a contract a held market depends on (oracle, feed, collateral or loan token, Pendle SY); a pause of a collateral token; one transaction minting ≥ 5 % of a collateral or yield token's supply; unrealised bad debt in a held market from 0.1 % of the vault (borrowers underwater, not yet liquidated; warn from 0.01 %); a pending change with no notice (`Submit` for a risk-increasing function whose timelock is 0); bad debt in a held market (`Liquidate.badDebtAssets`, your share computed), a loss recorded by an adapter but not yet accrued (`totalAssets()` below the stored `_totalAssets`), vault total assets falling (`AccrueInterest`), the adapter writing off shares (`BurnShares`); at least half of your position stuck behind the vault's contract holders in a run while the vault carries unrealised bad debt; a market's collateral at or past its drain threshold (`DrainWindow`) |
| warn | an oracle ≥ 3 % away from DefiLlama's price; a change of proxy admin, owner or Chainlink aggregator of a dependency; a steep liquidation curve: a 5 % oracle fall would make ≥ 25 % of a held market's debt liquidatable (markets holding ≥ 10 % of the vault); risk-increasing functions that can change with no notice (timelock 0, not abdicated), listed at start; a timelocked change submitted (`Submit`, decoded, with its execution date and timelock) or made live (`Accept`), new adapter, cap raised, fee or gate change, shorter timelock, `ForceDeallocate`, new liquidity adapter, a market crossing 25 % of the vault, ≥ 99 % utilisation on a market holding ≥ 10 %, an oracle moving ≥ 5 %, you no longer able to exit in full with a plain withdrawal, a gate blocking your exit, a block range that could not be read; at least half of your position stuck if the vault's contract holders withdrew before you (`ExitQueue`); a market's collateral within 2 points of its drain threshold (`DrainWindow`) |
| info | allocation moves, caps lowered, cancelled changes, liquidations without bad debt, your own and large (≥ 1 %) deposits and withdrawals |

Thresholds live in `riskdep/registry.json` (`watch`), documented in `docs/registry-reference.md`. What to do about each alert: `docs/alert-runbook.md`. Terms: `docs/glossary.md`.

**Cross-checks** (`riskdep/crosscheck.py`), at start and then every 300 blocks for `watch`, and once per `analyze` run:
- the block hash from the main RPC is compared with an independent one (`eth.drpc.org`, then `1rpc.io`); a difference is a *critical* alert;
- the Morpho API is compared with the chain: the vault's total assets for `watch`, the borrower's collateral and debt for `analyze` (0.5 % tolerance); a difference is a *warn*.

A check that can't run prints "not checked" and never stops the run. Why polling rather than a WebSocket: `docs/websocket-vs-polling.md`.

**Limits.** The free RPC serves state only ~64–90 blocks back, so for older ranges the state-based rules start at the oldest servable block; rules that use the event's own data stay exact. Reorgs deeper than 2 blocks are not handled. Underwater borrowers in the held markets (bad debt Blue has not yet written off, the window in which early exits shift a loss onto others) are not followed. A V1 vault held through `MorphoVaultV1Adapter` is watched as one opaque layer. The mempool is not watched.

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

Alerts go to `out/watch-user-<address>.jsonl`, and a restart resumes from `out/watch-user-<address>.cursor`. Each Vault V2 deposit gets the same tables as `watch --vault`, the drain threshold and the exit queue included. Every 300 blocks the tool looks for new positions and refreshes the exit quotes. A Blue `Borrow` on your behalf in a market not yet watched is picked up at once. Not covered: direct Blue supply, Vault V1 deposits, exit quotes for collateral other than a PT, and Morpho's opt-in pre-liquidation contracts. Authorising one of them still raises the `SetAuthorization` alert. The options behind these choices are in `docs/user-watcher-options.md`.

## graph: draw the dependency graph

```bash
python3 -m riskdep graph --example                                   # writes out/graph.html and out/graph.json
python3 -m riskdep graph --user <address> --vault <vault> --out out/graph.html
python3 -m riskdep graph --vault <vault> --no-siblings               # only what the vault and address hold
python3 -m riskdep graph --vault <vault> --record                    # save every response under fixtures/replay/graph-<vault>
python3 -m riskdep graph --vault 0xE0181090c22579B6A217f1522cbf8c9f1F0C1965 --replay   # RockawayX USDC Yield, offline
```

Builds the graph of `ANALYSIS_MONITORING.md` §1 from live data. Actors are addresses, vaults, and the main lenders of the borrowed markets. Pools are Blue markets and Pendle pools. It also draws assets, oracles with the feeds they read, and vault admins. The output is an interactive HTML page (Cytoscape.js from cdnjs) plus the same data as JSON. `docs/graph-example.html` is a rendered example, built before sibling markets existed.

**Sibling markets** (plan `2026-10-10-sibling-markets`). For every Blue market an address or vault of the graph holds, `graph` also adds the other Blue markets that can move its collateral's price or share its price inputs, drawn dashed:

| Relation | The sibling… | Example on RockawayX USDC Yield |
|---|---|---|
| same collateral | takes the same collateral token | PT-reUSD-10DEC2026/USDT next to PT-reUSD-10DEC2026/USDC |
| same underlying | takes a token with the same underlying: a PT and its Pendle underlying, an ERC-4626 share and its `asset()` | reUSD/USDC, behind PT-reUSD-10DEC2026 |
| shared price input | has an oracle reading, on its collateral side, a feed or vault the held market's oracle reads | PRIME/PYUSD ($189M) reads the PRIME / WYLDS feed under the vault's PRIME/USDC |
| lends a linked asset | lends the held collateral or its underlying: an exploit of its own collateral would borrow it and dump it | — |

Siblings come from the Morpho API (Ethereum markets with at least $1M supplied, their TVL, and at most 10 per held market, the largest borrow first) and are re-read on-chain. They connect to the held market through the asset, oracle or feed node they share, never through a direct edge. USDC and USDT never link markets. The thresholds are in `registry.json` (`graph`).

**Oracle classes.** Every market oracle is labelled `price-tracking` (a fall of the collateral's market price lowers it: liquidations, possibly a cascade) or `constant-price` (it does not: fixed value, exchange rate, NAV, linear discount; a depeg liquidates nobody and lands on the lenders), or `not classified` when no rule decides. Rules, in order, for each collateral-side input: an ERC-4626 rate; a composite or wrapper takes its inputs' class; Pendle's TWAP (`twapDuration()`) or linear-discount (`baseDiscountPerYear()`) getters; the feed's round history (it falls in at least 20 % of its changes: a market price); an answer of exactly 1.0 with no history; description or verified contract name (Etherscan key optional). Each label carries its basis.

**Market state.** Every Blue market node, held or sibling, carries its supply, borrow, the collateral of its borrowers and its liquidation curve at −2/−5/−10/−20 % (debt, positions, bad debt, collateral that would be sold); the `takes as collateral` edge carries the collateral amount, and an ERC-4626 asset has a `wraps` edge to the token it redeems into. That is the data the propagation engine of `docs/graph-propagation.md` needs.

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

Losses reach the vault by its share of each market, and a depositor (`--user`) by its share of the vault. The output gives the consequences per market and the path each loss took.

How a shock crosses each edge is an ordered list of rules in `registry.json` (`engine`), with criteria on the edge, its two nodes and the effect. Change them, or pass a file with `--rules`, to propagate differently without touching the code. Everything, with worked examples and the rule format: `docs/shock-engine.md`.

## analyze: Pendle PT on Morpho Blue

```bash
python3 -m riskdep analyze --demo                 # cached real snapshot, no network
python3 -m riskdep analyze --live --morpho-market <uniqueKey> [--user <addr>]
python3 -m riskdep analyze --live --pendle-market <market> --pt-amount <n>
```

Writes `out/report.html` and `out/report.json`.

- **Data date.** An offline run uses the snapshot's date, `fixtures/snapshot/as_of.json`, as "now", so the demo gives the same result on any later day. `--refresh` refetches everything and rewrites that date; `--live` fetches only what is missing and uses today's date.
- **Oracle.** Whether the lending market's oracle follows the PT market is inferred by comparing their prices. When the PT trades within 1 % of par (near maturity), the test can't tell, so the report says *ambiguous* and shows the verdict under the other oracle behaviour too.

## Layout

```
plan/        the charrette plans (design, decisions, tracker, interview log)
docs/        alert-runbook.md · glossary.md · registry-reference.md · how-risk-is-computed.md · how-a-block-is-analysed.md
             websocket-vs-polling.md · user-watcher-options.md · exit-queue.md · drain-threshold.md · graph-example.html/.json
riskdep/     sources · abi · vault · poller · rules · market_risk · drain · exit_queue · admin · watch (watch --vault)
             positions · borrower · borrower_rules · watch_user (watch --user) · graph
             discover · priors · propagate · simulate · decide · report (analyze)
             cli · registry.json (facts, assumptions, thresholds)
fixtures/    snapshot/ (analyze demo), replay/<vault>/ and replay/user-<address>/ (recorded watch ranges); tracked in git, the tests read them
tests/
```
