# Callbacks

> Source: https://docs.morpho.org/developers/midnight/concepts/callbacks

---

# Callbacks

A resting offer normally requires the maker to keep capital available in their wallet, where it cannot simultaneously earn Morpho Blue supply yield. A callback lets an offer source its funds from an external contract at settlement instead, so a maker can keep the capital earning on Morpho Blue until a taker arrives. This page explains what callbacks are, how the Morpho Blue lend callback works onchain, and how Morpho's router recognizes and repurposes that liquidity.

## [The idle-capital problem](#the-idle-capital-problem)

An offer is a standing commitment. A lender who publishes a buy offer on Midnight is promising to hand over loan tokens the moment a borrower takes it. Without a callback, the loan tokens remain in the maker's wallet until settlement, so the maker must maintain sufficient balance and allowance for the offer to fill. Those funds cannot simultaneously earn Morpho Blue supply yield while backing the offer.

Callbacks remove that dead time. Instead of relying on the maker's wallet balance at settlement, the offer names a contract that will produce the funds on demand, at the instant of settlement. Between publishing and being taken, the capital is free to do something productive. For the Blue-buy callback covered below, that "something productive" is supplying the same loan tokens to a Morpho Blue market, where the position can accrue interest at the market's variable supply rate until the offer is taken. That rate changes with market conditions and may fall to zero.

## [What a callback is](#what-a-callback-is)

Every onchain Midnight `Offer` includes two callback fields:

- `callback`: the address of the contract Midnight calls during settlement
- `callbackData`: opaque bytes passed through unchanged for that contract to interpret

A callback-free offer sets `callback` to the zero address and `callbackData` to `0x`. The REST API serializes `callbackData` as `callback_data`.

Callbacks play different roles depending on the offer side. For a buy offer—the lend flow covered on this page—a nonzero `callback` becomes the buyer callback. Midnight calls `onBuy` so the callback can supply the loan tokens instead of the maker's wallet. For a sell offer, the nonzero `callback` becomes the seller callback: Midnight transfers the loan tokens first, then calls `onSell`. A taker can separately provide a taker callback. Each path remains atomic: if a required callback step fails, the whole take reverts.

For a buy offer, a lend offer, the hook Midnight calls is `onBuy`. The callback receives how many loan tokens the fill needs (`buyerAssets`), sources exactly that amount, approves Midnight to pull it, and returns a success value. Nothing about this requires the maker's capital to have been idle; it only has to be reachable by the callback when the moment comes.

A callback is a general primitive, not a single feature. `blue_buy` (sourcing from a Morpho Blue supply position) is the first reference implementation, and the one the API and router understand today. Other funding sources can be built against the same hook.

## [The Blue-buy callback](#the-blue-buy-callback)

The reference implementation is `BlueBuyCallback.sol`. It is a small, ownable contract that holds a Morpho Blue supply position and sources a buy offer's funds by withdrawing from it. The maker creates it through the supported chain-specific `BlueBuyCallbackFactory`, funds its Blue position, and points their offers at it.

For Morpho's API and router to classify the callback as `blue_buy`, the factory must register the callback for that maker before the offer is posted. An independently deployed contract can implement the same callback hook and settle onchain, but it will not receive this router/API treatment; router validation can report `blue_callback`.

Its state is deliberately minimal:

```
address public immutable OWNER;     // the maker; the only buyer this callback will fund
address public immutable MIDNIGHT;  // the Midnight contract; the only address allowed to call onBuy
address public immutable BLUE;      // the Morpho Blue deployment funds are withdrawn from
uint256 public nonce;               // anti-replay for signed Blue authorizations
```

The settlement hook is the whole story (simplified from source):

```
function onBuy(
    bytes32,
    Market memory market,
    uint256 buyerAssets,   // exactly what this fill needs
    uint256,
    uint256,
    address buyer,
    bytes memory data      // ABI-encoded Blue MarketParams
) external returns (bytes32) {
    require(msg.sender == MIDNIGHT, NotMidnight());          // only Midnight may invoke the callback
    require(buyer == OWNER, NotOwnerBuyer());                // only funds transactions where the owner is the buyer

    MarketParams memory marketParams = abi.decode(data, (MarketParams));
    require(marketParams.loanToken == market.loanToken, InconsistentLoanToken());

    // Withdraw the funds from THIS contract's own Blue supply position…
    IMorpho(BLUE).withdraw(marketParams, buyerAssets, 0, address(this), address(this));
    // …and let Midnight pull them to settle the take.
    ERC20Lib.safeApprove(market.loanToken, MIDNIGHT, buyerAssets);

    return CALLBACK_SUCCESS;
}
```

