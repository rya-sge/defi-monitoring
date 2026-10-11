"""The README's five-minute path, pinned to the code: every output fragment the README quotes must appear in what
its commands print, offline. If a change moves a number the README shows a judge, this fails until the README follows."""

import re
from pathlib import Path

from riskdep import cli

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text()
FX = "0x2cA22cb25558fa2018ecb1CE4eD8AF92Ee7ea423"


def _quoted_fragments() -> list[str]:
    """The backticked output lines of the "What to read in the output" table, split at each ellipsis, plus the
    breakeven and outside-view lines the README shows in code."""
    section = README[README.index("What to read in the output") : README.index("**Is the number defensible")]
    rows = re.findall(r"^\| `([^`]+)` \|", section, re.M)
    shown = re.findall(r"^((?:if the incident is not certain|outside view):.*)$", README, re.M)
    return [p.strip(" .") for r in rows + shown for p in r.split("…") if len(p.strip(" .")) > 8]


def test_the_readme_quotes_what_the_commands_print(tmp_path, capsys):
    runs = [
        ["analyze", "--vault", FX, "--shock", "token=fxSAVE:0.30"],
        [
            "analyze",
            "--book",
            "examples/brief-ten-pockets.json",
            "--shock",
            "token=mGLOeuro:0.30",
            "--exit-cost",
            "0.11",
            "--conditional",
        ],
        ["analyze", "--book", "examples/brief-mixed-book.json", "--shock", "token=sUSDe:0.08", "--exit-cost", "0.11"],
    ]
    out = ""
    for args in runs:
        assert cli.main([*args, "--out", str(tmp_path)]) == 0
        out += capsys.readouterr().out
    flat = " ".join(out.split())
    fragments = _quoted_fragments()
    assert len(fragments) >= 12
    missing = [f for f in fragments if " ".join(f.split()) not in flat]
    assert not missing, f"the README quotes output the commands no longer print: {missing}"
