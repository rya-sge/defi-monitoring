import dagre from '@dagrejs/dagre';
import type { XYPosition } from '@xyflow/react';
import { Activity, Coins, Database, Eye, Globe, KeyRound, User, Vault } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { detailValue } from './format';
import type { GraphEdge, GraphNode, GraphNodeKind, GraphResponse, ReportGraph } from '../api/types';

/**
 * Okabe-Ito, copied from `riskdep/graph.py` so the web graph and the CLI's
 * standalone HTML colour the same kind the same way.
 */
export const KIND_COLOR: Record<GraphNodeKind, string> = {
  Actor: '#0072B2',
  Pool: '#009E73',
  Asset: '#E69F00',
  Oracle: '#CC79A7',
  Admin: '#D55E00',
  External: '#999999',
};

export type NodeShape = 'circle' | 'rect' | 'rounded' | 'hexagon';

/**
 * What a node is, finer than its kind: a vault and an address are both Actors, a market
 * oracle and the feed it reads are both Oracles, and the drawing has to tell them apart.
 */
export type NodeRole =
  'vault' | 'user' | 'market' | 'pendle' | 'asset' | 'oracle' | 'feed' | 'admin' | 'external';

export function nodeRole(node: GraphNode): NodeRole {
  const d = node.details;
  switch (node.kind) {
    case 'Actor':
      return detailValue(d.actor_type).startsWith('Vault') ? 'vault' : 'user';
    case 'Pool':
      return 'market_id' in d ? 'market' : 'pendle';
    case 'Asset':
      return 'asset';
    case 'Oracle':
      return 'role_in_oracle' in d ? 'feed' : 'oracle';
    case 'Admin':
      return 'admin';
    default:
      return 'external';
  }
}

/**
 * Circle: a token. Square: holds or routes assets, rounded for an address or a lender,
 * sharp for a vault or a pool; a vault is larger and tinted, a pool
 * flatter. Hexagon: holds nothing, smaller for a feed than for the
 * oracle that reads it (D64).
 */
const ROLE_DRAWING: Record<
  NodeRole,
  { shape: NodeShape; width: number; height: number; icon: LucideIcon }
> = {
  vault: { shape: 'rect', width: 96, height: 80, icon: Vault },
  user: { shape: 'rounded', width: 80, height: 70, icon: User },
  market: { shape: 'rect', width: 80, height: 52, icon: Database },
  pendle: { shape: 'rect', width: 80, height: 52, icon: Database },
  asset: { shape: 'circle', width: 56, height: 56, icon: Coins },
  oracle: { shape: 'hexagon', width: 60, height: 52, icon: Eye },
  feed: { shape: 'hexagon', width: 46, height: 40, icon: Activity },
  admin: { shape: 'hexagon', width: 60, height: 52, icon: KeyRound },
  external: { shape: 'hexagon', width: 60, height: 52, icon: Globe },
};

/** Shape, box (in flow units; the name sits outside it, underneath) and Lucide glyph. */
export function nodeDrawing(node: GraphNode) {
  return ROLE_DRAWING[nodeRole(node)];
}

/**
 * The slot each node's name gets in the layout, in flow units: the node is laid out as at
 * least this wide, and this much taller, so no two names can overlap (the name is sized to fit
 * its slot at every zoom — see `RiskNode`).
 */
export const NAME_SLOT = { width: 128, height: 40 };

/**
 * Oracle providers by the word naming them, the most specific first ("Ojo PT Feed Pendle
 * Chainlink-compatible" is Ojo's), with their DefiLlama protocol slug; Ojo has no logo there.
 */
const ORACLE_SLUG: [string, string | null][] = [
  ['ojo', null],
  ['redstone', 'redstone'],
  ['chronicle', 'chronicle'],
  ['pyth', 'pyth-network'],
  ['api3', 'api3'],
  ['pendle', 'pendle'],
  ['morpho', 'morpho'],
  ['chainlink', 'chainlink'],
];

