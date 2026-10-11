# RockawayX vaults: full dependency map

Follow-up to `ROCK-VAULT.md`. That file listed the vaults, their markets, the collateral issuers and the first feed of each oracle. It did **not** list every external dependency. This file adds the layers it missed, read on-chain on 2026-10-11. It covers the 8 Morpho vaults; §9 covers the other 25. §10 lists what I need from you to go further.

How it was read:
- the Morpho API (`vaultV2ByAddress`: roles, timelocks, gates, adapters; `marketPositions`);
- `eth_call` and `eth_getStorageAt` on publicnode: EIP-1967 slots, `owner()`, Safe `getThreshold()`/`getOwners()`, `latestRoundData()`, `FEED_1/2()`, `getMinDelay()`;
- Etherscan `getsourcecode` (contract names) and `getLogs` (`RoleGranted`/`RoleRevoked`);
- the Pendle API (`/v1/1/markets/active`);
- KyberSwap quotes, keyless;
- `riskdep graph --vault 0xD6d4…48Ec --replay`.

## 1. What ROCK-VAULT.md had, and what it missed

| Layer | In ROCK-VAULT.md | Missing, added here |
|---|---|---|
| Vault governance | curator address only | Safe threshold, allocators, sentinel, gates, timelock per function, force-deallocate penalty (§2) |
| Oracle wrapper | first feed name | every feed's contract, operator, admin, upgradeability, update age, and how the PT feeds work (§3) |
| Token contracts | issuer name | proxy type, implementation, upgrade admin and its delay, mint and pause roles (§4) |
| Bridges | "PST probably bridged" | PST: Chainlink CCIP. etrUSD: LayerZero V2. Hastra: native Ethereum vaults over off-chain flows (§5) |
| Market structure | utilisation | borrower concentration; who the main borrowers are (§6) |
| Exit liquidity | – | Pendle pool depth and expiries; DEX depth per collateral (§7) |
| Vault-on-vault | – | etrUSD is the Upshift vault's share; a looping vault (glPRIME) borrows PRIME; nvPRIME wraps PRIME (§8) |
| Non-Morpho vaults | named only | dependency list and what is needed (§9) |

Corrections to `ROCK-VAULT.md` §4:
- **The PT oracles are not market-priced.** PT-fxSAVE, PT-strUSD and PT-trUSD use `PendleSparkLinearDiscountOracle`, which prices by time alone. PT-reUSD uses Ojo, which takes the lower of a Pendle TWAP and a time-based feed.
- **fxSAVE's oracle computes NAV on-chain**, from the f(x) pool's accounting. No issuer publishes it.

## 2. Vault governance (all 8 vaults)

| Role | Address | What it is |
|---|---|---|
| Owner and curator (same address, all 8 vaults) | `0xbBacDCFB…f918` | Safe, **4 of 8** |
| Allocators | `0x1CDa…ba02`, `0xBDa6…f9e5`, `0xDF75…334b`, `0xac85…3A49`, `0xdd25…01a8` | **EOAs** (hot keys) |
| Allocator | `0x22D4…676A` | Safe, **1 of 1** |
| Sentinel (Ethereum) | `0x040E…3A47` | Safe, 1 of 4 |
| Sentinel (Base) | `0x8003…2E5f` | not probed |
| Deposit gate, Confidential RWA USDC only | `0x51f6…D525` | `WhitelistSendAssetsGate` (KYC whitelist on deposits; explains its 6 holders) |

Timelocks (days; 0 = immediate; **abd.** = abdicated, the function can never be called again). The gate columns were re-read on-chain with `abdicated(bytes4)` and `timelock(bytes4)` on 2026-10-11; a first reading of the Morpho API's durations missed the abdications and wrongly reported the exit gates as open with no delay.

