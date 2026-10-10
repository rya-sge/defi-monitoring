# Fork demo: a crisis played on a mainnet fork, for a video

**Yes, this works.** Anvil (Foundry 1.5.0, already installed in `~/.foundry/bin`) can fork Ethereum mainnet at a fixed block. It can run a crisis there with real contracts and real positions, by impersonating the accounts that can cause it. `riskdep watch` then follows the fork in real time through `RISKDEP_RPC_URL`.

The video shows the four judging criteria at once (`docs/hackaton_instruction/GOAL.md`):

| Criterion | What the demo shows |
|---|---|
| Dependency discovery (30 %) | the graph of the Belem vault, down to the single administered feed |
| Impact (30 %) | `analyze --vault` predicts the loss; the fork then shows it happening on the same numbers |
| Decision (25 %) | the verdict, and how long the depositor has to act |
| Demo on real data (15 %) | real mainnet state; nothing is mocked except the crisis itself |

Facts below were read on-chain on 2026-10-11 (see `ROCK-VAULT-DEP.md`). Re-read them at the fork block before recording.

## 1. The scenario: Belem RWA EURCV

Why this vault:
- it is the sponsor's own vault, $5.3M;
- 86 % of it sits in one market (mGLOeuro / EURCV, 77 % LLTV);
- that market has **one borrower** (`0xa122…E7c6`);
- its oracle is a Midas feed that **one EOA** can move.

### The facts that make the crisis

| Fact | Value | Source |
|---|---|---|
| Feed | `0x8b7b…9609`, `MGloEuroCustomAggregatorFeed` (8 decimals), read directly by the Morpho oracle `0x2b43…47b9` | getters |
| Who can write it | `feedAdminRole()` = `0x8cfa…f4da`, held by **EOA `0xa301…600c`** only | `RoleGranted` logs, `hasRole` |
| `setRoundData(int256)` | admin-only; no delay; only requires `minAnswer ≤ x ≤ maxAnswer` | source of impl `0xbfd2…795a` |
| `setRoundDataSafe` | adds a ≤ 1 % deviation and ≥ 1 h spacing check, but it is optional | same |
| Band | `minAnswer` 90,000 EUR, `maxAnswer` 110,000 EUR; **no setter**: changing it needs a proxy upgrade | same |
| Upgrade path | ProxyAdmin `0xbf25…` → `MidasTimelockController` `0xe3ee…1852`, **48 h** | `getMinDelay()` |
| Position | 52.58 mGLOeuro (5.258M EUR at 100,000) against 3.679M EURCV debt, **LTV 70.0 %** | graph replay |
| Liquidatable below | 100,000 × 0.700 / 0.77 = **90,857 EUR (−9.1 %)** | computed |
| Bad debt below | debt × LIF / collateral, with LIF = 1 / (0.3 × 0.77 + 0.7) = 1.074 → **75,142 EUR (−24.9 %)** | computed |
| Vault exit settings | `setReceiveAssetsGate` and `setSendSharesGate` with a **0 s** timelock; curator `0xbBac…f918` (Safe 4/8) | Morpho API |

### What these facts mean

1. **One EOA can make the sponsor's only borrower liquidatable with one transaction, and no delay.** A NAV of 90,000 (−10 %) is inside the band and below the 90,857 threshold.
2. **The oracle cannot show a loss beyond 10 % for at least 48 hours.** If the fund really loses 30 %, the price sits at 90,000 while the true collateral covers less than the debt. Lenders carry bad debt the market cannot see until the upgrade lands.
3. **The curator can stop every withdrawal at once** (0 s gate timelock).

## 2. The crisis, act by act

Each act is a shell step with `cast`, on screen on the left. On the right, `riskdep` reacts on its own. "Expected" names what `riskdep` should print. Rows marked † need the code changes in §4.

