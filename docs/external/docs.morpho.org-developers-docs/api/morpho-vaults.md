# Morpho Vaults

> Source: https://docs.morpho.org/developers/api/morpho-vaults

---

# Morpho Vaults

Enterprise API accessFor enterprise access, send requests to `https://private.api.morpho.org` with your API key in the `x-api-key` header. [Request an API key](https://docs.morpho.org/request-api-key/).

## [How to query Morpho Vaults Data thanks to the API?](#how-to-query-morpho-vaults-data-thanks-to-the-api)

Each example below is available as **REST** (selected by default) or **GraphQL** — use the tabs to switch.

- **REST** calls use public `GET` requests against `https://api.morpho.org` with standard public rate limits. Entities are addressed by a `<chainId>:<address>` selector (e.g. `1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB`). REST returns single-entity reads — config, state, APY averages and history, allocation history, and positions — and exposes listed-vault discovery through `GET /v0/vaults-v1` and `GET /v0/vaults-v2`, plus user-position lists through `GET /v1/vaults-v1/users/{user-address}/positions` and `GET /v1/vaults-v2/users/{user-address}/positions`; the V2 position list excludes fee wrappers, while unlisted-vault discovery, USD-denominated values, and reward APRs come from **GraphQL**.
- **GraphQL** queries run against the Playground at [https://api.morpho.org/graphql](https://api.morpho.org/graphql) — paste any query below and run it.

## [Discovery and Listing](#discovery-and-listing)

### [Vaults List](#vaults-list)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v0/vaults-v2`

```
curl -sS "https://api.morpho.org/v0/vaults-v2?chain_ids=1&limit=100" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1`

```
curl -sS "https://api.morpho.org/v0/vaults-v1?chain_ids=1&limit=100" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1` and `GET /v0/vaults-v2` return cursor-paginated listed-vault directories. These lists are not complete enumerations of indexed vaults: V1 membership is listing-gated, and V2 returns listed instances only. Use GraphQL to include unlisted vaults.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2s(first: 1000, where: { chainId_in: [1, 8453] }) {
    items {
      address
      symbol
      name
      listed
      asset {
        id
        address
        decimals
      }
      chain {
        id
        network
      }
    }
  }
}
```

```
query {
  vaults(first: 1000, where: { chainId_in: [1, 8453] }) {
    items {
      address
      symbol
      name
      listed
      asset {
        id
        address
        decimals
      }
      chain {
        id
        network
      }
    }
  }
}
```

## [Vault Metrics](#vault-metrics)

### [Total Deposits & Assets](#total-deposits--assets)

#### [All Vaults](#all-vaults)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v1/vaults-v2/{vault-selector}/state`

```
curl -sS "https://api.morpho.org/v1/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/state" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}/state`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/state" \
  -H "accept: application/json"
```

REST returns one vault's totals. Enumerate listed vaults with `GET /v0/vaults-v1` or `GET /v0/vaults-v2`, then call `/state` for each vault; use GraphQL for unlisted vaults and USD-denominated values.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2s(first: 100) {
    items {
      address
      totalAssets
      totalAssetsUsd
      totalSupply
      liquidityUsd
      idleAssetsUsd
      }
    }
  }
```

```
query {
  vaults(first: 100, orderBy: TotalAssetsUsd, orderDirection: Desc) {
    items {
      address
      state {
        totalAssets
        totalAssetsUsd
        totalSupply
      }
    }
  }
}
```

#### [Specific Vault](#specific-vault)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v1/vaults-v2/{vault-selector}/state`

```
curl -sS "https://api.morpho.org/v1/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/state" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}/state`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/state" \
  -H "accept: application/json"
```

Returns `total_assets`, `total_supply`, and `withdrawable_assets`; V2 also returns `allocated_assets` and `idle_assets`. USD-denominated values are GraphQL-only.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    address
     totalAssets
      totalAssetsUsd
      totalSupply
      liquidity
      liquidityUsd
      idleAssetsUsd
  }
}
```

```
query {
  vaultByAddress(
    address: "0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB"
    chainId: 1
  ) {
    address
    state {
      totalAssets
      totalAssetsUsd
      totalSupply
    }
    liquidity {
      underlying
      usd
    }
  }
}
```

### [APY (Native + Rewards)](#apy-native--rewards)

#### [All Vaults](#all-vaults-1)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v1/vaults-v2/{vault-selector}/apy-averages`

```
curl -sS "https://api.morpho.org/v1/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/apy-averages?lookback=six_hours" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}/apy-averages`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/apy-averages?lookback=six_hours" \
  -H "accept: application/json"
```

`/apy-averages` returns the realized average `apy` from share-price evolution over the selected `lookback` (post-fee, excluding rewards). REST calculates one vault at a time; use the listed-vault routes for listed discovery, and GraphQL for unlisted vaults and reward APRs.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2s(first: 10) {
    items {
      address
      asset {
        yield {
          apr
        }
      }
      avgNetApyExcludingRewards
      avgNetApy
      performanceFee
      managementFee
      maxRate
      rewards {
        asset {
          address
          chain {
            id
          }
        }
        supplyApr
      }
    }
  }
}
```

```
query {
  vaults(first: 100, orderBy: TotalAssetsUsd, orderDirection: Desc) {
    items {
      address
      asset {
        yield {
          apr
        }
      }
      state {
        apy
        netApy
        netApyExcludingRewards
        avgNetApyExcludingRewards
        avgNetApy
        dailyApy: avgNetApyExcludingRewards(lookback: ONE_DAY)
        dailyNetApy: avgNetApy(lookback: ONE_DAY)
        weeklyApy: avgNetApyExcludingRewards(lookback: SEVEN_DAYS)
        weeklyNetApy: avgNetApy(lookback: SEVEN_DAYS)
        monthlyApy: avgNetApyExcludingRewards(lookback: THIRTY_DAYS)
        monthlyNetApy: avgNetApy(lookback: THIRTY_DAYS)
        allRewards {
          asset {
            address
            chain {
              id
            }
          }
          supplyApr
        }
        allocation {
          supplyAssets
          supplyAssetsUsd
          market {
            marketId
            state {
              rewards {
                asset {
                  address
                  chain {
                    id
                  }
                }
                supplyApr
                borrowApr
              }
            }
          }
        }
      }
    }
  }
}
```

#### [Specific Vault](#specific-vault-1)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v1/vaults-v2/{vault-selector}/apy-averages`

```
curl -sS "https://api.morpho.org/v1/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/apy-averages?lookback=six_hours" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}/apy-averages`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/apy-averages?lookback=six_hours" \
  -H "accept: application/json"
```

`/apy-averages` returns the realized average `apy` from share-price evolution over `?lookback=<one_hour|six_hours|one_day|seven_days|thirty_days|ninety_days|one_year|inception>` (post-fee, **excluding rewards**). Reward APRs and per-market allocation breakdowns are GraphQL-only.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    address
    asset {
      yield {
        apr
      }
    }
    avgNetApyExcludingRewards
    avgNetApy
    performanceFee
    managementFee
    maxRate
    rewards {
      asset {
        address
        chain {
          id
        }
      }
      supplyApr
    }
  }
}
```

```
query {
  vaultByAddress(
    address: "0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB"
    chainId: 1
  ) {
    address
    asset {
      yield {
        apr
      }
    }
    state {
      apy
      netApy
      netApyExcludingRewards
      avgNetApyExcludingRewards
      avgNetApy
      dailyApy: avgNetApyExcludingRewards(lookback: ONE_DAY)
      dailyNetApy: avgNetApy(lookback: ONE_DAY)
      weeklyApy: avgNetApyExcludingRewards(lookback: SEVEN_DAYS)
      weeklyNetApy: avgNetApy(lookback: SEVEN_DAYS)
      monthlyApy: avgNetApyExcludingRewards(lookback: THIRTY_DAYS)
      monthlyNetApy: avgNetApy(lookback: THIRTY_DAYS)
      allRewards {
        asset {
          address
          chain {
            id
          }
        }
        supplyApr
      }
      allocation {
        supplyAssets
        supplyAssetsUsd
        market {
          marketId
          state {
            rewards {
              asset {
                address
                chain {
                  id
                }
              }
              supplyApr
              borrowApr
            }
          }
        }
      }
    }
  }
}
```

### [Share Price (Token Value)](#share-price-token-value)

#### [All Vaults](#all-vaults-2)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v1/vaults-v2/{vault-selector}/state`

```
curl -sS "https://api.morpho.org/v1/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/state" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}/state`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/state" \
  -H "accept: application/json"
```

`/state` returns `share_price_ray` — the normalized share price scaled by RAY (1e27), i.e. one whole share quoted in whole underlying tokens. Use the REST lists to enumerate listed vaults; unlisted-vault discovery and USD-denominated share price are GraphQL-only.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2s(first: 10) {
    items {
      address
      totalSupply
      totalAssets
      sharePrice
    }
  }
}
```

```
query {
  vaults(first: 100, orderBy: TotalAssetsUsd, orderDirection: Desc) {
    items {
      address
      state {
        sharePriceNumber
        sharePriceUsd
      }
    }
  }
}
```

#### [Specific Vault](#specific-vault-2)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v1/vaults-v2/{vault-selector}/state`

```
curl -sS "https://api.morpho.org/v1/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/state" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}/state`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/state" \
  -H "accept: application/json"
```

`/state` returns `share_price_ray` — the normalized share price scaled by RAY (1e27), i.e. one whole share quoted in whole underlying tokens. USD-denominated share price is GraphQL-only.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    totalAssets
    totalSupply
    sharePrice
  }
}
```

```
query {
  vaultByAddress(
    address: "0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB"
    chainId: 1
  ) {
    address
    state {
      sharePriceNumber
      sharePriceUsd
    }
  }
}
```

## [Configuration & Curation](#configuration--curation)

### [Vault Parameters](#vault-parameters)

#### [All Vaults](#all-vaults-3)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v0/vaults-v2/{vault-selector}`

```
curl -sS "https://api.morpho.org/v0/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB" \
  -H "accept: application/json"
```

Returns the core on-chain config (`owner`, `curator`, `timelock_seconds`, fees; V1 adds `guardian`; V2 adds `adapter_registry`, `liquidity_adapter`, `gates`). REST lists enumerate listed vaults only. Use GraphQL for unlisted-vault discovery, allocator lists, curator metadata, `listed` status, and free-form metadata.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2s(first: 10) {
    items {
      address
      name
      listed
      metadata {
        description
        image
      }
      allocators {
        allocator {
          address
        }
      }
      owner {
        address
      }
      curators {
        items {
          addresses {
            address
          }
        }
      }
      sentinels {
        sentinel {
          address
        }
      }
      timelocks {
        duration
        selector
        functionName
      }
    }
  }
}
```

```
query {
  vaults(first: 100, orderBy: TotalAssetsUsd, orderDirection: Desc) {
    items {
      address
      name
      listed
      metadata {
        description
      }
      allocators {
        address
      }
      state {
        owner
        curator
        guardian
        timelock
        curators {
          name
          socials {
            type
            url
          }
          image
        }
      }
    }
  }
}
```

#### [Specific Vault](#specific-vault-3)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v0/vaults-v2/{vault-selector}`

