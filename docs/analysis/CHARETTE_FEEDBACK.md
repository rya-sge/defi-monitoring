# Feedback on charrette, from its use on defi-monitoring

defi-monitoring (riskdep) was built in about three days, 9–12 October 2026, by five people and their agents, with charrette's plan loop: 52 plans in `plan/`, about 245 numbered decisions, 141 commits. This file lists what worked, what could be done better, and how, each point backed by what the repository shows. It is feedback on the method and the skills, not on the project.

## The evidence

| Measure | Value | Where |
|---|---|---|
| Plans | 52, 4,106 lines | `plan/*.plan.md` |
| Plans whose decisions were taken with no interview ("the agent's defaults") | 45 of 52 | the plans' status lines |
| Plans run with `verify off` | 49 of 50 that state a mandate | the `mandate:` line |
| Plans executed inline, by the agent of the conversation | 49 of 49 | the `mandate:` line |
| Plans leaving out §4 Flows and §5 State | 27 | the `Left out` line |
| Plans that started from a board (`brainstorm`) | 2 | |
| Plans whose tracker has no slice marked done | 3 | the web plans |
| Approval wording | one line each, e.g. "Yes go for it" | the status lines |
| Backlog documents outside the plans | `NEXT_STEP.md`, `GAP.md`, `GAPV2.md`, `GAPV3.md`, `IMPROVEMENT.md`, `ANALYSIS_CURRENT.md` (archived), `ANALYSIS_MONITORING.md` | `docs/analysis/`, root |
| Authors | 5 | `git log` |
| Decision-number collisions between developers | at least one (D150–D153), worked around by jumping to D180 | the fork-demo plan |

## What worked, to keep

- **Numbered decisions cited in the code.** Module docstrings cite `D96`, `D183`, `D240`; a reader goes from a line of code to the decision and its basis. This was the most useful habit of the project.
- **The tracker's state node.** "next / blocked / parked" let a new session, or another developer, pick up where the last one stopped.
- **"Read against" in every plan.** Each plan names the brief's criteria (`GOAL.md`: discovery 30 %, impact 30 %…), which kept the work aimed at how it would be judged.
- **Hard rules in the plan header.** "Keyless", "offline tests", "the agent never commits" were restated per plan and held.
- **Plans small enough to approve in one reading.** Most were one or two slices, which matches charrette's "iterate the loop" principle.

## What could be done better, and how

Ordered by how much each cost the project.

### 1. Decisions were mostly not interviewed

**Observed.** 45 of 52 plans say "No interview: the decisions below are the agent's defaults", then were approved in one line. Some of those defaults were wrong and found later, by writing documentation rather than by review:

- a Midas markdown applied at once, although the feed cannot fall below −10 % without a 48 h upgrade (GAPV2 G11);
- a siUSD markdown that did not move its oracle while the same report said it did (G19);
- an f(x) NAV oracle classified "published" from its name (G12).

**Why it matters.** The interview is where a person catches a wrong assumption cheaply. Skipped, the assumption ships, and the person's one-line "Yes" approves a table they did not read.

**How.**
- In `write-plan`: when the agent fills decisions with its own defaults, mark each `agent's default` in the decision table and show them first in the approval message, as a short list ("6 decisions are my defaults: …; confirm or change"), instead of the whole plan.
- In `interview`: a "fast" mode of three questions at most, for the decisions tagged `contract` (the ones that change an output), so skipping it is not the only cheap option.
- Let `pr-review` or `validate-delivery` re-surface the defaults after execution: "these defaults shipped; any to revisit?"

### 2. Decision numbers collide between developers

**Observed.** Decisions are numbered globally (D1…D245) across plans. With five developers working in parallel, two plans took the same numbers (D150–D153); one side renumbered to D180. Merge conflicts were frequent enough that `CLAUDE.md` carries a note saying they are expected.

**How.**
- Namespace decision ids by plan: `vault-incident#D3`, rendered short inside the plan and fully qualified when cited from code or another document. No global counter, nothing to collide.
- Or, if global numbers are kept, reserve ranges per developer or per branch in the roadmap.
- `write-conventions` could add a check: no decision id defined twice across `plan/`.

### 3. The backlog lives in six documents, not in the roadmap

**Observed.** What to do next was written, in turn, in `NEXT_STEP.md`, `GAP.md`, `IMPROVEMENT.md`, `GAPV2.md`, `GAPV3.md` and `ANALYSIS_CURRENT.md` (later archived), each with its own ids (A1…, K1…, G1…, steps 1…) and its own priority order. The `roadmap` skill was not used. A gap appears in several of them (Vault V1, other chains, issuer priors), with different wording and sizes.

**Why it matters.** Nobody can answer "what is next" from one place, and a gap closed in one document stays open in another.

**How.**
- Use `roadmap` as the single backlog: each gap document feeds slots into it, and the gap document keeps the analysis while the roadmap keeps the order and the status.
- Give charrette a "findings" or "gap" document type that `roadmap` can import from: id, criterion, size, status, the plan that closed it.
- When a plan delivers, `execute-plan` marks the matching slot done, so `GAPV2.md`'s status and the roadmap cannot drift.

### 4. Trackers go stale once the increment is delivered

**Observed.** Plan trackers keep a "next:" that points at work done later in other plans, e.g. the detect plan's state still says "next: FeedStale and the Zama batcher alerts", both since delivered. Three web plans show no slice done although the pages exist.

