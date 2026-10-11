// Should I keep this vault, and if it turns bad, how much can I get out, how fast and at what price?
import { useCallback, useState } from 'react';
import { Link } from '@tanstack/react-router';
import { useGraph, useMarket, useSelectedTarget, useShockSweep, useVault } from '../api/hooks';
import type { GraphNodeKind, Vault } from '../api/types';
import { LiquidationChart } from '../components/LiquidationChart';
import { Stat } from '../components/Stat';
import { Empty, ErrorState, Loading } from '../components/States';
import { Changes } from '../components/vault/Changes';
import { ExitPanel } from '../components/vault/ExitPanel';
import { RiskFigures } from '../components/vault/figures';
import { MarketDetail } from '../components/vault/MarketDetail';
import { MarketsTable } from '../components/vault/MarketsTable';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { KIND_COLOR, pointsOfFailure } from '../lib/graph';
import { num, percent, usd } from '../lib/format';
import { badDebt } from '../lib/risk';

export function VaultHubPage() {
  const { target, isPending: targetPending } = useSelectedTarget();
  const address = target && !target.startsWith('user-') ? target : undefined;
  const { data, isPending, error } = useVault(address);

  if (targetPending) return <Loading what="the targets" />;
  if (!address) return <Empty>Pick a vault in the top bar.</Empty>;
  if (isPending) return <Loading what="the vault" />;
  if (error) return <ErrorState what="the vault" error={error} />;
  return <VaultHub key={data.address} vault={data} />;
}

function VaultHub({ vault }: { vault: Vault }) {
  const [market, setMarket] = useState<string | null>(null);
  const loss = useCallback((drop: number) => badDebt(vault, drop), [vault]);

  return (
    <div className="mx-auto grid max-w-[1120px] gap-10 px-5.5 pt-9 pb-14">
      <Changes vault={vault} />
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="exposures">Exposures</TabsTrigger>
          <TabsTrigger value="exit">Exit</TabsTrigger>
          <TabsTrigger value="failure">Points of failure</TabsTrigger>
        </TabsList>
        <TabsContent value="overview" className="pt-4">
          <section className="grid gap-5.5 sm:grid-cols-2 sm:gap-9" aria-label="Vault risks">
            <Stat prominent label="Total assets" value={usd(vault.total_assets_usd)} />
            <RiskFigures vault={vault} />
          </section>
        </TabsContent>
        <TabsContent value="exposures" className="grid gap-8 pt-4">
          <MarketsTable vault={vault} onSelect={setMarket} />
          <LiquidationChart liquidations={vault.liquidations} badDebt={loss} />
        </TabsContent>
        <TabsContent value="exit">
          {vault.exit ? (
            <ExitPanel exit={vault.exit} symbol={vault.asset_symbol} />
          ) : (
            <Empty>No recorded state for this vault.</Empty>
          )}
        </TabsContent>
        <TabsContent value="failure" className="pt-4">
          <PointsOfFailure vault={vault} />
        </TabsContent>
      </Tabs>
      <Sheet open={market != null} onOpenChange={(open) => !open && setMarket(null)}>
        <SheetContent className="w-full overflow-auto sm:max-w-2xl">
          {market ? <MarketSheet id={market} /> : null}
        </SheetContent>
      </Sheet>
    </div>
  );
}

function MarketSheet({ id }: { id: string }) {
  const { data, isPending, error } = useMarket(id);
  return (
    <>
      <SheetHeader>
        <SheetTitle>{data?.label ?? 'Market'}</SheetTitle>
      </SheetHeader>
      <div className="grid gap-8 px-4 pb-6">
        {isPending ? (
          <Loading what="the market" />
        ) : error ? (
          <ErrorState what="the market" error={error} />
        ) : (
          <MarketDetail market={data} />
        )}
      </div>
    </>
  );
}

const SWEEP = { mode: 'reads-low', size: '10%' } as const;

