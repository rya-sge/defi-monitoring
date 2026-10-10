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

Alerts printed at **start-up** describe a standing condition, not a new event: they repeat after each restart. The start-up output also prints a **liquidation-curve table** for every watched market: the number of borrowers, the share of the debt liquidatable now, the unrealised bad debt, and the share liquidatable after an oracle fall of 2, 5, 10 and 20 %.

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
| `UnrealisedBadDebt` · Unrealised bad debt in *market* | warn from 0.01 % of the vault, critical from 0.1 % | Borrowers in a market the vault supplies are underwater: their collateral no longer covers their debt, but Blue has not written it off yet. The vault's share and yours are in the detail. | The market's borrowers in the start-up curve table; whether liquidators are active (`Blue.Liquidate`). | The loss is not in the share price yet, and depositors who exit before the liquidation leave it to those who stay. Exit capacity is the constraint: see [exit routes](#exit-routes-from-cheapest-to-most-expensive). |
| `DrainWindow` · *market* is X % from the drain threshold / Drain of *market* pays now | warn within 2 points of d\*; critical at d\* | The collateral of a market the vault supplies trades below its oracle price. Past d\* = 1 − LLTV / (1 + 0.5 %), anyone can buy it, post it and borrow the market's whole free liquidity (plus what the Public Allocator can move in) without intending to repay. The detail gives the drainable amount and the vault's share. | The drain-threshold table at start-up: the discount, d\*, the margin; the oracle's kind (an exchange-rate or fixed oracle does not follow a depeg); the collateral's market price elsewhere. | Warn: exit before the threshold, the liquidity is still there; watch the curator, who can lower caps at once. Critical: the market's liquidity can go in one block, and what was lent there is underwater at the market price. See `docs/drain-threshold.md`. |
| `ExitQueue` · X % of your position in *vault* would be stuck in a run | warn from 50 % stuck; critical when the vault also carries unrealised bad debt | If every contract holder of the vault (other vaults, funds, multisigs) withdrew before you, what can leave the vault now would not pay out at least half of your position. With unrealised bad debt, the part left behind would carry it. When the holder list is unavailable, the measure is "behind 50 % of the other depositors". | The exit-queue table at start-up: what you recover first out, behind the contracts, and last; your loss in each case. `docs/exit-queue.md` explains it. | Act before the threshold, not at it: withdraw what you can while liquidity is there (plain, then `forceDeallocate`), and size the position to what can leave. See [exit routes](#exit-routes-from-cheapest-to-most-expensive). |
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
| `LiquidationCurve` · A 5 % fall would liquidate X % of *market* | warn | In a market holding at least 10 % of the vault, a 5 % oracle fall would make at least 25 % of the debt liquidatable at once. Many liquidations together sell a lot of collateral into the market, which deepens the fall and can leave bad debt. | The start-up curve table: how the share grows at −10 and −20 %, and the bad debt column. | Weigh the vault's allocation to that market; nothing to do until prices move. |
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
| `LiquidationCurve` · A 5 % fall would liquidate X % of *market* | warn | Other borrowers of your market (your own position is excluded) hold at least 25 % of its debt within a 5 % fall of liquidation. Their liquidations would sell collateral into the market at once, which pushes the price, and your health factor, further down. | The start-up curve table, and your own liquidation distance. | Keep a larger margin than the curve's steep zone: if your liquidation sits just beyond theirs, their cascade can reach you. |

## Admin-surface alerts (vault depositors and borrowers)

These concern the contracts your markets depend on beyond Morpho: each market's oracle and the feeds or vault shares it reads, the collateral and loan tokens, and for a Pendle PT its SY and yield token. The start-up output lists them in an **admin surface** table: which are upgradeable, who their admin or owner is, which aggregator a Chainlink feed points to, and each oracle's gap to DefiLlama's price.

| Event · title | Level | What it means | Check | What you can do |
|---|---|---|---|---|
| `Admin.Upgraded` / `Admin.BeaconUpgraded` · *contract* was upgraded | critical | The code behind a token, an oracle or a feed changed. Its behaviour can now be anything the new code says. | The new implementation on a block explorer: is it verified, does the project announce it? | If the change is unannounced or the code unverified, treat the market as compromised: de-lever or exit until it is explained. |
| `AdminState` · Implementation / beacon of *contract* changed | critical | The same, found at a state refresh because no standard event was emitted. | As above. | As above. |
| `Admin.Paused` · *collateral* was paused | critical | A paused collateral token cannot be transferred, so liquidators cannot take it: liquidations can fail and leave bad debt. | The issuer's announcement; the market's liquidation curve. | Borrower: positions near liquidation cannot be saved by liquidators either; keep a wide margin. Depositor: exposure to that market is at risk. |
| `Admin.Paused` · *other contract* was paused | warn | A feed, SY or other dependency suspended its operations. | Which one, and why. | Watch the oracle: a paused feed can stop answering. |
| `Admin.Mint` · Large mint of *token* | critical | One transaction minted at least 5 % of a collateral or yield token's supply. Unbacked minting is how Resolv's USR depegged in March 2026. | The recipient and the issuer's backing. | If the mint is not explained, assume the token will depeg: de-lever, or exit the vault's exposure. |
| `Admin.AdminChanged` · Proxy admin changed | warn | Someone else can now upgrade the contract. | Who the new admin is (a timelock, a multisig, an EOA). | An EOA admin is the weakest; reconsider the dependency. |
| `Admin.OwnershipTransferred` / `AdminState` owner · Owner changed | warn | Control of the contract's owner functions moved. | The new owner. | As above. |
| `Admin.AggregatorProposed` / `AggregatorConfirmed` · Price feed change | warn | A Chainlink feed will use, or now uses, a different aggregator. Usually maintenance. | Chainlink's announcements; the oracle's next prices. | Watch for `OracleDivergence`. |
| `Admin.RoleGranted` · Admin role granted | warn | The default admin role of an access-controlled contract was granted to a new account. | The account. | As for an owner change. |
| `Admin.RoleGranted` / `RoleRevoked` · Role granted or revoked | info | A non-admin role changed (minter, pauser, …). | — | Nothing, unless it is a minter on a collateral token you depend on. |
| `Admin.Unpaused` | info | A pause ended. | — | Nothing. |
| `OracleDivergence` · Oracle of *market* is ±X % from the market price | warn | The oracle's price differs by at least 3 % from DefiLlama's collateral ÷ loan price. A fixed-rate or linear PT oracle differs by design; otherwise the oracle is lagging or misconfigured, or the market is dislocated. Liquidations follow the oracle. In `watch --user`, on a market you borrow from, the detail also gives the impact on your borrow if the gap is real (loss, liquidation, time to impact) and `depositor_impact` carries the loss (D93); `analyze --shock` gives the full incident view. | Which side is right: the oracle, or the market price. | A borrower whose oracle reads high is safer on paper than in reality: add margin. |
| `Blue.SetOwner` · Morpho Blue owner action | warn | Morpho Blue's owner changed. Blue is immutable: existing markets are not affected. | — | Nothing. |
| `Blue.EnableIrm` / `EnableLltv` / `SetFeeRecipient` | info | Morpho governance enabled a new rate model or LLTV, or changed the fee recipient. | — | Nothing. |
| `AdminSurface` · N of M contracts your markets depend on are upgradeable | info (start-up) | The list of upgradeable dependencies and who can upgrade them; "UUPS" means the upgrade right is in the contract's own code. | Whether those admins are timelocks or multisigs. | Context for the alerts above. |

## Data and infrastructure alerts

| Event · title | Level | What it means | What you can do |
|---|---|---|---|
| `CrossCheck` · Data sources disagree: second RPC | critical | The main RPC and an independent one return different blocks: one is on another fork or wrong. | Do not act on this run's data. Restart later, or point the tool at another RPC. |
| `CrossCheck` · Data sources disagree (Morpho API vs chain) | warn | The API's numbers differ from the chain's by more than 0.5 %. | The chain is authoritative; the API may be lagging. Positions found through the API may be stale. |
| `Gap` · Blocks X–Y could not be read | warn | The free RPC refused those blocks (too old); events in them were not checked. | Check the vault and your positions on a block explorer for that range. |
| `WARN RPC: …; retrying` (terminal line, not in the JSONL) | — | The RPC failed; the tool retries with backoff and does not move its cursor. | Nothing unless it persists; then check your network. |
| `WARN optional log filter skipped …` (terminal line) | — | The free RPC refused one of the admin-surface log queries for a range. Admin events of that range may be missed; upgrades, owner and feed changes are still caught at the next state refresh (at most 300 blocks later). | Nothing unless it repeats on every batch. |

## Exit routes, from cheapest to most expensive

For a **vault depositor**, as described in Morpho's documentation:

1. **Plain `withdraw` / `redeem`**: paid from the vault's idle assets and its liquidity market, no penalty. The `watch` start-up line "plain withdrawal can pay" gives the amount.
2. **Force withdrawal**: `forceDeallocate` pulls assets back from other markets at the adapter's penalty (at most 2 %); Morpho's `vaultExitBundlesV1ForceWithdrawVaultV2` takes the penalty-free part first. Limited to each market's unborrowed supply.
3. **In-kind redemption**: when the markets are fully borrowed, `vaultExitBundlesV1InKindRedemptionVaultV2` hands you the vault's supply positions in the markets instead of the asset. You then hold those positions directly and withdraw from each market as it frees up.

For a **borrower**: repay (in full or in part), add collateral, de-lever in one transaction (`blueBundlesV1RepayAndWithdrawCollateral`, bounded by a `maxLtv` check), or migrate the whole borrow to another market (`blueBundlesV1MigrateBorrowPosition`).
