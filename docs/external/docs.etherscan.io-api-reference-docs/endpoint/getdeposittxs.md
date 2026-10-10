# Get Deposit Transactions by Address

> Source: https://docs.etherscan.io/api-reference/endpoint/getdeposittxs

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/getdeposittxs#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/getdeposittxs","name":"Get Deposit Transactions by Address","description":"Retrieves all deposit transactions made by a specified address.","dateModified":"2026-08-20T09:11:04.089Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/getdeposittxs#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/getdeposittxs#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"L2 Deposits/Withdrawals","item":"https://docs.etherscan.io/api-reference/endpoint/txnbridge"},{"@type":"ListItem","position":3,"name":"Get Deposit Transactions by Address","item":"https://docs.etherscan.io/api-reference/endpoint/getdeposittxs"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/getdeposittxs#apireference","headline":"Get Deposit Transactions by Address","name":"Get Deposit Transactions by Address","description":"Retrieves all deposit transactions made by a specified address.","url":"https://docs.etherscan.io/api-reference/endpoint/getdeposittxs","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/getdeposittxs#webpage"},"dateModified":"2026-08-20T09:11:04.089Z","keywords":"deposit transactions, getdeposittxs","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

Get Deposit Transactions by AddresscURL

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
      "blockNumber": "132992375",
      "timeStamp": "1741583527",
      "blockHash": "0xef2ff158c8b12be842429f4a8cde58bfa6a389c5274b46f8a1dd2ee7f958ca4d",
      "hash": "0x64ccd0cfa9f333578b36227492f3bc7f5f3ec4bfa82cdc46f82884db680d8e5b",
      "nonce": "520502",
      "from": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "to": "0x4200000000000000000000000000000000000007",
      "value": "598200000000000",
      "gas": "490798",
      "gasPrice": "0",
      "input": "0xd764ad0b000100000000000000000000000000000000000000000000000000000002802a00000000000000000000000099c9fc46f92e8a1c0dec1b1747d010903e884be10000000000000000000000004200000000000000000000000000000000000001000000000000000000000000000000000000000000000000000002200f4a81300000000000000000000000000000000000000000000000000000000000000030d4000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000a41635f5fd0000000000000000000000001231deb6f5749ef6ce6943a275a1d3e7486f4eae00000000000000000000000080f3950a4d371c43360f292a4170624abd9eed03000000000000000000000000000000000000000000000000000002200f4a813000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
      "cumulativeGasUsed": "169497",
      "gasUsed": "117234",
      "isError": "0",
      "errDescription": "",
      "txreceipt_status": "1",
      "queueIndex": "999999",
      "L1transactionhash": "0x303bd05c47e62e1243a33210e535ebc70a7567e53a9972fbdef52ee5bcda5acb",
      "L1TxOrigin": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "tokenAddress": "ETH",
      "tokenSentFrom": "",
      "tokenSentTo": "0x80f3950a4d371c43360f292a4170624abd9eed03",
      "tokenValue": "598200000000000"
    },
    {
      "blockNumber": "134878032",
      "timeStamp": "1745354841",
      "blockHash": "0xd1a47b46e3aaed25c594507cf9df59c9ba7a25542fabed7e2b646efe8b6944f9",
      "hash": "0xb7cbf6eb529f60b28c6707a52e17c84e75bbe0a968e668a29e5a7550bfb00e92",
      "nonce": "527247",
      "from": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "to": "0x4200000000000000000000000000000000000007",
      "value": "1195403000000000",
      "gas": "490798",
      "gasPrice": "0",
      "input": "0xd764ad0b0001000000000000000000000000000000000000000000000000000000029a8300000000000000000000000099c9fc46f92e8a1c0dec1b1747d010903e884be100000000000000000000000042000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000043f36732dae00000000000000000000000000000000000000000000000000000000000000030d4000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000a41635f5fd0000000000000000000000001231deb6f5749ef6ce6943a275a1d3e7486f4eae00000000000000000000000080f3950a4d371c43360f292a4170624abd9eed030000000000000000000000000000000000000000000000000000043f36732dae000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
      "cumulativeGasUsed": "147297",
      "gasUsed": "92234",
      "isError": "0",
      "errDescription": "",
      "txreceipt_status": "1",
      "queueIndex": "999999",
      "L1transactionhash": "0xdca5992b97fcb3d2aa4d06f8c47c0786c0007009d15445712931ee0998f94caa",
      "L1TxOrigin": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "tokenAddress": "ETH",
      "tokenSentFrom": "",
      "tokenSentTo": "0x80f3950a4d371c43360f292a4170624abd9eed03",
      "tokenValue": "1195403000000000"
    }
  ]
}
```

L2 Deposits/Withdrawals
# Get Deposit Transactions by Address

Copy pageCopy pageRetrieves all deposit transactions made by a specified address.

Copy pageCopy pageGET/v2/apiTry itGet Deposit Transactions by AddresscURL

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
      "blockNumber": "132992375",
      "timeStamp": "1741583527",
      "blockHash": "0xef2ff158c8b12be842429f4a8cde58bfa6a389c5274b46f8a1dd2ee7f958ca4d",
      "hash": "0x64ccd0cfa9f333578b36227492f3bc7f5f3ec4bfa82cdc46f82884db680d8e5b",
      "nonce": "520502",
      "from": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "to": "0x4200000000000000000000000000000000000007",
      "value": "598200000000000",
      "gas": "490798",
      "gasPrice": "0",
      "input": "0xd764ad0b000100000000000000000000000000000000000000000000000000000002802a00000000000000000000000099c9fc46f92e8a1c0dec1b1747d010903e884be10000000000000000000000004200000000000000000000000000000000000001000000000000000000000000000000000000000000000000000002200f4a81300000000000000000000000000000000000000000000000000000000000000030d4000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000a41635f5fd0000000000000000000000001231deb6f5749ef6ce6943a275a1d3e7486f4eae00000000000000000000000080f3950a4d371c43360f292a4170624abd9eed03000000000000000000000000000000000000000000000000000002200f4a813000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
      "cumulativeGasUsed": "169497",
      "gasUsed": "117234",
      "isError": "0",
      "errDescription": "",
      "txreceipt_status": "1",
      "queueIndex": "999999",
      "L1transactionhash": "0x303bd05c47e62e1243a33210e535ebc70a7567e53a9972fbdef52ee5bcda5acb",
      "L1TxOrigin": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "tokenAddress": "ETH",
      "tokenSentFrom": "",
      "tokenSentTo": "0x80f3950a4d371c43360f292a4170624abd9eed03",
      "tokenValue": "598200000000000"
    },
    {
      "blockNumber": "134878032",
      "timeStamp": "1745354841",
      "blockHash": "0xd1a47b46e3aaed25c594507cf9df59c9ba7a25542fabed7e2b646efe8b6944f9",
      "hash": "0xb7cbf6eb529f60b28c6707a52e17c84e75bbe0a968e668a29e5a7550bfb00e92",
      "nonce": "527247",
      "from": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "to": "0x4200000000000000000000000000000000000007",
      "value": "1195403000000000",
      "gas": "490798",
      "gasPrice": "0",
      "input": "0xd764ad0b0001000000000000000000000000000000000000000000000000000000029a8300000000000000000000000099c9fc46f92e8a1c0dec1b1747d010903e884be100000000000000000000000042000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000043f36732dae00000000000000000000000000000000000000000000000000000000000000030d4000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000a41635f5fd0000000000000000000000001231deb6f5749ef6ce6943a275a1d3e7486f4eae00000000000000000000000080f3950a4d371c43360f292a4170624abd9eed030000000000000000000000000000000000000000000000000000043f36732dae000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
      "cumulativeGasUsed": "147297",
      "gasUsed": "92234",
      "isError": "0",
      "errDescription": "",
      "txreceipt_status": "1",
      "queueIndex": "999999",
      "L1transactionhash": "0xdca5992b97fcb3d2aa4d06f8c47c0786c0007009d15445712931ee0998f94caa",
      "L1TxOrigin": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "tokenAddress": "ETH",
      "tokenSentFrom": "",
      "tokenSentTo": "0x80f3950a4d371c43360f292a4170624abd9eed03",
      "tokenValue": "1195403000000000"
    }
  ]
}
```

