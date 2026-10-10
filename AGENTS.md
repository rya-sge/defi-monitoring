# defi-monitoring — agent guide

> **Note — keep in sync:** `AGENTS.md` and `CLAUDE.md` must always be **identical**. Any edit to one must be applied verbatim to the other.

> **Note — never commit:** an assistant must **never** run `git commit`, `git push`, `git tag`, `git merge`, `git rebase` or `git reset --hard` in this repository. Staging (`git add`) and read-only inspection (`git status`, `git diff`, `git log`) are fine; creating or moving history is the author's alone.
>
> Two reasons, one practical and one editorial. Commits here are GPG-signed (`commit.gpgsign = true`), and gpg cannot read a passphrase from a non-interactive session: the attempt fails with `gpg: cannot open '/dev/tty'` and leaves a half-staged index behind. And the author reviews the diff before it becomes history — a commit made for them removes the one checkpoint where a wrong change is still cheap to drop.
>
> So end a piece of work by leaving the tree ready and handing over the **one-line commit message** the note below asks for. If several commits are wanted — a style-only commit split from a behaviour commit, say — hand over the staging and commit commands for each, in order, and let the author run them.

> **Note — no browser automation:** do not work on this project through Claude for Chrome, or any other tool that drives a browser on your behalf. Check the UI the ordinary way: `pnpm dev` and look at it.

> **Note — merge conflicts are expected:** several developers work on this project in parallel, so a merge with `main` can conflict even when nothing is wrong: two people edited the same line for different reasons. Treat each side as an intentional change, not an error to discard.
>
> To resolve one: read both sides and the commits behind them (`git log --oneline <branch> -- <file>`), check which one matches the current code (the code wins over prose), and keep both intents when they are compatible rather than picking a side. If the two intents contradict and the code does not decide, ask the author. Remove every marker, `git add` the file, and hand over the merge commit as the note above says.

> **Note — be concise:** keep every summary, report and explanation short and direct. Lead with the result, state what changed and what it costs, stop. No preamble, no restating the request, no recap of steps the reader just watched, no closing paragraph that says the same thing again. Prose only where a table or a one-line command would not do.

> **Note — take the simplest route:** solve the problem that was asked with the plainest thing that works. No speculative abstraction, no configuration knob nobody requested, no extra layer in case the requirement grows — if it grows, add it then. Do not deliberate at length over a choice whose options are equivalent in practice: pick one, say which in a clause, move on. A long chain of reasoning about a small change is a sign the change is being made too big.
>
> The same applies to the code itself: write the fewest lines that read clearly. Reuse what the module already has instead of adding a parallel helper, delete rather than comment out, and prefer one direct expression to a staircase of intermediates. Concise is not cryptic — a name that explains itself beats a comment explaining a short one.

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

`riskdep` is a Python CLI (`python3 -m riskdep`) for the risk of DeFi positions on Ethereum, centred on Morpho. It has four subcommands: `analyze` (batch STAY / REDUCE / EXIT report for a Pendle PT used as Morpho Blue collateral), `watch` (follow a Morpho Vault V2 block by block and alert a depositor), `watch --user` (find every Blue borrow and Vault V2 deposit of an address and monitor them together) and `graph` (interactive dependency graph). All data comes from keyless public sources: the publicnode Ethereum RPC, the Morpho and Pendle APIs, DefiLlama. A React SPA in `web/` presents the same results in a browser.

## Key concepts

