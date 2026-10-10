"""D61: a live batch with no event reads only what moves without one; the fetcher routes the main RPC
(RISKDEP_RPC_URL) without changing its cache keys, and retries resend the request body unchanged."""

import pytest
import requests

from riskdep import borrower as B
from riskdep import sources as S
from riskdep import vault as V
from riskdep.poller import Batch
from riskdep.watch import W, light_read

E18 = 10**18
VAULT = "0x" + "bb" * 20
ASSET = "0x" + "01" * 20
ADAPTER = "0x" + "aa" * 20
DEP = "0x" + "dd" * 20
M1, M2 = "0x" + "11" * 32, "0x" + "22" * 32
ORACLE1, ORACLE2 = "0x" + "03" * 20, "0x" + "06" * 20


def view():
    mp1 = V.MarketParams(M1, ASSET, "0x" + "02" * 20, ORACLE1, "0x" + "04" * 20, 0.86, "kBTC")
    mp2 = V.MarketParams(M2, ASSET, "0x" + "05" * 20, ORACLE2, "0x" + "04" * 20, 0.915, "USDe")
    return V.VaultView(
        VAULT, ASSET, "RLUSD", 18, "Test vault", [V.AdapterView(ADAPTER, "market", {M1: mp1, M2: mp2})], None
    )


def full_state(depositor=DEP):
    return V.VaultState(
        block=100,
        total_assets=1000 * E18,
        total_supply=990 * E18,
        idle=100 * E18,
        real_assets={ADAPTER: 900 * E18},
        markets={
            M1: V.MarketState(M1, 600 * E18 * 10**6, 1000 * E18, 1000 * E18 * 10**6, 900 * E18, 600 * E18, 10**36),
            M2: V.MarketState(M2, 300 * E18 * 10**6, 1000 * E18, 1000 * E18 * 10**6, 500 * E18, 300 * E18, 10**36),
        },
        caps={"0x" + "cc" * 32: (600 * E18, 700 * E18, E18)},
        performance_fee=10**17,
        management_fee=0,
        depositor=depositor,
        depositor_shares=200 * E18,
        stored_total_assets=1000 * E18,
        liquidity_market=M2,
        penalties={ADAPTER: 10**14},
        can_send_shares=True,
        can_receive_assets=True,
    )


def word(n: int) -> str:
    return "0x" + format(n, "064x")


# --- when a batch may skip the full read


def batch(to_block=110, events=(), unknown=0, gap=None):
    return Batch(to_block, to_block, to_block + 2, list(events), unknown, gap)


def test_a_quiet_live_batch_reads_light():
    assert light_read(batch(), live=True, refresh=False, last_full=100)


@pytest.mark.parametrize(
    "case",
    [
        dict(b=batch(events=["an event"])),
        dict(b=batch(unknown=1)),
        dict(b=batch(gap=(101, 105))),
        dict(refresh=True),
        dict(live=False),
        dict(last_full=110 - W["full_state_every_blocks"]),
    ],
)
def test_anything_else_reads_in_full(case):
    args = {"b": batch(), "live": True, "refresh": False, "last_full": 100, **case}
    assert not light_read(args["b"], args["live"], args["refresh"], args["last_full"])


# --- the vault's light read


def test_light_state_replaces_only_the_moving_values():
    before = full_state()
    after = V.light_state(before, 111, 1001 * E18, 101 * E18, {ADAPTER: 901 * E18}, {M1: 9 * 10**35}, True, False)
    assert (after.block, after.total_assets, after.idle) == (111, 1001 * E18, 101 * E18)
    assert after.real_assets == {ADAPTER: 901 * E18}
    assert after.markets[M1].oracle_price == 9 * 10**35
    assert after.markets[M2].oracle_price == 10**36  # not read: kept
    assert (after.can_send_shares, after.can_receive_assets) == (True, False)
    for kept in ("total_supply", "caps", "depositor_shares", "stored_total_assets", "penalties", "performance_fee"):
        assert getattr(after, kept) == getattr(before, kept)
    assert after.markets[M1].total_borrow_assets == before.markets[M1].total_borrow_assets
    assert before.markets[M1].oracle_price == 10**36  # `before` untouched


