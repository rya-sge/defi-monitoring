"""`python -m riskdep notify`: post the watch alerts to a Telegram channel (TELEGRAM_BOT.md, option B).

A separate process that follows `out/watch-*.jsonl`, as the API does: the watcher never waits on Telegram. It posts
only alerts at or above the chosen level, nothing else: no heartbeat, no periodic message. Standing findings (alerts
with no transaction, printed again at every watch start) are posted once per `notify.dedup_blocks`, and those of one
start are grouped into a single message. Offsets are saved after each successful send, so a restart neither skips
nor resends. Credentials come from keys.ini `[alerts]` only; the token sits in the request path and is never printed.
"""

from __future__ import annotations

import html
import json
import time
from dataclasses import dataclass
from pathlib import Path

import requests

from . import sources as S
from . import vault_book
from .discover import REGISTRY

N = REGISTRY["notify"]
LEVELS = {"info": 0, "warn": 1, "critical": 2}
ICON = {"critical": "🔴", "warn": "🟠", "info": "🔵"}
API = "https://api.telegram.org/bot{token}/sendMessage"
RUNBOOK = "https://github.com/rya-sge/defi-monitoring/blob/main/docs/alert-runbook.md"
MAX_LEN = 4096  # Telegram's limit on one message


@dataclass
class Message:
    text: str
    silent: bool  # no sound on the phone: everything below critical
    end: int  # byte offset in the file once this message is sent


# --- pure parts ---------------------------------------------------------------


def target_names() -> dict[str, str]:
    """Vault address → label, from the books in examples/."""
    return {v.address.lower(): v.label for b in vault_book.examples().values() for v in b.vaults if v.label}


def target_label(target: str, names: dict[str, str]) -> str:
    """`watch-<target>.jsonl` → a readable name: the vault's label, else a short address."""
    user = target.startswith("user-")
    addr = target.removeprefix("user-")
    name = names.get(addr.lower()) or (f"{addr[:6]}…{addr[-4:]}" if addr.startswith("0x") else addr)
    return f"user {name}" if user else name


def _line(al: dict) -> str:
    return f"<b>{html.escape(al['event'])}</b> — {html.escape(al['title'])}"


def format_alert(al: dict, label: str) -> str:
    """One alert as Telegram HTML: level and target, event and title, detail, the depositor's impact, links."""
    parts = [f"{ICON[al['level']]} <b>{al['level'].upper()}</b> · {html.escape(label)}", _line(al)]
    if al.get("detail"):
        parts.append(html.escape(al["detail"]))
    if al.get("depositor_impact"):
        parts.append(f"You: {al['depositor_impact']:+,.2f}")
    tx = f' · <a href="https://etherscan.io/tx/{al["tx"]}">tx {al["tx"][:10]}…</a>' if al.get("tx") else ""
    parts.append(f'block {al["block"]}{tx} · <a href="{RUNBOOK}">runbook</a>')
    return _cap("\n".join(parts))


def format_digest(alerts: list[dict], label: str, why: str) -> str:
    """Several alerts in one message, the most severe first."""
    alerts = sorted(alerts, key=lambda a: -LEVELS[a["level"]])
    count = ", ".join(
        f"{n} {lv}" for lv in ("critical", "warn", "info") if (n := sum(a["level"] == lv for a in alerts))
    )
    head = f"{ICON[alerts[0]['level']]} <b>{html.escape(label)}</b> · {why}: {count}"
    return _cap("\n".join([head] + [f"• {_line(a)}" for a in alerts]))


def _cap(text: str) -> str:
    return text if len(text) <= MAX_LEN else text[: MAX_LEN - 1] + "…"


def select(rows: list[tuple[dict, int]], level: str, seen: dict[str, int], target: str) -> list[tuple[dict, int]]:
    """The alerts worth posting: at or above `level`, and a standing finding only if not posted in the last
    `dedup_blocks` blocks. `rows` are (alert, end offset); `seen` (key → block) is updated in place."""
    out = []
    for al, end in rows:
        if LEVELS.get(al.get("level"), -1) < LEVELS[level]:
            continue
        if al.get("tx") is None:
            key = f"{target}|{al['event']}|{al['title']}"
            if al["block"] - seen.get(key, -(10**12)) < N["dedup_blocks"]:
                continue
            seen[key] = al["block"]
        out.append((al, end))
    return out


def messages(rows: list[tuple[dict, int]], label: str) -> list[Message]:
    """The selected alerts as messages: standing findings of one block grouped into one digest, every other alert on
    its own, and the tail grouped into one digest past `burst_max` messages."""
    msgs: list[Message] = []
    i = 0
    while i < len(rows):
        al, end = rows[i]
        j = i + 1
        if al.get("tx") is None:
            while j < len(rows) and rows[j][0].get("tx") is None and rows[j][0]["block"] == al["block"]:
                j += 1
        group = [a for a, _ in rows[i:j]]
        text = format_alert(al, label) if len(group) == 1 else format_digest(group, label, f"block {al['block']}")
        crit = any(a["level"] == "critical" for a in group)
        msgs.append(Message(text, not crit, rows[j - 1][1]))
        i = j
    if len(msgs) > N["burst_max"]:
        keep = msgs[: N["burst_max"] - 1]
        rest = [a for a, e in rows if e > keep[-1].end] if keep else [a for a, _ in rows]
        crit = any(a["level"] == "critical" for a in rest)
        keep.append(Message(format_digest(rest, label, "burst"), not crit, msgs[-1].end))
        msgs = keep
    return msgs


