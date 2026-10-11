// Which single failure would hit the most of my book at once?
import { Fragment, useMemo, useState } from 'react';
import { Link } from '@tanstack/react-router';
import { ChevronRight, FlaskConical } from 'lucide-react';
import { cn } from 'cn';
import { useGraph, useSelectedTarget } from '../api/hooks';
import type { GraphNode, GraphResponse } from '../api/types';
import { FormattedText } from '../components/FormattedText';
import { Empty, ErrorState, Loading } from '../components/States';
import { crossView, totalExposure } from '../lib/cross';
import type { Shared } from '../lib/cross';
import { detailValue, percent, usd } from '../lib/format';
import { KIND_COLOR, nodeDrawing, nodeRole, targetNodeId } from '../lib/graph';
import type { NodeRole } from '../lib/graph';
import type { ScenarioSearch } from '../router';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

const ROLE_LABEL: Partial<Record<NodeRole, string>> = {
  oracle: 'Oracles',
  feed: 'Feeds',
  asset: 'Assets',
  market: 'Markets',
  pendle: 'Pendle pools',
  external: 'Off-chain',
  admin: 'Admins',
};

type Row = {
  shared: Shared;
  role: NodeRole;
  total: number;
  share: number | null;
  markets: Set<string>;
  /** Vault ids, largest exposure first. */
  vaults: string[];
};

export function ContagionPage() {
  const { data, isPending, error } = useGraph();
  const { target } = useSelectedTarget();
  if (isPending) return <Loading what="the dependency graph" />;
  if (error) return <ErrorState what="the dependency graph" error={error} />;
  return <ContagionView graph={data} focus={target ? targetNodeId(target) : null} />;
}

