"""Keyless data sources behind one cached fetcher.

Every request is keyed by a hash of (method, url, body) and stored under
data/snapshot/, so a live run doubles as the offline demo snapshot.
"""

from __future__ import annotations

import hashlib
import json
import time
import warnings
from pathlib import Path

from . import clock

warnings.filterwarnings("ignore", message=".*doesn't match a supported version.*")
import requests  # noqa: E402

SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "data" / "snapshot"

PENDLE = "https://api-v2.pendle.finance/core"
MORPHO = "https://blue-api.morpho.org/graphql"
LLAMA = "https://api.llama.fi"
LLAMA_COINS = "https://coins.llama.fi"
LLAMA_YIELDS = "https://yields.llama.fi"
RPC = "https://ethereum-rpc.publicnode.com"


class CacheMiss(RuntimeError):
    pass


class SourceError(RuntimeError):
    pass


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

    def _key(self, method: str, url: str, body) -> Path:
        raw = json.dumps([method, url, body], sort_keys=True).encode()
        return self.dir / (hashlib.sha256(raw).hexdigest()[:24] + ".json")

    def _request(self, method: str, url: str, body=None, transform=None):
        path = self._key(method, url, body)
        if self.mode not in ("refresh", "direct") and path.exists():
            return json.loads(path.read_text())["response"]
        if self.mode == "offline":
            raise CacheMiss(f"no cached response for {method} {url} {json.dumps(body)[:120] if body else ''}; rerun with --live")
        last = None
        for attempt in range(3):
            try:
                self.network_calls += 1
                if method == "GET":
                    r = requests.get(url, timeout=60)
                else:
                    r = requests.post(url, json=body, timeout=60)
                if r.status_code >= 400:
                    # the free node answers some refusals (archive reads) with 403 + a JSON-RPC error body
                    try:
                        body = r.json()
                    except ValueError:
                        body = None
                    if body is not None and "error" in json.dumps(body)[:2000]:
                        data = body
                        break
                r.raise_for_status()
                data = r.json()
                break
            except Exception as e:  # network, HTTP or JSON error
                last = e
                time.sleep(1.5 * (attempt + 1))
        else:
            raise SourceError(f"{method} {url} failed after 3 attempts: {last}")
        if transform:
            data = transform(data)
        if self.mode == "direct":
            return data
        path.write_text(json.dumps({"method": method, "url": url, "body": body,
                                    "fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                    "response": data}))
        return data

    def get_json(self, url: str, transform=None):
        return self._request("GET", url, None, transform)

    def post_json(self, url: str, body, transform=None):
        return self._request("POST", url, body, transform)


# --- thin clients -----------------------------------------------------------

def morpho(f: Fetcher, query: str, variables: dict | None = None) -> dict:
    data = f.post_json(MORPHO, {"query": query, "variables": variables or {}})
    if data.get("errors"):
        raise SourceError(f"Morpho API: {data['errors'][0].get('message')}")
    return data["data"]


def rpc_call(f: Fetcher, to: str, signature: str, args_hex: str = "") -> str | None:
    """eth_call at 'latest'; returns the hex result or None on revert."""
    from eth_utils import keccak
    data = "0x" + keccak(text=signature)[:4].hex() + args_hex
    resp = f.post_json(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                             "params": [{"to": to, "data": data}, "latest"]})
    return resp.get("result") if isinstance(resp, dict) else None


def rpc_batch(f: Fetcher, calls: list[tuple[str, str]], block: int | str = "latest") -> list[str | None]:
    """Many eth_call in one JSON-RPC batch. `calls` = [(to, calldata hex)]; None where reverted."""
    if not calls:
        return []
    tag = hex(block) if isinstance(block, int) else block
    body = [{"jsonrpc": "2.0", "id": i, "method": "eth_call", "params": [{"to": to, "data": data}, tag]}
            for i, (to, data) in enumerate(calls)]
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
        part = calls[i:i + chunk]
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
    return [{"id": p.get("id"), "name": p.get("name"), "slug": p.get("slug"), "category": p.get("category"),
             "tvl": p.get("tvl"), "listedAt": p.get("listedAt"), "audits": p.get("audits"),
             "chains": p.get("chains")} for p in data]


def llama_protocols(f: Fetcher) -> list[dict]:
    return f.get_json(f"{LLAMA}/protocols", transform=_slim_protocols)


def llama_hacks(f: Fetcher) -> list[dict]:
    return f.get_json(f"{LLAMA}/hacks")
