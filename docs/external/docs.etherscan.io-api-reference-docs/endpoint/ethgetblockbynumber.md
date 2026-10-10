# eth\_getBlockByNumber

> Source: https://docs.etherscan.io/api-reference/endpoint/ethgetblockbynumber

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/ethgetblockbynumber#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/ethgetblockbynumber","name":"eth_getBlockByNumber","description":"Get block information by number.","dateModified":"2026-08-20T09:11:04.417Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/ethgetblockbynumber#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/ethgetblockbynumber#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Geth/Parity Proxy","item":"https://docs.etherscan.io/api-reference/endpoint/ethblocknumber"},{"@type":"ListItem","position":3,"name":"eth_getBlockByNumber","item":"https://docs.etherscan.io/api-reference/endpoint/ethgetblockbynumber"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/ethgetblockbynumber#apireference","headline":"eth_getBlockByNumber","name":"eth_getBlockByNumber","description":"Get block information by number.","url":"https://docs.etherscan.io/api-reference/endpoint/ethgetblockbynumber","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/ethgetblockbynumber#webpage"},"dateModified":"2026-08-20T09:11:04.417Z","keywords":"eth_getBlockByNumber, block details","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

eth_getBlockByNumbercURL

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
    "difficulty": "0x1d95715bd14",
    "extraData": "0x",
    "gasLimit": "0x2fefd8",
    "gasUsed": "0x5208",
    "hash": "0x7eb7c23a5ac2f2d70aa1ba4e5c56d89de5ac993590e5f6e79c394e290d998ba8",
    "logsBloom": "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "miner": "0xf927a40c8b7f6e07c5af7fa2155b4864a4112b13",
    "mixHash": "0x13dd2c8aec729f75aebcd79a916ecb0f7edc6493efcc6a4da8d7b0ab3ee88444",
    "nonce": "0xc60a782e2e69ce22",
    "number": "0x10d4f",
    "parentHash": "0xf8d01370e6e274f8188954fbee435b40c35b2ad3d4ab671f6d086cd559e48f04",
    "receiptsRoot": "0x0c44b7ed0fefb613ec256341aa0ffdb643e869e3a0ebc8f58e36b4e47efedd33",
    "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
    "size": "0x275",
    "stateRoot": "0xd64a0f63e2c7f541e6e6f8548a10a5c4e49fda7ac1aa80f9dddef648c7b9e25f",
    "timestamp": "0x55c9ea07",
    "transactions": [
      {
        "blockHash": "0x7eb7c23a5ac2f2d70aa1ba4e5c56d89de5ac993590e5f6e79c394e290d998ba8",
        "blockNumber": "0x10d4f",
        "from": "0x4458f86353b4740fe9e09071c23a7437640063c9",
        "gas": "0x5208",
        "gasPrice": "0xba43b7400",
        "hash": "0xa442249820de6be754da81eafbd44a865773e4b23d7c0522d31fd03977823008",
        "input": "0x",
        "nonce": "0x1",
        "to": "0xbf3403210f9802205f426759947a80a9fda71b1e",
        "transactionIndex": "0x0",
        "value": "0xaa9f075c200000",
        "type": "0x0",
        "v": "0x1b",
        "r": "0x2c2789c6704ba2606e200e1ba4fd17ba4f0e0f94abe32a12733708c3d3442616",
        "s": "0x2946f47e3ece580b5b5ecb0f8c52604fa5f60aeb4103fc73adcbf6d620f9872b"
      }
    ],
    "transactionsRoot": "0x4a5b78c13d11559c9541576834b5172fe8b18507c0f9f76454fcdddedd8dff7a",
    "uncles": []
  }
}
```

Geth/Parity Proxy
# eth_getBlockByNumber

Copy pageCopy pageGet block information by number.

Copy pageCopy pageGET/v2/apiTry iteth_getBlockByNumbercURL

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
    "difficulty": "0x1d95715bd14",
    "extraData": "0x",
    "gasLimit": "0x2fefd8",
    "gasUsed": "0x5208",
    "hash": "0x7eb7c23a5ac2f2d70aa1ba4e5c56d89de5ac993590e5f6e79c394e290d998ba8",
    "logsBloom": "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "miner": "0xf927a40c8b7f6e07c5af7fa2155b4864a4112b13",
    "mixHash": "0x13dd2c8aec729f75aebcd79a916ecb0f7edc6493efcc6a4da8d7b0ab3ee88444",
    "nonce": "0xc60a782e2e69ce22",
    "number": "0x10d4f",
    "parentHash": "0xf8d01370e6e274f8188954fbee435b40c35b2ad3d4ab671f6d086cd559e48f04",
    "receiptsRoot": "0x0c44b7ed0fefb613ec256341aa0ffdb643e869e3a0ebc8f58e36b4e47efedd33",
    "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
    "size": "0x275",
    "stateRoot": "0xd64a0f63e2c7f541e6e6f8548a10a5c4e49fda7ac1aa80f9dddef648c7b9e25f",
    "timestamp": "0x55c9ea07",
    "transactions": [
      {
        "blockHash": "0x7eb7c23a5ac2f2d70aa1ba4e5c56d89de5ac993590e5f6e79c394e290d998ba8",
        "blockNumber": "0x10d4f",
        "from": "0x4458f86353b4740fe9e09071c23a7437640063c9",
        "gas": "0x5208",
        "gasPrice": "0xba43b7400",
        "hash": "0xa442249820de6be754da81eafbd44a865773e4b23d7c0522d31fd03977823008",
        "input": "0x",
        "nonce": "0x1",
        "to": "0xbf3403210f9802205f426759947a80a9fda71b1e",
        "transactionIndex": "0x0",
        "value": "0xaa9f075c200000",
        "type": "0x0",
        "v": "0x1b",
        "r": "0x2c2789c6704ba2606e200e1ba4fd17ba4f0e0f94abe32a12733708c3d3442616",
        "s": "0x2946f47e3ece580b5b5ecb0f8c52604fa5f60aeb4103fc73adcbf6d620f9872b"
      }
    ],
    "transactionsRoot": "0x4a5b78c13d11559c9541576834b5172fe8b18507c0f9f76454fcdddedd8dff7a",
    "uncles": []
  }
}
```