| Vault | addAdapter | increase caps | **setSendSharesGate / setReceiveAssetsGate** (exit) | setReceiveSharesGate | setSendAssetsGate (deposit) | setIsAllocator | setAdapterRegistry | performance fee |
|---|---|---|---|---|---|---|---|---|
| Confidential RWA USDC | 3 | 3 | **abd.** | abd. | 7 | 0 | abd. | 3 |
| f(x) Ecosystem | 3 | 3 | **abd.** | abd. | abd. | 0 | abd. | 0 |
| USDC Yield | 3 | 3 | **abd.** | abd. | abd. | 0 | abd. | 3 |
| Tori Ecosystem | 3 | 3 | **abd.** | abd. | abd. | 0 | abd. | 3 |
| Huma USDC Main | 3 | 3 | **abd.** | abd. | 0 | 0 | abd. | 3 |
| Belem RWA EURCV | 3 | 3 | **abd.** | abd. | abd. | 0 | abd. | 0 |
| NUVA Ecosystem | 3 | 3 | **abd.** | abd. | abd. | 0 | abd. | 0 |
| Midas USDC Prime (Base) | 7 | 7 | **abd.** | abd. | abd. | 0 (API) | 0 (API) | 0 |

What this means for a depositor:
- **No curator decision can lock depositors in.** In `VaultV2.sol` the `sendSharesGate` and `receiveAssetsGate` "can lock users out of exiting the vault", but on all 8 vaults both setters are abdicated: those gates stay at zero for good. What can stop an exit is liquidity (86–91 % utilisation), not governance. On a fork, the attempt reverts with `Abdicated` (`docs/analysis/FORK-PRESENTATION.md`, act 5).
- **Deposits can still be gated on two vaults:** Confidential (7 days, where the KYC whitelist already sits) and Huma USDC Main (0 days). That cannot block funds already in.
- `decreaseTimelock` takes the timelock of the function it targets (`submit`, line 314), so the 3-day timelocks on caps and adapters are real.
- An allocator can only move funds within the caps, but five of them are hot EOAs.
- The force-deallocate penalty is 1 % (Confidential, f(x), Tori, NUVA), 0.5 % (Yield, Huma) or 0 (Belem, Base). It is the price of forcing liquidity out of a market.

`riskdep watch` now states the exit-gate position at startup (`ExitGate`, D184): a warn when an exit gate can be set with no notice, an info when both are abdicated, as on these 8 vaults.

## 3. Oracle layer: every feed, its operator and its admin

Morpho's `MorphoChainlinkOracleV2` has no staleness check and no admin, so each feed below passes through as is.