- **Design first.** Each mode was built from a plan in `plan/` (design, numbered decisions `D1…`, tracker, interview log). Module docstrings cite those decisions (e.g. `D21`, `D37`); read the matching plan row before changing behaviour it governs.
- **Pure rules, I/O at the edges.** `rules.py`, `borrower_rules.py` and `propagate.py` are pure functions (decoded events + state before/after → alerts); network access lives in `sources.py`, `vault.py`, `borrower.py`, `poller.py`, `crosscheck.py`.
- **One cached fetcher.** `sources.py` keys every request by a hash of (method, url, body) and stores it under `data/snapshot/`, so a live run doubles as the offline demo snapshot. `RISKDEP_RPC_URL` changes where the main RPC's requests are sent, never the URL they are cached under. `--record` saves watch ranges under `data/replay/<vault>/` or `data/replay/user-<address>/`; `--replay` re-runs them offline.
- **One clock.** `clock.py` makes offline runs use `data/snapshot/as_of.json` as "now", so the demo is reproducible on any later day. Never call `time.time()`/`datetime.now()` directly in analysis code.
- **Registry, not constants.** Facts, assumptions, priors and watch thresholds live in `riskdep/registry.json` (`watch` key for alert thresholds), each with a stated basis.
- **Alert levels** are `info` / `warn` / `critical`; the trigger tables are in `README.md`.
- **Watch loop invariant:** discover, read state, poll, assess, alert, and save the cursor **last** (`out/watch-*.cursor`), so a restart resumes without skipping blocks. Polling runs 2 blocks behind the head every 12 s; deeper reorgs are not handled. A live batch with no event reads only what moves without one (`vault.read_light`, `borrower.read_prices`); any event, gap, undecoded log or refresh, and `watch.full_state_every_blocks`, force a full read (D61). Replays and `--blocks` runs always read in full.
- **Cross-checks never stop a run:** block hash against a second RPC (critical on mismatch), Morpho API against chain state (warn, 0.5 % tolerance); a check that cannot run prints "not checked".
- **Free-RPC limits:** state is servable only ~64–90 blocks back (state-based rules on older ranges start at the oldest servable block); at most 9 addresses per `eth_getLogs` filter (the poller splits longer lists); recent ranges are intermittently refused as "archive" (the poller retries). Admin-surface filters are optional: a refusal is a warning, not a gap.

## File tree

```
riskdep/
  __main__.py         entry point → cli.main
  cli.py              argparse: analyze, watch, graph
  pipeline.py         one analyse end to end, shared by the CLI and the API (no I/O of its own)
  api/
    main.py           FastAPI assembly, CORS, lifespan, /api/health
    schemas.py        the published contract, mirrored by openapi.json
    artifacts.py      the only reader of out/, and the fetch lock
    routes/           one module per resource: graph, report, alerts
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
  test_graph.py, test_market_risk.py, test_admin.py, test_decide.py, test_propagate.py, test_demo_snapshot.py, test_fixes.py, test_light_reads.py
pyproject.toml        project metadata, dependencies, ruff and pytest configuration
```

## Other important files

- `ARCHITECTURE.md` — how the system is built: modes, components and their imports, data sources and trust, data flow, state, testing, decision index.
- `README.md` — usage of every mode, alert trigger tables, limits.
- `NEXT_STEP.md` — the recommended next steps, with what each needs (decisions, sources, credentials, infrastructure).
- `PROVIDERS.md` — every external provider (RPC, APIs, CDNs): endpoints, queries, limits, trust model. Keep it current.
- `keys.example.ini` — template of the API keys and secrets (no values); the real `keys.ini` is git-ignored.
- `ANALYSIS_MONITORING.md` — design note: dependency graph, impact, monitoring, execution, and gaps of the current implementation (done / partial / missing).
- `plan/` — the six plans (`defi-risk-dependency`, `morpho-vault-v2-watcher`, `morpho-user-watcher`, `lenders-and-timelocks`, `market-borrowers`, `admin-surface`).
- `docs/` — `alert-runbook.md` (what each alert means and what to do), `glossary.md`, `registry-reference.md` (every `registry.json` key), `how-risk-is-computed.md`, `scenarios-and-breakeven.md`, `vault-depositor-scenarios.md`, `graph-propagation.md`, `how-a-block-is-analysed.md`, `websocket-vs-polling.md`, `user-watcher-options.md`, `graph-example.html/.json`.
- `docs/external/` — third-party references, read-only; check behaviour against them before changing a rule:
  - `docs.morpho.org-developers-docs/` — Morpho developer docs (contracts, Bundles, addresses, Midnight); `tests/test_watch_replay.py` checks the event selectors in `abi.py` against its `contracts/` pages.
  - `morpho/lib/morpho-blue` (`8e26ca6a`) and `morpho/lib/vault-v2` (`d992cb84`) — Morpho Blue and Vault V2 sources: events, liquidation and shares maths, authorisation, adapters, timelocks, gates.
  - `pendle/docs.pendle.finance-pendle-v2-dev-docs/` — Pendle V2 developer docs (contracts, oracles, integration, backend API).
  - `pendle/lib/pendle-core-v2-public` (`87685c89`), `pendle/lib/Pendle-SY-Public` (`73676d93`), `pendle/lib/external-integration` (`1694fea0`) — Pendle core (PT/YT, markets, router, oracles), SY wrappers, integration examples.
  - `docs.etherscan.io-api-reference-docs/` — Etherscan API V2 reference (`getsourcecode`, `getabi`, …); the key is in `keys.ini`.

  The five source repositories are git submodules (`.gitmodules`), pinned at the commits above: after a clone, run `git submodule update --init`. To move a pin, check out the new commit inside the submodule and stage the submodule path.
