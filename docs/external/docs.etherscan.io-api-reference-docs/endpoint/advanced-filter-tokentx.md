# ERC20 Token Transfers Advanced Filter

> Source: https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokentx

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokentx#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokentx","name":"ERC20 Token Transfers Advanced Filter","description":"Retrieves ERC20 token transfers with advanced from and to address filtering.","dateModified":"2026-08-20T09:11:04.425Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokentx#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokentx#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Account","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":3,"name":"ERC20 Token Transfers Advanced Filter","item":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokentx"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokentx#apireference","headline":"ERC20 Token Transfers Advanced Filter","name":"ERC20 Token Transfers Advanced Filter","description":"Retrieves ERC20 token transfers with advanced from and to address filtering.","url":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokentx","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-tokentx#webpage"},"dateModified":"2026-08-20T09:11:04.425Z","keywords":"advanced filter, ERC20 transfers, tokentx, from, to, fromto_opr","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

ERC20 Token Transfers Advanced FiltercURL

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
      "blockNumber": "4730207",
      "timeStamp": "1513240363",
      "hash": "0xe8c208398bd5ae8e4c237658580db56a2a94dfa0ca382c99b776fa6e7d31d5b4",
      "nonce": "406",
      "blockHash": "0x022c5e6a3d2487a8ccf8946a2ffb74938bf8e5c8a3f6d91b41c56378a96b5c37",
      "from": "0x642ae78fafbb8032da552d619ad43f1d81e4dd7c",
      "contractAddress": "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2",
      "to": "0x4e83362442b8d1bec281594cea3050c8eb01311c",
      "value": "5901522149285533025181",
      "tokenName": "Maker",
      "tokenSymbol": "MKR",
      "tokenDecimal": "18",
      "transactionIndex": "81",
      "gas": "940000",
      "gasPrice": "32010000000",
      "gasUsed": "77759",
      "cumulativeGasUsed": "2523379",
      "input": "deprecated",
      "methodId": "0xbe040fb0",
      "functionName": "redeem()",
      "confirmations": "18737452"
    }
  ]
}
```

Account
# ERC20 Token Transfers Advanced Filter

Copy pageCopy pageRetrieves ERC20 token transfers with advanced from and to address filtering.

Copy pageCopy pageGET/v2/apiTry itERC20 Token Transfers Advanced FiltercURL

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
      "blockNumber": "4730207",
      "timeStamp": "1513240363",
      "hash": "0xe8c208398bd5ae8e4c237658580db56a2a94dfa0ca382c99b776fa6e7d31d5b4",
      "nonce": "406",
      "blockHash": "0x022c5e6a3d2487a8ccf8946a2ffb74938bf8e5c8a3f6d91b41c56378a96b5c37",
      "from": "0x642ae78fafbb8032da552d619ad43f1d81e4dd7c",
      "contractAddress": "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2",
      "to": "0x4e83362442b8d1bec281594cea3050c8eb01311c",
      "value": "5901522149285533025181",
      "tokenName": "Maker",
      "tokenSymbol": "MKR",
      "tokenDecimal": "18",
      "transactionIndex": "81",
      "gas": "940000",
      "gasPrice": "32010000000",
      "gasUsed": "77759",
      "cumulativeGasUsed": "2523379",
      "input": "deprecated",
      "methodId": "0xbe040fb0",
      "functionName": "redeem()",
      "confirmations": "18737452"
    }
  ]
}
```

Beta
Explore and preview data from our [Advanced Filter](https://etherscan.io/advanced-filter) page.
Example response
```
{
  "status": "1",
  "message": "OK",
  "result": [
    {
      "blockNumber": "4730207",
      "timeStamp": "1513240363",
      "hash": "0xe8c208398bd5ae8e4c237658580db56a2a94dfa0ca382c99b776fa6e7d31d5b4",
      "nonce": "406",
      "blockHash": "0x022c5e6a3d2487a8ccf8946a2ffb74938bf8e5c8a3f6d91b41c56378a96b5c37",
      "from": "0x642ae78fafbb8032da552d619ad43f1d81e4dd7c",
      "contractAddress": "0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2",
      "to": "0x4e83362442b8d1bec281594cea3050c8eb01311c",
      "value": "5901522149285533025181",
      "tokenName": "Maker",
      "tokenSymbol": "MKR",
      "tokenDecimal": "18",
      "transactionIndex": "81",
      "gas": "940000",
      "gasPrice": "32010000000",
      "gasUsed": "77759",
      "cumulativeGasUsed": "2523379",
      "input": "deprecated",
      "methodId": "0xbe040fb0",
      "functionName": "redeem()",
      "confirmations": "18737452"
    }
  ]
}
```

#### Authorizations

[​](#authorization-apikey)apikeystringqueryrequiredEnter your Etherscan API key, or [set one up](https://docs.etherscan.io/set-up-your-api-key) if you don't have one.

#### Query Parameters

[​](#parameter-chainid)chainidstringrequiredChain ID to query, such as 1 for Ethereum or 42161 for Arbitrum from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:accountrequiredSet to account for this endpoint.

[​](#parameter-action)actionstringdefault:tokentxrequiredSet to tokentx for this endpoint.

[​](#parameter-contractaddress)contractaddressstringThe ERC20 token contract address to filter transfers by. Provide contractaddress, from, or to.

[​](#parameter-from)fromstringThe sender address to filter transfers by. Provide from, to, or contractaddress.

[​](#parameter-to)tostringThe recipient address to filter transfers by. Provide to, from, or contractaddress.

[​](#parameter-fromto-opr)fromto_oprstringRequired when from or to is provided. Use and when both addresses must match, or or when either address can match.

[​](#parameter-startblock)startblockintegerStarting block number to search from.

[​](#parameter-endblock)endblockstringEnding block number to search to, or latest for the latest block.

[​](#parameter-sort)sortstringSort order, either `desc` for the latest transactions first or `asc` for the oldest transactions first.

[​](#parameter-page)pageintegerPage number for pagination.

[​](#parameter-offset)offsetintegerNumber of records per page. Use the page parameter for subsequent records.

#### Response

200 - application/jsonSuccessful response

[​](#response-status)statusstring1 if the request returned data, 0 otherwise. A status of 0 can indicate an error or a valid request that returned no records.

[​](#response-message)messagestringOK on success, otherwise an error description such as NOTOK. See [common error messages](https://docs.etherscan.io/common-error-messages).

[​](#response-result)resultobject[]Show child attributes

[Get ERC20 Token Transfers by Address](https://docs.etherscan.io/api-reference/endpoint/tokentx)[Get ERC721 Token Transfers by Address](https://docs.etherscan.io/api-reference/endpoint/tokennfttx)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)