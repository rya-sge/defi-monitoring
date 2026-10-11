// If X breaks, how much do I lose, how fast, and do I stay or leave?
import { useState } from 'react';
import { Link, useNavigate, useSearch } from '@tanstack/react-router';
import { Info } from 'lucide-react';
import { useBooks, useIncidentImpact, useShockTargets, useShockTrace } from '../api/hooks';
import { EXAMPLE_SHOCK, USE_MOCKS } from '../api/client';
import type {
  IncidentRequest,
  IncidentResponse,
  ShockMode,
  ShockRequest,
  VaultIncident,
} from '../api/types';
import { Stat, StatRow } from '../components/Stat';
import { Empty, ErrorState, Loading } from '../components/States';
import {
  Breakeven,
  ConditionalFigures,
  FigureTable,
  LossBars,
  PropagationGraph,
  SiblingLosses,
  Tip,
} from '../components/scenario/IncidentParts';
import { TraceGraph, TraceSummary } from '../components/scenario/TraceViews';
import { isAddress, num, percent, shortHash, usd } from '../lib/format';
import { pStar, VERDICT_LABEL, VERDICT_PRIORITY, VERDICT_TONE } from '../lib/verdict';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const HORIZON = 30;
const DEFAULT_BOOK = 'rockawayx-ethereum';

/** The scenarios recorded in `mocks/incidents.json` (`scripts/export_incident_fixtures.py`). */
const PRESETS = [
  { shock: 'token=PST:0.3', label: 'PST −30%' },
  { shock: 'token=fxSAVE:0.3', label: 'fxSAVE −30%' },
  { shock: 'borrower=all:0.5:1', label: 'Largest borrowers default, 50% recovered' },
  { shock: 'venue=Binance:0.5', label: 'Binance loses 50% of USDe backing' },
];

const MODES: ShockMode[] = ['reads-low', 'reads-high', 'frozen', 'price'];

/** The conditional Monte Carlo draws a markdown's size: a borrower default has none. */
const request = (
  scope: Pick<IncidentRequest, 'example' | 'vaults'>,
  shock: string,
): IncidentRequest => ({
  ...scope,
  shocks: [shock],
  horizon: HORIZON,
  conditional: !shock.startsWith('borrower='),
});

