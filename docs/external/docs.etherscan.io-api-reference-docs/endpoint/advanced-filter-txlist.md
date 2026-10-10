# Normal Transactions Advanced Filter

> Source: https://docs.etherscan.io/api-reference/endpoint/advanced-filter-txlist

---

{"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://docs.etherscan.io/#organization","name":"Etherscan","url":"https://docs.etherscan.io","logo":{"@type":"ImageObject","url":"https://mintcdn.com/etherscan/O446YQrF1qMjlNwS/logo/etherscan-logo-dark.svg?fit=max&auto=format&n=O446YQrF1qMjlNwS&q=85&s=4e966e2dc30e631ecd17c82d5445201f"}},{"@type":"WebSite","@id":"https://docs.etherscan.io#website","name":"Etherscan","url":"https://docs.etherscan.io","publisher":{"@id":"https://docs.etherscan.io/#organization"}},{"@type":"WebPage","@id":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-txlist#webpage","url":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-txlist","name":"Normal Transactions Advanced Filter","description":"Retrieves Normal Transactions with advanced from and to address filtering.","dateModified":"2026-08-20T09:11:04.446Z","isPartOf":{"@id":"https://docs.etherscan.io#website"},"breadcrumb":{"@id":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-txlist#breadcrumb"}},{"@type":"BreadcrumbList","@id":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-txlist#breadcrumb","itemListElement":[{"@type":"ListItem","position":1,"name":"API Endpoints","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":2,"name":"Account","item":"https://docs.etherscan.io/api-reference/endpoint/balance"},{"@type":"ListItem","position":3,"name":"Normal Transactions Advanced Filter","item":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-txlist"}]},{"@type":["TechArticle","APIReference"],"@id":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-txlist#apireference","headline":"Normal Transactions Advanced Filter","name":"Normal Transactions Advanced Filter","description":"Retrieves Normal Transactions with advanced from and to address filtering.","url":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-txlist","mainEntityOfPage":{"@id":"https://docs.etherscan.io/api-reference/endpoint/advanced-filter-txlist#webpage"},"dateModified":"2026-08-20T09:11:04.446Z","keywords":"advanced filter, txlist, from, to, fromto_opr","publisher":{"@id":"https://docs.etherscan.io/#organization"},"isPartOf":{"@id":"https://docs.etherscan.io#website"}}]}document.documentElement.setAttribute('data-page-mode', "none");:root{
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

Normal Transactions Advanced FiltercURL

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
         "blockNumber":"25115190",
         "blockHash":"0x761e4c9928f804d020809bb21404787595bd1062f1ad975f4ee667514b9dfd31",
         "timeStamp":"1779024299",
         "hash":"0xf292888b132e986f79d95f5788fc21ca08e2096a7fa48ec1c5f265692f01e572",
         "nonce":"756",
         "transactionIndex":"180",
         "from":"0x9480fc2a527bb0f0e5e6a3cf2922bcd123b71302",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"1000000000000000",
         "gas":"21000",
         "gasPrice":"707543925",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"23218602",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"144453",
         "isError":"0"
      },
      {
         "blockNumber":"25110948",
         "blockHash":"0x787fcf3940a9c4903759c8db8f1e8ce7220dbe8a33b51cc274a1ab0f81dcb8fa",
         "timeStamp":"1778973191",
         "hash":"0x0978044c1bcefb3875e60e32ad17ac0ee5790ff288c7bf962b7c2da011a3e2da",
         "nonce":"2356321",
         "transactionIndex":"165",
         "from":"0xcfc0f98f30742b6d880f90155d4ebb885e55ab33",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"2280025690430300",
         "gas":"21000",
         "gasPrice":"99688389",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"20407487",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"148695",
         "isError":"0"
      },
      {
         "blockNumber":"25100650",
         "blockHash":"0x73d81243ce7d02253897285f13f0d902e809f4e81afe8d3279c3009e84493003",
         "timeStamp":"1778849339",
         "hash":"0xf4322f6349742333252e8b3a343ffea99956128b592671f0584369991cff1382",
         "nonce":"1",
         "transactionIndex":"110",
         "from":"0xb0c8bf8d41df1051d6e43a92df1ce00be18319d4",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"25184345489993000",
         "gas":"21000",
         "gasPrice":"614976667",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"14457597",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"158993",
         "isError":"0"
      },
      {
         "blockNumber":"25098446",
         "blockHash":"0xc6bc028585270139d04ef58831142a615e1f29fb1c19b6857bd186d714109d73",
         "timeStamp":"1778822831",
         "hash":"0x6fa98ca16eb30b2cfda0bf960d2d8451b16bf4fb2785add8ad842c79c0be3c2f",
         "nonce":"6",
         "transactionIndex":"72",
         "from":"0xe58bfe009d7252d4bfc3c319e3a0cdf8056877a9",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"86405841050975",
         "gas":"23100",
         "gasPrice":"187248990",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"11640736",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"161197",
         "isError":"0"
      },
      {
         "blockNumber":"25094060",
         "blockHash":"0x3d669f6f6eb063aef8e3b9ce01922b3b627a71cfb4ff8bc68026f89b163548ca",
         "timeStamp":"1778769947",
         "hash":"0x6d3758dde23f8e620d4a305a423578692f0cc8aa3dd2e125139b2ee692e5ae17",
         "nonce":"5398496",
         "transactionIndex":"208",
         "from":"0x264bd8291fae1d75db2c5f573b07faa6715997b5",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"26574330000000000",
         "gas":"500000",
         "gasPrice":"1395684614",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"19852043",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"165583",
         "isError":"0"
      },
      {
         "blockNumber":"25085369",
         "blockHash":"0xdbd0753accd55baa9f6c094dd3a01fb62bc455660d78d8beae4135828cc1921e",
         "timeStamp":"1778665091",
         "hash":"0xd4c1ee9f43b1e729edcb0ceb3cd3506e8a68fd88863af7e6d69a0f023b381622",
         "nonce":"18",
         "transactionIndex":"166",
         "from":"0x58db80d3949398cd0425397039c46241e13a8f33",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"7770000000000000",
         "gas":"31500",
         "gasPrice":"2125485961",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"19841086",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"174274",
         "isError":"0"
      },
      {
         "blockNumber":"25063398",
         "blockHash":"0x1051916494c8aebcdb5b6ee117b5abed2da13c8bb68fddec2e3aaf93400aaff3",
         "timeStamp":"1778400479",
         "hash":"0x55718bcae56111fdabb477a90db212d141d0192f46dd03d82c10328dea1694aa",
         "nonce":"0",
         "transactionIndex":"233",
         "from":"0x71c7662162200fe5698f60651c4f8c09c448976f",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"9149354516798",
         "gas":"21000",
         "gasPrice":"189722547",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"21912088",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"196245",
         "isError":"0"
      },
      {
         "blockNumber":"25019896",
         "blockHash":"0x1a22015e8121cb57244fe466565dd28853d04fa42718d1f1cf6a6f2493b3354f",
         "timeStamp":"1777876739",
         "hash":"0xd12412d17862dbea174cd2204aa5a9f9dabab06d7113c00e8a9e32eaf7000e02",
         "nonce":"10",
         "transactionIndex":"84",
         "from":"0x10dfb4f4640fdb8e4dd5da3b6a95f5b1ece453b2",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"67272908681009",
         "gas":"21000",
         "gasPrice":"1216643736",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"10068159",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"239747",
         "isError":"0"
      },
      {
         "blockNumber":"25002175",
         "blockHash":"0xa65b4d7ad52e2120791e4b85b43eec6579cbf331dd6614916077de1ced83fc46",
         "timeStamp":"1777663523",
         "hash":"0x01a53b23ffd82a81ec494605adb975a4322731d6d5346163429465a3b9eeafc6",
         "nonce":"0",
         "transactionIndex":"163",
         "from":"0x45d665904331f915b88d340f6424526205980088",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"0",
         "gas":"30000",
         "gasPrice":"296172198",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"12399193",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"257468",
         "isError":"0"
      },
      {
         "blockNumber":"24981765",
         "blockHash":"0x888a4dcbebde46b30e44eafe3ec7c2287612c4db022aecf6b4506b017a2ea36f",
         "timeStamp":"1777417847",
         "hash":"0x7ecb5b61fa626a93a9259691c6439d14e3f7288f200eb01c08388b37f0ebcae2",
         "nonce":"10",
         "transactionIndex":"364",
         "from":"0xb873178dc3cc31a16c9bae6894636fce17fbb12b",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"8021004715484893",
         "gas":"21000",
         "gasPrice":"1377717191",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"22455577",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"277878",
         "isError":"0"
      }
   ]
}
```

Account
# Normal Transactions Advanced Filter

Copy pageCopy pageRetrieves Normal Transactions with advanced from and to address filtering.

Copy pageCopy pageGET/v2/apiTry itNormal Transactions Advanced FiltercURL

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
         "blockNumber":"25115190",
         "blockHash":"0x761e4c9928f804d020809bb21404787595bd1062f1ad975f4ee667514b9dfd31",
         "timeStamp":"1779024299",
         "hash":"0xf292888b132e986f79d95f5788fc21ca08e2096a7fa48ec1c5f265692f01e572",
         "nonce":"756",
         "transactionIndex":"180",
         "from":"0x9480fc2a527bb0f0e5e6a3cf2922bcd123b71302",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"1000000000000000",
         "gas":"21000",
         "gasPrice":"707543925",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"23218602",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"144453",
         "isError":"0"
      },
      {
         "blockNumber":"25110948",
         "blockHash":"0x787fcf3940a9c4903759c8db8f1e8ce7220dbe8a33b51cc274a1ab0f81dcb8fa",
         "timeStamp":"1778973191",
         "hash":"0x0978044c1bcefb3875e60e32ad17ac0ee5790ff288c7bf962b7c2da011a3e2da",
         "nonce":"2356321",
         "transactionIndex":"165",
         "from":"0xcfc0f98f30742b6d880f90155d4ebb885e55ab33",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"2280025690430300",
         "gas":"21000",
         "gasPrice":"99688389",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"20407487",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"148695",
         "isError":"0"
      },
      {
         "blockNumber":"25100650",
         "blockHash":"0x73d81243ce7d02253897285f13f0d902e809f4e81afe8d3279c3009e84493003",
         "timeStamp":"1778849339",
         "hash":"0xf4322f6349742333252e8b3a343ffea99956128b592671f0584369991cff1382",
         "nonce":"1",
         "transactionIndex":"110",
         "from":"0xb0c8bf8d41df1051d6e43a92df1ce00be18319d4",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"25184345489993000",
         "gas":"21000",
         "gasPrice":"614976667",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"14457597",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"158993",
         "isError":"0"
      },
      {
         "blockNumber":"25098446",
         "blockHash":"0xc6bc028585270139d04ef58831142a615e1f29fb1c19b6857bd186d714109d73",
         "timeStamp":"1778822831",
         "hash":"0x6fa98ca16eb30b2cfda0bf960d2d8451b16bf4fb2785add8ad842c79c0be3c2f",
         "nonce":"6",
         "transactionIndex":"72",
         "from":"0xe58bfe009d7252d4bfc3c319e3a0cdf8056877a9",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"86405841050975",
         "gas":"23100",
         "gasPrice":"187248990",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"11640736",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"161197",
         "isError":"0"
      },
      {
         "blockNumber":"25094060",
         "blockHash":"0x3d669f6f6eb063aef8e3b9ce01922b3b627a71cfb4ff8bc68026f89b163548ca",
         "timeStamp":"1778769947",
         "hash":"0x6d3758dde23f8e620d4a305a423578692f0cc8aa3dd2e125139b2ee692e5ae17",
         "nonce":"5398496",
         "transactionIndex":"208",
         "from":"0x264bd8291fae1d75db2c5f573b07faa6715997b5",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"26574330000000000",
         "gas":"500000",
         "gasPrice":"1395684614",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"19852043",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"165583",
         "isError":"0"
      },
      {
         "blockNumber":"25085369",
         "blockHash":"0xdbd0753accd55baa9f6c094dd3a01fb62bc455660d78d8beae4135828cc1921e",
         "timeStamp":"1778665091",
         "hash":"0xd4c1ee9f43b1e729edcb0ceb3cd3506e8a68fd88863af7e6d69a0f023b381622",
         "nonce":"18",
         "transactionIndex":"166",
         "from":"0x58db80d3949398cd0425397039c46241e13a8f33",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"7770000000000000",
         "gas":"31500",
         "gasPrice":"2125485961",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"19841086",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"174274",
         "isError":"0"
      },
      {
         "blockNumber":"25063398",
         "blockHash":"0x1051916494c8aebcdb5b6ee117b5abed2da13c8bb68fddec2e3aaf93400aaff3",
         "timeStamp":"1778400479",
         "hash":"0x55718bcae56111fdabb477a90db212d141d0192f46dd03d82c10328dea1694aa",
         "nonce":"0",
         "transactionIndex":"233",
         "from":"0x71c7662162200fe5698f60651c4f8c09c448976f",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"9149354516798",
         "gas":"21000",
         "gasPrice":"189722547",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"21912088",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"196245",
         "isError":"0"
      },
      {
         "blockNumber":"25019896",
         "blockHash":"0x1a22015e8121cb57244fe466565dd28853d04fa42718d1f1cf6a6f2493b3354f",
         "timeStamp":"1777876739",
         "hash":"0xd12412d17862dbea174cd2204aa5a9f9dabab06d7113c00e8a9e32eaf7000e02",
         "nonce":"10",
         "transactionIndex":"84",
         "from":"0x10dfb4f4640fdb8e4dd5da3b6a95f5b1ece453b2",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"67272908681009",
         "gas":"21000",
         "gasPrice":"1216643736",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"10068159",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"239747",
         "isError":"0"
      },
      {
         "blockNumber":"25002175",
         "blockHash":"0xa65b4d7ad52e2120791e4b85b43eec6579cbf331dd6614916077de1ced83fc46",
         "timeStamp":"1777663523",
         "hash":"0x01a53b23ffd82a81ec494605adb975a4322731d6d5346163429465a3b9eeafc6",
         "nonce":"0",
         "transactionIndex":"163",
         "from":"0x45d665904331f915b88d340f6424526205980088",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"0",
         "gas":"30000",
         "gasPrice":"296172198",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"12399193",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"257468",
         "isError":"0"
      },
      {
         "blockNumber":"24981765",
         "blockHash":"0x888a4dcbebde46b30e44eafe3ec7c2287612c4db022aecf6b4506b017a2ea36f",
         "timeStamp":"1777417847",
         "hash":"0x7ecb5b61fa626a93a9259691c6439d14e3f7288f200eb01c08388b37f0ebcae2",
         "nonce":"10",
         "transactionIndex":"364",
         "from":"0xb873178dc3cc31a16c9bae6894636fce17fbb12b",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"8021004715484893",
         "gas":"21000",
         "gasPrice":"1377717191",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"22455577",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"277878",
         "isError":"0"
      }
   ]
}
```

