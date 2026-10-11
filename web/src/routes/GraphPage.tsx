import { useMemo, useState } from 'react';
import { X } from 'lucide-react';
import { useGraph, useSelectedTarget } from '../api/hooks';
import { GRAPH_NODE_KINDS } from '../api/types';
import type { GraphNodeKind } from '../api/types';
import { GraphCanvas } from '../components/GraphCanvas';
import type { FlowNeighbour, GraphSelection } from '../components/GraphCanvas';
import { DetailsTable } from '../components/DetailsTable';
import { ErrorState, Loading } from '../components/States';
import { KIND_COLOR, RISK_KEYS, edgeLabel, scopeToTarget } from '../lib/graph';
import { Button } from '@/components/ui/button';

const PANEL_H3 = 'mt-5.5 mb-1 text-[0.82rem] font-bold text-muted-foreground';

/** Splits a details bag into the risk figures and the rest. */
function splitRisk(details: Record<string, unknown>) {
  const risk: Record<string, unknown> = {};
  const rest: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(details)) {
    if ((RISK_KEYS as readonly string[]).includes(key)) risk[key] = value;
    else rest[key] = value;
  }
  return { risk, rest };
}

export function GraphPage() {
  const { target, isPending: targetPending } = useSelectedTarget();
  // One graph holds every vault the selector offers (the selector lists them from it), so
  // scoping is done here rather than with a live `?vault=` read per selection.
  const { data: full, dataUpdatedAt, isPending, error } = useGraph();
  const data = useMemo(() => full && scopeToTarget(full, target), [full, target]);
  const [hiddenKinds, setHiddenKinds] = useState<ReadonlySet<GraphNodeKind>>(new Set());
  const [selection, setSelection] = useState<GraphSelection>(null);

  const presentKinds = useMemo(
    () => GRAPH_NODE_KINDS.filter((kind) => data?.nodes.some((node) => node.kind === kind)),
    [data],
  );

  const visibleKinds = useMemo(
    () => new Set(GRAPH_NODE_KINDS.filter((kind) => !hiddenKinds.has(kind))),
    [hiddenKinds],
  );

  if (targetPending || isPending) return <Loading what="the dependency graph" />;
  if (error) return <ErrorState what="the dependency graph" error={error} />;
  if (!data) return <ErrorState what="the dependency graph" error="empty response" />;

  const toggleKind = (kind: GraphNodeKind) => {
    setHiddenKinds((previous) => {
      const next = new Set(previous);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });
  };

  return (
    <div className="relative h-full min-h-[70vh] overflow-hidden">
      {/* Remounting re-runs the layout when the target or data changes. */}
      <GraphCanvas
        key={`${target ?? ''}-${dataUpdatedAt}`}
        nodes={data.nodes}
        edges={data.edges}
        visibleKinds={visibleKinds}
        search=""
        selection={selection}
        onSelect={setSelection}
      />

      {/* Legend and kind filter in one: the colour chip keys the node colour. */}
      <div className="absolute bottom-3.5 left-3.5 flex flex-wrap gap-1 rounded-md bg-background/80">
        {presentKinds.map((kind) => (
          <Button
            key={kind}
            type="button"
            variant="ghost"
            size="xs"
            aria-pressed={!hiddenKinds.has(kind)}
            onClick={() => toggleKind(kind)}
            className="font-normal aria-[pressed=false]:opacity-40"
          >
            <span className="size-2.5" style={{ background: KIND_COLOR[kind] }} />
            {kind}
          </Button>
        ))}
      </div>

      {selection ? (
        <aside className="absolute top-3.5 right-3.5 bottom-12 w-[340px] max-w-[calc(100%-28px)] overflow-auto rounded-lg border bg-background p-5.5 shadow-sm">
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
          <SelectionPanel selection={selection} />
        </aside>
      ) : null}
    </div>
  );
}

function KindCounts({ title, items }: { title: string; items: FlowNeighbour[] }) {
  if (items.length === 0) return null;
  const counts = new Map<GraphNodeKind, number>();
  for (const item of items) counts.set(item.kind, (counts.get(item.kind) ?? 0) + 1);
  return (
    <>
      <h3 className={PANEL_H3}>{title}</h3>
      <p className="text-[0.86rem]">
        {[...counts].map(([kind, count]) => (
          <span key={kind} className="mr-3.5 inline-flex items-center gap-1.5">
            <span className="size-2.5" style={{ background: KIND_COLOR[kind] }} />
            {count} {kind}
          </span>
        ))}
      </p>
    </>
  );
}

function SelectionPanel({ selection }: { selection: NonNullable<GraphSelection> }) {
  if (selection.type === 'node') {
    const { node, dependsOn, exposed, edges } = selection;
    const { risk, rest } = splitRisk(node.details);
    const riskyEdges = edges.filter(({ edge }) => Object.keys(splitRisk(edge.details).risk).length);
    return (
      <div className="pr-6">
        <p>
          <b>{node.label}</b> <span className="text-muted-foreground">{node.kind}</span>
        </p>
        <h3 className={PANEL_H3}>Risk</h3>
        <DetailsTable details={risk} />
        <KindCounts title="Depends on" items={dependsOn} />
        <KindCounts title="Exposed to it" items={exposed} />
        {riskyEdges.map(({ edge, other, outgoing }) => (
          <div key={`${edge.source}-${edge.target}-${edge.rel}`}>
            <h3 className={PANEL_H3}>
              {outgoing ? `${edge.rel} → ${other}` : `${other} → ${edge.rel}`}
            </h3>
            <DetailsTable details={splitRisk(edge.details).risk} />
          </div>
        ))}
        <h3 className={PANEL_H3}>Details</h3>
        <DetailsTable details={rest} />
      </div>
    );
  }

  const { edge, sourceLabel, targetLabel } = selection;
  const amount = edgeLabel(edge.amount, edge.unit);
  const { risk, rest } = splitRisk(edge.details);
  return (
    <div className="pr-6">
      <p>
        <b>{sourceLabel}</b> <span className="text-muted-foreground">— {edge.rel} →</span>{' '}
        <b>{targetLabel}</b>
      </p>
      <h3 className={PANEL_H3}>Risk</h3>
      <DetailsTable details={{ ...(amount ? { amount } : {}), ...risk }} />
      {Object.keys(rest).length ? (
        <>
          <h3 className={PANEL_H3}>Details</h3>
          <DetailsTable details={rest} />
        </>
      ) : null}
    </div>
  );
}
