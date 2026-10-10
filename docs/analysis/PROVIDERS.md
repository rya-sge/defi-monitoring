# Data providers

Every external service the project calls, what it is used for, and what is known about its limits. All of them are public; only Etherscan needs an API key, and the tool runs without it (the check then reads "not checked"). Keep this file current: any change that adds, removes or replaces a provider, endpoint or query updates it in the same commit (see `CLAUDE.md`).

## Contents

- [Summary](#summary)
- [Ethereum RPC](#ethereum-rpc)
- [eRPC, optional local proxy](#erpc-optional-local-proxy)
- [Morpho API](#morpho-api)
- [Pendle API](#pendle-api)
- [DefiLlama](#defillama)
- [Etherscan](#etherscan)
- [Pharos](#pharos)
- [Scripts loaded by the HTML outputs](#scripts-loaded-by-the-html-outputs)
- [Defined but unused](#defined-but-unused)
- [Trust model](#trust-model)
- [Changing a provider](#changing-a-provider)

## Summary

| Provider | Endpoint | Kind | Key | Role | Defined in |
|---|---|---|---|---|---|
| publicnode | `https://ethereum-rpc.publicnode.com` | Ethereum JSON-RPC (HTTP) | no | all on-chain data | `riskdep/sources.py` (`RPC`) |
| dRPC | `https://eth.drpc.org` | Ethereum JSON-RPC (HTTP) | no | cross-check only (block hash) | `riskdep/crosscheck.py` (`SECOND_RPCS`) |
| 1RPC | `https://1rpc.io/eth` | Ethereum JSON-RPC (HTTP) | no | cross-check fallback; answers 410 "discontinued" since at least 2026-10-10 | `riskdep/crosscheck.py` (`SECOND_RPCS`) |
| eRPC (optional) | `http://127.0.0.1:4000/main/evm/1`, run locally | RPC proxy over 6 free endpoints | no | the main RPC's requests, when `RISKDEP_RPC_URL` points at it | `erpc.yaml`, `docs/erpc.md` |
| Morpho | `https://blue-api.morpho.org/graphql` | GraphQL API | no | discovery: positions, borrowers, lenders, vault roles | `riskdep/sources.py` (`MORPHO`) |
| Pendle | `https://api-v2.pendle.finance/core` | REST API | no | PT markets, implied yield, swap quotes | `riskdep/sources.py` (`PENDLE`) |
| DefiLlama | `https://api.llama.fi` | REST API | no | protocol list, hack record | `riskdep/sources.py` (`LLAMA`) |
| DefiLlama Coins | `https://coins.llama.fi` | REST API | no | token prices, price history | `riskdep/sources.py` (`LLAMA_COINS`) |
| Pharos | `https://api.pharos.watch` | REST API | no | issuer grades, off-chain backing, common-mode groups of stablecoins (optional) | `riskdep/pharos.py` (`URL`) |
| Etherscan | `https://api.etherscan.io/v2/api` | REST API | yes, `keys.ini` `[etherscan]` | whether an oracle's source is verified; an unclassified oracle input's contract name | `riskdep/sources.py` (`ETHERSCAN`) |
| jsDelivr | `https://cdn.jsdelivr.net` | CDN (browser) | no | Mermaid in the `analyze` report | `riskdep/report.py` |
| cdnjs | `https://cdnjs.cloudflare.com` | CDN (browser) | no | Cytoscape.js in the graph page | `riskdep/graph.py` |

Every request to the data providers goes through the cached fetcher of `riskdep/sources.py`, except the CDN scripts, which the browser loads when a report is opened.

## Ethereum RPC

**publicnode, `https://ethereum-rpc.publicnode.com`**: the source of every on-chain value.

| Method | Used for | Code |
|---|---|---|
| `eth_blockNumber` | the chain head, for the watch loop and the cross-checks | `poller.py`, `watch.py`, `watch_user.py`, `crosscheck.py`, `cli.py` |
| `eth_call` (single and JSON-RPC batches) | contract reads at a fixed block: Morpho Blue markets and positions, Vault V2 state, adapters, oracles and feeds, token metadata, rate models, the Vault V2 Public Allocator's settings (`0x00b8…1e27`); for the oracle class, each input's `latestRoundData`, the last 24 `getRoundData`, `FEED_1`/`FEED_2`/`innerOracle`, `twapDuration`, `baseDiscountPerYear`, and, for `graph` only and in a call of its own, `market()` of an input with a `twapDuration` (the Pendle pool it reads); for sibling markets, `asset()` of every candidate collateral | `sources.rpc_call`, `sources.rpc_batch` and every reader |
| `eth_getLogs` | the events of new blocks: vaults and adapters, Morpho Blue on the watched market ids, authorisations, admin events, mints | `poller.py` |
| `eth_getStorageAt` | proxy slots (EIP-1967, ZeppelinOS) of the admin surface | `admin.py` (via `sources.rpc_batch_methods`) |
| `eth_getCode` | minimal-proxy (EIP-1167) detection; whether a vault holder is a contract or a wallet (EIP-7702 delegations count as wallets) | `admin.py`, `discover.py`, `graph.py`, `exit_queue.py` |
| `eth_getBlockByNumber` | block hash for the cross-check | `crosscheck.py` |

**Limits measured on 2026-10-10:**
- **State history:** state is served only about 90 to 126 blocks back, so the tool reads at most 64 blocks back (`watch.state_window_blocks`).
- **Old log ranges** are refused ("Archive requests require a personal token"); the watch reports a gap.
- **At most 9 addresses per log filter**; 10 or more returns "Request blocked". The poller splits longer address lists (`poller.MAX_ADDRESSES`).
- **Intermittent "archive" refusals** on recent ranges: the same query alternates between success and refusal. The poller retries twice before treating the range as a gap.
- **Rate limit.** A burst gets HTTP 429 with a `-32005 Rate limit exceeded` error on every item of the batch: 15 of 36 parallel 60-call batches on 2026-10-10. A local eRPC whose upstreams are all busy answers HTTP 200 with the same kind of error per item. `sources.Fetcher` treats both alike (a 429, or a rate-limit message in any item, `sources._throttled`): it waits 2, 4 … 12 s and resends, up to 6 times (`THROTTLE_RETRIES`), then fails the request, and never caches such an answer. Before this, the body was passed on and every call read as reverted: a long `graph` run left 36 of 80 oracles `not classified` and could have recorded the errors. The fix for speed is eRPC, below.
- **Batches.** JSON-RPC batches of up to about 200 calls were accepted in every run. `market_risk` and `sources.rpc_batch_methods` split at 200 calls; `sources.rpc_batch` sends a reader's calls in one request (the largest today is the admin-surface read, about 140 calls for 47 contracts).

**Available but not used yet:** the WebSocket endpoint `wss://ethereum-rpc.publicnode.com` (`newHeads`, `logs`, `newPendingTransactions`, all verified) and `eth_simulateV1` (verified). See `docs/websocket-vs-polling.md`.

**Routing (`RISKDEP_RPC_URL`).** When this environment variable is set, `sources.Fetcher` sends the main RPC's requests to its value instead of publicnode, for example a local node, a proxy or a paid endpoint with its key. Requests stay cached under the publicnode URL, so snapshots and replays keep working and the key never reaches a file; an error names the public URL only, says the request went through `RISKDEP_RPC_URL`, and keeps only the kind of failure (`ConnectionError`), since `requests` prints the routed host and path apart, where a key could sit. The cross-checks keep calling dRPC and 1RPC directly: routing the main RPC to one of them would make the block-hash check compare that node with itself.

**Load (measured 2026-10-10, live, 12 s polls).** `watch --vault` on Sentora RLUSD Main: 13 calls/s before D61, about 2 calls/s on batches with no event (15 `eth_call`s instead of 104, plus the log filters). `watch --user` on the demo borrower: 4.2 calls/s before, 1.7 after. `eth_getLogs` (one request per filter, address lists split by 9) is now the largest share of the polling load. A startup or 300-block refresh is a burst of 670 to 890 calls. publicnode does not document a rate limit.

**dRPC `https://eth.drpc.org`, then 1RPC `https://1rpc.io/eth`**: called only by `crosscheck.second_rpc`, which compares one block hash with the main RPC at start and every 300 blocks. Other keyless endpoints tried on 2026-10-10 did not answer: LlamaRPC, Cloudflare's Ethereum gateway, and Ankr (which requires a key). **1RPC answers 410 "This endpoint has been discontinued"** (probe 2026-10-10): the fallback is dead, so when dRPC fails the check reads "not checked". A replacement must stay out of `erpc.yaml`'s upstreams.

## eRPC, optional local proxy

**`http://127.0.0.1:4000/main/evm/1`**, [eRPC](https://github.com/erpc/erpc) 0.3.0 run by the user with the committed `erpc.yaml` (setup: `docs/erpc.md`). `RISKDEP_RPC_URL` sends the main RPC's requests to it; nothing is sent there otherwise. It spreads them over the upstreams below, retries a refused call on another upstream (4 attempts), and caches answers in memory (finalized blocks without expiry, recent blocks for 30 s). No rate budget is configured: in 0.3.0 a spent budget rejects calls with no queue (`waitTime` is ignored), which turned one 200-call batch into rate-limit errors in the first test.

| Upstream | Endpoint | Batches | Probe 2026-10-10 (30-call `eth_call` batch 60 blocks back, `eth_getLogs`, `eth_getStorageAt`) |
|---|---|---|---|
| publicnode | `https://ethereum-rpc.publicnode.com` | up to 50 | all answered |
| Blast | `https://eth-mainnet.public.blastapi.io` | up to 50 | all answered |
| MEV Blocker | `https://rpc.mevblocker.io` | up to 50 | all answered |
| blockrazor | `https://eth.blockrazor.xyz` | up to 10 | 20 of 30 in a batch, then "too many requests"; logs and storage answered; pruned history |
| Nodies | `https://eth-pokt.nodies.app` | up to 10 | "maximum allowed is 10 requests per batch"; logs and storage answered |
| Tenderly gateway | `https://gateway.tenderly.co/public/mainnet` | single calls | batch throttled; logs and storage answered |

**Left out on purpose:** dRPC (the cross-check's independent node; its free plan also refuses batches above 3 calls), 1RPC (discontinued). **Tried and rejected:** LlamaRPC, BlockPI, OmniaTech, MeowRPC (no JSON answer), payload.de and SubQuery (unreachable), Lava (discontinued), OnFinality and merkle.io (throttled at once), ZAN (`eth_getLogs` needs an account), Ankr (key required), Cloudflare (batches of 10, `eth_getLogs` and `eth_getStorageAt` answer "Internal error"), Flashbots (refuses 30-call batches and recent log ranges).

**Measured 2026-10-10:** `graph --vault 0xE018…1965` (RockawayX USDC Yield) took 43 s direct and 20 s through eRPC, with the same graph (74 nodes, 106 edges, same oracle classes). `graph --example` took 8 to 12 min direct (65 siblings) and 178 s through eRPC with the $1M TVL floor (52 siblings). eRPC's log then shows upstream throttling it routes around, for example Tenderly's 20-call limit.

## Morpho API

**`https://blue-api.morpho.org/graphql`**, GraphQL. Used to *find* things the chain cannot list cheaply; every amount used in a decision is then read on-chain.

| Query (root field) | Used for | Code |
|---|---|---|
| `userByAddress` | an address's Blue positions and Vault V2 deposits | `positions.py` |
| `marketPositions` | a market's borrowers (`borrowShares_gte`), its main suppliers (ordered by supply shares), the largest borrower of a market | `market_risk.py`, `borrower.py`, `discover.py` |
| `marketById`, `marketPosition` | the `analyze` position and its market | `discover.py` |
| `vaultV2ByAddress` | the largest depositor of a vault; its holders, first 100 by size, for the exit queue; its allocators and sentinels (graph); its total assets (cross-check) | `vault.py`, `exit_queue.py`, `graph.py`, `crosscheck.py` |
| `markets` | every Ethereum Blue market with at least `graph.sibling_min_tvl_usd` supplied (its TVL, `supplyAssetsUsd_gte`): collateral, loan token, oracle and its base feeds and vault, borrow in USD; pages of 500 (136 markets at $1M on 2026-10-10) | `siblings.py` |

**Notes.** One page holds up to 1,000 items; `list_borrowers` pages with `skip`. Indexed data can lag the chain; the API-vs-chain cross-check warns beyond 0.5 %.

## Pendle API

**`https://api-v2.pendle.finance/core`**, REST.

| Path | Used for | Code |
|---|---|---|
| `/v1/1/markets/active`, `/v1/1/markets/inactive` | finding the Pendle market of a PT; its SY, underlying and expiry; the underlying of every PT among the sibling candidates; the pool's liquidity and implied yield (`details`), the squeeze depth and PT floor of the shock engine | `discover.py` (also called by `admin.py`, `graph.py`, `watch_user.py`), `siblings.py` |
| `/v2/1/markets/{market}/data` | implied yield, PT discount, liquidity | `discover.py` |
| `/v2/sdk/1/markets/{market}/swap` | a real quote for selling PT collateral: price impact and fees of an exit or a de-lever; for `graph`, two ladders per PT at nine sizes (5 % to 5× the pool's liquidity): PT → underlying without the aggregator, PT → loan token with it, the shock engine's sale-impact curves (about 18 requests per PT; a refusal, MarketProportionTooHigh, ends a ladder) | `discover.exit_quote`, `discover.quote_ladder` |

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
| `/prices/current/{chain:address,…}` | current token prices: PT holdings, and the independent price oracles are compared with (oracle divergence and the drain threshold, re-read at most every 25 blocks; a vault asset's USD price in a book of vaults) | `sources.coin_prices`, `discover.py`, `admin.py` |
| `/chart/{chain:address}` | one year of daily prices: the worst drawdown of a yield token | `sources.coin_drawdown`, `discover.py` |

**Note.** Some tokens are not priced (no entry); the oracle comparison then reports "not checked" for that market.

## Etherscan

**`https://api.etherscan.io/v2/api`** (API V2, `chainid=1`), REST. Key: `keys.ini`, section `[etherscan]`, `api_key`.

| Query | Used for | Code |
|---|---|---|
| `module=contract&action=getsourcecode&address=…` | whether the code behind the `analyze` position's oracle is verified: the implementation of an EIP-1167 clone, or of a proxy Etherscan recognises. A verified oracle drops the ×2 `oracle.unverified_factor` (D68) | `sources.contract_source`, `discover.oracle_verified` |
| same | the verified contract name of an oracle input that no structural or history rule classifies, matched against `graph.oracle_patterns` (D83); asked only for those inputs | `oracle_class._contract_name` |

**Notes.**
- **The key never leaves the request.** It is added to the outgoing URL only (`Fetcher.get_json(..., secret=…)`): cache keys, cached files and error messages carry the URL without it.
- **Only a slim answer is cached** (`verified`, `name`, `proxy`, `implementation`), not the source code; a refusal (`status` 0: bad key, rate limit) is never cached.
- **Without a key** and with no cached answer, verification is "not checked" and the ×2 applies, as before; an oracle input that only its name would classify stays "not classified" (on RockawayX USDC Yield: the `LossAdjustedPTFeed` of PT-siUSD-7JAN2027/USDC).
- The free tier's rate limit is not measured and not documented in the local copy of the docs; `analyze` makes one or two calls per run.
- Documentation: `docs/external/docs.etherscan.io-api-reference-docs`.

## Pharos

**`https://api.pharos.watch`**, REST, keyless (the other endpoints need a key in the `X-API-Key` header; not used). Optional: a failure prints "Pharos: not checked". How it is used: `docs/risk-assessment/outside-providers.md`.

| Path | Used for | Code |
|---|---|---|
| `/api/dependency-graph/v1` | each coin's Safety Score and grade, what backs it (wrapper or reserve share, with weights), its common-mode groups; slimmed to about 170 KB before caching | `pharos.load`, `vault_incident.py`, `graph.annotate_pharos` |

**Recording.** `fixtures/replay/pharos/`, one response, re-read by `--record` or `--refresh` and read without saving by `--live`. **Limits.** No published rate limit for the keyless endpoints; no SLA (run by one person, best effort). Methodology 10.16, model v9 when recorded.

## Scripts loaded by the HTML outputs

These are not data sources: the browser loads them when a report is opened, at a pinned version.

| Script | URL | Page |
|---|---|---|
| Mermaid 11.4.1 | `https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js` | `out/report.html` (`analyze`) |
| Cytoscape.js 3.30.2 | `https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js` | `out/graph.html`, `docs/graph-example.html` |

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

- **Keys and secrets** live in `keys.ini` at the repository root, which is git-ignored and readable only by its owner (`chmod 600`). `keys.example.ini` is the committed template: same sections and names, no values. Copy it with `cp keys.example.ini keys.ini`. Only Etherscan needs a key today (read by `sources.api_key`); the other sections are ready for next steps 1 to 6.

- **Endpoints** are constants: `RPC`, `MORPHO`, `PENDLE`, `LLAMA`, `LLAMA_COINS`, `ETHERSCAN` in `riskdep/sources.py`, `SECOND_RPCS` in `riskdep/crosscheck.py`, and the script URLs in `riskdep/report.py` and `riskdep/graph.py`.
- **A paid RPC** (archive and WebSocket access, needed by next steps 5 and 6) is set with `RISKDEP_RPC_URL`, its key included; keep the URL in `keys.ini` (section `[rpc]`, git-ignored) and export it from there. It is never committed, and the cache keys keep the publicnode URL. A paid endpoint can also be added to `erpc.yaml` as one more upstream, with its key through eRPC's `${VAR}` substitution from your shell, never written in the file.
- **The eRPC upstreams** live in `erpc.yaml`; a change there updates the eRPC table above in the same commit.
- **After any change:**
  - re-record the replays (`watch --blocks 1000 --record`, `watch --user <address> --blocks 300 --record`), because cached requests are keyed by their URL and body;
  - run the tests;
  - update this file in the same commit.
