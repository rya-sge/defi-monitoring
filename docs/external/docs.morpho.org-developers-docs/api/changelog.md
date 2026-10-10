# Morpho API Changelog

> Source: https://docs.morpho.org/developers/api/changelog

---

# Morpho API Changelog

This page tracks Morpho API deprecations and removals across the GraphQL and REST APIs.

The Morpho API exposes deprecation warnings directly in GraphQL responses, letting integrators detect deprecated fields at query time before they are removed. See [Deprecation warnings](https://docs.morpho.org/developers/api/get-started/#deprecation-warnings) for details on how to use them.

table {
  width: 100%;
  table-layout: fixed;
}
th, td {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  vertical-align: top;
}
code {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}
details { margin: 1rem 0 1.5rem; }
details > summary {
  cursor: pointer;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

In this changelog:

.tc-intro th:nth-child(1), .tc-intro td:nth-child(1) { width: 22%; } .tc-intro th:nth-child(2), .tc-intro td:nth-child(2) { width: 78%; }

| Change type | Meaning |
| --- | --- |
| **Field deprecation** | A field that is still present in the schema but not maintained anymore. Will be removed at a later stage. |
| **Field removal** | A field that is or will be removed from the schema. Using this field in a query will throw an error. |

## [March 1, 2027 - API fields removal](#march-1-2027---api-fields-removal)

View scheduled field removalsThe below fields will be fully removed from the Morpho API on **March 1, 2027**

.tc-20270301 th:nth-child(1), .tc-20270301 td:nth-child(1) { width: 45%; } .tc-20270301 th:nth-child(2), .tc-20270301 td:nth-child(2) { width: 35%; } .tc-20270301 th:nth-child(3), .tc-20270301 td:nth-child(3) { width: 20%; }
| **Deprecated Field** | **Replacement** | **Deprecation date** |
| --- | --- | --- |
| `IncorrectOracleConfigurationMarketWarningMetadata.` `expectedScaleFactor` | N/A | 2026-08-31 |
| `IncorrectOracleConfigurationMarketWarningMetadata.` `expectedScaleFactorExponent` | N/A | 2026-08-31 |
| `IncorrectOracleConfigurationMarketWarningMetadata.` `scaleFactor` | N/A | 2026-08-31 |
| `IncorrectOracleConfigurationMarketWarningMetadata.` `type` | N/A | 2026-08-31 |

## [October 21, 2026 - API fields removal](#october-21-2026---api-fields-removal)

View scheduled field removalsThe below fields will be fully removed from the Morpho API on **October 21, 2026**

.tc-oct21 th:nth-child(1), .tc-oct21 td:nth-child(1) { width: 52%; } .tc-oct21 th:nth-child(2), .tc-oct21 td:nth-child(2) { width: 28%; } .tc-oct21 th:nth-child(3), .tc-oct21 td:nth-child(3) { width: 20%; }
| **Deprecated Field** | **Replacement** | **Deprecation date** |
| --- | --- | --- |
| `Asset.priceUsd` | `price.usd` | 2026-03-19 |
| `Market.oracleAddress` | `oracle.address` | 2025-10-14 |
| `Market.targetBorrowUtilization` | N/A | 2026-04-13 |
| `Market.targetWithdrawUtilization` | N/A | 2026-04-13 |
| `VaultMetadata.forumLink` | N/A | 2026-04-10 |
| `VaultV2Metadata.forumLink` | N/A | 2026-04-10 |

## [September 30, 2026 - API fields removal](#september-30-2026---api-fields-removal)

View scheduled field removalsThe below fields will be fully removed from the Morpho API on **September 30, 2026**

.tc-sep30 th:nth-child(1), .tc-sep30 td:nth-child(1) { width: 45%; } .tc-sep30 th:nth-child(2), .tc-sep30 td:nth-child(2) { width: 35%; } .tc-sep30 th:nth-child(3), .tc-sep30 td:nth-child(3) { width: 20%; }
| **Deprecated Field** | **Replacement** | **Deprecation date** |
| --- | --- | --- |
| `Asset.oraclePriceUsd` | `price.usd` | 2026-02-05 |
| `Asset.spotPriceEth` | N/A | 2026-01-20 |
| `Asset.totalSupply` | N/A | 2026-01-20 |
| `Market.monthlyApys` | `state.monthlyApys` | 2025-09-09 |
| `Market.oracleInfo` | `oracle.data` | 2025-10-14 |
| `VaultState.dailyApy` | `avgNetApyExcludingRewards` | 2026-02-15 |
| `VaultState.dailyNetApy` | `avgNetApy` | 2026-02-15 |
| `VaultState.netApyWithoutRewards` | `netApyExcludingRewards` | 2026-02-15 |
| `VaultState.rewards` | `allRewards` | 2026-03-30 |
| `VaultState.weeklyApy` | `avgNetApyExcludingRewards` | 2026-02-15 |
| `VaultState.weeklyNetApy` | `avgNetApy` | 2026-02-15 |

## [August 26, 2026 - API fields removal](#august-26-2026---api-fields-removal)

View scheduled field removalsThe below fields will be fully removed from the Morpho API on **August 26, 2026**

.tc-aug26 th:nth-child(1), .tc-aug26 td:nth-child(1) { width: 55%; } .tc-aug26 th:nth-child(2), .tc-aug26 td:nth-child(2) { width: 25%; } .tc-aug26 th:nth-child(3), .tc-aug26 td:nth-child(3) { width: 20%; }
| **Deprecated Field** | **Replacement** | **Deprecation date** |
| --- | --- | --- |
| `Market.dailyApys` | `state.dailyApys` | 2025-09-09 |
| `Query.oracleFeedByAddress` | N/A | 2026-07-10 |
| `Query.oracleFeeds` | N/A | 2026-07-10 |
| `Query.oracleVaultByAddress` | N/A | 2026-07-10 |
| `Query.oracleVaults` | N/A | 2026-07-10 |
| `Query.publicAllocator` | N/A | 2026-07-10 |
| `Query.publicAllocators` | N/A | 2026-07-10 |
| `Query.vaultFactories` | N/A | 2026-07-10 |
| `Query.vaultFactoryByAddress` | N/A | 2026-07-10 |
| `Query.vaultV2Factories` | N/A | 2026-07-10 |
| `Query.vaultV2MetaMorphoAdapterFactories` | N/A | 2026-07-10 |
| `VaultV2.avgApy` | `avgNetApyExcludingRewards` | 2026-02-15 |

## [August 26, 2026 - Core REST API endpoints removal](#august-26-2026---core-rest-api-endpoints-removal)

View removal detailsImplemented on August 26, 2026

The **Core REST API** removed the following endpoints:

.tc-rest-aug26-core th:nth-child(1), .tc-rest-aug26-core td:nth-child(1) { width: 45%; } .tc-rest-aug26-core th:nth-child(2), .tc-rest-aug26-core td:nth-child(2) { width: 55%; }
| API | Change |
| --- | --- |
| `core` | Removed `GET /v0/vaults-v1/{vault-selector}/apy` and `GET /v0/vaults-v2/{vault-selector}/apy`. |
| `core` | Removed the `VaultApyResponse` schema. |

## [July 29, 2026 - API fields removal](#july-29-2026---api-fields-removal)

View scheduled field removalsThe below fields will be fully removed from the Morpho API on **July 29, 2026**

.tc-jul29 th:nth-child(1), .tc-jul29 td:nth-child(1) { width: 40%; } .tc-jul29 th:nth-child(2), .tc-jul29 td:nth-child(2) { width: 40%; } .tc-jul29 th:nth-child(3), .tc-jul29 td:nth-child(3) { width: 20%; }
| **Deprecated Field** | **Replacement** | **Deprecation date** |
| --- | --- | --- |
| `Asset.isWhitelisted` | `isListed` | 2025-12-22 |
| `Market.collateralPrice` | `state.price` | 2025-09-09 |
| `Market.creatorAddress` | `morphoBlue` | 2026-01-27 |
| `Query.transactions` | `vaultV2transactions`, `vaultV1Transactions`, `marketTransactions` | 2026-04-23 |
| `User.transactions` | `vaultV1Transactions`, `marketTransactions` | 2026-04-23 |
| `VaultState.lastTotalAssets` | `totalAssets` | 2026-04-16 |

## [June 24, 2026 - API fields removal](#june-24-2026---api-fields-removal)

View scheduled field removalsThe below fields will be fully removed from the Morpho API on **June 24, 2026**

.tc-jun24 th:nth-child(1), .tc-jun24 td:nth-child(1) { width: 45%; } .tc-jun24 th:nth-child(2), .tc-jun24 td:nth-child(2) { width: 35%; } .tc-jun24 th:nth-child(3), .tc-jun24 td:nth-child(3) { width: 20%; }
| **Deprecated Field** | **Replacement** | **Deprecation date** |
| --- | --- | --- |
| `Asset.historicalSpotPriceEth` | N/A | 2026-01-20 |
| `Asset.riskAnalysis` | N/A | 2026-01-20 |
| `AssetsFilters.credoraRiskScore_gte` | N/A | 2025-11-26 |
| `AssetsFilters.credoraRiskScore_lte` | N/A | 2025-11-26 |
| `Curator.url` | `socials.url` | 2025-09-09 |
| `Market.concentration` | N/A | 2025-09-09 |
| `Market.id` | `marketId` and `chain.id` | 2026-05-14 |
| `Market.oracleFeed` | `oracle.data` | 2025-10-14 |
| `Market.riskAnalysis` | N/A | 2025-09-09 |
| `MarketConcentration.borrowHhi` | N/A | 2026-01-28 |
| `MarketConcentration.supplyHhi` | N/A | 2026-01-28 |
| `MarketFilters.credoraRiskScore_gte` | N/A | 2025-11-26 |
| `MarketFilters.credoraRiskScore_lte` | N/A | 2025-11-26 |
| `MarketHistory.fee` | N/A | 2026-01-07 |
| `MarketHistory.price` | N/A | 2026-01-19 |
| `MarketOracleAccuracy.` `averagePercentDifference` | N/A | 2025-09-09 |
| `MarketOracleAccuracy.` `maxPercentDifference` | N/A | 2025-09-09 |
| `MarketStateReward.` `amountPerBorrowedToken` | N/A | 2025-09-12 |
| `MarketStateReward.` `amountPerSuppliedToken` | N/A | 2025-09-12 |
| `MarketStateReward.yearlyBorrowTokens` | N/A | 2025-09-12 |
| `MarketStateReward.yearlySupplyTokens` | N/A | 2025-09-12 |
| `OracleFeed.description` | N/A | 2025-10-08 |
| `OracleFeed.historicalPrice` | N/A | 2025-10-08 |
| `OracleFeed.pair` | N/A | 2025-10-08 |
| `OracleFeed.price` | N/A | 2025-10-08 |
| `OracleFeed.vendor` | N/A | 2025-10-08 |
| `OracleVault.decimals` | N/A | 2025-10-20 |
| `OracleVault.pair` | N/A | 2025-10-20 |
| `OracleVault.vendor` | N/A | 2025-10-20 |
| `Query.marketOracleAccuracy` | `marketById(marketId:, chainId:)` | 2026-05-14 |
| `Query.transactionByHash` | N/A | 2025-01-02 |
| `Query.users` | `userByAddress(address:, chainId:)` when the address is known; otherwise use address-scoped queries | 2026-05-14 |
| `User.id` | `address` and `chain.id` | 2026-05-14 |
| `User.tag` | N/A | 2026-05-14 |
| `Vault.id` | `address` and `chain.id` | 2026-05-14 |
| `VaultAllocationDto.enabled` | N/A | 2026-01-15 |
| `VaultFilters.credoraRiskScore_gte` | N/A | 2025-11-26 |
| `VaultFilters.credoraRiskScore_lte` | N/A | 2025-11-26 |
| `VaultState.id` | Parent `Vault.address` and `Vault.chain.id` | 2026-05-14 |
| `VaultStateReward.` `amountPerSuppliedToken` | N/A | 2026-03-20 |
| `VaultStateReward.` `yearlySupplyTokens` | N/A | 2026-03-20 |

When fetching an entity, pass `chainId` as an input argument where available. When reading an entity from the response, select `chain { id }`.

## [May 20, 2026 - API fields removal](#may-20-2026---api-fields-removal)

View scheduled field removalsThe below fields will be fully removed from the Morpho API on **May 20, 2026**

.tc-may20 th:nth-child(1), .tc-may20 td:nth-child(1) { width: 47%; } .tc-may20 th:nth-child(2), .tc-may20 td:nth-child(2) { width: 33%; } .tc-may20 th:nth-child(3), .tc-may20 td:nth-child(3) { width: 20%; }
| **Deprecated Field** | **Replacement** | **Deprecation date** |
| --- | --- | --- |
| `AssetsFilters.id_in` | `address_in` | 2026-02-11 |
| `AssetsFilters.whitelisted` | `listed` | 2025-12-22 |
| `CuratorFilters.chainId` | `chainId_in` | 2025-09-09 |
| `Market.allTimeApys` | `state.allTimeApy` | 2025-09-09 |
| `Market.quarterlyApys` | `state.quarterlyApys` | 2025-09-09 |
| `Market.uniqueKey` | `marketId` | 2026-03-30 |
| `Market.weeklyApys` | `state.weeklyApys` | 2025-09-09 |
| `Market.whitelisted` | `listed` | 2026-01-29 |
| `Market.yearlyApys` | `state.yearlyApys` | 2025-09-09 |
| `MarketFilters.collateralAssetId_in` | `collateralAssetSelector_in` | 2026-01-29 |
| `MarketFilters.id_in` | `selector_in` | 2026-01-29 |
| `MarketFilters.loanAssetId_in` | `loanAssetSelector_in` | 2026-01-29 |
| `MarketFilters.whitelisted` | `listed` | 2026-02-27 |
| `MarketHistory.allTimeNetBorrowApy` | `allTimeBorrowApy` | 2026-01-19 |
| `MarketHistory.allTimeNetSupplyApy` | `allTimeSupplyApy` | 2026-01-19 |
| `MarketHistory.rateAtUTarget` | `apyAtTarget` | 2025-12-23 |
| `MarketPosition.borrowAssets` | `state.borrowAssets` | 2025-09-09 |
| `MarketPosition.borrowAssetsUsd` | `state.borrowAssetsUsd` | 2025-09-09 |
| `MarketPosition.borrowShares` | `state.borrowShares` | 2025-09-09 |
| `MarketPosition.collateral` | `state.collateral` | 2025-09-09 |
| `MarketPosition.collateralUsd` | `state.collateralUsd` | 2025-09-09 |
| `MarketPosition.supplyAssets` | `state.supplyAssets` | 2025-09-09 |
| `MarketPosition.supplyAssetsUsd` | `state.supplyAssetsUsd` | 2025-09-09 |
| `MarketPosition.supplyShares` | `state.supplyShares` | 2025-09-09 |
| `MarketPosition.whitelisted` | `listed` | 2026-02-03 |
| `MarketPositionFilters.marketId_in` | `marketUniqueKey_in` | 2026-02-11 |
| `MarketPositionFilters.` `marketWhitelisted` | `marketListed` | 2026-02-27 |
| `MarketPositionFilters.userId_in` | `userAddress_in` | 2026-01-20 |
| `MarketState.rateAtUTarget` | `apyAtTarget` | 2026-01-07 |
| `MarketStateReward.borrowApy` | `borrowApr` | 2024-05-28 |
| `MarketStateReward.supplyApy` | `supplyApr` | 2024-05-28 |
| `MorphoBlueFilters.id_in` | `address_in` | 2026-02-11 |
| `MorphoChainlinkOracleData.vault` | `baseOracleVault` | 2025-09-09 |
| `MorphoChainlinkOracleV2Data.baseVault` | `baseOracleVault` | 2025-09-09 |
| `MorphoChainlinkOracleV2Data.quoteVault` | `quoteOracleVault` | 2025-09-09 |
| `PublicAllocatorFilters.id_in` | `address_in` | 2026-02-11 |
| `PublicAllocatorSharedLiquidity.` `allocationMarket` | `withdrawMarket` | 2025-12-17 |
| `PublicAllocatorSharedLiquidity.market` | `supplyMarket` | 2025-12-17 |
| `PublicallocatorReallocateFilters.` `marketId_in` | `marketSelector_in` | 2026-01-27 |
| `PublicallocatorReallocateFilters.` `vaultId_in` | `vaultSelector_in` | 2026-01-27 |
| `Query.asset` | `assetByAddress` | 2026-02-12 |
| `Query.market` | `marketById` | 2025-09-09 |
| `Query.marketAverageApys` | `state` | 2025-07-28 |
| `Query.marketByUniqueKey` | `marketById` | 2026-04-01 |
| `Query.morphoBlue` | `morphoBlueByAddress` | 2026-02-12 |
| `Query.search` | `markets and vaults` | 2026-03-20 |
| `Query.transaction` | `transactions` | 2026-02-12 |
| `Query.user` | `userByAddress` | 2026-02-12 |
| `Query.vault` | `vaultByAddress` | 2026-02-12 |
| `Query.vaultFactory` | `vaultFactoryByAddress` | 2026-02-12 |
| `RiskAnalysis.isUnderReview` | `analysis.isUnderReview` | 2025-09-09 |
| `RiskAnalysis.rating` | `analysis.rating` | 2025-09-09 |
| `RiskAnalysis.score` | `analysis.score` | 2025-09-09 |
| `RiskAnalysis.timestamp` | `analysis.timestamp` | 2025-09-09 |
| `TransactionFilters.assetId_in` | `assetAddress_in` | 2026-02-11 |
| `TransactionFilters.assetSymbol_in` | `assetAddress_in` | 2026-02-16 |
| `TransactionFilters.marketId_in` | `marketUniqueKey_in` | 2026-02-11 |
| `TransactionFilters.userId_in` | `userAddress_in` | 2026-02-11 |
| `TransactionFilters.vaultId_in` | `vaultAddress_in` | 2026-02-11 |
| `TransactionFilters.assetsUsd_gte` | N/A | 2026-02-16 |
| `TransactionFilters.assetsUsd_lte` | N/A | 2026-02-16 |
| `TransactionFilters.badDebtAssetsUsd_gte` | N/A | 2026-02-16 |
| `TransactionFilters.badDebtAssetsUsd_lte` | N/A | 2026-02-16 |
| `TransactionFilters.repaidAssetsUsd_gte` | N/A | 2026-02-16 |
| `TransactionFilters.repaidAssetsUsd_lte` | N/A | 2026-02-16 |
| `TransactionFilters.seizedAssetsUsd_gte` | N/A | 2026-02-16 |
| `TransactionFilters.seizedAssetsUsd_lte` | N/A | 2026-02-16 |
| `UsersFilters.assetId_in` | `assetAddress_in` | 2026-02-11 |
| `UsersFilters.id_in` | `address_in` | 2026-02-11 |
| `UsersFilters.marketId_in` | `marketUniqueKey_in` | 2026-02-11 |
| `UsersFilters.vaultId_in` | `vaultAddress_in` | 2026-02-11 |
| `Vault.dailyApy` | `state.avgNetApyExcludingRewards(lookback: ONE_DAY)` | 2026-01-15 |
| `Vault.dailyApys` | `state.avgNetApyExcludingRewards(lookback: ONE_DAY) and state.avgNetApy(lookback: ONE_DAY)` | 2026-01-15 |
| `Vault.monthlyApy` | `state.avgNetApyExcludingRewards(lookback: THIRTY_DAYS)` | 2026-01-15 |
| `Vault.monthlyApys` | `state.avgNetApyExcludingRewards(lookback: THIRTY_DAYS) and state.avgNetApy(lookback: THIRTY_DAYS)` | 2026-01-15 |
| `Vault.pendingCaps` | `state.pendingConfigs` | 2026-01-15 |
| `Vault.promoted` | `featured` | 2026-02-11 |
| `Vault.riskAnalysis` | `warnings` | 2025-11-26 |
| `Vault.weeklyApys` | `state.avgNetApyExcludingRewards(lookback: SEVEN_DAYS) and state.avgNetApy(lookback: SEVEN_DAYS)` | 2026-01-15 |
| `Vault.whitelisted` | `listed` | 2026-02-11 |
| `VaultFilters.assetId_in` | `assetAddress_in` | 2026-02-11 |
| `VaultFilters.curator_in` | `curatorAddress_in` | 2026-02-11 |
| `VaultFilters.id_in` | `address_in` | 2026-02-11 |
| `VaultFilters.promoted` | `featured` | 2026-02-11 |
| `VaultFilters.whitelisted` | `listed` | 2026-02-11 |
| `VaultHistoryDto.curator` | `vault.adminEvents` | 2026-04-20 |
| `VaultHistoryDto.feeRecipient` | `vault.adminEvents` | 2026-04-20 |
| `VaultHistoryDto.guardian` | `vault.adminEvents` | 2026-04-20 |
| `VaultHistoryDto.owner` | `vault.adminEvents` | 2026-04-20 |
| `VaultHistoryDto.sharePrice` | `sharePriceNumber` | 2026-01-15 |
| `VaultHistoryDto.skimRecipient` | `vault.adminEvents` | 2026-04-20 |
| `VaultMetadata.curators` | `state.curators` | 2025-09-09 |
| `VaultPosition.assets` | `state.assets` | 2025-09-09 |
| `VaultPosition.assetsUsd` | `state.assetsUsd` | 2025-09-09 |
| `VaultPosition.shares` | `state.shares` | 2025-09-09 |
| `VaultPosition.whitelisted` | `listed` | 2025-12-22 |
| `VaultPositionFilters.userId_in` | `userAddress_in` | 2026-01-20 |
| `VaultPositionFilters.vaultId_in` | `vaultAddress_in` | 2026-01-20 |
| `VaultPositionFilters.` `vaultWhitelisted` | `vaultListed` | 2026-02-11 |
| `VaultReallocateFilters.marketId_in` | `marketUniqueKey_in` | 2026-02-11 |
| `VaultReallocateFilters.vaultId_in` | `vaultAddress_in` | 2026-02-11 |
| `VaultState.allTimeApy` | `avgNetApyExcludingRewards` | 2026-02-15 |
| `VaultState.allTimeNetApy` | `avgNetApy` | 2026-02-15 |
| `VaultState.avgApy` | `avgNetApyExcludingRewards` | 2026-02-15 |
| `VaultState.biweeklyApy` | `avgNetApyExcludingRewards` | 2026-02-15 |
| `VaultState.biweeklyNetApy` | `avgNetApy` | 2026-02-15 |
| `VaultState.monthlyApy` | `avgNetApyExcludingRewards` | 2026-02-15 |
| `VaultState.monthlyNetApy` | `avgNetApy` | 2026-02-15 |
| `VaultState.pendingGuardian` | `pendingConfigs` | 2026-01-15 |
| `VaultState.pendingGuardianValidAt` | `pendingConfigs` | 2026-01-15 |
| `VaultState.pendingTimelock` | `pendingConfigs` | 2026-01-15 |
| `VaultState.pendingTimelockValidAt` | `pendingConfigs` | 2026-01-15 |
| `VaultState.quarterlyApy` | `avgNetApyExcludingRewards` | 2026-02-15 |
| `VaultState.quarterlyNetApy` | `avgNetApy` | 2026-02-15 |
| `VaultState.sharePrice` | `sharePriceNumber` | 2026-01-15 |
| `VaultState.yearlyApy` | `avgNetApyExcludingRewards` | 2026-02-15 |
| `VaultState.yearlyNetApy` | `avgNetApy` | 2026-02-15 |
| `VaultV2.gates` | `gatesConfig` | 2025-11-25 |
| `VaultV2.whitelisted` | `listed` | 2025-12-22 |
| `VaultV2sFilters.assetId_in` | `address_in` | 2026-02-11 |
| `VaultV2sFilters.curator_in` | `curatorAddress_in` | 2025-11-25 |
| `VaultV2sFilters.whitelisted` | `listed` | 2026-02-11 |

## [May 6, 2026 - Legacy rewards API deprecation](#may-6-2026---legacy-rewards-api-deprecation)

View deprecation detailsImplemented on May 6th, 2026

Announced on March 13, 2026

Rewards distribution has migrated from the legacy Morpho Universal Rewards Distributor (URD) system to Merkl. All new campaigns from July 2025 onwards use Merkl exclusively.

.tc-rewards th:nth-child(1), .tc-rewards td:nth-child(1) { width: 32%; } .tc-rewards th:nth-child(2), .tc-rewards td:nth-child(2) { width: 68%; }
| Deprecated endpoint | Alternative |
| --- | --- |
| `rewards.morpho.org/docs` | Deprecated. Historical rewards can still be claimed via   [rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/). |

## [April 23, 2026 - Morpho Vault V1 historical admin fields deprecation](#april-23-2026---morpho-vault-v1-historical-admin-fields-deprecation)

View deprecation detailsImplemented on April 23, 2026

Announced on April 23, 2026

The jobs backing the admin-address time series on Morpho Vaults V1 have been retired. The following fields remain in the schema for backwards compatibility but are no longer maintained and will be removed at a later stage.

**Deprecated fields & alternatives**

.tc-v1a th:nth-child(1), .tc-v1a td:nth-child(1) { width: 45%; } .tc-v1a th:nth-child(2), .tc-v1a td:nth-child(2) { width: 55%; }
| **Field** | **Alternative** |
| --- | --- |
| `vault.historicalState.` `curator` | `vault.adminEvents` `(where: { type_in: ["setCurator"] })` |
| `vault.historicalState.` `feeRecipient` | `vault.adminEvents` `(where: { type_in: ["setFeeRecipient"] })` |
| `vault.historicalState.` `guardian` | `vault.adminEvents` `(where: { type_in: ["setGuardian"] })` |
| `vault.historicalState.` `owner` | `vault.adminEvents` `(where: { type_in: ["ownershipTransferred"] })` |
| `vault.historicalState.` `skimRecipient` | `vault.adminEvents` `(where: { type_in: ["setSkimRecipient"] })` |

Apply the same pattern for the other four fields, using the matching `type_in` value and `... on <Event>Data` fragment:

.tc-v1b th:nth-child(1), .tc-v1b td:nth-child(1) { width: 45%; } .tc-v1b th:nth-child(2), .tc-v1b td:nth-child(2) { width: 55%; }
| **Event or field** | **Fragment or alternative** |
| --- | --- |
| `setFeeRecipient` | `SetFeeRecipientEventData { feeRecipient }` |
| `setGuardian` | `SetGuardianEventData { guardian }` |
| `vault.historicalState.` `guardian` | `vault.adminEvents` `(where: { type_in: ["setGuardian"] })` |
| `ownershipTransferred` | `OwnershipEventData { owner }` |
| `setSkimRecipient` | `SetSkimRecipientEventData { skimRecipient }` |

## [April 2, 2026 - pnl API fields removal](#april-2-2026---pnl-api-fields-removal)

View removal detailsImplemented on April 2, 2026

Announced on February 17, 2026

Removed fields:

| Removed field |
| --- |
| `vaultPosition.state.roeUsd` |
| `vaultPosition.historicalState.` `pnl` `pnlUsd` `roe` `roeUsd` |
| `vaultV2Position.roeUsd` |
| `vaultV2Position.historicalState.` `pnl` `pnlUsd` `roe` `roeUsd` |
| `marketPosition.state.` `pnl` `pnlUsd` `roe` `roeUsd` |
| `marketPosition.state.` `supplyPnl` `supplyPnlUsd` `supplyRoe` `supplyRoeUsd` |
| `marketPosition.state.borrowRoeUsd` |
| `marketPosition.state.` `collateralPnlUsd` `collateralRoeUsd` |
| `marketPosition.state.` `marginPnl` `marginPnlUsd` `marginRoe` `marginRoeUsd` |
| `marketPosition.historicalState.` `supplyPnl` `supplyPnlUsd` `supplyRoe` `supplyRoeUsd` |
| `marketPosition.historicalState.` `borrowPnl` `borrowPnlUsd` `borrowRoe` `borrowRoeUsd` |
| `marketPosition.historicalState.` `collateralPnlUsd` `collateralRoeUsd` |
| `marketPosition.historicalState.` `marginPnl` `marginPnlUsd` `marginRoe` `marginRoeUsd` |
| `user.state.` `vaultsPnlUsd` `vaultsRoeUsd` `vaultV2sPnlUsd` `vaultV2sRoeUsd` `marketsPnlUsd` `marketsRoeUsd` `marketsSupplyPnlUsd` `marketsSupplyRoeUsd` `marketsBorrowPnlUsd` `marketsBorrowRoeUsd` `marketsCollateralPnlUsd` `marketsCollateralRoeUsd` `marketsMarginPnlUsd` `marketsMarginRoeUsd` |
| `user.historicalState.` `vaultsPnlUsd` `vaultsRoeUsd` `vaultV2sPnlUsd` `vaultV2sRoeUsd` `marketsPnlUsd` `marketsRoeUsd` `marketsSupplyPnlUsd` `marketsSupplyRoeUsd` `marketsBorrowPnlUsd` `marketsBorrowRoeUsd` `marketsCollateralPnlUsd` `marketsCollateralRoeUsd` `marketsMarginPnlUsd` `marketsMarginRoeUsd` |

The fields that will be kept are:

.tc-pnl-kept th:nth-child(1), .tc-pnl-kept td:nth-child(1) { width: 38%; } .tc-pnl-kept th:nth-child(2), .tc-pnl-kept td:nth-child(2) { width: 62%; }
| Kept field | Note |
| --- | --- |
| `vaultPosition.` `state.` `pnl` | — |
| `vaultPosition.` `state.` `pnlUsd` | changed definition from "p&l if each interaction was realizing profit/loss in USD" to "currently p&l in underlying assets quoted in USD at the latest price" |
| `vaultPosition.` `state.` `roe` | — |
| `vaultV2Position.` `pnl` `pnlUsd` `roe` | — |
| `marketPosition.` `state.` `borrowPnl` `borrowPnlUsd` `borrowRoe` | — |

## [April 2, 2026 - API fields removal](#april-2-2026---api-fields-removal)

View removal detailsImplemented on April 2, 2026

Announced on January 26, 2026

This is the first removal notice of the Morpho API. One can expect this kind of removal notice every 6 months. This is a cleanup fields removal, removing only fields that are marked as deprecated for more than 1 year, with an alternative or a non longer maintained feature.

**Fields removed & alternatives**

.tc-api th:nth-child(1), .tc-api td:nth-child(1) { width: 50%; } .tc-api th:nth-child(2), .tc-api td:nth-child(2) { width: 50%; }
| **Field** | **Alternative** |
| --- | --- |
| `_crossVersionVaults` | NA |
| `marketAverageApys` | `market(s).state` |
| `transactionByHash` | NA |
| `marketOracleAccuracy` | NA |
| `asset.` `historicalSpotPriceEth` `spotPriceEth` `riskAnalysis` `totalSupply` | NA |
| `curators.items.url` | `curators.items.socials.url` |
| `market(s).` `allTimeApys` `dailyApys` `monthlyApys` `quaterlyApys` `weeklyApys` `yearlyApys` | `market(s).state.` `allTimeBorrowApy` `dailyApys` `monthlyApys` `quaterlyApys` `weeklyApys` `yearlyApys` |
| `market(s).collateralPrice` | `market(s).state.price` |
| `market(s).concentration` | NA |
| `market(s).` `oracleAddress` `oracleFeed` `oracleInfo` | `market(s).oracle.address` `market(s).oracle.data...` (×2) |
| `vault(s).` `dailyApy(s)` `monthlyApy(s)` `weeklyApy(s)` `pendingCaps` | `vault(s).state.` `dailyApy` `monthlyApy` `weeklyApy` `pendingConfigs` |
| `marketPosition(s).` `borrowAssets` `borrowAssetsUsd` `borrowShares` `collateral` `collateralUsd` `supplyAssets` `supplyAssetsUsd` `supplyShares` | `marketPosition(s).state.` `borrowAssets` `borrowAssetsUsd` `borrowShares` `collateral` `collateralUsd` `supplyAssets` `supplyAssetsUsd` `supplyShares` |
| `vaultPosition(s).` `assets` `assetsUsd` `shares` | `vaultPosition(s).state.` `assets` `assetsUsd` `shares` |
| `on MorphoChainlinkOracleV2Data` `.baseVault` `.quoteVault` `on MorphoChainlinkOracleData` `.vault` | `on MorphoChainlinkOracleV2Data` `.baseOracleVault` `.quoteOracleVault` `on MorphoChainlinkOracleData` `.baseOracleVault` |

Changes represented by `market(s)` / `vault(s)` are also applied to `marketByUniqueKey` and `vaultByAddress` queries.

## [October 16, 2025 - Limiting the maximum complexity of a query](#october-16-2025---limiting-the-maximum-complexity-of-a-query)

View change details16/10/2025

**Action**

GraphQL complexity details:

| Item |
| --- |
| **Max allowed complexity: 1,000,000** |
| **Base cost per operation: 10** |
| Each field adds cost; some fields declare explicit costs and/or multipliers. |

For details on how to check your queries' complexity and reduce it if needed, see [Maximum complexity of a GraphQL query](https://docs.morpho.org/developers/api/get-started/#maximum-complexity-of-a-graphql-query).

## [September 20, 2025 - Search limitation](#september-20-2025---search-limitation)

View change details20/09/2025

**Rational**

The `numberOfResults` was previously unbounded so the query can yield a huge amount of results which can have an impact on the performance of the Morpho API.

**Action**

.tc-search th:nth-child(1), .tc-search td:nth-child(1) { width: 22%; } .tc-search th:nth-child(2), .tc-search td:nth-child(2) { width: 63%; } .tc-search th:nth-child(3), .tc-search td:nth-child(3) { width: 15%; }
| Parameter | Constraint | Default |
| --- | --- | --- |
| `numberOfResults` | Must be within `[0, 1000]` in the search root resolver. | `5` |

## [September 19, 2025 - Fields removal](#september-19-2025---fields-removal)

View removal details19/09/2025

**Rational**

Some rewards fields were wrongly computed since the Merkl integration:

.tc-sep19a th:nth-child(1), .tc-sep19a td:nth-child(1) { width: 35%; } .tc-sep19a th:nth-child(2), .tc-sep19a td:nth-child(2) { width: 65%; }
| Affected field | Outcome |
| --- | --- |
| `yearlySupplyTokens` | Will always be set to 0 and be removed from the schema. |
| `yearlyBorrowTokens` | Will always be set to 0 and be removed from the schema. |
| `amountPerSuppliedToken` | Will always be set to 0 and be removed from the schema. |
| `amountPerBorrowedToken` | Will always be set to 0 and be removed from the schema. |

**Action**

These fields will always be set to 0 and be removed in the schema.

**Troubleshoot**

The Morpho API is integrating Merkl, these fields shouldn't be used and instead `supplyApy` and `borrowApy` fields should satisfy integrators needs.

The only removed use-cases along with this 4 fields should be:

| Removed use-case |
| --- |
| displaying rewards for an unpriced asset |
| computing the apy with a custom price (fdv feature on the Morpho app) |

[Rewards

Previous Page

](https://docs.morpho.org/developers/api/rewards/)[Get Started

Next Page

](https://docs.morpho.org/developers/sdks/get-started/)