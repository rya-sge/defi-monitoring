import { FormattedText } from '../components/FormattedText';
import { CHART_COLORS } from '../lib/charts';
import { useMemo } from 'react';
import { Link } from '@tanstack/react-router';
import { useSelectedTarget, useVault } from '../api/hooks';
import type { Vault } from '../api/types';
import { Empty, ErrorState, Loading } from '../components/States';
import { LiquidationChart } from '../components/LiquidationChart';
import { VaultLossChart } from '../components/VaultCharts';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Stat } from '../components/Stat';
import { usd, percent } from '../lib/format';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export function VaultPage() {
  const { target, isPending: targetPending } = useSelectedTarget();
  const address = target && !target.startsWith('user-') ? target : undefined;
  const { data, isPending, error } = useVault(address);

  if (targetPending) return <Loading what="the targets" />;
  if (!address) return <Empty>Pick a vault in the top bar.</Empty>;
  if (isPending) return <Loading what="the vault" />;
  if (error) return <ErrorState what="the vault" error={error} />;
  return <VaultView vault={data} />;
}

function VaultView({ vault }: { vault: Vault }) {
  const stats = useMemo(() => {
    const liquidatedAt = (fall: number) =>
      vault.liquidations.filter((l) => l.drop <= fall).reduce((sum, l) => sum + l.debt_usd, 0);
    return [
      {
        label: 'Liquidity',
        value: `${usd(vault.liquidity_usd)} (${percent(vault.total_assets_usd > 0 ? vault.liquidity_usd / vault.total_assets_usd : null)})`,
      },
      { label: 'Markets', value: String(vault.markets.length) },
      { label: 'Liquidated at −5 %', value: usd(liquidatedAt(0.05)) },
      { label: 'Liquidated at −10 %', value: usd(liquidatedAt(0.1)) },
    ];
  }, [vault]);

  return (
    <div className="mx-auto grid max-w-[1120px] gap-10 px-5.5 pt-9 pb-14">
      <header>
        <h1 className="m-0 truncate">{vault.name}</h1>
      </header>

      <section aria-label="Vault overview" className="grid gap-5.5 sm:grid-cols-2 sm:gap-9">
        <Stat prominent label="Total assets" value={usd(vault.total_assets_usd)} />
        <Table className="text-[0.86rem] tabular-nums">
          <TableBody>
            {stats.map(({ label, value }) => (
              <TableRow key={label}>
                <TableHead scope="row" className="font-normal text-muted-foreground">
                  {label}
                </TableHead>
                <TableCell className="text-right">{value}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </section>

      <Tabs defaultValue="liquidations">
        <TabsList>
          <TabsTrigger value="liquidations">Liquidations</TabsTrigger>
          <TabsTrigger value="loss">Vault loss</TabsTrigger>
        </TabsList>
        <TabsContent value="liquidations">
          <LiquidationChart liquidations={vault.liquidations} />
        </TabsContent>
        <TabsContent value="loss">
          <VaultLossChart vault={vault} />
        </TabsContent>
      </Tabs>

      <section aria-label="Market allocation">
        <h3>Market allocation</h3>
        <div className="flex min-h-14 rounded-md bg-muted">
          {vault.markets
            .filter((m) => m.share_of_vault > 0)
            .map((m, index) => (
              <Tooltip key={m.id}>
                <TooltipTrigger asChild>
                  <Link
                    to="/market/$marketId"
                    params={{ marketId: m.id }}
                    search={(prev) => prev}
                    aria-label={`${m.label}: ${percent(m.share_of_vault)} of vault, LLTV ${percent(m.lltv)}`}
                    className="flex min-w-0 flex-col justify-center overflow-hidden border-r border-background py-3.5 text-xs no-underline first:rounded-l-md last:rounded-r-md focus-visible:z-10"
                    style={{
                      width: `${m.share_of_vault * 100}%`,
                      background: CHART_COLORS[index % CHART_COLORS.length],
                      color: 'var(--bg)',
                    }}
                  >
                    <span className="truncate px-2">{m.label}</span>
                    <span className="truncate px-2 tabular-nums">
                      <FormattedText>{percent(m.share_of_vault)}</FormattedText>
                    </span>
                  </Link>
                </TooltipTrigger>
                <TooltipContent sideOffset={8} className="tabular-nums">
                  <div className="font-semibold">{m.label}</div>
                  <dl className="mt-1 grid grid-cols-[auto_auto] gap-x-5.5 gap-y-1">
                    <dt>Allocation</dt>
                    <dd className="text-right">{usd(m.allocation_usd)}</dd>
                    <dt>Of vault</dt>
                    <dd className="text-right">{percent(m.share_of_vault)}</dd>
                    <dt>Utilization</dt>
                    <dd className="text-right">{percent(m.utilization)}</dd>
                    <dt>Liquidity</dt>
                    <dd className="text-right">{usd(m.liquidity_usd)}</dd>
                    <dt>Borrow APY</dt>
                    <dd className="text-right">{percent(m.borrow_apy)}</dd>
                    <dt>LLTV</dt>
                    <dd className="text-right">{percent(m.lltv)}</dd>
                  </dl>
                </TooltipContent>
              </Tooltip>
            ))}
        </div>
      </section>

      <Table className="text-[0.86rem] tabular-nums">
        <TableHeader>
          <TableRow>
            <TableHead>Market</TableHead>
            <TableHead className="text-right">Allocation</TableHead>
            <TableHead className="text-right">Of vault</TableHead>
            <TableHead className="text-right">Utilization</TableHead>
            <TableHead className="text-right">Liquidity</TableHead>
            <TableHead className="text-right">Borrow APY</TableHead>
            <TableHead className="text-right">LLTV</TableHead>
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
              <TableCell className="text-right">{percent(m.utilization)}</TableCell>
              <TableCell className="text-right">{usd(m.liquidity_usd)}</TableCell>
              <TableCell className="text-right">{percent(m.borrow_apy)}</TableCell>
              <TableCell className="text-right">{percent(m.lltv)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
