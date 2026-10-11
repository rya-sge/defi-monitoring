import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { GRAPH_NODE_KINDS } from '../../api/types';
import type { ShockStatus, ShockTrace } from '../../api/types';
import { GraphCanvas } from '../GraphCanvas';
import type { GraphSelection } from '../GraphCanvas';
import { edgeId, runLayout } from '../../lib/graph';
import { usd, detailValue, num, percent } from '../../lib/format';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Tip } from './IncidentParts';

/** A shock trace (`riskdep shock`, `docs/model/shock-trace.md`): its summary and its graph. */

/** Severity colour of a reached node's ring; the status is always written out too. */
const STATUS_RING: Record<ShockStatus, string> = {
  shocked: 'var(--critical)',
  loss: 'var(--warn)',
  liquidations: 'var(--warn)',
  moved: 'var(--info)',
  reached: 'var(--muted)',
};

const ALL_KINDS = new Set(GRAPH_NODE_KINDS);

/** The markets table's headers and their tooltips (`docs/model/shock-engine.md`). */
const MARKET_COLUMNS = [
  ['Market', 'A Blue market where positions were liquidated or lenders lose'],
  ['Status', 'loss: lenders lose; liquidations: positions liquidated, no loss'],
  ['Lenders lose', 'Written-off, insolvent and drained debt, net of the state before the shock'],
  ['Liquidated', 'Debt repaid by liquidators, in the loan asset'],
  ['Sold $', 'Collateral sold by liquidators, in USD'],
] as const;

const n = (value: unknown) => (typeof value === 'number' ? value : 0);

export type TraceViewProps = { trace: ShockTrace; label: (id: string) => string };

/** Reached nodes, ordered by the wave they were first reached in. */
function reached(trace: ShockTrace) {
  return Object.entries(trace.nodes).sort(
    ([, a], [, b]) => (a.first_wave ?? 0) - (b.first_wave ?? 0),
  );
}

/** Steps no later step revises: the ones whose values still count. */
function finalSteps(trace: ShockTrace) {
  const revised = new Set(trace.steps.map((step) => step.replaces));
  return trace.steps.filter((step) => !revised.has(step.seq));
}

/* ---------------------------------------------------------------- summary */

