"""The as-of clock, the oracle ambiguity flag and the cross-checks."""

import json
import time

import pytest

from riskdep import clock, cli, crosscheck, discover
from riskdep import sources as S


@pytest.fixture(autouse=True)
def reset_clock():
    yield
    clock.set_as_of(None)


def test_offline_demo_does_not_depend_on_today(tmp_path, monkeypatch):
    """Was a bug: the DefiLlama chart URL used today's date, so the snapshot missed the next day."""
    real = time.time
    monkeypatch.setattr(time, "time", lambda: real() + 400 * 86400)
    assert cli.main(["analyze", "--demo", "--out", str(tmp_path), "--paths", "2000"]) == 0
    rep = json.loads((tmp_path / "report.json").read_text())
    assert rep["data_as_of"].startswith("2026-10-10")
    assert rep["position"]["days_to_maturity"] == pytest.approx(46.56, abs=0.01)


def _fake_oracle(monkeypatch, price):
    def rpc_call(f, to, sig, args=""):
        if sig == "price()":
            return hex(int(price * 10 ** 24))       # PT 18 decimals, loan 6 decimals: scale 1e24
        return None
    monkeypatch.setattr(S, "rpc_call", rpc_call)
    monkeypatch.setattr(S, "rpc", lambda f, m, p: "0x")


def test_oracle_near_par_is_ambiguous(monkeypatch):
    _fake_oracle(monkeypatch, 0.9935)
    mode, price, why, amb = discover.infer_oracle(None, "0x0", 18, 6, 0.9938, pt_discount=0.006)
    assert amb and mode == "market-tracking" and "Ambiguous" in why


def test_oracle_far_from_par_is_classified(monkeypatch):
    _fake_oracle(monkeypatch, 0.95)
    assert discover.infer_oracle(None, "0x0", 18, 6, 0.951, pt_discount=0.05)[0::3] == ("market-tracking", False)
    _fake_oracle(monkeypatch, 1.0)
    assert discover.infer_oracle(None, "0x0", 18, 6, 0.951, pt_discount=0.05)[0::3] == ("fundamental", False)


class FakeF:
    """Answers post_json by URL and method."""

    def __init__(self, answers):
        self.answers = answers

    def post_json(self, url, body):
        if isinstance(body, list):
            raise S.CacheMiss("batch")
        key = (url, body.get("method"))
        if key not in self.answers:
            raise S.SourceError("down")
        return {"result": self.answers[key]}


def test_second_rpc_agrees_and_disagrees():
    same = FakeF({(S.RPC, "eth_getBlockByNumber"): {"hash": "0xaa"},
                  (crosscheck.SECOND_RPCS[0], "eth_getBlockByNumber"): {"hash": "0xaa"}})
    assert crosscheck.second_rpc(same, 1).ok is True
    fork = FakeF({(S.RPC, "eth_getBlockByNumber"): {"hash": "0xaa"},
                  (crosscheck.SECOND_RPCS[0], "eth_getBlockByNumber"): {"hash": "0xbb"}})
    assert crosscheck.second_rpc(fork, 1).ok is False
    down = FakeF({(S.RPC, "eth_getBlockByNumber"): {"hash": "0xaa"}})
    assert crosscheck.second_rpc(down, 1).ok is None


def test_position_mismatch_is_reported(monkeypatch):
    # on-chain: 100 collateral units, 50 borrow shares worth 50 assets
    word = lambda x: hex(x)[2:].rjust(64, "0")
    pos = "0x" + word(0) + word(50 * 10 ** 6) + word(100 * 10 ** 18)
    mk = "0x" + word(0) + word(0) + word(50) + word(50 * 10 ** 6)
    monkeypatch.setattr(S, "rpc_batch", lambda f, calls, block: [pos, mk])
    assert crosscheck.morpho_position(None, "0x" + "00" * 32, "0x" + "11" * 20, 18, 0, 100.0, 50).ok is True
    assert crosscheck.morpho_position(None, "0x" + "00" * 32, "0x" + "11" * 20, 18, 0, 120.0, 50).ok is False


def test_unavailable_check_never_raises(monkeypatch):
    def boom(*a, **k):
        raise S.CacheMiss("x")
    monkeypatch.setattr(S, "rpc_batch", boom)
    assert crosscheck.morpho_position(None, "0x" + "00" * 32, "0x" + "11" * 20, 18, 6, 1.0, 1).ok is None