/** The oracle provider's slug from a node's label or shape; a bare "X / Y" is Chainlink's naming. */
function oracleSlug(node: GraphNode): string | null {
  const text = `${node.label} ${detailValue(node.details.shape)}`.toLowerCase();
  const named = ORACLE_SLUG.find(([word]) => text.includes(word));
  if (named) return named[1];
  return /^\S+ \/ \S+$/.test(node.label) ? 'chainlink' : null;
}

/** DefiLlama's keyless icon CDN: an asset by address, an oracle by provider (D67). */
export function logoUrl(node: GraphNode): string | null {
  if (node.kind === 'Oracle') {
    const slug = oracleSlug(node);
    return slug ? `https://icons.llamao.fi/icons/protocols/${slug}?w=48&h=48` : null;
  }
  const address = node.label.toUpperCase().startsWith('PT-')
    ? '0x808507121b80c02388fad14726482e061b8da827'
    : node.details.address;
  return node.kind === 'Asset' && typeof address === 'string'
    ? `https://token-icons.llamao.fi/icons/tokens/1/${address.toLowerCase()}?h=64&w=64`
    : null;
}

/** Edge amounts summed per unit, one formatted line per unit, at most two. */
function sumByUnit(edges: GraphEdge[], prefix = '', withUnit = true): string[] {
  const totals = new Map<string, number>();
  for (const { amount, unit } of edges) {
    if (amount != null) totals.set(unit ?? '', (totals.get(unit ?? '') ?? 0) + amount);
  }
  return [...totals]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2)
    .map(([unit, total]) => prefix + edgeLabel(total, withUnit ? unit : null))
    .filter((line) => line !== prefix);
}

/** "2026-12-10" → "10DEC26", the way Pendle names a maturity; short enough for the node. */
function ptDate(iso: string): string {
  const [y, m, d] = iso.split('-');
  const month = new Date(Date.UTC(2000, Number(m) - 1)).toLocaleString('en', {
    month: 'short',
    timeZone: 'UTC',
  });
  return `${d}${month.toUpperCase()}${y.slice(2)}`;
}

/** The amount line(s) inside a node (D63). */
export function nodeAmount(node: GraphNode, edges: GraphEdge[]): string[] {
  const d = node.details;
  const out = edges.filter((e) => e.source === node.id);
  const into = edges.filter((e) => e.target === node.id);
  switch (node.kind) {
    case 'Actor': {
      // "458,113,471 RLUSD" → "458.11M RLUSD", the format of every other amount.
      const total = /^([\d,.]+) (\S+)$/.exec(detailValue(d.total_assets));
      if (total) return [edgeLabel(Number(total[1].replace(/,/g, '')), total[2])];
      const supplied = sumByUnit(out.filter((e) => e.rel === 'supplies'));
      return supplied.length
        ? supplied
        : sumByUnit(
            out.filter((e) => e.rel === 'borrows from'),
            // A debt is a negative holding; a word would not fit the node.
            '−',
          );
    }
    case 'Pool': {
      const supplied = sumByUnit(into.filter((e) => e.rel === 'supplies'));
      if (supplied.length) return supplied;
      if (d.lltv) return [`LLTV ${detailValue(d.lltv)}`];
      return d.expiry ? [`exp ${ptDate(detailValue(d.expiry))}`] : [];
    }
    case 'Asset':
      // The unit is the asset's own symbol: printing it again would not fit the circle.
      return sumByUnit(
        edges.filter((e) => e.unit === node.label),
        '',
        false,
      );
    default:
      return [];
  }
}

/** The box a node is laid out in: its drawing, widened and lengthened by its name's slot. */
function layoutBox(node: GraphNode) {
  const { width, height } = nodeDrawing(node);
  return { width: Math.max(width, NAME_SLOT.width), height: height + NAME_SLOT.height };
}

/** A box's centre → the node's top-left corner (the name sits under the drawing). */
function topLeft(node: GraphNode, x: number, y: number): XYPosition {
  return { x: x - nodeDrawing(node).width / 2, y: y - layoutBox(node).height / 2 };
}

