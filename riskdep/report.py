"""HTML + JSON report. The HTML is one file; only Mermaid is loaded from a CDN."""

from __future__ import annotations

import html
import json
import math
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import clock
from .decide import Decision
from .discover import Position
from .priors import Prior
from .simulate import SimResult

KIND_STYLE = {
    "position": "fill:#1f6feb,color:#fff,stroke:#1f6feb",
    "lending": "fill:#8250df22,stroke:#8250df",
    "oracle": "fill:#d2992222,stroke:#d29922",
    "asset": "fill:#2da44e22,stroke:#2da44e",
    "amm": "fill:#0969da22,stroke:#0969da",
    "issuer": "fill:#cf222e22,stroke:#cf222e",
    "offchain": "fill:#cf222e0d,stroke:#cf222e,stroke-dasharray:4 3",
    "stable": "fill:#57606a22,stroke:#57606a",
    "chain": "fill:#57606a22,stroke:#57606a",
}


def _usd(x: float) -> str:
    return f"${x:,.0f}"


def mermaid(pos: Position, sim: SimResult) -> str:
    g = pos.graph
    ids = {n: f"n{i}" for i, n in enumerate(g.nodes)}
    contrib = {}
    for l in sim.layers:
        contrib[l.node] = contrib.get(l.node, 0) + l.contribution_usd
    lines = ["flowchart TB"]
    for n, a in g.nodes(data=True):
        label = a["label"].replace('"', "'")
        if n in contrib:
            label += f"<br/><b>EL {_usd(contrib[n])}</b>"
        lines.append(f'  {ids[n]}["{label}"]')
    for u, v, a in g.edges(data=True):
        lines.append(f'  {ids[u]} -->|"{a.get("rel", "")}"| {ids[v]}')
    for kind, style in KIND_STYLE.items():
        members = [ids[n] for n, a in g.nodes(data=True) if a["kind"] == kind]
        if members:
            lines.append(f"  classDef {kind} {style}")
            lines.append(f"  class {','.join(members)} {kind}")
    return "\n".join(lines)


def histogram_svg(losses: np.ndarray, equity: float, w: int = 640, h: int = 180) -> str:
    nz = losses[losses > 0]
    if nz.size == 0:
        return "<p class='muted'>No simulated path lost money.</p>"
    bins = 24
    top = max(equity, float(nz.max()))
    counts, edges = np.histogram(nz, bins=bins, range=(0, top))
    cmax = counts.max() or 1
    bw = (w - 40) / bins
    bars = []
    for i, c in enumerate(counts):
        bh = (h - 30) * c / cmax
        x = 30 + i * bw
        bars.append(f'<rect x="{x:.1f}" y="{h - 20 - bh:.1f}" width="{bw - 2:.1f}" height="{bh:.1f}" class="bar">'
                    f'<title>{_usd(edges[i])}–{_usd(edges[i + 1])}: {c} paths</title></rect>')
    ex = 30 + (w - 40) * min(1.0, equity / top)
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Loss distribution of the paths that lost money">'
            + "".join(bars)
            + f'<line x1="{ex:.1f}" x2="{ex:.1f}" y1="5" y2="{h - 20}" class="eq"/>'
            + f'<text x="{ex - 4:.1f}" y="14" text-anchor="end" class="lbl">equity {_usd(equity)}</text>'
            + f'<text x="30" y="{h - 4}" class="lbl">$0</text>'
            + f'<text x="{w - 10}" y="{h - 4}" text-anchor="end" class="lbl">{_usd(top)}</text></svg>')


CSS = """
:root{--bg:#ffffff;--fg:#1f2328;--muted:#59636e;--card:#f6f8fa;--line:#d1d9e0;--accent:#0969da;
--stay:#1a7f37;--reduce:#9a6700;--exit:#cf222e;--bar:#0969da99}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;
--card:#151b23;--line:#3d444d;--accent:#4493f8;--stay:#3fb950;--reduce:#d29922;--exit:#f85149;--bar:#4493f8aa}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--muted:#9198a1;--card:#151b23;--line:#3d444d;--accent:#4493f8;
--stay:#3fb950;--reduce:#d29922;--exit:#f85149;--bar:#4493f8aa}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.5rem;margin:0 0 4px}h2{font-size:1.15rem;margin:32px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}
.muted{color:var(--muted)}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px}
.verdict{border-left:6px solid var(--c);}.verdict .tag{font-weight:700;color:var(--c);font-size:1.4rem;letter-spacing:.04em}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-top:12px}
.kpi .v{font-size:1.25rem;font-weight:600}.kpi .k{font-size:.8rem;color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:.88rem}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{font-weight:600;color:var(--muted)}td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.scroll{overflow-x:auto}ul{padding-left:20px}li{margin:4px 0}
svg .bar{fill:var(--bar)}svg .eq{stroke:var(--exit);stroke-dasharray:4 3}svg .lbl{fill:var(--muted);font-size:11px}
.mermaid{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px;overflow-x:auto}
details{margin:6px 0}summary{cursor:pointer}code{font-size:.85em}
"""


