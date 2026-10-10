# Get Started

> Source: https://docs.morpho.org/developers/api/get-started

---

# Get Started

Enterprise API accessFor enterprise access, send requests to `https://private.api.morpho.org` with your API key in the `x-api-key` header. [Request an API key](https://docs.morpho.org/request-api-key/).

The Morpho API provides powerful, GraphQL and REST-based interfaces for accessing a comprehensive range of onchain and offchain data from the Morpho ecosystem. It is designed for developers building applications, dashboards, bots, or any service that requires reliable data on Morpho Markets, Morpho Vaults, user positions, and more.

The Morpho API is provided as-is, without a Service Level Agreement (SLA). While we strive to maintain reliable service, availability and uptime are not guaranteed.
We recommend implementing appropriate fallback mechanisms in production applications and avoiding hard dependencies on API availability for critical operations.

The Morpho API can evolve. Stay in touch with updates via the **[API Changelog](https://docs.morpho.org/developers/api/changelog/)**.

## [Endpoints](#endpoints)

**GraphQL API**: For all data related to Blue markets, vaults, and positions. You can explore the schema and run live queries in the [GraphQL Playground](https://api.morpho.org/graphql).

**REST API**: For all data related to Blue and Midnight markets, vaults, and positions. You can explore the routes supported in the [API Reference](https://docs.morpho.org/api/) page.

## [Key Data & Features](#key-data--features)

- **Real-time & Historical Data**: Access both current state and historical timeseries data for markets and vaults.
- **Market & Vault Analytics**: Retrieve metrics like APYs, TVL, utilization, fees, and market allocations.
- **User Positions**: Fetch detailed information on supply, borrow, and collateral positions for any user.
- **Rewards**: Query vault and market reward rates and campaign APRs.
- **Public Allocator Liquidity**: Query [Vault V2 Public Allocator liquidity](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/) available through the Public Allocator.

## [Supported Networks](#supported-networks)

The API provides data for fully supported deployments on networks including:

- **Ethereum** (Chain ID: 1)
- **Arbitrum** (Chain ID: 42161)
- **Arc** (Chain ID: 5042)
- **Base** (Chain ID: 8453)
- **HyperEVM** (Chain ID: 999)
- **Katana** (Chain ID: 747474)
- **Monad** (Chain ID: 143)
- **Op Mainnet** (Chain ID: 10)
- **Polygon** (Chain ID: 137)
- **Robinhood Chain** (Chain ID: 4663)
- **Unichain** (Chain ID: 130)
- **Stable** (Chain ID: 988)
- **Tempo** (Chain ID: 4217)
- **World Chain** (Chain ID: 480)

## [Morpho API main rules](#morpho-api-main-rules)

### [Maximum complexity of a GraphQL query](#maximum-complexity-of-a-graphql-query)

A complexity score is associated with each query in the Morpho API.

GraphQL complexity details:

- **Max allowed complexity: 1,000,000**
- Base cost per operation: 10
- Each field adds cost; some fields declare explicit costs and/or multipliers.

One can verify its queries' complexity in [https://api.morpho.org/graphql](https://api.morpho.org/graphql). The complexity number is returned as an extension.

If one of the query is above the threshold, you have the following alternatives:

- **Trim the selection set**: keep only fields you actually use. Prefer cheap snapshots (state.*) over histories when possible.
- **Lower fan-out**: reduce first (e.g., 25 or 50), then paginate.
- **Split the work**: fetch a light list first (IDs + a few cheap fields), then run follow-up queries for heavy history on a subset.
- **Tune multipliers**: for fields like currentIrmCurve(numberOfPoints: N), lower N.

### [Best Practices & Rate Limiting](#best-practices--rate-limiting)

To ensure reliable service for all users and protect against malicious usage, spam, and attacks, the API enforces the following rate limits:

| Limit | Threshold | Response |
| --- | --- | --- |
| **Standard** | 750 requests/minute | `429 Too Many Requests` with `Retry-After: 600` |
| **Severe abuse** | ~20,000 requests/hour (3,334 requests/10 min) | `429 Too Many Requests` with `Retry-After: 604800` |

Repeated violation of rate limits may result in multi-day cooldown periods or permanent denial.

We strongly recommend implementing the following best practices in your integration:

- **Cache Responses**: Cache API query results on your backend to reduce redundant requests and improve your application's performance.
- **Request Only What You Need**: Structure your GraphQL queries to fetch only the data fields required for your use case.
- **Avoid Excessive Polling**: Design your application to fetch data efficiently, respecting API limits to prevent interruptions.

The `numberOfResults` parameter in the search root resolver is constrained to be within [0, 1000] (default value being 5).

### [Deprecation Warnings](#deprecation-warnings)

API responses may include a `warnings` array in the `extensions` object when a queried field is scheduled for deprecation. We strongly recommend monitoring `response.extensions.warnings` in your integration and setting up alerts so you can migrate away from deprecated fields before they are removed.

A warning entry contains all the information you need to update your queries:

```
{
  "extensions": {
    "warnings": [
      {
        "type": "DEPRECATED_FIELD",
        "field": "Vault.whitelisted",
        "path": "vaultByAddress.whitelisted",
        "message": "Use listed instead.",
        "replacement": "listed",
        "deprecatedAt": "2026-02-11",
        "removalAt": "2026-05-06"
      }
    ]
  }
}
```

| Field | Description |
| --- | --- |
| `type` | The warning type. `DEPRECATED_FIELD` indicates a field that will be removed. |
| `field` | The deprecated field in `Type.fieldName` format. |
| `path` | The exact query path where the deprecated field was used. |
| `message` | A human-readable description of the deprecation. |
| `replacement` | The recommended replacement field. |
| `deprecatedAt` | The date the field was deprecated. |
| `removalAt` | The date the field will be removed from the API. |

Field removals are also communicated via the **[API Changelog](https://docs.morpho.org/developers/api/changelog/)**.

## [Where to Find Query Examples](#where-to-find-query-examples)

This page serves as a high-level overview. For detailed documentation and hands-on query examples, please refer to the dedicated sections below.

### [Comprehensive API Documentation](#comprehensive-api-documentation)

For a full list of available queries, schemas, and example use cases for each part of the protocol, explore these sections:

- [**Morpho Midnight API**](https://docs.morpho.org/developers/api/morpho-midnight/)
- [**Morpho Blue API**](https://docs.morpho.org/developers/api/morpho/)
- [**Morpho Vaults API**](https://docs.morpho.org/developers/api/morpho-vaults/)
- [**Vault V2 Public Allocator guide**](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/)
- [**Rewards**](https://docs.morpho.org/developers/api/rewards/)

### [Practical Integration Tutorials](#practical-integration-tutorials)

To see how the API is used in practical integration scenarios, check out our step-by-step tutorials:

- **Integrating Earn Data**: See the [Get Data for Earn](https://docs.morpho.org/developers/earn/tutorials/get-data/) tutorial.
- **Integrating Borrow Data**: Follow the [Get Data for Borrow](https://docs.morpho.org/developers/borrow/tutorials/get-data/) guide.
- **Using Public Allocator Liquidity**: Follow the [Vault V2 Public Allocator guide](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/).

[Resources

Previous Page

](https://docs.morpho.org/developers/rewards/resources/all/)[Morpho Midnight

Next Page

](https://docs.morpho.org/developers/api/morpho-midnight/)