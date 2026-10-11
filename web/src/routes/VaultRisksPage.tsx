import { useCallback, useMemo, useState } from 'react';
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
import { useAlerts, useGraph, useIncidentImpact, useSelectedTarget, useVault } from '../api/hooks';
import { GRAPH_NODE_KINDS } from '../api/types';
import type { Alert, GraphNodeKind, Vault, VaultExit, VaultMarket } from '../api/types';
import { ChartTooltip } from '../components/ChartTooltip';
import { GraphCanvas, KindFilter } from '../components/GraphCanvas';
import { LiquidationChart } from '../components/LiquidationChart';
import { Stat } from '../components/Stat';
import { Empty, ErrorState, Loading } from '../components/States';
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
import {
  blockNumber,
  compactNum,
  detailValue,
  etherscanUrl,
  num,
  percent,
  shortHash,
  usd,
} from '../lib/format';
import { badDebt, badDebtBy } from '../lib/risk';
import {
  KIND_COLOR,
  adjacent,
  flowLit,
  nodeAmount,
  pathNodes,
  pointsOfFailure,
} from '../lib/graph';
import type { Lit } from '../lib/graph';
import { useTwinGroups } from '../lib/useTwinGroups';
import { Button } from '@/components/ui/button';

// registry.json thresholds, which the frontend cannot read: watch.lender_concentration_warn,
// watch.concentration_top1_warn and watch.concentration_min_borrowers.
const COLUMNS = [
  { name: 'Market', why: 'Collateral / loan token of the Morpho Blue market the vault lends to' },
  { name: 'Allocation', right: true, why: 'USD the vault lends in this market' },
  {
    name: 'Of vault',
    right: true,
    why: "Allocation ÷ the vault's total: the higher, the more a problem here reaches your position",
  },
  {
    name: 'Of market',
    why: "The vault's share of the market's lenders. Main lender at 50%: the vault takes most of any loss and is drained first",
  },
  {
    name: 'Oracle',
    why: 'Tracks price: a collateral fall liquidates borrowers. Constant price: fixed, NAV or exchange rate; nobody is liquidated on a depeg and lenders take the loss. A red ring marks a stale feed',
  },
  {
    name: 'Cushion',
    why: "Light mark: 1 − LLTV, the fall that brings a borrower at max leverage to collateral = debt. Grey or red mark: the collateral's worst 1-year fall. Red: history already went past the cushion. The liquidation incentive makes bad debt start slightly earlier",
  },
  {
    name: 'Top borrower',
    why: "The largest borrower's share of the market's debt. Warns at 50% or under 5 borrowers: the loss is not spread",
  },
  {
    name: 'Utilization',
    right: true,
    why: 'Borrowed ÷ supplied. Near 100%, almost nothing can be withdrawn from this market',
  },
  {
    name: 'LLTV',
    right: true,
    why: 'Loan-to-value at which a borrower is liquidated. The higher, the thinner the cushion',
  },
];
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
  const ofAllocation = (keep: (m: VaultMarket) => boolean) =>
    vault.markets.filter(keep).reduce((sum, m) => sum + m.share_of_vault, 0);
  const leavable = exit ? exit.plain + exit.forced : 0;
  const run = exit?.holders
    .filter((h) => h.address !== exit.depositor)
    .slice(0, 3)
    .reduce((sum, h) => sum + h.assets, 0);
  const tolerated = Array.from({ length: 101 }, (_, i) => i / 100).find(
    (d) => loss(d) > 0.01 * vault.total_assets_usd,
  );
  const drawdowns = new Map(vault.markets.map((m) => [m.id, m.collateral_drawdown_1y]));
  const atWorst = badDebtBy(vault, (id) => drawdowns.get(id) ?? null);
  const skipped = vault.markets.filter((m) => m.collateral_drawdown_1y == null).length;
  const figures = [
    {
      label: 'Your exit now',
      tip: 'Share of your position that can leave at par now: idle, liquidity market and forceDeallocate',
      value: exit && exit.position > 0 ? percent(Math.min(1, leavable / exit.position)) : '—',
    },
    {
      label: 'Run coverage',
      tip: 'What can leave now ÷ the three largest other holders: below 1×, they alone empty it',
      value: run ? `${num(leavable / run, 1)}×` : '—',
      critical: !!run && leavable < run,
    },
    {
      label: 'Distance to bad debt',
      tip: 'The uniform collateral fall at which bad debt passes 1% of the vault',
      value: tolerated == null ? '> −100%' : `−${percent(tolerated)}`,
    },
    {
      label: 'Loss at historical worst',
      tip: `Bad debt if each collateral fell by its worst 1-year drawdown${skipped ? `; ${skipped} market${skipped > 1 ? 's' : ''} without history left out` : ''}`,
      value: `${usd(atWorst)} (${percent(vault.total_assets_usd > 0 ? atWorst / vault.total_assets_usd : null)})`,
      critical: atWorst > 0,
    },
    {
      label: 'Behind constant-price oracles',
      tip: 'Allocation in markets whose oracle does not follow the collateral: a depeg liquidates nobody',
      value: vault.markets.some((m) => m.oracle_class != null)
        ? percent(ofAllocation((m) => m.oracle_class === 'constant-price'))
        : '—',
    },
    {
      label: 'Concentrated',
      tip: 'Allocation in markets with one borrower above half the debt, or where the vault is the main lender',
      value: percent(
        ofAllocation((m) => (m.top1_share ?? 0) >= TOP1_WARN || m.share_of_market >= MAIN_LENDER),
      ),
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
                <TableHead scope="row" className="w-full max-w-0 font-normal text-muted-foreground">
                  <HoverTooltip>
                    <TooltipTrigger asChild>
                      <span className="block cursor-help truncate">{item.label}</span>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-72">{item.tip}</TooltipContent>
                  </HoverTooltip>
                </TableHead>
                <TableCell
                  className={cn('text-right whitespace-nowrap', item.critical && 'text-critical')}
                >
                  {item.value}
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
          <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
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
        <TabsContent value="dependencies">
          <Dependencies vault={vault} />
        </TabsContent>
      </Tabs>

      <Table className="text-[0.86rem] tabular-nums">
        <TableHeader>
          <TableRow>
            {COLUMNS.map(({ name, right, why }) => (
              <TableHead key={name} className={right ? 'text-right' : undefined}>
                <HoverTooltip>
                  <TooltipTrigger asChild>
                    <span className="cursor-help">{name}</span>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-72">{why}</TooltipContent>
                </HoverTooltip>
              </TableHead>
            ))}
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
  const recoveredAt = (q: number) =>
    e.position > 0 ? Math.min(e.position, Math.max(0, withdrawable - q)) / e.position : 0;
  const ticks = others
    .slice(0, 10)
    .map((h, i) => ({ ...h, q: others.slice(0, i + 1).reduce((sum, o) => sum + o.assets, 0) }));
  const data = Array.from({ length: 101 }, (_, i) => {
    const q = (e.total * i) / 100;
    return { q, recovered: recoveredAt(q) };
  });

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
            <LineChart data={data} margin={{ left: 8, right: 16, top: 20, bottom: 4 }}>
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
                  shape={({ cx, cy }: { cx?: number; cy?: number }) => (
                    <HoverTooltip>
                      <TooltipTrigger asChild>
                        <g className="cursor-help">
                          <circle cx={cx} cy={cy} r={8} fill="transparent" />
                          <circle
                            cx={cx}
                            cy={cy}
                            r={3}
                            fill={t.fast ? 'var(--chart-4)' : 'var(--muted)'}
                          />
                        </g>
                      </TooltipTrigger>
                      <TooltipContent className="tabular-nums">
                        <div className="font-semibold">{shortHash(t.address)}</div>
                        <div>{`${num(t.assets)} ${symbol} (${percent(t.assets / e.total)} of vault)`}</div>
                        <div>{`${num(t.q)} ${symbol} gone once it leaves`}</div>
                        <div>{`You recover ${percent(recoveredAt(t.q))}`}</div>
                      </TooltipContent>
                    </HoverTooltip>
                  )}
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

const FALLS = [0.1, 0.3, 0.5];
const VERDICT = { STAY: 'text-ok', REDUCE: 'text-warn', EXIT: 'text-critical' };

/** The vault's own graph with what it relies on, the risk rings and a shock run from an asset. */
function Dependencies({ vault }: { vault: Vault }) {
  const { data, isPending, error, dataUpdatedAt } = useGraph({ vault: vault.address });
  const twins = useTwinGroups(data);
  const graph = twins.graph;
  const [picked, setPicked] = useState<string | null>(null);
  // Level 1 around the vault by default; a click reveals more (D207).
  const [revealed, setRevealed] = useState<ReadonlySet<string>>(new Set());
  const [hiddenKinds, setHiddenKinds] = useState<ReadonlySet<GraphNodeKind>>(
    new Set(['Admin', 'External']),
  );
  const reveal = (ids: string[]) => setRevealed((previous) => new Set([...previous, ...ids]));
  const shown = useMemo(() => {
    if (!graph) return undefined;
    const ids = new Set([vault.address, ...adjacent(vault.address, graph.edges), ...revealed]);
    return {
      nodes: graph.nodes.filter((n) => ids.has(n.id)),
      edges: graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target)),
    };
  }, [graph, vault.address, revealed]);
  const [fall, setFall] = useState<number | null>(null);
  const node = graph?.nodes.find((n) => n.id === picked);
  const shock = node?.kind === 'Asset' && fall != null ? `token=${node.label}:${fall}` : null;
  const incident = useIncidentImpact(
    { vaults: [vault.address], shocks: shock ? [shock] : [], horizon: 30 },
    shock != null,
  );
  const result = shock ? incident.data?.vaults[0] : undefined;

  const points = useMemo(() => {
    if (!graph) return [];
    const all = pointsOfFailure(vault.address, graph.edges);
    const total = graph.edges
      .filter((e) => e.source === vault.address && e.rel === 'supplies')
      .reduce((sum, e) => sum + (e.amount ?? 0), 0);
    return all.flatMap((p) => {
      const n = graph.nodes.find((candidate) => candidate.id === p.id);
      return n && n.kind !== 'Pool'
        ? [{ ...p, node: n, share: total ? p.amount / total : null }]
        : [];
    });
  }, [graph, vault.address]);

  const hits = useMemo(() => {
    const ids = new Set(result?.hits.map((h) => h.market_id.toLowerCase()));
    return new Set(
      graph?.nodes
        .filter((n) => ids.has(n.id.toLowerCase()) || ids.has(detailValue(n.details.market_id)))
        .map((n) => n.id),
    );
  }, [graph, result]);

  const overlay = useMemo(() => {
    if (!graph) return undefined;
    const markets = new Map(vault.markets.map((m) => [m.id.toLowerCase(), m]));
    const out: Record<string, { ring?: string; amount: string[] }> = {};
    for (const n of graph.nodes) {
      const d = n.details;
      const market = markets.get(n.id.toLowerCase());
      const ring =
        n.id === picked
          ? 'var(--fg)'
          : hits.has(n.id) || (n.kind === 'Oracle' && d.stale === true)
            ? 'var(--critical)'
            : (market &&
                  (d.oracle_class === 'constant-price' || (market.top1_share ?? 0) >= TOP1_WARN)) ||
                /^[DF]/.test(detailValue(d.pharos_grade))
              ? 'var(--warn)'
              : undefined;
      if (ring) out[n.id] = { ring, amount: nodeAmount(n, graph.edges) };
    }
    return out;
  }, [graph, vault.markets, picked, hits]);

  const focus = useMemo<Lit>(() => {
    if (!graph) return null;
    const from = hits.size ? [...hits] : picked ? [picked] : [];
    if (!from.length) return null;
    const lit = { nodes: new Set<string>(), edges: new Set<string>() };
    for (const id of from) {
      const flow = flowLit(id, id, graph.edges);
      flow.nodes.forEach((n) => lit.nodes.add(n));
      flow.edges.forEach((e) => lit.edges.add(e));
    }
    return lit;
  }, [graph, hits, picked]);

  if (isPending) return <Loading what="the dependency graph" />;
  if (error) return <ErrorState what="the dependency graph" error={error} />;
  if (!graph || !shown) return null;

  const pick = (id: string | null) => {
    setPicked(id);
    setFall(null);
  };

  return (
    <div className="grid gap-6 pt-2 lg:grid-cols-[minmax(0,1fr)_300px]">
      <div className="grid gap-2">
        <div className="relative h-[560px] overflow-hidden rounded-md border">
          <GraphCanvas
            key={`${vault.address}-${dataUpdatedAt}-${twins.layoutKey}-${shown.nodes.length}`}
            nodes={shown.nodes}
            edges={shown.edges}
            visibleKinds={new Set(GRAPH_NODE_KINDS.filter((kind) => !hiddenKinds.has(kind)))}
            search=""
            selection={null}
            onSelect={(next) => {
              if (next?.type === 'node') {
                if (!twins.open(next.node)) {
                  pick(next.node.id);
                  reveal(adjacent(next.node.id, graph.edges));
                }
              } else if (!next) pick(null);
            }}
            focus={focus}
            overlay={overlay}
          />
          <KindFilter
            kinds={GRAPH_NODE_KINDS.filter((kind) => shown.nodes.some((n) => n.kind === kind))}
            hidden={hiddenKinds}
            onToggle={(kind) =>
              setHiddenKinds((previous) => {
                const next = new Set(previous);
                if (!next.delete(kind)) next.add(kind);
                return next;
              })
            }
            className="absolute bottom-3.5 left-3.5"
          />
        </div>
        <div className="flex gap-5 text-xs text-muted-foreground">
          {[
            ['var(--warn)', 'Warning'],
            ['var(--critical)', 'Critical'],
          ].map(([colour, word]) => (
            <span key={word} className="flex items-center gap-1.5">
              <span className="size-2 rounded-full" style={{ background: colour }} />
              {word}
            </span>
          ))}
        </div>
      </div>
      <aside className="grid content-start gap-6">
        <section aria-label="Points of failure">
          <HoverTooltip>
            <TooltipTrigger asChild>
              <h3 className="mt-0 w-fit cursor-help">Points of failure</h3>
            </TooltipTrigger>
            <TooltipContent className="max-w-72">
              {"What the vault's supply relies on, through the markets it lends to"}
            </TooltipContent>
          </HoverTooltip>
          <Table className="text-[0.86rem] tabular-nums">
            <TableBody>
              {points.slice(0, 8).map((p) => (
                <TableRow
                  key={p.id}
                  data-state={p.id === picked ? 'selected' : undefined}
                  className="cursor-pointer"
                  onClick={() => {
                    pick(p.id);
                    reveal(pathNodes(vault.address, p.id, graph.edges));
                  }}
                >
                  <TableCell className="w-full max-w-0">
                    <HoverTooltip>
                      <TooltipTrigger asChild>
                        <span className="flex items-center gap-2">
                          <span
                            className="size-2 shrink-0"
                            style={{ background: KIND_COLOR[p.node.kind] }}
                          />
                          <span className="truncate">{p.node.label}</span>
                        </span>
                      </TooltipTrigger>
                      <TooltipContent>{`${p.node.label} · ${num(p.amount)} ${p.unit ?? ''}`}</TooltipContent>
                    </HoverTooltip>
                  </TableCell>
                  <TableCell className="text-right whitespace-nowrap">{percent(p.share)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>
        {node ? (
          <section className="grid gap-3" aria-label="Selected node">
            <h3 className="m-0 truncate">{node.label}</h3>
            {node.kind === 'Asset' ? (
              <>
                <div className="flex gap-2">
                  {FALLS.map((f) => (
                    <Button
                      key={f}
                      type="button"
                      size="sm"
                      variant={fall === f ? 'default' : 'outline'}
                      onClick={() => setFall(f)}
                    >
                      −{percent(f)}
                    </Button>
                  ))}
                </div>
                {shock && incident.isPending ? (
                  <span className="text-xs text-muted-foreground">Running the shock…</span>
                ) : null}
                {shock && incident.error ? (
                  <span className="text-xs text-muted-foreground">{incident.error.message}</span>
                ) : null}
                {result ? (
                  <Table className="text-[0.86rem] tabular-nums">
                    <TableBody>
                      {[
                        {
                          label: 'Verdict',
                          value: (
                            <span className={cn('font-semibold', VERDICT[result.verdict])}>
                              {result.hits.length ? result.verdict.toLowerCase() : 'Unaffected'}
                            </span>
                          ),
                        },
                        {
                          label: 'Vault loss',
                          value: `${num(result.vault_loss)} ${result.symbol}`,
                        },
                        {
                          label: 'Position loss',
                          value: `${num(result.loss_if_stay)} ${result.symbol}`,
                        },
                        { label: 'Markets hit', value: String(result.hits.length) },
                      ].map(({ label, value }) => (
                        <TableRow key={label}>
                          <TableHead scope="row" className="font-normal text-muted-foreground">
                            {label}
                          </TableHead>
                          <TableCell className="text-right whitespace-nowrap">{value}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : null}
                {result ? (
                  <Button asChild variant="ghost">
                    <Link to="/incident" search={(prev) => ({ ...prev, target: vault.address })}>
                      Open incident
                    </Link>
                  </Button>
                ) : null}
              </>
            ) : null}
          </section>
        ) : null}
      </aside>
    </div>
  );
}
