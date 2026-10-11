"""`python -m riskdep notify`: post the watch alerts to a Telegram channel (TELEGRAM_BOT.md, option B).

A separate process that follows `out/watch-*.jsonl`, as the API does: the watcher never waits on Telegram. It posts
only alerts at or above the chosen level, nothing else: no heartbeat, no periodic message. Standing findings (alerts
with no transaction, printed again at every watch start) are posted once per `notify.dedup_blocks`. The alerts of one
block are one message: the cause first in plain words, the loss and the decision, the details folded underneath. Offsets are saved after each successful send, so a restart neither skips
nor resends. Credentials come from keys.ini `[alerts]` only; the token sits in the request path and is never printed.
"""

from __future__ import annotations

import html
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

from . import sources as S
from . import vault_book
from .discover import REGISTRY

N = REGISTRY["notify"]
LEVELS = {"info": 0, "warn": 1, "critical": 2}
ICON = {"critical": "🔴", "warn": "🟠", "info": "🔵"}
API = "https://api.telegram.org/bot{token}/sendMessage"
RUNBOOK = "https://github.com/rya-sge/defi-monitoring/blob/main/docs/reference/alert-runbook.md"
MAX_LEN = 4096  # Telegram's limit on one message


@dataclass
class Message:
    text: str
    silent: bool  # no sound on the phone: everything below critical
    end: int  # byte offset in the file once this message is sent
    buttons: list[tuple[str, str]] = field(default_factory=list)  # (label, url) under the message


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


# What each alert type means, in plain words (from the "What it means" column of the runbook); the incident's
# headline is the plain phrase of its cause.
PLAIN = {
    "Admin.Upgraded": "the code behind a price or a token was replaced",
    "Admin.BeaconUpgraded": "the code behind a price or a token was replaced",
    "AdminState": "the code or the owner of a dependency changed",
    "Admin.Mint": "a large amount of the collateral was created at once",
    "Admin.Paused": "a token the markets depend on was paused",
    "Admin.AdminChanged": "a new admin controls a dependency",
    "Admin.OwnershipTransferred": "a dependency changed owner",
    "Admin.AggregatorProposed": "a price feed is being replaced",
    "Admin.AggregatorConfirmed": "a price feed was replaced",
    "Admin.CallScheduled": "an upgrade is scheduled on a timelock",
    "Admin.RoleGranted": "someone was given admin rights",
    "FeedStale": "a price feed stopped updating",
    "CrossCheck": "two data sources disagree",
    "Gap": "some blocks could not be read",
    "Oracle": "the collateral's price moved sharply",
    "OracleDivergence": "the oracle disagrees with the market price",
    "DrainWindow": "the collateral trades far below its oracle price",
    "Blue.Liquidate": "a liquidation left debt nobody repays",
    "UnrealisedBadDebt": "loans are no longer covered by their collateral",
    "PendingLoss": "a loss is recorded but not yet in the share price",
    "Vault.AccrueInterest": "the vault's total assets fell",
    "Adapter.BurnShares": "the vault wrote off part of its lending",
    "Vault.Submit": "the curator queued a risky change",
    "Liquidity": "you can no longer withdraw everything at once",
    "Gate": "a gate blocks your withdrawal",
    "ExitQueue": "in a rush to the exit, you could be stuck",
    "OracleImpact": "the price drop has reached the vault",
    "HealthFactor": "your loan is close to liquidation",
    "Rate": "the borrow rate jumped",
    "Utilisation": "the market is almost fully lent out",
    "Exposure": "most of the vault sits in one market",
    "LiquidationCurve": "a small price fall would trigger many liquidations",
    "BorrowerConcentration": "one borrower holds most of the debt",
    "Timelock": "risky changes can be made with no notice",
}
# Cause first: a change of code or owner, then data problems, the price, the losses, the exit; OracleImpact carries
# the decision and goes on top, not in this order.
RANK = [("Admin", 0), ("FeedStale", 1), ("CrossCheck", 1), ("Gap", 1), ("Oracle", 2), ("DrainWindow", 3)]
LOSSES = ("Blue.Liquidate", "UnrealisedBadDebt", "PendingLoss", "Vault.AccrueInterest", "Adapter.BurnShares")
# The runbook section of each alert family, for the "What to do" button.
SECTION = [
    ("Admin", "admin-surface-alerts-vault-depositors-and-borrowers"),
    ("HealthFactor", "liquidation"),
    ("CrossCheck", "data-and-infrastructure-alerts"),
    ("Gap", "data-and-infrastructure-alerts"),
    ("FeedStale", "losses"),
    ("Vault.Submit", "governance-changes"),
    ("Exposure", "exposure-and-liquidity"),
    ("Liquidity", "exposure-and-liquidity"),
    ("ExitQueue", "exposure-and-liquidity"),
]
ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
LLTV = re.compile(r" \(LLTV [\d.]+%\)")
UNIT = re.compile(r"\d[\d,.]* ([A-Za-z][A-Za-z0-9]{1,9})\b")


def _esc(text: str) -> str:
    return html.escape(text, quote=False)  # Telegram needs only <, > and & escaped


def _rank(al: dict) -> int:
    ev = al["event"]
    if ev == "OracleImpact":
        return 9
    if ev in LOSSES:
        return 4
    return next((r for p, r in RANK if ev == p or ev.startswith(p + ".") or ev.startswith(p)), 5)


def _short(text: str) -> str:
    """Addresses as 0x1234…abcd, so a line fits a phone."""
    return ADDRESS.sub(lambda m: f"{m.group()[:6]}…{m.group()[-4:]}", text)


def plain(al: dict) -> str:
    return PLAIN.get(al["event"]) or PLAIN.get(al["event"].split(".")[0], "") or al["event"]


