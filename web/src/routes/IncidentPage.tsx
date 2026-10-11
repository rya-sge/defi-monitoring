import { ChartTooltip } from '../components/ChartTooltip';
import { FormattedText } from '../components/FormattedText';
import { Link, useNavigate, useSearch } from '@tanstack/react-router';
import { ArrowRight, ShieldQuestion, TriangleAlert } from 'lucide-react';
import { Bar, BarChart, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useIncidentImpact } from '../api/hooks';
import type { IncidentResponse, VaultIncident } from '../api/types';
import { ErrorState, Loading } from '../components/States';
import { usd, num, percent, shortHash } from '../lib/format';
import { INCIDENT } from '../mocks/incident';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

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
      to: '/incident',
      search: (prev) => ({ ...prev, target: vault.toLowerCase() }),
    });

  return (
    <div className="mx-auto grid max-w-[1440px] gap-8 px-5.5 pt-7 pb-12">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b pb-5">
        <div className="grid gap-2">
          <div className="flex items-center gap-2 text-sm">
            <TriangleAlert size={16} className="text-critical" />
            <span className="font-semibold text-critical">Critical</span>
            <span className="text-muted-foreground">Demo event</span>
          </div>
          <h1 className="m-0">
            {INCIDENT.title}{' '}
            <span className="tabular-nums">
              <FormattedText>−30%</FormattedText>
            </span>
          </h1>
        </div>
        <div className="grid gap-2 text-sm tabular-nums">
          <span>
            Occurred <b>{INCIDENT.occurredMinutesAgo} min ago</b>
          </span>
          <span>
            Detected <b>{INCIDENT.detectedMinutesAgo} min ago</b>
          </span>
        </div>
      </header>
      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
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
  const exit = v.verdict !== 'STAY';
  const data = [
    { name: 'Stay', value: v.loss_if_stay },
    { name: 'Exit first', value: v.loss_if_exit_first },
    { name: `Yield forgone (${v.horizon_days}d)`, value: v.exit_cost },
  ];
  const total = v.can_leave_now + v.stuck;

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
      <Table className="table-fixed tabular-nums" aria-label="Selected vault figures">
        <TableBody>
          {[
            {
              label: 'Vault exposure',
              value:
                v.asset_usd != null
                  ? usd(v.hits.reduce((sum, hit) => sum + hit.vault_exposure, 0) * v.asset_usd)
                  : '—',
            },
            {
              label: 'Estimated vault loss',
              value: `${num(v.vault_loss)} ${v.symbol}`,
              note: v.vault_total > 0 ? percent(v.vault_loss / v.vault_total) : '—',
            },
            {
              label: 'Position loss',
              value: `${num(v.loss_if_stay)} ${v.symbol}`,
              note: `${shortHash(v.depositor)} · ${num(v.depositor_assets)} ${v.symbol}`,
            },
            {
              label: 'Avoidable position loss',
              value: `${num(Math.max(0, v.loss_if_stay - v.loss_if_exit_first))} ${v.symbol}`,
            },
          ].map((item) => (
            <TableRow key={item.label}>
              <TableHead scope="row" className="w-[45%] whitespace-normal align-top font-normal">
                {item.label}
              </TableHead>
              <TableCell className="text-right whitespace-normal align-top">
                <div className="font-medium">{item.value}</div>
                {'note' in item && item.note ? (
                  <div className="mt-1 text-xs text-muted-foreground">{item.note}</div>
                ) : null}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <section className="grid gap-3" aria-label="Actions now">
        <h3 className="m-0">Now</h3>
        <ol className="grid list-decimal gap-3 pl-5 text-sm">
          <li>
            {exit ? (
              <>
                Withdraw up to{' '}
                <b className="tabular-nums">
                  <FormattedText>{`${num(v.can_leave_now)} ${v.symbol}`}</FormattedText>
                </b>
              </>
            ) : (
              <>
                Keep{' '}
                <b className="tabular-nums">
                  <FormattedText>{`${num(v.depositor_assets)} ${v.symbol}`}</FormattedText>
                </b>{' '}
                in the vault
              </>
            )}
          </li>
          <li>
            {exit ? (
              <>
                Monitor{' '}
                <b className="tabular-nums">
                  <FormattedText>{`${num(v.stuck)} ${v.symbol}`}</FormattedText>
                </b>{' '}
                still locked
              </>
            ) : affected ? (
              'Monitor collateral recovery and exit liquidity'
            ) : (
              'Continue monitoring'
            )}
          </li>
        </ol>
        {affected && v.loss_if_stay <= v.loss_if_exit_first ? (
          <span className="text-xs text-warn">
            Exiting first does not reduce the estimated loss
          </span>
        ) : null}
        <Button asChild variant="outline" className="justify-between">
          <Link to="/" search={(prev) => ({ ...prev, target: v.vault })}>
            Review withdrawal liquidity
            <ArrowRight size={14} />
          </Link>
        </Button>
      </section>
      <section>
        <h3 className="m-0">Position loss · {v.symbol}</h3>
        <ResponsiveContainer width="100%" height={136}>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 8, right: 0, bottom: 8, left: 0 }}
            barSize={36}
          >
            <XAxis type="number" hide />
            <YAxis type="category" dataKey="name" hide />
            <Tooltip
              cursor={false}
              content={(props) => (
                <ChartTooltip {...props} formatValue={(value) => `${num(value)} ${v.symbol}`} />
              )}
            />
            <Bar
              dataKey="value"
              name="Position loss"
              fill="var(--loss-bar)"
              activeBar={false}
              isAnimationActive={false}
            >
              <LabelList
                dataKey="name"
                position="insideLeft"
                offset={10}
                fill="#fff"
                fontSize={12}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <dl className="grid gap-2 text-xs text-muted-foreground">
          <div>
            <dt className="inline font-medium text-foreground">Stay: </dt>
            <dd className="inline">Estimated loss if you keep your full deposit.</dd>
          </div>
          <div>
            <dt className="inline font-medium text-foreground">Exit first: </dt>
            <dd className="inline">
              Estimated loss after withdrawing available liquidity before other depositors,
              including any modeled withdrawal penalty.
            </dd>
          </div>
          <div>
            <dt className="inline font-medium text-foreground">Yield forgone: </dt>
            <dd className="inline">
              Yield you give up on the withdrawn amount over {num(v.horizon_days, 0)} days, shown
              separately from the incident loss.
            </dd>
          </div>
        </dl>
      </section>
      <section className="grid gap-3" aria-label="Withdrawal liquidity">
        <div className="flex justify-between text-sm">
          <span>Withdrawable</span>
          <b className="tabular-nums">
            <FormattedText>{`${num(v.can_leave_now)} ${v.symbol}`}</FormattedText>
          </b>
        </div>
        {total > 0 ? (
          <div
            className="flex h-3 overflow-hidden rounded border"
            role="img"
            aria-label={`${num(v.can_leave_now)} withdrawable, ${num(v.stuck)} locked ${v.symbol}`}
          >
            <div
              className="bg-foreground"
              style={{ width: `${(100 * v.can_leave_now) / total}%` }}
            />
            <div className="flex-1 bg-muted" />
          </div>
        ) : null}
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>Locked</span>
          <span className="tabular-nums">
            <FormattedText>{`${num(v.stuck)} ${v.symbol}`}</FormattedText>
          </span>
        </div>
        <p className="m-0 text-xs text-muted-foreground">
          Withdrawable is the part of your deposit that current liquidity lets you withdraw first.
          Locked is the remainder still in the vault, exposed to the incident; it may become
          withdrawable as borrowers repay or liquidity returns. Locked is not the estimated loss.
        </p>
      </section>
      <section className="grid gap-3 border-t pt-4">
        <h3 className="m-0">Propagation</h3>
        {affected ? (
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span>PST</span>
            <ArrowRight size={13} />
            <span>{v.hits.length} markets</span>
            <ArrowRight size={13} />
            <span>Vault</span>
            <ArrowRight size={13} />
            <span>Position</span>
          </div>
        ) : (
          <span className="text-sm text-muted-foreground">No direct exposure</span>
        )}
        <div className="flex justify-between text-sm">
          <span>Other markets reached</span>
          <b className="tabular-nums">{v.sibling_losses.length}</b>
        </div>
      </section>
      <section className="grid gap-2 border-t pt-4 text-sm" aria-label="Insurance coverage">
        <h3 className="m-0 flex items-center gap-2">
          <ShieldQuestion size={16} />
          Coverage
        </h3>
        <div className="flex justify-between">
          <span>Policy held</span>
          <span className="text-muted-foreground">Unknown</span>
        </div>
        <div className="flex justify-between">
          <span>PST markdown covered</span>
          <span className="text-muted-foreground">Not verified</span>
        </div>
      </section>
    </aside>
  );
}
