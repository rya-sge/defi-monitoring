# GAPV2: suggested improvements, and how to build them

`GAP.md` challenges the risk model's assumptions (K1–K24). This file is narrower and newer (2026-10-11). It lists gaps found by:

- comparing riskdep with DeFiScan's Morpho vault review (`deficollective/defiscan-skills`, `review-morpho-vault/SKILL.md`, read 2026-10-11, not run);
- comparing it with DeFiScan's impact analysis of a permissioned function (`analyze-impact/SKILL.md`, in the local clone `../defiscan-skills/`, read 2026-10-11, not run): G10;
- the Zama, Ethena, Midas and f(x) write-ups of the same day (`docs/model/zama-confidential-vaults.md`, `docs/model/ethena.md`, `docs/model/midas.md`, `docs/model/fx-protocol.md`, `docs/model/infinifi.md`): G4, G5, G11–G20.

Each gap gets an id `G<n>`, what is missing, why it matters for the brief (`docs/hackaton_instruction/GOAL.md`: discovery 30 %, impact 30 %, decision 25 %, demo 15 %), how to build it in this codebase, and a size (S, M, L). Decision numbers are left to the plan that builds each one.

DeFiScan's skill reviews a MetaMorpho (Vault V1) vault and treats Vault V2 as out of scope. Several of its checks are therefore already covered here in V2 form, or do not apply; they are listed at the end.

## What to build first

The brief judges dependency discovery (30 %) and impact estimation (30 %) first, then decision usefulness (25 %) and the demo (15 %). It asks for impact that is "defensible" and for how an incident "propagates through the position's dependency stack". Three rules follow for the order:

1. **Fix what is wrong before adding what is missing.** A number a judge can show to be wrong costs more than a layer the tool does not draw. G11, G12 and G19 are of that kind, and G11 sits on the vault the fork demo plays.
2. **Then the gaps that change an impact figure or a dependency on the recorded vaults**, since the judges run those: G1, G13, G18.
3. **Then the decision and the demo**, which present what the first two compute: G10 with G2, then G6.

| Order | Gap | Why now | Size |
|---|---|---|---|
| 1 | **G11** Midas feed band in the incident and `OracleImpact` | Impact, defensibility: the Belem incident applies −30 % at once where the feed cannot go below −10 % without a 48 h upgrade, so the time to impact is wrong on the demo's own vault | S–M |
| 2 | **G19** What `token=` means for an ERC-4626 collateral whose oracle reads its rate | Impact, defensibility: on the RockawayX USDC Yield vault, a siUSD −30 % liquidates nobody (oracle × 1.000) while the same report says the loss lands at once; one of the two is wrong | S to verify |
| 3 | **G12** f(x) NAV oracle timing, and the freshness of feeds computed on read | Impact, defensibility: the incident says the loss waits for an issuer's round, where the NAV is likely computed on-chain; infiniFi's RT oracle reports "updated 2 min ago" because it stamps every read | S |
| 4 | **G1** Worst-case exposure up to the caps | Discovery and impact: an exposure the allocation hides, on every recorded vault, with no new read | S |
| 5 | **G18**, **G13** The issuer's own loss path: infiniFi's waterfall and pending loss; fxSAVE's NAV components | Impact and detection, propagation: turns a farm default or an fxUSD depeg into the markdown it causes, and gives an early warning before infiniFi books a loss | M each |
| 6 | **G10** with **G2** Admin changes by impact on existing deposits; who holds each role | Decision: an alert that says whether a queued change can reach the depositor's money, how much, and whether one key can make it | S + S |
| 7 | **G6** Web pages for incidents, shocks and backtests | Demo: the API routes exist and no page shows them | M |
| 8 | **G14**, **G5** Issuer exits (Midas, f(x), infiniFi, sUSDe); Ethena's venue stress as a bound | Decision: the exit a holder or a liquidator really has | S each |
| 9 | **G15** Issuer priors for mGLOeuro, fxSAVE, siUSD and the other RockawayX collateral | Impact, ex ante: today only the generic default applies | S |
| 10 | **G16**, **G20**, **G4** Hidden controls: f(x)'s and infiniFi's oracle and price setters; the Zama layer in the engine | Discovery | S each |
| later | G3, G7, G17, G8, G9 | Useful, but they change no figure on the recorded vaults, or widen scope rather than depth | — |

## Summary

