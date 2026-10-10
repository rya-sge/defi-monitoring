export type KpiTone = 'neutral' | 'ok' | 'warn' | 'critical';

export type KpiProps = {
  label: string;
  value: string;
  note?: string;
  tone?: KpiTone;
};

export function Kpi({ label, value, note, tone = 'neutral' }: KpiProps) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" data-tone={tone === 'neutral' ? undefined : tone}>
        {value}
      </div>
      {note ? <div className="kpi-note">{note}</div> : null}
    </div>
  );
}

export function KpiRow({ items }: { items: KpiProps[] }) {
  return (
    <div className="kpis">
      {items.map((item) => (
        <Kpi key={item.label} {...item} />
      ))}
    </div>
  );
}
