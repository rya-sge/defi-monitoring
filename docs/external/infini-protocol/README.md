# infiniFi — external references

This folder holds three sources for infiniFi, the issuer of iUSD, siUSD and liUSD:

| Folder | Source | Pin | Status |
|---|---|---|---|
| `docs.infinifi.xyz-docs/` | <https://docs.infinifi.xyz>. 9 pages plus `_index.md`. Each page starts with `> Source: <url>`, followed by ~490 lines of Mintlify CSS to skip; the text starts around line 495. | snapshot, undated (`vaults.md` says it is "generated from the infiniFi protocol API once per day") | **git-ignored** (`.gitignore` line 16), local only |
| `infinifi-protocol/` | <https://github.com/InfiniFi-Labs/infinifi-protocol> (Solidity 0.8.28, Foundry) | `aeb468e` (2026-10-01) | git submodule |
| `DefiLlama-Adapters/` | <https://github.com/InfiniFi-Labs/DefiLlama-Adapters> (InfiniFi fork, 55 MB). Only `projects/infiniFi/index.js` matters. | `28f2a2086` (2025-05-22, "add infiniFi TVL tracking") | git submodule |

This README is tracked. Read the submodules only; never edit them.

## Why it matters to riskdep

The RockawayX USDC Yield Morpho vault lends about $2.4M against siUSD, in an $8M market with a 91.5 % LLTV where one borrower holds 94 % of the debt (`docs/analysis/ROCK-VAULT-DEP.md`). The market oracle never sees a market price:

- `BASE_FEED_1` `0xF81A…7067` is `CHAINLINK_FORMATTED_ORACLE_IUSD` (`infinifi-protocol/deployment/configuration/addresses.1.json:507`). It is a `ChainlinkRTOracle` that returns `Accounting.price(iUSD)`.
- That value is an admin-set `FixedPriceOracle` (1.0).
- `BASE_VAULT` is siUSD `convertToAssets`.

So the Morpho price moves only when infiniFi itself books a loss. The contracts below say when that happens, in what order, and who can trigger it. They also show how a liquidator who seizes siUSD gets out: only through the Gateway, which can be paused, then through a FIFO redemption queue.

## Tree

```
infini-protocol/
├── docs.infinifi.xyz-docs/            # issuer docs (git-ignored)
│   ├── whitepaper.md                  # fractional-reserve design, FIFO redemption queue, Curve backstop
│   ├── slashing-mechanics.md          # tranches, loss waterfall, $25k safety buffer, worked $9M example
│   ├── risk-disclosures.md            # bank run, hacks, junior wiped out → iUSD socialised
│   ├── vaults.md                      # live farm list (liquid / illiquid, bucket, farm address)
│   ├── audits.md                      # audits, Hypernative, bug bounty, timelocks, 4/7 multisig
│   ├── oracles.md                     # Pendle PT oracle only (thin)
│   └── index.md, deposit-quickstart.md, pendle-liquidity-transfer.md
├── infinifi-protocol/                 # submodule
│   ├── deployment/configuration/      # addresses.{1,8453,143}.json, roles.{…}.json (who holds which role)
│   ├── script/                        # Deploy / ContractRegistry (FixedPriceOracle for iUSD)
│   ├── src/core/                      # InfiniFiCore (roles), CoreControlled (pause, emergencyAction)
│   ├── src/tokens/                    # ReceiptToken (iUSD), StakedToken (siUSD), LockedPositionToken (liUSD)
│   ├── src/finance/                   # Accounting, YieldSharing V1–V3 (P&L, loss waterfall), oracles/
│   ├── src/funding/                   # MintController, RedeemController, RedemptionPool (queue)
│   ├── src/locking/                   # LockingController (liUSD buckets), UnwindingModule
│   ├── src/integrations/              # Farm, MaturityFarm, FarmRegistry; farms/ (~40 farms) + farms/movement/
│   ├── src/gateway/                   # InfiniFiGatewayV1–V3 (user entry point, upgradeable proxy)
│   ├── src/periphery/                 # ChainlinkRTOracle, ChainlinkSTOracle(V2), UnstakeAndRedeemHelper
│   ├── src/governance/                # Timelock, AllocationVoting, MinorRolesManager
│   ├── src/libraries/                 # CoreRoles, FarmTypes, EpochLib, RedemptionQueue
│   └── test/                          # unit/, integration/, scenarios/
└── DefiLlama-Adapters/projects/infiniFi/
    └── index.js                       # TVL = Accounting.totalAssetsValue()
```