| # | Gap | Criterion | Size | Order |
|---|---|---|---|---|
| G1 | Worst-case exposure up to the caps, per oracle and feed | discovery, impact | S | 4 · **done: `CapExposure` and the incident's loss at the caps (D243); graph nodes open** |
| G2 | Who holds each role: EOA, Safe (threshold), timelock | discovery, decision | S | 6 |
| G3 | The protocol's hard limits next to the current settings | decision | S | later |
| G4 | The Zama layer in the engine's graph, and a decryption halt | discovery, impact | S–M | 10 |
| G5 | Ethena: the venue stress stated as a bound; custodians; the unstaking cooldown | impact, decision | S | 8 |
| G6 | Web pages for incidents, shocks and backtests | demo | M | 7 |
| G7 | Vault V1 (MetaMorpho) as a watch and incident target | discovery | M | later |
| G8 | Other chains | discovery | L | later |
| G9 | Audits, bug bounty, licence as provenance | — | S | optional |
| G10 | Each admin change classified: hits existing deposits, only future ones, or enables another change; with the funds it can move | impact, decision | S | 6 |
| G11 | Midas: the feed's band in the incident, the shock engine and `OracleImpact` | impact | S–M | 1 · **done in the incident (D241); the shock engine and `OracleImpact` open** |
| G12 | f(x): the NAV oracle's timing (published or computed on-chain); the freshness of feeds computed on read | impact | S | 3 · **done (D242)** |
| G13 | f(x): fxSAVE's NAV components, `fxusd=` / `aave=` shocks, the lower layers in the graph | discovery, impact | M | 5 |
| G14 | Issuer exits: Midas redemption, f(x) cooldown and instant fee, infiniFi's Gateway and queue | decision | S | 8 |
| G15 | Issuer priors for mGLOeuro, fxSAVE, siUSD and the other RockawayX collateral | impact | S | 9 |
| G16 | f(x): oracle-source updates that bypass the timelock, and the price oracle behind the NAV | discovery | S | 10 |
| G17 | Data and scope: Midas TVL, mROX | discovery | S | later |
| G18 | infiniFi: the loss waterfall (liUSD, safety buffer), a farm-loss shock, the pending-loss early warning | discovery, impact | M | 5 |
| G19 | `token=` on an ERC-4626 collateral whose oracle reads its rate: market fall or booked loss; the engine's `converts through` transmission | impact | S | 2 · **done (plan `2026-10-11-gapv2-fixes`, D240)** |
| G20 | infiniFi: price, oracle and loss events, and the pauses, not decoded | discovery | S | 10 |

## G1. Worst-case exposure up to the caps

**What is missing.** Exposure is measured from the current allocation (`VaultState.markets[*].vault_assets`). In a Vault V2, an allocator can move capital into any enabled market up to its caps immediately, with no timelock (`VaultV2.allocate`). So a market holding 5 % of the vault today can hold far more tomorrow, and nothing warns before it. The caps are already read (`vault.read_state`: `allocation`, `absoluteCap`, `relativeCap` per cap id), but they are used only for the drain threshold's headroom (`drain.headroom`).

DeFiScan's review bounds each price feed's funds at risk by the sum of the caps of the markets that feed prices (`feedCap`). That is the number to add.

**Why.** It is a dependency the position cannot see (discovery) and a larger possible loss (impact). An incident on a feed with 2 % allocated but 40 % allowed is a different decision.

**How.**

1. **The arithmetic, pure, in `drain.py` or a new `exposure.py`.** For one market, the most the vault can hold is the smallest of its three cap ids (`vault.cap_ids`: `adapter`, `collateral`, `market`), each `min(absoluteCap, relativeCap × totalAssets)`, with WAD meaning no limit (`drain.headroom` already does this).
   - The `collateral` id is shared by every market on the same collateral, and the `adapter` id by every market of the adapter. A sum over markets must cap each group by its shared id, or it double counts.
   - Per oracle or feed: group the markets whose price it enters (`shock.dependents` already maps oracles and feeds to markets), then sum their per-market limits under the shared-id constraint. Cap the result at `totalAssets`.
2. **Where it shows.**
   - `watch` start-up: one line per oracle and feed, "allocated X (a %), allowed up to Y (b %)". A `CapExposure` warn when the allowed share crosses the same 25 % as the existing market-share warning (`watch.market_share_warn`, or a new `watch.cap_exposure_warn` with its basis).
   - `graph`: `allocated_usd` and `cap_usd` on each oracle and feed node.
   - Vault incident: an extra line "at the caps, the same incident would cost Z". Run `vault_incident.run` a second time with each hit market's `vault_assets` replaced by its cap limit; the share of the market's loss the vault bears scales the same way.
3. **Registry.** `watch.cap_exposure_warn` with its basis; a row in `docs/reference/registry-reference.md`; the `CapExposure` row in `docs/reference/alert-runbook.md`.
4. **Tests.** Offline, on the recorded Belem and RockawayX vaults: the per-market limit equals `min` of its three ids; a shared collateral id is not double counted; the total never exceeds `totalAssets`.

**Size.** S. No new read.

## G2. Who holds each role

**What is missing.** `graph` reads the owner, the curator, the allocators and the sentinels, but not what each of them is. A single private key holding a role that changes risk with no notice is not flagged.

In Vault V2, the owner sets the curator and the sentinels immediately (`setCurator`, `setIsSentinel`: owner only, not timelocked). The curator's changes go through its timelocks. Allocators allocate within caps immediately. So an owner or an allocator held by one key matters most.

**Why.** It is a dependency (discovery) and changes the decision: a vault whose owner is an EOA can change its curator in one transaction.

**How.**

1. **Read, in `admin.py` or a small `roles.py`.** For each role holder, at the vault's block:
   - `eth_getCode`: empty is an EOA; `0xef0100` + address is an EIP-7702 delegated wallet, still one key (`exit_queue._is_contract` already tells these apart);
   - Safe: `getThreshold()`, `getOwners()` (a `n of m` label);
   - timelock: `getMinDelay()` (OpenZeppelin `TimelockController`, as `admin.py` already reads for D182);
   - anything else: "contract (unknown)".
