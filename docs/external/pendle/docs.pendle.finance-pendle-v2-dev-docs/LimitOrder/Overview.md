# Limit Orders

> Source: https://docs.pendle.finance/pendle-v2-dev/LimitOrder/Overview

---

- [](https://docs.pendle.finance/)
- Limit Orders
- Overview

On this page
# Limit Orders

Pendle's Limit Order system enables gasless, off-chain order creation with secure on-chain settlement. It allows users to place orders at specific implied APY rates, which are matched and settled through the Limit Order smart contract.

## How It Works[​](#how-it-works)

1. **Makers** create limit orders by either (a) signing off-chain with no gas — the recommended path for EOAs — or (b) pre-signing on-chain via `preSignSingle` / `preSignBatch`, which is intended for smart-contract makers. Orders specify a desired implied APY rate and are stored on Pendle's backend.
2. **Takers** query available orders via the API and fill them on-chain by calling the Limit Order contract. Pre-signed orders (and orders already partially filled) can be filled with an empty signature; ERC-1271 contract signatures are also supported.
3. The **Limit Order contract** settles orders atomically, transferring tokens between makers and takers at the agreed rates.

Limit orders are also integrated into the [Pendle Hosted SDK](https://docs.pendle.finance/pendle-v2-dev/Backend/HostedSdk) — when enabled, the SDK automatically includes limit order liquidity alongside AMM liquidity to improve execution prices, especially for large trades.

## Order Types[​](#order-types)

| Order Type | Description |
| --- | --- |
| `SY_FOR_PT` | Swap SY (or a supported token) for PT |
| `PT_FOR_SY` | Swap PT for SY (or a supported token) |
| `SY_FOR_YT` | Swap SY (or a supported token) for YT |
| `YT_FOR_SY` | Swap YT for SY (or a supported token) |

## Sections[​](#sections)

- [**Limit Order Contract**](https://docs.pendle.finance/pendle-v2-dev/LimitOrder/LimitOrderContract) — Smart contract reference: order struct, method definitions, and callback mechanism
- [**Create a Limit Order**](https://docs.pendle.finance/pendle-v2-dev/LimitOrder/CreateALimitOrder) — Guide for makers: generate, sign, and submit orders
- [**Cancel Limit Orders**](https://docs.pendle.finance/pendle-v2-dev/LimitOrder/CancelOrders) — Guide for makers: cancel specific orders or invalidate all via nonce
- [**Fill a Limit Order**](https://docs.pendle.finance/pendle-v2-dev/LimitOrder/FillALimitOrder) — Guide for takers: query and fill orders on-chain

## API Reference[​](#api-reference)

- [Maker APIs](https://api-v2.pendle.finance/limit-order/docs#/Maker) — Generate order data, submit orders, view active orders
- [Taker APIs](https://api-v2.pendle.finance/limit-order/docs#/Taker) — Query available orders for filling
- [Order Book Socket.IO feed](https://docs.pendle.finance/pendle-v2-dev/Backend/SocketIO#order-book) — Pushed order-book snapshots every 5s instead of polling REST

## Maker Incentives[​](#maker-incentives)

Certain markets offer token rewards to makers who provide liquidity through limit orders.

### How Incentives Work[​](#how-incentives-work)

- **Epochs**: Incentives are distributed on a weekly basis.
- **Qualifying orders**: To be eligible, an order must be placed within the market's configured APY range and remain active for a minimum period. Orders that are placed and immediately canceled do not qualify.
- **Reward calculation**: Rewards are proportional to your order's effective making amount relative to the total qualifying volume within the epoch.

### Incentive Modes[​](#incentive-modes)

| Mode | Description |
| --- | --- |
| `RELATIVE` | Rewards apply to orders placed within a configured APY range relative to the current market rate |
| `ABSOLUTE` | Rewards apply to orders placed within a fixed APY range |

### Qualifying for Rewards[​](#qualifying-for-rewards)

1. Check whether the market has an active incentive program.
2. Place an order within the market's configured APY range.
3. Keep the order active — rewards accumulate proportionally to your share of total qualifying making volume within the epoch.