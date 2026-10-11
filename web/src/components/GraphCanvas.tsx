import { useMemo, useState } from 'react';
import { MarkerType, Panel, ReactFlow, useNodesState, useReactFlow } from '@xyflow/react';
import type { XYPosition } from '@xyflow/react';
import { Maximize, Minus, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import '@xyflow/react/dist/base.css';
import type { GraphEdge, GraphNode, GraphNodeKind } from '../api/types';
import { detailValue } from '../lib/format';
import { edgeLabel, edgeWidth, layoutGraph, nodeAmount, reach } from '../lib/graph';
import { RiskEdge, RiskNode } from './GraphElements';
import type { RiskEdgeType, RiskNodeType } from './GraphElements';

export type FlowNeighbour = { id: string; label: string; kind: GraphNodeKind };

export type GraphSelection =
  | {
      type: 'node';
      node: GraphNode;
      /** Everything the node relies on, transitively (downstream). */
      dependsOn: FlowNeighbour[];
      /** Everything exposed to the node, transitively (upstream). */
      exposed: FlowNeighbour[];
      /** Incident edges, with the label of the node at the other end. */
      edges: { edge: GraphEdge; other: string; outgoing: boolean }[];
    }
  | { type: 'edge'; id: string; edge: GraphEdge; sourceLabel: string; targetLabel: string }
  | null;

export type GraphCanvasProps = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  /** Kinds currently shown; a node of a hidden kind is hidden with its edges. */
  visibleKinds: ReadonlySet<GraphNodeKind>;
  /** Free-text filter: matches label, id and details; non-matches are faded. */
  search: string;
  /** The selection drives the focus: its whole upstream and downstream flow stays lit. */
  selection: GraphSelection;
  onSelect: (selection: GraphSelection) => void;
  /** Lit when nothing is selected or searched: the impact page's reached nodes and steps. */
  focus?: Lit;
  /** Per node: a ring colour, and amount lines that replace the node's own. */
  overlay?: Record<string, { ring?: string; amount: string[] }>;
  /** Node positions to use instead of the dagre layout. */
  positions?: Map<string, XYPosition>;
  /** Draw edges without arrowheads (a symmetric relation). */
  undirected?: boolean;
};

const nodeTypes = { risk: RiskNode };
const edgeTypes = { risk: RiskEdge };
const FADED = 0.08;
const edgeId = (index: number) => `e${index}`;

/** Lit nodes and edges, or null when nothing is focused. */
export type Lit = { nodes: Set<string>; edges: Set<string> } | null;

/** The whole flow through the selection: upstream of its start, downstream of its end. */
function flowLit(selection: GraphSelection, edges: GraphEdge[]): Lit {
  if (!selection) return null;
  const [from, to] =
    selection.type === 'node'
      ? [selection.node.id, selection.node.id]
      : [selection.edge.source, selection.edge.target];
  const up = reach(from, edges, true);
  const down = reach(to, edges);
  const lit = new Set(
    edges.flatMap((e, i) =>
      (up.has(e.source) && up.has(e.target)) || (down.has(e.source) && down.has(e.target))
        ? [edgeId(i)]
        : [],
    ),
  );
  if (selection.type === 'edge') lit.add(selection.id);
  return { nodes: new Set([...up, ...down]), edges: lit };
}

/** Search hits and their direct neighbours. */
function searchLit(search: string, nodes: GraphNode[], edges: GraphEdge[]): Lit {
  const query = search.trim().toLowerCase();
  if (!query) return null;
  const hits = new Set(
    nodes
      .filter((n) =>
        `${n.label} ${n.id} ${JSON.stringify(n.details)}`.toLowerCase().includes(query),
      )
      .map((n) => n.id),
  );
  const lit = { nodes: new Set(hits), edges: new Set<string>() };
  edges.forEach((e, i) => {
    if (hits.has(e.source) || hits.has(e.target)) {
      lit.edges.add(edgeId(i));
      lit.nodes.add(e.source);
      lit.nodes.add(e.target);
    }
  });
  return lit;
}

function initialNodes(
  nodes: GraphNode[],
  edges: GraphEdge[],
  given?: Map<string, XYPosition>,
): RiskNodeType[] {
  const positions = given ?? layoutGraph(nodes, edges);
  return nodes.map((node) => ({
    id: node.id,
    type: 'risk',
    position: positions.get(node.id) ?? { x: 0, y: 0 },
    data: {
      node,
      amount: nodeAmount(node, edges),
      underlying: nodes.find(
        (candidate) =>
          candidate.kind === 'Asset' &&
          edges.some(
            (ptEdge) =>
              ptEdge.source === node.id &&
              ptEdge.rel === 'trades in / redeems through' &&
              edges.some(
                (poolEdge) =>
                  poolEdge.source === ptEdge.target &&
                  poolEdge.rel === 'yield source' &&
                  poolEdge.target === candidate.id,
              ),
          ),
      ),
    },
  }));
}