2. **Pure rule in `rules.py`.**
   - A `RoleHolder` start-up finding: critical for an owner that is an EOA or a 1-of-n Safe; warn for an allocator so held; info otherwise, with the label.
   - Re-read on `SetOwner`, `SetCurator` and `SetIsAllocator` events (already decoded), so a change of holder re-evaluates.
3. **Where it shows.** The admin nodes' labels in `graph` (`owner 0xab…cd (Safe 3/5)`) and the vault incident's notes.
4. **Registry, docs, tests.** The levels and their basis in `watch`; runbook rows; recorded Safe and EOA holders under the existing replay directories. A recording with `--record` adds the new calls.

**Size.** S. A few calls per holder.

## G3. The protocol's hard limits next to the current settings

**What is missing.** The limits a curator cannot exceed are not stated. From the pinned source (`docs/external/morpho/lib/vault-v2/src/libraries/ConstantsLib.sol`):

| Constant | Value |
|---|---|
| `MAX_PERFORMANCE_FEE` | 50 % |
| `MAX_MANAGEMENT_FEE` | 5 % a year |
| `MAX_FORCE_DEALLOCATE_PENALTY` | 2 % |
| `MAX_MAX_RATE` | 200 % APR |

For a Vault V1 (G7): `MAX_TIMELOCK` 2 weeks, `POST_INITIALIZATION_MIN_TIMELOCK` 1 day, `MAX_QUEUE_LENGTH` 30, `MAX_FEE` 50 % (`metamorpho-v1.1/src/libraries/ConstantsLib.sol`).

**Why.** A timelocked fee change alert is easier to judge with the ceiling next to it. A depositor's worst case on fees and on the force-deallocate penalty is bounded by these.

**How.** A `morpho_limits` registry key with the values and their source lines, the current fees and penalties already read (`performance_fee`, `management_fee`, `penalties`) shown against them at start-up, and in the `Submit` alert of a fee or penalty change ("from 10 % to 25 %, the ceiling is 50 %"). No new read. Size S.

## G4. The Zama layer in the engine's graph, and a decryption halt

**What is missing.** Two points from `docs/model/zama-confidential-vaults.md`:

- `graph.annotate_zama` runs only in the `graph` command (`cli.py:294`). The graphs that `shock`, `POST /api/shock` and the vault incident's engine run on are built by `graph.load` without it, so the engine never sees a Zama node.
- A decryption halt or a wrapper pause freezes both confidential exits. It is stated in the incident text, not modelled (Z5, left out because the engine propagates losses).

**Why.** Discovery: the shock trace and the incident should show the same hidden layer as the graph. Impact: a freeze during a market incident turns a loss a depositor could avoid into one they bear.

**How.**

1. Call `annotate_zama` inside `graph.load` (it needs no read), or in `shock.py` and `pipeline.incident` right after the load. Check that the engine ignores the new node kinds (no rule matches `decrypted by`, so nothing should change in the figures); `test_engine.py`'s trace regeneration test will catch a change in the committed example.
2. A `frozen` effect for the Zama Protocol node and the cShare: not a loss rule, but a flag the incident reads. When the hit vault is a Zama vault and the shock includes `zama:protocol:frozen`, the verdict states that a confidential holder cannot leave first: their loss is the stay loss.
3. Optionally, `p*` for a confidential holder computed with the instant exit's cost (amount revealed, no fee) rather than the yield given up.

**Size.** S for step 1, M with step 2.

## G5. Ethena: the venue stress as a bound; custodians; the cooldown

**What is missing.** From `docs/model/ethena.md`:

- Ethena's documentation says the backing never sits at an exchange; an exchange failure costs the profit and loss not yet settled, at most one daily cycle. The registry's `ethena.basis` and `ethena.py` still describe a venue incident as losing "a share of what sits at that venue", and the incident note does not say it is a bound.
- The dashboard splits the backing by exchange, not by custodian: a Copper or Ceffu failure cannot be shocked.
- sUSDe's unstaking cooldown (configurable up to 90 days) is not in the exit: a fast exit is a market sale.

**How.**

1. Reword `ethena.basis` and the `venue_loss` text: "margin delegated to that venue; losing a share of it assumes the settlement arrangement failed, an upper bound on an exchange failure". Add a second, default reading: the expected case, one day of unsettled profit and loss, estimated from the 30-day protocol yield on the venue's hedged notional (`protocol_yield × notional ÷ 365`).
2. `custodian=<name>:<loss>` only if Ethena publishes the split by custodian; otherwise state the gap, as now.
3. In the PT report and incidents on sUSDe, a line with the current cooldown read on-chain (`cooldownDuration()` on the sUSDe contract), so "leave through Ethena" shows its delay next to "sell on the market".

**Size.** S.

## G6. Web pages for incidents, shocks and backtests

**What is missing.** The API serves `POST /api/incident`, `GET /api/books`, `POST /api/shock`, `/api/shock/graphs`, `/api/shock/targets`, `/api/shock/sweep`, `GET /api/backtests` and `/api/backtest/{episode}`. The client wraps the shock and backtest routes (`web/src/api/client.ts`), but no page offers them: the Impact page shows one shock, the committed example.

