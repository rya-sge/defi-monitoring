"""Keyless data sources behind one cached fetcher.

Every request is keyed by a hash of (method, url, body) and stored under
fixtures/snapshot/, so a live run doubles as the offline demo snapshot.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import warnings
from pathlib import Path
from urllib.parse import urlsplit

from . import clock

warnings.filterwarnings("ignore", message=".*doesn't match a supported version.*")
import requests  # noqa: E402

SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "snapshot"

PENDLE = "https://api-v2.pendle.finance/core"
MORPHO = "https://blue-api.morpho.org/graphql"
LLAMA = "https://api.llama.fi"
LLAMA_COINS = "https://coins.llama.fi"
LLAMA_YIELDS = "https://yields.llama.fi"
RPC = "https://ethereum-rpc.publicnode.com"
ETHERSCAN = "https://api.etherscan.io/v2/api"  # needs a key: keys.ini [etherscan] api_key

KEYS_FILE = Path(__file__).resolve().parent.parent / "keys.ini"  # git-ignored; keys.example.ini is the template
THROTTLE_RETRIES = 6  # HTTP 429 resent after Retry-After, else 2, 4 … 32, 60 s: ~2 min of waiting before it fails
# A host that refuses for rate gets a gap between requests: PACE_MIN at the first refusal, doubled at each one after (up
# to PACE_MAX), narrowed by 5 % at each answer and dropped once under PACE_MIN. A burst slows itself down instead of
# spending its retries against the limit, and a host that never refuses (a paid RPC) is never slowed.
PACE_MIN, PACE_MAX = 0.05, 2.0
_hosts: dict[str, list[float]] = {}  # host -> [gap, monotonic time the next request may leave]

# Where a request is sent can differ from the URL it is cached under: RISKDEP_RPC_URL sends the main RPC's requests
# to another endpoint (a local node or proxy, a paid endpoint with its key) while cache keys, snapshots and replays
# keep the public URL, so the offline fixtures stay valid and a key never reaches a committed file.
ROUTES: dict[str, str] = {RPC: os.environ["RISKDEP_RPC_URL"]} if os.environ.get("RISKDEP_RPC_URL") else {}
# RISKDEP_FORK=1: the main RPC is a local mainnet fork (anvil, scripts/fork/). Its blocks after the fork point exist
# nowhere else and the Morpho API still describes mainnet, so the cross-checks against them are skipped (plan
# 2026-10-11-fork-demo, D1); every on-chain read is unchanged. A replay recorded on a fork sets it from its meta.
FORK: bool = os.environ.get("RISKDEP_FORK", "") not in ("", "0")


class CacheMiss(RuntimeError):
    pass


class SourceError(RuntimeError):
    pass


def _throttled(payload) -> bool:
    """A JSON-RPC answer refused for rate, in any batch item: HTTP-style code 429, or a message saying rate limit or too
    many requests (publicnode, eRPC, blockrazor, OnFinality on 2026-10-10). A bare -32005 is not enough: some nodes
    use it for 'too many log results', which a resend does not cure."""
    items = payload if isinstance(payload, list) else [payload] if isinstance(payload, dict) else []
    for it in items:
        err = it.get("error") if isinstance(it, dict) else None
        if isinstance(err, dict):
            msg = str(err.get("message", "")).lower()
            if err.get("code") == 429 or "rate limit" in msg or "rate-limit" in msg or "too many requests" in msg:
                return True
    return False


class Fetcher:
    """mode: 'offline' (cache only), 'live' (cache first, network on miss),
    'refresh' (network always, cache rewritten), 'direct' (network always, nothing cached:
    the watcher's live mode)."""

    def __init__(self, mode: str = "offline", snapshot_dir: Path = SNAPSHOT_DIR):
        if mode not in ("offline", "live", "refresh", "direct"):
            raise ValueError(mode)
        self.mode = mode
        self.dir = Path(snapshot_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.network_calls = 0
        self._recorded: set[Path] = set()  # refresh mode: requests already answered in this run

    def _key(self, method: str, url: str, body) -> Path:
        raw = json.dumps([method, url, body], sort_keys=True).encode()
        return self.dir / (hashlib.sha256(raw).hexdigest()[:24] + ".json")

    def cached(self, method: str, url: str, body=None) -> bool:
        return self._key(method, url, body).exists()

    def _request(self, method: str, url: str, body=None, transform=None, secret: dict | None = None):
        """`secret` (an API key) is added to the request only: never to the cache key, the stored URL or an error."""
        path = self._key(method, url, body)
        if (self.mode not in ("refresh", "direct") or path in self._recorded) and path.exists():
            # a recording keeps the first answer to a request: a second fetch in the same run (the Pendle market list,
            # read for a PT and again for the sibling search) would overwrite it with a later one, and the replay
            # would then disagree with what the recorded run computed from the first
            return json.loads(path.read_text())["response"]
        if self.mode == "offline":
            raise CacheMiss(
                f"no cached response for {method} {url} {json.dumps(body)[:120] if body else ''}; rerun with --live"
            )
        target = ROUTES.get(url, url)
        if secret:
            from urllib.parse import urlencode

            target += ("&" if "?" in target else "?") + urlencode(secret)
        last, done, failures, throttled = None, False, 0, 0
        pace = _hosts.setdefault(urlsplit(target).netloc, [0.0, 0.0])
        while failures < 3 and throttled < THROTTLE_RETRIES:
            try:
                if not (failures or throttled):  # a resend has already waited
                    time.sleep(max(0.0, pace[1] - time.monotonic()))
                pace[1] = time.monotonic() + pace[0]
                self.network_calls += 1
                if method == "GET":
                    r = requests.get(target, timeout=60)
                else:
                    r = requests.post(target, json=body, timeout=60)
                try:
                    payload = r.json()
                except ValueError:
                    payload = None
                if r.status_code == 429 or _throttled(payload):
                    # throttled: publicnode answers a burst with 429, a local eRPC with 200, both with a rate-limit
                    # error on every batch item. Wait and resend; passing that body on would read as calls that
                    # reverted, and a recording would keep it
                    throttled += 1
                    last = SourceError(f"rate limited {throttled} time(s), HTTP {r.status_code}")
                    pace[0] = min(PACE_MAX, max(PACE_MIN, 2 * pace[0]))
                    after = getattr(r, "headers", {}).get("Retry-After", "")
                    time.sleep(float(after) if after.isdigit() else min(60.0, 2.0**throttled))
                    continue
                pace[0] = 0.95 * pace[0] if 0.95 * pace[0] >= PACE_MIN else 0.0
                if (
                    r.status_code >= 400
                    and payload is not None
                    and ("error" in json.dumps(payload)[:2000] or (isinstance(payload, dict) and "message" in payload))
                ):
                    # the free node answers some refusals (archive reads) with 403 + a JSON-RPC error body;
                    # kept apart from `body`, which a retry must send again unchanged
                    data, done = payload, True
                    break
                r.raise_for_status()
                if payload is None:
                    raise ValueError("the response is not JSON")
                data, done = payload, True
                break
            except Exception as e:  # network, HTTP or JSON error
                last = e
                failures += 1
                time.sleep(1.5 * failures)
        if not done:
            # a routed URL may carry a key: name the public one only. requests' messages cut a URL into host, port
            # and path, so replacing the whole URL is not enough: a routed failure keeps only its kind
            msg = str(last) if target == url or isinstance(last, SourceError) else type(last).__name__
            for v in (secret or {}).values():
                msg = msg.replace(str(v), "***")
            hint = (
                " (sent through RISKDEP_RPC_URL: is the proxy running? Unset the variable to call the public RPC directly,"
                " see docs/setup/erpc.md)"
                if target != url and url in ROUTES
                else ""
            )
            raise SourceError(f"{method} {url} failed after {failures + throttled} attempts{hint}: {msg}")
        if transform:
            data = transform(data)
        if self.mode == "direct":
            return data
        path.write_text(
            json.dumps(
                {
                    "method": method,
                    "url": url,
                    "body": body,
                    "fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "response": data,
                }
            )
        )
        self._recorded.add(path)
        return data

    def get_json(self, url: str, transform=None, secret: dict | None = None):
        return self._request("GET", url, None, transform, secret)

    def post_json(self, url: str, body, transform=None):
        return self._request("POST", url, body, transform)


# --- thin clients -----------------------------------------------------------


def api_key(section: str, name: str = "api_key") -> str | None:
    """A key from keys.ini (never from the environment, never printed); None when absent or empty."""
    import configparser

    c = configparser.ConfigParser()
    c.read(KEYS_FILE)
    return c.get(section, name, fallback="").strip() or None


def archive_url() -> str | None:
    """An RPC serving old state, from keys.ini: `[rpc] url`, else `[alchemy] alchemy_ethereum_endpoint`. It may embed a
    key: it is only ever used as a route (`routed_rpc`), never cached, logged or printed."""
    return api_key("rpc", "url") or api_key("alchemy", "alchemy_ethereum_endpoint")


class routed_rpc:
    """`with routed_rpc(url):` sends the main RPC's requests to `url`; responses stay cached under the public URL, so a
    recording made through it replays offline with no key (D161)."""

    def __init__(self, url: str | None):
        self.url, self.before = url, None

    def __enter__(self):
        self.before = ROUTES.get(RPC)
        if self.url:
            ROUTES[RPC] = self.url
        return self

    def __exit__(self, *_):
        if self.before is None:
            ROUTES.pop(RPC, None)
        else:
            ROUTES[RPC] = self.before


def etherscan_logs(
    f: Fetcher, address: str, topic0: str, topic1: str | None, from_block: int, to_block: int
) -> list[dict]:
    """Event logs of one contract filtered by topic0 and topic1, through Etherscan (keyed; wide block ranges, which the
    free RPCs refuse), paged by 1,000; each log slimmed to block, time, topics, data and transaction (D161)."""
    key = api_key("etherscan")
    out, page = [], 1
    while True:
        url = (
            f"{ETHERSCAN}?chainid=1&module=logs&action=getLogs&address={address.lower()}&fromBlock={from_block}"
            f"&toBlock={to_block}&topic0={topic0}"
            + (f"&topic0_1_opr=and&topic1={topic1}" if topic1 else "")
            + f"&page={page}&offset=1000"
        )

        def slim(d):
            if str(d.get("status")) != "1" and d.get("message") != "No records found":
                raise SourceError(f"Etherscan logs: {d.get('message')}: {str(d.get('result'))[:120]}")
            return [
                {
                    "block": int(x["blockNumber"], 16),
                    "time": int(x["timeStamp"], 16),
                    "topics": x["topics"],
                    "data": x["data"],
                    "tx": x["transactionHash"],
                }
                for x in (d.get("result") or [])
            ]

        part = f.get_json(url, slim, {"apikey": key} if key else None)
        out += part
        if len(part) < 1000:
            return out
        page += 1


def contract_source(f: Fetcher, address: str) -> dict | None:
    """Etherscan `getsourcecode`, slimmed to {verified, name, proxy, implementation}; None when it cannot be known
    (no key and no cached answer, or Etherscan refused). Only the slim answer is cached, never the key."""
    url = f"{ETHERSCAN}?chainid=1&module=contract&action=getsourcecode&address={address.lower()}"
    key = api_key("etherscan")
    if not key and not (f.mode in ("offline", "live") and f.cached("GET", url)):
        return None

    def slim(d):
        if str(d.get("status")) != "1" or not d.get("result"):
            raise SourceError(f"Etherscan: {d.get('message')}")  # raised before caching: a refusal is not stored
        r = d["result"][0]
        return {
            "verified": bool(r.get("SourceCode")),
            "name": r.get("ContractName") or None,
            "proxy": r.get("Proxy") not in (None, "", "0"),
            "implementation": (r.get("Implementation") or "").lower() or None,
        }

    try:
        return f.get_json(url, slim, {"apikey": key} if key else None)
    except (SourceError, CacheMiss):
        return None


def morpho(f: Fetcher, query: str, variables: dict | None = None) -> dict:
    data = f.post_json(MORPHO, {"query": query, "variables": variables or {}})
    if data.get("errors"):
        raise SourceError(f"Morpho API: {data['errors'][0].get('message')}")
    return data["data"]


def rpc_call(f: Fetcher, to: str, signature: str, args_hex: str = "") -> str | None:
    """eth_call at 'latest'; returns the hex result or None on revert."""
    from eth_utils import keccak

    data = "0x" + keccak(text=signature)[:4].hex() + args_hex
    resp = f.post_json(
        RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, "latest"]}
    )
    return resp.get("result") if isinstance(resp, dict) else None