Arbitrum One Mainnet
Arbitrum Sepolia Testnet
OP Mainnet
OP Sepolia Testnet
Example response
```
{
  "status": "1",
  "message": "OK",
  "result": [
    {
      "blockNumber": "132992375",
      "timeStamp": "1741583527",
      "blockHash": "0xef2ff158c8b12be842429f4a8cde58bfa6a389c5274b46f8a1dd2ee7f958ca4d",
      "hash": "0x64ccd0cfa9f333578b36227492f3bc7f5f3ec4bfa82cdc46f82884db680d8e5b",
      "nonce": "520502",
      "from": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "to": "0x4200000000000000000000000000000000000007",
      "value": "598200000000000",
      "gas": "490798",
      "gasPrice": "0",
      "input": "0xd764ad0b000100000000000000000000000000000000000000000000000000000002802a00000000000000000000000099c9fc46f92e8a1c0dec1b1747d010903e884be10000000000000000000000004200000000000000000000000000000000000001000000000000000000000000000000000000000000000000000002200f4a81300000000000000000000000000000000000000000000000000000000000000030d4000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000a41635f5fd0000000000000000000000001231deb6f5749ef6ce6943a275a1d3e7486f4eae00000000000000000000000080f3950a4d371c43360f292a4170624abd9eed03000000000000000000000000000000000000000000000000000002200f4a813000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
      "cumulativeGasUsed": "169497",
      "gasUsed": "117234",
      "isError": "0",
      "errDescription": "",
      "txreceipt_status": "1",
      "queueIndex": "999999",
      "L1transactionhash": "0x303bd05c47e62e1243a33210e535ebc70a7567e53a9972fbdef52ee5bcda5acb",
      "L1TxOrigin": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "tokenAddress": "ETH",
      "tokenSentFrom": "",
      "tokenSentTo": "0x80f3950a4d371c43360f292a4170624abd9eed03",
      "tokenValue": "598200000000000"
    },
    {
      "blockNumber": "134878032",
      "timeStamp": "1745354841",
      "blockHash": "0xd1a47b46e3aaed25c594507cf9df59c9ba7a25542fabed7e2b646efe8b6944f9",
      "hash": "0xb7cbf6eb529f60b28c6707a52e17c84e75bbe0a968e668a29e5a7550bfb00e92",
      "nonce": "527247",
      "from": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "to": "0x4200000000000000000000000000000000000007",
      "value": "1195403000000000",
      "gas": "490798",
      "gasPrice": "0",
      "input": "0xd764ad0b0001000000000000000000000000000000000000000000000000000000029a8300000000000000000000000099c9fc46f92e8a1c0dec1b1747d010903e884be100000000000000000000000042000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000043f36732dae00000000000000000000000000000000000000000000000000000000000000030d4000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000a41635f5fd0000000000000000000000001231deb6f5749ef6ce6943a275a1d3e7486f4eae00000000000000000000000080f3950a4d371c43360f292a4170624abd9eed030000000000000000000000000000000000000000000000000000043f36732dae000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
      "cumulativeGasUsed": "147297",
      "gasUsed": "92234",
      "isError": "0",
      "errDescription": "",
      "txreceipt_status": "1",
      "queueIndex": "999999",
      "L1transactionhash": "0xdca5992b97fcb3d2aa4d06f8c47c0786c0007009d15445712931ee0998f94caa",
      "L1TxOrigin": "0x36bde71c97b33cc4729cf772ae268934f7ab70b2",
      "tokenAddress": "ETH",
      "tokenSentFrom": "",
      "tokenSentTo": "0x80f3950a4d371c43360f292a4170624abd9eed03",
      "tokenValue": "1195403000000000"
    }
  ]
}
```

