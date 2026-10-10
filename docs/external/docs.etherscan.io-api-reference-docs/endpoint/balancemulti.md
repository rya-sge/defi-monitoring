# Get Native Balance for Multiple Addresses

> Source: https://docs.etherscan.io/api-reference/endpoint/balancemulti

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/balancemulti#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/balancemulti","name":"Get Native Balance for Multiple Addresses","description":"Retrieves the native token balance held by multiple addresses in a single call.","dateModified":"2026-08-20T09:11:04.425Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/balancemulti#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/balancemulti#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Account","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":3,"name":"Get Native Balance for Multiple Addresses","item":"https://docs.etherscan.io/api-reference/endpoint/balancemulti"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/balancemulti#apireference","headline":"Get Native Balance for Multiple Addresses","name":"Get Native Balance for Multiple Addresses","description":"Retrieves the native token balance held by multiple addresses in a single call.","url":"https://docs.etherscan.io/api-reference/endpoint/balancemulti","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/balancemulti#webpage"},"dateModified":"2026-08-20T09:11:04.425Z","keywords":"Ether balance multi, Etherscan balancemulti, balance multiple addresses","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

.mint-mt-4 {
    margin-top: 1rem
}
.mint-text-base {
    font-size: 1rem;
    line-height: 1.5rem
}
.mint-font-medium {
    font-weight: 500
}
.mint-font-semibold {
    font-weight: 600
}
.mint-text-zinc-900 {
    --tw-text-opacity: 1;
    color: rgb(24 24 27 / var(--tw-text-opacity, 1))
}
.hover\:mint-underline:hover {
    text-decoration-line: underline
}
.dark\:mint-text-zinc-100:is(.dark *) {
    --tw-text-opacity: 1;
    color: rgb(244 244 245 / var(--tw-text-opacity, 1))
}Get Native Balance for Multiple AddressescURL

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
   "status":"1",
   "message":"OK",
   "result":[
      {
         "account":"0xddbd2b932c763ba5b1b7ae3b362eac3e8d40121a",
         "balance":"40891631566070000000000"
      },
      {
         "account":"0x63a9975ba31b0b9626b34300f7f627147df1f526",
         "balance":"332567136222827062478"
      },
      {
         "account":"0x198ef1ec325a96cc354c7266a038be8b5c558f67",
         "balance":"12005264493462223951724"
      }
   ]
}
```

Account
# Get Native Balance for Multiple Addresses

Copy pageCopy pageRetrieves the native token balance held by multiple addresses in a single call.

Copy pageCopy pageGET/v2/apiTry itGet Native Balance for Multiple AddressescURL

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
   "status":"1",
   "message":"OK",
   "result":[
      {
         "account":"0xddbd2b932c763ba5b1b7ae3b362eac3e8d40121a",
         "balance":"40891631566070000000000"
      },
      {
         "account":"0x63a9975ba31b0b9626b34300f7f627147df1f526",
         "balance":"332567136222827062478"
      },
      {
         "account":"0x198ef1ec325a96cc354c7266a038be8b5c558f67",
         "balance":"12005264493462223951724"
      }
   ]
}
```

Example response
```
{
   "status":"1",
   "message":"OK",
   "result":[
      {
         "account":"0xddbd2b932c763ba5b1b7ae3b362eac3e8d40121a",
         "balance":"40891631566070000000000"
      },
      {
         "account":"0x63a9975ba31b0b9626b34300f7f627147df1f526",
         "balance":"332567136222827062478"
      },
      {
         "account":"0x198ef1ec325a96cc354c7266a038be8b5c558f67",
         "balance":"12005264493462223951724"
      }
   ]
}
```

#### Authorizations

[​](#authorization-apikey)apikeystringqueryrequiredEnter your Etherscan API key, or [set one up](https://docs.etherscan.io/set-up-your-api-key) if you don't have one.

#### Query Parameters

[​](#parameter-chainid)chainidstringrequiredChain ID to query, eg 1 for Ethereum, 42161 for Arbitrum from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:accountrequiredSet to account for this endpoint.

[​](#parameter-action)actionstringdefault:balancemultirequiredSet to balancemulti for this endpoint.

[​](#parameter-address)addressstringrequiredComma-separated list of addresses to query, up to a maximum of 20 addresses per call.

[​](#parameter-tag)tagstringUse latest for the last block number of the chain. Also accepts a specific block number in hex format, like 0x10d4f up to the last 128 blocks.

#### Response

200 - application/jsonSuccessful response

[​](#response-status)statusstring1 if the request returned data, 0 otherwise. A status of 0 can indicate an error or a valid request that returned no records.

[​](#response-message)messagestringOK on success, otherwise an error description such as NOTOK. See [common error messages](https://docs.etherscan.io/common-error-messages).

[​](#response-result)resultobject[]Show child attributes

[Get Native Balance for an Address](https://docs.etherscan.io/api-reference/endpoint/balance)[Get Historical Native Balance for an Address](https://docs.etherscan.io/api-reference/endpoint/balancehistory)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)