**Why.** The demo criterion: a judge sees the book's verdict and the backtest's predicted-against-realised in the browser, not in a terminal.

**How.**

1. **Impact page:** a vault picker from `useShockTargets`' graphs, a node and mode picker from `useShockTargets`, and `useShockTrace(body)` with the chosen shock. A "sweep" tab with the ranking table.
2. **Incident page** (A5 in `NEXT_STEP.md`): a book picker (`GET /api/books`), a shock input, the book table with verdicts and p\*, each vault's detail on click. Client wrapper and fixture first (`mocks/incident.json`, recorded from the API), per the mock rule in `CLAUDE.md`.
3. **Backtest page:** the two episodes, per market predicted against realised, and the CLI's lines.
4. Each route lazy, as the others; `pnpm lint && pnpm build`.

**Size.** M, all in `web/`.

## G7. Vault V1 (MetaMorpho) as a target

**What is missing.** A Vault V1 appears only as a lender inside a market's graph (`graph.py:222`, `borrower.py:230`); it cannot be watched or put in a book. Item C5 of `NEXT_STEP.md`.

**How.**

1. **A reader `vault_v1.py`**, from the pinned source (`docs/external/morpho/lib/metamorpho-v1.1`): `owner`, `curator`, `guardian`, `timelock`, `fee`, `withdrawQueueLength` and `withdrawQueue(i)`, `config(id)` (cap, enabled, removableAt), `totalAssets`, `pendingCap`, `pendingTimelock`, `pendingGuardian`. **List the markets from `withdrawQueue`, never `supplyQueue`**: a curator often narrows `supplyQueue` to the idle market while capital stays in other markets (DeFiScan measured a 95 % undercount on one vault when walking `supplyQueue`).
2. **A view shaped like `VaultView`/`VaultState`**, so `market_risk`, `drain`, `exit_queue` and `vault_incident` reuse it unchanged; the differences (one cap per market, no adapters, a guardian instead of sentinels) live in the reader.
3. **Events** in `abi.py`: `SubmitCap`, `SetCap`, `SubmitTimelock`, `SetTimelock`, `SubmitGuardian`, `SetGuardian`, `SubmitMarketRemoval`, `RevokePendingCap`, `ReallocateSupply`, `ReallocateWithdraw`, `SetFee`; pure rules in `rules.py` beside the V2 ones.
4. **Cross-check:** the sum of the vault's supply over `withdrawQueue` against `totalAssets()`, within 1 %, as DeFiScan does; a larger gap means a market was missed.
5. **Recordings and tests:** one V1 vault recorded with `watch --record` and `analyze --vault --record`.

**Size.** M.

## G8. Other chains

**What is missing.** Ethereum only: `chainId: 1` in every Morpho API query, the Blue and Public Allocator addresses, the public RPC.

**How.** The chain as a parameter of `sources.Fetcher` (RPC route and API chain id), per-chain addresses in the registry (Morpho Blue is at the same address on most chains, read `MORPHO()` to confirm; the Public Allocator differs), recordings per chain. The brief is about Ethereum, so this adds little to the judging. Size L.

## G9. Audits, bug bounty, licence (optional)

DeFiScan attaches Morpho's audits, its Immunefi bounty and the licence to every vault review. For riskdep they would be provenance in the report, not an input to a number or a verdict. A static `morpho.provenance` registry key and one line in the report would cover it. Size S, optional.

## G10. What an admin change can do to money already deposited

**Source.** DeFiScan's `analyze-impact` skill takes one permissioned function and decides whether it can affect funds already committed or only future allocations. It traces the storage the function writes to every place that value is read, follows the call chain to where funds move, and classifies the end of that chain:

- a checkpoint or distribution path: the value is read only when new funds are allocated, so existing deposits are untouched;
- a claim or withdraw path: the value is read when users take money out, so existing deposits are affected;
- a swap or trade path: every current position is affected at once;
- a configuration path: a parameter that takes effect at the next interaction.

The verdict is FUTURE ONLY or RETROACTIVE, with an evidence chain of source lines, and the funds reachable along the path.

**What riskdep does today.** The admin changes it watches are one flat list, `RISK_INCREASING_VAULT` and `RISK_INCREASING_ADAPTER` (`abi.py:425`). A `Submit` of any of them is a warn, a timelock of 0 on any of them is the start-up `Timelock` finding, and the exit gates have their own `ExitGate` finding (D184). Nothing says whether a given change can reach money already in the vault, how much, or how soon. A performance-fee change and a `burnShares` get the same treatment, although one touches only future interest and the other writes a market off.

**Why.** Decision: the question a depositor asks on a `Submit` is "can this cost me what I already have, and before I can leave?". Impact: the amount a change can reach is a number the alert can carry (`Alert.depositor_impact` exists and is mostly empty for admin alerts).

**The classification, read from the pinned Vault V2 source** (`docs/external/morpho/lib/vault-v2/src`):