def rpc_batch(f: Fetcher, calls: list[tuple[str, str]], block: int | str = "latest") -> list[str | None]:
    """Many eth_call in one JSON-RPC batch. `calls` = [(to, calldata hex)]; None where reverted."""
    if not calls:
        return []
    tag = hex(block) if isinstance(block, int) else block
    body = [
        {"jsonrpc": "2.0", "id": i, "method": "eth_call", "params": [{"to": to, "data": data}, tag]}
        for i, (to, data) in enumerate(calls)
    ]
    resp = f.post_json(RPC, body)
    if not isinstance(resp, list):
        raise SourceError(f"RPC batch refused: {str(resp)[:200]}")
    by_id = {r.get("id"): r for r in resp}
    out = []
    for i in range(len(calls)):
        r = by_id.get(i, {})
        if "error" in r and "archive" in str(r["error"]).lower():
            raise SourceError(f"state at block {block} is too old for the free RPC: {r['error'].get('message')}")
        res = r.get("result")
        out.append(res if res and res != "0x" else None)
    return out


def rpc_batch_methods(f: Fetcher, calls: list[tuple[str, list]], chunk: int = 200) -> list:
    """Any JSON-RPC methods in batches, e.g. [("eth_getStorageAt", [addr, slot, tag])]; None on error."""
    out = []
    for i in range(0, len(calls), chunk):
        part = calls[i : i + chunk]
        body = [{"jsonrpc": "2.0", "id": j, "method": m, "params": p} for j, (m, p) in enumerate(part)]
        resp = f.post_json(RPC, body)
        if not isinstance(resp, list):
            raise SourceError(f"RPC batch refused: {str(resp)[:200]}")
        by_id = {r.get("id"): r for r in resp}
        for j in range(len(part)):
            r = by_id.get(j, {})
            if "error" in r and "archive" in str(r["error"]).lower():
                raise SourceError(f"state too old for the free RPC: {r['error'].get('message')}")
            out.append(r.get("result"))
    return out