| Act | On-chain action (fork) | riskdep on the right | Expected |
|---|---|---|---|
| 0. Baseline | fork at block B; `graph --vault 0xD6d4…48Ec` | graph in the browser; `watch` starts | startup: "86 % of the vault is in mGLOeuro/EURCV"; oracle class *constant-price* (administered); exit gates timelock 0 † |
| 1. Prediction | none | `analyze --vault 0xD6d4…48Ec --shock token=mGLOeuro:0.10`, then `:0.30` | at −10 %: liquidatable, no bad debt; at −30 %: bad debt ≈ 3.679M − 52.58 × 70,000 / 1.074 ≈ **€0.25M**, and the verdict |
| 2. Issuer markdown −10 % | impersonate `0xa301…600c`; `setRoundData(9000000000000)` | next poll | oracle-move alert (`oracle_move_warn`); market risk: the single borrower is liquidatable, the liquidation curve updates |
| 3. Liquidation (optional) | impersonate a EURCV holder; `Morpho.liquidate(...)` on `0xa122…` | Liquidate event | liquidation alert; utilisation and vault share price |
| 4. Depositors run | impersonate the vault's largest holders; `redeem` | Withdraw events | utilisation → 100 %; exit-queue position and recovery for the watched depositor |
| 5. Curator freezes exits | deploy `DenyAllGate`; impersonate the curator Safe; `submit(setReceiveAssetsGate(gate))`, then execute it in the same block | SetReceiveAssetsGate event | **critical**: "withdrawals now gated; timelock was 0" |
| 6. Deeper loss needs the timelock | impersonate a timelock proposer; `schedule(upgrade feed impl)`; `anvil_increaseTime 48h`; `execute`; `setRoundData(70000…)` | CallScheduled † then Upgraded, then the oracle move | warn at schedule time: "feed upgrade in 48 h" †; then bad debt realised on liquidation; the loss per depositor |
| 7. Recap | none | the report | predicted (act 1) against observed (acts 2–6), side by side |

Act 6 is the strongest point for the jury. The depositor gets 48 hours of warning **only if** the timelock queue is watched. Today `admin.py` sees `Upgraded`, which arrives when it is already too late.

### Alternative crises (same tooling, one act each)

| Crisis | Lever | Exposure | Shows |
|---|---|---|---|
| RedStone feed rewrite | 2-of-3 Safe `0x6906…4472` upgrades the strUSD fundamental feed (ProxyAdmin `0x8223…`), no timelock | ~$20M (Tori, USDC Yield) | an oracle-provider admin as a dependency |
| Unbacked PST mint | impersonate a CCIP `BurnMintTokenPool` (`0xbe77…`); `mint` | $34.7M PST markets | a bridge exploit the exchange-rate oracle does not see: the price stays at 1.138 while supply grows |
| PT-fxSAVE expiry | `anvil_increaseTime` past 2026-10-29 | $1M | the collateral becomes the underlying at maturity; linear oracle goes to 1 |
| Pendle pool dump | swap a large PT-reUSD amount into pool `0x1328…77c0`, then warp 15 min | $53.7M debt on a $12.4M pool | the Ojo `min(TWAP, linear)` feed follows the TWAP down |

## 3. Setting up the fork

```bash
# a fixed block, so takes are reproducible; needs an archive RPC (keys.ini [rpc], never committed)
FORK_BLOCK=<block of the recording day>
anvil --fork-url "$RISKDEP_RPC_URL_UPSTREAM" --fork-block-number $FORK_BLOCK \
      --chain-id 1 --block-time 12 --port 8545 --auto-impersonate
export RISKDEP_RPC_URL=http://127.0.0.1:8545
export RISKDEP_FORK=1          # see §4
```

- **RPC:**
  - The free publicnode serves state only about 64–90 blocks back, so `--fork-block-number` needs a paid archive endpoint (the `[rpc]` section of `keys.ini`).
  - Without one, fork at `latest` and record right away.
  - Anvil caches the fork's state in `~/.foundry/cache/rpc/`, so later takes run offline from that cache.
