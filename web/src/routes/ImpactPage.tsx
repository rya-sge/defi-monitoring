import { useMemo, useState } from 'react';
import { useShockTrace } from '../api/hooks';
import { GRAPH_NODE_KINDS } from '../api/types';
import type { ShockStatus, ShockTrace } from '../api/types';
import { GraphCanvas } from '../components/GraphCanvas';
import type { GraphSelection } from '../components/GraphCanvas';
import { ErrorState, Loading } from '../components/States';
import { edgeId } from '../lib/graph';
import { usd, detailValue, num, percent } from '../lib/format';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

/**
 * The impact of a shock (`riskdep shock`'s trace, `docs/model/shock-trace.md`): a summary and
 * the graph. The data is the committed example trace.
 */

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

export function ImpactPage() {
  const { data, isPending, error } = useShockTrace();
  if (isPending) return <Loading what="the shock trace" />;
  if (error) return <ErrorState what="the shock trace" error={error} />;

  const label = (id: string) => data.graph.nodes.find((node) => node.id === id)?.label ?? id;

  return (
    <div className="flex h-full flex-col px-5.5 pt-5.5">
      <header className="mb-3.5">
        <h1>Impact</h1>
        <p className="text-muted-foreground">
          {data.shocks.map((shock) => shock.label).join(' + ')} · block {data.block} ·{' '}
          {data.converged ? 'converged' : 'not converged: numbers are not final'} · example trace
        </p>
      </header>
      <Tabs defaultValue="summary" className="min-h-0 flex-1">
        <TabsList>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="graph">Graph</TabsTrigger>
        </TabsList>
        <TabsContent value="summary" className="overflow-auto pb-9">
          <Summary trace={data} label={label} />
        </TabsContent>
        <TabsContent value="graph" className="relative min-h-[60vh]">
          <ImpactGraph trace={data} label={label} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

type ViewProps = { trace: ShockTrace; label: (id: string) => string };

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

function Summary({ trace, label }: ViewProps) {
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
            <b>{label(id)}</b> {state.headline}
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

function ImpactGraph({ trace, label }: ViewProps) {
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

  const selected = selection?.type === 'node' ? selection.node.id : null;
  const state = selected ? trace.nodes[selected] : null;

  return (
    <>
      <GraphCanvas
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
            {state ? `${state.status}: ${state.headline}` : 'not reached by the shock'}
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
