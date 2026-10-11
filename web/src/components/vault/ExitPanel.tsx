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
import type { VaultExit } from '../../api/types';
import { ChartTooltip } from '../ChartTooltip';
import { Empty } from '../States';
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { blockNumber, compactNum, num, percent, shortHash } from '../../lib/format';

const AXIS = {
  axisLine: false,
  tickLine: false,
  tick: { fontSize: 10, fill: 'var(--muted)', fillOpacity: 0.7 },
} as const;

export function ExitPanel({ exit: e, symbol }: { exit: VaultExit; symbol: string }) {
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
