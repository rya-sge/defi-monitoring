# Spark Linear Discount Oracle (PT)

> Source: https://docs.pendle.finance/pendle-v2-dev/Contracts/Oracle/LinearDiscountOracle/SparkLinearDiscountOracle

---

- [](https://docs.pendle.finance/)
- Contracts
- Oracle
- Linear Discount Oracle
- Spark Linear Discount Oracle

On this page
# Spark Linear Discount Oracle (PT)

**Sources:**

- [`PendleSparkLinearDiscountOracle.sol`](https://github.com/pendle-finance/pendle-core-v2-public/blob/main/contracts/oracles/internal/PendleSparkLinearDiscountOracle.sol)
- [`PendleSparkLinearDiscountOracleFactory.sol`](https://github.com/pendle-finance/pendle-core-v2-public/blob/main/contracts/oracles/internal/PendleSparkLinearDiscountOracleFactory.sol)

## Overview[​](#overview)

`PendleSparkLinearDiscountOracle` is a deterministic feed that returns a **discount factor** for a given PT. The factor increases linearly as time passes and converges to `1.0` at maturity, so integrators can price PT conservatively without relying on external market data.

The returned value is a **multiplier in 18 decimals**, not a USD price. It implements `IPChainlinkOracleEssential` and is cardinality-free (no ring-buffer setup required).

For pricing formulas, use cases, and integration examples, see the [integration guide](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/LinearDiscountOracle).

---

## Should I use this oracle?[​](#should-i-use-this-oracle)

**Use this oracle if:**

- The market is newly listed and has no TWAP history yet
- Your protocol requires a manipulation-proof, fully deterministic price feed
- You prefer a predictable, auditable pricing function over market-derived rates

**Use [`PendlePYLpOracle`](https://docs.pendle.finance/pendle-v2-dev/Contracts/Oracle/PYLpOracle) instead if:**

- The market is established and has sufficient TWAP cardinality
- You need prices that track the actual market-implied rate

See [Choosing Linear Discount Parameters](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/ChoosingLinearDiscountParams) for guidance on selecting `baseDiscountPerYear`.

---

## Deployment[​](#deployment)

Deploy via `PendleSparkLinearDiscountOracleFactory`. Find the factory address under `"sparkLinearDiscountOracleFactory"` in the [Deployments on GitHub](https://github.com/pendle-finance/pendle-core-v2-public/tree/main/deployments).

```
// Deploy using the PT address directlyfunction createWithPt(address pt, uint256 baseDiscountPerYear) external returns (address);// Or derive PT from the market address automaticallyfunction createWithMarket(address market, uint256 baseDiscountPerYear) external returns (address);
```

Emits `OracleCreated(address indexed pt, uint256 baseDiscountPerYear, address oracle)`.

## `updatedAt` Staleness Compatibility[​](#updatedat-staleness-compatibility)

Most lending protocols reject feeds where `block.timestamp - updatedAt` exceeds a threshold. This oracle always returns `updatedAt = 0` — it is stateless and computes the price live from `block.timestamp`, so it is never stale by design.

If your protocol enforces a staleness check, use `PendleSparkLinearDiscountOracleFactoryWrapper` instead — it deploys and wraps the oracle in one step, returning `updatedAt = block.timestamp`. Find it under `"sparkLinearDiscountOracleFactoryWrapper"` in deployments. See [`LinearDiscountOracleWrapper`](https://docs.pendle.finance/pendle-v2-dev/Contracts/Oracle/LinearDiscountOracle/LinearDiscountOracleWrapper) for details.

---

## Reading the Price[​](#reading-the-price)

```
function latestRoundData()    external    view    returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound);
```

Only `answer` carries meaningful data. All other fields return `0`.

**Formula:**

```
timeLeft = max(maturity - block.timestamp, 0)discount = timeLeft × baseDiscountPerYear / SECONDS_PER_YEARanswer   = clamp(1e18 - discount, 0, 1e18)
```

`answer` is the current value of 1 PT as a fraction of its maturity redemption value. An `answer` of `0.95e18` means 1 PT is currently priced at 95% of 1 unit of the underlying asset.

```
function decimals() external pure returns (uint8);   // returns 18
```

---

## Contract Reference[​](#contract-reference)

### Public Variables[​](#public-variables)

| Variable | Type | Description |
| --- | --- | --- |
| `PT` | `address` | The PT token this oracle prices |
| `maturity` | `uint256` | Expiry timestamp, read from `PT.expiry()` at construction |
| `baseDiscountPerYear` | `uint256` | Annual discount slope; `1e18 = 100%/year`. Constructor enforces `<= 1e18`. |

### `getDiscount`[​](#getdiscount)

```
function getDiscount(uint256 timeLeft) public view returns (uint256);
```

Returns the raw discount amount for a given `timeLeft` in seconds. The `answer` from `latestRoundData()` equals `1e18 - getDiscount(timeLeft)`.

---

## Further Reading[​](#further-reading)

- [`LinearDiscountOracleWrapper`](https://docs.pendle.finance/pendle-v2-dev/Contracts/Oracle/LinearDiscountOracle/LinearDiscountOracleWrapper) — when and how to apply the `updatedAt` wrapper
- [LP Linear Discount Oracle](https://docs.pendle.finance/pendle-v2-dev/Contracts/Oracle/LinearDiscountOracle/LpLinearDiscountOracle) — deterministic pricing for LP tokens
- [Choosing Linear Discount Parameters](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/ChoosingLinearDiscountParams) — guidance on selecting `baseDiscountPerYear`
- [Integration Guide](https://docs.pendle.finance/pendle-v2-dev/Oracles/DeterministicOracles/LinearDiscountOracle) — pricing formulas, examples, and use cases