# Vault page for a curator

Drafted on 2026-10-11. The vault page (`web/src/routes/VaultPage.tsx`, `GET /api/vault/{address}`, `riskdep/dashboard.py`) shows what a Vault V2 holds. A curator placing client money needs it to answer four questions at a glance: **what can hurt me, can I get out, how fast, what changed**. This plan turns the five priorities of that review into page elements, in build order. Each is a figure where the curator looks first, not a paragraph (the frontend's no-explanatory-prose rule): explanations go in hover tooltips.

## Target layout

```
Vault name                                                    [changes strip: 2 pending · 1 in 7d]
┌ Total assets ────────┐  ┌ figures ─────────────────────────┐
│ $124.5M              │  │ Your exit now          $8.2M  7% │
│                      │  │ Bad debt at −10%       $0.00     │
│                      │  │ Bad debt at −30%       $1.4M  1% │
│                      │  │ Constant-price oracles  3 of 5   │
└──────────────────────┘  └──────────────────────────────────┘
[ Exit ] [ Liquidations ] [ Vault loss ]                    ← tabs, Exit first
Market allocation bar
Markets table: market · allocation · of vault · of market · oracle · cushion · top borrower · utilization · LLTV
```

## Items

| # | Element | Visual | Data | Backend work | Size |
|---|---|---|---|---|---|
| 1a | Bad debt, not liquidated debt | The two "Liquidated at −5 % / −10 %" rows become "Bad debt at −10 % / −30 %", in USD and % of assets, red when non-zero. The Liquidations chart gains a bad-debt line on the same x axis as the liquidated-debt bars, so the gap between "liquidated" and "lost" shows. | `vault.liquidations` + `lif`, the formula `VaultLossChart` already uses; move it into `lib/` and reuse it in both places. | None. | S |
| 1b | Vault's share of each market | New "Of market" column with a thin inline bar; ≥ `lender_concentration_warn` (0.5) gets a warn-coloured "main lender" tag: the vault is the liquidity of last resort and takes most of the loss. | `share_of_market`, already in the payload. | None. | XS |
| 1c | Cushion against history | "Cushion" column: a bar from 0 to 1 with a marker at 1 − LLTV (the fall the oracle can take before collateral ≤ debt) and a second marker at the collateral's worst 1-year fall. Red when the worst fall is past the cushion. Tooltip states both numbers. | `lltv`, `collateral_drawdown_1y`, both in the payload. | None. | S |
| 2 | Oracle class per market | "Oracle" column: a dot + word, "tracks price" (fg) or "constant price" (warn), "not classified" muted. A stale feed adds a small red ring on the dot; tooltip lists each input and its freshness ("updated 3h ago, every 1h"). One figure row: "Constant-price oracles 3 of 5", weighted by allocation in the tooltip. | `oracle_class`, `freshness`, `stale` on the Pool and Feed nodes of the recorded graph (`graph.py`, `fixtures/replay/graph-<vault>/`). | `dashboard.vault` joins them by market id when a graph recording exists for the vault; `null` otherwise. Add `oracle_class: str \| null`, `feeds: [{label, freshness, stale}]` to `VaultMarket`; regenerate `openapi.json` and `mocks/vaults.json`. | M |
| 3 | Changes strip | Top-right of the header: one compact pill ("2 pending · 1 in 7d"), critical-coloured if any pending change is executable within 24 h. Clicking opens a popover timeline: past changes (cap raised, market added, owner changed, oracle upgraded) as dated rows, pending timelocks as rows with a countdown ("executable in 1d 4h") and a link to the transaction on Etherscan. | Admin and timelock alerts from the vault's watch log (`out/watch-*.jsonl`, through `GET /api/alerts?target=<vault>`), filtered to their kinds; pending timelocks from `vault.py`'s state. | A `pending` list in the vault payload needs an on-chain read: serve it from the last watch cursor's state rather than from the dashboard's API-only path. First version: alerts only, no countdown. | M |
| 4 | Your exit | New first tab "Exit". Top: one stacked horizontal bar of the vault's assets: idle · withdrawable from markets · reachable through the Public Allocator · locked, each labelled in USD on hover. Below: the exit-queue curve, x = assets leaving ahead of you (0 → total), y = % of your deposit recovered at par, with a vertical marker at your queue position and the vault's top holders as ticks on the x axis. The header row "Your exit now" replaces "Liquidity". | `drain.py` (free liquidity, `PaConfig`, `pa_inflow`), `exit_queue.py` (`Liquidity`, `exit_at`, `queue_points`, `holders`). | A new `exit` object on the vault payload (`plain`, `forced`, `pa`, `locked`, `holders[]`, `points[]`), computed from a recorded watch or graph state; the depositor comes from the selected book or `?depositor=`. Without one, the bar shows the vault-level split and the curve is hidden. | L |
| 5 | Borrower concentration | "Top borrower" column: share of the market's debt as a thin bar plus %, warn at `concentration_top1_warn` (0.5) or below `concentration_min_borrowers` (5) borrowers; tooltip gives top 3 share and borrower count. | Each market's borrowers, already fetched by `dashboard.liquidations` (one Morpho query per market). | Compute `top1_share`, `top3_share`, `borrowers` in `dashboard._markets`/`vault` from that list; thresholds read from `registry.json`'s existing keys. Check the query's page size covers every borrower, or say "top of the first N". | S |
| 6 | Dependencies tab and points of failure | Tab "Dependencies" (mounted only when opened, so the large graph fixture loads on demand): the vault's own graph with twins grouped (D206), beside a "Points of failure" list: every non-pool node downstream of a market the vault supplies, with the share of the vault's supply that relies on it (`pointsOfFailure`), top 8; a row focuses the node's flow. | `GET /api/graph?vault=`. | None. | M |
| 7 | Shock from an asset | Picking an Asset node offers −10 / −30 / −50 %; the vault incident (`token=<symbol>:<fall>`, 30 days) gives the verdict, vault loss, position loss and markets hit, rings the hit markets in critical and lights their flow; a link opens the incident page. Mock mode answers only the recorded scenarios (PST, fxSAVE −30 %) and shows the fixture error otherwise. | `POST /api/incident`. | None. | S |
| 8 | Risk rings | Graph rings: critical for a stale feed and a shocked market; warn for a vault market with a constant-price oracle or a top borrower ≥ `concentration_top1_warn`, and for an asset or issuer graded D or F by Pharos; the picked node in the foreground colour. Legend under the graph. | Graph node details (`stale`, `oracle_class`, `pharos_grade`), the vault payload's `top1_share`. | None. | S |
| 9 | Figures, revised | The figures next to Total assets: your exit now (% of the position), run coverage (exit ÷ three largest other holders, critical below 1×), distance to bad debt (uniform fall where bad debt passes 1 % of assets), loss at historical worst (each collateral at its own 1-year drawdown, `badDebtBy`), share behind constant-price oracles, share concentrated (top borrower or main lender). Labels truncate with a tooltip. Replaces the bad debt at −10 / −30 % rows. | The vault payload. | None. | S |

## Build order

1. Items 1a–1c and 5: frontend plus one small `dashboard.py` change, no new source. Gives the curator the "what can hurt me" view.
2. Item 2: needs the graph join; vaults without a recording show "not classified", never a guess.
3. Item 4: the largest payoff for a fund, and the largest change (on-chain state in the dashboard path).
4. Item 3: first from alerts alone, countdown once pending timelocks are served.

## Rules for all items

- Colour carries risk only: warn and critical for the thresholds already in `registry.json`, the chart tokens for series, nothing decorative.
- Every new figure has a hover tooltip stating its basis in one line; no helper paragraphs.
- A figure that could not be computed reads "—" or "not classified", never 0.
- Every payload change regenerates `openapi.json` and the mocks from `python -m riskdep.dashboard` (never by hand), in the same commit.

## Deferred (need new data)

Depositor concentration beyond the exit curve's ticks; share price, flows and utilization history (7 / 30 days); collateral DEX depth at size; net APY by market (the cost side of leaving); Pharos grade and Nexus cover price per collateral (available, but belong with item 2's tooltip once it exists).
