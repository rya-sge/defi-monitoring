import { FormattedText } from './FormattedText';
import { useMemo } from 'react';
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TooltipContentProps } from 'recharts';
import type { Liquidation } from '../api/types';
import { compactUsd, percent, usd } from '../lib/format';

const STEP = 0.005;
const MAX = 0.3;

const TOOLTIP = 'tooltip-surface max-w-80 tabular-nums';
// No axis line, no tick marks, small faint labels: the bars carry the chart.
const AXIS = {
  axisLine: false,
  tickLine: false,
  tick: { fontSize: 10, fill: 'var(--muted)', fillOpacity: 0.7 },
} as const;

type Datum = { drop: number; debt: number; cumulative: number };

/** Debt liquidated per 0.5 % of oracle fall (bars) and its running total (line), up to a 30 % fall. */
export function LiquidationChart({
  liquidations,
  price,
}: {
  liquidations: Liquidation[];
  /** The collateral's price, when there is one: the tooltip then shows the liquidating price. */
  price?: number | null;
}) {
  const data = useMemo<Datum[]>(() => {
    const buckets = Array.from({ length: Math.round(MAX / STEP) + 1 }, (_, i) => ({
      drop: i * STEP,
      debt: 0,
      cumulative: 0,
    }));
    for (const { drop, debt_usd } of liquidations) {
      const bucket = buckets[Math.ceil(drop / STEP - 1e-9)];
      if (bucket) bucket.debt += debt_usd;
    }
    let total = 0;
    for (const bucket of buckets) bucket.cumulative = total += bucket.debt;
    return buckets;
  }, [liquidations]);

  return (
    <div>
      <h3>Liquidations by collateral price drop</h3>
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
            tickFormatter={(v: number) => `−${percent(v)}`}
          />
          {/* Two scales on purpose: the running total dwarfs any one bucket. Left = bars, right = line. */}
          <YAxis yAxisId="debt" {...AXIS} tickFormatter={(v: number) => compactUsd(v)} width={62} />
          <YAxis
            yAxisId="cumulative"
            orientation="right"
            {...AXIS}
            tickFormatter={(v: number) => compactUsd(v)}
            width={62}
          />
          <Tooltip content={(props) => <LiqTooltip {...props} price={price} />} cursor={false} />
          <Bar
            yAxisId="debt"
            dataKey="debt"
            fill="var(--chart-1)"
            activeBar={false}
            radius={[2, 2, 0, 0]}
            isAnimationActive={false}
          />
          <Line
            yAxisId="cumulative"
            dataKey="cumulative"
            type="stepAfter"
            stroke="var(--chart-2)"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function LiqTooltip({ active, payload, price }: TooltipContentProps & { price?: number | null }) {
  if (!active || !payload?.length) return null;
  const datum = payload[0].payload as Datum;
  return (
    <div className={TOOLTIP}>
      <strong>
        <FormattedText>{`Price −${percent(datum.drop)}${price != null ? ` · ${usd(price * (1 - datum.drop), 2)}` : ''}`}</FormattedText>
      </strong>
      <br />
      <div className="flex items-center gap-2">
        <span className="size-2 rounded-full bg-[var(--chart-1)]" />
        <FormattedText>{usd(datum.debt)}</FormattedText> liquidated here
      </div>
      <br />
      <div className="flex items-center gap-2">
        <span className="size-2 rounded-full bg-[var(--chart-2)]" />
        <FormattedText>{usd(datum.cumulative)}</FormattedText> cumulated
      </div>
    </div>
  );
}