export function TraceSummary({ trace, label }: TraceViewProps) {
  const entries = reached(trace);
  const markets = entries.filter(
    ([, state]) => state.model === 'blue_market' && state.status !== 'moved',
  );
  const assets = entries.filter(([, state]) => state.model === 'asset_price');
  const losers = entries.filter(
    ([, state]) => state.status === 'loss' && state.model === 'combine',
  );

  return (
    <div className="grid gap-9">
      <ul className="grid gap-1">
        {losers.map(([id, state]) => (
          <li key={id} className="text-lg">
            <b>{label(id)}</b>{' '}
            <Tip label={finalLoss(trace, id) ?? state.status} tip={state.headline} />
          </li>
        ))}
      </ul>

      <section>
        <h2 className="mt-0">Markets</h2>
        <Table>
          <TableHeader>
            <TableRow>
              {MARKET_COLUMNS.map(([name, tip], index) => (
                <TableHead key={name} className={index > 1 ? 'text-right' : undefined}>
                  <Tooltip>
                    <TooltipTrigger className="cursor-help">{name}</TooltipTrigger>
                    <TooltipContent>{tip}</TooltipContent>
                  </Tooltip>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody className="tabular-nums">
            {markets.map(([id, { status, detail: d }]) => (
              <TableRow key={id}>
                <TableCell>{label(id)}</TableCell>
                <TableCell>{status}</TableCell>
                <TableCell className="text-right font-semibold">
                  {num(n(d.lender_loss))} {detailValue(d.loan_unit)}
                </TableCell>
                <TableCell className="text-right">{num(n(d.liquidated_debt))}</TableCell>
                <TableCell className="text-right">{usd(n(d.collateral_sold_usd))}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </section>

      <section>
        <h2 className="mt-0">Sales into assets</h2>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Asset</TableHead>
              <TableHead className="text-right">Offered</TableHead>
              <TableHead className="text-right">Absorbed</TableHead>
              <TableHead className="text-right">Share absorbed</TableHead>
              <TableHead className="text-right">Price ×</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody className="tabular-nums">
            {assets.map(([id, { detail: d }]) => (
              <TableRow key={id}>
                <TableCell>{label(id)}</TableCell>
                <TableCell className="text-right">{usd(n(d.sold_usd))}</TableCell>
                <TableCell className="text-right">{usd(n(d.absorbed_usd))}</TableCell>
                <TableCell className="text-right">
                  {percent(n(d.absorbed_usd) / (n(d.sold_usd) || 1))}
                </TableCell>
                <TableCell className="text-right">{num(n(d.impact), 4)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </section>
    </div>
  );
}

/* ------------------------------------------------------------------ graph */

export function TraceGraph({ trace, label }: TraceViewProps) {
  const [selection, setSelection] = useState<GraphSelection>(null);
  const { nodes, edges, focus, overlay } = useMemo(() => {
    const overlay = Object.fromEntries(
      Object.entries(trace.nodes).map(([id, state]) => {
        const loss = state.status === 'loss' ? finalLoss(trace, id) : null;
        return [id, { ring: STATUS_RING[state.status], amount: loss ? [loss] : [state.status] }];
      }),
    );
    // Only what the shock reaches. A step names its edge by index (`e3`), so the kept edges are
    // renumbered and the steps' edges mapped onto the new indices.
    const reached = new Set(Object.keys(trace.nodes));
    const stepEdges = new Set(trace.steps.map((step) => step.edge));
    const kept = trace.graph.edges
      .map((edge, index) => ({ edge, id: edgeId(index) }))
      .filter(({ edge }) => reached.has(edge.source) && reached.has(edge.target));
    const focus = {
      nodes: reached,
      edges: new Set(kept.flatMap(({ id }, index) => (stepEdges.has(id) ? [edgeId(index)] : []))),
    };
    const nodes = trace.graph.nodes.filter((node) => reached.has(node.id));
    return { nodes, edges: kept.map(({ edge }) => edge), focus, overlay };
  }, [trace]);

  // The same ELK stress layout as the dependency page; ELK is async.
  const positions = useQuery({
    queryKey: ['trace-layout', nodes, edges],
    queryFn: () => runLayout('elk-stress', nodes, edges),
    staleTime: Infinity,
    gcTime: 0,
  });

  const selected = selection?.type === 'node' ? selection.node.id : null;
  const state = selected ? trace.nodes[selected] : null;

  if (!positions.data) return null;
  return (
    <>
      <GraphCanvas
        positions={positions.data}
        flow="free"
        nodes={nodes}
        edges={edges}
        visibleKinds={ALL_KINDS}
        search=""
        selection={selection}
        onSelect={setSelection}
        focus={focus}
        overlay={overlay}
      />
      {selected ? (
        <aside className="absolute top-3.5 right-3.5 w-[320px] rounded-lg border bg-background p-5.5 shadow-sm">
          <p className="mb-1 font-semibold">{label(selected)}</p>
          <p className="text-muted-foreground">
            {state ? (
              <Tip label={finalLoss(trace, selected) ?? state.status} tip={state.headline} />
            ) : (
              'Not reached'
            )}
          </p>
        </aside>
      ) : null}
    </>
  );
}

/** "−6.85k USDC": the last loss step that landed on the node. */
function finalLoss(trace: ShockTrace, id: string): string | null {
  const steps = finalSteps(trace).filter((step) => step.target === id && step.effect === 'loss');
  const total = steps.reduce((sum, step) => sum + n(step.value), 0);
  if (steps.length) return `−${num(total)} ${steps[0].unit}`;
  const own = trace.nodes[id];
  return own.detail.lender_loss != null
    ? `−${num(n(own.detail.lender_loss))} ${own.loss_unit ?? ''}`
    : null;
}