def write(pos: Position, priors: list[Prior], sim: SimResult, dec: Decision, quote: dict,
          out_dir: Path, mode: str, oracle_alt: dict | None = None) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    data_as_of = clock.now_dt().strftime("%Y-%m-%d %H:%M UTC")
    color = {"STAY": "var(--stay)", "REDUCE": "var(--reduce)", "EXIT": "var(--exit)"}[dec.verdict]
    e = html.escape

    kpis = [
        ("Collateral", f"{_usd(pos.collateral_usd)}"), ("Debt", _usd(pos.debt_usd)),
        ("Equity", _usd(pos.equity_usd)),
        ("Health factor", f"{pos.health_factor:.3f}" if pos.health_factor else "n/a"),
        ("Liquidates at oracle drop", f"−{pos.liquidation_drop:.2%}" if pos.liquidation_drop is not None else "n/a"),
        (f"Expected loss ({sim.horizon_days:.0f}d)", _usd(sim.expected_loss_usd)),
        (f"Carry ({sim.horizon_days:.0f}d)", _usd(dec.carry_usd)),
        ("Exit cost (quoted)", _usd(dec.exit_cost_usd)),
        ("P(any loss)", f"{sim.p_any_loss:.2%}"), ("P(liquidation)", f"{sim.p_liquidation:.2%}"),
        ("CVaR 99%", _usd(sim.cvar99_usd)), ("Exit pays if risk ×", f"{dec.risk_multiple_to_exit:.1f}"),
    ]
    kpi_html = "".join(f'<div class="card kpi"><div class="k">{k}</div><div class="v">{v}</div></div>' for k, v in kpis)

    rows = []
    for l in sim.layers:
        rows.append(f"<tr><td>{e(l.layer)}</td><td class='n'>{l.p_horizon:.2%}</td><td class='n'>{l.mean_severity:.1%}</td>"
                    f"<td class='n'>{_usd(l.standalone_loss_usd)}</td><td class='n'>{l.liquidation_rate:.0%}</td>"
                    f"<td class='n'><b>{_usd(l.contribution_usd)}</b></td><td>{e(' → '.join(l.example_path))}</td></tr>")
    rows.append(f"<tr><td colspan='5' class='muted'>Interaction of simultaneous incidents</td>"
                f"<td class='n'>{_usd(sim.interaction_usd)}</td><td></td></tr>")
    rows.append(f"<tr><td colspan='5'><b>Total expected loss</b></td><td class='n'><b>{_usd(sim.expected_loss_usd)}</b></td><td></td></tr>")

    nodes = "".join(f"<tr><td>{e(a['kind'])}</td><td>{e(a['label'])}</td><td>{e(a['evidence'])}</td><td class='muted'>{e(a['source'])}</td></tr>"
                    for n, a in pos.graph.nodes(data=True))
    basis = "".join(f"<details><summary><b>{e(p.layer)}</b>: {p.p_year:.2%}/yr, severity Beta({p.a}, {p.b}) "
                    f"mean {p.mean_severity:.1%}</summary><p class='muted'>{e(p.basis)}</p></details>" for p in priors)
    red = ""
    if dec.reduction:
        r = dec.reduction
        red = (f"<h2>De-lever option</h2><div class='card'><p>Sell <b>{_usd(r.sell_usd)}</b> of PT and repay debt "
               f"(quote: {e(r.source)}).</p><div class='grid'>"
               f"<div class='kpi'><div class='k'>Health factor</div><div class='v'>{pos.health_factor:.3f} → {r.new_health_factor:.3f}</div></div>"
               f"<div class='kpi'><div class='k'>Liquidates at</div><div class='v'>−{pos.liquidation_drop:.1%} → −{r.new_liquidation_drop:.1%}</div></div>"
               f"<div class='kpi'><div class='k'>Expected loss</div><div class='v'>{_usd(dec.expected_loss_usd)} → {_usd(r.expected_loss_usd)}</div></div>"
               f"<div class='kpi'><div class='k'>CVaR 99%</div><div class='v'>{_usd(sim.cvar99_usd)} → {_usd(r.cvar99_usd)}</div></div>"
               f"<div class='kpi'><div class='k'>Carry</div><div class='v'>{_usd(dec.carry_usd)} → {_usd(r.carry_usd)}</div></div>"
               f"<div class='kpi'><div class='k'>One-off cost</div><div class='v'>{_usd(r.cost_usd)}</div></div></div></div>")
    notes = "".join(f"<li>{e(n)}</li>" for n in pos.notes)

    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Position Risk Report</title>
