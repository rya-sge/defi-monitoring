# Midas — external references

`docs.midas.app-docs/` is a Markdown snapshot of the Midas documentation (https://docs.midas.app), 63 pages. Each page starts with its `> Source:` URL. It covers how mTokens are priced and how the NAV gets on chain, attestations, mint and redeem flows, the legal structure, the smart-contract registry, security, risk management, and per-product legal documents such as mROX. **The folder is git-ignored**: it exists only in the local checkout and a fresh clone does not have it. This README is tracked.

## Why it matters to riskdep

| riskdep exposure | Midas link | What to check here |
|---|---|---|
| Belem RWA EURCV vault (RockawayX for Belem Capital): about €4.5M EURCV lent against **mGLOeuro**, 77% LLTV, one borrower | Midas issues mGLOeuro (Midas Fasanara Global Euro). Its Morpho oracle reads `MGloEuroCustomAggregatorFeed` (`0x8b7b…9609`), a TransparentProxy | How the NAV is pushed and how often, the deviation and heartbeat checks, who can push or upgrade, and when redemptions pause |
| The mGLOeuro feed is administered: 100,000 EUR per token, 2 rounds since August, last update 17.5 days old | Midas pushes the NAV by transaction after co-signer review | The docs allow a cadence of "daily to weekly or longer", and NAV publication can pause |
| ProxyAdmin owned by `MidasTimelockController` (48 h); roles in `MidasAccessControl` | Midas upgrade timelock and role model | The docs confirm the 48 h delay and the role split, but give no address for the timelock or for AccessControl |
| mROX (RockawayX strategy on Midas, $3.4M) | Midas product with a legal page and registry entry | Issuer (Midas Software GmbH prospectus), token, oracle and vault addresses |

See `docs/analysis/ROCK-VAULT-DEP.md` (oracle table, admin table, concentration, exit routes, item 7 "Midas").

## Tree

```text
docs.midas.app-docs/
├── _index.md, index.md, welcome.md      # table of contents, "About Midas" landing page
├── welcome/                             # quick guide to investing (instant vs standard deposit)
├── transparency/                        # asset transparency, mToken pricing, oracle architecture, attestation engine
├── liquidity-and-composability/         # redemption methods, Midas Staked Liquidity (MSL), composability
├── investment-risk-management/          # strategy rules (manager guardrails), risk monitoring (1Token, stress tests)
├── legal/                               # legal structure (Lux securitisation vs German issuer), eligibility, risks
├── security/                            # security framework, smart-contract security, wallet/opsec, incident response
├── resources/                           # contract registry, audits, fees/definitions, official links, support
│   └── legal-product-documentation/     # one page per mToken: prospectus, final terms, financials (mROX here)
├── documents/issuer-documents/          # financial-crime policy, privacy policy
└── tools/                               # Midas native bridge
```

## Main files

| Path | What | riskdep use |
|---|---|---|
| `docs.midas.app-docs/transparency/oracle-architecture.md` | Three-step NAV pipeline: verification, Oracle Feed, Datafeed | Feed class `issuer-published (custom aggregator)`; deviation and heartbeat semantics |
| `docs.midas.app-docs/transparency/pricing-of-the-mtoken.md` | NAV formula, update cadence, Market Disruption Event | Staleness thresholds; why the price can stay flat |
| `docs.midas.app-docs/transparency/the-midas-attestation-engine.md` | PoR/NAV attestations (Chainlink CRE, LlamaRisk, Canary, vlayer) | Possible independent NAV check; not yet live for every token |
| `docs.midas.app-docs/resources/smart-contracts-registry.md` | Token, oracle, issuance and redemption addresses per mToken and chain | Cross-check the mGLOeuro and mROX addresses |
| `docs.midas.app-docs/security/smart-contract-security.md` | Midas Controller quorum, roles, pauses, 48 h timelock, daily state check | `admin.py` facts: who can upgrade, pause or mint |
| `docs.midas.app-docs/liquidity-and-composability.md` | Standard vs instant redemption, internal liquidity sleeve | Exit route and liquidation-collateral liquidity for mGLOeuro |
| `docs.midas.app-docs/legal/legal-structure.md` | Luxembourg securitisation vs Midas Software GmbH | Bankruptcy remoteness of the collateral |
| `docs.midas.app-docs/resources/legal-product-documentation/mrox.md` | mROX prospectus, final terms, issuer financials | mROX issuer and terms |

## Read first for this project

### mToken pricing & NAV oracle architecture
- `transparency/pricing-of-the-mtoken.md` § "The NAV Update Process": NAV = portfolio value ÷ mTokens outstanding. The cadence "can range from **daily to weekly or longer**, depending on the specific product". Strategy managers supply the valuation, and Midas deducts accrued fees and runs sanity checks.
- Same file, FAQ: if third-party reports arrive late, "NAV publication is paused". If no reliable NAV exists, a **"Market Disruption Event"** pauses the valuation date and redemptions. This fits mGLOeuro's flat 17.5-day-old value.
- Same file, § "Onchain Verification": each update is "reviewed by **at least two** trained co-signers".
- `transparency/oracle-architecture.md` § "The Oracle Feed": the feed stores the price with its timestamp and runs a **deviation check** against the previous price. A breach of the min/max bounds makes the update fail, and deposits and redemptions "may then be manually paused". "High-deviation updates can still be pushed onchain" through a higher-quorum process, so the deviation bound is not a hard cap on a markdown.
- Same file, § "The Datafeed Contract": the Datafeed (read by the minter and redeemer) checks the **heartbeat** (freshness) and **hardcoded min/max** limits, and reverts if either fails. riskdep should verify: the Morpho oracle reads the custom aggregator feed directly, so these Datafeed checks probably do not protect Morpho.
- Same file, § "Third-Party Oracles": payment tokens are priced by Chainlink or Pyth, with a stablecoin band of **0.997–1.003** that halts transactions when breached.
- `legal/investment-risks-1-0-1.md` § "Oracle Risk": NAV inputs "may be delayed or based on estimates".

### Asset transparency / attestations
- `transparency/asset-transparency.md`: the composition is shown at `midas.app/transparency?token=…` (allocations, protocol exposures, wallets).
- `transparency/the-midas-attestation-engine.md`: Attestation Engine at `0x2D6e9F608807436DE5D9603B00Abe3FEd1Bc809d`. The **POR Feed** notarises the risk manager's NAV email (vlayer), stores it on IPFS and publishes it through Chainlink CRE, and LlamaRisk and Canary verify it. Caveat: verification "does not yet apply to all mTokens" and "does **not** currently condition the onchain price update".

### Mint & redeem flows
- `welcome/quick-guide-to-investing.md`: in **Instant** deposit the mToken is minted at the current NAV. In **Standard** deposit it is minted at settlement, "typically at the next NAV update" (T+0 to T+X). A full instant capacity redirects deposits to standard mode.
- `liquidity-and-composability.md` § "Choosing Your Redemption Method": **standard** redemption is free and is processed after the next NAV update (FAQ: "usually T+2 to T+X"). **Instant** redemption depends on capacity and charges a fixed fee. § "Internal Liquidity Sleeve": up to **10% of TVL** may sit in USDC or mTBILL for some products.
- `resources/methodology-and-definitions.md` § "Fees": instant redemption fee "typically **20 to 100 bps**". Management fees accrue at each NAV update, and performance fees use a high-water mark.
- `liquidity-and-composability/midas-staked-liquidity-msl.md`: the MSL pool pays instant redemptions in USDC, and its loan "has **seniority** over any other investor in the mToken".
- `legal/eligibility-and-compliance.md`: no US persons, wallets are screened, KYC/AML and **professional whitelisting** apply to some strategies, and Midas can "pause an mToken for specific individual users". A Morpho liquidator may therefore be unable to redeem seized mGLOeuro.
- `security/smart-contract-security.md` § "On-Chain Transparency": readable views include `lastAnswer()`, `instantDailyLimit()`, `instantFee()`, `greenlistEnabled()`, `minFiatRedeemAmount()` and `paused()`.

### Legal structure & issuer
- `legal/legal-structure.md`: (1) a **Luxembourg securitisation** vehicle (law of 22 March 2004) with one compartment per product, statutory segregation, and an orphan structure owned by a charitable trust. (2) **Midas Software GmbH** (Germany), which gives contractual exposure only, "investors should not assume that assets are ring-fenced".
- `legal/investment-risks-1-0-1.md` § "Credit Risk": exposure to the issuer's credit, with possible **qualified subordination**. § "Duration & Liquidity Risk": instant redemption "may not be guaranteed".
- `investment-risk-management/strategy-rules.md`: managers trade inside a Midas MPC workspace with an approver quorum and a destination whitelist, and Midas can send "Emergency Instructions". (`investment-risk-management.md` is the same text.)

### Smart-contract registry & roles/access control
- `resources/smart-contracts-registry.md` § "mGLOeuro Smart Contracts" (Ethereum): token `0x2F8bae126b8d416C009b82Ccd60e4f9cAbbd7702`, **"mGLOeuro/USD Oracle"** `0x8B7B1689396ef4468df1c0faB181D29B47089609` (the same address as riskdep's feed, but labelled /USD while the feed reads 100,000 **EUR**), issuance vault `0xE0Dcf20b0460e1f9222528F3997F9D71Ad6375C5`, **Redemption Vault swapper** `0x1E9f04408FF38d1FB70CE939fC87D26D61F6F758`. The registry also has separate sections for mGLO and mGLOBAL. The page links a public upgrade tracker (Notion).
- `security/smart-contract-security.md` § "Midas Controller": `0x0312a9d1ff2372ddedcbb21e4b6389afc919ac4b`, a **1-of-3** quorum (Safe ≥4 signers with cold wallets, Fordefi MPC ≥4, Fireblocks MPC ≥4). § "Multisig/MPC Controls": oracle price updates need "typically **a minimum of three** independent approvers".
- Same file, § "Role-Based Access Control": Minter (deposit vault and OFT), Burner (redemption vault and OFT), Pauser (multisig), Token Management (manual OTC mint or burn).

### Security & incident response
- `security/smart-contract-security.md` § "Granular Pause Mechanisms": manual pauses only (deposits, instant redemption, standard redemption or all), a token-level transfer freeze, and a **48-hour** timelock on every upgrade. "Price updates and Oracle operations continue" during a pause. § "Smart Contract Integrity Verification": a state check runs at **00:00 UTC** each day, its CID goes to IPFS and on chain, and LlamaRisk and Canary re-check it. § "Bug Bounty": **$1M** pool, up to **$500k** for a critical (Sherlock, Cantina).
- `security/standard-incident-response-protocol.md`: triggers are a third-party vulnerability, unusual on-chain activity, or contagion. Subscriptions and redemptions pause, and status is posted on `midas.app/products` and `x.com/MidasRWA`.
- `resources/audits.md`: Sherlock (2024, 08/2025 Growth Oracle), Côme Du Crest (vaults, max supply, bridges), Halborn (Solana), Hacken (2023 legacy).

### Risk management
- `investment-risk-management/risk-monitoring.md`: 1Token PMS, market, depeg and protocol/counterparty risk classes, leverage and concentration limits, and credit, depeg and systemic stress scenarios. Limit breaches raise alerts before the NAV is published.

### Product page for mROX
- `resources/legal-product-documentation/mrox.md`: Midas Software GmbH **Base Prospectus 2026**, signed mROX Final Terms, and the issuer's 2025 financial statements (PDF links only). Its "strategy page" link points to `midas.app/mre7yield`, which looks like a copy-paste error.
- `resources/smart-contracts-registry.md` § "mROX Smart Contracts": Ethereum token `0x67E1F506B148d0Fc95a4E3fFb49068ceB6855c05`, oracle `0x7fF56C3a31476c231e74E4F64e9d9718572B54Aa`, issuance vault `0x511d88E64d843Ee11Bf039a3EB837393001aEDE7`, redemption vault `0xc33dAdA688f224c514682Ec6Ba940888d43C4b29`, and an OFT. It is also deployed on Monad.

## Gaps

| Missing | Why it matters | Where to get it |
|---|---|---|
| **No mGLOeuro (or mGLO) product page** in `resources/legal-product-documentation/` (only the registry entry) | We cannot see the issuer vehicle, NAV cadence, deviation bounds, redemption terms or Market Disruption Event clause for mGLOeuro | midas.app/mgloeuro page, mGLOeuro final terms or pricing supplement |
| Fasanara fund documents (the underlying fund's NAV policy, administrator, liquidity) | The value of mGLOeuro is the Fasanara NAV | Fasanara or Midas offering documents |
| Addresses of `MidasAccessControl`, `MidasTimelockController` and ProxyAdmin, and the holders of each role | The docs describe the roles and the 48 h delay without addresses | On chain via Etherscan; `midas-apps` GitHub |
| Contracts source (`CustomAggregatorFeed` deviation and min/max values, `DataFeed` heartbeat) | The real bounds for each feed | `github.com/midas-apps` (`resources/official-links.md`) |
| Audit PDFs and the mROX prospectus | Linked only, not downloaded | URLs in `resources/audits.md`, `resources/legal-product-documentation/mrox.md` |
