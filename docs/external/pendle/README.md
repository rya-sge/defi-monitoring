# Pendle — external references

Read-only references for Pendle V2: the developer docs scraped from <https://docs.pendle.finance/pendle-v2-dev/> (63 Markdown pages, one `> Source:` URL at the top of each) and three git submodules from <https://github.com/pendle-finance>: `lib/pendle-core-v2-public` at `87685c89`, `lib/Pendle-SY-Public` at `73676d9`, `lib/external-integration` at `1694fea` (pins from `git -C <path> rev-parse --short HEAD`). The docs folder is **tracked in git** (`git check-ignore` matches nothing, `git ls-files` lists its pages), unlike the Morpho, Chainlink or Tori docs folders. The three `lib/` folders are **submodules** (`.gitmodules`): run `git submodule update --init` after a clone. Never edit inside `lib/`.

## Why it matters to riskdep

`analyze` only supports a Pendle PT used as Morpho Blue collateral (`docs/how-risk-is-computed.md`). These sources back:

| riskdep piece | What it relies on here |
|---|---|
| `discover.py` `find_pendle_market`, `_build_pt_layers` | Pendle API `/v1/1/markets/{active,inactive}` and `/v2/1/markets/{m}/data` (implied APY, `ptDiscount`, liquidity, expiry) |
| `discover.py` `exit_quote` (exit cost) | Hosted SDK `/v2/sdk/1/markets/{m}/swap` → `priceImpact`, `fee`; Pendle AMM maths behind it |
| `riskdep/registry.json` `oracle_getters` / `oracle_patterns` | `twapDuration()` → price-tracking (`PendleChainlinkOracle`); `baseDiscountPerYear()` → constant-price (`PendleSparkLinearDiscountOracle`) |
| `oracle_class.py` (composites, `MAX_DEPTH = 2`) | Ojo `min(TWAP, linear)` and `MetaOracleDeviationTimelock` wrap the Pendle oracles below |
| `propagate.py` `pt_stress_extra` (registry `pt_stress_basis`, 1.5×) | PT trades below redemption value when the pool thins; the TWAP oracle passes it on, the linear one does not |
| maturity / days to maturity, ROCK-VAULT-DEP §7 | PT redeems 1:1 for the accounting asset at expiry, through the SY |
| priors (`registry.json` `protocols.pendle`) | Core or SY-adapter exploit reaches PT holders directly |

## Tree

```text
pendle/
├── README.md
├── docs.pendle.finance-pendle-v2-dev-docs/   # tracked; Pendle V2 dev docs (_index.md = table of contents)
│   ├── Backend/          # ApiOverview (endpoints, deprecations, rate limits), HostedSdk (convert/swap), RouterStatic, SocketIO
│   ├── Contracts/        # PendleMarket, StandardizedYield, YieldTokenization, UnitAndDecimals, sPENDLE
│   │   ├── Oracle/       # PYLpOracle, ChainlinkOracle, LinearDiscountOracle/{Spark,Lp,Wrapper}
│   │   ├── PendleRouter/ # overview, integration guide, ApiReference/{Pt,Yt,Liquidity,Misc,Simple}Functions, Types
│   │   ├── RouterStatic/ # off-chain quotes (swap/liquidity/rate/info functions)
│   │   └── PendleMarket/, StandardizedYield/, YieldTokenization/, LiquidityMining/
│   ├── Oracles/          # OracleOverview, PTAsCollateral, PTSanityChecks, HowToIntegratePtAndLpOracle, DeterministicOracles/
│   ├── Integration/      # cross-chain PT and oracle, community listing, points
│   └── LimitOrder/       # limit-order contract, create/fill/cancel
└── lib/
    ├── pendle-core-v2-public/   # submodule 87685c89; audits/, whitepapers/ (AMM, PT+YT, SY, LP_Oracle pdf), deployments/<chainId>-core.json
    │   └── contracts/
    │       ├── core/            # Market/ (PendleMarketV7, MarketMathCore, OracleLib), YieldContracts/ (PT, YT), StandardizedYield/ (PYIndex)
    │       ├── oracles/         # PtYtLpOracle/ (TWAP libs, PendlePYLpOracle, chainlink/), internal/ (linear discount), StatelessWrapper/
    │       ├── router/          # PendleRouterV4 + Action*V3 facets, math/ (approx), swap-aggregator/
    │       ├── offchain-helpers/router-static/   # *Static quote functions (priceImpact)
    │       ├── limit/, pt-looping/, cross-chain/, LiquidityMining/, interfaces/
    ├── Pendle-SY-Public/        # submodule 73676d9; 558 .sol files
    │   └── contracts/
    │       ├── core/StandardizedYield/   # SYBase*, v2/, implementations/ (113 per-protocol SY dirs: Ethena, FX, Reservoir, Midas, ...)
    │       └── interfaces/               # per-protocol external interfaces
    └── external-integration/    # submodule 1694fea; protocols/<29 integrators>/config.yaml, merged config.json
```

