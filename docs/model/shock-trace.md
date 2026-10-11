# Shock trace: the propagation as data

`riskdep shock` writes, next to its report, a trace of how the shock travelled through the dependency graph: `out/shock-<target>.trace.json`. It is meant for a front end that draws the graph and shows the propagation on it. The file is self-contained: it carries the graph it refers to.

```bash
python3 -m riskdep shock --vault 0xE0181090c22579B6A217f1522cbf8c9f1F0C1965 --replay --shock "Ojo PT:reads-low:10%"
# → out/shock-0xe0181090c22579b6a217f1522cbf8c9f1f0c1965.trace.json
```

`docs/model/shock-trace-example.json` is that run, committed (RockawayX USDC Yield, the Ojo PT feed reading 10 % low: 65 nodes, 93 edges, 39 steps over 14 waves). Work from it without running anything. How the engine decides each step is in `docs/model/shock-engine.md`; this page covers only the file.

## Using it

1. **Draw `graph`.** `nodes` and `edges` are those of `graph.json`, without the private `_` fields. Each edge gets an id `e<i>`, its position in the list, which is also how `graph.html` numbers its Cytoscape edges. An edge points from a node to what it depends on (a market → its oracle).
2. **Colour by `nodes`.** It holds the final state of every node the shock reached, keyed by node id: a `status` for the colour, a `headline` for a label or tooltip. A node absent from it was not reached.
3. **Animate `steps`, wave by wave.** Each step moves one effect over one edge (`edge`) from `source` to `target`. `waves[i].steps` lists the steps of wave i, and `waves[i].evaluated` the nodes recomputed in it. For a node's state as of a given wave, take its last entry in `evaluations_log` up to that wave.
4. **Explain a loss.** `paths[node]` lists the steps behind that node's final loss, from the shocked node onward. Highlight their edges.

**Waves are not time.** The engine iterates to a fixed point: each wave recomputes the nodes the previous one changed, until nothing moves. An early wave can overshoot. In the example, the vault's loss reads 27.1k, then 51.8k, then 7.2k, and settles at 6.9k: the first waves still assume every liquidation can sell its collateral, and later waves find that the reUSD exit absorbs only 13 %. Only the final state (`nodes`) is the answer. Show the waves as "how the effect spreads", not as a timeline of the event.

## Top level

| Key | What it holds |
|---|---|
| `format` | `riskdep.shock-trace/1`; the number changes when a field changes meaning or goes away |
| `block`, `as_of` | the block the graph was read at, and the time the run counts from (the recording's time on a replay) |
| `note` | the waves-are-not-time caveat, in one sentence |
| `shocks` | each shock: `node`, `mode` (`reads-low`, `reads-high`, `frozen`, `price`), `size` (a fraction; signed for `price`), `label` |
| `converged` | `false` if the evaluation budget ran out before the loop settled: the numbers are not final, say so |
| `evaluations` | how many node evaluations the run took |
| `graph` | `nodes` (`id`, `kind`, `label`, `details`) and `edges` (`id`, `source`, `target`, `rel`, `amount`, `unit`, `details`) |
| `rules` | each rule a step used: `apply` (the transmission), `effect`, `rel`, `basis` (why, in one sentence: good tooltip text) |
| `steps` | every effect carried over an edge, in the order the engine sent them |
| `evaluations_log` | every node evaluation, in order, with the node's state right after it |
| `waves` | per wave: `wave`, `evaluated` (node ids), `steps` (step `seq`s) |
| `nodes` | the final state of every reached node |
| `paths` | for each node with a loss, the `seq`s of the steps behind it |

## A step

| Field | Meaning |
|---|---|
| `seq` | 1, 2, 3…, the order sent; `steps[seq - 1]` is the step |
| `wave` | the wave of the evaluation that sent it (0: the shocked node) |
| `edge` | the edge id it travels over |
| `source`, `target` | node ids: where the effect comes from and where it lands |
| `direction` | `dependents`: against the edge's arrow, from a dependency to what depends on it (a feed → its oracle); `dependencies`: along it (a market's liquidation sales → its collateral) |
| `effect` | what is carried, see below |
| `value` | the raw value the target receives |
| `change` | the move, signed, in `unit`: a factor's change (−0.10 for ×0.90), an amount, an unabsorbed share |
| `unit` | `factor`, `USD`, `share`, or the loan token for a loss (`USDC`…) |
| `display` | the step in words, e.g. `misreport ×0.9000 (-10.00%)`, `80.60M USD offered for sale` |
| `rule` | the id of the rule that sent it, a key of `rules` |
| `replaces` | the `seq` of the earlier step this one revises (same source, target, effect and rule), or `null`; the earlier value no longer counts |

