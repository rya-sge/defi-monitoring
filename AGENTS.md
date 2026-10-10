# defi-monitoring — agent guide

> **Note — keep in sync:** `AGENTS.md` and `CLAUDE.md` must always be **identical**. Any edit to one must be applied verbatim to the other.

> **Note — never commit:** an assistant must **never** run `git commit`, `git push`, `git tag`, `git merge`, `git rebase` or `git reset --hard` in this repository. Staging (`git add`) and read-only inspection (`git status`, `git diff`, `git log`) are fine; creating or moving history is the author's alone.
>
> Two reasons, one practical and one editorial. Commits here are GPG-signed (`commit.gpgsign = true`), and gpg cannot read a passphrase from a non-interactive session: the attempt fails with `gpg: cannot open '/dev/tty'` and leaves a half-staged index behind. And the author reviews the diff before it becomes history — a commit made for them removes the one checkpoint where a wrong change is still cheap to drop.
>
> So end a piece of work by leaving the tree ready and handing over the **one-line commit message** the note below asks for. If several commits are wanted — a style-only commit split from a behaviour commit, say — hand over the staging and commit commands for each, in order, and let the author run them.

> **Note — merge conflicts are expected:** several developers work on this project in parallel, so a merge with `main` can conflict even when nothing is wrong: two people edited the same line for different reasons. Treat each side as an intentional change, not an error to discard.
>
> To resolve one: read both sides and the commits behind them (`git log --oneline <branch> -- <file>`), check which one matches the current code (the code wins over prose), and keep both intents when they are compatible rather than picking a side. If the two intents contradict and the code does not decide, ask the author. Remove every marker, `git add` the file, and hand over the merge commit as the note above says.

> **Note — be concise:** keep every summary, report and explanation short and direct. Lead with the result, state what changed and what it costs, stop. No preamble, no restating the request, no recap of steps the reader just watched, no closing paragraph that says the same thing again. Prose only where a table or a one-line command would not do.

> **Note — commit messages:** After each group of modifications or each feature added, always provide a **one-line GitHub commit message** (Conventional-Commits style, e.g. `feat: ...`, `fix: ...`, `docs: ...`).
>
> **Every reply that changed a file ends with it** — the commit message is the last thing in the reply, nothing after it. A reply that touched the repository and does not end that way is unfinished.
>
> **Never put `!` in a commit message** — not as the breaking-change marker (`feat!: ...`), not anywhere else. In an interactive bash, `!` inside double quotes triggers history expansion, so `git commit -m "feat!: ..."` aborts with `bash: !: unrecognized history modifier`. Signal a breaking change with an uppercase `BREAKING CHANGE:` line in the commit body instead, and keep the subject line free of `!`.

> **Note — no tool names in the changelog:** never name an assistant tool, skill or slash command in `CHANGELOG.md`. The changelog records what changed in *this project*, for readers who have no idea what tooling produced it. A line ending "the `<some-skill>` skill gained the corresponding check" documents the author's toolbox rather than the release, and it rots independently of the repository — the tool can be renamed or deleted, leaving a dangling reference to something the reader could never have seen. Describe the change and its effect; if the tooling matters, record it in the audit or analysis report instead.
>
> This is about **tool identities, not the word "Claude"**: files committed to the repository — `CLAUDE.md`, `AGENTS.md`, `CLAUDE_AUDIT.md`, `CLAUDE_ANALYSIS*.md` — are cited freely, because a reader can open them.

> **Note — do not hard-wrap prose in `CHANGELOG.md`:** one line per bullet or paragraph, and let the editor soft-wrap. Markdown collapses a single newline into a space, so a hard-wrapped bullet renders identically — the cost is invisible in the published changelog and paid entirely in the repository. Changing one word reflows every following line, so a one-word correction arrives as a multi-line diff in which a reviewer cannot see what actually changed; and because the wrap column depends on whoever wrote the entry, the file drifts into a mix of styles that reads as damage. Keep the line structure only where it is semantic: fenced code blocks, tables and blockquotes.