| Market | Feed contract | Type | Operator / admin | Last update | Reads |
|---|---|---|---|---|---|
| PST | `0x4be5…65e6` `EACAggregatorProxy` "PST-USDC Exchange Rate (Calculated)" | Chainlink exchange-rate feed | Chainlink, owner 4/9 multisig `0x21f7…73ca` | 0.5 h | 1.138 USDC; no USDC/USD quote |
| AUTO | `0x0a19…67cb` `EACAggregatorProxy` "Hastra Auto / WYLDS Exchange Rate" ÷ `0x8fff…18f6` USDC/USD | Chainlink | Chainlink 4/9 | 6.5 h | 1.0238 |
| PRIME, nvPRIME | `0xf17c…58d1` `EACAggregatorProxy` "PRIME / WYLDS Exchange Rate" ÷ USDC/USD (nvPRIME also × the `NuvaVault` rate) | Chainlink; the value comes from Hastra's `NAV_ORACLE_UPDATER_ROLE` | Chainlink 4/9 | 17.8 h | 1.0638 |
| fxSAVE | `0x9dd6…5827` `NetAssetValueChainlinkAdapter` "Net Asset Value in USD" | computed on-chain from fxSAVE's accounting (`updatedAt` = 0) | no admin seen | live | 1.1228 |
| strUSD | `0x7fda…0caa` → impl `EthereumPriceFeedStrusdFundamentalWithoutRoundsV1` | RedStone "fundamental" (issuer data), **upgradeable** | ProxyAdmin `0x8223…` owned by a **2-of-3 Safe** `0x6906…4472` | 2.0 h | 1.0298 |
| etrUSD | `0x835c…d659` → `EthereumPriceFeedEtrusdFundamentalusdWithoutRoundsV1` | RedStone fundamental, upgradeable | same 2-of-3 Safe | 2.0 h | 1.0146 |
| PT-strUSD, PT-trUSD (2nd feed) | `0x33c6…3b53` → `EthereumPriceFeedTrusdFundamentalWithoutRoundsV1` | RedStone fundamental, upgradeable | same 2-of-3 Safe | 8.0 h | **exactly 1.00000000**: trUSD is held at $1 |
| PT-fxSAVE, PT-strUSD, PT-trUSD | `0x9105…`, `0xcb8c…`, `0x7180…` `PendleSparkLinearDiscountOracle` | **linear discount: time only**; a crash in the PT pool never moves it | immutable | n/a (`updatedAt` = 0) | 0.993 / 0.970 / 0.972 |
| PT-reUSD | `0x77ee…5d89` `OjoPTFeed`, a minimal-proxy clone | **min(**`PendleChainlinkOracle` TWAP `0x570e…e7f6`, `ChainlinkCurrentTimestampAdapter` `0x7cfd…c994`**)**, 24 h staleness revert | Ojo; implementation `0x5aab…8585` (initialisable) | live | 0.9818 (the TWAP side is lower now) |
| siUSD | `0xf81a…7067` `ChainlinkRTOracle` "InfiniFi RT Oracle" × `BASE_VAULT` siUSD ÷ `0xc386…973d` `DummyFeed` | infiniFi's own oracle: an admin-set `FixedPriceOracle` value, **1.0** today; the quote is a dummy 1.0. Losses hit the safety buffer, then liUSD, then siUSD (its vault rate falls) before iUSD moves (`YieldSharingV3.sol:343-376`, see `docs/external/infini-protocol/README.md`) | infiniFi admin | live | iUSD held at $1, siUSD at its vault rate |
| mGLOeuro | `0x8b7b…9609` → impl `MGloEuroCustomAggregatorFeed` | Midas, **the issuer's admin publishes the NAV by transaction** | ProxyAdmin owned by `MidasTimelockController` (48 h); values written under `MidasAccessControl` | **419.8 h (17.5 days)** | 100,000 EUR; only 2 rounds since August (graph probe) |
| WBTC, cbBTC, wstETH, ETH, EUR/USD | Chainlink market feeds | price-tracking | Chainlink | normal | already modelled |

Consequences:
- **About $45M of the book has no market-price trigger at all:** PST, fxSAVE, PRIME, AUTO, nvPRIME, siUSD and mGLOeuro, plus PT-fxSAVE, PT-strUSD and PT-trUSD, which are priced by time alone. Liquidations start only if the issuer marks its value down, or if the time-based price passes the loan-to-value limit.
- **A 2-of-3 Safe (RedStone) can rewrite the strUSD, etrUSD and trUSD prices**, about $20M of collateral, by upgrading the feed with no timelock seen.
- **mGLOeuro has not been updated for 17.5 days and shows a flat value.** Belem's $4.5M rests on one administered value.
- **Feeds assume the loan token is worth exactly $1** in the PST, fxSAVE, siUSD and PT-reUSD markets: they carry no USDC/USD quote. The siUSD market uses a dummy feed fixed at 1.0. The Belem markets read EURCV through EUR/USD, so EURCV is assumed to equal 1 EUR.

## 4. Token contracts: who can upgrade, mint, pause

