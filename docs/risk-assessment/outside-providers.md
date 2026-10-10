# Outside risk providers

`riskdep` computes its own numbers from the chain. Outside providers add what the chain cannot show: how a stablecoin is backed off-chain, which coins share one admin key, and how an independent analyst grades an issuer. This document explains how each provider is used, what it changes in the output, and its limits.

| Provider | Status | Key | Used in |
|---|---|---|---|
| [Pharos](#1-pharos) | **in use** since 2026-10-11 (plan `2026-10-11-pharos`, D117–D122) | none | `analyze --vault` / `--book`, `graph` |
| [Nexus Mutual](#2-nexus-mutual-next) | next | none | planned: "stay and insure" in the verdict; an outside probability next to the breakeven p\* |
| Credora | not planned | whitelist only | its published method is cited as a basis (`docs/analysis/EXTERNAL_SOURCE.md` §3) |

The survey that chose them, with the live checks of 2026-10-10, is `docs/analysis/EXTERNAL_SOURCE.md`. Endpoints and limits are in `docs/analysis/PROVIDERS.md`.

## Contents

- [1. Pharos](#1-pharos)
  - [1.1 What it is](#11-what-it-is)
  - [1.2 What we read](#12-what-we-read)
  - [1.3 From a token to a Pharos id](#13-from-a-token-to-a-pharos-id)
  - [1.4 What it changes](#14-what-it-changes)
  - [1.5 What it found on the RockawayX book](#15-what-it-found-on-the-rockawayx-book)
  - [1.6 Recording, offline runs, freshness](#16-recording-offline-runs-freshness)
  - [1.7 Limits](#17-limits)
  - [1.8 Adding a token](#18-adding-a-token)
- [2. Nexus Mutual, next](#2-nexus-mutual-next)
- [3. Rules for any outside provider](#3-rules-for-any-outside-provider)

## 1. Pharos

### 1.1 What it is

Pharos (`https://pharos.watch`, run by TokenBrice, code MIT-licensed) is a stablecoin analytics site. It covers 396 stablecoins and yield dollars, including several Morpho vaults, and publishes for each one:

- a **Safety Score** from 0 to 100 and a letter grade (A+ to F; `NR` when not rated);
- what **backs** it, with weights: a wrapper (`serial-claim`, weight 1) or a share of a reserve basket (`basket-exposure`, weight w);
- the **common-mode groups** it belongs to: coins sharing one mint key, one upgrade admin, one reserve issuer, one redemption rail, one bridge, one chain or one DEX.

It is unrelated to the Pharos Network blockchain.

### 1.2 What we read

One keyless request: `GET https://api.pharos.watch/api/dependency-graph/v1`. Its nodes carry the grades and the backing, so the `safety-grades` endpoint is not needed. The response (0.5 MB) is slimmed to what is used (about 170 KB): each node's id, grade, score and backing; each group's kind, key and members.

| Pharos field | Becomes | Code |
|---|---|---|
| `nodes[].grade`, `score` | the grade shown on each hit market, in the book's notes, and on each graph asset | `pharos.Snapshot.grade` |
| `nodes[].roles[]` (`upstreamAssetId`, `weight`, `economicRole`) | the off-chain backing an incident follows, and the `backed by (Pharos)` graph edges | `pharos.exposure` |
| `commonModeGroups[]` (`kind`, `key`, `memberAssetIds`) | the "fails together" notes and the `shares (Pharos)` graph edges | `pharos.common_mode` |
| `asOfSec`, `methodologyVersion` | the date printed next to every grade | `pharos.Snapshot.as_of` |

Not used: `dependency-scenarios/v1` (45 modelled shocks, but as score changes, not losses); the keyed endpoints (stress score DEWS, depeg events, DEX liquidity, redemption backstops).

### 1.3 From a token to a Pharos id

Pharos ids are names, not addresses: `fxsave-f-x-protocol`, `iusd-infinifi`. `pharos.resolve` maps a token in this order (D118):

1. `registry.json` `pharos.ids`: address → `{id, symbol}`. Needed when a symbol is ambiguous: three coins are called iUSD, two reUSD.
2. An exact id: `token=iusd-infinifi:0.3` works.
3. The only id whose first part is the symbol: `fxSAVE` → `fxsave-f-x-protocol`. With two or more candidates, nothing matches.

A token that matches nothing is simply not graded. That is not an error.

### 1.4 What it changes

**In a vault or book incident** (`analyze --vault` / `--book --shock token=…`):

- **Off-chain backing (D119).** A token shock already reaches the markets whose collateral is the token, or wraps it on-chain (a PT, an ERC-4626 share; plan `2026-10-11-wrapped-collateral`). Pharos adds a third path: a market whose collateral is backed **off-chain** by the shocked token, through a reserve. The market's fall is the shock × the share of the backing, multiplied along the path:

  ```
  fall(market) = shock × Σ over paths Π weights      (capped at 1, depth 4, ignored below pharos.min_exposure = 1 %)
  ```

  The hit shows the path, e.g. `siUSD → iUSD ⇒ Pharos: iusd-infinifi → fxsave-f-x-protocol (16.4% of its backing)`. Such a market is reached through what its collateral holds, so the rule for wrapped collateral applies (D111): if the market's oracle tracks a market price, the fall is seen and borrowers are liquidated; if it is an exchange rate or a NAV, the oracle does not move, nothing is liquidated, and the loss is the hidden shortfall.

  The assumption: a loss in the reserve passes to the token pro rata. A protocol with a loss waterfall (infiniFi slashes its locked tranche first) passes less to its senior token, so this is an upper bound for those.
- **Grades (D120).** Each hit market shows the grade of its collateral, or of the first token it wraps that Pharos grades: `issuer grade (Pharos 2026-10-10): fxSAVE F 36`. The book lists the grades of every hit collateral. A grade is shown and never enters a loss: it is a judgement, not a probability.
- **Common-mode groups (D121).** The tool lists the other collateral of the vault that shares a narrow group with the shocked token, as a note. A narrow group is one of these kinds, with at most `max_group_members` (12) members:
  - mint control;
  - upgrade control;
  - reserve issuer;
  - redemption rail.

  Example: "trUSD with strUSD (mint control, upgrade control)". Such collateral fails with the token, so a second shock on it is not independent. Chain, DEX and wide bridge groups are dropped: Ethereum alone has 202 members.

**In `graph`** (`annotate_pharos`):

- each asset Pharos covers gets `pharos_id`, `pharos_grade`, `pharos_as_of`;
- each backing weight ≥ 1 % becomes a `backed by (Pharos)` edge, carrying the share and role. It points to the asset when it is already in the graph, else to a new External node;
- each narrow common-mode group shared by two assets of the graph becomes an External node, which both assets link to with `shares (Pharos)` edges.

The command prints `Pharos <date>: n asset(s) graded`, or `Pharos: not checked`.

### 1.5 What it found on the RockawayX book

Recorded book `examples/rockawayx-ethereum.json`, Pharos snapshot of 2026-10-10:

| Finding | Before Pharos | With Pharos |
|---|---|---|
| fxSAVE −30 % | 1 vault hit (f(x) Ecosystem, 2.01M USD) | 2 vaults: the siUSD market of RockawayX USDC Yield (2.36M of the vault) is reached, because fxSAVE backs 16.4 % of iUSD. Its oracle is an exchange rate, so the 4.9 % fall is hidden and below the borrowers' margin: no loss yet, but a new dependency |
| mGLOBAL (Midas) −50 % | not in any market: no hit | 43.4 % of iUSD's backing: a 21.7 % fall on the siUSD market, a 143k USD hidden shortfall in USDC Yield |
| fxUSD −30 % | no hit (fxSAVE's on-chain asset is the stability pool) | fxSAVE is a wrapper of fxUSD: 1.63M USD hidden shortfall in f(x) Ecosystem (its oracle is fxSAVE's exchange rate, which does not follow fxUSD), plus the iUSD path |
| trUSD −30 % | 1.61M USD, two vaults | the same loss, plus: trUSD and strUSD share their mint key and upgrade admin |
| Grades of the book's collateral | none | fxSAVE F 36, iUSD D 49, strUSD D 46, trUSD C- 54, reUSD F 38, EURCV A- 81, steakEURCV F 19 |

PST (Huma), mGLOeuro (Midas), AUTO, PRIME, nvPRIME and wYLDS are not covered by Pharos, or not rated there. Pharos rates stablecoins and yield dollars, not tokenised credit or fund shares.

### 1.6 Recording, offline runs, freshness

The response is cached by the project's fetcher under `fixtures/replay/pharos/`. It is committed, like every fixture, so tests and the demo run offline (D122).

| Run | Pharos is read from |
|---|---|
| offline (default) | the recording |
| `--record`, `--refresh` | Pharos, and the recording is rewritten |
| `--live` | Pharos, nothing saved |

If Pharos cannot be read, the run goes on and prints `Pharos: not checked`.

Pharos recomputes its grades often (methodology 10.16, model v9 when recorded). Every grade is printed with its publication date. Re-record before relying on a grade, and check the address map when the methodology version changes.

### 1.7 Limits

- **Stablecoins only.** No grade for Morpho, Pendle, an oracle, or tokenised credit (PST, mGLOeuro).
- **Grades are not probabilities.** They are shown next to our numbers, never multiplied into them. Turning them into a prior is step B5 of `NEXT_STEP.md`, with a stated mapping in the registry.
- **Backing is incomplete.** Ethena's hedges and custodians are not edges, and most nodes have `dependencyCoverageCount` 0. A missing edge means "not known to Pharos", not "no dependency".
- **Reserve weights are Pharos's.** Each edge's provenance is `live-reserve` or `curated-reserve`. They can lag the issuer's own report.
- **Pro-rata pass-through** overstates the loss for a token protected by a junior tranche (§1.4).
- **No SLA.** It is a free service. It is optional by design.

### 1.8 Adding a token

When an incident or a graph leaves a token ungraded that Pharos covers under an ambiguous name:

1. Find its id in the recording, or on `https://pharos.watch`.
2. Read the token's `symbol()` on-chain.
3. Add `"<address in lower case>": {"id": "<pharos id>", "symbol": "<symbol>"}` to `registry.json` `pharos.ids`.

Unambiguous symbols need nothing.

## 2. Nexus Mutual, next

Nexus Mutual sells cover against protocol exploits and depegs. Its API is keyless: `api.nexusmutual.io/v2/products` and `/v2/capacity`. These are the products relevant to the RockawayX book, as checked on 2026-10-11:

| Product (id) | Yearly price |
|---|---|
| Tori Finance (446) | 2.33 % |
| infiniFi (308) | 1.9–2.8 % |
| f(x) Protocol (137) | 1.8–8.2 % |
| fxUSD depeg (311) | 1.5 % |
| Midas (356) | 1.48 %, with little capacity |
| Morpho smart-contract cover (460) | 0.79 % |

Planned use, through the same fetcher and the same optional rules:

1. **"Stay and insure"** next to STAY and EXIT: the premium for the depositor's exposure over the horizon, when capacity covers it.
2. **An outside probability** next to the breakeven p\* (`NEXT_STEP.md` A2): price ÷ loading ÷ severity, with the loading as a range in the registry.

The open question is the wording. Protocol cover pays on an exploit, not on an issuer marking its NAV down or a borrower defaulting, so the tool must say which incidents a product covers before it offers "insure".

## 3. Rules for any outside provider

- **Keyless first.** A keyed provider needs `keys.ini` and drops out cleanly without it.
- **Optional.** It is never needed to produce a number. When it cannot be read, the run prints "not checked".
- **Shown, not blended.** An outside number appears next to ours, with its date and source. It only enters a computation through a mapping stated in `registry.json`, with its basis.
- **Recorded.** Responses go through `sources.Fetcher` into a committed fixture. Tests never call the network.
- **Documented in the same change.** That means a row in `docs/analysis/PROVIDERS.md`, a section in this document, and the registry keys in `docs/registry-reference.md`.
