import { useCallback, useMemo } from 'react';
import { Link } from '@tanstack/react-router';
import { ChevronDown } from 'lucide-react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { cn } from 'cn';
import { useAlerts, useSelectedTarget, useVault } from '../api/hooks';
import type { Alert, Vault, VaultExit, VaultMarket } from '../api/types';
import { ChartTooltip } from '../components/ChartTooltip';
import { LiquidationChart } from '../components/LiquidationChart';
import { Stat } from '../components/Stat';
import { Empty, ErrorState, Loading } from '../components/States';
import { VaultLossChart } from '../components/VaultCharts';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { blockNumber, compactNum, etherscanUrl, num, percent, shortHash, usd } from '../lib/format';
import { badDebt } from '../lib/risk';

// registry.json thresholds, which the frontend cannot read: watch.lender_concentration_warn,
// watch.concentration_top1_warn and watch.concentration_min_borrowers.
const MAIN_LENDER = 0.5;
const TOP1_WARN = 0.5;
const MIN_BORROWERS = 5;

/** Governance and admin-surface alerts (docs/alert-runbook.md): what the curator or a dependency changed. */
const CHANGE =
  /^(Admin|AdminState|Timelock|ExitGate|Blue\.SetOwner)\b|^(Vault|Adapter)\.(Submit|Accept|Revoke|Increase|Decrease|Add|Remove|Set|Abdicate|BurnShares)/;
const PENDING = /(Submit|CallScheduled)$/;

const AXIS = {
  axisLine: false,
  tickLine: false,
  tick: { fontSize: 10, fill: 'var(--muted)', fillOpacity: 0.7 },
} as const;

export function VaultRisksPage() {
  const { target, isPending: targetPending } = useSelectedTarget();
  const address = target && !target.startsWith('user-') ? target : undefined;
  const { data, isPending, error } = useVault(address);

  if (targetPending) return <Loading what="the targets" />;
  if (!address) return <Empty>Pick a vault in the top bar.</Empty>;
  if (isPending) return <Loading what="the vault" />;
  if (error) return <ErrorState what="the vault" error={error} />;
  return <VaultRisksView vault={data} />;
}