def read_new(path: Path, offset: int) -> tuple[list[tuple[dict, int]], int]:
    """Complete lines after `offset`, each with the offset just past it; a partly written last line waits."""
    with path.open("rb") as fh:
        fh.seek(offset)
        chunk = fh.read()
    rows, pos = [], offset
    for raw in chunk.split(b"\n")[:-1]:
        pos += len(raw) + 1
        if raw.strip():
            rows.append((json.loads(raw), pos))
    return rows, pos


# --- I/O ------------------------------------------------------------------------


def credentials() -> tuple[str, str] | None:
    token, chat = S.api_key("alerts", "telegram_bot_token"), S.api_key("alerts", "telegram_chat_id")
    return (token, chat) if token and chat else None


def send(creds: tuple[str, str], text: str, silent: bool, session=requests) -> bool:
    """One message; waits and retries on Telegram's 429, gives up (False) on any other failure."""
    token, chat = creds
    body = {
        "chat_id": chat,
        "text": text,
        "parse_mode": "HTML",
        "disable_notification": silent,
        "disable_web_page_preview": True,
    }
    for _ in range(N["max_retries"]):
        try:
            r = session.post(API.format(token=token), json=body, timeout=30)
        except requests.RequestException as e:
            print(f"telegram: {type(e).__name__}, will retry", flush=True)  # never the URL: it holds the token
            return False
        if r.status_code == 429:
            time.sleep(r.json().get("parameters", {}).get("retry_after", 5))
            continue
        if r.ok:
            return True
        print(f"telegram: HTTP {r.status_code} {r.json().get('description', '')}", flush=True)
        return False
    return False


class Notifier:
    def __init__(self, out_dir: Path, level: str, from_start: bool, creds, session=requests, gap: float | None = None):
        self.out_dir, self.level, self.from_start = out_dir, level, from_start
        self.creds, self.session = creds, session
        self.gap = N["min_gap_seconds"] if gap is None else gap
        self.state_path = out_dir / "notify.state.json"
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {}
        self.state.setdefault("offsets", {})
        self.state.setdefault("seen", {})
        self.names = target_names()
        self.last_send = 0.0

    def save(self) -> None:
        self.state_path.write_text(json.dumps(self.state, indent=1))

    def once(self) -> int:
        """One pass over every watch file; the number of messages sent."""
        sent = 0
        for path in sorted(self.out_dir.glob("watch-*.jsonl")):
            key = path.name
            if key not in self.state["offsets"]:
                self.state["offsets"][key] = 0 if self.from_start else path.stat().st_size
            target = path.stem.removeprefix("watch-")
            rows, end = read_new(path, self.state["offsets"][key])
            if not rows:
                self.state["offsets"][key] = end
                continue
            seen = dict(self.state["seen"])
            msgs = messages(select(rows, self.level, seen, target), target_label(target, self.names))
            for m in msgs:
                time.sleep(max(0.0, self.last_send + self.gap - time.monotonic()))  # only between alerts
                if not send(self.creds, m.text, m.silent, self.session):
                    self.save()
                    return sent  # the offset stays before the unsent message: retried next pass
                self.last_send = time.monotonic()
                self.state["offsets"][key] = m.end
                sent += 1
                self.save()
            self.state["offsets"][key] = end
            self.state["seen"] = seen
            self.save()
        return sent


def headline(path: Path) -> str:
    """The headline of an incident run (`out/book-incident.json`, or any JSON with a `headline`), as a message."""
    d = json.loads(path.read_text())
    name = d.get("name", path.stem)
    return _cap(f"📊 <b>Scenario</b> · {html.escape(name)}\n{html.escape(d['headline'])}")


def run(args) -> int:
    creds = credentials()
    if not creds:
        print("telegram: not configured (keys.ini [alerts] telegram_bot_token and telegram_chat_id)")
        return 1
    if args.test:
        ok = send(creds, "riskdep: test message, the alert bot can post to this channel.", True)
        print("telegram: test sent" if ok else "telegram: test failed")
        return 0 if ok else 1
    if args.post:
        ok = send(creds, headline(Path(args.post)), False)
        print("telegram: posted" if ok else "telegram: post failed")
        return 0 if ok else 1
    n = Notifier(Path(args.out), args.level, args.from_start, creds)
    print(f"notify: following {n.out_dir}/watch-*.jsonl, level ≥ {args.level}; Ctrl-C to stop", flush=True)
    try:
        while True:
            sent = n.once()
            if sent:
                print(f"notify: {sent} message(s) sent", flush=True)
            if args.once:
                return 0
            time.sleep(N["poll_seconds"])
    except KeyboardInterrupt:
        return 0
