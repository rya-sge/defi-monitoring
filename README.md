# defi-monitoring

Risk tooling for DeFi positions on Ethereum, built with the charrette loop: design and decisions first (`plan/`), then code. Three modes:

- **`analyze`**: batch risk report for a Pendle-PT position on Morpho Blue. It discovers the dependency stack, simulates incidents on each layer and ends with STAY / REDUCE / EXIT. Plan: `plan/2026-10-10-defi-risk-dependency.plan.md`.
- **`watch`**: follows a **Morpho Vault V2** block by block and alerts on every transaction that changes a depositor's exposure, losses or ability to exit. Plan: `plan/2026-10-10-morpho-vault-v2-watcher.plan.md`.
- **`watch --user`**: finds every Morpho Blue borrow and Vault V2 deposit of an address and follows them together: health factor, liquidation, actions on your behalf, borrow rate. Plan: `plan/2026-10-10-morpho-user-watcher.plan.md`.

All data comes from keyless public sources: the publicnode Ethereum RPC, the Morpho and Pendle APIs, and DefiLlama.

## Install

```bash
pip install -r requirements.txt     # Python >= 3.10
python3 -m pytest -q tests          # 70 tests, offline
```

## watch: Morpho Vault V2 depositor

```bash
python3 -m riskdep watch                                   # Sentora RLUSD Main, its largest depositor, live
python3 -m riskdep watch --vault <V2 address> --user <addr> --level warn
python3 -m riskdep watch --blocks 1000                     # check the last 1000 blocks, then stop
python3 -m riskdep watch --blocks 1000 --record            # same, saving every response under data/replay/<vault>
python3 -m riskdep watch --replay                          # re-run the recorded range offline
```

At start it reads the vault's structure on-chain (vault → adapters → Blue markets: collateral, LLTV, the vault's share, utilisation, caps, the liquidity market). It reports what a plain withdrawal can pay (idle assets plus the liquidity adapter's market, per the Morpho docs) separately from what only `forceDeallocate` can reach, at the adapter's penalty, and prints standing findings such as concentration or an exit that can't be done in full. It then polls every 12 s, 2 blocks behind the head, and prints one line per relevant transaction. Each alert is also appended to `out/watch-<vault>.jsonl`, and the cursor in `out/watch-<vault>.cursor` lets a restart resume where it stopped.

| Level | What triggers it |
|---|---|
| critical | bad debt in a held market (`Liquidate.badDebtAssets`, your share computed), a loss recorded by an adapter but not yet accrued (`totalAssets()` below the stored `_totalAssets`), vault total assets falling (`AccrueInterest`), the adapter writing off shares (`BurnShares`) |
| warn | a timelocked change submitted (`Submit`, decoded, with its execution date) or made live (`Accept`), new adapter, cap raised, fee or gate change, shorter timelock, `ForceDeallocate`, new liquidity adapter, a market crossing 25 % of the vault, ≥ 99 % utilisation on a market holding ≥ 10 %, an oracle moving ≥ 5 %, you no longer able to exit in full with a plain withdrawal, a gate blocking your exit, a block range that could not be read |
| info | allocation moves, caps lowered, cancelled changes, liquidations without bad debt, your own and large (≥ 1 %) deposits and withdrawals |

Thresholds live in `riskdep/registry.json` (`watch`).

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

The Morpho API (`userByAddress`) finds the positions: Blue markets where the address has debt, and Vault V2 deposits with shares. Everything monitored is then read on-chain. Each borrow's health factor is computed as Blue does: collateral × oracle `price()` × LLTV ÷ debt. Its borrow APY comes from the market's rate model (`borrowRateView`). A real Pendle exit quote is shown when the collateral is a PT. Each Vault V2 deposit is watched with the vault rules above, on its own events only.

| Level | What triggers it, for a borrow |
|---|---|
| critical | HF below the third level (default 1.02); HF ≤ 1, liquidatable; a `Liquidate` naming the address as borrower |
| warn | HF below the second level (default 1.05); a borrow, repay or collateral withdrawal made on your behalf by another address; a `SetAuthorization` by the address; the borrow APY 50 % above its value at start; utilisation ≥ 99 %; an oracle move ≥ 5 % or an oracle that stops answering |
| info | HF below the first level (default 1.10), and once when it recovers above it; your own borrows, repays and collateral moves |

Alerts go to `out/watch-user-<address>.jsonl`, and a restart resumes from `out/watch-user-<address>.cursor`. Every 300 blocks the tool looks for new positions and refreshes the exit quotes. A Blue `Borrow` on your behalf in a market not yet watched is picked up at once. Not covered: direct Blue supply, Vault V1 deposits, exit quotes for collateral other than a PT, and Morpho's opt-in pre-liquidation contracts. Authorising one of them still raises the `SetAuthorization` alert. The options behind these choices are in `docs/user-watcher-options.md`.

## analyze: Pendle PT on Morpho Blue

```bash
python3 -m riskdep analyze --demo                 # cached real snapshot, no network
python3 -m riskdep analyze --live --morpho-market <uniqueKey> [--user <addr>]
python3 -m riskdep analyze --live --pendle-market <market> --pt-amount <n>
```

Writes `out/report.html` and `out/report.json`.

- **Data date.** An offline run uses the snapshot's date, `data/snapshot/as_of.json`, as "now", so the demo gives the same result on any later day. `--refresh` refetches everything and rewrites that date; `--live` fetches only what is missing and uses today's date.
- **Oracle.** Whether the lending market's oracle follows the PT market is inferred by comparing their prices. When the PT trades within 1 % of par (near maturity), the test can't tell, so the report says *ambiguous* and shows the verdict under the other oracle behaviour too.

## Layout

```
plan/        the two charrette plans (design, decisions, tracker, interview log)
docs/        how-risk-is-computed.md · how-a-block-is-analysed.md · websocket-vs-polling.md · user-watcher-options.md
riskdep/     sources · abi · vault · poller · rules · watch (watch --vault)
             positions · borrower · borrower_rules · watch_user (watch --user)
             discover · priors · propagate · simulate · decide · report (analyze)
             cli · registry.json (facts, assumptions, thresholds)
data/        snapshot/ (analyze demo), replay/<vault>/ and replay/user-<address>/ (recorded watch ranges)
tests/
```