| Function | Who, delay | Class | Why (source) | Funds it can reach |
|---|---|---|---|---|
| `setReceiveAssetsGate`, `setSendSharesGate` | curator, timelocked | **Retroactive** | "Can lock users out of exiting the vault" (`VaultV2.sol`, gates note) | every deposit |
| `setReceiveSharesGate` | curator, timelocked | **Retroactive** for shares held on other contracts | "Can lock users out of getting back their shares deposited on an other contract"; a reverting gate "can block all vault interactions" | every deposit, if the gate reverts |
| `setSendAssetsGate` | curator, timelocked | **Future only** | "Gates depositing assets… cannot block users' funds" | none |
| `burnShares` (adapter) | curator, timelocked | **Retroactive** | sets the adapter's `supplyShares[marketId]` to 0 (`MorphoMarketV1AdapterV2.sol:155`): the vault's position in that market is written off | the vault's allocation to that market |
| `setForceDeallocatePenalty` | curator, timelocked | **Retroactive** for anyone who must force an exit | the penalty applies to a `forceDeallocate` made after it | the forced part of an exit, up to 2 % |
| `setPerformanceFee`, `setManagementFee` | curator, timelocked | **Future only** | `accrueInterest()` runs before the new fee is set (`VaultV2.sol:445`), so interest already earned is charged at the old rate | future interest |
| Fee recipients | curator, timelocked | **Future only** | where future fees go | none |
| `increaseAbsoluteCap`, `increaseRelativeCap`, `addAdapter`, `setAdapterRegistry`, `setIsAllocator` | curator, timelocked | **Enabler** | moves no money itself; lets an allocator move existing money further | up to the new caps (G1) |
| `allocate`, `deallocate`, `setLiquidityAdapterAndData` | allocator, **immediate** | **Retroactive** | moves existing money between markets, within caps | the cap headroom of the target markets (G1) |
| `setMaxRate` | allocator, immediate | **Future only** | `accrueInterest()` first (`VaultV2.sol:600`): caps future accrual | future interest |
| `setCurator`, `setIsSentinel`, `setOwner` | owner, **immediate** | **Enabler** | changes who can submit the changes above | depends on the next change (G2) |
| An oracle's feed or aggregator, a proxy upgrade of a dependency (admin surface) | outside the vault | **Retroactive** | reprices collateral already posted | the vault's allocation to the markets that read it |

So of the fourteen risk-increasing vault functions in `RISK_INCREASING_VAULT`, four can reach existing deposits by themselves, five are enablers, and five touch only future money. Of the two adapter functions, `burnShares` is retroactive; `setSkimRecipient` only redirects tokens the adapter is sent outside its positions (rewards), so it is future only. The allocator's own actions, which have no timelock at all, are the retroactive path that the enablers open.

**How to build it.**