/** Zoom in, zoom out, fit: shadcn buttons over React Flow's viewport API. */
function ZoomControls() {
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  const controls = [
    { label: 'Zoom in', icon: Plus, run: () => void zoomIn() },
    { label: 'Zoom out', icon: Minus, run: () => void zoomOut() },
    { label: 'Fit view', icon: Maximize, run: () => void fitView({ padding: 0.1 }) },
  ];
  return (
    <Panel position="bottom-right" className="flex flex-col">
      {controls.map(({ label, icon: Icon, run }) => (
        <Button
          key={label}
          type="button"
          variant="outline"
          size="icon-sm"
          aria-label={label}
          title={label}
          onClick={run}
          className="-mt-px first:mt-0"
        >
          <Icon />
        </Button>
      ))}
    </Panel>
  );
}

/**
 * Laid out once per mount: the caller remounts it (with `key`) to re-run the layout,
 * which also drops the user's drags.
 */
export function GraphCanvas({
  nodes,
  edges,
  visibleKinds,
  search,
  selection,
  onSelect,
  focus = null,
  overlay,
  positions,
  undirected = false,
}: GraphCanvasProps) {
  const [initial] = useState(() => initialNodes(nodes, edges, positions));
  const [rfNodes, , onNodesChange] = useNodesState(initial);

  const rfEdges = useMemo<RiskEdgeType[]>(
    () =>
      edges.map((edge, index) => {
        const hf = edge.details.health_factor;
        // Dependencies use dashes; every edge and arrowhead has the same readable contrast.
        const colour = 'var(--edge)';
        return {
          id: edgeId(index),
          type: 'risk',
          source: edge.source,
          target: edge.target,
          // Sized in screen units, so a thick edge does not get a giant arrowhead.
          markerEnd: undirected
            ? undefined
            : {
                type: MarkerType.ArrowClosed,
                color: colour,
                width: 14,
                height: 14,
                markerUnits: 'userSpaceOnUse',
              },
          data: {
            edge,
            width: edgeWidth(edge.amount),
            colour,
            label: [edgeLabel(edge.amount, edge.unit), hf != null ? `HF ${detailValue(hf)}` : '']
              .filter(Boolean)
              .join(' · '),
          },
        };
      }),
    [edges, undirected],
  );

  const lit = useMemo(
    () => flowLit(selection, edges) ?? searchLit(search, nodes, edges) ?? focus,
    [selection, search, nodes, edges, focus],
  );

  const shownNodes = useMemo(
    () =>
      rfNodes.map((n) => ({
        ...n,
        data: overlay?.[n.id] ? { ...n.data, ...overlay[n.id] } : n.data,
        hidden: !visibleKinds.has(n.data.node.kind),
        selected: selection?.type === 'node' && selection.node.id === n.id,
        style: { opacity: lit && !lit.nodes.has(n.id) ? FADED : 1 },
      })),
    [rfNodes, visibleKinds, lit, selection, overlay],
  );

  const shownEdges = useMemo(
    () =>
      rfEdges.map((e) => ({
        ...e,
        selected: selection?.type === 'edge' && selection.id === e.id,
        style: { opacity: lit && !lit.edges.has(e.id) ? FADED : 1 },
      })),
    [rfEdges, lit, selection],
  );

  const byId = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);
  const neighbours = (ids: Set<string>, self: string): FlowNeighbour[] =>
    [...ids].flatMap((id) => {
      const n = byId.get(id);
      return n && id !== self ? [{ id, label: n.label, kind: n.kind }] : [];
    });

  return (
    <ReactFlow
      className="absolute inset-0"
      nodes={shownNodes}
      edges={shownEdges}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      onNodesChange={onNodesChange}
      nodesConnectable={false}
      minZoom={0.1}
      fitView
      fitViewOptions={{ padding: 0.1 }}
      proOptions={{ hideAttribution: true }}
      aria-label="Interactive dependency graph"
      onNodeClick={(_, { data: { node } }) =>
        onSelect({
          type: 'node',
          node,
          dependsOn: neighbours(reach(node.id, edges), node.id),
          exposed: neighbours(reach(node.id, edges, true), node.id),
          edges: edges.flatMap((edge) => {
            const outgoing = edge.source === node.id;
            if (!outgoing && edge.target !== node.id) return [];
            const other = byId.get(outgoing ? edge.target : edge.source);
            return [{ edge, other: other?.label ?? '', outgoing }];
          }),
        })
      }
      onEdgeClick={(_, { id, data }) => {
        if (!data) return;
        onSelect({
          type: 'edge',
          id,
          edge: data.edge,
          sourceLabel: byId.get(data.edge.source)?.label ?? data.edge.source,
          targetLabel: byId.get(data.edge.target)?.label ?? data.edge.target,
        });
      }}
      onPaneClick={() => onSelect(null)}
    >
      <ZoomControls />
    </ReactFlow>
  );
}