**How.**
- A close-out step in `execute-plan`: when the last slice is done, the state node becomes `closed` with the commit, and "next" is replaced by a pointer to the roadmap.
- A project index generated from the trackers (status per plan: open, closed, superseded), so a reader does not open 52 files to know which are live.

### 5. Verification was off, and the demo failed in front of the person

**Observed.** 49 plans ran with `verify off`; `validate-delivery` was used once. The front end has no tests. Problems were found live, by the person:

- the fork demo posted nothing to Telegram, because `notify` is a separate process and reads another folder;
- a second demo run would also post nothing, because `notify`'s saved offsets survive the demo's reset of its alert files;
- a demo suspended with Ctrl-Z kept the fork's port and blocked the next run.

**How.**
- Default `verify` on for plans whose deliverable a person runs (a demo script, a page, a CLI command meant for presentation), off only for internal modules covered by tests.
- A verification skill template for demo scripts (`verification-skill-create`): rehearse with side effects disabled, run twice in a row, stop with Ctrl-C and with Ctrl-Z, check every external output (a message, a file, a port).
- `validate-delivery` with the person before a demo is presented, not after.

### 6. The plan template is too heavy for small increments

**Observed.** 27 plans leave out §4 Flows and §5 State, saying so in their header; many plans are one slice of a few hours. 52 plans in three days is one plan every two hours of work.

**How.**
- A "small" plan shape in `write-plan`: purpose, decisions, one slice, tests; Flows and State only when the plan adds a process or a stored state.
- Batch related small increments into one plan with several slices (the Midas, f(x) and infiniFi fixes of GAPV2 were done as one plan, `gapv2-fixes`, which worked well).

### 7. Where plans live is undecided

**Observed.** charrette's own convention keeps plans, boards and reports out of the repository, in the data home through `aiview path`. This project commits its 52 plans to `plan/`, lists them in `CLAUDE.md`, and indexes their decisions in `ARCHITECTURE.md`. `aiview` was not used.

**Why it matters.** Both choices are defensible: in-repo plans are reviewed with the code and cited from it; data-home plans do not clutter the tree. But charrette's skills assume the second, and the project silently did the first.

**How.**
- State the choice in charrette: an `in-repo` mode for `write-plan` (path, how the tracker is rendered without aiview, how plans are indexed), next to the data-home default.
- If plans stay in the repository, let `aiview` open a repository folder as a source, so the rendered tracker and diagrams are available without moving files.

### 8. Duplicated agent guides drift

**Observed.** `CLAUDE.md` and `AGENTS.md` must be identical (294 lines each) and were kept so by copying every edit by hand. Counts and lists inside them (tests, routes, plans, docs) went stale between edits and were fixed one at a time.

**How.**
- One file and a symbolic link, or one generated from the other.
- Sections that list things (plans, routes, test count) generated by a script rather than written, with a check in CI.
- A `write-conventions` rule: a convention that is a mechanical copy is enforced by a tool, not by a note.

### 9. No review between developers

**Observed.** Five authors committed to `main`; `pr-review` was not used. Overlaps (decision numbers, the same backlog item worked twice, docs updated in one file and not the other) surfaced as merge conflicts or later in the documentation.

**How.**
- Short-lived branches per plan and `pr-review` on merge, even for small plans; its "recurring findings" would have caught the repeated doc-drift findings.
- For parallel work, `swarm`'s board shows who is on which slot and avoids two people taking the same gap.

### 10. Design questions that deserved a board went straight to plans

**Observed.** Two plans started from a board. The probability model, the shock engine's rules and the incident semantics (what `token=` means for a vault share, see G19) were decided inside plans, in decision tables.

**How.** For a question with several defensible answers, `brainstorm` or `whiteboard-defense` before `write-plan`: the board records the alternatives considered, and the plan records only the choice. The G19 ambiguity, market fall or booked loss, is the kind of question a board makes visible early.

### 11. Code and documentation can contradict each other

**Observed.** The siUSD incident printed "oracle × 1.000" and "lands at once" in the same report; the whitepaper and model documents carried figures that changed when the code changed (six figures had to be re-run after the GAPV2 fixes).

**How.**
- A verification step that runs every documented example end to end and compares the figures quoted in the documents with the output (the project already has `test_readme.py` for the README; extend the pattern to `docs/`).
- In `technical-writing`: figures in documents come with the command and block that produced them, in a comment, so they can be re-run mechanically.

## Priorities

| Order | Change | Skill | Cost |
|---|---|---|---|
| 1 | Surface the agent's default decisions at approval; a short interview mode | `write-plan`, `interview` | small |
| 2 | Namespaced decision ids | `write-plan`, `write-conventions` | small |
| 3 | One backlog: gap documents feed `roadmap` | `roadmap` | medium |
| 4 | Verification on by default for demos and pages; a demo verification template | `execute-plan`, `verification-skill-create`, `validate-delivery` | medium |
| 5 | Close-out of trackers and a generated plan index | `execute-plan` | small |
| 6 | A small-plan shape | `write-plan` | small |
| 7 | An explicit in-repo mode for plans | `write-plan`, `aiview` | medium |
| 8 | Generated agent-guide sections, one guide file | `write-conventions` | small |
| 9 | Branches and `pr-review` for multi-developer work; `swarm` for parallel slots | `pr-review`, `swarm` | process |
| 10 | Boards for questions with several answers | `brainstorm`, `whiteboard-defense` | process |
| 11 | Documented figures re-run by a check | `technical-writing`, verification | medium |
