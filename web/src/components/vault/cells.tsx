import { cn } from 'cn';
import type { VaultMarket } from '../../api/types';
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { percent } from '../../lib/format';

// registry.json thresholds, which the frontend cannot read: watch.lender_concentration_warn,
// watch.concentration_top1_warn and watch.concentration_min_borrowers.
export const MAIN_LENDER = 0.5;
export const TOP1_WARN = 0.5;
export const MIN_BORROWERS = 5;

export function InlineBar({ value, warn = false }: { value: number; warn?: boolean }) {
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

export function OracleCell({ market: m }: { market: VaultMarket }) {
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

export function CushionCell({ market: m }: { market: VaultMarket }) {
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

export function BorrowerCell({ market: m }: { market: VaultMarket }) {
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
