# Fetch Rewards Data

> Source: https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data

---

# Fetch Rewards Data

This tutorial shows you how to fetch reward information for Morpho Vaults and Markets from both **Merkl API** and **Morpho API**. Understanding how to query both systems is essential for displaying complete reward information to your users.

## [What You'll Learn](#what-youll-learn)

- How to fetch Vault V2 reward rates from Morpho API
- How to query user-specific rewards from Merkl API
- How to combine data from multiple sources for a complete picture

## [Prerequisites](#prerequisites)

- Basic understanding of [Reward Programs](https://docs.morpho.org/developers/rewards/concepts/reward-campaigns/)
- Familiarity with REST and GraphQL APIs
- A tool for making API requests (curl, fetch, axios, or GraphQL client)

## [API Landscape Overview](#api-landscape-overview)

There are **two main APIs** for rewards data:

| API | Use Case | Rewards Type | Data Provided |
| --- | --- | --- | --- |
| **Morpho API** | Vault/Market reward rates | Merkl only | APRs, reward token info, integrated with vault/market data |
| **Merkl API** | User claimable rewards | Merkl only | User balances, claim data, real-time rewards |
| **Legacy Rewards** | User claimable rewards | URD only | Deprecated. Use [rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/) |

**Recommended Strategy:**

1. Use **Morpho API** for displaying reward APRs on vaults/markets
2. Use **Merkl API** for user-specific Merkl rewards
3. For legacy URD rewards, direct users to [rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/)

## [Fetching Morpho Vault V2 Rewards](#fetching-morpho-vault-v2-rewards)

### [Using Morpho API](#using-morpho-api)

Morpho Vault V2 rewards are **pre-aggregated** by the API. The `rewards` field on a Morpho Vault V2 already includes all reward sources across its supported adapters.

```
query VaultV2Rewards($address: String!, $chainId: Int!) {
  vaultV2ByAddress(address: $address, chainId: $chainId) {
    address
    name
    symbol
    apy
    netApy  # Complete APY including all rewards

    # Pre-aggregated rewards from all sources
    rewards {
      supplyApr
      asset {
        address
        symbol
        price {
          usd
        }
      }
    }

    # Adapters show where the vault allocates
    adapters {
      items {
        type      # Adapter type (liquidity, market, and other supported adapters)
        address
        assetsUsd
      }
    }
  }
}
```

**Variables example:**

```
{
  "address": "0xb576765fB15505433aF24FEe2c0325895C559FB2",
  "chainId": 1
}
```

**Returned fields:**

Fields below are returned as decimals (e.g. `0.05` = 5%).

- `apy`: Current APY of the vault (before fees), derived from liquidity adapter rates.
- `netApy`: Current net APY of the vault (after fees, including rewards), derived from liquidity adapter rates.
- `rewards[].supplyApr`: APR for each reward token.

**Key Integration Notes:**

- Use `vaultV2ByAddress` for Vault V2 reward queries
- APY and rewards fields are at the **top level** of the response
- **No manual aggregation needed**: the API pre-aggregates rewards from supported adapters

## [Fetching Market Rewards](#fetching-market-rewards)

Markets can have rewards for **supply** and **borrow**.

### [Using Morpho API](#using-morpho-api-1)

```
query MarketRewards($marketId: String!, $chainId: Int!) {
  marketById(marketId: $marketId, chainId: $chainId) {
    marketId
    loanAsset {
      symbol
    }
    collateralAsset {
      symbol
    }
    state {
      borrowApy
      supplyApy
      rewards {
        supplyApr
        borrowApr
        asset {
          address
          symbol
          price {
            usd
          }
        }
      }
    }
  }
}
```

**Key Fields:**

- `supplyApr`: Reward APR for suppliers
- `borrowApr`: Reward APR for borrowers (often negative, meaning borrowers earn rewards)

## [Fetching User-Specific Rewards](#fetching-user-specific-rewards)

### [Merkl API (Current Programs)](#merkl-api-current-programs)

To get a user's claimable Merkl rewards:

**Endpoint:**

```
GET https://api.merkl.xyz/v4/users/{address}/rewards?chainId={chainId}
```

**Example:**

```
curl "https://api.merkl.xyz/v4/users/0x1234...5678/rewards?chainId=1"
```

**Response Structure:**

```
[
  {
    "chain": { "id": 1, "name": "Ethereum" },
    "rewards": [
      {
        "token": { "address": "0xREWARD_TOKEN", "symbol": "MORPHO", "decimals": 18 },
        "amount": "2000000000000000000",
        "claimed": "1000000000000000000",
        "pending": "0",
        "proofs": ["0xproof1", "0xproof2"]
      }
    ]
  }
]
```

The response is an array of per-chain objects, each with a `rewards` array. A token's currently-claimable balance is `amount - claimed` (both are cumulative). `pending` is reward not yet in a live merkle root.

**TypeScript Example:**

```
async function fetchMerklRewards(userAddress: string, chainId: number) {
  const response = await fetch(
    `https://api.merkl.xyz/v4/users/${userAddress.toLowerCase()}/rewards?chainId=${chainId}`
  );
  const data = await response.json();

  // The endpoint returns an array of per-chain objects; flatten to a list of rewards.
  const rewards = data.flatMap((entry) => entry.rewards);

  // Aggregate the unclaimed balance per token (amount - claimed)
  const claimableByToken: Record<string, bigint> = {};

  for (const reward of rewards) {
    const unclaimed = BigInt(reward.amount) - BigInt(reward.claimed);
    claimableByToken[reward.token.address] =
      (claimableByToken[reward.token.address] || 0n) + unclaimed;
  }

  return claimableByToken;
}
```

### [Legacy Rewards (Pre-Merkl)](#legacy-rewards-pre-merkl)

**Legacy Rewards API Deprecated**

The `rewards.morpho.org` API has been deprecated. If you or your users have unclaimed rewards from historical Morpho programs (pre-Merkl migration), they can be claimed directly through the legacy rewards lookup app:

👉 **[rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/)**

All new reward programs are distributed exclusively via [Merkl](https://app.merkl.xyz/). See the [Merkl documentation](https://docs.merkl.xyz/) for integration details.

## [Performance Considerations](#performance-considerations)

### [Caching](#caching)

**Vault/Market Rewards (Morpho API):**

- Cache for 5-15 minutes
- Rewards rates change infrequently

**User Merkl Rewards:**

- Cache for 5-10 minutes
- Updates every 8 hours, but users expect fresh data

### [Parallel Fetching](#parallel-fetching)

Always fetch from multiple APIs in parallel:

```
const [vaultData, merklRewards] = await Promise.all([
  fetchVaultFromMorphoAPI(vaultAddress),
  fetchMerklRewards(userAddress),
]);
```

### [Error Handling](#error-handling)

```
async function fetchRewardsSafely(userAddress: string) {
  try {
    const merkl = await fetchMerklRewards(userAddress);
    return merkl;
  } catch (error) {
    console.error("Merkl API error:", error);
    return {}; // Fallback to empty
  }
}
```

## [API Rate Limits](#api-rate-limits)

Be mindful of rate limits:

| API | Rate Limit | Notes |
| --- | --- | --- |
| Morpho API | 5k / 5 min | Use responsibly |
| Merkl API | [10 request / second](https://docs.merkl.xyz/integrate-merkl/app) | Cache responses |

**Best Practice:** Cache aggressively and fetch only when needed.

## [Next Steps](#next-steps)

- **Display rewards**: Follow the [Integrate Display tutorial](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/)
- **Enable claiming**: See the [Claim Rewards tutorial](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/)

## [Resources](#resources)

- **Morpho API Playground**: [api.morpho.org/graphql](https://api.morpho.org/graphql)
- **Merkl Docs**: [docs.merkl.xyz/integrate-merkl/app](https://docs.merkl.xyz/integrate-merkl/app)
- **Legacy Rewards Lookup**: [rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/)

[Create a Rewards Program

Previous Page

](https://docs.morpho.org/developers/rewards/tutorials/create-program/)[Claim Rewards

Next Page

](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/)