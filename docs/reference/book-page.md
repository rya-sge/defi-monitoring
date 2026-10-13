# The Book page

**Question it answers:** *under this scenario, which pocket of my book do I act on first, and what does acting cost compared with not acting?*

It is the web app's home page, `/`: [belem.fuca.ch](https://belem.fuca.ch/), or `http://localhost:5173/` after `pnpm dev`. Code: `web/src/routes/BookPage.tsx`. The numbers come from the incident mode, `POST /api/incident` (`riskdep/pipeline.py`, `riskdep/vault_book.py`, `riskdep/conditional.py`), which is what `analyze --book … --shock … --conditional` runs on the command line. How that is computed in detail is in `docs/model/vault-incident.md` (§10 for the conditional distribution, §11 for books).

A **book** is a set of positions held together: here, Morpho Vault V2s (and, in one example, a Morpho borrow). A **scenario** is an incident that has happened: a collateral marked down, a borrower defaulting. The page answers the brief's question for the whole book at once: how much does the incident cost, which pockets are hit, and for each one, is leaving worth what it costs?

## The two selectors

**Book** (top right): the books in `examples/`, served by `GET /api/books`.

| Book | What it holds |
|---|---|
| RockawayX, Morpho Vault V2 on Ethereum (default) | 7 real vaults (RockawayX, Huma, Belem RWA EURCV), each counted at its full size: a curator's view |
| The brief's book | ten 1M USD pockets, one Vault V2 each: the brief's worked example |
| The brief's book, mixed | nine vault pockets and the brief's PT loop on Morpho, 1M each |

**Scenario:** the four incidents the public site has recorded answers for.

| Scenario | Shock | Meaning |
|---|---|---|
| PST −30 % | `token=PST:0.3` | the PST collateral's price falls 30 % |
| fxSAVE −30 % | `token=fxSAVE:0.3` | the fxSAVE collateral's price falls 30 % |
| Largest borrower defaults, 50 % recovered | `borrower=all:0.5:1` | in every market, the largest borrower stops repaying; their collateral is recovered at half its value |
| Binance loses 50 % of USDe backing | `venue=Binance:0.5` | Binance fails, taking half of Ethena's backing held there; it reaches the book as a USDe markdown |

The horizon is fixed at 30 days. Other scenarios work in the Scenario lab with the local API (`VITE_USE_MOCKS=false`); the public site only has these four.

## Reading the page

### Book totals

| Figure | Meaning |
|---|---|
| **Book loss** | What the incident costs the book, in USD, at the size given (no probability) |
| Book value | What the book is worth |
| Exposure | The money in the markets the incident hits |
| Breakeven p\* over 30 d | Total cost of leaving the hit pockets ÷ total loss that leaving avoids. Leaving pays if you think the incident's probability over 30 days is above this. Its yearly equivalent is shown underneath |

### Stay or leave, given the incident

Shown when the scenario has a size that can vary (token and venue shocks; not borrower defaults). The incident has happened, but it can get worse or recover, and liquidators may or may not step in. The model simulates 10,000 paths: in 30 % of them the fall partly recovers, in 70 % it holds or deepens, and each vault may have no liquidator depending on how deep its exit route is.

| Figure | Meaning |
|---|---|
| Stay, mean loss | Average loss if you stay, with the 95 % and 99 % worst cases underneath |
| Leave, mean cost | Average cost if you leave first: what is still lost, plus the certain cost of leaving |
| Staying is worse | Share of the paths where staying costs more than leaving. Shown in amber at 50 % or more |
| No liquidator | Share of the paths where nobody liquidates the bad positions |

### Act first on

One row per pocket, in the order to act: **Exit** first, then **Reduce**, then **Stay**. Within each, the lowest p\* first (where leaving buys the most per dollar it costs), then the largest loss.

