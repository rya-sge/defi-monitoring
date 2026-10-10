import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import type { Core, EdgeSingular, ElementDefinition, NodeSingular } from 'cytoscape';
import type { GraphEdge, GraphNode, GraphNodeKind } from '../api/types';
import { KIND_COLOR, KIND_SHAPE, edgeLabel, edgeWidth } from '../lib/graph';

export type GraphSelection =
  | { type: 'node'; node: GraphNode; incoming: string[]; outgoing: string[] }
  | { type: 'edge'; edge: GraphEdge; sourceLabel: string; targetLabel: string }
  | null;

export type GraphCanvasProps = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  /** Kinds currently shown; a node of a hidden kind is removed from the layout. */
  visibleKinds: ReadonlySet<GraphNodeKind>;
  /** Free-text filter: matches label, id and details; non-matches are faded. */
  search: string;
  onSelect: (selection: GraphSelection) => void;
  /** Bumped by the caller to re-run the layout or fit the viewport. */
  fitNonce: number;
  layoutNonce: number;
};

type NodeData = GraphNode & { label: string };
type EdgeData = GraphEdge & { id: string; label: string; w: number };

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function GraphCanvas({
  nodes,
  edges,
  visibleKinds,
  search,
  onSelect,
  fitNonce,
  layoutNonce,
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  // Keeps the tap handlers stable (they are bound once, at mount) while always
  // calling the newest callback. Written in an effect, never during render.
  const onSelectRef = useRef(onSelect);
  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const nodeEls: ElementDefinition[] = nodes.map((node) => ({
      data: { ...node } satisfies NodeData,
    }));
    const edgeEls: ElementDefinition[] = edges.map((edge, index) => ({
      data: {
        ...edge,
        id: `e${index}`,
        label: edgeLabel(edge.amount, edge.unit),
        w: edgeWidth(edge.amount),
      } satisfies EdgeData,
    }));

    const fg = cssVar('--fg');
    const line = cssVar('--line');
    const muted = cssVar('--muted');
    const edgeColor = cssVar('--edge');
    const bg = cssVar('--bg');

    const cy = cytoscape({
      container,
      elements: [...nodeEls, ...edgeEls],
      wheelSensitivity: 0.2,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (el: NodeSingular) =>
              KIND_COLOR[el.data('kind') as GraphNodeKind] ?? KIND_COLOR.External,
            shape: (el: NodeSingular) => KIND_SHAPE[el.data('kind') as GraphNodeKind] ?? 'ellipse',
            label: 'data(label)',
            'font-size': 10,
            color: fg,
            'text-valign': 'bottom',
            'text-margin-y': 4,
            width: 26,
            height: 26,
            'text-wrap': 'wrap',
            'text-max-width': '120px',
            'border-width': 1,
            'border-color': line,
          },
        },
        {
          selector: 'node[kind="Actor"]',
          style: {
            width: 44,
            height: 30,
            'font-weight': 'bold',
            'font-size': 11,
            'text-max-width': '90px',
          },
        },
        {
          selector: 'node[kind="Asset"],node[kind="Oracle"],node[kind="External"]',
          style: { 'min-zoomed-font-size': 9 },
        },
        {
          selector: 'edge',
          style: {
            width: 'data(w)',
            'line-color': edgeColor,
            'target-arrow-color': edgeColor,
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            opacity: 0.75,
            label: 'data(label)',
            'font-size': 8,
            color: muted,
            'text-rotation': 'autorotate',
            'text-background-color': bg,
            'text-background-opacity': 0.8,
          },
        },
        { selector: '.faded', style: { opacity: 0.08 } },
        { selector: '.hidden', style: { display: 'none' } },
        {
          selector: ':selected',
          style: { 'border-width': 3, 'border-color': fg, 'line-color': fg },
        },
      ],
      layout: { name: 'preset' },
    });

    cyRef.current = cy;

    cy.on('tap', 'node', (event) => {
      const node = event.target as NodeSingular;
      cy.elements().addClass('faded');
      node.closedNeighborhood().removeClass('faded');
      const label = (id: string) => cy.getElementById(id).data('label') as string;
      onSelectRef.current({
        type: 'node',
        node: node.data() as GraphNode,
        outgoing: node
          .outgoers('edge')
          .map((e: EdgeSingular) => `${e.data('rel') as string} → ${label(e.target().id())}`),
        incoming: node
          .incomers('edge')
          .map((e: EdgeSingular) => `${label(e.source().id())} → ${e.data('rel') as string}`),
      });
    });

    cy.on('tap', 'edge', (event) => {
      const edge = event.target as EdgeSingular;
      cy.elements().addClass('faded');
      edge.removeClass('faded');
      edge.connectedNodes().removeClass('faded');
      onSelectRef.current({
        type: 'edge',
        edge: edge.data() as GraphEdge,
        sourceLabel: edge.source().data('label') as string,
        targetLabel: edge.target().data('label') as string,
      });
    });

    cy.on('tap', (event) => {
      if (event.target === cy) {
        cy.elements().removeClass('faded');
        onSelectRef.current(null);
      }
    });

    runLayout(cy);

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [nodes, edges]);

  // Kind filter.
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.batch(() => {
      cy.nodes().forEach((node) => {
        const hidden = !visibleKinds.has(node.data('kind') as GraphNodeKind);
        node.toggleClass('hidden', hidden);
      });
    });
  }, [visibleKinds]);

  // Search: fade everything that is not a hit or a neighbour of one.
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const query = search.trim().toLowerCase();
    cy.elements().removeClass('faded');
    if (!query) return;
    const hits = cy.nodes().filter((node) => {
      const haystack = `${node.data('label') as string} ${node.id()} ${JSON.stringify(
        node.data('details'),
      )}`.toLowerCase();
      return haystack.includes(query);
    });
    cy.elements().addClass('faded');
    hits.closedNeighborhood().removeClass('faded');
  }, [search]);

  useEffect(() => {
    if (fitNonce > 0) cyRef.current?.fit(undefined, 30);
  }, [fitNonce]);

  useEffect(() => {
    const cy = cyRef.current;
    if (cy && layoutNonce > 0) runLayout(cy);
  }, [layoutNonce]);

  return (
    <div className="relative min-w-0">
      <div
        ref={containerRef}
        className="size-full"
        role="img"
        aria-label="Interactive dependency graph"
      />
    </div>
  );
}

/** Breadth-first from the actors and admins — the same roots the CLI uses. */
function runLayout(cy: Core): void {
  const roots = cy
    .nodes()
    .filter((node) => node.data('kind') === 'Actor' || node.data('kind') === 'Admin');
  cy.layout({
    name: 'breadthfirst',
    directed: true,
    spacingFactor: 1.5,
    ...(roots.length > 0 ? { roots } : {}),
  }).run();
}