<style>{CSS}</style></head><body><main>
<h1>{e(pos.label)}</h1>
<p class="muted">Generated {now} · data as of <b>{data_as_of}</b> ({e(mode)}) · horizon {sim.horizon_days:.0f} days (maturity {e((pos.maturity or '')[:10])}) · {sim.n:,} Monte Carlo paths</p>
<div class="card verdict" style="--c:{color}"><div class="tag">{dec.verdict}</div><p>{e(dec.headline.split(': ', 1)[-1])}</p>
<ul>{''.join(f'<li>{e(r)}</li>' for r in dec.reasons)}</ul></div>
<div class="grid">{kpi_html}</div>
{red}
<h2>Dependency stack</h2>
<p class="muted">Discovered from live sources; each layer shows its share of the expected loss. Dashed: off-chain dependencies of the issuer (registry).</p>
<pre class="mermaid">{e(mermaid(pos, sim))}</pre>
<h2>How each failure reaches the position</h2>
<div class="scroll"><table><thead><tr><th>Layer / event</th><th>P(horizon)</th><th>Mean severity</th><th>Loss if it happens</th><th>Liquidates</th><th>Expected loss</th><th>Typical propagation</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<h2>Loss distribution</h2>
<p class="muted">Paths that lost money ({sim.p_any_loss:.2%} of {sim.n:,}). VaR95 {_usd(sim.var95_usd)}, CVaR95 {_usd(sim.cvar95_usd)}, VaR99 {_usd(sim.var99_usd)}, CVaR99 {_usd(sim.cvar99_usd)}.</p>
<div class="card">{histogram_svg(sim.loss_samples, pos.equity_usd)}</div>
<h2>Evidence per layer</h2>
<div class="scroll"><table><thead><tr><th>Kind</th><th>Layer</th><th>What was read</th><th>Source</th></tr></thead><tbody>{nodes}</tbody></table></div>
<h2>Assumptions and their basis</h2>{basis}
<p class="muted">Exit quote: {e(quote['source'])}, price impact {quote['price_impact']:.3%}, fee {_usd(quote['fee_usd'])}. Oracle mode: <b>{e(pos.oracle_mode)}</b>{' (ambiguous, see notes)' if pos.oracle_ambiguous else ''}.</p>
{f'<h2>Notes</h2><ul>{notes}</ul>' if notes else ''}
<h2>Limits</h2><ul>
<li>Incidents are independent across layers, except an issuer exploit, which always comes with a depeg.</li>
<li>Exploit frequencies are base rates from the DefiLlama hack record by TVL tier and category, not protocol-specific audits.</li>
<li>Severities and depeg behaviour come from <code>registry.json</code>, each with its basis above; change them there.</li>
<li>Carry assumes the PT's implied APY and the current borrow APY hold over the horizon.</li></ul>
</main>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"></script>
<script>try{{mermaid.initialize({{startOnLoad:true,securityLevel:'loose',
theme:(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'default')}});}}catch(e){{}}</script>
</body></html>"""
    hp = out_dir / "report.html"
    hp.write_text(doc)

    def clean(o):
        if isinstance(o, float) and (math.isinf(o) or math.isnan(o)):
            return None
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [clean(v) for v in o]
        return o

    pos_d = {k: v for k, v in pos.__dict__.items() if k != "graph"}
    pos_d.update(collateral_usd=pos.collateral_usd, equity_usd=pos.equity_usd, liquidation_drop=pos.liquidation_drop)
    sim_d = {k: v for k, v in asdict(sim).items() if k != "loss_samples"}
    payload = {"generated": now, "data_as_of": data_as_of, "mode": mode, "position": pos_d,
               "graph": {"nodes": [{"id": n, **a} for n, a in pos.graph.nodes(data=True)],
                         "edges": [{"from": u, "to": v, **a} for u, v, a in pos.graph.edges(data=True)]},
               "priors": [asdict(p) for p in priors], "simulation": sim_d, "decision": asdict(dec), "exit_quote": quote,
               "oracle_sensitivity": oracle_alt}
    jp = out_dir / "report.json"
    jp.write_text(json.dumps(clean(payload), indent=2, default=str))
    return hp, jp
