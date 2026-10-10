# Get Event Logs by Address and Topics

> Source: https://docs.etherscan.io/api-reference/endpoint/getlogs-address-topics

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/getlogs-address-topics#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/getlogs-address-topics","name":"Get Event Logs by Address and Topics","description":"Retrieves event logs from a specified address, filtered by topics and block range.","dateModified":"2026-08-20T09:11:04.082Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/getlogs-address-topics#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/getlogs-address-topics#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Logs","item":"https://docs.etherscan.io/api-reference/endpoint/getlogs"},{"@type":"ListItem","position":3,"name":"Get Event Logs by Address and Topics","item":"https://docs.etherscan.io/api-reference/endpoint/getlogs-address-topics"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/getlogs-address-topics#apireference","headline":"Get Event Logs by Address and Topics","name":"Get Event Logs by Address and Topics","description":"Retrieves event logs from a specified address, filtered by topics and block range.","url":"https://docs.etherscan.io/api-reference/endpoint/getlogs-address-topics","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/getlogs-address-topics#webpage"},"dateModified":"2026-08-20T09:11:04.082Z","keywords":"event logs, address topics","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

Get Event Logs by Address and TopicscURL

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
      "address": "0x59728544b08ab483533076417fbbb2fd0b17ce3a",
      "topics": [
        "0x27c4f0403323142b599832f26acd21c74a9e5b809f2215726e244a4ac588cd7d",
        "0x00000000000000000000000023581767a106ae21c074b2276d25e5c3e136a68b",
        "0x000000000000000000000000000000000000000000000000000000000000236d",
        "0x000000000000000000000000c8a5592031f93debea5d9e67a396944ee01bb2ca"
      ],
      "data": "0x000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20000000000000000000000000000000000000000000000000f207539952d0000",
      "blockNumber": "0xe60262",
      "blockHash": "0xb40d77b4ffba5ae2a38cbc87a65a6c9b56f9af5d8bf320aa1f1b6af00b850778",
      "timeStamp": "0x62c26caf",
      "gasPrice": "0x5e2d742c9",
      "gasUsed": "0xfb7f8",
      "logIndex": "0x4b",
      "transactionHash": "0x26fe1a0a403fd44ef11ee72f3b4ceff590b6ea533684cb279cb4242be463304c",
      "transactionIndex": "0x39"
    },
    {
      "address": "0x59728544b08ab483533076417fbbb2fd0b17ce3a",
      "topics": [
        "0x27c4f0403323142b599832f26acd21c74a9e5b809f2215726e244a4ac588cd7d",
        "0x00000000000000000000000023581767a106ae21c074b2276d25e5c3e136a68b",
        "0x0000000000000000000000000000000000000000000000000000000000002261",
        "0x000000000000000000000000c8a5592031f93debea5d9e67a396944ee01bb2ca"
      ],
      "data": "0x000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20000000000000000000000000000000000000000000000000de0b6b3a7640000",
      "blockNumber": "0xe6035b",
      "blockHash": "0x5a46aeca5eaf8af1fbf56439b12dfea8fb27d18ca31020cc723271e119cffc04",
      "timeStamp": "0x62c27ab1",
      "gasPrice": "0x27e523173",
      "gasUsed": "0x3b86e",
      "logIndex": "0x1d7",
      "transactionHash": "0x3a299413cf2c91e376e542efcf3fc308c562da79af6e992401217cc6208c7f74",
      "transactionIndex": "0x92"
    }
  ]
}
```

Logs
# Get Event Logs by Address and Topics

Copy pageCopy pageRetrieves event logs from a specified address, filtered by topics and block range.

Copy pageCopy pageGET/v2/apiTry itGet Event Logs by Address and TopicscURL

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
      "address": "0x59728544b08ab483533076417fbbb2fd0b17ce3a",
      "topics": [
        "0x27c4f0403323142b599832f26acd21c74a9e5b809f2215726e244a4ac588cd7d",
        "0x00000000000000000000000023581767a106ae21c074b2276d25e5c3e136a68b",
        "0x000000000000000000000000000000000000000000000000000000000000236d",
        "0x000000000000000000000000c8a5592031f93debea5d9e67a396944ee01bb2ca"
      ],
      "data": "0x000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20000000000000000000000000000000000000000000000000f207539952d0000",
      "blockNumber": "0xe60262",
      "blockHash": "0xb40d77b4ffba5ae2a38cbc87a65a6c9b56f9af5d8bf320aa1f1b6af00b850778",
      "timeStamp": "0x62c26caf",
      "gasPrice": "0x5e2d742c9",
      "gasUsed": "0xfb7f8",
      "logIndex": "0x4b",
      "transactionHash": "0x26fe1a0a403fd44ef11ee72f3b4ceff590b6ea533684cb279cb4242be463304c",
      "transactionIndex": "0x39"
    },
    {
      "address": "0x59728544b08ab483533076417fbbb2fd0b17ce3a",
      "topics": [
        "0x27c4f0403323142b599832f26acd21c74a9e5b809f2215726e244a4ac588cd7d",
        "0x00000000000000000000000023581767a106ae21c074b2276d25e5c3e136a68b",
        "0x0000000000000000000000000000000000000000000000000000000000002261",
        "0x000000000000000000000000c8a5592031f93debea5d9e67a396944ee01bb2ca"
      ],
      "data": "0x000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20000000000000000000000000000000000000000000000000de0b6b3a7640000",
      "blockNumber": "0xe6035b",
      "blockHash": "0x5a46aeca5eaf8af1fbf56439b12dfea8fb27d18ca31020cc723271e119cffc04",
      "timeStamp": "0x62c27ab1",
      "gasPrice": "0x27e523173",
      "gasUsed": "0x3b86e",
      "logIndex": "0x1d7",
      "transactionHash": "0x3a299413cf2c91e376e542efcf3fc308c562da79af6e992401217cc6208c7f74",
      "transactionIndex": "0x92"
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
      "address": "0x59728544b08ab483533076417fbbb2fd0b17ce3a",
      "topics": [
        "0x27c4f0403323142b599832f26acd21c74a9e5b809f2215726e244a4ac588cd7d",
        "0x00000000000000000000000023581767a106ae21c074b2276d25e5c3e136a68b",
        "0x000000000000000000000000000000000000000000000000000000000000236d",
        "0x000000000000000000000000c8a5592031f93debea5d9e67a396944ee01bb2ca"
      ],
      "data": "0x000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20000000000000000000000000000000000000000000000000f207539952d0000",
      "blockNumber": "0xe60262",
      "blockHash": "0xb40d77b4ffba5ae2a38cbc87a65a6c9b56f9af5d8bf320aa1f1b6af00b850778",
      "timeStamp": "0x62c26caf",
      "gasPrice": "0x5e2d742c9",
      "gasUsed": "0xfb7f8",
      "logIndex": "0x4b",
      "transactionHash": "0x26fe1a0a403fd44ef11ee72f3b4ceff590b6ea533684cb279cb4242be463304c",
      "transactionIndex": "0x39"
    },
    {
      "address": "0x59728544b08ab483533076417fbbb2fd0b17ce3a",
      "topics": [
        "0x27c4f0403323142b599832f26acd21c74a9e5b809f2215726e244a4ac588cd7d",
        "0x00000000000000000000000023581767a106ae21c074b2276d25e5c3e136a68b",
        "0x0000000000000000000000000000000000000000000000000000000000002261",
        "0x000000000000000000000000c8a5592031f93debea5d9e67a396944ee01bb2ca"
      ],
      "data": "0x000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20000000000000000000000000000000000000000000000000de0b6b3a7640000",
      "blockNumber": "0xe6035b",
      "blockHash": "0x5a46aeca5eaf8af1fbf56439b12dfea8fb27d18ca31020cc723271e119cffc04",
      "timeStamp": "0x62c27ab1",
      "gasPrice": "0x27e523173",
      "gasUsed": "0x3b86e",
      "logIndex": "0x1d7",
      "transactionHash": "0x3a299413cf2c91e376e542efcf3fc308c562da79af6e992401217cc6208c7f74",
      "transactionIndex": "0x92"
    }
  ]
}
```