Beta
Explore and preview data from our [Advanced Filter](https://etherscan.io/advanced-filter) page.
Example response
```
{
   "status":"1",
   "message":"OK",
   "result":[
      {
         "blockNumber":"25115190",
         "blockHash":"0x761e4c9928f804d020809bb21404787595bd1062f1ad975f4ee667514b9dfd31",
         "timeStamp":"1779024299",
         "hash":"0xf292888b132e986f79d95f5788fc21ca08e2096a7fa48ec1c5f265692f01e572",
         "nonce":"756",
         "transactionIndex":"180",
         "from":"0x9480fc2a527bb0f0e5e6a3cf2922bcd123b71302",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"1000000000000000",
         "gas":"21000",
         "gasPrice":"707543925",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"23218602",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"144453",
         "isError":"0"
      },
      {
         "blockNumber":"25110948",
         "blockHash":"0x787fcf3940a9c4903759c8db8f1e8ce7220dbe8a33b51cc274a1ab0f81dcb8fa",
         "timeStamp":"1778973191",
         "hash":"0x0978044c1bcefb3875e60e32ad17ac0ee5790ff288c7bf962b7c2da011a3e2da",
         "nonce":"2356321",
         "transactionIndex":"165",
         "from":"0xcfc0f98f30742b6d880f90155d4ebb885e55ab33",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"2280025690430300",
         "gas":"21000",
         "gasPrice":"99688389",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"20407487",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"148695",
         "isError":"0"
      },
      {
         "blockNumber":"25100650",
         "blockHash":"0x73d81243ce7d02253897285f13f0d902e809f4e81afe8d3279c3009e84493003",
         "timeStamp":"1778849339",
         "hash":"0xf4322f6349742333252e8b3a343ffea99956128b592671f0584369991cff1382",
         "nonce":"1",
         "transactionIndex":"110",
         "from":"0xb0c8bf8d41df1051d6e43a92df1ce00be18319d4",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"25184345489993000",
         "gas":"21000",
         "gasPrice":"614976667",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"14457597",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"158993",
         "isError":"0"
      },
      {
         "blockNumber":"25098446",
         "blockHash":"0xc6bc028585270139d04ef58831142a615e1f29fb1c19b6857bd186d714109d73",
         "timeStamp":"1778822831",
         "hash":"0x6fa98ca16eb30b2cfda0bf960d2d8451b16bf4fb2785add8ad842c79c0be3c2f",
         "nonce":"6",
         "transactionIndex":"72",
         "from":"0xe58bfe009d7252d4bfc3c319e3a0cdf8056877a9",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"86405841050975",
         "gas":"23100",
         "gasPrice":"187248990",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"11640736",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"161197",
         "isError":"0"
      },
      {
         "blockNumber":"25094060",
         "blockHash":"0x3d669f6f6eb063aef8e3b9ce01922b3b627a71cfb4ff8bc68026f89b163548ca",
         "timeStamp":"1778769947",
         "hash":"0x6d3758dde23f8e620d4a305a423578692f0cc8aa3dd2e125139b2ee692e5ae17",
         "nonce":"5398496",
         "transactionIndex":"208",
         "from":"0x264bd8291fae1d75db2c5f573b07faa6715997b5",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"26574330000000000",
         "gas":"500000",
         "gasPrice":"1395684614",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"19852043",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"165583",
         "isError":"0"
      },
      {
         "blockNumber":"25085369",
         "blockHash":"0xdbd0753accd55baa9f6c094dd3a01fb62bc455660d78d8beae4135828cc1921e",
         "timeStamp":"1778665091",
         "hash":"0xd4c1ee9f43b1e729edcb0ceb3cd3506e8a68fd88863af7e6d69a0f023b381622",
         "nonce":"18",
         "transactionIndex":"166",
         "from":"0x58db80d3949398cd0425397039c46241e13a8f33",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"7770000000000000",
         "gas":"31500",
         "gasPrice":"2125485961",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"19841086",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"174274",
         "isError":"0"
      },
      {
         "blockNumber":"25063398",
         "blockHash":"0x1051916494c8aebcdb5b6ee117b5abed2da13c8bb68fddec2e3aaf93400aaff3",
         "timeStamp":"1778400479",
         "hash":"0x55718bcae56111fdabb477a90db212d141d0192f46dd03d82c10328dea1694aa",
         "nonce":"0",
         "transactionIndex":"233",
         "from":"0x71c7662162200fe5698f60651c4f8c09c448976f",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"9149354516798",
         "gas":"21000",
         "gasPrice":"189722547",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"21912088",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"196245",
         "isError":"0"
      },
      {
         "blockNumber":"25019896",
         "blockHash":"0x1a22015e8121cb57244fe466565dd28853d04fa42718d1f1cf6a6f2493b3354f",
         "timeStamp":"1777876739",
         "hash":"0xd12412d17862dbea174cd2204aa5a9f9dabab06d7113c00e8a9e32eaf7000e02",
         "nonce":"10",
         "transactionIndex":"84",
         "from":"0x10dfb4f4640fdb8e4dd5da3b6a95f5b1ece453b2",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"67272908681009",
         "gas":"21000",
         "gasPrice":"1216643736",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"10068159",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"239747",
         "isError":"0"
      },
      {
         "blockNumber":"25002175",
         "blockHash":"0xa65b4d7ad52e2120791e4b85b43eec6579cbf331dd6614916077de1ced83fc46",
         "timeStamp":"1777663523",
         "hash":"0x01a53b23ffd82a81ec494605adb975a4322731d6d5346163429465a3b9eeafc6",
         "nonce":"0",
         "transactionIndex":"163",
         "from":"0x45d665904331f915b88d340f6424526205980088",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"0",
         "gas":"30000",
         "gasPrice":"296172198",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"12399193",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"257468",
         "isError":"0"
      },
      {
         "blockNumber":"24981765",
         "blockHash":"0x888a4dcbebde46b30e44eafe3ec7c2287612c4db022aecf6b4506b017a2ea36f",
         "timeStamp":"1777417847",
         "hash":"0x7ecb5b61fa626a93a9259691c6439d14e3f7288f200eb01c08388b37f0ebcae2",
         "nonce":"10",
         "transactionIndex":"364",
         "from":"0xb873178dc3cc31a16c9bae6894636fce17fbb12b",
         "to":"0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
         "value":"8021004715484893",
         "gas":"21000",
         "gasPrice":"1377717191",
         "input":"0x",
         "methodId":"0x",
         "functionName":"",
         "contractAddress":"",
         "cumulativeGasUsed":"22455577",
         "txreceipt_status":"1",
         "gasUsed":"21000",
         "confirmations":"277878",
         "isError":"0"
      }
   ]
}
```

#### Authorizations

[​](#authorization-apikey)apikeystringqueryrequiredEnter your Etherscan API key, or [set one up](https://docs.etherscan.io/set-up-your-api-key) if you don't have one.

#### Query Parameters

[​](#parameter-chainid)chainidstringrequiredChain ID to query, such as 1 for Ethereum or 42161 for Arbitrum from our [supported chains](https://docs.etherscan.io/supported-chains).

[​](#parameter-module)modulestringdefault:accountrequiredSet to account for this endpoint.

[​](#parameter-action)actionstringdefault:txlistrequiredSet to txlist for this endpoint.

[​](#parameter-from)fromstringThe sender address to filter transactions by. Provide from or to.

[​](#parameter-to)tostringThe recipient address to filter transactions by. Provide to or from.

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

[Get Normal Transactions By Address](https://docs.etherscan.io/api-reference/endpoint/txlist)[Get ERC20 Token Transfers by Address](https://docs.etherscan.io/api-reference/endpoint/tokentx)[x](https://x.com/etherscan)[website](https://etherscan.io)[Powered byThis documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=etherscan)