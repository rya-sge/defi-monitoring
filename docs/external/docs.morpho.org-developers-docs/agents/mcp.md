# Morpho MCP

> Source: https://docs.morpho.org/developers/agents/mcp

---

# Morpho MCP

Morpho's hosted MCP server — query vaults, markets, and positions, and prepare unsigned transactions from any MCP-compatible agent.

Morpho MCP is Morpho's hosted, remote [MCP](https://modelcontextprotocol.io) server. It gives any MCP-compatible agent live access to Morpho vaults, markets, and positions, and lets it prepare unsigned transactions for you to review and sign.

Morpho MCP is **experimental** and pre-v1.0. Tool names, schemas, and behavior may change without notice. Do not build production systems against it yet.

## [Setup and Usage](#setup-and-usage)

The server is hosted, public, and read-only by design. There is nothing to install and no key to manage.

|  |  |
| --- | --- |
| **Endpoint** | `https://mcp.morpho.org/` |
| **Transport** | Streamable HTTP |
| **Authentication** | None — no API key, no account |
| **Server name** | `morpho-mcp` |

Two conventions apply to protocol calls:

- **Query tools accept chain IDs.** Pass exactly one of `chainId` or `chain` to `morpho_query_vaults` and `morpho_query_markets`. Prefer the numeric `chainId` from `morpho_get_supported_chains`. The legacy `chain` slug remains supported.
- **RPC tools require registered slugs.** The get, position, and prepare tools still require `chain`. They accept only entries where `morpho_get_supported_chains` returns `supportsRpcTools: true`. REST-only chain IDs work only with the two query tools.
- **Discover before you write.** Find a target with `morpho_query_vaults` or `morpho_query_markets`, inspect it with `morpho_get_vault` or `morpho_get_market`, then call a `morpho_prepare_*` tool. Never hardcode addresses.

`morpho_get_supported_chains` also returns `supportedProtocols` when Core REST provides it. Registered chains include a slug, explorer URL, and testnet status. REST-only entries can omit those fields.

A `morpho_prepare_*` tool returns a `PreparedOperation`: the `transactions` to sign, any `requirements` such as ERC-20 approvals (already included in `transactions`), an `outcome` preview of the resulting position, and a `warnings` array. Warnings carry a severity — an `error` means stop, and the transactions must not be presented for signing.

Prepare tools return **unsigned** transaction payloads. The server never signs and never broadcasts. You always review and submit the transaction yourself — treat every payload as untrusted until you have read it.

## [Setup Examples](#setup-examples)

### [Claude Code](#claude-code)

Add the server with the `claude mcp add` command. The `--scope user` flag registers it once for every project on your machine; drop it to scope the server to the current project.

```
claude mcp add morpho --scope user --transport http https://mcp.morpho.org/
```

Confirm it connected:

```
claude mcp list
```

Inside a session, `/mcp` lists the connected servers and the tools each exposes.

### [Codex](#codex)

Add the server with `codex mcp add`, passing `--url` to select the Streamable HTTP transport:

```
codex mcp add morpho --url https://mcp.morpho.org/
```

Confirm it connected:

```
codex mcp list
```

You can also declare the server in `~/.codex/config.toml` to make it global, or in a trusted project's `.codex/config.toml` to scope it to that project:

```
[mcp_servers.morpho]
url = "https://mcp.morpho.org/"
```

A `morpho_prepare_*` call simulates the transaction before returning, so it can take longer than a plain read. If Codex times out with a transport error, raise the per-server tool timeout:

```
[mcp_servers.morpho]
url = "https://mcp.morpho.org/"
tool_timeout_sec = 120
```

### [Other clients](#other-clients)

Any MCP client that speaks the Streamable HTTP transport can connect by pointing at the endpoint. In Cursor, add it to `.cursor/mcp.json`:

```
{ "mcpServers": { "morpho": { "type": "http", "url": "https://mcp.morpho.org/" } } }
```

## [Tools](#tools)