#### Authorizations

[​](#authorization-apikey)apikeystringqueryrequiredEnter your Etherscan API key, or [set one up](https://docs.etherscan.io/set-up-your-api-key) if you don't have one.

#### Query Parameters

[​](#parameter-chainid)chainidstringrequiredChain ID to query, eg 10 for Optimism or 42161 for Arbitrum from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:accountrequiredSet to account for this endpoint.

[​](#parameter-action)actionstringdefault:getdeposittxsrequiredSet to getdeposittxs for this endpoint.

[​](#parameter-address)addressstringrequiredAddress to check for cross-chain deposits from Ethereum to L2.

[​](#parameter-page)pageintegerPage number for pagination.

[​](#parameter-offset)offsetintegerNumber of records per page. Use the page parameter for subsequent records.

[​](#parameter-sort)sortstringSort order either `desc` for the latest transactions first or `asc` for the oldest transactions first.

#### Response

200 - application/jsonSuccessful response

[​](#response-status)statusstring1 if the request returned data, 0 otherwise. A status of 0 can indicate an error or a valid request that returned no records.

[​](#response-message)messagestringOK on success, otherwise an error description such as NOTOK. See [common error messages](https://docs.etherscan.io/common-error-messages).

[​](#response-result)resultobject[]Show child attributes

[Get Plasma Deposits by Address](https://docs.etherscan.io/api-reference/endpoint/txnbridge)[Get Withdrawal Transactions by Address](https://docs.etherscan.io/api-reference/endpoint/getwithdrawaltxs)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)