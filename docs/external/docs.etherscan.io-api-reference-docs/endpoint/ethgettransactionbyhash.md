# eth\_getTransactionByHash

> Source: https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash","name":"eth_getTransactionByHash","description":"Get transaction details by hash.","dateModified":"2026-08-20T09:11:04.420Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Geth/Parity Proxy","item":"https://docs.etherscan.io/api-reference/endpoint/ethblocknumber"},{"@type":"ListItem","position":3,"name":"eth_getTransactionByHash","item":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash#apireference","headline":"eth_getTransactionByHash","name":"eth_getTransactionByHash","description":"Get transaction details by hash.","url":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyhash#webpage"},"dateModified":"2026-08-20T09:11:04.420Z","keywords":"eth_getTransactionByHash, transaction details","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

eth_getTransactionByHashcURL

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
    "blockHash": "0xf850331061196b8f2b67e1f43aaa9e69504c059d3d3fb9547b04f9ed4d141ab7",
    "blockNumber": "0xcf2420",
    "from": "0x00192fb10df37c9fb26829eb2cc623cd1bf599e8",
    "gas": "0x5208",
    "gasPrice": "0x19f017ef49",
    "maxFeePerGas": "0x1f6ea08600",
    "maxPriorityFeePerGas": "0x3b9aca00",
    "hash": "0xbc78ab8a9e9a0bca7d0321a27b2c03addeae08ba81ea98b03cd3dd237eabed44",
    "input": "0x",
    "nonce": "0x33b79d",
    "to": "0xc67f4e626ee4d3f272c2fb31bad60761ab55ed9f",
    "transactionIndex": "0x5b",
    "value": "0x19755d4ce12c00",
    "type": "0x2",
    "accessList": [],
    "chainId": "0x1",
    "v": "0x0",
    "r": "0xa681faea68ff81d191169010888bbbe90ec3eb903e31b0572cd34f13dae281b9",
    "s": "0x3f59b0fa5ce6cf38aff2cfeb68e7a503ceda2a72b4442c7e2844d63544383e3",
    "yParity": "0x0"
  }
}
```

Geth/Parity Proxy
# eth_getTransactionByHash

Copy pageCopy pageGet transaction details by hash.

Copy pageCopy pageGET/v2/apiTry iteth_getTransactionByHashcURL

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
    "blockHash": "0xf850331061196b8f2b67e1f43aaa9e69504c059d3d3fb9547b04f9ed4d141ab7",
    "blockNumber": "0xcf2420",
    "from": "0x00192fb10df37c9fb26829eb2cc623cd1bf599e8",
    "gas": "0x5208",
    "gasPrice": "0x19f017ef49",
    "maxFeePerGas": "0x1f6ea08600",
    "maxPriorityFeePerGas": "0x3b9aca00",
    "hash": "0xbc78ab8a9e9a0bca7d0321a27b2c03addeae08ba81ea98b03cd3dd237eabed44",
    "input": "0x",
    "nonce": "0x33b79d",
    "to": "0xc67f4e626ee4d3f272c2fb31bad60761ab55ed9f",
    "transactionIndex": "0x5b",
    "value": "0x19755d4ce12c00",
    "type": "0x2",
    "accessList": [],
    "chainId": "0x1",
    "v": "0x0",
    "r": "0xa681faea68ff81d191169010888bbbe90ec3eb903e31b0572cd34f13dae281b9",
    "s": "0x3f59b0fa5ce6cf38aff2cfeb68e7a503ceda2a72b4442c7e2844d63544383e3",
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
    "blockHash": "0xf850331061196b8f2b67e1f43aaa9e69504c059d3d3fb9547b04f9ed4d141ab7",
    "blockNumber": "0xcf2420",
    "from": "0x00192fb10df37c9fb26829eb2cc623cd1bf599e8",
    "gas": "0x5208",
    "gasPrice": "0x19f017ef49",
    "maxFeePerGas": "0x1f6ea08600",
    "maxPriorityFeePerGas": "0x3b9aca00",
    "hash": "0xbc78ab8a9e9a0bca7d0321a27b2c03addeae08ba81ea98b03cd3dd237eabed44",
    "input": "0x",
    "nonce": "0x33b79d",
    "to": "0xc67f4e626ee4d3f272c2fb31bad60761ab55ed9f",
    "transactionIndex": "0x5b",
    "value": "0x19755d4ce12c00",
    "type": "0x2",
    "accessList": [],
    "chainId": "0x1",
    "v": "0x0",
    "r": "0xa681faea68ff81d191169010888bbbe90ec3eb903e31b0572cd34f13dae281b9",
    "s": "0x3f59b0fa5ce6cf38aff2cfeb68e7a503ceda2a72b4442c7e2844d63544383e3",
    "yParity": "0x0"
  }
}
```

#### Authorizations

[​](#authorization-apikey)apikeystringqueryrequiredEnter your Etherscan API key, or [set one up](https://docs.etherscan.io/set-up-your-api-key) if you don't have one.

#### Query Parameters

[​](#parameter-chainid)chainidstringrequiredChain ID to query, eg 1 for Ethereum, 42161 for Arbitrum from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:proxyrequiredSet to proxy for this endpoint.

[​](#parameter-action)actionstringdefault:eth_getTransactionByHashrequiredSet to eth_getTransactionByHash for this endpoint.

[​](#parameter-txhash)txhashstringrequiredThe transaction hash to query.

#### Response

200 - application/jsonSuccessful response

[​](#response-jsonrpc)jsonrpcstringJSON-RPC protocol version.

[​](#response-id)idintegerRequest identifier, echoed back from the request.

[​](#response-result)resultobjectShow child attributes

[eth_getBlockTransactionCountByNumber](https://docs.etherscan.io/api-reference/endpoint/ethgetblocktransactioncountbynumber)[eth_getTransactionByBlockNumberAndIndex](https://docs.etherscan.io/api-reference/endpoint/ethgettransactionbyblocknumberandindex)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)