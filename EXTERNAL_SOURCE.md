# External sources: Pharos, Credora, Nexus Mutual

This document reviews three outside providers of risk data, whose documentation is saved in `../newDocs/`. For each one: what it is, how its data can be reached (public, keyed, paid), what was checked live on 2026-10-10, and how it could improve `riskdep`'s risk computation. The gap ids `K<n>` refer to `GAP.md`; the others (C, M, R, G) to `ANALYSIS_MONITORING.md`.

## Contents

- [1. Summary](#1-summary)
- [2. Pharos](#2-pharos)
- [3. Credora](#3-credora)
- [4. Nexus Mutual](#4-nexus-mutual)
- [5. Three outside views of the same numbers](#5-three-outside-views-of-the-same-numbers)
- [6. How they fit the project](#6-how-they-fit-the-project)
- [7. Resources](#7-resources)

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
| **Look-through discovery** | Follow collateral and wrapper edges from the position's underlying (sUSDe → USDe, sUSDS → USDS → USDC 40.6 %) and draw them as layers in `analyze` and `graph` | K19 |
| **Correlation from common-mode groups** | Two layers in the same mint-control, upgrade-control, bridge or reserve-issuer group fail together: draw them from one common shock in `simulate` | K6, R3 |
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
| **Oracle classes** | Dynamic / Exchange / Fixed is a step past our market-tracking / fundamental binary, and Credora rates Fixed markets differently (LGD curves, not price paths) | K7, K8 |
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
| sUSDe / USDe depeg | 12 % | 0.98 % (0.25 % after 75 % recovery) | 3.0–3.5 % | **3–14×** | PT-sUSDe collateral PD 1.08 % (docs example) | sUSDe C (55), USDe C+ (62) |
| USDS depeg | 5 % | 0.18 % | 0.50–0.54 % | 3× | — | USDS B (71), sUSDS C+ (60) |
| Pendle exploit | 1.21 % | 0.17 % | 1.15–1.50 % | 7–9× | Pendle notch on PTs | — |
| Morpho Blue exploit | 5.03 % | 0.46 % | 1.65–2.71 % (blue-chip vaults and markets) | 4–6× | protocol PD **0.13 %** | — |

**What it shows:**
1. **Probabilities and prices disagree in opposite directions.**
   - Our **depeg probability** for sUSDe (12 %/yr) is 11× Credora's PD for PT-sUSDe collateral (1.08 %), a different but related event.
   - Our **Morpho exploit probability** (5.03 %) is 39× Credora's 0.13 %, the K4 finding.
   - But our **expected losses** are 3–14× **below** what the insurance market charges.

   The two errors are the ones `GAP.md` names: probabilities too high, severities too thin (K4, K5).
2. **Ethena is the widest gap.** The market charges 3 %/yr for USDe depeg cover. Our expected loss is 0.98 % at the trough, and only 0.25 % after the assumed 75 % recovery. A 75 % recovery is the assumption the price disagrees with most.
3. **None of these is the truth.** A cover price includes a loading, Credora's PD is a judgement on a curve, and a Pharos grade is not a probability. Three independent outside numbers that bracket ours are still the best evidence available for the brief's criterion, "is the number defensible". Disagreements should be shown, not hidden.

## 6. How they fit the project

### Where each source enters

| Module | Change | Source |
|---|---|---|
| `sources.py` | `pharos_grades()`, `pharos_graph()`, `pharos_scenarios()` (keyless); `nexus_products()`, `nexus_capacity()` (keyless); optional `pharos(endpoint)` with key, `credora_ratings(address)` with key. All through the cached `Fetcher`, so offline runs and tests keep working | all |
| `priors.py` | Issuer depeg prior: base rate × multiplier from the Pharos grade; exploit prior: K17 base rate × K18 multiplier, with Credora's tiers as the written basis | Pharos, Credora |
| `discover.py` / `graph.py` | Look-through layers from Pharos collateral and wrapper edges; common-mode groups as shared nodes | Pharos |
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
- **The docs themselves:** `../newDocs/` sits outside the repository. Move the three folders under `docs/external/` (git-ignored, like the Morpho and Etherscan docs) and list them in `CLAUDE.md` and `AGENTS.md`.

### Order

| Step | What | Effort |
|---|---|---|
| 1 | Nexus prices in `sources.py` + the "Outside view" table + the cross-check | S |
| 2 | Pharos keyless grades and graph: issuer multiplier, look-through layers, common-mode groups | S–M |
| 3 | "Stay and insure" in the verdict | S |
| 4 | Credora tiers as the written basis of K17–K18 in `registry.json` | S |
| 5 | Pharos supporter key: DEWS and depeg events in the watches | S |
| 6 | Credora API, if access is granted: PSL next to ours, vault PSL for K16 | S |

## 7. Resources

### Local documentation (`../newDocs/`)

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
