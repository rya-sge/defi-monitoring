# Choosing Linear Discount Parameters

> Source: https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/ChoosingLinearDiscountParams

---

- [](https://docs.pendle.finance/)
- Oracles
- Deterministic Oracles
- Choosing Params

On this page
# Choosing Linear Discount Parameters

In this documentation, we provide a Desmos graphic that let you fill in
parameters to help visualizing and choosing a good linear discount rate for the
linear discount oracle.

Desmos link: [https://www.desmos.com/calculator/xmtoxy6lkt](https://www.desmos.com/calculator/xmtoxy6lkt)

The Desmos link contains the example for the [USDe 25 SEP 2025 market](https://app.pendle.finance/trade/markets/0x6d98a2b6cdbf44939362a3e99793339ba2016af4/swap?view=yt&chain=ethereum).

- PT linear discount rate can be chosen to be 18%18\%18%.
- LP linear discount rate can be chosen to be 7%7\%7%.

See this in the Desmos graphic by changing rdiscountr_{discount}rdiscount​ in the corresponding folder.

## Parameters[​](#parameters)

### Market internal state[​](#market-internal-state)

The Desmos graphic requires some internal state of the Pendle market. The following notebook can be used to get the market’s internal state: [https://colab.research.google.com/drive/1CKltGGLWrdUoCVRpV1U9ZV2BqjMkN_OE?usp=sharing](https://colab.research.google.com/drive/1CKltGGLWrdUoCVRpV1U9ZV2BqjMkN_OE?usp=sharing)

For example, if the chosen market is [USDe 25 SEP 2025 market](https://app.pendle.finance/trade/markets/0x6d98a2b6cdbf44939362a3e99793339ba2016af4/swap?view=yt&chain=ethereum), the parameters can be obtained like the image on the left, and be filled as the image on the right.

| Running the notebook | Filling the parameters in Desmos |
| --- | --- |
| ![Params notebook](https://docs.pendle.finance/assets/images/params-notebook-aaaab1216ca4500929e7c19441b063ea.png) | ![Params Desmos](https://docs.pendle.finance/assets/images/params-desmos-31060ff8c44e4f55262f64570e0bfd5e.png) |

### Market yield range[​](#market-yield-range)

These parameters are opinionated. Please choose a yield range that you think the market will be trading in until maturity. The lower the rateMax\text{rateMax}rateMax, the less underprice the oracle will be, and the more capital efficient for the users.

Pendle Market also allows trading within a pre-determined yield range. If you are not sure about the yield range, use this.

This yield range can be obtained from the Pendle DApp UI:

| Click the spec button | Getting the yield range |
| --- | --- |
| ![image.png](https://docs.pendle.finance/assets/images/ui-market-specs-38e34a9610a7c250ae6752dce1010199.png) | ![image.png](https://docs.pendle.finance/assets/images/ui-market-yield-range-9196f2f97ef9779db2ed307ac02ae0a1.png) |

And filled it as the following:

![image.png](https://docs.pendle.finance/assets/images/yield-range-desmos-959e1a5076b466f39fcb5cf49c1419d8.png)

## Choosing between PT linear oracle and LP linear oracle[​](#choosing-between-pt-linear-oracle-and-lp-linear-oracle)

The Desmos graphic can help visualize both linear discount. The corresponding graphic can be toggled by clicking the corresponding folder

### Choosing the linear discount rate[​](#choosing-the-linear-discount-rate)

In both graphic:

- **The blue** lines are the maximum and minimum price of PT/LP (the price range).
- **The orange** line is the current price of PT/LP until maturity if there is no trade occurred.
- **The red** line is the discounted price of PT/LP with your discount rate.

Change rdiscountr_{discount}rdiscount​ to adjust the discounted price (the **red line**) and see its relation between the price range and the current price.

### Base price (or the matured price)[​](#base-price-or-the-matured-price)

For PT, since it can be redeem to asset 1:1 at maturity, the base price of PT is 1.

For LP, the base price is calculated in the Desmos graphic. It can be found in the *LP linear discount* Desmos folder:

![image.png](https://docs.pendle.finance/assets/images/lp-base-price-desmos-136f58b4c91a35d9ede4447fb6dd9847.png)

### Recommendation[​](#recommendation)

rdiscountr_{discount}rdiscount​ should be set so that the price is *sub-optimal* compare to the market price at all the time until maturity. Therefore:

- The **discounted price** line should be below the **current price**.
- The closer the **discounted price** line to the **current price**, the riskier.
- Setting rdiscountr_{discount}rdiscount​ so that the **discounted price** line is **under** the **lower price** line can make sure that the oracle price is always underpriced.

### Reference[​](#reference)

- [https://forum.sky.money/t/june-26-2025-proposed-changes-to-spark-for-upcoming-spell/26663](https://forum.sky.money/t/june-26-2025-proposed-changes-to-spark-for-upcoming-spell/26663) — Spark write up on linear discount rate for PT-syrupUSDC-28Aug2025, PT-USDe-25Sept2025, LP-USDS-14Aug2025.
- [https://www.desmos.com/calculator/n7wfzslz8l](https://www.desmos.com/calculator/n7wfzslz8l) — Desmos graphic for single trade on Pendle Market.