## Main files

| Path (relative to this README) | What | riskdep use |
|---|---|---|
| `lib/pendle-core-v2-public/contracts/oracles/internal/PendleSparkLinearDiscountOracle.sol` | linear discount to maturity, 43 lines | constant-price class; ROCK §3 PT-fxSAVE/strUSD/trUSD |
| `lib/pendle-core-v2-public/contracts/oracles/PtYtLpOracle/chainlink/PendleChainlinkOracle.sol` | Chainlink-shaped TWAP oracle | price-tracking class (`twapDuration()`); TWAP leg of Ojo PT-reUSD |
| `lib/pendle-core-v2-public/contracts/oracles/PtYtLpOracle/PendlePYOracleLib.sol` | TWAP PT/SY, PT/asset maths | how a pool move and an SY loss reach the price |
| `lib/pendle-core-v2-public/contracts/oracles/PtYtLpOracle/PendlePYLpOracle.sol` | pre-deployed oracle + cardinality check | is a TWAP oracle "ready" |
| `lib/pendle-core-v2-public/contracts/core/Market/MarketMathCore.sol` | AMM curve, fees, implied rate | exit cost / slippage, implied yield |
| `lib/pendle-core-v2-public/contracts/core/Market/PendleMarketV7.sol` | market: swaps, observations, expiry | TWAP storage, post-expiry behaviour |
| `lib/pendle-core-v2-public/contracts/core/YieldContracts/PendleYieldToken.sol` | mint/redeem PY, PY index | redemption at maturity |
| `lib/Pendle-SY-Public/contracts/core/StandardizedYield/SYBaseUpg.sol` | SY base: deposit/redeem/pause | SY redemption risk |
| `docs.pendle.finance-pendle-v2-dev-docs/Oracles/PTAsCollateral.md` | Pendle's risk framework for PT collateral | oracle, liquidity, liquidation sizing |
| `docs.pendle.finance-pendle-v2-dev-docs/Backend/ApiOverview.md` | API endpoints, deprecations, rate limits | `sources.PENDLE` calls |
| `docs.pendle.finance-pendle-v2-dev-docs/Backend/HostedSdk.md` | SDK convert/swap quote | `exit_quote` |
| `lib/external-integration/protocols/morpho/config.yaml` | PTs Pendle lists as Morpho collateral | cross-check RockawayX PT markets |

## Read first for this project

Prefixes: `C/` = `lib/pendle-core-v2-public/contracts/`, `S/` = `lib/Pendle-SY-Public/contracts/core/StandardizedYield/`, `D/` = `docs.pendle.finance-pendle-v2-dev-docs/`.

### PT pricing and oracles