```
curl -sS "https://api.morpho.org/v0/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB" \
  -H "accept: application/json"
```

Returns the core on-chain config: `owner`, `curator`, `timelock_seconds`, and fee setup (V1 adds `guardian`; V2 adds `adapter_registry`, `liquidity_adapter`, and `gates`). The allocators list, curator metadata, sentinels, `listed` status, and free-form `metadata` (description/image) are GraphQL-only.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    address
    name
    listed
    metadata {
      description
      image
    }
    allocators {
      allocator {
        address
      }
    }
    owner {
      address
    }
    curators {
      items {
        addresses {
          address
        }
      }
    }
    sentinels {
      sentinel {
        address
      }
    }
    timelocks {
      duration
      selector
      functionName
    }
  }
}
```

```
query {
  vaultByAddress(
    address: "0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB"
    chainId: 1
  ) {
    address
    name
    listed
    metadata {
      description
    }
    allocators {
      address
    }
    state {
      owner
      curator
      guardian
      timelock
      curators {
         name
        socials {
          type
          url
          }
        image
      }
    }
  }
}
```

### [Roles: Allocators & Sentinels](#roles-allocators--sentinels)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v0/vaults-v2/{vault-selector}`

```
# Vault config
curl -sS "https://api.morpho.org/v0/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145" \
  -H "accept: application/json"
```