- **Block time 12 s:** matches `watch.poll_seconds` (12) and lets the viewer see one act per poll. `--auto-impersonate` lets `cast send --unlocked --from <any address>` sign as anyone.
- **Impersonating contracts** (the curator Safe, the CCIP pool): anvil skips the EIP-3607 "sender has code" check for impersonated senders. If a version refuses, replace the Safe's code with a plain EOA via `anvil_setCode <safe> 0x`, which is the fallback.
- **Tokens for actors:** use `anvil_setBalance` for ETH, and `cast index` plus `anvil_setStorageAt` for ERC-20 balances. EURCV (`SmartCoin`) and mGLOeuro (Midas) may restrict transfers to whitelisted addresses. Check before act 3; if it fails, impersonate an existing holder, or skip act 3 (market risk already shows the liquidatable state).

## 4. What riskdep needs to run on a fork

| Issue on a fork | Effect today | Change |
|---|---|---|
| Block-hash cross-check against dRPC and 1rpc (`crosscheck.second_rpc`) | every fork block mismatches → a **critical** alert in each cross-check | `RISKDEP_FORK=1` → the check reads "not checked (fork)" |
| Morpho API against chain (`crosscheck.vault_total_assets`, the API calls in `positions.py`, `exit_queue.py`, `graph.py`) | the API still describes mainnet; after act 2 it diverges and warns | on a fork, skip the API-vs-chain warning; take positions from the API at the fork block (still true then) and from events after it |
| Clock (`clock.now()` = wall time) | after `anvil_increaseTime` the chain is ahead; timelock countdowns are wrong | on a fork, `now` = timestamp of the latest block |
| Recording (`--record`) | caches under `fixtures/replay/<vault>/`, overwriting the real recording of the same vault | `--record-as fork-belem` → `fixtures/replay/fork-belem/`; `--replay` of it for an offline re-run and a test |
| Timelock queue not watched | the 48 h warning of act 6 is invisible | add `CallScheduled` / `Cancelled` / `CallExecuted` (OpenZeppelin `TimelockController`) on the admin contracts found by `admin.py`; alert "upgrade of <feed> executable at <time>" |
| Exit gates with a 0 s timelock | an event alert only | a startup finding: "withdrawals can be gated with no delay by <curator>" |
| Administered feed band | not read | read `minAnswer` / `maxAnswer` of custom aggregators; report "the oracle cannot fall below X without an upgrade (48 h)" |

The first four changes are what make the demo run. The last three are findings from `ROCK-VAULT-DEP.md` that the demo puts on screen, and the product needs them anyway. Each gets its row in `docs/alert-runbook.md` and its threshold in `registry.json`, as the conventions require.

## 5. Files to add

```
scripts/fork/
  README.md                how to run the demo, in five commands
  foundry.toml             a small Foundry project for the two contracts (src = ".", solc pinned)
  addresses.env            every address and constant the scripts use, sourced by all of them (no secrets)
  start-fork.sh            starts anvil at FORK_BLOCK and checks it; prints the env to export
  crisis-belem.sh          acts 0–7 of §2 as cast commands, with captions, pauses and checks
  DenyAllGate.sol          the exit gate the curator sets in act 5
  MGloEuroFeedV2.sol       the feed implementation installed in act 6, with a wider band
  alt-redstone.sh, alt-pst-mint.sh, alt-fxsave-expiry.sh, alt-pendle-dump.sh   the alternative crises of §2
  tapes/act-*.tape         vhs scripts, one per act, for the video
plan/2026-10-1x-fork-demo.plan.md   decisions D… for the changes of §4
fixtures/replay/fork-belem/         the recorded fork run (committed, like the other replays)
tests/test_fork_replay.py           re-runs that recording offline and checks the alert sequence
```

