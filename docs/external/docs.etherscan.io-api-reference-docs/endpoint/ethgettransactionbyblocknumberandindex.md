# eth\_getTransactionByBlockNumberAndIndex

> Source: https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyblocknumberandindex

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyblocknumberandindex#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyblocknumberandindex","name":"eth_getTransactionByBlockNumberAndIndex","description":"Get transaction details by block number and index.","dateModified":"2026-08-20T09:11:04.412Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyblocknumberandindex#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyblocknumberandindex#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Geth/Parity Proxy","item":"https://docs.etherscan.io/api-reference/endpoint/ethblocknumber"},{"@type":"ListItem","position":3,"name":"eth_getTransactionByBlockNumberAndIndex","item":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyblocknumberandindex"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyblocknumberandindex#apireference","headline":"eth_getTransactionByBlockNumberAndIndex","name":"eth_getTransactionByBlockNumberAndIndex","description":"Get transaction details by block number and index.","url":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyblocknumberandindex","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyblocknumberandindex#webpage"},"dateModified":"2026-08-20T09:11:04.412Z","keywords":"eth_getTransactionByBlockNumberAndIndex, transaction in block","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

eth_getTransactionByBlockNumberAndIndexcURL

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
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "blockHash": "0x13c5311a78b9a8790c58f1d0d0660226352a498cc98b06e1861f1967d3a9d1b4",
    "blockNumber": "0xc6331d",
    "from": "0xd1af036d589b6ebfbaa184b339a30d32ef611708",
    "gas": "0x11170",
    "gasPrice": "0x5b7e259a7",
    "maxFeePerGas": "0x5b7e259a7",
    "maxPriorityFeePerGas": "0x5b7e259a7",
    "hash": "0xc7ef51f0bfe85eefbb1d4d88f5a39e82fbfc94987d8cbcb515f74d80b6e44902",
    "input": "0x2d2da806000000000000000000000000d1af036d589b6ebfbaa184b339a30d32ef611708",
    "nonce": "0x0",
    "to": "0xabea9132b05a70803a4e85094fd0e1800777fbef",
    "transactionIndex": "0x11a",
    "value": "0x57930b5db6a000",
    "type": "0x2",
    "accessList": [],
    "chainId": "0x1",
    "v": "0x0",
    "r": "0x595619be17755f7427d07626275e4c89b8f9d5a0a668515165ea000d30f26325",
    "s": "0x33d4b22c7c779fc9f04c81788cb4268d2c3f8dc9e219245570bdd384c6ca6690",
    "yParity": "0x0"
  }
}
```

Geth/Parity Proxy
# eth_getTransactionByBlockNumberAndIndex

Copy pageCopy pageGet transaction details by block number and index.

Copy pageCopy pageGET/v2/apiTry iteth_getTransactionByBlockNumberAndIndexcURL

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
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "blockHash": "0x13c5311a78b9a8790c58f1d0d0660226352a498cc98b06e1861f1967d3a9d1b4",
    "blockNumber": "0xc6331d",
    "from": "0xd1af036d589b6ebfbaa184b339a30d32ef611708",
    "gas": "0x11170",
    "gasPrice": "0x5b7e259a7",
    "maxFeePerGas": "0x5b7e259a7",
    "maxPriorityFeePerGas": "0x5b7e259a7",
    "hash": "0xc7ef51f0bfe85eefbb1d4d88f5a39e82fbfc94987d8cbcb515f74d80b6e44902",
    "input": "0x2d2da806000000000000000000000000d1af036d589b6ebfbaa184b339a30d32ef611708",
    "nonce": "0x0",
    "to": "0xabea9132b05a70803a4e85094fd0e1800777fbef",
    "transactionIndex": "0x11a",
    "value": "0x57930b5db6a000",
    "type": "0x2",
    "accessList": [],
    "chainId": "0x1",
    "v": "0x0",
    "r": "0x595619be17755f7427d07626275e4c89b8f9d5a0a668515165ea000d30f26325",
    "s": "0x33d4b22c7c779fc9f04c81788cb4268d2c3f8dc9e219245570bdd384c6ca6690",
    "yParity": "0x0"
  }
}
```

Example response
```
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "blockHash": "0x13c5311a78b9a8790c58f1d0d0660226352a498cc98b06e1861f1967d3a9d1b4",
    "blockNumber": "0xc6331d",
    "from": "0xd1af036d589b6ebfbaa184b339a30d32ef611708",
    "gas": "0x11170",
    "gasPrice": "0x5b7e259a7",
    "maxFeePerGas": "0x5b7e259a7",
    "maxPriorityFeePerGas": "0x5b7e259a7",
    "hash": "0xc7ef51f0bfe85eefbb1d4d88f5a39e82fbfc94987d8cbcb515f74d80b6e44902",
    "input": "0x2d2da806000000000000000000000000d1af036d589b6ebfbaa184b339a30d32ef611708",
    "nonce": "0x0",
    "to": "0xabea9132b05a70803a4e85094fd0e1800777fbef",
    "transactionIndex": "0x11a",
    "value": "0x57930b5db6a000",
    "type": "0x2",
    "accessList": [],
    "chainId": "0x1",
    "v": "0x0",
    "r": "0x595619be17755f7427d07626275e4c89b8f9d5a0a668515165ea000d30f26325",
    "s": "0x33d4b22c7c779fc9f04c81788cb4268d2c3f8dc9e219245570bdd384c6ca6690",
    "yParity": "0x0"
  }
}
```

#### Authorizations

[​](#authorization-apikey)apikeystringqueryrequiredEnter your Etherscan API key, or [set one up](https://docs.etherscan.io/set-up-your-api-key) if you don't have one.

#### Query Parameters

[​](#parameter-chainid)chainidstringrequiredChain ID to query, eg 1 for Ethereum, 42161 for Arbitrum from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:proxyrequiredSet to proxy for this endpoint.

[​](#parameter-action)actionstringdefault:eth_getTransactionByBlockNumberAndIndexrequiredSet to eth_getTransactionByBlockNumberAndIndex for this endpoint.

[​](#parameter-tag)tagstringBlock number in hex format.

[​](#parameter-index)indexstringTransaction index position in the block, in hex.

#### Response

200 - application/jsonSuccessful response

[​](#response-jsonrpc)jsonrpcstringJSON-RPC protocol version.

[​](#response-id)idintegerRequest identifier, echoed back from the request.

[​](#response-result)resultobjectShow child attributes

[eth_getTransactionByHash](https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash)[eth_getTransactionCount](https://docs.etherscan.io/api-reference/endpoint/ethgettransactioncount)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)