| Column | Meaning |
|---|---|
| Pocket | The vault (or borrow position) |
| Action | **Exit** (red), **Reduce** (amber), **Stay** (green), or **Unaffected** (grey) when the incident doesn't reach it. Hover it for the reason in one clause, e.g. "leaving pays above a 6.6 % chance over 30 days" or "leaving costs 2,495 USD, more than the 1,801 it saves" |
| Exposure | The pocket's money in the markets the incident hits |
| Loss if stay | The pocket's loss if it stays (the vault's whole loss in the RockawayX book) |
| Exit cost | The certain cost of leaving now: the yield given up over the horizon, or an unwind cost. The page sets no flat exit cost; `analyze --book … --exit-cost 0.11` gives the brief's 11 % |
| Saved by exit | How much less is lost by leaving first rather than staying |
| p\* | Exit cost ÷ saved by exit. When outside views exist (Nexus Mutual cover prices, Pharos grades), the value is underlined: hover it to compare |
| Buttons | Open the vault page; open the same scenario in the Scenario lab, focused on this pocket |

A dash means the vault's asset has no USD price.

**Two kinds of depositor.** In the RockawayX book, Exposure and Loss if stay are the **whole vault's**: what the curator sees. Exit cost, Saved by exit and p\* are for **one depositor**, by default the vault's largest holder. Only depositors ahead of the others in the exit queue avoid the loss by leaving, so Saved by exit is much smaller than Loss if stay. In the brief's books, each pocket is one depositor holding its stated amount, at the front of the queue, so all the columns are in that pocket's terms.

## Example: the public site, RockawayX book

The book is worth 99.1M USD.

**PST −30 %** (the default):

| | |
|---|---|
| Book loss | 5.2M on 34.7M exposed |
| Book p\* | 12.9 % over 30 days (81 % a year) |
| Stay, mean loss | 1.29M (p95 3.73M, p99 4.89M) |
| Leave, mean cost | 1.16M |
| Staying is worse | 78.9 % of 10,000 paths |
| No liquidator | 43.5 % |

| Pocket | Action | Exposure | Loss if stay | Exit cost | Saved by exit | p\* |
|---|---|---|---|---|---|---|
| RockawayX Confidential RWA USDC | Exit | 21.9M | 3.27M | 1,938 | 29,194 | 7 % |
| Huma USDC Main | Exit | 12.8M | 1.92M | 21,703 | 153,963 | 14 % |
| the five others | Unaffected | — | — | — | — | — |

Read it as: PST sits in two of the seven vaults. Leave the Confidential RWA vault first: leaving costs under 2,000 USD in yield and avoids about 29,000. It pays if the chance of the markdown is above 6.6 % over 30 days. Huma comes second.

**The other scenarios** on the same book:

- **fxSAVE −30 %:** 1.81M loss, one pocket to exit (RockawayX f(x) Protocol Ecosystem, p\* 8 %). RockawayX USDC Yield is hit (2.4M exposed) but stays: no bad debt reaches it.
- **Largest borrower defaults:** 12.8M loss, every vault hit. Six exit, led by RockawayX USDC Yield (p\* 5 %). Belem RWA EURCV stays: leaving costs 2,495 USD and saves only 1,801.
- **Binance −50 %:** no loss. The book holds no USDe, so every pocket is Unaffected. This is a correct answer, not a gap.

## Limits

- **The public site is a recording.** It shows the answers saved in `web/src/mocks/incidents.json`: the three books × the four scenarios, over 30 days. It doesn't follow the chain. The local app with `VITE_USE_MOCKS=false` computes them through the API.
- **The scenario is given, not predicted.** p\* says how likely the incident must be for leaving to pay; the page doesn't estimate that probability. The outside views in the p\* tooltip are the only probabilities shown.
- **The conditional figures rest on stated judgements.** The recovery share, the depth of the fall and the chance of no liquidator are set in `registry.json` `conditional`, with their basis. Calibrate them before relying on the 95 % and 99 % worst cases.
- **USD prices:** each vault's asset is priced through DefiLlama. When no price is available, 1 is assumed and the value is shown as a dash.