> **Note — never break the code in place to test a test:** when you need to verify that a test actually catches a defect — mutation testing: delete an assert, flip a condition, drop a delivery — do it in a **throwaway copy of the repository**, never in the working tree.
>
> Editing source forces a rebuild, and if that run is interrupted — an OOM kill, a timeout, a cancelled command — the restored source and the stale build output **disagree**: `git status` reports a clean tree while the build directory holds artifacts built from the mutated code. Nothing surfaces that state, and restoring the source does not restore the build. It has already happened once here, leaving compiled artifacts missing a safety check one step before a release tag.
>
> The procedure: `git worktree add /tmp/mut HEAD --detach`, copy across any uncommitted test files the mutation needs (a worktree is made from the last commit, so new tests are absent), mutate and run there, then `git worktree remove /tmp/mut`. If a mutation ever does run in the working tree, rebuild and **prove** recovery against a recorded build fingerprint rather than assuming it.

> **Note — long changelog entries get sub-bullets:** past roughly three sentences, a bullet stops being scannable — the defect, its blast radius, the fix, the precedent and the caveat all run together, so a reader looking for any one of them has to parse all five. Lead with one sentence naming *what changed*, then one sub-bullet per distinct claim: impact, fix, behaviour-change warning, cost, migration note. A useful trigger is length — compare against the file's own median bullet and split anything several times longer, since that length almost always means several claims in one paragraph. Sub-bullets follow the same no-hard-wrap rule: one line each.

## What this project is

**Read `docs/hackaton_instruction/GOAL.md` first:** it states the challenge this project answers (the DeFi Risk Dependency Challenge), what is expected, and how it is judged (dependency discovery 30 %, impact estimation 30 %, decision usefulness 25 %, working demo on real data 15 %). Weigh every change against it. The original brief is `docs/hackaton_instruction/Hackathon_DeFi-Risk-Dependency-Challenge_EN_v1.pdf` (one page, Belem Capital, EPFL Hackathon 2026): read it too, it holds what `GOAL.md` does not, such as the worked trade-off (a book in ten 10 % pockets, one affected, 11 % slippage to unwind: make stay-vs-exit explicit), the scope examples (oracle and feed-quality analysis, vaults deploying into an external venue such as a perp exchange, protocols concentrating a large share of on-chain TVL) and the exact criterion wording ("depth and correctness", "is the number defensible"). **Git-ignored**: the file is local only and its notice forbids copying it, so quote from it sparingly and never commit it.

`riskdep` is a Python CLI (`python3 -m riskdep`) for the risk of DeFi positions on Ethereum, centred on Morpho. It has four subcommands: `analyze` (batch STAY / REDUCE / EXIT report for a Pendle PT used as Morpho Blue collateral), `watch` (follow a Morpho Vault V2 block by block and alert a depositor), `watch --user` (find every Blue borrow and Vault V2 deposit of an address and monitor them together) and `graph` (interactive dependency graph, with the sibling markets of the held ones and each oracle's class). All data comes from public sources: the publicnode Ethereum RPC, the Morpho and Pendle APIs, DefiLlama, all keyless; and Etherscan, whose key in `keys.ini` is optional (without it, an oracle's source verification reads "not checked", and an oracle input only its name would classify reads "not classified").

## Key concepts