export type LayoutName =
  'dagre-tb' | 'dagre-lr' | 'lanes' | 'radial' | 'elk-layered' | 'elk-stress';

/** How edges attach under a layout: top to bottom, left to right, or centre to centre. */
export type LayoutFlow = 'TB' | 'LR' | 'free';

export const LAYOUTS: { value: LayoutName; label: string; flow: LayoutFlow }[] = [
  { value: 'dagre-tb', label: 'Layered, top down', flow: 'TB' },
  { value: 'dagre-lr', label: 'Layered, left to right', flow: 'LR' },
  { value: 'lanes', label: 'Lanes by role', flow: 'LR' },
  { value: 'radial', label: 'Radial from the vault', flow: 'free' },
  { value: 'elk-layered', label: 'ELK layered', flow: 'TB' },
  { value: 'elk-stress', label: 'ELK stress', flow: 'free' },
];

export const layoutFlow = (name: LayoutName): LayoutFlow =>
  LAYOUTS.find((l) => l.value === name)?.flow ?? 'TB';

/** dagre, top to bottom unless `rankdir` says otherwise; returns each node's top-left corner (D62). */
export function layoutGraph(
  nodes: GraphNode[],
  edges: GraphEdge[],
  rankdir: 'TB' | 'LR' = 'TB',
): Map<string, XYPosition> {
  const g = new dagre.graphlib.Graph();
  g.setGraph(
    rankdir === 'TB' ? { rankdir, ranksep: 50, nodesep: 16 } : { rankdir, ranksep: 90, nodesep: 8 },
  );
  g.setDefaultEdgeLabel(() => ({}));
  for (const node of nodes) g.setNode(node.id, layoutBox(node));
  for (const edge of edges) g.setEdge(edge.source, edge.target);
  dagre.layout(g);
  return new Map(
    nodes.map((node) => {
      const { x, y } = g.node(node.id);
      return [node.id, topLeft(node, x, y)];
    }),
  );
}

/** The column of each role in the lanes layout: who holds, what is held, what prices it, who stands behind. */
const LANE: Record<NodeRole, number> = {
  admin: 0,
  user: 1,
  vault: 1,
  market: 2,
  pendle: 2,
  asset: 3,
  oracle: 4,
  feed: 5,
  external: 6,
};

/**
 * Fixed columns by role, each ordered by the mean row of its neighbours (barycenter), swept
 * right then left a few times to undo crossings. Stable: the same graph always lands the same.
 */
export function layoutLanes(nodes: GraphNode[], edges: GraphEdge[]): Map<string, XYPosition> {
  const lane = new Map(nodes.map((n) => [n.id, LANE[nodeRole(n)]]));
  const columns: GraphNode[][] = Array.from({ length: 7 }, () => []);
  for (const n of nodes) columns[lane.get(n.id)!].push(n);
  const nonEmpty = columns.filter((c) => c.length);
  const neighbours = new Map<string, string[]>(nodes.map((n) => [n.id, []]));
  for (const e of edges) {
    neighbours.get(e.source)?.push(e.target);
    neighbours.get(e.target)?.push(e.source);
  }
  const row = new Map<string, number>();
  const rank = () =>
    nonEmpty.forEach((c) => c.forEach((n, i) => row.set(n.id, i / Math.max(1, c.length - 1))));
  rank();
  const sweep = (column: GraphNode[], side: number) => {
    const bary = (n: GraphNode) => {
      const near = neighbours
        .get(n.id)!
        .filter((id) => Math.sign(lane.get(id)! - lane.get(n.id)!) === side);
      const pool = near.length ? near : neighbours.get(n.id)!;
      return pool.length
        ? pool.reduce((s, id) => s + row.get(id)!, 0) / pool.length
        : row.get(n.id)!;
    };
    const keyed = new Map(column.map((n) => [n.id, bary(n)]));
    column.sort((a, b) => keyed.get(a.id)! - keyed.get(b.id)! || a.label.localeCompare(b.label));
    column.forEach((n, i) => row.set(n.id, i / Math.max(1, column.length - 1)));
  };
  for (let i = 0; i < 6; i++) {
    nonEmpty.slice(1).forEach((c) => sweep(c, -1));
    nonEmpty
      .slice(0, -1)
      .reverse()
      .forEach((c) => sweep(c, 1));
  }
  const GAP_X = 110;
  const GAP_Y = 10;
  const heights = nonEmpty.map((c) => c.reduce((s, n) => s + layoutBox(n).height + GAP_Y, 0));
  const tallest = Math.max(...heights);
  const out = new Map<string, XYPosition>();
  let x = 0;
  nonEmpty.forEach((column, i) => {
    const width = Math.max(...column.map((n) => layoutBox(n).width));
    let y = (tallest - heights[i]) / 2;
    for (const n of column) {
      const h = layoutBox(n).height;
      out.set(n.id, topLeft(n, x + width / 2, y + h / 2));
      y += h + GAP_Y;
    }
    x += width + GAP_X;
  });
  return out;
}

