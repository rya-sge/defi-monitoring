# GAPV5: what riskdep assumes about an issuer-rate oracle, checked on PST

PST/USDC is the book's largest market (38.0M, 35 % of the book). riskdep classes its oracle as constant-price, of the published kind (`docs/model/huma-pst.md`). Questioning that class on 2026-10-11 turned up four things the code assumes and does not check: the class rule looks at the direction of a feed's changes but not their size; the feed's value is taken as what PST is worth in USDC, with no check that anyone can mint or redeem at it; the loan token is taken to be worth exactly 1 USD; and a lower value is taken to arrive at the next round, with nothing read about who computes that round or how far it can fall. This file states each gap, what was measured, and what would close it.

## Status (2026-10-11)

| # | Gap | Where | Status |
|---|---|---|---|
| G5.1 | The class rule counts falls, not step sizes: a short run of rises in a market price would read as an accrual rate | `oracle_class.classify_input`, `registry.json` `graph` | open |
| G5.2 | The feed's value is not checked against what PST can be minted or redeemed for | `docs/model/huma-pst.md`; Huma's pool | open: needs Huma's pool rules |
| G5.3 | The oracle has no USDC/USD quote: USDC is taken to be worth exactly 1 USD | the oracle's quote side; `vault_incident` | open |
| G5.4 | Who computes "PST-USDC Exchange Rate (Calculated)", from what, and how far one round can move | `feeds.py`, `admin.py` | open: needs Chainlink's feed page |
| G5.5 | The pace of a markdown: "at its next round", about an hour, is an assumption | `oracle_class.MOVES`, `vault_incident.nav_timing` | open |

## G5.1 The class rule and a run of rises

**What the rule does.** `classify_input` reads at least 6 past rounds (`oracle_history_min`) and counts the changes and the falls. At least 20 % falls (`oracle_fall_share`) is a market price; fewer is an accrual rate. The threshold was set on 2026-10-10: USDC/USD, USDS/USD and ETH/USD fell 9 to 14 times in 24 rounds, and three exchange-rate and NAV feeds never fell.

**The gap.** The rule looks at the direction of each change, never its size. A market price in a steady run, or a feed with only 6 to 10 rounds readable, could rise every time and be classed as an accrual rate. The market would then be treated as one that no depeg can liquidate, which is wrong for a price-tracking oracle.

**Measured for PST** (49 rounds read live, 2026-10-11):

| | PST feed |
|---|---|
| Rounds | 49, about one an hour |
| Falls | 0 |
| Rise per hour | 4.35 to 13.18 parts per million, median 8.74 |
| Annualised | about 4 % to 12 %, median about 8 % |

The steps are tiny, regular and at a credit pool's yield: PST's class is right. A market price moves by much more between rounds, and both ways. Under a fair coin, 49 rises in a row has odds of about 0.5⁴⁹, about 1 in 10¹⁵.

**What would close it.** Two more conditions before "an accrual rate", each a registry threshold with its basis and a test:

1. **Step size:** every rise below a bound per round (for example 0.1 %). A market price breaks it quickly; an accrual never does.
2. **Pace:** the annualised rate of the steps inside a plausible yield range (for example 0 % to 30 %).

A feed that rises but fails either check is "not classified", shown and never guessed (D84), rather than constant-price.

## G5.2 Is 1.138 what PST can be minted or redeemed for?

**What riskdep assumes.** The oracle reads 1.138 USDC per PST, and the market lends against it. riskdep treats that as PST's value, and the gap to a DEX price as the drain's discount.

**What is known.** The value is a share of Huma's credit pool: its loans' interest is added to the share, not paid out. The pool lives on Solana, and PST on Ethereum is the copy bridged by CCIP (`bridge.py`).

**What is not known.** Whether Huma mints and redeems at that rate, and on what terms: fees, delays, queues, limits, who may redeem. If a redemption waits or pays a fee, a holder who needs USDC now gets less than 1.138, and the market overvalues PST even before any loss.

**What would close it.** Huma's pool rules: its Solana program, or its docs (`ROCK-VAULT-DEP.md` §10, item 1). Added under `docs/external/`, they would give the redemption path and its terms. riskdep would then state them as it does for siUSD's queue, fxSP's cool-down and Upshift's 7-day lag (an exit line, and the exit's cost in the incident).

## G5.3 USDC taken to be worth exactly 1 USD

**What riskdep assumes.** The PST oracle has a feed on the base side only: it converts PST to USDC at Huma's rate and stops there. The same holds for the fxSAVE, siUSD and PT-reUSD markets (`ROCK-VAULT-DEP.md` §3).

**The gap.** If USDC depegs, these oracles do not see it. For the lenders, who lent USDC and are repaid in USDC, this is mostly neutral. But the book's USD figures, and a comparison with a USD-priced collateral, take 1 USDC = 1 USD. riskdep's incident kinds shock collateral (`token=`) or the vault's own asset (`loan=`); a USDC depeg as a loan-asset shock on the USDC vaults is possible with `loan=USDC:<fall>`, but its effect through these oracles is not modelled.

**What would close it.** State in each incident on these markets that the oracle carries no quote of the loan token, and what a loan-token depeg does to the market's borrowers (their debt is worth less, so nobody is liquidated by it).

## G5.4 Who computes the round, and how far it can fall

**What is known.** The feed is a Chainlink `EACAggregatorProxy`, "PST-USDC Exchange Rate (Calculated)", owned by Chainlink's 4/9 multisig (`ROCK-VAULT-DEP.md` §3). "Calculated" means Chainlink computes it; from what source, and with what checks, is not read.

**The gap.** riskdep does not know:

- the source of the number: Huma's on-chain pool state on Solana, an API Huma publishes, or a report;
- whether a round can fall by any amount, or whether a deviation bound holds a large loss back, as the Midas band does (D241);
- whether the round can be pushed by Huma, or only by Chainlink's nodes.

**What would close it.** Chainlink's page for this feed, in the data-feeds documentation (`docs/external/chainlink/`) or on data.chain.link: its methodology, heartbeat, deviation and any bounds. If a bound exists, the incident should stage the markdown as it does for Midas (`vault_incident.feed_bands`).

## G5.5 The pace of a markdown

**What riskdep assumes.** A published value moves "at its next round, by a transaction" (`oracle_class.MOVES`); for PST, about an hour, from its round rhythm (D155).

**The gap.** That is when the feed can move, not when Huma's accounting records a loss. A default in the pool may take days or weeks to reach the share's value, depending on how Huma writes down a loan. Until then the oracle reads high, and the drain's discount can grow on DEXs while the market sees nothing.

**What would close it.** Huma's write-down policy (G5.2's documents). The incident's timing line would then say when a loss reaches the rate, not only when the rate reaches the oracle.

## What this does not change

The class of PST's oracle is right (G5.1's measure). So is the incident's shape: a market depeg liquidates nobody, a lowered rate lands at once, and liquidating PST needs a buyer that thin exit liquidity may not provide. The gaps are about how sure the figures can be, not about their direction.
