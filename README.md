# defi-monitoring

Risk tooling for DeFi positions on Ethereum, built with the charrette loop: design and decisions first (`plan/`), then code. Three modes:

- **`analyze`**: batch risk report for a Pendle-PT position on Morpho Blue. It discovers the dependency stack, simulates incidents on each layer and ends with STAY / REDUCE / EXIT. Plan: `plan/2026-10-10-defi-risk-dependency.plan.md`.
- **`watch`**: follows a **Morpho Vault V2** block by block and alerts on every transaction that changes a depositor's exposure, losses or ability to exit. Plan: `plan/2026-10-10-morpho-vault-v2-watcher.plan.md`.
- **`watch --user`**: finds every Morpho Blue borrow and Vault V2 deposit of an address and follows them together: health factor, liquidation, actions on your behalf, borrow rate. Plan: `plan/2026-10-10-morpho-user-watcher.plan.md`.

How the system is built (components, data sources, data flow, state, testing): `ARCHITECTURE.md`.

A browser UI over the same three outputs lives in `web/`.

All data comes from keyless public sources: the publicnode Ethereum RPC, the Morpho and Pendle APIs, and DefiLlama.

## Install

```bash
uv sync                             # Python >= 3.10
uv run pytest -q tests              # 112 tests, offline
```

Outside an activated virtualenv, prefix the `python3 -m riskdep …` commands below with `uv run`.

## watch: Morpho Vault V2 depositor

```bash
python3 -m riskdep watch                                   # Sentora RLUSD Main, its largest depositor, live
python3 -m riskdep watch --vault <V2 address> --user <addr> --level warn
python3 -m riskdep watch --blocks 1000                     # check the last 1000 blocks, then stop
python3 -m riskdep watch --blocks 1000 --record            # same, saving every response under data/replay/<vault>
python3 -m riskdep watch --replay                          # re-run the recorded range offline
```

