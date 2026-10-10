"""The as-of clock, the oracle ambiguity flag and the cross-checks."""

import json
import time

import pytest

from riskdep import cli, clock, crosscheck, discover
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
            return hex(int(price * 10**24))  # PT 18 decimals, loan 6 decimals: scale 1e24
        return None

    monkeypatch.setattr(S, "rpc_call", rpc_call)
    monkeypatch.setattr(S, "rpc", lambda f, m, p: "0x")
    monkeypatch.setattr(S, "contract_source", lambda f, a: None)


def test_oracle_near_par_is_ambiguous(monkeypatch):
    _fake_oracle(monkeypatch, 0.9935)
    mode, price, why, amb, verified = discover.infer_oracle(None, "0x0", 18, 6, 0.9938, pt_discount=0.006)
    assert amb and mode == "market-tracking" and "Ambiguous" in why
    assert verified is None and "not checked" in why


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
    same = FakeF(
        {
            (S.RPC, "eth_getBlockByNumber"): {"hash": "0xaa"},
            (crosscheck.SECOND_RPCS[0], "eth_getBlockByNumber"): {"hash": "0xaa"},
        }
    )
    assert crosscheck.second_rpc(same, 1).ok is True
    fork = FakeF(
        {
            (S.RPC, "eth_getBlockByNumber"): {"hash": "0xaa"},
            (crosscheck.SECOND_RPCS[0], "eth_getBlockByNumber"): {"hash": "0xbb"},
        }
    )
    assert crosscheck.second_rpc(fork, 1).ok is False
    down = FakeF({(S.RPC, "eth_getBlockByNumber"): {"hash": "0xaa"}})
    assert crosscheck.second_rpc(down, 1).ok is None


def test_position_mismatch_is_reported(monkeypatch):
    # on-chain: 100 collateral units, 50 borrow shares worth 50 assets
    def word(x):
        return hex(x)[2:].rjust(64, "0")

    pos = "0x" + word(0) + word(50 * 10**6) + word(100 * 10**18)
    mk = "0x" + word(0) + word(0) + word(50) + word(50 * 10**6)
    monkeypatch.setattr(S, "rpc_batch", lambda f, calls, block: [pos, mk])
    assert crosscheck.morpho_position(None, "0x" + "00" * 32, "0x" + "11" * 20, 18, 0, 100.0, 50).ok is True
    assert crosscheck.morpho_position(None, "0x" + "00" * 32, "0x" + "11" * 20, 18, 0, 120.0, 50).ok is False


def test_unavailable_check_never_raises(monkeypatch):
    def boom(*a, **k):
        raise S.CacheMiss("x")

    monkeypatch.setattr(S, "rpc_batch", boom)
    assert crosscheck.morpho_position(None, "0x" + "00" * 32, "0x" + "11" * 20, 18, 6, 1.0, 1).ok is None


def test_oracle_verification_follows_etherscan(monkeypatch):
    """D68: the implementation behind a clone or a proxy decides; unknown stays unknown."""
    answers = {
        "0xclone": {"verified": True, "name": "Proxy", "proxy": True, "implementation": "0ximpl"},
        "0ximpl": {"verified": True, "name": "MetaOracleDeviationTimelock", "proxy": False, "implementation": None},
        "0xraw": {"verified": False, "name": None, "proxy": False, "implementation": None},
    }
    monkeypatch.setattr(S, "contract_source", lambda f, a: answers.get(a))
    assert discover.oracle_verified(None, "0xclone", None) == (
        True,
        "source verified on Etherscan (MetaOracleDeviationTimelock)",
    )
    assert discover.oracle_verified(None, "0xany", "0ximpl")[0] is True
    assert discover.oracle_verified(None, "0xraw", None) == (False, "source not verified on Etherscan")
    assert discover.oracle_verified(None, "0xunknown", None)[0] is None


def test_unverified_factor_applies_unless_verified():
    from riskdep import priors

    tech = priors.REGISTRY["oracle"]["techniques"][0]
    st = {"hacks": [{"technique": tech}] * 10, "cat_n": {"Lending": 100}, "years": 5}  # 2 %/yr
    p = {v: priors.oracle_prior("oracle:x", v, st).p_year for v in (True, False, None)}
    assert p[False] == pytest.approx(2 * p[True]) and p[None] == p[False]
    assert "verified on Etherscan" in priors.oracle_prior("oracle:x", True, st).basis


def test_secret_reaches_the_request_only(tmp_path, monkeypatch):
    """The Etherscan key goes into the request URL, never into the cache file or an error message."""
    sent = []

    class R:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"status": "1", "result": [{"SourceCode": "x", "ContractName": "C", "Proxy": "0"}]}

    monkeypatch.setattr(S.requests, "get", lambda url, timeout: sent.append(url) or R())
    monkeypatch.setattr(S, "api_key", lambda section, name="api_key": "SECRET123")
    f = S.Fetcher("live", tmp_path)
    assert S.contract_source(f, "0xAbC")["name"] == "C"
    assert "apikey=SECRET123" in sent[0]
    assert all("SECRET123" not in p.read_text() for p in tmp_path.glob("*.json"))
    monkeypatch.setattr(S.requests, "get", lambda url, timeout: (_ for _ in ()).throw(RuntimeError(f"boom {url}")))
    monkeypatch.setattr(time, "sleep", lambda s: None)
    with pytest.raises(S.SourceError) as e:
        f.get_json(S.ETHERSCAN + "?x=1", secret={"apikey": "SECRET123"})
    assert "SECRET123" not in str(e.value)


def test_no_key_and_no_cache_means_not_checked(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "api_key", lambda section, name="api_key": None)
    assert S.contract_source(S.Fetcher("live", tmp_path), "0xabc") is None