The REST API spec does not document allocator or sentinel lists. Use the GraphQL example in the next tab to query these roles.

`GET /v0/vaults-v1/{vault-selector}`

```
# Vault config
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB" \
  -H "accept: application/json"
```

The REST API spec does not document an allocator list. Use the GraphQL example in the next tab. Morpho Vaults V1 has no sentinel role.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    address
    name
    allocators {
      allocator {
        address
      }
    }
    sentinels {
      sentinel {
        address
      }
    }
  }
}
```

```
query {
  vaultByAddress(
    address: "0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB"
    chainId: 1
  ) {
    address
    name
    allocators {
      address
    }
  }
}
```

## [Fee Wrapper](#fee-wrapper)

A Fee Wrapper is a Vault V2 configured in a specific, constrained mode that enables distribution channels to add a fee layer on top of an existing Morpho Vault V2.

### [FeeWrapper List](#feewrapper-list)

REST APIGraphQL`GET /v0/vaults-v2/{vault-selector}`

```
curl -sS "https://api.morpho.org/v0/vaults-v2/8453:0xd4468EF3745c315949a97090eD27b3F73b9b7C02" \
  -H "accept: application/json"
```

A fee wrapper is a Vault V2 — read it by `<chainId>:<address>` via the V2 endpoint. Listing all fee wrappers (filter by type) is GraphQL-only.

Unique FeeWrapperAll FeeWrappers
```
query VaultV2ByAddress {
  vaultV2ByAddress(
    address: "0xd4468EF3745c315949a97090eD27b3F73b9b7C02"
    chainId: 8453
  ) {
    type
    address
    name
  }
}
```

```
query VaultV2s {
  vaultV2s(skip: 0, first: 20, where: { type_in: [FeeWrapper] }) {
    items {
      address
      name
    }
  }
}
```

### [FeeWrapper Yield](#feewrapper-yield)

REST APIGraphQL`GET /v0/vaults-v2/{vault-selector}`

`GET /v1/vaults-v2/{vault-selector}/apy-averages`

```
# Config (performance / management fee setup)
curl -sS "https://api.morpho.org/v0/vaults-v2/8453:0xd4468EF3745c315949a97090eD27b3F73b9b7C02" \
  -H "accept: application/json"

