"""US4/US5 on a recorded real range of Sentora RLUSD Main: no network."""

import json
from pathlib import Path

from riskdep import sources as S, vault as V
from riskdep.abi import TIMELOCKED, selector
from riskdep.cli import DEMO_VAULT, REPLAY_DIR, main
from riskdep.poller import Poller

RDIR = REPLAY_DIR / DEMO_VAULT
META = json.loads((RDIR / "start.json").read_text())
DOCS = Path(__file__).resolve().parents[2] / "lib" / "docs.morpho.org-developers-docs" / "contracts"


def test_discovery_matches_real_assets():
    f = S.Fetcher("offline", RDIR)
    block = META["head"] - 2 - 64
    view = V.discover_vault(f, DEMO_VAULT, block)
    st = V.read_state(f, view, block, META["depositor"])
    assert len(view.market_ids) == 10 and all(a.kind == "market" for a in view.adapters)
    held = sum(m.vault_assets for m in st.markets.values())
    real = sum(st.real_assets.values())
    assert abs(held - real) / real < 1e-3
    # the 3 cap ids are right: the vault's allocation for each market id matches what it supplies
    a = view.adapters[0]
    for mp in a.markets.values():
        alloc = st.caps[V.cap_ids(a.address, mp)["market"]][0]
        assert abs(alloc - st.markets[mp.id].vault_assets) <= max(10 ** 15, 0.001 * alloc)


def test_poller_decodes_every_log_and_resumes(tmp_path):
    f = S.Fetcher("offline", RDIR)
    view = V.discover_vault(f, DEMO_VAULT, META["head"] - 2 - 64)
    cur = tmp_path / "c"
    p = Poller(f, view.kinds, view.market_ids, cur, 2, 500)
    p.cursor = META["cursor"]
    p.head = lambda: META["head"]
    b1 = p.next_batch()
    assert b1.unknown == 0 and b1.events
    p.save(b1.to_block)
    p2 = Poller(f, view.kinds, view.market_ids, cur, 2, 500)       # a restart
    p2.head = lambda: META["head"]
    assert p2.cursor == b1.to_block
    b2 = p2.next_batch()
    assert b2.from_block == b1.to_block + 1 and b2.unknown == 0
    p2.save(b2.to_block)
    assert p2.next_batch() is None


def test_replay_runs_offline(tmp_path, capsys):
    assert main(["watch", "--replay", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "kBTC" in out and "done:" in out
    lines = (tmp_path / f"watch-{DEMO_VAULT}.jsonl").read_text().splitlines()
    assert lines and all(json.loads(x)["level"] in ("info", "warn", "critical") for x in lines)


def test_selectors_match_the_morpho_docs():
    import re
    if not DOCS.exists():
        return
    docs = {}
    for name in ("morpho-vaults-v2.md", "morpho-market-v1-adapter-v2.md"):
        docs.update(dict(re.findall(r"\| `(\w+)` \| `0x([0-9a-f]{8})` \|", (DOCS / name).read_text())))
    for sig in TIMELOCKED:
        assert docs[sig.split("(")[0]] == selector(sig), sig
