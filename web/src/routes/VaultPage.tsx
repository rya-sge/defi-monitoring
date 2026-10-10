import { useMemo } from 'react';
import { Link } from '@tanstack/react-router';
import { useSelectedTarget, useVault } from '../api/hooks';
import type { Vault } from '../api/types';
import { Empty, ErrorState, Loading } from '../components/States';
import { LiquidationChart } from '../components/LiquidationChart';
import { DistanceToLossChart, ExitLiquidityChart, VaultLossChart } from '../components/VaultCharts';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatRow } from '../components/Stat';
import type { StatProps } from '../components/Stat';
import { compactUsd, percent } from '../lib/format';
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
  const stats = useMemo<StatProps[]>(() => {
    const liquidatedAt = (fall: number) =>
      vault.liquidations.filter((l) => l.drop <= fall).reduce((sum, l) => sum + l.debt_usd, 0);
    return [
      { label: 'Total assets', value: compactUsd(vault.total_assets_usd) },
      {
        label: 'Liquidity',
        value: compactUsd(vault.liquidity_usd),
        note: percent(vault.liquidity_usd / vault.total_assets_usd, 1),
      },
      { label: 'Markets', value: String(vault.markets.length) },
      { label: 'Liquidated at −5 %', value: compactUsd(liquidatedAt(0.05)) },
      { label: 'Liquidated at −10 %', value: compactUsd(liquidatedAt(0.1)) },
    ];
  }, [vault]);

  return (
    <div className="mx-auto grid max-w-[1120px] gap-10 px-5.5 pt-9 pb-14">
      <header className="flex items-baseline justify-between gap-6">
        <h1 className="m-0 truncate">{vault.name}</h1>
        <span className="mono text-[0.8rem] text-muted-foreground">{vault.address}</span>
      </header>

      <StatRow items={stats} />

      {/* Candidate views, side by side for now: keep the ones that earn their place. */}
      <Tabs defaultValue="liquidations">
        <TabsList>
          <TabsTrigger value="liquidations">Liquidations</TabsTrigger>
          <TabsTrigger value="loss">Vault loss</TabsTrigger>
          <TabsTrigger value="distance">Distance to loss</TabsTrigger>
          <TabsTrigger value="exit">Exit liquidity</TabsTrigger>
        </TabsList>
        <TabsContent value="liquidations">
          <LiquidationChart liquidations={vault.liquidations} />
        </TabsContent>
        <TabsContent value="loss">
          <VaultLossChart vault={vault} />
        </TabsContent>
        <TabsContent value="distance">
          <DistanceToLossChart vault={vault} />
        </TabsContent>
        <TabsContent value="exit">
          <ExitLiquidityChart vault={vault} />
        </TabsContent>
      </Tabs>

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
              <TableCell className="text-right">{compactUsd(m.allocation_usd)}</TableCell>
              <TableCell className="text-right">{percent(m.share_of_vault, 1)}</TableCell>
              <TableCell className="text-right">{percent(m.utilization, 1)}</TableCell>
              <TableCell className="text-right">{compactUsd(m.liquidity_usd)}</TableCell>
              <TableCell className="text-right">{percent(m.borrow_apy, 2)}</TableCell>
              <TableCell className="text-right">{percent(m.lltv, 1)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
