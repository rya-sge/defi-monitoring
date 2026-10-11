# Frontend incident decisions

Revised on 2026-10-11: the user wants an active incident alert, not a scenario simulator. The view answers what was detected, what is exposed, and what to do now. The real recorded example supplies impact; event age and severity are explicitly demo metadata until a detector supplies them.

## Decisions

| Choice | Implementation |
|---|---|
| Page | `/incident`, lazy loaded; Impact keeps its labelled example trace. |
| Event | Fixed PST −30% impact loads automatically; no form, presets, horizon control or run button. Occurred 19 minutes ago, detected 16 minutes ago, labelled demo. |
| Scope | One top-bar selector containing the seven recorded vaults; no book selector or watched-user options. |
| Weighting | Vault exposure/loss and depositor position loss remain separate; the monitored depositor identifier is visible. |
| Results | Entire rows select the vault by click, Enter or Space, synchronising the selector and URL; the selected row has a distinct background. The selected vault’s figures use a compact two-column label/value table; actions and charts sit in one column in a sidebar occupying one third of the table section; the table occupies two thirds. On narrow screens the sidebar stacks below the table. Sort EXIT, REDUCE, STAY, then estimated loss. |
| Decision | Backend verdict maps to withdrawal/hold instructions and amounts; stay/exit loss and yield forgone are charted across the full sidebar width, with hidden axes and labels on the bars, including zero-width bars (custom rectangle shape preserves their labels without changing the plotted values). Position-loss bars use a compact 136 px chart with 36 px bars, a dark berry fill and white labels without a text outline. No p* gauge: the incident is already assumed to have happened. No hit-markets table. No inline explanations: the selected vault's figures (vault exposure, estimated vault loss, position loss, avoidable loss, withdrawable, pool usage) sit in one label-to-figure table, labels truncated with a hover tooltip; propagation is a minimal graph (shocked collateral → hit markets → vault → position) with hover tooltips, and other markets reached expand into the sibling markets, each linking to its market page. |
| Outside view | Remove Nexus prose. Policy ownership and coverage are unknown; the current card says so. Future structured fields: provider/product, held policy, applicable event, annual premium range, available capacity, claim route. No incident-specific coverage conclusion inferred from cover price. |
| Combined Impact | One event page with Actions and Propagation. Reuse the Impact graph/path components only with a trace computed for this exact incident and vault/block. The Ojo example cannot explain a PST markdown. Engine waves are iterations, not elapsed minutes. |
| Mocks | 24 exact-request responses: PST −30%, fxSAVE −30%, largest borrower of all markets with 50% collateral recovery; 30 days; example book and each of its seven vaults. Unsupported requests return an actionable fixture error. |
| Provenance | Export through the real offline incident route and validate the published schema. Regenerate with `uv run python scripts/export_incident_fixtures.py`. |

## Validation

Required: frontend lint/build. Existing fixture responses remain unchanged. Visual review through `pnpm dev`: Huma selected by default, all row cells clickable, Enter/Space works, selector/URL/detail remain synchronised, Confidential RWA holds because leaving saves nothing, the hit-markets table is absent, and the panel stacks below the table on mobile.

## Deferred

Actual detection feed and occurrence/detection timestamps; same-event trace endpoint; structured Nexus coverage data and held policy; live position ownership. The existing Impact route keeps its separate labelled example until a matching trace is available.