### `scripts/fork/addresses.env`

One file for every address, so a fact re-read at a new fork block (step 1 of §8) changes in one place:
- the vault and its market id;
- the market parameters (EURCV, mGLOeuro, oracle `0x2b43…`, IRM `0x870a…`, LLTV 0.77);
- the feed and its admin EOA;
- the ProxyAdmin, the Midas timelock and its proposer and executor;
- the curator Safe, the largest depositors, the borrower;
- the computed thresholds (90,857 and 75,142).

It holds public data only. The RPC key never goes here: `start-fork.sh` reads it from `keys.ini`.

### `scripts/fork/start-fork.sh`

- Reads the upstream archive RPC from `keys.ini` (`[rpc]`, git-ignored) without printing it. Takes `FORK_BLOCK` as an argument, or forks at `latest` and prints the block chosen.
- Starts `anvil --fork-url … --fork-block-number … --chain-id 1 --block-time 12 --auto-impersonate`, and waits until `cast block-number` answers.
- Checks that it forked the right chain: `cast chain-id` = 1, the vault's `totalAssets` is non-zero, and the feed answers 100,000 EUR.
- Prints the two lines to export: `RISKDEP_RPC_URL=http://127.0.0.1:8545` and `RISKDEP_FORK=1`.
- Retakes: with `--dump-state out/fork-B.json` the first run saves the forked state, and `--load-state` restarts from it in seconds, with no upstream call. `out/` is git-ignored.

### `scripts/fork/crisis-belem.sh`

The demo itself, run in the left pane.

- **Structure:** `set -euo pipefail`; `source addresses.env`. Three helpers:
  - `caption "Act 2: the issuer marks the NAV down 10 %"` prints a large one-line title;
  - `pause` waits for Enter when run by hand, or sleeps N seconds under vhs;
  - `send_as <address> <to> <sig> <args…>` wraps `cast send --unlocked --from`.
- **Retakes:** `--act N` runs one act alone. Before each act the script takes an `evm_snapshot` and keeps its id, so `--retake N` reverts with `evm_revert` and plays the act again without restarting anvil.
- **Each act ends with a check** (`cast call`) that fails loudly when the chain did not move as planned. A take then never shows `riskdep` reacting to nothing.
- **The acts:**

| Act | Commands | Check |
|---|---|---|
| 0 | `riskdep graph --vault $VAULT`, opened in the browser; `riskdep watch --vault $VAULT` is started in the right pane by hand | the feed answers 100,000 |
| 1 | `riskdep analyze --vault $VAULT --shock token=mGLOeuro:0.10`, then `:0.30` | none (off-chain) |
| 2 | `send_as $MIDAS_FEED_ADMIN $FEED "setRoundData(int256)" 9000000000000` | `latestRoundData` answers 90,000; the borrower's LTV is above 77 % |
| 3 | give EURCV to a liquidator: impersonate a holder, or set its balance slot with `cast index` and `anvil_setStorageAt`. Then `approve` Morpho, and `liquidate((EURCV,mGLOeuro,oracle,irm,lltv), $BORROWER, seized, 0, 0x)` | the borrower's collateral fell. Skipped with a message if a token whitelist reverts |
| 4 | for each large depositor: `send_as $HOLDER $VAULT "redeem(uint256,address,address)" <shares> $HOLDER $HOLDER`, as far as liquidity allows | the market's utilisation is 100 % |
| 5 | `forge create DenyAllGate`. As the curator: `submit(bytes)` with `cast calldata "setReceiveAssetsGate(address)" $GATE`. Then anyone calls `setReceiveAssetsGate($GATE)` in the same block: the 0 s timelock has already passed | `receiveAssetsGate()` = `$GATE`; a test `redeem` reverts |
| 6 | `forge create MGloEuroFeedV2`. As the timelock proposer: `schedule(ProxyAdmin, 0, upgradeAndCall(feed, impl, 0x), 0, salt, 172800)`. Then `evm_increaseTime 172800` and `evm_mine`. As the executor: `execute(…)`. As the feed admin: `setRoundData(7000000000000)` | the feed's implementation slot = the new impl; `latestRoundData` answers 70,000 |
| 7 | `riskdep analyze --vault $VAULT --shock token=mGLOeuro:0.30` again, plus the watch's report | none |

