// Manager question: does my PT loop hold? Stay, reduce or exit, and how much do I sell?
import { useState } from 'react';
import type { ReactNode } from 'react';
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useAnalyze, useReport } from '../api/hooks';
import type { PositionIncident, Report, Verdict } from '../api/types';
import { ChartTooltip } from '../components/ChartTooltip';
import { FormattedText } from '../components/FormattedText';
import { Stat, StatRow } from '../components/Stat';
import { ErrorState, Loading } from '../components/States';
import { CHART_COLORS } from '../lib/charts';
import { compactUsd, days, num, percent, shortHash, usd } from '../lib/format';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Info } from 'lucide-react';
import { Tip } from '../components/scenario/IncidentParts';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

const VERDICT: Record<Verdict, string> = {
  STAY: 'text-ok',
  REDUCE: 'text-warn',
  EXIT: 'text-critical',
};

/** The shocks the offline fixture holds; the API takes any `analyze --shock`. */
const PRESETS = ['issuer_depeg=0.08', 'oracle=0.1', 'pool_move=1.5', 'venue=Binance:0.5'];

const fall = (value: number | null | undefined) => (value == null ? '—' : `−${percent(value)}`);

export function PositionPage() {
  const report = useReport();
  const analyze = useAnalyze();
  if (report.isPending) return <Loading what="the position report" />;
  if (report.error) return <ErrorState what="the position report" error={report.error} />;
  const data = analyze.data ?? report.data;

  return (
    <div className="mx-auto grid max-w-[1120px] gap-10 px-5.5 pt-9 pb-14">
      <header className="flex flex-wrap items-end justify-between gap-5.5">
        <div className="grid gap-2">
          <span className="text-sm text-muted-foreground">
            {shortHash(data.position.borrower)} · data as of {data.data_as_of}
          </span>
          <h1 className="m-0">{data.position.label}</h1>
        </div>
        <RunForm
          pending={analyze.isPending}
          onRun={(body) => analyze.mutate(body)}
          error={analyze.error}
        />
      </header>
      <Decision data={data} />
      {data.incident ? <Incident incident={data.incident} /> : null}
      <Position data={data} />
      <Economics data={data} />
      <Layers data={data} />
      <Discovery data={data} />
    </div>
  );
}

function RunForm({
  pending,
  onRun,
  error,
}: {
  pending: boolean;
  onRun: (body: { horizon: number; shocks: string[] }) => void;
  error: Error | null;
}) {
  const [horizon, setHorizon] = useState('30');
  const [shock, setShock] = useState('');
  return (
    <form
      className="grid gap-1.5"
      onSubmit={(event) => {
        event.preventDefault();
        onRun({ horizon: Number(horizon) || 30, shocks: shock.trim() ? [shock.trim()] : [] });
      }}
    >
      <div className="flex items-end gap-2 text-sm">
        <label className="grid gap-1">
          <span className="text-muted-foreground">Horizon (d)</span>
          <Input
            type="number"
            min={1}
            max={365}
            value={horizon}
            onChange={(e) => setHorizon(e.target.value)}
            className="h-8 w-20"
          />
        </label>
        <label className="grid gap-1">
          <span className="text-muted-foreground">Incident</span>
          <Input
            list="position-shocks"
            placeholder="none"
            value={shock}
            onChange={(e) => setShock(e.target.value)}
            className="h-8 w-52"
          />
          <datalist id="position-shocks">
            {PRESETS.map((p) => (
              <option key={p} value={p} />
            ))}
          </datalist>
        </label>
        <Button type="submit" size="sm" disabled={pending}>
          {pending ? 'Running…' : 'Run'}
        </Button>
      </div>
      {error ? <span className="max-w-md text-sm text-critical">{error.message}</span> : null}
    </form>
  );
}

function Decision({ data }: { data: Report }) {
  const d = data.decision;
  return (
    <section aria-label="Verdict" className="grid gap-3">
      <div className="flex flex-wrap items-baseline gap-4">
        <Tip
          label={<span className={`text-3xl font-bold ${VERDICT[d.verdict]}`}>{d.verdict}</span>}
          tip={[d.headline, ...d.reasons].join('\n')}
        />
      </div>
    </section>
  );
}

