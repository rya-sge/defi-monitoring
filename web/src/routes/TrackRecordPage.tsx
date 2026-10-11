// Manager question: can I trust the tool's numbers?
import { Fragment, useState } from 'react';
import { ChevronRight, Info } from 'lucide-react';
import { Tip } from '../components/scenario/IncidentParts';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useBacktest, useBacktests } from '../api/hooks';
import type { Backtest, MarketBacktest } from '../api/types';
import { ChartTooltip } from '../components/ChartTooltip';
import { FormattedText } from '../components/FormattedText';
import { StatRow } from '../components/Stat';
import { Empty, ErrorState, Loading } from '../components/States';
import { CHART_COLORS } from '../lib/charts';
import { blockNumber, compactUsd, etherscanUrl, num, percent, shortHash, usd } from '../lib/format';
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
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

const AXIS = {
  axisLine: false,
  tickLine: false,
  tick: { fontSize: 10, fill: 'var(--muted)', fillOpacity: 0.7 },
} as const;

/** Predicted against realised, as a signed relative error; exact when both are zero. */
function error(predicted: number, realised: number): string {
  if (realised === 0) return predicted === 0 ? '0%' : '—';
  const e = predicted / realised - 1;
  return `${e > 0 ? '+' : e < 0 ? '−' : ''}${percent(Math.abs(e))}`;
}

const sum = (markets: MarketBacktest[], key: keyof MarketBacktest) =>
  markets.reduce((total, m) => total + Number(m[key]), 0);

