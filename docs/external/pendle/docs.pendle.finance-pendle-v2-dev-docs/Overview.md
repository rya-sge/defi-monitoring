# Overview

> Source: https://docs.pendle.finance/pendle-v2-dev/Overview

---

- [](https://docs.pendle.finance/)
- Overview

On this page
# Overview

## Stay Connected[​](#stay-connected)

**Important:** Stay up to date with the latest developer updates and get support from our team:

- **Telegram**: Join [t.me/pendledevelopers](https://t.me/pendledevelopers) for all development updates, API changes, and important announcements
- **Telegram bot**: We have a Telegram bot for developers to ask about the API at [t.me/peepo_the_engineer_bot](https://t.me/peepo_the_engineer_bot)
- **Discord**: Get technical support on our [Discord Developer Channel](https://pendle.finance/discord) with responses within 24 hours

## For AI users[​](#for-ai-users)

- As many of us increasingly rely on AI tools to read and understand project documentation, we’ve added a new folder to the repository: [docs/Developers](https://github.com/pendle-finance/documentation/tree/master/docs/Developers). It contains a list of questions and answers about our system and our API, useful for AI to better understand our system and provide more accurate answers when you query them. Our in-house AI is also using these knowledge bases!
- Follow the instructions in [README.md](https://github.com/pendle-finance/documentation/tree/master?tab=readme-ov-file#ai-knowledge-bases) to index the knowledge bases for your AI.

## What do you want to do?[​](#what-do-you-want-to-do)

| Goal | Start here |
| --- | --- |
| **Build a trading bot or data aggregator** | [Quickstart](https://docs.pendle.finance/pendle-v2-dev/Quickstart) → [Backend API Overview](https://docs.pendle.finance/pendle-v2-dev/Backend/ApiOverview) |
| **Integrate PT/YT into your protocol (on-chain)** | [Router Overview](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/PendleRouterOverview) → [Integration Guide](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ContractIntegrationGuide) |
| **Price PT or LP (oracle / collateral)** | [Oracle Overview](https://docs.pendle.finance/pendle-v2-dev/Oracles/OracleOverview) → [How to Integrate](https://docs.pendle.finance/pendle-v2-dev/Oracles/HowToIntegratePtAndLpOracle) |
| **Analyze yields & APY composition** | [Market Historical Data API](https://docs.pendle.finance/pendle-v2-dev/Backend/ApiOverview#market-data-endpoints) |
| **Work with Limit Orders** | [Limit Order Overview](https://docs.pendle.finance/pendle-v2-dev/LimitOrder/Overview) |
| **Track sPENDLE rewards** | [sPENDLE API](https://docs.pendle.finance/pendle-v2-dev/Backend/ApiOverview#spendle-api-endpoints) |

## Core Documentation[​](#core-documentation)

- [High Level Architecture](https://docs.pendle.finance/pendle-v2-dev/HighLevelArchitecture)
- [StandardizedYield (SY)](https://docs.pendle.finance/pendle-v2-dev/Contracts/StandardizedYield)
- [Common Questions](https://docs.pendle.finance/pendle-v2-dev/FAQ)

## Integration Guides[​](#integration-guides)

### On-chain Integration[​](#on-chain-integration)

- **Router**: [Documentation](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/PendleRouterOverview) | [Integration Guide](https://docs.pendle.finance/pendle-v2-dev/Contracts/PendleRouter/ContractIntegrationGuide)
- **Oracles**: [Overview](https://docs.pendle.finance/pendle-v2-dev/Oracles/OracleOverview) | [Integration Guide](https://docs.pendle.finance/pendle-v2-dev/Oracles/HowToIntegratePtAndLpOracle) | [PT as Collateral](https://docs.pendle.finance/pendle-v2-dev/Oracles/PTAsCollateral) | [LP as Collateral](https://docs.pendle.finance/pendle-v2-dev/Oracles/LPAsCollateral)
- [Cross-Chain Oracle Service](https://docs.pendle.finance/pendle-v2-dev/Integration/CrossChainOracle) - Relay a bridged asset's exchange rate from its hub chain to list it on another chain
- [Example Repository](https://github.com/pendle-finance/pendle-examples-public) - Various contract interaction examples

### Off-chain Integration[​](#off-chain-integration)

- [Backend API overview](https://docs.pendle.finance/pendle-v2-dev/Backend/ApiOverview)
- [Market Historical Data & APY Breakdown](https://docs.pendle.finance/pendle-v2-dev/Backend/ApiOverview#market-data-endpoints) - Time-series data with detailed APY and fee breakdowns
- [RouterStatic](https://docs.pendle.finance/pendle-v2-dev/Backend/RouterStatic) - Extensively tested contract for off-chain calculations. Not audited; should not be used for on-chain fund-related operations.
- [sPENDLE API](https://docs.pendle.finance/pendle-v2-dev/Backend/ApiOverview#spendle-api-endpoints) - Staking stats and per-user reward data
- [Socket.IO Real-time Feeds](https://docs.pendle.finance/pendle-v2-dev/Backend/SocketIO) - Pushed real-time feeds

### Limit Orders[​](#limit-orders)

- [Contract](https://docs.pendle.finance/pendle-v2-dev/LimitOrder/LimitOrderContract) | [Create](https://docs.pendle.finance/pendle-v2-dev/LimitOrder/CreateALimitOrder) | [Cancel](https://docs.pendle.finance/pendle-v2-dev/LimitOrder/CancelOrders) | [Fill](https://docs.pendle.finance/pendle-v2-dev/LimitOrder/FillALimitOrder)

## Resources[​](#resources)

- [Deployed Contract Addresses](https://docs.pendle.finance/pendle-v2-dev/Deployments) — Core contracts and market addresses by chain
- [Core Contract Repository](https://github.com/pendle-finance/pendle-core-v2-public)
- [SY Contract Repository](https://github.com/pendle-finance/Pendle-SY-Public)
- [Example Repository](https://github.com/pendle-finance/pendle-examples-public)
- [Whitepapers](https://github.com/pendle-finance/pendle-v2-resources/tree/main/whitepapers)