# Realized average APY
curl -sS "https://api.morpho.org/v1/vaults-v2/8453:0xd4468EF3745c315949a97090eD27b3F73b9b7C02/apy-averages?lookback=six_hours" \
  -H "accept: application/json"
```

The config route (`GET /v0/vaults-v2/{selector}`) returns `performance_fee_wad`, `performance_fee_recipient`, `management_fee_wad`, and `management_fee_recipient`; `/apy-averages` returns realized average APY for the selected lookback. Reward APRs and historical share price are GraphQL-only.

Unique FeeWrapperAll FeeWrappers
```
query VaultV2ByAddress {
  vaultV2ByAddress(
    address: "0xd4468EF3745c315949a97090eD27b3F73b9b7C02"
    chainId: 8453
  ) {
    type
    apy
    avgNetApyExcludingRewards
    avgNetApy
    performanceFee
    performanceFeeRecipient
    managementFee
    managementFeeRecipient
    rewards {
      asset {
        symbol
        address
      }
      supplyApr
    }
  }
}
```

```
query VaultV2s {
  vaultV2s(skip: 0, first: 20, where: { type_in: [FeeWrapper] }) {
    items {
      type
      address
      apy
      avgNetApyExcludingRewards
      avgNetApy
      performanceFee
      performanceFeeRecipient
      managementFee
      managementFeeRecipient
      rewards {
        asset {
          symbol
          address
        }
        supplyApr
      }
    }
  }
}
```

## [Position Tracking](#position-tracking)

### [Vault Depositors](#vault-depositors)

#### [Specific Vault](#specific-vault-4)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v1/vaults-v2/users/{user-address}/positions`

