# Midnight

> Source: https://docs.morpho.org/developers/contracts/midnight

---

# Midnight

[Midnight repository](https://github.com/morpho-org/midnight)

## [Market parameters](#market-parameters)

### [Market id](#market-id)

The market id is a `bytes32` value derived from the market parameters. It is used to identify a market in Midnight and is computed by the `IdLib.toId` function using a `CREATE2`-style hash of the encoded `Market` struct.

```
function toId(Market memory market) internal pure returns (bytes32);
```

### [Market struct](#market-struct)

```
struct Market {
    uint256 chainId;
    address midnight;
    address loanToken;
    CollateralParams[] collateralParams;
    uint256 maturity;
    uint256 rcfThreshold;
    address enterGate;
    address liquidatorGate;
}
```

| Name | Type | Description |
| --- | --- | --- |
| `chainId` | uint256 | The chain ID the market is deployed on. |
| `midnight` | address | The Midnight contract address. |
| `loanToken` | address | The ERC-20 loan token. |
| `collateralParams` | CollateralParams[] | Array of collateral configurations (1 to 128). Entries must be sorted in strictly ascending order by collateral token address, with no duplicate tokens. |
| `maturity` | uint256 | Unix timestamp at which the market matures. |
| `rcfThreshold` | uint256 | Recovery close factor threshold, expressed in raw loan-token units using the loan token's decimals. Not a percentage. |
| `enterGate` | address | Optional gate controlling who can increase credit or debt. Zero address means no restriction. |
| `liquidatorGate` | address | Optional gate controlling who can liquidate. Zero address means no restriction. |

### [CollateralParams struct](#collateralparams-struct)

```
struct CollateralParams {
    address token;
    uint256 lltv;
    uint256 liquidationCursor;
    address oracle;
}
```

| Name | Type | Description |
| --- | --- | --- |
| `token` | address | The ERC-20 collateral token. |
| `lltv` | uint256 | Liquidation loan-to-value ratio (scaled by 1e18). Must be enabled by governance. |
| `liquidationCursor` | uint256 | Controls the liquidation incentive (scaled by 1e18). Must be enabled by governance. |
| `oracle` | address | Oracle returning the price of 1 collateral unit quoted in loan tokens, scaled by 1e36. |

Enabled `lltv` and `liquidationCursor` values must also form a compatible pair. The derived maximum liquidation incentive factor, `maxLif`, is scaled by `1e18`. Market creation requires `maxLif <= 2e18` and, unless `lltv == 1e18`, `lltv * maxLif <= 0.999e36`.

### [MarketState struct](#marketstate-struct)

```
struct MarketState {
    uint128 totalUnits;
    uint128 lossFactor;
    uint128 withdrawable;
    uint128 continuousFeeCredit;
    uint16 settlementFeeCbp0;
    // ... settlementFeeCbp1 through settlementFeeCbp6
    uint32 continuousFee;
    uint8 tickSpacing;
}
```

`totalUnits` tracks total outstanding credit-side units. It is not a debt total. `lossFactor` tracks cumulative slashing. `withdrawable` is the amount of loan tokens lenders can currently withdraw.

### [Position struct](#position-struct)

```
struct Position {
    uint128 credit;
    uint128 pendingFee;
    uint128 lastLossFactor;
    uint128 lastAccrual;
    uint128 debt;
    uint128 collateralBitmap;
    uint128[128] collateral;
}
```

Each address has one position per market. `credit` and `debt` are in units. `collateralBitmap` tracks which collateral slots are active. `pendingFee` tracks [the continuous fee](https://docs.morpho.org/learn/concepts/midnight/#fees) reserved against lender credit. [Settlement fees](https://docs.morpho.org/learn/concepts/midnight/#fees) are charged separately when an offer is taken and are not stored in the position.

## [Offer struct](#offer-struct)

```
struct Offer {
    Market market;
    bool buy;
    address maker;
    uint256 start;
    uint256 expiry;
    uint256 tick;
    bytes32 group;
    address callback;
    bytes callbackData;
    address receiverIfMakerIsSeller;
    address ratifier;
    bool reduceOnly;
    uint128 maxUnits;
    uint128 maxAssets;
    uint256 continuousFeeCap;
}
```

| Name | Type | Description |
| --- | --- | --- |
| `buy` | bool | `true` if the maker is buying units, `false` if the maker is selling units. Buying can first reduce debt before increasing credit; selling can first reduce credit before increasing debt. |
| `maker` | address | Address of the offer's maker. |
| `start` | uint256 | Unix timestamp before which the offer cannot be taken. |
| `expiry` | uint256 | Unix timestamp after which the offer can no longer be taken. |
| `tick` | uint256 | Price tick representing the fixed rate. Must be a multiple of the market's current `tickSpacing`; otherwise `take` reverts. |
| `group` | bytes32 | Identifier for the maker’s shared consumption counter. A consistent shared budget assumes the same `buy` direction, loan token, `maxUnits`, and `maxAssets` across offers. The core contract does not enforce these matches. |
| `callback` | address | Optional maker callback. For a buy offer, it is called as the buyer callback before loan-token transfers; for a sell offer, it is called as the seller callback after transfers. |
| `callbackData` | bytes | Data forwarded to the maker callback. |
| `receiverIfMakerIsSeller` | address | Receiver of loan tokens when the maker is the seller (`buy = false`). Must be the zero address when `buy = true`. |
| `ratifier` | address | Contract that validates whether the offer can be consumed by a given taker. |
| `reduceOnly` | bool | If `true`, the offer may only reduce the maker's position: a maker buy offer may only reduce maker debt, and a maker sell offer may only reduce maker credit. The taker's position is not restricted by this flag. |
| `maxUnits` | uint128 | Maximum units the offer can be filled for. |
| `maxAssets` | uint128 | Maximum assets (buyer assets if `buy`, seller assets otherwise). |
| `continuousFeeCap` | uint256 | Maximum continuous fee rate the maker accepts, expressed per second and scaled by `1e18`. Not an annualized rate. |

Exactly one of `maxUnits` and `maxAssets` must be non-zero. Setting both or neither causes `take` to revert.

## [Stored state](#stored-state)

The following public getters expose raw values stored by the Midnight contract. Position values can be stale because loss socialization and continuous fees are applied lazily; use [`updatePositionView`](#updatepositionview) for an up-to-date calculation.

### [position](#position)

```
function position(bytes32 id, address user)
    external
    view
    returns (
        uint128 credit,
        uint128 pendingFee,
        uint128 lastLossFactor,
        uint128 lastAccrual,
        uint128 debt,
        uint128 collateralBitmap
    );
```

Returns the raw stored position fields for `user` in market `id`. The fixed-size collateral array is read separately through the collateral getter and is not returned here.

### [marketState](#marketstate)

```
function marketState(bytes32 id)
    external
    view
    returns (
        uint128 totalUnits,
        uint128 lossFactor,
        uint128 withdrawable,
        uint128 continuousFeeCredit,
        uint16 settlementFeeCbp0,
        uint16 settlementFeeCbp1,
        uint16 settlementFeeCbp2,
        uint16 settlementFeeCbp3,
        uint16 settlementFeeCbp4,
        uint16 settlementFeeCbp5,
        uint16 settlementFeeCbp6,
        uint32 continuousFee,
        uint8 tickSpacing
    );
```

Returns the raw accounting and configuration state for market `id`, including total units, loss factor, withdrawable liquidity, accrued continuous-fee credit, settlement-fee breakpoints, continuous-fee rate, and tick spacing.

### [consumed](#consumed)

```
function consumed(address user, bytes32 group) external view returns (uint128);
```

Returns how much of `user`'s shared offer-group capacity has already been consumed. Depending on the offers in the group, the value represents units or assets.

### [isAuthorized](#isauthorized)

```
function isAuthorized(address authorizer, address authorized) external view returns (bool);
```

Returns the stored authorization flag indicating whether `authorized` may act on behalf of `authorizer`.

### [isLltvEnabled](#islltvenabled)

```
function isLltvEnabled(uint256 lltv) external view returns (bool);
```

Returns whether the WAD-scaled `lltv` value is enabled for market creation.

### [isLiquidationCursorEnabled](#isliquidationcursorenabled)

```
function isLiquidationCursorEnabled(uint256 liquidationCursor) external view returns (bool);
```

Returns whether the WAD-scaled `liquidationCursor` value is enabled for market creation.

## [Selected functions](#selected-functions)

### [take](#take)

```
function take(
    Offer memory offer,
    bytes memory ratifierData,
    uint256 units,
    address taker,
    address receiverIfTakerIsSeller,
    address takerCallback,
    bytes memory takerCallbackData
) external returns (uint256 buyerAssets, uint256 sellerAssets);
```

Executes a trade against an offer. Buying units first nets existing debt and only then increases credit; selling units first nets existing credit and only then increases debt. Settlement transfers loan tokens between the parties according to the matched tick price.

`take` calculates settlement fees at execution. If the fee changes after a quote, the taker may pay more or receive less than quoted. The function has no maximum-payment or minimum-receipt parameter.

#### [Parameters:](#parameters)

| Name | Type | Description |
| --- | --- | --- |
| `offer` | Offer | The offer to consume. |
| `ratifierData` | bytes | Data passed to the offer's ratifier for validation. |
| `units` | uint256 | Number of units to fill (must not exceed the offer's remaining capacity). |
| `taker` | address | Address taking the opposite side of the offer. The caller must be `taker` or an account authorized by `taker` on Midnight. |
| `receiverIfTakerIsSeller` | address | Receiver of loan tokens when the taker is the seller (`offer.buy = true`). Must be the zero address when `offer.buy = false`. |
| `takerCallback` | address | Optional taker callback. When `offer.buy = false`, it is the buyer callback and runs before loan-token transfers. When `offer.buy = true`, it is the seller callback and runs after transfers. |
| `takerCallbackData` | bytes | Data forwarded to the taker callback. |

#### [Return values:](#return-values)

| Name | Type | Description |
| --- | --- | --- |
| `buyerAssets` | uint256 | Loan tokens transferred from the buyer. |
| `sellerAssets` | uint256 | Loan tokens received by the seller. |

### [withdraw](#withdraw)

```
function withdraw(Market memory market, uint256 units, address onBehalf, address receiver) external;
```

Redeems credit units for loan tokens, subject to the position's available credit and the market's `withdrawable` liquidity.

#### [Parameters:](#parameters-1)

| Name | Type | Description |
| --- | --- | --- |
| `market` | Market | The market to withdraw from. |
| `units` | uint256 | Credit units to redeem. |
| `onBehalf` | address | Address whose credit is reduced. The caller must be `onBehalf` or an account authorized by `onBehalf` on Midnight. |
| `receiver` | address | Address that receives the loan tokens. |

### [repay](#repay)

```
function repay(Market memory market, uint256 units, address onBehalf, address callback, bytes memory data) external;
```

Repays debt units, releasing the borrower's obligation. Accepts an optional callback for flash-repay patterns.

#### [Parameters:](#parameters-2)

| Name | Type | Description |
| --- | --- | --- |
| `market` | Market | The market to repay in. |
| `units` | uint256 | Debt units to repay. |
| `onBehalf` | address | Borrower whose debt is reduced. The caller must be `onBehalf` or an account authorized by `onBehalf` on Midnight. |
| `callback` | address | Optional repayment callback. If nonzero, it must hold `units` of the loan token and approve Midnight before returning `CALLBACK_SUCCESS`. Midnight then pulls repayment from the callback with `transferFrom`. If zero, repayment is pulled from the caller. |
| `data` | bytes | Data forwarded to the callback. |

### [supplyCollateral](#supplycollateral)

```
function supplyCollateral(Market memory market, uint256 collateralIndex, uint256 assets, address onBehalf) external;
```

Deposits collateral for a borrower into a given collateral slot.

#### [Parameters:](#parameters-3)

| Name | Type | Description |
| --- | --- | --- |
| `market` | Market | The market to supply collateral to. |
| `collateralIndex` | uint256 | Index into `market.collateralParams`. |
| `assets` | uint256 | Amount of collateral to deposit. |
| `onBehalf` | address | Borrower who receives the collateral credit. The caller must be `onBehalf` or an account authorized by `onBehalf` on Midnight. |

### [withdrawCollateral](#withdrawcollateral)

```
function withdrawCollateral(
    Market memory market,
    uint256 collateralIndex,
    uint256 assets,
    address onBehalf,
    address receiver
) external;
```

Withdraws collateral for a borrower, provided the position remains healthy after withdrawal.

#### [Parameters:](#parameters-4)

| Name | Type | Description |
| --- | --- | --- |
| `market` | Market | The market to withdraw collateral from. |
| `collateralIndex` | uint256 | Index into `market.collateralParams`. |
| `assets` | uint256 | Amount of collateral to withdraw. |
| `onBehalf` | address | Borrower whose collateral is withdrawn. The caller must be `onBehalf` or an account authorized by `onBehalf` on Midnight. |
| `receiver` | address | Address that receives the collateral. |

### [liquidate](#liquidate)

```
function liquidate(
    Market memory market,
    uint256 collateralIndex,
    uint256 seizedAssets,
    uint256 repaidUnits,
    address borrower,
    bool postMaturityMode,
    address receiver,
    address callback,
    bytes memory data
) external returns (uint256 outputSeizedAssets, uint256 outputRepaidUnits);
```

Liquidates a borrower in normal mode when the position is unhealthy, or in post-maturity mode after maturity regardless of health. Set `postMaturityMode` to `false` for normal mode and `true` for post-maturity mode. After maturity, an unhealthy borrower can be eligible for either mode.

At least one of the `seizedAssets` or `repaidUnits` inputs must be `0`. When one is provided, the contract computes the other and returns both final values. Passing both inputs as `0` is permitted to realize bad debt without transferring tokens.

With a nonzero `callback`, Midnight sends seized collateral to `receiver` and calls `onLiquidate`, which must return `CALLBACK_SUCCESS`. Midnight then pulls the final `repaidUnits` of the loan token from the callback using `transferFrom`. For a nonzero repayment, the callback must hold those tokens and approve Midnight before returning. With no callback, repayment is pulled from the caller.

#### [Return values:](#return-values-1)

| Name | Type | Description |
| --- | --- | --- |
| `outputSeizedAssets` | uint256 | Collateral assets seized by the liquidator. |
| `outputRepaidUnits` | uint256 | Debt units repaid. |

### [flashLoan](#flashloan)

```
function flashLoan(address[] memory tokens, uint256[] memory assets, address callback, bytes memory data) external;
```

Flash-loans any tokens held by the contract. Midnight transfers the assets to `callback`, calls `onFlashLoan`, then pulls the same amounts back with `transferFrom`. Before returning `CALLBACK_SUCCESS`, the callback must hold the repayment amounts and approve Midnight to spend them.

### [touchMarket](#touchmarket)

```
function touchMarket(Market memory market) external returns (bytes32);
```

Creates a market if it does not yet exist and returns its id. Safe to call on an already-created market.

### [updatePosition](#updateposition)

```
function updatePosition(Market memory market, address user) external returns (uint128 newCredit, uint128 newPendingFee, uint128 accruedFee);
```

Applies accumulated slashing and continuous-fee accrual to a position. `withdraw` calls the internal update automatically, while `take` calls it when needed for existing or newly created credit. `repay`, `supplyCollateral`, `withdrawCollateral`, and `liquidate` do not call it directly.

## [Utility functions](#utility-functions)

### [multicall](#multicall)

```
function multicall(bytes[] memory calls) external;
```

Executes encoded Midnight calls sequentially in one transaction. Each call uses `delegatecall`, and the entire batch reverts with the failing call's error if any call fails.

### [setConsumed](#setconsumed)

```
function setConsumed(bytes32 group, uint128 amount, address onBehalf) external;
```

Sets the consumed amount for `onBehalf`'s offer group. `amount` must be equal to or greater than the current value, so the counter can never decrease. Setting it to `type(uint128).max` cancels all remaining offers in the group.

### [setIsAuthorized](#setisauthorized)

```
function setIsAuthorized(address authorized, bool newIsAuthorized, address onBehalf) external;
```

Grants or revokes persistent authorization for `authorized` to act on `onBehalf`'s Midnight state.

Authorization applies across all markets in this Midnight contract. An authorized account can also grant or revoke authorization for other accounts on behalf of `onBehalf`.

## [Computed views](#computed-views)

For `updatePositionView` and `isHealthy`, callers must ensure that `id` corresponds to `market` (`id == IdLib.toId(market)`). These functions do not validate the relationship.

### [updatePositionView](#updatepositionview)

```
function updatePositionView(Market memory market, bytes32 id, address user)
    external
    view
    returns (uint128 newCredit, uint128 newPendingFee, uint128 accruedFee);
```

Calculates the position after applying pending loss-factor slashing and continuous-fee accrual, without modifying storage. Returns the resulting credit, pending fee, and accrued fee.

### [toMarket](#tomarket)

```
function toMarket(bytes32 id) external view returns (Market memory);
```

Reconstructs and returns the immutable `Market` parameters stored for `id`. Reverts if the market has not been created.

### [isHealthy](#ishealthy)

```
function isHealthy(Market memory market, bytes32 id, address borrower) external view returns (bool);
```

Returns whether the borrower's collateral supports their debt. For positions with debt, it prices each active collateral, applies its LLTV, sums the resulting maximum debt, and checks that `maxDebt >= debt`.

### [settlementFee](#settlementfee)

```
function settlementFee(bytes32 id, uint256 timeToMaturity) external view returns (uint256);
```

Returns the WAD-scaled settlement-fee rate for the supplied time to maturity. The value is linearly interpolated between the market's configured fee breakpoints and uses the longest breakpoint at and beyond 360 days.

## [Interfaces](#interfaces)

### [IGate](#igate)

Gates are optional access-control contracts set at market creation. Two gate roles are available:

```
interface IEnterGate {
    function canIncreaseCredit(address account) external view returns (bool);
    function canIncreaseDebt(address account) external view returns (bool);
}

interface ILiquidatorGate {
    function canLiquidate(address account) external view returns (bool);
}
```

Gates cannot lock or seize user assets. They only control whether an account may enter a position or liquidate.

### [IRatifier](#iratifier)

Ratifiers validate offers at execution. Every offer specifies a ratifier; the maker must authorize it, and `take` succeeds only if `isRatified(...)` returns `CALLBACK_SUCCESS`.

```
interface IRatifier {
    function isRatified(Offer memory offer, bytes memory ratifierData, address taker) external view returns (bytes32);
}
```

Must return `keccak256("morpho.midnight.callbackSuccess")` to approve the take.

### [Callbacks](#callbacks)

Five callback interfaces are available for flash patterns:

```
interface IBuyCallback {
    function onBuy(bytes32 id, Market memory market, uint256 buyerAssets, uint256 units, uint256 pendingFeeIncrease, address buyer, bytes memory data) external returns (bytes32);
}

interface ISellCallback {
    function onSell(bytes32 id, Market memory market, uint256 sellerAssets, uint256 units, uint256 pendingFeeDecrease, address seller, address receiver, bytes memory data) external returns (bytes32);
}

interface IRepayCallback {
    function onRepay(bytes32 id, Market memory market, uint256 units, address onBehalf, bytes memory data) external returns (bytes32);
}

interface ILiquidateCallback {
    function onLiquidate(address caller, bytes32 id, Market memory market, uint256 collateralIndex, uint256 seizedAssets, uint256 repaidUnits, address borrower, address receiver, bytes memory data, uint256 badDebt) external returns (bytes32);
}

interface IFlashLoanCallback {
    function onFlashLoan(address caller, address[] memory tokens, uint256[] memory assets, bytes memory data) external returns (bytes32);
}
```

All callbacks must return `keccak256("morpho.midnight.callbackSuccess")`.

## [Constants](#constants)

| Constant | Value | Description |
| --- | --- | --- |
| `WAD` | `1e18` | Fixed-point scale. |
| `ORACLE_PRICE_SCALE` | `1e36` | Oracle price scale. |
| `CBP` | `1e12` | Cent basis point scale used for fees. |
| `MAX_CONTINUOUS_FEE` | `0.01e18 / 365 days` | Maximum continuous fee rate per second. |
| `TIME_TO_MAX_LIF` | `60 minutes` | Time from maturity for the liquidation incentive to reach its maximum in post-maturity mode. Normal mode uses the maximum immediately. |
| `MAX_COLLATERALS` | `128` | Maximum collateral types per market. |
| `MAX_COLLATERALS_PER_BORROWER` | `16` | Maximum active collateral slots per borrower position. |
| `DEFAULT_TICK_SPACING` | `4` | Default tick spacing for new markets. |

## [Periphery and ratifiers](#periphery-and-ratifiers)

Optional helper contracts are available in the [periphery folder](https://github.com/morpho-org/midnight/tree/main/src/periphery):

- **BlueBuyCallback** - callback that funds buy offers by withdrawing loan tokens previously supplied to a Morpho Blue market on behalf of the callback contract.
- **EcrecoverAuthorizer** - enables signature-based authorization changes after the helper has been authorized on Midnight for the relevant account. Signed changes are submitted through the helper and executed onchain.

Ratifier contracts are available in the [ratifiers folder](https://github.com/morpho-org/midnight/tree/main/src/ratifiers):

- **SetterRatifier** - verifies that an offer belongs to a Merkle root ratified by its maker.

[Addresses

Previous Page

](https://docs.morpho.org/developers/contracts/addresses/)[Blue

Next Page

](https://docs.morpho.org/developers/contracts/blue/)