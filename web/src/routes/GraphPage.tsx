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
    <div className="graph-layout">
      <aside className="graph-aside">
        <h1>{data.title}</h1>
        {/* The subtitle is the provenance line: chain, block, how it was read. */}
        <p className="block-sub">{data.subtitle}</p>

        <h2>Node types</h2>
        <div className="legend">
          {GRAPH_NODE_KINDS.filter((kind) => (counts.get(kind) ?? 0) > 0).map((kind) => (
            <label key={kind}>
              <input
                type="checkbox"
                checked={!hiddenKinds.has(kind)}
                onChange={() => toggleKind(kind)}
              />
              <span className="swatch" style={{ background: KIND_COLOR[kind] }} />
              <b>{kind}</b>
              <span className="muted">
                ({counts.get(kind)}) {KIND_DESCRIPTION[kind]}
              </span>
            </label>
          ))}
        </div>
        <p className="block-sub">
          Shape repeats the colour: rounded box Actor, ellipse Pool, tag Asset, diamond Oracle,
          triangle Admin, square External. Edge width grows with the amount carried (log scale, in
          the edge's token). Click a node to isolate its neighbours.
        </p>

        <h2>Find</h2>
        <label className="visually-hidden" htmlFor="graph-search">
          Filter nodes by symbol, address or market id
        </label>
        <input
          id="graph-search"
          type="search"
          placeholder="symbol, address, market id…"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <div className="graph-actions">
          <button type="button" onClick={() => setFitNonce((n) => n + 1)}>
            Fit
          </button>
          <button type="button" onClick={() => setLayoutNonce((n) => n + 1)}>
            Re-layout
          </button>
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
  if (!selection) return <p className="muted">Click a node or an edge.</p>;

  if (selection.type === 'node') {
    const { node, incoming, outgoing } = selection;
    return (
      <div>
        <p>
          <b>{node.label}</b> <span className="muted">{node.kind}</span>
        </p>
        <DetailsTable details={node.details} />
        {outgoing.length > 0 ? (
          <>
            <h3>Outgoing</h3>
            <ul className="reasons">
              {outgoing.map((line) => (
                <li key={`out-${line}`}>{line}</li>
              ))}
            </ul>
          </>
        ) : null}
        {incoming.length > 0 ? (
          <>
            <h3>Incoming</h3>
            <ul className="reasons">
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
        <b>{sourceLabel}</b> <span className="muted">— {edge.rel} →</span> <b>{targetLabel}</b>
      </p>
      <DetailsTable details={{ ...(amount ? { amount } : {}), ...edge.details }} />
    </div>
  );
}