```
curl -sS "https://api.morpho.org/v1/vaults-v2/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/positions?chain_ids=1&vault_addresses=0x04422053aDDbc9bB2759b248B574e3FCA76Bc145" \
  -H "accept: application/json"
```

`GET /v1/vaults-v1/users/{user-address}/positions`

```
curl -sS "https://api.morpho.org/v1/vaults-v1/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/positions?chain_ids=1&vault_addresses=0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB" \
  -H "accept: application/json"
```

REST lists one user's positions across the requested vaults; use GraphQL for the full depositor list of a vault.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    positions(first: 10, skip:0) {
      items {
        user {
          address
        }
        assets
        assetsUsd
        shares
      }
    }
    totalSupply
    asset {
      address
      symbol
    }
  }
}
```

```
query {
  vaultPositions(
    first: 10
    orderBy: Shares
    orderDirection: Desc
    where: { vaultAddress_in: ["0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB"] }
  ) {
    items {
      user {
        address
      }
      state {
        shares
        assets
        assetsUsd
      }
    }
  }
}
```

#### [Set of Vaults](#set-of-vaults)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v0/vaults-v2/{vault-selector}/users/{user-address}/position`

```
curl -sS "https://api.morpho.org/v0/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/position" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}/users/{user-address}/position`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/position" \
  -H "accept: application/json"
```

REST reads one (vault, user) position per request; use `GET /v1/vaults-v1/users/{user-address}/positions` or `GET /v1/vaults-v2/users/{user-address}/positions` to query a set of vaults at once. The V2 list excludes fee wrappers.

Morpho Vaults V2Morpho Vaults V1
```
query {
  vaultV2s(
    first: 10
    where: {
      chainId_in: [1]
      address_in: [
        "0xb576765fB15505433aF24FEe2c0325895C559FB2"
        "0x6dC58a0FdfC8D694e571DC59B9A52EEEa780E6bf"
      ]
    }
  ) {
    items {
      address
      name
      positions(first: 10, skip: 0) {
        items {
          user {
            address
          }
          assets
          assetsUsd
          shares
        }
        pageInfo {
          count
          countTotal
          skip
          limit
        }
      }
    }
    pageInfo {
      count
      countTotal
      skip
      limit
    }
  }
}
```

```
query {
  vaultPositions(
    first: 10
    orderBy: Shares
    orderDirection: Desc
    where: {
      vaultAddress_in: [
        "0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB"
        "0x73e65DBD630f90604062f6E02fAb9138e713edD9"
      ]
    }
  ) {
    items {
      vault {
        address
      }
      user {
        address
      }
      state {
        shares
        assets
        assetsUsd
      }
    }
  }
}
```

### [User Positions](#user-positions)

#### [User All Vaults Position](#user-all-vaults-position)

REST APIGraphQL`GET /v1/vaults-v2/users/{user-address}/positions`

`GET /v1/vaults-v1/users/{user-address}/positions`

```
# Vault V2 positions
curl -sS "https://api.morpho.org/v1/vaults-v2/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/positions?chain_ids=1&active_only=true&limit=100" \
  -H "accept: application/json"