| Effect | Value | What it means |
|---|---|---|
| `misreport` | factor | the oracle or feed reads that × what it should |
| `reading` | factor | the market an oracle input tracks moved |
| `frozen` | `true` | the oracle or feed no longer moves |
| `price` | factor | an asset's own market price |
| `value` | factor | an asset's worth inherited from an underlying, which no oracle sees unless a feed tracks that underlying |
| `collateral` | `{factor, kind, follows}` | an asset's move reaching a market that takes it: `kind` is `price` or `value`; `follows` says whether the market's oracle follows it |
| `sale` | USD | collateral offered for sale into an asset's market by liquidations, valued at today's price |
| `onward` | USD | the underlying a PT sale yields, sold on for dollars |
| `exit` | share | how much of the offered sale that market can absorb (1 = all) |
| `loss` | loan token | what a market's lenders, a vault or a depositor lose |

## A node's final state (`nodes[id]`)

| Field | Meaning |
|---|---|
| `status` | see below |
| `headline` | one line, e.g. `133 positions liquidatable, only 13% of their collateral sells: 9.79M USDC repaid, lenders lose 88.9k USDC` |
| `model` | how the engine computed it: `blue_market`, `asset_price`, `oracle_input`, `combine` |
| `effects` | the effects it passes on that differ from neutral |
| `loss_unit` | the token its loss is counted in, when it has one |
| `detail` | the model's numbers. For a Blue market: `oracle_factor`, `market_factor`, `positions_liquidated`, `liquidated_debt`, `bad_debt`, `insolvent`, `drained`, `lender_loss`, `executed`, `collateral_sold_usd`… (field by field in `docs/model/shock-engine.md`). For an asset with sales: `sold_usd`, `absorbed_usd`, `impact`, `floor` |
| `inputs` | the `seq`s of the steps whose values it holds at the end; following each step's `source` back gives the whole path |
| `first_wave` | the wave it was first recomputed in |

| `status` | When |
|---|---|
| `shocked` | a shock was applied to it |
| `loss` | it ends with a loss |
| `liquidations` | a Blue market where positions are liquidated with no loss to its lenders |
| `moved` | a price, reading or value changed, or a market's oracle or collateral moved, with no liquidation |
| `reached` | an effect arrived, but nothing changed: a rule stopped it, or it cancelled out |

An entry of `evaluations_log` has `seq`, `wave`, `node`, `model`, `status`, `headline`, `effects` and `detail` (without the market's `before` state). These are the same fields as the final state, taken right after that evaluation.

## Keeping the example current

A test (`tests/test_engine.py`, `test_the_committed_trace_example_is_current`) checks that `docs/model/shock-trace-example.json` equals what the command above writes. After a change to the engine, the rules or the RockawayX recording, regenerate it:

```bash
python3 -m riskdep shock --vault 0xE0181090c22579B6A217f1522cbf8c9f1F0C1965 --replay --shock "Ojo PT:reads-low:10%" \
  && cp out/shock-0xe0181090c22579b6a217f1522cbf8c9f1f0c1965.trace.json docs/model/shock-trace-example.json
```