/**
 * Rings by distance from `root` (edges either way); each ring keeps its nodes next to their
 * parent's angle, spaced so no two names overlap. Unreachable nodes go on an outer ring.
 */
export function layoutRadial(
  nodes: GraphNode[],
  edges: GraphEdge[],
  root?: string,
): Map<string, XYPosition> {
  const ids = new Set(nodes.map((n) => n.id));
  const start =
    root && ids.has(root) ? root : (nodes.find((n) => nodeRole(n) === 'vault') ?? nodes[0])?.id;
  const depth = new Map<string, number>();
  const parent = new Map<string, string>();
  if (start) {
    depth.set(start, 0);
    const queue = [start];
    for (let id = queue.shift(); id !== undefined; id = queue.shift())
      for (const next of adjacent(id, edges))
        if (ids.has(next) && !depth.has(next)) {
          depth.set(next, depth.get(id)! + 1);
          parent.set(next, id);
          queue.push(next);
        }
  }
  const outer = Math.max(0, ...depth.values()) + 1;
  const rings: GraphNode[][] = Array.from({ length: outer + 1 }, () => []);
  for (const n of nodes) rings[depth.get(n.id) ?? outer].push(n);
  const angle = new Map<string, number>();
  const out = new Map<string, XYPosition>();
  let radius = 0;
  rings.forEach((ring, d) => {
    if (!ring.length) return;
    if (d === 0) {
      ring.forEach((n) => {
        angle.set(n.id, 0);
        out.set(n.id, topLeft(n, 0, 0));
      });
      return;
    }
    const want = (n: GraphNode) => angle.get(parent.get(n.id) ?? '') ?? 0;
    ring.sort((a, b) => want(a) - want(b) || a.label.localeCompare(b.label));
    const circumference = ring.reduce((s, n) => s + layoutBox(n).width + 12, 0);
    radius = Math.max(radius + 230, circumference / (2 * Math.PI));
    // Centre the ring's arc on its parents' mean angle, so a subtree faces where it hangs.
    const offset = ring.reduce((s, n) => s + want(n), 0) / ring.length - Math.PI;
    let at = 0;
    for (const n of ring) {
      const share = (layoutBox(n).width + 12) / circumference;
      const a = offset + 2 * Math.PI * (at + share / 2);
      at += share;
      angle.set(n.id, a);
      out.set(n.id, topLeft(n, radius * Math.cos(a), radius * Math.sin(a)));
    }
  });
  return out;
}