def _unit(alerts: list[dict]) -> str:
    """The vault's asset as the alerts write it ("1,902,392 USDC"); empty when none says it."""
    for a in alerts:
        if m := UNIT.search(a.get("detail", "")):
            return " " + m.group(1)
    return ""


def runbook_url(al: dict) -> str:
    ev = al["event"]
    anchor = next((a for p, a in SECTION if ev.startswith(p)), "losses" if ev in LOSSES else "")
    if not anchor:
        anchor = "exposure-and-liquidity" if al["level"] == "warn" else "losses"
    return f"{RUNBOOK}#{anchor}"


def decision(impact: dict, unit: str) -> str:
    """The OracleImpact verdict as one line: what to do and what it changes for the depositor."""
    d = impact.get("data", {})
    verdict, stay, first, out = (
        d.get("verdict"),
        d.get("loss_if_stay"),
        d.get("loss_if_exit_first"),
        d.get("can_leave_now"),
    )
    if not verdict:
        return ""
    line = f"👉 <b>Decision: {_esc(verdict)}</b>"
    if verdict == "EXIT" and None not in (stay, first, out):
        return f"{line}. Withdraw the {out:,.0f}{unit} that can leave now: your loss falls from {stay:,.0f} to {first:,.0f}{unit}."
    if stay is not None:
        return f"{line}. Staying loses {stay:,.0f}{unit}; leaving first would not lower it enough to pay."
    return line


def format_incident(alerts: list[dict], label: str) -> tuple[str, list[tuple[str, str]]]:
    """Alerts of one block as one message: what happened (the cause first), what it costs, what to do, then the
    details folded in an expandable quote; and the buttons under it."""
    alerts = sorted(alerts, key=_rank)
    impact = next((a for a in alerts if a["event"] == "OracleImpact"), None)
    others = [a for a in alerts if a is not impact]
    cause = others[0] if others else impact
    top = max(alerts, key=lambda a: LEVELS[a["level"]])["level"]
    unit = _unit(alerts)
    head = plain(cause)
    lines = [
        f"{ICON[top]} <b>{_esc(label)}</b> — {_esc(head[:1].upper() + head[1:])}",
        _esc(_short(LLTV.sub("", cause["title"]))),
    ]
    if impact:
        d = impact.get("data", {})
        if d.get("vault_loss") is not None:
            you = f" · yours {d['loss_if_stay']:,.0f}{unit}" if d.get("loss_if_stay") is not None else ""
            lines.append(f"💸 The vault's loss: {d['vault_loss']:,.0f}{unit}{you}")
        if line := decision(impact, unit):
            lines.append(line)
    elif hit := next((a for a in alerts if a.get("depositor_impact")), None):
        lines.append(f"💸 Your share of the loss: {-hit['depositor_impact']:,.0f}{unit}")
    rows = []
    for a in others + ([impact] if impact else []):
        detail = f" — {_esc(_short(a['detail']))}" if a.get("detail") else ""
        rows.append(f"{ICON[a['level']]} <b>{_esc(plain(a))}</b>: {_esc(_short(a['title']))}{detail}")
    n = len(alerts)
    lines.append(
        f"<blockquote expandable>Details: {n} alert{'s' if n > 1 else ''}, block {alerts[0]['block']:,}\n"
        + "\n".join(rows)
        + "</blockquote>"
    )
    buttons = [("What to do", runbook_url(cause))]
    tx = next((a["tx"] for a in alerts if a.get("tx")), None)
    if tx and not S.FORK:  # a fork's transactions are not on Etherscan
        buttons.append(("Etherscan", f"https://etherscan.io/tx/{tx}"))
    return _cap("\n".join(lines)), buttons


def _cap(text: str) -> str:
    if len(text) <= MAX_LEN:
        return text
    # cut inside the details, keeping the quote closed so the HTML stays valid
    return text[: MAX_LEN - 20] + "…</blockquote>" if "<blockquote" in text else text[: MAX_LEN - 1] + "…"


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
    """The selected alerts as messages: one per block (an incident and its consequences arrive together), and past
    `burst_max` messages the rest as one."""
    groups: list[list[tuple[dict, int]]] = []
    for row in rows:
        if groups and groups[-1][0][0]["block"] == row[0]["block"]:
            groups[-1].append(row)
        else:
            groups.append([row])
    if len(groups) > N["burst_max"]:
        groups = groups[: N["burst_max"] - 1] + [[r for g in groups[N["burst_max"] - 1 :] for r in g]]
    out = []
    for g in groups:
        alerts = [a for a, _ in g]
        text, buttons = format_incident(alerts, label)
        out.append(Message(text, not any(a["level"] == "critical" for a in alerts), g[-1][1], buttons))
    return out


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


def send(creds: tuple[str, str], text: str, silent: bool, session=requests, buttons=()) -> bool:
    """One message; waits and retries on Telegram's 429; if Telegram rejects the HTML, sends it once as plain text
    so one bad message cannot block the queue; gives up (False) on any other failure."""
    token, chat = creds
    body = {
        "chat_id": chat,
        "text": text,
        "parse_mode": "HTML",
        "disable_notification": silent,
        "disable_web_page_preview": True,
    }
    if buttons:
        body["reply_markup"] = {"inline_keyboard": [[{"text": t, "url": u} for t, u in buttons]]}
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
        if r.status_code == 400 and "parse_mode" in body:
            body.pop("parse_mode")
            body["text"] = html.unescape(re.sub(r"<[^>]+>", "", text))
            continue
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
                if not send(self.creds, m.text, m.silent, self.session, m.buttons):
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
    return _cap(f"📊 <b>Scenario</b> · {_esc(name)}\n{_esc(d['headline'])}")


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
