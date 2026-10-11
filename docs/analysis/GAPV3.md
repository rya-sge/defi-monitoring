# GAPV3: the RockawayX vaults not analysed yet, and the protocols they add

`ROCK-VAULT.md` lists 33 RockawayX vaults (293.6M USD). riskdep analyses 7 of them: the Morpho Vault V2 vaults on Ethereum in the book `examples/rockawayx-ethereum.json` (99.1M USD). This file triages the other 26: whether each should be analysed, what it would add, what it would take, and which new protocols come with them. It complements `GAPV2.md`, which is about the model; this one is about coverage.

The 8 vaults the Dune page did not show at first were added to `ROCK-VAULT.md` §2 on 2026-10-11 (rows 26–33). The 5 of them that are Morpho vaults on Ethereum were read from the Morpho API the same day (`ROCK-VAULT.md` §3).

## How the vaults are triaged

Four questions, in this order:

1. **Can riskdep read it today?** Morpho Vault V2 on Ethereum: yes. Morpho on another chain: once the chain is a parameter (`GAPV2.md` G8). Another venue on Ethereum: a new reader. Another venue on another chain (Kamino on Solana, Lista on BSC): out of scope.
2. **How much money is at risk?** At the current allocation, and at the caps, since an allocator can fill the caps at once (`GAPV2.md` G1).
3. **Does it add a dependency the book does not have?** A new issuer, a new kind of oracle, a new venue. The brief scores discovery at 30 %, and its scope examples include "vaults deploying into an external venue" and "protocols concentrating a large share of TVL".
4. **Does it change a figure the judges see?** A vault whose loss rolls up into the RockawayX book changes the headline numbers.

## Summary

