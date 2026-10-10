# Linear Discount Oracle Wrapper

> Source: https://docs.pendle.finance/pendle-v2-dev/Contracts/Oracle/LinearDiscountOracle/LinearDiscountOracleWrapper

---

- [](https://docs.pendle.finance/)
- Contracts
- Oracle
- Linear Discount Oracle
- Oracle Wrapper

On this page
# Linear Discount Oracle Wrapper

**Sources:**

- [`PendleLinearDiscountOracleWrapper.sol`](https://github.com/pendle-finance/pendle-core-v2-public/blob/main/contracts/oracles/StatelessWrapper/PendleLinearDiscountOracleWrapper.sol)
- [`PendleSparkLinearDiscountOracleFactoryWrapper.sol`](https://github.com/pendle-finance/pendle-core-v2-public/blob/main/contracts/oracles/StatelessWrapper/PendleSparkLinearDiscountOracleFactoryWrapper.sol)

## Overview[​](#overview)

`PendleLinearDiscountOracleWrapper` is a thin stateless wrapper that fixes the one incompatibility between Pendle's deterministic oracles and Chainlink-consuming protocols: the `updatedAt` field.

Pendle's deterministic oracles (`PendleSparkLinearDiscountOracle`, `PendleLpLinearDiscountOracle`) return `updatedAt = 0` in `latestRoundData()` because their prices are computed entirely from `block.timestamp` and immutable constructor parameters — they are never "stale" by design. However, most lending protocols enforce a staleness check of the form `block.timestamp - updatedAt < threshold`, which will reject any feed that returns `updatedAt = 0`.

The wrapper solves this by forwarding all fields from the inner oracle unchanged, **except `updatedAt`**, which it overwrites with `block.timestamp`.

---

## When to Use the Wrapper[​](#when-to-use-the-wrapper)

**Does your protocol check `updatedAt` staleness?**

- **No** — Deploy `PendleSparkLinearDiscountOracle` directly via `PendleSparkLinearDiscountOracleFactory`.
- **Yes** (most lending protocols) — Deploy via `PendleSparkLinearDiscountOracleFactoryWrapper`. The wrapper always returns `updatedAt = block.timestamp`, satisfying any staleness threshold.
- **You already have a bare oracle** — Call `PendleSparkLinearDiscountOracleFactoryWrapper.wrap(existingOracle)` to add the wrapper without redeploying.

LP oracle has no factory wrapper`PendleLpLinearDiscountOracle` does not have a dedicated factory wrapper contract. To apply the wrapper to an LP oracle, deploy `PendleLpLinearDiscountOracle` via `PendleLpLinearDiscountOracleFactory`, then wrap the deployed address manually:

```
address lpOracle   = lpFactory.create(market, baseLpDiscountPerYear, lpMaturedPrice);address lpWrapped  = address(new PendleLinearDiscountOracleWrapper(lpOracle));
```

---

## `PendleLinearDiscountOracleWrapper`[​](#pendlelineardiscountoraclewrapper)

A minimal proxy that wraps **any** `IPChainlinkOracleEssential`-compatible oracle and replaces its `updatedAt` with `block.timestamp`.

```
contract PendleLinearDiscountOracleWrapper is IPChainlinkOracleEssential {    IPChainlinkOracleEssential public immutable innerOracle;    constructor(address _innerOracle);}
```

### `latestRoundData`[​](#latestrounddata)

```
function latestRoundData()    external    view    returns (        uint80  roundId,        int256  answer,        uint256 startedAt,        uint256 updatedAt,      // overwritten to block.timestamp        uint80  answeredInRound    );
```

All fields are forwarded from `innerOracle.latestRoundData()`, except `updatedAt` which is replaced with `block.timestamp`. The `answer` (the discount factor or LP price) is not modified in any way.

### `decimals`[​](#decimals)

```
function decimals() external view returns (uint8);
```

Delegates directly to `innerOracle.decimals()`. Returns `18` for all Pendle deterministic oracles.

---

## `PendleSparkLinearDiscountOracleFactoryWrapper`[​](#pendlesparklineardiscountoraclefactorywrapper)

A convenience contract that combines `PendleSparkLinearDiscountOracleFactory` and `PendleLinearDiscountOracleWrapper` into a single deployment step. Calling `createWithPt` or `createWithMarket` on this contract:

1. Deploys a `PendleSparkLinearDiscountOracle` (via the inner factory)
2. Immediately wraps it in `PendleLinearDiscountOracleWrapper`
3. Returns the **wrapper address** — the address your protocol should point at

Emits `WrapperOracleCreated(address indexed innerOracle, address indexed wrapper)` on each deployment.

```
contract PendleSparkLinearDiscountOracleFactoryWrapper {    PendleSparkLinearDiscountOracleFactory public immutable innerFactory;    constructor(address _innerFactory);}
```

### `createWithPt`[​](#createwithpt)

```
function createWithPt(    address pt,    uint256 baseDiscountPerYear) external returns (address wrapper);
```

Deploys a `PendleSparkLinearDiscountOracle` for the given PT address, then wraps it. Returns the wrapper address.

### `createWithMarket`[​](#createwithmarket)

```
function createWithMarket(    address market,    uint256 baseDiscountPerYear) external returns (address wrapper);
```

Derives the PT address from `IPMarket(market).readTokens()`, then proceeds identically to `createWithPt`.

### `wrap`[​](#wrap)

```
function wrap(address innerOracle) public returns (address wrapper);
```

Wraps an already-deployed `IPChainlinkOracleEssential`-compatible oracle in a new `PendleLinearDiscountOracleWrapper`. Useful if you deployed an oracle via `PendleSparkLinearDiscountOracleFactory` directly and need to add the wrapper afterwards.

**Deployment addresses:** Find the factory wrapper address for each chain under `"sparkLinearDiscountOracleFactoryWrapper"` in the [Deployments on GitHub](https://github.com/pendle-finance/pendle-core-v2-public/tree/main/deployments).

---

## Further Reading[​](#further-reading)

- [Spark Linear Discount Oracle](https://docs.pendle.finance/pendle-v2-dev/Contracts/Oracle/LinearDiscountOracle/SparkLinearDiscountOracle) — full contract reference for the PT oracle
- [LP Linear Discount Oracle](https://docs.pendle.finance/pendle-v2-dev/Contracts/Oracle/LinearDiscountOracle/LpLinearDiscountOracle) — full contract reference for the LP oracle
- [Choosing Linear Discount Parameters](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/ChoosingLinearDiscountParams) — guidance on setting `baseDiscountPerYear`