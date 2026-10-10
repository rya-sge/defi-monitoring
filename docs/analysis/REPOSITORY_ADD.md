# Repositories to add to `docs/external/`

Third-party sources that would let `riskdep` check its rules and registry entries against code instead of assumptions. Each one goes in as a git submodule pinned to a commit, under `docs/external/<protocol>/lib/<repo>`, with its line added to the `docs/external/` list in `CLAUDE.md` and `AGENTS.md` (kept identical).

Already present: Morpho Blue, Vault V2, Morpho developer docs, Pendle core / SY / integration and docs, Etherscan API docs.

Pins are the head of the named branch on 2026-10-10. Before pinning an issuer contract, confirm with Etherscan `getsourcecode` that the deployed source matches that commit.

## Summary

| Priority | Protocol | Repository | Branch @ pin | Gap / step |
|---|---|---|---|---|
| 1 | Morpho | `morpho-org/morpho-blue-oracles` | `main` @ `9d2a0b66` | M4, G4, admin surface |
| 1 | Sky | `sky-ecosystem/sdai` | **`susds`** @ `dfc7f41c` | step 3, M7 |
| 1 | Sky | `sky-ecosystem/usds` | `master` @ `d65551db` | step 3, M7 |
| 1 | Ethena | `ethena-labs/bbp-public-assets` | `main` @ `f3e56d5f` (archived) | step 3, M7 |
| 1 | Lido | `lidofinance/core` | `master` @ `1440c830` | step 3, M7 |
| 2 | Chainlink | Data Feeds documentation (no repository) | — | G4 |
| 2 | Sky | `sky-ecosystem/dss-lite-psm` | `main` @ `dbf00222` | M2, depeg model |
| 2 | Morpho | `morpho-org/metamorpho` | `main` @ `ded84e59` | C4, step 4 |
| 2 | Morpho | `morpho-org/metamorpho-v1.1` | `main` @ `3b17547e` | C4, step 4 |
| 3 | Morpho | `morpho-org/public-allocator` | `main` @ `4e280944` | C4, lender liquidity |
| 3 | Morpho | `morpho-org/pre-liquidation` | `main` @ `6f15d201` | G6 |
| 3 | Morpho | `morpho-org/bundler3` | `main` @ `b4014349` | X1, step 9 |
| 3 | Sky | `sky-ecosystem/dss` | `master` @ `fa4f6630` | M2 |

Priority 1: useful now, for code that already runs. Priority 2: needed by the next planned step. Priority 3: only when the step that needs it starts.

## Priority 1

### Morpho oracles: `morpho-org/morpho-blue-oracles`

`src/morpho-chainlink/` (`MorphoChainlinkOracleV2`) and `src/wsteth-exchange-rate-adapter/`.

- `admin.py` already calls this oracle's getters (`BASE_FEED_1/2`, `QUOTE_FEED_1/2`, `BASE_VAULT`, `QUOTE_VAULT`); the source fixes what they mean and how the price is scaled.
- The oracle has no staleness check (`ChainlinkDataFeedLib`: "Staleness is not checked because it's assumed that the Chainlink feed keeps its promises") and no admin: once deployed, nothing in it can change. A stale or wrong feed passes straight through to Morpho Blue.
- The vault conversion reads the collateral's ERC-4626 rate (sUSDe, sUSDS), not a market price, so an issuer depeg does not move the oracle. `propagate.py` models oracles on this assumption.

### Sky (sUSDS, USDS)

`registry.json` covers sUSDS (`0xa3931d71…fbd`, issuer Sky).

- **`sky-ecosystem/sdai`, branch `susds`**: `src/SUsds.sol`. The default branch is sDAI (`SavingsDai.sol`); sUSDS exists only on `susds`, so add it with `git submodule add -b susds https://github.com/sky-ecosystem/sdai docs/external/sky/lib/sdai`.
  - `file("ssr")` requires `ssr >= RAY`: the share price never falls, so an oracle reading sUSDS → USDS through `BASE_VAULT` never sees a USDS depeg.
  - UUPS-upgradeable; `_authorizeUpgrade` is `auth`, so any `wards` holder can upgrade. Admin events to watch: `Rely`, `Deny`, `File`, `Upgraded`.