- **Linear discount** `C/oracles/internal/PendleSparkLinearDiscountOracle.sol`: `maturity` and `baseDiscountPerYear` are immutable (:11-12, 100 % = 1e18, capped at 1e18 :15); `answer = 1e18 - timeLeft × baseDiscountPerYear / 365 days` (:28-33, :40-42); returns `updatedAt = 0` (:33) — matches ROCK §3 "`updatedAt` = 0". No market, SY or admin input: a pool crash or an SY loss never moves it. `C/oracles/StatelessWrapper/PendleLinearDiscountOracleWrapper.sol:17-24` only rewrites `updatedAt = block.timestamp` (for consumers with a staleness check). Audit: `lib/pendle-core-v2-public/audits/LinearDiscountOracle/WatchPug-SparkLinearDiscountOracle.pdf`.
- **Docs on linear**: `D/Oracles/OracleOverview.md:14` — Pendle now *recommends* the linear oracle for money markets (Gauntlet, Steakhouse use it). `D/Oracles/DeterministicOracles/LinearDiscountOracle.md:30` full formula `discount / PYIndex × yield-token USD`; :49 simplified `discount × accounting-asset USD` (ignores yield-token depeg). `D/Oracles/DeterministicOracles/ChoosingLinearDiscountParams.md:23-24` example: 18 % PT, 7 % LP (USDe Sep 2025).
- **TWAP library** `C/oracles/PtYtLpOracle/PendlePYOracleLib.sol`: `getPtToAssetRate` scales down by `syIndex/pyIndex` when the SY's exchange rate falls below the stored PY index (:20-27, SY insolvency); `getPtToAssetRateRaw` returns exactly 1.0 once `expiry <= block.timestamp` (:65-70), else `1 / exp(lnImpliedRate × t / 365d)` (:71-74); TWAP = `(cum[now] - cum[now-duration]) / duration` (:96-107); `duration = 0` reads the spot `lnImpliedRate` (:97-99).
- **PendleChainlinkOracle** `C/oracles/PtYtLpOracle/chainlink/PendleChainlinkOracle.sol`: immutable `market`, `twapDuration` (:18-19), oracle type PT_TO_SY / PT_TO_ASSET / LP_* (:113-123); `updatedAt = block.timestamp`, `roundId = 0` (:58-69) — never looks stale. Docs: `D/Contracts/Oracle/ChainlinkOracle.md`.
- **PendlePYLpOracle, cardinality** `C/oracles/PtYtLpOracle/PendlePYLpOracle.sol`: Ethereum `blockCycleNumerator = 11000` (:24); `cardinalityRequired = ceil(duration × 1000 / 11000) + 1` (:106-113); `getOracleState` flags too-small cardinality and missing history (:85-104). `D/Oracles/HowToIntegratePtAndLpOracle.md:55` recommends 900 s or 1800 s; :71-76 Ethereum cardinality 85 (900 s) / 165 (1800 s); new oracle needs `duration` seconds of history (:84). Registry sees 900 s on PT-reUSD.
- **TWAP storage** `C/core/Market/PendleMarketV7.sol:62` `observations[65_535]`; `observe` :274, `increaseObservationsCardinalityNext` :284. `D/Oracles/PTAsCollateral.md:65`: TWAP window ≤ 65,536 blocks (~9 days on Ethereum).
- **Sanity check** `D/Oracles/PTSanityChecks.md:23`: oracle vs UI price gap > 0.2 % means something is wrong.

### Market AMM, exit cost and slippage

- `C/core/Market/MarketMathCore.sol`: `IMPLIED_RATE_TIME = 365 days` (:44); trades revert past 96 % PT in the pool, `MAX_MARKET_PROPORTION` (:46, :337-339) — a hard ceiling on how much PT can be sold; `rateScalar = scalarRoot × 365d / timeToExpiry` (:356-359), so the curve stiffens and price impact per unit falls as maturity nears; exchange rate `ln(p/(1-p)) / rateScalar + rateAnchor`, must stay ≥ 1 (:326-345); fee from `lnFeeRateRoot` scaled by time to expiry (:223), split to reserve by `reserveFeePercent` (:246); `MarketExpired` revert on any trade after expiry (:210).
- `C/core/Market/PendleMarketV7.sol:305-310`: the factory can override the fee per router (`overriddenFee`), so the fee is governance-set, not fixed.
- `D/Contracts/PendleMarket.md:35-40` parameters (expiry, scalarRoot, initialAnchor, fee rate root); whitepaper `lib/pendle-core-v2-public/whitepapers/AMM.pdf`.
- `D/Oracles/PTAsCollateral.md:67-118` liquidation-liquidity study: liquidators must sell `dCap × cRatio × k × f × (1+p)` of PT with < `p` impact (example: $1M PT-stETH at 2.5 % impact); cascade note (`k = 1` strictest). Closest Pendle-side model of riskdep's exit-cost / liquidation logic.
- On-chain quote without the API: `C/offchain-helpers/router-static/base/ActionMarketCoreStatic.sol:343` `swapExactPtForTokenStatic` (returns `priceImpact`); docs `D/Contracts/RouterStatic/RouterStaticOverview.md`.

### SY wrappers and redemption risk

