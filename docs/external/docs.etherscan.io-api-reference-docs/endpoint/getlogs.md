# Get Event Logs by Address

> Source: https://docs.etherscan.io/api-reference/endpoint/getlogs

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/getlogs#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/getlogs","name":"Get Event Logs by Address","description":"Retrieves event logs from a specific address, with optional block range filtering.","dateModified":"2026-08-20T09:11:04.088Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/getlogs#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/getlogs#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Get Event Logs by Address","item":"https://docs.etherscan.io/api-reference/endpoint/getlogs"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/getlogs#apireference","headline":"Get Event Logs by Address","name":"Get Event Logs by Address","description":"Retrieves event logs from a specific address, with optional block range filtering.","url":"https://docs.etherscan.io/api-reference/endpoint/getlogs","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/getlogs#webpage"},"dateModified":"2026-08-20T09:11:04.088Z","keywords":"event logs, address logs","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

Get Event Logs by AddresscURL

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
      "address": "0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
      "topics": [
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        "0x0000000000000000000000000000000000000000000000000000000000000000",
        "0x000000000000000000000000c45a4b3b698f21f88687548e7f5a80df8b99d93d",
        "0x00000000000000000000000000000000000000000000000000000000000000b5"
      ],
      "data": "0x",
      "blockNumber": "0xc48174",
      "blockHash": "0x837e109ab8b1b40ec7d1032bff82397325d85e719b97d900fa0d9aa9745b2c27",
      "timeStamp": "0x60f9ce56",
      "gasPrice": "0x2e90edd000",
      "gasUsed": "0x247205",
      "logIndex": "0x",
      "transactionHash": "0x4ffd22d986913d33927a392fe4319bcd2b62f3afe1c15a2c59f77fc2cc4c20a9",
      "transactionIndex": "0x"
    },
    {
      "address": "0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
      "topics": [
        "0x645f26e653c951cec836533f8fe0616d301c20a17153debc17d7c3dbe4f32b28",
        "0x00000000000000000000000000000000000000000000000000000000000000b5"
      ],
      "data": "0x",
      "blockNumber": "0xc48174",
      "blockHash": "0x837e109ab8b1b40ec7d1032bff82397325d85e719b97d900fa0d9aa9745b2c27",
      "timeStamp": "0x60f9ce56",
      "gasPrice": "0x2e90edd000",
      "gasUsed": "0x247205",
      "logIndex": "0x1",
      "transactionHash": "0x4ffd22d986913d33927a392fe4319bcd2b62f3afe1c15a2c59f77fc2cc4c20a9",
      "transactionIndex": "0x"
    }
  ]
}
```

Logs
# Get Event Logs by Address

Copy pageCopy pageRetrieves event logs from a specific address, with optional block range filtering.

Copy pageCopy pageGET/v2/apiTry itGet Event Logs by AddresscURL

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
      "address": "0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
      "topics": [
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        "0x0000000000000000000000000000000000000000000000000000000000000000",
        "0x000000000000000000000000c45a4b3b698f21f88687548e7f5a80df8b99d93d",
        "0x00000000000000000000000000000000000000000000000000000000000000b5"
      ],
      "data": "0x",
      "blockNumber": "0xc48174",
      "blockHash": "0x837e109ab8b1b40ec7d1032bff82397325d85e719b97d900fa0d9aa9745b2c27",
      "timeStamp": "0x60f9ce56",
      "gasPrice": "0x2e90edd000",
      "gasUsed": "0x247205",
      "logIndex": "0x",
      "transactionHash": "0x4ffd22d986913d33927a392fe4319bcd2b62f3afe1c15a2c59f77fc2cc4c20a9",
      "transactionIndex": "0x"
    },
    {
      "address": "0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
      "topics": [
        "0x645f26e653c951cec836533f8fe0616d301c20a17153debc17d7c3dbe4f32b28",
        "0x00000000000000000000000000000000000000000000000000000000000000b5"
      ],
      "data": "0x",
      "blockNumber": "0xc48174",
      "blockHash": "0x837e109ab8b1b40ec7d1032bff82397325d85e719b97d900fa0d9aa9745b2c27",
      "timeStamp": "0x60f9ce56",
      "gasPrice": "0x2e90edd000",
      "gasUsed": "0x247205",
      "logIndex": "0x1",
      "transactionHash": "0x4ffd22d986913d33927a392fe4319bcd2b62f3afe1c15a2c59f77fc2cc4c20a9",
      "transactionIndex": "0x"
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
      "address": "0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
      "topics": [
        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        "0x0000000000000000000000000000000000000000000000000000000000000000",
        "0x000000000000000000000000c45a4b3b698f21f88687548e7f5a80df8b99d93d",
        "0x00000000000000000000000000000000000000000000000000000000000000b5"
      ],
      "data": "0x",
      "blockNumber": "0xc48174",
      "blockHash": "0x837e109ab8b1b40ec7d1032bff82397325d85e719b97d900fa0d9aa9745b2c27",
      "timeStamp": "0x60f9ce56",
      "gasPrice": "0x2e90edd000",
      "gasUsed": "0x247205",
      "logIndex": "0x",
      "transactionHash": "0x4ffd22d986913d33927a392fe4319bcd2b62f3afe1c15a2c59f77fc2cc4c20a9",
      "transactionIndex": "0x"
    },
    {
      "address": "0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
      "topics": [
        "0x645f26e653c951cec836533f8fe0616d301c20a17153debc17d7c3dbe4f32b28",
        "0x00000000000000000000000000000000000000000000000000000000000000b5"
      ],
      "data": "0x",
      "blockNumber": "0xc48174",
      "blockHash": "0x837e109ab8b1b40ec7d1032bff82397325d85e719b97d900fa0d9aa9745b2c27",
      "timeStamp": "0x60f9ce56",
      "gasPrice": "0x2e90edd000",
      "gasUsed": "0x247205",
      "logIndex": "0x1",
      "transactionHash": "0x4ffd22d986913d33927a392fe4319bcd2b62f3afe1c15a2c59f77fc2cc4c20a9",
      "transactionIndex": "0x"
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

[​](#parameter-address)addressstringrequiredAddress to check for logs.

[​](#parameter-from-block)fromBlockintegerrequiredStarting block number to search from.

[​](#parameter-to-block)toBlockintegerrequiredEnding block number to search to.

[​](#parameter-page)pageintegerPage number for pagination.

[​](#parameter-offset)offsetintegerNumber of records per page. Use the page parameter for subsequent records.

#### Response

200 - application/jsonSuccessful response

[​](#response-status)statusstring1 if the request returned data, 0 otherwise. A status of 0 can indicate an error or a valid request that returned no records.

[​](#response-message)messagestringOK on success, otherwise an error description such as NOTOK. See [common error messages](https://docs.etherscan.io/common-error-messages).

[​](#response-result)resultobject[]Show child attributes

[eth_estimateGas](https://docs.etherscan.io/api-reference/endpoint/ethestimategas)[Get Event Logs by Topics](https://docs.etherscan.io/api-reference/endpoint/getlogs-topics)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)