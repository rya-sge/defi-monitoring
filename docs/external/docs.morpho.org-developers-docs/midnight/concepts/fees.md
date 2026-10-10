# Fees

> Source: https://docs.morpho.org/developers/midnight/concepts/fees

---

# Fees

Midnight can charge two protocol-level fees on each market. Fees apply at different moments, to different participants, and are capped independently.

- One fee is charged **per trade (settlement fee)**, the moment an offer is taken
- The other accrues **continuously over time (continuous fee)** on outstanding credit

## [Settlement fee](#settlement-fee)

The settlement fee is charged when an offer is taken. Mechanically it **inserts a spread between the buyer's and the seller's settlement price**. The maker's quoted price `P` is the anchor: the maker settles at exactly `P`, and the taker settles on the other side of the spread, a fee `f` away.

- Maker posted a buy offer (lending) at price P: the taker is selling units (borrowing) and settles at  `P − f` (receiving less)
- Maker posted a sell offer (borrowing) at price P: the taker is buying units (lending) and settles at `P + f` (pays more)

Because rate is implied from price (`rate = 1/P − 1`), this also means the taker's effective rate is slightly worse than the headline rate on the offer (a lender-taker earns a touch less, a borrower-taker pays a touch more)

The **maker is always made whole at their quoted price**. The fee is paid entirely by the **taker.** The protocol keeps the difference.

**Settlement fee scales with maturity**

A flat per-trade fee would be punishing on short-dated trades and trivial on long-dated ones. A 25 bps fee on a one-week loan is an enormous *annualized* cost, while the same 25 bps on a three-year loan is negligible. Participants reason in annualized rate, so the settlement fee is defined as a function of **time to maturity** (TTM) and calibrated so the *annualized* fee stays bounded regardless of TTM. The fee rate `f(ttm)` is a **piecewise-linear, continuous** function with breakpoints at **0, 1, 7, 30, 90, 180, and 360 days** (constant after maturity and beyond 360 days). Between two breakpoints it interpolates linearly.

## [Continuous fee](#continuous-fee)

The second fee is unrelated to trading. It accrues **every second on outstanding credit** and is borne by **lenders only:** the holders of credit, and it is capped at **1% annualized**.

It doesn't move tokens as it accrues. Instead it accumulates and **materializes when the lender reduces their credit** (selling units, or redeeming them) at which point the accrued amount is netted out of what they receive. On a position, this accrued-but-unrealized amount is exactly the `pending_fee` field (denominated in units).

This is why a lender's realizable claim is not simply their `credit`: it is `credit` *net of* `pending_fee`, adjusted for any bad-debt loss the market has absorbed since the position was last updated → `realizable = (credit − pending_fee) × (MAX − loss_factor) / (MAX − last_loss_factor)`, where `MAX = 2^128 − 1`. When `loss_factor` equals `last_loss_factor`, this is `credit − pending_fee`.

**Fee schedule is fixed at entry**

When a lender *increases* their credit, the continuous fee that position will pay is crystallized at the value in force at that moment. Later changes to the market's continuous-fee value do **not** retroactively affect existing lending positions.

Say a lender enters a 100 credit position. The contract computes:

```
pendingFeeIncrease = creditIncrease * continuousFee * TTM
```

The contract stores that on the lender position as a pending fee. That is what the `pending_fee` in the API response represents: it is the remaining non-accrued amount of that continuous fee for this position.

```
credit     = 100 USDC
pendingFee =  10 USDC   (computed upfront: credit increase × continuous fee × TTM)
face value =  90 USDC   (credit - pending fee)
```

As time passes toward maturity, the protocol gradually claims it, that's the accrual.

Now assume we are halfway to maturity and 5 USDC of that fee has accrued. The contract applies the **same** deduction to both fields:

```
credit     = 100 - 5 = 95
pendingFee =  10 - 5 =  5
face value = 95 - 5  = 90   ← unchanged
```

That 5 USDC is collected at the market level as protocol revenue.

Now when the user’s position is fetched, we get the following back:

`GET /v0/midnight/markets/{market-id}/users/{user-address}/position`

```
GET /v0/midnight/markets/{market-id}/users/{user-address}/position

// Response excerpt (other fields omitted; values are illustrative)
{
  "data": {
    "chain_id":           8453,
    "market_id":          "0xd92de5e7fbb...7614",
    "user_address":       "0xYourWalletAddress",
    "last_indexed_block": "47457420",
    "loan_token":         "0x8335...2913",     // USDC
    "maturity":           1798761600,
    "type":               "lend",              // "lend" | "borrow" | "collateral_only"
    "credit":             "95000000",          // 95 USDC: started at 100, protocol has siphoned 5 so far
    "debt":               "0",                 // borrower side: 0 for a lender
    "pending_fee":        "5000000",           // 5 USDC: started at 10, 5 already accrued into continuousFeeCredit
    "last_loss_factor":   "0",
    "loss_factor":        "0",
    "collaterals":        []                   // lenders don't post collateral - always empty
  }
}
```

The face value (what the lender is actually owed, i.e. 95 - 5 = 90 USDC) is unchanged since entry.

The lender's gross credit drops from 100 → 95 → 90 while the pending fee drops in lockstep, so from the lender's perspective nothing changes (they were always going to get 90).

It's the accounting mechanism for recognizing revenue over time without ever changing what the lender is owed.

---

[Tick Structure

Previous Page

](https://docs.morpho.org/developers/midnight/concepts/tick-structure/)[Lend at a fixed rate

Next Page

](https://docs.morpho.org/developers/midnight/tutorials/lend-at-a-fixed-rate/)