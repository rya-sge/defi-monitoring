import { ChartTooltip } from '../components/ChartTooltip';
import { FormattedText } from '../components/FormattedText';
import { Link, useNavigate, useSearch } from '@tanstack/react-router';
import { ArrowRight, ChevronDown, TriangleAlert } from 'lucide-react';
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
import { useIncidentImpact } from '../api/hooks';
import type { IncidentResponse, VaultIncident } from '../api/types';
import { ErrorState, Loading } from '../components/States';
import { usd, num, percent } from '../lib/format';
import { INCIDENT } from '../mocks/incident';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

const VERDICT = { STAY: 'text-ok', REDUCE: 'text-warn', EXIT: 'text-critical' };
const PRIORITY = { EXIT: 0, REDUCE: 1, STAY: 2 };

export function IncidentPage() {
  const { data, isPending, error } = useIncidentImpact({
    example: INCIDENT.example,
    shocks: INCIDENT.shocks,
    horizon: INCIDENT.horizon,
  });
  if (isPending) return <Loading what="the incident" />;
  if (error) return <ErrorState what="the incident" error={error} />;
  return <IncidentView result={data} />;
}

function IncidentView({ result }: { result: IncidentResponse }) {
  const { target } = useSearch({ strict: false });
  const navigate = useNavigate();
  const rows = [...result.book.lines].sort(
    (a, b) =>
      PRIORITY[a.verdict] - PRIORITY[b.verdict] ||
      b.loss_usd - a.loss_usd ||
      a.name.localeCompare(b.name),
  );
  const v =
    result.vaults.find((vault) => vault.vault.toLowerCase() === target?.toLowerCase()) ??
    result.vaults.find((vault) => vault.vault.toLowerCase() === INCIDENT.defaultVault) ??
    result.vaults[0];
  if (!v) return null;
  const selected = v.vault.toLowerCase();
  const select = (vault: string) =>
    void navigate({
      to: '/incident',
      search: (prev) => ({ ...prev, target: vault.toLowerCase() }),
    });

  return (
    <div className="mx-auto grid max-w-[1440px] gap-8 px-5.5 pt-7 pb-12">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b pb-5">
        <div className="grid gap-2">
          <div className="flex items-center gap-2 text-sm">
            <TriangleAlert size={16} className="text-critical" />
            <span className="font-semibold text-critical">Critical</span>
            <span className="text-muted-foreground">Demo event</span>
          </div>
          <h1 className="m-0">
            {INCIDENT.title}{' '}
            <span className="tabular-nums">
              <FormattedText>−30%</FormattedText>
            </span>
          </h1>
        </div>
        <div className="grid gap-2 text-sm tabular-nums">
          <span>
            Occurred <b>{INCIDENT.occurredMinutesAgo} min ago</b>
          </span>
          <span>
            Detected <b>{INCIDENT.detectedMinutesAgo} min ago</b>
          </span>
        </div>
      </header>
      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,3fr)]">
        <section className="min-w-0" aria-label="Vault impacts">
          <h2 className="mt-0 mb-4">Vault impacts</h2>
          <Table className="tabular-nums">
            <TableHeader>
              <TableRow>
                <TableHead>Vault</TableHead>
                <TableHead className="text-right">Exposure</TableHead>
                <TableHead className="text-right">Est. loss</TableHead>
                <TableHead>Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow
                  key={row.vault}
                  tabIndex={0}
                  aria-label={`${row.name}, estimated loss ${usd(row.loss_usd)}, ${row.verdict}`}
                  aria-selected={row.vault.toLowerCase() === selected}
                  data-state={row.vault.toLowerCase() === selected ? 'selected' : undefined}
                  className="cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-ring"
                  onClick={() => select(row.vault)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      select(row.vault);
                    }
                  }}
                >
                  <TableCell className="max-w-72 whitespace-normal py-4 font-medium">
                    {row.name}
                  </TableCell>
                  <TableCell className="text-right">
                    {row.priced ? usd(row.exposure_usd) : '—'}
                  </TableCell>
                  <TableCell className="text-right">
                    {row.priced ? usd(row.loss_usd) : '—'}
                  </TableCell>
                  <TableCell>
                    <span className={`text-xs font-semibold ${VERDICT[row.verdict]}`}>
                      {row.hit_markets.length ? row.verdict.toLowerCase() : 'Unaffected'}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>
        <DecisionPanel key={selected} vault={v} />
      </div>
    </div>
  );
}

