# Next steps

Where the project goes next, in recommended order, and what each step needs. It continues the gap list of `ANALYSIS_MONITORING.md` §5 (the gap ids, such as D5 or C2, are those of that list) and the architecture described in `ARCHITECTURE.md`.

**Where the project stands.** The tool analyses a Pendle PT position on Morpho Blue (`analyze`), watches a Morpho Vault V2 or every Morpho position of an address block by block (`watch`), and draws the dependency graph (`graph`). The watches follow every borrower of the watched markets, the main lenders of borrowed markets and the vault timelocks. All data comes from free public sources, and 83 offline tests cover the rules and three recorded real ranges. The main limits are that alerts stay in the terminal, `analyze` supports only PT collateral, the tool never acts, and it runs on Ethereum mainnet only.

Each step below gives its goal, what it delivers, its size (**S** about a day, **M** a few days, **L** more), the decisions it needs, and what it needs as input: what is **already available**, and what is **needed from you**.

## Contents

- [Summary](#summary)
- [0. Validate what exists](#0-validate-what-exists)
- [1. Push alerts](#1-push-alerts)
- [2. `analyze` for any collateral](#2-analyze-for-any-collateral)
- [3. Watch the admins of oracles, Morpho Blue and collateral issuers](#3-watch-the-admins-of-oracles-morpho-blue-and-collateral-issuers)
- [4. Complete the position coverage](#4-complete-the-position-coverage)
- [5. Tests on a forked chain](#5-tests-on-a-forked-chain)
- [6. Reliable infrastructure](#6-reliable-infrastructure)
- [7. Other chains](#7-other-chains)
- [8. A better risk model](#8-a-better-risk-model)
- [9. Execution](#9-execution)
- [10. Housekeeping](#10-housekeeping)
- [What is already available](#what-is-already-available)
- [What I need from you](#what-i-need-from-you)

## Summary

| # | Step | Gap ids | Value | Size | Blocked on |
|---|---|---|---|---|---|
| 0 | Validate the current tool on your own positions | — | high | — | your addresses and feedback |
| 1 | Push alerts, no repeats after a restart | D5, D4 | high | S | a channel and its credentials |
| 2 | `analyze` for any collateral, with a generic exit quote | C2, M3, M7 | high | M | which collateral to support; a quote source |
| 3 | ~~Watch oracle, Blue owner and issuer admins~~ **done** without sources or key; refining it needs the sources | G3, G4 | — | — | for the refinement: oracle and issuer contract sources |
| 4 | Direct Blue supply, Vault V1, other adapters | C3, C4 | medium | M | nothing blocking |
| 5 | Tests on a forked chain with a forced liquidation | T1 | medium | M | an archive RPC |
| 6 | Archive RPC, backfill, WebSocket trigger, deeper reorgs | D1, D3 | medium | S–M | an RPC provider key |
| 7 | Other chains where Morpho is deployed | C5 | medium | M | which chains; an RPC per chain |
| 8 | Correlated failures, portfolio view, refined priors | M2, M6, M1 | medium | M–L | your risk policy |
| 9 | Execution: de-lever or exit through Morpho Bundles | X1 | high, risky | L | a security design and your signing setup |
| 10 | CI, cleanup, versioning | T2, T4 | low | S | GitHub repository settings |

## 0. Validate what exists

**Goal.** Every plan ends with a check by you, and none is ticked yet. Running the tool on positions you actually hold is the fastest way to learn whether alerts are too noisy, missing, or unclear.

**Delivers.** A list of corrections (thresholds, wording, missing alerts), recorded in the plans' decision tables.

**Needs from you.**
- The address or addresses you want to watch, and the vaults you deposit in.
- Twenty minutes with `watch --user <address>` and `analyze` on a position, and your reaction to the output: what you would act on, what you would ignore.

## 1. Push alerts

**Goal.** Warn and critical alerts reach you when you are not looking at the terminal. Today they stay in the terminal and the JSONL file.

**Delivers.** A notifier behind the existing alert printer, configured by environment variables; a deduplication store so a standing alert is not resent after each restart (gap D4); a test mode that sends one sample alert.

**Size.** S.

**Decisions.**
- Channel: Telegram bot, Slack or Discord webhook, ntfy.sh (no account), or email.
- Levels pushed: critical only, or warn and critical; a quiet period for info.
- Grouping: one message per alert, or one digest per batch.

**Needs from you.**
- The chosen channel's credentials, passed as environment variables and never committed: a Telegram bot token and chat id, a webhook URL, an ntfy topic, or SMTP settings.

**Already available.** The alert objects carry everything a message needs (level, title, detail, transaction, your impact).

## 2. `analyze` for any collateral

**Goal.** Today `analyze` refuses any collateral that is not a Pendle PT. Most Morpho borrows use other collateral (the demo address has sUSDS and PST borrows).

**Delivers.**
- The layer model for a plain collateral token (no Pendle pool): issuer, oracle, market, chain.
- A generic exit quote for any token.
- New `registry.json` entries for the yield sources found in your positions.

**Size.** M.

**Decisions.**
- Which collateral types to support first: liquid staking tokens, yield-bearing dollars, real-world-asset tokens, BTC wrappers.
- The quote source. No keyless aggregator has been verified yet: it needs probing, or an API key.

**Needs from you.**
- The list of collateral tokens you care about, so their issuers can be added to the registry with a sourced basis (depeg history, backing, admin powers).
- For each issuer without public data, its documentation or transparency page (reserves, redemption process).
- An aggregator API key if the keyless options turn out to be unreliable (for example a 0x or 1inch key).

**Already available.** The PT path, the propagation model and the verdict logic are generic; only discovery and the exit quote are PT-specific.

## 3. Watch the admins of oracles, Morpho Blue and collateral issuers

> **Done** (plan `plan/2026-10-10-admin-surface.plan.md`), without any API key or contract source. Both watches discover the admin surface of their markets and read standard storage slots, owners and Chainlink aggregators. They alert on upgrades, admin and owner changes, feed changes, pauses, admin roles, outsized mints of collateral and yield tokens, Morpho Blue owner actions, and oracle divergence from DefiLlama's price. **What remains**, and still needs the sources and the Etherscan key below: decoding *custom* admin functions that emit no standard event (today seen only when they change a slot, an owner or an aggregator, at the next 300-block refresh), and checking that new implementations are verified.

**Goal.** A position can be broken by someone other than the vault curator: an oracle's owner changing a feed, an upgradeable collateral token being upgraded, an issuer minting without backing (the USR incident of March 2026). Today none of these is watched (gaps G3, and G4 for the oracle against an independent price).

**Delivers.**
- For each watched market, the oracle's configuration and any admin or upgrade path (EIP-1967 proxy slots, owner, feed setters), watched by event and by storage read.
- The collateral token's proxy admin and implementation, and its mint and pause roles.
- An alert when the oracle diverges from an independent market price.

**Size.** M.

**Decisions.** Which admin actions are critical (implementation upgrade, feed change) and which are warn (pause, role change).

**Needs from you.**
- **Smart-contract sources** of the oracles behind your markets. Morpho's standard oracles are public (`morpho-org/morpho-blue-oracles`), but the demo market's oracle is a minimal proxy whose implementation has no verified source on Sourcify (Etherscan was not checked, as it needs a key): its source must come from Etherscan, from its deployer, or be inferred from bytecode.
- **Collateral and issuer contracts**: the repositories or verified sources of the tokens you care about, and their documentation on admin roles and upgrade procedures.
- An **Etherscan API key** (free tier) to fetch verified sources and ABIs automatically, instead of by hand.

## 4. Complete the position coverage

**Goal.** Watch the positions `watch --user` still skips: direct supply to Blue markets, Vault V1 (MetaMorpho) deposits, and Vault V2 adapters other than the market adapter (gaps C3, C4).

**Delivers.**
- Direct supply: the vault rules for bad debt, utilisation and exit, applied to a single market.
- Vault V1: a second vault reader, covering supply and withdraw queues, cap submissions and `lostAssets`.
- The `MorphoVaultV1Adapter` (a V2 vault holding a V1 vault) and the `MidnightAdapter` (fixed-rate markets), no longer shown as opaque.

**Size.** M (direct supply S, Vault V1 M, Midnight M).

**Needs from you.** Nothing blocking. Confirm which of the three matters to you, so it can be done first.

**Already available.** The Vault V1.1 source and events (`morpho-org/metamorpho-v1.1`, read at a pinned commit), the `MorphoVaultV1Adapter` and `MidnightAdapter` sources in `lib/vault-v2`, and Morpho's Midnight documentation in `lib/docs.morpho.org-developers-docs/midnight`.

## 5. Tests on a forked chain

**Goal.** The tests replay recorded real ranges, in which nothing dramatic happened: no liquidation with bad debt, no change submitted with no notice. A fork of mainnet lets a test *cause* those events and check that the right alert fires (gap T1).

**Delivers.** Scenario tests on a local fork:
- push an oracle down until a position is liquidatable;
- liquidate with bad debt;
- submit and accept a timelocked change;
- have a main lender withdraw.

**Size.** M.

**Needs from you.**
- An **archive RPC** endpoint (paid tier of Alchemy, Infura, QuickNode or similar): forking at a past block needs historical state, which the free endpoint refuses.

**Already available.** Foundry 1.5.0 (`forge`, `anvil`, `cast`) is installed; the Morpho Blue and Vault V2 sources are at the pinned commits in `lib/morpho-blue` and `lib/vault-v2`.

## 6. Reliable infrastructure

**Goal.** Remove the free RPC's limits: state only about 90 to 126 blocks back, no old log ranges, and occasional refusals (gaps D1, D3).

**Delivers.**
- Backfill after a long stop, instead of a reported gap.
- A WebSocket trigger for new blocks with the current polling as the source of truth, the hybrid of `docs/websocket-vs-polling.md`, which brings the latency from 25 to 40 seconds down to a few seconds.
- Handling of reorganisations deeper than 2 blocks.

**Size.** S to M.

**Needs from you.**
- An RPC provider key with archive and WebSocket access. The same key serves step 5.
- Where the watcher will run: your machine, a server, or a container. This decides restart, logging and alert delivery.

## 7. Other chains

**Goal.** Morpho is deployed on many chains; the tool covers Ethereum mainnet only (gap C5).

**Delivers.** A chain setting carrying the contract addresses, the RPC, the API chain id and the block time, so every mode runs on another chain.

**Size.** M.

**Needs from you.**
- Which chains matter (for example Base, Arbitrum).
- An RPC endpoint per chain; free ones exist but have the same limits as on mainnet.

**Already available.** Morpho's deployment addresses for every chain are in the local docs (`contracts/addresses.md`).

## 8. A better risk model

**Goal.** Make the `analyze` verdict less dependent on simplifications (gaps M1, M2, M6):
- failures are treated as independent, although a depeg, a draining pool and a lagging oracle tend to happen together;
- each position is analysed alone;
- incident probabilities are base rates, not protocol-specific.

**Delivers.**
- Correlated scenarios: joint shocks drawn from historical incidents.
- A portfolio view that combines the positions of an address sharing a layer.
- Priors refined per protocol.

**Size.** M to L.

**Decisions.** What "acceptable risk" means for you: the tail budget (today, reduce when the worst 1 % of months loses more than half the equity), the horizon, the stress scenarios that must always be survived.

**Needs from you.**
- **Your risk policy**: limits per position, per protocol and per collateral type; the horizon you decide on.
- Optionally, audit reports and incident post-mortems of the protocols you use, to justify protocol-specific priors.

**Already available.** A local corpus of DeFi hacks (`search-crypto-hack`) to calibrate correlated scenarios; DefiLlama's hack record and price history, already used.

## 9. Execution

**Goal.** Let the tool act on an alert, not just report it (gap X1). Examples:
- de-lever a borrow with `blueBundlesV1RepayAndWithdrawCollateral`, which includes a `maxLtv` check;
- move a borrow to another market with `blueBundlesV1MigrateBorrowPosition`;
- exit an illiquid vault with the force-withdraw or in-kind redemption Bundles.

**Delivers.**
- A transaction builder for these Bundles, with simulation before signing; the free RPC answers `eth_simulateV1`.
- An approval step and conditions that make the transaction revert when they no longer hold.

**Size.** L, with a security design written and agreed before any code.

**Decisions.**
- Fully manual (the tool prepares, you sign), semi-automatic (pre-approved actions within limits), or automatic.
- Which actions are allowed, and with what limits.

**Needs from you.**
- **Your signing setup**: a hardware wallet, a Safe multisig, or a dedicated key with limited authorisation. The tool should never hold a key with full control of your funds.
- **The Morpho Bundles source**, `morpho-org/bundles`, to pin and review the entrypoints used; its addresses are in the local docs.
- Optionally, a security review of the execution component before it touches real funds.

## 10. Housekeeping

**Goal.** Small items that keep the repository healthy.

**Delivers.**
- Continuous integration running the 83 offline tests on each push (gap T2).
- A decision on the old copy in `../projet/`, which still has a date bug (gap T4).
- Removal of the unused `LLAMA_YIELDS` constant in `riskdep/sources.py`.
- A `CHANGELOG.md` and a version bump policy.

**Size.** S.

**Needs from you.**
- Access to the GitHub repository settings, to enable Actions.
- Your decision on `../projet/`: delete it, or keep it frozen with a note.

## What is already available

| Material | Where | Used for |
|---|---|---|
| Morpho developer documentation | `../lib/docs.morpho.org-developers-docs` | contracts, Bundles, addresses on every chain, Midnight, exit routes |
| Morpho Blue source at `8e26ca6a` | `../lib/morpho-blue` | events, liquidation and shares maths, authorisation rules |
| Vault V2 source at `d992cb84` | `../lib/vault-v2` | vault, adapters (market, V1, Midnight), timelocks, gates |
| Vault V1.1 events | `morpho-org/metamorpho-v1.1` at `3b17547e`, read online | step 4 |
| Foundry 1.5.0 | `forge`, `anvil`, `cast` installed | step 5 |
| DeFi hack corpus | the `search-crypto-hack` skill | step 8 |
| Public data | publicnode RPC, Morpho, Pendle and DefiLlama APIs | everything today |

## What I need from you

Grouped by kind, for all steps:

**Decisions**
- [ ] The addresses and vaults to watch, and your feedback on a real run (step 0).
- [ ] The alert channel and the levels to push (step 1).
- [ ] The collateral types `analyze` should support first (step 2).
- [ ] Which positions to add first: direct supply, Vault V1 or Midnight (step 4).
- [ ] The chains to support (step 7).
- [ ] Your risk policy: limits, horizon, stress scenarios (step 8).
- [ ] The degree of automation for execution, and the allowed actions (step 9).
- [ ] What to do with `../projet/` (step 10).

**Documents and smart-contract sources**
- [ ] Sources or documentation of the oracles behind your markets, in particular the unverified ones (step 3).
- [ ] Sources and documentation of the collateral tokens and issuers you use: admin roles, upgrade procedure, reserves and redemption (steps 2 and 3).
- [ ] Optionally, audit reports and post-mortems of the protocols you use (step 8).
- [ ] The `morpho-org/bundles` repository at the release you would use (step 9).

**Access and credentials** (environment variables, never committed)
- [ ] Credentials of the alert channel (step 1).
- [ ] An RPC provider key with archive and WebSocket access (steps 5 and 6), and an RPC per extra chain (step 7).
- [ ] An Etherscan API key, free tier (step 3).
- [ ] Optionally, a DEX aggregator API key (step 2).
- [ ] GitHub Actions enabled on the repository (step 10).

**Infrastructure**
- [ ] Where the watcher runs permanently: machine, server or container (step 6).
- [ ] The signing setup for execution: hardware wallet, Safe or a limited key (step 9).