| Token | Contract | Upgrade path | Other powers |
|---|---|---|---|
| PST (Ethereum) | `BurnMintERC20` (Chainlink cross-chain token) | not a proxy | DEFAULT_ADMIN: Safe **4/5** `0x8c24…15eb`. **Minters/burners: two CCIP `BurnMintTokenPool`s** (`0xbe77…`, `0xfd34…`) owned by an `RBACTimelock` with a **3 h** delay (`0x4483…9449`, also the CCIP admin) |
| wYLDS, PRIME, AUTO (Hastra) | ERC-1967 → `YieldVaultV2` / `StakingVault` / `AutoStakingVault` | UPGRADER: `HastraTimelockController` (24 h) | PAUSER: 2 addresses, one an EOA. Roles in the source: `FREEZE_ADMIN`, `WHITELIST_ADMIN`, `WITHDRAWAL_ADMIN`, `REDEEM_OPERATOR`, `NAV_ORACLE_UPDATER`. 6 role hashes held, 1 by an EOA; the names behind them are not matched yet. wYLDS's asset is **USDC on Ethereum**, so the yield comes from off-chain flows run by the operator roles |
| nvPRIME (Nuva) | ERC-1967 → `NuvaVault` over PRIME | owner `GovernanceTimelock` (48 h) | PAUSER `0x402e…` |
| fxSAVE, fxSP stability pool `0x65c9…` (f(x); fxUSD itself is `0x0857…d8f6`) | Transparent proxy → `SavingFxUSD`, `FxUSDBasePool` | ProxyAdmin `0x9b54…` owned by `TimelockController` (**72 h**) | two-step redeem: cooldown restarts on each request; docs say 60 min and 1 % instant fee, the deploy parameter was 1800 s (read on-chain to confirm); keepers repay the pool at par, so its loss comes through an fxUSD or USDC depeg |
| trUSD, strUSD (Tori) | ERC-1967 → `TrUSD`, `StakedTrUSD` | owner Safe **3/5** `0x0c6b…8316`. Upgrades, new collateral, custodians and minters go through `TIMELOCK_ADMIN_ROLE`, which is held by a `TimelockController` `0xA952…6ef4` with a **24 h** delay (checked on-chain 2026-10-11 with `hasRole`/`getMinDelay`; Tori docs `security/roles.md`). The Safe acts with no delay on pause, mint and redeem limits, role grants and collateral removal | mint and redeem: KYC whitelist, 10 bps fee; strUSD unstaking takes 7 days |
| etrUSD (Tori Ecosystem Vault, Upshift) | Transparent proxy → `BridgeableReceiptToken`, **LayerZero V2** endpoint `0x1a44…728c` | ProxyAdmin owner Safe **4/6** `0x86ee…`; owner Safe 4/6 `0x4fde…` | it is the Upshift vault's share, cross-chain |
| PT-reUSD's underlying reUSD | ERC-1967 → `ShareToken` | admin not read | SY `PendleREUSDSY`, owner `0x2ad6…` |
| siUSD / iUSD (infiniFi) | `StakedToken` / `ReceiptToken`, not proxies | governed by infiniFi Core; timelock and 4/7 multisig per the docs only (not read on-chain) | siUSD exits are blocked when paused, while a loss is pending (`unaccruedYield() < 0`) and outside the pausable, upgradeable Gateway; then a FIFO redemption queue. Current farms are mostly off-chain credit (FalconX, Fasanara, New Silver) |
| mGLOeuro (Midas) | Transparent proxy → `mGLOeuro` | `MidasTimelockController` (48 h) | `MidasAccessControl`; 59.19 tokens in total (~100k EUR each) |
| EURCV (SG-Forge, loan asset of the Belem vault) | ERC-1967 → `SmartCoin` | UUPS; admin not read (SG-Forge registrar and operator roles) | freeze and blacklist by the issuer |

## 5. Bridges and cross-chain paths

