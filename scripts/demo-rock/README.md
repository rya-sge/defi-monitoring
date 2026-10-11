# RockawayX demo: a crisis on a fork, alerts on Telegram

One command: fork Ethereum mainnet, watch two RockawayX vaults with `riskdep`, cause two crises with the roles that could really cause them, and post every `warn` and `critical` alert to the private Telegram channel as it happens. It reuses `scripts/fork/` unchanged (`lib.sh`, `alt-redstone.sh`, `alt-pst-mint.sh`) and starts its own fork, copied from `start-fork.sh` with two differences: the upstream falls back to `keys.ini` `[alchemy]` (a keyless upstream rate-limits two watches until anvil gives up), and its anvil has its own process, so `start-fork.sh --stop` from another terminal cannot kill it; the vaults and their dependencies are in `docs/analysis/ROCK-VAULT.md`.

```bash
scripts/demo-rock/demo-rock.sh --no-telegram    # rehearsal: everything, nothing sent
scripts/demo-rock/demo-rock.sh                  # the demo, alerts to Telegram (≈ 5 min, 4 s between steps)
scripts/demo-rock/demo-rock.sh --manual         # wait for Enter between steps, for presenting live
```

Needs Foundry (`anvil`, `cast`, `forge`), `uv`, network access (the fork's upstream and the Morpho API) and, for Telegram, `keys.ini` `[alerts]` (`TELEGRAM_BOT.md`).

## What happens

| Step | On the fork | `riskdep` | Telegram |
|---|---|---|---|
| Start | fork at block 26,165,572 | `watch` on RockawayX Tori Ecosystem (`VAULT_TORI`, 69 % strUSD) and Huma USDC Main (`VAULT_HUMA`, 100 % PST); start-up findings stay in the terminal | an intro message, marked as a scenario |
| Act 1 | nothing yet | `analyze --book examples/rockawayx-ethereum.json --shock token=strUSD:0.32`, offline: the book loses 2.80M USD, 1.83M in Tori and 0.97M in USDC Yield; act first on Tori | the prediction's headline |
| Act 2 | RedStone's 2-of-3 Safe upgrades the strUSD feed (`alt-redstone.sh`): the oracle −32 % in one transaction | Tori's watch: the feed upgrade, the oracle move, liquidations | each warn and critical alert |
| Act 3 | a CCIP pool mints 15M unbacked PST, +7.0 % of the supply (`alt-pst-mint.sh 15000000`; the script's default 10M is 4.7 %, under the 5 % critical threshold); the oracle does not move | Huma's watch: the mint | each warn and critical alert |
| End | the fork stops | alert counts per vault | — |

Act 1 predicts the same −32 % that act 2 then causes, so the audience sees the forecast before the event.

## Files

`out/demo-rock/` (git-ignored): `watch-tori.log`, `watch-huma.log` (each watch's full output), `watch-*.jsonl` (alerts as JSON, what `notify` reads), `notify.log`, `predict-strusd/book-incident.json`.

## Before presenting

- Run `--no-telegram` once on the venue's network: the fork's upstream and the Morpho API must answer.
- Run `uv run python -m riskdep notify --test` once: `api.telegram.org` must be reachable.
- The channel only shows what happens after the watches start; clear it before the session if a rehearsal posted to it.
