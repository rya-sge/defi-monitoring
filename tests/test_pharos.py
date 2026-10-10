"""Pharos, keyless (plan 2026-10-11-pharos): the pure parts, the recorded snapshot, its use in incidents and graphs."""

import json
from pathlib import Path

import pytest

from riskdep import cli
from riskdep import pharos as PH
from riskdep import sources as S
from riskdep.graph import annotate_pharos, build_all

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "examples" / "rockawayx-ethereum.json"
RECORDED = ROOT / "fixtures" / "replay" / "pharos"
IUSD = "0x48f9e38f3070ad8945dfeae3fa70987722e3d89c"

TINY = {
    "asOfSec": 1791672421,
    "methodologyVersion": "10.16",
    "nodes": [
        {"id": "base-a", "grade": "A", "score": 80, "roles": []},
        {"id": "res-b", "grade": "F", "score": 30, "roles": []},
        {
            "id": "basket-c",
            "grade": "D",
            "score": 45,
            "roles": [
                {"up": "base-a", "w": 0.5, "role": "basket-exposure"},
                {"up": "res-b", "w": 0.2, "role": "basket-exposure"},
            ],
        },
        {"id": "wrap-d", "grade": "NR", "score": None, "roles": [{"up": "basket-c", "w": 1, "role": "serial-claim"}]},
        {"id": "dup-x", "grade": "C", "score": 50, "roles": []},
        {"id": "dup-y", "grade": "C", "score": 50, "roles": []},
    ],
    "groups": [
        {"kind": "mint-control", "key": "k1", "members": ["basket-c", "wrap-d"]},
        {"kind": "chain", "key": "ethereum", "members": ["basket-c", "wrap-d"]},  # kind not kept
        {"kind": "upgrade-control", "key": "wide", "members": [f"m{i}" for i in range(40)] + ["basket-c"]},  # too wide
    ],
}


def test_parse_resolve_and_grades():
    s = PH.parse(TINY)
    assert s.as_of == "2026-10-10" and s.grade("basket-c") == "D 45" and s.grade("wrap-d") == "NR"
    assert s.grade("nope") is None
    assert PH.resolve(s, "basket-c") == "basket-c" and PH.resolve(s, "0xabc", "WRAP") == "wrap-d"
    assert PH.resolve(s, "dup") is None  # two ids start with "dup": ambiguous, needs the registry
    assert PH.resolve(s, IUSD) == "iusd-infinifi"  # the registry's address map wins


def test_exposure_multiplies_along_paths():
    s = PH.parse(TINY)
    assert PH.exposure(s, "wrap-d", "res-b") == (pytest.approx(0.2), ["wrap-d", "basket-c", "res-b"])
    assert PH.exposure(s, "wrap-d", "base-a")[0] == pytest.approx(0.5)
    assert PH.exposure(s, "base-a", "res-b") == (0.0, [])
    assert PH.exposure(s, "wrap-d", "res-b", depth=1)[0] == 0.0


def test_common_mode_keeps_narrow_groups_of_listed_kinds():
    s = PH.parse(TINY)
    assert PH.common_mode(s, "basket-c", {"wrap-d": "D"}) == ["D (mint control)"]
    assert PH.common_mode(s, "basket-c", {"m1": "M1"}) == []  # only in the 41-member group, dropped


def test_recorded_snapshot_offline():
    s = PH.load(S.Fetcher("offline", RECORDED))
    assert s is not None and s.grade("fxsave-f-x-protocol") == "F 36"
    share, path = PH.exposure(s, "iusd-infinifi", "fxsave-f-x-protocol")
    assert share == pytest.approx(0.164) and path == ["iusd-infinifi", "fxsave-f-x-protocol"]
    assert PH.load(S.Fetcher("offline", RECORDED / "absent")) is None  # optional: no recording, no error


def test_book_reaches_iusd_through_pharos_backing(tmp_path):
    """fxSAVE backs 16.4 % of infiniFi's iUSD: an fxSAVE cut also reaches the siUSD market of RockawayX USDC Yield."""
    assert cli.main(["analyze", "--book", str(BOOK), "--shock", "token=fxSAVE:0.30", "--out", str(tmp_path)]) == 0
    r = json.loads((tmp_path / "book-incident.json").read_text())
    hit = {ln["name"] for ln in r["lines"] if ln["hit_markets"]}
    assert hit == {"RockawayX f(x) Protocol Ecosystem USDC", "RockawayX USDC Yield"}
    assert r["shocks"] == ["fxSAVE −30%"] and any("fxSAVE F 36" in n for n in r["notes"])
    y = "0xe0181090c22579b6a217f1522cbf8c9f1f0c1965"
    assert cli.main(["analyze", "--vault", y, "--shock", "token=fxSAVE:0.30", "--out", str(tmp_path)]) == 0
    (h,) = json.loads((tmp_path / f"vault-incident-{y}.json").read_text())["hits"]
    assert h["pharos_exposure"] == pytest.approx(0.164) and h["drop"] == pytest.approx(0.3 * 0.164)
    assert "Pharos" in h["via"] and not h["seen"] and h["grade"] == "iUSD D 49"


def test_common_mode_note_for_tori(tmp_path):
    assert cli.main(["analyze", "--book", str(BOOK), "--shock", "token=trUSD:0.30", "--out", str(tmp_path)]) == 0
    notes = json.loads((tmp_path / "book-incident.json").read_text())["notes"]
    assert any("trUSD with strUSD (mint control, upgrade control)" in n for n in notes)


def test_graph_annotated_offline():
    rdir = ROOT / "fixtures" / "replay" / "graph-0xe0181090c22579b6a217f1522cbf8c9f1f0c1965"
    meta = json.loads((rdir / "meta.json").read_text())
    g = build_all(S.Fetcher("offline", rdir), meta["block"], meta["users"], meta["vaults"], meta["siblings"])
    assert annotate_pharos(g, PH.load(S.Fetcher("offline", RECORDED))) >= 5
    label = {k: n["label"] for k, n in g.nodes.items()}
    backed = {
        (label[e["source"]], label[e["target"]]): e["details"]["share"]
        for e in g.edges
        if e["rel"] == "backed by (Pharos)"
    }
    assert backed[("strUSD", "trUSD")] == 1.0 and backed[("iUSD", "fxSAVE")] == pytest.approx(0.164)
    assert g.nodes[IUSD]["details"]["pharos_grade"] == "D 49"
