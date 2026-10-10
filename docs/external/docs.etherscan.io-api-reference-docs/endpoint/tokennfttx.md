# Get ERC721 Token Transfers by Address

> Source: https://docs.etherscan.io/api-reference/endpoint/tokennfttx

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/tokennfttx#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/tokennfttx","name":"Get ERC721 Token Transfers by Address","description":"Retrieves ERC-721 token transfers, filtered by address and/or token contract.","dateModified":"2026-08-20T09:11:04.091Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/tokennfttx#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/tokennfttx#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Account","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":3,"name":"Get ERC721 Token Transfers by Address","item":"https://docs.etherscan.io/api-reference/endpoint/tokennfttx"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/tokennfttx#apireference","headline":"Get ERC721 Token Transfers by Address","name":"Get ERC721 Token Transfers by Address","description":"Retrieves ERC-721 token transfers, filtered by address and/or token contract.","url":"https://docs.etherscan.io/api-reference/endpoint/tokennfttx","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/tokennfttx#webpage"},"dateModified":"2026-08-20T09:11:04.091Z","keywords":"ERC721 transfers, tokennfttx","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

Get ERC721 Token Transfers by AddresscURL

```
curl --request GET \
  --url 'https://api.etherscan.io/v2/api?apikey='
```

```
import requests

url = "https://api.etherscan.io/v2/api?apikey="

response = requests.get(url)

print(response.text)
```

```
const options = {method: 'GET'};

fetch('https://api.etherscan.io/v2/api?apikey=', options)
  .then(res => res.json())
  .then(res => console.log(res))
  .catch(err => console.error(err));
```

```
<?php

$curl = curl_init();

curl_setopt_array($curl, [
  CURLOPT_URL => "https://api.etherscan.io/v2/api?apikey=",
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => "",
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 30,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => "GET",
]);

$response = curl_exec($curl);
$err = curl_error($curl);

curl_close($curl);

if ($err) {
  echo "cURL Error #:" . $err;
} else {
  echo $response;
}
```

```
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.etherscan.io/v2/api?apikey="

	req, _ := http.NewRequest("GET", url, nil)

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(string(body))

}
```

```
HttpResponse<String> response = Unirest.get("https://api.etherscan.io/v2/api?apikey=")
  .asString();
```

```
require 'uri'
require 'net/http'

url = URI("https://api.etherscan.io/v2/api?apikey=")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

Example response
```
{
  "status": "1",
  "message": "OK",
  "result": [
    {
      "blockNumber": "4708120",
      "timeStamp": "1512907118",
      "hash": "0x031e6968a8de362e4328d60dcc7f72f0d6fc84284c452f63176632177146de66",
      "nonce": "0",
      "blockHash": "0x4be19c278bfaead5cb0bc9476fa632e2447f6e6259e0303af210302d22779a24",
      "from": "0xb1690c08e213a35ed9bab7b318de14420fb57d8c",
      "contractAddress": "0x06012c8cf97bead5deae237070f9587f8e7a266d",
      "to": "0x6975be450864c02b4613023c2152ee0743572325",
      "tokenID": "202106",
      "tokenName": "CryptoKitties",
      "tokenSymbol": "CK",
      "tokenDecimal": "0",
      "transactionIndex": "81",
      "gas": "158820",
      "gasPrice": "40000000000",
      "gasUsed": "60508",
      "cumulativeGasUsed": "4880352",
      "input": "deprecated",
      "methodId": "0x454a2ab3",
      "functionName": "bid(uint256 _tokenId)",
      "confirmations": "18759540"
    }
  ]
}
```

Account
# Get ERC721 Token Transfers by Address

Copy pageCopy pageRetrieves ERC-721 token transfers, filtered by address and/or token contract.

Copy pageCopy pageGET/v2/apiTry itGet ERC721 Token Transfers by AddresscURL

```
curl --request GET \
  --url 'https://api.etherscan.io/v2/api?apikey='
```

```
import requests

url = "https://api.etherscan.io/v2/api?apikey="

response = requests.get(url)

print(response.text)
```

```
const options = {method: 'GET'};

fetch('https://api.etherscan.io/v2/api?apikey=', options)
  .then(res => res.json())
  .then(res => console.log(res))
  .catch(err => console.error(err));
```

```
<?php

$curl = curl_init();

curl_setopt_array($curl, [
  CURLOPT_URL => "https://api.etherscan.io/v2/api?apikey=",
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => "",
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 30,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => "GET",
]);

$response = curl_exec($curl);
$err = curl_error($curl);

curl_close($curl);

