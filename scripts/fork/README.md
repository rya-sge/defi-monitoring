# Fork demo: a crisis on a mainnet fork

`riskdep` following a real crisis, caused on a local fork of Ethereum mainnet by the roles that could really cause it. The design, the facts behind each act and the video storyboard are in `docs/analysis/FORK-PRESENTATION.md`; the decisions are in `plan/2026-10-11-fork-demo.plan.md` (D180–D186).

Needs Foundry (`anvil`, `cast`, `forge`) and the project's `uv` environment. No key: the fork's upstream is `keys.ini [rpc] url` when set, else a keyless archive endpoint.

What each line of the output means: `DEMO-EXPLAINED.md`.

## One command

```bash
scripts/fork/demo.sh --short    # the 2-minute cut (112 s measured): prediction, markdown, timelocked upgrade, bad debt
scripts/fork/demo.sh            # everything, in one terminal: build, fork, watch in the background, acts 0–7, stop
scripts/fork/demo.sh --record   # the same, recorded to out/video/demo.cast (needs: sudo apt install asciinema)
scripts/fork/demo.sh --stop     # from another terminal: stops the demo, its watch and the fork
```

Ctrl-C in the demo's terminal stops it the same way. Only one demo runs at a time: a second one refuses to start, and `start-fork.sh` refuses a port that something else already holds.

It builds the contracts, forks mainnet at block 26,165,572, starts `riskdep watch --step 1 --poll 2` on the Belem vault in the background and plays each act; under each act it prints, marked `riskdep ▸`, the alerts the watch raised for it. At the end it stops the watch and the fork. `--short` plays acts 0, 1, 2, 6 and 7 with 2 s pauses: the prediction runs offline (from `fixtures/replay/incident-<vault>/`, in a second) while riskdep starts up, then only its three key start-up findings show; without act 3's early liquidation, the bad debt observed matches the prediction (252,914 against 251,761 EURCV, the gap being 48 h of interest). `--manual` waits for Enter between steps (presenting live), `--fast` skips act 1 (the two predictions, ≈ 1.5 min), `--block N` forks elsewhere. The watch's full output is in `out/demo/watch.log`.

## Step by step

```bash
(cd scripts/fork && forge build)                  # the two demo contracts
scripts/fork/start-fork.sh 26165572               # anvil at that block, checked; prints the two exports
export RISKDEP_RPC_URL=http://127.0.0.1:8545 RISKDEP_FORK=1

uv run python -m riskdep watch --vault 0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec --step 1   # right pane
scripts/fork/crisis-belem.sh                      # left pane: acts 0–7, Enter between acts
scripts/fork/start-fork.sh --stop                 # saves the state to out/fork-<block>.json
```

Without a fork, the watch's side replays offline:

```bash
uv run python -m riskdep watch --vault 0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec --replay --record-as fork-belem
```

## The crisis (`crisis-belem.sh`)

Belem RWA EURCV, $4.7M: 86 % lent against mGLOeuro, one borrower, a feed one EOA writes inside a fixed 90,000–110,000 EUR band.

| Act | On the fork | riskdep (`watch --step 1`) |
|---|---|---|
| 0 | facts: NAV 100,000, LTV 0.70 | startup: `FeedBand` (−10 % without a 48 h upgrade), `ExitGate` (abdicated), timelock watched, cross-checks "not checked" |
| 1 | `analyze --vault --shock token=mGLOeuro:0.10`, then `:0.30` | −10 %: liquidatable, no loss; −30 %: 251,761 EURCV bad debt |
| 2 | the feed admin EOA: `setRoundData(90,000)` | oracle −10.0 % (warn); liquidation curve |
| 3 | a liquidator seizes 2 mGLOeuro | `Blue.Liquidate` |
| 4 | the 0.5 % holder exits; the 99.5 % holder takes the rest | market 100 % utilised (warn); the next withdrawal reverts |
| 5 | the curator tries `setReceiveAssetsGate` | reverts `Abdicated`; `Submit` is info only |
| 6 | the Midas timelock schedules a feed upgrade; 48 h warp; execute; NAV 70,000 | `Admin.CallScheduled` (warn) 48 h before; `Admin.Upgraded` (critical); unrealised bad debt (critical) |
| 7 | the rest is liquidated | bad debt realised: 217,286 EURCV, against 251,761 predicted |

- `--act N` plays one act (they build on each other: play them in order on a fresh fork).
- `--retake N` reverts the fork to the snapshot taken just before act N and plays it again.
- `PAUSE=6` sleeps between steps instead of waiting for Enter (for recordings).

Every act ends with an on-chain check and stops the script if the chain did not move as planned.

## The alternative crises

Each runs alone on a fork, then `riskdep watch --vault <vault>` shows the effect.

| Script | What happens | Vault to watch |
|---|---|---|
| `alt-redstone.sh` | RedStone's 2-of-3 Safe upgrades the strUSD fundamental feed: oracle 1.03 → 0.70 in one transaction, no timelock | `VAULT_TORI` |
| `alt-pst-mint.sh [AMOUNT]` | a CCIP token pool mints 10M PST (+4.7 % supply); the oracle does not move | `VAULT_HUMA` (`Admin.Mint`) |
| `alt-fxsave-expiry.sh` | warp past 2026-10-29: the PT-fxSAVE linear oracle reaches 1.0 by time alone | `VAULT_FX` |

A time jump (act 6, `alt-fxsave-expiry.sh`) makes RedStone's push feeds stale on the fork, and they then revert: run `alt-redstone.sh` on a fork with no jump. The Pendle pool dump of FORK-PRESENTATION.md §2 is not scripted yet.

## Files

| File | Role |
|---|---|
| `addresses.env` | every address, slot and constant, read on-chain on 2026-10-11 at block 26,165,572; public data only |
| `lib.sh` | shared helpers: captions, pauses, `send_as` (any address, funded), `mine`, `deploy` |
| `start-fork.sh` | starts and checks anvil; `--stop` (saves the state), `--load STATE` (restarts without the upstream) |
| `crisis-belem.sh` | acts 0–7, with checks, snapshots and retakes |
| `alt-*.sh` | the alternative crises |
| `src/MGloEuroFeedV2.sol` | act 6's feed implementation: wider band, same writer, own ERC-7201 storage; **not Midas code** |
| `src/FixedAnswerFeed.sol` | `alt-redstone.sh`'s implementation: a fixed answer; **not RedStone code** |
| `demo.sh` | the whole demo in one command and one terminal; `--record` wraps it in asciinema |
| `tapes/*.tape` | [vhs](https://github.com/charmbracelet/vhs) scripts: `demo.tape` runs `demo.sh` in one take, plus one per act and one for the offline watch replay → `out/video/`. Not run here (vhs is not installed): install with `go install github.com/charmbracelet/vhs@latest` (needs `ttyd` and `ffmpeg`) |
| `foundry.toml` | builds `src/` against the Vault V2 interfaces in `docs/external/morpho/lib/vault-v2` |

The recording `fixtures/replay/fork-belem/` was made on a fresh fork with `crisis-belem.sh`, then `riskdep watch --blocks 32 --step 1 --record --record-as fork-belem`. `tests/test_fork_replay.py` replays it and checks the alert sequence.