## Main files

| Path | What | riskdep use |
|---|---|---|
| `infinifi-protocol/src/periphery/ChainlinkRTOracle.sol` | Morpho `BASE_FEED_1`: `price()` returns `Accounting.price(receiptToken)` | explains why the feed answers 1.0 |
| `infinifi-protocol/src/finance/Accounting.sol` | per-asset oracle map, `totalAssetsValue()` | backing vs supply; DefiLlama TVL |
| `infinifi-protocol/src/finance/oracles/FixedPriceOracle.sol` | iUSD price, set by `ORACLE_MANAGER` | the single number behind the Morpho price |
| `infinifi-protocol/src/finance/YieldSharingV3.sol` | `unaccruedYield()`, `_handleNegativeYield()` loss waterfall | detect a pending loss before it is booked |
| `infinifi-protocol/src/tokens/StakedToken.sol` | siUSD (ERC-4626): pause gates, `applyLosses` | siUSD rate and when siUSD cannot be withdrawn |
| `infinifi-protocol/src/tokens/ReceiptToken.sol` | iUSD: plain ERC20 with role-gated mint and burn | no pause, not a proxy |
| `infinifi-protocol/src/locking/LockingController.sol` | liUSD junior tranche, `applyLosses`, `maxLossPercentage` | size of the first-loss buffer |
| `infinifi-protocol/src/funding/RedeemController.sol`, `RedemptionPool.sol` | redemption and FIFO queue | exit time for a liquidator |
| `infinifi-protocol/src/core/CoreControlled.sol`, `src/libraries/CoreRoles.sol` | pause and roles | admin surface |
| `infinifi-protocol/deployment/configuration/addresses.1.json`, `roles.1.json` | mainnet addresses and role holders | registry entries, admin graph |
| `docs.infinifi.xyz-docs/slashing-mechanics.md` | the issuer's loss policy | scenario narrative |
| `DefiLlama-Adapters/projects/infiniFi/index.js` | TVL method | cross-check `totalAssetsValue` |

## Read first for this project

### iUSD / siUSD / liUSD and the loss waterfall
- `YieldSharingV3.sol:178-187`: `unaccruedYield() = totalAssetsValue / price(iUSD) − iUSD.totalSupply()`. A negative value is a loss that has not been booked yet.
- `YieldSharingV3.sol:343-376`: the order in which losses are applied:
  1. Safety buffer (iUSD held by YieldSharing), if it covers the whole loss.
  2. Locking users: `LockingController.applyLosses`, which covers liUSD and unwinding positions.
  3. siUSD holders: `StakedToken.applyLosses`.
  4. **Only then** the iUSD price: `newPrice = price × (supply − loss) / supply` via `FixedPriceOracle.setPrice`. **The RT oracle stays at 1.0 until liUSD and siUSD are wiped out.**
- `StakedToken.sol:126-137`: an siUSD loss is taken first from next-epoch rewards, then from current-epoch rewards, then from principal (the iUSD in the vault is burned). This lowers `convertToAssets`, which is the `BASE_VAULT` leg. Epoch = 1 week with a 3-day offset (`EpochLib.sol:5-6`).
- `LockingController.sol:66,432-446`: `maxLossPercentage = 0.999999e18`. A loss above it burns all liUSD and **pauses** the LockingController.
- `slashing-mechanics.md:525-526,539,563-573`: the docs call siUSD "Senior … last to absorb losses" and Locked-iUSD "Junior". The $25,000 safety buffer covers slippage. Worked example: a $9M bad debt on $10M junior + $10M senior leaves liUSD at $0.10 and siUSD untouched. The docs **merge siUSD and iUSD into the senior tranche**. The code (step 3 above) slashes siUSD before plain iUSD.
- `slashing-mechanics.md:602,609`: clear-cut defaults are slashed "without requiring a governance vote, subject to automated circuit breakers". "Lending against siUSD provides an additional safety buffer … discounted LTV."