The server exposes eighteen tools. Read tools answer questions about protocol state or the documentation; prepare tools return unsigned transactions.

| Category | Tool | Description |
| --- | --- | --- |
| **Utility** | `morpho_health_check` | Check the server and its connected services. |
| **Utility** | `morpho_get_supported_chains` | List known chains, Core protocols, and RPC-tool support. |
| **Vaults** | `morpho_query_vaults` | List and sort one vault version, with asset filtering and cursor pagination. |
| **Vaults** | `morpho_get_vault` | Get one vault's details. |
| **Markets** | `morpho_query_markets` | List markets with REST-supported asset and listed filters and cursor pagination. |
| **Markets** | `morpho_get_market` | Get one market's details. |
| **Positions** | `morpho_get_market_positions` | Get positions for a user across 1–100 explicit market IDs. |
| **Positions** | `morpho_get_vault_positions` | List a user's V1 or V2 vault positions with cursor pagination. |
| **Positions** | `morpho_get_token_balance` | A token balance, plus whether Morpho or the Bundler still needs an approval. |
| **Docs** | `morpho_doc_search` | Search the Morpho documentation by semantic similarity. |
| **Transactions** | `morpho_prepare_deposit` | Deposit into a vault, including any approval. |
| **Transactions** | `morpho_prepare_withdraw` | Withdraw from a vault. Accepts `"max"`. |
| **Transactions** | `morpho_prepare_supply` | Supply to a market, including any approval. |
| **Transactions** | `morpho_prepare_borrow` | Borrow from a market, with a health-factor check. |
| **Transactions** | `morpho_prepare_repay` | Repay a market borrow. Accepts `"max"`. |
| **Transactions** | `morpho_prepare_supply_collateral` | Supply collateral without borrowing, including any approval. |
| **Transactions** | `morpho_prepare_withdraw_collateral` | Withdraw collateral. Accepts `"max"`. |
| **Transactions** | `morpho_prepare_claim_rewards` | Claim Merkl rewards against the canonical Distributor. |

For product implementation and review guidance, install the separate [Morpho Skills](https://docs.morpho.org/developers/agents/skills/).

Vault `apyPct` is a realized average APY. Market `supplyApyPct` and `borrowApyPct` are 24-hour averages. All three are percentage strings from the Core REST API and exclude rewards. V2 vault fees are separate: `performanceFeePct` is charged against distributed interest, while `managementFeeAprPct` annualizes the per-second fee charged against total assets.

Both query responses always include `chainId` as a string. They also include `chain` when the ID has a registered MCP slug. Vault queries can sort by `address`, `name`, `creationTimestamp`, `creationBlockNumber`, or `performanceFee`. V2 queries can also sort by `managementFee`. Pass `sortBy` and `sortDirection` (`asc` or `desc`) together, or omit both.

## [Prompt Examples](#prompt-examples)

Once the server is connected, ask in plain language. Your agent picks the tools.

1. For vault `0x…` on Base, show its realized average APY, TVL, curator, and fee rates. Note that the APY excludes rewards.
2. Compare the borrow rates on the wstETH/WETH markets on Ethereum and Arbitrum.
3. For `0x…` on Base, show positions in market IDs `0x…` and `0x…`, and flag any health factor below 1.2.
4. List the V2 vault positions for `0x…` on Base, following every cursor page.
5. Prepare a 1,000 USDC deposit into vault `0x…` on Base for `0x…`, and show me the approval and deposit transactions before I sign anything.
6. If I borrow 1 WETH against my wstETH collateral on Ethereum, what is my health factor afterwards?
7. Do I have claimable Merkl rewards on Base? If so, prepare the claim.
8. Which chains does Morpho support, and what are their chain IDs?

[Get Started

Connect Claude Code, Codex, or Cursor to Morpho — query vaults, markets, and positions, and prepare unsigned transactions from your agent.

](https://docs.morpho.org/developers/agents/get-started/)[Skills

Install Morpho's builder skills to build, update, and review Earn and Borrow products.

](https://docs.morpho.org/developers/agents/skills/)