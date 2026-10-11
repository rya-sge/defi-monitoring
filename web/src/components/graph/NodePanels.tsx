import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { GraphNode } from '../../api/types';
import { CHART_COLORS } from '../../lib/charts';
import { compactNum, compactUsd, detailValue, percent, usd } from '../../lib/format';
import { ChartTooltip } from '../ChartTooltip';
import { DetailsTable } from '../DetailsTable';

const H3 = 'mt-5.5 mb-1 text-[0.82rem] font-bold text-muted-foreground';

type CurvePoint = { oracle_fall: number; liquidatable_debt: number; bad_debt: number };

const num = (v: unknown) => (typeof v === 'number' ? v : null);
const text = (v: unknown) => (v == null || v === '' ? null : detailValue(v));

/** The keys a typed panel shows, left out of the raw details below it. */
const TYPED = new Set([
  'liquidation_curve',
  'unrealised_bad_debt',
  'utilization',
  'total_borrow',
  'lltv',
  'oracle_class',
  'liquidity_usd',
  'impact_curve',
  'capacity_usd',
  'pharos_grade',
  'supply_text',
  'constant_kind',
  'freshness',
  'stale',
  'shared_text',
  'tracks_market',
  'class_basis',
  'concentration',
  'tvl_usd',
  'share_of_defi',
  'share_of_category',
  'rank_in_category',
  'category',
  'concentrated',
]);

function Facts({ rows }: { rows: [string, string | null][] }) {
  const kept = rows.filter((r): r is [string, string] => r[1] != null);
  return kept.length ? <DetailsTable details={Object.fromEntries(kept)} /> : null;
}

function LiquidationCurve({ curve, unit }: { curve: CurvePoint[]; unit: string }) {
  return (
    <div className="h-40">
      <ResponsiveContainer>
        <LineChart data={curve} margin={{ top: 6, right: 6, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis
            dataKey="oracle_fall"
            tickFormatter={(v: number) => `−${percent(v)}`}
            tick={{ fontSize: 11 }}
          />
          <YAxis tickFormatter={(v: number) => compactNum(v)} tick={{ fontSize: 11 }} width={44} />
          <Tooltip
            content={(props) => (
              <ChartTooltip
                {...props}
                formatLabel={(v) => `Oracle −${percent(Number(v))}`}
                formatValue={(v) => `${compactNum(v)} ${unit}`}
              />
            )}
          />
          <Line
            name="Liquidatable debt"
            dataKey="liquidatable_debt"
            stroke={CHART_COLORS[0]}
            dot={false}
            strokeWidth={2}
          />
          <Line
            name="Bad debt"
            dataKey="bad_debt"
            stroke={CHART_COLORS[2]}
            dot={false}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function ImpactCurve({ curve }: { curve: [number, number][] }) {
  const data = curve.map(([size, kept]) => ({ size, slippage: 1 - kept }));
  return (
    <div className="h-40">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 6, right: 6, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis dataKey="size" tickFormatter={compactUsd} tick={{ fontSize: 11 }} />
          <YAxis
            tickFormatter={(v: number) => `${(v * 100).toFixed(1)}%`}
            tick={{ fontSize: 11 }}
            width={44}
          />
          <Tooltip
            content={(props) => (
              <ChartTooltip
                {...props}
                formatLabel={(v) => `Sell ${compactUsd(Number(v))}`}
                formatValue={(v) => `${(v * 100).toFixed(2)}%`}
              />
            )}
          />
          <Line
            name="Slippage"
            dataKey="slippage"
            stroke={CHART_COLORS[3]}
            dot={false}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/** A node's risk read by kind, with a chart where the backend gives a curve; the raw rest below. */
export function NodePanel({ node, labelOf }: { node: GraphNode; labelOf: (id: string) => string }) {
  const d = node.details;
  const loan = detailValue(d.loan_unit);
  const curve = Array.isArray(d.liquidation_curve) ? (d.liquidation_curve as CurvePoint[]) : [];
  const impact = Array.isArray(d.impact_curve) ? (d.impact_curve as [number, number][]) : [];
  const rest = Object.fromEntries(
    Object.entries(d).filter(([k, v]) => !TYPED.has(k) && !Array.isArray(v) && k !== '_positions'),
  );
  return (
    <>
      {node.kind === 'Pool' ? (
        <>
          <Facts
            rows={[
              ['LLTV', text(d.lltv)],
              ['Utilization', text(d.utilization)],
              [
                'Total borrow',
                num(d.total_borrow) != null ? `${compactNum(num(d.total_borrow))} ${loan}` : null,
              ],
              [
                'Unrealised bad debt',
                num(d.unrealised_bad_debt) != null
                  ? `${compactNum(num(d.unrealised_bad_debt))} ${loan}`
                  : null,
              ],
              ['Oracle', text(d.oracle_class)],
            ]}
          />
          {curve.length ? (
            <>
              <h3 className={H3}>Liquidations by oracle fall</h3>
              <LiquidationCurve curve={curve} unit={loan} />
            </>
          ) : null}
        </>
      ) : null}
      {node.kind === 'Asset' ? (
        <>
          <Facts
            rows={[
              ['Pharos grade', text(d.pharos_grade)],
              ['Exit capacity', num(d.capacity_usd) != null ? usd(num(d.capacity_usd)) : null],
              ['Supply in Morpho', text(d.supply_text)],
            ]}
          />
          {impact.length ? (
            <>
              <h3 className={H3}>Exit slippage by size</h3>
              <ImpactCurve curve={impact} />
            </>
          ) : null}
        </>
      ) : null}
      {node.kind === 'Oracle' ? (
        <Facts
          rows={[
            ['Class', text(d.oracle_class)],
            ['Kind', text(d.constant_kind)],
            ['Freshness', text(d.freshness)],
            ['Stale', d.stale == null ? null : d.stale ? 'yes' : 'no'],
            ['Shared', text(d.shared_text)],
            ['Tracks', typeof d.tracks_market === 'string' ? labelOf(d.tracks_market) : null],
            ['Basis', text(d.class_basis)],
          ]}
        />
      ) : null}
      {node.kind === 'External' ? (
        <Facts
          rows={[
            ['Concentration', text(d.concentration)],
            ['TVL', num(d.tvl_usd) != null ? usd(num(d.tvl_usd), 0) : null],
            ['Share of DeFi', num(d.share_of_defi) != null ? percent(num(d.share_of_defi)) : null],
            [
              'Share of category',
              num(d.share_of_category) != null ? percent(num(d.share_of_category)) : null,
            ],
          ]}
        />
      ) : null}
      <h3 className={H3}>Details</h3>
      <DetailsTable details={rest} />
    </>
  );
}