1. **Registry, not code.** A `watch.admin_impact` table keyed by signature: `class` (`retroactive`, `future`, `enabler`), `reach` (`all`, `market`, `forced_exit`, `future_interest`, `caps`, `none`), and a `basis` citing the source line, as above. A new function is then a registry row. `registry-reference.md` documents the table.
2. **The amount, pure, in `rules.py`.** From the decoded `Submit` data (`describe_call` already decodes it):
   - `all`: the depositor's assets, or the vault's total;
   - `market`: the vault's allocation to the market named in the data;
   - `forced_exit`: the new penalty × what would leave by `forceDeallocate`;
   - `caps`: the new limit minus today's allocation (G1);
   - otherwise none.

   Put it in `Alert.depositor_impact` (negative, in the vault's asset) and in the title: "Submit setReceiveAssetsGate: retroactive, can lock all 4,685,206 EURCV in; executable in 3 days".
3. **Levels from the class, not the list.** Retroactive with no timelock: critical. Retroactive with a timelock: warn, with the execution date. Enabler: info, naming what it enables. Future only: info. This replaces the flat warn for every `Submit`, so the change belongs in the alerts plan's decision table (`plan/2026-10-11-alerts-and-verdict`), and every row in `alert-runbook.md` changes with it.
4. **The start-up table.** The `Timelock` finding becomes one line per class: "retroactive with no notice: …; enablers with no notice: …; future only: …", so the depositor sees at once whether a no-notice change can reach their money.
5. **Evidence.** Each alert's `data` carries the registry basis (the source line), so the runbook and the Telegram message can show why a change is retroactive.
6. **Tests.** One per class on recorded `Submit` events (record a range that holds one with `watch --record` if no recording does yet), and a check that every signature in `RISK_INCREASING_*` has a row in `watch.admin_impact`.

**What not to copy.** DeFiScan's skill finds the read sites by tracing a call graph over flattened sources, for any protocol. riskdep watches one known contract family whose source is pinned in `docs/external/morpho/`. The classification above is done once, from the source, and kept in the registry. A call-graph tracer would add a dependency and nothing the table does not already state.

**Size.** S: one registry table, one rule, one start-up line, the runbook rows.

## G11. Midas: the feed's band in the incident

**What is missing.** The mGLOeuro/EUR feed stores a fixed band, 90,000–110,000 EUR around 100,000, with no setter (D183). Below 90,000 it cannot report without new code, installed through the `MidasTimelockController` (48 h). `admin._read_bands` reads the band and `watch` reports it at start-up (`FeedBand`), but nothing else uses it:

- `analyze --vault 0xD6d4…48Ec --shock token=mGLOeuro:0.30` applies `oracle × 0.700` at once and says the loss lands "at its next published round";
- the shock engine has no floor on an oracle node;
- `OracleImpact` (`detect.py`) computes what becomes liquidatable at the fall it sees, with no warning that a larger loss is held behind the floor.

A −30 % NAV loss therefore shows as −10 % first (no bad debt on the Belem market), then −30 % only after an upgrade, or never if no upgrade is made. The fork demo plays exactly this sequence; the offline incident does not. (`docs/model/midas.md` §6.)

**How.**

1. **Carry the band into the incident.** `vault_incident.run` already reads each hit market's oracle profile. Add the feed's `(minAnswer, maxAnswer, answer)` from the admin surface's reads (`Contract.band`), and the timelock that controls the feed (`AdminWatch.timelock_over`, its delay).
2. **Two stages, as the meta-oracle already has.** `scenario` prints a meta-oracle's second stage (`after_switch`: "after the oracle switches (16 h)"). Use the same shape:
   - **now**: the oracle falls by `min(shock, 1 − minAnswer / answer)`; the bad debt at that fall; the rest stated as **hidden** ("a further 20 % is held behind the feed's floor");
   - **after the upgrade** (`timelock delay`): the full fall, the bad debt, the verdict.
   The verdict reads the time between the two: 48 h to act.
3. **The engine.** An oracle node gets `floor` in its details; the oracle transmission clamps its output at the floor and records the clamped part, so the shock trace shows it.
4. **`OracleImpact`.** When the oracle sits at its floor, say so: "the feed is at its floor: a larger loss cannot reach the market without an upgrade, and the watch alerts when one is scheduled (`Admin.CallScheduled`)".
5. **Tests.** The Belem recording: −30 % gives the −10 % stage (no bad debt) and the 48 h stage (251,761); the fork-belem replay still matches.

## G12. f(x): the NAV oracle's timing

**What is missing.** The fxSAVE/USDC market's oracle reads a feed named "Net Asset Value in USD". `graph.oracle_patterns` matches "net asset value" to the kind **published** ("net asset value reported by the issuer"), so the incident says the markdown lands "at its next published round, by a transaction". The pinned source computes fxSAVE's NAV on-chain: `nav(fxSAVE) = nav(fxSP) × share rate`, with fxUSD valued at its Curve EMA × Chainlink USDC/USD (`docs/external/fx-protocol/README.md`). If the feed reads that, an fxUSD depeg moves the oracle as the EMA moves, with no transaction by the issuer, and the kind is the one riskdep calls **exchange rate**.

**How.**

1. **Verify on the feed.** Read its source (Etherscan, `discover.py` already fetches verified sources) or call it at two blocks around an fxUSD price change: does `latestAnswer` call `nav()`, and is `updatedAt` the current block?
2. If so, a pattern before the generic "net asset value" one: the feed's contract or name for fxSAVE → `constant-price`, kind `exchange rate`, with that basis. The timing text then follows (`MOVES`: an exchange rate at once).
3. **A general signal for the probe**: a feed whose `updatedAt` equals the block's timestamp, and which has no round history, computes its answer on read. Prefer that to a name match when both are available.
4. **Freshness of such feeds.** infiniFi's `ChainlinkRTOracle` returns `updatedAt = block.timestamp` (`ChainlinkRTOracle.sol:44-48`), so the incident prints "updated 2 min ago" for a price an admin last set at an unknown date. For a feed computed on read, `feeds.py` should say "computed on read: no update time" and, where the value comes from a setter (infiniFi's `FixedPriceOracle.setPrice`), read the setter's last event instead (`PriceSet`, see G20).

**Size.** S once verified.

## G13. f(x): fxSAVE's NAV components, and the shocks they allow

**What is missing.** fxSAVE is shocked by a chosen markdown (`token=fxSAVE:0.30`). Nothing reads what its NAV is made of, so the tool cannot say what an fxUSD depeg, a USDC depeg or an Aave loss does to fxSAVE. `graph` draws fxSAVE `wraps` fxSP and `backed by (Pharos)` fxUSD, and stops there.

**Why.** The brief's strongest submissions explain how an incident propagates through the stack. For fxSAVE the stack is fxUSD (and the long positions behind it), USDC, and Aave; today the user has to guess the markdown.

**How**, modelled on `ethena.py` and `pipeline.venue_shocks`:

1. **`riskdep/fx.py`, a reader** at a block, from the pinned contracts:
   - fxSP: `totalYieldToken()` (fxUSD held), `totalStableToken()` (USDC held, including what is lent), `nav()`;
   - the Aave strategy's `totalSupply()` (the lent USDC);
   - `FxUSDPriceOracle.getPrice()` (the Curve EMA × USDC/USD);
   - fxSAVE's `convertToAssets(1e18)` and `nav()`;
   - the redemption parameters for G14: `redeemCoolDownPeriod()`, `instantRedeemFeeRatio()`.