/** ELK (elkjs, loaded on first use): `layered` with orthogonal routing, or `stress`. */
export async function layoutElk(
  nodes: GraphNode[],
  edges: GraphEdge[],
  algorithm: 'layered' | 'stress',
): Promise<Map<string, XYPosition>> {
  const { default: ELK } = await import('elkjs/lib/elk.bundled.js');
  const options: Record<string, string> =
    algorithm === 'layered'
      ? {
          'elk.algorithm': 'layered',
          'elk.direction': 'DOWN',
          'elk.edgeRouting': 'ORTHOGONAL',
          'elk.layered.spacing.nodeNodeBetweenLayers': '50',
          'elk.spacing.nodeNode': '16',
          'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
          'elk.layered.nodePlacement.strategy': 'BRANDES_KOEPF',
        }
      : { 'elk.algorithm': 'stress', 'elk.stress.desiredEdgeLength': '220' };
  const ids = new Set(nodes.map((n) => n.id));
  const laid = await new ELK().layout({
    id: 'root',
    layoutOptions: options,
    children: nodes.map((n) => ({ id: n.id, ...layoutBox(n) })),
    edges: edges
      .filter((e) => ids.has(e.source) && ids.has(e.target) && e.source !== e.target)
      .map((e, i) => ({ id: `e${i}`, sources: [e.source], targets: [e.target] })),
  });
  const byId = new Map(nodes.map((n) => [n.id, n]));
  return new Map(
    (laid.children ?? []).map((c) => {
      const n = byId.get(c.id)!;
      const box = layoutBox(n);
      return [c.id, topLeft(n, (c.x ?? 0) + box.width / 2, (c.y ?? 0) + box.height / 2)];
    }),
  );
}

/** Every layout behind one call; `root` centres the radial one. */
export function runLayout(
  name: LayoutName,
  nodes: GraphNode[],
  edges: GraphEdge[],
  root?: string,
): Promise<Map<string, XYPosition>> {
  switch (name) {
    case 'dagre-lr':
      return Promise.resolve(layoutGraph(nodes, edges, 'LR'));
    case 'lanes':
      return Promise.resolve(layoutLanes(nodes, edges));
    case 'radial':
      return Promise.resolve(layoutRadial(nodes, edges, root));
    case 'elk-layered':
      return layoutElk(nodes, edges, 'layered');
    case 'elk-stress':
      return layoutElk(nodes, edges, 'stress');
    default:
      return Promise.resolve(layoutGraph(nodes, edges));
  }
}

/** A watch target ("0x…" vault, "user-0x…") → the id of its node in the graph. */
export function targetNodeId(target: string): string {
  return target.startsWith('user-') ? `user:${target.slice('user-'.length)}` : target;
}

/**
 * The part of the graph one watch target stands on: its node, everything downstream of it
 * and everything upstream (its admins, its depositors). Siblings — other vaults on the same
 * markets — are dropped, not faded. A target with no node in the graph keeps the whole graph.
 */
export function scopeToTarget(graph: GraphResponse, target: string | undefined): GraphResponse {
  const root = target && targetNodeId(target);
  if (!root || !graph.nodes.some((n) => n.id === root)) return graph;
  const keep = new Set([...reach(root, graph.edges), ...reach(root, graph.edges, true)]);
  return {
    ...graph,
    nodes: graph.nodes.filter((n) => keep.has(n.id)),
    edges: graph.edges.filter((e) => keep.has(e.source) && keep.has(e.target)),
  };
}

/** Every node reachable from `start` following the edges forward (or backward), start included. */
export function reach(start: string, edges: GraphEdge[], backward = false): Set<string> {
  const seen = new Set([start]);
  const queue = [start];
  for (let id = queue.shift(); id !== undefined; id = queue.shift()) {
    for (const edge of edges) {
      const [from, to] = backward ? [edge.target, edge.source] : [edge.source, edge.target];
      if (from === id && !seen.has(to)) {
        seen.add(to);
        queue.push(to);
      }
    }
  }
  return seen;
}

/** The nodes one edge away from `id`, either way. */
export function adjacent(id: string, edges: GraphEdge[]): string[] {
  return edges.flatMap((e) => (e.source === id ? [e.target] : e.target === id ? [e.source] : []));
}

/** The nodes on some path from `from` down to `to`, both included. */
export function pathNodes(from: string, to: string, edges: GraphEdge[]): string[] {
  const up = reach(to, edges, true);
  return [...reach(from, edges)].filter((id) => up.has(id));
}

