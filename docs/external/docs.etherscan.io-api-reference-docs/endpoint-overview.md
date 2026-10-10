# Endpoint Overview

> Source: https://docs.etherscan.io/endpoint-overview

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/endpoint-overview#webpage","url":"https://docs.etherscan.io/endpoint-overview","name":"Endpoint Overview","description":"A complete list of Etherscan API endpoints, grouped by module.","dateModified":"2026-10-06T09:58:02.359Z","isPartOf":{"@id":"https://docs.etherscan.io#website"}},{"@type":["Article","TechArticle"],"@id":"https://docs.etherscan.io/endpoint-overview#article","headline":"Endpoint Overview","name":"Endpoint Overview","description":"A complete list of Etherscan API endpoints, grouped by module.","url":"https://docs.etherscan.io/endpoint-overview","mainEntityOfPage":{"@id":"https://docs.etherscan.io/endpoint-overview#webpage"},"dateModified":"2026-10-06T09:58:02.359Z","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
    --color-rgb: 36, 107, 238;
    --navbar-bg-hsl: 220, 25%, 100%;
}

/* Mintlify marks dark mode with the `dark` class on <html> (not `twoslash-dark`). */
:root.dark {
    --navbar-bg-hsl: 209, 23%, 9%;
}

#navbar {
    overflow: hidden;
    background-color: hsla(var(--navbar-bg-hsl), 1);
    background-image:
    radial-gradient(at 14% 42%, hsla(var(--navbar-bg-hsl), 1) 0px, transparent 50%),
    radial-gradient(at 39% 9%, hsla(var(--navbar-bg-hsl), 1) 0px, transparent 50%),
    radial-gradient(at 95% 85%, hsla(var(--navbar-bg-hsl), 1) 0px, transparent 50%),
    radial-gradient(at 99% 61%, hsla(var(--navbar-bg-hsl), 1) 0px, transparent 50%),
    radial-gradient(at 91% 60%, rgba(var(--color-rgb), 0.4) 0px, transparent 50%),
    radial-gradient(at 69% 0%, rgba(var(--color-rgb), 0.4) 0px, transparent 50%);
}

#navbar::after {
    content: '';
    width: 60rem;
    height: 60rem;
    position: absolute;
    top: -150%;
    right: -30%;
    background-image: url('/images/abstract-lines-kb.svg');
    background-size: 40rem;
    background-repeat: no-repeat;
    cursor: default;
    pointer-events: none
}

.data-\[is-opaque\=true\]\:bg-background-light[data-is-opaque=true] {
    background-color: initial !important;
}

.data-\[is-opaque\=true\]\:dark\:bg-background-dark\/75:is(.dark *)[data-is-opaque=true] {
    background-color: initial !important;
}

.prose:is(.dark *) {
    color: #D1D1D1;
}

.tryit-button {
    background-color: #0784C3 !important;
}

/* ── PRO tag pill flows inline at the end of the sidebar title ──
   Mintlify renders the nav tag as a flex sibling, so on long titles it drops
   to its own line. Switch the container to normal inline flow so the pill sits
   right after the last word of the title (where the old [PRO] text was) and
   wraps along with the text. */
.nav-tag-pill-text[data-nav-tag] {
    background-color: #0784C3 !important;
    color: #FFFFFF !important;
}
/* PRO+ (Pro Plus only): deeper blue, matches the <Pro plus /> badge in snippets/pro.jsx */
.nav-tag-pill-text[data-nav-tag="PRO+"] {
    background-color: #055a8c !important;
}
/* the container that holds the title span + the tag pill: inline flow, not flex */
a:has(.nav-tag-pill) div:has(> div > span.nav-tag-pill) {
    display: block;
}
/* the pill sits inline right after the title text */
a:has(.nav-tag-pill) div:has(> div > span.nav-tag-pill) > div:last-child {
    display: inline-flex;
    vertical-align: middle;
    margin-left: 0.375rem;
}