### Reserves and farms
- `whitepaper.md:535,589`: "the first fractional reserve stablecoin". Part of the illiquid allocation comes from liquid depositors.
- `FarmTypes.sol:6-12`: `PROTOCOL=0`, `LIQUID=1` (instant withdrawal, e.g. Aave), `MATURITY=2` (illiquid, principal locked until maturity). `Accounting.totalAssetsValueOf(type)` (`Accounting.sol:59`) splits backing by type.
- `Farm.sol:18,24,43,49`: per-farm `cap` (default `uint256.max`) and `maxSlippage` (0.999999e18).
- `vaults.md:523-690`. Active liquid farms: Cap stcUSD, Multi Farm (swap), Spark sUSDC. Active illiquid farms: 3F Bridge Facilitator, BASE Liquidity Farm, f(x) fxSAVE, FalconX Institutional (1w), Morpho infiniFi Ecosystem Vault (Steakhouse), New Silver ×2, Fasanara Genesis, Fasanara mGLOBAL. **Paused:** Aave USDC, Euler Sentora, Horizon. The current book is mostly off-chain credit; ROCK-VAULT-DEP's "Aave, Pendle, Fluid, Ethena" is out of date.

### Redemption queue and limits
- `RedeemController.sol:77-131`: `redeem` pays at once up to `liquidity()` (USDC on the controller minus `totalPendingClaims`) and queues the rest. **If the queue already has entries, the whole amount is queued.** `minRedemptionAmount = 1` (line 30).
- `RedeemController.sol:173-178`: USDC per iUSD = `price(iUSD) / price(USDC)`. Redemptions follow the same oracle.
- `RedemptionPool.sol:56-94`: the queue is filled FIFO as assets arrive (`RedemptionQueue.sol`, `uint96` amounts). `whitepaper.md:597`: requests are served "as illiquid assets reach maturity".
- `YieldSharingV3.sol:99-101,232-235`: direct siUSD ERC-4626 deposits and withdrawals **revert** unless the Gateway sets a transient flag. A liquidator must use `InfiniFiGatewayV2.unstake` (`:136`, `whenNotPaused`) or `UnstakeAndRedeemHelper.unstakeAndRedeem` (`:39`).
- `StakedToken.sol:66-77`: `maxRedeem` and `maxWithdraw` return 0 when siUSD is paused **or** `unaccruedYield() < 0`, which blocks exits while a loss is pending.
- `risk-disclosures.md:511-515`: in a bank run the exit is iUSD/USDC pools on Curve, Balancer and Fluid, at a depegged price.

### RT oracle (ChainlinkRTOracle)
- `ChainlinkRTOracle.sol:34-36`: `price() = Accounting(accounting).price(receiptToken)`. `:44-48`: `roundId 0`, `updatedAt = block.timestamp`, so there is never a staleness signal. `:29`: the `GOVERNOR` can repoint `accounting`.
- `Accounting.sol:30-38`: `price(asset) = IOracle(oracle[asset]).price()`. `setOracle` is gated by `ORACLE_MANAGER`.
- `FixedPriceOracle.sol:16-18`: `setPrice` is gated by `ORACLE_MANAGER`. Holders in `roles.1.json`: YIELD_SHARING_PROXY, ORACLE_FACTORY, ACCOUNTING, TIMELOCK_SHORT, TIMELOCK_LONG.
- An alternative feed exists: `ChainlinkSTOracle.sol:39-42` (`price(iUSD) × siUSD.convertToAssets(1e18)`), deployed as `CHAINLINK_FORMATTED_ORACLE_SIUSD` / `_V2`.
- `docs.infinifi.xyz-docs/oracles.md:508-526` covers only the Pendle PT oracle and claims "circuit breakers". It says nothing about the iUSD price.

