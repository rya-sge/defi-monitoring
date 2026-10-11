# riskdep

**Know what your DeFi position depends on, and when to get out.**

## The problem

A deposit in a DeFi vault looks like one position, but it rests on a stack the depositor never sees: the lending markets the vault supplies, the collateral they accept, the issuers behind that collateral, the oracles that price it, the feeds those oracles read, and the keys that can change any of them. When one layer fails, the loss travels up the stack, and how fast it arrives depends on how each layer is built. An oracle that follows a market price liquidates within minutes. One that reports the issuer's own NAV shows nothing until the issuer publishes a lower number, and then the whole loss lands in one transaction.

## What riskdep does

riskdep is a risk system for positions on Ethereum, centred on Morpho. Starting from a vault or an address, it answers four questions in sequence:

| Question | Answer |
|---|---|
| What does the position depend on? | A dependency graph, discovered from public data: vaults, markets, borrowers, collateral, issuers, oracles, feeds, admins, sibling markets |
| What would a failure cost? | A named incident (a markdown, a depeg, a feed failure, a borrower default) propagated through the graph by explicit rules: liquidations, bad debt, who bears it, and when |
| Is it worth acting on? | A STAY / REDUCE / EXIT verdict with its reason, the cost of leaving against what it saves, and the probability above which leaving pays |
| Is it happening now? | A block-by-block watch that alerts on what precedes a loss, such as an oracle upgrade scheduled behind a timelock, not only on the loss itself |

## How it is built

- **Public data only.** Ethereum RPC, the Morpho, Pendle and DefiLlama APIs, Pharos for issuer grades; all keyless.
- **Rules, not constants.** Every threshold, prior and propagation rule sits in one registry with its stated basis, so every number can be traced.
- **Reproducible.** Every run can be replayed offline from recorded mainnet responses, so a figure can be recomputed on any later day.
- **Interfaces.** A Python CLI (`analyze`, `watch`, `graph`, `shock`), an HTTP API with a browser interface, and alerts to Telegram.

## On real data

Applied to the seven Morpho vaults RockawayX curates on Ethereum (about 99 million USD), riskdep finds that 98 % of the book lends against tokens from young issuers, priced almost entirely by the issuers' own reports. A 30 % markdown of one issuer's token (Huma's PST) costs the book 5.2 million USD across two vaults, plus about 5.1 million in sibling markets outside the book, and the tool names the vault to leave first: the Confidential RWA vault, where leaving pays above a 6.6 % chance.

Built for the DeFi Risk Dependency Challenge (Belem Capital, EPFL Hackathon 2026). Full method in [`docs/whitepaper.md`](docs/whitepaper.md).
