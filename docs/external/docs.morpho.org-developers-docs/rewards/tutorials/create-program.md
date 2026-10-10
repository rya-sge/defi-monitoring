# Create a Rewards Program

> Source: https://docs.morpho.org/developers/rewards/tutorials/create-program

---

# Create a Rewards Program

This tutorial guides you through creating a new rewards program for Morpho Vaults or Markets using **Merkl**, the current standard for reward distribution.

## [Prerequisites](#prerequisites)

Before creating a rewards program, ensure you have:

- A clear incentive strategy (what behavior do you want to encourage?)
- Reward tokens ready for distribution
- Knowledge of target Morpho Markets or Vaults
- A wallet with assets to deposit reward tokens
- Understanding of [Reward Program Types](https://docs.morpho.org/developers/rewards/concepts/reward-campaigns/)

## [Overview: Merkl for Rewards Programs](#overview-merkl-for-rewards-programs)

[Merkl](https://merkl.xyz/) is the standard distribution system for Morpho rewards. It provides:

- **Automated Distribution**: Rewards calculated and distributed every 8 hours
- **Flexible Configuration**: Target specific markets, vaults, or user groups
- **Multi-Chain Support**: Works across all chains where Morpho is deployed
- **Transparent Tracking**: Real-time visibility into reward distribution

## [Creating a Program via Merkl](#creating-a-program-via-merkl)

Merkl provides a user-friendly interface for creating reward campaigns. The process differs slightly between Vault and Market programs.

### [Jump on the studio](#jump-on-the-studio)

[https://studio.merkl.xyz/create-campaign/lend](https://studio.merkl.xyz/create-campaign/lend)

### [Select `Morpho` as protocol](#select-morpho-as-protocol)

![Merkl Studio](https://docs.morpho.org/img/build/rewards/merkl-studio.png)
### [Fill the inputs as per Merkl doc](#fill-the-inputs-as-per-merkl-doc)

Check your configuration against [Campaigns displayed by Morpho](#campaigns-displayed-by-morpho) before you fund the campaign.

## [Campaigns displayed by Morpho](#campaigns-displayed-by-morpho)

Merkl distributes every campaign it accepts. The Morpho API and the Morpho App show a reward APR only for campaigns that match the conditions below. A campaign that does not match still distributes on Merkl, but Morpho interfaces do not show its APR.

These conditions follow the Morpho API's current filtering and can change.

### [Supported campaign types](#supported-campaign-types)

| Merkl type | Subtype | Rewards |
| --- | --- | --- |
| `MORPHOSUPPLY` | Any | Suppliers of one market |
| `MORPHOBORROW` | Any | Borrowers of one market |
| `MORPHOCOLLATERAL` | Any | Collateral providers of one market |
| `MORPHO` | `1` | Suppliers of one market |
| `MORPHO` | `2` | Borrowers of one market |
| `MORPHO` | `3` | Collateral providers of one market |
| `MORPHOSUPPLY_SINGLETOKEN` | Any | Suppliers of every listed market whose loan token is the target token |
| `MORPHOBORROW_SINGLETOKEN` | Any | Borrowers of every listed market whose loan token is the target token |
| `MULTILENDBORROW` | Any | Suppliers (entry `campaignType` `24`) or borrowers (entry `campaignType` `45`) of each market in the campaign |
| `MORPHOVAULT` | Any | Depositors of one vault |
| `ERC20LOGPROCESSOR` | Any | Holders of one vault's share token |
| `MORPHO` | `0` | Depositors of one vault |

The Morpho API ignores every other type and subtype, and every other `MULTILENDBORROW` entry `campaignType`.

### [Parameters to avoid](#parameters-to-avoid)

The Morpho API drops a campaign that uses any of these settings.

| Setting | What to do instead |
| --- | --- |
| `isPrivate: true` | Create a public campaign |
| Non-empty `params.whitelist` | Leave the whitelist empty |
| Any hook other than `hookType: 23` with `protocols` containing `MorphoVaultV2`, including that hook combined with another one | Use no hook, or only that hook. With it, the campaign counts only in the APR of Morpho Vault V2 depositors, not in market APRs |
| Less than 24 hours between `startTimestamp` and `endTimestamp` | Run the campaign for at least 24 hours |
| `rewardToken.type` other than `TOKEN`, such as points or pre-TGE rewards | Reward in an ERC-20 token |
| `rewardToken.isTest: true` | Use a production reward token |
| Reward token on a chain Morpho does not support for rewards, or an invalid `rewardToken.address` | Use a valid token on a supported chain |
| Market campaign without a valid `params.marketId` or `params.market`, single-token campaign without a valid `params.targetToken`, `MULTILENDBORROW` campaign without valid `params.markets` entries, or vault campaign whose `params.targetToken` is not the vault address | Set the target the campaign type expects |

Blacklists are supported: a `params.blacklist` does not make the API drop the campaign. If the blacklist contains a vault or a Vault V2 adapter address, the API does not forward that campaign to the vault's depositors.

### [Forwarded vault rewards](#forwarded-vault-rewards)

A Morpho Vault V2 depositor sees supply-side market campaigns for markets the vault reaches through a `MorphoMarketV1AdapterV2`, and the campaigns of vaults it allocates to through a `MorphoVaultV1Adapter`, weighted by allocation. The API does not forward rewards from a Morpho Vault V2 that another Morpho Vault V2 allocates to.

### [Display in the Morpho App](#display-in-the-morpho-app)

The Morpho App shows a reward only when the APR the Morpho API serves for it is above `0`. A campaign with a computed APR of `0`, such as a Target APR campaign whose target the native yield already meets, shows no reward.

## [Next Steps](#next-steps)

- **Fetch campaign data**: Follow the [Fetch Rewards Data tutorial](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/)
- **Integrate display**: Check out the [Integrate Display tutorial](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/)
- **Enable claiming**: See the [Claim Rewards tutorial](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/)

[Merkl Distribution System

Previous Page

](https://docs.morpho.org/developers/rewards/concepts/distribution-system/)[Fetch Rewards Data

Next Page

](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/)