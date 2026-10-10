# Get Address ERC20 Token Holding

> Source: https://docs.etherscan.io/api-reference/endpoint/addresstokenbalance

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/addresstokenbalance#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/addresstokenbalance","name":"Get Address ERC20 Token Holding","description":"Retrieves the list of ERC-20 tokens and balances held by a specified address.","dateModified":"2026-08-20T09:11:04.464Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/addresstokenbalance#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/addresstokenbalance#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Tokens","item":"https://docs.etherscan.io/api-reference/endpoint/tokensupply"},{"@type":"ListItem","position":3,"name":"Get Address ERC20 Token Holding","item":"https://docs.etherscan.io/api-reference/endpoint/addresstokenbalance"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/addresstokenbalance#apireference","headline":"Get Address ERC20 Token Holding","name":"Get Address ERC20 Token Holding","description":"Retrieves the list of ERC-20 tokens and balances held by a specified address.","url":"https://docs.etherscan.io/api-reference/endpoint/addresstokenbalance","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/addresstokenbalance#webpage"},"dateModified":"2026-08-20T09:11:04.464Z","keywords":"address token balance, erc20 holdings","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

Get Address ERC20 Token HoldingcURL

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
      "TokenAddress": "0xffffffff2ba8f66d4e51811c5190992176930278",
      "TokenName": "Furucombo",
      "TokenSymbol": "COMBO",
      "TokenQuantity": "1861606940000000000",
      "TokenDivisor": "18",
      "TokenPriceUSD": "0.000891470000000000"
    },
    {
      "TokenAddress": "0x53a1e9912323b8016424d6287286e3b6de263f76",
      "TokenName": "PUTIN Token",
      "TokenSymbol": "PTT",
      "TokenQuantity": "3500000000000000000000",
      "TokenDivisor": "18",
      "TokenPriceUSD": "0.000000000000000000"
    }
  ]
}
```

Tokens
# Get Address ERC20 Token Holding

Copy pageCopy pageRetrieves the list of ERC-20 tokens and balances held by a specified address.

Copy pageCopy pageGET/v2/apiTry itGet Address ERC20 Token HoldingcURL

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
      "TokenAddress": "0xffffffff2ba8f66d4e51811c5190992176930278",
      "TokenName": "Furucombo",
      "TokenSymbol": "COMBO",
      "TokenQuantity": "1861606940000000000",
      "TokenDivisor": "18",
      "TokenPriceUSD": "0.000891470000000000"
    },
    {
      "TokenAddress": "0x53a1e9912323b8016424d6287286e3b6de263f76",
      "TokenName": "PUTIN Token",
      "TokenSymbol": "PTT",
      "TokenQuantity": "3500000000000000000000",
      "TokenDivisor": "18",
      "TokenPriceUSD": "0.000000000000000000"
    }
  ]
}
```

This is a PRO endpoint, available to the [Standard Plan](https://docs.etherscan.io/rate-limits) and above
This endpoint is throttled to **2 calls/second** regardless of API Pro tier.
Example response
```
{
  "status": "1",
  "message": "OK",
  "result": [
    {
      "TokenAddress": "0xffffffff2ba8f66d4e51811c5190992176930278",
      "TokenName": "Furucombo",
      "TokenSymbol": "COMBO",
      "TokenQuantity": "1861606940000000000",
      "TokenDivisor": "18",
      "TokenPriceUSD": "0.000891470000000000"
    },
    {
      "TokenAddress": "0x53a1e9912323b8016424d6287286e3b6de263f76",
      "TokenName": "PUTIN Token",
      "TokenSymbol": "PTT",
      "TokenQuantity": "3500000000000000000000",
      "TokenDivisor": "18",
      "TokenPriceUSD": "0.000000000000000000"
    }
  ]
}
```

#### Authorizations

[​](#authorization-apikey)apikeystringqueryrequiredEnter your Etherscan API key, or [set one up](https://docs.etherscan.io/set-up-your-api-key) if you don't have one.

#### Query Parameters

[​](#parameter-chainid)chainidstringrequiredChain ID to query, eg 1 for Ethereum, 42161 for Arbitrum from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:accountrequiredSet to account for this endpoint.

[​](#parameter-action)actionstringdefault:addresstokenbalancerequiredSet to addresstokenbalance for this endpoint.

[​](#parameter-address)addressstringrequiredAddress to check for token holdings.

[​](#parameter-page)pageintegerPage number for pagination.

[​](#parameter-offset)offsetintegerNumber of records per page. Use the page parameter for subsequent records.

#### Response

200 - application/jsonSuccessful response

[​](#response-status)statusstring1 if the request returned data, 0 otherwise. A status of 0 can indicate an error or a valid request that returned no records.

[​](#response-message)messagestringOK on success, otherwise an error description such as NOTOK. See [common error messages](https://docs.etherscan.io/common-error-messages).

[​](#response-result)resultobject[]Show child attributes

[Get Token Info by ContractAddress](https://docs.etherscan.io/api-reference/endpoint/tokeninfo)[Get Address ERC721 Token Holding](https://docs.etherscan.io/api-reference/endpoint/addresstokennftbalance)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)