- **`sky-ecosystem/usds`**: `Usds.sol` (the underlying, also UUPS-upgradeable with `wards`: a second admin surface) and `DaiUsds.sol` (the 1:1 DAI ↔ USDS converter).

### Ethena (USDe, sUSDe): `ethena-labs/bbp-public-assets`

`registry.json` covers USDe (`0x4c9edd58…`) and sUSDe (`0x9d39a5de…`). The repository is archived; it is the public copy of the audited contracts, in `contracts/contracts/`.

- `USDe.sol`: who can mint (only the minter contract).
- `EthenaMinting.sol`: mint and redeem limits per block, the custodians, the roles that can pause.
- `StakedUSDeV2.sol`: the cooldown before unstaking, the blacklist roles (soft and full restriction), and how rewards vest. The blacklist and the cooldown bear on whether a liquidator can sell seized sUSDe.
- `SingleAdminAccessControl.sol`: the role model.

Ethena also publishes `ethena-labs/role-verification` (archived), a Python script that lists who holds each role; useful as a cross-check for `admin.py`, not as a submodule.

### Lido (wstETH): `lidofinance/core`

`registry.json` covers wstETH (`0x7f39c581…`).

- `contracts/0.6.12/WstETH.sol`: the wrapper; its rate is `stETH per share`, which a wstETH oracle reads.
- `contracts/0.4.24/Lido.sol` (stETH): rebasing, the oracle report that can lower the rate on a slashing, the pause roles.
- `contracts/0.8.9/WithdrawalQueue*.sol`: how long an exit through Lido takes, which bounds the exit route when the market price depegs.

The repository is large; a sparse checkout of `contracts/0.4.24`, `contracts/0.6.12`, `contracts/0.8.9` and `contracts/common` is enough.

## Priority 2

### Chainlink Data Feeds: documentation only

`admin.py` watches `AggregatorProposed` and `AggregatorConfirmed` on the feed proxies. What is missing is the heartbeat and the deviation threshold of each feed, which would let a stale feed be detected. Those are on the feed pages of the Chainlink documentation, not in a repository; `smartcontractkit/chainlink` is a node implementation and far larger than needed. Save the Data Feeds pages (architecture, the feed list for Ethereum mainnet) under `docs/external/docs.chain.link-data-feeds/`, as was done for Morpho and Etherscan.

### Sky peg module: `sky-ecosystem/dss-lite-psm`

The USDC peg-stability module, the "USDC via PSM" dependency named in the sUSDS registry entry and the main reason USDS holds its peg. Its fees (`tin`, `tout`) and debt ceiling bound how fast a USDS depeg is arbitraged away.

### Morpho Vault V1: `morpho-org/metamorpho` and `morpho-org/metamorpho-v1.1`

Needed for next step 4 (C4): direct Vault V1 deposits, and Vault V2 vaults that allocate through `MorphoVaultV1Adapter`.

- V1.0 realises bad debt; V1.1 does not, so a V2 vault holding V1.1 shares does not show V1.1 losses in its share price.
- Roles (curator, allocator, guardian), timelocks and the supply and withdraw queues, the V1 equivalent of what `vault.py` reads for V2.

## Priority 3

- **`morpho-org/public-allocator`**: lets anyone move liquidity between the markets of a V1 vault within set limits; it changes how much a lender can withdraw from a market. Add with Vault V1.
- **`morpho-org/pre-liquidation`**: the opt-in pre-liquidation contracts; today only the authorisation they need is alerted (G6).
- **`morpho-org/bundler3`**: needed only for execution, next step 9 (X1).
- **`sky-ecosystem/dss`**: the Sky core (`Vat`, `Jug`, `Vow`), the "Sky vaults" dependency and the bad-debt path behind USDS. Old and large; Sky's documentation may be enough.

## Not needed

- **Sky:** spells and governance (`spells-mainnet`, `executive-votes`, `polls`, `chief`), bridges and L2 code (`lz-*`, `op-*`, `arbitrum-*`, `xchain-*`), Spark and Grove code (`diamond-pau`, `*-pau-*`), and the archived repositories. `stusds` and `lockstake` only if a watched position holds stUSDS.
- **Uniswap, Curve:** the PT exit liquidity is the Pendle pool, already present.
- **DEX aggregators (0x, 1inch):** only their API documentation, and only once next step 2 picks a quote source.