A few details in that function are the design decisions that make the feature safe and legible:

- The Blue position is owned by the callback contract, not the maker's wallet. The `withdraw` call passes `address(this)` as both the position owner and the receiver, so the callback draws on its own supply. This keeps the earning position isolated behind one purpose-built contract with known behavior, which is exactly what lets a stranger's take route through it safely.
- Only Midnight can call it, and only for the owner's buys. `NotMidnight` and `NotOwnerBuyer` mean the callback can never be tricked into withdrawing for anyone else's fill.
- Loan tokens must match. `InconsistentLoanToken` rejects any `callback_data` whose Blue market pays out a different token than the offer settles in.
- It is atomic. The withdraw, the approval, and Midnight's pull all happen inside the taker's single transaction. If the Blue position cannot cover `buyerAssets`, the `withdraw` reverts and the take reverts with it. There is no partial or half-funded state.

Three housekeeping functions round it out: `setAuthorization` manages a Blue authorization directly, `setAuthorizationWithSig` performs a signed authorization update (with `nonce` guarding against replay), and `skim` sweeps any stray token balance back to the owner.

## [How the router recognizes the liquidity](#how-the-router-recognizes-the-liquidity)

A callback would be useless to integrators if the money it can produce were invisible until execution. The point of routing is to know, before anyone commits a transaction, how much of an offer is actually fillable.

Callback-backed offers are legible. The offer itself advertises its funding source: the `callback` address and the `callback_data` (the ABI-encoded Blue `MarketParams`) travel with the offer. The Morpho API surfaces this as a typed group — an offer group with `callback.type = "blue_buy"` exposes the callback contract and the Blue market it draws on:

```
GET /v0/midnight/users/{maker}/offer-groups?callback_type=blue_buy

// The callback metadata the router reads liquidity against:
{
  "callback": {
    "type": "blue_buy",
    "callback_address": "0x...callback",    // the BlueBuyCallback contract
    "market_id": "0x...blueMarket",         // the Blue position to inspect
    "market_params": { "loan_token": "0x...", "collateral_token": "0x...", "...": "..." }
  }
}
```

From there, the router does not take the offer's advertised size at face value. For each callback-backed offer, it computes the callback-funded capacity that can actually be sourced right now as the minimum of three onchain quantities:

- remaining group capacity: how much of the offer group is still unconsumed
- callback's Blue supply: `supplyAssets` of the callback contract's Blue position
- Blue market liquidity: unborrowed liquidity available to withdraw this block

This minimum caps that individual callback-backed offer. It is trustless: no promise from the maker, just three reads reconciled into one number. A quote can contain this offer together with other offers and intentional fallback excess, so the quote's `available_assets` is the aggregate capacity of the returned takeable-offer caps and can exceed the requested target. It is not this callback's three-way minimum. When a taker acts on the quote, their SDK or bundler constructs and submits a target-aware transaction from the returned takeable offers, limiting execution to the requested amount despite any fallback excess. Midnight then calls `onBuy`, and funds supplied to Blue—and potentially accruing interest at its variable market rate—are withdrawn and routed into settlement.

In the Midnight REST API v0, discover callback groups with `GET /v0/midnight/users/{user-address}/offer-groups`, inspect callback-backed offers with `GET /v0/midnight/books/{market-id}/{side}/takeable-offers` or `GET /v0/midnight/takeable-offers?maker={maker-address}`, and request an execution plan with `GET /v0/midnight/books/{market-id}/{side}/quote`.

## [How callback-backed settlement works](#how-callback-backed-settlement-works)

A Blue-backed offer follows this settlement flow:

1. the callback only ever withdraws from its own isolated Blue position
2. It will only act for the maker who owns it and only when the Midnight contract is the caller
3. The settlement token is checked against the Blue market
4. The entire funding step lives inside the taker's transaction so a shortfall reverts cleanly rather than settling half a fill

The taker experiences a Blue-backed offer through the same take flow as a wallet-funded offer: they submit a take and either get filled at the quoted terms or the transaction reverts.

[Mempool & Router

Previous Page

](https://docs.morpho.org/developers/midnight/concepts/mempool-router/)[Multi-Market Offers

Next Page

](https://docs.morpho.org/developers/midnight/concepts/multi-market-offers/)