| Path | Mechanism | What can go wrong | Affected |
|---|---|---|---|
| PST Solana ↔ Ethereum | Chainlink CCIP burn-and-mint (2 pools: an old and a new lane), admin RBACTimelock with a 3 h delay | an unbacked mint on Ethereum if the lane or the pool owner is compromised; the oracle (exchange rate) would not see it | Confidential RWA USDC, Huma USDC Main: **$34.7M** |
| etrUSD | LayerZero V2 OFT receipt token | a DVN or configuration compromise lets anyone mint etrUSD; the Upshift vault's assets sit elsewhere | Tori Ecosystem, USDC Yield: $1.9M |
| Hastra wYLDS | ERC-4626 on Ethereum holding USDC; the yield comes from Figure loans on Provenance through operator roles (off-chain) | custody and operator risk, not a bridge contract | $3.4M on Morpho |
| OnRe Core Vault (non-Morpho) | USDC → Chainlink CCIP → Solana (ONyc, Kamino, Loopscale, Exponent) | CCIP lane; all of Solana's DeFi stack | $3.5M |

## 6. Who borrows (counterparty concentration)

The Morpho API was read on 2026-10-11, keeping positions above $100.

| Market | Borrowers | Borrowed | Top 1 | Top 3 | Top borrower |
|---|---|---|---|---|---|
| mGLOeuro / EURCV | **1** | $4.12M | **100 %** | 100 % | EOA `0xa122…E7c6` |
| nvPRIME | 3 | $1.17M | **100 %** | 100 % | EOA `0x1d87…7317` |
| PRIME | 4 | $1.46M | **96 %** | 100 % | `MultiDepositorVault` "glPRIME" `0xc4C7…fe94`, a looping vault |
| siUSD | 5 | $7.19M | **94 %** | 100 % | an EIP-7702 delegated account `0xf9c8…7f36` |
| AUTO | 3 | $0.54M | 67 % | 100 % | EOA |
| PT-fxSAVE | 12 | $1.01M | 60 % | 84 % | – |
| PT-trUSD | 30 | $1.82M | 50 % | 73 % | – |
| etrUSD | 10 | $1.68M | 49 % | 86 % | EOA |
| PST | 7 | $34.38M | 48 % | **88 %** | EOA `0x9F0D…f952` |
| fxSAVE | 18 | $25.32M | 36 % | 65 % | EOA |
| strUSD | 46 | $12.55M | 19 % | 46 % | – |
| PT-reUSD | 99 | $53.69M | 10 % | 26 % | – |

The blue-chip and Base markets are left out: the 300-position page is filled by lenders there, so their counts are incomplete.