function VaultRisksView({ vault }: { vault: Vault }) {
  const exit = vault.exit ?? null;
  const loss = useCallback((drop: number) => badDebt(vault, drop), [vault]);
  const classified = vault.markets.filter((m) => m.oracle_class != null);
  const constant = classified.filter((m) => m.oracle_class === 'constant-price');
  const figures = [
    {
      label: 'Your exit now',
      value: exit
        ? `${num(exit.plain + exit.forced)} ${vault.asset_symbol} (${percent(exit.total > 0 ? (exit.plain + exit.forced) / exit.total : null)})`
        : '—',
    },
    ...[0.1, 0.3].map((drop) => {
      const value = loss(drop);
      return {
        label: `Bad debt at −${percent(drop)}`,
        value: `${usd(value)} (${percent(vault.total_assets_usd > 0 ? value / vault.total_assets_usd : null)})`,
        critical: value > 0,
      };
    }),
    {
      label: 'Constant-price oracles',
      value: classified.length ? `${constant.length} of ${classified.length}` : '—',
      tip: classified.length
        ? `${percent(constant.reduce((sum, m) => sum + m.share_of_vault, 0))} of the allocation`
        : undefined,
    },
  ];

  return (
    <div className="mx-auto grid max-w-[1120px] gap-10 px-5.5 pt-9 pb-14">
      <Changes vault={vault} />

      <section aria-label="Vault risks overview" className="grid gap-5.5 sm:grid-cols-2 sm:gap-9">
        <Stat prominent label="Total assets" value={usd(vault.total_assets_usd)} />
        <Table className="text-[0.86rem] tabular-nums">
          <TableBody>
            {figures.map((item) => (
              <TableRow key={item.label}>
                <TableHead scope="row" className="font-normal text-muted-foreground">
                  {item.label}
                </TableHead>
                <TableCell
                  className={cn(
                    'text-right',
                    'critical' in item && item.critical && 'text-critical',
                  )}
                >
                  {'tip' in item && item.tip ? (
                    <HoverTooltip>
                      <TooltipTrigger asChild>
                        <span className="cursor-help">{item.value}</span>
                      </TooltipTrigger>
                      <TooltipContent>{item.tip}</TooltipContent>
                    </HoverTooltip>
                  ) : (
                    item.value
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </section>

      <Tabs defaultValue="exit">
        <TabsList>
          <TabsTrigger value="exit">Exit</TabsTrigger>
          <TabsTrigger value="liquidations">Liquidations</TabsTrigger>
          <TabsTrigger value="loss">Vault loss</TabsTrigger>
        </TabsList>
        <TabsContent value="exit">
          {exit ? (
            <ExitPanel exit={exit} symbol={vault.asset_symbol} />
          ) : (
            <Empty>No recorded state for this vault.</Empty>
          )}
        </TabsContent>
        <TabsContent value="liquidations">
          <LiquidationChart liquidations={vault.liquidations} badDebt={loss} />
        </TabsContent>
        <TabsContent value="loss">
          <VaultLossChart vault={vault} />
        </TabsContent>
      </Tabs>

      <Table className="text-[0.86rem] tabular-nums">
        <TableHeader>
          <TableRow>
            <TableHead>Market</TableHead>
            <TableHead className="text-right">Allocation</TableHead>
            <TableHead className="text-right">Of vault</TableHead>
            <TableHead>Of market</TableHead>
            <TableHead>Oracle</TableHead>
            <TableHead>Cushion</TableHead>
            <TableHead>Top borrower</TableHead>
            <TableHead className="text-right">Utilization</TableHead>
            <TableHead className="text-right">LLTV</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {vault.markets.map((m) => (
            <TableRow key={m.id}>
              <TableCell>
                <Link to="/market/$marketId" params={{ marketId: m.id }} search={(prev) => prev}>
                  {m.label}
                </Link>
              </TableCell>
              <TableCell className="text-right">{usd(m.allocation_usd)}</TableCell>
              <TableCell className="text-right">{percent(m.share_of_vault)}</TableCell>
              <TableCell>
                <span className="flex items-center gap-2">
                  <InlineBar value={m.share_of_market} />
                  {percent(m.share_of_market)}
                  {m.share_of_market >= MAIN_LENDER ? (
                    <span className="text-xs text-warn">main lender</span>
                  ) : null}
                </span>
              </TableCell>
              <TableCell>
                <OracleCell market={m} />
              </TableCell>
              <TableCell>
                <CushionCell market={m} />
              </TableCell>
              <TableCell>
                <BorrowerCell market={m} />
              </TableCell>
              <TableCell className="text-right">{percent(m.utilization)}</TableCell>
              <TableCell className="text-right">{percent(m.lltv)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function InlineBar({ value, warn = false }: { value: number; warn?: boolean }) {
  return (
    <span className="inline-block h-1.5 w-14 shrink-0 overflow-hidden rounded-full bg-muted">
      <span
        className={cn('block h-full rounded-full', warn ? 'bg-warn' : 'bg-foreground')}
        style={{ width: `${Math.min(1, Math.max(0, value)) * 100}%` }}
      />
    </span>
  );
}

const ORACLE = {
  'price-tracking': { word: 'tracks price', dot: 'bg-foreground', text: '' },
  'constant-price': { word: 'constant price', dot: 'bg-warn', text: 'text-warn' },
  'not classified': {
    word: 'not classified',
    dot: 'bg-muted-foreground',
    text: 'text-muted-foreground',
  },
} as const;

function OracleCell({ market: m }: { market: VaultMarket }) {
  if (m.oracle_class == null) return '—';
  const { word, dot, text } = ORACLE[m.oracle_class];
  const feeds = m.feeds ?? [];
  const stale = feeds.some((feed) => feed.stale);
  return (
    <HoverTooltip>
      <TooltipTrigger asChild>
        <span className={cn('flex cursor-help items-center gap-2', text)}>
          <span
            className={cn(
              'size-2 shrink-0 rounded-full',
              dot,
              stale && 'ring-2 ring-critical ring-offset-1 ring-offset-background',
            )}
          />
          {word}
        </span>
      </TooltipTrigger>
      <TooltipContent>
        {feeds.length
          ? feeds.map((feed) => (
              <div key={feed.label} className={feed.stale ? 'text-critical' : undefined}>
                {feed.label}: {feed.freshness ?? 'freshness unknown'}
                {feed.stale ? ' · stale' : ''}
              </div>
            ))
          : 'No feed read'}
      </TooltipContent>
    </HoverTooltip>
  );
}

function CushionCell({ market: m }: { market: VaultMarket }) {
  const cushion = 1 - m.lltv;
  const worst = m.collateral_drawdown_1y;
  if (worst == null) return '—';
  const over = worst > cushion;
  return (
    <HoverTooltip>
      <TooltipTrigger asChild>
        <span className="relative inline-block h-1.5 w-24 cursor-help rounded-full bg-muted align-middle">
          <span
            className="absolute inset-y-0 left-0 rounded-full bg-foreground/30"
            style={{ width: `${cushion * 100}%` }}
          />
          <span
            className="absolute -inset-y-0.5 w-0.5 bg-foreground"
            style={{ left: `${cushion * 100}%` }}
          />
          <span
            className={cn(
              'absolute -inset-y-0.5 w-0.5',
              over ? 'bg-critical' : 'bg-muted-foreground',
            )}
            style={{ left: `${Math.min(1, worst) * 100}%` }}
          />
        </span>
      </TooltipTrigger>
      <TooltipContent>
        <div>Cushion {percent(cushion)}</div>
        <div className={over ? 'text-critical' : undefined}>Worst 1-year fall {percent(worst)}</div>
      </TooltipContent>
    </HoverTooltip>
  );
}

function BorrowerCell({ market: m }: { market: VaultMarket }) {
  if (m.top1_share == null) return '—';
  const warn = m.top1_share >= TOP1_WARN || (m.borrowers != null && m.borrowers < MIN_BORROWERS);
  return (
    <HoverTooltip>
      <TooltipTrigger asChild>
        <span className={cn('flex cursor-help items-center gap-2', warn && 'text-warn')}>
          <InlineBar value={m.top1_share} warn={warn} />
          {percent(m.top1_share)}
        </span>
      </TooltipTrigger>
      <TooltipContent>
        <div>Top 3 {percent(m.top3_share)}</div>
        <div>{m.borrowers ?? '—'} borrowers</div>
      </TooltipContent>
    </HoverTooltip>
  );
}

function Changes({ vault }: { vault: Vault }) {
  const { data, error } = useAlerts(vault.address);
  const changes = (data?.alerts ?? []).filter((alert) => CHANGE.test(alert.event)).reverse();
  const pending = changes.filter((alert) => PENDING.test(alert.event)).length;
  const critical = changes.some((alert) => alert.level === 'critical');
  const pill = 'rounded-full border px-2.5 py-0.5 text-xs tabular-nums';

  return (
    <Collapsible className="grid gap-4">
      <header className="flex items-center justify-between gap-4">
        <h1 className="m-0 truncate">{vault.name}</h1>
        {error ? (
          <span className={cn(pill, 'text-muted-foreground')}>Not watched</span>
        ) : !data ? null : changes.length ? (
          <CollapsibleTrigger
            className={cn(
              pill,
              'group flex shrink-0 cursor-pointer items-center gap-1',
              critical && 'border-critical text-critical',
            )}
          >
            {changes.length} {changes.length === 1 ? 'change' : 'changes'}
            {pending ? ` · ${pending} pending` : ''}
            <ChevronDown
              size={12}
              className="transition-transform group-data-[state=open]:rotate-180"
            />
          </CollapsibleTrigger>
        ) : (
          <span className={cn(pill, 'text-muted-foreground')}>No change</span>
        )}
      </header>
      <CollapsibleContent>
        <Table className="text-[0.86rem] tabular-nums">
          <TableBody>
            {changes.map((alert, index) => (
              <ChangeRow key={`${alert.block}-${alert.event}-${index}`} alert={alert} />
            ))}
          </TableBody>
        </Table>
      </CollapsibleContent>
    </Collapsible>
  );
}

const LEVEL = { info: 'bg-muted-foreground', warn: 'bg-warn', critical: 'bg-critical' } as const;

function ChangeRow({ alert }: { alert: Alert }) {
  const tx = alert.tx ? etherscanUrl(alert.tx) : null;
  return (
    <TableRow>
      <TableCell className="w-4">
        <span className={cn('block size-2 rounded-full', LEVEL[alert.level])} />
      </TableCell>
      <TableCell className="max-w-0 w-full">
        <HoverTooltip>
          <TooltipTrigger asChild>
            <span className="block truncate">{alert.title}</span>
          </TooltipTrigger>
          <TooltipContent className="max-w-96">{alert.detail}</TooltipContent>
        </HoverTooltip>
      </TableCell>
      <TableCell className="text-muted-foreground">{alert.event}</TableCell>
      <TableCell className="text-right">Block {blockNumber(alert.block)}</TableCell>
      <TableCell className="text-right">
        {tx && alert.tx ? (
          <a href={tx} target="_blank" rel="noreferrer">
            {shortHash(alert.tx)}
          </a>
        ) : (
          '—'
        )}
      </TableCell>
    </TableRow>
  );
}

function ExitPanel({ exit: e, symbol }: { exit: VaultExit; symbol: string }) {
  const withdrawable = e.plain + e.forced;
  const segments = [
    { label: 'Plain withdrawal', value: e.plain, color: 'var(--chart-1)' },
    {
      label: 'forceDeallocate',
      value: e.forced,
      color: 'var(--chart-2)',
      note: `${percent(e.penalty)} penalty`,
    },
    {
      label: 'Locked',
      value: Math.max(0, e.total - withdrawable),
      color: 'var(--line)',
    },
  ];
  const depositor = e.depositor?.toLowerCase() ?? null;
  const others = e.holders
    .filter((h) => h.address.toLowerCase() !== depositor)
    .sort((a, b) => b.assets - a.assets);
  const queue = depositor
    ? others.filter((h) => h.assets > e.position).reduce((s, h) => s + h.assets, 0)
    : null;
  const ticks = others
    .slice(0, 10)
    .map((h, i) => ({ ...h, q: others.slice(0, i + 1).reduce((sum, o) => sum + o.assets, 0) }));
  const data = useMemo(
    () =>
      Array.from({ length: 101 }, (_, i) => {
        const q = (e.total * i) / 100;
        return {
          q,
          recovered:
            e.position > 0 ? Math.min(e.position, Math.max(0, withdrawable - q)) / e.position : 0,
        };
      }),
    [e.total, e.position, withdrawable],
  );

  return (
    <div className="grid gap-8 pt-2">
      <section className="grid gap-3" aria-label="Vault liquidity">
        <HoverTooltip>
          <TooltipTrigger asChild>
            <h3 className="m-0 w-fit cursor-help">What can leave the vault now</h3>
          </TooltipTrigger>
          <TooltipContent>
            <div>Recorded at block {blockNumber(e.block)}</div>
            {e.public_allocator != null ? (
              <div>{`Public Allocator can move out up to ${num(e.public_allocator)} ${symbol}`}</div>
            ) : null}
          </TooltipContent>
        </HoverTooltip>
        <div className="flex h-8 overflow-hidden rounded-md">
          {segments
            .filter((s) => s.value > 0)
            .map((s) => (
              <HoverTooltip key={s.label}>
                <TooltipTrigger asChild>
                  <span
                    className="h-full border-r border-background last:border-r-0"
                    style={{ width: `${(100 * s.value) / e.total}%`, background: s.color }}
                  />
                </TooltipTrigger>
                <TooltipContent>
                  {`${s.label}: ${num(s.value)} ${symbol} (${percent(s.value / e.total)})`}
                  {'note' in s && s.note ? ` · ${s.note}` : ''}
                </TooltipContent>
              </HoverTooltip>
            ))}
        </div>
        <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
          {segments.map((s) => (
            <span key={s.label} className="flex items-center gap-1.5">
              <span className="size-2 rounded-full" style={{ background: s.color }} />
              {s.label}
            </span>
          ))}
        </div>
      </section>
      {e.position > 0 ? (
        <section aria-label="Exit queue">
          <h3>Your deposit recovered at par, by assets leaving ahead</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data} margin={{ left: 8, right: 16, top: 8, bottom: 4 }}>
              <CartesianGrid stroke="var(--line)" vertical={false} />
              <XAxis
                dataKey="q"
                type="number"
                domain={[0, e.total]}
                {...AXIS}
                tickFormatter={(v: number) => compactNum(v)}
              />
              <YAxis
                {...AXIS}
                domain={[0, 1]}
                tickFormatter={(v: number) => percent(v)}
                width={44}
              />
              <Tooltip
                cursor={false}
                content={(props) => (
                  <ChartTooltip
                    {...props}
                    formatLabel={(v) => `${num(Number(v), 0)} ${symbol} ahead`}
                    formatValue={(v) => percent(v)}
                  />
                )}
              />
              <Line
                dataKey="recovered"
                name="Recovered"
                type="linear"
                stroke="var(--chart-1)"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              {queue != null ? (
                <ReferenceLine
                  x={queue}
                  stroke="var(--fg)"
                  strokeDasharray="3 3"
                  label={{ value: 'You', position: 'top', fill: 'var(--fg)', fontSize: 11 }}
                />
              ) : null}
              {ticks.map((t) => (
                <ReferenceDot
                  key={t.address}
                  x={t.q}
                  y={0}
                  r={3}
                  fill={t.fast ? 'var(--chart-4)' : 'var(--muted)'}
                  stroke="none"
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-[var(--chart-4)]" />
              Contract holder ahead
            </span>
            <span className="flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-muted-foreground" />
              Other holder ahead
            </span>
          </div>
        </section>
      ) : (
        <Empty>No position in this vault.</Empty>
      )}
    </div>
  );
}
