# Verify Vyper Source Code

> Source: https://docs.etherscan.io/api-reference/endpoint/verifyvyper

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/verifyvyper#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/verifyvyper","name":"Verify Vyper Source Code","description":"Submit a Vyper contract for verification.","dateModified":"2026-08-20T09:11:04.085Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/verifyvyper#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/verifyvyper#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Contract Verification","item":"https://docs.etherscan.io/api-reference/endpoint/verifysourcecode"},{"@type":"ListItem","position":3,"name":"Verify Vyper Source Code","item":"https://docs.etherscan.io/api-reference/endpoint/verifyvyper"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/verifyvyper#apireference","headline":"Verify Vyper Source Code","name":"Verify Vyper Source Code","description":"Submit a Vyper contract for verification.","url":"https://docs.etherscan.io/api-reference/endpoint/verifyvyper","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/verifyvyper#webpage"},"dateModified":"2026-08-20T09:11:04.085Z","keywords":"verify contract, vyper verification","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

Verify Vyper Source CodecURL

```
curl --request POST \
  --url 'https://api.etherscan.io/v2/api?apikey=' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data codeformat=vyper-json \
  --data 'sourceCode=<string>' \
  --data contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7 \
  --data contractname=contracts/Verified.vy:Verified \
  --data compilerversion=vyper:0.4.0 \
  --data optimizationUsed=0 \
  --data constructorArguments=00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a
```

```
import requests

url = "https://api.etherscan.io/v2/api?apikey="

payload = {
    "codeformat": "vyper-json",
    "sourceCode": "<string>",
    "contractaddress": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "contractname": "contracts/Verified.vy:Verified",
    "compilerversion": "vyper:0.4.0",
    "optimizationUsed": "0",
    "constructorArguments": "00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a"
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
    codeformat: 'vyper-json',
    sourceCode: '<string>',
    contractaddress: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    contractname: 'contracts/Verified.vy:Verified',
    compilerversion: 'vyper:0.4.0',
    optimizationUsed: '0',
    constructorArguments: '00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a'
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
  CURLOPT_POSTFIELDS => "codeformat=vyper-json&sourceCode=%3Cstring%3E&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=contracts%2FVerified.vy%3AVerified&compilerversion=vyper%3A0.4.0&optimizationUsed=0&constructorArguments=00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a",
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

	payload := strings.NewReader("codeformat=vyper-json&sourceCode=%3Cstring%3E&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=contracts%2FVerified.vy%3AVerified&compilerversion=vyper%3A0.4.0&optimizationUsed=0&constructorArguments=00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a")

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
  .body("codeformat=vyper-json&sourceCode=%3Cstring%3E&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=contracts%2FVerified.vy%3AVerified&compilerversion=vyper%3A0.4.0&optimizationUsed=0&constructorArguments=00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a")
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
request.body = "codeformat=vyper-json&sourceCode=%3Cstring%3E&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=contracts%2FVerified.vy%3AVerified&compilerversion=vyper%3A0.4.0&optimizationUsed=0&constructorArguments=00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a"

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
# Verify Vyper Source Code

Copy pageCopy pageSubmit a Vyper contract for verification.

Copy pageCopy pagePOST/v2/apiTry itVerify Vyper Source CodecURL

```
curl --request POST \
  --url 'https://api.etherscan.io/v2/api?apikey=' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data codeformat=vyper-json \
  --data 'sourceCode=<string>' \
  --data contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7 \
  --data contractname=contracts/Verified.vy:Verified \
  --data compilerversion=vyper:0.4.0 \
  --data optimizationUsed=0 \
  --data constructorArguments=00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a
```

```
import requests

url = "https://api.etherscan.io/v2/api?apikey="

payload = {
    "codeformat": "vyper-json",
    "sourceCode": "<string>",
    "contractaddress": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "contractname": "contracts/Verified.vy:Verified",
    "compilerversion": "vyper:0.4.0",
    "optimizationUsed": "0",
    "constructorArguments": "00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a"
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
    codeformat: 'vyper-json',
    sourceCode: '<string>',
    contractaddress: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    contractname: 'contracts/Verified.vy:Verified',
    compilerversion: 'vyper:0.4.0',
    optimizationUsed: '0',
    constructorArguments: '00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a'
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
  CURLOPT_POSTFIELDS => "codeformat=vyper-json&sourceCode=%3Cstring%3E&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=contracts%2FVerified.vy%3AVerified&compilerversion=vyper%3A0.4.0&optimizationUsed=0&constructorArguments=00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a",
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

	payload := strings.NewReader("codeformat=vyper-json&sourceCode=%3Cstring%3E&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=contracts%2FVerified.vy%3AVerified&compilerversion=vyper%3A0.4.0&optimizationUsed=0&constructorArguments=00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a")

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
  .body("codeformat=vyper-json&sourceCode=%3Cstring%3E&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=contracts%2FVerified.vy%3AVerified&compilerversion=vyper%3A0.4.0&optimizationUsed=0&constructorArguments=00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a")
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
request.body = "codeformat=vyper-json&sourceCode=%3Cstring%3E&contractaddress=0xdAC17F958D2ee523a2206206994597C13D831ec7&contractname=contracts%2FVerified.vy%3AVerified&compilerversion=vyper%3A0.4.0&optimizationUsed=0&constructorArguments=00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a"

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

[​](#parameter-chainid)chainidstringrequiredChain ID to query, eg 1 for Ethereum, 42161 for Arbitrum from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:contractrequiredSet to contract for this endpoint.

[​](#parameter-action)actionstringdefault:verifysourcecoderequiredSet to verifysourcecode for this endpoint.

#### Body

application/x-www-form-urlencoded[​](#body-codeformat)codeformatstringrequiredUse `vyper-json` for Vyper contracts.

Example:`"vyper-json"`

[​](#body-source-code)sourceCodestringrequiredThe Vyper source code in JSON format.

[​](#body-contractaddress)contractaddressstringrequiredThe address where the contract is deployed.

Example:`"0xdAC17F958D2ee523a2206206994597C13D831ec7"`

[​](#body-contractname)contractnamestringrequiredThe contract name, including path if applicable.

Example:`"contracts/Verified.vy:Verified"`

[​](#body-compilerversion)compilerversionstringrequiredCompiler version used for compilation. See the [supported Vyper compiler versions](https://etherscan.io/vyperversions).

Example:`"vyper:0.4.0"`

[​](#body-optimization-used)optimizationUsedstringrequiredUse `1` if compiler optimizations were enabled, otherwise `0`.

Example:`"0"`

[​](#body-constructor-arguments)constructorArgumentsstringOptional constructor arguments used in contract deployment.

Example:`"00000000000000000000000074271f2282ed7ee35c166122a60c9830354be42a"`

#### Response

200 - application/jsonSuccessful response

[​](#response-status)statusstring1 if the request returned data, 0 otherwise. A status of 0 can indicate an error or a valid request that returned no records.

[​](#response-message)messagestringOK on success, otherwise an error description such as NOTOK. See [common error messages](https://docs.etherscan.io/common-error-messages).

[​](#response-result)resultstringGUID for the verification submission. Use it with [checkverifystatus](https://docs.etherscan.io/api-reference/endpoint/checkverifystatus) to poll the result.

[Verify zkSync Source Code](https://docs.etherscan.io/api-reference/endpoint/verifyzksyncsourcecode)[Verify Stylus Source Code](https://docs.etherscan.io/api-reference/endpoint/verifystylus)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)