function ContagionView({ graph, focus }: { graph: GraphResponse; focus: string | null }) {
  const [withLoanTokens, setWithLoanTokens] = useState(false);
  const [role, setRole] = useState<NodeRole | null>(null);
  const [open, setOpen] = useState<string | null>(null);

  const view = useMemo(() => crossView(graph, withLoanTokens), [graph, withLoanTokens]);
  const byId = useMemo(() => new Map(graph.nodes.map((n) => [n.id, n])), [graph]);
  // What all the vaults of the graph supply, in their loan units: the share's denominator.
  const book = useMemo(() => {
    const vaults = new Set(view.vaults.map((v) => v.id));
    return graph.edges
      .filter((e) => e.rel === 'supplies' && vaults.has(e.source))
      .reduce((sum, e) => sum + (e.amount ?? 0), 0);
  }, [graph, view]);

  const rows = useMemo<Row[]>(
    () =>
      view.shared
        .map((shared) => {
          const total = totalExposure(shared);
          return {
            shared,
            role: nodeRole(shared.node),
            total,
            share: book > 0 ? total / book : null,
            markets: new Set([...shared.markets.values()].flatMap((m) => [...m.keys()])),
            vaults: [...shared.exposure].sort((a, b) => b[1] - a[1]).map(([id]) => id),
          };
        })
        .sort((a, b) => b.total - a.total || b.vaults.length - a.vaults.length),
    [view, book],
  );
  const roles = [...new Set(rows.map((r) => r.role))].filter((r) => ROLE_LABEL[r]);
  const shown = role ? rows.filter((r) => r.role === role) : rows;
  const label = (id: string) => byId.get(id)?.label.replace(/^Vault /, '') ?? id;

  if (!rows.length) return <Empty>No dependency shared by two vaults.</Empty>;

  return (
    <div className="mx-auto grid max-w-[1280px] gap-6 px-5.5 pt-7 pb-14">
      <header className="flex flex-wrap items-baseline gap-x-5.5 gap-y-2">
        <h1 className="m-0">Contagion</h1>
        <p className="m-0 text-muted-foreground tabular-nums">
          <FormattedText>{`${view.vaults.length} vaults · ${usd(book)} supplied · ${rows.length} shared dependencies`}</FormattedText>
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" variant={role ? 'ghost' : 'secondary'} onClick={() => setRole(null)}>
          All
        </Button>
        {roles.map((r) => (
          <Button
            key={r}
            size="sm"
            variant={role === r ? 'secondary' : 'ghost'}
            onClick={() => setRole(role === r ? null : r)}
          >
            {ROLE_LABEL[r]}
          </Button>
        ))}
        <Label className="ml-auto flex items-center gap-2 font-normal">
          <Checkbox
            checked={withLoanTokens}
            onCheckedChange={(checked) => setWithLoanTokens(checked === true)}
          />
          Include loan tokens
        </Label>
      </div>

      <Table className="tabular-nums">
        <TableHeader>
          <TableRow>
            <TableHead className="w-8" />
            <TableHead>Dependency</TableHead>
            <TableHead>Vaults</TableHead>
            <TableHead className="text-right">
              <Tooltip>
                <TooltipTrigger className="cursor-help">Exposed</TooltipTrigger>
                <TooltipContent>
                  Vault supply into the markets that depend on it, loan units at par
                </TooltipContent>
              </Tooltip>
            </TableHead>
            <TableHead className="w-40">Share of vaults</TableHead>
            <TableHead className="text-right">Markets</TableHead>
            <TableHead>Signals</TableHead>
            <TableHead />
          </TableRow>
        </TableHeader>
        <TableBody>
          {shown.map((row) => {
            const id = row.shared.node.id;
            const expanded = open === id;
            const reachesFocus = focus != null && row.shared.exposure.has(focus);
            return (
              <Fragment key={id}>
                <TableRow
                  tabIndex={0}
                  aria-expanded={expanded}
                  data-state={expanded ? 'selected' : undefined}
                  className={cn(
                    'cursor-pointer',
                    reachesFocus && 'shadow-[inset_2px_0_0_var(--fg)]',
                  )}
                  onClick={() => setOpen(expanded ? null : id)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      setOpen(expanded ? null : id);
                    }
                  }}
                >
                  <TableCell className="text-muted-foreground">
                    <ChevronRight
                      size={14}
                      className={cn('transition-transform', expanded && 'rotate-90')}
                    />
                  </TableCell>
                  <TableCell className="max-w-80">
                    <Dependency node={row.shared.node} />
                  </TableCell>
                  <TableCell>
                    <VaultChips ids={row.vaults} label={label} focus={focus} />
                  </TableCell>
                  <TableCell className="text-right">{usd(row.total)}</TableCell>
                  <TableCell>
                    <ShareBar value={row.share} />
                  </TableCell>
                  <TableCell className="text-right">{row.markets.size}</TableCell>
                  <TableCell>
                    <Signals node={row.shared.node} />
                  </TableCell>
                  <TableCell className="text-right" onClick={(event) => event.stopPropagation()}>
                    <SimulateLink row={row} focus={focus} />
                  </TableCell>
                </TableRow>
                {expanded ? (
                  <TableRow className="hover:bg-transparent">
                    <TableCell />
                    <TableCell colSpan={7} className="pb-5">
                      <Breakdown row={row} label={label} byId={byId} />
                    </TableCell>
                  </TableRow>
                ) : null}
              </Fragment>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

function Dependency({ node }: { node: GraphNode }) {
  const { icon: Icon } = nodeDrawing(node);
  return (
    <span className="flex min-w-0 items-center gap-2">
      <Icon size={15} className="shrink-0" style={{ color: KIND_COLOR[node.kind] }} />
      <span className="truncate font-medium" title={node.label}>
        {node.label}
      </span>
    </span>
  );
}

function VaultChips({
  ids,
  label,
  focus,
}: {
  ids: string[];
  label: (id: string) => string;
  focus: string | null;
}) {
  const shown = ids.slice(0, 3);
  return (
    <span className="flex flex-wrap items-center gap-1">
      <span className="mr-1">{ids.length}</span>
      {shown.map((id) => (
        <span
          key={id}
          className={cn(
            'max-w-36 truncate rounded border px-1.5 py-0.5 text-xs',
            id === focus ? 'border-foreground text-foreground' : 'text-muted-foreground',
          )}
          title={label(id)}
        >
          {label(id)}
        </span>
      ))}
      {ids.length > shown.length ? (
        <span className="text-xs text-muted-foreground">+{ids.length - shown.length}</span>
      ) : null}
    </span>
  );
}

function ShareBar({ value }: { value: number | null }) {
  return (
    <span className="flex items-center gap-2">
      <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
        <span
          className="block h-full rounded-full bg-foreground"
          style={{ width: `${Math.min(1, value ?? 0) * 100}%` }}
        />
      </span>
      <span className="w-10 text-right">
        <FormattedText>{percent(value)}</FormattedText>
      </span>
    </span>
  );
}

function Signal({ text, tip, tone }: { text: string; tip: string; tone?: 'warn' | 'critical' }) {
  return (
    <Tooltip>
      <TooltipTrigger
        className={cn(
          'cursor-help rounded border px-1.5 py-0.5 text-xs whitespace-nowrap',
          tone === 'critical'
            ? 'text-critical'
            : tone === 'warn'
              ? 'text-warn'
              : 'text-muted-foreground',
        )}
      >
        {text}
      </TooltipTrigger>
      <TooltipContent className="max-w-80">{tip}</TooltipContent>
    </Tooltip>
  );
}

function Signals({ node }: { node: GraphNode }) {
  const d = node.details;
  const grade = detailValue(d.pharos_grade);
  const shared = detailValue(d.shared_text);
  const supply = detailValue(d.supply_text);
  return (
    <span className="flex flex-wrap gap-1">
      {grade ? (
        <Signal
          text={grade}
          tip="Pharos grade"
          tone={/^[DF]/.test(grade) ? 'critical' : /^C/.test(grade) ? 'warn' : undefined}
        />
      ) : null}
      {d.stale === true ? (
        <Signal
          text="Stale"
          tip={detailValue(d.freshness) || 'Last update later than its own rhythm'}
          tone="critical"
        />
      ) : null}
      {d.oracle_class === 'constant-price' ? (
        <Signal
          text="Constant price"
          tip={`Does not follow the market${d.constant_kind ? `: ${detailValue(d.constant_kind)}` : ''}; a depeg liquidates nobody`}
          tone="warn"
        />
      ) : null}
      {d.concentrated === true ? (
        <Signal text="Concentrated" tip={detailValue(d.concentration)} tone="warn" />
      ) : null}
      {shared ? <Signal text="Shared" tip={shared} /> : null}
      {supply ? <Signal text="Supply" tip={supply} /> : null}
    </span>
  );
}

/** The Scenario lab prefilled with this dependency failing, on the most exposed vault (or the selected one). */
function SimulateLink({ row, focus }: { row: Row; focus: string | null }) {
  const n = row.shared.node;
  const scenario: ScenarioSearch | null =
    row.role === 'oracle' || row.role === 'feed'
      ? { trace: `${n.id}:reads-low:10%` }
      : row.role === 'asset'
        ? { shock: `token=${n.label}:0.3` }
        : row.role === 'market'
          ? { shock: `borrower=${detailValue(n.details.market_id) || n.id}:0.5:1` }
          : null;
  if (!scenario) return null;
  const vault = focus && row.shared.exposure.has(focus) ? focus : row.vaults[0];
  return (
    <Button asChild size="sm" variant="ghost">
      <Link
        to="/scenario"
        search={(prev) => ({
          ...prev,
          book: undefined,
          shock: undefined,
          trace: undefined,
          ...scenario,
          target: vault,
        })}
        className="no-underline"
      >
        <FlaskConical />
        Simulate
      </Link>
    </Button>
  );
}

function Breakdown({
  row,
  label,
  byId,
}: {
  row: Row;
  label: (id: string) => string;
  byId: Map<string, GraphNode>;
}) {
  const lines = row.vaults.flatMap((vault) =>
    [...(row.shared.markets.get(vault) ?? [])]
      .sort((a, b) => b[1] - a[1])
      .map(([market, amount]) => ({ vault, market, amount })),
  );
  return (
    <Table className="text-[0.86rem] tabular-nums">
      <TableHeader>
        <TableRow>
          <TableHead>Vault</TableHead>
          <TableHead>Market</TableHead>
          <TableHead className="text-right">Supplied</TableHead>
          <TableHead className="text-right">Share of dependency</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {lines.map(({ vault, market, amount }) => {
          const node = byId.get(market);
          const marketId = node ? detailValue(node.details.market_id) : '';
          return (
            <TableRow key={`${vault}-${market}`}>
              <TableCell>{label(vault)}</TableCell>
              <TableCell className="max-w-96 truncate">
                {marketId ? (
                  <Link to="/market/$marketId" params={{ marketId }} search={(prev) => prev}>
                    {node?.label ?? market}
                  </Link>
                ) : (
                  (node?.label ?? market)
                )}
              </TableCell>
              <TableCell className="text-right">{usd(amount)}</TableCell>
              <TableCell className="text-right">
                <FormattedText>{percent(row.total > 0 ? amount / row.total : null)}</FormattedText>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
