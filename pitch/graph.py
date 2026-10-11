"""Lays out a recorded riskdep graph in layers and prints it as one inline SVG, drawn like GraphCanvas.

Usage: python -m riskdep graph --vault 0xE0181090c22579B6A217f1522cbf8c9f1F0C1965 --replay --out /tmp/rock
       python3 pitch/graph.py /tmp/rock.json   # paste the output where slides.md has the graph
"""

import collections
import json
import sys

g = json.load(open(sys.argv[1]))
N = {n["id"]: n for n in g["nodes"]}
C = {
    "Actor": "#0072B2",
    "Pool": "#009E73",
    "Asset": "#E69F00",
    "Oracle": "#CC79A7",
    "Admin": "#D55E00",
    "External": "#999999",
}
adj = collections.defaultdict(dict)  # dicts, not sets: insertion order keeps the layout reproducible
fwd = collections.defaultdict(dict)
for e in g["edges"]:
    adj[e["source"]][e["target"]] = adj[e["target"]][e["source"]] = fwd[e["source"]][e["target"]] = None
V = next(n["id"] for n in g["nodes"] if n["kind"] == "Actor")

# Depth: what the vault depends on to the right; who acts on it (admins, Zama) to the left; the rest next to a neighbour.
depth, q = {V: 0}, [V]
for s in q:
    for t in fwd[s]:
        if t not in depth:
            depth[t] = depth[s] + 1
            q.append(t)
while len(depth) < len(N):
    for k in [k for k in N if k not in depth]:
        placed = [depth[t] for t in adj[k] if t in depth]
        if placed:
            d = max(placed) if V not in adj[k] else 0
            depth[k] = d + 1 if d > 0 else min(placed) - 1
layers = collections.defaultdict(list)
for k, d in depth.items():
    layers[d].append(k)
order = sorted(layers)

# Barycentre sweeps, as dagre does, to keep crossings down.
pos = {k: i for d in order for i, k in enumerate(layers[d])}
for _ in range(8):
    for d in order:
        layers[d].sort(key=lambda k: sum(pos[t] for t in adj[k]) / len(adj[k]) if adj[k] else pos[k])
        n = len(layers[d])
        for i, k in enumerate(layers[d]):
            pos[k] = (i + 0.5) / n * 30

W, H = 1100, 520
x = {d: 40 + (W - 80) * i / (len(order) - 1) for i, d in enumerate(order)}
xy = {}
for d in order:
    n = len(layers[d])
    for i, k in enumerate(layers[d]):
        xy[k] = (x[d], H / 2 + (i - (n - 1) / 2) * min(64, (H - 40) / max(n - 1, 1)))

SHOCK = {k for k, n in N.items() if "strUSD" in n["label"] and "etrUSD" not in n["label"] and n["kind"] != "Oracle"} | {
    V
}
LABEL = {V} | {k for k in fwd[V] if N[k]["kind"] == "Pool"} | {k for k in SHOCK if N[k]["kind"] == "Asset"}


def shape(k, cls):
    n, (cx, cy) = N[k], xy[k]
    if k == V:
        return f'<rect class="{cls}" x="{cx - 34:.0f}" y="{cy - 16:.0f}" width="68" height="32" rx="5"/>'
    if n["kind"] == "Asset":
        return f'<circle class="{cls}" cx="{cx:.0f}" cy="{cy:.0f}" r="9"/>'
    if n["kind"] == "Pool":
        return f'<rect class="{cls}" x="{cx - 10:.0f}" y="{cy - 9:.0f}" width="20" height="18" rx="3"/>'
    w, h = (18, 16) if n["kind"] == "Oracle" and not n["label"].startswith("Oracle") else (22, 19)
    pts = [(-w / 2, 0), (-w / 4, -h / 2), (w / 4, -h / 2), (w / 2, 0), (w / 4, h / 2), (-w / 4, h / 2)]
    return f'<polygon class="{cls}" points="{" ".join(f"{cx + a:.0f},{cy + b:.0f}" for a, b in pts)}"/>'


out = [f'<svg class="graph fill" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">']
for e in g["edges"]:
    (x1, y1), (x2, y2) = xy[e["source"]], xy[e["target"]]
    if x1 > x2:
        (x1, y1), (x2, y2) = (x2, y2), (x1, y1)
    m = (x1 + x2) / 2
    cls = "edge shock-path" if {e["source"], e["target"]} <= SHOCK else "edge"
    out.append(f'<path class="{cls}" d="M{x1:.0f} {y1:.0f} C{m:.0f} {y1:.0f} {m:.0f} {y2:.0f} {x2:.0f} {y2:.0f}"/>')
for k, n in N.items():
    cx, cy = xy[k]
    out.append(shape(k, "node"))
    if k in SHOCK:
        out.append(shape(k, "shock-ring"))
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{5 if k == V else 3}" fill="{C[n["kind"]]}"/>')
for k in (k for k in N if k in LABEL):
    cx, cy = xy[k]
    label = N[k]["label"].removeprefix("Vault ").removeprefix("Blue ")
    out.append(f'<text class="label" x="{cx:.0f}" y="{cy + (30 if k == V else 22):.0f}">{label}</text>')
print("".join(out) + "</svg>")