export function ScenarioPage() {
  const search = useSearch({ from: '/scenario' });
  const { target } = useSearch({ strict: false });
  const navigate = useNavigate({ from: '/scenario' });
  const { data: books } = useBooks();

  const vault = !search.book && target && isAddress(target) ? target.toLowerCase() : undefined;
  const book = vault ? undefined : (search.book ?? DEFAULT_BOOK);
  const shock = search.shock ?? PRESETS[0].shock;
  const incident = useIncidentImpact(
    request(vault ? { vaults: [vault] } : { example: book }, shock),
  );

  const scopes = [
    ...(books ?? []).map((b) => ({ value: `book:${b.name}`, label: b.title })),
    ...[
      ...new Map(
        (books ?? [])
          .flatMap((b) => b.vaults)
          .filter((v) => v.kind !== 'borrow')
          .map((v) => [v.address.toLowerCase(), v.label ?? shortHash(v.address)]),
      ),
    ].map(([address, label]) => ({ value: address, label })),
  ];
  const scope = vault ?? `book:${book}`;

  return (
    <div className="mx-auto grid max-w-[1440px] gap-8 px-5.5 pt-7 pb-12">
      <header className="flex flex-wrap items-end gap-4 border-b pb-5">
        <h1 className="m-0 mr-auto">Scenario lab</h1>
        <Select
          value={scope}
          onValueChange={(value) =>
            void navigate({
              search: (prev) =>
                value.startsWith('book:')
                  ? { ...prev, book: value.slice(5), target: undefined }
                  : { ...prev, book: undefined, target: value },
            })
          }
        >
          <SelectTrigger size="sm" className="w-80" aria-label="Scope">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {scopes.map((s) => (
              <SelectItem key={s.value} value={s.value}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <ShockPicker
          shock={shock}
          onChange={(next) => void navigate({ search: (prev) => ({ ...prev, shock: next }) })}
        />
      </header>
      {incident.isPending ? (
        <Loading what="the incident" />
      ) : incident.error ? (
        <ErrorState what="the incident" error={incident.error} />
      ) : (
        <IncidentResult key={`${scope}-${shock}`} result={incident.data} />
      )}
    </div>
  );
}

function ShockPicker({ shock, onChange }: { shock: string; onChange: (shock: string) => void }) {
  const [draft, setDraft] = useState(shock);
  const preset = PRESETS.some((p) => p.shock === shock);
  return (
    <div className="flex items-center gap-2">
      <Select
        value={preset ? shock : 'custom'}
        onValueChange={(value) => value !== 'custom' && onChange(value)}
      >
        <SelectTrigger size="sm" className="w-72" aria-label="Shock">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {PRESETS.map((p) => (
            <SelectItem key={p.shock} value={p.shock}>
              {p.label}
            </SelectItem>
          ))}
          {USE_MOCKS ? null : <SelectItem value="custom">Custom</SelectItem>}
        </SelectContent>
      </Select>
      {USE_MOCKS ? null : (
        <form
          className="flex gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            if (draft.trim()) onChange(draft.trim());
          }}
        >
          <Input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="token=PST:0.3"
            aria-label="Custom shock"
            className="h-8 w-48"
          />
          <Button type="submit" size="sm" variant="secondary">
            Run
          </Button>
        </form>
      )}
    </div>
  );
}

function IncidentResult({ result }: { result: IncidentResponse }) {
  const b = result.book;
  const lines = [...b.lines].sort(
    (x, y) =>
      Number(y.hit_markets.length > 0) - Number(x.hit_markets.length > 0) ||
      VERDICT_PRIORITY[x.verdict] - VERDICT_PRIORITY[y.verdict] ||
      y.loss_usd - x.loss_usd,
  );
  const [picked, setPicked] = useState(lines[0]?.vault.toLowerCase());
  const v = result.vaults.find((x) => x.vault.toLowerCase() === picked) ?? result.vaults[0];
  const isBook = result.vaults.length > 1;

  return (
    <>
      <section className="grid gap-4" aria-label="Book">
        {b.notes.length ? (
          <Tip
            label={<Info size={14} className="text-muted-foreground" />}
            tip={b.notes.join('\n')}
          />
        ) : null}
        <div className="grid items-end gap-x-9 gap-y-5.5 sm:grid-cols-[auto_1fr]">
          <Stat prominent label="Loss" value={usd(b.loss_usd)} />
          <StatRow
            items={[
              { label: 'Exposure', value: usd(b.exposure_usd) },
              { label: 'Value', value: usd(b.value_usd) },
              { label: `Breakeven p* (${b.horizon_days}d)`, value: pStar(b.p_star) },
            ]}
          />
        </div>
        {b.conditional ? (
          <div className="max-w-md">
            <ConditionalFigures conditional={b.conditional} />
          </div>
        ) : null}
      </section>
      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,3fr)]">
        <div className="grid min-w-0 gap-8">
          {isBook ? (
            <section aria-label="Vaults">
              <h2 className="mt-0 mb-4">Vaults</h2>
              <Table className="tabular-nums">
                <TableHeader>
                  <TableRow>
                    <TableHead>Vault</TableHead>
                    <TableHead className="text-right">Exposure</TableHead>
                    <TableHead className="text-right">Loss</TableHead>
                    <TableHead className="text-right">
                      <Tip
                        label="Saved"
                        tip="Loss avoided by leaving first, net of the cost of leaving"
                      />
                    </TableHead>
                    <TableHead className="text-right">p*</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lines.map((line) => {
                    const id = line.vault.toLowerCase();
                    return (
                      <TableRow
                        key={id}
                        tabIndex={0}
                        data-state={id === v?.vault.toLowerCase() ? 'selected' : undefined}
                        className="cursor-pointer"
                        onClick={() => setPicked(id)}
                        onKeyDown={(event) => event.key === 'Enter' && setPicked(id)}
                      >
                        <TableCell className="max-w-72 truncate font-medium">{line.name}</TableCell>
                        <TableCell className="text-right">
                          {line.priced ? usd(line.exposure_usd) : '—'}
                        </TableCell>
                        <TableCell className="text-right">
                          {line.priced ? usd(line.loss_usd) : '—'}
                        </TableCell>
                        <TableCell className="text-right">{usd(line.saved_usd)}</TableCell>
                        <TableCell className="text-right">{pStar(line.p_star)}</TableCell>
                        <TableCell>
                          {line.hit_markets.length ? (
                            <span className={`text-xs font-semibold ${VERDICT_TONE[line.verdict]}`}>
                              <Tip label={VERDICT_LABEL[line.verdict]} tip={line.reason} />
                            </span>
                          ) : (
                            <span className="text-xs text-muted-foreground">Unaffected</span>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </section>
          ) : null}
          {v ? <Hits vault={v} /> : null}
        </div>
        {v ? <Decision key={v.vault} vault={v} /> : null}
      </div>
      {v ? <TraceSection vault={v.vault.toLowerCase()} /> : null}
    </>
  );
}

function Decision({ vault: v }: { vault: VaultIncident }) {
  const affected = v.hits.length > 0;
  return (
    <aside
      className="grid min-w-0 gap-6 self-start rounded-md border bg-[var(--surface)] p-5.5 lg:sticky lg:top-5"
      aria-label="Decision"
    >
      <header className="grid gap-1">
        <span
          className={`w-fit text-sm font-semibold ${affected ? VERDICT_TONE[v.verdict] : 'text-muted-foreground'}`}
        >
          <Tip label={affected ? VERDICT_LABEL[v.verdict] : 'Unaffected'} tip={v.reason} />
        </span>
        <h2 className="m-0">
          <Link to="/vault" search={(prev) => ({ ...prev, target: v.vault.toLowerCase() })}>
            {v.name}
          </Link>
        </h2>
      </header>
      <FigureTable
        label="Stay or exit"
        rows={[
          { label: 'Loss if stay', value: `${num(v.loss_if_stay)} ${v.symbol}` },
          { label: 'Loss if exit first', value: `${num(v.loss_if_exit_first)} ${v.symbol}` },
          {
            label: 'Withdrawable now',
            tip: 'What can leave before the loss lands',
            value: `${num(v.can_leave_now)} ${v.symbol}`,
          },
          {
            label: 'Stuck',
            tip: 'What cannot leave in time',
            value: `${num(v.stuck)} ${v.symbol}`,
          },
          {
            label: 'Vault loss',
            value: `${num(v.vault_loss)} ${v.symbol} (${percent(v.vault_total > 0 ? v.vault_loss / v.vault_total : null)})`,
          },
          { label: 'Your position', value: `${num(v.depositor_assets)} ${v.symbol}` },
        ]}
      />
      <LossBars vault={v} />
      <section className="grid gap-2 border-t pt-4 text-sm" aria-label="Breakeven">
        <h3 className="m-0">Breakeven</h3>
        <Breakeven
          pStar={v.p_star}
          pStarYear={v.p_star_year}
          horizon={v.horizon_days}
          outside={v.outside}
        />
      </section>
      {v.conditional ? (
        <section className="grid gap-2 border-t pt-4 text-sm" aria-label="Given the incident">
          <h3 className="m-0">Given the incident</h3>
          <ConditionalFigures conditional={v.conditional} />
        </section>
      ) : null}
      <section className="grid gap-3 border-t pt-4">
        <h3 className="m-0 flex items-center gap-2">
          Propagation
          {v.notes.length ? (
            <Tip
              label={<Info size={14} className="text-muted-foreground" />}
              tip={v.notes.join('\n')}
            />
          ) : null}
        </h3>
        {affected ? (
          <PropagationGraph vault={v} />
        ) : (
          <span className="text-sm text-muted-foreground">No direct exposure</span>
        )}
        <SiblingLosses vault={v} />
      </section>
    </aside>
  );
}

const exitLabel = (h: VaultIncident['hits'][number]) =>
  h.exit_impact != null
    ? `${h.exit_route ?? '—'} · ${percent(h.exit_impact)}`
    : (h.exit_route ?? '—');

function Hits({ vault: v }: { vault: VaultIncident }) {
  if (!v.hits.length) return <Empty>No market of {v.name} reached</Empty>;
  return (
    <section aria-label="Markets reached">
      <h2 className="mt-0 mb-4">Markets reached · {v.name}</h2>
      <Table className="tabular-nums">
        <TableHeader>
          <TableRow>
            <TableHead>Market</TableHead>
            <TableHead className="text-right">Fall</TableHead>
            <TableHead className="text-right">Bad debt</TableHead>
            <TableHead className="text-right">Vault loss</TableHead>
            <TableHead>When</TableHead>
            <TableHead>Oracle</TableHead>
            <TableHead>Grade</TableHead>
            <TableHead>
              <Tip
                label="Exit"
                tip="Exit liquidity at the size the liquidations seize: route and slippage"
              />
            </TableHead>
            <TableHead className="text-right">Defaulters</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {v.hits.map((h) => (
            <TableRow key={h.market_id}>
              <TableCell className="max-w-64 truncate">
                <Link
                  to="/market/$marketId"
                  params={{ marketId: h.market_id }}
                  search={(prev) => prev}
                >
                  {h.label}
                </Link>
              </TableCell>
              <TableCell className="text-right">
                {h.event === 'default' ? '—' : `−${percent(h.drop)}`}
              </TableCell>
              <TableCell className="text-right">{num(h.bad_debt)}</TableCell>
              <TableCell className="text-right">{num(h.vault_loss)}</TableCell>
              <TableCell className="max-w-48 truncate">
                <Tip label={h.timing.split(/[;:,]/)[0]} tip={h.timing} />
              </TableCell>
              <TableCell>{h.oracle_class}</TableCell>
              <TableCell>{h.grade ?? '—'}</TableCell>
              <TableCell>
                {h.exit_text ? (
                  <Tip label={exitLabel(h)} tip={`${h.exit_text} (${h.exit_source})`} />
                ) : (
                  exitLabel(h)
                )}
              </TableCell>
              <TableCell className="text-right">{h.defaulters.length || '—'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </section>
  );
}

/** The engine's trace on the vault's recorded graph; mocking, only the committed example exists. */
function TraceSection({ vault }: { vault: string }) {
  const { trace } = useSearch({ from: '/scenario' });
  const navigate = useNavigate({ from: '/scenario' });
  const targets = useShockTargets(USE_MOCKS ? undefined : vault);
  const [node, setNode] = useState('');
  const [mode, setMode] = useState<ShockMode>('reads-low');
  const [size, setSize] = useState('10%');
  const example = EXAMPLE_SHOCK.vault?.[0] === vault;
  const run = (shock: string) => void navigate({ search: (prev) => ({ ...prev, trace: shock }) });

  return (
    <section className="grid gap-4 border-t pt-6" aria-label="Propagation trace">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="m-0 mr-auto">Propagation trace</h2>
        {USE_MOCKS ? (
          example ? (
            <Button size="sm" variant="secondary" onClick={() => run(EXAMPLE_SHOCK.shocks[0])}>
              {EXAMPLE_SHOCK.shocks[0]}
            </Button>
          ) : (
            <span className="text-sm text-muted-foreground">No recorded trace</span>
          )
        ) : (
          <>
            <Select value={node} onValueChange={setNode}>
              <SelectTrigger size="sm" className="w-72" aria-label="Node">
                <SelectValue
                  placeholder={targets.isPending ? 'Loading…' : 'Oracle, feed or asset'}
                />
              </SelectTrigger>
              <SelectContent>
                {(targets.data ?? []).map((t) => (
                  <SelectItem key={t.node} value={t.node}>
                    {t.label} · {t.held}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={mode} onValueChange={(value) => setMode(value as ShockMode)}>
              <SelectTrigger size="sm" className="w-32" aria-label="Mode">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MODES.map((m) => (
                  <SelectItem key={m} value={m}>
                    {m}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {mode === 'frozen' ? null : (
              <Input
                value={size}
                onChange={(e) => setSize(e.target.value)}
                aria-label="Size"
                className="h-8 w-20"
              />
            )}
            <Button
              size="sm"
              variant="secondary"
              disabled={!node}
              onClick={() => run(mode === 'frozen' ? `${node}:frozen` : `${node}:${mode}:${size}`)}
            >
              Run
            </Button>
          </>
        )}
      </div>
      {targets.error ? <ErrorState what="the shockable nodes" error={targets.error} /> : null}
      {trace && (!USE_MOCKS || (example && trace === EXAMPLE_SHOCK.shocks[0])) ? (
        <TraceResult body={{ vault: [vault], shocks: [trace] }} />
      ) : null}
    </section>
  );
}

function TraceResult({ body }: { body: ShockRequest }) {
  const { data, isPending, error } = useShockTrace(body);
  if (isPending) return <Loading what="the trace" />;
  if (error) return <ErrorState what="the trace" error={error} />;
  const label = (id: string) => data.graph.nodes.find((node) => node.id === id)?.label ?? id;
  return (
    <Tabs defaultValue="summary">
      <TabsList>
        <TabsTrigger value="summary">Summary</TabsTrigger>
        <TabsTrigger value="graph">Graph</TabsTrigger>
      </TabsList>
      <p className="text-sm text-muted-foreground tabular-nums">
        {data.shocks.map((s) => s.label).join(' + ')} · block {data.block} ·{' '}
        {data.converged ? 'converged' : 'not converged'}
      </p>
      <TabsContent value="summary" className="pb-9">
        <TraceSummary trace={data} label={label} />
      </TabsContent>
      <TabsContent value="graph" className="relative h-[70vh]">
        <TraceGraph trace={data} label={label} />
      </TabsContent>
    </Tabs>
  );
}
