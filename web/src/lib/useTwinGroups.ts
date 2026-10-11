import { useMemo, useState } from 'react';
import type { GraphNode, GraphResponse } from '../api/types';
import { GROUP_KEY, groupTwins } from './graph';

type Graph = Pick<GraphResponse, 'nodes' | 'edges'>;

/**
 * A graph with its structural twins grouped (D206). `open` expands a clicked group and says
 * whether it was one; `layoutKey` changes with each expansion, for the canvas to re-lay out.
 */
export function useTwinGroups(graph: Graph | undefined) {
  const [expanded, setExpanded] = useState<ReadonlySet<string>>(new Set());
  const grouped = useMemo(() => graph && groupTwins(graph, expanded), [graph, expanded]);
  const open = (node: GraphNode) => {
    if (!(GROUP_KEY in node.details)) return false;
    setExpanded((previous) => new Set([...previous, node.id]));
    return true;
  };
  return { graph: grouped, open, layoutKey: expanded.size };
}
