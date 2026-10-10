# The shock engine: what happens to a vault when a node fails

`riskdep shock` applies a failure to one or several nodes of the dependency graph and propagates it. The failure can be an oracle or feed that reads low, reads high or freezes, or a collateral whose market price falls. The command prints what each market, each vault and a depositor lose, and the path the loss took. How a failure crosses each edge is decided by **rules**, which are data in `riskdep/registry.json`; you can change them or add your own without touching the code. Plan: `plan/2026-10-10-propagation-engine.plan.md` (D89–D96).

This is step 1, a deterministic what-if. Step 2 will draw failures at random with probabilities and give a stay / reduce / exit verdict.

## Contents

- [Run it](#run-it)
- [Reading the output](#reading-the-output)
- [What a failure does to a market](#what-a-failure-does-to-a-market)
- [The squeeze](#the-squeeze)
- [How the engine walks the graph](#how-the-engine-walks-the-graph)
- [Rules](#rules)
- [Extending it](#extending-it)
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
python3 -m riskdep shock --vault $V --shock …                          # live graph (eRPC recommended, docs/erpc.md)
python3 -m riskdep shock --vault $V --user <depositor> --shock …       # adds that depositor's share
python3 -m riskdep shock --vault $V --replay --rules my-rules.json --shock …
```

A shock is `<node>:<mode>[:<size>]`:
- **node:** an address, a market id, or a fragment of a label that matches one node only (`"PRIME / WYLDS"`, `"Ojo PT"`).
- **mode:** `reads-low` and `reads-high` (an oracle or feed misreports by the size), `frozen` (it stops moving), or `price` (an asset's market price moves by the size; `price:30%` means a fall).

Several `--shock` options are applied together: a stuck feed *and* a falling collateral is one scenario. The JSON goes to `out/shock-<vault>.json` (or `out/shock-sweep-<vault>.json`).

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
  PT-reUSD-10DEC2026/USDC            held price-tracking    0.857   0.953      80.31M  157      3.06M          0         0    3.06M USDC    96.11M
  PT-reUSD-10DEC2026/USDT            sib  price-tracking    0.857   0.953       7.32M   54     249.0k          0         0   249.0k USDT     8.76M
  squeeze: 104.87M of PT-reUSD-10DEC2026 (at today's price) sold into a 12.41M pool: impact × 0.9527, floor 0.9527, price × 0.9527
  Vault RockawayX USDC Yield loses 235.8k (1.278% of its 18.44M)
```

The low reading liquidates 157 positions. Their PT is sold into a 12.4M Pendle pool, which pushes the PT down to its floor (see [the squeeze](#the-squeeze)). The oracle follows the PT, so it reads 0.9 × 0.953. Blue then writes off 3.06M that the collateral, really worth 0.953, would have covered. The vault's 7.7 % share of the market is 235.8k.

`--sweep` prints one line per node, ranked by the vaults' total loss, with the market whose lenders lose the most:

```
  node                                           kind     vault loss  % vault markets  worst market (its lenders lose)
  Oracle 0x217d…51f0                             Oracle        94.0k   0.510%       2  PT-reUSD-10DEC2026/USDC (1.22M)
  Ojo PT Feed Pendle Chainlink-compatible Oracle Oracle        94.0k   0.510%       2  PT-reUSD-10DEC2026/USDC (1.22M)
  USDC / USD                                     Oracle        70.4k   0.382%       6  strUSD/USDC (196.5k)
```

## What a failure does to a market

For each Blue market the engine has, from the graph, every borrower's collateral value V (at today's oracle price) and debt D, the LLTV, the free liquidity, and the oracle class. A failure reaches it as two factors:
- **fo**, applied to the oracle's reading;
- **fm**, applied to the collateral's market value.

An oracle that misreports by m and follows a collateral moving by f gives fo = m × f. A constant-price oracle, or a frozen one, does not follow: fo = m. In every case fm = f. With LIF = 1 / (0.3 LLTV + 0.7):

| Case | When | Lenders lose |
|---|---|---|
| liquidated | fo V × LLTV < D, and liquidating pays: fm / fo ≥ 1 / LIF | Blue's write-off, max(0, D − fo V / LIF) |
| liquidatable, not worth liquidating | fo V × LLTV < D, fm / fo < 1 / LIF | the insolvent part, max(0, D − fm V) |
| healthy by the oracle | fo V × LLTV ≥ D | the insolvent part, max(0, D − fm V): zero unless the market fell under a stuck or high oracle |
| drain | the collateral trades δ = 1 − fm / fo below its oracle and δ > d\* = 1 − LLTV / (1 + 0.5 %) | the free liquidity × max(0, 1 − (1 − δ) / LLTV) |

Everything is net of the same computation before the shock, so debt already underwater is not counted as the shock's. The four failure modes then read:

- **Reads low:** liquidates healthy borrowers. Past the LIF, Blue writes off debt the collateral really covered.
- **Reads high:** the collateral looks dearer than it is; past d\*, the market can be drained.
- **Frozen, or constant-price, under a falling market:** nobody is liquidated. The insolvent debt and the drain are the lenders'.
- **Price-tracking under a falling market:** liquidations, and Blue writes off what the collateral no longer covers.

## The squeeze

Liquidators sell what they seize into the collateral's pool, which lowers its price, and every market taking that collateral sees the new price, held or sibling. Price-tracking markets liquidate more, and the engine repeats until nothing moves.

Three assumptions bound it:
- **Depth.** Only a pool of known depth moves the price: a PT's Pendle pool liquidity, or an entry in `engine.depth_usd`. Elsewhere sales are reported and the price stays.
- **Impact.** A constant-product pool with reserves depth / 2 on each side: the price falls by the factor (R / (R + S))² for S sold, valued at today's price.
- **PT floor.** A PT redeems at par at maturity, so a buyer holding it there stops the fall. The floor is the price at which that buyer earns `stress_yield` (50 % APY, a judgement): ((1 + implied yield) / (1 + 50 %))^(days to maturity / 365). For PT-reUSD-10DEC2026, 60 days out at an 11.8 % implied yield, that is −4.7 %.

The floor usually binds: tens of millions of PT against a 12M pool would otherwise send the price to zero, which no holder to maturity would accept. Change it in the `asset` node rule.

## How the engine walks the graph

Edges point from a node to what it depends on (a market → its oracle → a feed). A failure travels the other way, from a dependency to everything that depends on it. The exception is a market's sales, which go along the edge to its collateral.

Each node carries **effects**:

| Effect | On | Combine |
|---|---|---|
| `misreport` (factor) | oracles, feeds | product |
| `frozen` | oracles, feeds | any |
| `price` (factor) | assets, Pendle pools | product, × the squeeze impact |
| `sale` (USD at today's price) | assets | sum |
| `loss` (loan units) | markets, vaults, depositors | sum |

A node stores each input under the node and the rule it came from. When a value changes, the input is replaced, not added again. A node's **model** recomputes its effects from its inputs: a Blue market evaluates its borrowers, an asset applies the squeeze, anything else combines. A changed effect is sent on through the matching edge rules. The run stops when no input changes by more than ε (10⁻⁶), or after `max_evaluations` (20,000); the report then warns that the numbers are not final.

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
| `effect` | the effect the rule carries: `misreport`, `frozen`, `price`, `sale`, `loss` |
| `rel` | the edge's relation (`reads`, `priced by`, `takes as collateral`, `wraps`, `supplies`, …); omitted: any |
| `direction` | `dependents` (default: against the edge) or `dependencies` (along it) |
| `when` | criteria, all required (below) |
| `apply` | the transmission: `stop`, `pass` (`exponent`: −1 for a quote feed; `as`: rename the effect), `collateral_price` (`follows`), `liquidation_sale`, `supplier_loss`, `depositor_loss` |
| `params` | the transmission's parameters |
| `basis` | why; kept with the rule |

A node rule has `id`, `when` (on `node.<field>`), `apply` (`blue_market` with `slippage` and `buy_cost`; `asset_price` with `depth`, `depth_usd`, `floor`, `stress_yield`; `combine`), `params` and `basis`.

**Criteria.**
- **Keys:** `rel`; `value` (the effect's value); `edge.<field>` (`role`, `amount`, …); `from.<field>` (the node carrying the effect); `to.<field>` (the node receiving it); `node.<field>` in node rules.
- **Node fields:** `id`, `kind`, `label`, or any detail of the node: `oracle_class`, `sibling`, `market_id`, `lltv_value`, `total_supply`, `liquidity_usd`, ….
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
     "apply": "pass", "params": {"exponent": 0.5},
     "basis": "a wrapper with a redemption queue passes on only part of a large fall"}
  ],
  "node_rules": [
    {"id": "deeper-pools", "when": {"node.kind": "Asset"}, "apply": "asset_price",
     "params": {"depth": "pendle_pool", "floor": "pendle_maturity", "stress_yield": 0.25},
     "basis": "holders to maturity step in at 25 % APY"}
  ]
}
```

## Extending it

- **A behaviour rules can express:** add a rule (in a `--rules` file for a study, in `registry.json` for everyone), with its basis.
- **A new kind of transmission or node:** write a function in `riskdep/engine.py`, register it in `TRANSMISSIONS` or `NODE_MODELS`, and give it a pure test in `tests/test_engine.py`. A transmission takes `(graph, edge, from, to, effect, value, params, states)` and returns a list of `(node, effect, value)`. A node model takes `(graph, node, state, params)` and returns `(effects, detail)`.
- **A new kind of node** (another lending protocol, say) needs only graph nodes and edges of its own, plus a node model. The engine does not change.

## Limits

- **No probabilities.** Step 1 says what happens if, not how likely it is; the verdict comes with step 2.
- **Instantaneous shocks.** The shock is applied at once and liquidations are full. Real liquidations are partial and spread over blocks, and oracles lag (a TWAP takes 15 minutes).
- **Depth is known only for PTs**, and the constant-product model with a floor is a rough stand-in for Pendle's curve and for buyers to maturity.
- **The drain counts free liquidity only.** Not the Public Allocator's inflow, and not the vault's allocators moving more in.
- **Depositors share pro rata,** with no run order (step 2 brings `exit_queue` in).
- **Two oracle classes.** An oracle that follows another asset than its collateral (stUSDS priced through USDS / USD) is treated as following its collateral or not, nothing in between (`GAP.md` K7).
