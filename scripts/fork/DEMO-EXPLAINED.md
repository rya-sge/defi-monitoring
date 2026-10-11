# What `demo.sh --short` shows, line by line

The demo copies Ethereum mainnet onto your machine (a *fork*), then plays a crisis on a real vault with the accounts that could really cause it. `riskdep` watches the vault the whole time, and its alerts appear marked `riskdep ▸`. The script is `scripts/fork/demo.sh`, the design is in `docs/analysis/FORK-PRESENTATION.md`, and the commands are in `scripts/fork/README.md`.

## The words you need

| Word | Here |
|---|---|
| **Vault** | *Belem RWA EURCV*, a Morpho Vault V2 curated by RockawayX. Depositors put in EURCV; the vault lends it to borrowers. |
| **EURCV** | A euro stablecoin issued by Société Générale-Forge: 1 EURCV ≈ 1 EUR. The vault's currency. |
| **mGLOeuro** | A token issued by Midas for a Fasanara private-credit fund. One token is worth about 100,000 EUR. Borrowers post it as collateral. |
| **NAV** | Net asset value: what the fund says one mGLOeuro is worth. It is not a market price; the issuer publishes it. |
| **Oracle / feed** | The contract that tells Morpho what the collateral is worth. Here it reads the NAV that Midas writes into a feed. |
| **LTV** | Loan-to-value: debt ÷ value of the collateral. |
| **LLTV** | Liquidation LTV: 77 % in this market. Above it, anyone can liquidate the borrower. |
| **Liquidation** | Someone repays part of the debt and takes the collateral, with a bonus of 7.4 % here (the LIF, 1 / (0.3 × 0.77 + 0.7) = 1.074). |
| **Bad debt** | Debt that the collateral can no longer cover. It is written off, and the vault's depositors lose it. |
| **Timelock** | A contract that makes a change wait (here 48 h) between being announced and taking effect. |
| **Abdicated** | A vault function the curator has given up for good: it can never be called again. |
| **EOA** | A plain wallet, controlled by one private key; not a multisig, not a contract. |

## Part 1: setting up

```
riskdep — a crisis on a mainnet fork
  building the demo contracts and forking Ethereum mainnet at block 26165572…
  fork at block 26165572: vault holds 4,710,724 EURCV, mGLOeuro NAV 100,000 EUR
```

- The script compiles the two small demo contracts (`scripts/fork/src/`), then starts **anvil**, a local Ethereum node. It copies mainnet's state as it was at block 26,165,572 (11 October 2026), so every balance, position and contract is real.
- Anything done from here on happens only on your machine. Nothing is sent to the real network.
- The check line confirms it forked the right chain: the vault holds 4.71M EURCV, and the mGLOeuro feed reads 100,000 EUR.

```
  starting riskdep watch on the Belem RWA EURCV vault (one block per batch, polling every 2 s)…
```

- `riskdep watch` starts in the background, connected to the fork (`RISKDEP_RPC_URL`, `RISKDEP_FORK=1`). It does what it would do on mainnet:
  1. reads the vault's structure;
  2. reads every borrower of its markets;
  3. reads who controls each contract they depend on;
  4. follows every new block.