### `scripts/fork/DenyAllGate.sol`

About 15 lines. It implements `IReceiveAssetsGate.canReceiveAssets(address)` and `ISendSharesGate.canSendShares(address)` from `vault-v2`, both returning `false`. It is the simplest gate a curator could legitimately set. That is the point of act 5: the risk is in the vault's settings, not in a bug. It compiles against the `docs/external/morpho/lib/vault-v2` interfaces through a `foundry.toml` remapping.

### `scripts/fork/MGloEuroFeedV2.sol`

The implementation act 6 installs through the timelock. A real Midas response to a 30 % fund loss would need the same: the deployed implementation has no setter for `minAnswer`, so only an upgrade can move the band.

- **It must keep the storage layout** of `MGloEuroCustomAggregatorFeed` (implementation `0xbfd2…795a`). Two ways:
  - the simple one: copy the verified source (`cast source` or Etherscan; check the licence first) and add one admin-only `setBand(min, max)` function after the existing ones;
  - the shortcut: change only the `minAnswer` check.
- **Check the layout** with `forge inspect … storageLayout` against the original before the take.
- **Fallback** for a quick take: `anvil_setStorageAt` on the `minAnswer` slot skips the upgrade. It also skips the 48 h timelock, which is the point of the act, so it is for rehearsal only.

### `scripts/fork/alt-*.sh`

One file per alternative crisis of §2, each with the same helpers, its own check, and the `riskdep` command to run beside it:

| Script | Action | Check |
|---|---|---|
| `alt-redstone.sh` | impersonate the 2-of-3 Safe `0x6906…`; upgrade the strUSD fundamental feed (ProxyAdmin `0x8223…`) to an implementation answering 0.70 | the strUSD market's oracle price −32 % |
| `alt-pst-mint.sh` | impersonate the CCIP pool `0xbe77…`; `mint(attacker, 10M PST)` on the `BurnMintERC20` | PST supply +10M while the oracle still answers 1.138: the oracle does not see a bridge exploit |
| `alt-fxsave-expiry.sh` | `evm_increaseTime` past 2026-10-29 | the PT-fxSAVE linear oracle answers 1.0; the PT is redeemable |
| `alt-pendle-dump.sh` | sell a large PT-reUSD amount through the Pendle router into pool `0x1328…`, then warp 15 min (the 900 s TWAP) | the Ojo feed follows the TWAP side down |

### `scripts/fork/tapes/act-*.tape`

