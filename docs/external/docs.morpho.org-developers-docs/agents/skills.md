# Skills

> Source: https://docs.morpho.org/developers/agents/skills

---

# Skills

Install Morpho's builder skills to build, update, and review Earn and Borrow products.

The `morpho-builder` plugin gives coding agents two self-contained skills for Morpho Earn and Borrow products. Each skill covers current data sources, `@morpho-org/morpho-sdk` transaction flows, product UI, safety guidance, and pre-launch review.

## [Install](#install)

Install both skills on an [Agent Skills](https://agentskills.io)-compatible host:

```
npx skills add morpho-org/morpho-skills
```

Or pick individual skills:

```
npx skills add morpho-org/morpho-skills --skill earn-integration
npx skills add morpho-org/morpho-skills --skill borrow-integration
```

Claude Code can install the same skills from the Morpho marketplace:

```
/plugin marketplace add morpho-org/morpho-skills
/plugin install morpho-builder@morpho-skills
```

Both installation paths expose the same skills, product references, review workflow, and checker prompts.

## [Available skills](#available-skills)

| Plugin | Skill | Product |
| --- | --- | --- |
| `morpho-builder` | `earn-integration` | Earn with Morpho Vault V2 |
| `morpho-builder` | `borrow-integration` | Borrow with Blue, Midnight, or both products |

Pick the skill by product. The same skill handles build, update, review, audit, quality assurance, and pre-launch requests. There are no separate review skills.

## [Integration skills](#integration-skills)

### [Build or update](#build-or-update)

- **Earn** defaults to Morpho Vault V2. It covers vault discovery, live data, variable APY and rewards, deposit and withdrawal actions, liquid and illiquid exits, positions, UI copy, and safety checks. Vault V1 appears only as migration or compatibility context.
- **Borrow** first identifies Blue variable-rate borrowing, Midnight fixed-rate fixed-term borrowing, or both. It then loads product-specific data, transaction, rate, risk, liquidity, refinancing, quote, maturity, and UI guidance. A mixed integration keeps Blue and Midnight behavior separate.

Both skills use the Morpho API for indexed discovery and fresh protocol entities for transaction execution. They guide the agent through SDK requirements, transaction building, final simulation, submission, and receipt reconciliation.

### [Review or audit](#review-or-audit)

Review mode runs eight evidence-based checkers: vocabulary, attribution, disclosure, rate transparency, conversion, clarity and safety, discoverability, and math correctness. The skill runs them in parallel when the agent can delegate, or sequentially otherwise.

The skill validates checker results against a product acceptance matrix, performs a red-flag pass, and returns a release recommendation. Mixed Borrow reviews keep separate Blue and Midnight verdicts. A review reports missing evidence as `UNVERIFIED` and does not edit the product unless you also request fixes.

## [Use cases](#use-cases)

**Build or update an Earn product.** Ask the agent to use `earn-integration` for a Vault V2 discovery, deposit, position, or exit flow.

**Build or update a Borrow product.** Ask the agent to use `borrow-integration` and name Blue, Midnight, or both when you know the target product.

**Run a pre-launch review.** Ask the same product skill to review the integration. It returns evidence-backed checker results, the acceptance matrix, red flags, and a release recommendation.

[Morpho MCP

Morpho's hosted MCP server — query vaults, markets, and positions, and prepare unsigned transactions from any MCP-compatible agent.

](https://docs.morpho.org/developers/agents/mcp/)[llms.txt

Next Page

](https://docs.morpho.org/developers/agents/llms/)