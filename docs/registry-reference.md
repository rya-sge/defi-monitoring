# `registry.json` reference

`riskdep/registry.json` holds every fact, assumption and threshold the tool uses that is not read from a live source. Each probability and severity carries a `basis` field saying where it comes from, and the `analyze` report prints those bases. This page explains each key: its unit, which code reads it, and what changing it does.

Rules for editing:

- **Keep the `basis` honest.** A changed number gets a changed basis: a source, a date, or "judgement" and why.
- **Run the tests after any change:** `python3 -m pytest -q tests`. They run offline; a change that breaks a threshold test shows up there.
- **Addresses are lowercase** Ethereum mainnet addresses.
- **Probabilities are per year** and fractions between 0 and 1; severities are Beta distributions `{"a": …, "b": …}` whose mean is a / (a + b).

## Contents

- [`chain`](#chain)
- [`issuers`](#issuers)
- [`stables`](#stables)
- [`protocols`](#protocols)
- [`oracle`](#oracle)
- [`frequency`](#frequency)
- [`unknown_issuer`](#unknown_issuer)
- [Top-level parameters of `analyze`](#top-level-parameters-of-analyze)
- [`watch`](#watch)
- [How to add a yield issuer](#how-to-add-a-yield-issuer)

## `chain`

The settlement chain as a layer of the `analyze` model. One entry, `ethereum`.

| Key | Unit | Meaning |
|---|---|---|
| `label` | text | the name shown in the report |
| `p_year` | probability per year | chance of an incident (today 1 %) |
| `severity` | Beta | loss of value if it happens (mean 0.5 %) |
| `basis` | text | justification |

Read by `discover.py` (graph node) and `priors.py` (the `chain` event).

## `issuers`

One entry per yield-bearing token that can sit behind a Pendle PT, keyed by the token's address. Today: sUSDe, USDe, wstETH, sUSDS.

| Key | Unit | Meaning |
|---|---|---|
| `symbol`, `issuer` | text | shown in the report and the graph |
| `llama_slug` | DefiLlama slug | finds the protocol in DefiLlama's list, for its size, category and listing date |
| `category` | DefiLlama category | used when the slug is not found |
| `kind` | text | descriptive only |
| `dependencies` | list of text | off-chain dependencies, drawn as External nodes |
| `depeg.p_year` | probability per year | chance of a depeg |
| `depeg.severity` | Beta | size of the depeg |
| `depeg.recovery` | fraction | share of the depeg recovered by the horizon; the rest is a permanent loss |
| `depeg.basis` | text | justification |
| `hack.severity`, `hack.basis` | Beta, text | loss of backing if the issuer is exploited; the exploit's probability is computed from the hack record (see `frequency`) |

Read by `discover.py`, `priors.py` and `graph.py`. A token not listed here falls back to `unknown_issuer`, and the report says so.

## `stables`

The loan tokens' issuers, keyed by address (USDC, USDT): `symbol`, `issuer`, `basis`. Descriptive only: for a borrower, a depeg of the loan token lowers the debt, so the model has no loss channel for it. Read by `discover.py` and `graph.py`.

## `protocols`

The two protocols whose exploits the model includes: `pendle` and `morpho-blue`.

| Key | Unit | Meaning |
|---|---|---|
| `label` | text | shown in the report |
| `llama_slug`, `category` | DefiLlama | locate the protocol for the frequency estimate |
| `severity` | Beta | loss if exploited (Pendle mean 14 %, Morpho Blue mean 9 %) |
| `basis` | text | justification |

Read by `priors.py`.

## `oracle`

The oracle-failure event of `analyze`.

| Key | Unit | Meaning |
|---|---|---|
| `techniques` | list | DefiLlama hack techniques counted as oracle failures (misconfigured, stale, predictable); spot-price manipulation is excluded |
| `unverified_factor` | multiplier | applied when the oracle's code is unverified (today 2) |
| `p_year_floor` | probability per year | minimum (today 1 %) |
| `severity` | Beta | how far the oracle misreports downwards (mean 10 %) |

Read by `priors.py`.

## `frequency`

How an exploit probability is derived from DefiLlama's hack record (details in `docs/how-risk-is-computed.md`, section 3).

| Key | Unit | Meaning |
|---|---|---|
| `years` | years | look-back window of the hack record (5) |
| `min_tvl_usd` | USD | protocols below this size are ignored in the counts |
| `tiers_usd` | USD | size bands: under 10M, 10M to 100M, over 100M |
| `category_multiplier_clip` | [min, max] | bounds of the category adjustment (0.5 to 2) |
| `age_factor` | multipliers | 2 for a protocol listed less than a year ago, 1 between one and three years, 0.7 beyond |
| `floor`, `cap` | probability per year | the result is kept between 0.5 % and 15 % |

Read by `priors.py`.

## `unknown_issuer`

The conservative default for a yield token not in `issuers`: a 15 % yearly depeg chance with 60 % recovery, and a heavy exploit severity (mean 33 %). Same fields as an `issuers` entry, plus `category` (`Yield`). Read by `priors.py`.

## Top-level parameters of `analyze`

| Key | Unit | Meaning | Read by |
|---|---|---|---|
| `pt_stress_extra_discount` | multiplier | during a depeg, an oracle that follows the PT market sees the depeg × (1 + this), because the PT trades below its backing as the Pendle pool drains (0.5) | `propagate.py`, `simulate.py`, `decide.py` |
| `gas_exit_usd` | USD | gas cost added to every exit and de-lever estimate (25) | `decide.py` |
| `tail_budget` | fraction of equity | REDUCE when CVaR 99 % exceeds this share of the equity (0.5) | `decide.py` |

## `watch`

The thresholds of `watch --vault` and `watch --user`. Changing them changes when alerts fire; `docs/alert-runbook.md` describes each alert.

| Key | Unit | Default | Alert or behaviour it controls |
|---|---|---|---|
| `poll_seconds` | seconds | 12 | delay between two polls |
| `confirmations` | blocks | 2 | how far behind the newest block the watcher stays |
| `max_range` | blocks | 500 | largest block range read in one batch |
| `state_window_blocks` | blocks | 64 | how far back state is read; older ranges use the oldest servable block |
| `crosscheck_every_blocks` | blocks | 300 | cadence of cross-checks, lender refresh, exit quotes and position rediscovery |
| `market_share_warn` | fraction of the vault | 0.25 | `Exposure` at start, and `Adapter.Allocate` raised to warn when a market crosses it |
| `utilization_warn` | fraction | 0.99 | utilisation alerts, for vaults and borrows |
| `utilization_min_share` | fraction of the vault | 0.10 | a vault market's utilisation is alerted only if it holds at least this share |
| `oracle_move_warn` | fraction | 0.05 | `Oracle` moved alerts |
| `large_flow_info` | fraction of the vault | 0.01 | someone else's deposit or withdrawal is reported above this size |
| `lender_min_share` | fraction of supply | 0.05 | who counts as a main lender of a borrowed market |
| `lender_max` | count | 5 | main lenders kept per market |
| `lender_concentration_warn` | fraction of supply | 0.5 | `Lender` concentration warning at start |
| `lender_withdraw_min_share` | fraction of supply | 0.05 | `Lender` withdrawal warning |

The health-factor levels of `watch --user` are not here: they are a command-line option, `--hf` (default `1.10,1.05,1.02`).

## How to add a yield issuer

When a PT's underlying is not in `issuers`, `analyze` uses `unknown_issuer` and says so in the report's notes. To add it:

1. **Find the token address** of the underlying: it is the `underlyingAsset` of the Pendle market, or the `issuer` node of the graph.
2. **Find its DefiLlama slug and category** at `https://api.llama.fi/protocols` (the `slug` and `category` fields).
3. **Collect its depeg history:** the worst prices it traded at, when, and how quickly it recovered. The tool also prints its worst one-year drawdown.
4. **Add the entry**, with each number justified in its `basis`:

```json
"0x<token address, lowercase>": {
  "symbol": "TOKEN", "issuer": "Protocol name", "llama_slug": "protocol-slug", "category": "Category",
  "kind": "synthetic-dollar",
  "dependencies": ["What it relies on off-chain"],
  "depeg": {"p_year": 0.10, "severity": {"a": 1.5, "b": 15.0}, "recovery": 0.7,
            "basis": "Worst observed depeg and date; why this frequency and recovery."},
  "hack": {"severity": {"a": 1.0, "b": 4.0}, "basis": "What an exploit would take, and any backstop."}
}
```

5. **Run it on your position:** `python3 -m riskdep analyze --live --morpho-market <id> --user <address>`. Do not `--refresh` the demo snapshot: it rewrites the snapshot and its date, which the offline tests rely on.
6. **Run the tests.**

A severity's mean is a / (a + b): `{"a": 1.5, "b": 15.0}` averages 9 %. Raising `a` relative to `b` makes larger losses more likely.