.mint-mr-0\.5 {
    margin-right: 0.125rem
}
.mint-mt-6 {
    margin-top: 1.5rem
}
.mint-flex {
    display: flex
}
.mint-flex-wrap {
    flex-wrap: wrap
}
.mint-items-center {
    align-items: center
}
.mint-gap-1\.5 {
    gap: 0.375rem
}
.mint-text-\[11px\] {
    font-size: 11px
}
.mint-uppercase {
    text-transform: uppercase
}
.mint-tracking-wide {
    letter-spacing: 0.025em
}
.mint-text-zinc-900 {
    --tw-text-opacity: 1;
    color: rgb(24 24 27 / var(--tw-text-opacity, 1))
}
.dark\:mint-text-white:is(.dark *) {
    --tw-text-opacity: 1;
    color: rgb(255 255 255 / var(--tw-text-opacity, 1))
}
## On this page

- [Account](#account)
- [Blocks](#blocks)
- [Contracts](#contracts)
- [Contract Verification](#contract-verification)
- [Gas Tracker](#gas-tracker)
- [Geth/Parity Proxy](#geth%2Fparity-proxy)
- [Logs](#logs)
- [Stats](#stats)
- [Transactions](#transactions)
- [Tokens](#tokens)
- [L2 Deposits/Withdrawals](#l2-deposits%2Fwithdrawals)
- [ENS](#ens)
- [Nametags](#nametags)
- [Usage](#usage)
- [Beta Endpoints](#beta-endpoints)

# Endpoint Overview

Copy pageCopy pageA complete list of Etherscan API endpoints, grouped by module.

Copy pageCopy pageEvery Etherscan API endpoint, grouped by module. One key works across all 60+ [supported chains](https://docs.etherscan.io/supported-chains).

## Set up your API key

Create a free key and make your first call in minutes.
Endpoints marked  are available to the [Standard plan](https://docs.etherscan.io/rate-limits) and above. Endpoints marked  require the [Pro Plus plan](https://etherscan.io/api/pricing). Community endpoint access depends on the chain’s [plan availability](https://docs.etherscan.io/supported-chains). Source code and ABI endpoints are available on all chains for every API plan, including the Free tier.

## [​](#account)Account

| Endpoint | Description |
| --- | --- |
| [Get Native Balance for an Address](https://docs.etherscan.io/api-reference/endpoint/balance) | Retrieves the native token balance held by a specific address. |
| [Get Native Balance for Multiple Addresses](https://docs.etherscan.io/api-reference/endpoint/balancemulti) | Retrieves the native token balance held by multiple addresses in a single call. |
| [Get Historical Native Balance for an Address](https://docs.etherscan.io/api-reference/endpoint/balancehistory) | Retrieves the balance of a specified address at a given block height. |
| [Get Normal Transactions By Address](https://docs.etherscan.io/api-reference/endpoint/txlist) | Retrieves the transaction history of a specified address, with optional pagination. |
| [Normal Transactions Advanced Filter](https://docs.etherscan.io/api-reference/endpoint/advanced-filter-txlist) | Retrieves Normal Transactions with advanced from and to address filtering. |
| [Get ERC20 Token Transfers by Address](https://docs.etherscan.io/api-reference/endpoint/tokentx) | Retrieves ERC-20 token transfers, filtered by address and/or token contract. |
| [ERC20 Token Transfers Advanced Filter](https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokentx) | Retrieves ERC20 token transfers with advanced from and to address filtering. |
| [Get ERC721 Token Transfers by Address](https://docs.etherscan.io/api-reference/endpoint/tokennfttx) | Retrieves ERC-721 token transfers, filtered by address and/or token contract. |
| [ERC721 Token Transfers Advanced Filter](https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokennfttx) | Retrieves ERC721 token transfers with advanced from and to address filtering. |
| [Get ERC1155 Token Transfers by Address](https://docs.etherscan.io/api-reference/endpoint/token1155tx) | Retrieves ERC-1155 token transfers, filtered by address and/or token contract. |
| [ERC1155 Token Transfers Advanced Filter](https://docs.etherscan.io/api-reference/endpoint/advanced-filter-token1155tx) | Retrieves ERC1155 token transfers with advanced from and to address filtering. |
| [Get Internal Transactions by Address](https://docs.etherscan.io/api-reference/endpoint/txlistinternal) | Retrieves the internal transaction history of a specified address, with optional pagination. |
| [Internal Transactions Advanced Filter](https://docs.etherscan.io/api-reference/endpoint/advanced-filter-txlistinternal) | Retrieves Internal Transactions with advanced from and to address filtering. |
| [Get Internal Transactions by Block Range](https://docs.etherscan.io/api-reference/endpoint/txlistinternal-blockrange) | Returns internal transactions within a specified block range, with optional pagination. |
| [Get Internal Transactions by Transaction Hash](https://docs.etherscan.io/api-reference/endpoint/txlistinternal-txhash) | Retrieves the list of internal transactions executed within a specific transaction. |
| [Get Blocks Validated by Address](https://docs.etherscan.io/api-reference/endpoint/getminedblocks) | Retrieves the list of blocks validated by a specified address. |
| [Get Beacon Chain Withdrawals by Address](https://docs.etherscan.io/api-reference/endpoint/txsbeaconwithdrawal) | Retrieves beacon chain withdrawals, optionally filtered by address. |
| [Get Address Funded By](https://docs.etherscan.io/api-reference/endpoint/fundedby) | Retrieves the address and transaction that first funded a specific EOA address, useful for tracing fund origins. Not available to contract addresses. |

## [​](#blocks)Blocks

| Endpoint | Description |
| --- | --- |
| [Get Block and Uncle Rewards by Block Number](https://docs.etherscan.io/api-reference/endpoint/getblockreward) | Retrieves block rewards along with associated Uncle block rewards. |
| [Get Block Transaction Counts by Block Number](https://docs.etherscan.io/api-reference/endpoint/getblocktxnscount) | Retrieves transaction counts for a specified Ethereum block. |
| [Get Estimated Block Countdown by Block Number](https://docs.etherscan.io/api-reference/endpoint/getblockcountdown) | Retrieves the estimated time, in seconds, until a specified block is mined. |
| [Get Block Number by Timestamp](https://docs.etherscan.io/api-reference/endpoint/getblocknobytime) | Retrieves the block number mined at a specific timestamp. |
| [Get Daily Average Block Size](https://docs.etherscan.io/api-reference/endpoint/dailyavgblocksize) | Retrieves the average daily block size over a specified date range. |
| [Get Daily Block Count and Rewards](https://docs.etherscan.io/api-reference/endpoint/dailyblkcount) | Retrieves the daily count of mined blocks along with the corresponding block rewards. |
| [Get Daily Block Rewards](https://docs.etherscan.io/api-reference/endpoint/dailyblockrewards) | Retrieves the daily distribution of block rewards to miners. |
| [Get Daily Average Block Time](https://docs.etherscan.io/api-reference/endpoint/dailyavgblocktime) | Retrieves the daily average time taken to successfully mine a block. |
| [Get Daily Uncle Block Count and Rewards](https://docs.etherscan.io/api-reference/endpoint/dailyuncleblkcount) | Returns the daily count of Uncle blocks mined and their associated rewards. |

## [​](#contracts)Contracts

| Endpoint | Description |
| --- | --- |
| [Get Contract ABI](https://docs.etherscan.io/api-reference/endpoint/getabi) | Retrieve the ABI for a verified smart contract. |
| [Get Contract Source Code](https://docs.etherscan.io/api-reference/endpoint/getsourcecode) | Retrieve the source code for a verified smart contract. |
| [Get Contract Creator and Creation Tx Hash](https://docs.etherscan.io/api-reference/endpoint/getcontractcreation) | Retrieve a contract’s deployer address and creation transaction. |

## [​](#contract-verification)Contract Verification

| Endpoint | Description |
| --- | --- |
| [Verify Solidity Source Code](https://docs.etherscan.io/api-reference/endpoint/verifysourcecode) | Submit a Solidity source code for verification. |
| [Verify zkSync Source Code](https://docs.etherscan.io/api-reference/endpoint/verifyzksyncsourcecode) | Submit zkSync source code for verification. |
| [Verify Vyper Source Code](https://docs.etherscan.io/api-reference/endpoint/verifyvyper) | Submit a Vyper contract for verification. |
| [Verify Stylus Source Code](https://docs.etherscan.io/api-reference/endpoint/verifystylus) | Submit Stylus source code for verification. |
| [Verify Proxy Contract](https://docs.etherscan.io/api-reference/endpoint/verifyproxycontract) | Submit a proxy contract for verification. |
| [Check Source Code Verification Status](https://docs.etherscan.io/api-reference/endpoint/checkverifystatus) | Check the status of a source code verification request. |
| [Check Proxy Contract Verification Status](https://docs.etherscan.io/api-reference/endpoint/checkproxyverification) | Check the status of a proxy contract verification. |

## [​](#gas-tracker)Gas Tracker

| Endpoint | Description |
| --- | --- |
| [Get Estimation of Confirmation Time](https://docs.etherscan.io/api-reference/endpoint/gasestimate) | Estimate confirmation time based on a provided gas price. |
| [Get Gas Oracle](https://docs.etherscan.io/api-reference/endpoint/gasoracle) | Get current gas price recommendations. |
| [Get Daily Average Gas Limit](https://docs.etherscan.io/api-reference/endpoint/dailyavggaslimit) | Retrieve daily average gas limit statistics. |
| [Get Ethereum Daily Total Gas Used](https://docs.etherscan.io/api-reference/endpoint/dailygasused) | Retrieves the total daily gas usage for transactions within the network |
| [Get Daily Average Gas Price](https://docs.etherscan.io/api-reference/endpoint/dailyavggasprice) | Retrieve daily average gas price statistics. |

## [​](#geth/parity-proxy)Geth/Parity Proxy

| Endpoint | Description |
| --- | --- |
| [eth_blockNumber](https://docs.etherscan.io/api-reference/endpoint/ethblocknumber) | Fetch the latest block number. |
| [eth_getBlockByNumber](https://docs.etherscan.io/api-reference/endpoint/ethgetblockbynumber) | Get block information by number. |
| [eth_getUncleByBlockNumberAndIndex](https://docs.etherscan.io/api-reference/endpoint/ethgetunclebyblocknumberandindex) | Get uncle block details by block number and index. |
| [eth_getBlockTransactionCountByNumber](https://docs.etherscan.io/api-reference/endpoint/ethgetblocktransactioncountbynumber) | Get the number of transactions in a block. |
| [eth_getTransactionByHash](https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash) | Get transaction details by hash. |
| [eth_getTransactionByBlockNumberAndIndex](https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyblocknumberandindex) | Get transaction details by block number and index. |
| [eth_getTransactionCount](https://docs.etherscan.io/api-reference/endpoint/ethgettransactioncount) | Get the number of transactions sent from an address. |
| [eth_sendRawTransaction](https://docs.etherscan.io/api-reference/endpoint/ethsendrawtransaction) | Broadcast a signed transaction to the network. |
| [eth_getTransactionReceipt](https://docs.etherscan.io/api-reference/endpoint/ethgettransactionreceipt) | Get the receipt of a transaction by hash. |
| [eth_call](https://docs.etherscan.io/api-reference/endpoint/ethcall) | Execute a call without creating a transaction. |
| [eth_getCode](https://docs.etherscan.io/api-reference/endpoint/ethgetcode) | Get the code stored at an address. |
| [eth_getStorageAt](https://docs.etherscan.io/api-reference/endpoint/ethgetstorageat) | Get the value at a storage position. |
| [eth_gasPrice](https://docs.etherscan.io/api-reference/endpoint/ethgasprice) | Get the current gas price. |
| [eth_estimateGas](https://docs.etherscan.io/api-reference/endpoint/ethestimategas) | Estimate the gas required for a transaction. |

## [​](#logs)Logs

| Endpoint | Description |
| --- | --- |
| [Get Event Logs by Address](https://docs.etherscan.io/api-reference/endpoint/getlogs) | Retrieves event logs from a specific address, with optional block range filtering. |
| [Get Event Logs by Topics](https://docs.etherscan.io/api-reference/endpoint/getlogs-topics) | Retrieves event logs within a specified block range, filtered by topics. |
| [Get Event Logs by Address and Topics](https://docs.etherscan.io/api-reference/endpoint/getlogs-address-topics) | Retrieves event logs from a specified address, filtered by topics and block range. |

## [​](#stats)Stats

| Endpoint | Description |
| --- | --- |
| [Get Total Supply of Ether](https://docs.etherscan.io/api-reference/endpoint/ethsupply) | Retrieves the current circulating supply of Ether, excluding ETH2 staking rewards and EIP-1559 burned fees. |
| [Get Total Supply of Ether 2](https://docs.etherscan.io/api-reference/endpoint/ethsupply2) | Retrieves the current Ether supply, including circulation, ETH2 staking rewards, EIP-1559 burned fees, and total ETH withdrawn from the beacon chain. |
| [Get Ether Last Price](https://docs.etherscan.io/api-reference/endpoint/ethprice) | Retrieves the latest price of the native/gas token. |
| [Get Ethereum Nodes Size](https://docs.etherscan.io/api-reference/endpoint/chainsize) | Retrieves the total size of the Ethereum blockchain, in bytes, within a specified date range. |
| [Get Total Nodes Count](https://docs.etherscan.io/api-reference/endpoint/nodecount) | Retrieves the total count of discoverable Ethereum nodes. |
| [Get Historical Total Nodes Count](https://docs.etherscan.io/api-reference/endpoint/nodecounthistory) | Retrieves the historical daily count of discoverable Ethereum nodes. |
| [Get Daily Network Transaction Fee](https://docs.etherscan.io/api-reference/endpoint/dailytxnfee) | Retrieves the total transaction fees paid to miners each day. |
| [Get Daily New Address Count](https://docs.etherscan.io/api-reference/endpoint/dailynewaddress) | Retrieves the daily count of newly created addresses. |
| [Get Daily ENS Registration Count](https://docs.etherscan.io/api-reference/endpoint/dailyensregister) | Retrieves the daily count of ENS registrations on Ethereum. |
| [Get Daily Network Utilization](https://docs.etherscan.io/api-reference/endpoint/dailynetutilization) | Retrieves the daily average percentage of gas used relative to the gas limit. |
| [Get Daily Average Network Hash Rate](https://docs.etherscan.io/api-reference/endpoint/dailyavghashrate) | Retrieves the historical hash rate, reflecting the processing power of the network over time. |
| [Get Daily Transaction Count](https://docs.etherscan.io/api-reference/endpoint/dailytx) | Retrieves the daily number of transactions executed in the blockchain. |
| [Get Daily Average Network Difficulty](https://docs.etherscan.io/api-reference/endpoint/dailyavgnetdifficulty) | Returns the historical mining difficulty data of the network. |
| [Get Ether Historical Price](https://docs.etherscan.io/api-reference/endpoint/ethdailyprice) | Returns the historical price data for 1 ETH. |

## [​](#transactions)Transactions

| Endpoint | Description |
| --- | --- |
| [Check Contract Execution Status](https://docs.etherscan.io/api-reference/endpoint/getstatus) | Retrieves the current status and execution result of a specific transaction. |
| [Check Transaction Receipt Status](https://docs.etherscan.io/api-reference/endpoint/gettxreceiptstatus) | Retrieves the execution status of a specific transaction using its transaction hash. |

## [​](#tokens)Tokens

| Endpoint | Description |
| --- | --- |
| [Get ERC20-Token TotalSupply by ContractAddress](https://docs.etherscan.io/api-reference/endpoint/tokensupply) | Returns the amount of an ERC-20 token in circulation. |
| [Get Historical ERC20-Token TotalSupply by ContractAddress & BlockNo](https://docs.etherscan.io/api-reference/endpoint/tokensupplyhistory) | Returns the amount of an ERC-20 token in circulation at a certain block height. |
| [Get ERC20-Token Account Balance for TokenContractAddress](https://docs.etherscan.io/api-reference/endpoint/tokenbalance) | Retrieves the current ERC-20 token balance for a specified address. |
| [Get Historical ERC20-Token Account Balance by BlockNo](https://docs.etherscan.io/api-reference/endpoint/tokenbalancehistory) | Retrieves the ERC-20 token balance for a specified address at a given block height. |
| [Get Top Token Holders](https://docs.etherscan.io/api-reference/endpoint/topholders) | Returns the list of top holders for a specified ERC-20 token. |
| [Get Token Holder List by Contract Address](https://docs.etherscan.io/api-reference/endpoint/tokenholderlist) | Retrieves the current list of ERC-20 token holders and their token balances. |
| [Get Token Holder Count by Contract Address](https://docs.etherscan.io/api-reference/endpoint/tokenholdercount) | Retrieves a simple count of ERC-20 token holders. |
| [Get Token Info by ContractAddress](https://docs.etherscan.io/api-reference/endpoint/tokeninfo) | Retrieves project details and social media links for an ERC-20/ERC-721/ERC-1155 token. |
| [Get Address ERC20 Token Holding](https://docs.etherscan.io/api-reference/endpoint/addresstokenbalance) | Retrieves the list of ERC-20 tokens and balances held by a specified address. |
| [Get Address ERC721 Token Holding](https://docs.etherscan.io/api-reference/endpoint/addresstokennftbalance) | Retrieves the ERC-721 tokens and their quantities owned by a specific address. |
| [Get Address ERC721 Token Inventory by Contract](https://docs.etherscan.io/api-reference/endpoint/addresstokennftinventory) | Retrieves the ERC-721 token IDs owned by an address for a given NFT contract. |

## [​](#l2-deposits/withdrawals)L2 Deposits/Withdrawals

| Endpoint | Description |
| --- | --- |
| [Get Plasma Deposits by Address](https://docs.etherscan.io/api-reference/endpoint/txnbridge) | Retrieves a list of Plasma deposit transactions received by a specified address. |
| [Get Deposit Transactions by Address](https://docs.etherscan.io/api-reference/endpoint/getdeposittxs) | Retrieves all deposit transactions made by a specified address. |
| [Get Withdrawal Transactions by Address](https://docs.etherscan.io/api-reference/endpoint/getwithdrawaltxs) | Retrieves all withdrawal transactions made by a specified address. |

## [​](#ens)ENS

| Endpoint | Description |
| --- | --- |
| [Resolve an ENS Name to an Address](https://docs.etherscan.io/api-reference/endpoint/forwardresolve) | Resolves an ENS name or onchain subdomain to its address. |

## [​](#nametags)Nametags

| Endpoint | Description |
| --- | --- |
| [Get Metadata for an Address](https://docs.etherscan.io/api-reference/endpoint/getaddresstag) | Get nametags and metadata for the specified address. |

## [​](#usage)Usage

| Endpoint | Description |
| --- | --- |
| [Get API Usage](https://docs.etherscan.io/api-reference/endpoint/getapilimit) | Returns your current API credit usage and limit for the interval. |
| [Chainlist](https://docs.etherscan.io/api-reference/endpoint/chainlist) | Returns the list of all supported Etherscan mainnet and testnet chains. |

## [​](#beta-endpoints)Beta Endpoints

| Endpoint | Description |
| --- | --- |
| [Get Prediction Market Trades by Address](https://docs.etherscan.io/api-reference/endpoint/get-prediction-market-trades-by-address) | Retrieves prediction market trades from Polymarket by an address. |

[Get Native Balance for an Address](https://docs.etherscan.io/api-reference/endpoint/balance)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)