/** Detail keys that speak to risk, shown first in the selection panel. */
export const RISK_KEYS = [
  'health_factor',
  'liquidation_at',
  'lltv',
  'utilization',
  'share_of_market',
  'share_of_vault',
  'collateral',
  'expiry',
  'idle',
  'plain_withdrawal_capacity',
] as const;

/**
 * `analyze` embeds a networkx graph with lowercase kinds, flat node attributes
 * and `from`/`to` edges — not the `/api/graph` shape. This maps it onto the
 * six `/api/graph` kinds so a single Cytoscape component renders both.
 *
 * The mapping is a judgement call, not something the backend states:
 *   position, issuer           -> Actor     (capital at stake / the counterparty behind it)
 *   lending, amm               -> Pool      (where liquidity sits)
 *   asset, stable              -> Asset
 *   oracle                     -> Oracle
 *   chain, offchain            -> External  (dependency outside the position)
 */
const REPORT_KIND_TO_GRAPH_KIND: Record<string, GraphNodeKind> = {
  position: 'Actor',
  issuer: 'Actor',
  lending: 'Pool',
  amm: 'Pool',
  asset: 'Asset',
  stable: 'Asset',
  oracle: 'Oracle',
  chain: 'External',
  offchain: 'External',
};

export function normalizeReportGraph(
  graph: ReportGraph,
  title: string,
  subtitle: string,
): GraphResponse {
  const nodes: GraphNode[] = graph.nodes.map((node) => {
    const { id, kind, label, ...rest } = node;
    return {
      id,
      kind: REPORT_KIND_TO_GRAPH_KIND[kind] ?? 'External',
      label,
      details: { layer: kind, ...rest } satisfies Record<string, unknown>,
    };
  });

  const edges: GraphEdge[] = graph.edges.map((edge) => ({
    source: edge.from,
    target: edge.to,
    rel: edge.rel,
    amount: null,
    unit: null,
    details: {},
  }));

  return { title, subtitle, nodes, edges };
}

/** Log scale, same curve as the CLI's HTML, so edge widths read alike. */
export function edgeWidth(amount: number | null): number {
  if (amount == null || amount <= 0) return 1;
  return Math.min(10, 1 + Math.log10(1 + amount) / 1.2);
}

export function edgeLabel(amount: number | null, unit: string | null): string {
  if (amount == null || amount < 1) return '';
  const magnitude =
    Math.abs(amount) >= 1e6
      ? `${(amount / 1e6).toFixed(2)}M`
      : Math.abs(amount) >= 1e3
        ? `${(amount / 1e3).toFixed(1)}k`
        : amount.toFixed(2);
  return unit ? `${magnitude} ${unit}` : magnitude;
}

/** At least this many structural twins are drawn as one stacked node until it is clicked. */
const GROUP_MIN = 6;
export const GROUP_KEY = 'grouped';

/** What a label names, without its address: "mint control: ethereum:0x…" → "mint control". */
const labelStem = (label: string) => label.split(/:|\s0x/)[0].trim();

/**
 * Merges nodes of one kind and label stem with exactly the same edges (same relation to the same
 * neighbours),
 * GROUP_MIN or more of them, into one node; `expanded` holds the groups the user opened.
 */
