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

**Read `docs/hackaton_instruction/GOAL.md` first:** it states the challenge this project answers (the DeFi Risk Dependency Challenge), what is expected, and how it is judged (dependency discovery 30 %, impact estimation 30 %, decision usefulness 25 %, working demo on real data 15 %). Weigh every change against it. The original brief is `docs/hackaton_instruction/Hackathon_DeFi-Risk-Dependency-Challenge_EN_v1.pdf` (one page, Belem Capital, EPFL Hackathon 2026): read it too, it holds what `GOAL.md` does not, such as the worked trade-off (a book in ten 10 % pockets, one affected, 11 % slippage to unwind: make stay-vs-exit explicit), the scope examples (oracle and feed-quality analysis, vaults deploying into an external venue such as a perp exchange, protocols concentrating a large share of on-chain TVL) and the exact criterion wording ("depth and correctness", "is the number defensible"). **Git-ignored**: the file is local only and its notice forbids copying it, so quote from it sparingly and never commit it.

`riskdep` is a Python CLI (`python3 -m riskdep`) for the risk of DeFi positions on Ethereum, centred on Morpho. It has five subcommands: `analyze` (batch STAY / REDUCE / EXIT report for a Pendle PT used as Morpho Blue collateral), `watch` (follow a Morpho Vault V2 block by block and alert a depositor), `watch --user` (find every Blue borrow and Vault V2 deposit of an address and monitor them together), `graph` (interactive dependency graph, with the sibling markets of the held ones and each oracle's class) and `shock` (apply a failure to a node of that graph and propagate it to every market, vault and depositor, by rules kept in `registry.json`). All data comes from public sources: the publicnode Ethereum RPC, the Morpho and Pendle APIs, DefiLlama, all keyless; Pharos and Nexus Mutual, keyless and optional (issuer grades, off-chain backing, common-mode groups; cover prices; `docs/risk-assessment/outside-providers.md`); KyberSwap, keyless (exit liquidity in vault incidents); Ethena's transparency API, keyless (USDe's backing venues); Sky's core read on-chain (USDS and DAI's backing); and Etherscan, whose key in `keys.ini` is optional (without it, an oracle's source verification reads "not checked", and an oracle input only its name would classify reads "not classified"). A React SPA in `web/` presents the same results in a browser.

## Key concepts

- **Design first.** Each mode was built from a plan in `plan/` (design, numbered decisions `D1…`, tracker, interview log). Module docstrings cite those decisions (e.g. `D21`, `D37`); read the matching plan row before changing behaviour it governs.
- **Pure rules, I/O at the edges.** `rules.py`, `borrower_rules.py` and `propagate.py` are pure functions (decoded events + state before/after → alerts); network access lives in `sources.py`, `vault.py`, `borrower.py`, `poller.py`, `crosscheck.py`.
- **One cached fetcher.** `sources.py` keys every request by a hash of (method, url, body) and stores it under `fixtures/snapshot/`, so a live run doubles as the offline demo snapshot. `RISKDEP_RPC_URL` changes where the main RPC's requests are sent, never the URL they are cached under. `--record` saves watch ranges under `fixtures/replay/<vault>/` or `fixtures/replay/user-<address>/`, and graphs under `fixtures/replay/graph-<target>/`; `--replay` re-runs them offline. A recording keeps the first answer to a request repeated in the same run, so the replay sees what the recorded run computed from.
- **One clock.** `clock.py` makes offline runs use `fixtures/snapshot/as_of.json` as "now", so the demo is reproducible on any later day. Never call `time.time()`/`datetime.now()` directly in analysis code.
- **Registry, not constants.** Facts, assumptions, priors and watch thresholds live in `riskdep/registry.json` (`watch` key for alert thresholds), each with a stated basis. So do the shock engine's propagation rules (`engine`): a new propagation behaviour is a rule first, and a new transmission function in `engine.py` only when no rule can express it.
- **Alert levels** are `info` / `warn` / `critical`; the trigger tables are in `README.md`.
- **Watch loop invariant:** discover, read state, poll, assess, alert, and save the cursor **last** (`out/watch-*.cursor`), so a restart resumes without skipping blocks. Polling runs 2 blocks behind the head every 12 s; deeper reorgs are not handled. A live batch with no event reads only what moves without one (`vault.read_light`, `borrower.read_prices`); any event, gap, undecoded log or refresh, and `watch.full_state_every_blocks`, force a full read (D61). Replays and `--blocks` runs always read in full.
- **Cross-checks never stop a run:** block hash against a second RPC (critical on mismatch), Morpho API against chain state (warn, 0.5 % tolerance); a check that cannot run prints "not checked". On a local fork (`RISKDEP_FORK=1`, which requires `RISKDEP_RPC_URL`) both read "not checked": the fork's blocks exist nowhere else (D180); a recording made there replays as one.
- **Free-RPC limits:** state is servable only ~64–90 blocks back (state-based rules on older ranges start at the oldest servable block); at most 9 addresses per `eth_getLogs` filter (the poller splits longer lists); recent ranges are intermittently refused as "archive" (the poller retries). Admin-surface filters are optional: a refusal is a warning, not a gap. Under a burst publicnode answers HTTP 429, and a local eRPC answers 200, both with a rate-limit error per batch item: `sources.Fetcher` waits and resends either (`_throttled`, up to 6 times) and never caches it. For long live runs, the optional local eRPC proxy (`erpc.yaml`, `docs/setup/erpc.md`) spreads the calls over six free endpoints; it must never list dRPC, the cross-check's independent node.

## File tree

```
riskdep/
  __main__.py         entry point → cli.main
  cli.py              argparse: analyze, watch, graph
  pipeline.py         one analyse, and one vault or book incident, end to end, shared by the CLI and the API (no I/O of its own beyond the fetchers)
  api/
    main.py           FastAPI assembly, CORS, lifespan, /api/health
    schemas.py        the published contract, mirrored by openapi.json
    artifacts.py      the only reader of out/, and the fetch lock
    routes/           one module per resource: graph, report, incident (books, incident, after), shock (graphs, targets, trace, sweep), backtest, alerts, dashboard (vault, market)
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
  exposure.py         worst-case exposure up to a Vault V2's caps: a market's limit, a group's under shared cap ids (pure)
  drain.py            drain threshold of each vault market: d*, the drainable amount, the Public Allocator
  scenario.py         incident mode: a known incident's impact, time to impact and verdict; alert impacts
  vault_incident.py   incident mode for a vault depositor: a collateral markdown (through the shock engine when the vault's graph is recorded), a borrower default, a drain by unbacked collateral, or a depeg of the vault's own asset (loan=)
  pharos.py           Pharos, keyless: issuer grades, off-chain backing, common-mode groups (optional)
  exit_liquidity.py   exit liquidity of a collateral, live from KyberSwap's aggregator (keyless): the route at the incident's size
  ethena.py           Ethena, keyless: USDe's backing by venue, the reserve fund, the yields; a venue's loss as a USDe markdown
  infinifi.py         infiniFi's loss waterfall (buffer, liUSD, siUSD, iUSD) and pending loss, read on-chain from siUSD
  upshift.py          Upshift's Tori vault behind etrUSD: off-chain assets, the daily NAV cap, the 7-day exit, the queue
  bridge.py           bridged collaterals: PST's CCIP lanes and rate limits, etrUSD's LayerZero peers; a forged mint's bound
  fx.py               fxSAVE's NAV components (fxUSD, USDC idle and lent), read on-chain from fxSP
  sky.py              Sky's backing read on-chain: debt by source, the peg module's USDC, surplus, debt auctions; a source's loss as a USDS markdown
  nexus.py            Nexus Mutual, keyless: cover prices as an outside probability next to the breakeven p* (optional)
  after.py            a vault after an incident: what has landed, what is still at risk (unrealised, pending), the verdict on that part only
  vault_book.py       a book of vaults (file or --vault flags) under one incident, added up in USD, with the exposure on venues not read
  notify.py           the notify command: posts the watch alerts at or above a level to a Telegram channel (TELEGRAM_BOT.md)
  exit_queue.py       a depositor's place in a run on a vault: recovery and loss by queue position
  roles.py            who holds each Vault V2 role: one key, a Safe n/m, a timelock, a contract; RoleHolder findings
  admin.py            admin surface of the watched markets: upgrades, owners, feeds, pauses, mints, oracle divergence
  # web dashboard
  dashboard.py        a Vault V2's market allocation and a market's borrowers by liquidating fall (Morpho API)
  # graph
  graph.py            dependency graph as JSON + Cytoscape.js HTML
  siblings.py         sibling markets: other Blue markets sharing a held market's collateral, underlying or price input
  oracle_class.py     oracle class, price-tracking or constant-price, and a constant-price one's kind, from structure and round history (pure + probe)
  feeds.py            feed quality: each feed's freshness against its own update rhythm (pure)
  tvl.py              TVL concentration of the graph's protocols, from DefiLlama (pure)
  backtest.py         a past incident replayed: the prediction against the Liquidate events (backtest subcommand)
  pendle_amm.py       a Pendle V2 pool rebuilt from its on-chain state at any block: Pendle's own pool math (pure + read)
  depth.py            discovery depth for a borrow position: the graph's layers in the PT report (pure)
  detect.py           detection → impact for a vault: an oracle fall's loss and verdict in the watches (pure)
  zama.py             Zama confidential vaults: the cShare pool, the batchers, a confidential depositor's two exits
  conditional.py      the conditional Monte Carlo of vault and book incidents: the loss of staying given the incident (pure)
  # shock
  engine.py           propagation engine (pure): effects, rule matching, transmissions, the Blue market model, the squeeze
  shock.py            the shock command: resolve shocks, run the engine on a built or replayed graph, report, sweep
  # analyze
  discover.py         position → numbers plus a typed layer graph
  priors.py           per-layer incident priors
  propagate.py        how a shock on one layer reaches the position (pure)
  simulate.py         Monte Carlo over layer incidents
  decide.py           STAY / REDUCE / EXIT verdict
  report.py           HTML + JSON report
tests/                pytest, all offline (snapshot + recorded replays)
  test_watch_rules.py, test_watch_replay.py, test_borrower.py, test_watch_user_replay.py,
  test_graph.py, test_siblings.py, test_oracle_class.py, test_engine.py, test_market_risk.py, test_exit_queue.py, test_drain.py, test_scenario.py, test_vault_incident.py, test_vault_book.py, test_pharos.py, test_breakeven.py, test_feeds.py, test_backtest.py, test_conditional.py, test_zama.py, test_detect.py, test_readme.py, test_depth.py, test_pendle_amm.py, test_exit_liquidity.py, test_concentration.py, test_ethena.py, test_sky.py, test_after.py, test_gapv2_fixes.py, test_admin_impact.py, test_issuer_stacks.py, test_bridge.py, test_gapv3.py, test_admin.py, test_decide.py, test_propagate.py, test_demo_snapshot.py, test_fixes.py, test_light_reads.py, test_api.py, test_dashboard.py, test_fork_replay.py, test_notify.py
scripts/fork/          the crisis demo on a local mainnet fork (anvil): demo.sh (all in one), start-fork.sh, crisis-belem.sh, alt-*.sh, lib.sh,
                      addresses.env, src/ (two demo contracts, not protocol code), tapes/ (vhs); see its README.md
pyproject.toml        project metadata, dependencies, ruff and pytest configuration
```

## Other important files

- `docs/hackaton_instruction/Hackathon_DeFi-Risk-Dependency-Challenge_EN_v1.pdf` — the original challenge brief (PDF, git-ignored, local only); the source of `GOAL.md`.
- `docs/hackaton_instruction/GOAL.md` — the challenge brief: what to build, what is expected, the judging criteria and their weights, and where the repository answers each.
- `docs/analysis/ARCHITECTURE.md` — how the system is built: modes, components and their imports, data sources and trust, data flow, state, testing, decision index.
- `README.md` — usage of every mode, alert trigger tables, limits.
- `docs/archive/ANALYSIS_CURRENT.md` — archived (superseded 2026-10-11): the 2026-10-10 assessment that read the brief as detect → impact → how fast → decide and turned the project to known-incident answers; its plan is built. The current state is `GOAL.md`'s criteria map and `docs/analysis/NEXT_STEP.md`.
- `docs/analysis/NEXT_STEP.md` — the next steps, in recommended order (phases A to D), with how each would be built and what it needs; it records what has been built and merges the earlier versions 1 and 2. Keep it current when a step is done.
- `docs/risk-assessment/outside-providers.md` — the outside risk providers and how each is used: Pharos and Nexus Mutual (both in use, keyless); the rules any outside provider follows. `docs/analysis/EXTERNAL_SOURCE.md` is the survey that chose them.
- `docs/analysis/PROVIDERS.md` — every external provider (RPC, APIs, CDNs): endpoints, queries, limits, trust model. Keep it current.
- `keys.example.ini` — template of the API keys and secrets (no values); the real `keys.ini` is git-ignored. `[alchemy]` (or `[rpc] url`) is an archive RPC, used only as a route by `backtest --record`: its URL embeds the key, so it is never cached, logged or printed.
- `erpc.yaml` — configuration of the optional local eRPC proxy (eRPC 0.3.0, six free upstreams, no key); `docs/setup/erpc.md` is the setup guide. Its upstream list is mirrored in `docs/analysis/PROVIDERS.md`.
- `docs/analysis/ANALYSIS_MONITORING.md` — design note: dependency graph, impact, monitoring, execution, and gaps of the current implementation (done / partial / missing).
- `plan/` — the fifty plans (`defi-risk-dependency`, `morpho-vault-v2-watcher`, `morpho-user-watcher`, `lenders-and-timelocks`, `market-borrowers`, `admin-surface`, `exit-queue`, `drain-threshold`, `sibling-markets`, `incident-mode`, `propagation-engine`, `vault-incident`, `vault-book`, `wrapped-collateral`, `borrower-concentration`, `pharos`, `one-number`, `breakeven`, `incident-api`, `judge-path`, `fork-demo`, `feed-quality`, `backtest`, `conditional`, `pt-channels`, `zama`, `mixed-book`, `detect`, `alerts-and-verdict`, `backtest-crash`, `depth`, `pool-move`, `oracle-kinds`, `stressed-exit`, `pendle-pool`, `exit-liquidity`, `shared-and-supply`, `venues`, `sky`, `value-at-risk`, `after`, `priors-k3-k4`, `priors-k5-k15-k17`, `cascade-and-liquidity`, `gapv2-fixes`, `admin-impact`, `issuer-stacks`, `bridges`, `gapv3`, and `web-graph-react-flow` for the SPA's graph).
- `examples/` — `rockawayx-ethereum.json`, the demo book of vaults and the template for any other (`analyze --book`); `rockawayx-ethereum-all.json`, the same with the five small vaults found later (all twelve Morpho Vault V2 of RockawayX on Ethereum, `docs/analysis/GAPV3.md`); `brief-ten-pockets.json`, the brief's own book of ten 1M pockets (`pocket` weighting, with `--exit-cost 0.11`); `brief-mixed-book.json`, the same with the brief's PT loop as a borrow pocket (`kind: borrow`); `brief-three-shapes.json`, the loop, the same PT held without a borrow (`kind: pt`) and a vault, side by side.
- `docs/` — the documentation, grouped; `docs/README.md` is the index:
  - `docs/model/` — how risk and impact are computed: `how-risk-is-computed.md`, `how-probabilities-are-computed.md` (where every probability comes from: hack base rates, oracle and market-event priors, the breakeven p\*, outside views), `monte-carlo.md` (how `analyze`'s simulation works), `scenarios-and-breakeven.md`, `vault-incident.md` (incident mode end to end: `analyze --vault` / `--book`, `POST /api/incident`), `vault-depositor-scenarios.md`, `shock-engine.md` (the shock engine and its rules), `shock-trace.md` (the propagation trace for a front end, example in `shock-trace-example.json`), `graph-propagation.md`, `zama-confidential-vaults.md` (what is computed for a Zama confidential vault, and what is not), `ethena.md` (the same for Ethena's USDe and sUSDe), `midas.md`, `fx-protocol.md` and `infinifi.md` (the same for Midas's mGLOeuro, f(x)'s fxSAVE and infiniFi's siUSD).
  - `docs/watch/` — detection and monitoring: `how-a-block-is-analysed.md`, `how-an-incident-is-detected.md` (each kind of incident: its signal, detector, threshold, timing and alert; OracleImpact; the early warnings; what is not detected), `drain-threshold.md`, `exit-queue.md`, `user-watcher-options.md`, `websocket-vs-polling.md`.
  - `docs/reference/` — look-up material: `alert-runbook.md` (what each alert means and what to do), `registry-reference.md` (every `registry.json` key), `glossary.md`.
  - `docs/setup/` — running it: `erpc.md` (the optional local RPC proxy), `telegram-botfather-commands.md`.
  - `docs/examples/` — `graph-example.html/.json`.
  - `docs/img/` — the mindmaps and diagrams, each `.png` next to its `.puml`.
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
  - `upschift/docs.upshift.finance-docs/` — Upshift documentation (the folder name is spelt so): its vaults (single- and multi-asset, accounting, atomic redemption, the risk-management framework and policy engine), curators, contracts and addresses, the REST API and SDK; the venue of the Tori Ecosystem Vault, whose share is etrUSD, collateral in two RockawayX vaults (`docs/analysis/GAPV3.md` §2). **Git-ignored**: it exists only in the local checkout, so read it there; a fresh clone does not have it.
  - `ember/learn.ember.so-docs/` — Ember Protocol documentation (tokenized multi-chain vaults: core concepts, vault managers, security, API); the venue of RockawayX's Y10K vault (`docs/analysis/GAPV3.md` §2). **Git-ignored**: it exists only in the local checkout, so read it there; a fresh clone does not have it.
  - `risk-assessment/` — documentation of the external risk providers reviewed in `docs/analysis/EXTERNAL_SOURCE.md` (what each offers, access, and the proposed weighted blend with `riskdep`'s own estimates):
    - `credora.network-docs-docs/` — Credora (PSL, probability of a loss of at least 1 % per year; rating methodologies, the Morpho implementation, the GraphQL API behind a whitelist).
    - `docs.nexusmutual.io-docs/` — Nexus Mutual (cover products and pricing, capacity, claims, the keyless `/v2/products` and `/v2/capacity` API); its cover prices are converted to yearly probabilities.
    - `pharos.watch-safety-scores-docs/` — Pharos (stablecoin safety grades and scores, the dependency graph and scenarios; keyless and supporter-key endpoints).
    **Git-ignored**: the three folders exist only in the local checkout, so read them there; a fresh clone does not have them.
  - `docs.zama.org-protocol-docs/` — Zama Protocol documentation (FHEVM confidential smart contracts: protocol and litepaper, Solidity guides, the relayer SDK, confidential tokens, the confidential swap and confidential vault apps, examples, changelog). **Git-ignored**: it exists only in the local checkout, so read it there; a fresh clone does not have it.
  - `sky/` — Sky (formerly Maker: USDS, sUSDS, DAI; the PSM, the core accounting, the surplus buffer), the issuer behind the USDS, sUSDS and DAI markets of the recorded graphs and the Spark vault of the brief's book:
    - `developers.skyeco.com-docs/` — Sky developer documentation (protocol, guides such as the LitePSM, deep dives such as the rate mechanism, security, the archived shutdown). **Git-ignored**: it exists only in the local checkout, so read it there; a fresh clone does not have it.
    - `usds` (`d65551db`), `spells-mainnet` (`0c57941f`), `dss-exec-lib` (`de6b715c`) — Sky sources: USDS and sUSDS, the executive spells that change Sky's parameters, and the library they are written with.
    - `dss` (`fa4f6630`), `dss-lite-psm` (`dbf00222`) — Sky's core (the Vat, the Vow, joins, the oracle security module) and the LitePSM, read by `sky.py`; `executive-votes` (`d9a57443`), the text of each executive vote (where the allocators' proxies are named); `sky-protocol-info` (`d7b2af9e`), the deployments of every module, the ChainLog's address among them.

  - `chainlink-ccip/` — Chainlink CCIP: `chainlink-ccip` (`d20496f3`), the contracts (`TokenPool`, `BurnMintTokenPool`, `RateLimiter`), read by `bridge.py`; `documentation` (`5dbdbb0f`), Chainlink's documentation site, CCIP under `src/content/ccip/`.
  - `layzerzero/` — LayerZero V2 (the folder name is spelt so): `layerzero-v2` (`9c741e7f`), the endpoint, the ULN message libraries and `OAppCore` (peers); `devtools` (`4973ba8b`), the OApp and OFT packages.

  The source repositories are git submodules (twenty-one, listed in `.gitmodules`), pinned at the commits above: after a clone, run `git submodule update --init`. To move a pin, check out the new commit inside the submodule and stage the submodule path.
- `fixtures/snapshot/` (analyze demo cache + `as_of.json`) and `fixtures/replay/` (recorded watch ranges, graphs, vault incidents, the Pharos snapshot under `pharos/`, the Nexus prices under `nexus/` and Ethena's backing under `ethena/`, Sky's core under `sky/`, infiniFi's under `infinifi/`, f(x)'s under `fx/`, the bridges under `bridge/`, Upshift's Tori vault under `upshift/`) — test fixtures; do not delete or regenerate casually. **Tracked in git, not ignored, on purpose:** every test runs offline from these cached responses, so CI and any fresh clone need them; a cache file present on one machine only makes a test pass locally and fail in CI. They used to live under `data/`, which `.gitignore` ignores, and new cache files were silently left out of commits (the exit-queue test failed in CI for that reason). So a new cached response (`--record`, `--live`, or a live fetch into these folders) is committed with the change that needs it: check `git status fixtures/`. They hold public responses only: API keys go on the request, never into a cache file (`sources.Fetcher`, `secret`).
- `out/` — run outputs (reports, alert `.jsonl`, cursors); git-ignored.
- `conftest.py` — puts the repo root on `sys.path` for tests.
- `openapi.json` — the committed front/back contract, generated from `riskdep/api/`; CI fails if it has drifted.
- `pyproject.toml` — project metadata, the runtime dependencies, the `dev` dependency group, and the ruff and pytest configuration.
- `uv.lock` — the exact resolved version of every dependency; committed, because this is an application and not a library.
- `.pre-commit-config.yaml` — the pre-commit hooks: `ruff check --fix`, then `ruff format`, then `prettier --write` over `web/` only. Prettier is pinned to the version in `web/pnpm-lock.yaml` and runs in pre-commit's own node environment, so the hook does not need `web/node_modules`; its `exclude` repeats `web/.prettierignore`, which prettier cannot find from the repo root.
- `.github/workflows/ci.yml` — CI on every push, three parallel jobs: `checks` (`ruff check` plus the `openapi.json` drift check) and `tests` (`pytest`) on Python 3.10, and `web` (`pnpm lint && pnpm build`) on Node 22 with pnpm 11.

## The web frontend (`web/`)

React 19 + TypeScript 5.9 + Vite 7, TanStack Router (routes) and Query (fetching), **Tailwind CSS v4 + shadcn/ui** for the interface, React Flow (`@xyflow/react`, laid out with dagre) for the graph, Recharts for the report charts. **pnpm**, not npm: `pnpm-lock.yaml` and `pnpm-workspace.yaml` are committed, and `allowBuilds: esbuild` in the workspace file is what lets esbuild run its install script. `web/.env` is committed on purpose — it holds the mock switch and no secret. Usage, the page-by-page tour and the `/api` contract are in `README.md`; what follows is what an agent needs before editing.

```
web/src/
  main.tsx            QueryClient (retry 1, no refetch on focus) + RouterProvider
  router.tsx          five routes, each a lazyRouteComponent; `/` is the vault, `/market/$marketId` a market
  index.css           the Tailwind entry: the raw palette, the @theme mapping, the base layer
  api/types.ts        hand-written shapes of the /api payloads
  api/client.ts       fetch wrappers, the USE_MOCKS switch, one method per endpoint
  api/hooks.ts        useHealth / useReport / useGraph / useAnalyze, with the query keys
  api/stream.ts       subscribeWatch: polls /api/alerts with a block cursor, or replays the fixtures when mocking
  components/         AppShell (shadcn `Sidebar`: nav with icons + provenance; top bar with the target selector) · GraphCanvas · GraphElements (the custom node and edge) · Stat · DetailsTable · States
  components/ui/      vendored shadcn primitives, stock (sidebar brings sheet, tooltip, skeleton and hooks/use-mobile.ts)
  lib/format.ts       usd / percent / num / shortHash / etherscanUrl…, all null-tolerant
  lib/utils.ts        re-exports `cn` from the `cn` package, where `components.json` tells `shadcn add` to import it
  lib/graph.ts        kind colours, shapes and icons, node amounts, dagre layout, flow reach, edge width, report-graph normalisation
  routes/             VaultPage (follows the top-bar selector) · MarketPage · GraphPage · ImpactPage (a shock trace, one view per tab) · WatchPage
  mocks/              report.json, graph.json, vaults.json, markets.json, shock-trace.json (a copy of docs/model/shock-trace-example.json), shock.json, backtests.json, alerts.ts
```

**Invariants.**

- **The types are read off real output, not generated.** `api/types.ts` was written from `out/report.json` and `out/graph.json`, which are git-ignored, so `src/mocks/` is the only committed copy. Change a payload in `report.py` or `graph.py` and both the type and the fixture must follow, or mock mode silently renders the old shape.
- **`inf`/`nan` arrive as `null`.** The report writer's `clean()` maps them, so a health factor with no debt or a risk multiple with no expected loss is `null`. Such fields are typed `number | null` and every formatter in `lib/format.ts` returns an em dash for null — keep that property when adding one.
- **Two graph shapes, one renderer.** `/api/graph` returns the six capitalised kinds of `graph.py`; the graph embedded in a report is a serialised networkx graph with lowercase kinds and `from`/`to` edges. `lib/graph.ts` maps the second onto the first, and that mapping is a judgement call documented in place — not something the backend states.
- **The node colours are duplicated from `riskdep/graph.py` into `lib/graph.ts`** (with the edge width curve), so the SPA and the CLI's standalone HTML read alike. A colour change touches both files. The shapes are not shared: the SPA draws by role (`nodeRole`: circle asset; near-square vault or pool, rounded for an address; hexagon for what holds no assets, smaller for a price feed than for its oracle — D64), the CLI keeps its Cytoscape shapes (D66). It lives in TypeScript and not in the Tailwind theme on purpose: there colour is *data*, keyed to the shape that repeats it, and not part of the interface palette.
- **`index.css` holds the raw palette; the Tailwind theme is a naming layer over it, never a second palette.** `--bg`, `--fg`, `--muted`, `--line` and `--edge` are a contract with two consumers that cannot read Tailwind: Recharts takes `var(--line)` strings that land in SVG attributes, and the graph's nodes, edges and arrowheads use `var(--bg)`, `var(--fg)` and `var(--edge)` in inline styles. Renaming one means updating `GraphElements` and `GraphCanvas` in the same commit. shadcn's own token names (`--color-background`, `--color-border`, `--color-card`…) are aliased onto the same values, so a vendored component that still says `bg-card` paints the one ground instead of introducing a surface.
- **The vendored shadcn components are stock** (`pnpm dlx shadcn add --overwrite` is safe), with two local edits: `TableRow` draws its hairline at `border-border/50`, and Prettier reformats them. The sidebar's colours are mapped onto the palette in `@theme` (`--color-sidebar*`), not the hsl values the CLI writes; the CLI's `tw-animate-css` import and `.dark` class variant are dropped (dark mode follows the system and the `data-theme` attribute), so `animate-*` classes are inert; `eslint.config.js` turns `react-hooks/purity` off for `components/ui/**` because the stock `SidebarMenuSkeleton` calls `Math.random` in a `useMemo`. The theme gives every control a light radius (`--radius: 0.5rem`, shadcn's scale), and the quiet surfaces (`muted`, `accent`, `secondary`) are the ground with 5–6 % ink. Colour is reserved for severity — `info` / `warn` / `critical` / `ok`, plus the graph's data palette — and is carried by a **word**, never by a number: no figure is ever coloured. Prose, labels **and numbers** use the system UI stack, numbers with `tabular-nums`; the `mono` utility is for identifiers only (addresses, hashes, market ids, event names).
- **Impact reads `POST /api/shock`:** `api.shockTrace()` posts the committed example (`EXAMPLE_SHOCK`) by default and returns `mocks/shock-trace.json` when mocking; refresh that file by copying `docs/model/shock-trace-example.json` whenever the test that keeps it current regenerates it. `mocks/shock.json` (graphs, targets, sweep of the example vault) and `mocks/backtests.json` are recorded from the API's offline answers, not hand-written. `POST /api/incident` and the backtests have no page yet.
- **Mocks are the default, including with no `.env`:** `USE_MOCKS` is `import.meta.env.VITE_USE_MOCKS !== 'false'`. Every endpoint added to `api/client.ts` needs its fixture branch in the same commit, or mock mode breaks on that page.
- **Two fixture alerts are invented.** The `critical` entries in `mocks/alerts.ts` are modelled on `docs/reference/alert-runbook.md` because no recorded run has one; the header of that file says so. Never cite their `data` keys as the real event payload.
- **SSE, not WebSocket:** named events `alert` and `tick`, one JSON object each. `min_level` is a server-side filter, so `WatchPage` restarts the stream by remounting on `key={minLevel}` rather than resetting state in an effect. The browser reconnects on its own; `onStatus` only reports the gap.
- **Routes are lazy because Recharts and React Flow are heavy; only Impact needs both.** A new heavy dependency belongs behind `lazyRouteComponent`, not in the shell.
- **`GraphCanvas` lays out once per mount.** dagre runs in the initial state, and the page remounts the canvas with `key` to re-lay out (on new data or Re-layout), which also drops the user's drags. Focus, kind filter and search are derived from props, never stored. Names and edge labels counter-scale with the zoom (`clamp(1/zoom, 1, 2.5)`, D65); the amount inside a node scales with it. React Flow's `base.css` only is imported, and its `<Controls>` are not used: zoom and fit are shadcn `Button`s over `useReactFlow()` in a `<Panel>`.

**Tooling.** TypeScript is strict with `noUnusedLocals`/`noUnusedParameters`, split into `tsconfig.app.json` (src) and `tsconfig.node.json` (vite config); eslint runs `recommendedTypeChecked` over both projects and makes `no-explicit-any` and `consistent-type-imports` errors, with `react-refresh/only-export-components` turned off for `src/components/ui/**` alone, because the generated primitives export their variants next to the component. Prettier is 100 columns, single quotes, trailing commas — **not** ruff's 120, and the two should not be unified; the generated fixtures are in `.prettierignore`. There are no frontend tests, so `pnpm lint && pnpm build` (the build type-checks with `tsc -b`) is the whole gate — the `web` CI job runs exactly that, and the pre-commit `prettier` hook formats `web/` before it gets there. Run both before handing work over.

## Dependencies (tested versions)

Python ≥ 3.10; CI runs the suite on 3.10, the floor `requires-python` in `pyproject.toml` declares. `uv.lock` is the source of truth for versions; it currently pins requests 2.34.2, numpy 2.5.3, networkx 3.7, eth-utils 6.0.0, eth-abi 6.0.0, eth-hash 0.8.0 with pycryptodome 3.24.0, and in the `dev` group pytest 9.1.1 and ruff 0.17.0. `eth-hash[pycryptodome]` is a runtime dependency in its own right: `eth-abi`/`eth-utils` pull `eth-hash` in without a keccak backend, and `abi.py` needs one to compute event signatures — without the extra, `pytest` fails at collection with `ImportError: None of these hashing backends are installed`. The HTML outputs load Mermaid (report) and Cytoscape.js (graph) from a CDN.

## Common commands

```bash
uv sync
uv run pytest -q tests                                 # 415 tests, offline
uv run python -m riskdep analyze --demo                # cached snapshot, no network → out/report.html/.json
uv run python -m riskdep watch --replay                # re-run the recorded vault range offline
uv run python -m riskdep watch --blocks 1000 --record  # live range, saved for --replay
uv run python -m riskdep watch --user <address>        # every Morpho position of an address, live
uv run python -m riskdep graph --example               # out/graph.html + out/graph.json
uv run python -m riskdep graph --vault 0xE0181090c22579B6A217f1522cbf8c9f1F0C1965 --replay  # recorded RockawayX graph, siblings and oracle classes, offline
uv run python -m riskdep shock --vault 0xE0181090c22579B6A217f1522cbf8c9f1F0C1965 --replay --shock "Ojo PT:reads-low:10%"  # a failure propagated, offline
uv run ruff format . && uv run ruff check .            # format and lint, 120 columns
~/.local/bin/erpc erpc.yaml                            # optional local RPC proxy (docs/setup/erpc.md), in its own terminal
export RISKDEP_RPC_URL=http://127.0.0.1:4000/main/evm/1  # route live runs through it; unset to go direct
uv run uvicorn riskdep.api:app --reload                # the HTTP API for web/, docs at /docs
uv run python -m riskdep notify                        # post watch alerts to Telegram (keys.ini [alerts]), next to watch
scripts/fork/demo.sh --short                           # crisis demo on a mainnet fork, one command, ~2 min (--record: asciinema; --stop)
scripts/fork/start-fork.sh 26165572                    # or step by step: an anvil fork (scripts/fork/README.md)
RISKDEP_RPC_URL=http://127.0.0.1:8545 RISKDEP_FORK=1 uv run python -m riskdep watch --vault 0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec --step 1
scripts/fork/crisis-belem.sh                           # the Belem crisis, act by act, in another terminal
uv run python -m riskdep watch --vault 0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec --replay --record-as fork-belem  # the same, offline
```

```bash
cd web && pnpm install                                 # pnpm, not npm
pnpm dev                                               # http://localhost:5173, on the fixtures
pnpm lint && pnpm build                                # eslint + prettier, then tsc -b + vite build
```

## Conventions

- Tests must stay offline: a new network call needs a cached snapshot or a recorded replay behind it.
- New thresholds or assumptions go in `registry.json` with their basis, not as literals in code, and in `docs/reference/registry-reference.md`.
- A new or changed alert gets its row in `docs/reference/alert-runbook.md`.
- Any change that adds, removes or replaces a data provider, endpoint, query or browser script (RPC, API, CDN) updates `docs/analysis/PROVIDERS.md` in the same commit.
- Keys and secrets go only in `keys.ini` (git-ignored, `chmod 600`), never in code, docs or committed files; a new key gets its name, with no value, in `keys.example.ini`. Do not use `.env` files for this project.
- Rule modules stay pure (no I/O); put fetching in the source/state modules.
- `api/` routes and validates, nothing else: a new rule or threshold goes in the rule modules and `registry.json`, never in a route. Change a payload and you must regenerate `openapi.json` in the same commit.
- The API never hosts the watcher. `watch` is its own process writing `out/watch-*.jsonl`; the API reads it with a block cursor.
- A behaviour change that departs from a plan decision is recorded in that plan's decision table.
- Leave format and lint to ruff, at 120 columns, in pre-commit and in CI; never mix a style-only commit with a behaviour change.
- `uv.lock` is committed: change a dependency with `uv add` / `uv lock`, never by editing the lock by hand — CI runs `uv sync --locked` and fails if the lock has drifted from `pyproject.toml`.
- Never hand-edit `web/src/mocks/report.json`, `graph.json`, `vaults.json` or `markets.json`: regenerate them with `analyze --demo`, `graph --example` and `python -m riskdep.dashboard` with every Vault V2 of the fixture graph (offline, from the snapshot) and copy the files out of `out/`.
- Package version lives in `pyproject.toml` and must stay in step with `riskdep/__init__.py` `__version__` (currently `0.1.0`); nothing in the code reads `__version__`, only the docs cite it. There is no `CHANGELOG.md` yet.
