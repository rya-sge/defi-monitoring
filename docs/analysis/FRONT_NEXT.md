# Front end — what to build next (2026-10-11)

What the merge of `main` at `944e877` (PR #17) makes possible in `web/`, ordered by the brief's judging weights (`docs/hackaton_instruction/GOAL.md`).

Implementation: `/incident` is now an active-alert demo, with one vault selector, fully clickable vault rows, actions and charts in a right-hand panel. The PST −30% impact comes from the recorded RockawayX example; occurrence/detection ages are labelled demo metadata. The scenario form, hit-markets table, explanatory prose, p* gauge and Nexus prose are removed. Impact and Incident should become one event view: decisions first, propagation underneath, using the same incident/block. Nexus should supply an actionable coverage card from structured data, not a probability comparison. See `plan/2026-10-11-front-incident.plan.md`.

## What `main` brought

| Commit | Change |
|---|---|
| `4ae73a0` | Vault and book incidents run through the shock engine on recorded graphs: `analyze` and `shock` give one number, with the squeeze and sibling contagion. |
| `065fe52` | Breakeven probability **p\***: the incident probability over the horizon above which leaving now pays, from the yield given up; the book says which vault to act on first (lowest p\*). Nexus Mutual cover prices as a keyless outside view. |
| `e49cc3a` | `POST /api/incident` (a vault, an ad hoc list of vaults, an inline book or an example book) and `GET /api/books`. |

Already in from the previous merge: Pharos grades and common-mode groups, the book of vaults, the borrower-concentration alert, wrapped collateral, the no-liquidator branch.

Example, offline: `analyze --book examples/rockawayx-ethereum.json --shock token=PST:0.30` — the book loses 5.2M of 99M (5.24 %) in 2 of 7 vaults; Huma is EXIT (p\* 14 % over 30 days, 84 %/yr); Confidential RWA is STAY (leaving first saves nothing: 18.6M of its 26M is stuck); contagion outside the book: 4.5M PYUSD lost on PST/PYUSD.

## What `/api/incident` returns

- **Book** (`BookIncident`): headline, value / exposure / loss in USD, the book's p\*, notes, one `VaultLine` per vault (value, exposure, loss, verdict, p\*, exit cost, saved).
- **Vault** (`VaultIncident`): stay vs exit — `loss_if_stay`, `can_leave_now`, `stuck`, `loss_if_exit_first`, `exit_cost`, `apy`, `p_star`, `p_star_year` — the verdict and its `reason`, `sibling_losses`, `common_mode`, `outside` (Nexus), notes.
- **Hit market** (`MarketHit`): drop, liquidatable debt, bad debt, vault share and loss, `oracle_class`, `timing` (how fast it lands, in words), `exit_route` (none / thin / deep), `no_liquidator_shortfall`, `top1_share` / `top3_share`, Pharos `grade`, the engine's `engine` line.

## What to build, in order

1. **Incident page — the decision simulator** (decision usefulness, 25 %).
   - Input: a book (`GET /api/books`) or the vault of the top-bar selector; a shock builder — a collateral of that vault and a fall (slider), or a borrower default and its recovery; the horizon.
   - Output: the book's headline, then the vaults table sorted by p\* (exposure, loss, loss %, p\*/yr, verdict, saved).
2. **Decision card per vault** (a row of that table, opened).
   - One bar chart: loss if I stay · loss if I exit first · exit cost — the brief's stay-vs-exit trade-off made explicit.
   - A bar: can leave now vs stuck.
   - The verdict's `reason`, verbatim.
3. **Breakeven gauge.** Horizon p\* first, with p\*/yr on a 0–100 % scale as a secondary view. Nexus explanations appear separately: a cover price is not an incident probability, and protocol cover may refer to a different event. A numeric comparison needs structured outside fields; outside figures never determine the verdict.
4. **Hit-markets table** (impact estimation, 30 %): drop, bad debt, vault loss, oracle class, `timing`, top1/top3 concentration, exit route, Pharos grade; the sibling markets reached below it. `timing` and the oracle class answer "how fast".
5. **Vault page on the engine.** Replace the "Vault loss" tab (every collateral falling together, an approximation) with the engine's loss as one chosen collateral falls (one `POST /api/incident` per point); Pharos grade and oracle class as columns of the markets table.
6. **Impact page on real data.** It shows the committed example trace: no endpoint serves a shock trace yet. Needs a `shock` route in the backend.

## Constraints

- Offline, `/api/incident` answers only for recorded vaults (the RockawayX book, `0xd6d4…`); any other needs `live=true`, tens of seconds of RPC. Mock mode needs recorded responses as fixtures, like `vaults.json`.
- Items 1–4 need no backend change when Nexus is displayed as prose; a numeric Nexus marker needs structured outside fields. Item 5 needs one call per point (or a sweep route), item 6 a new route.
