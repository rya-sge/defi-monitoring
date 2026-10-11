# Scenarios and breakeven probabilities

> **Figures updated 2026-10-11 (D232–D237, GAP K3, K4, K5, K15, K17).** Oracle exploits are counted by the oracle layer only; Morpho Blue's core prior drops the Lending multiplier; hacks are weighted by age (half-life 2 years), which puts the top band at 3.29 %/yr; a synthetic dollar can collapse (2 %/yr, near total); the PT's stress in a depeg follows its time to maturity (a measured +9.79-point yield spike) instead of ×1.5. The demo's expected loss over 30 days is now **6,327 USD** (it was 6,265), its CVaR99 502,576 USD, the stress it should survive 9.2 % (was 12.2 %); the worked figures below were computed before, and their reasoning is unchanged.


This document details point 4.2 of `docs/analysis/comparison_team.md`: how `analyze` decides today from estimated probabilities, why the teammates question that, and how named scenarios with a **breakeven probability** would complement it. Every number comes from the offline demo position (a Morpho Blue borrower using PT-sUSDE-26NOV2026 as collateral, data as of 2026-10-10) and was computed with the tool's own loss function, `propagate.loss()`. A [learn section](#learn-what-you-need-to-understand) at the end explains the concepts used.

## Contents

- [1. The question](#1-the-question)
- [2. What the tool does today](#2-what-the-tool-does-today)
- [3. Why the teammates question it](#3-why-the-teammates-question-it)
- [4. The breakeven probability](#4-the-breakeven-probability)
- [5. Worked example on the demo position](#5-worked-example-on-the-demo-position)
- [6. How the two views fit together](#6-how-the-two-views-fit-together)
- [7. What could be implemented](#7-what-could-be-implemented)
- [8. Limits](#8-limits)
- [Learn: what you need to understand](#learn-what-you-need-to-understand)

## 1. The question

A portfolio manager holds a position and has three choices: **stay**, **reduce** (sell part of the collateral to repay debt), or **exit**. Staying earns a return (the *carry*) but exposes the position to incidents; leaving costs money now (the *exit cost*). The question is which choice is better, given what could go wrong.

## 2. What the tool does today

`analyze` estimates **how likely** each kind of incident is over the next 30 days, and **how much** it would cost:

1. **Probabilities.** Each layer (the chain, the yield source, the Pendle pool, Morpho, the oracle) gets a yearly probability of an incident. Exploit probabilities come from DefiLlama's record of hacks, by protocol size and category; depeg probabilities come from `registry.json`, each with a written basis. A 12 % yearly chance of an sUSDe depeg becomes 1.05 % over 30 days.
2. **Simulation.** 20,000 simulated months: in each, incidents happen at random with those probabilities, and the loss of each month is computed.
3. **Decision.** From the average loss (the *expected loss*), the average of the worst 1 % of months (*CVaR 99 %*) and the real exit cost quoted by Pendle.

For the demo position:

| Amount over 30 days | Value |
|---|---|
| Collateral | 3,934,214 USD |
| Debt | 3,413,978 USD |
| Equity (collateral − debt) | 520,236 USD |
| Carry (what staying earns) | 5,697 USD |
| Exit cost (price impact, fees, gas) | 78,946 USD |
| Expected loss (simulation) | 6,265 USD |
| CVaR 99 % | 510,184 USD, 98 % of the equity |

The verdict is **REDUCE**: the expected loss exceeds the carry, and the worst months lose almost everything, but a full exit costs more than it saves. The report adds one line in the direction the teammates ask for: *a full exit would only pay if incident probabilities were 13.5 times the estimates* (`risk_multiple_to_exit` = (carry + exit cost) ÷ expected loss = 84,643 ÷ 6,265).

## 3. Why the teammates question it

- **Team 2:** probabilities are "the weakest part of any such model". Nobody knows the chance that Ethena loses a third of its backing next month, and a base rate built from other protocols' hacks is at best an order of magnitude.
- **Team 1:** start with named scenarios, which a manager can read and discuss, and add a Monte Carlo later.

Both point at the same thing: the verdict depends on numbers the user cannot check. If the true depeg probability were three times higher, would the answer change? The current report answers only globally (the "13.5 times" line), not scenario by scenario.

## 4. The breakeven probability

Instead of estimating the probability, **compute the probability at which the decision flips**, and let the user judge whether reality is above or below it.

For one scenario *s* with a loss L(s) if it happens, over the horizon:

- **Staying** earns the carry and loses L(s) with probability p: on average, carry − p · L(s).
- **Exiting** costs the exit cost now and gives up the carry, but avoids L(s).

Exiting pays when p · L(s) > exit cost + carry, so the **breakeven probability** is:

$$
p^\star = \frac{\text{exit cost} + \text{carry}}{L(s)}
$$

If you believe the scenario is more likely than p\* over the horizon, exit; otherwise stay. Team 2's version, p\* = exit cost ÷ L(s), leaves out the carry; including it is consistent with the rule `analyze` already applies.

The same reasoning applies to **reducing**: de-levering costs its own price impact and some carry, and saves the part of the loss it avoids:

$$
p^\star_{\text{reduce}} = \frac{\text{reduce cost} + \text{carry given up}}{L(s) - L_{\text{reduced}}(s)}
$$

Two reading rules:
- **p\* above 100 %** means the decision never flips: even a certain incident costs less than leaving.
- **A low p\*** means the action is cheap insurance: a small belief in the scenario is enough to justify it.

## 5. Worked example on the demo position

The scenarios below use the demo position's numbers. The oracle is treated as following the PT market, as `analyze` does; the last column shows the loss if it did not. A depeg's "recovery" is the share of the depeg that comes back by the end of the horizon.

The de-lever is the one `analyze` proposes: sell 1.29M USD of collateral (33 %) and repay debt, at a quoted cost of 1,023 USD, giving up 1,347 USD of carry. It moves the liquidation distance from a 5.2 % to a 12.2 % oracle fall.

| Scenario over 30 days | Loss L(s) | Liquidated | p\* exit | Loss after de-lever | p\* reduce | Loss with a fundamental oracle |
|---|---|---|---|---|---|---|
| sUSDe depeg 5 %, 75 % recovers | 375,222 (72 % of equity) | yes | 22.6 % | 33,003, not liquidated | **0.7 %** | 49,178 |
| sUSDe depeg 10 %, 75 % recovers | 520,236 (all) | yes | 16.3 % | 441,405, liquidated | **3.0 %** | 98,355 |
| sUSDe depeg 10 %, no recovery | 520,236 (all) | yes | 16.3 % | 447,469, liquidated | **3.3 %** | 393,421 |
| sUSDe depeg 20 %, 75 % recovers | 520,236 (all) | yes | 16.3 % | 520,236, liquidated | — | 196,711 |
| Oracle misprices −5 % | 0 | no | — | 0 | — | 0 |
| Oracle misprices −10 % | 478,591 (92 %) | yes | 17.7 % | 0, not liquidated | **0.5 %** | 478,591 |
| Ethena loses 30 % of its backing | 520,236 (all) | yes | 16.3 % | 520,236 | — | 520,236 |
| Pendle SY exploit, 30 % | 520,236 (all) | yes | 16.3 % | 520,236 | — | 520,236 |
| Morpho exploit, 10 % of collateral | 393,421 (76 %) | no | 21.5 % | 264,025 | **1.8 %** | 393,421 |

"—" means the action does not change the loss in that scenario, so no probability makes it pay.

**What the table says.**
- **Exiting** pays only if you believe one of these shocks has a 16 to 23 % chance over the next 30 days. For a large, established protocol that is a strong belief: it matches the simulation's verdict that a full exit costs too much.
- **De-levering** pays from a belief of 0.5 to 3.3 % in the scenarios it helps. The simulation's own estimate of an sUSDe depeg of any size over 30 days is 1.05 %. So for small and medium shocks, de-levering is cheap insurance, which is why the verdict is REDUCE.
- **De-levering does not help against total-loss shocks** (Ethena losing its backing, a Pendle exploit, a 20 % depeg): the equity is lost either way. Only exiting protects against them, at a 16 % breakeven.
- **The loss is not proportional to the shock.** A 5 % depeg costs 72 % of the equity, and a 10 % depeg costs all of it, because the leverage (health factor 1.053) turns a shock beyond the 5.2 % liquidation distance into a liquidation. The oracle misprice shows it most clearly: −5 % costs nothing, −10 % costs 92 %.
- **The oracle behaviour matters.** With an oracle that does not follow the market, the same 5 % depeg costs 49,178 instead of 375,222, because no liquidation is triggered and most of the depeg recovers.

## 6. How the two views fit together

The two approaches answer different questions, and the report can show both:

| | Monte Carlo (today) | Scenarios with p\* (proposed) |
|---|---|---|
| Question answered | "What does the record of past incidents suggest?" | "How likely would this have to be for me to act?" |
| Probabilities | estimated from base rates | not needed: the user judges against p\* |
| Output | expected loss, tail loss, one verdict | a loss and a breakeven per named shock, per action |
| Strength | combines every risk into one number | readable, discussable, no hidden assumption about likelihood |
| Weakness | depends on base rates the user cannot check | covers only the scenarios listed; no single number |

The `risk_multiple_to_exit` line is the bridge: it is the global breakeven, over all scenarios weighted by their estimated probabilities.

A proposed report section:

```
Scenarios (30 days)                     loss      p* exit   p* reduce
sUSDe depeg 5 %, 75 % recovers        375,222      22.6 %      0.7 %
Oracle misprices −10 %                478,591      17.7 %      0.5 %
Ethena loses 30 % of its backing      520,236      16.3 %        —
...
Model estimate: an sUSDe depeg of any size within 30 days: 1.05 %.
Reading: reduce if you believe any line above is more likely than its p* reduce;
exit if you believe a total-loss line is more likely than its p* exit.
```

## 7. What could be implemented

**Size: S.** The loss function already exists and is pure.

1. **Scenario definitions in `registry.json`**, each with a name, the shock (layer and severity, as `propagate.loss()` takes it), a recovery for depegs, and a basis: for example the worst depeg on record for the yield token, a fixed oracle misprice, a fixed exploit size. One generic set applies to every position; issuers can add their own.
2. **`decide.scenarios(position, quote, reduction)`**, pure: for each scenario, the loss now, the loss after the proposed de-lever and with the other oracle behaviour, and p\* for exit and for reduce.
3. **Report and JSON**: the table of section 5 in `report.html`, the same data in `report.json`, and a one-line summary in the terminal ("reduce pays from 0.5 %; exit from 16.3 %").
4. **Tests**: the breakeven formula, the "—" case, and the demo values.
5. **A team decision** (D-row in a new plan): keep the Monte Carlo as the verdict and show the scenarios as a second view, or make the scenarios the basis of the verdict and the Monte Carlo a context line. A middle option is to let `registry.json` set `verdict_basis`.

The same table extends to a vault depositor once point 4.3 (`analyze --vault`) exists: the loss of a scenario is then the vault's share of each market's bad debt after the shock.

## 8. Limits

- **One scenario at a time.** Real crises combine shocks (a depeg drains the Pendle pool and the oracle follows), which the scenario list must name explicitly.
- **Today's exit cost.** p\* compares leaving *now* with staying. In a crisis the exit cost rises (worse slippage, crowded exits), so waiting for the scenario to start before leaving is more expensive than the table suggests.
- **Liquidations at the oracle price.** The loss assumes the liquidator takes the collateral at the oracle price with the liquidation bonus, with no market impact and no cascade.
- **The horizon matters.** p\* is a probability *over the horizon* (30 days here). A 16 % chance per month is a very different belief from 16 % per year.
- **Expected values hide ruin.** Breakeven reasoning compares averages. A manager who cannot afford to lose the whole equity should also apply a limit on the worst case, which is what the CVaR tail budget does today.

## Learn: what you need to understand

The concepts below are enough to read this document, `docs/model/how-risk-is-computed.md`, and the `analyze` report. Each comes with where it appears in the project.

### Probability over a horizon

A probability is always *over a period*. If an incident has a yearly probability p, the probability that it happens at least once over h days, assuming the risk is spread evenly over the year, is:

$$
p_h = 1 - (1 - p)^{h/365}
$$

A 12 % yearly chance becomes 1.05 % over 30 days, not 12 ÷ 12 = 1 %. The difference is small for small probabilities. *In the project:* `simulate._p_horizon`.

### Expected value and expected loss

The expected value of a gamble is the average outcome if it were repeated many times: the sum of each outcome times its probability. A 1 % chance of losing 500,000 USD has an expected loss of 5,000 USD. Decisions "on average" compare expected values: stay if the carry exceeds the expected loss. *In the project:* the expected loss of `analyze`.

### Base rates and their limits

A base rate is how often something happened in a reference group, used as a first estimate for a new case: "protocols of this size were hacked 2.66 % of the time per year". It anchors an estimate in data, which is better than intuition alone. Its limits: the reference group may not resemble the case (a large audited protocol is not an average one), and rare events have few data points. The *base rate fallacy* is the opposite error: ignoring the base rate in favour of a vivid story about the case. *In the project:* `priors.py`, gap M1.

### Distributions and the Beta distribution

A distribution describes how likely each value is. The tool uses a **Beta distribution** for an incident's severity because it lives between 0 and 1, a fraction of value lost, and its shape is set by two numbers a and b. Its average is a ÷ (a + b): Beta(2, 18) averages 10 %, with most values between 2 and 20 % and a few larger. *In the project:* every `severity` in `registry.json`.

### Monte Carlo simulation

When outcomes combine several random events, the distribution of the total is hard to compute by formula. A Monte Carlo simulation draws thousands of random cases and looks at the results. With n draws, the error on an average shrinks like 1 ÷ √n: 20,000 months give a stable expected loss but a less precise estimate of very rare tails. *In the project:* `simulate.run`, 20,000 months.

### Tail risk: VaR and CVaR

The average hides the bad cases. The **VaR 99 %** (value at risk) is the loss exceeded in 1 % of cases; the **CVaR 99 %** (conditional value at risk, also called expected shortfall) is the average loss *of* that worst 1 %. CVaR is preferred because it says how bad the bad cases are, not only where they start; bank regulation moved from VaR to expected shortfall for that reason. When incidents occur in fewer than 5 % of cases, the VaR 95 % is zero, which is why the tool measures the tail at 99 %. *In the project:* the CVaR 99 % tail budget of the verdict.

### Non-linear losses and leverage

With leverage, the loss is not proportional to the shock. Below the liquidation distance a price fall costs its size times the collateral; beyond it, a liquidation seizes most of the collateral at once. The loss curve has a "cliff". Small changes in the shock or in the health factor near that cliff change the outcome completely, which is why the scenario table shows −5 % costing nothing and −10 % costing almost everything. *In the project:* `propagate.loss`, the health factor and the liquidation distance.

### Scenario analysis, stress tests and sensitivity

- **Scenario analysis** asks "what happens if this specific thing occurs?" and gives a loss for each named case.
- **A stress test** is a scenario chosen to be severe but plausible, often from history (the worst depeg on record).
- **Sensitivity analysis** moves one input at a time to see which ones the result depends on (the oracle behaviour here).

None of them needs a probability, which is their strength and their limit.

### Breakeven (indifference) probability

The probability at which two choices have the same expected value. It turns a question nobody can answer ("what is the probability?") into one a person can ("is it more likely than 16 %?"). *In the project:* section 4 of this document; `risk_multiple_to_exit` is its global version.

### Risk versus uncertainty

Economists distinguish **risk**, where probabilities are known (a die), from **uncertainty**, where they are not (will an issuer lose its backing next month?). DeFi incidents are mostly uncertainty. Methods built for risk (Monte Carlo with estimated probabilities) give precise-looking numbers on uncertain inputs; breakeven reasoning is built for uncertainty.

### Calibration and subjective probability

Using p\* means stating your own probability. A person is **calibrated** if the events they call 10 % likely happen about 10 % of the time. Calibration improves with practice and feedback. Writing down estimates and checking them later is the standard method, and the *Brier score* (the mean squared error of probability forecasts) measures it.

### Optionality and cheap insurance

Some actions cost little and remove a large part of a bad outcome: they behave like insurance. De-levering in the table costs about 2,400 USD (quote plus carry given up) and turns a 375,222 USD loss into 33,003 in the 5 % depeg case. When insurance is cheap relative to the loss it removes, a small belief in the risk is enough to buy it.

### Risk aversion

Expected values treat a sure loss of 5,000 USD and a 1 % chance of losing 500,000 USD as equal. Most investors are not indifferent: losing the whole equity can end a strategy, so they accept a slightly lower average to avoid ruin. That preference is risk aversion, and it is why the tool applies a tail budget on top of the expected-value rule.

### Check your understanding

1. **Why is the loss of a 5 % depeg 72 % of the equity and not 5 %?** The position has a health factor of 1.053: a fall of 5.2 % in the oracle price liquidates it. The oracle follows the PT market, which falls further than the underlying during a depeg (1.5 times, here 7.5 %), so the position is liquidated and most of the collateral is seized at the depressed price.
2. **Why does reducing have a much lower p\* than exiting?** It costs about 2,400 USD instead of about 84,600 (exit cost plus carry), and for small and medium shocks it removes most of the loss by moving the liquidation distance beyond the shock.
3. **Why does reducing not help against a 30 % loss of Ethena's backing?** The loss is larger than the equity even after de-levering, so the equity is lost in both cases; only exiting avoids it.
4. **If you believe a 10 % oracle misprice has a 1 % chance this month, what should you do?** Reduce (p\* reduce 0.5 % < 1 %), not exit (p\* exit 17.7 % > 1 %).
5. **What does "exit only pays if probabilities were 13.5 times the estimates" mean?** The expected loss over all scenarios, weighted by the model's probabilities, would have to be 13.5 times larger before exiting beats staying.

### Further reading

- John C. Hull, *Risk Management and Financial Institutions* (Wiley): VaR, expected shortfall, stress testing, scenario analysis.
- Philippe Jorion, *Value at Risk: The New Benchmark for Managing Financial Risk* (McGraw-Hill).
- Frank H. Knight, *Risk, Uncertainty and Profit* (1921): the distinction between risk and uncertainty.
- Philip E. Tetlock and Dan Gardner, *Superforecasting: The Art and Science of Prediction* (2015): calibration and stating probabilities.
- Daniel Kahneman, *Thinking, Fast and Slow* (2011): base rates and the biases that ignore them.
- Morpho's [liquidation documentation](https://docs.morpho.org/developers/borrow/concepts/liquidation): health factor, liquidation incentive, bad debt.
- In this repository: `docs/model/how-risk-is-computed.md` (the `analyze` model step by step) and `docs/reference/glossary.md`.