if ($err) {
  echo "cURL Error #:" . $err;
} else {
  echo $response;
}
```

```
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.etherscan.io/v2/api?apikey="

	req, _ := http.NewRequest("GET", url, nil)

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(string(body))

}
```

```
HttpResponse<String> response = Unirest.get("https://api.etherscan.io/v2/api?apikey=")
  .asString();
```

```
require 'uri'
require 'net/http'

url = URI("https://api.etherscan.io/v2/api?apikey=")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Get.new(url)

response = http.request(request)
puts response.read_body
```

Example response
```
{
  "status": "1",
  "message": "OK",
  "result": [
    {
      "blockNumber": "4708120",
      "timeStamp": "1512907118",
      "hash": "0x031e6968a8de362e4328d60dcc7f72f0d6fc84284c452f63176632177146de66",
      "nonce": "0",
      "blockHash": "0x4be19c278bfaead5cb0bc9476fa632e2447f6e6259e0303af210302d22779a24",
      "from": "0xb1690c08e213a35ed9bab7b318de14420fb57d8c",
      "contractAddress": "0x06012c8cf97bead5deae237070f9587f8e7a266d",
      "to": "0x6975be450864c02b4613023c2152ee0743572325",
      "tokenID": "202106",
      "tokenName": "CryptoKitties",
      "tokenSymbol": "CK",
      "tokenDecimal": "0",
      "transactionIndex": "81",
      "gas": "158820",
      "gasPrice": "40000000000",
      "gasUsed": "60508",
      "cumulativeGasUsed": "4880352",
      "input": "deprecated",
      "methodId": "0x454a2ab3",
      "functionName": "bid(uint256 _tokenId)",
      "confirmations": "18759540"
    }
  ]
}
```

Example response
```
{
  "status": "1",
  "message": "OK",
  "result": [
    {
      "blockNumber": "4708120",
      "timeStamp": "1512907118",
      "hash": "0x031e6968a8de362e4328d60dcc7f72f0d6fc84284c452f63176632177146de66",
      "nonce": "0",
      "blockHash": "0x4be19c278bfaead5cb0bc9476fa632e2447f6e6259e0303af210302d22779a24",
      "from": "0xb1690c08e213a35ed9bab7b318de14420fb57d8c",
      "contractAddress": "0x06012c8cf97bead5deae237070f9587f8e7a266d",
      "to": "0x6975be450864c02b4613023c2152ee0743572325",
      "tokenID": "202106",
      "tokenName": "CryptoKitties",
      "tokenSymbol": "CK",
      "tokenDecimal": "0",
      "transactionIndex": "81",
      "gas": "158820",
      "gasPrice": "40000000000",
      "gasUsed": "60508",
      "cumulativeGasUsed": "4880352",
      "input": "deprecated",
      "methodId": "0x454a2ab3",
      "functionName": "bid(uint256 _tokenId)",
      "confirmations": "18759540"
    }
  ]
}
```

#### Authorizations

[​](#authorization-apikey)apikeystringqueryrequiredEnter your Etherscan API key, or [set one up](https://docs.etherscan.io/set-up-your-api-key) if you don't have one.

#### Query Parameters

[​](#parameter-chainid)chainidstringrequiredChain ID to query, eg 1 for Ethereum, 42161 for Arbitrum from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:accountrequiredSet to account for this endpoint.

[​](#parameter-action)actionstringdefault:tokennfttxrequiredSet to tokennfttx for this endpoint.

[​](#parameter-contractaddress)contractaddressstringThe ERC-721 token contract address to filter transfers by. Provide at least one of `address` or `contractaddress`.

[​](#parameter-address)addressstringThe account address to filter transfers by. Provide at least one of `address` or `contractaddress`.

[​](#parameter-page)pageintegerPage number for pagination.

[​](#parameter-offset)offsetintegerNumber of records per page. Use the page parameter for subsequent records.

[​](#parameter-startblock)startblockintegerStarting block number to search from.

[​](#parameter-endblock)endblockintegerEnding block number to search to.

[​](#parameter-sort)sortstringSort order either `desc` for the latest transactions first or `asc` for the oldest transactions first.

#### Response

200 - application/jsonSuccessful response

[​](#response-status)statusstring1 if the request returned data, 0 otherwise. A status of 0 can indicate an error or a valid request that returned no records.

[​](#response-message)messagestringOK on success, otherwise an error description such as NOTOK. See [common error messages](https://docs.etherscan.io/common-error-messages).

[​](#response-result)resultobject[]Show child attributes

[ERC20 Token Transfers Advanced Filter](https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokentx)[ERC721 Token Transfers Advanced Filter](https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokennfttx)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)