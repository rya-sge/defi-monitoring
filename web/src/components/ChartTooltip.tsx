import type { TooltipContentProps } from 'recharts';
import { num } from '../lib/format';
import { CHART_COLORS } from '../lib/charts';
import { FormattedText } from './FormattedText';

type Props = TooltipContentProps & {
  formatValue?: (value: number, payload: unknown) => string;
  formatLabel?: (label: unknown) => string;
};

export function ChartTooltip({
  active,
  payload,
  label,
  formatValue = (value) => num(value),
  formatLabel = String,
}: Props) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tooltip-surface max-w-80 tabular-nums">
      {label != null ? (
        <div className="mb-1 font-semibold">
          <FormattedText>{formatLabel(label)}</FormattedText>
        </div>
      ) : null}
      {payload.map((item, index) => (
        <div key={String(item.dataKey ?? index)} className="flex items-center gap-2 py-0.5">
          <span
            className="size-2 shrink-0 rounded-full"
            style={{ background: item.color ?? CHART_COLORS[index % CHART_COLORS.length] }}
          />
          <span className="text-muted-foreground">{String(item.name ?? 'Value')}</span>
          <span className="ml-auto pl-3">
            <FormattedText>{formatValue(Number(item.value), item.payload)}</FormattedText>
          </span>
        </div>
      ))}
    </div>
  );
}
