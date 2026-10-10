# Alert runbook

What each alert of `python3 -m riskdep watch` means, what to check, and what can be done about it. One entry per alert; the **event** column is the `event` field of the JSONL line (`out/watch-*.jsonl`), and the **title** is what the terminal prints. Terms are defined in `docs/glossary.md`.

The tool only alerts; it never acts. Every action below is taken by you, with your own wallet. The Morpho contracts named in the actions (Bundles, `forceDeallocate`, in-kind redemption) are described in Morpho's documentation; check the exact amounts in a simulation before signing.

## Contents

- [Reading an alert](#reading-an-alert)
- [Before acting on any alert](#before-acting-on-any-alert)
- [Vault depositor alerts](#vault-depositor-alerts)
- [Borrower alerts](#borrower-alerts)
- [Data and infrastructure alerts](#data-and-infrastructure-alerts)
- [Exit routes, from cheapest to most expensive](#exit-routes-from-cheapest-to-most-expensive)

## Reading an alert

```
WARN     #26162630 tx 0x2dcc1a5fe8… 100% of PT-sUSDE-26NOV2026/USDC (LLTV 91.5%) is funded by Vault Pendle Ecosystem USDC — …
^level   ^block    ^transaction    ^title                                                                               ^detail
```

| Level | Meaning | Expected reaction time |
|---|---|---|
| **critical** | money is being lost now, or can be lost in the next block | minutes |
| **warn** | the risk of the position changed; a decision may be needed | hours |
| **info** | context: a move worth knowing, nothing to decide | when convenient |

Each JSONL line also carries `depositor_impact` (your share of a loss, in the vault's asset, negative for a loss) and `data` (the raw numbers behind the alert).

Alerts printed at **start-up** describe a standing condition, not a new event: they repeat after each restart.

## Before acting on any alert

1. **Open the transaction** on a block explorer (`https://etherscan.io/tx/<tx>`) when the alert has one, and confirm it says what the alert says.
2. **Check the data sources agreed.** A `CrossCheck` alert in the same run means the data may be wrong (see the last section).
3. **Re-read the state now.** Alerts are 25 to 40 seconds behind the chain (2 confirmations, 12-second polling). For a fast-moving situation, re-run `watch --user <address> --blocks 10` to get the current table.

## Vault depositor alerts

### Losses

| Event · title | Level | What it means | Check | What you can do |
|---|---|---|---|---|
| `Blue.Liquidate` · Bad debt in *market* | critical | A liquidation in a market the vault supplies left debt the collateral did not cover. The vault's share of it is a loss for every depositor; `depositor_impact` gives yours. | Whether other positions in that market are also underwater (the next bad debt). The size of the vault's allocation to the market. | The loss is already realised. Decide whether to stay, using exit capacity and the market's remaining exposure. |
| `PendingLoss` · Loss recorded by an adapter, not yet accrued | critical | An adapter's assets fell below what the vault has recorded. Every deposit and withdrawal accrues it first, so it is already in the price you would exit at. | Which market lost value (look for a `Blue.Liquidate` with bad debt in the same batch). | Same as above: the loss is in the price. It is a signal that something happened, not a window to exit before others. |
| `Vault.AccrueInterest` · Vault total assets fell | critical | The vault's share price dropped at an accrual. | The cause in the preceding batches. | As above. |
| `Adapter.BurnShares` · Supply shares written off | critical | The curator wrote off the vault's position in a market (a timelocked action, so a `Submit` preceded it). | The market and the amount. | As above; review the curator's earlier `Submit` alerts. |

### Governance changes

| Event · title | Level | What it means | Check | What you can do |
|---|---|---|---|---|
| `Vault.Submit` / `Adapter.Submit` · Pending change with no notice | critical | A risk-increasing change was submitted for a function whose timelock is 0: it can take effect in the same block. | The decoded change in the title and detail: which function, which value. | If the change is unacceptable (a fee rise, an unknown allocator, a gate), exit now; there is no warning period to wait for. |
| `Vault.Submit` / `Adapter.Submit` · Pending change | warn | A change was submitted; the detail gives the date from which it can be executed and the function's timelock. | The decoded change, and the date. | You have until that date to exit if you disagree. A sentinel can revoke it (watch for `Revoke`). |
| `*.Accept` · Change now live | warn | A submitted change was executed. | That it matches the `Submit` you saw. | Re-assess the vault with the new rule in place. |
| `*.Revoke` · Pending change cancelled | info | A pending change was withdrawn. | — | Nothing. |
| `Timelock` · N risk-increasing change(s) can be made with no notice | warn (start-up) | These functions have a zero timelock and are not abdicated, so their `Submit` will give no warning. | The list: fee setters, allocator list, gates, penalty. | Decide whether you accept a curator who can change these instantly. Each such `Submit` will then be critical. |
| `Vault.IncreaseAbsoluteCap` / `IncreaseRelativeCap` · Cap raised | warn | More of the vault may go to a market, a collateral or an adapter. | The identifier in the title (which market or collateral). | Check that collateral's soundness and oracle. |
| `Vault.AddAdapter` · New adapter | warn | A new place the vault's money can go. | What the adapter supplies to. | As above. |
| `Vault.SetPerformanceFee` / `SetManagementFee` | warn | A fee changed (bounded at 50 % of interest and 5 % a year). | The new value. | Compare the net yield with alternatives. |
| `Vault.Set…Gate`, `SetAdapterRegistry`, `SetCurator`, `SetOwner`, `SetIsAllocator`, `DecreaseTimelock`, `SetForceDeallocatePenalty` · Vault configuration | warn | Who controls the vault, who may exit, or how much notice is given changed. | The detail (`key=value`). | A shorter timelock or a new exit gate reduces your protection; reconsider the position. |
| `Vault.SetIsSentinel`, `IncreaseTimelock`, `Abdicate`, `SetMaxRate` · Vault configuration | info | A risk-reducing or neutral change. | — | Nothing. |
| `Vault.SetLiquidityAdapterAndData` · Deposits and withdrawals now go through another adapter | warn | An allocator changed where plain deposits and withdrawals are routed (not timelocked). | The new liquidity market. | Your plain-withdrawal capacity changed: check the next status line. |

### Exposure and liquidity

| Event · title | Level | What it means | Check | What you can do |
|---|---|---|---|---|
| `Exposure` · X % of the vault is in *market* | warn (start-up) | One market holds more than 25 % of the vault: a bad debt there hits every depositor. | That market's collateral, oracle and LLTV. | Accept the concentration or move to a more diversified vault. |
| `Adapter.Allocate` / `Deallocate` | info, warn above 25 % or for a new market | The allocator moved money; the detail gives the new allocation and share. | — | Nothing, unless it crosses into a market you would not lend to. |
| `Liquidity` · You can no longer exit in full with a plain withdrawal | warn | Idle assets plus the liquidity market no longer cover your position. | The detail: payable now, and how much more `forceDeallocate` can reach, at what penalty. | See [exit routes](#exit-routes-from-cheapest-to-most-expensive). |
| `Gate` · A gate blocks your exit | warn | `canSendShares` or `canReceiveAssets` refuses your address. | Which gate, on Etherscan. | Contact the curator; a different receiver address may pass `canReceiveAssets`. |
| `Vault.ForceDeallocate` · Liquidity forced out of an adapter | warn | Someone paid the penalty to pull assets back to the vault, usually to exit. | Who, and how much. | A sign that others are leaving; check exit capacity. |
| `Blue.Withdraw` / `Borrow` · *market* is ≥ 99 % utilised | warn | A market holding at least 10 % of the vault is fully borrowed: nothing more can leave it until borrowers repay. | Its share of the vault. | Exit capacity through that market is gone for now. |
| `Oracle` · Oracle of *market* moved ±X % | warn | The collateral of a held market was repriced by at least 5 % between two reads. | The direction: a fall brings liquidations and possibly bad debt. | Watch the next batches for `Blue.Liquidate`. |
| `Caps` · *market* is being wound down | info (start-up) | Its cap is 0 but money is still allocated: the curator is leaving it. | — | Nothing. |
| `Structure` · Adapter is opaque / forceDeallocate is free | info (start-up) | An adapter the tool does not expand, or a zero force-deallocation penalty. | — | Nothing; context for the other alerts. |
| `Vault.Deposit` / `Withdraw` / `Transfer` · Your … / Large … | info | Your own movement, or someone else's above 1 % of the vault. | — | Nothing. |
| `Blue.Liquidate` · Liquidation in *market* | info | A liquidation without bad debt. | — | Nothing. |
| `Blue.SetFee` · Protocol fee changed | info | Morpho's fee on a held market's interest changed. | — | Nothing. |

## Borrower alerts

### Liquidation

| Event · title | Level | What it means | Check | What you can do |
|---|---|---|---|---|
| `HealthFactor` · Liquidatable now on *market* | critical | HF ≤ 1: anyone can liquidate the position now. | — | Repay or add collateral immediately; a liquidation costs the liquidator's bonus (up to 15 % of the repaid debt). |
| `Blue.Liquidate` · You were liquidated on *market* | critical | A liquidation of your position happened; the detail gives the debt repaid, the collateral seized and any bad debt. | The remaining position in the borrow table of the next start-up. | Decide whether to close what remains. |
| `HealthFactor` · HF below the third level (default 1.02) | critical | A fall of about 2 % in the oracle price liquidates you. | The detail gives the exact fall that liquidates. | Act now: repay part of the debt or add collateral. A single-transaction de-lever is Morpho's `blueBundlesV1RepayAndWithdrawCollateral`. |
| `HealthFactor` · HF below the second level (default 1.05) | warn | About a 5 % fall liquidates you. | The collateral's recent volatility. | Plan the de-lever now, while gas and liquidity allow. |
| `HealthFactor` · HF below the first level (default 1.10) | info | About a 9 % fall liquidates you. | — | Know your options; set your own levels with `--hf`. |
| `HealthFactor` · HF back above the first level | info | The position recovered. | — | Nothing. |
| `Oracle` · Oracle unreadable on *market* | warn | The oracle's `price()` reverts. Blue cannot liquidate, and you cannot borrow more or withdraw collateral. | Whether the oracle or one of its feeds is down. | Wait, or repay; nothing can be withdrawn until the oracle answers. |
| `Oracle` · Oracle of *market* moved ±X % | warn | Your collateral was repriced by at least 5 %; the detail gives the new HF. | The direction. | A fall: see the HF alerts. |

### Who can act on the position

| Event · title | Level | What it means | Check | What you can do |
|---|---|---|---|---|
| `Blue.Borrow` / `WithdrawCollateral` · … on your behalf by *address* | warn | An address other than yours borrowed against your collateral or withdrew it. Morpho Blue allows this only to an address you authorised. | Who the caller is: a Bundle you used, a bot you set up, or something unexpected. | If unexpected, revoke its authorisation (`setAuthorization(address, false)` on Morpho Blue) and move the position. |
| `Blue.Repay` / `SupplyCollateral` · … on your behalf by *address* | info | Someone repaid your debt or added collateral for you. Anyone may do this without authorisation, and it lowers your risk. | — | Nothing. |
| `Blue.SetAuthorization` · Your address authorised / removed *address* | warn | An authorisation was given or removed for your address. An authorised address can borrow and withdraw collateral for you. | That you did it. | If you did not, revoke it at once and move the position: the key or signature that authorised it is compromised. |
| `Blue.Borrow` / `Repay` / … · Your *action* | info | Your own action. | — | Nothing. |

### Cost and liquidity of the borrow

| Event · title | Level | What it means | Check | What you can do |
|---|---|---|---|---|
| `Rate` · Borrow rate up on *market* | warn | The borrow APY is 50 % above its value when the watch started. | The collateral's yield against the new rate (the carry). | Repay part, or move the borrow to another market with Morpho's `blueBundlesV1MigrateBorrowPosition`, which repays the source with funds borrowed on the destination in one transaction. |
| `Utilisation` · *market* is X % utilised | warn | The market is fully used: the rate model pushes the rate towards 4 × its target until lenders return or borrowers repay. | The rate in the next batches. | As above. |
| `Lender` · X % of *market* is funded by *vault* | warn (start-up) | One lender holds most of the supply you borrow from. If its allocator moves the liquidity, which needs no timelock, the rate jumps. | Who the lender is; the graph (`riskdep graph --user <address>`) shows it. | Accept the dependency, or prefer markets with several lenders. |
| `Lender` · Main lender *vault* withdrew from *market* | warn | A main lender took out at least 5 % of the market's supply. | The new utilisation and rate. | As for a rate rise. |

## Data and infrastructure alerts

| Event · title | Level | What it means | What you can do |
|---|---|---|---|
| `CrossCheck` · Data sources disagree: second RPC | critical | The main RPC and an independent one return different blocks: one is on another fork or wrong. | Do not act on this run's data. Restart later, or point the tool at another RPC. |
| `CrossCheck` · Data sources disagree (Morpho API vs chain) | warn | The API's numbers differ from the chain's by more than 0.5 %. | The chain is authoritative; the API may be lagging. Positions found through the API may be stale. |
| `Gap` · Blocks X–Y could not be read | warn | The free RPC refused those blocks (too old); events in them were not checked. | Check the vault and your positions on a block explorer for that range. |
| `WARN RPC: …; retrying` (terminal line, not in the JSONL) | — | The RPC failed; the tool retries with backoff and does not move its cursor. | Nothing unless it persists; then check your network. |

## Exit routes, from cheapest to most expensive

For a **vault depositor**, as described in Morpho's documentation:

1. **Plain `withdraw` / `redeem`**: paid from the vault's idle assets and its liquidity market, no penalty. The `watch` start-up line "plain withdrawal can pay" gives the amount.
2. **Force withdrawal**: `forceDeallocate` pulls assets back from other markets at the adapter's penalty (at most 2 %); Morpho's `vaultExitBundlesV1ForceWithdrawVaultV2` takes the penalty-free part first. Limited to each market's unborrowed supply.
3. **In-kind redemption**: when the markets are fully borrowed, `vaultExitBundlesV1InKindRedemptionVaultV2` hands you the vault's supply positions in the markets instead of the asset. You then hold those positions directly and withdraw from each market as it frees up.

For a **borrower**: repay (in full or in part), add collateral, de-lever in one transaction (`blueBundlesV1RepayAndWithdrawCollateral`, bounded by a `maxLtv` check), or migrate the whole borrow to another market (`blueBundlesV1MigrateBorrowPosition`).