#### Authorizations

[​](#authorization-apikey)apikeystringqueryrequiredEnter your Etherscan API key, or [set one up](https://docs.etherscan.io/set-up-your-api-key) if you don't have one.

#### Query Parameters

[​](#parameter-chainid)chainidstringrequiredChain ID to query, eg 1 for Ethereum, 42161 for Arbitrum from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:logsrequiredSet to logs for this endpoint.

[​](#parameter-action)actionstringdefault:getLogsrequiredSet to getLogs for this endpoint.

[​](#parameter-from-block)fromBlockintegerrequiredStarting block number to search from.

[​](#parameter-to-block)toBlockintegerrequiredEnding block number to search to.

[​](#parameter-address)addressstringrequiredAddress to check for logs.

[​](#parameter-topic0)topic0stringFirst topic to filter by, such as an event signature.

[​](#parameter-topic0-1-opr)topic0_1_oprstringTopic operator between topic0 and topic1, either and or or.

[​](#parameter-topic1)topic1stringSecond topic to filter by.

[​](#parameter-page)pageintegerPage number for pagination.

[​](#parameter-offset)offsetintegerNumber of records per page. Use the page parameter for subsequent records.

#### Response

200 - application/jsonSuccessful response

[​](#response-status)statusstring1 if the request returned data, 0 otherwise. A status of 0 can indicate an error or a valid request that returned no records.

[​](#response-message)messagestringOK on success, otherwise an error description such as NOTOK. See [common error messages](https://docs.etherscan.io/common-error-messages).

[​](#response-result)resultobject[]Show child attributes

[Get Event Logs by Topics](https://docs.etherscan.io/api-reference/endpoint/getlogs-topics)[Get Total Supply of Ether](https://docs.etherscan.io/api-reference/endpoint/ethsupply)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)