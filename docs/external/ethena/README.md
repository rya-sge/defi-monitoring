# Ethena — external references

`docs.ethena.fi-docs/` holds the Ethena documentation (USDe and sUSDe) scraped from <https://docs.ethena.fi> as 86 Markdown pages, one per GitBook page, each starting with a `> Source:` line pointing to the live URL. `_index.md` is the table of contents. The folder is **git-ignored** like the other doc folders under `docs/external/`: it exists only in the local checkout, so a fresh clone does not have it. Read-only: check a registry value or a rule against these pages before changing it.

## Why it matters to riskdep

| riskdep element | Ethena dependency |
|---|---|
| Demo position | PT-sUSDE-26NOV2026 collateral on Morpho against USDC: the PT redeems into sUSDe at maturity |
| `riskdep/registry.json` issuers | `0x9d39a5de…` sUSDe and `0x4c9edd58…` USDe (both `issuer: Ethena`, `category: Basis Trading`, `kind: synthetic-dollar`): depeg prior 12 %/yr, Beta(1.6, 18) severity, 75 % recovery; hack severity Beta(1.2, 3.0) "loss of a custodian or CEX holding hedges" |
| Oracle backup | The demo `MetaOracleDeviationTimelock` backup reads `USDe / USD` (`docs/how-risk-is-computed.md`) |
| Look-through (GAP K19/M7, EXTERNAL_SOURCE) | Discovery stops at the issuer; USDe's hedges, custodians and backing are not in the graph |
| Other positions | Re's reUSD buffer holds USDe/sUSDe (RockawayX PT-reUSD exposure $13.3M); infiniFi deploys to Ethena |

## Tree

```
docs.ethena.fi-docs/
├── _index.md, index.md, *.md          # TOC, landing page, one overview page per section
├── overview/                           # how USDe works, off-exchange custody, ENA, USDtb, whitelabel
│   └── ena/                            # ENA tokenomics
├── backing-assets/                     # backing categories (basis trade, lending, RWA, liquid stables)
│   └── crypto-basis-trade/             # delta-neutral examples and stability
├── backing-custody-and-security/       # OES custody, dashboards
│   └── overview/                       # OES in detail, Copper Clearloop case study
├── protocol-overview/                  # reserve fund, peg arbitrage, rewards, scenario analysis
│   ├── risks/                          # funding, liquidation, custodial, exchange, backing, stablecoin, margin
│   ├── governance/                     # risk committee
│   └── underlying-derivatives/         # basis, futures vs perps, inverse vs linear
├── technical-design/                   # key addresses, oracles, hedging, minting, staking
│   ├── hedging-system/                 # internal services, dependency risk
│   ├── key-trust-assumptions/          # multisig and timelock matrix
│   ├── minting-usde/                   # mint/redeem contract V2, key functions, order checks
│   ├── overview/                       # GitHub/contracts overview (roles, cooldown, blacklist)
│   └── staking-usde/                   # StakedUSDe key functions, security measures
├── api-documentation/                  # mint/redeem RFQ API (whitelisted)
├── resources/                          # audits, attestations, FAQ, risk disclosures, legal T&Cs
└── video-guides/                       # buy/stake USDe, stake ENA, unlock
```

## Main files

| Path | What | riskdep use |
|---|---|---|
| [technical-design/key-addresses.md](docs.ethena.fi-docs/technical-design/key-addresses.md) | Mainnet addresses: USDe, sUSDe, Mint & Redeem V1/V2, Reserve Fund, multisigs, Curve/Uniswap pools | Check registry issuer keys; reserve-fund address for a balance read |
| [protocol-overview/risks.md](docs.ethena.fi-docs/protocol-overview/risks.md) + `risks/*.md` | Ethena's own risk taxonomy (7 risks) | Basis for depeg/hack priors and the look-through layers |
| [overview/off-exchange-custody.md](docs.ethena.fi-docs/overview/off-exchange-custody.md) | OES model, current custodian list | Custodian dependencies in `registry.json` |
| [protocol-overview/reserve-fund.md](docs.ethena.fi-docs/protocol-overview/reserve-fund.md) | Reserve fund role and funding | First-loss buffer cited in the hack basis |
| [technical-design/staking-usde/staking-key-functions.md](docs.ethena.fi-docs/technical-design/staking-usde/staking-key-functions.md) | StakedUSDe roles, cooldown, blacklist, redistribution | sUSDe exit time and seizure risk |
| [technical-design/key-trust-assumptions.md](docs.ethena.fi-docs/technical-design/key-trust-assumptions.md) | Privileged roles, multisig, timelocks | Admin-key layer |
| [technical-design/minting-usde/mint-and-redeem-contract-v2.md](docs.ethena.fi-docs/technical-design/minting-usde/mint-and-redeem-contract-v2.md) | Per-block limits, whitelist, stable delta limit | Redemption capacity (peg defence) |
| [resources/audits.md](docs.ethena.fi-docs/resources/audits.md) | Audit programme and reports | Code-risk evidence for the Ethena exploit prior |

