# Morpho — external references

Read-only Morpho references for `riskdep`. `docs.morpho.org-developers-docs/` is the Morpho developer documentation (https://docs.morpho.org/developers) scraped to markdown (87 pages). It is **git-ignored**, so it exists only in the local checkout; `tests/test_watch_replay.py` skips its selector check when the folder is absent. The four `lib/` folders are git submodules (run `git submodule update --init` after a clone), pinned at: `morpho-blue` `8e26ca6a` (github.com/morpho-org/morpho-blue), `vault-v2` `d992cb84` (morpho-org/vault-v2), `morpho-blue-oracles` `9d2a0b66` (morpho-org/morpho-blue-oracles), `metamorpho-v1.1` `3b17547e` (morpho-org/metamorpho-v1.1). Their own nested `lib/` submodules (forge-std, morpho-blue-irm, midnight, …) are **not** initialised and are empty.

## Why it matters to riskdep

- **`lib/vault-v2`** → `vault.py` (vault → adapters → markets, cap ids, real assets), `rules.py` and `admin.py` (role, gate, timelock and cap events), `exit_queue.py` (liquidity adapter, `forceDeallocate` penalty), `drain.py` (Public Allocator inflow), `abi.py` (Vault V2 and adapter events and selectors); the gate and timelock findings of `docs/analysis/ROCK-VAULT-DEP.md` §2.
- **`lib/morpho-blue`** → `abi.py` (Blue events), `market_risk.py` (health check, LIF, bad debt), `drain.py` (LLTV arbitrage), `exit_queue.py` (bad debt written off only at liquidation); `docs/analysis/GAP.md` K9 (liquidation at the oracle price).
- **`lib/morpho-blue-oracles`** → `oracle_class.py` (base vault × base feeds ÷ quote vault × quote feeds), `admin.py` (feeds and vaults an oracle reads); ROCK-VAULT-DEP.md §3 ("no staleness check and no admin"), GAP.md K23 (feed quality).
- **`lib/metamorpho-v1.1`** → the future Vault V1 deposit watch (`docs/analysis/NEXT_STEP.md` step 4) and the `MorphoVaultV1Adapter` of Vault V2.
- **`docs.morpho.org-developers-docs/contracts/`** → `tests/test_watch_replay.py::test_selectors_match_the_morpho_docs` checks the `TIMELOCKED` selectors in `abi.py` against the tables in `morpho-vaults-v2.md` and `morpho-market-v1-adapter-v2.md`; `addresses.md` gives the Blue, IRM and `BluePublicAllocator` addresses (`drain.py` cites it).
- **`docs.morpho.org-developers-docs/api/`** → `sources.py` (`morpho()` GraphQL: `vaultV2ByAddress`, `marketPositions`, `markets`, `marketById`, `userByAddress`, `vaults`).
- **`contracts/irm.md`** → GAP.md K10 (AdaptiveCurveIRM rate risk); `earn/tutorials/force-deallocate.md`, `in-kind-redemption.md` → `exit_queue.py`.

## Tree

```
morpho/
├── README.md
├── docs.morpho.org-developers-docs/   # scraped docs, git-ignored; _index.md is the table of contents
│   ├── contracts/                     # per-contract reference: functions, events, selector tables, addresses
│   ├── api/                           # GraphQL API: endpoint, limits, vault / market / Midnight queries
│   ├── borrow/                        # Blue concepts: liquidation, LTV, IRM, shared liquidity, Public Allocator tutorial
│   ├── earn/                          # vault concepts and tutorials: forceDeallocate, in-kind exit, assets flow
│   ├── midnight/                      # Morpho Midnight (fixed-rate, ticks, maturity exits)
│   ├── ecosystem/                     # oracle providers, bots, dashboards
│   ├── rewards/  sdks/  agents/       # rewards distribution, TypeScript SDK, LLM/MCP access (low relevance)
└── lib/
    ├── morpho-blue/src/               # Morpho.sol, libraries/ (Constants, Events, SharesMath, MathLib), periphery/, interfaces/
    ├── vault-v2/src/                  # VaultV2.sol, adapters/ (MarketV1AdapterV2, VaultV1Adapter, Midnight), periphery/ (gates, registries, BluePublicAllocator), libraries/
    ├── morpho-blue-oracles/src/       # morpho-chainlink/ (MorphoChainlinkOracleV2 + libraries), wsteth-exchange-rate-adapter/
    └── metamorpho-v1.1/src/           # MetaMorphoV1_1.sol, libraries/ (Constants, Events, Pending), interfaces/
```

## Main files

| Path | What it holds | riskdep uses it for |
|---|---|---|
| `lib/vault-v2/src/VaultV2.sol` | The vault; the header (lines 21–148) states every design rule: losses, caps, adapters, liquidity adapter, timelocks, gates, roles | gate/timelock alerts, exit model, cap ids |
| `lib/vault-v2/src/libraries/EventsLib.sol` | 41 Vault V2 events | `abi.py` signatures, `rules.py` |
| `lib/vault-v2/src/libraries/ConstantsLib.sol` | `MAX_MAX_RATE` 200 % APR, `MAX_PERFORMANCE_FEE` 50 %, `MAX_MANAGEMENT_FEE` 5 %/yr, `MAX_FORCE_DEALLOCATE_PENALTY` 2 % | bounds on admin settings |
| `lib/vault-v2/src/adapters/MorphoMarketV1AdapterV2.sol` | Blue-market adapter: `ids()` (3 cap ids), `realAssets`, `burnShares` | `vault.cap_ids`, real assets, loss write-off |
| `lib/vault-v2/src/adapters/MorphoVaultV1Adapter.sol` | Adapter into a Vault V1 (single id `"this"`) | nested-vault exposure |
| `lib/vault-v2/src/periphery/blue-public-allocator/BluePublicAllocator.sol` | Permissionless reallocation within PA caps, with a penalty | `drain.py` inflow (D71) |
| `lib/vault-v2/src/periphery/gates/WhitelistSendAssetsGate.sol`, `WhitelistReceiveSharesGate.sol` | Reference whitelist gates | identifying gate contracts (ROCK-VAULT-DEP §2) |
| `lib/morpho-blue/src/Morpho.sol` | Blue core: supply/borrow/liquidate, interest accrual, health check | `market_risk.py`, `drain.py` |
| `lib/morpho-blue/src/libraries/ConstantsLib.sol` | `MAX_FEE` 25 %, `ORACLE_PRICE_SCALE` 1e36, `LIQUIDATION_CURSOR` 0.3, `MAX_LIQUIDATION_INCENTIVE_FACTOR` 1.15 | LIF, price scaling |
| `lib/morpho-blue/src/libraries/EventsLib.sol` | 18 Blue events (`Liquidate` carries bad debt) | `abi.py`, `rules.py` |
| `lib/morpho-blue/src/libraries/SharesMathLib.sol` | Virtual shares 1e6 / virtual assets 1 | share ↔ asset conversion |
| `lib/morpho-blue-oracles/src/morpho-chainlink/MorphoChainlinkOracleV2.sol` | Standard oracle, `price()` at lines 151–156, `SCALE_FACTOR` lines 132–138 | `oracle_class.py`, `admin.py` |
| `lib/morpho-blue-oracles/src/morpho-chainlink/libraries/ChainlinkDataFeedLib.sol` | `getPrice`: no staleness, no bounds check | staleness warnings |
| `lib/metamorpho-v1.1/src/MetaMorphoV1_1.sol` | Vault V1.1: queues, caps, timelock, `lostAssets` | future V1 watch |
| `docs.morpho.org-developers-docs/contracts/morpho-vaults-v2.md` | Vault V2 reference with selector table | selector test, roles |
| `docs.morpho.org-developers-docs/contracts/morpho-market-v1-adapter-v2.md` | Adapter reference with selector table | selector test |
| `docs.morpho.org-developers-docs/contracts/addresses.md` | Deployed addresses per chain | Blue, IRM, PA addresses |
| `docs.morpho.org-developers-docs/api/get-started.md`, `api/morpho-vaults.md`, `api/morpho.md` | GraphQL endpoint, limits, example queries | `sources.py` |

## Read first for this project

**Vault V2 roles, timelocks, gates, adapters**
- `lib/vault-v2/src/VaultV2.sol:114-130` (GATES): `sendSharesGate` and `receiveAssetsGate` each "Can lock users out of exiting the vault"; `receiveSharesGate` "Can block all vault interactions if it reverts"; `sendAssetsGate` "is not critical (cannot block users' funds)". Set to 0 to disable. Basis of ROCK-VAULT-DEP §2 (gate timelock 0 in all 8 RockawayX vaults).
- `VaultV2.sol:135-141` (ROLES): owner cannot directly hurt depositors but sets curator and sentinels; curator only through a timelock; allocators move funds within caps with no timelock, set the liquidity adapter (can block deposits and withdrawals, not `forceDeallocate`) and `maxRate`; roles are not two-step.
- `VaultV2.sol:99-112` (TIMELOCKS, ABDICATION): the timelock of `decreaseTimelock(sel, …)` is `timelock[sel]`; abdicated functions can never be called; `submit` at line 306, `revoke` 329, `decreaseTimelock` 425, `abdicate` 434. Line 148: at creation every timelock is 0 and there are no gates.
- `VaultV2.sol:21-47`: losses are realised in `accrueInterest` from adapters' `realAssets()`; relative caps are "soft" (not checked on exit) and relative to `firstTotalAssets`; track allocations with `Allocate`/`Deallocate` events only.
- `VaultV2.sol:78-82` (LIQUIDITY ADAPTER): deposits go to it, withdrawals pull from it when idle is short.
- `lib/vault-v2/src/adapters/MorphoMarketV1AdapterV2.sol:259-265`: cap ids `"this"`, `"collateralToken"`, `"this/marketParams"`; lines 18–34: only AdaptiveCurveIRM markets, `burnShares` is timelocked so "reactive depositors might be able to exit before the share price reduction".

**Blue liquidation, LIF, bad debt**
- `lib/morpho-blue/src/Morpho.sol:527-538`: healthy iff `collateral × price / 1e36 × LLTV ≥ borrowed` (borrow rounded up).
- `Morpho.sol:366-369`: `LIF = min(1.15, 1 / (1 − 0.3 × (1 − LLTV)))` (constants in `libraries/ConstantsLib.sol:5-14`); LLTV 86 % → 1.0438, 91.5 % → 1.026, cap 1.15 reached at LLTV ≤ ~56.5 %. `borrow/concepts/liquidation.md:45-66` rounds 86 % to "≈ 1.05".
- `Morpho.sol:390-402`: bad debt is written off only when a liquidation leaves collateral = 0; it is deducted from `totalSupplyAssets` (lenders' loss) and reported in the `Liquidate` event. Until then it stays in the share price (the "unrealised bad debt" of `market_risk.py` and `exit_queue.py`).

**IRM (AdaptiveCurveIRM)**
- `docs.morpho.org-developers-docs/contracts/irm.md:109-170, 280-289`: target utilisation 90 %; rate at 100 % = 4 × r90 (`CURVE_STEEPNESS` 4); `ADJUSTMENT_SPEED` 50/yr, so r90 doubles in ~5 days at 100 %; `INITIAL_RATE_AT_TARGET` 4 %, min 0.1 %, max 200 % APR. Ethereum address `0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC` (`contracts/addresses.md:89`). Source not in this folder (see Gaps).

**Oracles, scaling, no staleness check**
- `lib/morpho-blue-oracles/src/morpho-chainlink/MorphoChainlinkOracleV2.sol:151-156`: `price = SCALE_FACTOR × baseVault.convertToAssets(sample) × baseFeed1 × baseFeed2 / (quoteVault… × quoteFeed1 × quoteFeed2)`; `SCALE_FACTOR` (lines 132–138) brings the result to 1e36 adjusted for decimals. Immutable, no admin.
- `libraries/ChainlinkDataFeedLib.sol:13-26`: a zero feed returns 1; "Staleness is not checked", min/max bounds not checked, only `answer >= 0`. `libraries/VaultLib.sol:13-16`: vault conversion is `convertToAssets` (exchange-rate, not market).
- `wsteth-exchange-rate-adapter/WstEthStEthExchangeRateChainlinkAdapter.sol:26`: a Chainlink-shaped exchange rate (constant-price class in `oracle_class.py`).
- `docs.morpho.org-developers-docs/contracts/oracles.md:79-87` (assumptions) and `ecosystem/oracles.md` (Pendle PT, LST rates, f(x) adapters).

**Vault V1.1: lostAssets, queues**
- `lib/metamorpho-v1.1/src/MetaMorphoV1_1.sol:923-937`: if real assets drop below `lastTotalAssets − lostAssets`, `lostAssets` grows; losses are tracked, not socialised away silently (`lostAssets` storage at line 109).
- `libraries/ConstantsLib.sol:10-16`: `MAX_TIMELOCK` 2 weeks, `POST_INITIALIZATION_MIN_TIMELOCK` 1 day, `MAX_QUEUE_LENGTH` 30; queues set at `MetaMorphoV1_1.sol:336` (`setSupplyQueue`) and `351` (`updateWithdrawQueue`), `reallocate` at 394.

**Public Allocator**
- `lib/vault-v2/src/periphery/blue-public-allocator/BluePublicAllocator.sol:13-23`: must be a vault allocator; only `MorphoMarketV1AdapterV2` adapters; per-call penalty paid by the caller as a donation to the vault; vault caps still enforced; anyone can front-run to make it revert; can drain the liquidity market. Ethereum address `0x00b8e150…1e27` (`contracts/addresses.md:401`), as in `drain.py:28`.
- `docs.morpho.org-developers-docs/contracts/blue-public-allocator.md:13-19, 181` and `borrow/tutorials/public-allocator.md`.

**Exit routes**
- `VaultV2.sol:785-798` (`forceDeallocate`): permissionless in-kind exit; penalty `assets × forceDeallocatePenalty[adapter]` (≤ 2 %) withdrawn from `onBehalf`; optimal amount when illiquid is `min(market liquidity, A / (1 + penalty))`.
- `docs.morpho.org-developers-docs/earn/tutorials/force-deallocate.md` (cost, per-market capacity, largest-market-first, zero-penalty vaults) and `earn/tutorials/in-kind-redemption.md` (V2 and V1 variants); `contracts/morpho-vaults-v2.md:199-215, 762-779`.

**API docs used by sources.py**
- `docs.morpho.org-developers-docs/api/get-started.md:20, 53-81`: endpoint `https://api.morpho.org/graphql`; max complexity 1,000,000; 750 requests/min (429 with `Retry-After: 600`), ~20,000/hour triggers a 7-day ban. `sources.py:24` still calls `https://blue-api.morpho.org/graphql`.
- `api/morpho-vaults.md:157, 319` (`vaultV2ByAddress` queries), `api/morpho.md` (markets, positions), `api/changelog.md` (schema changes).

## Gaps

- **AdaptiveCurveIRM source**: `vault-v2/lib/morpho-blue-irm` is not initialised (only `src/imports/AdaptiveCurveIrmImport.sol` points to it); constants come from `irm.md` only. Add `morpho-org/morpho-blue-irm` for K10.
- **Midnight source**: `vault-v2/lib/midnight` is empty; `MidnightAdapter.sol` and its ratifiers cannot be read against the core.
- **Vault V1.0 (`metamorpho`)**: older vaults (no `lostAssets`) are not here.
- **Bundler3 / adapters** (`contracts/bundles.md` only) and the legacy flow-cap `PublicAllocator` for Vault V1 (no source).
- **Non-standard oracles** used by watched markets (Pendle PT linear-discount / TWAP wrappers, RedStone, Ojo, Midas custom aggregators): not Morpho code; see ROCK-VAULT-DEP.md §10.
- **GraphQL schema**: no SDL/introspection dump; field names are only in examples. The `blue-api` vs `api.morpho.org` endpoint should be checked.
- **Formal specs / audits**: `lib/*/certora` and `audits/` exist in the submodules but are not summarised here.
