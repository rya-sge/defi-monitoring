# riskdep

**Know what your DeFi position depends on, and when to get out.**

## The problem

A deposit in a DeFi vault looks like one position, but it rests on a stack the depositor never sees: the lending markets the vault supplies, the collateral they accept, the issuers behind that collateral, the oracles that price it, the feeds those oracles read, and the keys that can change any of them. When one layer fails, the loss travels up the stack.

How fast it arrives depends on the oracle. If the oracle follows a market price, liquidations start within minutes. If it reports the issuer's own NAV, nothing shows until the issuer publishes a lower number, and then the whole loss lands in one transaction.

## What riskdep does

riskdep is a risk system for positions on Ethereum, centred on Morpho. Starting from a vault or an address, it answers four questions in sequence:

1. **What does the position depend on?** A dependency graph, discovered from public data: vaults, markets, borrowers, collateral, issuers, oracles, feeds, admins and sibling markets.
2. **What would a failure cost?** A named incident, such as a markdown, a depeg, a feed failure or a borrower default, is propagated through the graph by explicit rules: liquidations, bad debt, who bears it, and when.
3. **Is it worth acting on?** A STAY / REDUCE / EXIT verdict with its reason, the cost of leaving against what it saves, and the probability above which leaving pays.
4. **Is it happening now?** A block-by-block watch alerts on what precedes a loss, such as an oracle upgrade scheduled behind a timelock, not only on the loss itself.

## How it is built

- **Public data only.** The core runs on keyless sources: a public Ethereum RPC, the Morpho, Pendle and DefiLlama APIs, and Pharos for issuer grades. Optional API keys add more: Etherscan for verified oracle sources, Alchemy for archive reads at a past block, and 0x or 1inch for exit quotes.
- **Rules, not constants.** Every threshold, prior and propagation rule sits in one registry with its stated basis, so every number can be traced.
- **Reproducible.** Every run can be replayed offline from recorded mainnet responses, so a figure can be recomputed on any later day.
- **Interfaces.** A Python CLI (`analyze`, `watch`, `graph`, `shock`), an HTTP API with a browser interface, and alerts to Telegram.

## On real data

Applied to a live book of seven curated Morpho vaults on Ethereum (about 99 million USD), riskdep finds that 98 % of the book lends against tokens from young issuers, priced almost entirely by the issuers' own reports. A 30 % markdown of one issuer's token (Huma's PST) costs the book 5.2 million USD across two vaults, plus about 5.1 million in sibling markets outside the book, and the tool names the vault to leave first, the one where leaving pays above a 6.6 % chance.


