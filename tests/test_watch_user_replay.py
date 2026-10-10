"""watch --user on recorded real ranges: a borrower with 6 borrows, and a Vault V2 depositor. No network."""

import json

from riskdep import borrower as B
from riskdep import positions
from riskdep import sources as S
from riskdep.cli import DEMO_BORROWER, REPLAY_DIR, main

DEPOSITOR = "0xb03d620e49b6a21ea9d02142831c3f61c2fcbabc"


def test_borrower_positions_match_the_api():
    d = REPLAY_DIR / f"user-{DEMO_BORROWER}"
    meta = json.loads((d / "start.json").read_text())
    f = S.Fetcher("offline", d)
    up = positions.discover_user(f, DEMO_BORROWER)
    assert len(up.borrows) == 6
    block = meta["head"] - 2 - 64
    markets = B.discover_markets(f, up.borrows, block)
    states = B.read_borrows(f, markets, DEMO_BORROWER, block)
    for mid, st in states.items():
        api = up.api_state[mid]
        assert st.collateral == api["collateral"]
        assert abs(st.debt / api["borrowAssets"] - 1) < 1e-3  # interest since the API's last update
        hf = st.hf(markets[mid].lltv)
        assert 1 < hf < 2 and st.apy is not None


def test_borrower_replay_runs_offline(tmp_path, capsys):
    assert main(["watch", "--user", DEMO_BORROWER, "--replay", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "found 6 borrow(s)" in out and "lowest HF" in out and "undecoded" not in out
    lines = (tmp_path / f"watch-user-{DEMO_BORROWER}.jsonl").read_text().splitlines()
    assert any(json.loads(x)["event"] == "HealthFactor" for x in lines)


def test_depositor_replay_uses_the_vault_rules(tmp_path, capsys):
    assert main(["watch", "--user", DEPOSITOR, "--replay", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "1 Vault V2 deposit(s)" in out and "Sentora RLUSD Main" in out and "undecoded" not in out


def test_hf_levels_are_validated(capsys):
    import pytest

    for bad in ("1.1,abc", "0.9", "1.3,1.2,1.1,1.05"):
        with pytest.raises(SystemExit):
            main(["watch", "--user", DEPOSITOR, "--hf", bad])