- `data/snapshot/` (analyze demo cache + `as_of.json`) and `data/replay/` (recorded watch ranges) — test fixtures; do not delete or regenerate casually.
- `out/` — run outputs (reports, alert `.jsonl`, cursors); git-ignored.
- `conftest.py` — puts the repo root on `sys.path` for tests.
- `openapi.json` — the committed front/back contract, generated from `riskdep/api/`; CI fails if it has drifted.
- `pyproject.toml` — project metadata, the runtime dependencies, the `dev` dependency group, and the ruff and pytest configuration.
- `uv.lock` — the exact resolved version of every dependency; committed, because this is an application and not a library.
- `.pre-commit-config.yaml` — the pre-commit hooks: `ruff check --fix`, then `ruff format`, then `prettier --write` over `web/` only. Prettier is pinned to the version in `web/pnpm-lock.yaml` and runs in pre-commit's own node environment, so the hook does not need `web/node_modules`; its `exclude` repeats `web/.prettierignore`, which prettier cannot find from the repo root.
- `.github/workflows/ci.yml` — CI on every push, three parallel jobs: `checks` (`ruff check` plus the `openapi.json` drift check) and `tests` (`pytest`) on Python 3.10, and `web` (`pnpm lint && pnpm build`) on Node 22 with pnpm 11.

## The web frontend (`web/`)

React 19 + TypeScript 5.9 + Vite 7, TanStack Router (routes) and Query (fetching), **Tailwind CSS v4 + shadcn/ui** for the interface, Cytoscape for the graph, Recharts for the report charts. **pnpm**, not npm: `pnpm-lock.yaml` and `pnpm-workspace.yaml` are committed, and `allowBuilds: esbuild` in the workspace file is what lets esbuild run its install script. `web/.env` is committed on purpose — it holds the mock switch and no secret. Usage, the page-by-page tour and the `/api` contract are in `README.md`; what follows is what an agent needs before editing.

```
web/src/
  main.tsx            QueryClient (retry 1, no refetch on focus) + RouterProvider
  router.tsx          three routes, each a lazyRouteComponent
  index.css           the Tailwind entry: the raw palette, the @theme mapping, the base layer
  api/types.ts        hand-written shapes of the /api payloads
  api/client.ts       fetch wrappers, the USE_MOCKS switch, one method per endpoint
  api/hooks.ts        useHealth / useReport / useGraph / useAnalyze, with the query keys
  api/stream.ts       subscribeWatch: polls /api/alerts with a block cursor, or replays the fixtures when mocking
  components/         AppShell (header, nav, provenance) · GraphCanvas · Stat · DetailsTable · States
  components/ui/      vendored shadcn primitives, restyled to the minimal world
  lib/format.ts       usd / percent / num / shortHash / etherscanUrl…, all null-tolerant
  lib/graph.ts        kind colours and shapes, edge width, report-graph normalisation
  routes/             PositionPage · GraphPage · WatchPage
  mocks/              report.json, graph.json, alerts.ts
```

