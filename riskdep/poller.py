"""Block poller (D21): eth_blockNumber + eth_getLogs from a saved cursor.

The cursor is the last block whose alerts were written. The poller stays `confirmations`
blocks behind the head, so a reorg shallower than that is never seen. Ranges the free node
refuses as "archive" are skipped and reported as a gap, never silently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import sources as S
from .abi import EVENTS, MORPHO_BLUE, Event, decode_log

BLUE_TOPICS = sorted({e.topic0 for e in EVENTS if e.contract == "blue" and e.name != "SetAuthorization"})


@dataclass
class Batch:
    from_block: int
    to_block: int
    head: int
    events: list[Event]
    unknown: int = 0                   # logs on our filters that no spec decodes
    gap: tuple[int, int] | None = None  # blocks that could not be read

    @property
    def by_tx(self) -> dict[str, list[Event]]:
        out: dict[str, list[Event]] = {}
        for e in self.events:
            out.setdefault(e.tx, []).append(e)
        return out


@dataclass
class Poller:
    f: S.Fetcher
    kinds: dict[str, str]              # address -> blue | vault | adapter
    market_ids: list[str]
    cursor_path: Path
    confirmations: int = 2
    max_range: int = 500
    start_back: int = 50               # first run: start this many blocks behind the safe head
    extra_filters: list[dict] = field(default_factory=list)   # more eth_getLogs filters (address, topics)
    cursor: int | None = field(default=None, init=False)

    def __post_init__(self):
        if self.cursor_path.exists():
            self.cursor = int(self.cursor_path.read_text().strip())

    def save(self, block: int) -> None:
        self.cursor = block
        self.cursor_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.cursor_path.with_suffix(".tmp")
        tmp.write_text(str(block))
        tmp.replace(self.cursor_path)

    def head(self) -> int:
        return int(S.rpc(self.f, "eth_blockNumber", []), 16)

    def _logs(self, a: int, b: int) -> list[dict]:
        watched = [x for x, k in self.kinds.items() if k != "blue"]
        flt = [{"address": watched, "fromBlock": hex(a), "toBlock": hex(b)}] if watched else []
        if self.market_ids:
            flt.append({"address": MORPHO_BLUE, "fromBlock": hex(a), "toBlock": hex(b),
                        "topics": [BLUE_TOPICS, self.market_ids]})
        flt += [{**x, "fromBlock": hex(a), "toBlock": hex(b)} for x in self.extra_filters]
        out = []
        for q in flt:
            r = self.f.post_json(S.RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs", "params": [q]})
            if "error" in r:
                msg = str(r["error"].get("message", r["error"]))
                if "archive" in msg.lower():
                    raise ArchiveRange(msg)
                if "range" in msg.lower() or "limit" in msg.lower() or "too many" in msg.lower():
                    raise RangeTooLarge(msg)
                raise S.SourceError(f"eth_getLogs: {msg}")
            out += r["result"]
        return out

    def next_batch(self) -> Batch | None:
        """The next range of new, confirmed blocks, decoded; None when caught up."""
        head = self.head()
        safe = head - self.confirmations
        if self.cursor is None:
            self.cursor = safe - self.start_back
        if safe <= self.cursor:
            return None
        a = self.cursor + 1
        b = min(safe, self.cursor + self.max_range)
        gap = None
        while True:
            try:
                raw = self._logs(a, b)
                break
            except ArchiveRange:
                # too old for the free node: jump to the last window it serves, report the gap
                new_a = max(a, safe - self.max_range + 1)
                if new_a == a:
                    raise S.SourceError(f"blocks {a}-{b} refused as archive even at the head")
                gap = (a, new_a - 1)
                a, b = new_a, safe
            except RangeTooLarge:
                if b == a:
                    raise
                b = a + (b - a) // 2
        raw.sort(key=lambda l: (int(l["blockNumber"], 16), int(l["logIndex"], 16)))
        events, unknown = [], 0
        for log in raw:
            ev = decode_log(log, self.kinds)
            if ev is None:
                unknown += 1
            else:
                events.append(ev)
        return Batch(a, b, head, events, unknown, gap)


class ArchiveRange(S.SourceError):
    pass


class RangeTooLarge(S.SourceError):
    pass