function Position({ data }: { data: Report }) {
  const p = data.position;
  return (
    <section aria-label="Position" className="grid gap-5.5 sm:grid-cols-[auto_1fr] sm:gap-9">
      <Stat prominent label="Equity" value={usd(p.equity_usd, 0)} />
      <StatRow
        items={[
          { label: 'Collateral', value: usd(p.collateral_usd, 0) },
          { label: 'Debt', value: usd(p.debt_usd, 0) },
          {
            label: 'Health factor',
            value: num(p.health_factor),
            tone: p.health_factor != null && p.health_factor < 1.05 ? 'warn' : 'neutral',
          },
          { label: 'Liquidated at', value: fall(p.liquidation_drop) },
          { label: 'Maturity', value: days(p.days_to_maturity) },
          { label: 'Implied APY', value: percent(p.implied_apy) },
          { label: 'Borrow APY', value: percent(p.borrow_apy) },
          { label: 'Oracle', value: p.oracle_mode },
        ]}
      />
    </section>
  );
}

function Rows({ rows }: { rows: [ReactNode, ReactNode, string?][] }) {
  return (
    <Table className="text-[0.86rem] tabular-nums">
      <TableBody>
        {rows.map(([label, value, tip], i) => (
          <TableRow key={i}>
            <TableHead scope="row" className="font-normal text-muted-foreground">
              {tip ? (
                <HoverTooltip>
                  <TooltipTrigger asChild>
                    <span className="cursor-help">{label}</span>
                  </TooltipTrigger>
                  <TooltipContent>{tip}</TooltipContent>
                </HoverTooltip>
              ) : (
                label
              )}
            </TableHead>
            <TableCell className="text-right">
              <FormattedText>{value}</FormattedText>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function Economics({ data }: { data: Report }) {
  const d = data.decision;
  const r = d.reduction;
  const q = data.exit_quote;
  return (
    <section aria-label="Stay or leave" className="grid gap-9 md:grid-cols-2">
      <div>
        <h3>Stay or leave · {data.simulation.horizon_days} d</h3>
        <Rows
          rows={[
            ['Carry', usd(d.carry_usd, 0)],
            [
              'Exit cost',
              usd(d.exit_cost_usd, 0),
              `${q.source}${q.estimated ? ' (estimated)' : ''}: impact ${num(q.price_impact * 100)}%, fee ${usd(q.fee_usd, 0)}`,
            ],
            ['Expected loss', usd(d.expected_loss_usd, 0)],
            ['Net of staying', usd(d.net_stay_usd, 0)],
            [
              'Risk multiple to exit',
              d.risk_multiple_to_exit == null ? '—' : `${num(d.risk_multiple_to_exit, 1)}×`,
            ],
            ['Stress fall', fall(d.stress_drop)],
          ]}
        />
      </div>
      <div>
        <h3>Reduce</h3>
        <Rows
          rows={[
            ['Sell', usd(r.sell_usd, 0), r.source],
            ['New health factor', num(r.new_health_factor)],
            ['New liquidation fall', fall(r.new_liquidation_drop)],
            ['Cost', usd(r.cost_usd, 0)],
            ['Expected loss after', usd(r.expected_loss_usd, 0)],
            ['CVaR 99 after', usd(r.cvar99_usd, 0)],
          ]}
        />
        {data.oracle_sensitivity ? (
          <>
            <h3>If the oracle is {data.oracle_sensitivity.oracle_mode}</h3>
            <Rows
              rows={[
                [
                  'Verdict',
                  <span className={`font-semibold ${VERDICT[data.oracle_sensitivity.verdict]}`}>
                    {data.oracle_sensitivity.verdict}
                  </span>,
                ],
                ['Expected loss', usd(data.oracle_sensitivity.expected_loss_usd, 0)],
                ['CVaR 99', usd(data.oracle_sensitivity.cvar99_usd, 0)],
                ['P(liquidation)', percent(data.oracle_sensitivity.p_liquidation)],
              ]}
            />
          </>
        ) : null}
      </div>
    </section>
  );
}

/** "now", "16 h", "never": the oracle's delay before the incident can liquidate. */
function timeToAct(t: PositionIncident['timing']): string {
  if (t.never) return 'never';
  if (t.seconds == null) return '—';
  if (t.seconds === 0) return 'now';
  return t.seconds < 3600 ? `${num(t.seconds / 60, 0)} min` : `${num(t.seconds / 3600, 0)} h`;
}

function Incident({ incident: i }: { incident: PositionIncident }) {
  const shock = Object.entries(i.shocks)
    .map(([k, v]) => `${k} ${k === 'pool_move' ? `${num(v, 1)}×` : `−${percent(v)}`}`)
    .join(' + ');
  const texts = [
    i.pool_move?.text,
    i.stressed_exit?.text,
    ...i.path,
    ...(i.after_switch
      ? i.after_switch.path.map((p) => `after ${i.after_switch!.after}: ${p}`)
      : []),
    ...i.notes,
  ].filter((t): t is string => !!t);
  return (
    <section aria-label="Incident" className="grid gap-4 rounded-md border p-5.5">
      <div className="flex flex-wrap items-baseline gap-4">
        <span className="text-sm text-muted-foreground">Given {shock}</span>
        <Tip
          label={<span className={`text-xl font-bold ${VERDICT[i.verdict]}`}>{i.verdict}</span>}
          tip={i.reason}
        />
        {texts.length ? (
          <Tip
            label={<Info size={14} className="text-muted-foreground" />}
            tip={texts.join('\n')}
          />
        ) : null}
      </div>
      <StatRow
        items={[
          {
            label: 'Loss if staying',
            value: usd(i.loss_usd, 0),
            note: `${percent(i.loss_share_of_equity)} of equity`,
            tone: i.liquidated ? 'critical' : 'neutral',
          },
          ...(i.after_switch
            ? [
                {
                  label: `Loss after ${i.after_switch.after}`,
                  value: usd(i.after_switch.loss_usd, 0),
                  note: `${percent(i.after_switch.loss_share_of_equity)} of equity`,
                  tone: i.after_switch.liquidated ? ('critical' as const) : ('neutral' as const),
                },
              ]
            : []),
          { label: 'Exit cost now', value: usd(i.exit_cost_usd, 0), note: i.exit_source },
          { label: 'Oracle fall', value: fall(i.oracle_drop) },
          ...(i.reduction
            ? [
                {
                  label: 'Sell to survive',
                  value: usd(i.reduction.sell_usd, 0),
                  note: `${percent(i.reduction.share)} of the position, loss after ${usd(i.reduction.loss_after_usd, 0)}`,
                },
              ]
            : []),
          ...(i.stressed_exit
            ? [
                {
                  label: 'Sellable after liquidations',
                  value: usd(i.stressed_exit.sellable_usd, 0),
                  note: `slippage ${percent(i.stressed_exit.slippage_after)}`,
                  tone: i.stressed_exit.full_exit ? ('neutral' as const) : ('warn' as const),
                },
              ]
            : []),
          ...(i.pool_move
            ? [
                {
                  label: 'Pool sale',
                  value: usd(i.pool_move.sold_usd, 0),
                  note: `moves the pool ${percent(i.pool_move.pool_fall)}; liquidates at ${percent(i.pool_move.liquidation_fall)}`,
                },
              ]
            : []),
        ]}
      />
      <div className="text-sm">
        <span className="text-muted-foreground">Time to act · </span>
        <Tip label={timeToAct(i.timing)} tip={i.timing.text} />
      </div>
    </section>
  );
}

function Layers({ data }: { data: Report }) {
  const s = data.simulation;
  const rows = [...s.layers]
    .sort((a, b) => b.contribution_usd - a.contribution_usd)
    .map((l) => ({ ...l, name: l.layer }));
  return (
    <section aria-label="Where the expected loss comes from" className="grid gap-5.5">
      <h3 className="m-0">Expected loss by layer</h3>
      <StatRow
        items={[
          { label: 'Expected loss', value: usd(s.expected_loss_usd, 0) },
          { label: 'VaR 99', value: usd(s.var99_usd, 0) },
          { label: 'CVaR 99', value: usd(s.cvar99_usd, 0) },
          { label: 'P(any loss)', value: percent(s.p_any_loss) },
          { label: 'P(liquidation)', value: percent(s.p_liquidation) },
        ]}
      />
      <ResponsiveContainer width="100%" height={Math.max(160, rows.length * 40)}>
        <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 24 }}>
          <XAxis
            type="number"
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 10, fill: 'var(--muted)', fillOpacity: 0.7 }}
            tickFormatter={(v: number) => compactUsd(v)}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={280}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: 'var(--fg)' }}
          />
          <Tooltip
            cursor={false}
            content={(props) => (
              <ChartTooltip
                {...props}
                formatValue={(v, payload) => {
                  const l = payload as (typeof rows)[number];
                  return `${usd(v, 0)} · p ${percent(l.p_horizon)} · alone ${usd(l.standalone_loss_usd, 0)}`;
                }}
              />
            )}
          />
          <Bar
            dataKey="contribution_usd"
            name="Contribution"
            fill={CHART_COLORS[0]}
            activeBar={false}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

function List({ title, items }: { title: string; items: string[] | undefined }) {
  if (!items?.length) return null;
  return (
    <div>
      <h4 className="mt-0 mb-2">{title}</h4>
      <ul className="m-0 grid gap-1 pl-5 text-sm">
        {items.map((t) => (
          <li key={t}>
            <FormattedText>{t}</FormattedText>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Discovery({ data }: { data: Report }) {
  const d = data.discovery;
  if (!d) return null;
  const protocols = Object.values(d.protocols ?? {});
  return (
    <section aria-label="Discovery depth" className="grid gap-7">
      <h2 className="m-0">Discovery depth</h2>
      <div className="grid gap-7 md:grid-cols-2">
        <List
          title="Oracle"
          items={[d.oracle_profile ?? d.oracle ?? '', d.oracle_shared ?? ''].filter(Boolean)}
        />
        <List
          title="Backing and grade"
          items={[
            ...(d.backing ?? []).map(
              (b) => `${b.token} backed by ${b.backed_by} (${percent(b.share)})`,
            ),
            ...Object.entries(d.grades ?? {}).map(([t, g]) => `${t}: Pharos ${g}`),
          ]}
        />
        <List
          title="Concentration"
          items={[
            ...(d.position_share ?? []),
            ...(d.supply ?? []),
            ...protocols.map((p) => p.concentration),
          ]}
        />
        <List title="External venues" items={d.venues} />
      </div>

      {d.admin?.length ? (
        <div>
          <h3>Who can change it</h3>
          <Table className="text-[0.86rem] tabular-nums">
            <TableHeader>
              <TableRow>
                <TableHead>Contract</TableHead>
                <TableHead>Upgradeable</TableHead>
                <TableHead>Admin</TableHead>
                <TableHead className="text-right">Timelock</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {d.admin.map((a) => (
                <TableRow key={a.address + a.role}>
                  <TableCell>{a.role}</TableCell>
                  <TableCell>{a.upgradeable ? 'yes' : 'no'}</TableCell>
                  <TableCell>{shortHash(a.admin)}</TableCell>
                  <TableCell className={`text-right ${a.timelock_h == null ? 'text-warn' : ''}`}>
                    {a.timelock_h == null ? 'none' : `${num(a.timelock_h, 0)} h`}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : null}

      {d.market_curve?.length ? (
        <div>
          <h3>Market liquidations by oracle fall · {d.market}</h3>
          <Table className="text-[0.86rem] tabular-nums">
            <TableHeader>
              <TableRow>
                <TableHead>Oracle fall</TableHead>
                <TableHead className="text-right">Positions</TableHead>
                <TableHead className="text-right">Liquidatable debt</TableHead>
                <TableHead className="text-right">Bad debt</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {d.market_curve.map((c) => (
                <TableRow key={c.oracle_fall}>
                  <TableCell>{fall(c.oracle_fall)}</TableCell>
                  <TableCell className="text-right">{c.positions}</TableCell>
                  <TableCell className="text-right">{usd(c.liquidatable_debt, 0)}</TableCell>
                  <TableCell className={`text-right ${c.bad_debt > 0 ? 'text-critical' : ''}`}>
                    {usd(c.bad_debt, 0)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : null}

      {d.siblings?.length ? (
        <div>
          <h3>Sibling markets at {fall(d.sibling_fall)}</h3>
          <Table className="text-[0.86rem] tabular-nums">
            <TableHeader>
              <TableRow>
                <TableHead>Market</TableHead>
                <TableHead>Linked by</TableHead>
                <TableHead>Oracle</TableHead>
                <TableHead className="text-right">Borrow</TableHead>
                <TableHead className="text-right">Liquidatable</TableHead>
                <TableHead className="text-right">Bad debt</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {d.siblings.map((s) => (
                <TableRow key={s.label + s.linked_by}>
                  <TableCell>{s.label}</TableCell>
                  <TableCell className="max-w-72 whitespace-normal text-muted-foreground">
                    {s.linked_by}
                  </TableCell>
                  <TableCell>{s.oracle_class ?? '—'}</TableCell>
                  <TableCell className="text-right">{`${num(s.borrow, 0)} ${s.unit}`}</TableCell>
                  <TableCell className="text-right">{`${num(s.liquidatable_at_fall, 0)} ${s.unit}`}</TableCell>
                  <TableCell
                    className={`text-right ${s.bad_debt_at_fall > 0 ? 'text-critical' : ''}`}
                  >
                    {`${num(s.bad_debt_at_fall, 0)} ${s.unit}`}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : null}
    </section>
  );
}
