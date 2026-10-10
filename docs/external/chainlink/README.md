# Chainlink — external references

`docs.chain.link-data-feeds-docs/` is a Markdown export of the Chainlink Data Feeds documentation
(<https://docs.chain.link/data-feeds>): 51 pages on price, exchange-rate, SmartData / Proof of Reserve, SVR, rate and
L2 sequencer feeds, the `AggregatorV3Interface` API and the guides for non-EVM chains. The folder is **git-ignored**: it
exists only in the local checkout, so read it there; a fresh clone does not have it. This README is tracked.

## Why it matters to riskdep

| riskdep piece | Chainlink concept it depends on |
|---|---|
| `MorphoChainlinkOracleV2` (base vault × base feeds ÷ quote vault × quote feeds) | `latestRoundData()` read with **no staleness check**, so heartbeat, deviation and shutdown behaviour pass straight into the Morpho price |
| `riskdep/admin.py` (`AggregatorProposed` / `AggregatorConfirmed`) | the proxy → aggregator upgrade path, run by the proxy `owner` multisig |
| `riskdep/oracle_class.py` (price-tracking vs constant-price, `oracle_history_*` in `registry.json`) | round history via `getRoundData`, phase-encoded proxy `roundId`s, exchange-rate feeds that are "not equivalent to market price feeds" |
| RockawayX vaults (`docs/analysis/ROCK-VAULT-DEP.md` §3–§5) | "PST-USDC Exchange Rate (Calculated)", "PRIME / WYLDS Exchange Rate", "Hastra Auto / WYLDS Exchange Rate" (Custom, Exchange Rate category), USDC/USD, EUR/USD, BTC/USD, ETH/USD, wstETH market feeds; `EACAggregatorProxy` owned by the 4/9 multisig `0x21f7…73ca` |
| `docs/analysis/GAP.md` K7 (oracle is not binary), K23 / feed quality (heartbeat, deviation, staleness not measured), G4 | feed categories, heartbeat/deviation, Bounded feeds, single-source risk |

## Tree

```
docs.chain.link-data-feeds-docs/
├── *.md                        # top-level pages: overview, API reference, selecting feeds, historical data, L2 sequencer, SVR, SmartData…
├── price-feeds/                # price feed address page (rendered dynamically: no feed table in the export)
├── rates-feeds/                # rate & volatility feed addresses
├── smartdata/                  # SmartData / Proof of Reserve addresses and wallet-address-manager risks
├── mvr-feeds/                  # Multiple-Variable Response feeds: API reference (incl. confirmAggregator)
│   └── guides/                 # ethers.js, viem, Solidity consumers
├── svr-feeds/                  # Smart Value Recapture searcher onboarding (Atlas, Ethereum)
├── tokenized-equity-feeds/     # tokenized equity providers (Coinbase, Ondo, Robinhood)
├── us-government-macroeconomic/# US government macro data feed addresses
├── solana/  starknet/  stellar/# non-EVM consumer guides (starknet/tutorials/snfoundry/)
```

## Main files

| Path | What | riskdep use |
|---|---|---|
| `docs.chain.link-data-feeds-docs/overview.md` | components (consumer, proxy, aggregator), proxy/aggregator updates, monitoring | admin watch, staleness and limit checks |
| `docs.chain.link-data-feeds-docs/api-reference.md` | `AggregatorV3Interface`, `AccessControlledOffchainAggregator` functions | ABI and return semantics of `latestRoundData` / `getRoundData` |
| `docs.chain.link-data-feeds-docs/historical-data.md` | proxy `roundId` = `phase << 64 \| aggregatorRoundId`, walking phases | round-history probe in `oracle_class.py` across aggregator changes |
| `docs.chain.link-data-feeds-docs/selecting-data-feeds.md` | risk categories, Custom feeds, shutdown policy, risk mitigation, Bounded and Exchange Rate feeds | feed classification, K7 / feed-quality gap |
| `docs.chain.link-data-feeds-docs/data-sources.md` | sourcing model per asset type | single- vs multi-source per feed |
| `docs.chain.link-data-feeds-docs/developer-responsibilities.md` | market-integrity and code risks are the integrator's | Morpho's missing checks are by design, riskdep must measure them |
| `docs.chain.link-data-feeds-docs/smartdata.md` | Proof of Reserve (offchain, cross-chain), NAVLink, SmartAUM | NAV / reserve feeds are constant-price inputs |
| `docs.chain.link-data-feeds-docs/contract-registry.md` | Flags registry: `getFlag(proxy)` true = Chainlink-owned and active | verify a feed is official before trusting its admin |
| `docs.chain.link-data-feeds-docs/deprecating-feeds.md` | feeds scheduled for deprecation (Ethereum list rendered dynamically) | shutdown watch |
| `docs.chain.link-data-feeds-docs/svr-feeds.md` | SVR dual aggregator, fallback delay, variants | identify SVR proxies, liquidation-backrun MEV |
| `docs.chain.link-data-feeds-docs/l2-sequencer-feeds.md` | sequencer uptime feeds, grace period example | L2 only, out of scope on Ethereum |
| `docs.chain.link-data-feeds-docs/mvr-feeds/api-reference.md` | `IBundleAggregatorProxy`, `confirmAggregator` | bundle feeds, if one ever appears in a market |

## Read first for this project

### latestRoundData semantics and staleness checks
- `api-reference.md` § latestRoundData: returns `roundId, answer, startedAt, updatedAt, answeredInRound`; `answeredInRound` is
  "Deprecated - Previously used when answers could take multiple rounds to be computed". Do not use it as a freshness test.
- `overview.md` § Check the timestamp of the latest answer: "Your application should track the `latestTimestamp` variable or use
  the `updatedAt` value … If your application detects that the reported answer is not updated within the heartbeat …, pause
  operation or switch to an alternate operation mode".
- `overview.md` § Check the latest answer against reasonable limits: `minAnswer`/`maxAnswer` "On most data feeds, these values
  are no longer used and they do not stop your application from reading the most recent answer."
- `selecting-data-feeds.md` § Data Feed Shutdown Policy: once shut down, "`latestAnswer` will return `0`" and
  "`latestRoundData` will revert with no data available"; two weeks of notice "except where conditions require an accelerated
  deprecation". A Morpho oracle reading a shut-down feed reverts, which freezes borrows and liquidations on the market.
- `selecting-data-feeds.md` § Bounded Market Price Feeds: above the cap (e.g. $1.05 for a stablecoin) "the price will not be
  reported on-chain. Instead, the most recently written on-chain price will be the value returned"; no lower bound.

### Heartbeat and deviation threshold
- `overview.md` § Check the timestamp: "the aggregator updates its `latestAnswer` when the value deviates beyond a specified
  threshold or when the heartbeat idle time has passed"; values are at data.chain.link or in the address lists. "Some heartbeats
  are configured to last several hours."
- Same section: wrapped or liquid-staking feeds "might have different heartbeat and deviation thresholds than that of the
  underlying asset", and thresholds differ for the same asset across chains; combining feeds (wstETH × ETH/USD, X ÷ USDC/USD)
  adds a margin of error.
- `historical-data.md` § `roundId` in Aggregator: round IDs increase but "This increase may not be monotonic".

### Proxy / aggregator architecture and AggregatorProposed / Confirmed
- `overview.md` § Single-value Feed Components: the proxy "point[s] to the aggregator … enables the underlying aggregator to be
  upgraded without any service interruption"; `EACAggregatorProxy.sol` is the common example.
- `overview.md` § Updates to proxy and aggregator contracts: updates include "a complete replacement of the aggregator that the
  proxy uses"; owner is "a multi-signature safe" (BTC/USD owner `0x21f73D42Eb58Ba49dDB685dc29D3bF5c0f0373CA`, the same 4/9
  multisig as the RockawayX exchange-rate feeds in ROCK-VAULT-DEP §3).
