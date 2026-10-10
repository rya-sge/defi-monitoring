# Get Started

> Source: https://docs.morpho.org/developers/agents/get-started

---

# Get Started

Connect Claude Code, Codex, or Cursor to Morpho — query vaults, markets, and positions, and prepare unsigned transactions from your agent.

Morpho Agents gives an AI agent structured access to the Morpho protocol. Ask it for a vault's realized average APY, a market's borrow rate, or a wallet's health factor, and it answers from live onchain and API data. Ask it to deposit, borrow, or repay, and it hands back an unsigned transaction for you to review and sign.

Morpho Agents is **experimental** and pre-v1.0. Tool schemas, command syntax, and behavior may change without notice. Do not build production systems against it yet.

## [Quickstart](#quickstart)

The shortest path is the hosted MCP server. It needs no account, no API key, and nothing to install — point your agent at `https://mcp.morpho.org/` and it can read Morpho.

Claude CodeCodexCursor
```
claude mcp add morpho --scope user --transport http https://mcp.morpho.org/
```

```
codex mcp add morpho --url https://mcp.morpho.org/
```

Add the server to `.cursor/mcp.json`:

```
{ "mcpServers": { "morpho": { "type": "http", "url": "https://mcp.morpho.org/" } } }
```

Then ask your agent a question:

```
For vault 0x… on Base, what are its realized average APY, TVL, curator, and fee rates?
```

For per-client setup, the full tool reference, and more prompts, see [Morpho MCP](https://docs.morpho.org/developers/agents/mcp/).

## [Two ways to connect](#two-ways-to-connect)

Morpho MCP and Morpho Skills serve different tasks. Use the hosted server to query the protocol or prepare unsigned transactions in a conversation. Install the skills when an agent is building, updating, or reviewing product code.

|  | [Morpho MCP](https://docs.morpho.org/developers/agents/mcp/) | [Morpho Skills](https://docs.morpho.org/developers/agents/skills/) |
| --- | --- | --- |
| How the agent uses it | Tool calls to a hosted server | Local product guidance, references, and review checkers |
| Setup | Connect to `https://mcp.morpho.org/` | `npx skills add morpho-org/morpho-skills` |
| Best for | Live queries and unsigned transactions | Building and reviewing Earn and Borrow products |

The `earn-integration` and `borrow-integration` skills each include build/update and review modes. They cover current data sources, SDK transaction flows, product UI, safety checks, and evidence-based pre-launch reviews.

## [What your agent can do](#what-your-agent-can-do)

**Read** — list and inspect vaults and markets, fetch a user's positions and token balances, and check which chains are supported.

**Prepare** — build unsigned transactions for vault deposits and withdrawals, market supply, borrow, and repay, collateral supply and withdrawal, and rewards claims.

Prepare operations return **unsigned** transaction payloads. Nothing signs and nothing broadcasts — you always review and submit the transaction yourself. Treat every payload as untrusted until you have read it.

Morpho Agents works across every chain Morpho is deployed on. Rather than hardcoding a list that will drift, ask your agent to call `morpho_get_supported_chains` — it returns each chain's slug, chain ID, and explorer URL.

## [Next steps](#next-steps)

- **[Morpho MCP](https://docs.morpho.org/developers/agents/mcp/)** — endpoint details, per-client setup, the full tool table, and prompt examples.
- **[Morpho Skills](https://docs.morpho.org/developers/agents/skills/)** — install the Earn and Borrow builder skills, and see when to use each mode.
- **[Using LLMs](https://docs.morpho.org/developers/agents/llms/)** — feed these docs to an agent as plain Markdown.

[Morpho Optimizers (Deprecated)

Previous Page

](https://docs.morpho.org/developers/contracts/morpho-v0/)[Morpho MCP

Morpho's hosted MCP server — query vaults, markets, and positions, and prepare unsigned transactions from any MCP-compatible agent.

](https://docs.morpho.org/developers/agents/mcp/)