[vhs](https://github.com/charmbracelet/vhs) scripts, one per act. Each sets the font size, the window size and the typing speed, and uses `Hide`/`Show` around setup lines. Each calls `crisis-belem.sh --act N` with `pause` set to sleep. One act per file keeps retakes cheap. The output goes to `out/video/` (git-ignored); the cut is done outside the repository.

### `plan/2026-10-1x-fork-demo.plan.md`

The repository builds each feature from a plan with numbered decisions. The module docstrings cite them. This plan records the choices behind §4:
- what `RISKDEP_FORK` turns off, and what it never turns off (the on-chain reads);
- the clock on a fork (latest block timestamp);
- the name and location of `--record-as`;
- the timelock-queue events watched, and the alert levels;
- the startup finding for 0 s exit gates;
- reading the band of custom aggregators.

It follows the format of the other plans in `plan/` (decisions, tracker, interview log).

### `fixtures/replay/fork-belem/` and `tests/test_fork_replay.py`

- **The recording:** one run of `crisis-belem.sh` with `riskdep watch --record-as fork-belem` saves every response the watch received. Like the other replays, it is committed with the change that needs it, so CI and the video can replay it offline.
- **The test** re-runs the recording with `--replay` and asserts:
  - the alert sequence and levels: oracle move (act 2), liquidatable borrower, withdrawals (act 4), critical exit gate (act 5), upgrade scheduled and then executed (act 6);
  - the two thresholds (90,857 and 75,142 EUR) within rounding;
  - that no "second RPC" critical appears, which proves the fork flag works.
- **It also guards the demo:** if a later change breaks the demo, CI fails before the video is shown.

## 6. The video

**Length 3–4 min. Layout:** tmux in three panes: crisis script (left, large captions), `riskdep watch` (right), anvil log (bottom, small). A browser window for the graph and the report.

| Time | Screen | Voice-over (one line) |
|---|---|---|
| 0:00–0:20 | title; the RockawayX dashboard | "33 vaults, $294M. Which ones would a crisis hit, and how fast?" |
| 0:20–0:50 | `graph` of the Belem vault | "86 % in one market, one borrower, an oracle one wallet can move." |
| 0:50–1:15 | act 1, `analyze --vault --shock` | "Before anything happens: at −10 % the borrower is liquidatable; at −30 % depositors lose €0.25M." |
| 1:15–1:45 | act 2, `setRoundData` | "One transaction from the issuer's key. The watch sees it on the next block." |
| 1:45–2:15 | act 4, the run | "Depositors leave; utilisation hits 100 %; here is where our depositor stands in the queue." |
| 2:15–2:40 | act 5, the gate | "The curator closes the exit. No timelock, nobody could stop it." |
| 2:40–3:20 | act 6, schedule → warp 48 h → upgrade | "A real loss needs an upgrade, behind 48 hours. riskdep sees it queued: that is the window to leave." |
| 3:20–3:45 | act 7, the report | "Predicted against observed: the same numbers." |

**Recording:** [`vhs`](https://github.com/charmbracelet/vhs) `.tape` scripts make terminal takes reproducible, with fixed font and timing. The tape files sit in `scripts/fork/`. Alternatively, asciinema plus OBS for the browser. Record each act separately and cut, so a failed act does not cost the whole take.

## 7. Risks

| Risk | Mitigation |
|---|---|
| Token whitelists (EURCV, mGLOeuro) block the liquidation of act 3 | act 3 is optional; check in step 2 of §8 |
| No archive RPC: no fixed block | fork `latest` on the recording day; the anvil cache keeps it |
| Anvil `eth_getLogs` before the fork block goes upstream and hits rate limits | start the watch at the fork block (`--from-block` or a cursor at B) |
| The facts change before recording (NAV update, borrower repays, band changed) | step 1 re-reads every fact in §1 at the fork block and recomputes the thresholds |
| Showing a "how to attack" recipe | every act uses a role the protocol grants (issuer, curator, timelock); no exploit. Say so in the video |

## 8. Order of work

1. **Fork and facts:** start anvil at B and re-read §1 at B (band, role holder, position, LTV, thresholds). Half a day.
2. **Dry run of the acts with `cast` only**, no riskdep: impersonation of the EOA and of the Safe, the gate, the timelock schedule and warp, the token whitelists. Half a day.
3. **The four demo changes of §4:** fork flag, cross-checks, clock, `--record-as`. One day, with tests.
4. **The three product changes of §4:** timelock queue, standing exit-gate risk, feed band. One to two days; useful beyond the demo.
5. **`crisis-belem.sh` with captions; record `fixtures/replay/fork-belem/`; `tests/test_fork_replay.py`.** Half a day.
6. **The vhs tapes and the video cut.** Half a day.

Steps 1 and 2 decide whether act 3 stays. Steps 1, 2, 3 and 5 alone already give a working video. Step 4 is what makes act 6 land.
