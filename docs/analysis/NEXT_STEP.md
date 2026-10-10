# Next steps

Where the project goes next, in recommended order, and what each step needs. This file merges the two earlier versions (version 1, by infrastructure step; version 2, by the brief's judging weights) and drops what has been built since. It follows the reading of the brief in `ANALYSIS_CURRENT.md`: **an incident is known; the tool must detect it, compute its impact on the book, say how fast it lands, and decide stay or exit**.

Sources: the brief (`docs/hackaton_instruction/GOAL.md` and its PDF), the gap review `GAP.md` (K1–K25), the gap list of `ANALYSIS_MONITORING.md` (C, D, M, R, T, X ids), the teammates' feedback (`comparison_team.md`), and the RockawayX and Belem findings (`ROCK-VAULT.md`).

Each step gives its goal, how it would be built, its size (**S** about a day, **M** a few days, **L** more), and what it needs.

## Contents

- [1. Where the project stands](#1-where-the-project-stands)
- [2. What has been built](#2-what-has-been-built)
- [3. How the remaining steps are ordered](#3-how-the-remaining-steps-are-ordered)
- [4. Summary](#4-summary)
- [5. Phase A: complete the brief's chain](#5-phase-a-complete-the-briefs-chain)
- [6. Phase B: make the numbers defensible](#6-phase-b-make-the-numbers-defensible)
- [7. Phase C: discovery depth and the brief's scope items](#7-phase-c-discovery-depth-and-the-briefs-scope-items)
- [8. Phase D: operations](#8-phase-d-operations)
- [9. The demo](#9-the-demo)
- [10. What is already available](#10-what-is-already-available)
- [11. What is needed from you](#11-what-is-needed-from-you)

## 1. Where the project stands

| Criterion (weight) | Strong now | Still weak | Main gaps |
|---|---|---|---|
| Dependency discovery (30 %) | A PT position's five layers; vault → adapters → markets → borrowers and lenders; the admin surface; sibling Blue markets, `wraps` edges and an oracle class per input in `graph`; issuer NAV feeds recognised (Midas) | `analyze` does not use siblings or the admin surface; a wrapped collateral is not matched by a vault incident (D108); Blue only; Ethereum only; feed quality and TVL concentration not measured | K19, K23, K25, R5, D108, C5 |
| Impact estimation (30 %) | Incident mode for a borrower and for a vault depositor; a book of vaults in USD; unrealised bad debt, curves to −50 %, exit queue, drain threshold | The rate and implied-yield channels of a PT loop; layers independent; no cascade; liquidity returned by liquidations not modelled; biased exploit priors | K10, K11, K6, K9, K1, K17 |
| Decision usefulness (25 %) | A verdict given a known incident; time to impact from the oracle type; a book headline naming the vault to act on; alerts carrying an impact | No breakeven probability p\*; the uncertainty around a known incident is not drawn; the ex-ante verdict uses the mean only | K21, K13, K14 |
| Working demo on real data (15 %) | The brief's sponsor's vault (Belem) and the curator's seven Ethereum vaults recorded; 188 offline tests; CI | The book mixes no borrow pockets; no HTML for vault and book incidents | K21 |

## 2. What has been built

Steps of the two earlier versions that are now done, with their plans:

| Step | Built | Plan |
|---|---|---|
| Admin surface of oracles, Blue and issuers (v1 step 3) | upgrades, owners, feeds, pauses, mints, Blue owner, oracle divergence | `2026-10-10-admin-surface` |
| Oracle verification (part of K7) | Etherscan `getsourcecode`; the ×2 prior only for unverified oracles | D68 |
| Run on a vault, drain threshold | exit queue, `ExitQueue`; d\*, `DrainWindow`, Public Allocator inflow | `2026-10-10-exit-queue`, `2026-10-10-drain-threshold` |
| Sibling markets and oracle classes (part of K19, K7) | in `graph`; `wraps` edges; curves on every market | `2026-10-10-sibling-markets` |
| Incident mode for a position (v2 A1) | `analyze --shock`; verdict given the incident | `2026-10-10-incident-mode` |
| How fast (v2 A2) | time to impact from the oracle class, TWAP window, meta-oracle timelock and switch | `2026-10-10-incident-mode` |
| Detection → impact (part) | `OracleDivergence` on a borrowed market carries the impact; divergence checked every batch | D93, D97 |
| Oracle mode from structure (part of v2 B4) | the ex-ante simulation reads the oracle's structure before the price inference | D96 |
| Vault depositor's loss under an incident (most of v2 D1) | `analyze --vault --shock token=…`; curves widened to −30 and −50 % | `2026-10-11-vault-incident` |
| A book (part of v2 A3) | `analyze --book` / several `--vault`, user-defined, in USD, with a headline; `--record` for any vault | `2026-10-11-vault-book` |
| Wrapped collateral in vault incidents (A1) | a token reaches the markets whose collateral wraps it; hidden shortfall when the oracle does not follow | `2026-10-11-wrapped-collateral` |
| CI (part of v1 step 10) | lint and tests on every push | — |

**No longer relevant:** v1 step 2 as written ("`analyze` for any collateral") is replaced, for vaults, by the vault incident mode, which takes any collateral; for a borrower it continues as part of A2 below. The v1 → v2 carry-over table and the "phase A first" ordering are superseded by this file.

## 3. How the remaining steps are ordered

1. **Complete the brief's chain** before refining any number: what is missing between detection, impact, speed and the decision, for the vaults the demo now uses.
2. **Then the largest errors in the numbers**: the channels that cost positions without any incident (rates, implied yield), the uncertainty around a known incident, the cascade.
3. **Then the brief's scope items** (discovery depth, feed quality, concentration, external venues, other chains).
4. **Operations** (alerts out of the terminal, infrastructure, execution) last, except where a step needs them.

## 4. Summary

| # | Step | Gaps | Size | Builds on |
|---|---|---|---|---|
| ~~**A1**~~ | ~~Look-through of wrapped collateral in vault incidents~~ **done** (plan `2026-10-11-wrapped-collateral`) | D108, K26 | S–M | `siblings.underlyings` |
| **A2** | Breakeven probability p\* for a position, a vault and a book; mixed books with borrow and PT pockets | K21, M6 | M | `vault_book.py`, `scenario.py`, `decide.py` |
| **A3** | Detection → impact for vaults: an issuer NAV update triggers the vault incident; other alert types carry an impact | K20, K22 | S–M | `vault_incident.py`, the watches |
| **A4** | Conditional Monte Carlo around a known incident | K6, K14 | M | `simulate.py`, `scenario.py`, `vault_incident.py` |
| **A5** | HTML for vault and book incidents | demo | S | `report.py` |
| B1 | Borrow-rate channel (AdaptiveCurveIRM) | K10 | S | utilisation already read |
| B2 | PT implied-yield channel | K11 | S | Pendle historical data |
| B3 | Horizon to maturity, stressed exit cost | K12 | S | Pendle quotes at several sizes |
| B4 | Oracle structure, rest: drain priority, split constant-price, pool-move event | K7, K8 | M | `oracle_class.py` |
| B5 | Priors: decayed window, survivorship, double count, two-part depeg, off-chain prior, protocol multiplier, the RockawayX issuers | K1–K5, K17, K18 | M | `priors.py`, `registry.json` |
| B6 | Liquidation cascade with slippage; liquidity returned by liquidations | K9 | M | curves of held and sibling markets |
| B7 | Tail-aware verdict, sampling error shown | K13, K14 | S–M | `simulate.py`, `decide.py` |
| B8 | Market-price revaluation of loans; the drain as a loss channel | K16 | S–M | `market_risk.py`, `drain.py` |
| C1 | Discovery depth in `analyze`; watch the siblings; other venues | K19, R5, R6 | M | `admin.py`, `siblings.py` |
| C2 | Feed quality | K23, R3 | S–M | `oracle_class.py` |
| C3 | TVL concentration | K25 | S | `graph` market nodes |
| C4 | External venues (perp, CEX) | K24 | M–L | registry |
| C5 | Other chains, Vault V1, direct supply | C5, C3, C4 | M–L | `metamorpho-v1.1` submodule |
| D1 | Validate on your own positions | — | — | your addresses |
| D2 | Push alerts | D4, D5 | S | a channel |
| D3 | Tests on a forked chain | T1 | M | an archive RPC |
| D4 | Reliable infrastructure | D1, D3 | S–M | an RPC key |
| D5 | Execution through Bundles | X1 | L | a security design |
| D6 | Housekeeping | T4 | S | — |

If time allows one phase, do **A**. If two, **A then B1, B5 and B6**: the PT loop's largest error, the RockawayX issuers' priors, and the cascade the sponsor's vault would face.

## 5. Phase A: complete the brief's chain

### A1. Look-through of wrapped collateral (D108) — done

**Status: done on 2026-10-11** (plan `2026-10-11-wrapped-collateral`, D110–D111). A token now reaches the markets whose collateral wraps it, with the path shown; a market whose oracle does not track a market counts a hidden shortfall. `token=trUSD:0.30` reaches two RockawayX vaults (1.61M USD). Left: etrUSD, a vault of vaults that answers no `asset()`, stays opaque; an issuer NAV oracle that reprices from its underlying is not detected as such.

**Why.** A vault incident matches a token only as the markets' direct collateral. A trUSD or wYLDS markdown finds no market in the RockawayX book, although PT-trUSD, PT-strUSD, etrUSD and wYLDS-based markets depend on those tokens (`ROCK-VAULT.md` §5.2).

**How.**
- Build, for each market's collateral, the chain of what it wraps: a PT → its SY → its yield token (Pendle API, already used); an ERC-4626 share → `asset()` (the `wraps` edges of `graph`); a vault of vaults such as etrUSD → its underlying vault. `siblings.underlyings` already resolves the first two.
- A shocked token then hits every market whose collateral wraps it, with the fall passed through: one for one for a share, and for a PT through the oracle's class (a linear-discount PT oracle does not move with its underlying's NAV until it is repriced).
- The output says through which wrapper each market was reached.

**Tests.** On the recorded RockawayX book, `token=trUSD:0.30` reaches the PT-trUSD and etrUSD markets.

**Size.** S–M.

### A2. Breakeven probability and mixed books (K21, M6)

**Why.** The brief asks to make "expensive and certain against cheap and uncertain" explicit, and Team 2 proposed the breakeven probability for it. The book exists for vaults only, and gives losses but not p\*.

**How.**
- **p\*** for each incident and each pocket: p\* = (cost of leaving) / (loss avoided by leaving).
  - Borrower: cost = exit quote + carry given up; loss avoided = the incident's loss.
  - Vault depositor: cost = `forceDeallocate` penalty + yield given up over the horizon; loss avoided = loss if it stays − loss if it leaves first.
  - Exiting pays if one believes P(incident) > p\*. A pure `decide.breakeven(cost, avoided)`.
- **Headline:** the book line gains "exit pays above p\* = x %", per vault and for the book.
- **Mixed books:** pockets of kind `borrow` and `pt` next to the `vault` pockets, through `scenario.assess`, so the brief's book of ten pockets can be entered.
- **Shared layers drawn once** (M6), for the ex-ante simulation of a book: each shared (event, node) drawn once per path for every pocket that holds it.
- **The brief's example as a test:** ten pockets of 10 %, one wiped out, an 11 % unwind: p\* = 11 %.

**Size.** M.

### A3. Detection → impact for vaults (K20, K22)

**Why.** For the sponsor's vault the incident is an issuer NAV update, published by transaction, with no market move before it. Today the watches see the oracle move (`OracleDivergence`, oracle-move alerts) but no alert carries the vault's loss.

**How.**
- In `watch --vault` and for vault deposits in `watch --user`: the feeds classed constant-price (issuer NAV) are watched for new rounds (`AnswerUpdated`, or a changed `latestRoundData` at each light read). A fall of x % calls `vault_incident` with `token=<collateral>:x`, and the alert carries the vault's and the depositor's loss and the verdict.
- Other alert types: an upgrade of the oracle or the collateral token maps to a named scenario from the registry (B-phase scenario library); `DrainWindow` already carries its impact.

**Size.** S–M.

### A4. Conditional Monte Carlo (K6, K14)

**Why.** Incident mode gives one answer. Once an incident is known, its evolution is still uncertain: how deep it goes, whether it recovers, whether it spreads to other issuers or to the Pendle pool. That distribution is the "staying is uncertain" side of the brief (`ANALYSIS_CURRENT.md` §6).

**How.**
- `simulate.run(..., observed=…)`: the observed layers hit in every path, their severity drawn from "the observed size or worse" with a probability of recovery (registry, with a basis from past incidents of the same kind).
- The other layers' probabilities depend on the incident: a depeg raises the Pendle pool's and the oracle's; an issuer markdown raises the other issuers' in the same common-mode group (issuers that lend to one another, `EXTERNAL_SOURCE.md` Pharos groups).
- For vaults: draws of the NAV cut and of whether liquidators act (D103).
- Output: the loss distribution of staying against the certain cost of leaving, and p\* for the bad branch.

**Size.** M.

### A5. HTML for vault and book incidents

The vault and book incident modes write JSON and terminal text only. A page with the book table, each vault's hit markets and the headline makes the demo readable. **Size:** S.

## 6. Phase B: make the numbers defensible

### B1. The borrow rate (K10)

For a 7.6× PT loop, a +10 pp borrow rate for 30 days costs $28,060, 4.5× the whole modelled expected loss. **How:**
- the AdaptiveCurveIRM rule from `docs/external/…/contracts/irm.md`: target utilisation 90 %, the rate ×4 at 100 %, and `rateAtTarget` doubling in about 5 days while utilisation stays at 100 %;
- `rateAtTarget(id)` read on-chain, and a two-state utilisation path per Monte Carlo path;
- a `borrow_rate` shock for incident mode.

**Size:** S.

### B2. The PT's implied yield (K11)

A PT's price moves with its implied yield: +20 pp costs 2.2 % on the demo. **How:** price = (1 + y)^(−T); the distribution of implied-yield rises from Pendle's `/v3/{chainId}/markets/{address}/historical-data`; a `pt_yield` event passed to the oracle according to its class. **Size:** S.

### B3. Horizon and stressed exit cost (K12)

The verdict compares a one-off exit cost with a 30-day loss while the PT redeems at par at maturity. **How:** horizon to maturity for PTs; exit now, hold to maturity and de-lever compared; the exit quote recomputed at a stressed pool depth from Pendle quotes at several sizes. **Size:** S.

### B4. Oracle structure, the rest (K7, K8)

Done: classification in `graph`, incident mode and the ex-ante simulation; the meta-oracle's sources and switch; Midas NAV feeds. **Remaining:**
- `drain.py` uses the class (D70 measured the gap without classifying): a constant-price oracle is where the gap can grow.
- Split constant-price into exchange rate and fixed or linear discount (Credora's Dynamic / Exchange / Fixed, `EXTERNAL_SOURCE.md` §3).
- A pool-move event for TWAP oracles (PT-reUSD, 2026-08-25): impact of a trade from Pendle quotes; its cost is the liquidation incentive.
- Classify the 8 sibling oracles still `not classified` in the Belem graph, and the wstETH custom feed.

**Size:** M.

### B5. The priors (K1–K5, K17, K18) and the RockawayX issuers

| Gap | Change |
|---|---|
| K17, K1 | Weight hacks by age (half-life about 1.5 years); tier protocols by their TVL at the hack date (DefiLlama `/protocol/{slug}`) |
| K3 | Remove oracle techniques from the lending layer's count |
| K5, K2 | A two-part depeg for synthetic dollars (shallow, plus a rare collapse); an off-chain prior per issuer (custodian, CEX, manager, keys) |
| K18 | A bounded protocol multiplier (0.25×–4×) from admin powers, upgrades since the last audit, Nexus Mutual's cover price, immutability |
| `ROCK-VAULT.md` §6 | Registry entries for Huma PST, f(x), Tori, Re, Midas, Hastra, Nuva, infiniFi, EURCV, with their basis; today they all fall back to `unknown_issuer` |

**Size:** M.

### B6. Liquidation cascade and returned liquidity (K9)

**How:** a pure loop: at a fall d, the curves of every market holding the collateral (held and sibling, `graph`) give the collateral liquidated; its price impact (Pendle quotes for PTs, k·√Q otherwise) gives an extra fall, until stable. For vaults: the debt liquidators repay comes back as free liquidity in the market, which changes what can leave; for issuer-priced collateral, a liquidation needs a buyer of the issuer's token (D103), so a "no liquidator" branch keeps the liquidity locked. **Size:** M.

### B7. Tail-aware verdict and sampling error (K13, K14)

The demo's CVaR 99 % is 98 % of equity, and its carry sits inside the expected loss's 95 % interval (6,265 ± 745 USD). **How:** sample the priors and report ranges; compare carry with the upper end; a second CVaR budget for EXIT; show the standard error, and mark a verdict reason that rests on a difference inside it. **Size:** S–M.

### B8. Loans at the market price; the drain as a loss channel (K16, rest)

**How:** in `market_risk.value`, a second valuation at the market price (DefiLlama) for markets whose oracle does not follow the market: the hidden bad debt; a scenario past d\* adds the drainable amount as bad debt and removes it from the exit capacity; Vault V1.1's realisation rule once C5 reads V1. **Size:** S–M.

## 7. Phase C: discovery depth and the brief's scope items

- **C1. Depth in `analyze`, siblings watched, other venues (K19, R5, R6).** The admin surface as layers with priors (B5's multiplier); one look-through level (an ERC-4626 vault behind an oracle, sUSDS → USDS → PSM → USDC); off-chain dependencies as typed registry nodes; the siblings' liquidations and oracle moves added to the poller's filters; sibling markets on Euler, Aave, Silo, Fluid. **M.**
- **C2. Feed quality (K23, R3).** The age of each feed's last update against its heartbeat (`FeedStale` alert); deviation threshold; one feed under several markets; a meta-oracle's live source and challenge state. The local Chainlink docs are `docs/external/chainlink/`. **S–M.**
- **C3. TVL concentration (K25).** The protocol's share of its category's TVL; a collateral's share held in Morpho markets (from `graph`'s market nodes) and against its pool's depth. **S.**
- **C4. External venues (K24).** A typed venue node (perp or CEX, custody, withdrawal delay), a prior and a funding-rate scenario; RockawayX's other venues (Kamino, Upshift, Ember, Midas, Accountable) as issuer or venue nodes. **M–L.**
- **C5. Other chains, Vault V1, direct supply (C5, C3, C4).** The chain as a parameter (RockawayX Midas USDC Prime is on Base; `chainId: 1` is hard-coded in the Morpho API queries); a Vault V1 reader from `docs/external/morpho/lib/metamorpho-v1.1`; the vault rules applied to a direct Blue supply; Solana out of scope before the event. **M–L.**

## 8. Phase D: operations

- **D1. Validate on your own positions.** The Belem and RockawayX vaults are now the demo; a run on the positions you hold, and your reaction to the output, would set the thresholds.
- **D2. Push alerts (D4, D5).** A notifier behind the alert printer (Telegram, Slack, Discord, ntfy or email), credentials in `keys.ini` `[alerts]`; a deduplication store so a standing alert is not resent after a restart; a test message. **S.**
- **D3. Tests on a forked chain (T1).** Cause the events the recordings never had: an oracle pushed down, a liquidation with bad debt, a NAV cut published, a timelocked change. Needs an archive RPC; Foundry is installed. **M.**
- **D4. Reliable infrastructure (D1, D3).** Backfill after a stop, a WebSocket trigger (`docs/websocket-vs-polling.md`), deeper reorgs. The optional eRPC proxy (`docs/erpc.md`) already absorbs rate limits and fails over; archive reads still need a paid RPC. **S–M.**
- **D5. Execution (X1).** De-lever, migrate or exit through Morpho Bundles, simulated before signing, with a security design first; the tool never holds a key with full control. **L.**
- **D6. Housekeeping (T4).** Remove the unused `LLAMA_YIELDS` constant in `riskdep/sources.py`; decide on the old copy in `../projet/`; add a `CHANGELOG.md` and a version policy. **S.**

## 9. The demo

What a judge sees in five minutes:

1. **The sponsor's vault:** `graph --vault 0xd6d4…48ec` (the Midas NAV feed and its admin, the liquidity market) and `watch --vault` on its recording (99.46 % one depositor, `ExitQueue`).
2. **An incident on it:** `analyze --vault 0xd6d4…48ec --shock token=mGLOeuro:0.30`: 251,761 EURCV of bad debt, at once on publication, and why leaving first does not help this depositor.
3. **The curator's book:** `analyze --book examples/rockawayx-ethereum.json --shock token=PST:0.30`: 5.19M USD in two vaults, and the vault to act on first.
4. **A borrower's view:** `analyze --demo --shock issuer_depeg=0.08`: no liquidation for 16 hours, then liquidation through the meta-oracle's backup.
5. **The defence:** each number's basis, the oracle classes with their evidence, and the ex-ante Monte Carlo as the secondary view.

## 10. What is already available

| Material | Where | Used for |
|---|---|---|
| Morpho developer docs | `docs/external/morpho/docs.morpho.org-developers-docs` (local, git-ignored) | contracts, Bundles, addresses on every chain, IRM |
| Morpho Blue, Vault V2, Vault V1.1, oracles sources | `docs/external/morpho/lib/` (submodules) | events, maths, adapters, Public Allocator, `MorphoChainlinkOracleV2` |
| Pendle docs and sources | `docs/external/pendle/` | PT, SY, oracles, historical data (B2) |
| Chainlink Data Feeds docs | `docs/external/chainlink/` (local, git-ignored) | feed quality (C2) |
| Etherscan key and docs | `keys.ini` `[etherscan]`; `docs/external/docs.etherscan.io-api-reference-docs` | verified names and sources |
| Recordings | `fixtures/snapshot/`, `fixtures/replay/` (Sentora, two users, the Belem and RockawayX vaults, two graphs) | offline demo and tests |
| The demo book | `examples/rockawayx-ethereum.json` | `analyze --book` |
| eRPC proxy | `erpc.yaml`, `docs/erpc.md` | rate limits, failover |
| External sources (Pharos, Credora, Nexus) | `EXTERNAL_SOURCE.md` | B5 priors, A4 common-mode groups |
| Foundry, the DeFi hack corpus | installed; the `search-crypto-hack` skill | D3; B5 and A4 calibration |

## 11. What is needed from you

**Decisions**
- [ ] The book for the demo beyond RockawayX: the borrow and PT pockets to add (A2).
- [ ] The probability of recovery and the size distribution of an issuer NAV cut, or the incidents to calibrate them on (A4).
- [ ] The horizon rule for open-ended positions (B3) and a second tail budget for EXIT (B7).
- [ ] The scope of phase C before the event: which of C1–C5 fit, which stay stated limits.
- [ ] The alert channel and the levels to push (D2); the degree of automation for execution (D5); what to do with `../projet/` (D6).

**Documents**
- [ ] The issuers' documentation for B5: Huma, f(x), Tori, Re, Midas, Hastra, Nuva, infiniFi (backing, redemption, admin powers).
- [ ] Optionally, audit reports and post-mortems of the protocols used.

**Access and credentials** (in `keys.ini`, git-ignored; names in `keys.example.ini`)
- [x] Etherscan API key.
- [ ] An archive RPC with WebSocket access (D3, D4), and an RPC per extra chain (C5).
- [ ] The alert channel's credentials (D2).
- [ ] Optionally a Pharos key (A3, A4) and a DEX aggregator key (B6).