def test_read_light_sends_one_batch_of_the_moving_values(monkeypatch):
    sent = []

    def fake_batch(f, calls, block):
        sent.append((calls, block))
        values = [1001 * E18, 101 * E18, 1, 0, 901 * E18, 9 * 10**35]
        return [word(v) for v in values] + [None]  # the second oracle reverts

    monkeypatch.setattr(S, "rpc_batch", fake_batch)
    after = V.read_light(None, view(), 111, full_state())
    calls, block = sent[0]
    assert len(sent) == 1 and block == 111
    assert [to for to, _ in calls] == [VAULT, ASSET, VAULT, VAULT, ADAPTER, ORACLE1, ORACLE2]
    assert len(calls) == 7  # a full read of the same vault sends 3 per market, 3 per cap id and 13 more
    assert (after.total_assets, after.idle, after.real_assets[ADAPTER]) == (1001 * E18, 101 * E18, 901 * E18)
    assert (after.can_send_shares, after.can_receive_assets) == (True, False)
    assert after.markets[M1].oracle_price == 9 * 10**35
    assert after.markets[M2].oracle_price is None  # a revert reads as None, as in a full read
    assert after.depositor_shares == 200 * E18


def test_read_light_without_a_depositor_skips_the_gates(monkeypatch):
    sent = []
    monkeypatch.setattr(S, "rpc_batch", lambda f, calls, block: sent.append(calls) or [word(1)] * len(calls))
    after = V.read_light(None, view(), 111, full_state(depositor=None))
    assert len(sent[0]) == 5
    assert after.can_send_shares is True  # copied from the full read


# --- borrows


def test_borrows_are_revalued_at_the_new_prices(monkeypatch):
    m = B.BorrowMarket(M1, ASSET, "0x" + "02" * 20, ORACLE1, "0x" + "04" * 20, 915 * 10**15, "USDC", "PT-x", 6, 18)
    st = B.BorrowState(M1, 100 * E18, 90 * 10**6, 90 * 10**6, 10**24, 1000 * 10**6, 900 * 10**6, 10**9)
    monkeypatch.setattr(S, "rpc_batch", lambda f, calls, block: [word(9 * 10**23)])
    prices = B.read_prices(None, {M1: m}, 111)
    after = B.with_prices({M1: st}, prices)
    assert prices == {M1: 9 * 10**23}
    assert after[M1].hf(m.lltv) == pytest.approx(st.hf(m.lltv) * 0.9)
    assert (after[M1].debt, after[M1].rate_per_second) == (st.debt, st.rate_per_second)


# --- the fetcher


class Resp:
    def __init__(self, status, payload=None):
        self.status_code, self.payload = status, payload

    def json(self):
        if self.payload is None:
            raise ValueError("not JSON")
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


BODY = {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}
ROUTED = "http://127.0.0.1:4000/main/evm/1?key=SECRET"


def test_a_routed_request_is_cached_under_the_public_url(monkeypatch, tmp_path):
    posts = []
    monkeypatch.setattr(S, "ROUTES", {S.RPC: ROUTED})
    monkeypatch.setattr(
        S.requests, "post", lambda url, json, timeout: posts.append(url) or Resp(200, {"result": "0x1"})
    )
    f = S.Fetcher("live", tmp_path)
    assert f.post_json(S.RPC, BODY) == {"result": "0x1"}
    assert posts == [ROUTED]
    cached = f._key("POST", S.RPC, BODY)
    assert cached.exists() and "SECRET" not in cached.read_text()


def test_a_retry_after_a_refusal_resends_the_same_body(monkeypatch, tmp_path):
    bodies = []
    answers = iter([Resp(429), Resp(200, {"result": "0x2"})])
    monkeypatch.setattr(S.requests, "post", lambda url, json, timeout: bodies.append(json) or next(answers))
    monkeypatch.setattr(S.time, "sleep", lambda s: None)
    assert S.Fetcher("direct", tmp_path).post_json(S.RPC, BODY) == {"result": "0x2"}
    assert bodies == [BODY, BODY]


