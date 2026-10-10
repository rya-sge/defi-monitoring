# Watching an address: the options and their trade-offs

The plan `plan/2026-10-10-morpho-user-watcher.plan.md` adds `watch --user <address>`, which finds a Morpho user's positions and follows them block by block. Writing it required four choices, asked as questions Q8 to Q11 of its interview. This document sets out, for each one, the options, what each costs and buys, and when another answer would be the better one. Your answers are recorded, and each can be revisited: they are decisions D31 to D35 of the plan.

The figures below come from the probes made on 2026-10-10 on the demo borrower `0xdf81…2730`. That address holds 12 Blue positions, 6 of them with debt; the Vault V2 position the API lists for it is empty (0 shares).

## Contents

- [1. Which positions to watch](#1-which-positions-to-watch)
- [2. How to set health-factor alerts](#2-how-to-set-health-factor-alerts)
- [3. How to watch the borrow rate](#3-how-to-watch-the-borrow-rate)
- [4. Exit cost for collateral that is not a Pendle PT](#4-exit-cost-for-collateral-that-is-not-a-pendle-pt)
- [Summary](#summary)

## 1. Which positions to watch

Question Q8, decision D31. A Morpho address can hold four kinds of position: Blue borrows, direct Blue supply, Vault V2 deposits and Vault V1 deposits. Each needs its own reader and its own rules.

| Option | Advantages | Drawbacks |
|---|---|---|
| **Borrows + V2 deposits** (chosen) | Covers the two positions where a user loses money fastest: liquidation and vault bad debt. The V2 part reuses the vault watcher that already exists and is tested. One run, one alert log for both. | Direct Blue supply and V1 deposits held by the same address are ignored, and the tool says so at start-up. |
| **Everything** | Nothing the address holds goes unwatched. | V1 vaults (MetaMorpho) are a different contract: other events (`ReallocateSupply`, `SubmitCap`, `UpdateLostAssets`…), supply and withdraw queues instead of adapters, and losses recorded in `lostAssets` rather than in the share price. That is a second vault reader to write and test, roughly the size of the V2 one. |
| **Blue borrows only** | The smallest increment, the fastest to deliver. | A user with a vault deposit runs two commands and reads two logs, and a risk shared by both positions, such as a market used by the borrow and by the vault, is seen twice, separately. |

**When to choose another answer.** "Everything" if the addresses you care about hold V1 vaults, which is still common for older deposits. Direct Blue supply is the cheaper of the two additions: the vault watcher already computes a supplier's share of bad debt and a market's withdrawable liquidity, so it could come in a small follow-up.

## 2. How to set health-factor alerts

Question Q9, decision D33. The health factor (HF) is collateral × oracle price × LLTV ÷ debt. Blue liquidates at HF ≤ 1, and Morpho's liquidation guide suggests warning users below 1.1.

The HF and the oracle drop that would trigger liquidation are two views of the same number, since the drop equals 1 − 1/HF:

| HF level | Oracle fall that liquidates |
|---|---|
| 1.10 | 9.1 % |
| 1.05 | 4.8 % |
| 1.02 | 2.0 % |

| Option | Advantages | Drawbacks |
|---|---|---|
| **1.10 / 1.05 / 1.02, overridable** (chosen) | Three levels give an escalation: time to plan at 1.10, act at 1.05, emergency at 1.02. The first level matches Morpho's own guidance. `--hf` lets a cautious user move all three up. | Three alerts for one market move can feel noisy on a position that hovers around a level; the plan limits this by alerting only when a level is crossed downwards, and once on recovery. |
| **One threshold 1.10** | Simplest, one alert per position. | No escalation: the same message at 1.09 and at 1.01, and nothing between the warning and the liquidation. |
| **Price-distance based** | Speaks the language of market moves ("a 5 % drop liquidates you"), which is easier to compare with a collateral's usual volatility. | Equivalent to HF levels (table above), so it adds no information; and HF is what Morpho's app and docs display, so two different scales would coexist. The startup table shows both anyway. |

**When to choose another answer.** If you run very high leverage, where 1.10 is never reached in normal operation, the defaults would alert permanently; then set your own levels with `--hf`. A volatility-aware threshold (for example an alert when the liquidation distance falls below twice the collateral's recent daily move) would be better than either, but needs price history per collateral and is not in this increment.

## 3. How to watch the borrow rate

Question Q10, decision D35. Morpho Blue markets use the AdaptiveCurveIRM: it steers utilisation towards 90 %, the rate at 100 % utilisation is 4 × the rate at target, and the target rate itself moves over time. The probe read 3.74 % on the demo borrower's market, identical to the API.

| Option | Advantages | Drawbacks |
|---|---|---|
| **Jumps + utilisation** (chosen) | Needs no input from the user. A 50 % rise from the value at start catches a rate that is drifting up; the 99 % utilisation alert catches the moment the rate is about to spike, before the debt has grown. Works for every market without knowing what the collateral yields. | "50 % above the start" depends on when the run began: a run started during a spike treats the spike as normal. The alert says the rate moved, not whether the position still pays. |
| **Absolute APY threshold** | Directly tied to the user's economics: "warn me if borrowing costs more than 12 %", typically the yield of the collateral. | The user must know and pass a number per position; one threshold for six different markets is wrong for most of them; a rate rising from 3 % to 8 % stays silent under a 12 % threshold. |
| **Not in this increment** | Smaller scope. | The rate is the risk that grows silently: a borrow can stay far from liquidation while its cost exceeds what the collateral earns, and nothing would show it. |

**When to choose another answer.** If you know the yield of each collateral, the best rule is the difference between that yield and the borrow rate (the carry), which `analyze` already computes for Pendle PT collateral. An `--max-apy` flag could be added beside the jump rule rather than replacing it.

## 4. Exit cost for collateral that is not a Pendle PT

Question Q11, decision D34. Leaving a borrow means selling collateral to repay debt, and the cost depends on how deep the market for that collateral is. The tool already gets a real quote from Pendle's API for PT collateral.

| Option | Advantages | Drawbacks |
|---|---|---|
| **PT only, others not quoted** (chosen) | Uses a source already integrated and tested; no new dependency; the table says plainly "not quoted" rather than showing a guessed number. | For the demo address, 2 of the 6 borrows (PST and sUSDS collateral) have no exit cost shown. |
| **Keyless aggregator quote** | One source for any collateral, so every borrow gets a cost. | Not verified yet: which aggregators answer without an API key, what rate limits they apply, and whether their quote for a large size is reliable all need probing first. Some collateral (staked or wrapped tokens) exits better through its own redemption than through a swap, which an aggregator quote would miss. |

**When to choose another answer.** If most of your borrows use collateral other than PTs, the aggregator becomes worth a probe and its own decision.

## Summary

| # | Question | Chosen | Main reason | Revisit if |
|---|---|---|---|---|
| Q8 | Positions | Borrows + V2 deposits | the two fastest ways to lose money, with the vault watcher reused | your addresses hold V1 vaults or direct supply |
| Q9 | HF alerts | 1.10 / 1.05 / 1.02, overridable | escalation, aligned with Morpho's 1.1 guidance | you run leverage that sits below 1.10 by design |
| Q10 | Borrow rate | jumps + utilisation | works for every market with no input | you know each collateral's yield and want a carry rule |
| Q11 | Exit cost | PT only | already integrated and tested | most of your collateral is not a PT |
