# The Pendle pool at a past block, plan

> **Status**: approved: the person, 2026-10-11, "Implement next step" (`NEXT_STEP.md` B6). No interview: the decisions below are the agent's defaults.
> **Delivers**: a Pendle V2 pool rebuilt from its on-chain state at any block (`pendle_amm.py`: Pendle's own market math), checked against Pendle's quotes; in the PT-reUSD backtest, the pool behind the oracle's fall: its implied APY before and at the first liquidation, the PT sold into it, the sale the pool's math needs from the state before, and the squeeze (what the pool still accepted against what the liquidations seized); the debt repaid as liquidity returned to the markets.
> **Hard rule**: offline from recordings (the pool's state read once through the archive route, cached under the public URL, no key); `web/` untouched; the agent never commits.
> **Read against**: `docs/hackaton_instruction/GOAL.md` (impact 30 %: "is the number defensible"); `docs/analysis/GAP.md` K8, K9, K27; plans `2026-10-11-backtest`, `2026-10-11-pool-move`; `pendle-core-v2-public` `MarketMathCore.sol`.
> **Left out**: §4 Flows and §5 State.

## The tracker

```mermaid
flowchart TB
  %% tracker
  ST["📍 state · 2026-10-11<br/>repo: defi-monitoring, not committed<br/>deployed: nothing<br/>next: the engine's squeeze on the rebuilt pool; returned liquidity in vault incidents<br/>blocked: nothing<br/>parked: limit orders (the router fills them before the pool)"]

  subgraph SL1["Slice 1 · the pool"]
    S1.1["✅ S1.1 pendle_amm: read, sell_pt, max_sale, sale_for_apy;<br/>checked against Pendle's quotes<br/>went on: PT with 6 decimals, SY with 18"]
  end

  subgraph SL2["Slice 2 · the backtest"]
    S2.1["✅ S2.1 the pool before and at the first liquidation, the squeeze,<br/>returned liquidity; 3 tests; docs"]
  end

  ST ~~~ S1.1
  S1.1 --> S2.1

  classDef done stroke:#4a9d5f,stroke-width:2px,fill:#7f7f7f1a
  classDef state stroke:#8a8a8a,stroke-width:1px,fill:#7f7f7f12
  class S1.1,S2.1 done
  class ST state
```

mandate: mode classic · no git, the person commits · inline · tests at the slice end · verify off

# Design

## 1. Why, and why not

The backtest applied the oracle's observed fall: it tested impact given the incident, but could not say where the fall came from, and the quote API answers for now only. Pendle's pool math is public and its state is on-chain, so the pool can be rebuilt at any block. **Non-goals**: limit orders (off-chain books the router fills before the pool; they do not move the pool's implied rate); the TWAP's path block by block (the oracle's observed prices already are the shock).

## 8. Decisions

| id | Kind | Decision | Status | Source | Slice |
|---|---|---|---|---|---|
| D207 | contract | `pendle_amm.sell_pt`: Pendle V2's `MarketMathCore` in floating point: rate scalar, anchor from the last implied rate, the exchange rate at the post-trade proportion (refused above 96 %), the fee rate, the reserve's share, and the new implied rate. Amounts in PT units (the PT's decimals; SY's 18 converted by its rate). Checked against Pendle's pool-only quotes on the demo pool at one block: 1e-9 at 1,000 PT, 1e-5 at 10,000 (beyond, the router also fills limit orders) | agreed, agent's default | `MarketMathCore.sol` | S1 |
| D208 | contract | An episode may name the Pendle pool its oracle's TWAP reads (`backtest.episodes.<name>.pendle_market`): the pool is read before the episode and at the first liquidation; the report gives the APY move, the PT sold into the pool and what it paid out, the sale the pool's math needs from the state before to reach that APY, and the squeeze: the PT the pool still accepted at the first liquidation against the PT the liquidations seized. The debt the liquidators repaid is shown as liquidity returned to the markets | agreed, agent's default | D161–D164 | S2 |
| D209 | contract | `pendle_amm.read`: `readState(RouterV4)`, `readTokens()`, the SY's `exchangeRate()`, the YT's `pyIndexStored()` (the index is the larger), the PT's `decimals()` and the block's timestamp, in two batches and one block read; an old block through the archive route, recorded | agreed, agent's default | D161 | S1 |

# Execution

## 9. The slices

| Slice | Done when | Went on |
|---|---|---|
| S1 | the pool math matches Pendle's quotes on a recorded block | PT-reUSD's PT has 6 decimals and its SY 18: amounts scaled by the PT's decimals |
| S2 | the backtest replays the pool offline; 343 tests pass | from the state 60 blocks before, the pool's math needs 5.52M PT to lift the implied APY from 10.58 % to 20.37 %; the pool took 5.43M (+1.7 %) and paid 5.21M (model −0.2 %). At the first liquidation it accepted only 309k more PT; the liquidations seized 38.6M |

## Interview log

No interview: the person asked for the next step.