function DecisionPanel({ vault: v }: { vault: VaultIncident }) {
  const affected = v.hits.length > 0;
  const data = [
    { name: 'Stay', value: v.loss_if_stay },
    { name: 'Exit first', value: v.loss_if_exit_first },
    { name: `Yield forgone (${v.horizon_days}d)`, value: v.exit_cost },
  ];
  const total = v.can_leave_now + v.stuck;
  const figures = [
    {
      label: 'Vault exposure',
      value:
        v.asset_usd != null
          ? usd(v.hits.reduce((sum, hit) => sum + hit.vault_exposure, 0) * v.asset_usd)
          : '—',
    },
    { label: 'Estimated vault loss', value: `${num(v.vault_loss)} ${v.symbol}` },
    { label: 'Position loss', value: `${num(v.loss_if_stay)} ${v.symbol}` },
    {
      label: 'Avoidable position loss',
      value: `${num(Math.max(0, v.loss_if_stay - v.loss_if_exit_first))} ${v.symbol}`,
    },
    { label: 'Withdrawable', value: `${num(v.can_leave_now)} ${v.symbol}` },
    { label: 'Pool usage', value: total > 0 ? percent(v.stuck / total) : '—' },
  ];

  return (
    <aside
      className="grid min-w-0 grid-cols-1 gap-6 border-t pt-5 lg:sticky lg:top-5 lg:border-t-0 lg:border-l lg:pt-0 lg:pl-7"
      aria-label="Selected vault action"
    >
      <header className="grid gap-2">
        <span className={`text-sm font-semibold ${VERDICT[v.verdict]}`}>
          {affected ? v.verdict.toLowerCase() : 'Unaffected'}
        </span>
        <h2 className="m-0">{v.name}</h2>
      </header>
      <Table className="tabular-nums" aria-label="Selected vault figures">
        <TableBody>
          {figures.map((item) => (
            <TableRow key={item.label}>
              <TableHead scope="row" className="w-full max-w-0 font-normal">
                <HoverTooltip>
                  <TooltipTrigger asChild>
                    <span className="block truncate">{item.label}</span>
                  </TooltipTrigger>
                  <TooltipContent>{item.label}</TooltipContent>
                </HoverTooltip>
              </TableHead>
              <TableCell className="text-right font-medium whitespace-nowrap">
                <FormattedText>{item.value}</FormattedText>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {affected && v.loss_if_stay <= v.loss_if_exit_first ? (
        <span className="text-xs text-warn">Exiting first does not reduce the estimated loss</span>
      ) : null}
      <Button asChild variant="ghost">
        <Link to="/" search={(prev) => ({ ...prev, target: v.vault })}>
          Review withdrawal liquidity
          <ArrowRight size={14} />
        </Link>
      </Button>
      <section>
        <h3 className="m-0">Position loss · {v.symbol}</h3>
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
              <LabelList
                dataKey="name"
                position="insideLeft"
                offset={10}
                fill="#fff"
                fontSize={12}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </section>
      <section className="grid gap-3 border-t pt-4">
        <h3 className="m-0">Propagation</h3>
        {affected ? (
          <PropagationGraph vault={v} />
        ) : (
          <span className="text-sm text-muted-foreground">No direct exposure</span>
        )}
        <Collapsible className="grid gap-2 text-sm">
          <div className="flex justify-between">
            <HoverTooltip>
              <TooltipTrigger asChild>
                <span className="cursor-help">Other markets reached</span>
              </TooltipTrigger>
              <TooltipContent>
                Morpho markets this vault does not supply where the same shock costs lenders a loss
              </TooltipContent>
            </HoverTooltip>
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
      </section>
      <section className="grid gap-2 border-t pt-4 text-sm" aria-label="Insurance coverage">
        <h3 className="m-0">Coverage</h3>
        <div className="flex justify-between">
          <span>Policy held</span>
          <span className="text-muted-foreground">Unknown</span>
        </div>
        <div className="flex justify-between">
          <span>PST markdown covered</span>
          <span className="text-muted-foreground">Not verified</span>
        </div>
      </section>
    </aside>
  );
}

const STEP_X = [16, 112, 208, 304];

function PropagationGraph({ vault: v }: { vault: VaultIncident }) {
  const rowHeight = 22;
  const top = 8;
  const mid = top + (v.hits.length * rowHeight) / 2;
  const exposed = v.hits.reduce((sum, hit) => sum + hit.vault_exposure, 0);
  const marketY = v.hits.map((_, index) => top + rowHeight * (index + 0.5));
  const curve = (x1: number, y1: number, x2: number, y2: number) =>
    `M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`;
  const steps = [
    { name: 'PST', figure: `−${percent(v.hits[0]?.drop)}`, why: 'The shocked collateral' },
    {
      name: `${v.hits.length} markets`,
      figure: v.asset_usd != null ? usd(exposed * v.asset_usd) : '—',
      why: "The vault's markets that take it as collateral",
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