def test_a_failure_names_the_public_url_not_the_routed_one(monkeypatch, tmp_path):
    def down(url, json, timeout):
        raise requests.ConnectionError(f"cannot reach {url}")

    monkeypatch.setattr(S, "ROUTES", {S.RPC: ROUTED})
    monkeypatch.setattr(S.requests, "post", down)
    monkeypatch.setattr(S.time, "sleep", lambda s: None)
    with pytest.raises(S.SourceError) as e:
        S.Fetcher("direct", tmp_path).post_json(S.RPC, BODY)
    assert "SECRET" not in str(e.value) and S.RPC in str(e.value)
    assert "RISKDEP_RPC_URL" in str(e.value)  # a colleague whose local proxy is down is told where to look


def test_a_routed_failure_never_prints_the_key_from_a_requests_message(monkeypatch, tmp_path):
    """requests reports host, port and path apart, so the routed URL never appears whole and cannot be replaced."""

    def down(url, json, timeout):
        raise requests.ConnectionError(
            "HTTPSConnectionPool(host='eth.example.com', port=443): Max retries exceeded with url: /v2/SECRET"
        )

    monkeypatch.setattr(S, "ROUTES", {S.RPC: "https://eth.example.com/v2/SECRET"})
    monkeypatch.setattr(S.requests, "post", down)
    monkeypatch.setattr(S.time, "sleep", lambda s: None)
    with pytest.raises(S.SourceError) as e:
        S.Fetcher("direct", tmp_path).post_json(S.RPC, BODY)
    assert "SECRET" not in str(e.value) and "eth.example.com" not in str(e.value) and "ConnectionError" in str(e.value)


THROTTLED = [{"jsonrpc": "2.0", "id": 0, "error": {"code": -32005, "message": "Rate limit exceeded"}}]


def test_a_throttled_batch_is_resent_and_its_errors_never_recorded(monkeypatch, tmp_path):
    """publicnode answers a burst with 429 and a -32005 error per item (probe 2026-10-10): resent, not passed on as
    reverted calls, and a recording keeps only the good answer (plan 2026-10-10-sibling-markets, S3)."""
    answers = iter([Resp(429, THROTTLED), Resp(429, THROTTLED), Resp(200, [{"id": 0, "result": "0x2"}])])
    waits = []
    monkeypatch.setattr(S.requests, "post", lambda url, json, timeout: next(answers))
    monkeypatch.setattr(S.time, "sleep", waits.append)
    f = S.Fetcher("refresh", tmp_path)
    assert f.post_json(S.RPC, [BODY]) == [{"id": 0, "result": "0x2"}]
    assert waits == [2.0, 4.0] and "-32005" not in f._key("POST", S.RPC, [BODY]).read_text()


def test_throttling_that_does_not_stop_fails_the_request(monkeypatch, tmp_path):
    monkeypatch.setattr(S.requests, "post", lambda url, json, timeout: Resp(429, THROTTLED))
    monkeypatch.setattr(S.time, "sleep", lambda s: None)
    with pytest.raises(S.SourceError, match="429"):
        S.Fetcher("direct", tmp_path).post_json(S.RPC, [BODY])


def test_rate_limit_errors_inside_a_200_reply_are_resent_too(monkeypatch, tmp_path):
    """A local eRPC whose budget is spent answers HTTP 200 with a rate-limit error per item: same treatment as a 429."""
    erpc = [{"jsonrpc": "2.0", "id": 0, "error": {"code": -32005, "message": "rate-limit exceeded"}}]
    answers = iter([Resp(200, erpc), Resp(200, [{"id": 0, "result": "0x3"}])])
    monkeypatch.setattr(S.requests, "post", lambda url, json, timeout: next(answers))
    monkeypatch.setattr(S.time, "sleep", lambda s: None)
    f = S.Fetcher("refresh", tmp_path)
    assert f.post_json(S.RPC, [BODY]) == [{"id": 0, "result": "0x3"}]
    assert "rate-limit" not in f._key("POST", S.RPC, [BODY]).read_text()


def test_other_errors_with_code_32005_are_passed_on():
    """Some nodes use -32005 for 'too many log results': resending would not help, so it is not throttling."""
    assert not S._throttled([{"id": 0, "error": {"code": -32005, "message": "query returned more than 10000 results"}}])
    assert S._throttled({"error": {"code": 429, "message": "slow down"}})
