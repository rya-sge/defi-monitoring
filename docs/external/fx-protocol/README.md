# f(x) Protocol — external references

This folder holds the f(x) Protocol (AladdinDAO) sources behind the fxSAVE and PT-fxSAVE collateral of the RockawayX f(x) Protocol Ecosystem vault. It has two parts:

- `fxprotocol.gitbook.io-fx-docs-docs/` is a Markdown export of <https://fxprotocol.gitbook.io/fx-docs>. It is **git-ignored** and exists only in the local checkout.
- `fx-protocol-contracts/` is a **git submodule** of <https://github.com/AladdinDAO/fx-protocol-contracts> (f(x) v2), pinned at `5e198e9`. After a clone, run `git submodule update --init`.

Contract citations below are `file:line` at that pin.

## Why it matters to riskdep

| Exposure | Size | What decides the loss |
|---|---|---|
| fxSAVE collateral, 91.5 % LLTV | ~$20M USDC | The Morpho oracle reads an on-chain NAV, not a market price. NAV = fxSP NAV × fxSAVE share rate, and fxUSD is marked at its Curve EMA. A fxUSD depeg, a USDC depeg or an Aave loss in the pool lowers the NAV. A DEX dump does not. |
| PT-fxSAVE-29OCT2026 | ~$1M | Priced by time alone (linear discount). At expiry the PT becomes fxSAVE. |
| Exit | – | Redeeming is a two-step cooldown and pays out in fxUSD **and** USDC. The instant route pays a fee. DEX depth is thin: a $1M sale loses about 27 %. |
| Admin | – | The ProxyAdmin `0x9B54…` sits behind a 3-day timelock. Role holders can change the cooldown, the fee and the oracle source; oracle changes bypass the timelock. |

## Tree

```
fx-protocol/
  fxprotocol.gitbook.io-fx-docs-docs/   gitbook export (git-ignored)
    f-x-protocol-mechanisms/            stability pool, rebalancing/liquidation brake, fees, invariant
    risk-management/                    risk framework, peg protection, risk parameters, oracle/{steth,wbtc,eth}
    faq/                                "what could go wrong", "LUNA-like risk", peg FAQ
    developers/                         integrating fxSAVE, keeper bots, long/short pool integration
    guides/                             stake/unstake stability pool (cooldown, "Fast" exit)
    more/resources/                     contracts, multisig + timelock
    ~/revisions/                        an older snapshot of the same pages; ignore it unless you are diffing
  fx-protocol-contracts/                AladdinDAO/fx-protocol-contracts @ 5e198e9 (submodule)
    contracts/
      core/                             FxUSDBasePool (fxSP), SavingFxUSD (fxSAVE), PegKeeper, FxUSDPriceOracle,
                                        PoolManager, ReservePool, FxUSDRegeneracy (fxUSD token), ProtocolFees
      core/pool/                        long pools: BasePool (ticks, liquidation, bad-debt redistribution), AaveFundingPool
      core/short/                       short pools, CreditNote
      fund/strategy/                    AaveV3Strategy: the pool's USDC lent to Aave
      price-oracle/                     collateral oracles (stETH, WBTC, spot/anchor bases)
      periphery/facets/                 router diamond facets (SavingFxUSDFacet = instant fxSAVE exit)
      common/concentrator/              ConcentratorBase (fxSAVE harvest fees)
      interfaces/                       ISavingFxUSD, IFxUSDBasePool, IPegKeeper, IFxUSDPriceOracle
    ignition/deployments/               mainnet deployed addresses per upgrade
    ignition/parameters/                deployment parameters (initial cooldown, depeg price, LTVs)
    test/, simulation/                  hardhat/foundry tests, simulations
```

## Main files