- `S/SYBaseUpg.sol`: `redeem` checks `isValidTokenOut` and `minTokenOut` (:67-84); `pause()` by owner (:170-171) and `_beforeTokenTransfer ... whenNotPaused` (:178) — **a paused SY blocks every SY transfer**, hence swaps and PT redemption. Same in `S/SYBase.sol:168-176` and `S/v2/SYBaseUpgV2.sol:165-173`.
- `S/implementations/PendleERC4626NoRedeemUpgSY.sol:31-42`: "NoRedeem" SYs hand out the vault share only (`exchangeRate = convertToAssets(1e18)`); exiting to the asset then depends on the issuer's own queue.
- `S/implementations/FX/PendleFXSaveSY.sol` (PT-fxSAVE): redeem to USDC/fxUSD goes through `instantRedeem` and reverts `"FXSave: insufficient asset"` (:51-75, :66).
- `S/implementations/Reservoir/PendleReservoirUSDSY.sol:59-61`: `exchangeRate()` hard-coded to 1.0 — an issuer loss never reaches PY index or oracles.
- `D/Contracts/StandardizedYield.md:43` PT converges to `1 / exchangeRate`; :82-88 mint/redeem quirks (caps, minimums, no direct unstake); :134 `previewRedeem` is best-effort.

### Expiry and redemption at maturity

- `C/core/YieldContracts/PendleYieldToken.sol`: `_pyIndexCurrent = max(SY.exchangeRate, stored)` (:403-413) — the index never falls, so SY losses after the max are not shown in the PY index (the reason for the `syIndex < pyIndex` branch in the oracle lib); post-expiry index frozen at `firstPYIndex` (:379-392, :399); PT redeems to `assetToSy(index, amountPY)` SY, post-expiry yield goes to treasury (:353-363, :323-346).
- `D/Contracts/YieldTokenization.md:82-83`: pre-expiry PT+YT needed, post-expiry PT alone. After expiry the market stops trading (`MarketMathCore.sol:210`) and the TWAP oracle returns 1.0 (`PendlePYOracleLib.sol:68-69`), the linear oracle 1.0 (discount 0): the position becomes the SY's underlying.

### Router

- `C/router/ActionSwapPTV3.sol:55` `swapExactPtForToken`; `C/router/ActionMiscV3.sol:44` `redeemPyToToken`, :205 `exitPreExpToToken`, :286 `exitPostExpToToken` (liquidator / holder exit paths). Docs `D/Contracts/PendleRouter/ApiReference/MiscFunctions.md:289`, :348, `D/Contracts/PendleRouter/ApiReference/PtFunctions.md`; limit orders can fill part of a swap (`D/LimitOrder/Overview.md`).

### Backend API used by `sources.py` (`PENDLE = https://api-v2.pendle.finance/core`)

| riskdep call | Doc status |
|---|---|
| `GET /v1/1/markets/{active,inactive}` (`discover.py`, `siblings.py`) | **not documented** in this copy; `D/Backend/ApiOverview.md:60-64` points to `GET /v2/markets/all` (paginated) |
| `GET /v2/1/markets/{m}/data` (`_build_pt_layers`) | **deprecated**, `D/Backend/ApiOverview.md:93`, :99 |
| `GET /v2/sdk/1/markets/{m}/swap` (`exit_quote`) | replaced by Convert, `D/Backend/HostedSdk.md:356-360`; GET convert itself deprecated for `POST /v3/sdk/{chainId}/convert` (`ApiOverview.md:94`, :100) |
| `enableAggregator=true` | each aggregator adds CU: kyberswap 1, okx 1, paraswap 15, base 5 (`HostedSdk.md:320-326`) |
| rate limit | 200 CU/min and 200,000 CU/week per IP (`ApiOverview.md:117`); handle 429 (:154) |

## Gaps

- Not in these sources: `OjoPTFeed` (min(TWAP, linear), 24 h staleness), `MetaOracleDeviationTimelock`, `LossAdjustedPTFeed`, `ChainlinkCurrentTimestampAdapter` — third-party wrappers; read their verified source on Etherscan.
- No SY for reUSD (Re), strUSD or trUSD (Tori) in `Pendle-SY-Public` at `73676d9` (only fxSAVE, Reservoir rUSD/wsrUSD); their redemption path must come from the deployed SY's verified source.
- riskdep's three Pendle API calls are undocumented or deprecated (table above); expect breakage and plan a move to `/v2/markets/all` and `POST /v3/sdk/1/convert`.
- No market addresses or per-market `scalarRoot`/fee here; `lib/pendle-core-v2-public/deployments/1-core.json` gives factories and router only.
- Docs are a dated scrape with no commit pin; `ChoosingLinearDiscountParams.md` relies on an external Desmos sheet and Colab notebook.
