import type { ReactNode } from 'react';
import { Link } from '@tanstack/react-router';
import { ChevronDown } from 'lucide-react';
import {
  Bar,
  BarChart,
  LabelList,
  Rectangle,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { Conditional, VaultIncident } from '../../api/types';
import { num, percent, usd } from '../../lib/format';
import { pStar } from '../../lib/verdict';
import { ChartTooltip } from '../ChartTooltip';
import { FormattedText } from '../FormattedText';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Table, TableBody, TableCell, TableHead, TableRow } from '@/components/ui/table';
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

/** A label with its explanation on hover. */
export function Tip({ label, tip }: { label: ReactNode; tip: string }) {
  return (
    <HoverTooltip>
      <TooltipTrigger asChild>
        <span className="cursor-help">{label}</span>
      </TooltipTrigger>
      <TooltipContent className="max-w-80 whitespace-pre-line">{tip}</TooltipContent>
    </HoverTooltip>
  );
}

/** Label / value rows, the value right-aligned. */
export function FigureTable({
  rows,
  label,
}: {
  rows: { label: string; tip?: string; value: string; tone?: string }[];
  label: string;
}) {
  return (
    <Table className="tabular-nums" aria-label={label}>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.label}>
            <TableHead scope="row" className="w-full max-w-0 font-normal">
              {row.tip ? <Tip label={row.label} tip={row.tip} /> : row.label}
            </TableHead>
            <TableCell className={`text-right font-medium whitespace-nowrap ${row.tone ?? ''}`}>
              <FormattedText>{row.value}</FormattedText>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

/** The depositor's loss staying, exiting first, and the yield given up by leaving. */
export function LossBars({ vault: v }: { vault: VaultIncident }) {
  const data = [
    { name: 'Stay', value: v.loss_if_stay },
    { name: 'Exit first', value: v.loss_if_exit_first },
    { name: `Yield forgone (${v.horizon_days}d)`, value: v.exit_cost },
  ];
  return (
    <ResponsiveContainer width="100%" height={136}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 8, right: 0, bottom: 8, left: 0 }}
        barSize={36}
      >
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" hide />
        <Tooltip
          cursor={false}
          content={(props) => (
            <ChartTooltip {...props} formatValue={(value) => `${num(value)} ${v.symbol}`} />
          )}
        />
        <Bar
          dataKey="value"
          name="Position loss"
          shape={<Rectangle />}
          fill="var(--loss-bar)"
          activeBar={false}
          isAnimationActive={false}
        >
          <LabelList dataKey="name" position="insideLeft" offset={10} fill="#fff" fontSize={12} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Sibling markets the engine reaches, by loss, each linked to its market page. */
export function SiblingLosses({ vault: v }: { vault: VaultIncident }) {
  return (
    <Collapsible className="grid gap-2 text-sm">
      <div className="flex justify-between">
        <Tip
          label="Other markets reached"
          tip="Morpho markets this vault does not supply where the same shock costs lenders a loss"
        />
        {v.sibling_losses.length ? (
          <CollapsibleTrigger className="group flex cursor-pointer items-center gap-1 font-bold tabular-nums">
            {v.sibling_losses.length}
            <ChevronDown
              size={14}
              className="text-muted-foreground transition-transform group-data-[state=open]:rotate-180"
            />
          </CollapsibleTrigger>
        ) : (
          <b className="tabular-nums">{v.engine_block != null ? 0 : '—'}</b>
        )}
      </div>
      <CollapsibleContent>
        <ul className="m-0 grid list-none gap-1 p-0">
          {[...v.sibling_losses]
            .sort((a, b) => b[2] - a[2])
            .map(([id, market, loss, unit]) => (
              <li key={id}>
                <Link
                  to="/market/$marketId"
                  params={{ marketId: id }}
                  search={(prev) => prev}
                  className="flex justify-between gap-4 rounded px-2 py-1 hover:bg-accent"
                >
                  <span className="truncate">{market}</span>
                  <span className="whitespace-nowrap tabular-nums">
                    <FormattedText>{`${num(loss)} ${unit}`}</FormattedText>
                  </span>
                </Link>
              </li>
            ))}
        </ul>
      </CollapsibleContent>
    </Collapsible>
  );
}

/** The breakeven p* against the outside views (Nexus Mutual cover prices): their head, the rest on hover. */
export function Breakeven({
  pStar: p,
  pStarYear,
  horizon,
  outside,
}: {
  pStar: number | null;
  pStarYear: number | null;
  horizon: number;
  outside: string[];
}) {
  return (
    <div className="grid gap-2">
      <FigureTable
        label="Breakeven"
        rows={[
          {
            label: `Breakeven p* (${horizon}d)`,
            tip: 'Probability of the incident over the horizon above which leaving now pays',
            value: pStar(p),
          },
          { label: 'Breakeven p* / yr', tip: 'The same, per year', value: pStar(pStarYear) },
        ]}
      />
      {outside.length ? (
        <ul className="m-0 grid list-none gap-1 p-0 text-sm">
          {outside.map((line) => (
            <li key={line} className="truncate">
              <Tip label={line.split(':')[0]} tip={line} />
            </li>
          ))}
        </ul>
      ) : (
        <span className="text-sm text-muted-foreground">No outside price</span>
      )}
    </div>
  );
}

/** The conditional Monte Carlo: the loss of staying given the incident against leaving, in USD. */
export function ConditionalFigures({ conditional: c }: { conditional: Conditional }) {
  return (
    <FigureTable
      label="Stay or leave, given the incident"
      rows={[
        { label: 'Stay, mean', tip: c.text, value: usd(c.stay_mean, 0) },
        { label: 'Stay, 95%', value: usd(c.stay_p95, 0) },
        { label: 'Stay, 99%', value: usd(c.stay_p99, 0) },
        {
          label: 'Leave, mean',
          tip: 'Loss left after leaving first, plus the certain cost of leaving',
          value: usd(c.leave_mean, 0),
        },
        {
          label: 'Staying is worse',
          tip: `Share of ${num(c.paths, 0)} paths where staying costs more than leaving`,
          value: percent(c.p_stay_worse),
          tone: c.p_stay_worse >= 0.5 ? 'text-critical' : undefined,
        },
        {
          label: 'No liquidator',
          tip: 'Share of paths where no liquidator steps in',
          value: percent(c.no_liquidator_share),
        },
      ]}
    />
  );
}

const STEP_X = [16, 112, 208, 304];

/** Shock → the vault's markets → the vault → the position, sized by exposure. */
export function PropagationGraph({ vault: v }: { vault: VaultIncident }) {
  const rowHeight = 22;
  const top = 8;
  const mid = top + (v.hits.length * rowHeight) / 2;
  const exposed = v.hits.reduce((sum, hit) => sum + hit.vault_exposure, 0);
  const marketY = v.hits.map((_, index) => top + rowHeight * (index + 0.5));
  const curve = (x1: number, y1: number, x2: number, y2: number) =>
    `M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`;
  const shocked = Object.keys(v.shocks).join(' + ') || 'Default';
  const steps = [
    {
      name: shocked,
      figure: v.hits[0]?.event === 'default' ? '—' : `−${percent(v.hits[0]?.drop)}`,
      why: 'The shock',
    },
    {
      name: `${v.hits.length} markets`,
      figure: v.asset_usd != null ? usd(exposed * v.asset_usd) : '—',
      why: "The vault's markets it reaches",
    },
    {
      name: 'Vault',
      figure: v.vault_total > 0 ? `−${percent(v.vault_loss / v.vault_total)}` : '—',
      why: "Their bad debt is the vault's loss",
    },
    {
      name: 'Position',
      figure: v.depositor_assets > 0 ? `−${percent(v.loss_if_stay / v.depositor_assets)}` : '—',
      why: 'Shared by depositors pro rata',
    },
  ];
  const node = (x: number, y: number, r: number, loss = false) => (
    <circle cx={x} cy={y} r={r} fill={loss ? 'var(--loss-bar)' : 'var(--fg)'} />
  );

  return (
    <svg
      viewBox={`0 0 320 ${top * 2 + v.hits.length * rowHeight + 34}`}
      className="w-full"
      role="img"
      aria-label={steps.map((step) => `${step.name} ${step.figure}`).join(', ')}
    >
      <g fill="none" stroke="var(--edge)" strokeWidth={1}>
        {marketY.map((y, index) => (
          <g key={index}>
            <path d={curve(STEP_X[0], mid, STEP_X[1], y)} />
            <path d={curve(STEP_X[1], y, STEP_X[2], mid)} />
          </g>
        ))}
        <path d={curve(STEP_X[2], mid, STEP_X[3], mid)} />
      </g>
      {node(STEP_X[0], mid, 5)}
      {v.hits.map((hit, index) => (
        <HoverTooltip key={hit.market_id}>
          <TooltipTrigger asChild>
            <g className="cursor-help">
              {node(
                STEP_X[1],
                marketY[index],
                2.5 + 3.5 * Math.sqrt(exposed > 0 ? hit.vault_exposure / exposed : 0),
              )}
            </g>
          </TooltipTrigger>
          <TooltipContent>{hit.label}</TooltipContent>
        </HoverTooltip>
      ))}
      {node(STEP_X[2], mid, 5, v.vault_loss > 0)}
      {node(STEP_X[3], mid, 5, v.loss_if_stay > 0)}
      {steps.map((step, index) => (
        <HoverTooltip key={step.name}>
          <TooltipTrigger asChild>
            <text
              x={STEP_X[index]}
              y={top * 2 + v.hits.length * rowHeight + 10}
              textAnchor={index === 0 ? 'start' : index === 3 ? 'end' : 'middle'}
              fontSize={11}
              className="cursor-help tabular-nums"
            >
              <tspan fill="var(--fg)">{step.name}</tspan>
              <tspan x={STEP_X[index]} dy={14} fill="var(--muted)">
                {step.figure}
              </tspan>
            </text>
          </TooltipTrigger>
          <TooltipContent>{step.why}</TooltipContent>
        </HoverTooltip>
      ))}
    </svg>
  );
}