2. **Pure markdowns.**
   - `fxusd=<depeg>`: fxSAVE falls by fxUSD's value share of fxSP × the depeg;
   - `usdc=<depeg>`: by USDC's share × the depeg (and USDC-quoted markets move too);
   - `aave=<loss>`: by the lent share × the loss.
   Each becomes a `token=fxSAVE:<markdown>` (and `token=PT-fxSAVE` through the wrap) in `pipeline.venue_shocks`, with a note giving the split, as the Ethena venue note does.
3. **The graph** (`annotate_fx`): fxSP's two sides with their USD amounts, the Aave strategy, the Curve pool behind fxUSD's price, f(x)'s reserve fund; edges `holds`, `lends to`, `priced by`.
4. **Recordings** under `fixtures/replay/fx/`, like `ethena/`; tests on the recorded split.

**Size.** M.

## G14. Issuer exits

**What is missing.** The exit modelled for a collateral is the DEX route (`exit_liquidity`). An issuer's own redemption is not:

- Midas: mGLOeuro has no DEX route, only redemption with Midas; its delay, fees and gating are not read;
- f(x): `requestRedeem` then `claim` after a cooldown of up to 7 days, restarting on each new request, paid in a mix of fxUSD and USDC, while the locked shares still bear the pool's losses; or `instantRedeem` with a fee of up to 5 % (`FxUSDBasePool.sol:301-392`);
- Ethena: the sUSDe cooldown (G5);
- infiniFi: siUSD unstakes only through the Gateway, which can be paused; `maxRedeem` is 0 while a loss is pending (`StakedToken.sol:66-77`); iUSD then redeems up to the controller's liquidity and queues the rest FIFO, served as illiquid farms mature (`RedeemController.sol:77-131`). There is no DEX entry for siUSD in `exit_liquidity`.

**Why.** Whether a liquidator acts depends on how it can get rid of what it seizes; whether a holder can leave first depends on how fast it can redeem.

