# Nexus Mutual in riskdep: how it is used and what it changes

Nexus Mutual sells on-chain cover against protocol exploits and depegs. `riskdep` reads its public prices and turns them into an **outside probability**, printed next to the breakeven probability p\* of a vault or book incident. It is a reference for the reader: **it changes no number the tool computes and never enters a verdict** (plan `2026-10-11-breakeven`, D145–D146).

- [1. Where it appears](#1-where-it-appears)
- [2. Data flow](#2-data-flow)
- [3. From a price to a probability](#3-from-a-price-to-a-probability)
- [4. What it is compared with: p\*](#4-what-it-is-compared-with-p)
- [5. Worked example](#5-worked-example)
- [6. Impact on the probability, and its limits](#6-impact-on-the-probability-and-its-limits)
- [7. Maintenance](#7-maintenance)

## 1. Where it appears

| Entry point | Output |
|---|---|
| `analyze --vault <addr> --shock token=<collateral>:<fall>` | an `outside view:` line under the breakeven line |
| `analyze --book <file> --shock …` | the same line for each vault of the book with a mapped hit |
| `POST /api/incident` | `outside: list[str]` on each vault incident (`riskdep/api/schemas.py`) |

Not used by `analyze` on a Pendle PT, `watch`, `graph` or `shock`.

## 2. Data flow

```
api.nexusmutual.io/v2/products ─┐
api.nexusmutual.io/v2/capacity ─┴─ nexus.load ── pipeline.nexus_prices ── vault_incident.run(nexus=…)
                                                                              │
                     registry.json nexus.products ── nexus.covers ── nexus.implied ── nexus.outside_line
```

1. **Fetch** (`riskdep/nexus.py:load`): two keyless GET requests. `/products` is cut down to `{id, name, type}`, and `/capacity` to `{id, min, max, usdc}`: the yearly price range, as a fraction of the amount covered, and the capacity left in USDC (asset 6).
2. **Cache**: `pipeline._outside_fetcher("nexus", mode)` saves the responses under `fixtures/replay/nexus/`. Runs are offline by default, `record`/`refresh` read the API again and save the answer, and `live` reads it without saving. If the API cannot be read, `load` returns `None` and the line is left out; the run still completes.
3. **Map** (`nexus.covers`, pure): the tokens it looks up are the collateral of every hit market plus every token that collateral wraps. Each one is looked up in `registry.json` → `nexus.products`. Each product is kept once, and only if Nexus quotes a non-zero price for it now.
4. **Convert** (`nexus.implied`, pure): see §3.
5. **Print** (`nexus.outside_line`): price, capacity, implied range, and what the cover does **not** pay on.

Mapped today (`registry.json`, see `docs/reference/registry-reference.md#nexus`):

| Token | Product (id) | Kind | Yearly price (2026-10-11) |
|---|---|---|---|
| trUSD, strUSD, etrUSD | Tori Finance (446) | protocol | 2.33 % |
| fxSAVE | f(x) Protocol (137) | protocol | 1.8–8.2 % |
| fxUSD | fxUSD depeg (311) | depeg | 1.5 % |
| iUSD, siUSD | infiniFi (308) | protocol | 1.9–2.8 % |
| mGLOeuro | Midas (356) | protocol | 1.48 %, little capacity |

## 3. From a price to a probability

A cover price is the expected payout plus a loading for capital cost and margin:

```
price = loading × P(covered event per year) × severity
⇒ P = price ÷ (loading × severity)
```

- **severity**: the shock's fall for a token markdown (`token=fxSAVE:0.30` gives 0.30), or 1 − recovery for a borrower default. When several shocks apply, the largest is used.
- **loading**: unobservable, so it is bracketed by `registry.json` `nexus.loading` = [2, 5]. With a loading of 3, the depeg frequencies Nexus implies for USDe and USDS match the tool's own (`docs/analysis/EXTERNAL_SOURCE.md` §7.5).
- **range**: low = min price ÷ (5 × severity), high = max price ÷ (2 × severity), capped at 1.

The range combines the price spread with the loading bracket, so it is wide by construction: the loading bracket alone makes it span a factor of 2.5.

## 4. What it is compared with: p\*

p\* is the tool's own number (`vault_incident.breakeven`, D142–D143): the probability of the incident, over the horizon, above which leaving now pays.

```
cost of leaving = par × APY × days / 365     (yield given up; or par × --exit-cost)
saving          = loss if you stay − loss if you leave
p*              = cost / saving               (over --horizon days, default 30)
p*/yr           = 1 − (1 − p*)^(365 / days)
```

The tool prints the two side by side and **never compares them**. The reader makes the comparison:

- Nexus-implied range **well below** p\*/yr: by the market's view, staying is cheaper than leaving.
- Range **above** p\*/yr: the market prices the covered event as likely enough that leaving would pay.
- Range **straddling** p\*/yr: no conclusion. The range is too wide, or the covered event too narrow (§6).

## 5. Worked example

The f(x) Protocol Ecosystem vault under a 30 % markdown of fxSAVE, offline:

```bash
uv run python -m riskdep analyze --vault 0x2cA22cb25558fa2018ecb1CE4eD8AF92Ee7ea423 --shock token=fxSAVE:0.30
```

```
verdict given the incident: EXIT: withdraw the 2,500,571 that can leave now, before the bad debt is written off: your loss falls from 215,276 to 0; …
if the incident is not certain: leaving now forgoes 17,042 USDC of yield over 30 days (8.29%/yr); it pays if the incident's probability over 30 days is above 7.92% (63.3%/yr)
outside view: Nexus f(x) Protocol cover 1.82%–8.20%/yr, capacity 2,539,669 USDC: implies 1.2%–13.7%/yr for an exploit of the protocol at this severity; it pays on that, not on an issuer's markdown or a borrower's default
```

| Step | Value |
|---|---|
| p\* | 17,042 / 215,276 = 7.92 % over 30 days, i.e. 63.3 %/yr |
| Nexus low | 1.82 % ÷ (5 × 0.30) = **1.2 %/yr** |
| Nexus high | 8.20 % ÷ (2 × 0.30) = **13.7 %/yr** |

Reading: if the markdown is certain, EXIT. If it is not, leaving pays only if it is more than 63 %/yr likely. Nexus prices an exploit of f(x) at 1–14 %/yr. On that evidence a depositor would stay, unless they had a reason other than an exploit to expect the markdown.

## 6. Impact on the probability, and its limits

**On the computation: none.** The Monte Carlo of `analyze`, the conditional Monte Carlo (`--conditional`), p\*, the verdict and the book's act-first order (lowest p\*) are all computed without Nexus. Removing it, or failing to read it, changes no number; it only removes one line.

**On the reading: an order of magnitude.** It gives an outside, market-priced figure for one cause of the incident, against which p\* can be read. Three limits keep it a display only:

- **Different event.** Protocol cover pays on a smart-contract exploit of the protocol, not on an issuer marking its NAV down or a borrower defaulting, and depeg cover pays on a depeg, not on a NAV markdown. The incident priced by p\* has more causes than the event Nexus covers, so the Nexus figure is closer to a lower bound on the incident's probability than an estimate of it.
- **Different holding.** The cover protects funds held in the protocol, not a Morpho vault lending against its token. That is why no "stay and insure" premium is offered: it would present as a hedge a cover that does not pay on these incidents.
- **Unobservable loading.** The [2, 5] bracket is a judgement with a stated basis, not a measured value. A price also includes the mutual's capacity constraints, as the Midas product's small capacity shows.

## 7. Maintenance

- **Refresh prices**: run the incident with `--record` (or `--refresh`) and commit the new files under `fixtures/replay/nexus/`. Without them, tests that run offline in CI fail.
- **Add a product**: find its id in `/v2/products`, read its wording (the IPFS annex) to set `kind`, add `"<token address>": {"product": <id>, "kind": "protocol" | "depeg", "token": "<symbol>"}` to `registry.json` `nexus.products`, and update `docs/reference/registry-reference.md`.
- **Tests**: `tests/test_breakeven.py` (`test_nexus_covers_and_implied_probability`, `test_recorded_nexus_offline`, `test_vault_breakeven_offline`).
- **Related docs**: `docs/risk-assessment/outside-providers.md` §2, `docs/analysis/PROVIDERS.md` (endpoints and limits), `docs/model/scenarios-and-breakeven.md`, `plan/2026-10-11-breakeven.plan.md`.
