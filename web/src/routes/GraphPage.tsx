import { useMemo, useState } from 'react';
import { useGraph } from '../api/hooks';
import { GRAPH_NODE_KINDS } from '../api/types';
import type { GraphNodeKind } from '../api/types';
import { GraphCanvas } from '../components/GraphCanvas';
import type { GraphSelection } from '../components/GraphCanvas';
import { DetailsTable } from '../components/DetailsTable';
import { ErrorState, Loading } from '../components/States';
import { KIND_COLOR, KIND_DESCRIPTION } from '../lib/graph';
import { edgeLabel } from '../lib/graph';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const ASIDE_SUB = 'mb-3.5 text-[0.82rem] text-muted-foreground';
const ASIDE_H3 = 'mt-5.5 mb-1 text-[0.82rem] font-bold text-muted-foreground';
const ASIDE_LIST = 'grid max-w-measure list-disc gap-2 pl-[1.1em] text-[0.84rem]';

export function GraphPage() {
  const { data, isPending, error } = useGraph();
  const [hiddenKinds, setHiddenKinds] = useState<ReadonlySet<GraphNodeKind>>(new Set());
  const [search, setSearch] = useState('');
  const [selection, setSelection] = useState<GraphSelection>(null);
  const [fitNonce, setFitNonce] = useState(0);
  const [layoutNonce, setLayoutNonce] = useState(0);

  const counts = useMemo(() => {
    const result = new Map<GraphNodeKind, number>();
    for (const node of data?.nodes ?? []) {
      result.set(node.kind, (result.get(node.kind) ?? 0) + 1);
    }
    return result;
  }, [data]);

  const visibleKinds = useMemo(
    () => new Set(GRAPH_NODE_KINDS.filter((kind) => !hiddenKinds.has(kind))),
    [hiddenKinds],
  );

  if (isPending) return <Loading what="the dependency graph" />;
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
    <div className="grid h-[calc(100vh-53px)] grid-cols-[340px_1fr] max-[860px]:h-auto max-[860px]:grid-cols-1 max-[860px]:grid-rows-[auto_70vh]">
      <aside className="overflow-auto border-r border-border p-5.5 max-[860px]:border-r-0 max-[860px]:border-b [&_h2]:mt-9">
        <h1 className="text-[1.05rem]">{data.title}</h1>
        {/* The subtitle is the provenance line: chain, block, how it was read. */}
        <p className={ASIDE_SUB}>{data.subtitle}</p>

        <h2>Node types</h2>
        <div>
          {GRAPH_NODE_KINDS.filter((kind) => (counts.get(kind) ?? 0) > 0).map((kind) => (
            // The control and the colour key line up with the first line of the
            // label, not with the middle of a description that wraps.
            <Label
              key={kind}
              className="my-3.5 flex cursor-pointer items-start gap-2 text-[0.85rem] font-normal"
            >
              <Checkbox
                className="mt-[0.28em]"
                checked={!hiddenKinds.has(kind)}
                onCheckedChange={() => toggleKind(kind)}
              />
              {/* The one place a colour chip is content: it keys the node colour
                  in the canvas, alongside the shape that repeats it. */}
              <span
                className="mt-[0.28em] size-[11px] shrink-0"
                style={{ background: KIND_COLOR[kind] }}
              />
              <span>
                <b>{kind}</b>{' '}
                <span className="text-muted-foreground">
                  ({counts.get(kind)}) {KIND_DESCRIPTION[kind]}
                </span>
              </span>
            </Label>
          ))}
        </div>
        <p className={ASIDE_SUB}>
          Shape repeats the colour: rounded box Actor, ellipse Pool, tag Asset, diamond Oracle,
          triangle Admin, square External. Edge width grows with the amount carried (log scale, in
          the edge's token). Click a node to isolate its neighbours.
        </p>

        <h2>Find</h2>
        <Label htmlFor="graph-search" className="sr-only">
          Filter nodes by symbol, address or market id
        </Label>
        <Input
          id="graph-search"
          type="search"
          placeholder="symbol, address, market id…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <div className="mt-3.5 flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setFitNonce((n) => n + 1)}
          >
            Fit
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setLayoutNonce((n) => n + 1)}
          >
            Re-layout
          </Button>
        </div>

        <h2>Selection</h2>
        <SelectionPanel selection={selection} />
      </aside>

      <GraphCanvas
        nodes={data.nodes}
        edges={data.edges}
        visibleKinds={visibleKinds}
        search={search}
        onSelect={setSelection}
        fitNonce={fitNonce}
        layoutNonce={layoutNonce}
      />
    </div>
  );
}

function SelectionPanel({ selection }: { selection: GraphSelection }) {
  if (!selection) return <p className="text-muted-foreground">Click a node or an edge.</p>;

  if (selection.type === 'node') {
    const { node, incoming, outgoing } = selection;
    return (
      <div>
        <p>
          <b>{node.label}</b> <span className="text-muted-foreground">{node.kind}</span>
        </p>
        <DetailsTable details={node.details} />
        {outgoing.length > 0 ? (
          <>
            <h3 className={ASIDE_H3}>Outgoing</h3>
            <ul className={ASIDE_LIST}>
              {outgoing.map((line) => (
                <li key={`out-${line}`}>{line}</li>
              ))}
            </ul>
          </>
        ) : null}
        {incoming.length > 0 ? (
          <>
            <h3 className={ASIDE_H3}>Incoming</h3>
            <ul className={ASIDE_LIST}>
              {incoming.map((line) => (
                <li key={`in-${line}`}>{line}</li>
              ))}
            </ul>
          </>
        ) : null}
      </div>
    );
  }

  const { edge, sourceLabel, targetLabel } = selection;
  const amount = edgeLabel(edge.amount, edge.unit);
  return (
    <div>
      <p>
        <b>{sourceLabel}</b> <span className="text-muted-foreground">— {edge.rel} →</span>{' '}
        <b>{targetLabel}</b>
      </p>
      <DetailsTable details={{ ...(amount ? { amount } : {}), ...edge.details }} />
    </div>
  );
}