Example response
```
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "difficulty": "0x1d95715bd14",
    "extraData": "0x",
    "gasLimit": "0x2fefd8",
    "gasUsed": "0x5208",
    "hash": "0x7eb7c23a5ac2f2d70aa1ba4e5c56d89de5ac993590e5f6e79c394e290d998ba8",
    "logsBloom": "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "miner": "0xf927a40c8b7f6e07c5af7fa2155b4864a4112b13",
    "mixHash": "0x13dd2c8aec729f75aebcd79a916ecb0f7edc6493efcc6a4da8d7b0ab3ee88444",
    "nonce": "0xc60a782e2e69ce22",
    "number": "0x10d4f",
    "parentHash": "0xf8d01370e6e274f8188954fbee435b40c35b2ad3d4ab671f6d086cd559e48f04",
    "receiptsRoot": "0x0c44b7ed0fefb613ec256341aa0ffdb643e869e3a0ebc8f58e36b4e47efedd33",
    "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
    "size": "0x275",
    "stateRoot": "0xd64a0f63e2c7f541e6e6f8548a10a5c4e49fda7ac1aa80f9dddef648c7b9e25f",
    "timestamp": "0x55c9ea07",
    "transactions": [
      {
        "blockHash": "0x7eb7c23a5ac2f2d70aa1ba4e5c56d89de5ac993590e5f6e79c394e290d998ba8",
        "blockNumber": "0x10d4f",
        "from": "0x4458f86353b4740fe9e09071c23a7437640063c9",
        "gas": "0x5208",
        "gasPrice": "0xba43b7400",
        "hash": "0xa442249820de6be754da81eafbd44a865773e4b23d7c0522d31fd03977823008",
        "input": "0x",
        "nonce": "0x1",
        "to": "0xbf3403210f9802205f426759947a80a9fda71b1e",
        "transactionIndex": "0x0",
        "value": "0xaa9f075c200000",
        "type": "0x0",
        "v": "0x1b",
        "r": "0x2c2789c6704ba2606e200e1ba4fd17ba4f0e0f94abe32a12733708c3d3442616",
        "s": "0x2946f47e3ece580b5b5ecb0f8c52604fa5f60aeb4103fc73adcbf6d620f9872b"
      }
    ],
    "transactionsRoot": "0x4a5b78c13d11559c9541576834b5172fe8b18507c0f9f76454fcdddedd8dff7a",
    "uncles": []
  }
}
```

#### Authorizations

[​](#authorization-apikey)apikeystringqueryrequiredEnter your Etherscan API key, or [set one up](https://docs.etherscan.io/set-up-your-api-key) if you don't have one.

#### Query Parameters

[​](#parameter-chainid)chainidstringrequiredChain ID to query, eg 1 for Ethereum, 42161 for Arbitrum from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:proxyrequiredSet to proxy for this endpoint.

[​](#parameter-action)actionstringdefault:eth_getBlockByNumberrequiredSet to eth_getBlockByNumber for this endpoint.

[​](#parameter-tag)tagstringBlock number in hex format eg 0x10d4f or "latest".

[​](#parameter-boolean)booleanstringrequiredSet to true to return full transaction objects or false for transaction hashes only.

#### Response

200 - application/jsonSuccessful response

[​](#response-jsonrpc)jsonrpcstringJSON-RPC protocol version.

[​](#response-id)idintegerRequest identifier, echoed back from the request.

[​](#response-result)resultobjectShow child attributes

[eth_blockNumber](https://docs.etherscan.io/api-reference/endpoint/ethblocknumber)[eth_getUncleByBlockNumberAndIndex](https://docs.etherscan.io/api-reference/endpoint/ethgetunclebyblocknumberandindex)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)