**How.** A registry `issuer_exits` table per token: route (`redeem`, `cooldown`, `instant`), delay, fee, gating, and the on-chain getters that give the live values (f(x)'s two above; sUSDe's `cooldownDuration()`; infiniFi's `RedeemController.liquidity()` and queue length). The vault incident uses it in two places: the liquidator's exit when the DEX has no route ("issuer redemption: up to 7 days, or 5 % now"), and the PT and collateral holder's own exit in the PT report. Size S.

## G15. Issuer priors

**What is missing.** `registry.json` `issuers` has four entries (sUSDe, USDe, wstETH, sUSDS). mGLOeuro, fxSAVE and the other RockawayX collateral (PST, strUSD, etrUSD, siUSD, reUSD, PRIME…) have none, so an `analyze` run on one of them falls back to `unknown_issuer` (a 15 %/yr depeg, Beta(1.5, 10), 60 % recovered). The vault incident does not need a prior (it states p\*), but no ex-ante expected loss can be given for these positions.

**How.** One registry entry per token, with a basis from its own history where there is one (fxUSD's depegs, Midas's NAV rounds), and otherwise from the Pharos grade as an outside anchor (a stated mapping from grade to a yearly depeg probability, documented in `how-probabilities-are-computed.md`), never silently. Size S, mostly research.

## G16. f(x): oracle-source updates without a timelock

**What is missing.** f(x)'s own documentation says its 3-day timelock has one exception: "oracle source updates" bypass it. The events of those updates, `UpdateCurvePool` and `UpdateMaxPriceDeviation` (`IFxUSDPriceOracle.sol`), are not in `admin.ADMIN_EVENTS`. And `FxUSDPriceOracle`, which sets fxUSD's price inside fxSAVE's NAV, sits deeper than the admin surface's discovery (market oracle → feeds → vaults).

**How.** Discover it from fxSAVE: fxSAVE → its base pool → `priceOracle()`. Add the two events as a small protocol list next to `ADMIN_EVENTS` (decoded only on that contract), with a warn: "f(x) changed the price source behind fxSAVE's NAV, with no timelock". Start-up line: "fxSAVE's price source can be changed with no notice". Size S.

## G17. Data and scope

- **Midas TVL.** DefiLlama's `midas-rwa` slug reports no TVL, so the concentration line reads "no TVL reported". A fallback from the chain: the token's supply × its NAV (59.19 mGLOeuro × about 100,000 EUR), stated as such.
- **mROX** (Midas, RockawayX's own strategy, about 3.4M USD) is not a Morpho position and is not modelled (`ROCK-VAULT.md` §3). It would need a reader of Midas's issuance contracts and of mROX's own positions.

Size S for the TVL fallback; mROX is out of scope for now.

## G18. infiniFi: the loss waterfall and the pending loss

**What is missing.** siUSD is shocked by a chosen markdown. infiniFi's contracts say how a farm loss becomes a siUSD loss (`YieldSharingV3.sol:343-376`): the safety buffer first, then liUSD and the unwinding positions, then siUSD's rewards and principal, and only then the iUSD price. None of these sizes is read, so the tool cannot say how large a farm default must be before siUSD loses anything. And infiniFi exposes a pending loss before booking it: `unaccruedYield() < 0` (`YieldSharingV3.sol:178-187`), the moment siUSD exits also close.

**Why.** Impact: the brief asks how an incident propagates through the stack; here the stack has an explicit first-loss tranche. Detection: a public signal that precedes the oracle move.

**How**, modelled on `ethena.py`:

1. **`riskdep/infinifi.py`, a reader** at a block: `Accounting.totalAssetsValue()` and its split by farm type (`totalAssetsValueOf(LIQUID)`, `(MATURITY)`); iUSD supply and price; the liUSD total (`LockingController`), siUSD's total assets; the safety buffer (iUSD held by YieldSharing); `unaccruedYield()`; the redemption controller's liquidity and queue.
2. **A pure waterfall**: `infinifi=<loss in USD or as a share of the backing>` → what each tranche absorbs → the siUSD markdown (its loss ÷ its assets) and the iUSD markdown, as `token=siUSD:` and `token=iUSD:` shocks in `pipeline.venue_shocks`, with a note giving the split ("liUSD absorbs 9.0M of 9.5M; siUSD loses 0.5M, 1.2 %").
3. **A watch rule**: `InfiniFi.PendingLoss` (warn, then critical with the size relative to liUSD) when `unaccruedYield()` turns negative on a watched market's collateral, with the note that siUSD exits are closed until the loss is booked.
4. **The graph**: liUSD and the safety buffer in front of siUSD, the farm types behind iUSD.
5. **Recordings** under `fixtures/replay/infinifi/`; tests on the recorded sizes.

**Size.** M.

## G19. What `token=` means for an ERC-4626 collateral

**What is missing.** `analyze --vault 0xE018…1965 --shock token=siUSD:0.30` reports, for the siUSD/USDC market, "shock engine: oracle × 1.000, collateral market × 0.700": nobody is liquidated and the bad debt is counted as hidden. The same report's timing line says the loss lands "at once, when the issuer's accounting records the loss". The graph knows the oracle `converts through` siUSD's share rate (`BASE_VAULT`), and a loss infiniFi books lowers that rate (`StakedToken.applyLosses`). So either the engine reads `token=siUSD` as a fall of siUSD's market price only, which is a depeg, or its `converts through` transmission does not carry the markdown to the oracle. On fxSAVE, also an ERC-4626, the same shock moves the oracle (× 0.700), so the two vaults are not treated alike.

**Why.** Impact, defensibility: with the oracle moving, the market liquidates and the vault's loss and verdict change.

**How.**

1. **Verify** in `engine.py` which effect a `token=` shock sets on an Asset node (market price, or value) and which effect the `converts through` edge rule carries to the oracle. A one-market test on the recorded graph settles it.
2. **Make the meaning explicit.** `token=<t>:<f>` stays a loss of value, so an oracle that applies the token's rate sees it; a separate `depeg=<t>:<f>` is a fall of the market price with the rate unchanged. The incident's text says which one ran.
3. **Regression**: siUSD −30 % liquidates on the siUSD/USDC market; fxSAVE −30 % is unchanged; the committed shock-trace example is unchanged.

**Size.** S to verify; S–M if the edge rule changes.

## G20. infiniFi's price, oracle and loss events

**What is missing.** The iUSD price behind the oracle is set by `FixedPriceOracle.setPrice` (`ORACLE_MANAGER`); the RT oracle's source can be repointed by the `GOVERNOR` (`SetAccounting`); a booked siUSD loss emits `VaultLoss`; every module can be paused through `InfiniFiCore` roles. `PriceSet`, `OracleSet`, `SetAccounting` and `VaultLoss` are not in `admin.ADMIN_EVENTS`, and the roles live in `InfiniFiCore`, which the admin surface does not reach from the market's oracle.

**How.** Discover the chain from the oracle: the RT oracle → its `accounting()` → `Accounting.oracle(iUSD)` → the `FixedPriceOracle`; and siUSD → `core()`. Decode the four events on those contracts only (a small protocol list next to `ADMIN_EVENTS`): `PriceSet` and `OracleSet` warn ("the price behind siUSD's oracle was set to …"), `VaultLoss` critical with the amount ("infiniFi booked a loss on siUSD"), pauses critical. The timelocks' delays (1 day and 7 days per the docs) are read on-chain where the role holder is a timelock. Size S.

## Already covered, or not applicable

| DeFiScan check | In riskdep |
|---|---|
| The vault's total cross-checked against on-chain `totalAssets()` | `crosscheck.py`: Morpho API against chain, 0.5 % tolerance |
| Price feeds discovered inside each market's oracle (`BASE_FEED_1`…) | `oracle_class.py`, `admin.py`, `discover.py` |
| The guardian's veto of pending changes | Vault V2 sentinels drawn with their role (`graph.py`); V1 guardian in G7 |
| Every permissioned function scored with its delay | Functions changeable with no notice listed at start, abdication checked, exit gates flagged (`rules.py`, D184) |
| Fields that tick every heartbeat kept out of alerts | Alerts fire on events and thresholds, never on a raw ticking value |
| Allocators enumerated from `SetIsAllocator` | Decoded in `rules.py`; listed and confirmed with `isAllocator` in `graph.py` |
| Call graph, lines of code, logo, project registration | Specific to the DeFiScan site; not a risk input |
