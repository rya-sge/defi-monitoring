# Blue

> Source: https://docs.morpho.org/developers/contracts/blue

---

# Blue

[Blue repository](https://github.com/morpho-org/morpho-blue/tree/731e3f7ed97cf15f8fe00b86e4be5365eb3802ac)
This page documents the Blue (Morpho Blue) variable rate market contract.

## [Market Parameters](#market-parameters)

### [Market id](#market-id)

The market id is a `bytes32` keccak256 hash of the [5 parameters of a market](#marketparams-struct). It is used to identify a market in Morpho.

```
type Id is bytes32;
```

To get the id from the parameters, a temporary solution is to execute [this gist](https://gist.github.com/tomrpl/3cfd34e04a01f9cbae2b16887f8026cf), or retrieve the id at market creation.

### [Market struct](#market-struct)

The market struct is defined as follows:

```
struct Market {
    uint128 totalSupplyAssets;
    uint128 totalSupplyShares;
    uint128 totalBorrowAssets;
    uint128 totalBorrowShares;
    uint128 lastUpdate;
    uint128 fee;
}
```

It contains the state of a market.
`totalBorrowAssets` & `totalSupplyAssets` accrues the interest of the market only until last interest accrual, while `totalBorrowShares` & `totalSupplyShares` are representing the total shares distributed over lenders / borrowers.

### [MarketParams struct](#marketparams-struct)

The majority of the entrypoints accept a `MarketParams` struct as parameter. This struct is defined as follows:

```
struct MarketParams {
    address loanToken;
    address collateralToken;
    address oracle;
    address irm;
    uint256 lltv;
}
```

As an integrator, you need to recover these 5 parameters to interact with Morpho.
You can also use the [idToMarketParams](#idtomarketparams) view function to recover the parameters of a given market from the bytes32 id.

## [Functions](#functions)

### [setOwner](#setowner)

```
function setOwner(address newOwner) external;
```

Sets `newOwner` as `owner` of the contract.

- Warning: No two-step transfer ownership.
- Warning: The owner can be set to the zero address.

#### [Parameters:](#parameters)

| Name | Type | Description |
| --- | --- | --- |
| `newOwner` | address | The new owner address. |

### [enableIrm](#enableirm)

```
function enableIrm(address irm) external;
```

Enables `irm` as a possible IRM for market creation.

- Warning: It is not possible to disable an IRM.

#### [Parameters:](#parameters-1)

| Name | Type | Description |
| --- | --- | --- |
| `irm` | address | The irm address to enable. |

### [enableLltv](#enablelltv)

```
function enableLltv(uint256 lltv) external;
```

Enables `lltv` as a possible LLTV for market creation.

- Warning: It is not possible to disable a LLTV.

#### [Parameters:](#parameters-2)

| Name | Type | Description |
| --- | --- | --- |
| `lltv` | uint256 | The lltv value to enable (18 decimals). |

### [setFee](#setfee)

```
function setFee(MarketParams memory marketParams, uint256 newFee) external;
```

Sets the `newFee` for the given market `marketParams`.

- Warning: The recipient can be the zero address.

#### [Parameters:](#parameters-3)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](#marketparams-struct) | The market parameters. |
| `newFee` | uint256 | The new fee value. |

### [setFeeRecipient](#setfeerecipient)

```
function setFeeRecipient(address newFeeRecipient) external;
```

Sets `newFeeRecipient` as `feeRecipient` of the fee.

- Warning: If the fee recipient is set to the zero address, fees will accrue there and will be lost.
- Modifying the fee recipient will allow the new recipient to claim any pending fees not yet accrued. To ensure that the current recipient receives all due fees, accrue interest manually prior to making any changes.

#### [Parameters:](#parameters-4)

| Name | Type | Description |
| --- | --- | --- |
| `newFeeRecipient` | address | The address of the new fee recipient. |

### [createMarket](#createmarket)

```
function createMarket(MarketParams memory marketParams) external;
```

Creates the market defined by `marketParams`.

Here is the list of assumptions on the market's dependencies (tokens, IRM and oracle) that guarantees
Morpho behaves as expected:

- The token should be ERC20 compliant, except that it can omit return values on `transfer` and `transferFrom`.
- The token balance of Morpho should only decrease on `transfer` and `transferFrom`. In particular, tokens with burn functions are not supported.
- The token should not re-enter Morpho on `transfer` nor `transferFrom`.
- The token balance of the sender (resp. receiver) should decrease (resp. increase) by exactly the given amount on `transfer` and `transferFrom`. In particular, tokens with fees on transfer are not supported.
- The IRM should not re-enter Morpho.
- The oracle should return a price with the correct scaling.

Here is a list of properties on the market's dependencies that could break Morpho's liveness properties:

- The token can revert on `transfer` and `transferFrom` for a reason other than an approval or balance issue.
- A very high amount of assets (~1e35) supplied or borrowed can make the computation of `toSharesUp` and `toSharesDown` overflow.
- The IRM can revert on `borrowRate`.
- A very high borrow rate returned by the IRM can make the computation of `interest` in `_accrueInterest` overflow.
- The oracle can revert on `price`. Note that this can be used to prevent `borrow`, `withdrawCollateral` and `liquidate` from being used under certain market conditions.
- A very high price returned by the oracle can make the computation of `maxBorrow` in `_isHealthy` overflow, or the computation of `assetsRepaid` in `liquidate` overflow.
- The borrow share price of a market with less than 1e4 assets borrowed can be decreased by manipulations, to the point where `totalBorrowShares` is very large and borrowing overflows.

#### [Parameters:](#parameters-5)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](#marketparams-struct) | The market parameters |

### [supply](#supply)

```
function supply(
        MarketParams memory marketParams,
        uint256 assets,
        uint256 shares,
        address onBehalf,
        bytes memory data
    ) external returns (uint256 assetsSupplied, uint256 sharesSupplied);
```

Supplies `assets` or `shares` on behalf of `onBehalf`, optionally calling back the caller's `onMorphoSupply` function with the given `data`.

- Either `assets` or `shares` should be zero. Most usecases should rely on `assets` as an input so the caller is guaranteed to have `assets` tokens pulled from their balance, but the possibility to mint a specific amount of shares is given for full compatibility and precision.
- Supplying a large amount can revert for overflow.
- Supplying an amount of shares may lead to supply more or fewer assets than expected due to slippage. Consider using the `assets` parameter to avoid this.

#### [Parameters:](#parameters-6)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to supply assets to. |
| `assets` | uint256 | The amount of assets to supply. |
| `shares` | uint256 | The amount of shares to mint. |
| `onBehalf` | address | The address that will own the increased supply position. |
| `data` | bytes | Arbitrary data to pass to the `onMorphoSupply` callback. Pass empty data if not needed. |

#### [Return Values:](#return-values)

| Name | Type | Description |
| --- | --- | --- |
| `assetsSupplied` | uint256 | The amount of assets supplied. |
| `sharesSupplied` | uint256 | The amount of shares minted. |

### [withdraw](#withdraw)

```
function withdraw(
        MarketParams memory marketParams,
        uint256 assets,
        uint256 shares,
        address onBehalf,
        address receiver
    ) external returns (uint256 assetsWithdrawn, uint256 sharesWithdrawn);
```

Withdraws `assets` or `shares` on behalf of `onBehalf` to `receiver`.

- Either `assets` or `shares` should be zero. To withdraw max, pass the `shares`'s balance of `onBehalf`.
- `msg.sender` must be authorized to manage `onBehalf`'s positions.
- Withdrawing an amount corresponding to more shares than supplied will revert for underflow.
- It is advised to use the `shares` input when withdrawing the full position to avoid reverts due to conversion roundings between `shares` and `assets`.

#### [Parameters:](#parameters-7)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to withdraw assets from. |
| `assets` | uint256 | The amount of assets to withdraw. |
| `shares` | uint256 | The amount of shares to burn. |
| `onBehalf` | address | The address of the owner of the supply position. |
| `receiver` | address | The address that will receive the withdrawn assets. |

#### [Return Values:](#return-values-1)

| Name | Type | Description |
| --- | --- | --- |
| `assetsWithdrawn` | uint256 | The amount of assets withdrawn. |
| `sharesWithdrawn` | uint256 | The amount of shares burned. |

### [borrow](#borrow)

```
function borrow(
        MarketParams memory marketParams,
        uint256 assets,
        uint256 shares,
        address onBehalf,
        address receiver
    ) external returns (uint256 assetsBorrowed, uint256 sharesBorrowed);
```

Borrows `assets` or `shares` on behalf of `onBehalf` to `receiver`.

- Either `assets` or `shares` should be zero. Most usecases should rely on `assets` as an input so the caller is guaranteed to borrow `assets` of tokens, but the possibility to mint a specific amount of shares is given for full compatibility and precision.
- `msg.sender` must be authorized to manage `onBehalf`'s positions.
- Borrowing a large amount can revert for overflow.
- Borrowing an amount of shares may lead to borrow fewer assets than expected due to slippage. Consider using the `assets` parameter to avoid this.

#### [Parameters:](#parameters-8)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to borrow assets from. |
| `assets` | uint256 | The amount of assets to borrow. |
| `shares` | uint256 | The amount of shares to mint. |
| `onBehalf` | address | The address that will own the increased borrow position. |
| `receiver` | address | The address that will receive the borrowed assets. |

#### [Return Values:](#return-values-2)

| Name | Type | Description |
| --- | --- | --- |
| `assetsBorrowed` | uint256 | The amount of assets borrowed. |
| `sharesBorrowed` | uint256 | The amount of shares minted. |

### [repay](#repay)

```
function repay(
        MarketParams memory marketParams,
        uint256 assets,
        uint256 shares,
        address onBehalf,
        bytes memory data
    ) external returns (uint256 assetsRepaid, uint256 sharesRepaid);
```

Repays `assets` or `shares` on behalf of `onBehalf`, optionally calling back the caller's `onMorphoRepay` function with the given `data`.

- Either `assets` or `shares` should be zero. To repay max, pass the `shares`'s balance of `onBehalf`.
- Repaying an amount corresponding to more shares than borrowed will revert for underflow.
- It is advised to use the `shares` input when repaying the full position to avoid reverts due to conversion roundings between shares and assets.
- An attacker can front-run a repay with a small repay making the transaction revert for underflow.

#### [Parameters:](#parameters-9)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to repay assets from. |
| `assets` | uint256 | The amount of assets to repay. |
| `shares` | uint256 | The amount of shares to burn. |
| `onBehalf` | address | The address of the owner of the debt position. |
| `data` | bytes | Arbitrary data (example `0x`) to pass to the `onMorphoRepay` callback. Pass empty data if not needed. |

#### [Return Values:](#return-values-3)

| Name | Type | Description |
| --- | --- | --- |
| `assetsRepaid` | uint256 | The amount of assets repaid. |
| `sharesRepaid` | uint256 | The amount of shares burned. |

### [supplyCollateral](#supplycollateral)

```
function supplyCollateral(MarketParams memory marketParams, uint256 assets, address onBehalf, bytes memory data)
        external;
```

Supplies `assets` of collateral on behalf of `onBehalf`, optionally calling back the caller's `onMorphoSupplyCollateral` function with the given `data`.

- Interest are not accrued since it's not required and it saves gas.
- Supplying a large amount can revert for overflow.

#### [Parameters:](#parameters-10)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to supply collateral to. |
| `assets` | uint256 | The amount of assets to supply. |
| `onBehalf` | address | The address that will own the increased collateral position. |
| `data` | bytes | Arbitrary data to pass to the `onMorphoSupplyCollateral` callback. Pass empty data if not needed. |

### [withdrawCollateral](#withdrawcollateral)

```
function withdrawCollateral(MarketParams memory marketParams, uint256 assets, address onBehalf, address receiver)
        external;
```

Withdraws `assets` of collateral on behalf of `onBehalf` to `receiver`.

- `msg.sender` must be authorized to manage `onBehalf`'s positions.
- Withdrawing an amount corresponding to more collateral than supplied will revert for underflow.

#### [Parameters:](#parameters-11)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to withdraw collateral from. |
| `assets` | uint256 | The amount of assets to withdraw. |
| `onBehalf` | address | The address that owns the collateral position. |
| `receiver` | address | The address that will receive the collateral assets. |

### [liquidate](#liquidate)

```
function liquidate(
        MarketParams memory marketParams,
        address borrower,
        uint256 seizedAssets,
        uint256 repaidShares,
        bytes memory data
    ) external returns (uint256, uint256);
```

Liquidates the given `repaidShares` of debt asset or seize the given `seizedAssets` of collateral on the
given market `marketParams` of the given `borrower`'s position, optionally calling back the caller's
`onMorphoLiquidate` function with the given `data`.

- Either `seizedAssets` or `repaidShares` should be zero.
- Seizing more than the collateral balance will underflow and revert without any error message.
- Repaying more than the borrow balance will underflow and revert without any error message.
- An attacker can front-run a liquidation with a small repay making the transaction revert for underflow.

#### [Parameters:](#parameters-12)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](#marketparams-struct) | The market of the position. |
| `borrower` | address | The owner of the position. |
| `seizedAssets` | uint256 | The amount of collateral to seize. |
| `repaidShares` | uint256 | The amount of shares to repay. |
| `data` | bytes | Arbitrary data to pass to the `onMorphoLiquidate` callback. Pass empty data if not needed. |

#### [Return Values:](#return-values-4)

| Name | Type | Description |
| --- | --- | --- |
| `assetsSeized` | uint256 | The amount of assets seized. |
| `assetsRepaid` | uint256 | The amount of assets repaid. |

### [flashLoan](#flashloan)

```
function flashLoan(address token, uint256 assets, bytes calldata data) external;
```

Executes a flash loan.

- Flash loans have access to the whole balance of the contract (the liquidity and deposited collateral of all markets combined, plus donations).
- Warning: Not ERC-3156 compliant but compatibility is easily reached:
a. `flashFee` is zero.
b. `maxFlashLoan` is the token's balance of this contract.
c. The receiver of `assets` is the caller.

Learn more about flash loans on Morpho Blue [here](https://docs.morpho.org/learn/concepts/flashloans/).

#### [Parameters:](#parameters-13)

| Name | Type | Description |
| --- | --- | --- |
| `token` | address | The token to flash loan. |
| `assets` | uint256 | The amount of assets to flash loan. |
| `data` | bytes | Arbitrary data to pass to the `onMorphoFlashLoan` callback. |

### [setAuthorization](#setauthorization)

```
function setAuthorization(address authorized, bool newIsAuthorized) external;
```

Sets the authorization for `authorized` to manage `msg.sender`'s positions.

#### [Parameters:](#parameters-14)

| Name | Type | Description |
| --- | --- | --- |
| `authorized` | address | The authorized address. |
| `newIsAuthorized` | bool | The new authorization status. |

### [setAuthorizationWithSig](#setauthorizationwithsig)

```
struct Authorization {
    address authorizer;
    address authorized;
    bool isAuthorized;
    uint256 nonce;
    uint256 deadline;
}

struct Signature {
    uint8 v;
    bytes32 r;
    bytes32 s;
}

function setAuthorizationWithSig(Authorization calldata authorization, Signature calldata signature) external;
```

Sets the authorization for `authorization.authorized` to manage `authorization.authorizer`'s positions.

- Warning: Reverts if the signature has already been submitted.
- The signature is malleable, but it has no impact on the security here.
- The nonce is passed as argument to be able to revert with a different error message.

setAuthorization vs. setAuthorizationWithSigWhile both functions achieve the same outcome (managing operator permissions), they serve different use cases:

- **`setAuthorization`**: Requires an onchain transaction directly from the `authorizer`'s address (or a contract they control). It's simpler for direct interactions but costs gas for the authorizer.
- **`setAuthorizationWithSig`**: Uses an EIP-712 signature created offchain by the `authorizer`. This signature can then be submitted onchain by *any* address (e.g., the `authorized` party, a relayer, or the Morpho Bundler). This enables gasless approvals for the authorizer and is essential for meta-transactions and efficient bundling flows, especially with EOAs.

#### [Authorization struct](#authorization-struct)

| Name | Type | Description |
| --- | --- | --- |
| `authorizer` | address | The address authorizing the authorization. |
| `authorized` | address | The address to authorize. |
| `isAuthorized` | bool | The new authorization status. |
| `nonce` | uint256 | The nonce of the authorizer. |
| `deadline` | uint256 | The deadline after which the signature is invalid. |

#### [Parameters:](#parameters-15)

| Name | Type | Description |
| --- | --- | --- |
| `authorization` | [Authorization](#authorization-struct) | The authorization to set. |
| `signature` | Signature | The signature to validate. |

### [accrueInterest](#accrueinterest)

```
function accrueInterest(MarketParams memory marketParams) external;
```

Accrues interest for the given market `marketParams`.

#### [Parameters:](#parameters-16)

| Name | Type | Description |
| --- | --- | --- |
| `marketParams` | [MarketParams](#marketparams-struct) | The market parameters. |

## [Views Functions](#views-functions)

### [DOMAIN_SEPARATOR](#domain_separator)

```
function DOMAIN_SEPARATOR() external view returns (bytes32);
```

The EIP-712 domain separator.

- Warning: Every EIP-712 signed message based on this domain separator can be reused on another chain sharing the same chain id because the domain separator would be the same.

#### [Return Values:](#return-values-5)

| Type | Description |
| --- | --- |
| bytes32 | The EIP-712 domain separator. |

### [owner](#owner)

```
function owner() external view returns (address);
```

The owner of the contract.

- It has the power to change the owner.
- It has the power to set fees on markets and set the fee recipient.
- It has the power to enable but not disable IRMs and LLTVs.

#### [Return Values:](#return-values-6)

| Type | Description |
| --- | --- |
| address | The owner of the contract. |

### [feeRecipient](#feerecipient)

```
function feeRecipient() external view returns (address);
```

The fee recipient of all markets.

- The recipient receives the fees of a given market through a supply position on that market.

#### [Return Values:](#return-values-7)

| Type | Description |
| --- | --- |
| address | The fee recipient address. |

### [isIrmEnabled](#isirmenabled)

```
function isIrmEnabled(address irm) external view returns (bool);
```

Whether the `irm` is enabled.

#### [Parameters:](#parameters-17)

| Name | Type | Description |
| --- | --- | --- |
| `irm` | address | The irm address. |

#### [Return Values:](#return-values-8)

| Type | Description |
| --- | --- |
| bool | Boolean equals to `true` if irm is enabled, `false` otherwise. |

### [isLltvEnabled](#islltvenabled)

```
function isLltvEnabled(uint256 lltv) external view returns (bool);
```

Whether the `lltv` is enabled.

#### [Parameters:](#parameters-18)

| Name | Type | Description |
| --- | --- | --- |
| `lltv` | address | The lltv address. |

#### [Return Values:](#return-values-9)

| Type | Description |
| --- | --- |
| bool | Boolean equals to `true` if lltv is enabled, `false` otherwise. |

### [isAuthorized](#isauthorized)

```
function isAuthorized(address authorizer, address authorized) external view returns (bool);
```

Whether `authorized` is authorized to modify `authorizer`'s position on all markets.

- Anyone is authorized to modify their own positions, regardless of this variable.

#### [Parameters:](#parameters-19)

| Name | Type | Description |
| --- | --- | --- |
| `authorizer` | address | The authorizer address. |
| `authorized` | address | The authorized address. |

#### [Return Values:](#return-values-10)

| Type | Description |
| --- | --- |
| bool | Boolean equals to `true` if `authorized` address is authorized to modify `authorizer`'s position, `false` otherwise. |

### [nonce](#nonce)

```
function nonce(address authorizer) external view returns (uint256);
```

The `authorizer`'s current nonce. Used to prevent replay attacks with EIP-712 signatures.

#### [Parameters:](#parameters-20)

| Name | Type | Description |
| --- | --- | --- |
| `authorizer` | address | The authorizer address. |

#### [Return Values:](#return-values-11)

| Type | Description |
| --- | --- |
| uint256 | The current nonce value. |

### [extSloads](#extsloads)

```
function extSloads(bytes32[] memory slots) external view returns (bytes32[] memory);
```

Returns the data stored on the different `slots`.

#### [Parameters:](#parameters-21)

| Name | Type | Description |
| --- | --- | --- |
| `slots` | bytes32[] | The array of slots to retrieve the data stored into. |

#### [Return Values:](#return-values-12)

| Type | Description |
| --- | --- |
| bytes32[] | The data stored. |

### [idToMarketParams](#idtomarketparams)

```
function idToMarketParams(Id id)
        external
        view
        returns (address loanToken, address collateralToken, address oracle, address irm, uint256 lltv);
```

The market params corresponding to `id`.

- This mapping is not used in Morpho. It is there to enable reducing the cost associated to calldata on layer 2s by creating a wrapper contract with functions that take `id` as input instead of `marketParams`.

#### [Parameters:](#parameters-22)

| Name | Type | Description |
| --- | --- | --- |
| `id` | Id | The market id |

#### [Return Values:](#return-values-13)

| Name | Type | Description |
| --- | --- | --- |
| `loanToken` | address | The loan token of the market. |
| `collateralToken` | address | The collateral token of the market. |
| `oracle` | address | The oracle of the market. |
| `irm` | address | The IRM of the market. |
| `lltv` | uint256 | The LLTV of the market. |

### [market](#market)

```
function market(Id id)
        external
        view
        returns (
            uint128 totalSupplyAssets,
            uint128 totalSupplyShares,
            uint128 totalBorrowAssets,
            uint128 totalBorrowShares,
            uint128 lastUpdate,
            uint128 fee
        );
```

The market state corresponding to `id`.

- Interest are not accrued, and assets values are not updated. Their values are the one at the last update.
- One can use the [MorphoBalancesLib](#morphobalanceslib) to accrue interests

#### [Parameters:](#parameters-23)

| Name | Type | Description |
| --- | --- | --- |
| `id` | Id | The market id |

#### [Return Values:](#return-values-14)

| Name | Type | Description |
| --- | --- | --- |
| `totalSupplyAssets` | uint128 | The total supply assets of the market. |
| `totalSupplyShares` | uint128 | The total supply shares of the market. |
| `totalBorrowAssets` | uint128 | The total borrow assets of the market. |
| `totalBorrowShares` | uint128 | The total borrow shares of the market. |
| `lastUpdate` | uint128 | The last update timestamp of the market. |
| `fee` | uint128 | The fee of the market. |

### [position](#position)

```
function position(Id id, address user)
        external
        view
        returns (uint256 supplyShares, uint128 borrowShares, uint128 collateral);
```

The state of the position of `user` on the market corresponding to `id`.

#### [Parameters:](#parameters-24)

| Name | Type | Description |
| --- | --- | --- |
| `id` | Id | The market id. |
| `user` | address | The user address. |

#### [Return Values:](#return-values-15)

| Name | Type | Description |
| --- | --- | --- |
| `supplyShares` | uint256 | The total supply shares of the user on a given market. |
| `borrowShares` | uint128 | The total borrow shares of the user on a given market. |
| `collateral` | uint128 | The total collateral assets of the user on a given market. |

## [MorphoBalancesLib](#morphobalanceslib)

The MorphoBalancesLib is a library that allows you to accrue interest and
update the assets values of a market. You can easily retrieve market amounts
and user balances with interests.

> The Github code is available [**here**](https://github.com/morpho-org/morpho-blue/blob/be2306afd655232d2cf16547c18be0077014bae0/src/libraries/periphery/MorphoBalancesLib.sol)

### [expectedMarketBalances](#expectedmarketbalances)

```
function expectedMarketBalances(IMorpho morpho, MarketParams memory marketParams)
        internal
        view
        returns (
            uint256 totalSupplyAssets,
            uint256 totalSupplyShares,
            uint256 totalBorrowAssets,
            uint256 totalBorrowShares
            );
```

Returns the expected market balances of a market after having accrued interests, defined in [Market](#market-struct).

#### [Parameters:](#parameters-25)

| Name | Type | Description |
| --- | --- | --- |
| `morpho` | IMorpho | The Morpho contract (injected when used as library). |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to get the expected balances from. |

#### [Return Values:](#return-values-16)

| Name | Type | Description |
| --- | --- | --- |
| `totalSupplyAssets` | uint256 | The total supply assets of the market (with interests accrued). |
| `totalSupplyShares` | uint256 | The total supply shares of the market. |
| `totalBorrowAssets` | uint256 | The total borrow assets of the market (with interests accrued). |
| `totalBorrowShares` | uint256 | The total borrow shares of the market. |

### [expectedTotalSupplyAssets](#expectedtotalsupplyassets)

```
function expectedTotalSupplyAssets(IMorpho morpho, MarketParams memory marketParams)
        internal
        view
        returns (uint256 totalSupplyAssets);
```

Returns the expected total supply assets of a market after having accrued interests.

#### [Parameters:](#parameters-26)

| Name | Type | Description |
| --- | --- | --- |
| `morpho` | IMorpho | The Morpho contract (injected when used as library). |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to get the expected total supply from. |

#### [Return Values:](#return-values-17)

| Name | Type | Description |
| --- | --- | --- |
| `totalSupplyAssets` | uint256 | The total supply assets of the market (with interests accrued). |

### [expectedTotalBorrowAssets](#expectedtotalborrowassets)

```
function expectedTotalBorrowAssets(IMorpho morpho, MarketParams memory marketParams)
        internal
        view
        returns (uint256 totalBorrowAssets);
```

Returns the expected total borrow assets of a market after having accrued interests.

#### [Parameters:](#parameters-27)

| Name | Type | Description |
| --- | --- | --- |
| `morpho` | IMorpho | The Morpho contract (injected when used as library). |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to get the expected total borrow from. |

#### [Return Values:](#return-values-18)

| Name | Type | Description |
| --- | --- | --- |
| `totalBorrowAssets` | uint256 | The total borrow assets of the market (with interests accrued). |

### [expectedTotalSupplyShares](#expectedtotalsupplyshares)

```
function expectedTotalSupplyShares(IMorpho morpho, MarketParams memory marketParams)
        internal
        view
        returns (uint256 totalSupplyShares);
```

Returns the expected total supply shares of a market after having accrued interests.

- It can grow only if fees > 0

#### [Parameters:](#parameters-28)

| Name | Type | Description |
| --- | --- | --- |
| `morpho` | IMorpho | The Morpho contract (injected when used as library). |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to get the expected total supply from. |

#### [Return Values:](#return-values-19)

| Name | Type | Description |
| --- | --- | --- |
| `totalSupplyShares` | uint256 | The total supply shares of the market (with interests accrued). |

### [expectedSupplyAssets](#expectedsupplyassets)

```
function expectedSupplyAssets(IMorpho morpho, MarketParams memory marketParams, address user)
        internal
        view
        returns (uint256)
```

Returns the expected supply assets of a user on a market after having accrued interests.

- Warning: Wrong for `feeRecipient` because their supply shares increase is not taken into account.
- Warning: Withdrawing using the expected supply assets can lead to a revert due to conversion roundings from assets to shares.

#### [Parameters:](#parameters-29)

| Name | Type | Description |
| --- | --- | --- |
| `morpho` | IMorpho | The Morpho contract (injected when used as library). |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to get the expected supply assets from. |
| `user` | address | The user to get the expected supply assets from. |

#### [Return Values:](#return-values-20)

| Name | Type | Description |
| --- | --- | --- |
| `supplyAssets` | uint256 | The supply assets of the user (with interests accrued). |

### [expectedBorrowAssets](#expectedborrowassets)

```
function expectedBorrowAssets(IMorpho morpho, MarketParams memory marketParams, address user)
        internal
        view
        returns (uint256)
```

Returns the expected borrow assets of a user on a market after having accrued interests.

- Warning: The expected balance is rounded up, so it may be greater than the market's expected total borrow
assets.

#### [Parameters:](#parameters-30)

| Name | Type | Description |
| --- | --- | --- |
| `morpho` | IMorpho | The Morpho contract (injected when used as library). |
| `marketParams` | [MarketParams](#marketparams-struct) | The market to get the expected borrow assets from. |
| `user` | address | The user to get the expected borrow assets from. |

#### [Return Values:](#return-values-21)

| Name | Type | Description |
| --- | --- | --- |
| `borrowBalance` | uint256 | The borrow assets of the user (with interests accrued). |

## [Errors Codes](#errors-codes)

The full list of custom errors are displayed directly in the ErrorsLib of the [Morpho contracts](https://github.com/morpho-org/morpho-blue/blob/main/src/libraries/ErrorsLib.sol). For example, see the [Morpho contract deployed on Ethereum mainnet](https://etherscan.io/address/0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb#code#F10#L1).

Below is the list of the different **Errors** that can be thrown, along with their explanations:

| Errors Message (returned data) | Error Natspec |
| --- | --- |
| "already set" | Thrown when the value is already set. |
| "healthy position" | Thrown when the position to liquidate is healthy. |
| "inconsistent input" | Thrown when not exactly one of the input amount is zero. |
| "insufficient collateral" | Thrown when the collateral is insufficient to `borrow` or `withdrawCollateral`. |
| "insufficient liquidity" | Thrown when the liquidity is insufficient to `withdraw` or `borrow`. |
| "invalid nonce" | Thrown when the nonce is invalid. |
| "invalid signature" | Thrown when the authorization signature is invalid. |
| "irm not enabled" | Thrown when the IRM is not enabled at market creation. |
| "lltv not enabled" | Thrown when the LLTV is not enabled at market creation. |
| "market already created" | Thrown when the market is already created. |
| "market not created" | Thrown when the market is not created. |
| "max fee exceeded" | Thrown when the fee to set exceeds the maximum fee. |
| "max lltv exceeded" | Thrown when the LLTV to enable exceeds the maximum LLTV. |
| "max uint128 exceeded" | Thrown when the maximum uint128 is exceeded. |
| "no code" | Thrown when a token to transfer doesn't have code. |
| "not owner" | Thrown when the caller is not the owner. |
| "signature expired" | Thrown when the authorization signature is expired. |
| "transfer from reverted" | Thrown when a token transferFrom reverted. |
| "transfer from returned false" | Thrown when a token transferFrom returned false. |
| "transfer returned false" | Thrown when a token transfer returned false. |
| "transfer reverted" | Thrown when a token transfer reverted. |
| "unauthorized" | Thrown when the caller is not authorized to conduct an action. |
| "zero address" | Thrown when a zero address is passed as input. |
| "zero assets" | Thrown when zero assets is passed as input. |

[Midnight

Previous Page

](https://docs.morpho.org/developers/contracts/midnight/)[Morpho Vaults V2

Next Page

](https://docs.morpho.org/developers/contracts/morpho-vaults-v2/)