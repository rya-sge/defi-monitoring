import { useMemo, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Sankey,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useShockTrace } from '../api/hooks';
import { GRAPH_NODE_KINDS } from '../api/types';
import type { ShockStatus, ShockTrace } from '../api/types';
import { GraphCanvas } from '../components/GraphCanvas';
import type { GraphSelection } from '../components/GraphCanvas';
import { ErrorState, Loading } from '../components/States';
import { compactNum, compactUsd, detailValue, num, percent } from '../lib/format';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

/**
 * The impact of a shock (`riskdep shock`'s trace, `docs/shock-trace.md`), one view per tab.
 * A first, minimal pass to compare the views: the data is the committed example trace.
 */

/** Severity colour of a reached node's ring; the status is always written out too. */
const STATUS_RING: Record<ShockStatus, string> = {
  shocked: 'var(--critical)',
  loss: 'var(--warn)',
  liquidations: 'var(--warn)',
  moved: 'var(--info)',
  reached: 'var(--muted)',
};

const AXIS = {
  axisLine: false,
  tickLine: false,
  tick: { fontSize: 10, fill: 'var(--muted)' },
} as const;

const ALL_KINDS = new Set(GRAPH_NODE_KINDS);

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
          <TabsTrigger value="path">Path</TabsTrigger>
          <TabsTrigger value="flow">Flow</TabsTrigger>
          <TabsTrigger value="waves">Waves</TabsTrigger>
          <TabsTrigger value="matrix">Matrix</TabsTrigger>
        </TabsList>
        <TabsContent value="summary" className="overflow-auto pb-9">
          <Summary trace={data} label={label} />
        </TabsContent>
        <TabsContent value="graph" className="relative min-h-[60vh]">
          <ImpactGraph trace={data} label={label} />
        </TabsContent>
        <TabsContent value="path" className="overflow-auto pb-9">
          <LossPath trace={data} label={label} />
        </TabsContent>
        <TabsContent value="flow" className="overflow-auto pb-9">
          <SaleFlow trace={data} label={label} />
        </TabsContent>
        <TabsContent value="waves" className="overflow-auto pb-9">
          <Waves trace={data} label={label} />
        </TabsContent>
        <TabsContent value="matrix" className="overflow-auto pb-9">
          <Matrix trace={data} label={label} />
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
  const markets = entries.filter(([, state]) => state.model === 'blue_market');
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
              <TableHead>Market</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Oracle ×</TableHead>
              <TableHead className="text-right">Market ×</TableHead>
              <TableHead className="text-right">Liquidated</TableHead>
              <TableHead className="text-right">Positions</TableHead>
              <TableHead className="text-right">Write-off</TableHead>
              <TableHead className="text-right">Insolvent</TableHead>
              <TableHead className="text-right">Drained</TableHead>
              <TableHead className="text-right">Lenders lose</TableHead>
              <TableHead className="text-right">Sold $</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody className="tabular-nums">
            {markets.map(([id, { status, detail: d }]) => (
              <TableRow key={id}>
                <TableCell>{label(id)}</TableCell>
                <TableCell>{status}</TableCell>
                <TableCell className="text-right">{num(n(d.oracle_factor), 3)}</TableCell>
                <TableCell className="text-right">{num(n(d.market_factor), 3)}</TableCell>
                <TableCell className="text-right">{compactNum(n(d.liquidated_debt))}</TableCell>
                <TableCell className="text-right">{n(d.positions_liquidated)}</TableCell>
                <TableCell className="text-right">{compactNum(n(d.bad_debt))}</TableCell>
                <TableCell className="text-right">{compactNum(n(d.insolvent))}</TableCell>
                <TableCell className="text-right">{compactNum(n(d.drained))}</TableCell>
                <TableCell className="text-right font-semibold">
                  {compactNum(n(d.lender_loss))} {detailValue(d.loan_unit)}
                </TableCell>
                <TableCell className="text-right">{compactUsd(n(d.collateral_sold_usd))}</TableCell>
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
                <TableCell className="text-right">{compactUsd(n(d.sold_usd))}</TableCell>
                <TableCell className="text-right">{compactUsd(n(d.absorbed_usd))}</TableCell>
                <TableCell className="text-right">
                  {percent(n(d.absorbed_usd) / (n(d.sold_usd) || 1), 0)}
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
  const { focus, overlay } = useMemo(() => {
    const overlay = Object.fromEntries(
      Object.entries(trace.nodes).map(([id, state]) => {
        const loss = state.status === 'loss' ? finalLoss(trace, id) : null;
        return [id, { ring: STATUS_RING[state.status], amount: loss ? [loss] : [state.status] }];
      }),
    );
    const focus = {
      nodes: new Set(Object.keys(trace.nodes)),
      edges: new Set(trace.steps.map((step) => step.edge)),
    };
    return { focus, overlay };
  }, [trace]);

  const selected = selection?.type === 'node' ? selection.node.id : null;
  const state = selected ? trace.nodes[selected] : null;

  return (
    <>
      <GraphCanvas
        nodes={trace.graph.nodes}
        edges={trace.graph.edges}
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
  if (steps.length) return `−${compactNum(total)} ${steps[0].unit}`;
  const own = trace.nodes[id];
  return own.detail.lender_loss != null
    ? `−${compactNum(n(own.detail.lender_loss))} ${own.loss_unit ?? ''}`
    : null;
}

/* ------------------------------------------------------------------- path */

function LossPath({ trace, label }: ViewProps) {
  const losers = Object.keys(trace.paths);
  const [target, setTarget] = useState(losers.at(-1) ?? '');
  const steps = (trace.paths[target] ?? []).map((seq) => trace.steps[seq - 1]);

  return (
    <div className="grid max-w-3xl gap-5.5">
      <Select value={target} onValueChange={setTarget}>
        <SelectTrigger className="w-96">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {losers.map((id) => (
            <SelectItem key={id} value={id}>
              {label(id)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p className="text-muted-foreground">{trace.nodes[target]?.headline}</p>
      <ol className="grid gap-3.5 border-l pl-5.5">
        {steps.map((step) => (
          <li key={step.seq} title={trace.rules[step.rule]?.basis}>
            <div className="text-[0.8rem] text-muted-foreground">
              wave {step.wave} · {step.rule}
            </div>
            <div>
              {label(step.source)} → <b>{label(step.target)}</b>
            </div>
            <div className="tabular-nums">{step.display}</div>
          </li>
        ))}
      </ol>
    </div>
  );
}

/* ------------------------------------------------------------------- flow */

/** Where the liquidation sales go: sellers → assets → absorbed or not sold. In USD. */
function SaleFlow({ trace, label }: ViewProps) {
  const data = useMemo(() => {
    const names: string[] = [];
    const index = (name: string) => {
      if (!names.includes(name)) names.push(name);
      return names.indexOf(name);
    };
    const links: { source: number; target: number; value: number }[] = [];
    for (const step of finalSteps(trace)) {
      if (step.effect !== 'sale' && step.effect !== 'onward') continue;
      links.push({
        source: index(label(step.source)),
        target: index(label(step.target)),
        value: n(step.value),
      });
    }
    for (const [id, state] of Object.entries(trace.nodes)) {
      const sold = n(state.detail.sold_usd);
      const absorbed = n(state.detail.absorbed_usd);
      if (!sold || absorbed >= sold) continue;
      links.push({ source: index(label(id)), target: index('absorbed'), value: absorbed });
      links.push({ source: index(label(id)), target: index('not sold'), value: sold - absorbed });
    }
    return { nodes: names.map((name) => ({ name })), links };
  }, [trace, label]);

  return (
    <div className="h-[460px] max-w-5xl">
      <ResponsiveContainer width="100%" height="100%">
        <Sankey
          data={data}
          nodePadding={36}
          margin={{ top: 10, right: 160, bottom: 10, left: 10 }}
          link={{ stroke: 'var(--edge)', strokeOpacity: 0.35 }}
          node={<SankeyNode />}
        >
          <Tooltip formatter={(value) => compactUsd(Number(value))} />
        </Sankey>
      </ResponsiveContainer>
    </div>
  );
}

type SankeyNodeProps = {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  payload?: { name: string; value: number };
};

function SankeyNode({ x = 0, y = 0, width = 0, height = 0, payload }: SankeyNodeProps) {
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} rx={2} fill="var(--fg)" fillOpacity={0.6} />
      <text
        x={x + width + 6}
        y={y + height / 2}
        dominantBaseline="middle"
        fontSize={11}
        fill="var(--fg)"
      >
        {payload?.name} · {compactUsd(payload?.value ?? 0)}
      </text>
    </g>
  );
}

/* ------------------------------------------------------------------ waves */

/** Each loss as the loop computed it, round by round: early rounds overshoot. */
function Waves({ trace, label }: ViewProps) {
  const [wave, setWave] = useState(trace.waves.length - 1);
  const losers = Object.keys(trace.paths);
  const series = trace.waves.map(({ wave: w }) => {
    const point: Record<string, number> = { wave: w };
    for (const id of losers) {
      const entry = trace.evaluations_log.filter((e) => e.node === id && e.wave <= w).at(-1);
      point[id] = entry ? lossOf(entry.detail, trace, id, w) : 0;
    }
    return point;
  });
  const states = reached(trace).map(([id]) => ({
    id,
    entry: trace.evaluations_log.filter((e) => e.node === id && e.wave <= wave).at(-1),
  }));

  return (
    <div className="grid max-w-5xl gap-9">
      <p className="text-muted-foreground">{trace.note}</p>
      <div className="h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={series} margin={{ left: 10, right: 20 }}>
            <CartesianGrid stroke="var(--line)" vertical={false} />
            <XAxis dataKey="wave" {...AXIS} />
            <YAxis {...AXIS} tickFormatter={(v: number) => compactNum(v)} width={50} />
            <Tooltip formatter={(value) => compactNum(Number(value))} />
            {losers.map((id, i) => (
              <Line
                key={id}
                dataKey={id}
                name={label(id)}
                stroke="var(--fg)"
                strokeOpacity={1 - i * 0.3}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => setWave((w) => Math.max(0, w - 1))}>
          Previous
        </Button>
        <span className="w-28 text-center tabular-nums">
          round {wave} / {trace.waves.length - 1}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setWave((w) => Math.min(trace.waves.length - 1, w + 1))}
        >
          Next
        </Button>
      </div>
      <Table>
        <TableBody>
          {states.map(({ id, entry }) => (
            <TableRow key={id}>
              <TableCell className="w-72">{label(id)}</TableCell>
              <TableCell className="w-28 text-muted-foreground">
                {entry?.status ?? 'not yet'}
              </TableCell>
              <TableCell className="whitespace-normal">{entry?.headline}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

/** A node's loss at round `w`: a market's own lender loss, else the last loss step it received. */
function lossOf(detail: Record<string, unknown>, trace: ShockTrace, id: string, w: number): number {
  if (detail.lender_loss != null) return n(detail.lender_loss);
  const step = trace.steps
    .filter((s) => s.target === id && s.effect === 'loss' && s.wave <= w)
    .at(-1);
  return n(step?.value);
}

/* ----------------------------------------------------------------- matrix */

/** Rows: reached nodes. Columns: rounds. A cell: the node's status when it was evaluated then. */
function Matrix({ trace, label }: ViewProps) {
  const rounds = trace.waves.map((w) => w.wave);
  return (
    <Table className="w-auto">
      <TableHeader>
        <TableRow>
          <TableHead>Node</TableHead>
          {rounds.map((w) => (
            <TableHead key={w} className="w-10 text-center tabular-nums">
              {w}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {reached(trace).map(([id]) => (
          <TableRow key={id}>
            <TableCell>{label(id)}</TableCell>
            {rounds.map((w) => {
              const entry = trace.evaluations_log
                .filter((e) => e.node === id && e.wave === w)
                .at(-1);
              return (
                <TableCell
                  key={w}
                  title={entry?.headline}
                  className="text-center text-[0.75rem]"
                  style={{
                    background: entry
                      ? `color-mix(in srgb, ${STATUS_RING[entry.status]} 18%, transparent)`
                      : undefined,
                  }}
                >
                  {entry ? entry.status.slice(0, 4) : ''}
                </TableCell>
              );
            })}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
