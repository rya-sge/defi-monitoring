"""The conditional Monte Carlo (plan 2026-10-11-conditional): given the incident, the loss of staying drawn against
the certain cost of leaving."""

import json
from pathlib import Path

import numpy as np
import pytest

from riskdep import cli
from riskdep import conditional as CD

TEN = Path(__file__).resolve().parent.parent / "examples" / "brief-ten-pockets.json"
M = [0.0, 0.5, 1.0, 2.0]


def test_draws_recover_or_hold_around_the_given_fall():
    m = CD.draw_multiples(np.random.default_rng(1), 200_000)
    assert (m < 1).mean() == pytest.approx(0.3 + 0.7 * 0.5, abs=0.01)  # recoveries, and half of the lognormal
    assert np.median(m[m > 1]) > 1


def test_simulate_against_a_linear_curve():
    c = CD.Curve("v", M, [0, 50, 100, 200], [0, 0, 0, 0], [1, 1, 1, 1], exit_cost=50.0, no_liquidator_prob=0.0)
    d = CD.simulate([c], fall=0.3, n=50_000, seed=3)
    assert d.leave_mean == pytest.approx(50) and d.stay_p99 > d.stay_p50
    # staying costs more than 50 when m > 0.5: 97.6 % of the held-or-deepened paths, half of the recovered ones
    assert d.p_stay_worse == pytest.approx(0.7 * 0.976 + 0.3 * 0.5, abs=0.02)
    locked = CD.Curve("v", M, [0, 50, 100, 200], [0, 0, 0, 0], [0, 0, 0, 0], 50.0, no_liquidator_prob=1.0)
    assert (
        CD.simulate([locked], 0.3, n=1000).stay_mean == 0
        and CD.simulate([locked], 0.3, n=1000).no_liquidator_share == 1
    )


def test_worst_route():
    assert CD.worst_route(["deep", "thin"]) == "thin" and CD.worst_route([None, "deep"]) == "unknown"


def test_the_briefs_ten_pockets_drawn(tmp_path, capsys):
    """Leaving the hit pocket costs 110,000 for sure; staying costs less on average but more in its tail."""
    args = ["analyze", "--book", str(TEN), "--shock", "token=mGLOeuro:0.30", "--exit-cost", "0.11", "--conditional"]
    assert cli.main([*args, "--out", str(tmp_path)]) == 0
    d = json.loads((tmp_path / "book-incident.json").read_text())["conditional"]
    assert d["leave_mean"] == pytest.approx(110_000, rel=0.01)
    assert d["stay_mean"] < d["leave_mean"] < d["stay_p95"] and 0.05 < d["p_stay_worse"] < 0.4
    assert "given the incident, drawn" in capsys.readouterr().out


def test_conditional_needs_a_markdown(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(
            ["analyze", "--book", str(TEN), "--shock", "borrower=all:0.5", "--conditional", "--out", str(tmp_path)]
        )


def test_the_briefs_pt_loop_drawn(tmp_path, capsys):
    """D203: the borrow pocket of the mixed book gets its own distribution and joins the book's."""
    mixed = TEN.with_name("brief-mixed-book.json")
    args = ["analyze", "--book", str(mixed), "--shock", "token=sUSDe:0.10", "--exit-cost", "0.11", "--conditional"]
    assert cli.main([*args, "--out", str(tmp_path)]) == 0
    d = json.loads((tmp_path / "book-incident.json").read_text())["conditional"]
    assert d["leave_mean"] == pytest.approx(110_000, rel=0.01)
    assert d["leave_mean"] < d["stay_p50"] <= d["stay_p95"] <= 1_000_000 and d["p_stay_worse"] > 0.9
    assert "PT-sUSDe loop on Morpho (the brief's example), given the incident" in capsys.readouterr().out
