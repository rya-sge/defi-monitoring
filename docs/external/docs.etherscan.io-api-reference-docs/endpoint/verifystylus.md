# Verify Stylus Source Code

> Source: https://docs.etherscan.io/api-reference/endpoint/verifystylus

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/verifystylus#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/verifystylus","name":"Verify Stylus Source Code","description":"Submit Stylus source code for verification.","dateModified":"2026-08-20T09:11:04.080Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/verifystylus#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/verifystylus#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Contract Verification","item":"https://docs.etherscan.io/api-reference/endpoint/verifysourcecode"},{"@type":"ListItem","position":3,"name":"Verify Stylus Source Code","item":"https://docs.etherscan.io/api-reference/endpoint/verifystylus"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/verifystylus#apireference","headline":"Verify Stylus Source Code","name":"Verify Stylus Source Code","description":"Submit Stylus source code for verification.","url":"https://docs.etherscan.io/api-reference/endpoint/verifystylus","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/verifystylus#webpage"},"dateModified":"2026-08-20T09:11:04.080Z","keywords":"verify contract, stylus verification","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

Verify Stylus Source CodecURL

```
curl --request POST \
  --url 'https://api.etherscan.io/v2/api?apikey=' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data codeformat=stylus \
  --data sourceCode=https://github.com/OffchainLabs/stylus-hello-world \
  --data contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7 \
  --data contractname=stylus_hello_world \
  --data compilerversion=stylus:0.5.3 \
  --data licenseType=3
```

```
import requests

url = "https://api.etherscan.io/v2/api?apikey="

payload = {
    "codeformat": "stylus",
    "sourceCode": "https://github.com/OffchainLabs/stylus-hello-world",
    "contractaddress": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "contractname": "stylus_hello_world",
    "compilerversion": "stylus:0.5.3",
    "licenseType": "3"
}
headers = {"Content-Type": "application/x-www-form-urlencoded"}

response = requests.post(url, data=payload, headers=headers)

print(response.text)
```

```
const options = {
  method: 'POST',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
  body: new URLSearchParams({
    codeformat: 'stylus',
    sourceCode: 'https://github.com/OffchainLabs/stylus-hello-world',
    contractaddress: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    contractname: 'stylus_hello_world',
    compilerversion: 'stylus:0.5.3',
    licenseType: '3'
  })
};

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
  CURLOPT_CUSTOMREQUEST => "POST",
  CURLOPT_POSTFIELDS => "codeformat=stylus&sourceCode=https%3A%2F%2Fgithub.com%2FOffchainLabs%2Fstylus-hello-world&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=stylus_hello_world&compilerversion=stylus%3A0.5.3&licenseType=3",
  CURLOPT_HTTPHEADER => [
    "Content-Type: application/x-www-form-urlencoded"
  ],
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
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.etherscan.io/v2/api?apikey="

	payload := strings.NewReader("codeformat=stylus&sourceCode=https%3A%2F%2Fgithub.com%2FOffchainLabs%2Fstylus-hello-world&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=stylus_hello_world&compilerversion=stylus%3A0.5.3&licenseType=3")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(string(body))

}
```

```
HttpResponse<String> response = Unirest.post("https://api.etherscan.io/v2/api?apikey=")
  .header("Content-Type", "application/x-www-form-urlencoded")
  .body("codeformat=stylus&sourceCode=https%3A%2F%2Fgithub.com%2FOffchainLabs%2Fstylus-hello-world&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=stylus_hello_world&compilerversion=stylus%3A0.5.3&licenseType=3")
  .asString();
```

```
require 'uri'
require 'net/http'

url = URI("https://api.etherscan.io/v2/api?apikey=")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/x-www-form-urlencoded'
request.body = "codeformat=stylus&sourceCode=https%3A%2F%2Fgithub.com%2FOffchainLabs%2Fstylus-hello-world&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=stylus_hello_world&compilerversion=stylus%3A0.5.3&licenseType=3"

response = http.request(request)
puts response.read_body
```

Example response
```
{
    "status": "1",
    "message": "OK",
    "result": "a7lpxkm9kpcpicx7daftmjifrfhiuhf5vqqnawhkfhzfrcpnxj"
}
```

Contract Verification
# Verify Stylus Source Code

Copy pageCopy pageSubmit Stylus source code for verification.

Copy pageCopy pagePOST/v2/apiTry itVerify Stylus Source CodecURL

```
curl --request POST \
  --url 'https://api.etherscan.io/v2/api?apikey=' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data codeformat=stylus \
  --data sourceCode=https://github.com/OffchainLabs/stylus-hello-world \
  --data contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7 \
  --data contractname=stylus_hello_world \
  --data compilerversion=stylus:0.5.3 \
  --data licenseType=3
```