# Vault V1 positions
curl -sS "https://api.morpho.org/v1/vaults-v1/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/positions?chain_ids=1&active_only=true&limit=100" \
  -H "accept: application/json"
```

REST lists every active vault position a user holds, separately for V1 and V2, with cursor pagination. The V2 list excludes fee wrappers.

```
query GetUserVaultPositions($address: String!, $chainId: Int!) {
  userByAddress(address: $address, chainId: $chainId) {
    address
    chain {
      id
    }
    vaultV2Positions {
      shares
      vault {
        address
        symbol
      }
    }
    vaultPositions {
      state {
        shares
      }
      vault {
        address
        symbol
      }
    }
  }
}
```

**Query Variables example:**

```
{
  "address": "USER_ADDRESS",
  "chainId": 8453
}
```

#### [User Market Position](#user-market-position)

REST APIGraphQL`GET /v1/vaults-v2/users/{user-address}/positions`

`GET /v1/vaults-v1/users/{user-address}/positions`

```
# Vault V2 positions
curl -sS "https://api.morpho.org/v1/vaults-v2/users/0x821880a3E2bac432d67E5155e72BB655Ef65fa5E/positions?chain_ids=1&active_only=true&limit=100" \
  -H "accept: application/json"

# Vault V1 positions
curl -sS "https://api.morpho.org/v1/vaults-v1/users/0x821880a3E2bac432d67E5155e72BB655Ef65fa5E/positions?chain_ids=1&active_only=true&limit=100" \
  -H "accept: application/json"
```

REST lists a user's vault positions by version; the V2 list excludes fee wrappers. Market positions still require explicit market IDs, and a combined cross-vault/cross-market overview and transaction history are GraphQL-only.

```
query {
  userByAddress(
    chainId: 1
    address: "0x821880a3E2bac432d67E5155e72BB655Ef65fa5E"
  ) {
    address
    marketPositions {
      market {
        marketId
      }
      state {
        borrowAssets
        borrowAssetsUsd
        supplyAssets
        supplyAssetsUsd
      }
    }
    vaultPositions {
      vault {
        address
        name
      }
      state {
        assets
        assetsUsd
        shares
      }
    }
    vaultV2Positions {
      vault {
        address
        name
      }
      assets
      assetsUsd
      shares
    }
  }
  vaultV1Transactions(
    first: 10
    orderBy: Time
    orderDirection: Desc
    where: {
      userAddress_in: ["0x821880a3E2bac432d67E5155e72BB655Ef65fa5E"]
      chainId_in: [1]
    }
  ) {
    items {
      txHash
      timestamp
      type
    }
  }
  marketTransactions(
    first: 10
    orderBy: Timestamp
    orderDirection: Desc
    where: {
      userAddress_in: ["0x821880a3E2bac432d67E5155e72BB655Ef65fa5E"]
      chainId_in: [1]
    }
  ) {
    items {
      txHash
      timestamp
      type
    }
  }
  vaultV2transactions(
    first: 10
    orderBy: Time
    orderDirection: Desc
    where: {
      userAddress_in: ["0x821880a3E2bac432d67E5155e72BB655Ef65fa5E"]
      chainId_in: [1]
    }
  ) {
    items {
      txHash
      timestamp
      type
      shares
      assets
      vault {
        address
        name
      }
    }
  }
}
```

### [User Earnings](#user-earnings)

#### [Earnings Across All Vaults](#earnings-across-all-vaults)

REST APIGraphQL`GET /v0/vaults-v2/{vault-selector}/users/{user-address}/position/performance`

`GET /v0/vaults-v1/{vault-selector}/users/{user-address}/position/performance`

```
# Vault V2 performance
curl -sS "https://api.morpho.org/v0/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/position/performance" \
  -H "accept: application/json"