- **Design first.** Each mode was built from a plan in `plan/` (design, numbered decisions `D1…`, tracker, interview log). Module docstrings cite those decisions (e.g. `D21`, `D37`); read the matching plan row before changing behaviour it governs.
- **Pure rules, I/O at the edges.** `rules.py`, `borrower_rules.py` and `propagate.py` are pure functions (decoded events + state before/after → alerts); network access lives in `sources.py`, `vault.py`, `borrower.py`, `poller.py`, `crosscheck.py`.
- **One cached fetcher.** `sources.py` keys every request by a hash of (method, url, body) and stores it under `fixtures/snapshot/`, so a live run doubles as the offline demo snapshot. `RISKDEP_RPC_URL` changes where the main RPC's requests are sent, never the URL they are cached under. `--record` saves watch ranges under `fixtures/replay/<vault>/` or `fixtures/replay/user-<address>/`, and graphs under `fixtures/replay/graph-<target>/`; `--replay` re-runs them offline.
- **One clock.** `clock.py` makes offline runs use `fixtures/snapshot/as_of.json` as "now", so the demo is reproducible on any later day. Never call `time.time()`/`datetime.now()` directly in analysis code.
- **Registry, not constants.** Facts, assumptions, priors and watch thresholds live in `riskdep/registry.json` (`watch` key for alert thresholds), each with a stated basis.
- **Alert levels** are `info` / `warn` / `critical`; the trigger tables are in `README.md`.
- **Watch loop invariant:** discover, read state, poll, assess, alert, and save the cursor **last** (`out/watch-*.cursor`), so a restart resumes without skipping blocks. Polling runs 2 blocks behind the head every 12 s; deeper reorgs are not handled. A live batch with no event reads only what moves without one (`vault.read_light`, `borrower.read_prices`); any event, gap, undecoded log or refresh, and `watch.full_state_every_blocks`, force a full read (D61). Replays and `--blocks` runs always read in full.
- **Cross-checks never stop a run:** block hash against a second RPC (critical on mismatch), Morpho API against chain state (warn, 0.5 % tolerance); a check that cannot run prints "not checked".
- **Free-RPC limits:** state is servable only ~64–90 blocks back (state-based rules on older ranges start at the oldest servable block); at most 9 addresses per `eth_getLogs` filter (the poller splits longer lists); recent ranges are intermittently refused as "archive" (the poller retries). Admin-surface filters are optional: a refusal is a warning, not a gap. Under a burst publicnode answers HTTP 429, and a local eRPC answers 200, both with a rate-limit error per batch item: `sources.Fetcher` waits and resends either (`_throttled`, up to 6 times) and never caches it. For long live runs, the optional local eRPC proxy (`erpc.yaml`, `docs/erpc.md`) spreads the calls over six free endpoints; it must never list dRPC, the cross-check's independent node.

## File tree

```
riskdep/
  __main__.py         entry point → cli.main
  cli.py              argparse: analyze, watch, graph
  sources.py          keyless HTTP/RPC sources behind one cached fetcher (fixtures/snapshot/)
  clock.py            single clock; snapshot date when offline
  abi.py              Morpho Blue / Vault V2 / adapter event and function signatures
  registry.json       facts, assumptions, priors, thresholds
  crosscheck.py       second-RPC block hash and API-vs-chain checks
  # watch (Vault V2)
  vault.py            Vault V2 structure (vault → adapters → Blue markets) and state at a block
  poller.py           eth_blockNumber + eth_getLogs from a saved cursor
  rules.py            pure impact rules for a Vault V2 depositor
  watch.py            the watch loop
  # watch --user
  positions.py        what an address holds on Morpho (API lookup)
  borrower.py         Blue borrow positions, health factor and a market's main lenders, read on-chain
  borrower_rules.py   pure borrower rules (HF levels, on-behalf actions, rate, oracle, main lenders)
  watch_user.py       the watch --user loop
  # both watches
  market_risk.py      every borrower of the watched markets: unrealised bad debt, liquidation curves
  drain.py            drain threshold of each vault market: d*, the drainable amount, the Public Allocator
  scenario.py         incident mode: a known incident's impact, time to impact and verdict; alert impacts
  vault_incident.py   incident mode for a vault depositor: a collateral markdown or a borrower default
  vault_book.py       a book of vaults (file or --vault flags) under one incident, added up in USD
  exit_queue.py       a depositor's place in a run on a vault: recovery and loss by queue position
  admin.py            admin surface of the watched markets: upgrades, owners, feeds, pauses, mints, oracle divergence
  # graph
  graph.py            dependency graph as JSON + Cytoscape.js HTML
  siblings.py         sibling markets: other Blue markets sharing a held market's collateral, underlying or price input
  oracle_class.py     oracle class, price-tracking or constant-price, from structure and round history (pure + probe)
  # analyze
  discover.py         position → numbers plus a typed layer graph
  priors.py           per-layer incident priors
  propagate.py        how a shock on one layer reaches the position (pure)
  simulate.py         Monte Carlo over layer incidents
  decide.py           STAY / REDUCE / EXIT verdict
  report.py           HTML + JSON report
tests/                pytest, all offline (snapshot + recorded replays)
  test_watch_rules.py, test_watch_replay.py, test_borrower.py, test_watch_user_replay.py,
  test_graph.py, test_siblings.py, test_oracle_class.py, test_market_risk.py, test_exit_queue.py, test_drain.py, test_scenario.py, test_vault_incident.py, test_vault_book.py, test_admin.py, test_decide.py, test_propagate.py, test_demo_snapshot.py, test_fixes.py, test_light_reads.py
pyproject.toml        project metadata, dependencies, ruff and pytest configuration
```

