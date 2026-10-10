# External sources: Pharos, Credora, Nexus Mutual

> **Status 2026-10-11.** Pharos's keyless dependency graph is in use (plan `2026-10-11-pharos`): grades, off-chain backing in incidents, common-mode groups. Nexus Mutual is next. How each is used now: `docs/risk-assessment/outside-providers.md`; this document stays the survey.

This document reviews three outside providers of risk data, whose documentation is saved in `docs/external/risk-assessment/` (git-ignored, local only). For each one: what it is, how its data can be reached (public, keyed, paid), what was checked live on 2026-10-10, and how it could improve `riskdep`'s risk computation. The gap ids `K<n>` refer to `GAP.md`; the others (C, M, R, G) to `ANALYSIS_MONITORING.md`.

## Contents

- [1. Summary](#1-summary)
- [2. Pharos](#2-pharos)
- [3. Credora](#3-credora)
- [4. Nexus Mutual](#4-nexus-mutual)
- [5. Three outside views of the same numbers](#5-three-outside-views-of-the-same-numbers)
- [6. How they fit the project](#6-how-they-fit-the-project)
- [7. Proposal: internal and external estimates, weighted](#7-proposal-internal-and-external-estimates-weighted)
- [8. Resources](#8-resources)

## 1. Summary

| | Pharos | Credora (RedStone) | Nexus Mutual |
|---|---|---|---|
| What it is | Stablecoin analytics: safety grades, depeg tracking, early-warning stress score, dependency graph | Credit ratings for DeFi assets, Morpho markets and vaults: a probability of loss (PSL) and a letter grade | Discretionary mutual selling cover against exploits and depegs |
| Covers | 396 stablecoins and yield dollars, including some Morpho vaults | Assets (stablecoins, RWAs, staking tokens), Morpho and Spark markets and vaults | 478 products: protocols, vaults, markets, depegs |
| Access | **3 endpoints keyless**; the rest need a key | **Key only**, after a whitelist form | **Keyless** REST API |
| Key | Supporter: a $10 donation, 10 req/min, revocable, no SLA. Partner: free for free services, from 120 req/min | `ClientSecret` header; granted on request | none |
| Checked live | `/api/safety-grades`, `/api/dependency-graph/v1`, `/api/dependency-scenarios/v1`: 200 | `api.credora.io/graphql`: 401 "Missing ClientSecret header" | `/v2/products`, `/v2/capacity`: 200 |
| Most useful for us | Issuer grades, look-through dependencies, common-mode groups, live stress and depeg events | A full method to copy (anchor PD + notches) and a PSL to check our numbers against | Market prices of cover: an outside upper bound on expected loss, and the price of insuring instead of exiting |
| Gaps it serves | K5, K6, K17–K20, K22, K23, K25, R3, M7 | K4, K7, K13, K17, K18, K16 | K4, K5, K17, K18, K21 |
| Fits "keyless public sources" | partly (3 endpoints) | no | yes |

**Recommendation, in order:**
1. **Nexus Mutual prices.** Keyless, one call, and it gives the clearest outside check on our numbers (§5). Add the "stay and insure" option to the verdict (K21).
2. **Pharos keyless endpoints.** Issuer grades and the dependency graph improve discovery depth and the issuer priors right away.
3. **A Pharos supporter key**, for the stress score (DEWS) and depeg events in the watches.
4. **Credora's method** now, as the template for K17–K18. Its API only if access is granted; it would need `keys.ini` and gives a PSL to compare, not an input.

## 2. Pharos

**What it is.** A free stablecoin analytics site run by TokenBrice (`https://pharos.watch`, code MIT-licensed on GitHub at `TokenBrice/pharos-watch`). It is unrelated to the Pharos Network blockchain. It publishes:
- a **Safety Score** per coin (0–100 and a letter grade, methodology v10.16);
- **PegScore**: time at peg and event severity;
- **DEWS**, a per-coin early-warning stress score recomputed every 30 minutes from eight signals: supply velocity, pool balance drift, liquidity erosion, price confidence, cross-source divergence, blacklist activity, mint/burn flow, yield anomaly;
- **PSI**, an ecosystem-wide stability index;
- a library of 27 reconstructed depegs (6 survived, 8 wounded, 13 died). The USD0++ case (Jan 2025) set off "a deleveraging cascade across Morpho".

### Access

OpenAPI 3.1 spec at `https://pharos.watch/openapi.json`; base URL `https://api.pharos.watch`; key in the `X-API-Key` header.

| Without a key | With a key (selection) |
|---|---|
| `/api/safety-grades`: grade and score of every coin | `/api/stress-signals` (DEWS), `/api/stability-index` (PSI) |
| `/api/dependency-graph/v1`: nodes, edges, common-mode groups | `/api/depeg-events`, `/api/depeg-resolver` (expected depeg duration) |
| `/api/dependency-scenarios/v1`: modelled shocks and their downstream effect | `/api/dex-liquidity`, `/api/dex-liquidity-history` |
| | `/api/redemption-backstops`, `/api/stablecoin-reserves/{id}` |
| | `/api/bluechip-ratings`, `/api/report-cards/v9`, `/api/safety-score-history-v2` |
| | `/api/mint-burn-events`, `/api/blacklist`, `/api/supply-history` |
| | `/api/snapshots/{date}.json`: a full daily snapshot |

**Keys:**
- **Supporter key:** donate $10 or more from a wallet, then claim the key with a signed message. 10 requests/min, no expiry, "revocable, best effort, no SLA".
- **Partner key:** free when the service using it is free; from 120 requests/min; terms negotiated for commercial use.

Every response carries its freshness (`asOfSec`, `publicationStatus`).

### What the keyless data says about our issuers (2026-10-10)

| Coin | Pharos id | Score | Grade |
|---|---|---|---|
| USDC (loan asset) | `usdc-circle` | 89 | A+ |
| USDT | `usdt-tether` | 69 | B- |
| USDS | `usds-sky` | 71 | B |
| sUSDS | `susds-sky` | 60 | C+ |
| USDe | `usde-ethena` | 62 | C+ |
| sUSDe (the demo's underlying) | `susde-ethena` | 55 | C |
| RLUSD (the watched Sentora vaults' asset) | `rlusd-ripple` | 73 | B |
| Two Sentora RLUSD vaults | `senrlusdv2-sentora`, `sxsrlusd-sentora` | 43, 64 | D, C+ |

**Dependency graph:**
- **Size:** 396 nodes and 309 edges: 202 collateral (basket-weighted), 104 wrapper, 3 mechanism.
- **Common-mode groups:** 748, by kind:
  - mint control 291;
  - bridge route 189;
  - chain 143;
  - reserve issuer 88;
  - upgrade control 28;
  - DEX protocol 6;
  - redemption rail 3.
- **What it shows for our coins:**
  - sUSDS wraps USDS, and **USDS is 40.6 % backed by USDC** (live reserve). This is the look-through `analyze` lacks (K19).
  - sUSDe wraps USDe. USDe has **no collateral edges**: its hedges and custodians are not in the graph, only common-mode groups (LayerZero bridge route, Curve and PancakeSwap pools, the Ethena mint control).

**Scenarios.** 45 modelled shocks: 15 root coins × three kinds (`depeg`, `mint-control-compromise`, `score-limit`). Each lists the downstream coins, their score change and their distance in hops. For example, a USDC depeg reaches 32 coins. These are **score** changes, not dollar losses.

### How it could be used

| Use | How | Gaps |
|---|---|---|
| **Issuer depeg prior from a grade** | Map the Safety Score to the depeg prior's frequency or severity as a bounded multiplier on a base rate (the K17 design): sUSDe at C should not get the same prior as an A+ coin. Today the 4 registry issuers are set by hand | K5, K17, K18, M7 |
| **Look-through discovery** | Follow collateral and wrapper edges from the position's underlying (sUSDe → USDe, sUSDS → USDS → USDC 40.6 %) and draw them as layers in `analyze` and `graph`. `graph` already draws the on-chain part of a wrapper, an ERC-4626 share's `wraps` edge to its `asset()` (plan `2026-10-10-sibling-markets`); Pharos adds the off-chain backing (USDS → USDC through the PSM, reserves) that `asset()` cannot show | K19 |
| **Correlation from common-mode groups** | Two layers in the same mint-control, upgrade-control, bridge or reserve-issuer group fail together: draw them from one common shock in `simulate`. `graph` now shows the on-chain common modes (one node per shared asset, oracle and feed, across held and sibling markets); Pharos's groups add the off-chain ones (mint keys, bridges, reserve issuers) | K6, R3 |
| **Contagion paths** | Pharos's scenarios name which coins a root failure reaches, and in how many hops. Use them as named scenarios (K20) and as a check on our propagation | K6, K20 |
| **Live warning** *(key)* | DEWS and depeg events as watch alerts, before the price moves; the depeg resolver's expected duration as the `recovery` input of a depeg | K22, K5 |
| **Exit liquidity** *(key)* | DEX liquidity and its history for the underlying, for exit cost under stress and for concentration | K9, K12, K25 |
| **Redemption route** *(key)* | Redemption backstops: whether a primary redemption exists and how fast, the alternative exit when pools are thin | K12, K22 |

**Limits:**
- **Stablecoins only.** Pharos rates the issuer layer, not Pendle, Morpho Blue or an oracle.
- **Grades, not probabilities.** A grade needs a mapping to a yearly frequency, which is a judgement that goes in `registry.json` with its basis.
- **It changes quickly.** Methodology v10.16, model v9. Pin `methodologyVersion` in the cache and re-check the mapping when it changes.
- **Coverage is uneven.** Ethena's backing is not in the edges, and `dependencyCoverageCount` is 0 for most nodes.
- **No SLA.** A supporter key is revocable and best effort. Keep Pharos optional: a missing response prints "not checked", like the cross-checks.
- **Not checked yet:** whether `senrlusdv2-sentora` is the Sentora RLUSD Main vault the watches follow; the keyed `/api/stablecoin/{id}` gives the address.

## 3. Credora

**What it is.** A rating agency for DeFi, part of RedStone. It publishes, per asset, Morpho market and vault:
- a letter grade on its DeFi scale;
- a **PSL**, the annualised probability of losing 1 % or more of principal.

USDC is the benchmark at A+.

### Access

| Item | Detail |
|---|---|
| Endpoint | `https://api.credora.io/graphql` (POST) |
| Authentication | Header `ClientSecret: <key>`; the key is granted after a whitelist request (Google Form). Checked: no key gives `401 Unauthorized: Missing ClientSecret header` |
| Main query | `ratings(filter: {protocol, product, ratingType, chainId, curator, address}, page, limit)`: `id, address, name, chainId, protocol, ratingType, product, curator, Metrics {rating, psl, publishDate}` |
| Rating types | "indicative" (Credora's own) and "commissioned" (paid for by the rated party) |

### The method (local docs)

The method matters as much as the API, because it is the design `GAP.md` K17–K18 reaches for.

1. **Anchor, then notches.**
   - An **anchor PD** comes from asset quality, custody and smart-contract risk.
   - **Modifiers** then move it in notches along one PD curve. The curve is calibrated on S&P, Moody's and Fitch one-year default rates, 1990–2023.
   - The modifiers are collateralisation, governance (upgrade and mint permissions, timelocks), market adoption, operational security (key custody, circuit breakers, privilege scope, incident playbook), peg track record, regulatory cover, reserve management and reserve transparency.
2. **Smart-contract risk is tiered, not counted:**

   | Factor | Tiers |
   |---|---|
   | Audit quality | Formal verification + multiple top audits > multiple audits + bounty > single audit > unaudited |
   | Contract maturity | 0–6, 6–18, 18–36, 36–60, 60+ months. **A material upgrade resets the clock.** Morpho Blue sits in 18–36 months |

3. **Morpho markets:**
   - the oracle is classified as **Dynamic**, **Exchange** or **Fixed**;
   - Fixed markets are rated from **loss-given-default curves** in extreme scenarios;
   - Dynamic and Exchange markets are rated by Monte Carlo: 100,000 price paths over 35 days, from 30-day volatility plus default jumps drawn from the collateral's PD and LGD;
   - then a liquidation simulation against a liquidity curve;
   - bad debt above 1 % of principal counts toward the PSL.
4. **Adjustments:** an oracle-risk modifier, and a **Morpho protocol PD of 0.13 %** (Ethereum and Base). **Principal tokens** get a notch for Pendle risk on top of the underlying's rating.
5. **Vaults** aggregate their markets' PSL, then adjust for the curator's record, governance and concentration.

A worked example in the docs: PT-sUSDe markets at LLTV 91.5 % with a **Fixed** oracle carry a collateral PD of **1.08 %/yr**. PT-USDS with an Exchange oracle carries 0.76 %.

### How it could be used

| Use | How | Gaps |
|---|---|---|
| **Copy the structure** (no API needed) | Base rate × notches from a stated curve; maturity tiers with reset on upgrade; audit tiers; oracle classes. This is K17 + K18 written out by a rating agency, citable as a basis | K17, K18, K15 |
| **Oracle classes** | Dynamic / Exchange / Fixed is a step past our two classes, and Credora rates Fixed markets differently (LGD curves, not price paths). Since plan `2026-10-10-sibling-markets`, `graph` classifies oracle inputs from their structure as `price-tracking` or `constant-price` (`oracle_class.py`); Credora's split maps onto it as Dynamic = price-tracking, and Exchange and Fixed = the two kinds of constant-price that the code does not yet tell apart | K7, K8 |
| **Check our numbers** *(key)* | Fetch the PSL of the demo's market and of the watched vaults. Report it next to ours: "Credora PSL x %, ours y %". A large gap is a finding, in either direction | K4, "is the number defensible" |
| **Vault depositor view** *(key)* | Vault PSL is exactly the depositor number `analyze` lacks (K16); use it as an outside reference until ours exists | K16 |
| **Tail-aware decision** | PSL is a probability of a loss above a threshold, the kind of tail metric K13 asks the verdict to use | K13 |

**Limits:**
- **Keyed and whitelisted.** It breaks the project's keyless design; the key would go in `keys.ini` (a new `[credora]` section, empty in `keys.example.ini`).
- **Commissioned ratings are paid for by the rated curator.** Show `ratingType` next to every number.
- **PSL is not expected loss.** It is P(loss ≥ 1 %) per year. It doesn't say how large the loss is.
- **Coverage is limited.** Only rated vaults and markets are covered, and `publishDate` can lag.

## 4. Nexus Mutual

**What it is.** A discretionary mutual: members buy cover, stakers underwrite it with NXM, and a claims committee decides on payouts. It has paid more than $18.5M in claims (to Aug 2026). Pricing:
- each staking pool sets a target price;
- the price rises 0.05 % per 1 % of pool capacity used, then decays back;
- an Advisory Board floor prevents a race to the bottom.

### Access

| Endpoint | Returns | Checked |
|---|---|---|
| `GET https://api.nexusmutual.io/v2/products` | 478 products: id, name, product type, cover assets, min price, deprecated flag | 200, keyless |
| `GET https://api.nexusmutual.io/v2/capacity` | per product: `minAnnualPrice`, `maxAnnualPrice`, `availableCapacity` by asset | 200, keyless |
| `GET https://api.nexusmutual.io/v2/capacity/pools/{poolId}` | the same per staking pool | documented |
| `GET https://api.nexusmutual.io/v2/quote` | premium for a given product, amount and period | documented |
| `@nexusmutual/sdk` | wraps the above | — |
| Claims | `https://nexusmutual.io/claims`, Dune dashboard `nexus_mutual/claims` | — |

### Prices for our layers (2026-10-10, annual, as a share of the amount covered)

| Product (id) | Min | Max | Capacity |
|---|---|---|---|
| Ethena USDe Depeg (253) | **3.00 %** | 3.50 % | yes |
| Sky USDS Depeg (261) | 0.50 % | 0.54 % | yes |
| Sky Protocol (45) | 0.65 % | 1.20 % | yes |
| Pendle (128) | 1.15 % | 1.50 % | yes |
| Blue Chip Morpho Vaults & Markets (229) | 1.65 % | 2.71 % | yes |
| Aave v3 (97), for reference | 0.88 % | 2.85 % | yes |
| sUSDe Pendle (170), Sky Savings Rate sUSDS (238), Steakhouse / Gauntlet / Re7 MetaMorpho (172–175), wstETH/USDC Morpho Blue (149) | 0 | 0 | none: not currently sold |

### How it could be used

| Use | How | Gaps |
|---|---|---|
| **An outside upper bound on expected loss** | A cover price is an expected payout plus a loading for capital and margin. Our yearly expected loss per $ for a layer should sit **below** it, but not far below (§5) | K4, K5, K17 |
| **A protocol-specific signal** | Price relative to its category (Pendle 1.15 % vs Blue Chip Morpho 1.65 %) as one input of K18's multiplier | K18 |
| **A third option for the verdict: stay and insure** | The brief's trade-off is "exiting is expensive and certain, staying is cheap and uncertain". Cover turns part of the uncertain loss into a certain premium. Insuring the demo's $3.93M collateral against a USDe depeg for 30 days costs about 3 % × 30/365 × $3.93M ≈ **$9,700**, against the $78,946 exit cost. The verdict can show this next to EXIT and REDUCE, when capacity exists and the wording covers the risk | K21, K12 |
| **Loss evidence** | The claims record: what was paid, for which events | K2 |

**Limits:**
- **Not a liquid market.** Prices are set by stakers within floors, and a price of 0 means the product is not sold.
- **The cover wording decides what pays out.** Depeg covers have their own trigger and exclusions; read the wording (linked from each product's IPFS metadata) before treating the price as a probability of **our** loss.
- **The loading is unknown**, so a price is an upper bound, not an estimate.
- **Capacity is finite.** Check it against the position's size before offering "insure" as an option.
- **No price for a PT loop itself.** The PT-sUSDe product (170) is not sold.

## 5. Three outside views of the same numbers

Our model's yearly expected loss per dollar, for each layer, set against the outside numbers. Ours is p_year × mean severity, from `registry.json` and the snapshot priors; for a depeg, the loss at the trough, before recovery.

| Layer | Ours, p_year | Ours, E[loss]/yr | Nexus price/yr | Nexus ÷ ours | Credora | Pharos |
|---|---|---|---|---|---|---|
| sUSDe / USDe depeg | 12 % | 0.98 % (0.25 % after 75 % recovery) | 3.0–3.5 % | **3–14×** | PT-sUSDe collateral PD 1.08 % (worked example in the docs, data from June 2025: an illustration, not a current rating) | sUSDe C (55), USDe C+ (62) |
| USDS depeg | 5 % | 0.18 % | 0.50–0.54 % | 3× | — | USDS B (71), sUSDS C+ (60) |
| Pendle exploit | 1.21 % | 0.17 % | 1.15–1.50 % | 7–9× | Pendle notch on PTs | — |
| Morpho Blue exploit | 5.03 % | 0.46 % | 1.65–2.71 % (blue-chip vaults and markets) | 4–6× | protocol PD **0.13 %** (stated in the public method page, undated) | — |

**Where the Credora numbers come from.** Neither comes from the API, which needs a whitelisted key. Both are printed in Credora's public documentation:
- 0.13 % in `protocol-implementations/morpho.md` ("The calculated Morpho Protocol PDs for Ethereum and Base is 0.13%");
- 1.08 % in the worked example `protocol-implementations/morpho/example-vault.md`, built on two Spark vaults with data from June 2025.

The 0.13 % is a parameter of the method, applied to every Morpho market Credora rates, but undated. The 1.08 % is an example. Neither is a live rating of the markets we watch; those need the API (§3).

**What it shows:**
1. **Probabilities and prices disagree in opposite directions.**
   - Our **depeg probability** for sUSDe (12 %/yr) is 11× Credora's PD for PT-sUSDe collateral (1.08 %), a different but related event.
   - Our **Morpho exploit probability** (5.03 %) is 39× Credora's 0.13 %, the K4 finding.
   - But our **expected losses** are 3–14× **below** what the insurance market charges.

   The two errors are the ones `GAP.md` names: probabilities too high, severities too thin (K4, K5).
2. **Ethena is the widest gap.** The market charges 3 %/yr for USDe depeg cover. Our expected loss is 0.98 % at the trough, and only 0.25 % after the assumed 75 % recovery. A 75 % recovery is the assumption the price disagrees with most.
3. **None of these is the truth.** A cover price includes a loading, Credora's PD is a judgement on a curve, and a Pharos grade is not a probability. Three independent outside numbers that bracket ours are still the best evidence available for the brief's criterion, "is the number defensible". Disagreements should be shown, not hidden.
4. **Much of the price gap is loading.** Taking out an insurance loading of 3 brings the Nexus-implied depeg frequencies back to ours (sUSDe 12.2 % vs 12 %, USDS 4.6 % vs 5 %); see §7.5. The Morpho exploit disagreement with Credora remains.

## 6. How they fit the project

### Where each source enters

| Module | Change | Source |
|---|---|---|
| `sources.py` | `pharos_grades()`, `pharos_graph()`, `pharos_scenarios()` (keyless); `nexus_products()`, `nexus_capacity()` (keyless); optional `pharos(endpoint)` with key, `credora_ratings(address)` with key. All through the cached `Fetcher`, so offline runs and tests keep working | all |
| `priors.py` | Issuer depeg prior: base rate × multiplier from the Pharos grade; exploit prior: K17 base rate × K18 multiplier, with Credora's tiers as the written basis | Pharos, Credora |
| `discover.py` / `graph.py` | Look-through layers from Pharos collateral and wrapper edges, next to the on-chain `wraps` edges `graph` already draws; common-mode groups as shared nodes, alongside the shared asset, oracle and feed nodes of the sibling markets | Pharos |
| `simulate.py` | One common shock per Pharos common-mode group (K6) | Pharos |
| `decide.py` | "Stay and insure" option with the Nexus price and capacity; Credora PSL shown as a reference | Nexus, Credora |
| `report.py` | An "Outside view" table (§5) per layer, with the date and source of each number | all |
| `watch.py`, `watch_user.py` | Pharos DEWS and depeg events as alerts *(key)* | Pharos |
| `crosscheck.py` | "Model vs outside view": warn when our yearly expected loss for a layer exceeds its cover price, or is below a tenth of it | Nexus |

### Project rules that apply

- **`PROVIDERS.md` in the same commit:** each new endpoint gets its row (endpoint, query, limits, key).
- **Keys:** a `[pharos]` and a `[credora]` section, with names and no values, in `keys.example.ini`; the values in `keys.ini` only. Nexus needs none.
- **Tests stay offline:** cache the responses under `fixtures/snapshot/` once, so tests and the demo run without the network.
- **New thresholds and mappings** (grade → multiplier, cover price → bound) go in `registry.json` with their basis, and in `docs/registry-reference.md`.
- **The docs themselves:** done. The three folders are in `docs/external/risk-assessment/`, git-ignored and listed in `CLAUDE.md` and `AGENTS.md`.

### Order

| Step | What | Effort |
|---|---|---|
| 1 | Nexus prices in `sources.py` + the "Outside view" table + the cross-check | S |
| 2 | Pharos keyless grades and graph: issuer multiplier, look-through layers, common-mode groups | S–M |
| 3 | "Stay and insure" in the verdict | S |
| 4 | Credora tiers as the written basis of K17–K18 in `registry.json` | S |
| 5 | Pharos supporter key: DEWS and depeg events in the watches | S |
| 6 | Credora API, if access is granted: PSL next to ours, vault PSL for K16 | S |

## 7. Proposal: internal and external estimates, weighted

The goal: each risk number in `analyze` comes from **our own computation and the outside providers together**, with a stated weight for each, instead of from our computation alone. The weights live in `registry.json`, and the report shows every component, so a reader sees where the number comes from and how far the sources disagree.

### 7.1 What we can use, by access level

| Access | Source | Data | Status |
|---|---|---|---|
| **Now, no key** | Nexus Mutual `/v2/products`, `/v2/capacity` | Annual cover price per protocol and per depeg, capacity | checked, works |
| **Now, no key** | Pharos `/api/safety-grades`, `/api/dependency-graph/v1`, `/api/dependency-scenarios/v1` | Issuer grades, look-through edges, common-mode groups, modelled contagion | checked, works |
| **Now, no key** | Credora public method docs | Morpho protocol PD 0.13 % (method parameter, undated); smart-contract and maturity tiers; oracle classes | in `docs/external/risk-assessment/` |
| **Supporter key, $10 donation** | Pharos keyed endpoints | DEWS stress score, depeg events, depeg duration, DEX liquidity, redemption backstops, daily snapshots | to obtain; recommended |
| **Whitelist form, not guaranteed** | Credora GraphQL | Live rating and PSL for Morpho markets and vaults | to request; the plan works without it |
| **Already held** | Etherscan (`keys.ini`) | Verified oracle sources | in use (D68) |

The plan must give a full answer with the first three rows only. Each keyed source adds weight when present and drops out cleanly when absent ("not checked", like the cross-checks).

### 7.2 What each source can estimate

The sources do not measure the same thing. Before they can be weighted, each is converted to the same quantity: **a yearly probability of the event** for one layer. The severity stays ours, from `registry.json`, until K5 is fixed.

| Source | Gives | Conversion to a yearly probability | Layers |
|---|---|---|---|
| Internal | p_year from the hack record (K17 base rate × K18 multiplier) or a registry entry | none | all |
| Nexus Mutual | Annual price π, an expected payout plus a loading | p = π ÷ L ÷ mean severity, with L the loading (registry: 3, range 2–5, basis: cover price includes capital cost and margin) | protocol exploit (Morpho, Pendle, Sky), issuer depeg (USDe, USDS) |
| Pharos | Grade A+ … F (score 0–100) | A table grade → p_year (registry, a judgement at first; calibrated later on Pharos depeg events, keyed) | issuer depeg |
| Credora (docs) | Morpho protocol PD 0.13 % | none: already a yearly PD | Morpho exploit |
| Credora (API) | Market or vault PSL: P(loss ≥ 1 %) | compared with our P(loss ≥ 1 % of equity) from the simulation, not blended into a single layer | market, vault (check only) |

**No outside source covers** the oracle layer, the Pendle pool move (K8), the borrow rate (K10) or the PT's implied yield (K11). Those stay internal, with weight 1.

### 7.3 How to weight

**Pool in log space, not linearly.** The sources differ by orders of magnitude (Morpho exploit: 5.03 % ours, 0.13 % Credora). A linear average is dominated by the largest number; a weighted geometric mean (log pooling, the usual way to combine probability forecasts) keeps each source's influence proportional to its weight:

$$
\log p = \frac{\sum_i w_i \log p_i}{\sum_i w_i}
$$

**Each weight is the product of three factors.** All three live in `registry.json` with a basis.

$$
w_i = b_i \times f_i \times r_i
$$

| Factor | Meaning | Proposed values |
|---|---|---|
| b_i, base trust | How much the source's method deserves for this layer | per source and layer, table below |
| f_i, freshness | 0.5^(age ÷ half-life) | live APIs: half-life 30 days; Credora docs: 180 days; undated figure: fixed 0.5 |
| r_i, relevance | Does it measure our event? | 1 if the same event (USDe depeg cover for a sUSDe depeg); 0.5 if related (Blue Chip Morpho vaults for one Morpho market); 0 if not |

**Proposed base trust, a starting point to argue about:**

| Layer | Internal | Nexus | Pharos | Credora |
|---|---|---|---|---|
| Protocol exploit (Morpho, Pendle, Sky) | 0.3 | 0.4 | — | 0.3 |
| Issuer depeg (USDe, USDS) | 0.4 | 0.3 | 0.3 | (API only) |
| Oracle, pool move, rates | 1 | — | — | — |

The reasoning:
- **Internal stays at least 0.3** on every layer. It is the only source that knows the position (its oracle, LLTV, PT), and K17 already limits how much the hack record alone should weigh.
- **Nexus gets the most on exploits.** It is the only live price, set by people with capital at risk.
- **Pharos gets as much as Nexus on depegs.** Its whole method is about stablecoins, and its record covers 27 reconstructed depegs.
- **Credora's 0.13 % weighs as much as our own hack record** on Morpho exploits. It is an agency's stated parameter, but undated, so its freshness factor halves it.

### 7.4 Guard rails

1. **The blend stays inside the sources' range.** It is clipped to [min p_i, max p_i], so it can never be more extreme than every source.
2. **Disagreement is shown, not averaged away.** If max p_i ÷ min p_i > 10, the report flags "sources disagree" for that layer and runs the verdict three times: internal only, blended, and the most pessimistic source. If the verdict changes, it says so, as the oracle sensitivity line already does.
3. **The spread becomes the uncertainty.** The range [min p_i, max p_i] is the interval K14 asks for; the verdict compares carry with the expected loss at the upper end (K13).
4. **A missing source drops out.** Its weight is 0 and the others renormalise; the report prints "Nexus: not checked" rather than failing.
5. **Severity stays internal** until K5 is fixed, so the blend changes frequencies only, and the effect of each source stays readable.
6. **One CLI switch** `--blend internal|blended|pessimistic` (default `blended`) reproduces any of the three runs.

### 7.5 Worked example (snapshot data, 2026-10-10)

Loading L = 3. All three sources are fresh, except Credora's undated figure, kept here at its base weight to show the method.

| Layer | Internal | Nexus-implied | Pharos | Credora | Weights | **Blended** | Spread |
|---|---|---|---|---|---|---|---|
| Morpho Blue exploit | 5.03 % | 1.65 % ÷ 3 ÷ 0.091 = 6.04 % | — | 0.13 % | 0.3 / 0.4 / — / 0.3 | **1.81 %** | 46× → "sources disagree" |
| Pendle exploit | 1.21 % | 1.15 % ÷ 3 ÷ 0.138 = 2.78 % | — | — | 0.5 / 0.5 | **1.83 %** | 2.3× |
| sUSDe depeg | 12 % | 3.0 % ÷ 3 ÷ 0.082 = 12.2 % | C → 8 % (proposed map) | — | 0.4 / 0.3 / 0.3 | **10.7 %** | 1.5× |
| USDS depeg | 5 % | 0.50 % ÷ 3 ÷ 0.036 = 4.6 % | B → 4 % | — | 0.4 / 0.3 / 0.3 | **4.6 %** | 1.25× |

**What it shows:**
- **On depegs, the sources roughly agree once the loading is taken out.** §5's "insurers charge 3–14× our expected loss" is mostly the insurance loading. The **loading L is the single most important assumption** of the Nexus conversion: it should be a range (2–5) shown in the report, not a point.
- **On Morpho exploits they don't agree.** Our 5.03 % and Nexus's 6.04 % sit on one side, Credora's 0.13 % on the other. The blend lands at 1.81 %, and the 46× spread is itself the finding: the "sources disagree" flag fires, and the verdict is also run with the pessimistic source. This is K4 made visible.
- **Pharos's grade map is a judgement.** Until it is calibrated on Pharos's own depeg events (keyed), its weight should stay at or below the internal one.

### 7.6 In the code

| Where | What |
|---|---|
| `riskdep/sources.py` | `nexus_products()`, `nexus_capacity()`, `pharos_grades()`, `pharos_graph()`, `pharos_scenarios()` (keyless); `pharos(endpoint)`, `credora_ratings(address)` read their key from `keys.ini` and return `None` without it. All through the cached `Fetcher` |
| `riskdep/outside.py` (new, pure) | `estimates(layer, ...) -> list[Estimate]` with value, source, date, base trust, freshness, relevance; `blend(estimates) -> Blended` (log pool, clip, spread, disagreement flag). No I/O, unit-tested |
| `riskdep/priors.py` | `Prior` gets `p_internal` and `components`; `p_year` becomes the blended value according to `--blend` |
| `riskdep/registry.json` | A `blend` section: base trust per layer and source, half-lives, the loading L and its range, the Pharos grade → p table, the disagreement ratio (10); each with a basis |
| `riskdep/decide.py` | The three-way run when a layer disagrees; "stay and insure" from Nexus price and capacity (K21) |
| `riskdep/report.py` | An "Outside view" table per layer: every component, its weight, the blend, the spread |
| `PROVIDERS.md`, `keys.example.ini` | New rows; `[pharos] api_key =` and `[credora] client_secret =` with no values |
| `fixtures/snapshot/` | One recorded response per endpoint, so tests and the demo stay offline |
| `tests/test_outside.py` | Log pool, clip, missing source, freshness, disagreement flag; the worked example above as a test case |

### 7.7 Order

| Step | What | Needs | Effort |
|---|---|---|---|
| 1 | `outside.py` with Nexus only: exploit and depeg layers, report table, `--blend` | nothing | S |
| 2 | Pharos keyless grades in the depeg blend; look-through and common-mode groups (K19, K6) | nothing | S–M |
| 3 | Credora's 0.13 % and method tiers as the documented basis (K17–K18) | nothing | S |
| 4 | Pharos supporter key: DEWS and depeg events in the watches; calibrate the grade map on depeg events | $10 key | S–M |
| 5 | Credora API: PSL check per market and vault, and a fourth source in the blend | whitelist | S |

Steps 1–3 need no key, and together they turn §5's comparison into a number the verdict actually uses.

## 8. Resources

### Local documentation (`docs/external/risk-assessment/`)

| Folder | Files used |
|---|---|
| `pharos.watch-safety-scores-docs/` | `learn.md` (mechanisms, case studies, PSI, DEWS, PegScore) |
| `credora.network-docs-docs/` | `api-documentation.md`, `api-documentation/ratings.md`, `methodologies/defi-rating-scale.md`, `methodologies/assets/framework-architecture/` (anchor PD, smart-contract risk, audit quality, contract maturity, modifiers), `protocol-implementations/morpho.md`, `protocol-implementations/morpho/example-vault.md` |
| `docs.nexusmutual.io-docs/` | `developers.md`, `developers/pos-integrations.md`, `protocol/pricing.md`, `overview/claims-history.md`, `overview/cover-products/` |

### Online, checked on 2026-10-10

- Pharos site and API page: https://pharos.watch/ and https://pharos.watch/api/
- Pharos OpenAPI spec: https://pharos.watch/openapi.json
- Pharos keyless endpoints: https://api.pharos.watch/api/safety-grades, https://api.pharos.watch/api/dependency-graph/v1, https://api.pharos.watch/api/dependency-scenarios/v1
- Pharos source code: https://github.com/TokenBrice/pharos-watch
- Pharos used in vault policies (Newton): https://docs.newton.xyz/developers/vaults/policies/pharos-safe-mode and https://docs.newton.xyz/developers/vaults/policies/pharos-treasury
- Pharos listed by QuickNode: https://www.quicknode.com/builders-guide/tools/pharos-stablecoin-analytics-by-tokenbrice
- Credora GraphQL endpoint (keyed): https://api.credora.io/graphql
- Credora documentation: https://www.credora.network/docs/
- Nexus Mutual API and OpenAPI docs: https://api.nexusmutual.io/v2/products, https://api.nexusmutual.io/v2/capacity, https://api.nexusmutual.io/v2/api/docs/
- Nexus Mutual SDK: https://github.com/NexusMutual/sdk
- Nexus Mutual claims: https://nexusmutual.io/claims and https://dune.com/nexus_mutual/claims

### Project files

`GAP.md` (gap ids), `riskdep/registry.json` (our priors and severities), `riskdep/priors.py` (snapshot exploit priors), `docs/how-risk-is-computed.md` (demo position and exit cost), `PROVIDERS.md` and `CLAUDE.md` (project rules on providers and keys).
