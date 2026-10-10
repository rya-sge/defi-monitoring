# Cross-Chain PT

> Source: https://docs.pendle.finance/pendle-v2-dev/Integration/CrossChainPT

---

- [](https://docs.pendle.finance/)
- Integration Guides
- Cross-Chain PT

On this page
# Cross-Chain PT

## Terminology[​](#terminology)

- Hub chain — the chain that the PT is originated from.
- Spoke chain — the chain that the bridged PT is deployed onto.

There is only 1 hub chain, but there can be multiple spoke chains. The terms "hub PT" and "spoke PT" are also used for the PT on the corresponding chain.

## 1. Why Cross-Chain PT?[​](#1-why-cross-chain-pt)

Cross-chain PT enables protocols and money markets on spoke chains to list Pendle PT assets while leveraging the deep liquidity of hub chain markets:

- **Redeemable at maturity** — always redeemable 1:1 with the underlying asset at maturity
- **Predictable price behavior** — PT price generally increases toward the underlying asset value over time, though it can decrease temporarily due to yield rate changes
- **Low liquidation risk** — bounded price behavior reduces liquidation risk compared to other collateral types
- **Hub chain liquidity** — spoke chains benefit from the hub chain's AMM depth without needing their own deep pools

## 2. Requesting a New Cross-Chain PT Deployment[​](#2-requesting-a-new-cross-chain-pt-deployment)

To request a new cross-chain PT deployment for your protocol or chain:

1. Submit your request via the [Cross-Chain PT Request Form](https://launch.pendle.finance/f/q1BK1hNyQ)
2. The Pendle team will review and complete the deployment

> **Note:** This request flow will migrate to the listing portal at [portal.pendle.finance](https://portal.pendle.finance) in the future.

## 3. Bridging, Selling, and Bridging Back[​](#3-bridging-selling-and-bridging-back)

Once a cross-chain PT is deployed, liquidators and users need a way to sell PT received on the spoke chain. Since AMM depth lives on the hub chain, selling involves bridging the PT to the hub chain, swapping, and bridging proceeds back.

**Example: PT-sUSDe on Sonic**

1. **Bridge** PT-sUSDe from Sonic (spoke chain) to Ethereum (hub chain)
2. **Sell** PT-sUSDe on the Ethereum Pendle market (deeper liquidity)
3. **Bridge** proceeds (e.g., USDC) back to Sonic

### Using Pendle UI (No Code)[​](#using-pendle-ui-no-code)

For manual or low-frequency operations:

1. Go to [Pendle Trade Markets](https://app.pendle.finance/trade/markets)
2. The UI handles bridging, swapping, and returning funds automatically in a single transaction

For a detailed UI walkthrough, see the [Cross-Chain PT App Guide](https://docs.pendle.finance/pendle-v2/AppGuide/CrossChainPT).

### Using pt-bridger Script (Programmatic)[​](#using-pt-bridger-script-programmatic)

For programmatic or automated flows (e.g., liquidation bots), use the **pt-bridger** script:

- **Repository:** [pendle-finance/pt-bridger](https://github.com/pendle-finance/pt-bridger)

## 4. Risks of Cross-Chain PT in Money Markets[​](#4-risks-of-cross-chain-pt-in-money-markets)

Protocols listing cross-chain PT as collateral should be aware of the following risks if the AMM on the **hub chain** is chosen for liquidation:

- **PT price can decrease before maturity** — changes in the yield rate can cause PT price to drop, even though it converges to 1:1 at maturity
- **Price drops may trigger liquidation** — if PT is used as collateral in a money market, a price decrease can push positions below the liquidation threshold
- **Bridging time** — there is a deplay to bridge PT and token back and fort, up to a few minutes. Liquidator is adviced to prepare their own tokens to liquidate the position first then use the [pt-bridger script](#using-pt-bridger-script-programmatic) to bridge the PT to the hub chain, sell it, and bridge proceeds back

## 5. Liquidation AMM[​](#5-liquidation-amm)

To address the liquidation risk on spoke chains, Pendle provides a **FixedPricePTAMM**.

- This AMM is deployed on **spoke chain**, enabling fast and direct liquidation with flash loan. There is no bridging deplay.
- This AMM allows to swap PT to token with a **fixed** price, which is provided by a [Linear discount oracle](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/LinearDiscountOracle). The price feed by this oracle is **deterministic**, and is **linearly** converged to 1 at PT's maturity. The convergence rate is called the *discounted rate*.

Because the AMM is **fast** and **deterministic**, it is suitable for the liquidation application on spoke chain. We also refer to this AMM as the liquidation AMM.

Pendle can help deploy a **FixedPricePTAMM** with a Linear discount oracle of your **desired** *discounted rate*. Alternatively, you can self-deploy the Linear discount oracle via the [Pendle Public DApp](https://dapp-public.pendle.finance/deploy-oracle).

### The Recommended Discounted Rate for the Oracle[​](#the-recommended-discounted-rate-for-the-oracle)

The oracle's *discounted rate* is defined as the PT price **one year** before the PT's maturity (so it is also called the *annually discounted rate*).

It is **recommended** to choose the discounted rate to satisfy the **suboptimal price** condition: the *discounted price* should **always** be smaller than PT market price on hub chain.

The *discounted rate* can be derived from the maximum yield of the market on the hub chain with the following formula:

ln⁡(1+max yield)\ln (1 + \textrm{max yield})ln(1+max yield)
For example, if the maximum yield of a market is 27%, the the recommended *discounted rate* is ln⁡(1+27%)≈0.239≈24%\ln(1 + 27\%) \approx 0.239 \approx 24\%ln(1+27%)≈0.239≈24%.

This formula guarantees the above condition about the suboptimal price.

The maximum yield of the market can be seen in the Specs section on Pendle DApp.

Example for the USDe 2025Sep market.
| Click the spec button | Getting the yield range |
| --- | --- |
| ![image.png](https://docs.pendle.finance/assets/images/ui-market-specs-38e34a9610a7c250ae6752dce1010199.png) | ![image.png](https://docs.pendle.finance/assets/images/ui-market-yield-range-9196f2f97ef9779db2ed307ac02ae0a1.png) |

Here the liquidity yield range is 5% - 27%. So the maximum yield is 27%.

tipThe specs page shows the maximum *possible* yield that the market allows to trade. If the implied yield is low and is not likely to hit this maximum yield, lower *max yield* can be chosen to increase the capital efficiency of the **FixedPricePTAMM**.

### How to Seed Liquidity[​](#how-to-seed-liquidity)

To bootstrap the Liquidation AMM with initial liquidity:

1. Coordinate with the Pendle team after your cross-chain PT deployment is complete
2. Provide initial liquidity to the Discount Rate AMM on the spoke chain
3. The seeded liquidity serves as the backstop for liquidation events

### Managing AMM Liquidity[​](#managing-amm-liquidity)

- **Who manages it** — the protocol listing PT as collateral is responsible for ensuring adequate liquidation AMM liquidity on the spoke chain
- **Rebalancing after liquidation events** — when liquidations consume AMM liquidity, the pool needs to be replenished to maintain liquidation capacity
- **Flashloan-based liquidation flow** — liquidators can use flashloans to execute liquidations, selling the PT through the Discount Rate AMM and repaying the flashloan from the proceeds. After liquidation, the consumed liquidity should be replenished by the managing protocol

### Liquidation Bot[​](#liquidation-bot)

Pendle runs liquidation bot for this AMM to help with liquidation on Morpho.

Please reach out if you want Pendle to support the liquidation bot system for your market.