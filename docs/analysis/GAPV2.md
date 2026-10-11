# GAPV2: suggested improvements, and how to build them

`GAP.md` challenges the risk model's assumptions (K1–K24). This file is narrower and newer (2026-10-11). It lists gaps found by:

- comparing riskdep with DeFiScan's Morpho vault review (`deficollective/defiscan-skills`, `review-morpho-vault/SKILL.md`, read 2026-10-11, not run);
- comparing it with DeFiScan's impact analysis of a permissioned function (`analyze-impact/SKILL.md`, in the local clone `../defiscan-skills/`, read 2026-10-11, not run): G10;
- the Zama and Ethena write-ups of the same day (`docs/model/zama-confidential-vaults.md`, `docs/model/ethena.md`).

Each gap gets an id `G<n>`, what is missing, why it matters for the brief (`docs/hackaton_instruction/GOAL.md`: discovery 30 %, impact 30 %, decision 25 %, demo 15 %), how to build it in this codebase, and a size (S, M, L). Decision numbers are left to the plan that builds each one.

DeFiScan's skill reviews a MetaMorpho (Vault V1) vault and treats Vault V2 as out of scope. Several of its checks are therefore already covered here in V2 form, or do not apply; they are listed at the end.

## Summary

| # | Gap | Criterion | Size | Recommended order |
|---|---|---|---|---|
| G1 | Worst-case exposure up to the caps, per oracle and feed | discovery, impact | S | 1 |
| G2 | Who holds each role: EOA, Safe (threshold), timelock | discovery, decision | S | 2 |
| G3 | The protocol's hard limits next to the current settings | decision | S | 3 |
| G4 | The Zama layer in the engine's graph, and a decryption halt | discovery, impact | S–M | 4 |
| G5 | Ethena: the venue stress stated as a bound; custodians; the unstaking cooldown | impact, decision | S | 5 |
| G6 | Web pages for incidents, shocks and backtests | demo | M | 6 |
| G7 | Vault V1 (MetaMorpho) as a watch and incident target | discovery | M | 7 |
| G8 | Other chains | discovery | L | later |
| G9 | Audits, bug bounty, licence as provenance | — | S | optional |
| G10 | Each admin change classified: hits existing deposits, only future ones, or enables another change; with the funds it can move | impact, decision | S | 2, with G2 |

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
