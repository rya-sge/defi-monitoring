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

| Criterion | Main answer | Documents |
|---|---|---|
| Dependency discovery | `analyze` discovers a Pendle PT position's layers; both watches discover a vault's or an address's markets, their borrowers and lenders, and the admin surface (oracles, feeds, tokens, issuers); `graph` draws it | `docs/analysis/ARCHITECTURE.md`, `docs/graph-propagation.md` |
| Impact estimation | incident priors and a Monte Carlo through the stack (`analyze`); unrealised bad debt, liquidation curves, the exit queue and the drain threshold (watches) | `docs/how-risk-is-computed.md`, `docs/vault-depositor-scenarios.md`, `docs/exit-queue.md`, `docs/drain-threshold.md` |
| Decision usefulness | STAY / REDUCE / EXIT with carry, exit cost from a real quote, and a de-lever size; block-by-block alerts with a runbook | `docs/scenarios-and-breakeven.md`, `docs/alert-runbook.md` |
| Working demo on real data | live runs on public sources (`docs/analysis/PROVIDERS.md`); offline demo and replays recorded from mainnet (`fixtures/`) | `README.md` |
