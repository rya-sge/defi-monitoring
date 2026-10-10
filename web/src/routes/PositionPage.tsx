import { useMemo } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TooltipContentProps } from 'recharts';
import { useReport } from '../api/hooks';
import { ErrorState, Loading } from '../components/States';
import { StatRow } from '../components/Stat';
import type { StatProps } from '../components/Stat';
import type { Liquidation, Report, SimulationLayer } from '../api/types';
import { compactUsd, days, num, percent, usd } from '../lib/format';

const BLOCKS = 'grid grid-cols-[repeat(auto-fit,minmax(min(400px,100%),1fr))] gap-x-14 gap-y-9';
const TOOLTIP =
  'max-w-[320px] rounded-md border bg-popover p-2 text-[0.82rem] text-popover-foreground tabular-nums shadow-md';
// No axis line, no tick marks, small faint labels: the bars carry the chart.
const AXIS = {
  axisLine: false,
  tickLine: false,
  tick: { fontSize: 10, fill: 'var(--muted)', fillOpacity: 0.7 },
} as const;

const VERDICT_TONE: Record<string, string> = {
  STAY: 'text-ok',
  REDUCE: 'text-warn',
  EXIT: 'text-critical',
};

export function PositionPage() {
  const { data, isPending, error } = useReport();

  if (isPending) return <Loading what="the report" />;
  if (error) return <ErrorState what="the report" error={error} />;
  if (!data) return <ErrorState what="the report" error="empty response" />;

  return <PositionView report={data} />;
}

