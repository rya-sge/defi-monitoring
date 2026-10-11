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
 * sharp for a vault or a pool. Hexagon: holds nothing, smaller for a feed than for the
 * oracle that reads it (D64).
 */
const ROLE_DRAWING: Record<
  NodeRole,
  { shape: NodeShape; width: number; height: number; icon: LucideIcon }
> = {
  vault: { shape: 'rect', width: 80, height: 70, icon: Vault },
  user: { shape: 'rounded', width: 80, height: 70, icon: User },
  market: { shape: 'rect', width: 80, height: 70, icon: Database },
  pendle: { shape: 'rect', width: 80, height: 70, icon: Database },
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

/** DefiLlama's keyless token-icon CDN, by address (D67). */
export function tokenIconUrl(node: GraphNode): string | null {
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

/** dagre, top to bottom; returns each node's top-left corner (D62). */
export function layoutGraph(nodes: GraphNode[], edges: GraphEdge[]): Map<string, XYPosition> {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: 'TB', ranksep: 50, nodesep: 16 });
  g.setDefaultEdgeLabel(() => ({}));
  for (const node of nodes) {
    const { width, height } = nodeDrawing(node);
    g.setNode(node.id, {
      width: Math.max(width, NAME_SLOT.width),
      height: height + NAME_SLOT.height,
    });
  }
  for (const edge of edges) g.setEdge(edge.source, edge.target);
  dagre.layout(g);
  return new Map(
    nodes.map((node) => {
      const { x, y } = g.node(node.id);
      const { width, height } = nodeDrawing(node);
      return [node.id, { x: x - width / 2, y: y - (height + NAME_SLOT.height) / 2 }];
    }),
  );
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