- *One block per batch* means it reads the state after each block, so each step of the crisis shows up separately. *Every 2 s* is how often it asks the fork for new blocks (12 s on mainnet, Ethereum's block time).
- Reading everything takes about a minute, so the next two parts play while it works.

## Part 2: the vault

```
Belem RWA EURCV: one market, one borrower, an oracle one wallet can move
  vault 0xD6d4…48Ec holds 4,710,724 EURCV; 86 % lent against mGLOeuro at 77 % LLTV
  mGLOeuro NAV: 100,000 EUR, written by the EOA 0xa301…600c alone, inside a fixed band 90,000–110,000
  the only borrower 0xa122…E7c6 sits at LTV 0.6997
```

The three facts that make this vault fragile, read on-chain by the script:

1. **Concentration.** 86 % of the vault is lent in one market, against one collateral (mGLOeuro).
2. **One wallet sets the price.** The feed's value is written by a single EOA, the only holder of Midas's feed-admin role. It can change it in one transaction, with no delay. The feed accepts any value between 90,000 and 110,000 EUR. Going below 90,000 needs new code, installed through a 48 h timelock (Part 6).
3. **One borrower.** All the debt (3.68M EURCV) belongs to one address. It posted 52.58 mGLOeuro, worth 5.26M EUR at 100,000 each, so its LTV is 3.68 / 5.26 = **0.70**.

From these numbers:
- **Liquidatable** when the price falls below 100,000 × 0.70 / 0.77 ≈ **90,857 EUR (−9.1 %)**.
- **Bad debt** below debt × 1.074 / 52.58 ≈ **75,142 EUR (−24.9 %)**, when even the whole collateral, sold with the liquidator's bonus, no longer repays the debt.

## Part 3: the prediction, before anything happens

```
before anything happens: what would a markdown cost?
  if mGLOeuro were marked down 10 %:
    vault loss 0 EURCV (0.00% of 4,710,697)
    verdict given the incident: STAY: the collateral still covers the debt after the fall: no bad debt reaches the vault
```

- This is `riskdep analyze --vault … --shock token=mGLOeuro:0.10`: "what if the issuer marked mGLOeuro down 10 %?". It runs offline, from a recording of the vault (`fixtures/replay/incident-0xd6d4…/`), which is why it takes a second.
- **At −10 %:** the price is 90,000, below the 90,857 threshold, so the borrower becomes liquidatable. Its collateral is still worth more than its debt with the bonus (90,000 > 75,142), though. A liquidator repays the debt in full and keeps the difference, and the vault loses nothing.
- **Verdict STAY:** nothing reaches the depositors, so leaving would only cost the yield they give up.
- The total (4,710,697) differs by a few EURCV from the fork's 4,710,724 because the recording was made a few hundred blocks earlier; interest has accrued since.

```
  if mGLOeuro were marked down 30 %:
    vault loss 251,761 EURCV (5.34% of 4,710,697)
    verdict given the incident: STAY: leaving first saves only 382 (0.2% of the 250,399 loss): the depositor holds 99% of the vault, so the loss falls on it either way
```

- **At −30 %:** the price is 70,000, below the 75,142 bad-debt threshold. Liquidating all 52.58 mGLOeuro at 70,000 with the 7.4 % bonus repays about 3.43M of the 3.68M debt. The rest, **251,761 EURCV**, is bad debt, so the vault loses 5.34 % of its assets.
- **The depositor** is the largest one (`0x4F87…0545`), who holds 99.5 % of the vault: its share of the loss is 250,399.
- **Why STAY, even with a 250k loss?**
  - A depositor who leaves *before* the loss is written off avoids it, and the others take it. That only works if there are others: this depositor *is* almost the whole vault.
  - Also, at 91 % utilisation only ~8 % of the vault can be withdrawn at all.
  - Leaving first would save 382 EURCV, less than the yield it would give up. The loss lands on this depositor whatever it does.
- The script saves this −30 % prediction, to compare it at the end with what really happens on the fork.

```
  riskdep has finished reading the vault, its markets and who controls them:
```

The watch has finished starting up. Its three most important start-up findings follow.

## Part 4: what riskdep found before the crisis

```
riskdep ▸ INFO  Withdrawals cannot be gated: both exit gates are abdicated
riskdep ▸ WARN  mGLOeuro/EUR cannot report below 90,000 (-10.0%) without an upgrade through timelock 0xe3ee… (48 h)
riskdep ▸ INFO  1 timelock(s) control contracts your markets depend on; their queue is watched
```

- **Exit gates abdicated** (`ExitGate`). Vault V2 lets a curator install "gates" that can block withdrawals. Here the curator has given that power up for good, so no decision can lock depositors in. What can still stop an exit is liquidity: the money is lent out.
- **Feed band** (`FeedBand`). `riskdep` read the feed's limits (`minAnswer` 90,000, `maxAnswer` 110,000). The feed has no function to change them, so the oracle cannot show a loss larger than 10 % until new code is installed, and that code must pass through Midas's 48 h timelock. Until then, a real loss beyond 10 % stays invisible: the market prices the collateral at 90,000, and the shortfall is bad debt nobody sees.
- **Timelock watched.** `riskdep` found that timelock above the feed (owner of its proxy admin) and now watches its queue. A change is seen when it is *scheduled*, 48 h before it can land.

## Part 5: the issuer marks the NAV down 10 %

```
the issuer marks the NAV down 10 %: one transaction, no delay
  NAV now 90,000 EUR; borrower LTV 0.7774 against a 0.77 LLTV
riskdep ▸ WARN  Oracle of mGLOeuro/EURCV moved -10.0%
riskdep ▸ WARN  A 5% fall would liquidate 100% of mGLOeuro/EURCV …
riskdep ▸ WARN  Oracle of mGLOeuro/EURCV is -10.1% from the market price
```

- The script impersonates the feed-admin wallet (anvil can send a transaction from any address) and calls `setRoundData(90,000)`. One transaction, accepted at once.
- The borrower's LTV is now 77.7 %, above the 77 % LLTV: it can be liquidated.
- `riskdep` sees it on the next block:
  - the oracle moved −10 %;
  - the liquidation curve has become steep;
  - the oracle now differs from DefiLlama's market price, because the feed follows the issuer and not a market.

## Part 6: the real loss is 30 %, and the upgrade behind 48 h

```
the real loss is 30 %: the oracle cannot show it without an upgrade, behind 48 h
  upgrade of the feed scheduled on the Midas timelock: executable in 48 h — riskdep alerts now, not at execution
riskdep ▸ WARN  Scheduled on timelock 0xe3ee…: upgrade of mGLOeuro/EUR, executable in 48 h
  … 48 hours later
  new feed code installed; NAV now 70,000 EUR; borrower LTV 0.9995
riskdep ▸ CRITICAL  mGLOeuro/EUR … was upgraded
riskdep ▸ WARN      Executed on timelock 0xe3ee…: upgrade of mGLOeuro/EUR
riskdep ▸ CRITICAL  Unrealised bad debt in mGLOeuro/EURCV … 252,236 EURCV
```

Suppose the fund really lost 30 %. Midas cannot publish 70,000: the feed refuses anything below 90,000. Only new code can lift that floor.

1. **Scheduled.** The Midas proposer (a Safe) queues the upgrade on the timelock. `riskdep` raises a **warn at once**. **This is the depositor's window: 48 hours to reduce or leave before the new price applies.** Without watching the queue, the first sign would be the upgrade itself, too late.
2. **48 hours later.** The script moves the fork's clock forward 48 h (`evm_increaseTime`): no real waiting.
3. **Executed.** The upgrade lands (critical: the feed's code changed) and the admin sets 70,000. The demo implementation (`scripts/fork/src/MGloEuroFeedV2.sol`) is not Midas code. It stands for what Midas would install: the same interface with a wider band.
4. **Unrealised bad debt** (critical). At 70,000 the collateral no longer covers the debt. Nobody has liquidated yet, so the loss is not written off, but `riskdep` already counts it: 252,236 EURCV, and the depositor's share.

## Part 7: liquidation realises the bad debt

```
liquidating the rest realises the bad debt
  vault assets 4,711,456 → 4,458,542 EURCV: 252,914 lost by the depositors
  predicted in act 1 for a 30 % markdown: 251,761; observed: 252,914: the same, within rounding
riskdep ▸ CRITICAL  Bad debt in mGLOeuro/EURCV … 252,914 EURCV of bad debt realised
riskdep ▸ CRITICAL  Loss recorded by an adapter, not yet accrued …
```

- A liquidator (an address the script funds with EURCV) seizes all the remaining collateral. Morpho writes the uncovered debt off, so the vault's assets fall by 252,914 EURCV, and the share price falls with them.
- **Prediction against reality:** `riskdep` predicted 251,761 in Part 3, before anything happened; the fork lost 252,914. The 0.5 % gap is the interest the debt accrued during the 48 h time jump.
- The last alert says the loss is booked in the market but not yet in the vault's own total. The next deposit or withdrawal will apply it, so whoever moves first moves at the old price.

## The end

```
End — what riskdep said, by level
  5 critical
  13 warn
```

The watch is stopped and the fork deleted. The full log is in `out/demo/watch.log`, and the alerts as JSON in `out/demo/watch-0xd6d4….jsonl`. The same run, recorded once, replays offline with no fork:

```bash
uv run python -m riskdep watch --vault 0xD6d4b804014EF27836dBe9f8f6Bf6c71251548Ec --replay --record-as fork-belem
```

## What the demo proves

1. **Dependency discovery.** From the vault address alone, `riskdep` found the feed, the wallet that writes it, its fixed band, and the timelock that controls its code, two levels away from the vault.
2. **Impact.** It priced a 30 % markdown at 251,761 EURCV before it happened, and the fork confirmed it.
3. **Timing and decision.** It saw the upgrade 48 h before it could land, and it said STAY: for this depositor, leaving first cannot help.
4. **Real data.** Every number comes from mainnet's real state. Only the crisis itself is played, and only through roles the protocols really grant (issuer, timelock proposer, liquidator); no exploit is involved.