function PositionView({ report }: { report: Report }) {
  const { position, decision, simulation } = report;

  const stats = useMemo<StatProps[]>(() => {
    const hf = position.health_factor;
    const hfTone: StatProps['tone'] =
      hf == null ? 'neutral' : hf <= 1.02 ? 'critical' : hf <= 1.1 ? 'warn' : 'ok';
    const dropTone: StatProps['tone'] =
      position.liquidation_drop == null
        ? 'neutral'
        : position.liquidation_drop < decision.stress_drop
          ? 'warn'
          : 'ok';

    return [
      {
        label: 'Health factor',
        value: num(hf, 3),
        note: `LLTV ${percent(position.lltv, 1)}`,
        tone: hfTone,
      },
      { label: 'Liquidating fall', value: percent(position.liquidation_drop), tone: dropTone },
      { label: 'Equity', value: compactUsd(position.equity_usd) },
      { label: 'Expected loss', value: compactUsd(simulation.expected_loss_usd) },
      { label: 'CVaR 99', value: compactUsd(simulation.cvar99_usd) },
      { label: 'Exit cost', value: compactUsd(decision.exit_cost_usd) },
      { label: 'Maturity', value: days(position.days_to_maturity) },
    ];
  }, [position, decision, simulation]);

  return (
    <div className="mx-auto grid max-w-[1120px] gap-10 px-5.5 pt-9 pb-14">
      <header className="flex items-baseline justify-between gap-6">
        <h1 className="m-0 truncate">{position.label}</h1>
        <div
          className={`text-3xl leading-none font-extrabold tracking-[-0.03em] ${VERDICT_TONE[decision.verdict]}`}
        >
          {decision.verdict}
        </div>
      </header>

      <StatRow items={stats} />

      <LiquidationChart
        liquidations={position.liquidations}
        price={position.pt_price_usd}
        own={position.liquidation_drop}
      />

      <div className={BLOCKS}>
        <LayerContributionChart layers={simulation.layers} />
        <TailChart report={report} />
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------- charts */

const LIQ_STEP = 0.005;
const LIQ_MAX = 0.3;

type LiqDatum = { drop: number; debt: number; cumulative: number };

/** Debt of every borrower of the market, by the oracle fall that liquidates it, and its running total. */
function LiquidationChart({
  liquidations,
  price,
  own,
}: {
  liquidations: Liquidation[];
  price: number | null;
  own: number | null;
}) {
  const data = useMemo<LiqDatum[]>(() => {
    const buckets = Array.from({ length: Math.round(LIQ_MAX / LIQ_STEP) + 1 }, (_, i) => ({
      drop: i * LIQ_STEP,
      debt: 0,
      cumulative: 0,
    }));
    for (const { drop, debt_usd } of liquidations) {
      const bucket = buckets[Math.ceil(drop / LIQ_STEP - 1e-9)];
      if (bucket) bucket.debt += debt_usd;
    }
    let total = 0;
    for (const bucket of buckets) bucket.cumulative = total += bucket.debt;
    return buckets;
  }, [liquidations]);

  return (
    <div>
      <h3>Liquidations by oracle fall</h3>
      <ResponsiveContainer width="100%" height={360}>
        <ComposedChart
          data={data}
          barCategoryGap={1}
          margin={{ left: 8, right: 16, top: 8, bottom: 4 }}
        >
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis
            dataKey="drop"
            {...AXIS}
            interval={9}
            tickFormatter={(v: number) => percent(v, 0)}
          />
          <YAxis {...AXIS} tickFormatter={(v: number) => compactUsd(v)} width={62} />
          <Tooltip
            content={(props) => <LiqTooltip {...props} price={price} />}
            cursor={{ fill: 'var(--line)', opacity: 0.3 }}
          />
          <Bar dataKey="debt" fill="var(--muted)" radius={[2, 2, 0, 0]} isAnimationActive={false} />
          <Line
            dataKey="cumulative"
            type="stepAfter"
            stroke="var(--fg)"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
          {own != null && own <= LIQ_MAX ? (
            <ReferenceLine
              x={Math.ceil(own / LIQ_STEP - 1e-9) * LIQ_STEP}
              stroke="var(--fg)"
              strokeDasharray="3 3"
              label={{
                value: 'this position',
                position: 'insideTopRight',
                fontSize: 10,
                fill: 'var(--muted)',
              }}
            />
          ) : null}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function LiqTooltip({ active, payload, price }: TooltipContentProps & { price: number | null }) {
  if (!active || !payload?.length) return null;
  const datum = payload[0].payload as LiqDatum;
  return (
    <div className={TOOLTIP}>
      <strong>
        fall {percent(datum.drop, 1)}
        {price != null ? ` · ${usd(price * (1 - datum.drop), 4)}` : null}
      </strong>
      <br />
      {usd(datum.debt)} liquidated here
      <br />
      {usd(datum.cumulative)} cumulated
    </div>
  );
}

type LayerDatum = {
  name: string;
  contribution: number;
  layer: SimulationLayer;
};

function LayerContributionChart({ layers }: { layers: SimulationLayer[] }) {
  const data = useMemo<LayerDatum[]>(
    () =>
      [...layers]
        .sort((a, b) => b.contribution_usd - a.contribution_usd)
        .map((layer) => ({ name: layer.layer, contribution: layer.contribution_usd, layer })),
    [layers],
  );

  return (
    <div>
      <h3>Expected loss by layer</h3>
      <ResponsiveContainer width="100%" height={40 + data.length * 44}>
        <BarChart
          data={data}
          layout="vertical"
          barCategoryGap={2}
          margin={{ left: 8, right: 24, top: 4, bottom: 4 }}
        >
          <XAxis type="number" {...AXIS} tickFormatter={(v: number) => compactUsd(v)} />
          <YAxis
            type="category"
            dataKey="name"
            {...AXIS}
            width={196}
            tickFormatter={(v: string) => (v.length > 36 ? `${v.slice(0, 35)}…` : v)}
          />
          <Tooltip
            content={(props) => <LayerTooltip {...props} />}
            cursor={{ fill: 'var(--line)', opacity: 0.3 }}
          />
          <Bar dataKey="contribution" fill="var(--muted)" isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function LayerTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload?.length) return null;
  const datum = payload[0].payload as LayerDatum;
  const { layer } = datum;
  return (
    <div className={TOOLTIP}>
      <strong>{layer.layer}</strong>
      {usd(layer.contribution_usd)} of expected loss
      <br />
      {percent(layer.p_horizon)} chance over the horizon
      <br />
      {usd(layer.standalone_loss_usd)} if it happens
      <br />
      liquidates {percent(layer.liquidation_rate, 0)} of the time
    </div>
  );
}

type TailDatum = { name: string; value: number; note: string };

function TailChart({ report }: { report: Report }) {
  const { simulation, position } = report;
  const data: TailDatum[] = [
    { name: 'VaR 95', value: simulation.var95_usd, note: 'loss the worst 5% starts at' },
    { name: 'CVaR 95', value: simulation.cvar95_usd, note: 'mean loss of the worst 5%' },
    { name: 'VaR 99', value: simulation.var99_usd, note: 'loss the worst 1% starts at' },
    { name: 'CVaR 99', value: simulation.cvar99_usd, note: 'mean loss of the worst 1%' },
  ];

  return (
    <div>
      <h3>Tail measures</h3>
      <ResponsiveContainer width="100%" height={236}>
        <BarChart data={data} barCategoryGap={2} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis dataKey="name" {...AXIS} />
          <YAxis {...AXIS} tickFormatter={(v: number) => compactUsd(v)} width={62} />
          <Tooltip
            content={(props) => <TailTooltip {...props} equity={position.equity_usd} />}
            cursor={{ fill: 'var(--line)', opacity: 0.3 }}
          />
          <Bar dataKey="value" isAnimationActive={false}>
            {data.map((datum) => (
              <Cell
                key={datum.name}
                fill={datum.value >= position.equity_usd ? 'var(--critical)' : 'var(--muted)'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function TailTooltip({ active, payload, equity }: TooltipContentProps & { equity: number }) {
  if (!active || !payload?.length) return null;
  const datum = payload[0].payload as TailDatum;
  return (
    <div className={TOOLTIP}>
      <strong>
        {datum.name}: {usd(datum.value)}
      </strong>
      {datum.note}
      <br />
      {equity > 0 ? `${percent(datum.value / equity, 0)} of equity` : null}
    </div>
  );
}