- `historical-data.md` § `roundId` in proxy: `uint80(uint256(_phase) << PHASE_OFFSET | _originalId)`; `_phase` "is incremented
  each time the underlying aggregator implementation is updated". A confirmed aggregator change shows as a new phase in
  `roundId >> 64`; the docs do not name the `AggregatorProposed`/`AggregatorConfirmed` events (only
  `mvr-feeds/api-reference.md` § confirmAggregator, "only the owner or an authorized entity can call this").
- `overview.md` § Components of an aggregator: use `typeAndVersion()` to identify the aggregator type; aggregators differ by
  network.

### Feed categories and risk tiers
- `selecting-data-feeds.md` § Data Feed Categories: Low, Medium, High, Very High market pricing risk, New Token, Custom,
  Deprecating, Unrated; "If a feed does not display one of these categories … Treat it as unevaluated".
- § New Token Feeds: no history for a rigorous assessment; after a probationary period re-rated or deprecated.
- § Custom Feeds: "can differ materially from standard market price feeds in sourcing, methodology, update behavior, and risk
  profile"; sub-types with their tier: Onchain Single Source (High), Onchain PoR (Medium), **Exchange Rate (Medium)**, Custom
  Index (High), Offchain Single Source (High), Offchain PoR (High), LP Token (High), **Wrapped Calculated (Very High)**.
