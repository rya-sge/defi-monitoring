# The drain threshold: when a depeg empties a market

This document explains the drain threshold built into both watches (`watch --vault` and each vault deposit of `watch --user`). It answers a question the exit queue (`docs/exit-queue.md`) leaves open: **until when can a depositor still get out?** On a market whose oracle does not follow the collateral's market price, a depeg past a computable threshold lets anyone borrow all of the market's free liquidity in one block, and that liquidity never comes back. The model comes from Team 2's feedback (`teammate/team2.md`, "Fixed oracles"), and closes item 2 of `docs/analysis/comparison_team.md` §5. A [learn section](#learn-what-you-need-to-understand) at the end explains the concepts used.

Every number below comes from **Sentora RLUSD Main**, from the recorded replay at block 26,162,932 (2026-10-10).

## Contents

- [1. Why a drain threshold](#1-why-a-drain-threshold)
- [2. What was built](#2-what-was-built)
- [3. The threshold d\*](#3-the-threshold-d)
- [4. How much can be drained](#4-how-much-can-be-drained)
- [5. The `DrainWindow` alert](#5-the-drainwindow-alert)
- [6. Effect on the exit queue](#6-effect-on-the-exit-queue)
- [7. Reading the output: Sentora RLUSD Main](#7-reading-the-output-sentora-rlusd-main)
- [8. Limits](#8-limits)
- [9. Code and tests](#9-code-and-tests)
- [Learn: what you need to understand](#learn-what-you-need-to-understand)

## 1. Why a drain threshold

Morpho Blue prices collateral with the market's oracle, not with the market. If the two agree, a depeg makes borrowers liquidatable and liquidators repay their debt: the market loses little and liquidity comes back. Many oracles do not follow the market on purpose:

| Oracle kind | What it reads | On a depeg of the collateral |
|---|---|---|
| Market-tracking | a market price feed of the collateral | the oracle falls, borrowers are liquidated |
| Exchange-rate | a vault's conversion rate (wstETH → stETH, sUSDe → USDe), the underlying assumed at par | the oracle does not move |
| Linear discount or fixed | a formula (a PT accreting to par) or a constant | the oracle does not move |

When the oracle does not move, Team 2 points out that the loss is not avoided. It turns into something worse:

1. **Borrowers stop repaying**: once their collateral is worth less than their debt at the market price, defaulting is their best move.
2. **The market can be drained.** An arbitrageur buys the cheap collateral, posts it, borrows against the oracle's value and walks away. That borrows every unit the market can lend, in one block.
3. **The loss is not recorded**: no liquidation happens, so the share price of a vault supplying the market stays at par, and the loss falls on whoever is still in the vault (the exit queue).

The useful output is the threshold at which step 2 starts paying, because it is the moment the exit window closes.

## 2. What was built

| Piece | Where |
|---|---|
| d\*, the discount, the drainable amount and the bad debt per market | `riskdep/drain.py`, pure functions |
| The Vault V2 Public Allocator's settings, read on-chain | `drain.read_pa` |
| A start-up table in both watches, per vault | `drain.table`, printed after the liquidation curves, before the exit queue |
| An alert, `DrainWindow`, re-evaluated every batch | `drain.assess` |
| The drainable liquidity taken out of the exit queue | `exit_queue.liquidity(st, drained)` |
| Three thresholds | `registry.json` → `watch.drain_buy_cost`, `watch.drain_margin`, `watch.drain_check_every_blocks` |
| Tests | `tests/test_drain.py` (8 tests) |
| Design and decisions D69–D74 | `plan/2026-10-10-drain-threshold.plan.md` |

No new provider: the oracle prices come with each state read, the market prices from DefiLlama (already used by the oracle-divergence check), the Public Allocator's settings from the RPC.

## 3. The threshold d\*

Let δ be how far the collateral trades below its oracle price, and c the cost of buying it at the size of the drain (price impact and fees). For each unit borrowed, the arbitrageur posts collateral worth 1 / LLTV at the oracle price, which costs it (1 − δ)(1 + c) / LLTV at the market. The drain pays when that is less than the unit borrowed:

$$
\frac{(1-\delta)(1+c)}{\text{LLTV}} < 1 \iff \delta > d^\star = 1 - \frac{\text{LLTV}}{1+c}
$$

With c = 0, d\* = 1 − LLTV, Team 2's approximation: 8.5 % at a 91.5 % LLTV, 14 % at 86 %. The tool uses c = `drain_buy_cost`, 0.5 % by default, low on purpose: a lower cost gives an earlier threshold, which is the conservative side for a depositor.

| LLTV | d\* with c = 0 | d\* with c = 0.5 % |
|---|---|---|
| 91.5 % | 8.50 % | 8.96 % |
| 86 % | 14.00 % | 14.43 % |
| 77 % | 23.00 % | 23.38 % |

**How δ is measured.** The tool does not classify the oracle; it measures δ directly: δ = 1 − market ÷ oracle, with the oracle's `price()` from each state read and the market price from DefiLlama (collateral price ÷ loan-token price). A market-tracking oracle keeps δ near 0 whatever happens, so its markets simply never approach d\*; an oracle that does not follow the market lets δ grow with the depeg. The same number also catches a market-tracking oracle that has stopped updating or been misconfigured, which is drainable in exactly the same way.

**The bad debt a drain leaves.** The drained loans are backed by collateral worth (1 − δ) / LLTV per unit at the market. Once that is below 1, the difference is bad debt:

$$
\text{bad debt} = \text{drained} \times \max\!\left(0,\ 1 - \frac{1-\delta}{\text{LLTV}}\right)
$$

It starts at δ = 1 − LLTV and grows with the depeg, since nothing liquidates the drained positions.

## 4. How much can be drained

**The market's free liquidity**: supply minus borrows. That is what the arbitrageur borrows.

**What the Public Allocator can move in.** Morpho's `BluePublicAllocator` (Ethereum `0x00b8…1e27`) lets **anyone** move a Vault V2's assets between its markets, within limits the vault's allocators set. During a drain, the arbitrageur can use it to pull the vault's healthy liquidity into the market being drained, then borrow that too. The tool reads, for the watched vault:

| Setting | Read with |
|---|---|
| Is the Public Allocator an allocator of the vault at all? | `isAllocator(publicAllocator)` on the vault |
| Can it allocate idle assets? | `vaultData(vault).canPullFromIdle` |
| Which adapters take part | `isActiveAdapter(vault, adapter)` |
| The Public Allocator's cap on the destination market | `absoluteCap(vault, id)` |
| Which markets it can pull from | `canPullFromMarket(vault, id)` |

The inflow into a market is the smallest of: the Public Allocator's cap minus the vault's allocation there; the room left under the vault's own three caps for that market (adapter, collateral, market id; absolute and relative); and the sources it may pull (idle assets if allowed, plus the withdrawable part of every other market it may pull from).

$$
\text{drainable} = \text{free liquidity} + \text{Public Allocator inflow}
$$

When the settings cannot be read (a replay older than the free RPC's state window), the table says so and counts no inflow.

## 5. The `DrainWindow` alert

| Level | When |
|---|---|
| warn | the collateral's discount δ comes within `drain_margin` (2 points) of d\* |
| critical | δ reaches d\*: the drain pays now |

It fires **on crossing**, per market, and gives the drainable amount, the vault's share of the market's supply, and, once open, the bad debt at the current discount. `depositor_impact` on a critical is the vault's share of the drainable amount: liquidity that leaves as loans never repaid.

**Cadence.** Oracle prices come with every state read. DefiLlama's prices are re-read every `drain_check_every_blocks` (25 blocks, about 5 minutes), so a depeg is seen within that delay.

## 6. Effect on the exit queue

Once a market is past d\*, its liquidity is not there for depositors: the first arbitrageur takes it. The exit queue therefore removes, from what can leave the vault, each open market's withdrawable part and what the Public Allocator would pull into it, first from the `forceDeallocate` tier, then from the plain tier. The table then prints a line saying how much was left out.

## 7. Reading the output: Sentora RLUSD Main

`watch --replay` prints, after the liquidation curves:

```
  drain threshold (oracle above the market price: a fixed or exchange-rate oracle lets the gap grow; Public Allocator settings not read: its inflow is not counted):
    market                                     below oracle      d*   margin        drainable vault share
    USDe/RLUSD (LLTV 91.5%)                          +0.03%   8.96%    8.93%    4,316,064 RLUSD        100%
    syrupUSDC/RLUSD (LLTV 91.5%)                     +0.02%   8.96%    8.94%      552,016 RLUSD        100%
    weETH/RLUSD (LLTV 86.0%)                         +0.15%  14.43%   14.28%   16,555,966 RLUSD        100%
    wstETH/RLUSD (LLTV 86.0%)                        +0.14%  14.43%   14.29%      116,878 RLUSD        100%
    kBTC/RLUSD (LLTV 86.0%)                          -0.07%  14.43%   14.50%   22,355,123 RLUSD        100%
    cbBTC/RLUSD (LLTV 86.0%)                         -0.23%  14.43%   14.65%    1,491,959 RLUSD        100%
    FXRP/RLUSD (LLTV 77.0%)                          -0.05%  23.38%   23.44%      963,800 RLUSD        100%
```

- **Every market is far from its threshold**: the oracles agree with the market to within 0.25 %. No alert fires.
- **The closest are the stablecoin-like markets** at a 91.5 % LLTV: a USDe or syrupUSDC depeg of 9 % opens them.
- **Sentora is the only supplier of each market** (vault share 100 %): whatever is drained is its depositors' money.
- **The Public Allocator** is not an allocator of this vault (checked live on 2026-10-10), so no healthy liquidity can be pulled in. On the replay its settings are not readable (the block is too old for the free RPC), and the table says so.

**A simulated USDe depeg.** Feeding the recorded state a USDe market price 10.7 % below the oracle (a test, `test_recorded_vault_is_far_from_every_threshold`):

| USDe below its oracle | Drain open | Drainable | Bad debt of the drained loans |
|---|---|---|---|
| 8.96 % (d\*) | yes | 4.32M RLUSD | 0.02M |
| 10.7 % | yes | 4.32M | 0.10M |
| 15 % | yes | 4.32M | 0.31M |
| 20 % | yes | 4.32M | 0.54M |
| 30 % | yes | 4.32M | 1.01M |

The exit queue then loses those 4.32M: what can leave falls from 85.6M to 81.3M, and the largest depositor's stuck part, even first out, rises from 63.8M to 68.2M.

## 8. Limits

- **The loans already made are not revalued.** The USDe market has 50M of the vault in it, 45.7M of it already lent against USDe. With an oracle that does not move, those loans are also underwater at the market price, but `market_risk.py` values positions at the oracle price, so their bad debt does not show. Valuing positions at the market price as well is the natural next step.
- **The buying cost is one number** (`drain_buy_cost`), not a quote per token and size. A real slippage curve (gap M3) would refine d\*.
- **Only the watched vault's Public Allocator** is counted. Other vaults supplying the same market can be drained into it through their own settings; deposits routed by a liquidity adapter add more.
- **DefiLlama is the market price.** A token DefiLlama does not price gives no discount ("n/a"), and an aggregate price can lag a fast depeg by the re-read delay.
- **No oracle classification.** The tool measures the gap rather than labelling the oracle; it does not say in advance which markets *can* drift.
- **A single block.** The model treats the drain as instant; it does not model competing arbitrageurs, a curator lowering caps in time (cap decreases are not timelocked), or MEV ordering.

## 9. Code and tests

| Function | Pure | Role |
|---|---|---|
| `d_star(lltv, cost)`, `discount(divergence)` | yes | the threshold and the measured gap |
| `headroom(cap, total)`, `pa_inflow(view, st, pa, market)` | yes | the Public Allocator inflow |
| `MarketDrain.drainable`, `.margin`, `.open`, `.bad_debt()` | yes | per market |
| `drains(view, st, markets, divergence, pa)` | yes | all markets of a vault |
| `assess`, `table` | yes | the alert and the start-up table |
| `drained_vault_liquidity` | yes | what the exit queue loses |
| `read_pa(f, view, block)` | no | the Public Allocator's settings |
| `VaultDrain` | — | wires it all into `watch.py` and `watch_user.py` |

`admin.py` gained `fresh_prices` (DefiLlama prices re-read at a cadence) and `divergence_at` (pure), which `read_divergence` now uses as well.

`tests/test_drain.py` checks d\* against Team 2's figures, the discount, the cap headroom (absolute and relative), the Public Allocator inflow bounded by its cap, the vault's caps and its sources, the alert's warn → critical crossing, the bad-debt formula, the exit queue's reduction, and the recorded vault (calm, then a simulated USDe depeg).

## Learn: what you need to understand

### Oracle price versus market price

A lending market needs to know what the collateral is worth. It asks its oracle, not the market, because a market price can be manipulated within one block. Many oracles go further and ignore the market on purpose: they price a liquid staking token at its redemption rate, or a PT at a formula that reaches par at maturity, because the market price of these tokens is noisy and could liquidate borrowers for no lasting reason. The cost of that choice is that a real depeg is invisible to the market.

### Why borrowing against an overvalued collateral drains a market

If the oracle says a token is worth 1 and the market sells it at 0.85, borrowing 0.915 against each token bought at 0.85 is a profit of 0.065 per token, with no intention of repaying. Every lender's free liquidity can be borrowed this way, in one transaction. *In the project:* `drain.d_star`, `MarketDrain.bad_debt`.

### The Public Allocator

Vault V2 lets its allocators delegate some reallocations to a public contract, so that borrowers can pull liquidity into the market they need without waiting for the curator. It is useful in normal times and dangerous in a drain: the healthy liquidity it can move is liquidity the drain can reach. The vault's allocators bound it with caps and can disable it. *In the project:* `drain.read_pa`, `drain.pa_inflow`; Morpho's documentation in `docs/external/morpho/docs.morpho.org-developers-docs/contracts/blue-public-allocator.md`, source in `docs/external/morpho/lib/vault-v2/src/periphery/blue-public-allocator/`.

### Check your understanding

1. **Why is d\* about 1 − LLTV?** At a discount of 1 − LLTV, collateral bought at the market is worth exactly what can be borrowed against it at the oracle; any deeper discount makes borrowing more than paying.
2. **Why do the 91.5 % LLTV markets open first?** Their buffer between the oracle value and the loan is the thinnest: 8.5 %, against 14 % at 86 %.
3. **Why can the drain cost more than the free liquidity?** The Public Allocator can move the vault's healthy liquidity into the market first, and that is borrowed too.
4. **Why does the tool not need to know the oracle's kind?** It measures the gap between the oracle and the market. A market-tracking oracle keeps that gap near zero, so its markets never come close to d\*.
5. **Why does an open drain shrink the exit queue?** The drained liquidity is borrowed by the arbitrageur before depositors can withdraw it.

### Further reading

- Team 2, `teammate/team2.md`, "Fixed oracles: you're right, and it's worse than slightly mitigated".
- Morpho's documentation, [oracles](https://docs.morpho.org/developers/contracts/oracles) and the [Blue Public Allocator](https://docs.morpho.org/developers/contracts/blue-public-allocator) (local copies under `docs/external/morpho/docs.morpho.org-developers-docs/contracts/`).
- In this repository: `docs/exit-queue.md`, `docs/alert-runbook.md`, `docs/glossary.md`.
