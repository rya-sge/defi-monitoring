import { useCallback, useMemo, useState } from 'react';
import { Link } from '@tanstack/react-router';
import { cn } from 'cn';
import { useGraph, useIncidentImpact, useSelectedTarget, useVault } from '../../api/hooks';
import { GRAPH_NODE_KINDS } from '../../api/types';
import type { GraphNodeKind, Vault } from '../../api/types';
import { ExpandAll, GraphCanvas, KindFilter } from '../../components/GraphCanvas';
import { LiquidationChart } from '../../components/LiquidationChart';
import { Stat } from '../../components/Stat';
import { Empty, ErrorState, Loading } from '../../components/States';
import { TOP1_WARN } from '../../components/vault/cells';
import { Changes } from '../../components/vault/Changes';
import { ExitPanel } from '../../components/vault/ExitPanel';
import { RiskFigures } from '../../components/vault/figures';
import { MarketsTable } from '../../components/vault/MarketsTable';
import { Table, TableBody, TableCell, TableHead, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { detailValue, num, percent, usd } from '../../lib/format';
import { badDebt } from '../../lib/risk';
import { KIND_COLOR, flowLit, nodeAmount, pointsOfFailure } from '../../lib/graph';
import type { Lit } from '../../lib/graph';
import { useReveal } from '../../lib/useReveal';
import { useTwinGroups } from '../../lib/useTwinGroups';
import { Button } from '@/components/ui/button';

export function VaultRisksPage() {
  const { target, isPending: targetPending } = useSelectedTarget();
  const address = target && !target.startsWith('user-') ? target : undefined;
  const { data, isPending, error } = useVault(address);

  if (targetPending) return <Loading what="the targets" />;
  if (!address) return <Empty>Pick a vault in the top bar.</Empty>;
  if (isPending) return <Loading what="the vault" />;
  if (error) return <ErrorState what="the vault" error={error} />;
  return <VaultRisksView vault={data} />;
}
function VaultRisksView({ vault }: { vault: Vault }) {
  const exit = vault.exit ?? null;
  const loss = useCallback((drop: number) => badDebt(vault, drop), [vault]);
  return (
    <div className="mx-auto grid max-w-[1120px] gap-10 px-5.5 pt-9 pb-14">
      <Changes vault={vault} />

      <section aria-label="Vault risks overview" className="grid gap-5.5 sm:grid-cols-2 sm:gap-9">
        <Stat prominent label="Total assets" value={usd(vault.total_assets_usd)} />
        <RiskFigures vault={vault} />
      </section>

      <Tabs defaultValue="exit">
        <TabsList>
          <TabsTrigger value="exit">Exit</TabsTrigger>
          <TabsTrigger value="liquidations">Liquidations</TabsTrigger>
          <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
        </TabsList>
        <TabsContent value="exit">
          {exit ? (
            <ExitPanel exit={exit} symbol={vault.asset_symbol} />
          ) : (
            <Empty>No recorded state for this vault.</Empty>
          )}
        </TabsContent>
        <TabsContent value="liquidations">
          <LiquidationChart liquidations={vault.liquidations} badDebt={loss} />
        </TabsContent>
        <TabsContent value="dependencies">
          <Dependencies vault={vault} />
        </TabsContent>
      </Tabs>

      <MarketsTable vault={vault} />
    </div>
  );
}

const FALLS = [0.1, 0.3, 0.5];
const VERDICT = { STAY: 'text-ok', REDUCE: 'text-warn', EXIT: 'text-critical' };

/** The vault's own graph with what it relies on, the risk rings and a shock run from an asset. */
function Dependencies({ vault }: { vault: Vault }) {
  const { data, isPending, error, dataUpdatedAt } = useGraph({ vault: vault.address });
  const twins = useTwinGroups(data);
  const graph = twins.graph;
  const [picked, setPicked] = useState<string | null>(null);
  // Level 1 around the vault by default; a click opens or closes a node (D212).
  const reveal = useReveal(graph, vault.address);
  const shown = reveal.graph;
  const [hiddenKinds, setHiddenKinds] = useState<ReadonlySet<GraphNodeKind>>(
    new Set(['Admin', 'External']),
  );
  const [fall, setFall] = useState<number | null>(null);
  const node = graph?.nodes.find((n) => n.id === picked);
  const shock = node?.kind === 'Asset' && fall != null ? `token=${node.label}:${fall}` : null;
  const incident = useIncidentImpact(
    { vaults: [vault.address], shocks: shock ? [shock] : [], horizon: 30 },
    shock != null,
  );
  const result = shock ? incident.data?.vaults[0] : undefined;

  const points = useMemo(() => {
    if (!graph) return [];
    const all = pointsOfFailure(vault.address, graph.edges);
    const total = graph.edges
      .filter((e) => e.source === vault.address && e.rel === 'supplies')
      .reduce((sum, e) => sum + (e.amount ?? 0), 0);
    return all.flatMap((p) => {
      const n = graph.nodes.find((candidate) => candidate.id === p.id);
      return n && n.kind !== 'Pool'
        ? [{ ...p, node: n, share: total ? p.amount / total : null }]
        : [];
    });
  }, [graph, vault.address]);

  const hits = useMemo(() => {
    const ids = new Set(result?.hits.map((h) => h.market_id.toLowerCase()));
    return new Set(
      graph?.nodes
        .filter((n) => ids.has(n.id.toLowerCase()) || ids.has(detailValue(n.details.market_id)))
        .map((n) => n.id),
    );
  }, [graph, result]);

  const overlay = useMemo(() => {
    if (!graph) return undefined;
    const markets = new Map(vault.markets.map((m) => [m.id.toLowerCase(), m]));
    const out: Record<string, { ring?: string; amount: string[] }> = {};
    for (const n of graph.nodes) {
      const d = n.details;
      const market = markets.get(n.id.toLowerCase());
      const ring =
        n.id === picked
          ? 'var(--fg)'
          : hits.has(n.id) || (n.kind === 'Oracle' && d.stale === true)
            ? 'var(--critical)'
            : (market &&
                  (d.oracle_class === 'constant-price' || (market.top1_share ?? 0) >= TOP1_WARN)) ||
                /^[DF]/.test(detailValue(d.pharos_grade))
              ? 'var(--warn)'
              : undefined;
      if (ring) out[n.id] = { ring, amount: nodeAmount(n, graph.edges) };
    }
    return out;
  }, [graph, vault.markets, picked, hits]);

  const focus = useMemo<Lit>(() => {
    if (!graph) return null;
    const from = hits.size ? [...hits] : picked ? [picked] : [];
    if (!from.length) return null;
    const lit = { nodes: new Set<string>(), edges: new Set<string>() };
    for (const id of from) {
      const flow = flowLit(id, id, graph.edges);
      flow.nodes.forEach((n) => lit.nodes.add(n));
      flow.edges.forEach((e) => lit.edges.add(e));
    }
    return lit;
  }, [graph, hits, picked]);

  if (isPending) return <Loading what="the dependency graph" />;
  if (error) return <ErrorState what="the dependency graph" error={error} />;
  if (!graph || !shown) return null;
  const visibleKinds = new Set(GRAPH_NODE_KINDS.filter((kind) => !hiddenKinds.has(kind)));

  const pick = (id: string | null) => {
    setPicked(id);
    setFall(null);
  };

  return (
    <div className="grid gap-6 pt-2 lg:grid-cols-[minmax(0,1fr)_300px]">
      <div className="grid gap-2">
        <div className="relative h-[560px] overflow-hidden rounded-md border">
          <GraphCanvas
            key={`${vault.address}-${dataUpdatedAt}-${twins.layoutKey}`}
            positions={reveal.positions}
            nodes={shown.nodes}
            edges={shown.edges}
            visibleKinds={visibleKinds}
            more={reveal.more(visibleKinds)}
            search=""
            selection={null}
            onSelect={(next) => {
              if (next?.type === 'node') {
                if (!twins.open(next.node)) {
                  pick(next.node.id);
                  reveal.toggle(next.node.id);
                }
              } else if (!next) pick(null);
            }}
            focus={focus}
            overlay={overlay}
          />
          <ExpandAll
            all={reveal.all}
            onExpand={reveal.expandAll}
            onCollapse={reveal.collapseAll}
            className="absolute top-3.5 left-3.5"
          />
          <KindFilter
            kinds={GRAPH_NODE_KINDS.filter((kind) => shown.nodes.some((n) => n.kind === kind))}
            hidden={hiddenKinds}
            onToggle={(kind) =>
              setHiddenKinds((previous) => {
                const next = new Set(previous);
                if (!next.delete(kind)) next.add(kind);
                return next;
              })
            }
            className="absolute bottom-3.5 left-3.5"
          />
        </div>
        <div className="flex gap-5 text-xs text-muted-foreground">
          {[
            ['var(--warn)', 'Warning'],
            ['var(--critical)', 'Critical'],
          ].map(([colour, word]) => (
            <span key={word} className="flex items-center gap-1.5">
              <span className="size-2 rounded-full" style={{ background: colour }} />
              {word}
            </span>
          ))}
        </div>
      </div>
      <aside className="grid content-start gap-6">
        <section aria-label="Points of failure">
          <HoverTooltip>
            <TooltipTrigger asChild>
              <h3 className="mt-0 w-fit cursor-help">Points of failure</h3>
            </TooltipTrigger>
            <TooltipContent className="max-w-72">
              {"What the vault's supply relies on, through the markets it lends to"}
            </TooltipContent>
          </HoverTooltip>
          <Table className="text-[0.86rem] tabular-nums">
            <TableBody>
              {points.slice(0, 8).map((p) => (
                <TableRow
                  key={p.id}
                  data-state={p.id === picked ? 'selected' : undefined}
                  className="cursor-pointer"
                  onClick={() => {
                    pick(p.id);
                    reveal.showPath(p.id);
                  }}
                >
                  <TableCell className="w-full max-w-0">
                    <HoverTooltip>
                      <TooltipTrigger asChild>
                        <span className="flex items-center gap-2">
                          <span
                            className="size-2 shrink-0"
                            style={{ background: KIND_COLOR[p.node.kind] }}
                          />
                          <span className="truncate">{p.node.label}</span>
                        </span>
                      </TooltipTrigger>
                      <TooltipContent>{`${p.node.label} · ${num(p.amount)} ${p.unit ?? ''}`}</TooltipContent>
                    </HoverTooltip>
                  </TableCell>
                  <TableCell className="text-right whitespace-nowrap">{percent(p.share)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>
        {node ? (
          <section className="grid gap-3" aria-label="Selected node">
            <h3 className="m-0 truncate">{node.label}</h3>
            {node.kind === 'Asset' ? (
              <>
                <div className="flex gap-2">
                  {FALLS.map((f) => (
                    <Button
                      key={f}
                      type="button"
                      size="sm"
                      variant={fall === f ? 'default' : 'outline'}
                      onClick={() => setFall(f)}
                    >
                      −{percent(f)}
                    </Button>
                  ))}
                </div>
                {shock && incident.isPending ? (
                  <span className="text-xs text-muted-foreground">Running the shock…</span>
                ) : null}
                {shock && incident.error ? (
                  <span className="text-xs text-muted-foreground">{incident.error.message}</span>
                ) : null}
                {result ? (
                  <Table className="text-[0.86rem] tabular-nums">
                    <TableBody>
                      {[
                        {
                          label: 'Verdict',
                          value: (
                            <span className={cn('font-semibold', VERDICT[result.verdict])}>
                              {result.hits.length ? result.verdict.toLowerCase() : 'Unaffected'}
                            </span>
                          ),
                        },
                        {
                          label: 'Vault loss',
                          value: `${num(result.vault_loss)} ${result.symbol}`,
                        },
                        {
                          label: 'Position loss',
                          value: `${num(result.loss_if_stay)} ${result.symbol}`,
                        },
                        { label: 'Markets hit', value: String(result.hits.length) },
                      ].map(({ label, value }) => (
                        <TableRow key={label}>
                          <TableHead scope="row" className="font-normal text-muted-foreground">
                            {label}
                          </TableHead>
                          <TableCell className="text-right whitespace-nowrap">{value}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : null}
                {result ? (
                  <Button asChild variant="ghost">
                    <Link
                      to="/old/incident"
                      search={(prev) => ({ ...prev, target: vault.address })}
                    >
                      Open incident
                    </Link>
                  </Button>
                ) : null}
              </>
            ) : null}
          </section>
        ) : null}
      </aside>
    </div>
  );
}