| Path | What | riskdep use |
|---|---|---|
| `fx-protocol-contracts/contracts/core/SavingFxUSD.sol` | fxSAVE, an ERC-4626 over fxSP staked in a Convex/FXN gauge | Share rate, `nav()`, two-step redeem |
| `fx-protocol-contracts/contracts/core/FxUSDBasePool.sol` | fxSP, the stability pool holding fxUSD and USDC | NAV formula, cooldown, instant fee, depeg guard, rebalance/liquidate, peg arbitrage |
| `fx-protocol-contracts/contracts/core/FxUSDPriceOracle.sol` | fxUSD price = Curve EMA × Chainlink USDC/USD | The price that marks fxSAVE's NAV |
| `fx-protocol-contracts/contracts/core/PegKeeper.sol` | Buyback and stabilize, 0.995 threshold | Peg-defence triggers |
| `fx-protocol-contracts/contracts/core/PoolManager.sol` | Long pool manager: rebalance, liquidate, redeem, pause | Loss path, emergency pause |
| `fx-protocol-contracts/contracts/core/pool/BasePool.sol` | Tick liquidation, bad-debt redistribution | What happens past the liquidation line |
| `fx-protocol-contracts/contracts/core/ReservePool.sol` | Reserve fund that pays liquidation bonuses and shortfalls | First loss buffer |
| `fx-protocol-contracts/contracts/fund/strategy/AaveV3Strategy.sol` | USDC lent to Aave | Aave dependency inside the NAV |
| `fx-protocol-contracts/ignition/deployments/ethereum/deployed_addresses.json`, `…/upgrade-20250318/…`, `…/upgrade-20251031/…` | Mainnet addresses | Address registry |
| `fxprotocol.gitbook.io-fx-docs-docs/risk-management/risk-parameters.md` | Every governed parameter | LTV lines, bounties, cooldown, depeg thresholds |
| `fxprotocol.gitbook.io-fx-docs-docs/risk-management/risk-framework.md` | Loss waterfall | Order of loss absorption |
| `fxprotocol.gitbook.io-fx-docs-docs/more/resources/multisig.md` | Multisigs, timelock | Admin surface |

## Read first for this project

### fxUSD peg & stability pool
- `fxprotocol.gitbook.io-fx-docs-docs/f-x-protocol-mechanisms/stability-pool.md` says depositors put in fxUSD or USDC. Below peg the pool "swaps USDC for fxUSD", and on a USDC depeg it "halts peg maintenance and temporarily disables deposits".
- `fxprotocol.gitbook.io-fx-docs-docs/risk-management/advanced-peg-protection-mechanisms.md` lists five layers:
  - minting and redemptions;
  - stability-pool arbitrage;
  - Funding I, which starts when USDC in the pool falls below 5 %;
  - Funding II (10× the Aave USDC rate, minting stopped), which starts when the Curve EMA falls below $0.998 and the pool's USDC is exhausted;
  - redemption for $1 of wstETH/WBTC with a 0.5 % fee, which gives "a hard floor … at $0.995".
- `FxUSDBasePool.sol:461-513` holds `arbitrage`, callable only by the PegKeeper. Selling fxUSD for USDC reverts if USDC < `stableDepegPrice` (`:476`). The swap must return at least the oracle-priced amount (`:503`). So during a depeg the pool buys fxUSD and becomes more concentrated in it.
- `PegKeeper.sol:105`: `priceThreshold` = 0.995. `:115-127`: borrowing is allowed at EMA ≥ 0.995; funding and redemption are enabled below it.

### fxSAVE share price / NAV
- `SavingFxUSD.sol:154-156`: `totalAssets` = fxSP held + gauge balance of the Convex vault.
- `SavingFxUSD.sol:164-166`: `nav() = FxUSDBasePool.nav() × convertToAssets(1e18) / 1e18`.
- `FxUSDBasePool.sol:255-264`: `nav = (totalYieldToken × fxUSDPrice + totalStable × USDCPrice) / supply`. fxUSD is valued at `FxUSDPriceOracle.getPrice()`, not at $1.
- `FxUSDPriceOracle.sol:130-140`: the price is the Curve StableSwap-NG `price_oracle(0)` (EMA) × Chainlink USDC/USD. `:166-180`: the Chainlink read reverts on a negative answer or on a stale one (`heartbeat`), so the NAV call can revert.
- `FxUSDBasePool.sol:682-690`: the stable balance includes `IStrategy.totalSupply()`, the USDC lent to Aave. Docs: up to 80 % goes to Aave (`risk-parameters.md`).
- fxSAVE harvests and compounds wstETH/WBTC/FXN rewards (`SavingFxUSD.sol:214-228`). Its fees apply to rewards only: expense ratio ≤ 50 %, harvester ≤ 10 % (`common/concentrator/ConcentratorBase.sol:42,45`).

### Redemption cooldown & instant fee
- `SavingFxUSD.sol:190-201,327-346`: `requestRedeem` burns fxSAVE at once and moves the fxSP to a per-user `LockedFxSaveProxy` (`:25-49`), which calls `FxUSDBasePool.requestRedeem`. `claim` (`:204-211,349-354`) runs after the cooldown.
- `FxUSDBasePool.sol:301-311`: `unlockAt = now + redeemCoolDownPeriod`. Each new request **restarts the timer for the whole pending amount**. Locked shares cannot be transferred (`:540-548`).
- `FxUSDBasePool.sol:314-351`: `redeem` pays a **pro-rata mix of fxUSD and USDC** worked out at claim time, so the locked fxSP still bears losses during the cooldown.
- `FxUSDBasePool.sol:354-392`: `instantRedeem` charges `instantRedeemFeeRatio` on both legs. `:80`: the cap is `MAX_INSTANT_REDEEM_FEE = 5e16` (5 %). `:395`: `NO_INSTANT_REDEEM_FEE_ROLE` exits without the fee.
- `FxUSDBasePool.sol:562`: the cooldown can be at most `7 days`.
- What each source says about the cooldown:
  - docs: "Stablity Pool redemption Period 60 minutes" (`risk-parameters.md`); "Stability Pool early exit fee 1%" (`fees.md`);
  - initial deploy: `RedeemCoolDownPeriod: 1800` s (`ignition/parameters/ethereum.json:22`).
