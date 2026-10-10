# Rewards

> Source: https://docs.morpho.org/developers/api/rewards

---

# Rewards

Enterprise API accessFor enterprise access, send requests to `https://private.api.morpho.org` with your API key in the `x-api-key` header. [Request an API key](https://docs.morpho.org/request-api-key/).

## [Endpoints](#endpoints)

There are several endpoints to get information about rewards:

1. Morpho API: [https://api.morpho.org/graphql](https://api.morpho.org/graphql)
2. Merkl API: [https://api.merkl.xyz/docs](https://api.merkl.xyz/docs) (external)

You can read more about Rewards integration in your product in the dedicated section [here](https://docs.morpho.org/developers/rewards/get-started/).

For Merkl API usage with user rewards, see [Fetch Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/).

## [Legacy Rewards API (Deprecated)](#legacy-rewards-api-deprecated)

**Legacy Rewards API Deprecated**

The `rewards.morpho.org` API has been deprecated. If you or your users have unclaimed rewards from historical Morpho programs (pre-Merkl migration), they can be claimed directly through the legacy rewards lookup app:

👉 **[rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/)**

All new reward programs are distributed exclusively via [Merkl](https://app.merkl.xyz/protocols/morpho?tokenType=all&sort=tvl-desc). See the [Merkl documentation](https://docs.merkl.xyz/) for integration details.

## [Morpho Vault V2](#morpho-vault-v2)

For rewards data, the Morpho API retrieves information from the Merkl API.

```
query VaultV2Rewards($address: String!, $chainId: Int!) {
  vaultV2ByAddress(address: $address, chainId: $chainId) {
    address
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

Morpho Vault V2 rewards are pre-aggregated by the API. The `rewards` field already includes all reward sources across all adapters. See [Fetch Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/#fetching-morpho-vault-v2-rewards) for a complete walkthrough.

## [Morpho Vault V1](#morpho-vault-v1)

### [Rewards received through Vault programs](#rewards-received-through-vault-programs)

```
{
  vaults(where: { chainId_in: [8453] }) {
    items {
      state {
        allRewards {
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
}
```

### [Rewards per allocated market](#rewards-per-allocated-market)

```
{
  marketPositions(
    where: { userAddress_in: ["0xEbFA750279dEfa89b8D99bdd145a016F6292757b"] }
  ) {
    items {
      supplyAssets
      market {
        marketId
        loanAsset {
          name
          symbol
        }
        collateralAsset {
          name
          symbol
        }
        lltv
        oracle {
          address
        }
        irmAddress
        state {
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
  }
}
```

### [Complete Vault Rewards](#complete-vault-rewards)

To retrieve the rewards that a Morpho Vault V1 inherits, you have to check both the vault-level rewards and the rewards inherited from the allocated markets:

```
query VaultByAddress($address: String!, $chainId: Int!) {
  vaultByAddress(address: $address, chainId: $chainId) {
    address
    state {
      allRewards {
        asset {
          address
          name
          chain {
            id
          }
        }
        supplyApr
      }
      allocation {
        market {
          marketId
          state {
            rewards {
              supplyApr
              asset {
                address
                chain {
                  id
                }
              }
            }
          }
        }
        supplyAssetsUsd
      }
    }
    chain {
      id
    }
  }
}
```

**Variables example:**

```
{
  "address": "0x9aB2d181E4b87ba57D5eD564D3eF652C4E710707",
  "chainId": 8453
}
```

You can then compute the overall Morpho Vault V1 rewards following [the Morpho Vault rewards computation](https://docs.morpho.org/developers/earn/tutorials/get-data/#apy-native--rewards).

## [Morpho Markets](#morpho-markets)

```
{
  markets(orderBy: SupplyAssetsUsd, orderDirection: Desc) {
    items {
      marketId
      state {
        rewards {
          supplyApr
          borrowApr
          asset {
            address
            chain {
              id
            }
          }
        }
      }
    }
  }
}
```

#### Explanation of Fields

- `supplyApr`: The annual percentage rate for supplying tokens, available if the reward token is priced.
- `borrowApr`: The annual percentage rate for borrowing tokens, available if the reward token is priced.

For any questions on how to integrate the data, feel free to message Morpho via the chatbox on **[help.morpho.org](https://help.morpho.org)**.

[Vault V2 Public Allocator

Previous Page

](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/)[Changelog

Next Page

](https://docs.morpho.org/developers/api/changelog/)