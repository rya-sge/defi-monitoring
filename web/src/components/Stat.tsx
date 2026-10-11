import { cn } from 'cn';
import { FormattedText } from './FormattedText';

export type StatTone = 'neutral' | 'ok' | 'warn' | 'critical';

export type StatProps = {
  label: string;
  value: string;
  note?: string;
  tone?: StatTone;
  prominent?: boolean;
};

const TONE: Record<'warn' | 'critical', string> = {
  warn: 'text-warn',
  critical: 'text-critical',
};

export function Stat({ label, value, note, tone = 'neutral', prominent = false }: StatProps) {
  return (
    <div>
      <div className="text-[0.8rem] text-muted-foreground">
        <FormattedText>{label}</FormattedText>
        {/* Severity is a word beside the label; the number itself is never coloured. */}
        {tone === 'warn' || tone === 'critical' ? (
          <span className={cn('ml-2 font-semibold', TONE[tone])}>{tone}</span>
        ) : null}
      </div>
      <div
        className={cn(
          'mt-1 font-semibold tracking-[-0.02em] tabular-nums',
          prominent
            ? 'text-[clamp(2.5rem,4vw,3.75rem)] leading-none font-bold'
            : 'text-xl leading-snug',
        )}
      >
        <FormattedText>{value}</FormattedText>
      </div>
      {note ? (
        <div className="mt-1 text-[0.8rem] text-muted-foreground">
          <FormattedText>{note}</FormattedText>
        </div>
      ) : null}
    </div>
  );
}

export function StatRow({ items }: { items: StatProps[] }) {
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(min(220px,100%),1fr))] gap-x-9 gap-y-5.5">
      {items.map((item) => (
        <Stat key={item.label} {...item} />
      ))}
    </div>
  );
}