- Instant fxSAVE exit through the router: `SavingFxUSDFacet.sol:96` `instantRedeemFromFxSave` (`developers/integrating-fxsave.md`; the router is `0x3363…C708`). Enso routes only this fee-paying path.

### Rebalancing / liquidation brake and losses to the stability pool
- `risk-parameters.md`:
  - rebalance at LTV 88 % (bounty 2.5 %);
  - liquidation at LTV 95 % (bounty 4 %);
  - leverage 1.1–7×;
  - a redemption takes at most 20 % per xPOSITION;
  - USDC deposits stop at oracle ≤ 0.995;
  - collateral lent to shorts: cap 50 %.
- `FxUSDBasePool.sol:405-458,614-680`: on a rebalance or liquidation, the pool's fxUSD (then USDC) repays debt, the **keeper** takes the collateral and repays the pool `amountUSD` at par in fxUSD or USDC (`:653-680`). The pool never holds wstETH/WBTC, so a collateral price gap falls on the keeper, not on fxSP.
- `PoolManager.sol:222-229`: only fxSP can rebalance or liquidate while fxSP supply ≥ `permissionedLiquidationThreshold`. Below it (docs: $10,000) keepers use their own funds.
- `PoolManager.sol:523-569`: liquidation bonus or shortfall is taken from the `ReservePool` (`ReservePool.sol:71`).
- `pool/BasePool.sol:640-646`: if collateral runs out before the debt, the remainder is **redistributed** to all positions via `debtIndex`.
- Docs waterfall (`risk-framework.md`, `faq/what-could-go-wrong.md`):
  1. rebalance;
  2. liquidation;
  3. Reserve Fund;
  4. bad debt shared across xPOSITIONs (and from sPOSITIONs to xPOSITIONs);
  5. recapitalisation: "If the total collateralization ratio drops below 100%, the protocol halts new xPOSITION openings".
- `faq/is-there-any-luna-like-risk.md`: "No … backed exclusively by tier-1 exogenous DeFi assets". The docs give no stability-pool loss case.
- **riskdep reading of how fxSAVE loses value:**
  - (a) the fxUSD Curve EMA falls (backing gap or sell pressure); NAV falls by fxUSD share × depeg;
  - (b) USDC/USD falls;
  - (c) loss or illiquidity at Aave on the lent USDC;
  - (d) collateral gaps faster than keepers act, then reserve and redistribution exhausted, then fxUSD under-backed, which leads to (a);
  - (e) an upgrade or role change.

### Oracles used by f(x) itself
- fxUSD/USD: `FxUSDPriceOracle.sol:89-92`, `isPegged` within `maxDePeg`/`maxUpPeg` deviations (settable, `:117`). The Curve pool can be changed by the admin (`:110`).
- USDC/USD: Chainlink, with a heartbeat packed into the immutable `Chainlink_USDC_USD_Spot` (`FxUSDPriceOracle.sol:40,166-180`).
- Collateral (`risk-management/oracle/steth.md`, `wbtc.md`):
  - a spot price (Chainlink, Uniswap V3, Curve, Balancer) and an anchor (Curve EMA × Chainlink);
  - the anchor is used when spot deviates by more than 1 % (stETH) or 2 % (WBTC);
  - the minimum price is used for xPOSITION rebalance and liquidation;
  - code: `contracts/price-oracle/StETHPriceOracle.sol`, `WBTCPriceOracle.sol`, `LSDPriceOracleBase.sol`, `SpotPriceOracleBase.sol`.

### Fees
- `f-x-protocol-mechanisms/fees.md`:
  - open 0.3 % / close 0.1 % (xPOSITION and sPOSITION);
  - fxMINT 0.5 % / 0.2 %;
  - rebalance/liquidation: 10 % of the bounty;
  - harvest bounty 1 % (0.01 % for fxSAVE);
  - **stability-pool early exit 1 %**;
  - funding I/II/III tied to the Aave USDC rate (×10 for II and III).
- "All adjustable by governance."

