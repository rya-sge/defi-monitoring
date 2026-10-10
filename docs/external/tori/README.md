# Tori Finance — external references

`docs.tori.finance-docs/` is a Markdown snapshot of the Tori Finance documentation (<https://docs.tori.finance>; pages last modified 21–22 September 2026): trUSD and strUSD, backing, peg, reserve fund, strategy, contracts, roles and timelocks, audits, risk disclosures and legal terms. 32 pages, each starting with `> Source: <url>` followed by a JSON-LD block that you can skip. The folder is **git-ignored** (`.gitignore` line 15), so it exists only in the local checkout. This README is tracked.

## Why it matters to riskdep

The RockawayX Morpho vaults hold about $18.9M of Tori collateral: strUSD, etrUSD, PT-trUSD-26NOV2026 and PT-strUSD-26NOV2026. The Upshift Tori Ecosystem Vault ($24.9M) also sits behind etrUSD. Every one of them comes down to trUSD, a delta-neutral synthetic dollar backed by off-chain custodians and trading venues. No market price reflects that backing: the oracles are RedStone "fundamental" feeds (trUSD is held at exactly 1.0). These docs are the issuer's own account of what stands behind the price, who can change the contracts, and how slowly money can get out. See `docs/analysis/ROCK-VAULT-DEP.md`.

## Tree

```
docs.tori.finance-docs/
├── index.md, _index.md, quickstart.md   # landing page, page index, swap/stake walkthrough
├── products/      # trusd.md, strusd.md: token facts, ERC-4626 rate, 7-day cooldown
├── solution/      # backing.md, peg-mechanism.md, reserve-fund.md
├── strategy/      # overview.md: money markets, futures basis, calendar spreads, risk limits
├── security/      # overview.md, roles.md (role matrix, 24 h timelock), audits.md
├── resources/     # contracts.md, risks.md, institutional*.md, pre-deposit.md (etrUSD), integrations, cores, ...
├── faq/           # general.md, security.md, trusd.md
└── legal/         # risk.md (long risk disclosure), trusd-terms.md, trusd-protocol.md, terms, privacy, cookies
```

## Main files

| Path | What | riskdep use |
|---|---|---|
| `docs.tori.finance-docs/resources/contracts.md` | Ethereum, Monad and Pharos addresses, CCIP pools, Timelock | Match the collateral addresses; the timelock address |
| `docs.tori.finance-docs/security/roles.md` | Role matrix: holder, custody and functions of each role | Admin surface, timelock question, what to watch |
| `docs.tori.finance-docs/products/strusd.md` | strUSD: ERC-4626, `totalAssets / totalShares`, 7-day cooldown | Exit delay, how the rate moves |
| `docs.tori.finance-docs/solution/backing.md` | Two custody layers, Accountable attestations | Off-chain dependency |
| `docs.tori.finance-docs/solution/peg-mechanism.md` | Arbitrage via KYC'd mint/redeem at NAV | Why the trUSD = 1.0 feed may be wrong |
| `docs.tori.finance-docs/solution/reserve-fund.md` | Buffer for extraordinary losses only | Loss waterfall |
| `docs.tori.finance-docs/strategy/overview.md` | Trading book and its controls | Source of losses |
| `docs.tori.finance-docs/resources/institutional.md` | Mint/redeem: KYC whitelist, 10 bps fee | Who can redeem |
| `docs.tori.finance-docs/resources/pre-deposit.md` | Tori Ecosystem Vault (etrUSD) on Upshift, curated by RockawayX | etrUSD lock-up and withdrawal delay |
| `docs.tori.finance-docs/resources/risks.md`, `legal/risk.md` | Risk disclosures | Scenario inputs |
| `docs.tori.finance-docs/security/audits.md` | Sherlock, Nethermind, bug bounty | Audit status |
| `docs.tori.finance-docs/faq/security.md` | Upgrades, custodians, pause | Custodians are not named |

## Read first for this project

Paths below are relative to `docs.tori.finance-docs/`.

**Backing & custody**
- `solution/backing.md`: there are two layers. On-chain assets are held in audited contracts. Off-chain assets are held "with qualified institutional custodians in segregated accounts". Reserves are "hedged positions", attested continuously by Accountable (`tori.accountable.capital`: AUM, composition, liability coverage ratio, reserve-fund status). NAV is published at `app.tori.finance/transparency`.
- `faq/security.md` (l. 90): "**We do not disclose the custodians** that hold the protocol's off-chain reserves". Collateral can move only to a custody address registered through the 24 h timelock.
- `security/roles.md`: Tori reaches "centrally-cleared liquidity venues". No venue is named anywhere in the docs.
- `resources/institutional-custody.md`: Anchorage Digital, BitGo and Cactus Custody are where **holders** can keep trUSD/strUSD. They are not the protocol's reserve custodians.

**Peg mechanism & mint/redeem**
- `resources/institutional.md`: mint and redeem are limited to KYC/AML-whitelisted participants, with a **10 bps** fee each way. Redemption pays out in USDC or USDT. Everyone else uses a market swap.
- `solution/peg-mechanism.md`: "The bound is redemption, not market depth". The peg holds only "as long as the protocol maintains its backing".
- `security/roles.md`: mint and redeem are capped per block, per asset and globally (`setMaxMintPerBlock`, `setMaxRedeemPerBlock`, set by the 3/5 Safe). The Gatekeeper role (MPC + an external party) can call `disableMintRedeem` in one transaction. The Minter and Redeemer roles are held by 3 EOAs, which can only submit EIP-712 orders that users signed.
- `legal/risk.md` §9.2: "Redemptions may be delayed during periods of market stress". `legal/trusd-terms.md` §14: Tori may "decline to process any purchase or repurchase request without prior notice".

**strUSD staking & cooldown**
- `products/strusd.md`: strUSD is an ERC-4626 vault with 18 decimals, upgradeable through a proxy. Staking is instant. Unstaking takes a **7-day cooldown** followed by a claim. The rate is `totalAssets / totalShares`.
- `faq/general.md` (l. 151): rewards can go negative. A loss "is reported on-chain through the same distribution path that pays rewards" (`reportLoss`, held by the Rewarder role: the Safe plus the Distributor contract `0xa0C4…D375`).

**Reserve fund**
- `solution/reserve-fund.md`: the fund is paid from part of the protocol's share of gross carry, plus seed capital. It is used only for "counterparty failures, extreme market dislocations, operational emergencies", not for normal drawdowns. **No size is given**: it is "finite, disclosed in the attestations". It is "not third-party insurance". `legal/risk.md` §14.2 says "There is no insurance fund or bailout mechanism".

**Strategy**
- `strategy/overview.md`: three strategies. Money markets ("usually our largest allocation"), futures basis (the worked example uses AAPL, so traditional-finance underlyings are included) and calendar spreads. Risk limits cover each asset, venue and strategy, plus VaR and circuit breakers. The disclosed risks are timing, capacity, execution and **counterparty default**. `legal/risk.md` (l. 233): "The failure of one or more major counterparties could result in significant losses to the trUSD Reserves".

**Contracts & addresses** (`resources/contracts.md`)
- trUSD `0xd0580192E98eA6CEB9c7b6191Ed2E27560911697` and strUSD `0x280839980a7eD0D7717F64125fE241012E5F5815` match riskdep's addresses.
- Minting `0xe16b…3F1E`, Distributor `0xa0C4…D375`, trUSD Silo `0xF7c0…60B4`, **Timelock `0xA952453E39F77108Ee37C1b92de593F1C59A6ef4`**.
- CCIP Lock & Release pools: trUSD `0x558d…96e2`, strUSD `0xb12E…c38B`. Monad and Pharos use Burn & Mint. Each lane is limited to 1,500,000 tokens, refilled over 6 h.
- **etrUSD `0x6f20…592d` is not listed**: these docs cover only the tokens Tori issues. etrUSD belongs to Upshift. `resources/pre-deposit.md` gives its terms: a $50M cap, USDC/USDT, then a soft lock-up with a **7-day withdrawal period** (the 30-day hard lock-up has ended). Nexus Mutual cover is available.

**Roles & timelocks** (`security/roles.md`)
- The **3-of-5 Safe** (Safe v1.4.1) is the Owner/Admin of trUSD, strUSD, Minting, Distributor and YT-Lock. It acts **without delay** on: role grants and revokes, `pause`/`unpause`, the per-block mint and redeem limits, removing collateral, and `removeCustodianAddress`.
- The **timelock** `0xA952…6ef4` (`getMinDelay` = **86,400 s = 24 h**) holds the "Timelock Admin" role. It gates `_authorizeUpgrade`, `addAllowedToken`/`enableAllowedToken`, `addCustodianAddress`, `setStablesDeltaLimit` and `setMinter`. The Safe is the Proposer. An MPC vault is the Executor and the Canceller.
- `resources/contracts.md`: this timelock **replaced `0x7af35ab3…` on 15 September 2026**. The admin role moved to it through the old timelock's own 24 h queue.
- Contradiction: `faq/security.md` (l. 67) says upgrades are "queued and executed by the 3-of-5 Safe", but the role matrix makes an MPC vault the Executor.

**Audits** (`security/audits.md`)
- Sherlock collaborative audit, 15–22 Jan 2026. Nethermind review (NM_0854), 24–26 Mar 2026. Both covered the full protocol and the "oracle integration". The bug bounty pays up to $1M. Hypernative monitors the contracts (`security/overview.md`).

**Oracles**
- RedStone is **not mentioned** anywhere. The only oracle text is generic: `legal/risk.md` §5.3, and the Nexus Mutual cover of "oracle risk".

**Risk disclosures**
- `resources/risks.md` (updated August 2026) covers strategy, smart contract, counterparty, peg, liquidity (7-day cooldown), regulatory and CCIP risks, with "No insurance" and "No guaranteed returns".
- `legal/risk.md` §14 (catastrophic loss, l. 493–524) says total loss is possible and "The Company has no obligation to make users whole".

## Gaps

- **Timelock vs riskdep**: the docs say a 24 h timelock (`0xA952…6ef4`) gates upgrades. `ROCK-VAULT-DEP.md` found "no timelock seen on-chain". It probably read only `owner()`, which is the Safe; the timelock is a separate role. To check on-chain, call `hasRole(<upgrade role>, 0xA952…)` on trUSD and strUSD, call `getMinDelay()` on the timelock, and confirm that the old `0x7af35ab3…` no longer holds a role. Even if the timelock is confirmed, the Safe can still pause and change limits with no delay.
- The off-chain custodians, the trading venues, the reserve-fund size and the NAV method are not in the docs; they exist only on the Accountable dashboard.
- The MPC thresholds (Executor, Canceller, Gatekeeper, Whitelister) are off-chain and not yet attested ("we intend to publish").
- There are no addresses for YT-Lock or for the Gatekeeper's external party.
- RedStone's `trUSD_FUNDAMENTAL` (fixed at 1.0) and `strUSD_FUNDAMENTAL`: the docs do not say what they read.
- The Upshift and etrUSD contracts and their LayerZero configuration are out of scope here. The RockawayX thesis is linked from `resources/integrations.md` but not mirrored.