## Read first for this project

**USDe backing & delta-neutral hedge**
- [backing-assets/overview.md](docs.ethena.fi-docs/backing-assets/overview.md): volatile assets "paired with a corresponding short derivatives position so that the combined position is delta-neutral"; backing now diversifying into non-crypto basis, DeFi/institutional lending, RWA, liquid stablecoins; allocation set by the Risk Committee and published on the Transparency dashboard (no numbers in the page).
- [protocol-overview/risks/liquidation-risk.md](docs.ethena.fi-docs/protocol-overview/risks/liquidation-risk.md): "6% ETH LST's and 7% liquid stables as of January 2025"; stETH/ETH spread "would have to diverge to 65%" before incremental liquidation; historic max 8 % (pre-Shapella).
- [protocol-overview/scenario-analysis.md](docs.ethena.fi-docs/protocol-overview/scenario-analysis.md): unrealised PnL in BTC/USDT on inverse vs linear contracts; a BTC rise needs settlement-currency (USDT) balance or exchange borrowing.

**Custody (off-exchange settlement)**
- [overview/off-exchange-custody.md](docs.ethena.fi-docs/overview/off-exchange-custody.md): custodians "Copper, Ceffu, Kraken and Anchorage Digital"; the exchange gets delegated margin but "cannot withdraw the underlying assets"; PnL settled "generally daily"; attestations "at minimum monthly".
- [protocol-overview/risks/custodial-risk.md](docs.ethena.fi-docs/protocol-overview/risks/custodial-risk.md): three risks (accessibility, operational duties, custodian failure); "Copper's Clearloop settles PnL between exchange partners and Ethena daily".
- [protocol-overview/risks/exchange-failure-risk.md](docs.ethena.fi-docs/protocol-overview/risks/exchange-failure-risk.md): hedges on Binance, Bybit, Bitget, Deribit, OKX; exposure to a failed exchange limited to "outstanding PnL between ... settlement cycles".
- [backing-custody-and-security/real-time-dashboards.md](docs.ethena.fi-docs/backing-custody-and-security/real-time-dashboards.md): Copper and Ceffu are omnibus, so on-chain deposit addresses do not show the protocol's holdings.

**Reserve fund (size)**
- [protocol-overview/reserve-fund.md](docs.ethena.fi-docs/protocol-overview/reserve-fund.md): revenue share to the fund "currently 0%"; absorbs negative revenue and "shortfalls in backing"; size only on the Transparency dashboard (no figure in the docs).
- [technical-design/key-addresses.md](docs.ethena.fi-docs/technical-design/key-addresses.md): Reserve Fund `0x2b5ab59163a6e93b4486f6055d33ca4a115dd4d5`, "4/10 signers"; sUSDe Payout Fund `0x71e4…3a87`, 3/11.

**Mint & redeem (whitelisted, limits)**
- [technical-design/minting-usde.md](docs.ethena.fi-docs/technical-design/minting-usde.md): RFQ from the Pricing API, signed EIP-712 order; "Ethena does have the ability to reject an order".
- [protocol-overview/peg-arbitrage-mechanism.md](docs.ethena.fi-docs/protocol-overview/peg-arbitrage-mechanism.md): mint/redeem only by "authorized, whitelisted users"; "about 0.50% of backing assets" held as stablecoins in the minting contract, replenished from "4% of the backing assets" in stablecoins.
- [technical-design/minting-usde/mint-and-redeem-contract-v2.md](docs.ethena.fi-docs/technical-design/minting-usde/mint-and-redeem-contract-v2.md): per-asset and global max-per-block limits "measured in USDe terms"; stable/USDe delta limit in bps; V2 at `0xe3490297…62D3`.
- [technical-design/minting-usde/order-validity-checks.md](docs.ethena.fi-docs/technical-design/minting-usde/order-validity-checks.md): "$N per block limit check"; one mint/redeem request per user per block. No limit values are published.

**sUSDe staking & cooldown**
- [technical-design/staking-usde.md](docs.ethena.fi-docs/technical-design/staking-usde.md): ERC-4626; rewards paid "every 8 hours and linearly vest over 8 hours"; sUSDe value "can only increase or stay flat"; on unstake USDe sits in USDeSilo `0x7FC7…3425`; sUSDe not offered to EU/EEA residents.
- [technical-design/overview/github-overview.md](docs.ethena.fi-docs/technical-design/overview/github-overview.md): "14 day cooldown period on unstaking sUSDe ... configurable up to 90 days".
- [technical-design/staking-usde/staking-key-functions.md](docs.ethena.fi-docs/technical-design/staking-usde/staking-key-functions.md): `setCooldownDuration` "up to a maximum value of 90 days".