Most RWA markets are **one or two loopers**. If such a borrower walks away, or is a related party of the issuer, it is a single event. The vault depends on that borrower repaying, more than on a liquidation working. Finding out who these addresses are (issuer treasury, fund, RockawayX's own strategy) is in §10.

## 7. Exit liquidity

**Pendle pools behind the PT collateral:**

| PT | Pool | Liquidity | Expiry | Days left |
|---|---|---|---|---|
| PT-reUSD-10DEC2026 | `0x1328…77c0` | $12.4M | 2026-12-10 | 60 |
| PT-strUSD-26NOV2026 | `0xac02…addb` | $4.6M | 2026-11-26 | 46 |
| PT-fxSAVE-29OCT2026 | `0x8308…9454` | $1.4M | **2026-10-29** | **18** |
| PT-trUSD-26NOV2026 | `0xfcf0…c947` | $1.1M | 2026-11-26 | 46 |

At expiry a PT redeems 1:1 for the yield-bearing token. Each vault's exposure then becomes the underlying (fxSAVE, strUSD, trUSD) unless the curator re-allocates. Debt on PT-reUSD ($53.7M) is **4.3× the pool**. The PT-trUSD pool, at $1.1M, is smaller than the $1.97M the Tori vault lends against it.

**DEX depth (KyberSwap aggregator, selling into USDC, measured against the oracle price):**

| Token | $0.1M | $1M | $5M | Market debt |
|---|---|---|---|---|
| PRIME | 0.0 % | 0.0 % | −0.1 % | $1.5M |
| PST | 0.0 % | 0.0 % | no usable route | $34.4M |
| strUSD | −0.2 % | −1.1 % | −69 % | $12.6M |
| fxSAVE | −0.5 % | **−27 %** | −83 % | $25.3M |
| etrUSD | **−55 %** | −92 % | −99 % | $1.7M |
| AUTO, mGLOeuro | no route | no route | no route | $0.5M, $4.1M |
| siUSD, nvPRIME, the PTs | not measured reliably (the quotes go through Pendle or the issuer, not a DEX) | | | |

A liquidator can absorb only small positions in most of these markets. In a markdown, the bad debt is set by issuer redemption (queues, cooldowns, KYC), not by a DEX. Today `riskdep` measures exit cost only for the PT position in `analyze`.

## 8. Vault-on-vault chains

- **USDC Yield and Tori Ecosystem → etrUSD → Upshift "Tori Ecosystem Vault" ($24.9M) → trUSD → Tori's off-chain trading book.** RockawayX's Upshift vault is also collateral in its Morpho vaults. A Tori loss is counted at three levels.
- **NUVA Ecosystem → nvPRIME (`NuvaVault`) → PRIME (`StakingVault`) → wYLDS (`YieldVaultV2`, USDC) → Figure loans.** Four wrappers, three admin sets.
- **USDC Yield → the PRIME market → glPRIME (`MultiDepositorVault`) loops PRIME**: a third-party leveraged vault is 96 % of the borrowing.
- **Kamino "Huma PST" ($42.5M) and the Morpho PST markets ($34.7M)** depend on the same Huma pool. On Ethereum, PST is the CCIP-bridged copy.

## 9. The non-Morpho vaults (25 of 33, $194M)

Not analysed on-chain. What each depends on, and what `riskdep` would need:

| Vault | Depends on | Needs |
|---|---|---|
| Kamino ×9 (Solana, $122M) | Kamino Lend (klend), Scope/Pyth/Switchboard oracles, collateral ONyc, PRIME, PST, oTFY, rkuSOL, PT-rkuSOL (Exponent), SOL | Solana RPC and the Kamino API; klend source; an SVM reader (out of scope today) |
| Upshift Tori Ecosystem (Ethereum, $24.9M) and Earn ctUSD (Citrea) | Upshift (August) vault contracts, trUSD, LayerZero (etrUSD) | Upshift contracts and docs |
| Ember Y10K (Ethereum, $17.8M) | Ember vault platform; "private liquidity deals" (pre-deposits, genesis launches): positions not public | Ember contracts; a positions disclosure |
| Feather PYUSD0 (Sei, $12.4M) | Feather (a Morpho fork on Sei?), PYUSD0 (LayerZero PYUSD), Sei | Sei RPC; Feather docs |
| Oku RockawayX USDC (Pharos chain, $11.2M) | Oku on the Pharos L1; a bridged USDC | Pharos RPC; Oku docs |
| OnRe Core Vault (Accountable, $3.5M) | Accountable vault, CCIP, Solana: ONyc, Kamino, Loopscale, Exponent | Accountable contracts and docs |
| mROX (Midas, $3.4M) | Midas issuance contracts, custodian, RockawayX's market-neutral book (Morpho, Curve, Pendle) | Midas contracts; mROX positions report |
| RockawayX YIELD PT (Lista, BSC, $1.3M) | Lista Lending (a Morpho fork), Pendle PTs on BSC | BSC RPC; Lista docs |
| Midas USDC Prime (Base, $0.6M) | Morpho on Base | a chain parameter in `riskdep` |

## 10. What I need from you

Please add these under `docs/external/` (as submodules where there is a repository), or send the keys, so the next pass can confirm what this file infers.

**Smart-contract sources (highest exposure first):**
1. **Huma**: PST pool and CCIP setup (`huma-finance` repositories: the Solana program and the EVM `BurnMintERC20` deployment). Huma PST is $34.7M on Morpho and $82M across RockawayX.
2. **f(x) Protocol**: `AladdinDAO/fx-protocol-contracts` (`SavingFxUSD`, `FxUSDBasePool`, `NetAssetValueChainlinkAdapter`).
3. **Tori**: `TrUSD`, `StakedTrUSD`, and how mint and redeem work. Is there a timelock behind the 3/5 Safe?
4. **Re**: `ShareToken` (reUSD), redemption buffer contracts.
5. **Hastra**: `YieldVaultV2`, `StakingVault`, `AutoStakingVault` (verified on Etherscan, so I can fetch these myself; say if you prefer a pinned repository). Also the meaning of the 6 unmatched role hashes.
6. **infiniFi**: `infinifi-protocol` (Core, `ChainlinkRTOracle`, `StakedToken`, the redemption queue).
7. **Midas**: `midas-contracts` (`mGLOeuro`, `CustomAggregatorFeed`, `MidasAccessControl`, redemption vaults).
8. **Nuva**: `NuvaVault`.
9. **Ojo**: `OjoPTFeed` and `ChainlinkCurrentTimestampAdapter` (what FEED_2 computes).
10. **RedStone**: the fundamental feed implementations, and the process of the 2/3 Safe.
11. **Upshift / August**, **Ember**, **Accountable**: vault contracts.

**Documentation:**
- Chainlink: the feed pages for "PST-USDC Exchange Rate (Calculated)", "PRIME / WYLDS" and "Hastra Auto / WYLDS" (what data, heartbeat, deviation). Also the CCIP docs (token pools, rate limits, `RBACTimelock`). The `chainlink/docs.chain.link-data-feeds-docs/` folder may already hold the feed part.
- LayerZero V2: the OFT and DVN configuration docs (etrUSD).
- RedStone: the "fundamental" feed methodology.
- Issuer attestations and reports: Tori via Accountable, Huma pool reports, Re's capital stack, OnRe monthly attestations, the Fasanara fund NAV policy (mGLOeuro), SG-Forge EURCV terms.
- RockawayX's own risk framework (curation limits, its policy on the fee and allocator changes that have no timelock) and any statement on who the main borrowers are (§6).

**Access:**
- A **Dune API key** (in `keys.ini`, `[dune] api_key`) to read the 8 hidden rows and the vault history.
- RPC URLs for **Base**, **BSC**, **Sei** and **Solana** if those vaults are in scope. `riskdep` is Ethereum-only today.
- A yes or no on scope: Ethereum Morpho only, or also the Solana and Kamino side ($122M).

## 11. What to change in riskdep

These follow from the findings above, in order of value:

1. **A standing "exit gate" finding in `watch`**: done (`ExitGate`, D184). On these 8 vaults it reports the gates abdicated.
2. **Feed-admin and feed-age facts in `oracle_class.py` and `admin.py`**: add the classes `linear-discount PT`, `on-chain NAV`, `issuer-published (custom aggregator)`, `dummy/constant`. Add a warning for an upgradeable feed under a Safe with no timelock (RedStone 2/3), and a staleness warning (mGLOeuro, 17.5 days).
3. **Borrower concentration in `market_risk.py`**: show top-1 and top-3 shares, and flag markets with fewer than 5 borrowers.
4. **Bridges as graph nodes**: CCIP (PST) and LayerZero (etrUSD) as Admin or Protocol nodes, with their owners and delays.
5. **Registry**: the issuer entries listed in `ROCK-VAULT.md` §6, plus RedStone, Ojo, Chainlink exchange-rate feeds and CCIP as oracle and bridge entries with priors.
6. **PT expiry handling**: the collateral switches to the underlying at maturity (PT-fxSAVE in 18 days).
