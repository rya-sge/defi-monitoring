# The exit queue: a depositor's place in a run on a vault

This document explains the run / queue model built into both watches (`watch --vault` and `watch --user`). It answers the question a Morpho Vault V2 depositor faces when something goes wrong: **if everyone heads for the exit, how much of my position gets out, and how much of the loss do I end up carrying?** The model comes from Team 2's feedback (`teammate/team2.md`, "Run / queue model"), and closes item 1 of `docs/analysis/comparison_team.md` §5. A [learn section](#learn-what-you-need-to-understand) at the end explains the concepts used.

Every number below comes from **Sentora RLUSD Main**, the largest Morpho Vault V2 on Ethereum, from the recorded replay at block 26,162,932 (2026-10-10). The depositor is its largest holder (`0xb03d…babc`).

## Contents

- [1. Why a queue model](#1-why-a-queue-model)
- [2. What was built](#2-what-was-built)
- [3. The model](#3-the-model)
- [4. Who is ahead of you](#4-who-is-ahead-of-you)
- [5. The loss cases](#5-the-loss-cases)
- [6. Reading the output: Sentora RLUSD Main](#6-reading-the-output-sentora-rlusd-main)
- [7. The `ExitQueue` alert](#7-the-exitqueue-alert)
- [8. Limits](#8-limits)
- [9. Code and tests](#9-code-and-tests)
- [Learn: what you need to understand](#learn-what-you-need-to-understand)

## 1. Why a queue model

For a lending vault, the cost of leaving is rarely a price impact: while liquidity exists, a withdrawal is paid at par. The cost is **the race for that liquidity**. Team 2 breaks the exit cost into four terms:

| Term | When it matters |
|---|---|
| Slippage | Only on what must be sold rather than redeemed (PTs, LP tokens); vault shares have no market to speak of |
| **Queue cost** | The extra loss from being behind others in the withdrawal line. Dominant in a crisis |
| **Stuck cost** | The part of the position that cannot leave, and keeps its exposure while it waits |
| Forgone yield | What leaving costs if the incident turns out to be nothing |

The watches already showed **how much can leave now** (plain withdrawal and `forceDeallocate`) and **the loss not yet written off** (`UnrealisedBadDebt`). They did not say what happens when other depositors compete for the same liquidity. That is the gap this model fills.

Why a run is rational: Morpho Blue records bad debt only when the underwater position is liquidated. Until then the vault's share price stays at par, so whoever withdraws first is paid in full and leaves the loss to those who stay. With a fixed oracle (exchange-rate or linear-discount), no liquidation fires at all and the loss can stay hidden much longer.

## 2. What was built

| Piece | Where |
|---|---|
| The model: recovery, stuck part, loss at each queue position | `riskdep/exit_queue.py`, pure functions |
| The vault's holders, each classified as contract or wallet | `exit_queue.holders`: Morpho API, then `eth_getCode` |
| A start-up table in both watches, per vault and depositor | `exit_queue.table`, printed after the liquidation curves |
| An alert, `ExitQueue`, re-evaluated every batch | `exit_queue.assess`; holders re-read every 300 blocks |
| Two thresholds | `registry.json` → `watch.exit_queue_phi`, `watch.exit_queue_stuck_warn` |
| Tests | `tests/test_exit_queue.py` (8 tests, including Team 2's worked example) |
| Design and decisions D62–D67 | `plan/2026-10-10-exit-queue.plan.md` |

Nothing new is needed to run it: the same keyless Morpho API and RPC as before.

## 3. The model

Notation, all in the vault's asset:

| Symbol | Meaning | Read from |
|---|---|---|
| T | the vault's total assets | `totalAssets()` |
| A | the depositor's assets | its shares × the share price |
| W_plain | what a plain withdrawal can pay: idle assets and the liquidity market | `VaultState.withdrawable` |
| W_forced | what only `forceDeallocate` reaches: the other markets' unborrowed part | `VaultState.force_withdrawable` |
| W | W_plain + W_forced: everything that can leave now | |
| q | the other depositors' assets that leave before you: your **queue position** | section 4 |
| L | the vault's share of the bad debt in a loss case | section 5 |
| X | the vault's assets in the markets that carry L | section 5 |

**What you recover at par.** Liquidity is paid in arrival order, plain liquidity first:

$$
R(q) = \min\big(A,\ \max(0,\ W - q)\big), \qquad S(q) = A - R(q)
$$

S(q) is the **stuck** part: it stays in the vault. The slice of R that lies beyond W_plain comes out through `forceDeallocate` and pays the adapter's penalty (the highest penalty among the vault's adapters, to be conservative).

**The loss on what stays.** The model assumes the run drains everything that can leave before the bad debt is written off (decision D63, the worst case Team 2 describes). The loss L then falls on the T − W left in the vault:

$$
\rho = \min\!\left(1,\ \frac{L}{T - W}\right), \qquad \text{your loss}(q) = S(q)\cdot\rho + \text{penalty}
$$

**Two reference points.**

- **Pro rata**, what you lose if nobody runs and the loss is shared by every holder: A · L / T.
- **Last out, later**, the upper bound. Over time, borrowers in the healthy markets repay and their liquidity is withdrawn too, so the very last holders are left with only the markets that carry the loss. If you are among them, you lose min(A, X) · L / X.

**Team 2's example** checks the formulas (it is a test, `test_team2_example_loss_by_queue_position`): a 100M vault, 15M in a market that depegs 30 % (a 4.5M loss), 20M of liquidity elsewhere.

| Queue position | Your loss, % of your position |
|---|---|
| Pro rata | 4.5 % |
| First out | 0 % |
| Behind the first 20M | 4.5 / 80 = 5.6 % |
| Last out, later | 30 % |

The spread from 0 % to 30 % depends only on your place in the queue. That spread is what acting early is worth.

## 4. Who is ahead of you

Team 2 suggests ranking the competing claims by how fast their holders react: contracts (other vaults, funds, multisigs run by bots or teams on call) move first; plain wallets move slowly. The model computes four named queue positions:

| Queue position | q (other depositors' assets ahead of you) |
|---|---|
| first out | 0 |
| behind contracts | every holder with code, except you |
| behind φ of others | φ × (T − A), with φ = `exit_queue_phi`, 0.5 by default |
| last of the run | T − A, everyone else |

**How holders are found.** The Morpho API lists a vault's holders (`vaultV2ByAddress.positions`, first page of 100, the largest first). On Sentora that page covers 99.4 % of the vault's shares out of 342 holders; the unlisted rest is not counted as contracts. Each holder's shares are converted to assets at the on-chain share price, then `eth_getCode` tells a contract from a wallet.

**EIP-7702 wallets.** Since the Pectra upgrade, a wallet can delegate to smart-account code, and `eth_getCode` then returns `0xef0100` followed by the delegate's address. Such a wallet is still signed for by a person, so it counts as a wallet. Among Sentora's 100 listed holders, 28 have code: 21 are contracts and 7 are delegated wallets.

**When holders are unknown** (the API does not answer), the "behind contracts" row is dropped and the alert measures the "behind φ of others" position instead, and says so.

## 5. The loss cases

The model needs a loss L to share out. It takes it from the borrower positions the watches already value (`market_risk.py`), so no new scenario engine is involved:

| Case | L, the vault's loss | X, the exposure that carries it |
|---|---|---|
| now | the vault's share of each market's **unrealised bad debt** | the vault's assets in the markets with unrealised bad debt |
| all collateral −2, −5, −10, −20, −30, −50 % (−30 and −50 added by D98) | the vault's share of each market's bad debt if **every** collateral gapped down by that much at once | the vault's assets in the markets with bad debt at that fall |

The "all collateral" rows are a deliberately simple stress: they reuse the liquidation-curve points (D50) and move every market together. Named scenarios per collateral (BTC −50 %, a USDe depeg, a feed misreport) are point 4.3 of `docs/analysis/comparison_team.md` and `docs/vault-depositor-scenarios.md`.

## 6. Reading the output: Sentora RLUSD Main

`watch --replay` prints, after the liquidation curves:

```
  exit queue (100 of 342 holders listed, 99.4% of the vault; other contracts hold 19.9%):
    position 149,441,244 RLUSD · can leave now 85,594,094 (39,242,287 plain + 46,351,806 forced at 0.01%)
    queue position             others ahead         at par          stuck
    first out                             0     85,594,094     63,847,151
    behind contracts             90,939,204              0    149,441,244
    behind 50% of others        154,335,078              0    149,441,244
    last of the run             308,670,156              0    149,441,244
    your loss, RLUSD                    pro rata              first out       behind contracts   behind 50% of others        last of the run        last out, later
    now                                        0                  4,635                      0                      0                      0                      0
    all collateral −2%                         0                  4,635                      0                      0                      0                      0
    all collateral −5%                         0                  4,635                      0                      0                      0                      0
    all collateral −10%                  165,672                 91,680                203,739                203,739                203,739                507,866
    all collateral −20%                1,840,366                971,576              2,263,230              2,263,230              2,263,230              5,214,149
```

**The first table: what gets out.**
- The depositor holds 149.4M RLUSD, 32.6 % of the vault. Only 85.6M can leave now: 39.2M idle (the vault has no liquidity adapter) and 46.4M through `forceDeallocate`, at a 0.01 % penalty.
- **Even first out, 63.8M stays stuck**: the position is larger than everything that can leave.
- Twenty other contract holders hold 90.9M, more than the 85.6M that can leave. **If they go first, nothing is left for this depositor**, and the whole 149.4M stays in.

**The second table: what it costs.**
- **Now** there is no unrealised bad debt, so there is no loss to share. First out still pays 4,635 RLUSD, the `forceDeallocate` penalty on 46.4M.
- **All collateral −10 %** leaves 0.51M of bad debt in the vault, in markets holding 54.8M of it. Pro rata, the depositor would lose 165,672. Exiting first cuts that to 91,680, because 85.6M leaves at par. Behind the contracts, the whole position stays and takes the higher loss rate of a drained vault (0.51M over the 372.5M left, 0.14 %): 203,739. If the depositor stays to the very end while the healthy markets empty, the bound is 507,866.
- **All collateral −20 %** follows the same pattern, ten times larger: from 1.84M pro rata, through 2.26M behind the contracts, to 5.21M as the last one out.

**What it says.** On this vault, the queue matters less than the size of the position. The depositor cannot get out fully even first in line, because it owns a third of the vault and the vault lends most of its money. Its best lever is the order of magnitude, not the timing: if the run happens, it ends up carrying the loss along with the slow wallets. The useful signal is therefore "act before the threshold", not "race at the threshold", as Team 2 puts it, which is what the alert below reports.

## 7. The `ExitQueue` alert

| Level | When |
|---|---|
| warn | at least `exit_queue_stuck_warn` (50 %) of your position would be stuck if every contract holder withdrew before you |
| critical | the same, **and** the vault already carries unrealised bad debt, which would fall on the stuck part |

It fires **on crossing** (a level higher than at the previous batch), like the other state alerts, so it does not repeat every block. The holder list is re-read with the full refresh every 300 blocks; the depositor's assets and the liquidity are re-read every batch.

On the replay the warn fires at start-up: 100 % of the position would be stuck behind the contract holders. There is no unrealised bad debt today, so it stays a warn. The runbook entry is in `docs/alert-runbook.md`.

## 8. Limits

- **The run drains everything before the write-off** (D63). That is the worst case for a holder who stays. If liquidators act quickly, bad debt is written off earlier and shared pro rata among more holders.
- **Liquidity is today's.** Borrowers repaying, liquidations repaying debt, and the curator reallocating all add liquidity during a run; new deposits from the vault's supply queue add some too. None of that is modelled, except as the "last out, later" bound.
- **Reaction speed is a binary proxy.** "Has code" is not "reacts fast": a dormant multisig is slow and a bot-run wallet is fast. φ is a single number with no data behind it.
- **Holders are read now, not at the replay's block.** The list and the code checks are cached in the replays from a request made the same day as the recording.
- **The "all collateral" cases are crude.** Every collateral falls by the same amount at once, as a gap, with no liquidation on the way and no slippage.
- **Not modelled here:** MEV ordering within a block. The drain of a market whose oracle does not follow the market, with the Public Allocator's inflow, is now modelled separately and taken out of the exit queue's liquidity (`docs/drain-threshold.md`).
- **Vault V2 only.** Vault V1 deposits are not watched yet (step 4 of `docs/analysis/NEXT_STEP.md`).

## 9. Code and tests

| Function | Pure | Role |
|---|---|---|
| `exit_at(liq, q)` | yes | R, the forced part, the penalty, S at queue position q |
| `loss_rate(liq, L)` | yes | ρ |
| `depositor_loss`, `pro_rata_loss`, `last_out_loss` | yes | the loss columns |
| `queue_points(liq, holders, depositor)` | yes | the named queue positions |
| `loss_cases(risks, shares, vault_assets)`, `vault_cases(risk, st)` | yes | L and X per case, from `market_risk` |
| `alert_point`, `assess` | yes | the alert |
| `holders(f, vault, …)` | no | Morpho API and `eth_getCode` |
| `VaultExit` | — | wires it all into `watch.py` and `watch_user.py` |

`tests/test_exit_queue.py` checks Team 2's example, the plain/forced split and the penalty, the cap on ρ, the queue points with and without holders, the EIP-7702 rule, the loss cases, the alert's warn → critical crossing, and the replay (holders read offline, table printed, alert written).

## Learn: what you need to understand

### Bank runs

A bank lends most of its deposits, so it can never pay every depositor at once. If depositors expect others to withdraw, withdrawing first is the rational move, and the expectation fulfils itself. Diamond and Dybvig (1983) formalised this: first come, first served plus illiquid assets make runs an equilibrium. A Morpho vault is in the same position: it lends most of its assets, and pays withdrawals in arrival order.

### Why a hidden loss turns into a run

If a loss were marked in the share price at once, leaving would not avoid it: everyone would exit at the lower price. The run is rational only while the loss is **not yet marked**. On Morpho Blue, bad debt is marked when the underwater position is liquidated, so between "the collateral no longer covers the debt" and "the liquidation" (or forever, with a fixed oracle), exits at par shift the loss onto those who stay.

### Queue position, not probability

The model does not say how likely a run is. It says, **if** one happens, what you lose as a function of how many others leave before you. That turns an unknowable question (will they run?) into a known one (how much does being late cost?), which is the same move the breakeven probability makes in `docs/scenarios-and-breakeven.md`.

### Plain withdrawal and `forceDeallocate`

A Vault V2 pays a plain withdrawal from its idle assets and from one market chosen by the curator, the liquidity market. Anyone can also call `forceDeallocate` to pull the unborrowed part of another market back into the vault, paying a small penalty set per adapter (at most 2 %). Borrowed assets cannot be pulled at all: they come back only when borrowers repay or are liquidated. *In the project:* `vault.VaultState.withdrawable`, `force_withdrawable`; `docs/glossary.md`.

### Contracts, wallets and EIP-7702

An Ethereum address either has code (a contract) or not (a wallet controlled by a key). Since the Pectra upgrade (May 2025), EIP-7702 lets a wallet point to contract code, so it has code but is still signed for by its key holder. `eth_getCode` returns `0xef0100` plus the delegate's address for such a wallet.

### Check your understanding

1. **Why does the depositor have 63.8M stuck even if it exits first?** Its position (149.4M) is larger than everything that can leave now (85.6M).
2. **Why is "behind contracts" as bad as "last of the run" here?** The other contracts hold 90.9M, more than the 85.6M that can leave: once they are out, nothing liquid is left.
3. **Why is the loss behind the contracts higher than pro rata?** Pro rata spreads the loss over the whole vault (458M). In a run, it falls on the 372.5M that could not leave, so each unit left loses more.
4. **Why does first out still cost 4,635 RLUSD with no bad debt?** That is the 0.01 % `forceDeallocate` penalty on the 46.4M pulled from the non-liquidity markets.
5. **What would turn the warn into a critical?** Any unrealised bad debt in one of the vault's markets: the stuck part would then be carrying a real loss.

### Further reading

- Douglas W. Diamond and Philip H. Dybvig, "Bank Runs, Deposit Insurance, and Liquidity", *Journal of Political Economy* 91(3), 1983.
- Morpho's documentation: [assets flow and withdrawal limits](https://docs.morpho.org/developers/earn/tutorials/assets-flow) (local copy under `docs/external/morpho/docs.morpho.org-developers-docs/earn/`).
- EIP-7702, "Set Code for EOAs": <https://eips.ethereum.org/EIPS/eip-7702>.
- In this repository: `teammate/team2.md` (the original model), `docs/vault-depositor-scenarios.md` (losses under named shocks), `docs/alert-runbook.md` (exit routes).