- § Single Source Data Providers: single source is used "when only one authoritative source exists … such as a protocol-published
  NAV, reserve value, redemption rate, exchange rate".
- § Risk Mitigation / Stablecoin-specific considerations: circuit breakers, kill switch, monitoring, CAPO-style upside cap.

### Exchange-rate, SmartData and Proof of Reserve feeds (what "Calculated" means)
- `selecting-data-feeds.md` § Custom Feeds: Exchange Rate Feeds "read an exchange rate from an external contract onchain …
  Chainlink does not own or control these contracts in any way. They are not equivalent to market price feeds."
- § Exchange Rate Feeds: they "report the internal redemption rates for an asset … sourced directly from a specified smart
  contract on a source chain and relayed to a destination chain". This is why riskdep classes them constant-price: the issuer's
  contract (e.g. Hastra's `NAV_ORACLE_UPDATER_ROLE`) sets the value, not a market.
- `data-sources.md` table: "Exchange Rate Feeds | On-chain data"; "SmartData NAV (offchain) | Sourced directly from Fund
  Administrator or Asset Manager".
- "(Calculated)" in a feed name is not defined in the export. The nearest definitions: `price-feeds.md` ("there are some
  exceptions where … data values are calculated") and Wrapped Calculated Feeds ("a derivative formed from a calculated method")
  in `selecting-data-feeds.md` § Custom Feeds. Read PST-USDC as an exchange-rate feed computed from an on-chain source.
- `smartdata.md` § Proof of Reserve Feeds: offchain reserves are third-party, custodian or "⚠ Self-reported" (issuer API);
  cross-chain reserves come from a wallet address manager or a self-hosted address list, both issuer-reported. § Using
  Single-value SmartData Feeds: same `AggregatorV3Interface`. `smartdata/addresses.md` § Risks for Proof of Reserve feeds using
  the wallet address manager.

### SVR feeds
- `svr-feeds.md` § How SVR Works: dual aggregator; the same report goes publicly to the Standard aggregator and privately
  (Flashbots MEV-Share) to the SVR aggregator; "If the private route fails or times out, the SVR feed automatically reverts to
  the Standard Feed price after a configurable delay".
- § SVR Feed Variants: SVR (Shared), Aave SVR, SVR-Backup (Legacy). § Default SVR Activation: on by default on Base and Ink;
  protocols opt out by "reading from the 'Standard' proxy that complements every SVR proxy".

### L2 sequencer uptime
- `l2-sequencer-feeds.md`: status `0` up / `1` down; example consumer uses `GRACE_PERIOD_TIME = 3600`; "Chainlink is no longer
  expanding L2 Sequencer Uptime Feeds to additional networks". Not used: riskdep is Ethereum mainnet only.

### CCIP
- Only mentioned in passing: `selecting-data-feeds.md` § Exchange Rate Feeds (LST/LRT minted on L2 "while Chainlink CCIP
  transfers the underlying asset to a layer 1"), and a `ccip_basic_receiver` example in `solana/using-data-feeds-solana.md`.

## Gaps

| Missing | Why it matters | Where to get it |
|---|---|---|
| Per-feed heartbeat, deviation, category for the RockawayX feeds (PST-USDC, PRIME / WYLDS, Hastra Auto / WYLDS) and USDC/USD, EUR/USD, BTC/USD, ETH/USD, wstETH | the address pages render dynamically (`price-feeds/addresses.md` shows "Loading..."), so no per-feed value is in the export; needed for a staleness rule (GAP K23) | data.chain.link feed pages (heartbeat, deviation, category per feed) |
| Which source contract each exchange-rate feed reads, and the meaning of "(Calculated)" | decides who can move the price (ROCK-VAULT-DEP §3) | data.chain.link feed page, aggregator `typeAndVersion()` and source on Etherscan |
| `EACAggregatorProxy` source and the `AggregatorProposed` / `AggregatorConfirmed` events | admin.py relies on them; only linked to GitHub here | `smartcontractkit/chainlink` `contracts/src/v0.6/EACAggregatorProxy.sol` |
| CCIP docs (token pools, `BurnMintTokenPool`, rate limits, RMN, `RBACTimelock`) | PST is bridged Solana ↔ Ethereum through CCIP (ROCK-VAULT-DEP §4–§5, $34.7M) | docs.chain.link/ccip, not exported |
| Ethereum deprecation list | `deprecating-feeds.md` table renders dynamically | docs.chain.link/data-feeds/deprecating-feeds |
| Data Streams, OCR / DON architecture pages | linked, not exported | docs.chain.link/data-streams, architecture-overview |