**Invariants.**

- **The types are read off real output, not generated.** `api/types.ts` was written from `out/report.json` and `out/graph.json`, which are git-ignored, so `src/mocks/` is the only committed copy. Change a payload in `report.py` or `graph.py` and both the type and the fixture must follow, or mock mode silently renders the old shape.
- **`inf`/`nan` arrive as `null`.** The report writer's `clean()` maps them, so a health factor with no debt or a risk multiple with no expected loss is `null`. Such fields are typed `number | null` and every formatter in `lib/format.ts` returns an em dash for null — keep that property when adding one.
- **Two graph shapes, one renderer.** `/api/graph` returns the six capitalised kinds of `graph.py`; the graph embedded in a report is a serialised networkx graph with lowercase kinds and `from`/`to` edges. `lib/graph.ts` maps the second onto the first, and that mapping is a judgement call documented in place — not something the backend states.
- **The node palette is duplicated from `riskdep/graph.py` into `lib/graph.ts`** (node colours and shapes, edge width curve), so the SPA and the CLI's standalone HTML look like one tool. A colour change touches both files. It lives in TypeScript and not in the Tailwind theme on purpose: there colour is *data*, keyed to the shape that repeats it, and not part of the interface palette.
- **`index.css` holds the raw palette; the Tailwind theme is a naming layer over it, never a second palette.** `--bg`, `--fg`, `--muted`, `--line` and `--edge` are a contract with two consumers that cannot read Tailwind: Recharts takes `var(--line)` strings that land in SVG attributes, and `GraphCanvas` resolves those five names with `getComputedStyle` because Cytoscape needs resolved colours. Renaming one means updating `GraphCanvas` in the same commit. shadcn's own token names (`--color-background`, `--color-border`, `--color-card`…) are aliased onto the same values, so a vendored component that still says `bg-card` paints the one ground instead of introducing a surface.
- **The interface is deliberately minimal and the vendored shadcn components are restyled to match**: one ground, no cards or panels, radius `0` across every scale, no shadows, no motion. Colour is reserved for severity — `info` / `warn` / `critical` / `ok`, plus the graph's data palette — and the level is always a word too, so severity survives without colour. Prose and labels use the system UI stack, every machine value (addresses, hashes, amounts, block numbers) uses the `mono` utility: the two faces are a semantic split, not a per-call-site decision. Re-running `pnpm dlx shadcn add --overwrite` restores the stock radii, shadows and focus rings; strip them again.
- **Mocks are the default, including with no `.env`:** `USE_MOCKS` is `import.meta.env.VITE_USE_MOCKS !== 'false'`. Every endpoint added to `api/client.ts` needs its fixture branch in the same commit, or mock mode breaks on that page.
- **Two fixture alerts are invented.** The `critical` entries in `mocks/alerts.ts` are modelled on `docs/alert-runbook.md` because no recorded run has one; the header of that file says so. Never cite their `data` keys as the real event payload.
- **SSE, not WebSocket:** named events `alert` and `tick`, one JSON object each. `min_level` is a server-side filter, so `WatchPage` restarts the stream by remounting on `key={minLevel}` rather than resetting state in an effect. The browser reconnects on its own; `onStatus` only reports the gap.
- **Routes are lazy because Recharts and Cytoscape are heavy and no page needs both.** A new heavy dependency belongs behind `lazyRouteComponent`, not in the shell.
- **`GraphCanvas` is the one imperative component.** Cytoscape is built in an effect, `onSelect` is held in a ref so the tap handlers bind once, and the CSS tokens are read with `getComputedStyle` at mount — so a runtime theme switch would need a re-init, which is why `data-theme` has no toggle yet.

