# Data providers

Every external service the project calls, what it is used for, and what is known about its limits. All of them are public and need no API key. Keep this file current: any change that adds, removes or replaces a provider, endpoint or query updates it in the same commit (see `CLAUDE.md`).

## Contents

- [Summary](#summary)
- [Ethereum RPC](#ethereum-rpc)
- [Morpho API](#morpho-api)
- [Pendle API](#pendle-api)
- [DefiLlama](#defillama)
- [Scripts loaded by the HTML outputs](#scripts-loaded-by-the-html-outputs)
- [Configured but not used yet](#configured-but-not-used-yet)
- [Defined but unused](#defined-but-unused)
- [Trust model](#trust-model)
- [Changing a provider](#changing-a-provider)

## Summary

| Provider | Endpoint | Kind | Key | Role | Defined in |
|---|---|---|---|---|---|
| publicnode | `https://ethereum-rpc.publicnode.com` | Ethereum JSON-RPC (HTTP) | no | all on-chain data | `riskdep/sources.py` (`RPC`) |
| dRPC | `https://eth.drpc.org` | Ethereum JSON-RPC (HTTP) | no | cross-check only (block hash) | `riskdep/crosscheck.py` (`SECOND_RPCS`) |
| 1RPC | `https://1rpc.io/eth` | Ethereum JSON-RPC (HTTP) | no | cross-check fallback | `riskdep/crosscheck.py` (`SECOND_RPCS`) |
| Morpho | `https://blue-api.morpho.org/graphql` | GraphQL API | no | discovery: positions, borrowers, lenders, vault roles | `riskdep/sources.py` (`MORPHO`) |
| Pendle | `https://api-v2.pendle.finance/core` | REST API | no | PT markets, implied yield, swap quotes | `riskdep/sources.py` (`PENDLE`) |
| DefiLlama | `https://api.llama.fi` | REST API | no | protocol list, hack record | `riskdep/sources.py` (`LLAMA`) |
| DefiLlama Coins | `https://coins.llama.fi` | REST API | no | token prices, price history | `riskdep/sources.py` (`LLAMA_COINS`) |
| jsDelivr | `https://cdn.jsdelivr.net` | CDN (browser) | no | Mermaid in the `analyze` report | `riskdep/report.py` |
| cdnjs | `https://cdnjs.cloudflare.com` | CDN (browser) | no | Cytoscape.js in the graph page | `riskdep/graph.py` |

Every request to the data providers goes through the cached fetcher of `riskdep/sources.py`, except the CDN scripts, which the browser loads when a report is opened.

## Ethereum RPC

**publicnode, `https://ethereum-rpc.publicnode.com`**: the source of every on-chain value.

| Method | Used for | Code |
|---|---|---|
| `eth_blockNumber` | the chain head, for the watch loop and the cross-checks | `poller.py`, `watch.py`, `watch_user.py`, `crosscheck.py`, `cli.py` |
| `eth_call` (single and JSON-RPC batches) | contract reads at a fixed block: Morpho Blue markets and positions, Vault V2 state, adapters, oracles and feeds, token metadata, rate models | `sources.rpc_call`, `sources.rpc_batch` and every reader |
| `eth_getLogs` | the events of new blocks: vaults and adapters, Morpho Blue on the watched market ids, authorisations, admin events, mints | `poller.py` |
| `eth_getStorageAt` | proxy slots (EIP-1967, ZeppelinOS) of the admin surface | `admin.py` (via `sources.rpc_batch_methods`) |
| `eth_getCode` | minimal-proxy (EIP-1167) detection | `admin.py`, `discover.py`, `graph.py` |
| `eth_getBlockByNumber` | block hash for the cross-check | `crosscheck.py` |

**Limits measured on 2026-10-10:**
- **State history:** state is served only about 90 to 126 blocks back, so the tool reads at most 64 blocks back (`watch.state_window_blocks`).
- **Old log ranges** are refused ("Archive requests require a personal token"); the watch reports a gap.
- **At most 9 addresses per log filter**; 10 or more returns "Request blocked". The poller splits longer address lists (`poller.MAX_ADDRESSES`).
- **Intermittent "archive" refusals** on recent ranges: the same query alternates between success and refusal. The poller retries twice before treating the range as a gap.
- **Batches.** JSON-RPC batches of up to about 200 calls were accepted in every run. `market_risk` and `sources.rpc_batch_methods` split at 200 calls; `sources.rpc_batch` sends a reader's calls in one request (the largest today is the admin-surface read, about 140 calls for 47 contracts).

**Available but not used yet:** the WebSocket endpoint `wss://ethereum-rpc.publicnode.com` (`newHeads`, `logs`, `newPendingTransactions`, all verified) and `eth_simulateV1` (verified). See `docs/websocket-vs-polling.md`.

**Routing (`RISKDEP_RPC_URL`).** When this environment variable is set, `sources.Fetcher` sends the main RPC's requests to its value instead of publicnode, for example a local node, a proxy or a paid endpoint with its key. Requests stay cached under the publicnode URL, so snapshots and replays keep working and the key never reaches a file; an error names the public URL only. The cross-checks keep calling dRPC and 1RPC directly: routing the main RPC to one of them would make the block-hash check compare that node with itself.

**Load (measured 2026-10-10, live, 12 s polls).** `watch --vault` on Sentora RLUSD Main: 13 calls/s before D61, about 2 calls/s on batches with no event (15 `eth_call`s instead of 104, plus the log filters). `watch --user` on the demo borrower: 4.2 calls/s before, 1.7 after. `eth_getLogs` (one request per filter, address lists split by 9) is now the largest share of the polling load. A startup or 300-block refresh is a burst of 670 to 890 calls. publicnode does not document a rate limit.

**dRPC `https://eth.drpc.org`, then 1RPC `https://1rpc.io/eth`**: called only by `crosscheck.second_rpc`, which compares one block hash with the main RPC at start and every 300 blocks. Other keyless endpoints tried on 2026-10-10 did not answer: LlamaRPC, Cloudflare's Ethereum gateway, and Ankr (which requires a key).

## Morpho API

**`https://blue-api.morpho.org/graphql`**, GraphQL. Used to *find* things the chain cannot list cheaply; every amount used in a decision is then read on-chain.

| Query (root field) | Used for | Code |
|---|---|---|
| `userByAddress` | an address's Blue positions and Vault V2 deposits | `positions.py` |
| `marketPositions` | a market's borrowers (`borrowShares_gte`), its main suppliers (ordered by supply shares), the largest borrower of a market | `market_risk.py`, `borrower.py`, `discover.py` |
| `marketById`, `marketPosition` | the `analyze` position and its market | `discover.py` |
| `vaultV2ByAddress` | the largest depositor of a vault; its allocators and sentinels (graph); its total assets (cross-check) | `vault.py`, `graph.py`, `crosscheck.py` |

**Notes.** One page holds up to 1,000 items; `list_borrowers` pages with `skip`. Indexed data can lag the chain; the API-vs-chain cross-check warns beyond 0.5 %.

## Pendle API

**`https://api-v2.pendle.finance/core`**, REST.

| Path | Used for | Code |
|---|---|---|
| `/v1/1/markets/active`, `/v1/1/markets/inactive` | finding the Pendle market of a PT; its SY, underlying and expiry | `discover.py` (also called by `admin.py`, `graph.py`, `watch_user.py`) |
| `/v2/1/markets/{market}/data` | implied yield, PT discount, liquidity | `discover.py` |
| `/v2/sdk/1/markets/{market}/swap` | a real quote for selling PT collateral: price impact and fees of an exit or a de-lever | `discover.exit_quote` |

**Note.** The swap endpoint refuses quotes above 100M USD of input.

## DefiLlama

**`https://api.llama.fi`**, REST.

| Path | Used for | Code |
|---|---|---|
| `/protocols` | each protocol's size, category and listing date, for incident base rates | `sources.llama_protocols`, `priors.py` |
| `/hacks` | the hack record of the last 5 years, for incident base rates | `sources.llama_hacks`, `priors.py` |

**`https://coins.llama.fi`**, REST.

| Path | Used for | Code |
|---|---|---|
| `/prices/current/{chain:address,…}` | current token prices: PT holdings, and the independent price oracles are compared with | `sources.coin_prices`, `discover.py`, `admin.py` |
| `/chart/{chain:address}` | one year of daily prices: the worst drawdown of a yield token | `sources.coin_drawdown`, `discover.py` |

**Note.** Some tokens are not priced (no entry); the oracle comparison then reports "not checked" for that market.

## Scripts loaded by the HTML outputs

These are not data sources: the browser loads them when a report is opened, at a pinned version.

| Script | URL | Page |
|---|---|---|
| Mermaid 11.4.1 | `https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js` | `out/report.html` (`analyze`) |
| Cytoscape.js 3.30.2 | `https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js` | `out/graph.html`, `docs/graph-example.html` |

## Configured but not used yet

**Etherscan API V2, `https://api.etherscan.io/v2/api`** (`chainid=1`), key in `keys.ini` section `[etherscan]`. No code calls it yet; it is meant for step 3 of `NEXT_STEP.md` (verified sources and ABIs of the admin surface). Tested by hand on 2026-10-10: `module=contract&action=getsourcecode` returned the verified source of the demo oracle `0xF8b2…1b08` (an EIP-1167 clone, which Etherscan resolves to its implementation `0x9b46…de5b`, `MetaOracleDeviationTimelock` by Steakhouse Financial, solc 0.8.28). Documentation: `docs/external/docs.etherscan.io-api-reference-docs`. Free-tier limits are not measured yet.

## Defined but unused

| Constant | Endpoint | Status |
|---|---|---|
| `LLAMA_YIELDS` in `riskdep/sources.py` | `https://yields.llama.fi` | defined, never called; candidate for removal (`NEXT_STEP.md` step 10) |

## Trust model

- **The chain decides, the APIs find.** Positions, borrowers, lenders and roles found through an API are re-read on-chain before any amount is used.
- **Cross-checks** at start and every 300 blocks:
  - **second RPC:** the block hash from an independent RPC; a mismatch is a critical alert;
  - **Morpho API against the chain:** a gap beyond 0.5 % is a warn.

  A check that cannot run prints "not checked".
- **Single points of failure:** the main RPC (every on-chain value) and the Morpho API (discovery). If the Morpho API is down at start, `watch --user` cannot find positions; `--market <id>` lists borrows by hand.

## Changing a provider

- **Keys and secrets** live in `keys.ini` at the repository root, which is git-ignored and readable only by its owner (`chmod 600`). `keys.example.ini` is the committed template: same sections and names, no values. Copy it with `cp keys.example.ini keys.ini`. No provider called by the code today needs a key; the Etherscan key is filled in for step 3, the other sections are ready for next steps 1 to 6.

- **Endpoints** are constants: `RPC`, `MORPHO`, `PENDLE`, `LLAMA`, `LLAMA_COINS` in `riskdep/sources.py`, `SECOND_RPCS` in `riskdep/crosscheck.py`, and the script URLs in `riskdep/report.py` and `riskdep/graph.py`.
- **A paid RPC** (archive and WebSocket access, needed by next steps 5 and 6) is set with `RISKDEP_RPC_URL`, its key included; keep the URL in `keys.ini` (section `[rpc]`, git-ignored) and export it from there. It is never committed, and the cache keys keep the publicnode URL.
- **After any change:**
  - re-record the replays (`watch --blocks 1000 --record`, `watch --user <address> --blocks 300 --record`), because cached requests are keyed by their URL and body;
  - run the tests;
  - update this file in the same commit.