export function TrackRecordPage() {
  const list = useBacktests();
  const [picked, setPicked] = useState<string>();
  const episode = picked ?? list.data?.find((b) => b.recorded)?.episode;
  const backtest = useBacktest(episode);

  if (list.isPending) return <Loading what="the backtests" />;
  if (list.error) return <ErrorState what="the backtests" error={list.error} />;
  if (!episode) return <Empty>No recorded backtest.</Empty>;

  return (
    <div className="mx-auto grid max-w-[1120px] gap-10 px-5.5 pt-9 pb-14">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="grid gap-1">
          <h1 className="m-0">Track record</h1>
          {backtest.data ? (
            <p className="m-0 text-muted-foreground tabular-nums">
              Before block {blockNumber(backtest.data.before_block)} · liquidations{' '}
              {blockNumber(backtest.data.blocks[0])}–{blockNumber(backtest.data.blocks[1])}
            </p>
          ) : null}
        </div>
        <Select value={episode} onValueChange={setPicked}>
          <SelectTrigger aria-label="Episode" size="sm" className="w-96 max-w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {list.data.map((b) => (
              <SelectItem key={b.episode} value={b.episode} disabled={!b.recorded}>
                {b.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </header>
      {backtest.isPending ? (
        <Loading what="the episode" />
      ) : backtest.error ? (
        <ErrorState what="the episode" error={backtest.error} />
      ) : (
        <EpisodeView key={episode} backtest={backtest.data} />
      )}
    </div>
  );
}

function EpisodeView({ backtest: b }: { backtest: Backtest }) {
  const ms = b.markets;
  const missed = ms.reduce((n, m) => n + m.missed.length, 0);
  const extra = ms.reduce((n, m) => n + m.extra.length, 0);
  const pairs = [
    ['Positions liquidated', 'predicted_positions', 'realised_positions', (v: number) => num(v, 0)],
    ['Debt liquidated', 'predicted_debt', 'realised_repaid', usd],
    ['Liquidation bonus', 'predicted_bonus', 'realised_bonus', usd],
    ['Bad debt', 'predicted_bad_debt', 'realised_bad_debt', usd],
  ] as const;

  return (
    <>
      <h2 className="m-0">{b.title}</h2>
      <StatRow
        items={[
          ...pairs.map(([label, p, r, fmt]) => {
            const predicted = sum(ms, p);
            const realised = sum(ms, r);
            return {
              label,
              value: fmt(predicted),
              note: `realised ${fmt(realised)} · error ${error(predicted, realised)}`,
            };
          }),
          {
            label: 'Missed',
            value: num(missed, 0),
            note: `${num(extra, 0)} predicted, not liquidated`,
            tone: missed > 0 ? ('critical' as const) : ('neutral' as const),
          },
        ]}
      />
      <DebtChart markets={ms} />
      <MarketsTable markets={ms} />
      {b.pool ? <PoolBlock pool={b.pool} /> : null}
      {b.notes.length ? (
        <Tip
          label={
            <span className="flex w-fit items-center gap-1 text-sm text-muted-foreground">
              <Info size={14} /> Notes {b.notes.length}
            </span>
          }
          tip={b.notes.join('\n')}
        />
      ) : null}
    </>
  );
}

function DebtChart({ markets }: { markets: MarketBacktest[] }) {
  const data = markets.map((m) => ({
    label: m.label.replace(/\s*\(LLTV.*\)$/, ''),
    predicted: m.predicted_debt,
    realised: m.realised_repaid,
  }));
  return (
    <section aria-label="Debt liquidated by market">
      <h3>Debt liquidated, predicted and realised</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ left: 8, right: 16, top: 8, bottom: 4 }}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis dataKey="label" {...AXIS} interval={0} />
          <YAxis {...AXIS} tickFormatter={(v: number) => compactUsd(v)} width={60} />
          <Tooltip
            cursor={false}
            content={(props) => <ChartTooltip {...props} formatValue={(v) => usd(v)} />}
          />
          <Bar
            dataKey="predicted"
            name="Predicted"
            fill={CHART_COLORS[0]}
            activeBar={false}
            isAnimationActive={false}
          />
          <Bar
            dataKey="realised"
            name="Realised"
            fill={CHART_COLORS[1]}
            activeBar={false}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

function MarketsTable({ markets }: { markets: MarketBacktest[] }) {
  const [open, setOpen] = useState<string | null>(null);
  return (
    <section aria-label="Markets">
      <h3>By market</h3>
      <Table className="tabular-nums">
        <TableHeader>
          <TableRow>
            <TableHead />
            <TableHead>Market</TableHead>
            <TableHead className="text-right">Oracle fall</TableHead>
            <TableHead className="text-right">Positions</TableHead>
            <TableHead className="text-right">Debt predicted</TableHead>
            <TableHead className="text-right">Debt realised</TableHead>
            <TableHead className="text-right">Error</TableHead>
            <TableHead className="text-right">Missed</TableHead>
            <TableHead className="text-right">Extra</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {markets.map((m) => {
            const expanded = open === m.market_id;
            return (
              <Fragment key={m.market_id}>
                <TableRow
                  className="cursor-pointer"
                  data-state={expanded ? 'selected' : undefined}
                  aria-expanded={expanded}
                  onClick={() => setOpen(expanded ? null : m.market_id)}
                >
                  <TableCell className="w-6 text-muted-foreground">
                    <ChevronRight
                      size={14}
                      className={
                        expanded ? 'rotate-90 transition-transform' : 'transition-transform'
                      }
                    />
                  </TableCell>
                  <TableCell className="font-medium">{m.label}</TableCell>
                  <TableCell className="text-right">
                    <FormattedText>{`−${percent(m.oracle_fall)}`}</FormattedText>
                  </TableCell>
                  <TableCell className="text-right">
                    {m.predicted_positions} / {m.realised_positions}
                  </TableCell>
                  <TableCell className="text-right">{usd(m.predicted_debt)}</TableCell>
                  <TableCell className="text-right">{usd(m.realised_repaid)}</TableCell>
                  <TableCell className="text-right">
                    {error(m.predicted_debt, m.realised_repaid)}
                  </TableCell>
                  <TableCell
                    className={m.missed.length ? 'text-right text-critical' : 'text-right'}
                  >
                    {m.missed.length}
                  </TableCell>
                  <TableCell className="text-right">{m.extra.length}</TableCell>
                </TableRow>
                {expanded ? (
                  <TableRow className="hover:bg-transparent">
                    <TableCell />
                    <TableCell colSpan={8} className="whitespace-normal">
                      <MarketDetail market={m} />
                    </TableCell>
                  </TableRow>
                ) : null}
              </Fragment>
            );
          })}
        </TableBody>
      </Table>
    </section>
  );
}

function MarketDetail({ market: m }: { market: MarketBacktest }) {
  const later = new Set(m.extra_later);
  const defended = new Set(m.extra_defended);
  const left = m.extra.filter((a) => !later.has(a) && !defended.has(a));
  const sale = m.from_sale;
  return (
    <div className="grid gap-4 py-2">
      <div className="grid grid-cols-[repeat(auto-fit,minmax(160px,1fr))] gap-x-6 gap-y-2 text-sm">
        <Figure label="Borrowers" value={num(m.borrowers, 0)} />
        <Figure label="Liquidate events" value={num(m.realised_events, 0)} />
        <Figure
          label="Bonus"
          value={`${usd(m.predicted_bonus)} / ${usd(m.realised_bonus)}`}
          tip="Predicted / realised"
        />
        <Figure
          label="Bad debt"
          value={`${usd(m.predicted_bad_debt)} / ${usd(m.realised_bad_debt)}`}
          tip="Predicted / realised"
        />
        <Figure
          label="Left liquidatable"
          value={`${num(m.left_debt, 0)} ${m.loan_symbol}`}
          tip="Debt of the extra positions neither liquidated later nor defended, at the window's end"
        />
        <Figure
          label="Dust"
          value={num(m.left_dust, 0)}
          tip="Left positions too small for a liquidator's gas"
        />
        {sale ? (
          <Figure
            label="From the sale alone"
            value={`−${percent(Number(sale.oracle_fall))} · ${num(Number(sale.positions), 0)} positions`}
            tip={`The pool sale alone, through Pendle's pool math: ${usd(Number(sale.debt))} debt, ${String(sale.missed)} missed, ${String(sale.extra)} extra`}
          />
        ) : null}
      </div>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
        <Addresses title="Missed" items={m.missed} critical />
        <Addresses title="Liquidated later" items={m.extra_later} />
        <Addresses title="Defended" items={m.extra_defended} />
        <Addresses title="Left liquidatable" items={left} />
      </div>
    </div>
  );
}

function Figure({ label, value, tip }: { label: string; value: string; tip?: string }) {
  const name = <span className="text-muted-foreground">{label}</span>;
  return (
    <div className="grid">
      {tip ? (
        <HoverTooltip>
          <TooltipTrigger asChild>
            <span className="w-fit cursor-help">{name}</span>
          </TooltipTrigger>
          <TooltipContent>{tip}</TooltipContent>
        </HoverTooltip>
      ) : (
        name
      )}
      <span className="tabular-nums">
        <FormattedText>{value}</FormattedText>
      </span>
    </div>
  );
}

function Addresses({
  title,
  items,
  critical = false,
}: {
  title: string;
  items: string[];
  critical?: boolean;
}) {
  if (!items.length) return null;
  return (
    <div className="grid content-start gap-1 text-sm">
      <span className={critical ? 'font-semibold text-critical' : 'text-muted-foreground'}>
        {title} <span className="tabular-nums">{items.length}</span>
      </span>
      <ul className="m-0 grid max-h-48 list-none gap-0.5 overflow-auto p-0">
        {items.map((a) => (
          <li key={a}>
            <a href={etherscanUrl(a) ?? undefined} target="_blank" rel="noreferrer">
              {shortHash(a)}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** The Pendle pool behind the oracle (D208): the sale that moved it and the squeeze after. */
function PoolBlock({ pool: p }: { pool: Record<string, unknown> }) {
  const n = (key: string) => {
    const v = p[key];
    return typeof v === 'number' ? v : null;
  };
  const market = typeof p.market === 'string' ? p.market : null;
  return (
    <section aria-label="Pendle pool" className="grid gap-3">
      <h3 className="m-0">
        Pendle pool behind the oracle{' '}
        {market ? (
          <a
            href={etherscanUrl(market) ?? undefined}
            target="_blank"
            rel="noreferrer"
            className="text-sm font-normal"
          >
            {shortHash(market)}
          </a>
        ) : null}
      </h3>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-x-6 gap-y-3 text-sm">
        <Figure
          label="Implied APY"
          value={`${percent(n('apy_before'))} → ${percent(n('apy_at_first'))}`}
          tip="Before the episode → at the first liquidation"
        />
        <Figure label="PT sold" value={`${num(n('pt_sold'), 0)} PT`} tip="Net, into the pool" />
        <Figure label="Paid out" value={num(n('asset_out'), 0)} />
        <Figure
          label="Model sale"
          value={`${num(n('model_sale'), 0)} PT`}
          tip="The sale Pendle's pool math needs, from the state before, to reach that APY"
        />
        <Figure
          label="Price move from the sale"
          value={n('sale_fall') == null ? '—' : `−${percent(n('sale_fall'))}`}
        />
        <Figure
          label="Seized vs pool capacity"
          value={`${num(n('seized_pt'), 0)} / ${num(n('capacity_at_first'), 0)} PT`}
          tip="PT the liquidations seized / PT the pool still accepted at the first liquidation"
        />
      </div>
    </section>
  );
}
