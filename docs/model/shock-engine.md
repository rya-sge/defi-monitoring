# The shock engine: what happens to a vault when a node fails

`riskdep shock` applies a failure to one or several nodes of the dependency graph and propagates it. The failure can be an oracle or feed that reads low, reads high or freezes, or a collateral whose market price falls. The command prints what each market, each vault and a depositor lose, and the path the loss took. How a failure crosses each edge is decided by **rules**, which are data in `riskdep/registry.json`; you can change them or add your own without touching the code. Plan: `plan/2026-10-10-propagation-engine.plan.md` (D104–D111).

This is step 1, a deterministic what-if. Step 2 will draw failures at random with probabilities and give a stay / reduce / exit verdict.

## Contents

- [Run it](#run-it)
- [Reading the output](#reading-the-output)
- [What a failure does to a market](#what-a-failure-does-to-a-market)
- [The squeeze](#the-squeeze)
- [How the engine walks the graph](#how-the-engine-walks-the-graph)
- [Rules](#rules)
- [Extending it](#extending-it)
- [Validation: what is checked, what is not](#validation-what-is-checked-what-is-not)
- [Limits](#limits)

## Run it

```bash
V=0xE0181090c22579B6A217f1522cbf8c9f1F0C1965        # RockawayX USDC Yield; --replay uses its recorded graph

python3 -m riskdep shock --vault $V --replay --list                     # what can be shocked, and what it prices
python3 -m riskdep shock --vault $V --replay --shock "Ojo PT:reads-low:10%"
python3 -m riskdep shock --vault $V --replay \
    --shock "PRIME / WYLDS:frozen" --shock 0x19ebb35279a16207ec4ba82799cc64715065f7f6:price:-30%
python3 -m riskdep shock --vault $V --replay --sweep reads-high:20%    # every oracle and feed in turn, ranked
python3 -m riskdep shock --vault $V --replay --sweep price:-30%        # every asset in turn
python3 -m riskdep shock --vault $V --shock …                          # live graph (eRPC recommended, docs/setup/erpc.md)
python3 -m riskdep shock --vault $V --user <depositor> --shock …       # adds that depositor's share
python3 -m riskdep shock --vault $V --replay --rules my-rules.json --shock …
```

A shock is `<node>:<mode>[:<size>]`:
- **node:** an address, a market id, or a fragment of a label that matches one node only (`"PRIME / WYLDS"`, `"Ojo PT"`).
- **mode:** `reads-low` and `reads-high` (an oracle or feed misreports by the size), `frozen` (it stops moving), or `price` (an asset's market price moves by the size; `price:30%` means a fall).

Several `--shock` options are applied together: a stuck feed *and* a falling collateral is one scenario. The JSON goes to `out/shock-<vault>.json` (or `out/shock-sweep-<vault>.json`). A single run also writes `out/shock-<vault>.trace.json`, every step of the propagation tied to an edge of the graph, for a front end to draw (`docs/model/shock-trace.md`, with a committed example).

## Reading the output

The PRIME / WYLDS feed stuck while PRIME falls 30 %, on RockawayX USDC Yield (recorded 2026-10-10):

```
  market                                  oracle class     oracle  market  liquidated  pos  write-off  insolvent   drained  lenders lose    sold $
  PRIME/USDC                         held constant-price    1.000   0.700           0    0          0      93.3k    245.0k   138.9k USDC         0
  PRIME/PYUSD                        sib  constant-price    1.000   0.700           0    0          0     17.34M    20.60M  21.17M PYUSD         0
  PRIME/AUSD                         sib  constant-price    1.000   0.700           0    0          0     655.5k    541.4k   756.2k AUSD         0
  nvPRIME/USDC                       sib  constant-price    1.000   0.700           0    0          0        168    128.7k    24.1k USDC         0
  Vault RockawayX USDC Yield loses 122.8k (0.666% of its 18.44M)
  path to Vault RockawayX USDC Yield:
    Vault RockawayX USDC Yield ← loss 122801 from Blue PRIME/USDC [supplier]
      Blue PRIME/USDC ← collateral factor 0.7, follows False from PRIME [collateral-constant]
        PRIME ← price 0.7 from shock [price]
      Blue PRIME/USDC ← frozen True from Oracle 0x999e…119a [oracle-frozen]
        Oracle 0x999e…119a ← frozen True from PRIME / WYLDS Exchange Rate [frozen-base-feed]
          PRIME / WYLDS Exchange Rate ← frozen True from shock [frozen]
```

| Column | Meaning |
|---|---|
| `held` / `sib` | a market the vault holds, or a sibling market |
| `oracle`, `market` | the factors applied to today's oracle reading and to the collateral's market value |
| `liquidated`, `pos` | debt repaid by liquidators, and how many positions |
| `write-off` | debt Blue writes off when a liquidation takes all the collateral and debt is left |
| `insolvent` | debt the collateral no longer covers, with nobody liquidating: the borrower walks away, and the loss is the lenders' |
| `drained` | free liquidity borrowed against collateral bought cheap, once its discount to the oracle passes the drain threshold d\* |
| `lenders lose` | write-off + insolvent + the drained loss, net of the market's state before the shock |
| `sold $` | collateral liquidators sell into its pool, valued at today's price |

Each line of the path is one input of a node: where it came from, and in brackets the rule that carried it. Here the vault's 122.8k comes from its share of PRIME/USDC's 138.9k. Nobody was liquidated (constant-price oracle), so the loss is the insolvent debt plus a drain of the market's 245k of free liquidity. The $189M PRIME/PYUSD sibling on the same feed loses 21.17M, which the vault does not bear.

The Ojo PT feed reading 10 % low:

```
  PT-reUSD-10DEC2026/USDC            held price-tracking    0.892   0.952       9.79M  133      88.9k          0         0    88.9k USDC    85.08M
  PT-reUSD-10DEC2026/USDT            sib  price-tracking    0.892   0.952      953.6k   49       3.9k          0         0     3.9k USDT     8.29M
  reUSD/USDC                         sib  constant-price    1.000   0.961           0    0          0          0         0        0 USDC         0
  reUSD/USDT                         sib  constant-price    1.000   0.961           0    0          0          0         0        0 USDT         0
  sold into PT-reUSD-10DEC2026's market: 93.37M offered (at today's price): impact × 0.9915, price × 0.9915
  sold into reUSD's market: 93.37M offered (at today's price), 13% absorbed: impact × 0.9606, price × 0.9606
  Vault RockawayX USDC Yield loses 6.9k (0.037% of its 18.44M)
```

The low reading makes 133 positions liquidatable, and liquidators offer $93M of PT:
- **The Pendle pool absorbs it with little impact** (−0.85 %, from Pendle's own quotes). The oracle reads that pool, so it ends at 0.9 × 0.9915.
- **The reUSD that comes out does not all sell.** It must be sold for dollars, and the reUSD-to-USDC market absorbs only $12.4M, 13 % of the offer. reUSD falls 3.9 % there, and so does the PT's worth (`market` 0.952). The oracle does not see that fall.
- **Most liquidations cannot finish.** Only 13 % of the debt is liquidated; the remaining positions stay open and, at these prices, solvent.

Blue writes off 88.9k in the held market, and the vault's 7.7 % share is 6.9k.

A depeg of reUSD itself, the underlying of the PT (`--shock <reUSD>:price:-30%`):

```
  PT-reUSD-10DEC2026/USDC            held price-tracking    1.000   0.700           0    0          0     17.50M    13.83M   20.74M USDC         0
  reUSD/USDC                         sib  constant-price    1.000   0.700           0    0          0      2.02M     1.02M    2.26M USDC         0
  Vault RockawayX USDC Yield loses 1.60M (8.666% of its 18.44M)
```

The PT oracle is Pendle's PT_TO_ASSET type: it prices the PT against its underlying and counts the underlying at $1, so a reUSD depeg leaves it at 1.000. Nobody is liquidated. The loss is debt the PT no longer covers, plus a drain: anyone can buy reUSD cheap, mint PT and borrow against it at full price.

A failure in a **sibling's** oracle (`--shock "reUSD/USD exchange rate:reads-low:15%"`) liquidates 29 positions in the reUSD markets. Their liquidators sell $11.3M of reUSD, which lowers reUSD by 3.9 % and with it our PT's worth, while our oracle stays at 1.000: nothing is liquidated in our market, but its borrowers' margin is thinner. This is the path by which another market's failure, through another asset, reaches the vault.

`--sweep` prints one line per node, ranked by the vaults' total loss, with the market whose lenders lose the most:

```
  node                                           kind     vault loss  % vault markets  worst market (its lenders lose)
  Oracle 0x217d…51f0                             Oracle        95.1k   0.516%       2  PT-reUSD-10DEC2026/USDC (1.23M)
  Ojo PT Feed Pendle Chainlink-compatible Oracle Oracle        95.1k   0.516%       2  PT-reUSD-10DEC2026/USDC (1.23M)
  Dummy feed with 12 decimals                    Oracle        69.5k   0.377%       2  siUSD/USDC (236.0k)
```

## What a failure does to a market

For each Blue market the engine has, from the graph, every borrower's collateral value V (at today's oracle price) and debt D, the LLTV, the free liquidity, and the oracle class. A failure reaches it as two factors:
- **fo**, applied to the oracle's reading;
- **fm**, applied to the collateral's worth.

Three things can move the oracle:
- its own misreport m;
- a `reading`: a market one of its feeds **tracks** moved (a Pendle TWAP tracks its PT's pool; a "SYM / USD" feed tracks that pair);
- for a price-tracking oracle with no tracked feed, its collateral's own market price.

The collateral's worth moves with its own market price and with any move it inherits from an underlying (a wrapper's asset, a PT's yield token). No oracle sees an inherited move unless one of its feeds tracks that underlying. A frozen oracle or feed keeps its reading.

With LIF = 1 / (0.3 LLTV + 0.7), and e the share of the collateral that its market can absorb:

| Case | When | Lenders lose |
|---|---|---|
| liquidated | fo V × LLTV < D, and liquidating pays: fm / fo ≥ 1 / LIF | Blue's write-off, max(0, D − fo V / LIF), on the share e that can sell its collateral; the rest stays insolvent where the collateral no longer covers it |
| liquidatable, not worth liquidating | fo V × LLTV < D, fm / fo < 1 / LIF | the insolvent part, max(0, D − fm V) |
| healthy by the oracle | fo V × LLTV ≥ D | the insolvent part, max(0, D − fm V): zero unless the collateral's worth fell under a stuck, high or blind oracle |
| drain | the collateral trades δ = 1 − fm / fo below its oracle and δ > d\* = 1 − LLTV / (1 + 0.5 %) | the free liquidity × max(0, 1 − (1 − δ) / LLTV) |

Everything is net of the same computation before the shock, so debt already underwater is not counted as the shock's. The failure modes then read:

- **Reads low:** liquidates healthy borrowers. Past the LIF, Blue writes off debt the collateral really covered.
- **Reads high:** the collateral looks dearer than it is; past d\*, the market can be drained.
- **Frozen, constant-price, or blind to the move (an underlying's depeg under a PT oracle), under a falling worth:** nobody is liquidated. The insolvent debt and the drain are the lenders'.
- **The tracked market falls:** liquidations, Blue's write-offs, and as many of them as the collateral's markets can absorb.

## The squeeze

Liquidators offer what they seize for sale, and the price of what they sell falls. That reaches every market taking that collateral, held or sibling, and the engine repeats until nothing moves.

**Impact from real quotes.** When the graph is built, each PT gets two ladders of Pendle swap quotes, at 5 % to 5× its pool's liquidity:
- **PT → its underlying, without the aggregator:** the pool's own price, which a Pendle TWAP oracle reads.
- **PT → the loan token, through the aggregator:** the underlying received, sold for dollars.

Each ladder becomes a curve of the marginal price after each size, relative to the first. The PT carries the first curve, its underlying the second.

**Capacity.** A ladder stops where Pendle refuses the next size ("MarketProportionTooHigh. Market liquidity is likely insufficient") or where the marginal price falls under half of spot. What is offered beyond that is not sold:
- the price stays where the last sale left it;
- the share that went through is sent back to the markets, and their liquidations complete only in that proportion.

**Chain.** A PT sold into its pool comes out as the underlying, which goes on to the underlying's exit. Liquidations in markets taking the underlying directly (reUSD/USDC) sell into the same exit.

**PT floor.** A PT never falls below the price at which a buyer holding it to maturity earns `stress_yield` (50 % APY, a judgement): ((1 + implied yield) / (1 + 50 %))^(days to maturity / 365). With real quotes it rarely binds.

**Ratchet.** A sale offered stays offered, so the loop settles even when falling prices make later liquidations unprofitable.

On 2026-10-10 the quotes gave, for RockawayX USDC Yield:

| Market | Capacity | Marginal price at the last size |
|---|---|---|
| PT-reUSD-10DEC2026 into its pool | none up to $62M | −0.85 % |
| reUSD sold for USDC | $12.35M | −3.9 % |
| PT-strUSD-26NOV2026 into its pool | $3.44M | −4.1 % |
| strUSD sold for USDC | $1.39M | −12 % |
| PT-trUSD-26NOV2026 and trUSD | about $0.85M | −2.6 % |

`impact: constant_product` in the `asset` node rule brings back the first model, a constant-product pool on the Pendle liquidity, for comparison only. Against the quotes it was about 100 times too steep: −88 % for $12M, where Pendle quoted −0.59 %.

## How the engine walks the graph

Edges point from a node to what it depends on (a market → its oracle → a feed). A failure travels the other way, from a dependency to everything that depends on it. The exceptions are sales, which go along the edges: a market → its collateral → a PT's pool → its underlying.

Each node carries **effects**:

| Effect | On | Combine |
|---|---|---|
| `misreport` (factor) | oracles, feeds | product |
| `reading` (factor): the market a feed tracks moved | oracles, feeds | product |
| `frozen` | oracles, feeds | any |
| `price` (factor): the asset's own market | assets, Pendle pools | product, × the sale impact |
| `value` (factor): a move inherited from an underlying | assets, Pendle pools | product |
| `sale` (USD at today's price) | assets | sum |
| `onward` (USD): underlying received from a PT sale | Pendle pools | sum |
| `exit` (share absorbed) | assets, then markets | smallest |
| `loss` (loan units) | markets, vaults, depositors | sum |

A node stores each input under the node and the rule it came from. When a value changes, the input is replaced, not added again. A node's **model** recomputes its effects from its inputs:
- a Blue market evaluates its borrowers;
- an asset applies the impact of what is offered into its market;
- an oracle or feed drops its readings when frozen;
- anything else combines.

A changed effect is sent on through the matching edge rules. The run stops when no input changes by more than ε (10⁻⁶), or after `max_evaluations` (20,000); the report then warns that the numbers are not final.

## Rules

`registry.json` → `engine.edge_rules` and `engine.node_rules`, tried in order; the first match decides, and no match stops the effect there. `--rules my-rules.json` puts the file's lists first, so its rules win.

An edge rule:

```json
{"id": "collateral-tracking", "effect": "price", "rel": "takes as collateral",
 "when": {"to.oracle_class": "price-tracking"},
 "apply": "collateral_price", "params": {"follows": true},
 "basis": "a price-tracking oracle follows its collateral's market: a fall liquidates borrowers"}
```

| Field | Meaning |
|---|---|
| `id` | shown in the path, between brackets |
| `effect` | the effect the rule carries: `misreport`, `reading`, `frozen`, `price`, `value`, `sale`, `onward`, `exit`, `loss` |
| `rel` | the edge's relation (`reads`, `tracks`, `priced by`, `takes as collateral`, `wraps`, `yield source`, `supplies`, …); omitted: any |
| `direction` | `dependents` (default: against the edge) or `dependencies` (along it) |
| `when` | criteria, all required (below) |
| `apply` | the transmission: `stop`, `pass` (`exponent`: −1 for a quote feed; `as`: rename the effect), `collateral_price` (`follows`), `liquidation_sale`, `supplier_loss`, `depositor_loss` |
| `params` | the transmission's parameters |
| `basis` | why; kept with the rule |

A node rule has `id`, `when` (on `node.<field>`), `apply` (`blue_market` with `slippage` and `buy_cost`; `asset_price` with `impact` (`quotes` or `constant_product`), `depth`, `depth_usd`, `floor`, `stress_yield`; `oracle_input`; `combine`), `params` and `basis`.

**Criteria.**
- **Keys:** `rel`; `value` (the effect's value); `edge.<field>` (`role`, `amount`, …); `from.<field>` (the node carrying the effect); `to.<field>` (the node receiving it); `node.<field>` in node rules.
- **Node fields:** `id`, `kind`, `label`, or any detail of the node: `oracle_class`, `oracle_tracks_bound`, `sibling`, `market_id`, `lltv_value`, `total_supply`, `capacity_usd`, `liquidity_usd`, ….
- **Operators,** by suffix: `__in`, `__not_in`, `__ne`, `__gt`, `__gte`, `__lt`, `__lte`, `__contains` (case-insensitive), `__exists`. No suffix means equality.

**Examples** for `my-rules.json`:

```json
{
  "edge_rules": [
    {"id": "unclassified-follows", "effect": "price", "rel": "takes as collateral",
     "when": {"to.oracle_class": "not classified"},
     "apply": "collateral_price", "params": {"follows": true},
     "basis": "for a borrower, assume an oracle we cannot classify follows the market"},

    {"id": "ignore-small-siblings", "effect": "sale", "rel": "takes as collateral", "direction": "dependencies",
     "when": {"from.sibling": true, "from.total_supply__lt": 5000000},
     "apply": "stop",
     "basis": "sibling markets under $5M do not sell into the pool in this scenario"},

    {"id": "half-a-pass", "effect": "price", "rel": "wraps", "when": {"value__lt": 0.9},
     "apply": "pass", "params": {"as": "value", "exponent": 0.5},
     "basis": "a wrapper with a redemption queue passes on only part of a large fall"}
  ],
  "node_rules": [
    {"id": "deeper-pools", "when": {"node.kind": "Asset"}, "apply": "asset_price",
     "params": {"impact": "quotes", "floor": "pendle_maturity", "stress_yield": 0.25},
     "basis": "holders to maturity step in at 25 % APY"}
  ]
}
```

## Extending it

- **A behaviour rules can express:** add a rule (in a `--rules` file for a study, in `registry.json` for everyone), with its basis.
- **A new kind of transmission or node:** write a function in `riskdep/engine.py`, register it in `TRANSMISSIONS` or `NODE_MODELS`, and give it a pure test in `tests/test_engine.py`. A transmission takes `(graph, edge, from, to, effect, value, params, states)` and returns a list of `(node, effect, value)`. A node model takes `(graph, node, state, params)` and returns `(effects, detail)`.
- **A new kind of node** (another lending protocol, say) needs only graph nodes and edges of its own, plus a node model. The engine does not change.

## Used by `analyze --vault` and `--book`

A vault or book incident (`analyze --vault … --shock token=T:f`) runs this engine on the vault's recorded graph (plan `2026-10-11-one-number`, D139–D141). The issuer markdown it describes is, in the engine's terms, `T:price:-f` plus `reads-low:f` on every constant-price input of the oracles of markets taking T: the issuer cuts the rate its own feed publishes. That is not `T:price:-f` alone, which is a market fall the rate feed does not follow. On RockawayX USDC Yield, PRIME −30 % costs the vault 131,162 USDC either way once mapped like this; `T:price:-30%` alone gives 122.8k. The engine's figures replace the incident module's on the markets it moves, and its sibling markets are listed as contagion.

## Validation: what is checked, what is not

| Part | Checked against | Status |
|---|---|---|
| Blue's accounting: liquidation, write-off, LIF, insolvent debt, drain threshold | Morpho Blue's `liquidate`, `drain.py`; hand-worked tests | faithful |
| Positions, LLTVs, free liquidity | read on-chain at the graph's block | exact at that block |
| Sale impact and capacity | Pendle swap quotes at nine sizes per PT, recorded with the graph | real, but a snapshot of one moment |
| Which price an oracle follows | Pendle oracles read on-chain (`baseOracleType` 1 = PT_TO_ASSET for PT-reUSD), Chainlink-style feed names | the tracked binding covers Pendle TWAPs and "SYM / USD" feeds; other price-tracking oracles fall back to their class |
| A full episode | a real event | **not yet** (below) |

**Future step: a backtest.** On 2026-08-25, according to the source cited in `docs/analysis/GAP.md` K8, trading in YT-reUSD pushed PT-reUSD's implied yield from about 11 % to over 20 % in nine minutes, a min(TWAP, linear) oracle fell 0.5 to 2.8 %, Morpho liquidated 33 PT-reUSD positions, borrowers paid about $946k of liquidation bonus, and no bad debt was left. Replaying it would be the first test of the engine against reality:
1. Rebuild the graph at the block before the event: positions, oracle and pool states.
2. Apply the oracle's measured fall as a shock.
3. Compare the predicted positions liquidated, debt repaid and bonus with the `Liquidate` events of the following blocks.

It needs an archive RPC, because the free node serves state only about 100 blocks back and `keys.ini [rpc]` is empty. It also needs Pendle quotes from that time, which the API does not serve, so the pool curve would come from the pool's reserves at that block. Listed in `docs/analysis/NEXT_STEP.md`.

## Limits

- **No probabilities.** Step 1 says what happens if, not how likely it is; the verdict comes with step 2.
- **Instantaneous shocks.** Liquidations are full and happen at once, and oracles do not lag (a Pendle TWAP takes 15 minutes, and the Ojo feed takes the lower of the TWAP and a linear discount).
- **Outcome at the final prices.** The ratchet keeps the sales liquidators offered, but each market is evaluated at the prices the loop ends on. A liquidation that went through early, before an exit filled up, is counted only if it still pays at the end.
- **Beyond capacity the price stays.** Real markets would keep falling; the engine stops the price at the last quoted size and turns the unsold part into liquidations that do not complete.
- **Exit curves are bounded by the PT ladder.** An underlying's exit is measured with the underlying a PT sale yields, so it is known only up to the PT pool's own capacity (trUSD: about $0.85M).
- **The quotes are a snapshot.** They come from the moment the graph was built, and pool depth changes daily.
- **The drain counts free liquidity only.** Not the Public Allocator's inflow, and not the vault's allocators moving more in.
- **Depositors share pro rata,** with no run order (step 2 brings `exit_queue` in).
- **Oracle binding by structure and name.** A feed tracks a market when it is a Pendle TWAP or is named "SYM / USD" after an asset of the graph. Other price-tracking oracles fall back to following their collateral, and a meta-oracle that switches source (`MetaOracleDeviationTimelock`) is not modelled.
