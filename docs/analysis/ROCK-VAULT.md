# RockawayX vaults: dependencies and what `riskdep` can analyse

Source: the Dune dashboard [rockawayxvault/rockawayx-dashboard](https://dune.com/rockawayxvault/rockawayx-dashboard), read on 2026-10-10. Each Morpho vault was then read from the Morpho API (`vaultV2ByAddress`: adapters, market positions, collateral, LLTV, oracle). Each oracle was read on-chain with the `MorphoChainlinkOracleV2` getters, and each feed with `description()`. Figures are from that day and move daily.

## 1. Summary

- **33 vaults, $293.6M, 9 venues, 8 chains.** The 25 largest vaults add up to $293.7M, so the 8 rows the page did not show are dust.

  | Venue | TVL |
  |---|---|
  | Kamino (Solana) | $122.1M |
  | Morpho (Ethereum, Base) | $96.9M |
  | Upshift | $24.9M |
  | Ember | $17.8M |
  | Feather (Sei) | $12.4M |
  | Oku (Pharos) | $11.2M |
  | Accountable | $3.5M |
  | Midas | $3.4M |
  | Lista (BSC) | $1.3M |

- **The 8 Morpho vaults are all Vault V2, and `riskdep` can read the 7 on Ethereum today.**
  - Each vault holds one `MorphoMarketV1` adapter, has no Vault V1 underneath, and has nothing idle.
  - All 8 have the same address as curator and owner: `0xbBacDCFB…f918`.
  - The demo vault of the `graph` command, `0xE018…1965`, is one of them.
- **The risk sits in the issuers, not in Morpho.** About 98 % of the $99.7M Morpho book lends against RWA, credit or yield tokens from young issuers:
  - Huma, Tori, f(x), Re, Hastra, Midas/Fasanara, infiniFi and Nuva.
  - None of them is in `registry.json`, whose issuers are only sUSDe, USDe, wstETH and sUSDS.
- **Nearly every oracle is an issuer-reported rate or NAV, not a market price.** A market depeg therefore does not trigger liquidations. The loss arrives all at once when the issuer marks down its NAV, and it lands on the vault as bad debt. This is the "constant-price" or fundamental case that `oracle_class.py` is built to flag.
- **Utilisation is 86–91 % in every market.** A depositor who wants out depends on borrowers repaying, which is exactly what `drain.py` and `exit_queue.py` measure.
- **The same issuers show up across venues.** Huma PST is collateral in 2 Morpho vaults and backs 3 Kamino vaults. Tori is in 2 Morpho vaults and the Upshift vault. Hastra is in 3 Morpho vaults and 1 Kamino market. One issuer incident therefore hits several RockawayX vaults at once, which is the concentration the brief asks about.
- **One vault is Belem's.** "Belem RWA EURCV" ($5.3M, 4 holders) is a RockawayX-curated vault for the challenge's sponsor. It is the most relevant demo target (§5).

## 2. The vaults

| # | Vault | Chain | Venue | Address | Asset | TVL | APY | Holders |
|---|---|---|---|---|---|---|---|---|
| 1 | RockawayX RWA USDC | Solana | Kamino | `DWSXb18x…7KaP` | USDC | $62.7M | 5.6 % | 1,163 |
| 2 | Huma PST | Solana | Kamino | `DzgYbR8H…KDHz` | PST | $42.5M | 0.0 % | – |
| 3 | Tori Ecosystem Vault | Ethereum | Upshift | `0xcd69…De54` | trUSD | $24.9M | 3.3 % | – |
| 4 | **RockawayX Confidential RWA USDC** | Ethereum | Morpho V2 | `0xc207…Da36` | USDC | $23.9M | 10.0 % | 6 |
| 5 | **RockawayX f(x) Protocol Ecosystem USDC** | Ethereum | Morpho V2 | `0x2cA2…a423` | USDC | $20.7M | 8.1 % | 156 |
| 6 | **RockawayX USDC Yield** | Ethereum | Morpho V2 | `0xE018…1965` | USDC | $18.6M | 6.1 % | 167 |
| 7 | Y10K | Ethereum | Ember | `0x9539…e074` | eY10K | $17.8M | 9.0 % | 17 |
| 8 | **RockawayX Tori Ecosystem** | Ethereum | Morpho V2 | `0x3BD9…9478` | USDC | $13.6M | 6.0 % | 34 |
| 9 | **Huma USDC Main** | Ethereum | Morpho V2 | `0x8aC9…475c` | USDC | $12.6M | 7.3 % | 51 |
| 10 | Feather PYUSD0 | Sei | Feather | `0x6137…7a06` | PYUSD0 | $12.4M | 6.3 % | 14 |
| 11 | RockawayX USDC | Pharos | Oku | `0x047c…02E5` | USDC | $11.2M | 4.0 % | – |
| 12 | Obligate oTFY | Solana | Kamino | `6nk5K3Pi…m6WF` | oTFY | $7.2M | 20.5 % | – |
| 13 | **Belem RWA EURCV** | Ethereum | Morpho V2 | `0xD6d4…48Ec` | EURCV | $5.3M | 2.6 % | 4 |
| 14 | RockawayX SOL | Solana | Kamino | `HoffqVZU…2or` | SOL | $3.7M | 4.2 % | 30 |
| 15 | OnRe Core Vault | Ethereum | Accountable | `0x0F0a…B3c4` | USDC | $3.5M | 11.2 % | 58 |
| 16 | mROX | Ethereum | Midas | `0x67E1…5c05` | mROX | $3.4M | 8.6 % | 14 |
| 17 | Raiku rkuSOL | Solana | Kamino | `J7idSfhv…HZrP` | rkuSOL | $2.6M | 1.9 % | – |
| 18 | Marinade USDC Cluster | Solana | Kamino | `2TNCzzYJ…dgGA` | USDC | $1.6M | 5.8 % | 439 |
| 19 | **RockawayX NUVA Ecosystem** | Ethereum | Morpho V2 | `0x93e0…2E5a` | USDC | $1.5M | 7.5 % | 32 |
| 20 | Raiku PT-rkuSOL | Solana | Kamino | `7272BNf9…DwSPLqN` | PT-rkuSOL-31OCT26 | $1.4M | 1.9 % | – |
| 21 | RockawayX YIELD PT | BSC | Lista | `0xb5a3…5dd2` | USDT | $1.3M | 23.3 % | 209 |
| 22 | **RockawayX Midas USDC Prime** | Base | Morpho V2 | `0xAE41…9Edc` | USDC | $0.6M | 4.6 % | 13 |
| 23 | Huma USDC | Solana | Kamino | `4QKFoFDz…mpnkCphj` | USDC | $0.6M | 6.8 % | – |
| 24 | Obligate USDC | Solana | Kamino | `Au2Cg9CN…5ZW` | USDC | $0.05M | 6.5 % | – |
| 25 | Earn ctUSD | Citrea | Upshift | `0x6849…0BA2` | ctUSD | $0.05M | 0.0 % | – |

Bold rows are the Morpho vaults detailed in §3. The page's text names Plume, Etherlink and 0G, and DefiLlama adds Monad with $15.0M. No row on the page carries those chains, so they are either in the 8 hidden rows (which add up to almost nothing) or counted by DefiLlama outside this table.

**Two of them are also Zama confidential vaults** (checked on-chain on 2026-10-11, addresses from `docs/external/docs.zama.org-protocol-docs/confidential-vault/reference/addresses.md`). Zama's Confidential Vault protocol puts a deposit and a redeem batcher and a confidential share token (cShare, ERC-7984) in front of a public Vault V2, so a depositor's amount stays encrypted; batches settle once a day. How `riskdep` could analyse them: `docs/analysis/ZAMA-VAULT.md`.

| Vault | Zama app | Vault | cShare | Deposit batcher | Redeem batcher | Deposit gate | Held through cShare |
|---|---|---|---|---|---|---|---|
| RockawayX Confidential RWA USDC (#4) | [rockawayx-usdc-rwa](https://app.zama.org/earn/ethereum/0xc207d3f66537D7F66456808379A0E560cF20Da36/rockawayx-usdc-rwa) | `0xc207…Da36` | `0xB1B1…EB30` | `0x084f…eEc1` | `0x43e8…0E4b` | `0x51f6…D525`: only the deposit batcher may deposit | 99.1 % |
| RockawayX USDC Yield (#6) | [rockawayx-usdc-high-yield](https://app.zama.org/earn/ethereum/0xE0181090c22579B6A217f1522cbf8c9f1F0C1965/rockawayx-usdc-high-yield) | `0xE018…1965` | `0x4FCC…B88f` | `0x2dEA…724d` | `0xf18A…d8a8` | none: public deposits too | 0.8 % |

Both use cUSDC `0xe978…72B2`. So the "6 holders" of #4 are in practice one: the cShare wrapper, behind which the confidential depositors sit.

## 3. Morpho vaults: markets, collateral, oracles

All 8 are Vault V2, each with a single `MorphoMarketV1` adapter. The Morpho API names vault 6 "RockawayX USDC Yield"; the dashboard calls it "RockawayX YIELD USDC".

| Vault (TVL) | Collateral (issuer) | Vault supply | LLTV | Util. | Market size | Oracle → feed |
|---|---|---|---|---|---|---|
| **Confidential RWA USDC** ($26.4M) | PST (Huma) | $21.86M | 86 % | 91 % | $38.0M | `0xa565…` → "PST-USDC Exchange Rate (Calculated)" |
| | PT-reUSD-10DEC2026 (Re, Pendle) | $3.98M | 91.5 % | 89 % | $120.5M | `0x217d…` → "Ojo PT Feed Pendle" |
| | AUTO (Hastra) | $0.60M | 77 % | 90 % | $0.6M | `0x9abd…` → "Hastra Auto / WYLDS Exchange Rate" ÷ USDC/USD |
| **f(x) Protocol Ecosystem** ($21.0M) | fxSAVE (f(x)) | $19.96M | 91.5 % | 90 % | $28.1M | `0x1693…` → "Net Asset Value in USD" |
| | PT-fxSAVE-29OCT2026 (f(x), Pendle) | $1.02M | 91.5 % | 88 % | $1.1M | `0x5911…` → unnamed PT feed `0x9105…` |
| **USDC Yield** ($18.4M) | PT-reUSD-10DEC2026 | $9.30M | 91.5 % | 89 % | $120.5M | `0x217d…` (as above) |
| | strUSD (Tori) | $4.91M | 86 % | 87 % | $14.4M | `0x1506…` → "RedStone strUSD_FUNDAMENTAL" ÷ USDC/USD |
| | siUSD (infiniFi) | $2.36M | 91.5 % | 90 % | $8.0M | `0xd2cC…` → "InfiniFi RT Oracle" × siUSD vault rate |
| | PRIME (Hastra) | $1.51M | 86 % | 86 % | $1.7M | `0x999e…` → "PRIME / WYLDS Exchange Rate" ÷ USDC/USD |
| | PT-strUSD-26NOV2026 (Tori, Pendle) | $0.26M | 86 % | 87 % | $0.8M | `0xdB6e…` → PT feed × "RedStone trUSD_FUNDAMENTAL" |
| | etrUSD (Tori Ecosystem Vault share) | $0.11M | 86 % | 90 % | $1.9M | `0xF731…` → "RedStone etrUSD_FUNDAMENTAL/USD" |
| **Tori Ecosystem** ($13.6M) | strUSD | $9.39M | 86 % | 87 % | $14.4M | `0x1506…` (as above) |
| | PT-trUSD-26NOV2026 | $1.97M | **94.5 %** | 90 % | $2.0M | `0x3458…` → PT feed × "RedStone trUSD_FUNDAMENTAL" |
| | etrUSD | $1.75M | 86 % | 90 % | $1.9M | `0xF731…` |
| | PT-strUSD-26NOV2026 | $0.49M | 86 % | 87 % | $0.8M | `0xdB6e…` |
| **Huma USDC Main** ($12.8M) | PST (Huma) | $12.84M | 86 % | 91 % | $38.0M | `0xa565…` |
| **Belem RWA EURCV** ($5.3M, loan asset EURCV) | mGLOeuro (Midas / Fasanara) | $4.52M | 77 % | 91 % | $4.5M | `0x2b43…` → "mGLOeuro/EUR" |
| | WBTC | $0.51M | 86 % | 89 % | $5.2M | `0x4072…` → WBTC/BTC × BTC/USD ÷ EUR/USD |
| | cbBTC | $0.13M | 86 % | 89 % | $15.0M | `0xbA75…` |
| | wstETH | $0.11M | 86 % | 90 % | $2.0M | `0x44D6…` → wstETH/ETH × ETH/USD ÷ EUR/USD |
| **NUVA Ecosystem** ($1.5M) | nvPRIME (Nuva vault on Hastra PRIME) | $1.29M | 86 % | 90 % | $1.3M | `0x9cc1…` → nvPRIME vault rate × PRIME/WYLDS ÷ USDC/USD |
| | cbBTC | $0.25M | 86 % | 90 % | $337M | `0xA6D6…` |
| **Midas USDC Prime** (Base, $0.6M) | cbETH, cbBTC, WETH | $0.19M + $0.20M + $0.19M | 86 % | 90 % | blue-chip | Chainlink |

### Exposure by issuer (Morpho book, $99.7M)

| Issuer family | Tokens | Morpho exposure | Share | Also elsewhere in RockawayX |
|---|---|---|---|---|
| Huma (PayFi credit, Arf originator) | PST | $34.7M | 35 % | Kamino Huma PST $42.5M, the Huma market of RWA USDC (~$5M), Huma USDC $0.6M |
| f(x) Protocol (fxUSD stability pool) | fxSAVE, PT-fxSAVE | $21.0M | 21 % | – |
| Tori (delta-neutral synthetic dollar) | strUSD, etrUSD, PT-trUSD, PT-strUSD | $18.9M | 19 % | Upshift Tori Ecosystem Vault $24.9M |
| Re (reinsurance, senior tranche) | PT-reUSD | $13.3M | 13 % | – |
| Midas / Fasanara (private credit, EUR) | mGLOeuro | $4.5M | 5 % | mROX (Midas, RockawayX's own strategy) $3.4M |
| Hastra / Figure (home-equity loans) | PRIME, AUTO, nvPRIME | $3.4M | 3 % | Prime market of Kamino RWA USDC (~$5.9M) |
| infiniFi (fractional reserve) | siUSD | $2.4M | 2 % | – |
| Blue chips | WBTC, cbBTC, wstETH, cbETH, WETH | $1.6M | 2 % | – |

The Kamino allocations come from RockawayX's own published update and were not read on-chain.

Huma alone backs about $82M across the RockawayX vaults, 28 % of the firm's total. That breaks the curator's own published 25 % single-protocol limit (see Resources).

### What sits behind each issuer (second-order dependencies)

| Issuer | Depends on | Loss path into a vault |
|---|---|---|
| Huma PST | Arf-originated cross-border payment credit (affiliated), a ~25 % stablecoin buffer, Solana (PST is issued there; on Ethereum it is a bridged or wrapped token) | defaults, or a run that drains the buffer → issuer rate cut → bad debt with no liquidation |
| f(x) fxSAVE | fxUSD stability pool: wstETH (Lido) and WBTC positions, a USDC reserve; 60 min cooldown | fxUSD depeg or a stability-pool loss → NAV feed down |
| Tori trUSD / strUSD / etrUSD | off-chain custodians and trading venues (basis, calendar spreads), Accountable attestations | venue or custodian failure (an FTX-type event) → fundamental feed cut |
| Re reUSD | quota-share reinsurance (US), ≥ 50 % on-chain buffer partly in USDe/sUSDe (Ethena), Pendle PT pool | cat losses above the equity and mezzanine tranches; Ethena depeg; PT pool or Ojo feed |
| Hastra PRIME / AUTO | Figure home-equity loans on Provenance, wYLDS, bridged from Solana | loan defaults, bridge failure |
| Midas mGLOeuro | Fasanara receivables fund, Midas issuance contracts | fund NAV markdown; EUR redemption |
| infiniFi siUSD | fractional reserve, now mostly off-chain credit farms (FalconX, Fasanara, New Silver; Aave paused); safety buffer then liUSD take losses first, then siUSD | strategy loss beyond the liUSD tranche; bank-run on reserves |
| SG-Forge EURCV (loan asset) | Société Générale-Forge, EUR/USD feed | EURCV depeg: the oracles price EURCV as 1 EUR |

## 4. What the oracles mean for the analysis

- **Fundamental or NAV feeds.** These cover PST, fxSAVE, strUSD, etrUSD, PRIME, AUTO, nvPRIME, siUSD and mGLOeuro, about 75 % of the book. The issuer, or RedStone reading the issuer, reports the rate.
  - A drop in market price never reaches the oracle, so nothing gets liquidated during a depeg.
  - The loss arrives when the reported rate falls, all at once and larger than the margin. At an 86 % LLTV, a rate cut of more than about 14 % turns straight into bad debt.
  - So for a lender the right model is "probability of a markdown × size", not a liquidation cascade.
  - `oracle_class.py` should class all of these as constant-price or issuer-reported. *(2026-10-11: run on the Belem vault, §5.1; Midas's feed needed a new registry pattern, `CustomAggregator`. The other vaults are not probed yet.)*
- **The loan asset is assumed to be worth $1 in some markets.** Four oracles have no USDC/USD quote feed: PST, fxSAVE, PT-reUSD and mGLOeuro. In the Belem vault, EURCV is priced through EUR/USD, so a EURCV depeg goes unseen as well.
- **PT feeds.** These come from Ojo, and from three unnamed feeds on PT-fxSAVE, PT-strUSD and PT-trUSD. Whether each is a linear discount, a TWAP or the minimum of the two needs the getter probe. The PT-trUSD market's 94.5 % LLTV leaves only a 5.5 % margin.
- **Blue-chip markets** (WBTC, cbBTC, wstETH, cbETH, WETH) use standard Chainlink feeds. `riskdep` already models them, and they are 2 % of the book.

## 5. How `riskdep` could analyse them

| Vault | Today | What is missing |
|---|---|---|
| 7 Ethereum Morpho V2 vaults (#4, 5, 6, 8, 9, 13, 19) | `watch --vault`, `graph --vault` (siblings, oracle classes), `drain.py`, `exit_queue.py`, `market_risk.py` run as is; #6 is already recorded for `graph --replay` | registry entries for the issuers (§6); the fundamental-feed class in `oracle_class.py`; one Morpho book view across all 8 vaults (shared markets: PST in #4 and #9, strUSD and PT-reUSD in #6 and #8 / #4) |
| PT-reUSD, PT-fxSAVE, PT-strUSD, PT-trUSD markets | `analyze` fits a borrower who loops these PTs on Morpho | issuer entries for Re, f(x), Tori; Ojo and other PT oracles in `registry.json` `oracle.techniques` |
| Midas USDC Prime (Base) | – | `chainId:1` is hard-coded in 12 Morpho API queries, and the RPC is Ethereum only: a chain parameter is needed |
| mROX, OnRe Core, Y10K, Upshift Tori (Ethereum, non-Morpho) | – | different contracts (Midas, Accountable, Ember, Upshift); `graph` could show them as issuer nodes, since their tokens are the collateral (etrUSD is the Tori vault's share) |
| Kamino (Solana), Feather (Sei), Oku (Pharos), Lista (BSC), Citrea | out of scope | non-EVM or other chains; list them as off-chain dependency nodes only |

**Suggested demo target: Belem RWA EURCV (`0xD6d4…48Ec`).** It is the sponsor's own vault, small enough for the free RPC, and it shows three things the tool should explain:
- 86 % of it sits in one market (mGLOeuro at 77 % LLTV, 91 % utilisation), whose oracle is an issuer NAV;
- the loan asset EURCV is priced by an FX feed, with a constant-price assumption;
- the blue-chip remainder is well covered already.

The commands below were run on 2026-10-11; the results are in §5.1:

```bash
uv run python -m riskdep graph --vault 0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec --record
uv run python -m riskdep watch --vault 0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec --blocks 1000 --record
```

### 5.1 The Belem vault, recorded and checked (2026-10-11)

Both commands were run, and the recordings are in `fixtures/replay/graph-0xd6d4…48ec/` (graph, block 26,164,854) and `fixtures/replay/0xd6d4…48ec/` (watch, blocks 26,163,909 to 26,164,908). Tests: `test_belem_held_markets_and_the_midas_nav_feed` (`tests/test_graph.py`) and `test_belem_vault_replay` (`tests/test_watch_replay.py`).

**The vault.** 4,710,686 EURCV, nothing idle, one `MorphoMarketV1AdapterV2` adapter:

| Market | LLTV | Vault's allocation | Share | Utilisation | Vault's share of supply | Oracle class |
|---|---|---|---|---|---|---|
| mGLOeuro/EURCV (the liquidity market) | 77 % | 4,040,272 | 85.8 % | 91.0 % | 100 % | constant-price (issuer NAV) |
| WBTC/EURCV | 86 % | 455,555 | 9.7 % | 89.1 % | 10 % | price-tracking |
| cbBTC/EURCV | 86 % | 116,441 | 2.5 % | 89.5 % | 1 % | price-tracking |
| wstETH/EURCV | 86 % | 97,960 | 2.1 % | 89.7 % | 6 % | price-tracking |
| steakEURCV/EURCV, oTFYe/EURCV | 91.5 %, 77 % | 2, 1 | 0 % | — | — | constant-price |

**What the recording confirms from §1–§4:**
- 86 % of the vault is in mGLOeuro/EURCV, at 91 % utilisation, and the vault is that market's only lender.
- The loan asset EURCV is never priced itself: the oracles read EUR / USD, so a EURCV depeg is not seen.
- The blue-chip markets use standard Chainlink feeds and are classed price-tracking.

**What it adds:**
- **The mGLOeuro oracle is the issuer's own NAV.** Its feed `0x8b7b…9609` is Midas's `MGloEuroCustomAggregatorFeed` behind a `TransparentUpgradeableProxy`. It answers 100,000 EUR per mGLOeuro and has two rounds in its history, 2026-08-04 and 2026-09-23, both at 100,000. `oracle_class` first returned `not classified`: too few rounds for the history rule, and no pattern for the name. The registry now has a `CustomAggregator` pattern, classed constant-price, and the replay classes it so.
- **The issuer controls both the token and its price.** The mGLOeuro token `0x2f8b…7702` and its NAV feed are both upgradeable, with the same admin, `0xbf25…0aac`.
- **mGLOeuro/EURCV is also the vault's liquidity market**: deposits go there, and a plain withdrawal can only draw on its free liquidity, 361,743 EURCV.
- **One depositor holds 99.46 % of the vault**, 4,685,206 EURCV out of 4 holders. It can withdraw 1,031,701 now (361,743 plain, 669,958 through `forceDeallocate`, at no penalty), and 3,653,504 is stuck even first in line (`ExitQueue` warn, 78 % stuck).
- **The two mGLOeuro borrowers** borrow 3.68M EURCV against 52.58 mGLOeuro, worth 5.26M EUR at the NAV: about 70 % of collateral, against a 77 % LLTV. A NAV cut of about 9 % or more makes them liquidatable; bad debt starts only past a cut of about 25 %, where the collateral divided by the liquidation incentive (1.074) no longer covers the debt. The watch's curve stops at a 20 % fall, so it shows no bad debt for this market.
- **Governance:** seven risk-increasing changes have no timelock (fees, fee recipients, `setIsAllocator`, `setForceDeallocatePenalty`, the adapter's skim recipient); adding an adapter or raising a cap takes 3 days; the gates are abdicated.

**Incident mode for vaults, run on 2026-10-11** (`analyze --vault 0xd6d4…48ec --shock token=mGLOeuro:<cut>`, plan `2026-10-11-vault-incident`):

| Midas NAV cut | Debt liquidatable in mGLOeuro/EURCV | Bad debt (all on the vault) | Share of the vault | Verdict for the 99.46 % depositor |
|---|---|---|---|---|
| −10 % | 3.68M of 3.68M (both borrowers) | 0 | 0 % | STAY: the collateral still covers the debt |
| −30 % | 3.68M | 251,761 EURCV | 5.3 % | STAY: leaving first saves 382 (0.2 %) |
| −50 % | 3.68M | 1,230,838 EURCV | 26.1 % | STAY: leaving first saves 1,867 (0.2 %) |

The incident lands at once when Midas publishes the new NAV: the oracle is the issuer's own figure, so no market move announces it. For the largest depositor, leaving first changes almost nothing, because it is 99.46 % of the vault and the loss falls on it either way; withdrawing the 1.03M that can leave only reduces its exposure to a further cut. A small depositor in the same vault would be told to EXIT: the first 1.03M out leaves the loss to those who stay.

### 5.2 The RockawayX book under one issuer incident (2026-10-11)

The seven Ethereum vaults are in `examples/rockawayx-ethereum.json` and recorded under `fixtures/replay/incident-<vault>/` (`analyze --book … --record`, plan `2026-10-11-vault-book`). The book is 99.1M USD, each vault at its total assets. Each issuer token cut by 30 %, one at a time:

| Token cut by 30 % | Vaults holding it | In those markets | Book loss | Vaults where leaving first lowers the loss |
|---|---|---|---|---|
| PST (Huma) | Confidential RWA USDC, Huma USDC Main | 34.70M | **5.19M (5.24 %)** | Huma USDC Main |
| fxSAVE (f(x)) | f(x) Protocol Ecosystem USDC | 19.89M | 1.88M (1.90 %) | f(x) Protocol Ecosystem USDC |
| strUSD (Tori) | USDC Yield, Tori Ecosystem | 14.30M | 1.60M (1.61 %) | both |
| siUSD (infiniFi) | USDC Yield | 2.36M | 0.40M (0.40 %) | USDC Yield |
| mGLOeuro (Midas) | Belem RWA EURCV | 4.52M | 0.28M (0.28 %) | none |
| etrUSD (Tori) | USDC Yield, Tori Ecosystem | 1.86M | 0.26M (0.26 %) | Tori Ecosystem |
| PRIME (Hastra) | USDC Yield | 1.51M | 0.13M (0.13 %) | USDC Yield |
| nvPRIME (Nuva) | NUVA Ecosystem | 1.29M | 0.03M (0.03 %) | NUVA Ecosystem |
| AUTO (Hastra) | Confidential RWA USDC | 0.60M | 0.02M (0.02 %) | none |

**What it says:**
- **Huma is the book's largest single issuer risk.** A 30 % PST cut costs 5.2M, more than every other issuer's cut combined, because PST backs most of the Confidential RWA vault and all of Huma USDC Main.
- **Tori reaches two vaults through two tokens** (strUSD and etrUSD); together a 30 % cut on both would cost about 1.9M.
- **Leaving first lowers the loss in most hit vaults**, because they have many depositors; Belem is the exception, with one depositor at 99.46 %.

**Wrapped collateral (D124, then D126–D127).** The table above matches a token as the markets' direct collateral. Since plan `2026-10-11-wrapped-collateral`, a token also reaches the markets whose collateral wraps it:

| Token cut by 30 % | Vaults reached | In those markets | Book loss | Through |
|---|---|---|---|---|
| trUSD (Tori) | Tori Ecosystem, USDC Yield | 17.01M | 1.61M (1.63 %) | strUSD, PT-strUSD, PT-trUSD (oracles constant-price: hidden shortfall) |
| wYLDS (Hastra) | Confidential RWA USDC, USDC Yield, NUVA Ecosystem | 3.40M | 0.09M (0.09 %) | PRIME, AUTO, nvPRIME |

etrUSD, a vault of Tori vaults, answers no `asset()` and stays opaque.

## 6. Registry additions this needs

Each entry needs its basis, as `registry.json` requires: issuer category, TVL, age, audits, the Pharos or Nexus estimate where one exists (`EXTERNAL_SOURCE.md` §7), and the redemption route. In order of exposure:

1. **Huma PST** `0x22aE3D9a…d4c7`. Category: private credit. Single-originator concentration.
2. **f(x) fxSAVE** `0x7743e50F…fc39` (its asset is the fxSP stability-pool share `0x65c9a641…`, `FxUSDBasePool`; fxUSD itself is `0x0857…d8f6`).
3. **Tori**:
   - trUSD `0xd0580192…1697`;
   - strUSD `0x28083998…5815`;
   - etrUSD `0x6f20aE2C…592d`, a vault of vaults.
4. **Re reUSD**, through PT-reUSD `0xeCfaFdC7…3483`. Its dependency on Ethena reuses the existing sUSDe entry.
5. **Midas mGLOeuro** `0x2F8bae12…7702`, and **SG-Forge EURCV** `0x5f7827fd…85ff2` as a non-USD stable in `stables`.
6. **Hastra** PRIME `0x19ebb352…F7F6`, AUTO `0x997E2Efb…1da9` and wYLDS `0x6ad038ca…66cc`. **Nuva** nvPRIME `0xC360e625…87D1`.
7. **infiniFi** siUSD `0xDBDC1Ef5…bCB` (iUSD `0x48f9e38f…`).
8. **Blue chips** WBTC, cbBTC, cbETH, which are only partly covered (wstETH is already in).

Without these entries, every one of these tokens falls back to `unknown_issuer`, and the priors then read the same for Huma as for infiniFi.

## 7. Resources

- Dune dashboard: <https://dune.com/rockawayxvault/rockawayx-dashboard>
- Morpho API `https://blue-api.morpho.org/graphql` (`vaultV2ByAddress`, adapters, `MorphoMarketV1Adapter.positions`), queried 2026-10-10.
- On-chain `eth_call` (publicnode) of `BASE_FEED_1/2`, `BASE_VAULT`, `QUOTE_FEED_1/2`, `QUOTE_VAULT`, `description()`, `name()`, `asset()`.
- DefiLlama protocol `rockawayx` (`https://api.llama.fi/protocol/rockawayx`): chains and TVL by chain.
- RockawayX:
  - [Tori vault thesis and risk disclosure](https://rockawayx.com/insights/rockawayx-tori-ecosystem-vault-investment-thesis-risk-disclosure)
  - [Vault curation overview](https://rockawayx.com/insights/rockawayx-vault-curation-an-overview-of-products-capabilities)
  - [Curating capital flows (concentration limits)](https://rockawayx.com/insights/rockawayx-curating-capital-flows)
  - [Kamino diversified vault](https://rockawayx.com/insights/rockawayx-and-kamino-launch-new-diversified-market-neutral-vault-in-partnership-with-onre-huma-figure-and-solstice)
  - [mROX launch](https://rockawayx.com/insights/rockawayx-and-midas-launch-mrox-surpassing-6m-in-week-one-tvl)
  - [OnRe Core Vault](https://rockawayx.com/insights/bringing-onres-onyc-to-ethereum-with-onre-core-vault)
  - [Huma yield spotlight](https://rockawayx.com/insights/yield-spotlight-huma-finance)
  - [Morpho forum: RockawayX vaults](https://forum.morpho.org/t/introducing-rockawayx-vaults-on-morpho/2214)
- Huma:
  - [Sentora asset risk review](https://sentora.com/asset-risk-reviews/huma)
  - [Jupiter PayFi risk report](https://static-r2.jup.ag/lend/risk-research/payfi-risk-report.pdf)
- Tori:
  - [DefiLlama trUSD](https://defillama.com/stablecoin/tori-trusd)
  - [Alea research](https://alearesearch.io/newsletters/tori-finance-market-neutral-yield)
- Re:
  - [docs.re.xyz](https://docs.re.xyz)
  - [Re capital stack](https://re.xyz/insights/inside-res-capital-stack-how-reusd-and-reusde-unlock-insurance-yield)
- f(x):
  - [MixBytes on f(x) 2.0](https://mixbytes.io/blog/modern-stablecoins-how-they-re-made-f-x-protocol-2-0)
  - [f(x) FAQ](https://fx.aladdin.club/v2/faq)
- Hastra:
  - [DefiLlama PRIME](https://defillama.com/rwa/asset/PRIME)
  - [Figure RWA consortium](https://www.barchart.com/story/news/36455614/figure-and-leading-crypto-partners-launch-rwa-consortium-for-onchain-finance-on-solana)
- infiniFi:
  - [Nansen](https://research.nansen.ai/articles/understanding-infini-fi-the-on-chain-fractional-reserve-banking-protocol)
  - [web3-ethereum-defi docs](https://web3-ethereum-defi.readthedocs.io/vaults/infinifi/index.html)
- Midas: [mGLOBAL on Aave Horizon](https://cfotech.co.uk/story/midas-launches-mglobal-as-collateral-on-aave-horizon)
- OnRe: [ONyc docs](https://docs.onre.finance/introduction/onre-tokenized-reinsurance-onyc)
- Ember Y10K: [Trading Strategy](https://tradingstrategy.ai/vaults/ember-y10k)
- Zama Confidential Vault: [docs](https://docs.zama.org/protocol/confidential-vault) (local copy `docs/external/docs.zama.org-protocol-docs/`), the app pages of [rockawayx-usdc-rwa](https://app.zama.org/earn/ethereum/0xc207d3f66537D7F66456808379A0E560cF20Da36/rockawayx-usdc-rwa) and [rockawayx-usdc-high-yield](https://app.zama.org/earn/ethereum/0xE0181090c22579B6A217f1522cbf8c9f1F0C1965/rockawayx-usdc-high-yield)