# Vault V1 performance
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/position/performance" \
  -H "accept: application/json"
```

`/position/performance` returns per-vault `net_earnings_assets` (≈ pnl) and `return_on_capital` (≈ roe); the aggregate across all vaults is GraphQL-only.

```
query {
  userByAddress(address: "USERADDRESS", chainId: 1) {
    vaultV2Positions {
      vault {
        name
        address
      }
      assets
      assetsUsd
      shares
      pnl
      pnlUsd
      roe # time-weighted return since inception (non-annualized)
    }
    vaultPositions {
      vault {
        name
        address
      }
      state {
        assets
        assetsUsd
        shares
        pnl
        pnlUsd
        roe # time-weighted return since inception (non-annualized)
      }
    }
  }
}
```

#### [Earnings on a Specific Vault](#earnings-on-a-specific-vault)

REST APIGraphQLMorpho Vault V2Morpho Vault V1`GET /v0/vaults-v2/{vault-selector}/users/{user-address}/position`

`GET /v0/vaults-v2/{vault-selector}/users/{user-address}/position/performance`

```
# Position: shares + assets
curl -sS "https://api.morpho.org/v0/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/position" \
  -H "accept: application/json"

# Performance: net earnings + return on capital
curl -sS "https://api.morpho.org/v0/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/position/performance" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}/users/{user-address}/position`

`GET /v0/vaults-v1/{vault-selector}/users/{user-address}/position/performance`

```
# Position: shares + assets
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/position" \
  -H "accept: application/json"

# Performance: net earnings + return on capital
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/position/performance" \
  -H "accept: application/json"
```

`/position` returns `shares` and `assets`; `/position/performance` returns `net_earnings_assets` (≈ `pnl`) and `return_on_capital` (≈ `roe` — time-weighted since inception, non-annualized). USD-denominated values are GraphQL-only.

Morpho Vault V2Morpho Vault V1
```
query {
  vaultV2PositionByAddress(
    userAddress: "USERADDRESS"
    vaultAddress: "MORPHOVAULTV2ADDRESS"
    chainId: 1
  ) {
    vault {
      name
      address
    }
    assets
    assetsUsd
    shares
    pnl
    pnlUsd
    roe # time-weighted return since inception (non-annualized)
  }
}
```

```
query {
  vaultPositions(where: {
    userAddress_in: ["USERADDRESS"]
    vaultAddress_in: ["MORPHOVAULTV1ADDRESS"]
    chainId_in: [1]
  }) {
    items {
      vault {
        name
        address
      }
      state {
        assets
        assetsUsd
        shares
        pnl
        pnlUsd
        roe # time-weighted return since inception (non-annualized)
      }
    }
  }
}
```

## [Historical Data](#historical-data)

### [APY Historical State](#apy-historical-state)

#### [All Vaults](#all-vaults-4)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v0/vaults-v2/{vault-selector}/apy/history`

```
curl -sS "https://api.morpho.org/v0/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/apy/history?lookback=thirty_days" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}/apy/history`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB/apy/history?lookback=thirty_days" \
  -H "accept: application/json"
