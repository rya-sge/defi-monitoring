import { useMemo } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { Vault, VaultMarket } from '../api/types';
import { compactUsd, percent } from '../lib/format';

const AXIS = {
  axisLine: false,
  tickLine: false,
  tick: { fontSize: 10, fill: 'var(--muted)', fillOpacity: 0.7 },
} as const;
const TOOLTIP = {
  contentStyle: {
    background: 'var(--bg)',
    border: '1px solid var(--line)',
    borderRadius: 6,
    fontSize: 12,
  },
  cursor: { fill: 'var(--line)', opacity: 0.3 },
} as const;
const LEGEND = { wrapperStyle: { fontSize: 12 } } as const;

/** Two markets can share a collateral and a loan token: the LLTV tells them apart. */
const marketName = (m: VaultMarket) => `${m.label} · ${percent(m.lltv, 1)}`;

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
            tickFormatter={(v: number) => `−${percent(v, 0)}`}
          />
          <YAxis {...AXIS} tickFormatter={(v: number) => percent(v, 1)} width={52} />
          <Tooltip
            {...TOOLTIP}
            labelFormatter={(v) => `collateral −${percent(Number(v), 0)}`}
            formatter={(v, _name, item) => [
              `${percent(Number(v), 2)} of assets (${compactUsd((item.payload as { usd: number }).usd)})`,
              'bad debt',
            ]}
          />
          <Line
            dataKey="loss"
            stroke="var(--fg)"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Per market: the fall at which its first borrower turns into bad debt, beside the collateral's worst year. */
export function DistanceToLossChart({ vault }: { vault: Vault }) {
  const data = useMemo(
    () =>
      vault.markets.map((m) => {
        const falls = vault.liquidations
          .filter((l) => l.market === m.id && l.debt_usd > 0)
          .map((l) =>
            l.collateral_usd > 0 ? Math.max(0, 1 - (m.lif * l.debt_usd) / l.collateral_usd) : 0,
          );
        return {
          name: marketName(m),
          firstLoss: falls.length ? Math.min(...falls) : null,
          drawdown: m.collateral_drawdown_1y,
        };
      }),
    [vault],
  );

  return (
    <div>
      <h3>Fall to the first bad debt vs the collateral's worst year</h3>
      <ResponsiveContainer width="100%" height={60 + data.length * 52}>
        <BarChart
          data={data}
          layout="vertical"
          barGap={2}
          margin={{ left: 8, right: 24, top: 4, bottom: 4 }}
        >
          <CartesianGrid stroke="var(--line)" horizontal={false} />
          <XAxis type="number" {...AXIS} tickFormatter={(v: number) => percent(v, 0)} />
          <YAxis type="category" dataKey="name" {...AXIS} width={220} />
          <Tooltip {...TOOLTIP} formatter={(v) => (v == null ? '—' : percent(Number(v), 1))} />
          <Legend {...LEGEND} />
          <Bar
            dataKey="firstLoss"
            name="fall to first bad debt"
            fill="var(--fg)"
            isAnimationActive={false}
          />
          <Bar
            dataKey="drawdown"
            name="worst 1-year drawdown"
            fill="var(--muted)"
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Per market: what the vault can pull out now (the market's idle liquidity) and what stays lent. */
export function ExitLiquidityChart({ vault }: { vault: Vault }) {
  const data = useMemo(
    () =>
      vault.markets.map((m) => {
        const now = Math.min(m.allocation_usd, m.liquidity_usd);
        return { name: marketName(m), now, locked: m.allocation_usd - now };
      }),
    [vault],
  );

  return (
    <div>
      <h3>Withdrawable now vs locked, by market</h3>
      <ResponsiveContainer width="100%" height={60 + data.length * 36}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
          <CartesianGrid stroke="var(--line)" horizontal={false} />
          <XAxis type="number" {...AXIS} tickFormatter={(v: number) => compactUsd(v)} />
          <YAxis type="category" dataKey="name" {...AXIS} width={220} />
          <Tooltip {...TOOLTIP} formatter={(v) => compactUsd(Number(v))} />
          <Legend {...LEGEND} />
          <Bar
            dataKey="now"
            name="withdrawable now"
            stackId="a"
            fill="var(--fg)"
            isAnimationActive={false}
          />
          <Bar
            dataKey="locked"
            name="lent out"
            stackId="a"
            fill="var(--muted)"
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
