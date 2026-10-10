# Morpho Blue

> Source: https://docs.morpho.org/developers/api/morpho

---

# Morpho Blue

Enterprise API accessFor enterprise access, send requests to `https://private.api.morpho.org` with your API key in the `x-api-key` header. [Request an API key](https://docs.morpho.org/request-api-key/).

## [How to query Morpho Blue data with the API?](#how-to-query-morpho-blue-data-with-the-api)

Each example below is available as **REST** (selected by default) or **GraphQL** — use the tabs to switch.

- **REST** calls use public `GET` requests against `https://api.morpho.org` with standard public rate limits. Markets are addressed by a `<chainId>:<marketId>` selector and tokens by `<chainId>:<address>`. REST provides single-entity reads, a cursor-paginated market list through `GET /v1/blue/markets`, and versioned lists of a user's vault positions. Aggregate cross-market overviews, oracle feed composition, USD values, and reward APRs still come from **GraphQL**.
- **GraphQL** queries run against the Playground at [https://api.morpho.org/graphql](https://api.morpho.org/graphql). By default the API returns only the first 100 results and reads from the Ethereum network.

## [Discovery and Listing](#discovery-and-listing)

### [Markets List](#markets-list)

REST APIGraphQL`GET /v1/blue/markets`

```
curl -sS "https://api.morpho.org/v1/blue/markets?chain_id=8453&listed=true&limit=100" \
  -H "accept: application/json"
```

REST lists markets with cursor pagination and supports `chain_id`, `loan_token`, `collateral_token`, and `listed` filters. It does not expose the GraphQL API's broader sorting and aggregate filters.

All MarketsListed Markets
```
query {
  markets {
    items {
      marketId
      lltv
      oracle {
        address
      }
      irmAddress
      loanAsset {
        address
        symbol
        decimals
      }
      collateralAsset {
        address
        symbol
        decimals
      }
      state {
        borrowAssets
        supplyAssets
        fee
        utilization
      }
    }
  }
}
```

```
query {
  markets(where: { listed: true }) {
    items {
      marketId
      listed
      lltv
      oracle {
        address
      }
      irmAddress
      loanAsset {
        address
        symbol
        decimals
      }
      collateralAsset {
        address
        symbol
        decimals
      }
      state {
        borrowAssets
        supplyAssets
        fee
        utilization
      }
    }
  }
}
```

### [Market Parameters](#market-parameters)

REST APIGraphQL`GET /v0/blue/markets/{market-selector}`

```
curl -sS "https://api.morpho.org/v0/blue/markets/8453:0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836" \
  -H "accept: application/json"
```

REST reads one market at a time by `<chainId>:<marketId>`. The response gives the immutable config: `loan_token`, `collateral_token`, `oracle_address`, `irm_address`, and `lltv_wad`. Use `GET /v1/blue/markets` to enumerate and filter across markets by `chain_id`, `loan_token`, `collateral_token`, and `listed`.

All MarketsSpecific Market
```
query {
  markets(
    first: 100
    orderBy: SupplyAssetsUsd
    orderDirection: Desc
    where: { chainId_in: [1, 8453] }
  ) {
    items {
      marketId
      loanAsset { address }
      collateralAsset { address }
      lltv
      irmAddress
      oracle {
        address
      }
    }
  }
}
```

```
query {
  marketById(
    marketId: "0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836"
    chainId: 8453
  ) {
    marketId
    loanAsset { address }
    collateralAsset { address }
    lltv
    irmAddress
    oracle {
      address
    }
  }
}
```

## [Market Metrics](#market-metrics)

### [Total Collateral, Borrow & Supply](#total-collateral-borrow--supply)

REST APIGraphQL`GET /v0/blue/markets/{market-selector}/state`

```
curl -sS "https://api.morpho.org/v0/blue/markets/8453:0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836/state" \
  -H "accept: application/json"
```

`/state` returns `total_supply_assets`, `total_borrow_assets`, their share counts (`total_supply_shares`, `total_borrow_shares`), and `fee_wad`. USD-denominated values and aggregate collateral totals are GraphQL-only.

All MarketsSpecific Market
```
query {
    markets(
      first: 100
      orderBy: SupplyAssetsUsd
      orderDirection: Desc
      where: { chainId_in: [1, 8453] }
    ) {
      items {
        marketId
        state {
          collateralAssets
          collateralAssetsUsd
          borrowAssets
          borrowAssetsUsd
          supplyAssets
          supplyAssetsUsd
          liquidityAssets
          liquidityAssetsUsd
        }
      }
    }
  }
```

```
query {
  marketById(
    marketId: "0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836"
    chainId: 8453
  ) {
    state {
      collateralAssets
      borrowAssets
      supplyAssets
      liquidityAssets
    }
  }
}
```

### [Market APY (Native & Rewards)](#market-apy-native--rewards)

REST APIGraphQL`GET /v0/blue/markets/{market-selector}/apy-averages`

```
curl -sS "https://api.morpho.org/v0/blue/markets/8453:0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836/apy-averages" \
  -H "accept: application/json"
```

`/apy-averages` returns `supply_apy_averages` and `borrow_apy_averages`, each keyed by fixed trailing windows (`24h`, `7d`, `30d`, `90d`, `1y`). Values **exclude rewards** — reward APRs are GraphQL-only.

All MarketsSpecific Market
```
query {
  markets(
    first: 100
    orderBy: SupplyAssetsUsd
    orderDirection: Desc
    where: { chainId_in: [1, 8453] }
  ) {
    items {
      marketId
      state {
        borrowApy
        avgBorrowApy
        avgNetBorrowApy
        supplyApy
        avgSupplyApy
        avgNetSupplyApy
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
```

```
query {
  marketById(
    marketId: "0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836"
    chainId: 8453
  ) {
    state {
      borrowApy
      avgBorrowApy
      avgNetBorrowApy
      supplyApy
      avgSupplyApy
      avgNetSupplyApy
      rewards {
        supplyApr
        borrowApr
      }
    }
  }
}
```

## [Asset Information](#asset-information)

### [Assets (Price & Yield)](#assets-price--yield)

REST APIGraphQL`GET /v0/tokens/{token-selector}`

`GET /v0/tokens/{token-selector}/price`

```
# Token identity + metadata
curl -sS "https://api.morpho.org/v0/tokens/1:0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0" \
  -H "accept: application/json"

# Canonical USD spot price
curl -sS "https://api.morpho.org/v0/tokens/1:0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0/price" \
  -H "accept: application/json"
```

REST reads one token at a time by `<chainId>:<address>`: `/tokens/{selector}` for identity/metadata and `/tokens/{selector}/price` for the USD spot price (`price`, `timestamp`, `provider`). Native yield (`yield.apr`) and multi-asset symbol filtering are GraphQL-only.

```
query GetAssetsWithPriceAndYield {
  assets(where: { symbol_in: ["wstETH", "WETH"], chainId_in: [1] }) {
    items {
      symbol
      address
      price(maxLag: 12) {
        usd
        timestamp
      }
      yield {
        apr
        lookback
      }
      chain {
        id
        network
      }
    }
  }
}
```

- `price.usd` is the current price of the asset in USD.
- `price.timestamp` is when the returned price was recorded.
- `maxLag` is the maximum lookback window in hours, from `0` to `24`; default is `12`.
- `yield.apr` is the asset APR, when available.
- `yield.lookback` is the lookback period used to compute the APR, in seconds.
- `yield` can be `null` when no native-yield data is available.
- USD prices are sourced from DefiLlama today, so availability and freshness can depend on DefiLlama coverage for the asset.

## [Position Tracking](#position-tracking)

### [User Positions](#user-positions)

#### [User All Markets Position](#user-all-markets-position)

REST APIGraphQL`GET /v0/blue/markets/{market-selector}/users/{user-address}/position`

`GET /v0/blue/markets/{market-selector}/users/{user-address}/position/performance`

```
# Current market position
curl -sS "https://api.morpho.org/v0/blue/markets/1:0x698fe98247a40c5771537b5786b2f3f9d78eb487b4ce4d75533cd0e94d88a115/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/position" \
  -H "accept: application/json"

# Realized and unrealized position performance
curl -sS "https://api.morpho.org/v0/blue/markets/1:0x698fe98247a40c5771537b5786b2f3f9d78eb487b4ce4d75533cd0e94d88a115/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/position/performance" \
  -H "accept: application/json"
```

REST returns a **single** user's position in a market — `collateral_assets`, `supply_shares`, and `borrow_shares` — keyed by `<chainId>:<marketId>` and user address. The performance route adds `supply_net_earnings_assets`, `supply_return_on_capital`, `borrow_net_cost_assets`, and `borrow_cost_on_capital` under average-cost accounting. Listing every position in a market, and USD-denominated values, are GraphQL-only.

```
query {
  marketPositions(
    first: 10,
    orderBy: BorrowShares,
    orderDirection: Desc
    where: {
      marketUniqueKey_in: ["0x698fe98247a40c5771537b5786b2f3f9d78eb487b4ce4d75533cd0e94d88a115"]
    }
  ) {
    items {
      user { address }
      state {
        collateral
        borrowAssets
        borrowAssetsUsd
      }
    }
  }
}
```

#### [User Market Position](#user-market-position)

REST APIGraphQL`GET /v0/blue/markets/{market-selector}/users/{user-address}/position`

`GET /v1/vaults-v2/users/{user-address}/positions`

```
# Market position
curl -sS "https://api.morpho.org/v0/blue/markets/1:0x698fe98247a40c5771537b5786b2f3f9d78eb487b4ce4d75533cd0e94d88a115/users/0x821880a3E2bac432d67E5155e72BB655Ef65fa5E/position" \
  -H "accept: application/json"

# Vault V2 positions
curl -sS "https://api.morpho.org/v1/vaults-v2/users/0x821880a3E2bac432d67E5155e72BB655Ef65fa5E/positions?chain_ids=1&active_only=true&limit=100" \
  -H "accept: application/json"
```

REST reads market positions one market at a time and lists a user's vault positions separately for V1 and V2. A combined cross-market/cross-vault overview and transaction history are GraphQL-only.

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

### [All Market Positions](#all-market-positions)

REST APIGraphQL`GET /v0/blue/markets/{market-selector}/users/{user-address}/position`

```
curl -sS "https://api.morpho.org/v0/blue/markets/1:0x698fe98247a40c5771537b5786b2f3f9d78eb487b4ce4d75533cd0e94d88a115/users/0xabcdefabcdefabcdefabcdefabcdefabcdefabcd/position" \
  -H "accept: application/json"
```

REST returns one user's position in a market (`collateral_assets`, `supply_shares`, `borrow_shares`). Listing every position in a market, and USD-denominated values, are GraphQL-only.

```
query {
  marketPositions(
    first: 10
    orderBy: SupplyShares
    orderDirection: Desc
    where: {
      marketUniqueKey_in: [
        "0x698fe98247a40c5771537b5786b2f3f9d78eb487b4ce4d75533cd0e94d88a115"
      ]
    }
  ) {
    items {
      market {
        marketId
        loanAsset {
          address
          symbol
        }
        collateralAsset {
          address
          symbol
        }
      }
      user {
        address
      }
      state {
        supplyShares
        supplyAssets
        supplyAssetsUsd
        borrowShares
        borrowAssets
        borrowAssetsUsd
        collateral
        collateralUsd
      }
    }
  }
}
```

## [Risk & Oracle Data](#risk--oracle-data)

### [Oracle Data](#oracle-data)

Oracle data is returned if the oracle's type is `ChainlinkOracle` or `ChainlinkOracleV2`.
`creationEvent` field is specific to `ChainlinkOracleV2` oracles.
More on oracles and `ChainlinkOracleV2` oracles in the oracle section [here](https://docs.morpho.org/learn/concepts/oracle/#morphochainlinkoraclev2-a-reference-implementation).

#### [All Markets](#all-markets)

REST APIGraphQL`GET /v0/oracles/{oracle-selector}/state`

```
curl -sS "https://api.morpho.org/v0/oracles/1:0x2a01EB9496094dA03c4E364Def50f5aD1280AD72/state" \
  -H "accept: application/json"
```

REST exposes the oracle's live quote — `price`, `last_updated_at`, `last_indexed_block` — by `<chainId>:<oracleAddress>`. The feed composition (`baseFeed*`, `quoteFeed*`, `scaleFactor`, vault conversions) is GraphQL-only.

```
query Markets($first: Int, $skip: Int, $orderBy: MarketOrderBy, $orderDirection: OrderDirection, $where: MarketFilters) {
  markets(first: $first, skip: $skip, orderBy: $orderBy, orderDirection: $orderDirection, where: $where) {
    items {
      marketId
      oracle {
        address
        type
        data {
          ... on MorphoChainlinkOracleData {
            baseFeedOne {
              address
            }
            baseFeedTwo {
              address
            }
            baseOracleVault {
              address
            }
            quoteFeedOne {
              address
            }
            quoteFeedTwo {
              address
            }
            scaleFactor
            vaultConversionSample
          }
          ... on MorphoChainlinkOracleV2Data {
            baseFeedOne {
              address
            }
            baseFeedTwo {
              address
            }
            baseOracleVault {
              address
            }
            baseVaultConversionSample
            quoteFeedOne {
              address
            }
            quoteFeedTwo {
              address
            }
            quoteOracleVault {
              address
            }
            quoteVaultConversionSample
            scaleFactor
          }
        }
        creationEvent {
          txHash
          timestamp
          blockNumber
        }
      }
    }
  }
}
```

With the following `variables` as example:

```
{
  "first": 100,
  "skip": 0,
  "orderBy": "SupplyAssetsUsd",
  "orderDirection": "Desc",
  "where": {
    "chainId_in": [
      1,
      8453
    ],
    "listed": true
  }
}
```

#### [Specific Market](#specific-market)

REST APIGraphQL`GET /v0/oracles/{oracle-selector}/state`

```
curl -sS "https://api.morpho.org/v0/oracles/1:0x2a01EB9496094dA03c4E364Def50f5aD1280AD72/state" \
  -H "accept: application/json"
```

REST exposes the oracle's live quote (`price`, `last_updated_at`, `last_indexed_block`) by `<chainId>:<oracleAddress>`; the feed composition is GraphQL-only.

```
query {
  marketById(
    marketId: "0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836"
    chainId: 8453
  ) {
    marketId
    oracle {
      address
      type
      creationEvent {
        txHash
        timestamp
        blockNumber
      }
      data {
        ... on MorphoChainlinkOracleV2Data {
          baseFeedOne {
            address
          }
          baseFeedTwo {
            address
          }
          baseOracleVault {
            address
          }
          baseVaultConversionSample
          quoteFeedOne {
            address
          }
          quoteFeedTwo {
            address
          }
          quoteOracleVault {
            address
          }
          quoteVaultConversionSample
          scaleFactor
        }
        ... on MorphoChainlinkOracleData {
          baseFeedOne {
            address
          }
          baseFeedTwo {
            address
          }
          baseOracleVault {
            address
          }
          quoteFeedOne {
            address
          }
          quoteFeedTwo {
            address
          }
          scaleFactor
          vaultConversionSample
        }
      }
    } 
  }
}
```

## [Historical Data](#historical-data)

Historical data is available through both REST and GraphQL, with different parameters for each:

- **REST** exposes trailing history via fixed `lookback` windows (`one_day`, `seven_days`, `thirty_days`, `ninety_days`, `one_year`, `inception`) passed as a query string on the relevant `/history` endpoint. It is per-market/per-vault; enumeration and USD-denominated series are GraphQL-only.
- **GraphQL** exposes historical data through the `historicalState` field, which takes `startTimestamp`, `endTimestamp`, and `interval` (`YEAR`, `QUARTER`, `MONTH`, `WEEK`, `DAY`, `HOUR`) as query variables — see the GraphQL tab in each example below.

The queries need to be backfilled to return proper data (i.e. the historical data needs to be indexed and stored). Some queries are not backfilled and are flagged as deprecated in [the Morpho API sandbox](https://api.morpho.org/graphql).

How to use the GraphQL `historicalState` variablesHere are the available variables when using a `historicalState` query:

- `startTimestamp`: beginning of the historical data in UNIX timestamp format,
- `endTimestamp`: end of the historical data in UNIX timestamp format,
- `interval`: interval of the historical data points (`YEAR`, `QUARTER`, `MONTH`, `WEEK`, `DAY`, `HOUR`).
Inputting these variables is not mandatory but it is advised to specify them to control the specific data returned.

If no variables are specified, the default values will be:

- `startTimestamp`: 0,
- `endTimestamp`: infinity,
- `interval`: will adjust according to `startTimestamp` and `endTimestamp` to return around 50 data points.

Note that the `historicalState` field is not accessible through the (multiple) markets(...) and vaults(...) list queries. Historical data is only available through individual market or vault queries like `market(id: "")`, `marketById`, `vault(id: "")` or `vaultByAddress`.

### [Historical APYs](#historical-apys)

REST APIGraphQL`GET /v0/blue/markets/{market-selector}/apy/history`

```
curl -sS "https://api.morpho.org/v0/blue/markets/8453:0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836/apy/history?lookback=thirty_days" \
  -H "accept: application/json"
```

REST returns trailing supply/borrow APY history via fixed `lookback` windows (`one_day`, `seven_days`, `thirty_days`, `ninety_days`, `one_year`, `inception`) instead of an arbitrary `startTimestamp`/`endTimestamp`/`interval`.

```
query MarketById($marketId: String!, $chainId: Int!, $options: TimeseriesOptions) {
  marketById(marketId: $marketId, chainId: $chainId) {
    historicalState {
      borrowApy(options: $options) {
        x
        y
      }
      supplyApy(options: $options) {
        x
        y
      }
    }
  }
}
```

With the following `variables`:

```
{
  "marketId": "0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836",
  "chainId": 8453,
  "options": {
    "startTimestamp": 1755420554,
    "endTimestamp": 1755506954,
    "interval": "HOUR"
  }
}
```

### [Historical Market States](#historical-market-states)

REST APIGraphQL`GET /v0/blue/markets/{market-selector}/state/history`

```
curl -sS "https://api.morpho.org/v0/blue/markets/1:0x608929d6de2a10bacf1046ff157ae38df5b9f466fb89413211efb8f63c63833a/state/history?lookback=thirty_days" \
  -H "accept: application/json"
```

`/state/history` returns trailing `total_supply_assets` / `total_borrow_assets` history via fixed `lookback` windows (`one_day` … `inception`). USD-denominated series are GraphQL-only.

```
query MarketApys($options: TimeseriesOptions) {
  marketById(
    marketId: "0x608929d6de2a10bacf1046ff157ae38df5b9f466fb89413211efb8f63c63833a"
    chainId: 1
  ) {
    marketId
    historicalState {
      supplyAssetsUsd(options: $options) {
        x
        y
      }
      borrowAssetsUsd(options: $options) {
        x
        y
      }
    }
  }
}
```

With the following `variables`:

```
"variables": {
"startTimestamp": 1707749700,
"endTimestamp": 1708354500,
"interval": HOUR,
}
```

### [Historical Asset Price](#historical-asset-price)

REST APIGraphQL`GET /v0/tokens/{token-selector}/price`

```
curl -sS "https://api.morpho.org/v0/tokens/1:0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0/price" \
  -H "accept: application/json"
```

REST returns the current USD spot price (`price`, `timestamp`, `provider`); a historical price series is GraphQL-only.

```
query {
  wstETHWeeklyPriceUsd: assetByAddress(
    address: "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
    chainId: 1
  ) {
    historicalPriceUsd(
      options: {
        startTimestamp: 1707749700
        endTimestamp: 1708354500
        interval: HOUR
      }
    ) {
      x
      y
    }
  }
}
```

All queries sent for `assetByAddress`, `marketById` and `vaultByAddress` should include the `chainId` parameter.

[Morpho Midnight

Previous Page

](https://docs.morpho.org/developers/api/morpho-midnight/)[Morpho Vaults

Next Page

](https://docs.morpho.org/developers/api/morpho-vaults/)