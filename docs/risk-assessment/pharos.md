# Pharos in riskdep: how it is used and what it changes

Pharos (`https://pharos.watch`, run by TokenBrice, MIT-licensed; unrelated to the Pharos Network blockchain) grades stablecoins and yield dollars and publishes what backs each one. `riskdep` reads it for three things (plan `2026-10-11-pharos`, D133–D138):

1. **Off-chain backing.** This one **changes the numbers**: a token shock reaches markets whose collateral is backed by that token through a reserve, so it adds hits and losses.
2. **Issuer grades.** Shown next to each hit and on the graph, never used in a computation.
3. **Common-mode groups.** Coins that fail together, given as a note and as graph edges, never used in a computation.

Contrast with Nexus Mutual (`nexus.md`), which never changes a number.

- [1. Where it appears](#1-where-it-appears)
- [2. Data flow](#2-data-flow)
- [3. From a token to a Pharos id](#3-from-a-token-to-a-pharos-id)
- [4. Off-chain backing: the part that changes the loss](#4-off-chain-backing-the-part-that-changes-the-loss)
- [5. Grades and common-mode groups: shown only](#5-grades-and-common-mode-groups-shown-only)
- [6. Worked examples](#6-worked-examples)
- [7. Impact, and its limits](#7-impact-and-its-limits)
- [8. Maintenance](#8-maintenance)

## 1. Where it appears

| Entry point | What Pharos adds |
|---|---|
| `analyze --vault <addr> --shock token=<t>:<fall>` | markets reached through off-chain backing, with their loss; `issuer grade` on each hit; a common-mode note |
| `analyze --book <file> --shock …` | the same per vault, and the book's notes: the grades of the hit collateral, the common-mode groups across the book |
| `POST /api/incident` | `grade` and `pharos_exposure` per hit; `pharos` (the snapshot date) and `common_mode` per vault (`riskdep/api/schemas.py`) |
| `graph` | `pharos_grade` on assets, `backed by (Pharos)` and `shares (Pharos)` edges (`graph.annotate_pharos`) |

Not used by `analyze` on a Pendle PT, `watch` or `shock`. The shock engine never reads Pharos: a market reached only through Pharos keeps the figures from `vault_incident.py` (§4).

## 2. Data flow

```
api.pharos.watch/api/dependency-graph/v1 ── pharos.load ── pipeline.pharos_snapshot ─┬─ vault_incident.run(pharos=…)
                                                                                      └─ graph.annotate_pharos
registry.json pharos.ids ── pharos.resolve ─┬─ pharos.exposure     → vault_incident.pharos_reach  (loss)
                                            ├─ Snapshot.grade      → vault_incident.graded        (display)
                                            └─ pharos.common_mode  → incident and book notes      (display)
```

1. **Fetch** (`riskdep/pharos.py:load`): one keyless GET. The 0.5 MB response is cut down to about 170 KB: each node's id, grade, score and backing roles (`upstreamAssetId`, `weight`, `economicRole`); each common-mode group's kind, key and members; and the publication date.
2. **Parse** (`pharos.parse`, pure): grades by id (`NR` when not rated); backing by id (a wrapper has weight 1, a basket share its weight); groups kept only if their kind is in `pharos.common_mode_kinds` and they have 2 to `max_group_members` (12) members.
3. **Cache**: `pipeline._outside_fetcher("pharos", mode)` saves the response under `fixtures/replay/pharos/`. Runs are offline by default, `record`/`refresh` read the API again and save the answer, and `live` reads it without saving. If the API cannot be read, `load` returns `None` and the run prints `Pharos: not checked`; it still completes.

## 3. From a token to a Pharos id

Pharos ids are names (`fxsave-f-x-protocol`), not addresses. `pharos.resolve` (D134) tries three things in order:

1. `registry.json` `pharos.ids`: address → `{id, symbol}`. This is required for ambiguous symbols: there are three iUSD ids and two reUSD ids.
2. An exact id: `--shock token=iusd-infinifi:0.3` works.
3. The only id whose first part is the symbol: `fxSAVE` → `fxsave-f-x-protocol`. If two or more ids match, nothing is matched.

A token that matches nothing is simply left out: it is not graded and not followed. That is not an error.

## 4. Off-chain backing: the part that changes the loss

Without Pharos, a token shock reaches only markets whose collateral **is** that token or **wraps it on-chain**: a PT, an ERC-4626 share (plan `wrapped-collateral`). Pharos adds a third route (D135): collateral backed **off-chain** by the shocked token, through a reserve.

`vault_incident.pharos_reach` is pure. It is tried only for `token=` shocks, and only when no on-chain match was found. For each market, it walks the collateral's on-chain path (collateral, then each token it wraps). It takes the first token Pharos knows that is not the target itself, and computes:

```
share = pharos.exposure(token, target)
      = Σ over backing paths  Π edge weights      (depth ≤ 4, capped at 1)
fall(market) = shock × share                      (ignored when share < pharos.min_exposure = 1 %)
```

The market then becomes a hit, with this fall applied to its collateral price. The rule for wrapped collateral (D127) decides what follows:

- **Oracle tracks a market price:** the fall is seen, borrowers below the new price are liquidated, and the bad debt is the loss.
- **Oracle is an exchange rate or a NAV:** the oracle does not move, so nothing is liquidated. The loss is the **hidden shortfall**: what the lenders would lose if the markdown persisted.

These hits are kept out of the shock engine. A Pharos-reached hit keeps the figures from `vault_incident.py`, and the run says so in a note. They then feed everything downstream like any other hit: the vault loss, the depositor's loss when staying or leaving, the verdict, p\*, the book total, and the conditional Monte Carlo.

**Assumption:** a loss in the reserve passes to the token **pro rata**. For a protocol with a loss waterfall (infiniFi slashes its locked tranche first), the senior token loses less, so the figure is an **upper bound** there.

## 5. Grades and common-mode groups: shown only

**Grades (D136).** Each hit shows `issuer grade (Pharos <date>): <symbol> <grade> <score>`, for its collateral or for the first token in its on-chain path that Pharos grades. The book lists the grades of every hit collateral. The `graph` command puts `pharos_grade` on every asset Pharos covers. A grade is Pharos's judgement on a 0–100 scale, not a probability. It is never multiplied into a loss or a prior. Turning grades into a prior is step B5 of `docs/analysis/NEXT_STEP.md`, and is not done.

**Common-mode groups (D137).** The tool lists the vault's other collateral that shares a **narrow** group with the shocked token. A narrow group is one of these kinds, with at most 12 members:

- mint control;
- upgrade control;
- reserve issuer;
- redemption rail.

Example note: `trUSD with strUSD (mint control, upgrade control): one failure of that key, admin or issuer reaches both, so a second shock on them is not independent`. Chain, DEX and wide bridge groups are dropped: Ethereum alone has 202 members. The note does not add a second shock. To price the joint failure, the reader passes both tokens with `--shock`. In `graph`, a shared group becomes an External node, which both assets link to with `shares (Pharos)` edges.

## 6. Worked examples

All offline, using the snapshot recorded on 2026-10-11.

**A loss that exists only through Pharos:** RockawayX USDC Yield, mGLOBAL (Midas) −50 %.

```bash
uv run python -m riskdep analyze --vault 0xE0181090c22579B6A217f1522cbf8c9f1F0C1965 --shock token=mGLOBAL:0.50
```

```
siUSD/USDC (LLTV 91.5%): 0 of 7,194,692 USDC of debt liquidatable (12 borrowers); bad debt 485,180; the vault supplies 29% → its loss 142,972
  issuer grade (Pharos 2026-10-11): iUSD D 49
  reached through what its collateral wraps: siUSD → iUSD ⇒ Pharos: iusd-infinifi → mglobal-midas-fasanara (43.4% of its backing); the oracle does not follow it: no liquidation, the lenders' shortfall if the markdown persists is counted as the loss (hidden)
vault loss 142,972 USDC (0.78% of 18,445,040)
```

| Step | Value |
|---|---|
| mGLOBAL's share of iUSD's backing (Pharos) | 43.4 % |
| fall applied to siUSD | 50 % × 43.4 % = **21.7 %** |
| siUSD oracle | an exchange rate (constant price): no liquidation |
| hidden bad debt in the market, the vault's 29 % of it | 485,180, of which **142,972 USDC** falls on the vault |

mGLOBAL is not the collateral of any market in the book. **Without Pharos, this shock finds no hit and the loss is 0.**

**A note only:** RockawayX Tori Ecosystem, trUSD −30 %. The loss is the same with or without Pharos, because trUSD is reached on-chain. Pharos adds the grades `trUSD C- 54` and `strUSD D 46`, and the note that trUSD and strUSD share a mint key and an upgrade admin.

The RockawayX book in figures, with and without Pharos, is in `outside-providers.md` §1.5. In short, fxSAVE −30 % reaches a second vault, because fxSAVE is 16.4 % of iUSD's backing; fxUSD −30 % produces a 1.63M USD hidden shortfall in the f(x) vault, because fxSAVE wraps fxUSD.

## 7. Impact, and its limits

**On the computation**:

| Pharos part | Changes a number? | Which |
|---|---|---|
| off-chain backing | **yes**, and only upward (it adds hits) | hit list, market fall, vault loss, depositor loss, verdict, p\*, book total and act-first order, conditional Monte Carlo |
| grades | no | shown only |
| common-mode groups | no | shown only; a second shock is the reader's choice |

If Pharos is removed or unreadable, the loss falls back to the hits found on-chain and the grades and notes are left out. The run does not fail.

**Limits**:

- **Stablecoins and yield dollars only.** Pharos has no grade or backing for Morpho, Pendle, oracles, or tokenised credit and fund shares (PST, mGLOeuro, AUTO, PRIME, wYLDS).
- **Backing is incomplete.** Most nodes have no backing edges, and Ethena's hedges and custodians are missing. A missing edge means "not known to Pharos", not "no dependency": the loss is then understated, never invented.
- **The weights are Pharos's**, with `live-reserve` or `curated-reserve` provenance, and can lag the issuer's own report. Every grade is printed with its publication date.
- **Pro-rata pass-through** overstates the loss on a token protected by a junior tranche (§4).
- **A path is cut off at depth 4**, and a share below 1 % is ignored.
- **Pharos is a free service with no SLA**, which is why it is optional by design.

## 8. Maintenance

- **Refresh the snapshot**: run with `--record` (or `--refresh`) and commit the new file under `fixtures/replay/pharos/`. Re-check `pharos.ids` when Pharos's methodology version changes (10.16, model v9 when recorded).
- **Add a token** under an ambiguous symbol: find its id in the recording or on pharos.watch, read the token's `symbol()` on-chain, and add `"<address in lower case>": {"id": "<pharos id>", "symbol": "<symbol>"}` to `registry.json` `pharos.ids`. Update `docs/reference/registry-reference.md` too.
- **Thresholds** (`registry.json` `pharos`): `min_exposure` (1 %), `common_mode_kinds`, `max_group_members` (12), each with its basis.
- **Tests**: `tests/test_pharos.py` (parse and resolve, exposure along paths, narrow groups, offline snapshot, the book reaching iUSD through Pharos backing, the Tori common-mode note, the annotated graph).
- **Related docs**: `docs/risk-assessment/outside-providers.md` §1, `docs/analysis/PROVIDERS.md`, `plan/2026-10-11-pharos.plan.md`, `nexus.md`.
