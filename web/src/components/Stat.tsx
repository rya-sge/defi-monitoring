import { cn } from 'cn';

export type StatTone = 'neutral' | 'ok' | 'warn' | 'critical';

export type StatProps = {
  label: string;
  value: string;
  note?: string;
  tone?: StatTone;
};

const TONE: Record<Exclude<StatTone, 'neutral'>, string> = {
  ok: 'text-ok',
  warn: 'text-warn',
  critical: 'text-critical',
};

export function Stat({ label, value, note, tone = 'neutral' }: StatProps) {
  return (
    <div>
      <div className="text-[0.8rem] text-muted-foreground">{label}</div>
      <div
        className={cn(
          'mt-1 font-mono text-2xl font-semibold tracking-[-0.02em] tabular-nums',
          tone !== 'neutral' && TONE[tone],
        )}
      >
        {value}
      </div>
      {note ? <div className="mt-1 text-[0.8rem] text-muted-foreground">{note}</div> : null}
    </div>
  );
}

export function StatRow({ items }: { items: StatProps[] }) {
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(min(190px,100%),1fr))] gap-x-9 gap-y-5.5">
      {items.map((item) => (
        <Stat key={item.label} {...item} />
      ))}
    </div>
  );
}
