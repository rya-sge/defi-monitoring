"""Telegram delivery (TELEGRAM_BOT.md): selection, grouping, formatting and offsets, offline with a stubbed session."""

import json

import requests

from riskdep import notify as NT

CREDS = ("123:token", "-10042")


def alert(level="warn", block=100, tx="0xabc0000000000000", event="Exposure", title="t", **kw):
    return {"level": level, "block": block, "tx": tx, "event": event, "title": title, "detail": "", **kw}


class Resp:
    def __init__(self, status=200, body=None):
        self.status_code, self.ok, self.body = status, status == 200, body or {"ok": status == 200}

    def json(self):
        return self.body


class Session:
    """Answers each post with the next scripted response (200 once the script is used up) and records the body."""

    def __init__(self, script=()):
        self.script, self.posts = list(script), []

    def post(self, url, json, timeout):
        self.posts.append(json)
        r = self.script.pop(0) if self.script else Resp()
        if isinstance(r, Exception):
            raise r
        return r


def write(path, alerts):
    with path.open("a") as fh:
        for a in alerts:
            fh.write(json.dumps(a) + "\n")


def notifier(tmp_path, session, level="warn"):
    return NT.Notifier(tmp_path, level, True, CREDS, session=session, gap=0)


def test_only_risk_is_posted(tmp_path):
    write(tmp_path / "watch-0xvault.jsonl", [alert("info"), alert("warn", title="w"), alert("critical", title="c")])
    s = Session()
    assert notifier(tmp_path, s).once() == 2
    assert [p["disable_notification"] for p in s.posts] == [True, False]  # sound for critical only
    assert notifier(tmp_path, Session()).once() == 0  # nothing new, nothing sent: no heartbeat


def test_standing_findings_grouped_and_sent_once(tmp_path):
    start = [alert(tx=None, title="a"), alert(tx=None, title="b", level="critical")]
    write(tmp_path / "watch-0xvault.jsonl", start)
    s = Session()
    assert notifier(tmp_path, s).once() == 1
    assert "1 critical, 1 warn" in s.posts[0]["text"] and s.posts[0]["disable_notification"] is False
    # a watch restart prints them again a few blocks later: not resent
    write(tmp_path / "watch-0xvault.jsonl", [alert(tx=None, title="a", block=110)])
    assert notifier(tmp_path, Session()).once() == 0
    # after the dedup window they are news again
    write(tmp_path / "watch-0xvault.jsonl", [alert(tx=None, title="a", block=110 + NT.N["dedup_blocks"])])
    assert notifier(tmp_path, Session()).once() == 1


def test_burst_collapses_to_digest(tmp_path):
    n = NT.N["burst_max"] + 5
    write(tmp_path / "watch-0xvault.jsonl", [alert(title=f"t{i}", tx=f"0x{i:016x}") for i in range(n)])
    s = Session()
    assert notifier(tmp_path, s).once() == NT.N["burst_max"]
    assert "burst: 6 warn" in s.posts[-1]["text"]


def test_failed_send_keeps_offset(tmp_path):
    write(tmp_path / "watch-0xvault.jsonl", [alert(title="one", tx="0x1"), alert(title="two", tx="0x2")])
    s = Session([Resp(), requests.ConnectionError()])
    assert notifier(tmp_path, s).once() == 1
    s2 = Session()
    assert notifier(tmp_path, s2).once() == 1  # only the unsent one comes back
    assert "two" in s2.posts[0]["text"]


def test_rate_limit_is_waited_out(tmp_path):
    s = Session([Resp(429, {"ok": False, "parameters": {"retry_after": 0}}), Resp()])
    assert NT.send(CREDS, "x", True, s) and len(s.posts) == 2


def test_partial_line_waits(tmp_path):
    path = tmp_path / "watch-0xvault.jsonl"
    write(path, [alert(title="done")])
    with path.open("a") as fh:
        fh.write('{"level": "warn", "blo')  # the watcher is mid-write
    rows, end = NT.read_new(path, 0)
    assert len(rows) == 1 and end == rows[0][1]


def test_format_escapes_and_names(tmp_path):
    text = NT.format_alert(alert(title="a < b & c", detail="<x>", depositor_impact=-12.5), "Vault")
    assert "a &lt; b &amp; c" in text and "&lt;x&gt;" in text and "You: -12.50" in text
    assert "etherscan.io/tx/0xabc" in text and len(NT.format_alert(alert(detail="x" * 5000), "V")) <= NT.MAX_LEN
    names = NT.target_names()
    assert NT.target_label("0xc207d3f66537d7f66456808379a0e560cf20da36", names) == "RockawayX Confidential RWA USDC"
    assert NT.target_label("user-0xdf81987465681d0515058fe0a47a3bd174012730", names) == "user 0xdf81…2730"


def test_headline_of_an_incident(tmp_path):
    p = tmp_path / "book-incident.json"
    p.write_text(json.dumps({"name": "Book", "headline": "PST −30%: the book loses 5,195,130 USD"}))
    assert "Scenario" in NT.headline(p) and "5,195,130" in NT.headline(p)
