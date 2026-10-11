# GAP: a challenge of the risk computation

This document challenges how `riskdep analyze` computes risk: the priors, the propagation, the simulation and the verdict. It is checked against the code, the project docs, the teammates' notes and outside evidence (incidents from 2022 to 2026, and the methods of risk firms and academic work). It sits next to `ANALYSIS_MONITORING.md`, which lists the known gaps (M1–M7, R1–R7). Status notes marked *(update 2026-10-10)* record what the `graph` work of plan `2026-10-10-sibling-markets` (sibling markets, oracle classes, liquidation curves per market, an optional eRPC proxy) changed for each gap. This file questions the model's assumptions themselves. Each gap gets an id `K<n>`, and a gap that extends an existing one names it.

Numbers for the demo position come from `docs/model/how-risk-is-computed.md` and the offline snapshot (`fixtures/snapshot/`, as of 2026-10-10). The position holds PT-sUSDE-26NOV2026 against USDC on Morpho Blue: collateral $3.93M, debt $3.41M, equity $0.52M, leverage 7.6×, LLTV 91.5 %, liquidation distance 5.16 %, verdict REDUCE.

## Contents

- [1. Verdict](#1-verdict)
- [2. Summary table](#2-summary-table)
- [3. Probabilities](#3-probabilities)
- [4. Severities and correlation](#4-severities-and-correlation)
- [5. Oracle and liquidation mechanics](#5-oracle-and-liquidation-mechanics)
- [6. Loss channels the model does not have](#6-loss-channels-the-model-does-not-have)
- [7. The decision rule](#7-the-decision-rule)
- [8. Vault depositors](#8-vault-depositors)
- [9. Against the challenge brief](#9-against-the-challenge-brief)
- [10. What holds up](#10-what-holds-up)
- [11. Recommended order](#11-recommended-order)
- [12. Resources](#12-resources)

## 1. Verdict

**Update 2026-10-11.** Since this review, the tool answers the brief's question as asked: incident mode for a position and for a vault depositor (K20 done), time to impact from the oracle's type (K22 partial), and a user-defined book of vaults in USD (K21 partial). It was run on the brief's sponsor's own vault (Belem RWA EURCV) and on the curator's seven Ethereum vaults (`ROCK-VAULT.md`). Vault and book incidents now run through the shock engine when the vault's graph is recorded, so `analyze` and `shock` give one number and the squeeze and sibling markets enter the vault's figures (plan `2026-10-11-one-number`; part of K9). Pharos's keyless dependency graph now adds issuer grades, off-chain backing and common-mode groups (plan `2026-10-11-pharos`; part of K19). That work found two new gaps, K26 (wrapped collateral not matched) and K27 (liquidations of issuer-priced collateral assumed).

Later the same day: the breakeven p\* and a conditional distribution of the loss of staying (K21, K14, K6 in part); the brief's ten pockets with an 11 % unwind; the PT loop's rate and implied-yield channels as incidents (K10, K11); feed freshness and TVL concentration (K23, K25 in part); and a **backtest** of the 2026-08-25 PT-reUSD liquidations, the case K8 cites: given the oracle's observed fall, the model predicted the same 20 borrowers as liquidated, and the USDC market's debt and incentive within 0.8 % (K8, K9 in part). **Known incident, no prior.** The brief starts from a known incident, and every known-incident answer (incident mode, vault and book incidents, the shock engine, p\*, the conditional draw) takes it as given. The gaps about the hack-history priors (K1–K5, K15, K17, K18) concern only `analyze --demo`'s ex-ante Monte Carlo, the secondary view. The status of every gap is in the summary table (§2), and the order of the remaining work is in `NEXT_STEP.md` §3. The review below is kept as written on 2026-10-10.

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

Its exploit priors rest entirely on a 5-year hack history. That history is biased downward by survivorship, and it is stale in a field whose attack mix changes every year. It should set the base rate only, with protocol-specific signals moving it within bounds (§3, K17–K18). Its severity tails are thin for synthetic dollars (§4).

None of these gaps means the demo verdict is wrong. Every one of them points the same way, though: **more risk than reported**.

**Against the challenge brief (§9),** the tool covers the brief's own worked example: the five layers of a Pendle PT, a stay-or-exit verdict with execution cost, a demo on real data. It misses the brief's question in the form it is asked:
- the impact **when a component is hit**, rather than a probability-weighted average (K20);
- on a **book** of pockets, with the stay-or-exit trade-off made explicit as a breakeven probability (K21);
- **how fast** the impact arrives (K22).

Of the scope items the brief names, feed quality, vaults in external venues, TVL concentration and other chains are partial or missing (K23–K25, C5).

## 2. Summary table

| Id | Gap | Direction | Evidence | Impact | Effort | Status (2026-10-11), step in `NEXT_STEP.md` |
|---|---|---|---|---|---|---|
| K1 | Hack base rate drops hacked protocols whose TVL has since fallen below $1M | under-states | 305 of 1,070 hacks dropped on the snapshot | high | S | open (B5) |
| K2 | Hack ledger misses off-chain failures (custodian, fund manager, key compromise) | under-states | Stream, Resolv | high | M | open (B5) |
| K3 | Lending exploit and oracle layers double-count oracle exploits | over-states | Lending category includes oracle hacks | low | S | open (B5) |
| K4 | Morpho Blue exploit prior (5.0 %/yr) far above other anchors | over-states frequency | Credora 0.13 %/yr; never exploited | low | S | open (B5) |
| K5 | Depeg severity tail too thin for a synthetic dollar | under-states tail | P(depeg > 50 %) = 0.002 % in the model; USR −97 %, xUSD −77 %, deUSD −98 % | high | S | open (B5) |
| K6 | Layers independent; only issuer hack → depeg is linked | under-states tail | Nov 2025 cluster; Resolv chain; PT-reUSD | high | M | partial: shared assets, oracles and feeds in `graph`; Pharos common-mode groups named in incidents; the conditional draw shares one incident across a book's vaults (plan `2026-10-11-conditional`); the ex-ante simulation still draws layers independently (B5) |
| K7 | Oracle is "market-tracking" or "fundamental"; real oracles are composites | wrong mechanism | demo oracle is a `MetaOracleDeviationTimelock`; min(TWAP, linear) oracles | high | M | partial: `oracle_class.py` used by `graph`, incident mode and the ex-ante mode (D96); meta-oracle sources and switch read; Midas NAV feeds recognised; constant-price split by kind (exchange rate, published, linear discount, fixed), which decides whether a markdown reaches the oracle and so where the engine drains (plan `2026-10-11-oracle-kinds`); the ex-ante simulation keeps two modes |
| K8 | Oracle manipulation of a thin Pendle pool is not a loss channel | under-states | PT-reUSD, 33 liquidations, LLTV 91.5 % | high | S–M | partial: backtested given the observed oracle fall (plan `2026-10-11-backtest`: the same 20 borrowers, USDC debt and incentive within 0.8 %); a second episode, the 2025-10-10 crash, misses no liquidated borrower in six markets (plan `2026-10-11-backtest-crash`); the pool move as a loss channel for the PT position (plan `2026-10-11-pool-move`); the pool at a past date rebuilt from its state: the backtest's fall traces to a 5.4M PT sale, which the pool's math reproduces within 1.7 %; from that sale alone, the model predicts the same liquidated borrowers, none missed (plan `2026-10-11-pendle-pool`, D210) |
| K9 | Liquidation at the oracle price with LIF; no slippage, no cascade, no partial liquidation | under-states | LlamaRisk PT supply ≫ AMM depth; Gauntlet, Credora simulate it | medium | M | partial: the shock engine sells liquidated collateral into its market (Pendle quotes) across held and sibling markets, and vault incidents use it (plan `2026-10-11-one-number`); the backtest confirms the liquidation set and sizes (plan `2026-10-11-backtest`); returned liquidity and the squeeze at a past date open (B6) |
| K10 | Borrow-rate risk of the AdaptiveCurveIRM | under-states | rate ×4 at 100 % utilisation, curve doubles in 5 days | high | S | partial: `--shock borrow_rate=` (plan `2026-10-11-pt-channels`); not drawn in the Monte Carlo (B1) |
| K11 | PT implied-yield (duration) risk | under-states | +20 pp implied yield = −2.2 % PT price on the demo | medium | S | partial: `--shock pt_yield=` (plan `2026-10-11-pt-channels`); not drawn in the Monte Carlo (B2) |
| K12 | Exit cost (one-off) compared with a 30-day loss, while holding to maturity is free | biases to STAY | maturity in 46.6 days | medium | S | partial: the verdict states the hold-to-maturity path against leaving now (plan `2026-10-11-alerts-and-verdict`); the exit cost after the incident's own liquidations, from real quotes, with the part that can still leave (plan `2026-10-11-stressed-exit`); other holders' sales not counted |
| K13 | EXIT rule uses the mean only; CVaR 98 % of equity still gives REDUCE | biases to STAY | Bundi: yields cover the mean, not the tail | medium | S | partial: EXIT when de-levering still leaves CVaR99 ≥ 90 % of equity (plan `2026-10-11-alerts-and-verdict`); the conditional distribution shows a vault's tail (plan `2026-10-11-conditional`) |
| K14 | Point estimates without uncertainty; Poisson-style one event per layer | hides uncertainty | dispersion index 3.27; ξ unstable | medium | M | partial: the expected loss printed with its 95 % interval, and a reason inside it reads "about equal" (plan `2026-10-11-judge-path`); vault and book incidents give a distribution (plan `2026-10-11-conditional`); priors still point estimates (B5) |
| K15 | Age factor and PT stress ×1.5 have no empirical basis | unknown | no study found | low | S | open (B5) |
| K16 | Depositor loss under a scenario still missing for vaults (drain d\* done in the watches) | missing | Team 2; deUSD, wstUSR | high | M | mostly done: `analyze --vault --shock token=…` (plan `2026-10-11-vault-incident`), through the shock engine, with wrapped collateral (K26 done); missing: loans at the market price, the drain as a loss channel (B8) |
| K17 | Exploit prior rests only on a 5-year hack history; attack mix shifts yearly | stale, noisy | top classes change every year; a 2-year window raises Morpho Blue to 8.6 % | high | S | open (B5) |
| K18 | No protocol-specific signal (admin powers, audit scope, insurance price, reputation) | blind to the protocol | 67.6 % of audited incidents outside audit scope (H1 2026); Nexus prices 1.05–1.44 %/yr | medium | S–M | open (B5); admin powers already read by `admin.py` |
| K19 | Discovery stops at the issuer; admin surface not in `analyze` | shallow | brief scores depth at 30 %; issuer deps typed by hand | high | M | partial: `graph` has siblings, `wraps` edges, the admin surface, issuer NAV feeds, Pharos off-chain backing, feed freshness and protocol TVL; and the PT report now carries them too (plan `2026-10-11-depth`); the venues behind USDe (plan `2026-10-11-venues`) and Sky's backing behind USDS, DAI and sUSDS, read on-chain (plan `2026-10-11-sky`); other chains open |
| K20 | No "this component is affected now" input; impact is always probability-weighted | missing | brief's worked example marks the oracle "incident" | high | S | done: `analyze --shock`, `--vault`, `--book` (also over HTTP); `OracleDivergence` on a borrowed market carries the impact; `OracleImpact` carries the vault's and the depositor's loss and the verdict when a vault market's oracle falls (plan `2026-10-11-detect`) |
| K21 | No book (pocket weights), no breakeven p\*, no single headline number | missing | brief's 10 × 10 % book, 11 % unwind example | high | S–M | partial: a user-defined book of vaults in USD with a headline (plan `2026-10-11-vault-book`); the breakeven p\* per vault and for the book, and the vault to act on first by lowest p\* (plan `2026-10-11-breakeven`); the brief's ten pockets with an 11 % unwind (`pocket` weighting, `--exit-cost`, plan `2026-10-11-judge-path`); the conditional distribution of the book (plan `2026-10-11-conditional`); borrow pockets next to vaults, the brief's PT loop among them (plan `2026-10-11-mixed-book`) |
| K22 | No time to impact or time to exit in `analyze` | missing | brief asks "and how fast"; USR −97 % in 17 min | medium | S | partial: time to impact per oracle type, including the PT yield and the borrow rate (plan `2026-10-11-pt-channels`); time to exit is "one block" at today's quote (B3) |
| K23 | Feed quality (heartbeat, staleness, sources, shared feed) not measured | missing | named in the brief's scope | medium | S–M | partial: each feed's freshness against its own rhythm, in `graph` and vault incidents (plan `2026-10-11-feed-quality`); the band, timelock and exit gates in the fork demo's `admin.py` (plan `2026-10-11-fork-demo`); `FeedStale` in `watch --vault` (plan `2026-10-11-alerts-and-verdict`); a feed or oracle read by several markets flagged as shared (plan `2026-10-11-shared-and-supply`, D215) |
| K24 | Vaults or hedges in an external venue (perp, CEX) not covered | missing | named in the brief's scope; Belem runs market-neutral | medium | M–L | partial: the venues behind USDe (exchanges with their share of the backing, custodians, reserve fund) in `graph` and the PT report, a `venue=` incident through every incident path, a funding-stress line (plan `2026-10-11-venues`); Vault V2 adapters into non-Morpho venues and Belem's own hedges open |
| K25 | Concentration of TVL (protocol share of chain, position share of pool and supply) not measured | missing | named in the brief's scope | medium | S | partial: each protocol's share of DeFi and of its category in `graph` (plan `2026-10-11-feed-quality`); a collateral's share of its supply posted in Morpho, and the PT position's share of its market and of its pool (plan `2026-10-11-shared-and-supply`, D216–D217) |
| K26 | A vault incident matches a token only as the markets' direct collateral, not through what wraps it (a PT, an ERC-4626 share, a vault of vaults) | under-states reach | trUSD and wYLDS match no RockawayX market, although PT-trUSD, etrUSD and wYLDS-based markets depend on them | medium | S–M | done: plan `2026-10-11-wrapped-collateral`; etrUSD (no `asset()`) stays opaque |
| K27 | A vault incident assumes liquidations happen; issuer-priced collateral needs a buyer of the issuer's token, and the liquidity liquidations return is not modelled | unknown direction | Belem: 3.68M of mGLOeuro-backed debt liquidatable at a 10 % NAV cut, with one market as the vault's only liquidity source | medium | M | partial: the no-liquidator branch, exit liquidity quoted live on KyberSwap at the size the incident liquidates (plan `2026-10-11-exit-liquidity`; the registry's hand measurements as the fallback), borrower concentration and default (plan `2026-10-11-borrower-concentration`); the no-liquidator branch drawn in the conditional distribution (plan `2026-10-11-conditional`); missing: the liquidity liquidations return (B6) |

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

### K17. Hack history carries all the weight, over a window that is too long

`exploit_p_year` comes entirely from past hacks: a TVL tier rate over 5 years, × a category multiplier, × an age factor. DeFi changes faster than that window.

**The attack mix shifts from year to year.** Most frequent classifications in DefiLlama's hack record (snapshot):

| Year | Hacks | Top classifications |
|---|---|---|
| 2021 | 127 | Protocol Logic, Token & Share Accounting, Oracle Manipulation |
| 2022 | 184 | Access Control, Oracle Manipulation, Frontend & Infrastructure |
| 2023 | 197 | Access Control, Oracle Manipulation, Protocol Logic |
| 2024 | 217 | Access Control, Protocol Logic, Token & Share Accounting |
| 2025 | 148 | Access Control, **Key Compromise**, Token & Share Accounting |
| 2026 (to 10 Oct) | 292 | Access Control, Token & Share Accounting, Oracle Manipulation, **Bridge & Cross-Chain** |

Other sources say the same thing:
- **Chainalysis:** private-key compromise at centralised services was 88 % of Q1 2025 losses, and DeFi hack losses did not rise with TVL.
- **Sentora:** the share of exploits that come from smart-contract bugs is shrinking.

Designs also change. An immutable, formally verified core like Morpho Blue has little in common with the 2021 lending forks that fill the Lending category.

**A shorter window does not lower the prior.** Here is `exploit_p_year` re-run on the snapshot with only the window changed:

| Window | Hacks kept | ≥ $100M tier | Pendle | Morpho Blue | Ethena | Lido | Sky |
|---|---|---|---|---|---|---|---|
| 5 years (current) | 145 | 34 hacks, 2.66 %/yr | 1.21 % | 5.03 % | 1.33 % | 0.93 % | 2.62 % |
| 3 years | 102 | 23, 2.99 % | 1.61 % | 5.99 % | 1.50 % | 1.05 % | 2.80 % |
| 2 years | 85 | 22, 4.30 % | 1.66 % | **8.59 %** | 2.38 % | 1.50 % | 3.62 % |
| 1 year | 59 | 17, 6.64 % | 3.71 % | 13.28 % | 5.29 % | 2.32 % | 2.32 % |

The rates go **up** as the window shortens, for two reasons:
- recent years had more hacks (2026 is already a record);
- survivorship (K1) has had less time to remove recent victims.

The rates also get **noisier**. The ≥ $100M tier rests on 22 hacks over 2 years, and one category multiplier can swing a protocol by 2×: Morpho Blue goes from 5.0 % to 8.6 %.

So a 2-year window makes the history more **relevant** but not more **reliable**. The real issue is that this one noisy, backward-looking number is the whole exploit prior.

**Fix: keep the history, cap its weight.**
1. **Decay instead of cutting.** Weight each hack by its age with a half-life of about 1–2 years: a 2024 hack counts half as much as a 2025 one. That follows the shift in attack mix without discarding data. Put the half-life in `registry.json` with its basis.
2. **Use the history for the level, not for the protocol.** History is good at one thing: how often protocols of this kind and size get hacked. Keep it as the **base rate** of the category and tier, and shrink small cells toward the overall rate (credibility weighting, as Bundi does).
3. **Let protocol-specific signals move it, within bounds** (K18). The exploit prior becomes base rate × a protocol multiplier, the multiplier clipped to a stated range (for example 0.25×–4×). The history then sets the order of magnitude, the protocol's own evidence sets the position inside it, and neither can dominate.
4. **Show both parts in the report:** "category base rate 2.7 %/yr, × 0.4 for immutable formally verified core with no exploit in 2.7 years → 1.1 %/yr". A reader can disagree with one factor without rejecting the whole number.

This replaces the current age factor (K15), which becomes one input of the multiplier.

### K18. Protocol-specific signals: audits, reputation, insurance, admin powers

The model knows a protocol only by its TVL, category and age. Risk firms use more:
- **Credora** starts from a base probability of default and applies modifiers (oracle risk, governance, curator track record, concentration).
- **DeFiSafety** scores process quality: code, documentation, tests, admin controls, oracles. Its score decays as its report ages.
- **Exponential** grades protocol risk from design, governance and security posture.

These signals are harder to compute than a hack count, and none of them is proof. But they describe **this** protocol rather than its category.

| Signal | What it says | Evidence | How to get it | Ease |
|---|---|---|---|---|
| **Admin powers**: upgradeable or not, who is admin, timelock, multisig threshold | Whether a key or a governance vote can change the code or drain funds; access control and key compromise are the most frequent hack classes since 2022 | Hack record table in K17 | **Already read** by `admin.py` (EIP-1967 slots, owner, Chainlink aggregator) for every watched contract | easy |
| **Code changed since the last audit** | Whether the deployed code is still the audited code | In H1 2026, 46 of 68 incidents with a prior audit (67.6 %, 94 % of losses) had an attack path **outside every audit's scope** (Czech Technical University / ack3 preprint, via news) | Proxy `Upgraded` events (already watched by `admin.py`) after the last audit date | medium |
| **Audits** (number, firms, dates) | Whether the code was reviewed | Weak alone. Halborn: about 20 % of the top-100 hacked protocols were audited. Sentora: about 66 % of hacks involved audited code. Exponential: no published audit → 68 % higher chance of a negative event. Stream and Elixir were both audited | DefiLlama `audits` is a status flag, not a count: on 2026-10-10 all 7 protocols checked show `"2"`, Stream and Elixir included, and 156 of 257 protocols ≥ $100M show `"0"`. The real list needs `audit_links` or a registry entry | hard |
| **Insurance price** | What capital providers charge to cover a loss: a market-implied upper bound on the yearly probability × severity | Nexus Mutual × Symbiotic listing: Aave v3 1.23 %/yr, Pendle 1.05 %, selected Morpho vaults and markets 1.44 % (second-loss layer, launch prices) | Nexus Mutual `https://api.nexusmutual.io/v2/capacity`, keyless, 478 products with min/max annual price; the product-to-name mapping is not in that endpoint | medium |
| **Time × TVL without exploit** (Lindy) | How much value the code has protected, and for how long | No study found; the argument holds for **immutable** code only, since each upgrade resets the clock. Mature, audited protocols were still exploited in 2025 (Balancer $128M, Cetus $220M) | DefiLlama TVL history × time since the last `Upgraded` event | medium |
| **Formal verification, immutability** | Whether whole classes of bugs are excluded | Morpho Blue: immutable, formally verified, no core exploit found | Registry entry with a link | easy, by hand |
| **Bug bounty** (max payout vs TVL) | Incentive to disclose rather than exploit | No study ties it to fewer hacks; a heuristic only | Immunefi pages, no official API | hard |
| **Off-chain dependencies** (custodians, CEX, signing keys, fund manager) | Exposure the hack record does not see (K2) | Stream (manager loss), Resolv (cloud signing key) | Registry entry per issuer, from its docs | by hand |
| **Reputation, team track record** | Response to past incidents; for vaults, the curator's history | Pendle paused and protected about $105M in the Penpie exploit; MEV Capital realised bad debt in Nov 2025, Steakhouse had no Resolv exposure | Registry entry with a dated basis | by hand, subjective |
| **Third-party ratings** | An outside judgement to compare with | S&P rates USDe 5 (weak); Credora rates Morpho vaults | Credora, S&P reports; no keyless API found | hard |

**What to keep in mind:**
- **Reputation fails exactly when it matters.** Stream had an audit and well-known curators lent to it. Signals must stay bounded multipliers on a base rate, never a replacement for it.
- **A by-hand signal is a judgement.** It goes in `registry.json` with a dated basis and a source, like the depeg priors, so it can be challenged and refreshed.
- **Start with what is already read.** Admin powers and upgrades since the last audit come from `admin.py`, which the watches already run. The insurance price is one keyless call. Audits, reputation and ratings can follow, by hand, for the handful of protocols in the registry.

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

- **Age factor** (×2 under one year, ×0.7 over three years). No survival study of DeFi protocols by age was found. Evidence runs both ways: attacks on old unmaintained contracts (Truebit, Yearn v1) against a falling loss per incident. Label it as a judgement in `registry.json`, and fold it into K17's protocol multiplier, where the time since the last upgrade (Lindy for immutable code) replaces the time since listing.
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
- *(update 2026-10-10)* The `graph` command now joins sibling markets to held ones through the asset, oracle or feed they share, so the common-mode links are visible as shared nodes. They are not yet used as correlation: `simulate.run` still draws each layer of one position independently, and no book combines positions (K21).

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
- **Status: partial.** `oracle_class.py` (plan `2026-10-10-sibling-markets`, D82–D84) reads the structure for the `graph` command: base vault, composites (`FEED_1`/`FEED_2`, as in the Ojo min(TWAP, linear) feed under PT-reUSD) and wrappers (`innerOracle`), Pendle's `twapDuration` and `baseDiscountPerYear`, then the feeds' round history, then names. It labels each oracle `price-tracking` or `constant-price`, still two classes, with the input that decided. The shock engine also ties each input to the market it tracks (D115): PT-reUSD's oracle is Pendle PT_TO_ASSET, so it follows the PT's pool but not reUSD's dollar price. `analyze` still uses the price inference, and a `MetaOracleDeviationTimelock` stays `not classified`.

### K8. Liquidation without any incident

On 2026-08-25, one wallet spent $320k on YT-reUSD over 9 minutes. The trades pushed the PT's implied yield from about 11 % to more than 20 %. A min(TWAP, linear) oracle dropped 0.5–2.8 %, and Morpho liquidated 33 PT-reUSD positions at LLTV 91.5 %. Borrowers paid about $946k of liquidation bonus. There was no bad debt, and the price recovered within five hours. (Single detailed source plus news corroboration; see §12.)

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
- *(update 2026-10-10)* The `graph` command now computes, for every held **and sibling** Blue market, the liquidation curve with the collateral it would seize (D81 of plan `2026-10-10-sibling-markets`). That is the sale pressure the loop needs, across every market that holds the same collateral, not only the watched ones.
- **Fix:** the loop already proposed (collateral seized at a drop → Pendle price impact for that size → new drop, until stable), with the per-market curve that `market_risk.py` already computes.
- **Status: partial.** `riskdep shock` runs that loop across every market taking the collateral (plan `2026-10-10-propagation-engine`, D109, D112–D114). The impact comes from Pendle quote ladders: PT into its pool, then the underlying sold for dollars. Each ladder has a capacity beyond which liquidations cannot complete, and a PT floor applies where a buyer to maturity earns 50 % APY. The quotes showed the constant-product model about 100× too steep, and the cliff in the exit for dollars ($12.35M for reUSD), not in the pool. `analyze` still liquidates at the oracle price with no slippage, and no episode has been replayed yet (`docs/analysis/NEXT_STEP.md` step 11).

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

1. ~~**A depositor loss under a scenario**~~ **done 2026-10-11** (`analyze --vault --shock token=…`, plan `2026-10-11-vault-incident`; a book of vaults in plan `2026-10-11-vault-book`). Original text: Σ over the vault's markets of its share of supply × the market's bad debt at that drop. `market_risk.value()` already returns bad debt at a given drop. **Still missing.**
2. ~~**The fixed-oracle drain d\*** (Team 2)~~ **done** in the watches (`riskdep/drain.py`, `DrainWindow` alert, `docs/watch/drain-threshold.md`). With a linear-discount, hardcoded or NAV oracle, a depeg never liquidates, and borrowers can loop the depegged asset in until caps are full; that is what happened on wstUSR, where the oracle marked $1.13 while the market was near $0.63. What remains is to feed it into `analyze`: the drained amount is a loss channel for a depositor, and the probability of crossing d\* comes from the depeg prior (K5).

Incidents add a third: the **realisation rule** depends on the vault version.
- V1.0 realises bad debt for every holder at once.
- V1.1 doesn't, so the last holders take it: a run incentive.
- V2 realises it through `realAssets()`.

A V2 vault holding V1.1 shares through `MorphoVaultV1Adapter` inherits the V1.1 behaviour (see `REPOSITORY_ADD.md`).

### K26. Wrapped collateral is not matched (found 2026-10-11)

A vault incident (`--shock token=<collateral>:<fall>`) hits the markets whose collateral **is** that token. A markdown of a token reaches more markets than that: those whose collateral wraps it. In the RockawayX book, `token=trUSD:0.30` and `token=wYLDS:0.30` hit nothing, although PT-trUSD, PT-strUSD, etrUSD (a vault of Tori vaults) and wYLDS-based markets depend on them (`ROCK-VAULT.md` §5.2).

- *(done 2026-10-11, plan `2026-10-11-wrapped-collateral`: `token=trUSD:0.30` now reaches the PT-trUSD, PT-strUSD and strUSD markets of two vaults, 1.61M USD (2.03M since vault incidents run through the shock engine, which prices the squeeze on strUSD's thin market); a market whose oracle does not track a market counts a hidden shortfall, D127.)*
- **Fix:** resolve each market's collateral to what it wraps, through a PT's SY and yield token, an ERC-4626 share's `asset()` and a vault of vaults' underlying (`siblings.underlyings` and the `wraps` edges already resolve the first two), and pass the fall through, according to the oracle's class (`NEXT_STEP.md` A1).

### K27. Liquidations of issuer-priced collateral are assumed (found 2026-10-11)

A vault incident values every borrower at the shocked oracle price and counts the bad debt as if every liquidatable position were liquidated. For collateral priced by the issuer's NAV (mGLOeuro, PST, fxSAVE, strUSD…), a liquidator receives the issuer's token, which may have no market: it has to be redeemed with the issuer. Two consequences follow:

- **If no liquidator acts,** the bad debt stays unrealised, the share price stays at par, and the market's liquidity stays locked; on Belem the hit market is also the vault's only liquidity source.
- **If liquidators act,** the debt they repay comes back as free liquidity, which changes what depositors can withdraw. Neither branch is modelled.

- *(partial 2026-10-11, plan `2026-10-11-borrower-concentration`: each hit market shows its collateral's exit liquidity (`exit_liquidity` in the registry, measured once from KyberSwap quotes) and, when thin or absent, the loss if nobody liquidates; the concentration of its borrowers; and `--shock borrower=<target>:<recovery>[:<n>]` prices the default of the largest borrowers, on any vault or book. `BorrowerConcentration` warns in the vault watch. Belem's mGLOeuro market is owed by one borrower: its default at 50 % recovery costs 1.05M EURCV, 22 % of the vault.)*
- **Fix, rest:** the liquidity returned by liquidations, in the cascade of `NEXT_STEP.md` B6, and the no-liquidator branch as a draw in the conditional Monte Carlo (A4); exit liquidity measured live rather than recorded.

## 9. Against the challenge brief

The brief is `docs/hackaton_instruction/Hackathon_DeFi-Risk-Dependency-Challenge_EN_v1.pdf` (Belem Capital, EPFL Hackathon 2026). Its task is: "Automatically identify the dependencies of a position, and estimate the potential economic impact on that position when one of them is affected", then answer "stay in the position, or is the expected loss high enough to justify exiting despite execution costs?". The judging is:
- dependency discovery 30 %;
- impact estimation ("is the number defensible") 30 %;
- decision usefulness 25 %;
- a working demo on real data 15 %.

### Requirement by requirement

| The brief asks | What the tool does | Status | Gap |
|---|---|---|---|
| The worked example: a Pendle PT, 5 layers (chain, yield issuer, oracle, PT AMM, lending market) | `analyze` builds exactly these layers for a PT on Morpho Blue | met | — |
| Discover dependencies **automatically** | Chain, Pendle market, oracle and Morpho market are found on-chain and through the APIs. The issuer's own dependencies (custodians, CEX, keys) are typed by hand for 4 issuers. The admin surface is found automatically, but only by `graph` and the watches, not by `analyze`. *(update 2026-10-10)* `graph` also finds sibling Blue markets and `wraps` edges | partial | K19 |
| Discovery **depth** (30 %) | 5 layers for a PT. Stops at the issuer: no look-through into what backs it (USDe's hedges and custodians, sUSDS's PSM and USDC) | partial | K19, M7 |
| Impact "when **one of them is affected**" | The report gives, per layer, the loss if it happens ("Loss if it happens", the mean over a severity draw). There is no way to say "**this** oracle is affected now, at this size" and get the impact; the input is always a probability, never an observed incident | partial | K20 |
| "Is the number defensible" (30 %) | Every number has a basis, but K1–K18 show the exploit, depeg and rate parts are biased or missing | partial | K1–K18 |
| Stay or exit "despite execution costs" | EL vs carry vs exit cost, a CVaR tail budget, de-lever sizing, a real Pendle quote | met, with K12 and K13 | — |
| The **book** example: ten pockets of 10 %, one affected, unwinding costs 11 % | Works per position in USD. No book, no pocket weight, no loss as a share of the book; the 11 % example can't be entered or reproduced. *(2026-10-11: a book of vaults exists, with the loss as a share of the book; borrow and PT pockets and p\* are still missing, so the 11 % example cannot be entered yet)* | partial | K21 |
| "Makes that trade-off explicit" | One line: "a full exit would only pay if probabilities were k× the estimates". No breakeven probability, which is exactly the "expensive and certain vs cheap and uncertain" trade-off | partial | K21 |
| "What it does to your book, **and how fast**" | Watches alert block by block; the exit queue and the drain window give time for vault depositors. `analyze` has one 30-day horizon and no time to impact or time to exit | partial | K22 |
| "Turn ... into **one number**" | A verdict label plus several dollar amounts; no single headline number a manager reads first | partial | K21 |
| Any ecosystem: Solana, EVM chains, Canton, Tempo | Ethereum mainnet only (C5). Belem's mandates include SOL | missing | C5 |
| Oracle dependency and **feed-quality** analysis | Oracle mode inferred, verified on Etherscan, admins and aggregator changes watched, oracle vs DefiLlama price. Feed quality itself (heartbeat, deviation threshold, staleness, number of sources, single feed under several markets) is not measured. *(update 2026-10-10)* `graph` classifies every oracle input as price-tracking or constant-price from its structure and round history | partial | K23, K7, R3 |
| **Vaults that deploy into an external venue**, e.g. a perp exchange | Not covered. Morpho Vault V2 adapters other than Morpho markets are opaque (C4); no perp venue, no off-chain venue | missing | K24 |
| **Protocols concentrating a large share of on-chain TVL** | Not measured. Lender concentration inside a market is (R4); the share of a chain's TVL that one protocol holds is not | missing | K25 |
| Working prototype on real data (15 %) | Live and offline runs on real positions, recorded replays, tests | met | — |
| Belem's context: capital only on protocols that clear a **pre-selection scorecard**; positions are fund deposits and market-neutral strategies | The priors use no scorecard (K18); `analyze` covers a borrower, not a depositor (K16); delta-neutral legs are not modelled (K24). *(2026-10-11: `analyze --vault` and `--book` cover depositors and curators, run on Belem's own vault)* | partial | K18, K24 |

### K19. Discovery stops at the issuer

The brief scores discovery on "depth and correctness". `analyze` reaches the issuer and stops. The issuer's own dependencies are text in `registry.json`, not discovered:
- USDe: hedges on CEXs, custodians, collateral;
- sUSDS: the USDC peg module and the Sky core.

Their failures are exactly the ones that broke issuers in 2025–2026 (K2). The admin surface (proxies, owners, feeds) **is** discovered automatically by `admin.py`, but only `graph` and the watches use it.

- **Fix:**
  - add the admin surface to `analyze`'s graph as layers with their own priors (K18);
  - look through one level where it is on-chain: sUSDS → USDS → PSM → USDC, or the ERC-4626 vault behind an exchange-rate oracle;
  - keep the off-chain part as typed registry nodes, drawn in the graph, so the depth is visible even where it is not computed.
- *(update 2026-10-10, partial)* The `graph` command now goes one hop sideways and one level down:
  - **sibling markets**: the Blue markets that share a held market's collateral, underlying or collateral-side price input, or lend that collateral, above $1M of supply (`siblings.py`);
  - **`wraps` edges**: an ERC-4626 share to its `asset()`, which is the on-chain look-through for vault-share collateral;
  - **oracle inputs** decomposed, each with its class.

  `analyze` still stops at the issuer, and siblings are found on Morpho Blue only: Euler, Aave, Silo or Fluid markets on the same collateral are not in the graph (R5 in `ANALYSIS_MONITORING.md`).

### K20. No "this component is affected now" mode

*(update 2026-10-10, done)* `analyze --shock EVENT=SEVERITY` gives the impact of a known incident, the time to impact and a verdict with the incident certain (plan `2026-10-10-incident-mode`, D89–D95). In `watch --user`, an `OracleDivergence` alert on a borrowed market carries the impact on that borrow (D93). Other alert types do not carry one yet.

The brief's worked example marks layer 3, the oracle, with "incident". Its question is conditional: a component **is** hit, what does it do to the position? `analyze` answers an unconditional question: what loss to expect over 30 days, given yearly probabilities. The per-layer "loss if it happens" comes close, but at a drawn severity and with no input from the user.

- **Fix:** the scenario table already proposed in `comparison_team.md` §4.2. One call to `propagate.loss()` per named shock, plus a CLI input for an observed incident:
  - `--shock oracle=-0.10`;
  - `--shock issuer_depeg=0.08`;
  - `--shock pool=-0.03`.

  The output is the loss, whether the position is liquidated, and the verdict with that probability set to 1. The watches could call the same function when they raise a critical alert, which turns an alert into an impact number.

### K21. No book, and no breakeven

The brief's example is about a book: ten pockets of 10 %, one affected, an 11 % unwinding cost. Three things are missing to reproduce it:
1. **A book.** A list of positions with their weights, so the loss and the exit cost read as a share of the book, and two pockets that share a layer are combined (M6).
2. **The breakeven probability** p\* = exit cost ÷ L(s) (Team 2, `docs/model/scenarios-and-breakeven.md`). On the brief's numbers, an 11 % exit cost against a total loss of the pocket gives p\* = 11 %: exit if you believe the incident wipes out the pocket with more than 11 % probability over the horizon. That's the trade-off "made explicit", and it does not depend on a base rate.
3. **One headline number.** For example "expected loss X % of the book; exit pays above p\* = Y %", above the verdict.

### K22. "How fast" is not an output of `analyze`

*(update 2026-10-10, partial)* Incident mode reports the time to impact from the oracle's type: a feed's next update, a Pendle TWAP window, a meta-oracle's challenge timelock through its live source, or never for a constant-price oracle. On the demo it found that the oracle's live source is a Pendle linear discount, so a depeg liquidates nothing for 16 hours and everything after the switch to the `USDe / USD` backup. The time to exit is still "one block at today's quote".

The brief asks what an incident does "and how fast". For a PT loop, speed decides everything:
- USR fell 97 % in 17 minutes;
- PT-reUSD's oracle moved in 9 minutes;
- an exit through the Pendle pool takes one block, but only at the depth left in the pool.

`analyze` has a 30-day horizon. The watches react in 12 seconds but give no impact number (K20).

- **Fix:** report, per scenario, the time from the incident to liquidation (zero for a TWAP move, the timelock for a meta-oracle switch, never for a linear discount) next to the time to exit.

### K23. Feed quality is not measured

The brief names "oracle dependency and feed-quality analysis" in its scope. What exists:
- oracle-mode inference;
- Etherscan verification;
- aggregator-change and admin events;
- the oracle vs DefiLlama price, warned from 3 %.

What a feed-quality analysis would add:
- heartbeat and deviation threshold;
- age of the last update compared with the heartbeat (the Morpho oracle itself does not check staleness);
- the number of nodes or sources;
- whether one feed carries several markets or positions (R3);
- for a meta-oracle, which source is live and its timelock.

Chainlink publishes most of these for each feed (`REPOSITORY_ADD.md`, priority 2).

*(update 2026-10-10)* `oracle_class.py` now reads each feed's recent round history (`getRoundData`) to decide its class, and the graph draws one feed node per feed, shared by every market that reads it. Both are the raw material of a staleness check and of R3 (one feed under several markets), but neither is measured or alerted yet.

### K24. Vaults that deploy into an external venue

The brief names "vaults routing capital into a perp venue". Belem runs market-neutral strategies, so its positions have a hedge leg on a perp exchange. The tool covers Morpho and Pendle only; any Vault V2 adapter other than a Morpho market adapter is opaque (C4).

The same structure is inside USDe: delta-neutral, with hedges on CEXs. The model reduces it to one depeg prior.

- **Fix:** start with a typed "external venue" node:
  - the venue (on-chain perp such as Hyperliquid, or a CEX);
  - custody;
  - the withdrawal delay;
  - funding-rate exposure.

  Give it a prior with a basis, and a funding-rate scenario. A full model of a perp venue is a separate project.

### K25. Concentration of TVL is not measured

The brief names "protocols concentrating a large share of on-chain TVL". The tool measures lender concentration inside a market (R4), but not:
- the share of Ethereum's lending TVL that Morpho holds;
- the share of a collateral's supply that sits in one Pendle pool or one Morpho market (LlamaRisk measured PT supply on lending markets at 12.8× to 30× the AMM depth, K9);
- the share of a vault in one market.

DefiLlama's `/protocols` (already fetched) gives TVL by protocol and chain.

- **Fix:** a concentration line per layer: protocol share of the chain's category TVL, and position or market share of the PT supply and of the pool depth. A high share means both a systemic node and a slow exit.
- *(update 2026-10-10)* The `graph` command now records the collateral held by every held and sibling Blue market (`takes as collateral`, with the amount). Summed per collateral and compared with its supply, that gives the share of a token sitting in Morpho markets; the line is not computed yet.

## 10. What holds up

The challenge also found choices that the evidence supports.

- **"The APIs find, the chain decides".** Re-reading every amount on-chain matches the lesson of the Morpho PAXG market (2024): the UI showed the right price while the oracle was wrong by 10¹².
- **Oracle against an independent price (G4 done).** Every oracle incident in the list would have shown as a gap between the oracle and the market.
- **Unrealised bad debt and liquidation curves per market.** This is the measure Credora and Gauntlet build on.
- **The registry's basis for sUSDe** already names the CEX-only print of 2025-10-10. That is the right venue distinction (K5 only asks the distribution to follow it).
- **Expected loss per year of Morpho Blue:** 0.46 % of collateral, close to Bundi's 0.62 % pure premium (K4).
- **The "risk multiple to exit" line** partly answers Team 2's breakeven-probability argument.
- **No cascade on blue-chip collateral** is consistent with 2025-10-10. It's the PT, with its thin pool, where the assumption fails (K9).

## 11. Recommended order

The order of the remaining work now lives in `NEXT_STEP.md`, which merges the earlier plans and follows the reading of the brief in `docs/archive/ANALYSIS_CURRENT.md` (detect → impact → how fast → decide). How the gaps map onto it:

| `NEXT_STEP.md` phase | Steps | Gaps |
|---|---|---|
| A: complete the brief's chain | A1 wrapped collateral, A2 breakeven p\* and mixed books, A3 NAV-update detection for vaults, A4 conditional Monte Carlo, A5 HTML | K26, K21, M6, K20 (rest), K22, K6, K14 |
| B: make the numbers defensible | B1 rates, B2 implied yield, B3 horizon, B4 oracle structure, B5 priors, B6 cascade, B7 tail, B8 market-price loans | K10, K11, K12, K7, K8, K1–K5, K15, K17, K18, K9, K27, K13, K14, K16 (rest) |
| C: discovery depth and scope | C1 depth and siblings, C2 feed quality, C3 concentration, C4 external venues, C5 other chains and Vault V1 | K19, K23, K25, K24, C5 |
| Done | incident mode, time to impact, vault incident, book of vaults | K20, K16 (most), K21 (part), K22 (part) |

The order recommended on 2026-10-10 put K20 and K21 first; both are now done or partly done.

## 12. Resources

### Project files

| File | Used for |
|---|---|
| `docs/hackaton_instruction/Hackathon_DeFi-Risk-Dependency-Challenge_EN_v1.pdf` | the challenge brief, scope and judging weights (§9) |
| `riskdep/priors.py` | base rates, tiers, age factor, oracle prior |
| `riskdep/propagate.py` | loss per shock, liquidation rule |
| `riskdep/simulate.py` | Monte Carlo, horizon probability, tail metrics |
| `riskdep/decide.py` | carry, exit cost, verdict, de-lever sizing |
| `riskdep/discover.py` | oracle inference (`infer_oracle`), exit quote |
| `riskdep/registry.json` | depeg and hack severities, frequency parameters, PT stress, tail budget |
| `docs/model/how-risk-is-computed.md` | demo numbers, stated limits |
| `docs/model/scenarios-and-breakeven.md` | breakeven probability, horizon conversion |
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

### Protocol-specific signals (K17, K18)

- Halborn, top-100 DeFi hacks (share audited): https://halborn.com/blog/post/halborn-all-time-top-100-defi-hacks-report-summary
- Sentora figures on audited code in hacks (secondary): https://hackmd.io/@Extropy/auditWarn
- Attack paths outside audit scope, H1 2026 (news report of a preprint, not read directly): https://www.kucoin.com/news/flash/680m-lost-in-defi-hacks-outside-audit-scope-in-h1-2026
- Exponential, DeFi risk factors (no published audit): https://dlnews.com/articles/defi/study-on-defi-protocols-found-risk-factors/ and https://features.llama.fi/uploads/pdf/exponentialfi-report-evaluating-risk-in-defi.pdf
- DefiLlama protocols (`audits`, `audit_links`, `listedAt`; queried 2026-10-10): https://api.llama.fi/protocols
- Nexus Mutual capacity and prices (keyless): https://api.nexusmutual.io/v2/capacity
- Nexus Mutual × Symbiotic listing prices: https://symbioticfi.notion.site/Nexus-Mutual-x-Symbiotic-2a781c079c17800bbe0dedc08a574b98
- DeFiSafety process-quality scoring, time-decayed (discussion): https://gov.idle.finance/t/a-discussion-about-risk/1126
- Lindy effect and upgradeable protocols (opinion): https://cointelegraph.com/opinion/how-lindy-effect-users-overconfident-de-fi-brands
- 2025 exploits of mature protocols: https://blog.amberdata.io/defis-year-of-exploits-2b-lost-lessons-learned
- Exploits moving away from smart contracts (Sentora): https://sentora.com/research/articles/the-pulse-exploits-moving-away-from-smart-contracts
- 2025 loss mix (Chainalysis via ForkLog; PeckShield via Cointelegraph): https://forklog.com/en/losses-from-crypto-hacks-reached-3-4bn-in-2025/ and https://cointelegraph.com/news/crypto-3-4-billion-losses-2025-wallet-hacks
- `fixtures/snapshot/` DefiLlama `/hacks` re-run with 5-, 3-, 2- and 1-year windows (K17 tables)

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