def rpc(f: Fetcher, method: str, params: list):
    resp = f.post_json(RPC, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    return resp.get("result")


def coin_prices(f: Fetcher, addresses: list[str]) -> dict:
    keys = ",".join(f"ethereum:{a}" for a in sorted({a.lower() for a in addresses}))
    return f.get_json(f"{LLAMA_COINS}/prices/current/{keys}")["coins"]


def coin_drawdown(f: Fetcher, address: str, days: int = 365) -> dict:
    """Worst peak-to-trough drawdown of the token's USD price over `days` (daily)."""
    start = int(clock.now()) // 86400 * 86400 - days * 86400
    url = f"{LLAMA_COINS}/chart/ethereum:{address.lower()}?start={start}&span={days}&period=1d"
    pts = f.get_json(url).get("coins", {}).get(f"ethereum:{address.lower()}", {}).get("prices", [])
    peak, worst = 0.0, 0.0
    for p in pts:
        peak = max(peak, p["price"])
        if peak:
            worst = max(worst, 1 - p["price"] / peak)
    return {"points": len(pts), "max_drawdown": worst}


def _slim_protocols(data):
    return [
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "slug": p.get("slug"),
            "category": p.get("category"),
            "tvl": p.get("tvl"),
            "listedAt": p.get("listedAt"),
            "audits": p.get("audits"),
            "chains": p.get("chains"),
        }
        for p in data
    ]


def llama_protocols(f: Fetcher) -> list[dict]:
    return f.get_json(f"{LLAMA}/protocols", transform=_slim_protocols)


def llama_hacks(f: Fetcher) -> list[dict]:
    return f.get_json(f"{LLAMA}/hacks")