### Admin, roles, upgradeability
- `more/resources/multisig.md`:
  - operational Safe `0x26B2…BbF`, 6 signatures;
  - Timelock `0x6886…E61a`: "mandatory 3-day public timelock"; **exception: "oracle source updates" bypass it**;
  - emergency Safe `0x28c9…eF62`, 3 signatures, can only pause LongPoolManager and ShortPoolManager.
- `PoolManager.sol:761`: `setPause` (`EMERGENCY_ROLE`, `:74`). `:743-748`: `reduceDebt` (`DEBT_REDUCER_ROLE`).
- `FxUSDBasePool` `DEFAULT_ADMIN_ROLE` can change, with no on-chain delay unless the role holder is the timelock:
  - the depeg price (`:521`);
  - the cooldown (`:527`, ≤ 7 days);
  - the instant fee (`:531`, ≤ 5 %).
- `SavingFxUSD.sol:209`: `claimFor` (`CLAIM_FOR_ROLE`) can claim a user's unlocked redemption; `:236`: admin sets the gauge batch threshold.
- `ReservePool.sol:91`: `withdrawFund` (admin).
- Proxies: ProxyAdmin `FxProxyAdmin` `0x9B54B7703551D9d0ced177A78367560a8B2eDDA4` and `CustomProxyAdmin` `0xd41d…324B` (`ignition/deployments/ethereum/deployed_addresses.json`). Upgrade history is in `ignition/deployments/upgrade-*` (latest 20260217).

### Contract addresses (Ethereum)

| Contract | Address | Source |
|---|---|---|
| fxSAVE (SavingFxUSD proxy) | `0x7743e50F534a7f9F1791DdE7dCD89F7783Eefc39` | `ignition/deployments/upgrade-20250318/deployed_addresses.json` |
| fxSP (FxUSDBasePool proxy) | `0x65C9A641afCEB9C0E6034e558A319488FA0FA3be` | `…/ethereum/deployed_addresses.json` |
| fxUSD (FxUSDRegeneracy) | `0x085780639CC2cACd35E474e71f4d000e2405d8f6` | same |
| PegKeeper | `0x50562fe7e870420F5AAe480B7F94EB4ace2fcd70` | same |
| PoolManager (long) | `0x250893CA4Ba5d05626C785e8da758026928FCD24` | same |
| ReservePool | `0x297dD69725911FE5F08B8F8C5EDdDb724D7D11df` | same |
| wstETH long pool / WBTC long pool | `0x6Ecfa38F…22E8` / `0xAB709e26…2473` | same / upgrade-20250318 |
| AaveV3StrategyUSDC | `0x376aa9086060740f444c4E7A5411ff235816Aa0C` | upgrade-20250318 |
| fxSP gauge (V2) | `0x215D87bd3c7482E2348338815E059DE07Daf798A` | upgrade-20250318 |
| Router diamond | `0x33636D49FbefBE798e15e7F356E8DBef543CC708` | same |
| ProxyAdmin | `0x9B54B7703551D9d0ced177A78367560a8B2eDDA4` | all |
| Timelock | `0x68863fb8855b04509a835082478D6E3D0bE4E61a` | `fxprotocol.gitbook.io-fx-docs-docs/more/resources/multisig.md` |

## Gaps

- **`NetAssetValueChainlinkAdapter` (the Morpho oracle `0x9dd6…5827`) is not in this repository.** It probably reads `SavingFxUSD.nav()`, but that is unconfirmed: get its verified source from Etherscan.
- **Live parameters are not in the sources.** Docs say 60 min cooldown and 1 % fee; the deploy set 1800 s; the code allows up to 7 days and 5 %. Read these on-chain:
  - `redeemCoolDownPeriod()`, `instantRedeemFeeRatio()` and `stableDepegPrice()` on `0x65C9…`;
  - `priceThreshold()` on `0x50562…`;
  - the deviations on FxUSDPriceOracle.
- **Unknown addresses.** The FxUSDPriceOracle proxy address and its `curvePool` (fxUSD/USDC) do not appear in the `deployed_addresses.json` files read, so the depth of the pool that sets the NAV is not documented here.
- **Role holders.** Who holds `DEFAULT_ADMIN_ROLE` on fxSP and fxSAVE (timelock or Safe) is not stated; check `getRoleMember`/events. Docs say only that the ProxyAdmin goes through the 3-day timelock.
- **No quantified stability-pool loss model** in the docs, and the "LUNA" FAQ is a one-line denial. The loss paths above are inferred from the code.
- **`docs/analysis/ROCK-VAULT.md` labels `0x65c9a641…` as "underlying fxUSD".** That address is fxSP (FxUSDBasePool); fxUSD is `0x0857…d8f6`.
- **The docs export is partly stale** ("Last updated 1 year ago" on several pages; `~/revisions/` is older still). The code pin wins.
