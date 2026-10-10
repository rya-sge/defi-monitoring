import type cytoscape from 'cytoscape';
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

/** Cytoscape shapes, also from `riskdep/graph.py`. */
export const KIND_SHAPE: Record<GraphNodeKind, cytoscape.Css.NodeShape> = {
  Actor: 'round-rectangle',
  Pool: 'ellipse',
  Asset: 'round-tag',
  Oracle: 'diamond',
  Admin: 'triangle',
  External: 'rectangle',
};

export const KIND_DESCRIPTION: Record<GraphNodeKind, string> = {
  Actor: 'whose capital is at stake: an address, a Vault V2',
  Pool: 'where liquidity sits: Blue market, Pendle pool',
  Asset: 'token: loan, collateral, yield source, reused vault share',
  Oracle: 'market oracle and the feeds it reads',
  Admin: 'decides for a vault: owner, curator, allocator, sentinel',
  External: 'off-chain dependency (registry.json)',
};

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
