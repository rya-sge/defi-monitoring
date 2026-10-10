# Rewards: Developer Resources

> Source: https://docs.morpho.org/developers/rewards/resources/all

---

# Rewards: Developer Resources

This page is your central hub for all the tools, links, and data sources you need to integrate Morpho rewards into your application.

## [Quick Reference](#quick-reference)

| Resource | Link |
| --- | --- |
| **Morpho API** | [api.morpho.org/graphql](https://api.morpho.org/graphql) |
| **Merkl API** | [api.merkl.xyz/docs](https://api.merkl.xyz/docs#description/introduction) |
| **Legacy Rewards** | [rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/) |
| **Merkl Docs** | [docs.merkl.xyz](https://docs.merkl.xyz/) |

## [APIs](#apis)

### [Morpho API (Recommended for Vault/Market Rewards)](#morpho-api-recommended-for-vaultmarket-rewards)

The Morpho API provides integrated rewards data alongside vault and market information.

- **GraphQL Playground**: [api.morpho.org/graphql](https://api.morpho.org/graphql)
- **Documentation**: [Morpho API Docs](https://docs.morpho.org/developers/api/morpho/)
- **Rewards Queries**:

  - [Morpho Markets Rewards](https://docs.morpho.org/developers/api/rewards/#morpho-markets-rewards)
  - [Morpho Vaults Rewards](https://docs.morpho.org/developers/api/rewards/#morpho-vaults-rewards)

**Use Cases:**

- Fetch vault APY + rewards APR
- Get market reward rates (supply, borrow, collateral)
- Combine base yield and rewards in one query
- Historical data and time-series queries

### [Merkl API (Primary for User Rewards)](#merkl-api-primary-for-user-rewards)

Merkl's REST API for current reward programs and user claimable amounts.

- **Base URL**: `https://api.merkl.xyz/`
- **Documentation**: [api.merkl.xyz/docs](https://api.merkl.xyz/docs#description/introduction)
- **Key Endpoint**:

  - User Rewards (includes the cumulative `amount`, `claimed`, and merkle `proofs` needed to claim): `GET /v4/users/{address}/rewards?chainId={chainId}`

**Use Cases:**

- Fetch user claimable rewards (current programs)
- Get Merkle proofs for claiming
- Real-time reward accrual (updates every 8 hours)

### [Legacy Rewards (Deprecated)](#legacy-rewards-deprecated)

**Legacy Rewards API Deprecated**

The `rewards.morpho.org` API has been deprecated. If you or your users have unclaimed rewards from historical Morpho programs (pre-Merkl migration), they can be claimed directly through the legacy rewards lookup app:

👉 **[rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/)**

All new reward programs are distributed exclusively via [Merkl](https://app.merkl.xyz/). See the [Merkl documentation](https://docs.merkl.xyz/) for integration details.

## [Smart Contracts](#smart-contracts)

### [Merkl Distributor Contracts](#merkl-distributor-contracts)

All Merkl smart contract addresses, categorized by chain are listed [here](https://app.merkl.xyz/status).

**Key Functions:**

- `claim(address[] users, address[] tokens, uint256[] amounts, bytes32[][] proofs)` - Claim cumulative Merkl reward amounts

### [Contract ABIs](#contract-abis)

**Merkl Distributor ABI:**

```
[
  {
    "inputs": [
      { "name": "users", "type": "address[]" },
      { "name": "tokens", "type": "address[]" },
      { "name": "amounts", "type": "uint256[]" },
      { "name": "proofs", "type": "bytes32[][]" }
    ],
    "name": "claim",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
]
```

## [SDKs & Tools](#sdks--tools)

### [Morpho SDKs](#morpho-sdks)

While there's no dedicated rewards SDK, you can use Morpho's core SDKs for related functionality:

- **`@morpho-org/morpho-sdk`**: The default SDK for vaults and markets - entity classes (`/entities`) and Viem-based fetchers (`/fetch`) via subpath exports
- **`@morpho-org/simulation-sdk`**: Simulate transactions

**Learn More**: [Morpho SDKs Documentation](https://docs.morpho.org/developers/sdks/get-started/)

### [GraphQL Clients](#graphql-clients)

For querying the Morpho API:

- **[graphql-request](https://github.com/graffle-js/graffle/tree/graphql-request)**: Lightweight GraphQL client
- **[Apollo Client](https://www.apollographql.com/docs/react/)**: Full-featured GraphQL client
- **[urql](https://formidable.com/open-source/urql/)**: Flexible GraphQL client

### [Web3 Libraries](#web3-libraries)

For claiming rewards onchain:

- **[viem](https://viem.sh/)**: Modern TypeScript web3 library (recommended)
- **[ethers.js](https://docs.ethers.org/)**: Popular web3 library
- **[web3.js](https://web3js.readthedocs.io/)**: Classic web3 library

## [External Documentation](#external-documentation)

### [Merkl](#merkl)

- **Official Docs**: [docs.merkl.xyz](https://docs.merkl.xyz/)
- **Integration Guide**: [docs.merkl.xyz/integrate-merkl/app](https://docs.merkl.xyz/integrate-merkl/app)

### [Morpho](#morpho)

- **Developer Hub**: [/developers/](https://docs.morpho.org/developers/)
- **API Documentation**: [/developers/api/rewards/](https://docs.morpho.org/developers/api/rewards/)

## [Onchain Data Sources](#onchain-data-sources)

- **Merkl Subgraphs**: See [Merkl docs](https://docs.merkl.xyz/)

## [Tutorials & Guides](#tutorials--guides)

### [Getting Started](#getting-started)

- [Rewards Integration Overview](https://docs.morpho.org/developers/rewards/get-started/)
- [Understanding Reward Programs](https://docs.morpho.org/developers/rewards/concepts/reward-campaigns/)
- [Distribution System (Merkl)](https://docs.morpho.org/developers/rewards/concepts/distribution-system/)

### [Step-by-Step Tutorials](#step-by-step-tutorials)

- [Create a Rewards Program](https://docs.morpho.org/developers/rewards/tutorials/create-program/)
- [Fetch Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/)
- [Claim Rewards](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/)
- [Integrate Rewards Display](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/)

## [Support Channels](#support-channels)

### [For Integrators](#for-integrators)

- **Technical Questions**: [help.morpho.org](https://help.morpho.org)

### [For Reward Issuers](#for-reward-issuers)

- **Program Creation Help**: [Merkl Docs](https://docs.merkl.xyz/)

## [Monitoring & Analytics](#monitoring--analytics)

### [Dashboards](#dashboards)

- **Merkl Dashboard**: [merkl.xyz](https://merkl.xyz/) - View active campaigns
- **Morpho App**: [app.morpho.org](https://app.morpho.org) - See rewards on vaults/markets

### [Analytics Tools](#analytics-tools)

- **Dune Analytics**: [Morpho Dashboards](https://docs.morpho.org/developers/ecosystem/data-dashboards/)
- **DefiLlama**: Track TVL and yields across Morpho

## [Governance & Updates](#governance--updates)

### [Morpho Governance](#morpho-governance)

- **Snapshot**: [snapshot.box/#/s.eth](https://snapshot.box/#/s:morpho.eth)

### [Migration Information](#migration-information)

- **MIP 111**: [Snapshot Proposal](https://snapshot.box/#/s:morpho.eth/proposal/0xadf3862d97cf4e8bb84a4b3d5117abe1a9db774e92ad97c65bde22214c0b76c9) - Migration to Merkl

## [Need Help?](#need-help)

If you can't find what you're looking for, reach out via:

- **Chat**: [help.morpho.org](https://help.morpho.org)

[Integrate Rewards Display

Previous Page

](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/)[Get Started

Next Page

](https://docs.morpho.org/developers/api/get-started/)