### Pausing, governance and roles (InfiniFiCore)
- `InfiniFiCore.sol:8`: `AccessControlEnumerable`. `createRole` and `setRoleAdmin` are gated by `GOVERNOR` (`:50,58`).
- `CoreControlled.sol:9,54,59,84`: every module is `Pausable`. `pause` needs `PAUSE`, `unpause` needs `UNPAUSE`. `emergencyAction` makes arbitrary calls.
- `CoreRoles.sol:8-95`: 25 roles.
- `roles.1.json`:

  | Role | Holders |
  |---|---|
  | GOVERNOR | TIMELOCK_LONG, FLUID_REWARDS_CLAIMER |
  | PAUSE | TIMELOCK_LONG, EMERGENCY_WITHDRAWAL, PAUSER_1–4, MATURED_FARM_CLEANER, TEAM_MULTISIG |
  | UNPAUSE | EMERGENCY_WITHDRAWAL, TEAM_MULTISIG |
  | FINANCE_MANAGER | YIELD_SHARING_PROXY, PL_SMOOTHER_HELPER, … |

- `audits.md:538-544`: timelocks of 1 day and 7 days. TEAM_MULTISIG is a 4/7 Safe, `0x8060…400c`.
- Addresses (`addresses.1.json`): CORE `0xF6d4…5490`, ACCOUNTING `0x7A5C…42B3`, RECEIPT_TOKEN `0x48f9…D89c`, STAKED_TOKEN `0xDBDC…9bCB`, YIELD_SHARING_PROXY `0x90E9…AE3b`, GATEWAY_PROXY `0x3f04…25b5` (with GATEWAY_PROXY_ADMIN, so the Gateway is upgradeable).
- `ReceiptToken.sol:11`: iUSD has no `whenNotPaused` on transfer. Only mint and burn are role-gated. siUSD transfers are not paused either; only its 4626 limits go to 0. ROCK-VAULT-DEP marks both tokens "pausable", which is only true for siUSD.

### Audits
- `audits.md:512-536`:
  - Spearbit (Apr 2025), plus addenda for PRs 169, 228, 209, 224 and 233 (Jun–Dec 2025)
  - Cantina crowd audit (May 2025)
  - Certora formal verification (May 2025)
  - TestMachine pen-test (Jun 2025)
  - Three Sigma (ongoing)
  - Hypernative monitoring
  - Cantina bug bounty

  The reports are DocSend links only and are not stored here.

### Risk disclosures
- `risk-disclosures.md:519`: a single-asset default is "socialized across **all locked-iUSD depositors**".
- `risk-disclosures.md:531`: if locked-iUSD is wiped out, losses go to iUSD holders through "a rebase-mechanism". The code does this through the oracle price, not a rebase.
- `risk-disclosures.md:539`: under a fully inverted yield curve, infiniFi "will no longer operate normally".

### TVL accounting (DefiLlama)
- `DefiLlama-Adapters/projects/infiniFi/index.js:1-13`: calls `Accounting(0x7A5C…42B3).totalAssetsValue()` and books the result as USDC (`/1e12`). The TVL is therefore infiniFi's own oracle-priced farm total. It is not checked against the underlying positions, and a farm marked at par still counts in full.

## Gaps

- The docs snapshot has no date, and `vaults.md` changes daily. Farm sizes and balances are not in it. Read `FarmRegistry` and `Farm.assets()` on-chain.
- Not in the repo: the source of `GATEWAY_IMPLEMENTATION_V4` (`addresses.1.json`; only V1–V3 are in `src/gateway/`), the `TIMELOCK_SHORT` and `TIMELOCK_LONG` delays (only the docs give 1 day and 7 days), the PAUSER_1–4 signers, and the multisig threshold (only the docs give 4/7).
- Which YieldSharing version is behind `YIELD_SHARING_PROXY` must be checked on-chain. These notes assume V3.
- Docs and code disagree on whether siUSD is junior to plain iUSD. riskdep should follow the code (siUSD is slashed before the iUSD price moves).
- The audit PDFs are not stored here. The DefiLlama fork is pinned at May 2025 and may lag upstream.
- Nothing describes the "automated circuit breakers" (`slashing-mechanics.md:602`), the keeper (`KEEPER_LOSS`) cadence for `accrue()`, or how long `unaccruedYield() < 0` can block siUSD exits.
