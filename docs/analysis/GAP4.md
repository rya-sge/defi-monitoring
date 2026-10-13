# GAP4: the backtest's debt figure, and how the slides present it

The PT-reUSD backtest (`riskdep backtest`, plan `2026-10-11-backtest`) predicts the right borrowers in both markets: 13 of 13 and 7 of 7, none missed, none extra. Its debt figure is weaker. It predicts the **full debt** of every liquidatable position, while liquidators repaid less, much less in the USDT market (1.89M predicted, 0.96M repaid). This file explains the gap from the recording and proposes a fix: give the debt as a range with a lower bound that Morpho's own rule sets. It also lists the wording changes the presentation needs (`slides.fuca.ch/agencetoutrisk`, slides 6 to 8).

## Status (2026-10-11)

| # | Improvement | Where | Status |
|---|---|---|---|
| G4.1 | Debt as a range: the minimum that restores health, up to the full debt | `backtest.py`, README, test | open |
| G4.2 | Per-position check: repaid within the range, full or partial | `backtest.py` | open |
| G4.3 | Slide 8 wording and figures | the slides (outside this repository) | open |
| G4.4 | Slides 6 and 7 wording | the slides | open |
| G4.5 | Which liquidator takes a whole position and which stops at the floor | — | not planned: one episode cannot calibrate it |

## 1. What the gap is

The model counts, for each position below the LLTV at the episode's lowest oracle price, its whole debt (`backtest.compare`, `predicted_debt`). That is the most the liquidators **could** repay. Morpho lets a liquidator repay any amount, so the realised figure can only be equal or smaller.

Position by position, from `fixtures/replay/backtest-pt-reusd-2026-08-25/` (debt read at block 25,829,808, the state before):

| Market | Positions liquidated in full | Positions liquidated in part | Predicted | Repaid |
|---|---|---|---|---|
| PT-reUSD/USDC | 12 | 1 (`0x5d86…`, 28 %) | 35.46M | 35.19M |
| PT-reUSD/USDT | 4 | 3 (`0xc819…` 19 %, `0x6554…` 31 %, `0xfeff…` 14 %) | 1.89M | 0.96M |

The USDT gap is almost entirely those three positions, which liquidators repaid in small events of 36k to 108k each, five on one position. The USDC gap is the one partial position.

## 2. The lower bound Morpho's rule sets

`Morpho.liquidate` requires the position to be unhealthy when it is called. A liquidator who repays in several events must therefore stop once the position is healthy again. The repayment that restores health at price $P$ follows from the health rule, with $V = C \cdot P$ the collateral value:

$$
(V - r \cdot \text{LIF}) \cdot \text{LLTV} \geq D - r
\iff
r \geq r_{\min} = \frac{D - V \cdot \text{LLTV}}{1 - \text{LIF} \cdot \text{LLTV}}
$$

The bound holds while $\text{LIF} \cdot \text{LLTV} < 1$ (here $1.02617 \times 0.915 = 0.939$). Below $r_{\min}$ the position stays liquidatable, and above it a further liquidation reverts. So the realised repayment of a liquidated position lies in $[r_{\min}, D]$, unless the oracle moves again during the episode, which can lower the floor further as the price recovers.

Checked on the recording at each market's lowest price:

| Market | Minimum ($\sum r_{\min}$) | Repaid | Maximum ($\sum D$) | Positions within the range |
|---|---|---|---|---|
| PT-reUSD/USDC | 8.05M | **35.19M** | 35.46M | 13 / 13 |
| PT-reUSD/USDT | 0.33M | **0.96M** | 1.89M | 7 / 7 |

Each of the four partial liquidations stopped at or just above its own floor (for example, `0xfeff…` needed 28.6k to be healthy again and was repaid 35.9k). The other sixteen were taken in full, mostly by one liquidator repaying 96 % of the debt in single events.

## 3. What to build

### G4.1 Debt as a range

- **`backtest.compare`:** add `predicted_min_debt`, the sum of $r_{\min}$ over the predicted positions at the lowest price, clipped to $[0, D]$ per position. Keep `predicted_debt` as the maximum. The bonus gets the same two bounds ($\times (\text{LIF} - 1)$).
- **`Backtest.lines()`:** print `debt liquidatable` as `min – max` next to `repaid`, e.g. `8,053,571 – 35,463,198 / 35,188,280`.
- **README backtest table:** the same range, and one sentence on why the floor exists.
- **The `from_sale` and cascade variants:** carry the range too, so the prediction from the trade alone is stated the same way.

### G4.2 Per-position check

- For each liquidated position, the repaid sum against its $[r_{\min}, D]$: count the positions inside, and classify each as `full` (repaid ≥ 99 % of $D$) or `partial`.
- A line in the output: `repaid within [min, max] for 20 of 20 positions (16 full, 4 partial)`.
- **Test** in `tests/test_backtest.py`: every liquidated position of the recorded episode lies within its range, and the counts are 16 full and 4 partial. A model change that moves a bound past the chain fails the suite, as D164 already does for the borrowers.
- **The second episode** (`crash-2025-10-10`) has a moving oracle and many extra positions. Run the check there before stating it as general; positions liquidated after a further price fall can exceed a floor computed at one price, so the floor must be taken at the price of each event's block for that episode.

Size: about 20 lines in `backtest.py`, one test, the README table. No new data: everything is in the existing recording.

## 4. The slides

### G4.3 Slide 8 (the backtest)

- **Column title.** "Dette liquidée" mixes a prediction with a realised figure. Use "Dette liquidable / remboursée" (liquidatable / repaid).
- **Figures.** Show the range: "35,19M dans 8,05–35,46M" and "0,96M dans 0,33–1,89M". The USDT row then reads as inside the prediction instead of half of it.
- **One line for questions.** The shock is the observed oracle fall; from the trade alone, the rebuilt Pendle pool gives −2.36 % and the same 20 positions (README, backtest section).

### G4.4 Slides 6 and 7

- **Slide 6** shows "50 % of the vault on a constant-price oracle" without naming the vault. Name it: RockawayX USDC Yield (`0xE018…1965`), 9.14M of 18.44M allocated, at the recorded block.
- **Slide 7** says "Sortir en premier, au pair". "Au pair" is jargon for a non-finance audience; "sans décote" (without a discount) or "retrait au prix plein" (withdrawal at full price) reads more easily. The 34,538 under it is the loss left after leaving first (the part that cannot leave at once), not a cost of leaving; a short label says so.

## 5. What this does not fix

- **Who liquidates in full.** One liquidator took whole positions; smaller ones took chunks and stopped near the floor. Which behaviour applies depends on a liquidator's capital and on how much seized PT it can sell (the Pendle pool accepted only 309,320 more PT at the first liquidation, against 38.6M seized). A model of it would need many episodes; the range states what the protocol guarantees without it.
- **Interest.** The debt is read 60 blocks before the first liquidation, so a fully repaid position shows a few units more repaid than predicted. Negligible, and not worth reading the state per event.
