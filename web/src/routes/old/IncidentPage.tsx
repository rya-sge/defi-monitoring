import { FormattedText } from '../../components/FormattedText';
import { Link, useNavigate, useSearch } from '@tanstack/react-router';
import { ArrowRight, TriangleAlert } from 'lucide-react';
import { useIncidentImpact } from '../../api/hooks';
import {
  Breakeven,
  LossBars,
  PropagationGraph,
  SiblingLosses,
} from '../../components/scenario/IncidentParts';
import type { IncidentResponse, VaultIncident } from '../../api/types';
import { ErrorState, Loading } from '../../components/States';
import { usd, num, percent } from '../../lib/format';
import { INCIDENT } from '../../mocks/incident';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

const VERDICT = { STAY: 'text-ok', REDUCE: 'text-warn', EXIT: 'text-critical' };
const PRIORITY = { EXIT: 0, REDUCE: 1, STAY: 2 };

export function IncidentPage() {
  const { data, isPending, error } = useIncidentImpact({
    example: INCIDENT.example,
    shocks: INCIDENT.shocks,
    horizon: INCIDENT.horizon,
  });
  if (isPending) return <Loading what="the incident" />;
  if (error) return <ErrorState what="the incident" error={error} />;
  return <IncidentView result={data} />;
}

function IncidentView({ result }: { result: IncidentResponse }) {
  const { target } = useSearch({ strict: false });
  const navigate = useNavigate();
  const rows = [...result.book.lines].sort(
    (a, b) =>
      PRIORITY[a.verdict] - PRIORITY[b.verdict] ||
      b.loss_usd - a.loss_usd ||
      a.name.localeCompare(b.name),
  );
  const v =
    result.vaults.find((vault) => vault.vault.toLowerCase() === target?.toLowerCase()) ??
    result.vaults.find((vault) => vault.vault.toLowerCase() === INCIDENT.defaultVault) ??
    result.vaults[0];
  if (!v) return null;
  const selected = v.vault.toLowerCase();
  const select = (vault: string) =>
    void navigate({
      to: '/old/incident',
      search: (prev) => ({ ...prev, target: vault.toLowerCase() }),
    });

  return (
    <div className="mx-auto grid max-w-[1440px] gap-8 px-5.5 pt-7 pb-12">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b pb-5">
        <div className="grid gap-2">
          <div className="flex items-center gap-2 text-sm">
            <TriangleAlert size={16} className="text-critical" />
            <span className="font-semibold text-critical">Critical</span>
          </div>
          <h1 className="m-0">
            {INCIDENT.title}{' '}
            <span className="tabular-nums">
              <FormattedText>−30%</FormattedText>
            </span>
          </h1>
        </div>
      </header>
      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,3fr)]">
        <section className="min-w-0" aria-label="Vault impacts">
          <h2 className="mt-0 mb-4">Vault impacts</h2>
          <Table className="tabular-nums">
            <TableHeader>
              <TableRow>
                <TableHead>Vault</TableHead>
                <TableHead className="text-right">Exposure</TableHead>
                <TableHead className="text-right">Est. loss</TableHead>
                <TableHead>Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow
                  key={row.vault}
                  tabIndex={0}
                  aria-label={`${row.name}, estimated loss ${usd(row.loss_usd)}, ${row.verdict}`}
                  aria-selected={row.vault.toLowerCase() === selected}
                  data-state={row.vault.toLowerCase() === selected ? 'selected' : undefined}
                  className="cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-ring"
                  onClick={() => select(row.vault)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      select(row.vault);
                    }
                  }}
                >
                  <TableCell className="max-w-72 whitespace-normal py-4 font-medium">
                    {row.name}
                  </TableCell>
                  <TableCell className="text-right">
                    {row.priced ? usd(row.exposure_usd) : '—'}
                  </TableCell>
                  <TableCell className="text-right">
                    {row.priced ? usd(row.loss_usd) : '—'}
                  </TableCell>
                  <TableCell>
                    <span className={`text-xs font-semibold ${VERDICT[row.verdict]}`}>
                      {row.hit_markets.length ? row.verdict.toLowerCase() : 'Unaffected'}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>
        <DecisionPanel key={selected} vault={v} />
      </div>
    </div>
  );
}

function DecisionPanel({ vault: v }: { vault: VaultIncident }) {
  const affected = v.hits.length > 0;
  const total = v.can_leave_now + v.stuck;
  const figures = [
    {
      label: 'Vault exposure',
      value:
        v.asset_usd != null
          ? usd(v.hits.reduce((sum, hit) => sum + hit.vault_exposure, 0) * v.asset_usd)
          : '—',
    },
    { label: 'Estimated vault loss', value: `${num(v.vault_loss)} ${v.symbol}` },
    { label: 'Position loss', value: `${num(v.loss_if_stay)} ${v.symbol}` },
    {
      label: 'Avoidable position loss',
      value: `${num(Math.max(0, v.loss_if_stay - v.loss_if_exit_first))} ${v.symbol}`,
    },
    { label: 'Withdrawable', value: `${num(v.can_leave_now)} ${v.symbol}` },
    { label: 'Pool usage', value: total > 0 ? percent(v.stuck / total) : '—' },
  ];

  return (
    <aside
      className="grid min-w-0 grid-cols-1 gap-6 border-t pt-5 lg:sticky lg:top-5 lg:border-t-0 lg:border-l lg:pt-0 lg:pl-7"
      aria-label="Selected vault action"
    >
      <header className="grid gap-2">
        <span className={`text-sm font-semibold ${VERDICT[v.verdict]}`}>
          {affected ? v.verdict.toLowerCase() : 'Unaffected'}
        </span>
        <h2 className="m-0">{v.name}</h2>
      </header>
      <Table className="tabular-nums" aria-label="Selected vault figures">
        <TableBody>
          {figures.map((item) => (
            <TableRow key={item.label}>
              <TableHead scope="row" className="w-full max-w-0 font-normal">
                <HoverTooltip>
                  <TooltipTrigger asChild>
                    <span className="block truncate">{item.label}</span>
                  </TooltipTrigger>
                  <TooltipContent>{item.label}</TooltipContent>
                </HoverTooltip>
              </TableHead>
              <TableCell className="text-right font-medium whitespace-nowrap">
                <FormattedText>{item.value}</FormattedText>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {affected && v.loss_if_stay <= v.loss_if_exit_first ? (
        <span className="text-xs text-warn">Exiting first does not reduce the estimated loss</span>
      ) : null}
      <Button asChild variant="ghost">
        <Link to="/old/vault" search={(prev) => ({ ...prev, target: v.vault })}>
          Review withdrawal liquidity
          <ArrowRight size={14} />
        </Link>
      </Button>
      <section>
        <h3 className="m-0">Position loss · {v.symbol}</h3>
        <LossBars vault={v} />
      </section>
      <section className="grid gap-3 border-t pt-4">
        <h3 className="m-0">Propagation</h3>
        {affected ? (
          <PropagationGraph vault={v} />
        ) : (
          <span className="text-sm text-muted-foreground">No direct exposure</span>
        )}
        <SiblingLosses vault={v} />
      </section>
      <section className="grid gap-2 border-t pt-4 text-sm" aria-label="Breakeven">
        <h3 className="m-0">Breakeven</h3>
        <Breakeven
          pStar={v.p_star}
          pStarYear={v.p_star_year}
          horizon={v.horizon_days}
          outside={v.outside}
        />
      </section>
    </aside>
  );
}
