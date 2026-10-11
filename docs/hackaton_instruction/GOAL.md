# Goal: the DeFi Risk Dependency Challenge

This file states what the project has to build, from the challenge brief (the original, a one-page PDF by Belem Capital for the EPFL Hackathon 2026, is `docs/hackaton_instruction/Hackathon_DeFi-Risk-Dependency-Challenge_EN_v1.pdf`; it is git-ignored, so only local checkouts have it). Every design choice in this repository answers to it; where the implementation stands against it is in `docs/analysis/ANALYSIS_MONITORING.md` (gaps), `docs/analysis/NEXT_STEP.md` (what comes next) and `docs/analysis/comparison_team.md` (choices against the teammates' proposals).

## The challenge

Build a working risk system that can automatically uncover the hidden dependencies behind an on-chain position and quantify what happens when one of those dependencies fails.

A single DeFi position may rely on multiple layers: the settlement chain, underlying assets or yield sources, oracles, liquidity venues, lending markets and other protocols. The goal is to turn this complex dependency graph into a clear, defensible risk signal that a portfolio manager can actually use.

The prototype should:

1. **identify the dependencies** of a position;
2. **estimate the potential economic impact** of a security incident, a market disruption or a technical failure;
3. **help answer the real decision**: is the expected loss from staying in the position high enough to justify exiting, despite slippage and execution costs?

Any methodology is allowed (graph analysis, simulations, statistical models, agent-based approaches, others), on any ecosystem (EVM, Solana, Canton, Tempo, others). The emphasis is on sound reasoning, accurate dependency discovery, defensible impact estimation, and a working implementation using real data.

The strongest submissions go beyond flagging that an incident occurred. They explain **how the incident propagates through the position's dependency stack** and what the resulting portfolio impact could be. As the brief's Pendle PT example shows, one portfolio position can depend on five distinct layers: the settlement chain, the underlying yield source, the oracle, the AMM market and the lending venue.

## What is expected

A **working prototype**, not an architecture or a slide deck. It operates on **real data** and produces an output a risk or portfolio manager could realistically act on.

## How it is judged

| Criterion | Weight | The question it asks |
|---|---|---|
| Dependency discovery | 30 % | Does the tool find the layers a position really depends on, automatically and accurately? |
| Impact estimation | 30 % | Is the economic impact of a failure, and its propagation through the stack, estimated in a defensible way? |
| Decision usefulness | 25 % | Does the output say stay or exit, and why? |
| Working demo on real data | 15 % | Does it run on live or recorded real data, end to end? |

## Where this repository answers each criterion

The five-minute path is `README.md` §"The answer in five minutes"; every command below runs offline on mainnet recordings, with no key. The strongest evidence per criterion (state 2026-10-11):

| Criterion | Main answer, with the evidence | Try it | Documents |
|---|---|---|---|
| Dependency discovery | A position's stack read on-chain and from keyless APIs, past the issuer: vault → adapters → markets → borrowers and lenders; oracles and each feed's class, kind (exchange rate, published, linear discount, fixed) and freshness, a meta-oracle's two sources and its switch; who can change each contract and through which timelock; the sibling markets that sell the same collateral; Pharos grades and off-chain backing; **the venues behind USDe** (Ethena's backing by exchange: Binance 13.4 %, OKX 4.2 %…, the custodians, the 62.1M reserve fund); **feeds shared by several markets** (EUR/USD prices 5 markets, 3 of them Belem's); **concentration** (88.8 % of mGLOeuro's supply in one Morpho market; the brief's PT position is half its market, whose PT is 8.2× its Pendle pool's); protocol TVL shares | `graph --vault <V> --replay`; `analyze --demo` (discovery depth) | `docs/analysis/ARCHITECTURE.md`, `docs/model/graph-propagation.md`, plans `depth`, `venues`, `shared-and-supply`, `oracle-kinds` |
| Impact estimation | A known incident propagated through the stack with no probability: the shock engine over the recorded graph (liquidations at the shocked oracle, bad debt, the squeeze, drains where the oracle keeps reading), for a position, a vault, a book; the timing from the oracle's kind. **Backtested**: the PT-reUSD liquidations of 2026-08-25 are predicted from the 5.4M PT sale alone (the Pendle pool rebuilt from its on-chain state, its math matching Pendle's quotes to 1e-9): an oracle fall of 2.36 % (observed 2.45 % and 2.76 %) and the same 13 and 7 borrowers, none missed; debt and incentive within 1 %; a second episode (the 2025-10-10 crash) misses no liquidated borrower in six markets | `backtest`; `analyze --vault <V> --shock token=fxSAVE:0.30`; `analyze --demo --shock venue=Binance:0.5` | `docs/model/vault-incident.md`, `docs/model/shock-engine.md`, plans `backtest`, `pendle-pool`, `one-number` |
| Decision usefulness | STAY / REDUCE / EXIT given the incident, against the cost of leaving: the exit priced after the incident's own liquidations sell first (on the brief's position, after a 10 % oracle fall only a tenth can still leave through Pendle); exit liquidity quoted live on KyberSwap; the breakeven probability p\* and Nexus cover prices next to it; the brief's ten pockets with an 11 % unwind, and its mixed book with the PT loop, as one rule, with the distribution of the loss given the incident; hold-to-maturity against leaving now; block-by-block alerts with a runbook and Telegram | `analyze --book examples/brief-ten-pockets.json --shock token=mGLOeuro:0.30 --exit-cost 0.11 --conditional` | `docs/model/scenarios-and-breakeven.md`, `docs/reference/alert-runbook.md`, plans `stressed-exit`, `breakeven`, `conditional`, `mixed-book` |
| Working demo on real data | Every mode runs live on public sources and replays offline from mainnet recordings (`fixtures/`), zero network calls; an HTTP API (`riskdep/api/`, contract in `openapi.json`) and a browser UI (`web/`); a crisis replayed on a mainnet fork (`scripts/fork/`) | `uv run pytest -q tests` (all offline); `scripts/fork/demo.sh --short` | `README.md`, `docs/analysis/PROVIDERS.md` |

The brief's three scope examples: **oracle and feed quality** (classes and kinds, freshness, shared feeds, `FeedStale`), **a vault routing capital into a perp venue** (the venues behind USDe; Vault V2 adapters into non-Morpho venues are open), **protocols concentrating TVL** (DefiLlama shares, supply posted in Morpho). What is open is in `docs/analysis/GAP.md` and `docs/analysis/NEXT_STEP.md`.