**Tooling.** TypeScript is strict with `noUnusedLocals`/`noUnusedParameters`, split into `tsconfig.app.json` (src) and `tsconfig.node.json` (vite config); eslint runs `recommendedTypeChecked` over both projects and makes `no-explicit-any` and `consistent-type-imports` errors, with `react-refresh/only-export-components` turned off for `src/components/ui/**` alone, because the generated primitives export their variants next to the component. Prettier is 100 columns, single quotes, trailing commas — **not** ruff's 120, and the two should not be unified; the generated fixtures are in `.prettierignore`. There are no frontend tests, so `pnpm lint && pnpm build` (the build type-checks with `tsc -b`) is the whole gate — the `web` CI job runs exactly that, and the pre-commit `prettier` hook formats `web/` before it gets there. Run both before handing work over.

## Dependencies (tested versions)

Python ≥ 3.10; CI runs the suite on 3.10, the floor `requires-python` in `pyproject.toml` declares. `uv.lock` is the source of truth for versions; it currently pins requests 2.34.2, numpy 2.5.3, networkx 3.7, eth-utils 6.0.0, eth-abi 6.0.0, eth-hash 0.8.0 with pycryptodome 3.24.0, and in the `dev` group pytest 9.1.1 and ruff 0.17.0. `eth-hash[pycryptodome]` is a runtime dependency in its own right: `eth-abi`/`eth-utils` pull `eth-hash` in without a keccak backend, and `abi.py` needs one to compute event signatures — without the extra, `pytest` fails at collection with `ImportError: None of these hashing backends are installed`. The HTML outputs load Mermaid (report) and Cytoscape.js (graph) from a CDN.

## Common commands

```bash
uv sync
uv run pytest -q tests                                 # 126 tests, offline
uv run python -m riskdep analyze --demo                # cached snapshot, no network → out/report.html/.json
uv run python -m riskdep watch --replay                # re-run the recorded vault range offline
uv run python -m riskdep watch --blocks 1000 --record  # live range, saved for --replay
uv run python -m riskdep watch --user <address>        # every Morpho position of an address, live
uv run python -m riskdep graph --example               # out/graph.html + out/graph.json
uv run ruff format . && uv run ruff check .            # format and lint, 120 columns
uv run uvicorn riskdep.api:app --reload                # the HTTP API for web/, docs at /docs
```

```bash
cd web && pnpm install                                 # pnpm, not npm
pnpm dev                                               # http://localhost:5173, on the fixtures
pnpm lint && pnpm build                                # eslint + prettier, then tsc -b + vite build
```

## Conventions

- Tests must stay offline: a new network call needs a cached snapshot or a recorded replay behind it.
- New thresholds or assumptions go in `registry.json` with their basis, not as literals in code, and in `docs/registry-reference.md`.
- A new or changed alert gets its row in `docs/alert-runbook.md`.
- Any change that adds, removes or replaces a data provider, endpoint, query or browser script (RPC, API, CDN) updates `PROVIDERS.md` in the same commit.
- Keys and secrets go only in `keys.ini` (git-ignored, `chmod 600`), never in code, docs or committed files; a new key gets its name, with no value, in `keys.example.ini`. Do not use `.env` files for this project.
- Rule modules stay pure (no I/O); put fetching in the source/state modules.
- `api/` routes and validates, nothing else: a new rule or threshold goes in the rule modules and `registry.json`, never in a route. Change a payload and you must regenerate `openapi.json` in the same commit.
- The API never hosts the watcher. `watch` is its own process writing `out/watch-*.jsonl`; the API reads it with a block cursor.
- A behaviour change that departs from a plan decision is recorded in that plan's decision table.
- Leave format and lint to ruff, at 120 columns, in pre-commit and in CI; never mix a style-only commit with a behaviour change.
- `uv.lock` is committed: change a dependency with `uv add` / `uv lock`, never by editing the lock by hand — CI runs `uv sync --locked` and fails if the lock has drifted from `pyproject.toml`.
- Never hand-edit `web/src/mocks/report.json` or `graph.json`: regenerate them with `analyze --demo` and `graph --example` and copy the files out of `out/`.
- Package version lives in `pyproject.toml` and must stay in step with `riskdep/__init__.py` `__version__` (currently `0.1.0`); nothing in the code reads `__version__`, only the docs cite it. There is no `CHANGELOG.md` yet.
