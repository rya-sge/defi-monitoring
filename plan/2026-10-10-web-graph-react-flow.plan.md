# Web dependency graph on React Flow, plan

> **Status**: approved: the person, 2026-10-10, "go, suis tes recommandations pour les 3 questions". Implemented.
> **Delivers**: the SPA's dependency graph (`web/src/routes/GraphPage.tsx`) drawn with React Flow instead of Cytoscape. Each node is a shape by role, with its icon centred, its amount inside at the bottom and its name underneath. Edges carry arrows and labels. The selection panel, kind legend, search, full-flow focus and vault selector of the previous increment keep working. Proof: `pnpm lint && pnpm build`, then the visual checks of §9 in `pnpm dev`.
> **Hard rule**: frontend only. The `/api/graph` payload, `openapi.json` and the CLI's `graph.html` are left alone, and the agent never commits.
> **Read against**: `@xyflow/react` 12 (custom nodes, `MarkerType`, `useReactFlow`, `useStore`, `EdgeLabelRenderer`); `@dagrejs/dagre` 1 (layered layout); `web/src/mocks/graph.json` (134 edges, 100 nodes).

## 1. Why, and why not

Cytoscape draws on a canvas, so a node cannot hold arbitrary content. An icon is a background image, text sits outside the shape, every colour has to be resolved with `getComputedStyle`, and a theme switch needs a re-init. React Flow renders nodes as React components and edges as SVG. Icons, an amount inside the node, CSS shapes and `var(--…)` colours become ordinary JSX and CSS.

**Stories**
- **W1**: read at a glance what each node is (shape and icon) and how much sits in it (amount).
- **W2**: follow a flow by its arrows and select anything to see its risk.

**Non-goals**
- **CLI graph:** the CLI's `graph.html` stays on Cytoscape (see D66).
- **Edge routing:** no routing around nodes.
- **Layouts:** no saved layouts and no layout picker.
- **Minimap:** none.
- **Edit mode:** none. The graph stays read-only.

## 2. What changes on screen

| Element | Before (Cytoscape) | After (React Flow) |
|---|---|---|
| Asset | orange tag, logo as background | **circle**, 56 px, logo centred |
| Vault, address, lender (Actor) | blue rounded box | **rectangle**, 104 × 60 px, Lucide `Vault` / `User` |
| Pool (Blue market, Pendle pool) | green ellipse | **rectangle**, 104 × 60 px, Lucide `Landmark` / `Waves` |
| Oracle, Admin, External (hold no assets) | diamond / triangle / square | **hexagon**, 60 × 52 px, Lucide `Eye` / `KeyRound` / `Globe` |
| Amount | sub-label under the name | **inside the node, bottom line**, `mono`, 10 px |
| Name | under the node | under the node, outside the shape, max 160 px, two lines then ellipsis |
| Edge | line + small triangle | SVG path, **closed arrowhead** at the target, width on the existing log scale, label "amount · HF x" at mid-path |

**Node anatomy**
- **Body:** fill `--bg` and a 2 px border in the kind colour. The kind colour also tints the icon.
- **Selection:** the selected element gets a border in `--fg`.
- **Contrast:** an outline keeps the text legible on every kind colour, where a filled node would not. Orange `#E69F00` with white text fails contrast, for instance.
- **Hexagon:** an inline SVG `<polygon>`, so its border follows the shape. A `clip-path` would cut the border off.
- **Circle and rectangle:** CSS `border-radius: 50%` and `0`.

## 3. Modules, after

**`web/package.json`**
- adds `@xyflow/react` 12 and `@dagrejs/dagre` 1;
- removes `cytoscape`.
- **Lock file:** `pnpm-lock.yaml` is regenerated with pnpm. pnpm is not on this machine's PATH, so the agent runs `bunx pnpm@11 add …`. `bun.lock` is not the lock file CI reads.

