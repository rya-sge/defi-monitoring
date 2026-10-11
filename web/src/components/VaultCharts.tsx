import { ChartTooltip } from './ChartTooltip';
import { useMemo } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { Vault } from '../api/types';
import { usd, percent } from '../lib/format';

const AXIS = {
  axisLine: false,
  tickLine: false,
  tick: { fontSize: 10, fill: 'var(--muted)', fillOpacity: 0.7 },
} as const;
/** The vault's loss, in % of its assets, if every collateral fell by the same fraction at once. */
export function VaultLossChart({ vault }: { vault: Vault }) {
  const data = useMemo(() => {
    const lif = new Map(vault.markets.map((m) => [m.id, m.lif]));
    return Array.from({ length: 51 }, (_, i) => {
      const drop = i / 100;
      const loss = vault.liquidations.reduce(
        (sum, l) =>
          sum +
          Math.max(
            0,
            l.debt_usd - (l.collateral_usd * (1 - drop)) / (lif.get(l.market ?? '') ?? 1),
          ),
        0,
      );
      return { drop, loss: loss / vault.total_assets_usd, usd: loss };
    });
  }, [vault]);

  return (
    <div>
      <h3>Vault loss if every collateral falls together</h3>
      <ResponsiveContainer width="100%" height={360}>
        <LineChart data={data} margin={{ left: 8, right: 16, top: 8, bottom: 4 }}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis
            dataKey="drop"
            {...AXIS}
            interval={4}
            tickFormatter={(v: number) => `−${percent(v)}`}
          />
          <YAxis {...AXIS} tickFormatter={(v: number) => percent(v)} width={52} />
          <Tooltip
            cursor={false}
            content={(props) => (
              <ChartTooltip
                {...props}
                formatLabel={(v) => `Collateral −${percent(Number(v))}`}
                formatValue={(v, payload) =>
                  `${percent(v)} of assets (${usd((payload as { usd: number }).usd)})`
                }
              />
            )}
          />
          <Line
            dataKey="loss"
            name="Bad debt"
            stroke="var(--chart-3)"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
