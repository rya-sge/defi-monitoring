# Interest Rate Models

> Source: https://docs.morpho.org/developers/contracts/irm

---

# Interest Rate Models

[Interest Rate Model repository](https://github.com/morpho-org/morpho-blue-irm)
Interest rate models are defined as a list of governance-approved contracts.
Each contract implements the [IRM interface](https://github.com/morpho-org/morpho-blue/blob/main/src/interfaces/IIrm.sol) exposed below.

## [Function](#function)

### [borrowRate](#borrowrate)

```
function borrowRate(MarketParams memory marketParams, Market memory market) external returns (uint256);
```

Returns the borrow rate of the market `marketParams`.

#### [Parameters:](#parameters)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](https://docs.morpho.org/get-started/resources/contracts/morpho/#marketparams-struct) | The MarketParams struct of the market. |
| `market` | [Market](https://docs.morpho.org/get-started/resources/contracts/morpho/#market-struct) | The Market struct of the market. |

#### [Return values:](#return-values)

| Name | Type | Description |
| --- | --- | --- |
| `borrowRate` | uint256 | The borrow rate of the market. |

## [View Function](#view-function)

### [borrowRateView:](#borrowrateview)

```
function borrowRateView(MarketParams memory marketParams, Market memory market) external view returns (uint256);
```

Returns the borrow rate of the market `marketParams` without modifying any storage.

#### [Parameters:](#parameters-1)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](https://docs.morpho.org/get-started/resources/contracts/morpho/#marketparams-struct) | The MarketParams struct of the market. |
| `market` | [Market](https://docs.morpho.org/get-started/resources/contracts/morpho/#market-struct) | The Market struct of the market. |

#### [Return values:](#return-values-1)

| Name | Type | Description |
| --- | --- | --- |
| `borrowRate` | uint256 | The borrow rate of the market. |

Make sure the input parameters correspond to the last time the market was
updated (check `lastUpdate`) and apply the returned borrow rate as is applied
in Morpho over the period between the market's `lastUpdate` and the query's
block timestamp.

## [Calculations](#calculations)

The Annual Percentage Yields (APY) for both borrowing and supplying are key indicators of the returns for lenders and the cost for borrowers. The APY takes into account the compounding interest to provide a standardized measure of yields over a one-year period.

### [Borrow APY](#borrow-apy)

The Borrow APY is calculated using the following formula:

borrowAPY=(e(borrowRate×secondsPerYear)−1)\text{borrowAPY} = \left(e^{\left(\text{borrowRate} \times \text{secondsPerYear}\right)} - 1\right)borrowAPY=(e(borrowRate×secondsPerYear)−1)
Where:

- `borrowRate` is the borrow rate per second, as determined by the Interest Rate Model (IRM),
- `secondsPerYear` represents the total number of seconds in a year (31,536,000).

To obtain the `borrowRate` value, a simple call can be made to the `borrowRateView` or `borrowRate` functions defined in the upper sections.

### [Supply APY](#supply-apy)

The Supply APY is calculated considering the utilization and the fee. The formula is:

The `fee` is the portion of the interest paid by borrowers that is retained by the protocol. For more details, see the [Curator Fee Section](https://docs.morpho.org/curate/concepts/fee/).

supplyAPY=borrowAPY×utilization×(1−fee)\text{supplyAPY} = \text{borrowAPY} \times \text{utilization} \times (1 - \text{fee})supplyAPY=borrowAPY×utilization×(1−fee)
Where:

- `fee` is the fee of the market, to be activated by the governance, on a per-market basis,
- `utilization` is calculated as:

utilization=totalBorrowAssetstotalSupplyAssets\text{utilization} = \frac{\text{totalBorrowAssets}}{\text{totalSupplyAssets}}utilization=totalSupplyAssetstotalBorrowAssets​

# [AdaptiveCurveIRM](#adaptivecurveirm)

Here is a video that shows how the Adaptive Curve IRM works:

Your browser does not support the video tag.

## [Overview](#overview)

In Morpho, the interest borrowers pay is defined by an external interest rate model (IRM) that can be chosen at market creation among a governance-defined collection.

The AdaptiveCurveIRM is the first IRM that will be available for Morpho markets. It fundamentally differs from the ones used in traditional lending pools for two main reasons:

- Unlike current lending pools' IRMs which can be updated, the AdaptiveCurveIRM is immutable. It must therefore adapt autonomously to market conditions, such as changes in interest rates on other venues.
- In Morpho, the supply is not used as collateral. There is no need to keep markets very liquid to allow liquidations at any time. Removing this systemic risk enables more aggressive target utilization of the capital and lower penalties for illiquidity, enabling more efficient markets.

The AdaptiveCurveIRM is designed to adjust utilization to the target utilization, which is set at 90%. There are two time horizons at play: In the short term, we don't want utilization to get too low, or too high and cause liquidity problems. In the medium and long term, we want the rate level to adapt to changing market dynamics.

To achieve this, the AdaptiveCurveIRM adjusts user incentives through the action of two different mechanisms:

- The Curve Mechanism
- The Adaptive Mechanism

## [The Curve Mechanism](#the-curve-mechanism)

This mechanism is similar to the interest rate curve used in traditional lending pools.

The curve is characterized by two parameters:

r90% which is the target rate at utilization target utarget=0.9r_{90\%} \text{ which is the target rate at utilization target } u_{target}=0.9r90%​ which is the target rate at utilization target utarget​=0.9
and

c=4c=4c=4
a fixed parameter that determines the steepness of the curve above and below the utilization target.

![Curve Mechanism 1](https://docs.morpho.org/img/morpho-blue/curve-mechanism-01.png)
At each interaction, utilization will change, resulting in a discontinuous change in the rate determined by the curve.

For example:

- if utilization is 90%, the rate is

r90%r_{90\%}r90%​
- if utilization is 100%, the rate (APR) is

4∗r90%4*r_{90\%}4∗r90%​

The aim of the Curve Mechanism is to manage short-term utilization changes.

## [The Adaptive Mechanism](#the-adaptive-mechanism)

This mechanism continuously shifts the curve to adjust to market conditions over time.

Note that the rate follows the shift of the curve. This means that the rate is continuously evolving over time, even when there is no interaction.

The shifting of the curve is done by continuously changing the value of r_90% over time:

- When the utilization is above the target utilization,

r90%r_{90\%}r90%​
continuously shifts upwards.

- When the utilization is below the target utilization,

r90%r_{90\%}r90%​
continuously shifts downwards.

 
![Morpho Banner](https://docs.morpho.org/img/morpho-blue/curve-mechanism-02.png)
The speed at which r90% moves is updated at each interaction: the farther we are from the target, the faster r90%, hence the curve, shifts.

For example, if the utilization remains at 100% for 5 days,

r90%r_{90\%}r90%​
will progressively double.
This is the maximum speed at which

r90%r_{90\%}r90%​
can move.

The values of some
[constants](https://github.com/morpho-org/morpho-blue-irm/blob/main/src/adaptive-curve-irm/libraries/ConstantsLib.sol)
are hardcoded into the code deployed on Ethereum, such as
`TARGET_UTILIZATION`, `INITIAL_RATE_AT_TARGET`, etc.

## [Formal description](#formal-description)

We define:

- Utilzation
uuu

u(t)u(t)u(t)
is the ratio of total borrow over total supply at time

ttt
The utilization target is constant:

u_target=0.9u\_{target}=0.9
u_target=0.9

- Error (
eee

):

∀t,\forall t,∀t,
e(u)={u(t)−utarget1−utargetif u(t)>utargetu(t)−utargetutargetif u(t)≤utargete(u)=\begin{cases}
\frac{u(t)-u_{target}}{1-u_{target}}&\text{if } u(t)>u_{target} 
\frac{u(t)-u_{target}}{u_{target}}&\text{if } u(t)\le u_{target}
\end{cases}e(u)={1−utarget​u(t)−utarget​​​if u(t)>utarget​utarget​u(t)−utarget​​​if u(t)≤utarget​​
It can be seen as the difference between the utilization and the target, divided by a normalization factor. The normalization is here to make the distance between utarget and u = 1 equals to the distance between utarget and

u=0u=0
u=0
![Morpho Banner](https://docs.morpho.org/img/morpho-blue/curve-mechanism-05.png)

- Curve:

curve(u)={(1−1kd)∗e(u)+1if u≤utarget(kd−1)∗e(u)+1if u>utarget\text{curve}(u)=
\begin{cases}
(1-\frac{1}{k_d})*e(u)+1&\text{if } u\le u_{target} 
(k_d-1)*e(u)+1&\text{if } u>u_{target}
\end{cases}curve(u)={(1−kd​1​)∗e(u)+1​if u≤utarget​(kd​−1)∗e(u)+1​if u>utarget​​
with

kd=4k_d=4
kd​=4

- History of interactions (

H\mathcal{H}H

):

Noting

tit_iti​
the time at which the

ithi^{th}ith
interaction occurred,

∀t,\forall t,∀t,
H(t)={0}+{ti}ti<t\mathcal{H}(t)=\{0\}+\{t_i\}_{t_i< t}H(t)={0}+{ti​}ti​<t​

- Last interaction (

last  \text{last}last
∀t,\forall t,∀t,
last(t)=max⁡(H(t))\text{last}(t) = \max(\mathcal{H}(t))last(t)=max(H(t))

- Speed factor (

speed  \text{speed}
speed
):

∀t, speed(t)=exp⁡(kP∗e(u(last(t)))∗(t−last(t))), with kp=50\forall t, \text{ speed}(t) = \exp \big({k_P*e(\text{u}(\text{last}(t)))*(t-\text{last}(t))\big)}, \text{ with } k_p = 50∀t, speed(t)=exp(kP​∗e(u(last(t)))∗(t−last(t))), with kp​=50

- Rate at target (

rT  r_T
rT​
rT(0)r_T(0)rT​(0)
is set to an arbitrary value

Then,

∀t>0,rT(t)=rT(last(t))∗speed(t)\forall t >0, r_T(t)=r_{T}(\text{last}(t))*\text{speed}(t)∀t>0,rT​(t)=rT​(last(t))∗speed(t)
At any time t, the borrow rate

rrr
is given by the formula:

r(t)=rT(t)∗curve(u(t))r(t) = r_{T}(t)* \text{curve}(u(t))r(t)=rT​(t)∗curve(u(t))

## [Implementation](#implementation)

> [Adaptive Curve IRM Github repository](https://github.com/morpho-org/morpho-blue-irm)

The contract implements the [Interest Rate Model interface](https://github.com/morpho-org/morpho-blue/blob/main/src/interfaces/IIrm.sol) to fit Morpho's specifications.

Moreover, the implementation stores configuration variables and a market parameter updated at each `borrowRate` call for this market.

## [Variables](#variables)

### [Constants](#constants)

The values of the following constants are hardcoded into the [code deployed on Ethereum](https://etherscan.io/address/0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC#code#F8#L27)

- `CURVE_STEEPNESS`: Curve steepness (scaled by WAD), value = `4`.
- `ADJUSTMENT_SPEED`: Adjustment speed per second (scaled by WAD), value = `50/nb of seconds per year`.
- `TARGET_UTILIZATION`: Target utilization (scaled by WAD), value = `90%`.
- `INITIAL_RATE_AT_TARGET`: Initial rate at target per second (scaled by WAD), value = `4%/nb of seconds per year`.
- `MIN_RATE_AT_TARGET`: Minimum rate at target per second (scaled by WAD), value = `0.1%/nb of seconds per year`.
- `MAX_RATE_AT_TARGET`: Maximum rate at target per second (scaled by WAD), value = `200%/nb of seconds per year`.

## [Immutables](#immutables)

- `MORPHO`: Address of Morpho.

## [Mappings](#mappings)

### [Rate at target](#rate-at-target)

```
mapping(Id => uint256) public rateAtTarget;
```

Rate at target utilization for each market. Tells the height of the curve.

## [Events](#events)

### [BorrowRateUpdate](#borrowrateupdate)

```
event BorrowRateUpdate(Id indexed id, uint256 avgBorrowRate, uint256 rateAtTarget);
```

Emitted when the borrow rate is updated (called by Morpho).

#### [Parameters:](#parameters-2)

| Name | Type | Description |
| --- | --- | --- |
| `id` | Id | The id of the market. |
| `avgBorrowRate` | uint256 | The average borrow rate of the market. |
| `rateAtTarget` | uint256 | The stored rate at target of the market. |

[Oracles

Previous Page

](https://docs.morpho.org/developers/contracts/oracles/)[Bundles

Next Page

](https://docs.morpho.org/developers/contracts/bundles/)