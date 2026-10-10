# Etherscan API V2 — reference

Offline Markdown copy of the Etherscan API V2 reference (`_index.md`, `endpoint-overview.md` and 93 pages under `endpoint/`, one per endpoint), scraped from <https://docs.etherscan.io/api-reference/> (each page's header gives its own source URL). This folder is tracked in git. Base URL: `https://api.etherscan.io/v2/api?chainid=…`; the key goes in `keys.ini`, `[etherscan] api_key` (optional).

## Why it matters to riskdep

| Module | Endpoint | Use |
|---|---|---|
| `riskdep/sources.py` (`contract_source`) | `module=contract&action=getsourcecode`, `chainid=1` | slim answer `{verified, name, proxy, implementation}`; a refusal (`status` 0) is never cached |
| `riskdep/discover.py` (`oracle_verified`) | `getsourcecode` (via `sources`) | verified oracle drops the ×2 `oracle.unverified_factor` (D68) |
| `riskdep/oracle_class.py` (`_contract_name`) | `getsourcecode` (via `sources`) | `ContractName` matched against `graph.oracle_patterns` (D83) |
| `riskdep/priors.py`, `riskdep/scenario.py` | none (consume the result) | verified status in the oracle prior; contract `name` |
| `riskdep/graph.py` | none (links to `etherscan.io/address/…`) | HTML graph links |
| analyses (not in the CLI) | `getLogs` (RoleGranted/RoleRevoked), `getsourcecode` | admin/role history, source reading |

See also `docs/analysis/PROVIDERS.md`, section "Etherscan".

## Tree

```
docs.etherscan.io-api-reference-docs/
├── README.md               # this file
├── _index.md               # table of contents of every page
├── endpoint-overview.md    # all endpoints grouped by module, plan badges (Free / Standard / Pro Plus)
└── endpoint/               # one page per endpoint: params, cURL/JS/PHP samples, sample response
    # contracts: getsourcecode, getabi, getcontractcreation, verifysourcecode, verifyvyper,
    #            verifystylus, verifyzksyncsourcecode, verifyproxycontract, checkverifystatus,
    #            checkproxyverification
    # logs:      getlogs, getlogs-topics, getlogs-address-topics
    # accounts:  balance, balancemulti, balancehistory, txlist, txlistinternal(-blockrange,-txhash),
    #            tokentx, tokennfttx, token1155tx, advanced-filter-*, getminedblocks, fundedby,
    #            getdeposittxs, getwithdrawaltxs, txsbeaconwithdrawal, txnbridge, addresstoken*
    # tokens:    tokensupply, tokenbalance, tokeninfo, tokenholderlist, tokenholdercount,
    #            topholders, tokensupplyhistory, tokenbalancehistory
    # proxy:     ethcall, ethgetstorageat, ethgetcode, ethblocknumber, ethgettransaction*,
    #            ethgetblockbynumber, ethsendrawtransaction, ethestimategas, ethgasprice, ...
    # stats:     ethsupply, ethsupply2, ethprice, ethdailyprice, chainsize, nodecount, daily*
    # blocks:    getblockreward, getblockcountdown, getblocknobytime, getblocktxnscount
    # gas/tx:    gasoracle, gasestimate, getstatus, gettxreceiptstatus
    # misc:      chainlist, getapilimit, getaddresstag, forwardresolve
```

## Main files

| Path | What | riskdep use |
|---|---|---|
| `endpoint/getsourcecode.md` | verified source, `ContractName`, `Proxy`, `Implementation` | `sources.contract_source` |
| `endpoint/getabi.md` | ABI as a JSON string | not used (ABIs are in `abi.py`) |
| `endpoint/getlogs.md`, `endpoint/getlogs-topics.md`, `endpoint/getlogs-address-topics.md` | event logs by address and/or topics | role-history analyses |
| `endpoint/ethcall.md`, `endpoint/ethgetstorageat.md`, `endpoint/ethgetcode.md` | JSON-RPC proxy | alternative to the RPC provider |
| `endpoint/chainlist.md` | supported chains and their `apiurl` | multi-chain |
| `endpoint/getapilimit.md` | credit usage | rate-limit checks |
| `endpoint-overview.md` | endpoint list by module + plan | which endpoints the free key can call |

## Read first for this project

- **getsourcecode** — `endpoint/getsourcecode.md`: params `chainid` (required), `module=contract`, `action=getsourcecode`, `address`. Result is an array of one object with `SourceCode`, `ABI`, `ContractName`, …, `"Proxy": "0"`, `"Implementation": ""` (`Proxy` "1" + `Implementation` address when Etherscan recognises a proxy). Unverified contracts return empty `SourceCode`/`ContractName`.
- **getabi** — `endpoint/getabi.md`: `module=contract&action=getabi&address=…`; `result` is the ABI as an escaped JSON *string* to parse again.
- **getLogs** — `endpoint/getlogs.md` (by address), `endpoint/getlogs-topics.md` (topics only), `endpoint/getlogs-address-topics.md` (both): `module=logs&action=getLogs`, `fromBlock`/`toBlock` ("required"; "Keep the range narrow to avoid timeouts and large responses"), `topic0`…`topic3` ("At least one of topic0-topic3 is required" without address), `topic0_1_opr` "either `and` or `or`", `page` + `offset` ("Number of records per page. Use the page parameter for subsequent records"). For RoleGranted/RoleRevoked: `topic0` = event hash, `topic1` = role.
- **proxy module** — `endpoint/ethcall.md` (`module=proxy&action=eth_call`, "Execute a call without creating a transaction"), `endpoint/ethgetstorageat.md` (`action=eth_getStorageAt`, `position` "Storage position in hex", `tag` latest/block hex; result is a 32-byte hex string — e.g. EIP-1967 implementation slot). Proxy-module answers are raw JSON-RPC (`jsonrpc`/`id`/`result`), not `status`/`message`.
- **chainid** — every page: "Chain ID to query, eg 1 for Ethereum, 42161 for Arbitrum". `endpoint/chainlist.md` lists `apiurl` per chain (`?chainid=1`, `8453` Base, `137`, `42161`, `11155111`…). BSC is `56`; one key works for all chains, but some chains need a paid plan (`endpoint-overview.md` line 145).
- **rate limits / free tier** — `endpoint-overview.md`: "Create a free key"; contract source "and ABI endpoints are available on all chains for every API plan, including the Free tier"; badges mark Standard and Pro Plus endpoints (link to `docs.etherscan.io/rate-limits`, not copied). `endpoint/getapilimit.md`: `creditLimit`, `"limitInterval": "daily"`.
- **errors** — `endpoint/getsourcecode.md` response: `status` "1 if the request returned data, 0 otherwise. A status of 0 can indicate an error"; `message` "OK on success, otherwise an error description such as NOTOK". riskdep treats `status` 0 (bad key, rate limit) as "not checked" and does not cache it.

## Gaps

- No rate-limits page (calls/second per plan) and no supported-chains page: only links to `docs.etherscan.io/rate-limits` and `/supported-chains`.
- The 1000-results-per-query cap of `getLogs` and the 10 000-record pagination window are not stated in these pages; rely on PROVIDERS.md or narrow block ranges.
- No list of error strings (`Max rate limit reached`, `Invalid API Key`, `Missing/Invalid API Key`…); only `NOTOK` is named.
- Guides (getting started, V1→V2 migration, API key) are not copied, only `api-reference/endpoint/*`.