```

REST exposes trailing history via fixed `lookback` windows (`one_day`, `seven_days`, `thirty_days`, `ninety_days`, `one_year`, `inception`) and is per-vault. Use the REST lists for listed-vault discovery; unlisted-vault discovery and cross-vault history queries are GraphQL-only.

Morpho Vaults V2Morpho Vaults V1
```
query VaultV2Apys($options: TimeseriesOptions) {
  vaultV2s(first: 10, orderBy: TotalAssetsUsd, orderDirection: Desc) {
    items {
      address
      name
      historicalState {
        avgApy(options: $options, lookbackHours: 24) {
          x
          y
        }
        avgNetApy(options: $options, lookbackHours: 24) {
          x
          y
        }
      }
    }
  }
}
```

```
query VaultApys($options: TimeseriesOptions) {
  vaults(first: 10, orderBy: TotalAssetsUsd, orderDirection: Desc) {
    items {
      address
      name
      historicalState {
        apy(options: $options) {
          x
          y
        }
        netApy(options: $options) {
          x
          y
        }
      }
    }
  }
}
```

#### [Specific Vault](#specific-vault-5)

REST APIGraphQLMorpho Vaults V2Morpho Vaults V1`GET /v0/vaults-v2/{vault-selector}/apy/history`

```
curl -sS "https://api.morpho.org/v0/vaults-v2/1:0x04422053aDDbc9bB2759b248B574e3FCA76Bc145/apy/history?lookback=thirty_days" \
  -H "accept: application/json"
```

`GET /v0/vaults-v1/{vault-selector}/apy/history`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0x73e65DBD630f90604062f6E02fAb9138e713edD9/apy/history?lookback=thirty_days" \
  -H "accept: application/json"
```

REST exposes trailing history via fixed `lookback` windows (`one_day`, `seven_days`, `thirty_days`, `ninety_days`, `one_year`, `inception`) rather than an arbitrary `startTimestamp`/`endTimestamp`/`interval`.

Morpho Vaults V2Morpho Vaults V1
```
query VaultV2Apys($options: TimeseriesOptions) {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    address
    name
    historicalState {
      avgApy(options: $options, lookbackHours: 24) {
        x
        y
      }
      avgNetApy(options: $options, lookbackHours: 24) {
        x
        y
      }
    }
  }
}
```

```
query VaultApys($options: TimeseriesOptions) {
  vaultByAddress(address: "0x73e65DBD630f90604062f6E02fAb9138e713edD9") {
    address
    name
    historicalState {
      apy(options: $options) {
        x
        y
      }
      netApy(options: $options) {
        x
        y
      }
    }
  }
}
```

**Query Variables:**

```
{
  "options": {
    "startTimestamp": 1768211594,
    "endTimestamp": 1768384394,
    "interval": "DAY"
  }
}
```

### [Historical Allocation (Morpho Vaults V1)](#historical-allocation-morpho-vaults-v1)

REST APIGraphQL`GET /v0/vaults-v1/{vault-selector}/allocations/history`

```
curl -sS "https://api.morpho.org/v0/vaults-v1/1:0x73e65DBD630f90604062f6E02fAb9138e713edD9/allocations/history?lookback=thirty_days" \
  -H "accept: application/json"
```

REST returns per-market allocation history for a **single** vault via fixed `lookback` windows; append `&market_id=<id>` to filter to one market. Listing allocations across all vaults and USD-denominated series are GraphQL-only.

All VaultsSpecific Vault
```
query Vaults($options: TimeseriesOptions) {
  vaults (first: 10, skip: 0, orderBy: TotalAssetsUsd, orderDirection: Desc) {
    items {
      address
      name
      historicalState {
        allocation {
          market {
            marketId
          }
          supplyAssets(options: $options) {
            x
            y
          }
          supplyAssetsUsd(options: $options)  {
            x
            y
          }
        }
      } 
    }
  }
}
```

```
query VaultApys($options: TimeseriesOptions) {
  vaultByAddress(address: "0x73e65DBD630f90604062f6E02fAb9138e713edD9") {
    address
    historicalState {
      allocation {
        market {
          marketId
        }
        supplyAssets(options: $options) {
          x
          y
        }
        supplyAssetsUsd(options: $options) {
          x
          y
        }
      }
    }
  }
}
```

**Query Variables:**

```
{
  "options": {
    "startTimestamp": 1768211594,
    "endTimestamp": 1768384394,
    "interval": "DAY"
  }
}
```

[Morpho Blue

Previous Page

](https://docs.morpho.org/developers/api/morpho/)[Vault V2 Public Allocator

Next Page

](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/)