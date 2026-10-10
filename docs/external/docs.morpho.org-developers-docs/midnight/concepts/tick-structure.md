# Tick Structure

> Source: https://docs.morpho.org/developers/midnight/concepts/tick-structure

---

# Tick Structure

## [Discrete price grid](#discrete-price-grid)

Midnight enforces a **discrete price grid** for offers. Offers can only be placed at prices corresponding to valid ticks. This prevents economically meaningless undercutting (offering at a price 1 wei better) and creates natural price levels around which liquidity concentrates.

The market state endpoint gives you `tick_granularity` , the practical constraint a maker needs before constructing an offer:

`GET /v0/midnight/markets/{market-id}/state`

```
// Check what tick values are valid for this market
GET /v0/midnight/markets/{marketId}/state

// In the response:
"tick_granularity": 1
```

Valid ticks must be multiples of this value.

- `tick_granularity`: 1 means every integer tick is valid
- `tick_granularity`: 2 would mean only even ticks (42, 40, 38...)

## [Constant relative change](#constant-relative-change)

The tick grid is designed so that consecutive ticks correspond to a **constant relative change in implied return**, not a constant absolute price step. This matters because the end goal of the activity is a return, and a fixed price increment implies different rate increments depending on how far prices are from par.

```
// The unquantized price at tick n, where δ is the target relative increment in implied return
P(n) = 1 / (1 + (1 + δ)(N/2 − n))

// Consecutive ticks satisfy:
return(n−1) = (1 + δ) × return(n)
```

This means the relative change in implied rate is constant across the grid (each step is the same percentage bigger than the last, not the same absolute amount). `δ` is fixed at the protocol layer (`δ` = 0.02, i.e. 2%). All markets share the same tick spacing and `δ` is not configurable per market.

In order to see the actual tick-to-price mapping where liquidity exists, use the following query:

`GET /v0/midnight/books/{market-id}/{side}`

```
GET /v0/midnight/books/{marketId}/asks?depth=4

// Each price level shows the tick and its corresponding price:
{
  "data": [
    { "tick": 42, "price": "952380952380952320", "units": "10000000000", "count": 3 },
    { "tick": 43, "price": "951474785918173312", "units": "18500000000", "count": 5 },
    { "tick": 44, "price": "950552270869375104", "units": "7200000000",  "count": 2 },
    { "tick": 45, "price": "949613146596339456", "units": "4100000000",  "count": 1 }
  ]
}

// tick 42: price ≈ 0.9524 → rate = 5.000%
// tick 43: price ≈ 0.9515 → rate = 5.100%  (5.100 / 5.000 = 1.02 exactly)
// tick 44: price ≈ 0.9506 → rate = 5.202%  (5.202 / 5.100 = 1.02 exactly)
// tick 45: price ≈ 0.9496 → rate = 5.306%  (5.306 / 5.202 = 1.02 exactly)

// Every consecutive pair: rate(n-1) / rate(n) = 1.02 = 1 + δ
```

Near par (P ≈ 1), where rate is close to zero, the rate-based spacing becomes impractically fine, so prices are quantized to a granularity of `ε = 1×10⁻⁶`. This lets the same immutable grid handle both far-from-par and near-par quoting.

The protocol is designed so that tick spacing could be refined per market in the future (only made finer, never coarser). A market would start with wide ticks (δ=2%) and graduate to tighter quoting (δ=1% or δ=0.5%) as liquidity deepens.

The definition of ticks ensures that enabling finer spacing would never invalidate existing offers. This capability is not yet active: all markets currently share a single fixed grid at δ=0.02.

[Multi-Market Offers

Previous Page

](https://docs.morpho.org/developers/midnight/concepts/multi-market-offers/)[Fees

Next Page

](https://docs.morpho.org/developers/midnight/concepts/fees/)