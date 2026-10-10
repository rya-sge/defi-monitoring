# defi-monitoring — agent guide

> **Note — keep in sync:** `AGENTS.md` and `CLAUDE.md` must always be **identical**. Any edit to one must be applied verbatim to the other.

> **Note — commit messages:** After each group of modifications or each feature added, always provide a **one-line GitHub commit message** (Conventional-Commits style, e.g. `feat: ...`, `fix: ...`, `docs: ...`).
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

`riskdep` is a Python CLI (`python3 -m riskdep`) for the risk of DeFi positions on Ethereum, centred on Morpho. It has four subcommands: `analyze` (batch STAY / REDUCE / EXIT report for a Pendle PT used as Morpho Blue collateral), `watch` (follow a Morpho Vault V2 block by block and alert a depositor), `watch --user` (find every Blue borrow and Vault V2 deposit of an address and monitor them together) and `graph` (interactive dependency graph). All data comes from keyless public sources: the publicnode Ethereum RPC, the Morpho and Pendle APIs, DefiLlama.

## Key concepts

- **Design first.** Each mode was built from a plan in `plan/` (design, numbered decisions `D1…`, tracker, interview log). Module docstrings cite those decisions (e.g. `D21`, `D37`); read the matching plan row before changing behaviour it governs.
- **Pure rules, I/O at the edges.** `rules.py`, `borrower_rules.py` and `propagate.py` are pure functions (decoded events + state before/after → alerts); network access lives in `sources.py`, `vault.py`, `borrower.py`, `poller.py`, `crosscheck.py`.
- **One cached fetcher.** `sources.py` keys every request by a hash of (method, url, body) and stores it under `data/snapshot/`, so a live run doubles as the offline demo snapshot. `--record` saves watch ranges under `data/replay/<vault>/` or `data/replay/user-<address>/`; `--replay` re-runs them offline.
- **One clock.** `clock.py` makes offline runs use `data/snapshot/as_of.json` as "now", so the demo is reproducible on any later day. Never call `time.time()`/`datetime.now()` directly in analysis code.
- **Registry, not constants.** Facts, assumptions, priors and watch thresholds live in `riskdep/registry.json` (`watch` key for alert thresholds), each with a stated basis.
- **Alert levels** are `info` / `warn` / `critical`; the trigger tables are in `README.md`.
- **Watch loop invariant:** discover, read state, poll, assess, alert, and save the cursor **last** (`out/watch-*.cursor`), so a restart resumes without skipping blocks. Polling runs 2 blocks behind the head every 12 s; deeper reorgs are not handled.
- **Cross-checks never stop a run:** block hash against a second RPC (critical on mismatch), Morpho API against chain state (warn, 0.5 % tolerance); a check that cannot run prints "not checked".
- **Free-RPC limits:** state is servable only ~64–90 blocks back (state-based rules on older ranges start at the oldest servable block); at most 9 addresses per `eth_getLogs` filter (the poller splits longer lists); recent ranges are intermittently refused as "archive" (the poller retries). Admin-surface filters are optional: a refusal is a warning, not a gap.

## File tree

```
riskdep/
  __main__.py         entry point → cli.main
  cli.py              argparse: analyze, watch, graph
  sources.py          keyless HTTP/RPC sources behind one cached fetcher (data/snapshot/)
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
  admin.py            admin surface of the watched markets: upgrades, owners, feeds, pauses, mints, oracle divergence
  # graph
  graph.py            dependency graph as JSON + Cytoscape.js HTML
  # analyze
  discover.py         position → numbers plus a typed layer graph
  priors.py           per-layer incident priors
  propagate.py        how a shock on one layer reaches the position (pure)
  simulate.py         Monte Carlo over layer incidents
  decide.py           STAY / REDUCE / EXIT verdict
  report.py           HTML + JSON report
tests/                pytest, all offline (snapshot + recorded replays)
  test_watch_rules.py, test_watch_replay.py, test_borrower.py, test_watch_user_replay.py,
  test_graph.py, test_market_risk.py, test_admin.py, test_decide.py, test_propagate.py, test_demo_snapshot.py, test_fixes.py
```

## Other important files

- `ARCHITECTURE.md` — how the system is built: modes, components and their imports, data sources and trust, data flow, state, testing, decision index.
- `README.md` — usage of every mode, alert trigger tables, limits.
- `NEXT_STEP.md` — the recommended next steps, with what each needs (decisions, sources, credentials, infrastructure).
- `ANALYSIS_MONITORING.md` — design note: dependency graph, impact, monitoring, execution, and gaps of the current implementation (done / partial / missing).
- `plan/` — the six plans (`defi-risk-dependency`, `morpho-vault-v2-watcher`, `morpho-user-watcher`, `lenders-and-timelocks`, `market-borrowers`, `admin-surface`).
- `docs/` — `alert-runbook.md` (what each alert means and what to do), `glossary.md`, `registry-reference.md` (every `registry.json` key), `how-risk-is-computed.md`, `how-a-block-is-analysed.md`, `websocket-vs-polling.md`, `user-watcher-options.md`, `graph-example.html/.json`.
- `data/snapshot/` (analyze demo cache + `as_of.json`) and `data/replay/` (recorded watch ranges) — test fixtures; do not delete or regenerate casually.
- `out/` — run outputs (reports, alert `.jsonl`, cursors); git-ignored.
- `conftest.py` — puts the repo root on `sys.path` for tests.

## Dependencies (tested versions)

Python 3.10.12 (requires ≥ 3.10). From `requirements.txt`, tested with: requests 2.25.1, numpy 2.1.1, networkx 2.8.8, eth-utils 5.3.1, eth-abi 5.2.0, pytest 7.4.4. The HTML outputs load Mermaid (report) and Cytoscape.js (graph) from a CDN.

## Common commands

```bash
pip install -r requirements.txt
python3 -m pytest -q tests                         # 99 tests, offline
python3 -m riskdep analyze --demo                  # cached snapshot, no network → out/report.html/.json
python3 -m riskdep watch --replay                  # re-run the recorded vault range offline
python3 -m riskdep watch --blocks 1000 --record    # live range, saved for --replay
python3 -m riskdep watch --user <address>          # every Morpho position of an address, live
python3 -m riskdep graph --example                 # out/graph.html + out/graph.json
```

## Conventions

- Tests must stay offline: a new network call needs a cached snapshot or a recorded replay behind it.
- New thresholds or assumptions go in `registry.json` with their basis, not as literals in code, and in `docs/registry-reference.md`.
- A new or changed alert gets its row in `docs/alert-runbook.md`.
- Rule modules stay pure (no I/O); put fetching in the source/state modules.
- A behaviour change that departs from a plan decision is recorded in that plan's decision table.
- Package version is `riskdep/__init__.py` `__version__` (currently `0.1.0`); there is no `CHANGELOG.md` yet.
