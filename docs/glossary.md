# Glossary

Plain-language definitions of the terms used in this repository's reports, alerts and documents, grouped by theme. Each definition says how the term is used here; where a number is given, it is the value the tool uses.

## Contents

- [Morpho Blue: markets and borrowing](#morpho-blue-markets-and-borrowing)
- [Morpho Vault V2: vaults and their governance](#morpho-vault-v2-vaults-and-their-governance)
- [Contract admin and upgrades](#contract-admin-and-upgrades)
- [Pendle and yield sources](#pendle-and-yield-sources)
- [Risk measures](#risk-measures)
- [The dependency graph](#the-dependency-graph)
- [Blockchain data and the watcher](#blockchain-data-and-the-watcher)

## Morpho Blue: markets and borrowing

| Term | Definition |
|------|------------|
| **Morpho Blue** | Morpho's lending protocol: one contract holding many isolated lending markets. |
| **Market** | One lending pool in Morpho Blue, defined by five parameters: the loan token, the collateral token, the oracle, the interest-rate model and the LLTV. Its id is the hash of those five parameters. |
| **Supplier / lender** | An account that deposits the loan token into a market and earns interest from borrowers. |
| **Borrower** | An account that posts collateral in a market and borrows its loan token against it. |
| **Collateral** | The token a borrower posts as security; it is seized if the borrower is liquidated. |
| **Oracle** | The contract that tells a market the price of its collateral in the loan token. Liquidations follow its price, not the market price. |
| **Price feed** | A source an oracle reads, for example a Chainlink `ETH / USD` feed. One oracle can combine several feeds. |
| **LLTV** | Liquidation loan-to-value: the share of the collateral's oracle value a borrower's debt may reach before liquidation, for example 86 % or 91.5 %. |
| **Health factor (HF)** | Collateral × oracle price × LLTV ÷ debt. Above 1 the position is safe; at 1 or below anyone can liquidate it. |
| **Liquidation distance** | The fall in the oracle price that would bring the health factor to 1: 1 − 1/HF. An HF of 1.05 means a 4.8 % fall liquidates. |
| **Liquidation** | A third party repays part or all of a borrower's debt and receives the borrower's collateral in exchange, with a bonus. |
| **LIF (liquidation incentive factor)** | The liquidator's bonus, set by the LLTV: min(1.15, 1 / (0.3 × LLTV + 0.7)). At LLTV 91.5 %, a liquidator repaying 100 receives 102.6 of collateral. |
| **Bad debt** | Debt left after a liquidation when the collateral did not cover it. Blue deducts it from the market's supply, so the lenders lose it. |
| **Unrealised bad debt** | The uncovered debt of a borrower who is already underwater but not yet liquidated. Blue records nothing until the liquidation. |
| **Liquidation curve** | For a market, the share of its debt that would become liquidatable after an oracle fall of 2, 5, 10 or 20 %. A steep curve means many positions would be liquidated, and their collateral sold, at once. |
| **Utilisation** | Borrows ÷ supply in a market. At 100 % no lender can withdraw until borrowers repay. |
| **Interest-rate model (IRM), AdaptiveCurveIRM** | The contract that sets a market's borrow rate from its utilisation. Morpho's AdaptiveCurveIRM targets 90 % utilisation; at 100 % the rate is 4 × the rate at target, and that target rate adapts over time. |
| **Shares and assets** | Blue counts supply and debt in shares, converted to token amounts (assets) with the market's totals and small virtual amounts that protect against rounding attacks. |
| **Authorisation** | Permission a Blue account gives another address to borrow, withdraw or withdraw collateral on its behalf. Anyone may repay or add collateral for anyone without it. |
| **Bundle** | A Morpho contract that performs a fixed sequence of operations on the caller's own position in one transaction, for example repay-and-withdraw-collateral or migrating a borrow to another market. |

## Morpho Vault V2: vaults and their governance

| Term | Definition |
|------|------------|
| **ERC-4626** | The Ethereum standard for tokenised vaults: you deposit a token and receive vault shares; the shares are redeemable for a growing amount of the token. |
| **Vault V2** | Morpho's ERC-4626 vault: it takes deposits of one token and lends them across Blue markets (or other targets) through adapters, under caps and timelocks. |
| **Vault V1 (MetaMorpho)** | The previous generation of Morpho vaults, which lend directly to Blue markets through supply and withdraw queues. |
| **Adapter** | The contract through which a Vault V2 places its money. `MorphoMarketV1AdapterV2` supplies to Blue markets; in a market, the supplier you see is the adapter, not the vault. |
| **Share price** | The vault's total assets ÷ its shares: what one share is worth. It rises with interest and falls with losses. |
| **`totalAssets()` and `_totalAssets`** | `totalAssets()` is the vault's value computed as if interest were accrued now; `_totalAssets` is the stored value, updated only when the vault accrues. A gap means a loss was recorded by an adapter but not yet accrued. |
| **Idle assets** | Tokens the vault holds directly, not lent out. A plain withdrawal is paid from them first. |
| **Liquidity adapter / liquidity market** | The adapter, and for a market adapter the single market, that plain deposits and withdrawals go through. |
| **Plain withdrawal capacity** | What a normal withdraw or redeem can pay now: idle assets plus what the liquidity market can return. |
| **`forceDeallocate`** | A call anyone can make to pull a vault's assets back from an adapter, paying the adapter's penalty (at most 2 %), typically to exit beyond the plain capacity. |
| **In-kind redemption** | An exit that hands the depositor the vault's market positions instead of tokens, used when the markets' liquidity is borrowed out. |
| **Owner** | The vault role that appoints the curator and the sentinels; it cannot move funds. |
| **Curator** | The vault role that changes its configuration (adapters, caps, fees, gates, timelocks) through timelocked submissions. |
| **Allocator** | The vault role that moves money between adapters and markets within the caps; it also sets the liquidity adapter and the maximum rate, without a timelock. |
| **Sentinel** | A vault role that can only reduce risk: lower caps, deallocate and cancel pending changes. |
| **Cap** | The maximum the vault may allocate under an identifier: one per adapter, one per collateral token and one per market, as an absolute amount or a share of the vault. |
| **Timelock** | The delay between a curator submitting a change and the earliest time it can be executed, set per function. It is a depositor's warning period. |
| **Submit / Accept / Revoke** | The three steps of a timelocked change: announced, executed, or cancelled. |
| **Abdication** | The permanent disabling of a vault function: an abdicated setter can never be called again. |
| **Gate** | An optional contract that decides who may send or receive the vault's shares or tokens; an exit gate can refuse a withdrawal. |
| **Performance fee / management fee** | Fees the vault takes on interest (at most 50 %) and on assets (at most 5 % a year). |
| **maxRate** | The fastest the vault's total assets may grow (at most 200 % a year). It caps gains, not losses. |
| **Main lender** | In this tool, a supplier holding at least 5 % of a market's supply. A dominant main lender's departure raises the market's rate. |

## Contract admin and upgrades

| Term | Definition |
|------|------------|
| **Admin surface** | The contracts a market depends on beyond Morpho (oracle, feeds, tokens, Pendle SY) and the people who can change them. |
| **Proxy / upgradeable contract** | A contract that forwards every call to an implementation contract whose address can be changed, so its code can be replaced without changing its address. |
| **EIP-1967** | The standard that fixes where a proxy stores its implementation, admin and beacon addresses, so they can be read from outside. USDC's older proxy uses the equivalent ZeppelinOS slots. |
| **UUPS proxy** | A proxy whose upgrade function lives in the implementation code; it has no separate admin slot. |
| **Beacon** | A contract that holds the implementation address for many proxies at once; upgrading the beacon upgrades all of them. |
| **Minimal proxy (EIP-1167 clone)** | A tiny contract that forwards to a fixed implementation; it cannot be upgraded. |
| **Owner / roles** | The account allowed to call a contract's restricted functions (`Ownable`), or the accounts holding named permissions such as minter or pauser (`AccessControl`). |
| **Chainlink aggregator** | The contract a Chainlink price-feed proxy reads from; its owner can switch the proxy to a new aggregator. |
| **Pause** | A switch that suspends a token's transfers or a contract's operations. |

## Pendle and yield sources

| Term | Definition |
|------|------------|
| **Yield source / issuer** | The protocol behind a yield-bearing token, for example Ethena for sUSDe or Lido for wstETH. |
| **SY (standardised yield)** | Pendle's wrapper around a yield-bearing token. |
| **PT (principal token)** | Pendle's token that redeems for one unit of the underlying at maturity; before maturity it trades at a discount. |
| **Implied APY** | The fixed yield a PT holder earns by holding to maturity, implied by its discount. |
| **PT discount / par** | How far below its redemption value (par) a PT trades. Near maturity the discount approaches zero. |
| **Depeg** | A token trading below the value it is meant to track, for example a synthetic dollar below 1. |

## Risk measures

| Term | Definition |
|------|------------|
| **Layer** | One system a position depends on: the chain, the yield source, the Pendle market, the lending market, the oracle. |
| **Severity** | The fraction of value lost when a layer fails, drawn from a Beta distribution set in `registry.json`. |
| **Base rate** | How often protocols of a given size and category were exploited in the last five years, from DefiLlama's hack record. |
| **Monte Carlo** | Running many simulated months (20,000 here) in which failures happen at random, to estimate the distribution of losses. |
| **Expected loss** | The average loss over the simulated months. |
| **VaR 99 % / CVaR 99 %** | The loss exceeded in 1 % of months, and the average loss of those worst 1 % of months. |
| **Carry** | What the position earns over the horizon: the collateral's yield minus the interest on the debt. |
| **Exit cost** | What leaving would cost now: price impact and fees of selling the collateral, plus gas. |
| **Price impact** | How much worse a large sale's price is than the current price, because it consumes the pool's liquidity. |
| **Drain threshold (d\*)** | The discount of a collateral below its oracle price from which borrowing against it, with no intent to repay, pays: d\* = 1 − LLTV / (1 + buying cost). Past it, a market's free liquidity can be borrowed in one block (`docs/drain-threshold.md`). |
| **Public Allocator** | A Morpho contract that lets anyone move a vault's assets between its markets, within caps its allocators set. Useful for borrowers in normal times; in a drain, it can bring the vault's healthy liquidity within reach. |
| **Run** | Depositors withdrawing all at once because they expect others to, while the vault can pay only what it has not lent. The first out are paid at par; the rest wait, and carry any loss not yet written off. |
| **Queue position** | In a run, the other depositors' assets that leave before you. What you recover at par and what you lose depend on it (`docs/exit-queue.md`). |
| **Stuck** | The part of a vault position that cannot leave now, because the vault's liquidity is exhausted or lent out; it comes back only as borrowers repay or are liquidated. |
| **STAY / REDUCE / EXIT** | The verdict of `analyze`: exit when the expected loss exceeds carry plus exit cost; reduce when the carry does not cover the expected loss, the tail is too heavy, or liquidation is closer than a stress drop; stay otherwise. |

## The dependency graph

| Term | Definition |
|------|------------|
| **Actor** | A node whose capital is at stake: an address with positions, a Vault V2, a Vault V1. |
| **Pool** | A node where liquidity sits and is priced: a Blue market, a Pendle pool. |
| **Asset** | A token node; a vault share appears only when another protocol reuses it. |
| **Admin** | A node that decides for a vault without its own capital at stake: owner, curator, allocator, sentinel. |
| **External** | An off-chain dependency of a yield source, such as custodians or exchanges, listed in `registry.json`. |
| **Edge** | A dependency between two nodes, derived from an on-chain attribute (a market's oracle, a vault's adapter), with the amount it carries where one exists. |

## Blockchain data and the watcher

| Term | Definition |
|------|------------|
| **Block** | A batch of Ethereum transactions, about one every 12 seconds. |
| **Event / log** | A record a contract emits when something happens, for example a `Liquidate`. The watcher reads these. |
| **Topic** | An indexed field of an event, which a node can filter on. The first topic identifies the event; for Blue events, the second is the market id. |
| **`eth_getLogs` / `eth_call`** | The node requests that return the events of a block range, and the result of reading a contract. |
| **JSON-RPC batch** | Many requests sent to the node in one message, all answered at the same block. |
| **RPC (node endpoint)** | The service the tool queries for blockchain data. It uses free, keyless public endpoints. |
| **Confirmations** | How many blocks the watcher stays behind the newest one (2), so that a short reorganisation is never analysed. |
| **Reorganisation (reorg)** | The replacement of recent blocks by a different version of the chain. |
| **Cursor** | The last block whose alerts were written, saved to a file so a restart resumes there. |
| **Archive data** | Old state or logs. The free endpoint served state only about 90 to 126 blocks back in our measurements and refuses older log ranges; the tool reads state at most 64 blocks back to stay safe. |
| **Replay** | A recorded block range re-run offline from saved responses, used by the tests. |
| **Cross-check** | Comparing two sources of the same fact: the block hash from two independent nodes, or the Morpho API against the chain. |
