export type StatTone = 'neutral' | 'ok' | 'warn' | 'critical';

export type StatProps = {
  label: string;
  value: string;
  note?: string;
  tone?: StatTone;
};

export function Stat({ label, value, note, tone = 'neutral' }: StatProps) {
  return (
    <div>
      <div className="stat-label">{label}</div>
      <div className="stat-value" data-tone={tone === 'neutral' ? undefined : tone}>
        {value}
      </div>
      {note ? <div className="stat-note">{note}</div> : null}
    </div>
  );
}

export function StatRow({ items }: { items: StatProps[] }) {
  return (
    <div className="stats">
      {items.map((item) => (
        <Stat key={item.label} {...item} />
      ))}
    </div>
  );
}