export function groupTwins(
  graph: Pick<GraphResponse, 'nodes' | 'edges'>,
  expanded: ReadonlySet<string>,
): Pick<GraphResponse, 'nodes' | 'edges'> {
  const incident = new Map<string, string[]>();
  for (const e of graph.edges) {
    incident.set(e.source, [...(incident.get(e.source) ?? []), `>${e.rel}>${e.target}`]);
    incident.set(e.target, [...(incident.get(e.target) ?? []), `<${e.rel}<${e.source}`]);
  }
  const twins = new Map<string, GraphNode[]>();
  for (const n of graph.nodes) {
    const key = `${n.kind}|${labelStem(n.label)}|${(incident.get(n.id) ?? []).sort().join('|')}`;
    twins.set(key, [...(twins.get(key) ?? []), n]);
  }
  const groupOf = new Map<string, string>();
  const groups: GraphNode[] = [];
  for (const [key, members] of twins) {
    const id = `group:${key}`;
    if (members.length < GROUP_MIN || expanded.has(id)) continue;
    groups.push({
      id,
      kind: members[0].kind,
      label: `${members.length} × ${labelStem(members[0].label) || members[0].kind}`,
      details: { [GROUP_KEY]: members.length, members: members.map((m) => m.label).join(', ') },
    });
    for (const m of members) groupOf.set(m.id, id);
  }
  if (!groups.length) return graph;
  const seen = new Set<string>();
  const edges = graph.edges.flatMap((e) => {
    const source = groupOf.get(e.source) ?? e.source;
    const target = groupOf.get(e.target) ?? e.target;
    if (source === e.source && target === e.target) return [e];
    const key = `${source}|${e.rel}|${target}`;
    if (seen.has(key)) return [];
    seen.add(key);
    // One edge stands for the group's: no single amount fits it.
    return [{ ...e, source, target, amount: null }];
  });
  return { nodes: [...graph.nodes.filter((n) => !groupOf.has(n.id)), ...groups], edges };
}

/** React Flow edge id of the edge at `index` in the graph's edge list. */
export const edgeId = (index: number) => `e${index}`;

/** Lit nodes and edges, or null when nothing is focused. */
export type Lit = { nodes: Set<string>; edges: Set<string> } | null;

/** The whole flow through a node or an edge: upstream of `from`, downstream of `to`. */
export function flowLit(from: string, to: string, edges: GraphEdge[]): NonNullable<Lit> {
  const up = reach(from, edges, true);
  const down = reach(to, edges);
  const lit = new Set(
    edges.flatMap((e, i) =>
      (up.has(e.source) && up.has(e.target)) || (down.has(e.source) && down.has(e.target))
        ? [edgeId(i)]
        : [],
    ),
  );
  return { nodes: new Set([...up, ...down]), edges: lit };
}

/**
 * What the vault's assets rely on: for every node downstream of a market the vault supplies,
 * the sum of the vault's supply to those markets, largest first.
 */
export function pointsOfFailure(
  vault: string,
  edges: GraphEdge[],
): { id: string; amount: number; unit: string | null }[] {
  const exposed = new Map<string, number>();
  const supplies = edges.filter((e) => e.source === vault && e.rel === 'supplies' && e.amount);
  for (const s of supplies)
    for (const id of reach(s.target, edges))
      if (id !== vault) exposed.set(id, (exposed.get(id) ?? 0) + (s.amount ?? 0));
  const unit = supplies[0]?.unit ?? null;
  return [...exposed]
    .map(([id, amount]) => ({ id, amount, unit }))
    .sort((a, b) => b.amount - a.amount);
}

export type WeakLink = { id: string; level: 'critical' | 'warn'; reason: string };

/**
 * The graph's weak links, read off the node details alone: what is already failing (critical)
 * and what would make a failure worse or harder to see (warn). Critical first.
 */
export function weakLinks(nodes: GraphNode[]): WeakLink[] {
  const out: WeakLink[] = [];
  for (const n of nodes) {
    const d = n.details;
    const add = (level: WeakLink['level'], reason: string) => out.push({ id: n.id, level, reason });
    if (n.kind === 'Pool' && typeof d.unrealised_bad_debt === 'number' && d.unrealised_bad_debt > 0)
      add('critical', 'Unrealised bad debt');
    if (n.kind === 'Oracle' && d.stale === true) add('critical', 'Stale feed');
    if (n.kind === 'Pool' && d.oracle_class === 'constant-price')
      add('warn', 'Constant-price oracle');
    if (n.kind === 'Oracle' && typeof d.shared_text === 'string' && d.shared_text)
      add('warn', 'Shared by other markets');
    if (/^[DF]/.test(detailValue(d.pharos_grade)))
      add('warn', `Pharos ${detailValue(d.pharos_grade)}`);
    if (n.kind === 'External' && d.concentrated === true) add('warn', 'Concentrated TVL');
  }
  return out.sort((a, b) => Number(a.level === 'warn') - Number(b.level === 'warn'));
}
