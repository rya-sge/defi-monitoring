"""The HTTP API (riskdep/api.py), offline: artifacts from out/, analysis from the snapshot.

The artifact routes need `out/report.json` and `out/graph.json`, which are git-ignored, so each
test writes what it needs into a tmp_path and points `api.OUT` at it. `POST /api/analyze` reads
the committed snapshot and writes nothing.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from riskdep import cli, clock, pipeline, report
from riskdep import graph as GR
from riskdep import sources as S
from riskdep.api import app, artifacts


@pytest.fixture
def client(tmp_path, monkeypatch):
    # artifacts.OUT is read at call time, so pointing it at tmp_path is enough
    monkeypatch.setattr(artifacts, "OUT", tmp_path)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def report_file(tmp_path):
    f = S.Fetcher("offline")
    clock.set_as_of(json.loads((S.SNAPSHOT_DIR / "as_of.json").read_text())["as_of"])
    res = pipeline.analyze(f, paths=2000)
    payload = report.to_dict(
        res.position, res.priors, res.simulation, res.decision, res.quote, "offline", res.oracle_alt
    )
    (tmp_path / "report.json").write_text(json.dumps(payload, default=str))
    return payload


@pytest.fixture
def graph_file(tmp_path):
    g = GR.Graph()
    g.node("0xaa", "Actor", "Address 0xaa…", address="0xaa")
    g.node("0xbb", "Pool", "Market", lltv=0.915)
    g.edge("0xaa", "0xbb", "borrows from", 1000.0, "USDC")
    doc = GR.to_dict(g, "test graph", GR.subtitle_for(26_000_000))
    (tmp_path / "graph.json").write_text(json.dumps(doc, default=str))
    return doc


def test_health_reports_the_snapshot_date(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and body["mode"] == "offline"
    assert body["data_as_of"].endswith("UTC")


def test_missing_artifacts_say_which_command_to_run(client):
    for path in ("/api/report", "/api/graph"):
        r = client.get(path)
        assert r.status_code == 404
        assert "python -m riskdep" in r.json()["detail"]


def test_graph_serves_the_written_artifact(client, graph_file):
    body = client.get("/api/graph").json()
    assert body["title"] == "test graph"
    assert [n["kind"] for n in body["nodes"]] == ["Actor", "Pool"]
    # the whole graph comes in one payload: the client traverses it, no per-node endpoint
    assert body["edges"] == [
        {"source": "0xaa", "target": "0xbb", "rel": "borrows from", "amount": 1000.0, "unit": "USDC", "details": {}}
    ]


def test_report_keeps_the_shape_the_ui_consumes(client, report_file):
    body = client.get("/api/report").json()
    assert body["decision"]["verdict"] in {"STAY", "REDUCE", "EXIT"}
    assert body["simulation"]["layers"] and body["priors"]
    assert body["position"]["collateral_usd"] > 0
    # networkx serialisation, not the /api/graph shape: the alias must survive the response model
    assert set(body["graph"]["edges"][0]) == {"from", "to", "rel"}


def test_analyze_runs_on_the_snapshot_without_touching_out(client, tmp_path):
    body = client.post("/api/analyze", json={"paths": 2000, "horizon": 30}).json()
    assert body["decision"]["verdict"] in {"STAY", "REDUCE", "EXIT"}
    assert body["simulation"]["n"] == 2000
    assert not list(tmp_path.iterdir())


def test_analyze_serves_an_incident_from_its_shocks(client):
    body = client.post("/api/analyze", json={"paths": 2000, "shocks": ["issuer_depeg=0.08"]}).json()
    assert body["incident"]["verdict"] in {"STAY", "REDUCE", "EXIT"}
    assert client.post("/api/analyze", json={"shocks": ["nonsense=0.1"]}).status_code == 422


def test_analyze_rejects_an_out_of_range_horizon(client):
    assert client.post("/api/analyze", json={"horizon": 0}).status_code == 422


def test_analyze_needs_an_amount_with_a_pendle_market(client):
    r = client.post("/api/analyze", json={"pendle_market": "0x47ad2cd1dd15739a7a035b9d3b7828d916fef77e"})
    assert r.status_code == 422 and "pt_amount" in r.json()["detail"]


def _write_alerts(out_dir, name, rows):
    (out_dir / f"watch-{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


ROWS = [
    {"level": "info", "block": 100, "tx": None, "event": "Exposure", "title": "a", "detail": "", "data": {}},
    {"level": "warn", "block": 101, "tx": "0x" + "11" * 32, "event": "Caps", "title": "b", "detail": "", "data": {}},
    {
        "level": "critical",
        "block": 102,
        "tx": None,
        "event": "BadDebt",
        "title": "c",
        "detail": "",
        "depositor_impact": -12.5,
        "data": {},
    },
]


def test_targets_lists_each_watch_file(client, tmp_path):
    _write_alerts(tmp_path, "0xvault", ROWS)
    _write_alerts(tmp_path, "user-0xabc", ROWS[:1])
    body = client.get("/api/targets").json()
    assert {t["target"]: (t["alerts"], t["last_block"]) for t in body} == {
        "0xvault": (3, 102),
        "user-0xabc": (1, 100),
    }


def test_alerts_cursor_only_returns_what_is_new(client, tmp_path):
    _write_alerts(tmp_path, "0xvault", ROWS)
    first = client.get("/api/alerts").json()
    assert first["cursor"] == 102 and len(first["alerts"]) == 3
    assert first["counts"] == {"info": 1, "warn": 1, "critical": 1}

    again = client.get("/api/alerts", params={"since": first["cursor"]}).json()
    assert again["alerts"] == [] and again["cursor"] == 102


def test_alerts_level_is_a_floor_not_an_equality(client, tmp_path):
    _write_alerts(tmp_path, "0xvault", ROWS)
    body = client.get("/api/alerts", params={"level": "warn"}).json()
    assert [a["level"] for a in body["alerts"]] == ["warn", "critical"]
    assert body["alerts"][-1]["depositor_impact"] == -12.5


def test_alerts_on_an_unknown_target_points_at_the_listing(client, tmp_path):
    _write_alerts(tmp_path, "0xvault", ROWS)
    r = client.get("/api/alerts", params={"target": "nope"})
    assert r.status_code == 404 and "/api/targets" in r.json()["detail"]


def test_alerts_with_no_watch_output_says_so(client):
    r = client.get("/api/alerts")
    assert r.status_code == 404 and "riskdep watch" in r.json()["detail"]


def test_openapi_is_served_and_names_every_route(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {
        "/api/health",
        "/api/graph",
        "/api/report",
        "/api/analyze",
        "/api/books",
        "/api/incident",
        "/api/targets",
        "/api/alerts",
        "/api/vault/{address}",
        "/api/market/{market_id}",
        "/api/shock",
        "/api/shock/graphs",
        "/api/shock/targets",
        "/api/shock/sweep",
        "/api/backtests",
        "/api/backtest/{episode}",
    }


# --- a known incident on a vault or a book (plan 2026-10-11-incident-api), offline from the recordings

FX = "0x2ca22cb25558fa2018ecb1ce4ed8af92ee7ea423"


def test_books_lists_the_examples(client):
    books = {b["name"]: b for b in client.get("/api/books").json()}
    assert len(books["rockawayx-ethereum"]["vaults"]) == 7


def test_incident_on_an_example_book(client):
    r = client.post("/api/incident", json={"example": "rockawayx-ethereum", "shocks": ["token=PST:0.30"]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert 5.0e6 < body["book"]["loss_usd"] < 5.4e6 and "Act first on" in body["book"]["headline"]
    assert len(body["vaults"]) == 7 and body["book"]["p_star"] is not None


def test_incident_on_one_vault_matches_the_cli(client, tmp_path):
    r = client.post("/api/incident", json={"vaults": [FX], "shocks": ["token=fxSAVE:0.30"], "horizon": 30})
    assert r.status_code == 200, r.text
    (v,) = r.json()["vaults"]
    assert cli.main(["analyze", "--vault", FX, "--shock", "token=fxSAVE:0.30", "--out", str(tmp_path)]) == 0
    same = json.loads((tmp_path / f"vault-incident-{FX}.json").read_text())
    assert v["vault_loss"] == pytest.approx(same["vault_loss"]) and v["p_star"] == pytest.approx(same["p_star"])
    assert any(h["source"] == "engine" for h in v["hits"]) and v["outside"]


@pytest.mark.parametrize(
    "body, status",
    [
        ({"example": "rockawayx-ethereum", "shocks": []}, 422),  # no shock
        ({"example": "rockawayx-ethereum", "vaults": [FX], "shocks": ["token=PST:0.3"]}, 422),  # two books
        ({"vaults": [FX], "shocks": ["token=PST"]}, 422),  # malformed shock
        ({"example": "nope", "shocks": ["token=PST:0.3"]}, 404),
        ({"vaults": ["0x" + "1" * 40], "shocks": ["token=PST:0.3"]}, 404),  # not recorded
    ],
)
def test_incident_errors(client, body, status):
    assert client.post("/api/incident", json=body).status_code == status


def test_incident_takes_the_briefs_exit_cost(client):
    body = {"example": "brief-ten-pockets", "shocks": ["token=mGLOeuro:0.30"], "exit_cost": 0.11}
    r = client.post("/api/incident", json=body)
    assert r.status_code == 200, r.text
    hit = next(ln for ln in r.json()["book"]["lines"] if ln["hit_markets"])
    assert hit["exit_cost_usd"] == pytest.approx(110_000) and hit["reason"].startswith("leaving costs")
    assert client.post("/api/incident", json={**body, "exit_cost": 1.5}).status_code == 422


def test_incident_with_the_conditional_distribution(client):
    body = {"example": "brief-ten-pockets", "shocks": ["token=mGLOeuro:0.30"], "exit_cost": 0.11, "conditional": True}
    r = client.post("/api/incident", json=body)
    assert r.status_code == 200, r.text
    d = r.json()["book"]["conditional"]
    assert d["paths"] == 10_000 and d["stay_p95"] > d["leave_mean"]


def test_incident_on_the_mixed_book(client):
    body = {"example": "brief-mixed-book", "shocks": ["token=sUSDe:0.08"], "exit_cost": 0.11}
    r = client.post("/api/incident", json=body)
    assert r.status_code == 200, r.text
    assert any(ln["verdict"] == "EXIT" and ln["name"].startswith("PT-sUSDe") for ln in r.json()["book"]["lines"])


# --- a failure propagated through a recorded graph, and the backtests, offline

RX = "0xe0181090c22579b6a217f1522cbf8c9f1f0c1965"  # RockawayX USDC Yield, the documented shock


def test_shock_graphs_list_the_recordings(client):
    graphs = {g["target"]: g for g in client.get("/api/shock/graphs").json()}
    assert graphs[RX]["vaults"] == [RX] and graphs[RX]["block"] == 26164907


def test_shock_targets_put_the_held_markets_first(client):
    rows = client.get("/api/shock/targets", params={"vault": RX}).json()
    assert rows[0]["held"] >= rows[-1]["held"]
    assert any(r["node"] == "0x77ee147391eac11c92817e771860ff4aad265d89" for r in rows)


def test_shock_matches_the_committed_trace(client):
    r = client.post("/api/shock", json={"vault": [RX], "shocks": ["Ojo PT:reads-low:10%"]})
    assert r.status_code == 200, r.text
    body = r.json()
    same = json.loads(
        (Path(__file__).resolve().parent.parent / "docs" / "model" / "shock-trace-example.json").read_text()
    )
    assert body["shocks"] == same["shocks"] and body["paths"] == same["paths"]
    assert body["nodes"].keys() == same["nodes"].keys()
    # a replay moves the clock to its recording; the API's clock stays on the snapshot
    assert client.get("/api/health").json()["data_as_of"].startswith("2026-10-10")


def test_shock_sweep_ranks_by_vault_loss(client):
    r = client.post("/api/shock/sweep", json={"vault": [RX], "mode": "reads-low", "size": "10%", "top": 5})
    assert r.status_code == 200, r.text
    losses = [x["vault_loss"] for x in r.json()["ranking"]]
    assert len(losses) == 5 and losses == sorted(losses, reverse=True) and losses[0] > 0


@pytest.mark.parametrize(
    "path, body, status",
    [
        ("/api/shock", {"vault": [RX], "shocks": []}, 422),  # no shock
        ("/api/shock", {"shocks": ["Ojo PT:frozen"]}, 422),  # no vault or user
        ("/api/shock", {"vault": [RX], "shocks": ["no such node:frozen"]}, 422),
        ("/api/shock", {"vault": [RX], "shocks": ["Ojo PT:sideways"]}, 422),  # unknown mode
        ("/api/shock", {"vault": ["0x" + "1" * 40], "shocks": ["x:frozen"]}, 404),  # not recorded
        ("/api/shock/sweep", {"vault": [RX], "mode": "reads-low"}, 422),  # reads-low needs a size
    ],
)
def test_shock_errors(client, path, body, status):
    assert client.post(path, json=body).status_code == status


def test_backtests_list_the_registry_episodes(client):
    eps = {b["episode"]: b for b in client.get("/api/backtests").json()}
    assert eps["pt-reusd-2026-08-25"]["recorded"] and eps["pt-reusd-2026-08-25"]["markets"] == 2


def test_backtest_replays_an_episode(client):
    r = client.get("/api/backtest/pt-reusd-2026-08-25")
    assert r.status_code == 200, r.text
    body = r.json()
    usdc = body["markets"][0]
    assert usdc["predicted_positions"] == usdc["realised_positions"] == 13
    assert body["pool"] and body["lines"][0].startswith("BACKTEST")
    assert client.get("/api/backtest/nope").status_code == 404