At start it reads the vault's structure on-chain (vault → adapters → Blue markets: collateral, LLTV, the vault's share, utilisation, caps, the liquidity market). It reports what a plain withdrawal can pay (idle assets plus the liquidity adapter's market, per the Morpho docs) separately from what only `forceDeallocate` can reach, at the adapter's penalty, and prints standing findings such as concentration or an exit that can't be done in full. It also lists every borrower of the vault's markets (Morpho API, positions read on-chain) and prints each market's liquidation curve and unrealised bad debt; positions are re-read when an event touches them and fully refreshed every 300 blocks. Finally it prints the **admin surface** of those markets: each oracle and the feeds it reads, the collateral and loan tokens, Pendle SY and yield tokens, whether each is upgradeable and who controls it, and each oracle's gap to DefiLlama's price. It then polls every 12 s, 2 blocks behind the head, and prints one line per relevant transaction. Each alert is also appended to `out/watch-<vault>.jsonl`, and the cursor in `out/watch-<vault>.cursor` lets a restart resume where it stopped.

| Level | What triggers it |
|---|---|
| critical | an upgrade of a contract a held market depends on (oracle, feed, collateral or loan token, Pendle SY); a pause of a collateral token; one transaction minting ≥ 5 % of a collateral or yield token's supply; unrealised bad debt in a held market from 0.1 % of the vault (borrowers underwater, not yet liquidated; warn from 0.01 %); a pending change with no notice (`Submit` for a risk-increasing function whose timelock is 0); bad debt in a held market (`Liquidate.badDebtAssets`, your share computed), a loss recorded by an adapter but not yet accrued (`totalAssets()` below the stored `_totalAssets`), vault total assets falling (`AccrueInterest`), the adapter writing off shares (`BurnShares`) |
| warn | an oracle ≥ 3 % away from DefiLlama's price; a change of proxy admin, owner or Chainlink aggregator of a dependency; a steep liquidation curve: a 5 % oracle fall would make ≥ 25 % of a held market's debt liquidatable (markets holding ≥ 10 % of the vault); risk-increasing functions that can change with no notice (timelock 0, not abdicated), listed at start; a timelocked change submitted (`Submit`, decoded, with its execution date and timelock) or made live (`Accept`), new adapter, cap raised, fee or gate change, shorter timelock, `ForceDeallocate`, new liquidity adapter, a market crossing 25 % of the vault, ≥ 99 % utilisation on a market holding ≥ 10 %, an oracle moving ≥ 5 %, you no longer able to exit in full with a plain withdrawal, a gate blocking your exit, a block range that could not be read |
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

Alerts go to `out/watch-user-<address>.jsonl`, and a restart resumes from `out/watch-user-<address>.cursor`. Every 300 blocks the tool looks for new positions and refreshes the exit quotes. A Blue `Borrow` on your behalf in a market not yet watched is picked up at once. Not covered: direct Blue supply, Vault V1 deposits, exit quotes for collateral other than a PT, and Morpho's opt-in pre-liquidation contracts. Authorising one of them still raises the `SetAuthorization` alert. The options behind these choices are in `docs/user-watcher-options.md`.

## graph: draw the dependency graph

```bash
python3 -m riskdep graph --example                                   # writes out/graph.html and out/graph.json
python3 -m riskdep graph --user <address> --vault <vault> --out out/graph.html
```

Builds the graph of `ANALYSIS_MONITORING.md` §1 from live data. Actors are addresses, vaults, and the main lenders of the borrowed markets. Pools are Blue markets and Pendle pools. It also draws assets, oracles with the feeds they read, and vault admins. The output is an interactive HTML page (Cytoscape.js from cdnjs) plus the same data as JSON. `docs/graph-example.html` is a rendered example.

## analyze: Pendle PT on Morpho Blue

```bash
python3 -m riskdep analyze --demo                 # cached real snapshot, no network
python3 -m riskdep analyze --live --morpho-market <uniqueKey> [--user <addr>]
python3 -m riskdep analyze --live --pendle-market <market> --pt-amount <n>
```

Writes `out/report.html` and `out/report.json`.

- **Data date.** An offline run uses the snapshot's date, `data/snapshot/as_of.json`, as "now", so the demo gives the same result on any later day. `--refresh` refetches everything and rewrites that date; `--live` fetches only what is missing and uses today's date.
- **Oracle.** Whether the lending market's oracle follows the PT market is inferred by comparing their prices. When the PT trades within 1 % of par (near maturity), the test can't tell, so the report says *ambiguous* and shows the verdict under the other oracle behaviour too.

## web: the browser UI

A React single-page app in `web/`, one page per CLI mode: **Position** (the `analyze` report: verdict, KPIs, where the expected loss comes from, tail measures, exit and oracle sensitivity), **Dependency graph** (the `graph` output in Cytoscape, filterable by node kind, searchable, with a selection panel) and **Alerts** (the `watch` stream, newest first, with level counts and a minimum-level filter).

```bash
cd web
pnpm install
pnpm dev          # http://localhost:5173
pnpm build        # tsc -b && vite build -> web/dist
pnpm preview      # serve the build
pnpm lint         # eslint + prettier --check
pnpm format       # prettier --write
```

**It runs with no backend.** `VITE_USE_MOCKS` in `web/.env` defaults to true, and the hooks then resolve fixtures copied from real CLI output (`out/report.json`, `out/graph.json`, `out/watch-*.jsonl`) into `web/src/mocks/`. The alert stream is replayed one entry every 1.5 s, then ends. Two `critical` alerts in that fixture are **fabricated** — no recorded run has one, so their wording is modelled on `docs/alert-runbook.md`; everything else is verbatim recorded output.

**The backend.** `riskdep/api.py` is a FastAPI app serving the routes below; Vite proxies `/api` to it. With `VITE_USE_MOCKS=false` the hooks hit it for real.

```bash
uv run uvicorn riskdep.api:app --reload      # http://127.0.0.1:8000, docs at /docs
```

It owns no risk logic: `pipeline.analyze` computes, `report.to_dict` and `graph.to_dict` shape, the API routes. The watcher is **not** hosted — `python -m riskdep watch` stays its own process and appends to `out/watch-*.jsonl`, which `GET /api/alerts` reads with a block cursor. One poll loop per target however many browsers are open, and either side can restart without the other.

`openapi.json` is committed and is the contract: regenerate it with the command below, and CI fails if it has drifted from the code.

```bash
uv run python -c "import json,riskdep.api as a; print(json.dumps(a.app.openapi(), indent=2))" > openapi.json
```

| Endpoint | Serves |
|---|---|
| `GET /api/health` | `{status, mode, data_as_of}` — the mode chip in the header |
| `GET /api/report` | the last `analyze` report written to `out/` |
| `POST /api/analyze` | run `analyze` (market, user, horizon, paths, live) and return the report; writes nothing |
| `GET /api/graph?user=&vault=&block=` | the dependency graph; with no user and no vault, the last one written to `out/` |
| `GET /api/targets` | one entry per `out/watch-*.jsonl`: the watch targets with alerts |
| `GET /api/alerts?target=&since=&level=&limit=` | alerts after a block cursor; pass the returned `cursor` back as `since` |

**Limits.** Read-only: no wallet, no transaction, no form to launch a run — the Position and Graph pages read whatever the backend serves for the default position, and the Alerts page passes only `min_level` (the `target` filter and `POST /api/analyze` are typed and wired in the client, but no page offers them). Dark mode follows the system; the `data-theme` override the stylesheet supports has no toggle. Alerts arrive by polling `/api/alerts` every 3 s with a block cursor, not over a socket; a failed poll is surfaced and retried on the next tick. No frontend tests, and CI does not build `web/`.

## Layout

```
plan/        the two charrette plans (design, decisions, tracker, interview log)
docs/        alert-runbook.md · glossary.md · registry-reference.md · how-risk-is-computed.md · how-a-block-is-analysed.md
             websocket-vs-polling.md · user-watcher-options.md · graph-example.html/.json
riskdep/     sources · abi · vault · poller · rules · watch (watch --vault)
             positions · borrower · borrower_rules · watch_user (watch --user) · graph
             discover · priors · propagate · simulate · decide · report (analyze)
             cli · registry.json (facts, assumptions, thresholds)
data/        snapshot/ (analyze demo), replay/<vault>/ and replay/user-<address>/ (recorded watch ranges)
tests/
web/         React SPA: src/api (client, hooks, SSE, types) · src/routes (the three pages)
             src/components · src/lib · src/mocks (fixtures from real CLI output)
```