**`web/src/lib/graph.ts`**
- `KIND_COLOR`: unchanged, still mirrored from `graph.py`.
- `KIND_SHAPE` (Cytoscape) is replaced by `nodeShape(node): 'circle' | 'rect' | 'hexagon'`.
- `nodeIcon(node)` returns a Lucide component, or a logo URL for an asset. The SVG data URIs go.
- `tokenIconUrl(address)`: unchanged.
- **New `nodeAmount(node, edges)`**, applying D63.
- **New `layoutGraph(nodes, edges)`**: dagre, `rankdir: 'LR'`, returns positions (D62).
- **New `reach(id, edges, backward?)`**: the downstream (or upstream) closure, by plain BFS. It replaces Cytoscape's `predecessors()` / `successors()`.
- `edgeWidth`, `edgeLabel`, `RISK_KEYS`, `normalizeReportGraph`: unchanged.

**`web/src/components/GraphElements.tsx`**, new: the custom node and edge types, both `risk`. The edge is a bezier with its counter-scaled label; the node draws:
- the shape;
- the icon centred, with an `<img onError>` that falls back to the Lucide `Coins` icon for an asset with no logo;
- the amount line;
- the name below;
- hidden `Handle`s (target on the left, source on the right).

**`web/src/components/GraphCanvas.tsx`**, rewritten as declarative React.
- **Setup:** `ReactFlowProvider` → `ReactFlow` with `nodeTypes={{ risk: GraphNode }}`.
- **Props:** `defaultEdgeOptions` gives every edge `markerEnd: ArrowClosed` and an `--edge` stroke. `nodesConnectable={false}`, `fitView`, `minZoom 0.1`. No `<Background>`, to keep one ground. Zoom in, zoom out and fit are shadcn `Button`s over `useReactFlow()` in a `<Panel>` (React Flow's `<Controls>` are not used).
- **Props:** `nodes`, `edges`, `visibleKinds`, `search`, `selection`, `onSelect`. The nonces go: the focus is derived from `selection`, Fit is the `<Controls>` button, and Re-layout remounts the canvas with `key`.
- **Fade:** a faded element gets `opacity: 0.08`. It applies to selection focus (via `reach`) and to search (hits and their neighbours stay lit).
- **Hidden kinds:** set `hidden: true` on those nodes. React Flow hides their edges itself.
- **Layout:** `layoutGraph` runs once per mount; a remount (new data, Re-layout) re-runs it and undoes the user's drags.
- **Drop:** `getComputedStyle`, `cssVar`, the zoom-event font hack and `crossorigin`.

**`web/src/routes/GraphPage.tsx`**
- **Unchanged:** the overlays (search and Re-layout, legend, provenance, floating panel) and the vault selector wiring.
- **Change:** `GraphSelection` is now built from the payload with `reach`, and passed back to the canvas as `selection`, no longer from Cytoscape collections. Its shape is unchanged.

**`web/src/index.css`**: imports `@xyflow/react/dist/base.css` (the structural CSS, not the themed one) inside the lazy graph chunk, plus a few `.react-flow__…` overrides: no radius, no shadow, `--line` borders on the controls.

**Docs, in the same change**
- **`CLAUDE.md` = `AGENTS.md`**, verbatim, in both:
  - the stack line becomes "React Flow for the graph";
  - the invariant "GraphCanvas is the one imperative component" is replaced (nothing is imperative any more);
  - the palette contract drops the `getComputedStyle` consumer;
  - "Routes are lazy because Recharts and Cytoscape…" becomes "…Recharts and React Flow…";
  - the node-palette invariant says the shapes now differ from the CLI's (D66).
- **`README.md`**:
  - line 99: "the `graph` output in React Flow";
  - line 138: the `data-theme` limit loses its Cytoscape reason. A toggle becomes possible, but none is added.
- **`index.css` header comment:** the three palette consumers become two.
- **`PROVIDERS.md`:**
  - the icon CDN row stays;
  - the note about `crossorigin` becomes "loaded by a plain `<img>`".

## 8. Decisions

| id | Kind | Decision | Status | Source | Slice |
|---|---|---|---|---|---|
| D62 | module | Layout with dagre, top to bottom (`rankdir TB`, `ranksep 50`, `nodesep 16`), each node at least `NAME_SLOT` wide and `NAME_SLOT.height` taller for its name (D65); handles on top (in) and bottom (out), and the name gets an opaque, rounded app-background ground because outgoing edges leave through it. React Flow ships no layout; elkjs is 6 times larger for no gain at 100 nodes. First built left to right, turned vertical at the person's request | agreed | the person, 2026-10-10 | S1 |
| D68 | contract | The graph shows one vault at a time, never all. The selector lists every vault of the unscoped graph (the last `graph.json`, or the fixture) plus the watched addresses, watched targets first, by name; it defaults to the first watch target and has no "All". Only the selection's node, everything downstream and everything upstream of it (admins, depositors) are drawn; sibling vaults on the same markets are removed, not faded (`scopeToTarget`). Scoping is done in the client on that one graph, never by a live `?vault=` read: every vault offered is in it, and `graph.build` reads Vault V2 only. A vault that is only a capital provider of a watched market shows the part of it the graph holds (its markets), not its whole book. All edges and arrowheads use `--edge` at full opacity, with a 2 px minimum rendered width; dependencies remain dashed | agreed | the person, 2026-10-10 | S1 |
| D63 | contract | Amount inside a node: a Vault with `total_assets` shows it. Another Actor shows the sum of its outgoing `supplies` amounts, or of its `borrows from` amounts prefixed "debt" if it supplies nothing. A Pool shows the sum of incoming `supplies` ("watched supply", since the payload has no market totals). An Asset shows the sum of edge amounts whose unit is its symbol. With no amount, the line falls back to LLTV (market) or expiry (Pendle pool). Oracle, Admin and External show none. Several units are never summed: one line per unit, at most two | agreed | `graph.json` keys | S1 |
| D64 | contract | Shapes by role (`nodeRole`), not by kind alone: circle 56 px = asset; near-square = holds or routes assets, sharp corners for a vault or a pool, rounded for an address or a lender (80 × 70); a vault is larger (96 × 80) on a 22 % tint of its kind colour instead of the neutral ground, and a pool flatter (80 × 52); two offset cards behind a node are reserved for a group of twins (D206); hexagon = holds nothing, 60 × 52 for an oracle, admin or external, 46 × 40 for a price feed (an Oracle node with `role_in_oracle`). Icons by role too: `Vault`/`User`, `Database` for both pool roles, `Eye` (oracle)/`Activity` (feed), `KeyRound`, `Globe`. Every node but a vault sits on the same neutral ground (12 % ink) with no border; the kind colour is in the icon alone. Selected: a 2 px border in the kind colour and a 6 px halo of it at 10 % opacity. Every amount — inside a node or on an edge — is the same `mono` 9 px in a faintly tinted box; a vault total is compacted like the rest ("458.11M RLUSD"), a debt is signed "−", an expiry is Pendle-style "exp 10DEC26". Edges with no amount are dashed | agreed | the person, 2026-10-10/11 | S1 |
| D65 | contract | Text under zoom: React Flow scales everything with the viewport. The node name and the edge labels are counter-scaled by `clamp(1/zoom, 1, 2.5)` (zoom read with `useStore`). Names never overlap: dagre lays each node out at least `NAME_SLOT` wide (128) and that much taller (40), and the counter-scaled name is narrowed to `128 / scale` and clamped to one line above scale 1.4, so it always stays inside its slot (full name on hover). Icons are 48 % of the node's short side (logos 58 %), centred above the amount. Edge labels are not de-overlapped | agreed | the person, 2026-10-10/11 | S1 |
| D66 | contract | The CLI's `graph.html` stays on Cytoscape with its current shapes. Colours stay shared between both; shapes now differ, and `CLAUDE.md` says so. Aligning `graph.py` (ellipse / round-rectangle / hexagon all exist in Cytoscape) is a 5-line follow-up if wanted | agreed | — | — |
| D67 | module | The graph page omits search, Re-layout and the provenance subtitle at the person’s request (2026-10-11). The icons are Lucide React components rendered directly. An asset logo is an `<img>` from DefiLlama's token-icon CDN by address, with the `Coins` icon on error. PT assets use Pendle’s token logo with the yield-source asset logo in a top-right badge, bordered by 1 px of the node ground; the existing graph edges identify the underlying. No API client and no cache layer: the browser caches the images | agreed | `PROVIDERS.md` | S1 |
| D206 | module | On the graph page, nodes of one kind and label stem with exactly the same edges (same relation to the same neighbours), six or more, are drawn as one stacked node "N × stem" (`groupTwins`, lib/graph.ts); clicking it expands the group and re-lays out. The group's edges carry no amount. Other pages draw every node | agreed | the person, 2026-10-11 | S1 |

## 9. The slices

**S1, React Flow canvas**
- `GraphNode` (shapes, icon, amount, name), `GraphCanvas` rewritten, and the `lib/graph.ts` helpers.
- Check: `pnpm lint && pnpm build`, and the Cytoscape chunk is gone from the build output.

**S2, docs**
- The edits listed in §3.
- Check: `diff CLAUDE.md AGENTS.md` is empty.

**Visual checks in `pnpm dev`, with the fixtures:**
1. An asset is a circle with its logo centred, and an unknown token shows `Coins`.
2. Vaults and markets are rectangles, and oracles and admins are hexagons.
3. Amounts sit inside the bottom of the node; RLUSD vault: "458,113,471 RLUSD".
4. Names are under the nodes and stay readable when zoomed out to fit.
5. Every edge has an arrowhead, and `borrows from` shows "1.10M USDC · HF 1.0945".
6. Clicking an asset lights its whole upstream and downstream flow and opens the panel; clicking the pane clears it.
7. The legend toggles hide kinds, search fades the rest, and Fit (in the controls) and Re-layout work.
8. Dark mode looks right without a reload.

## Interview log

- 2026-10-11, the person: "le bg color des nœuds … neutre, pour tous les nodes. pas de border, à part quand selected: border 2px et outline de genre 5-8px avec opacity 0.10" — D64 updated.

- 2026-10-11, the person: larger icons relative to the node; "le layout par défaut … que les textes n'overlap pas" — D65 extended.

- 2026-10-11, the person: dashed edges without amount; amounts in a slightly contrasted box, all in the same font; nodes with a faint ground and a much softer border; near-square, smaller rectangles; tell vault from user and oracle from price feed — D64 rewritten.

- 2026-10-10, the person: the selector shows vault names, lists every vault ("pour la liste des vaults, oui"), and "les edges qui ne contiennent pas d'infos de montant doivent être d'une autre couleur" — D68 extended.

- 2026-10-10, the person: "le graph doit être vertical"; "par défaut, le graph doit être uniquement sur un vault … sans les siblings (pas juste grisé, vraiment pas visible)" — D62 turned to top-to-bottom, D68 added.

- 2026-10-10, the person: "go, suis tes recommandations pour les 3 questions" — D63 (an asset shows the sum of the edge amounts in its unit), D65 (counter-scaled names and edge labels) and D66 (CLI shapes unchanged), as proposed.

- 2026-10-10, the person: replace Cytoscape with React Flow. Wanted: icons centred on the nodes; amounts inside the node, at the bottom; circles for assets, squares or rectangles for vaults and pools, hexagons for oracles, admins and anything else that holds no assets; edges with arrows; the node name under the node.