```
import requests

url = "https://api.etherscan.io/v2/api?apikey="

payload = {
    "codeformat": "stylus",
    "sourceCode": "https://github.com/OffchainLabs/stylus-hello-world",
    "contractaddress": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "contractname": "stylus_hello_world",
    "compilerversion": "stylus:0.5.3",
    "licenseType": "3"
}
headers = {"Content-Type": "application/x-www-form-urlencoded"}

response = requests.post(url, data=payload, headers=headers)

print(response.text)
```

```
const options = {
  method: 'POST',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
  body: new URLSearchParams({
    codeformat: 'stylus',
    sourceCode: 'https://github.com/OffchainLabs/stylus-hello-world',
    contractaddress: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    contractname: 'stylus_hello_world',
    compilerversion: 'stylus:0.5.3',
    licenseType: '3'
  })
};

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
  CURLOPT_CUSTOMREQUEST => "POST",
  CURLOPT_POSTFIELDS => "codeformat=stylus&sourceCode=https%3A%2F%2Fgithub.com%2FOffchainLabs%2Fstylus-hello-world&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=stylus_hello_world&compilerversion=stylus%3A0.5.3&licenseType=3",
  CURLOPT_HTTPHEADER => [
    "Content-Type: application/x-www-form-urlencoded"
  ],
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
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.etherscan.io/v2/api?apikey="

	payload := strings.NewReader("codeformat=stylus&sourceCode=https%3A%2F%2Fgithub.com%2FOffchainLabs%2Fstylus-hello-world&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=stylus_hello_world&compilerversion=stylus%3A0.5.3&licenseType=3")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(string(body))

}
```

```
HttpResponse<String> response = Unirest.post("https://api.etherscan.io/v2/api?apikey=")
  .header("Content-Type", "application/x-www-form-urlencoded")
  .body("codeformat=stylus&sourceCode=https%3A%2F%2Fgithub.com%2FOffchainLabs%2Fstylus-hello-world&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=stylus_hello_world&compilerversion=stylus%3A0.5.3&licenseType=3")
  .asString();
```

```
require 'uri'
require 'net/http'

url = URI("https://api.etherscan.io/v2/api?apikey=")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Content-Type"] = 'application/x-www-form-urlencoded'
request.body = "codeformat=stylus&sourceCode=https%3A%2F%2Fgithub.com%2FOffchainLabs%2Fstylus-hello-world&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=stylus_hello_world&compilerversion=stylus%3A0.5.3&licenseType=3"

response = http.request(request)
puts response.read_body
```

Example response
```
{
    "status": "1",
    "message": "OK",
    "result": "a7lpxkm9kpcpicx7daftmjifrfhiuhf5vqqnawhkfhzfrcpnxj"
}
```

Arbitrum One Mainnet
Arbitrum Sepolia Testnet
Example response
```
{
    "status": "1",
    "message": "OK",
    "result": "a7lpxkm9kpcpicx7daftmjifrfhiuhf5vqqnawhkfhzfrcpnxj"
}
```

#### Authorizations

[​](#authorization-apikey)apikeystringqueryrequiredEnter your Etherscan API key, or [set one up](https://docs.etherscan.io/set-up-your-api-key) if you don't have one.

#### Query Parameters

[​](#parameter-chainid)chainidstringrequiredChain ID to query, eg 42161 for Arbitrum One from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:contractrequiredSet to contract for this endpoint.

[​](#parameter-action)actionstringdefault:verifysourcecoderequiredSet to verifysourcecode for this endpoint.

#### Body

application/x-www-form-urlencoded[​](#body-codeformat)codeformatstringrequiredUse `stylus` for Stylus projects.

Example:`"stylus"`

[​](#body-source-code)sourceCodestringrequiredPublic Git repository that hosts the Stylus source code.

Example:`"https://github.com/OffchainLabs/stylus-hello-world"`

[​](#body-contractaddress)contractaddressstringrequiredThe address where the contract is deployed.

Example:`"0xdAC17F958D2ee523a2206206994597C13D831ec7"`

[​](#body-contractname)contractnamestringrequiredThe contract name that matches your Stylus deployment.

Example:`"stylus_hello_world"`

[​](#body-compilerversion)compilerversionstringrequiredStylus compiler version used for compilation.

Example:`"stylus:0.5.3"`

[​](#body-license-type)licenseTypeintegerLicense identifier from the [open source license options](https://arbiscan.io/contract-license-types).

Example:`3`

#### Response

200 - application/jsonSuccessful response

[​](#response-status)statusstring1 if the request returned data, 0 otherwise. A status of 0 can indicate an error or a valid request that returned no records.

[​](#response-message)messagestringOK on success, otherwise an error description such as NOTOK. See [common error messages](https://docs.etherscan.io/common-error-messages).

[​](#response-result)resultstringGUID for the verification submission. Use it with [checkverifystatus](https://docs.etherscan.io/api-reference/endpoint/checkverifystatus) to poll the result.

[Verify Vyper Source Code](https://docs.etherscan.io/api-reference/endpoint/verifyvyper)[Verify Proxy Contract](https://docs.etherscan.io/api-reference/endpoint/verifyproxycontract)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)