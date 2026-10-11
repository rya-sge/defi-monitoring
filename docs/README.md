# Documentation

Usage of every mode is in the repository's `README.md`; how the code is built is in `analysis/ARCHITECTURE.md`. The documents below explain what the tool computes and detects, and why.

## Where to start

| If you want to know… | Read |
|---|---|
| How a position's risk becomes STAY / REDUCE / EXIT | `model/how-risk-is-computed.md` |
| Where every probability comes from | `model/how-probabilities-are-computed.md` |
| How an incident is detected, and how fast | `watch/how-an-incident-is-detected.md` |
| What an alert means and what to do | `reference/alert-runbook.md` |
| What a threshold or parameter is, and its basis | `reference/registry-reference.md` |

## `model/`: how risk and impact are computed

| Document | Content |
|---|---|
| `how-risk-is-computed.md` | `analyze` end to end: the position, its layers, the priors, propagation, the simulation and the verdict |
| `how-probabilities-are-computed.md` | Hack base rates, oracle and market-event priors, Beta severities, the breakeven p\*, outside views |
| `monte-carlo.md` | How the simulation samples incidents and turns them into a loss distribution |
| `scenarios-and-breakeven.md` | Scenarios and breakeven probabilities |
| `vault-incident.md` | Incident mode for a vault depositor and a book of vaults (`analyze --vault` / `--book`, `POST /api/incident`) |
| `vault-depositor-scenarios.md` (+ pdf) | A vault depositor's loss under a scenario |
| `shock-engine.md` | The shock engine: what happens to a vault when a node fails, and its rules |
| `shock-trace.md`, `shock-trace-example.json` | The propagation as data, for a front end |
| `graph-propagation.md` (+ pdf) | The dependency graph as a propagation engine |
| `midas.md` | Midas (mGLOeuro): the published NAV feed, its band and timelock, the Belem incident, and what is not computed |
| `fx-protocol.md` | f(x) Protocol (fxSAVE, PT-fxSAVE): what backs fxSAVE, the RockawayX f(x) incident, exits, and what is not computed |
| `infinifi.md` | infiniFi (iUSD, siUSD): the oracle, the loss waterfall, the RockawayX USDC Yield incident, and what is not computed |
| `ethena.md` | Ethena (USDe, sUSDe): the backing by venue, the priors, a venue failure, funding stress, contagion, and what is not computed |
| `zama-confidential-vaults.md` | Zama confidential vaults: the hidden layer, who loses, the two exits, contagion, alerts, and what is not computed |

## `watch/`: detection and monitoring

| Document | Content |
|---|---|
| `how-an-incident-is-detected.md` | Each kind of incident: its signal, detector, threshold, timing and alert; OracleImpact; early warnings; what is not detected |
| `how-a-block-is-analysed.md` | One block through the watcher: fetch, decode, read, assess, cursor |
| `drain-threshold.md` | When a depeg empties a market: the drain threshold d\* |
| `exit-queue.md` | A depositor's place in a run on a vault |
| `user-watcher-options.md` | Watching an address: the options and their trade-offs |
| `websocket-vs-polling.md` | Following the chain: WebSocket subscription vs polling |

## `reference/`: look-up material

| Document | Content |
|---|---|
| `alert-runbook.md` | Every alert: what it means, what to check, what to do |
| `registry-reference.md` | Every key of `riskdep/registry.json`, with its unit and basis |
| `glossary.md` | The terms used across the project |

## `setup/`: running it

| Document | Content |
|---|---|
| `erpc.md` | Running riskdep through the optional local eRPC proxy |
| `telegram-botfather-commands.md` | The Telegram bot's BotFather commands |

## Other folders

| Folder | Content |
|---|---|
| `examples/` | `graph-example.html/.json`, an example output of `graph` |
| `img/` | Mindmaps and diagrams, each `.png` next to its `.puml` |
| `analysis/` | Assessments and project notes: `ARCHITECTURE.md`, `PROVIDERS.md`, `NEXT_STEP.md`, `ANALYSIS_MONITORING.md`, `GAP.md`, `EXTERNAL_SOURCE.md`, `ROCK-VAULT.md`, `ROCK-VAULT-DEP.md`, `ZAMA-VAULT.md`, `FORK-PRESENTATION.md`, `REPOSITORY_ADD.md`, `comparison_team.md` |
| `archive/` | Superseded documents kept for their reasoning: `ANALYSIS_CURRENT.md` (the 2026-10-10 assessment behind the known-incident answers) |
| `risk-assessment/` | Outside risk providers in riskdep: `outside-providers.md`, `nexus.md`, `pharos.md`, and the providers' own documentation (git-ignored) |
| `external/` | Third-party documentation and source repositories (Morpho, Pendle, Chainlink, issuers), each with its own `README.md` |
| `hackaton_instruction/` | The challenge brief (`GOAL.md`) |
