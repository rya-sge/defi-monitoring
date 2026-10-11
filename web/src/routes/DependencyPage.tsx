// What does this vault depend on, down to which layer, and where are the weak links?
import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Panel } from '@xyflow/react';
import { X } from 'lucide-react';
import { useGraph, useSelectedTarget } from '../api/hooks';
import { GRAPH_NODE_KINDS } from '../api/types';
import type { GraphEdge, GraphNode, GraphNodeKind } from '../api/types';
import { ExpandAll, GraphCanvas, KindFilter } from '../components/GraphCanvas';
import type { GraphSelection } from '../components/GraphCanvas';
import { DetailsTable } from '../components/DetailsTable';
import { NodePanel } from '../components/graph/NodePanels';
import { ErrorState, Loading } from '../components/States';
import {
  KIND_COLOR,
  LAYOUTS,
  edgeLabel,
  layoutFlow,
  nodeAmount,
  reach,
  runLayout,
  scopeToTarget,
  targetNodeId,
  weakLinks,
} from '../lib/graph';
import type { LayoutName } from '../lib/graph';
import { useReveal } from '../lib/useReveal';
import { useTwinGroups } from '../lib/useTwinGroups';
import { detailValue } from '../lib/format';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const LAYOUT_KEY = 'graph-layout';
const H3 = 'mt-5.5 mb-1 text-[0.82rem] font-bold text-muted-foreground';
const RING = { critical: 'var(--critical)', warn: 'var(--warn)' };

function storedLayout(): LayoutName {
  try {
    const saved = localStorage.getItem(LAYOUT_KEY);
    return LAYOUTS.find((l) => l.value === saved)?.value ?? 'dagre-tb';
  } catch {
    return 'dagre-tb';
  }
}

/** The deepest layer below the root, edges followed forward. */
function layers(root: string, edges: GraphEdge[]): number {
  const depth = new Map([[root, 0]]);
  const queue = [root];
  for (let id = queue.shift(); id !== undefined; id = queue.shift())
    for (const e of edges)
      if (e.source === id && !depth.has(e.target)) {
        depth.set(e.target, depth.get(id)! + 1);
        queue.push(e.target);
      }
  return Math.max(...depth.values());
}

/** The selection a click on `node` would make, for a click in the weak-link list. */
function nodeSelection(node: GraphNode, nodes: GraphNode[], edges: GraphEdge[]): GraphSelection {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const around = (ids: Set<string>) =>
    [...ids].flatMap((id) => {
      const n = byId.get(id);
      return n && id !== node.id ? [{ id, label: n.label, kind: n.kind }] : [];
    });
  return {
    type: 'node',
    node,
    dependsOn: around(reach(node.id, edges)),
    exposed: around(reach(node.id, edges, true)),
    edges: edges.flatMap((edge) => {
      const outgoing = edge.source === node.id;
      if (!outgoing && edge.target !== node.id) return [];
      return [
        { edge, other: byId.get(outgoing ? edge.target : edge.source)?.label ?? '', outgoing },
      ];
    }),
  };
}