| Order | Vault | Venue, chain | Size | New dependency | Readable today | Recommendation |
|---|---|---|---|---|---|---|
| 1 | RockawayX wETH | Morpho V2, Ethereum | $2.1k | **ETH+ (Reserve)**, weETH (ether.fi) | yes | Add to the book; analyse the ETH+ market and its oracle |
| 2 | RockawayX EUROP | Morpho V2, Ethereum | $11.2k | **EURØP (Schuman Financial) as the loan asset**, weETH | yes | Add to the book; model the loan asset's depeg |
| 3 | Midas USDC Prime (Ethereum), RockawayX USDC Prime, Figure USDC Main | Morpho V2, Ethereum | $3.5k, $10, $11 | none (blue chips, Hastra's PRIME) | yes | Add to the book; record once for the caps |
| 4 | Tori Ecosystem Vault | Upshift, Ethereum | $24.9M | Upshift's vault and its strategies | no: a new reader | Analyse: same issuer as 19 % of the Morpho book, an external venue |
| 5 | mROX | Midas, Ethereum | $3.4M | Midas's issuance contracts; RockawayX's own market-neutral book | no: a new reader | Analyse with the Midas work (`GAPV2.md` G11, G14) |
| 6 | Y10K | Ember, Ethereum | $17.8M | Ember's multi-strategy vault | no: a new reader | Analyse after Upshift: larger, but no overlap with the book's issuers known yet |
| 7 | OnRe Core Vault | Accountable, Ethereum | $3.5M | OnRe reinsurance, Accountable's attestations | no: a new reader | Later: reinsurance is already a dependency through Re's reUSD |
| 8 | Midas USDC Prime (Base) | Morpho V2, Base | $0.6M | none (cbETH, cbBTC, WETH) | after G8 | Later, with other chains |
| 9 | Kamino vaults (RWA USDC, Huma PST, SOL, Raiku, Marinade, Obligate, Huma USDC, Huma USDS, Raiku SOL) | Kamino, Solana | $122.1M | Kamino's markets; Huma PST on Solana | no | Out of scope for a reader; count the Huma exposure at issuer level (see below) |
| 10 | Feather PYUSD0, RockawayX USDC (Oku), RockawayX YIELD PT (Lista), Earn ctUSD | Sei, Pharos, BSC, Citrea | $12.4M, $11.2M, $1.3M, $0.05M | other chains and venues | no | Out of scope |
| — | Y10K AUSD Vault | Morpho, Monad | $0 | AUSD (Agora) | no | Skip while empty |

## 1. The five Morpho vaults on Ethereum found later

All five are Vault V2 with one `MorphoMarketV1` adapter, owned and curated by the same address as the seven analysed (`0xbBacDCFB…f918`), and none is a Zama confidential vault. Together they hold about $17k. riskdep reads them with no new code.

**Why add them anyway.** Their size today says little: an allocator can fill each market up to its caps at once, and the caps were not read. The book's headline and the "at the caps" figures are only complete with every vault the curator runs. Adding them costs one recording per vault (graph and incident) and five lines in `examples/rockawayx-ethereum.json`.

### RockawayX wETH ($2.1k)

| Market | LLTV | Vault's supply | Market size | Utilisation |
|---|---|---|---|---|
| ETH+ / WETH | 94.5 % | $2.1k: the only lender | $2.1k | 99 % |
| wstETH / WETH | 96.5 % | $0, enabled | $86.9M | 83 % |
| weETH / WETH | 94.5 % | $0, enabled | $14.8M | 81 % |
| WBTC / WETH | 91.5 % | $0, enabled | $0.2M | 71 % |

The ETH+ market is the vault's own: it is the only lender, 99 % is borrowed, and the LLTV is 94.5 %, so borrowers have little room before liquidation and the vault has almost no free liquidity to withdraw from. ETH+ is Reserve Protocol's basket of liquid-staking tokens: a new issuer for the book, with its own oracle (`0x0705…`) to classify.

### RockawayX EUROP ($11.2k)

The loan asset is **EURØP** (`0x8888…5E51`), Schuman Financial's euro stablecoin. Its four markets (wstETH, cbBTC, weETH, WBTC, all at 86 % LLTV) each hold about $2.8k, the vault is their only lender, and nothing is borrowed.

What is new is the side of the risk: in every other RockawayX vault the depositor lends USDC or EURCV against risky collateral, and the issuer risk sits in the collateral. Here the depositor holds EURØP itself, so a depeg of EURØP is a direct loss to the depositor, before any market is involved. riskdep's incidents shock collateral, not the loan asset; that is the gap this vault exposes (see §4).

### Midas USDC Prime (Ethereum), RockawayX USDC Prime, Figure USDC Main

Blue-chip markets (wstETH, cbBTC, WBTC) at 86 % LLTV, the same large markets the NUVA vault already uses, plus Hastra's PRIME for Figure USDC Main, already analysed in the USDC Yield vault. Nothing new to discover; add them for completeness and for their caps.

## 2. Vaults on other venues on Ethereum

These are where the money is: 49.6M USD across four vaults, on venues riskdep does not read.

**Tori Ecosystem Vault (Upshift, $24.9M).** The highest priority. Tori is already 19 % of the Morpho book (strUSD, etrUSD, PT-trUSD), so this vault adds the same issuer through a second venue, which is the cross-venue concentration the brief asks about. etrUSD, collateral in two RockawayX Morpho vaults, is a share of this very vault, so its oracle's value depends on what this vault holds. And Tori's strategy runs on trading venues and custodians, the brief's "vault deploying into an external venue". What it takes: a reader for Upshift's vault (its strategies and their allocations, its share price, its withdrawal path), drawn behind etrUSD in the graph, and Tori's venues where Tori publishes them, as Ethena's are.

**mROX (Midas, $3.4M).** RockawayX's own market-neutral strategy, issued by Midas, which already backs the Belem vault. Its positions sit on Morpho, Curve and Pendle (`ROCK-VAULT-DEP.md`), protocols riskdep reads. What it takes: Midas's issuance and redemption contracts (shared with the Midas exit work, `GAPV2.md` G14), then the strategy's own positions, read as a borrower's.

**Y10K (Ember, $17.8M).** A multi-strategy vault. Its strategies are not documented here; a first step is to read where it allocates and whether it overlaps the book's issuers.

**OnRe Core Vault (Accountable, $3.5M).** Reinsurance, attested by Accountable. The book already depends on reinsurance through Re's reUSD; OnRe would add a second reinsurance issuer, with off-chain risk that the chain does not show.

## 3. Vaults out of scope, and the one dependency to keep

The Kamino vaults on Solana hold 122.1M USD, 42 % of RockawayX's total; Feather (Sei), Oku (Pharos), Lista (BSC) and Upshift's Citrea vault add 25M more. riskdep reads EVM chains only, and a Solana reader is a separate project.

One dependency should still be counted: **Huma PST**. It backs the Kamino Huma PST vault ($42.5M) and part of the Kamino RWA USDC vault, on top of 34.7M USD on Morpho. Huma is about 28 % of RockawayX's total, above the curator's own 25 % single-protocol limit. Without reading Kamino, the book can carry the Kamino exposure as a stated off-chain line per issuer (amount, source, date), so that the PST incident reports the firm-wide loss next to the Morpho one, clearly labelled as not read on-chain.

## 4. New protocols to analyse

| Protocol | Where it appears | What to analyse | Priority |
|---|---|---|---|
| **Reserve, ETH+** | RockawayX wETH: a 94.5 % LLTV market at 99 % utilisation, the vault its only lender | The basket's composition (liquid-staking tokens), its redemption, its oracle's class and kind, the RToken's admin and its timelock | 1 |
| **Schuman Financial, EURØP** | RockawayX EUROP's loan asset | A depeg of the loan asset: a direct loss to the depositor. riskdep needs a `loan=` incident (the vault's own asset marked down), and EURØP's backing and redemption as a regulated e-money token | 2 |
| **Upshift** (Tori Ecosystem Vault) | $24.9M; behind etrUSD | The vault's strategies, allocations and withdrawal path; Tori's venues | 3 |
| **Midas mROX** | $3.4M | Issuance and redemption, then the strategy's positions on Morpho, Curve and Pendle | 4 |
| **ether.fi, weETH** | Enabled in RockawayX wETH and EUROP, $0 today | A liquid-restaking token: the restaking layer behind ETH, its withdrawal queue, its oracle; a registry issuer entry next to wstETH | 5 |
| **Ember** (Y10K) | $17.8M | Its strategies first | 6 |
| **Accountable / OnRe** | $3.5M | Reinsurance attestations; comparison with Re | 7 |
| **Agora, AUSD** | The empty Monad vault; already a sibling market (PST/AUSD) in the PST incident | Nothing new until the Monad vault holds money | — |

## What to build first

1. **Add the five Ethereum vaults to the book and record them.** No code: one recording each and five lines in the book file. The book then covers every Morpho vault RockawayX runs on Ethereum, and their caps enter the "at the caps" figures.
2. **ETH+**: classify its oracle and add Reserve as an issuer. It is the only new market where the vault is the sole lender at 99 % utilisation and a high LLTV.
3. **A `loan=` incident for EURØP**: the first vault where the depositor's own asset is the issuer risk. Small in code (a markdown of the vault's asset applied to the depositor's position), large in what it shows.
4. **The off-chain Kamino line for Huma**, so the PST incident states the firm-wide loss.
5. **Upshift's Tori vault**: the largest Ethereum vault outside Morpho, and the same issuer as a fifth of the Morpho book.
6. **mROX**, with the Midas exit work; then Ember and OnRe.

Out of scope until a non-EVM reader exists: Kamino, Feather, Oku, Lista and Citrea.
