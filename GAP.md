# GAP: a challenge of the risk computation

This document challenges how `riskdep analyze` computes risk: the priors, the propagation, the simulation and the verdict. It is checked against the code, the project docs, the teammates' notes and outside evidence (incidents from 2022 to 2026, and the methods of risk firms and academic work). It sits next to `ANALYSIS_MONITORING.md`, which lists the known gaps (M1–M7). This file questions the model's assumptions themselves. Each gap gets an id `K<n>`, and a gap that extends an existing one names it.

Numbers for the demo position come from `docs/how-risk-is-computed.md` and the offline snapshot (`fixtures/snapshot/`, as of 2026-10-10). The position holds PT-sUSDE-26NOV2026 against USDC on Morpho Blue: collateral $3.93M, debt $3.41M, equity $0.52M, leverage 7.6×, LLTV 91.5 %, liquidation distance 5.16 %, verdict REDUCE.

## Contents

- [1. Verdict](#1-verdict)
- [2. Summary table](#2-summary-table)
- [3. Probabilities](#3-probabilities)
- [4. Severities and correlation](#4-severities-and-correlation)
- [5. Oracle and liquidation mechanics](#5-oracle-and-liquidation-mechanics)
- [6. Loss channels the model does not have](#6-loss-channels-the-model-does-not-have)
- [7. The decision rule](#7-the-decision-rule)
- [8. Vault depositors](#8-vault-depositors)
- [9. What holds up](#9-what-holds-up)
- [10. Recommended order](#10-recommended-order)
- [11. Resources](#11-resources)

## 1. Verdict

The model is careful and well documented, and every number has a stated basis. Its weak point is not the arithmetic but **what it treats as a risk**. It prices incidents: hacks, depegs, oracle failures. For a 7.6× PT loop, the losses that actually happened to positions like this in 2025–2026 mostly came from somewhere else:

1. **Rates, not incidents.**
   - A borrow-rate spike or a rise in the PT's implied yield costs the position without any incident.
   - A borrow rate +10 pp for 30 days costs **$28,060**, 4.5× the whole modelled expected loss ($6,265).
2. **Oracle design.**
   - A Pendle TWAP oracle liquidated about $36M of Morpho PT loops on 2026-08-25 with no fundamental move.
   - Hardcoded and NAV oracles hid the Resolv and deUSD collapses until lenders held the bad debt.
   - The model reduces all of this to one binary: does the oracle track the market or not.
3. **Correlated failures.**
   - In Nov 2025, xUSD, deUSD and USDX depegged within days of one another, through lending links between issuers.
   - The model's layers are independent.

Its base rates are also biased downward, by survivorship in the hack record (§3). Its severity tails are thin for synthetic dollars (§4).

None of these gaps means the demo verdict is wrong. Every one of them points the same way, though: **more risk than reported**.

## 2. Summary table

| Id | Gap | Direction | Evidence | Impact | Effort |
|---|---|---|---|---|---|
| K1 | Hack base rate drops hacked protocols whose TVL has since fallen below $1M | under-states | 305 of 1,070 hacks dropped on the snapshot | high | S |
| K2 | Hack ledger misses off-chain failures (custodian, fund manager, key compromise) | under-states | Stream, Resolv | high | M |
| K3 | Lending exploit and oracle layers double-count oracle exploits | over-states | Lending category includes oracle hacks | low | S |
| K4 | Morpho Blue exploit prior (5.0 %/yr) far above other anchors | over-states frequency | Credora 0.13 %/yr; never exploited | low | S |
| K5 | Depeg severity tail too thin for a synthetic dollar | under-states tail | P(depeg > 50 %) = 0.002 % in the model; USR −97 %, xUSD −77 %, deUSD −98 % | high | S |
| K6 | Layers independent; only issuer hack → depeg is linked | under-states tail | Nov 2025 cluster; Resolv chain; PT-reUSD | high | M |
| K7 | Oracle is "market-tracking" or "fundamental"; real oracles are composites | wrong mechanism | demo oracle is a `MetaOracleDeviationTimelock`; min(TWAP, linear) oracles | high | M |
| K8 | Oracle manipulation of a thin Pendle pool is not a loss channel | under-states | PT-reUSD, 33 liquidations, LLTV 91.5 % | high | S–M |
| K9 | Liquidation at the oracle price with LIF; no slippage, no cascade, no partial liquidation | under-states | LlamaRisk PT supply ≫ AMM depth; Gauntlet, Credora simulate it | medium | M |
| K10 | Borrow-rate risk of the AdaptiveCurveIRM | under-states | rate ×4 at 100 % utilisation, curve doubles in 5 days | high | S |
| K11 | PT implied-yield (duration) risk | under-states | +20 pp implied yield = −2.2 % PT price on the demo | medium | S |
| K12 | Exit cost (one-off) compared with a 30-day loss, while holding to maturity is free | biases to STAY | maturity in 46.6 days | medium | S |
| K13 | EXIT rule uses the mean only; CVaR 98 % of equity still gives REDUCE | biases to STAY | Bundi: yields cover the mean, not the tail | medium | S |
| K14 | Point estimates without uncertainty; Poisson-style one event per layer | hides uncertainty | dispersion index 3.27; ξ unstable | medium | M |
| K15 | Age factor and PT stress ×1.5 have no empirical basis | unknown | no study found | low | S |
| K16 | Depositor loss under a scenario still missing for vaults (drain d\* done in the watches) | missing | Team 2; deUSD, wstUSR | high | M |

## 3. Probabilities

### K1. Survivorship in the hack base rate

`priors.hack_stats` keeps a hack only if the protocol's **current** TVL is at least $1M, and assigns its tier from that current TVL (`riskdep/priors.py`, the `tvl < min_tvl_usd` filter).

On the cached snapshot:

| Hacks in the 5-year window | No DefiLlama protocol id | Protocol now below $1M (dropped) | Kept |
|---|---|---|---|
| 1,070 ($12.94B) | 620 ($5.72B) | **305 ($2.44B)** | **145** |

A protocol that a hack destroyed is precisely the one that drops out. The registry's basis says survivorship "biases small tiers up, not the ≥ $100M tier", which only covers the denominator. The numerator loses more: two hacked protocols are dropped for every one kept. A protocol hacked at $500M that now holds $50M also lands in the wrong tier.

- **Effect:** every exploit prior is too low. Measured against the 450 hacks that had a protocol id (145 + 305), the bias could reach about 3×; the exact factor needs each protocol's TVL at the date of its hack.
- **Fix:** tier each protocol by its TVL at the hack date. DefiLlama's `/protocol/{slug}` returns TVL history. Show the rate with and without the dropped hacks.

### K2. Losses that are not in a hack ledger

The issuer's exploit prior counts DefiLlama hacks in its category. The losses that broke synthetic dollars in 2025–2026 were mostly not smart-contract hacks:

- **Stream xUSD (Nov 2025):** an external fund manager lost $93M.
- **Resolv USR (Mar 2026):** a compromised AWS KMS signing key let the attacker mint 80M USR.

Ethena's own risk page lists custodial failure, exchange failure and margin-collateral risk as separate risks. Bundi's merged dataset shows that single-source hack ledgers have known coverage gaps, and that most lending losses are economic-design and oracle failures, not code exploits.

- **Fix:** keep the hack ledger for code risk. For a synthetic or off-chain issuer, add an operational / counterparty prior in `registry.json` with its own basis: custodian, CEX, manager, keys.

### K3. Oracle exploits counted twice

The Morpho Blue exploit prior uses the **Lending** category multiplier. Lending hacks in the record include oracle misconfigurations and stale feeds. The oracle layer then counts the same techniques again (`oracle_prior`).

- **Fix:** take oracle techniques out of the category counts used for the lending layer.

### K4. The Morpho Blue prior

On the snapshot, `exploit_p_year("morpho-blue")` gives **5.0 %/yr**, 4× Pendle's 1.2 %/yr. That's because the Lending category rate is high, mostly forks with spot-price oracles.

Other anchors:
- Credora uses a smart-contract probability of default of **0.13 %/yr** for Morpho.
- No exploit of the Morpho Blue core was found. The PAXG market loss (2024) and the front-end incident (Apr 2025) were market configuration and off-chain respectively.

The expected loss per year still lands close to an independent estimate. 5.0 % × mean severity 9 % = 0.46 % of collateral a year, against Bundi's pure premium of 0.62 % of TVL for Morpho Blue. So the frequency is high and the severity is low, and the two errors roughly cancel.

- **Fix:** move risk from "core exploit" to "market configuration", which is a per-market oracle check (K7), and say so in the basis.

### K14. One number, no uncertainty

- **One event per layer.** Each layer is a Bernoulli draw per horizon (`simulate._p_horizon`). Bundi rejects a Poisson model of event counts in 5 of 7 sectors (dispersion index 3.27): events cluster.
- **The tail shape is unstable.** Lending's estimated tail shape moves from ξ = 0.75 to 0.35 when one event is removed.
- **No range is shown.** The report gives "13.5× the estimates" for the risk multiple but no interval on the expected loss itself.

**Fix:** sample the priors themselves; for example, draw p_year from a Beta fitted to the counts. Report the expected loss and CVaR as a range. Compare carry with the upper bound (§7).

### K15. Two parameters without a source

- **Age factor** (×2 under one year, ×0.7 over three years). No survival study of DeFi protocols by age was found. Evidence runs both ways: attacks on old unmaintained contracts (Truebit, Yearn v1) against a falling loss per incident. Label it as a judgement in `registry.json`.
- **PT stress ×1.5** (`pt_stress_extra_discount`). The basis is a sentence. Evidence now exists to calibrate it:
  - LlamaRisk's PT drop scenarios ($0.12 and $0.21 drops);
  - the Aave maximum discount rates for PT-sUSDe (21–31 %);
  - the PT-reUSD trough of −2.77 % from a $320k trade.

## 4. Severities and correlation

### K5. The depeg tail of a synthetic dollar

sUSDe depeg severity is Beta(1.6, 18):

| | Mean | P(> 20 %) | P(> 50 %) |
|---|---|---|---|
| Model | 8.2 % | 5.0 % | **0.002 %** |

Synthetic and leveraged-yield dollars that broke in 2025–2026 went far deeper: USR −97 % on DEX within 17 minutes, xUSD about −77 % in a day, deUSD to near zero. The academic depeg literature finds that fiat-backed coins depeg often and mildly, while crypto-backed coins depeg less often but longer and deeper.

The model reaches a deep loss only through the issuer **hack** branch: Beta(1.2, 3), P(> 50 %) = 16 %, but at a hack-ledger frequency (K2).

- **Fix:** use a two-part severity for a synthetic dollar: a frequent shallow wick plus a rare collapse with severity near total. The collapse frequency comes from K2's operational prior, not from the hack ledger.
- **Venue matters:** USDe's −35 % on 2025-10-10 was on Binance only. On-chain pools and Chainlink stayed near par. The severity has to be the one the **oracle and the PT pool** see, not a CEX print. The registry basis already says this; the distribution should be fitted to on-chain prices.

### K6. Independence

`simulate.run` draws each layer independently. Its only link is issuer hack → depeg (D12). Incidents show three other links:

| Link | Incident |
|---|---|
| Issuer → issuer (one issuer lends to another) | Stream held about 90 % of deUSD and owed Elixir $68M through a Morpho loan; xUSD, deUSD and USDX all broke in the same week of Nov 2025 |
| Issuer → oracle | NAV and hardcoded oracles kept pricing wstUSR and deUSD at par after their collapse |
| Pendle pool → oracle | A TWAP oracle on a thin pool moves with any trade large enough (PT-reUSD) |
| Depeg → Pendle pool → exit cost | LPs leave the pool during a depeg; `pt_stress_extra_discount` models this for the oracle only, not for the exit quote |

`ANALYSIS_MONITORING.md` has this as M2 (medium).

- **Assessment:** the evidence argues for **high**. Every large loss in the incident list was a chain of layers, never a single one.
- **Fix:** run named scenarios alongside the Monte Carlo, as both teams asked (`comparison_team.md` §4.2): replay of the Nov-2025 contagion, replay of Resolv, PT yield spike + pool drain, CEX-only wick. Add a common-shock factor that raises every layer's probability in the same draw.

## 5. Oracle and liquidation mechanics

### K7. The oracle is not binary

`discover.infer_oracle` classifies the oracle by comparing its price with the PT's market price: "market-tracking" or "fundamental", and "ambiguous" near par. It falls back to market-tracking when it can't tell.

The oracles actually used for PT markets combine several parts:

| Oracle | PT → underlying | Underlying → loan asset | What a depeg does |
|---|---|---|---|
| Pendle TWAP (15 min) | market, lagged | feed or hardcoded | liquidates on a pool move, even a manipulated one |
| Linear discount | deterministic | feed or hardcoded | never liquidates on a depeg: **lenders take the loss** |
| min(TWAP, linear) | the lower of the two | feed | capped above, no floor: liquidates on a pool move |
| Meta-oracle with deviation timelock (the demo: `MetaOracleDeviationTimelock`, Steakhouse) | switches between a primary and a backup after a deviation lasts long enough | — | depends on which source is live and the timelock length |

- **Why the binary fails:**
  - Classifying by price can't tell these apart near par. The demo PT is 0.62 % below par, so the result is ambiguous.
  - "Conservative" depends on who you are. Market-tracking is the worst case for a **borrower**; for a **lender** the linear discount is.
- **Fix:** read the oracle's structure. The source is now verified on Etherscan (D68), and `admin.py` already reads `BASE_FEED_*` and `BASE_VAULT`. Map each known oracle type to its rule, and fall back to price inference only for unknown ones. `REPOSITORY_ADD.md` lists `morpho-blue-oracles`; for the Chainlink part its library says "Staleness is not checked".

### K8. Liquidation without any incident

On 2026-08-25, one wallet spent $320k on YT-reUSD over 9 minutes. The trades pushed the PT's implied yield from about 11 % to more than 20 %. A min(TWAP, linear) oracle dropped 0.5–2.8 %, and Morpho liquidated 33 PT-reUSD positions at LLTV 91.5 %. Borrowers paid about $946k of liquidation bonus. There was no bad debt, and the price recovered within five hours. (Single detailed source plus news corroboration; see §11.)

The demo sits at the same LLTV with a 5.16 % buffer. In the model, the only path to a liquidation without a real loss is the `oracle` layer (misconfiguration, mean −10 %, 2.0 %/yr). A manipulation of the pool is not in it. Its cost to the borrower is the LIF, 2.6 % of the debt repaid, plus the loss of the position.

- **Fix:** add a "pool move" event for TWAP-based oracles.
  - Frequency: the history of large implied-yield moves in the Pendle market.
  - Size: the price impact of a given capital, from Pendle's quote at several sizes, which is already available.
  - Loss: the LIF on the debt repaid, with no loss of value.

### K9. Liquidation clears at the oracle price, once

`propagate.loss` seizes debt × LIF at the oracle price, with no slippage, no cascade and no partial liquidation. This is M3 part 2 and the cascade loop in `comparison_team.md` (item 8).

- **Evidence for the gap:**
  - LlamaRisk measured PT supply on lending markets at **12.8× (PT-sUSDe) and 30× (PT-USDe)** the depth of the Pendle AMM.
  - Its modelled bad debt rose from $7M to $70M as the PT drop went from $0.12 to $0.21: strongly non-linear.
  - Gauntlet and Credora both simulate liquidator behaviour and depth.
- **Evidence against it:** on 2025-10-10 lending liquidations cleared with almost no bad debt, but that was blue-chip collateral.
- **Fix:** the loop already proposed (collateral seized at a drop → Pendle price impact for that size → new drop, until stable), with the per-market curve that `market_risk.py` already computes.

## 6. Loss channels the model does not have

### K10. The borrow rate

Morpho's AdaptiveCurveIRM targets 90 % utilisation:
- at 100 % utilisation the rate is **4× the rate at target**;
- that rate-at-target **doubles in 5 days** if utilisation stays at 100 % (Morpho docs, `contracts/irm.md`).

A loop's carry is the spread between the PT yield and the borrow rate: 5.01 % − 3.74 % on the demo, at 7.6× leverage.

| Borrow rate shock, 30 days | Cost to the demo |
|---|---|
| +5 pp | $14,030 |
| +10 pp | $28,060 |
| +15 pp | $42,090 |

The whole modelled expected loss is $6,265. `ANALYSIS_MONITORING.md` ranks this as M5, impact **low**. For a leveraged loop it is the most frequent way to lose money: lenders leave a market whenever a better rate appears elsewhere, with no incident at all. The watch already alerts on utilisation; `analyze` doesn't use it.

- **Fix:** draw a borrow-rate path from the IRM, using the market's utilisation history and the 4× / 5-day rule, and subtract its cost from carry in each simulated month.
- **The exit-delay side:** a borrower can always repay, but to repay they must sell the PT, which is K12's exit cost.

### K11. The PT's implied yield

A PT's price before maturity moves with its implied yield. On the demo (46.6 days to maturity):

| Implied yield move | PT price |
|---|---|
| +5 pp | −0.59 % |
| +10 pp | −1.16 % |
| +20 pp | −2.20 % |
| +40 pp | −4.04 % |

With a market-tracking oracle, a +40 pp spike liquidates the demo by itself. PT-reUSD's implied yield went from about 11 % to more than 20 % in nine minutes. The effect shrinks with time to maturity, so this matters most for long PTs. The carry formula assumes the PT accretes at the implied yield, which is only true at maturity.

- **Fix:** add the implied-yield move as a draw (its distribution from the Pendle market's history), price the PT from it, and feed the price to the oracle according to K7.

## 7. The decision rule

### K12. A one-off cost against a 30-day loss

The rule EXIT if EL > carry + exit cost compares a one-off cost ($78,946) with the loss of **one month**. The PT matures in 46.6 days, and at maturity it redeems at par with no price impact.

- **The fair alternatives:**
  - exit now at the quote;
  - hold to maturity and bear the risk of 46.6 days;
  - de-lever part now.
- **Why it matters:** with a horizon shorter than maturity, the exit cost is spread over too short a period. With no maturity, a 30-day horizon would treat the exit cost as if it were paid every month.
- **The quote:** the exit quote is taken in calm conditions. In the scenarios where exiting matters, the pool is thinner (K6).
- **Fix:** set the horizon to the time to maturity for a PT. Report the exit cost under stress (the quote with the pool depth of the stress scenario), not only today's.

### K13. The tail barely moves the verdict

EXIT depends only on the mean. A CVaR 99 % of **98 % of equity**, the demo's, only gives REDUCE. Bundi finds that lending yields cover the expected loss but "a negligible fraction" of the tail. Practitioners decide on the tail:
- Gauntlet: insolvency VaR 95 and Liquidations-at-Risk;
- Credora: the probability of a loss above 1 %.

The `tail_budget` of 50 % of equity is a stated choice, but nothing ties it to the leverage or to the holder's mandate.

- **Fix:**
  - compare carry with the **upper** bound of the expected loss (K14);
  - let a CVaR beyond a second, higher budget (e.g. 80 % of equity) give EXIT;
  - report P(loss > x % of equity) next to CVaR.

## 8. Vault depositors

### K16. The depositor still has no loss number

`comparison_team.md` §4.3 already calls this the largest gap against the track's "impact" criterion. The exit queue model and the drain threshold are done; one piece is not.

1. **A depositor loss under a scenario:** Σ over the vault's markets of its share of supply × the market's bad debt at that drop. `market_risk.value()` already returns bad debt at a given drop. **Still missing.**
2. ~~**The fixed-oracle drain d\*** (Team 2)~~ **done** in the watches (`riskdep/drain.py`, `DrainWindow` alert, `docs/drain-threshold.md`). With a linear-discount, hardcoded or NAV oracle, a depeg never liquidates, and borrowers can loop the depegged asset in until caps are full; that is what happened on wstUSR, where the oracle marked $1.13 while the market was near $0.63. What remains is to feed it into `analyze`: the drained amount is a loss channel for a depositor, and the probability of crossing d\* comes from the depeg prior (K5).

Incidents add a third: the **realisation rule** depends on the vault version.
- V1.0 realises bad debt for every holder at once.
- V1.1 doesn't, so the last holders take it: a run incentive.
- V2 realises it through `realAssets()`.

A V2 vault holding V1.1 shares through `MorphoVaultV1Adapter` inherits the V1.1 behaviour (see `REPOSITORY_ADD.md`).

## 9. What holds up

The challenge also found choices that the evidence supports.

- **"The APIs find, the chain decides".** Re-reading every amount on-chain matches the lesson of the Morpho PAXG market (2024): the UI showed the right price while the oracle was wrong by 10¹².
- **Oracle against an independent price (G4 done).** Every oracle incident in the list would have shown as a gap between the oracle and the market.
- **Unrealised bad debt and liquidation curves per market.** This is the measure Credora and Gauntlet build on.
- **The registry's basis for sUSDe** already names the CEX-only print of 2025-10-10. That is the right venue distinction (K5 only asks the distribution to follow it).
- **Expected loss per year of Morpho Blue:** 0.46 % of collateral, close to Bundi's 0.62 % pure premium (K4).
- **The "risk multiple to exit" line** partly answers Team 2's breakeven-probability argument.
- **No cascade on blue-chip collateral** is consistent with 2025-10-10. It's the PT, with its thin pool, where the assumption fails (K9).

## 10. Recommended order

| Order | Gaps | Why first | Effort |
|---|---|---|---|
| 1 | K10, K11, K12 | The largest effect on a PT loop; IRM rules and PT pricing are deterministic, no new data source | S each |
| 2 | K1, K3, K5 | Fix known biases in the existing priors; one data call (TVL history) | S |
| 3 | K7, K8 | Oracle structure: decides which channel a shock takes; sources now available | M |
| 4 | K6 + named scenarios, K13 | Correlated stress and a tail-aware verdict; answers both teams | M |
| 5 | K16 | Depositor loss under a scenario, and d\* fed into `analyze`; the track's use case | M |
| 6 | K9, K14, K2, K4, K15 | Cascade loop, parameter uncertainty, off-chain priors, recalibration | M |

## 11. Resources

### Project files

| File | Used for |
|---|---|
| `riskdep/priors.py` | base rates, tiers, age factor, oracle prior |
| `riskdep/propagate.py` | loss per shock, liquidation rule |
| `riskdep/simulate.py` | Monte Carlo, horizon probability, tail metrics |
| `riskdep/decide.py` | carry, exit cost, verdict, de-lever sizing |
| `riskdep/discover.py` | oracle inference (`infer_oracle`), exit quote |
| `riskdep/registry.json` | depeg and hack severities, frequency parameters, PT stress, tail budget |
| `docs/how-risk-is-computed.md` | demo numbers, stated limits |
| `docs/scenarios-and-breakeven.md` | breakeven probability, horizon conversion |
| `ANALYSIS_MONITORING.md` | existing gaps M1–M7, C2, G4 |
| `comparison_team.md`, `teammate/team1.md`, `teammate/team2.md` | teammates' positions: breakeven p\*, scenarios first, cascade, run model, fixed-oracle drain |
| `PROVIDERS.md` | demo oracle identification (`MetaOracleDeviationTimelock`) |
| `docs/external/docs.morpho.org-developers-docs/contracts/irm.md` | AdaptiveCurveIRM: target 90 %, 4× steepness, 5-day doubling |
| `docs/external/pendle/docs.pendle.finance-pendle-v2-dev-docs/` | linear discount and Chainlink-style PT oracles |
| `fixtures/snapshot/` (DefiLlama `/hacks`, `/protocols`) | survivorship count (K1), priors on the snapshot (K4) |

### Methodology and data

Vendor material (Gauntlet, Chaos Labs, LlamaRisk, Credora) is self-published. LlamaRisk discloses that Ethena pays it.

- Bundi, DeFi loss frequency and severity (arXiv 2609.00911, 2026; merged 7-source dataset, negative binomial, GPD tails, pure premium per venue): https://arxiv.org/pdf/2609.00911
- SoK on DeFi attacks (IEEE S&P 2023): https://arxiv.org/pdf/2208.13035
- DefiLlama, 99 exploits in Q2 2026: https://newsletter.defillama.com/p/99-exploits-the-most-hacked-quarter-in-defi-history
- Chainalysis 2025 figures via The Block: https://www.theblock.co/post/382477/crypto-hack-2025-chainalysis
- Immunefi loss reports: https://immunefi.com/blog/research/immunefi-crypto-losses-q1-2025-report/
- Attacks on old contracts (DL News): https://www.dlnews.com/articles/defi/truebit-hit-by-exploit-as-attackers-increasingly-target-older-defi-protocols/
- Bitcoin Suisse loss-per-incident trend: https://www.finews.com/news/english-news/72926-defi-hacks-exploits-kelp-dao-analysis-bitcoin-suisse
- S&P Stablecoin Stability Assessment, USDe: https://spglobal.com/ratings/en/research/pdf-articles/250116-stablecoin-stability-assessment-usde-101611700
- S&P on USDe's risk weight in the Sky rating (DL News): https://www.dlnews.com/articles/defi/why-ethena-usde-got-a-high-risk-weighting-in-sp-global-sky-credit-rating/
- Moody's depeg count (The Block): https://www.theblock.co/post/261727/large-cap-stablecoins-have-depegged-609-times-this-year-moodys-analytics-says
- Depeg episodes by backing type (Comillas): https://repositorio.comillas.edu/xmlui/handle/11531/100397
- Chaos Labs, USDe funding-rate backtest: https://governance.aave.com/t/chaos-labs-ethenas-usde-and-susde-funding-rates-08-06-24/18565
- LlamaRisk, Ethena exposure on Aave: https://governance.aave.com/t/llamarisk-insights-addressing-ethenas-aave-exposure/23245
- Ethena risk documentation: https://docs.ethena.fi/solution-overview/risks
- Gauntlet VaR methodology: https://www.gauntlet.xyz/resources/improved-var-methodology
- Gauntlet Morpho curation methodology: https://www.gauntlet.xyz/resources/under-the-hood-unpacking-our-morpho-vault-curation-methodology
- Gauntlet, Nov 2025 liquidity stress: https://www.gauntlet.xyz/resources/market-report-liquidity-stress-period-nov-2025
- Credora, how Morpho is rated: https://docs.redstone.finance/docs/redstone-credora/how-to-rate-morpho/
- Credora Morpho vault methodology: https://credora-forum.discourse.group/t/morpho-vault-methodology/160
- Morpho liquidation docs: https://docs.morpho.org/learn/concepts/liquidation
- Morpho risk documentation: https://docs.morpho.org/morpho/concepts/risk-documentation
- Morpho bad debt, Vault V1 and V2: https://docs.morpho.org/curate/tutorials-v1/bad-debt/ and https://docs.morpho.org/curate/tutorials-v2/bad-debt/
- Aave PT-sUSDe listings (discount rates, LTV/LT/LB): https://governance.aave.com/t/arfc-onboard-susde-july-expiry-pt-tokens-on-aave-v3-core-instance/21878/3, https://governance.aave.com/t/direct-to-aip-onboard-susde-september-expiry-pt-tokens-on-aave-v3-core-instance/22313/3, https://governance.aave.com/t/direct-to-aip-onboard-susde-november-expiry-pt-tokens-on-aave-v3-core-instance/22894/2
- LlamaRisk, Aave's PT exposure (supply vs AMM depth, bad-debt scenarios): https://governance.aave.com/t/llamarisk-insights-aaves-pt-token-exposure-risk-outlook/22312
- Chaos Labs Pendle PT risk oracle: https://chaoslabs.xyz/posts/introducing-pendle-pt-risk-oracle and https://governance.aave.com/t/arfc-pendle-principal-token-risk-oracle/20962
- RedStone dynamic PT oracle: https://blog.redstone.finance/2025/11/20/redstone-dynamic-pt-oracle-unlocking-pendles-principal-tokens-in-defi-lending/
- Webacy on PT oracles: https://www.webacy.com/blog/congratulations-your-oracle-works
- Network simulation of DeFi systemic risk (stylised): https://nhsjs.com/2026/modeling-systemic-risk-in-decentralized-finance-a-network-simulation-approach/
- Composability contagion review: https://arxiv.org/html/2508.12007v1

### Incidents

Several figures come from secondary reporting and differ between sources; the gaps above use only the figures that sources agree on, or say "about".

- **Stream xUSD / Elixir deUSD / Morpho (Nov 2025):**
  - https://www.theblock.co/post/377961/elixir-sunsets-deusd-synthetic-stablecoin-following-stream-finance-unwinding-aims-full-redemptions
  - https://forum.arbitrum.foundation/t/update-stream-finance-xusd-situation-and-impact-assessment/30206
  - https://forum.morpho.org/t/mev-capital-elixir-usdc-vault-updates/767
  - https://decrypt.co/347285/stream-finance-stablecoin-plunges-77-protocol-fund-manager-loses-93-million
  - https://thresholdnetwork.notion.site/Elixir-deUSD-Morpho-Vault-Incident-Postmortem-November-2025-2b0725fcbcb080b79a44c27b1b3935a3
- **USDX depeg (Nov 2025):**
  - https://www.theblock.co/post/377917/synthetic-stablecoin-usdx-depegs-pancakeswap-lista
- **Resolv USR (Mar 2026):**
  - https://nexusmutual.io/blog/resolv-protocol-incident-report-by-nexus-mutual
  - https://theblock.co/post/394582/resolvs-usr-stablecoin-depegs-after-attacker-mints-80-million-unbacked-tokens-extracts-roughly-25-million
  - https://sentora.com/research/articles/the-resolv-hack-25m-from-a-single-compromised-key
  - https://forum.morpho.org/t/mev-capital-pts-usdc-vault-updates/1815
- **PT-reUSD TWAP liquidations on Morpho (Aug 2026)** (one detailed, unattributed analysis plus news coverage):
  - https://hackmd.io/@kanveuler/BJe_n1ivGe
  - https://cryptobriefing.com/morpho-liquidations-pendle-reusd-cascade/
- **2025-10-10 crash and the USDe print on Binance:**
  - https://www.21shares.com//research/why-did-ethenas-stablecoin-remain-stable-onchain-but-depegged-on-binance
  - https://www.galaxy.com/insights/research/cryptos-flash-crash-liquidation-binance-adl-auto-deleveraging
  - https://sentora.com/research/articles/the-pulse-flash-crash-liquidations-and-market-resilience
- **Morpho PAXG oracle misconfiguration (Oct 2024):**
  - https://thedefiant.io/news/defi/morpho-user-exploits-oracle-error-to-turn-usd350-into-usd230k
  - https://forum.morpho.org/t/retrospective-wsteth-wm-wbtc-wm-market-oracle-configuration/878
- **Morpho front-end incident (Apr 2025):**
  - https://cointelegraph.com/news/white-hat-intercepts-2-million-morpho-blue-hack
- **stETH discount (Jun 2022):**
  - https://fortune.com/crypto/2022/06/17/steth-token-trading-pool-crypto-investors