/** The engine's sweep: each oracle and feed reading 10 % low in turn, ranked by the vault's loss. */
function PointsOfFailure({ vault }: { vault: Vault }) {
  const sweep = useShockSweep({ vault: [vault.address], ...SWEEP });
  if (sweep.isPending) return <Loading what="the sweep" />;
  if (sweep.error) return <GraphPoints vault={vault} />;
  return (
    <Table className="text-[0.86rem] tabular-nums">
      <TableHeader>
        <TableRow>
          <TableHead>Reads 10% low</TableHead>
          <TableHead className="text-right">Vault loss</TableHead>
          <TableHead className="text-right">Markets hit</TableHead>
          <TableHead>Worst market</TableHead>
          <TableHead />
        </TableRow>
      </TableHeader>
      <TableBody>
        {sweep.data.ranking.map((r) => (
          <TableRow key={r.node}>
            <TableCell className="max-w-72">
              <NodeLabel kind={r.kind} label={r.label} />
            </TableCell>
            <TableCell className="text-right whitespace-nowrap">
              {num(r.vault_loss)} {vault.asset_symbol}
            </TableCell>
            <TableCell className="text-right">{r.markets_hit}</TableCell>
            <TableCell className="max-w-56 truncate">{r.worst_market ?? '—'}</TableCell>
            <TableCell className="text-right">
              <Simulate vault={vault.address} trace={`${r.node}:${SWEEP.mode}:${SWEEP.size}`} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

/** Without a recorded sweep: what the vault's supply reaches in its graph, by amount exposed. */
function GraphPoints({ vault }: { vault: Vault }) {
  const { data: graph, isPending, error } = useGraph({ vault: vault.address });
  if (isPending) return <Loading what="the dependency graph" />;
  if (error) return <ErrorState what="the dependency graph" error={error} />;
  const supplied = graph.edges
    .filter((e) => e.source === vault.address && e.rel === 'supplies')
    .reduce((sum, e) => sum + (e.amount ?? 0), 0);
  const points = pointsOfFailure(vault.address, graph.edges).flatMap((p) => {
    const node = graph.nodes.find((n) => n.id === p.id);
    return node && (node.kind === 'Oracle' || node.kind === 'Asset') ? [{ ...p, node }] : [];
  });
  if (!points.length) return <Empty>No point of failure found.</Empty>;
  return (
    <Table className="text-[0.86rem] tabular-nums">
      <TableHeader>
        <TableRow>
          <TableHead>Dependency</TableHead>
          <TableHead className="text-right">Supply exposed</TableHead>
          <TableHead className="text-right">Of vault</TableHead>
          <TableHead />
        </TableRow>
      </TableHeader>
      <TableBody>
        {points.slice(0, 15).map((p) => (
          <TableRow key={p.id}>
            <TableCell className="max-w-72">
              <NodeLabel kind={p.node.kind} label={p.node.label} />
            </TableCell>
            <TableCell className="text-right whitespace-nowrap">
              {num(p.amount)} {p.unit ?? ''}
            </TableCell>
            <TableCell className="text-right">
              {percent(supplied ? p.amount / supplied : null)}
            </TableCell>
            <TableCell className="text-right">
              <Simulate
                vault={vault.address}
                trace={`${p.id}:${p.node.kind === 'Asset' ? 'price' : SWEEP.mode}:${SWEEP.size}`}
              />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function NodeLabel({ kind, label }: { kind: string; label: string }) {
  const colour = KIND_COLOR[kind as GraphNodeKind] as string | undefined;
  return (
    <span className="flex items-center gap-2">
      <span className="size-2 shrink-0" style={{ background: colour ?? 'var(--muted)' }} />
      <span className="truncate">{label}</span>
    </span>
  );
}

function Simulate({ vault, trace }: { vault: string; trace: string }) {
  return (
    <Button asChild size="sm" variant="ghost">
      <Link to="/scenario" search={(prev) => ({ ...prev, target: vault, trace })}>
        Simulate
      </Link>
    </Button>
  );
}