**Funding-rate risk & negative funding**
- [protocol-overview/risks/funding-risk.md](docs.ethena.fi-docs/protocol-overview/risks/funding-risk.md): BTC/ETH funding averaged "7.8% - 9%" annualised over 3 years; negative days 17.5 % (ETH) and 15.9 % (BTC); with staking yield "only 8.84% of days" net negative; longest negative streak "13 days", longest positive "176 days"; reserve fund steps in, "Ethena does not pass on any 'negative revenue'" to sUSDe; data "as of 31st December 2024".
- [protocol-overview/rewards-mechanism.md](docs.ethena.fi-docs/protocol-overview/rewards-mechanism.md): how revenue flows to sUSDe.

**Depeg history**
- Not documented. [protocol-overview/peg-arbitrage-mechanism.md](docs.ethena.fi-docs/protocol-overview/peg-arbitrage-mechanism.md) only gives a hypothetical (buy at 0.95 on Curve, redeem at 1.00). The registry's events (Binance ~0.65 on 2025-10-10, ~0.3 % dip in Apr-2024) come from outside sources (GAP.md).

**Oracles / price**
- [technical-design/use-of-oracles.md](docs.ethena.fi-docs/technical-design/use-of-oracles.md): prices from CeFi exchanges (Binance, Bybit, OKX, Deribit, Bitmex, Bitget), Pyth and Redstone, all off-chain for mint/redeem pricing. Nothing on the on-chain USDe/USD feeds lending markets use.
- [technical-design/key-trust-assumptions.md](docs.ethena.fi-docs/technical-design/key-trust-assumptions.md): `MINTER_ROLE` mints "within 5% of 3rd party oracle pricing provided by Pyth and Redstone".

**Roles / blacklist (liquidators seizing sUSDe)**
- [technical-design/overview/github-overview.md](docs.ethena.fi-docs/technical-design/overview/github-overview.md): `SOFT_RESTRICTED_STAKER_ROLE` (e.g. USA) cannot stake or unstake; `FULL_RESTRICTED_STAKER_ROLE` "cannot move sUSDe" and Ethena "has the ability to repossess funds"; "no restrictions or ability to freeze funds of USDe".
- [technical-design/staking-usde/staking-key-functions.md](docs.ethena.fi-docs/technical-design/staking-usde/staking-key-functions.md): "Fully Restricted Stakers cannot receive sUSDe"; admin can redistribute locked sUSDe.
- Consequence: a liquidator who redeems seized PT into sUSDe must not be fully restricted, and a soft-restricted one cannot unstake (must sell on secondary markets, which Ethena does not "procure or facilitate").
- [technical-design/key-trust-assumptions.md](docs.ethena.fi-docs/technical-design/key-trust-assumptions.md) and [matrix-of-multisig-and-timelocks.md](docs.ethena.fi-docs/technical-design/key-trust-assumptions/matrix-of-multisig-and-timelocks.md): admin multisig "requires 7 signatures"; "7 day time-locks" on core functions; ≥3 gatekeeper EOAs can only disable mint/redeem; 20 minter/redeemer EOAs.

**Risks page**
- [protocol-overview/risks.md](docs.ethena.fi-docs/protocol-overview/risks.md): funding, liquidation, custodial, exchange failure, backing assets, stablecoin-related, margin collateral (one page each under `risks/`).
- [resources/general-risk-disclosures.md](docs.ethena.fi-docs/resources/general-risk-disclosures.md): legal risk disclosures.

**Audits**
- [resources/audits.md](docs.ethena.fi-docs/resources/audits.md): v1 by Zellic, Quantstamp (18 Oct 2023), Spearbit/Cantina (18 Oct 2023), Pashov (22 Oct 2023), Code4rena (13 Nov 2023), "No critical or high level issues"; Pashov V2 (23 May 2024); Chaos Labs LST market-risk analysis; Immunefi bounty "upcoming". Reports are linked PDFs, not in the folder.

## Gaps

| Gap | Effect on riskdep |
|---|---|
| No reserve fund size, backing composition or per-block mint limits (all on dashboards/contracts) | Read on-chain (`0x2b5a…d4d5` balances, `maxMintPerBlock`, `cooldownDuration()`) or via DefiLlama; not from the docs |
| No depeg history (Apr-2024, 2025-10-10 Binance print) | Registry depeg basis relies on GAP.md sources |
| Cooldown stated only as "14 day" in an old contracts page | Live value must be read from sUSDe `cooldownDuration()` |
| Custodian lists disagree: Copper/Ceffu/Kraken/Anchorage (`overview/off-exchange-custody.md`) vs Copper/Ceffu/Fireblocks (`backing-custody-and-security/overview.md`); none names Cobo | `registry.json` lists "Copper, Ceffu, Cobo": update it |
| Funding data stops at 31 Dec 2024 | Funding-risk prior needs a newer source (Chaos Labs backtest in GAP.md) |
| No on-chain USDe/USD oracle description | Oracle layer must come from Chainlink/Morpho docs |
| GAP.md links `docs.ethena.fi/solution-overview/risks`; the page now lives at `protocol-overview/risks` | Fix the link in GAP.md |
| Audit PDFs and dashboards are external links only | Fetch separately if needed |