## Other important files

- `docs/hackaton_instruction/Hackathon_DeFi-Risk-Dependency-Challenge_EN_v1.pdf` — the original challenge brief (PDF, git-ignored, local only); the source of `GOAL.md`.
- `docs/hackaton_instruction/GOAL.md` — the challenge brief: what to build, what is expected, the judging criteria and their weights, and where the repository answers each.
- `docs/analysis/ARCHITECTURE.md` — how the system is built: modes, components and their imports, data sources and trust, data flow, state, testing, decision index.
- `README.md` — usage of every mode, alert trigger tables, limits.
- `docs/analysis/ANALYSIS_CURRENT.md` — the latest assessment (2026-10-10): the brief read as detect → impact → how fast → decide, where the tool stands on each step, why the Monte Carlo should become conditional on the observed incident, and the resulting order of work. Read it before `docs/analysis/NEXT_TASK.md`.
- `docs/analysis/NEXT_TASK.md` — the task-level detail of incident mode (done) and of the book and the conditional Monte Carlo; `NEXT_STEP.md` holds the current order.
- `docs/analysis/NEXT_STEP.md` — the next steps, in recommended order (phases A to D), with how each would be built and what it needs; it records what has been built and merges the earlier versions 1 and 2. Keep it current when a step is done.
- `docs/analysis/PROVIDERS.md` — every external provider (RPC, APIs, CDNs): endpoints, queries, limits, trust model. Keep it current.
- `keys.example.ini` — template of the API keys and secrets (no values); the real `keys.ini` is git-ignored.
- `erpc.yaml` — configuration of the optional local eRPC proxy (eRPC 0.3.0, six free upstreams, no key); `docs/erpc.md` is the setup guide. Its upstream list is mirrored in `docs/analysis/PROVIDERS.md`.
- `docs/analysis/ANALYSIS_MONITORING.md` — design note: dependency graph, impact, monitoring, execution, and gaps of the current implementation (done / partial / missing).
- `plan/` — the fourteen plans (`defi-risk-dependency`, `morpho-vault-v2-watcher`, `morpho-user-watcher`, `lenders-and-timelocks`, `market-borrowers`, `admin-surface`, `exit-queue`, `drain-threshold`, `sibling-markets`, `incident-mode`, `vault-incident`, `vault-book`, `wrapped-collateral`, `borrower-concentration`).
- `examples/` — `rockawayx-ethereum.json`, the demo book of vaults and the template for any other (`analyze --book`).
- `docs/` — `alert-runbook.md` (what each alert means and what to do), `glossary.md`, `registry-reference.md` (every `registry.json` key), `how-risk-is-computed.md`, `monte-carlo.md` (how `analyze`'s simulation works; its mindmap in `docs/img/`), `scenarios-and-breakeven.md`, `vault-depositor-scenarios.md`, `graph-propagation.md`, `how-a-block-is-analysed.md`, `websocket-vs-polling.md`, `user-watcher-options.md`, `exit-queue.md`, `erpc.md` (the optional local RPC proxy), `drain-threshold.md`, `graph-example.html/.json`.
- `docs/external/` — third-party references, read-only; check behaviour against them before changing a rule:
  - `morpho/docs.morpho.org-developers-docs/` — Morpho developer docs (contracts, Bundles, addresses, Midnight, Vault V2 exit routes); `tests/test_watch_replay.py` checks the event selectors in `abi.py` against its `contracts/` pages, and skips that check when the folder is absent. **Git-ignored**: it exists only in the local checkout, so read it there; a fresh clone does not have it.
  - `morpho/lib/morpho-blue` (`8e26ca6a`) and `morpho/lib/vault-v2` (`d992cb84`) — Morpho Blue and Vault V2 sources: events, liquidation and shares maths, authorisation, adapters, timelocks, gates.
  - `morpho/lib/morpho-blue-oracles` (`9d2a0b66`) — Morpho's standard oracles: `MorphoChainlinkOracleV2` (price = base vault × base feeds ÷ quote vault × quote feeds) and the wstETH exchange-rate adapter.
  - `morpho/lib/metamorpho-v1.1` (`3b17547e`) — Morpho Vault V1.1 (MetaMorpho): supply and withdraw queues, caps, `lostAssets`; the source for watching Vault V1 deposits (step 4 of `docs/analysis/NEXT_STEP.md`).
  - `pendle/docs.pendle.finance-pendle-v2-dev-docs/` — Pendle V2 developer docs (contracts, oracles, integration, backend API).
  - `pendle/lib/pendle-core-v2-public` (`87685c89`), `pendle/lib/Pendle-SY-Public` (`73676d93`), `pendle/lib/external-integration` (`1694fea0`) — Pendle core (PT/YT, markets, router, oracles), SY wrappers, integration examples.
  - `docs.etherscan.io-api-reference-docs/` — Etherscan API V2 reference (`getsourcecode`, `getabi`, …); the key is in `keys.ini`.
  - `chainlink/docs.chain.link-data-feeds-docs/` — Chainlink Data Feeds documentation (price, rates, SmartData / Proof of Reserve, SVR feeds; `latestRoundData`, heartbeat and deviation, L2 sequencer uptime). **Git-ignored**: it exists only in the local checkout, so read it there; a fresh clone does not have it.
  - `tori/docs.tori.finance-docs/` — Tori Finance documentation (trUSD and strUSD: backing, peg mechanism, reserve fund, strategy, contracts and roles, audits, risks); the issuer behind the strUSD, etrUSD and PT-trUSD collateral of the RockawayX vaults (`docs/analysis/ROCK-VAULT-DEP.md`). **Git-ignored**: it exists only in the local checkout, so read it there; a fresh clone does not have it.
  - `infini-protocol/docs.infinifi.xyz-docs/` — infiniFi documentation (iUSD, siUSD and liUSD: whitepaper, vaults, oracles, slashing mechanics and the loss waterfall, Pendle liquidity, audits, risk disclosures); the issuer behind the siUSD collateral of the RockawayX USDC Yield vault (`docs/analysis/ROCK-VAULT-DEP.md`). **Git-ignored**: it exists only in the local checkout, so read it there; a fresh clone does not have it.
  - `midas/docs.midas.app-docs/` — Midas documentation (mTokens: oracle architecture and mToken pricing, asset transparency, legal structure, smart-contract registry, security, risk management, per-product terms such as mROX); the issuer behind the mGLOeuro collateral of the Belem RWA EURCV vault and of RockawayX's mROX (`docs/analysis/ROCK-VAULT-DEP.md`). **Git-ignored**: it exists only in the local checkout, so read it there; a fresh clone does not have it.
  - `fx-protocol/fxprotocol.gitbook.io-fx-docs-docs/` — f(x) Protocol documentation (fxUSD and fxSAVE: stability pool, rebalancing and liquidation brake, the f(x) invariant, fees, integrating fxSAVE, keeper bots, contracts, "what could go wrong"); the issuer behind the fxSAVE and PT-fxSAVE collateral of the RockawayX f(x) Protocol Ecosystem vault (`docs/analysis/ROCK-VAULT-DEP.md`). **Git-ignored**: it exists only in the local checkout, so read it there; a fresh clone does not have it.
  - `ethena/docs.ethena.fi-docs/` — Ethena documentation (USDe and sUSDe: backing assets, custody and off-exchange settlement, hedging and funding risk, reserve fund, mint and redeem, staking cooldown, roles and blacklist, API); the issuer of the demo position's PT-sUSDE collateral and of the USDe/sUSDe entries in `registry.json`, and a dependency of Re's reUSD and of infiniFi. **Git-ignored**: it exists only in the local checkout, so read it there; a fresh clone does not have it.

  The seven source repositories are git submodules (`.gitmodules`), pinned at the commits above: after a clone, run `git submodule update --init`. To move a pin, check out the new commit inside the submodule and stage the submodule path.
- `fixtures/snapshot/` (analyze demo cache + `as_of.json`) and `fixtures/replay/` (recorded watch ranges and graphs) — test fixtures; do not delete or regenerate casually. **Tracked in git, not ignored, on purpose:** every test runs offline from these cached responses, so CI and any fresh clone need them; a cache file present on one machine only makes a test pass locally and fail in CI. They used to live under `data/`, which `.gitignore` ignores, and new cache files were silently left out of commits (the exit-queue test failed in CI for that reason). So a new cached response (`--record`, `--live`, or a live fetch into these folders) is committed with the change that needs it: check `git status fixtures/`. They hold public responses only: API keys go on the request, never into a cache file (`sources.Fetcher`, `secret`).
- `out/` — run outputs (reports, alert `.jsonl`, cursors); git-ignored.
- `conftest.py` — puts the repo root on `sys.path` for tests.
- `pyproject.toml` — project metadata, the runtime dependencies, the `dev` dependency group, and the ruff and pytest configuration.
- `uv.lock` — the exact resolved version of every dependency; committed, because this is an application and not a library.
- `.pre-commit-config.yaml` — the pre-commit hooks: `ruff check --fix`, then `ruff format`.
- `.github/workflows/ci.yml` — CI on every push, two parallel jobs on Python 3.10: `checks` (`ruff check`) and `tests` (`pytest`).

## Dependencies (tested versions)

Python ≥ 3.10; CI runs the suite on 3.10, the floor `requires-python` in `pyproject.toml` declares. `uv.lock` is the source of truth for versions; it currently pins requests 2.34.2, numpy 2.5.3, networkx 3.7, eth-utils 6.0.0, eth-abi 6.0.0, eth-hash 0.8.0 with pycryptodome 3.24.0, and in the `dev` group pytest 9.1.1 and ruff 0.17.0. `eth-hash[pycryptodome]` is a runtime dependency in its own right: `eth-abi`/`eth-utils` pull `eth-hash` in without a keccak backend, and `abi.py` needs one to compute event signatures — without the extra, `pytest` fails at collection with `ImportError: None of these hashing backends are installed`. The HTML outputs load Mermaid (report) and Cytoscape.js (graph) from a CDN.

## Common commands

```bash
uv sync
uv run pytest -q tests                                 # 197 tests, offline
uv run python -m riskdep analyze --demo                # cached snapshot, no network → out/report.html/.json
uv run python -m riskdep watch --replay                # re-run the recorded vault range offline
uv run python -m riskdep watch --blocks 1000 --record  # live range, saved for --replay
uv run python -m riskdep watch --user <address>        # every Morpho position of an address, live
uv run python -m riskdep graph --example               # out/graph.html + out/graph.json
uv run python -m riskdep graph --vault 0xE0181090c22579B6A217f1522cbf8c9f1F0C1965 --replay  # recorded RockawayX graph, siblings and oracle classes, offline
uv run ruff format . && uv run ruff check .            # format and lint, 120 columns
~/.local/bin/erpc erpc.yaml                            # optional local RPC proxy (docs/erpc.md), in its own terminal
export RISKDEP_RPC_URL=http://127.0.0.1:4000/main/evm/1  # route live runs through it; unset to go direct
```

## Conventions

- Tests must stay offline: a new network call needs a cached snapshot or a recorded replay behind it.
- New thresholds or assumptions go in `registry.json` with their basis, not as literals in code, and in `docs/registry-reference.md`.
- A new or changed alert gets its row in `docs/alert-runbook.md`.
- Any change that adds, removes or replaces a data provider, endpoint, query or browser script (RPC, API, CDN) updates `docs/analysis/PROVIDERS.md` in the same commit.
- Keys and secrets go only in `keys.ini` (git-ignored, `chmod 600`), never in code, docs or committed files; a new key gets its name, with no value, in `keys.example.ini`. Do not use `.env` files for this project.
- Rule modules stay pure (no I/O); put fetching in the source/state modules.
- A behaviour change that departs from a plan decision is recorded in that plan's decision table.
- Leave format and lint to ruff, at 120 columns, in pre-commit and in CI; never mix a style-only commit with a behaviour change.
- `uv.lock` is committed: change a dependency with `uv add` / `uv lock`, never by editing the lock by hand — CI runs `uv sync --locked` and fails if the lock has drifted from `pyproject.toml`.
- Package version lives in `pyproject.toml` and must stay in step with `riskdep/__init__.py` `__version__` (currently `0.1.0`); nothing in the code reads `__version__`, only the docs cite it. There is no `CHANGELOG.md` yet.
