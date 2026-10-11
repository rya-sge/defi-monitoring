import { useMemo, useState } from 'react';
import type { GraphNodeKind, GraphResponse } from '../api/types';
import { adjacent, layoutGraph, pathNodes } from './graph';

type Graph = Pick<GraphResponse, 'nodes' | 'edges'>;

/**
 * The graph as far as the user opened it (D212): the root and its neighbours, the neighbours
 * of every opened node still in view, and the last path asked for. `toggle` opens or closes a
 * node; closing one hides what only it revealed. Without a root in the graph, all of it.
 */
export function useReveal(graph: Graph | undefined, root: string | undefined) {
  const [opened, setOpened] = useState<ReadonlySet<string>>(new Set());
  const [path, setPath] = useState<string[]>([]);
  const shown = useMemo(() => {
    if (!graph || !root || !graph.nodes.some((n) => n.id === root)) return graph;
    const ids = new Set([root, ...adjacent(root, graph.edges), ...path]);
    for (let grew = true; grew;) {
      grew = false;
      for (const id of opened)
        if (ids.has(id))
          for (const next of adjacent(id, graph.edges))
            if (!ids.has(next)) {
              ids.add(next);
              grew = true;
            }
    }
    return {
      nodes: graph.nodes.filter((n) => ids.has(n.id)),
      edges: graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target)),
    };
  }, [graph, root, opened, path]);
  const toggle = (id: string) =>
    setOpened((previous) => {
      const next = new Set(previous);
      if (!next.delete(id)) next.add(id);
      return next;
    });
  const showPath = (to: string) => setPath(graph && root ? pathNodes(root, to, graph.edges) : []);
  /** Per node in view: its neighbours of a visible kind that are not in view, the "+N". */
  const more = (visibleKinds: ReadonlySet<GraphNodeKind>): Record<string, number> => {
    if (!graph || !shown || shown === graph) return {};
    const kinds = new Map(graph.nodes.map((n) => [n.id, n.kind]));
    const ids = new Set(shown.nodes.map((n) => n.id));
    return Object.fromEntries(
      shown.nodes.map((n) => [
        n.id,
        new Set(
          adjacent(n.id, graph.edges).filter((id) => {
            const kind = kinds.get(id);
            return !ids.has(id) && kind != null && visibleKinds.has(kind);
          }),
        ).size,
      ]),
    );
  };
  // Laid out once on the whole graph, so opening a node never moves the others.
  const positions = useMemo(() => graph && layoutGraph(graph.nodes, graph.edges), [graph]);
  return {
    graph: shown,
    positions,
    more,
    /** Everything in view: the button then collapses back to level 1. */
    all: !!graph && opened.size >= graph.nodes.length,
    expandAll: () => setOpened(new Set(graph?.nodes.map((n) => n.id))),
    collapseAll: () => {
      setOpened(new Set());
      setPath([]);
    },
    toggle,
    showPath,
  };
}