export function DependencyPage() {
  const { target, isPending: targetPending } = useSelectedTarget();
  // A Vault V2 gets its own graph, every market it allocates to; any other target is scoped
  // from the shared graph.
  const shared = useGraph();
  const ownGraph =
    !!target &&
    detailValue(shared.data?.nodes.find((n) => n.id === target)?.details.actor_type).startsWith(
      'Vault V2',
    );
  const own = useGraph(ownGraph ? { vault: target } : {});
  const { data: full, dataUpdatedAt, error } = own;
  const scoped = useMemo(
    () => full && (ownGraph ? full : scopeToTarget(full, target)),
    [full, ownGraph, target],
  );
  const twins = useTwinGroups(scoped);
  const root = target ? targetNodeId(target) : undefined;
  const reveal = useReveal(twins.graph, root);
  const data = reveal.graph;

  const [layout, setLayout] = useState<LayoutName>(storedLayout);
  const graphKey = `${target ?? ''}-${dataUpdatedAt}-${twins.layoutKey}`;
  // Laid out once on the whole graph, so opening a node never moves the others; ELK is async.
  const positions = useQuery({
    queryKey: ['graph-layout', layout, graphKey],
    queryFn: () => runLayout(layout, twins.graph!.nodes, twins.graph!.edges, root),
    enabled: !!twins.graph,
    staleTime: Infinity,
    gcTime: 0,
  });

  const [hiddenKinds, setHiddenKinds] = useState<ReadonlySet<GraphNodeKind>>(
    new Set(['Admin', 'External']),
  );
  const [search, setSearch] = useState('');
  const [selection, setSelection] = useState<GraphSelection>(null);

  const weak = useMemo(() => weakLinks(twins.graph?.nodes ?? []), [twins.graph]);
  const overlay = useMemo(() => {
    if (!data) return undefined;
    const out: Record<string, { ring?: string; amount: string[] }> = {};
    for (const w of weak) {
      const n = data.nodes.find((candidate) => candidate.id === w.id);
      if (n && !out[n.id]) out[n.id] = { ring: RING[w.level], amount: nodeAmount(n, data.edges) };
    }
    return out;
  }, [data, weak]);

  const presentKinds = useMemo(
    () => GRAPH_NODE_KINDS.filter((kind) => data?.nodes.some((node) => node.kind === kind)),
    [data],
  );
  const visibleKinds = useMemo(
    () => new Set(GRAPH_NODE_KINDS.filter((kind) => !hiddenKinds.has(kind))),
    [hiddenKinds],
  );

  if (targetPending || shared.isPending || own.isPending)
    return <Loading what="the dependency graph" />;
  if (error) return <ErrorState what="the dependency graph" error={error} />;
  if (!data || !twins.graph)
    return <ErrorState what="the dependency graph" error="empty response" />;
  if (positions.error) return <ErrorState what="the layout" error={positions.error} />;

  const all = twins.graph;
  const labelOf = (id: string) => all.nodes.find((n) => n.id === id)?.label ?? id;
  const pick = (layoutName: LayoutName) => {
    setLayout(layoutName);
    try {
      localStorage.setItem(LAYOUT_KEY, layoutName);
    } catch {
      // a blocked storage only loses the remembered choice
    }
  };
  const toggleKind = (kind: GraphNodeKind) =>
    setHiddenKinds((previous) => {
      const next = new Set(previous);
      if (!next.delete(kind)) next.add(kind);
      return next;
    });

  return (
    <div className="relative h-full min-h-[70vh] overflow-hidden">
      {positions.data ? (
        <GraphCanvas
          key={`${graphKey}-${layout}`}
          positions={positions.data}
          flow={layoutFlow(layout)}
          nodes={data.nodes}
          edges={data.edges}
          visibleKinds={visibleKinds}
          more={reveal.more(visibleKinds)}
          overlay={overlay}
          search={search}
          selection={selection}
          onSelect={(next) => {
            // A group of twins opens on click; it has nothing of its own to show.
            if (next?.type !== 'node') setSelection(next);
            else if (twins.open(next.node)) setSelection(null);
            else {
              reveal.toggle(next.node.id);
              setSelection(next);
            }
          }}
        >
          <Panel position="top-left" className="flex flex-wrap items-center gap-2">
            <Select value={layout} onValueChange={(v) => pick(v as LayoutName)}>
              <SelectTrigger size="sm" className="w-52 bg-background" aria-label="Layout">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LAYOUTS.map((l) => (
                  <SelectItem key={l.value} value={l.value}>
                    {l.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search"
              aria-label="Search the graph"
              className="h-8 w-44 bg-background"
            />
            <ExpandAll
              all={reveal.all}
              onExpand={reveal.expandAll}
              onCollapse={reveal.collapseAll}
            />
            <span className="text-[0.8rem] text-muted-foreground tabular-nums">
              {all.nodes.length} nodes ·{' '}
              {root && all.nodes.some((n) => n.id === root) ? layers(root, all.edges) : '—'} layers
            </span>
          </Panel>
          <Panel position="bottom-left">
            <KindFilter kinds={presentKinds} hidden={hiddenKinds} onToggle={toggleKind} />
          </Panel>
        </GraphCanvas>
      ) : (
        <Loading what="the layout" />
      )}

      <aside className="absolute top-3.5 right-3.5 bottom-12 w-[340px] max-w-[calc(100%-28px)] overflow-auto rounded-lg border bg-background p-5.5 shadow-sm">
        {selection ? (
          <>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute top-2 right-2"
              aria-label="Close"
              onClick={() => setSelection(null)}
            >
              <X />
            </Button>
            <SelectionPanel selection={selection} labelOf={labelOf} />
          </>
        ) : (
          <WeakLinks
            weak={weak}
            labelOf={labelOf}
            onPick={(id) => {
              const node = all.nodes.find((n) => n.id === id);
              if (!node) return;
              reveal.showPath(id);
              setSelection(nodeSelection(node, all.nodes, all.edges));
            }}
          />
        )}
      </aside>
    </div>
  );
}

function WeakLinks({
  weak,
  labelOf,
  onPick,
}: {
  weak: ReturnType<typeof weakLinks>;
  labelOf: (id: string) => string;
  onPick: (id: string) => void;
}) {
  return (
    <>
      <h2 className="mt-0 mb-2 text-base">Weak links</h2>
      {weak.length === 0 ? <p className="text-muted-foreground">None found</p> : null}
      <ul className="m-0 grid list-none gap-0.5 p-0">
        {weak.map((w) => (
          <li key={`${w.id}-${w.reason}`}>
            <button
              type="button"
              onClick={() => onPick(w.id)}
              className="flex w-full items-baseline gap-2 rounded px-2 py-1.5 text-left text-sm hover:bg-accent"
            >
              <span
                className="size-2 shrink-0 translate-y-[-1px] rounded-full"
                style={{ background: RING[w.level] }}
              />
              <span className="min-w-0 flex-1 truncate">{labelOf(w.id)}</span>
              <span className="shrink-0 text-muted-foreground">{w.reason}</span>
            </button>
          </li>
        ))}
      </ul>
    </>
  );
}

function SelectionPanel({
  selection,
  labelOf,
}: {
  selection: NonNullable<GraphSelection>;
  labelOf: (id: string) => string;
}) {
  if (selection.type === 'node') {
    const { node, dependsOn, exposed } = selection;
    const counts = (items: typeof dependsOn) => {
      const by = new Map<GraphNodeKind, number>();
      for (const item of items) by.set(item.kind, (by.get(item.kind) ?? 0) + 1);
      return [...by];
    };
    return (
      <div className="pr-6">
        <p className="mt-0">
          <b>{node.label}</b> <span className="text-muted-foreground">{node.kind}</span>
        </p>
        {[
          ['Depends on', counts(dependsOn)],
          ['Exposed to it', counts(exposed)],
        ].map(([title, items]) =>
          (items as [GraphNodeKind, number][]).length ? (
            <div key={title as string}>
              <h3 className={H3}>{title as string}</h3>
              <p className="m-0 text-[0.86rem]">
                {(items as [GraphNodeKind, number][]).map(([kind, count]) => (
                  <span key={kind} className="mr-3.5 inline-flex items-center gap-1.5">
                    <span className="size-2.5" style={{ background: KIND_COLOR[kind] }} />
                    {count} {kind}
                  </span>
                ))}
              </p>
            </div>
          ) : null,
        )}
        <NodePanel node={node} labelOf={labelOf} />
      </div>
    );
  }
  const { edge, sourceLabel, targetLabel } = selection;
  const amount = edgeLabel(edge.amount, edge.unit);
  return (
    <div className="pr-6">
      <p className="mt-0">
        <b>{sourceLabel}</b> <span className="text-muted-foreground">— {edge.rel} →</span>{' '}
        <b>{targetLabel}</b>
      </p>
      <DetailsTable details={{ ...(amount ? { amount } : {}), ...edge.details }} />
    </div>
  );
}
