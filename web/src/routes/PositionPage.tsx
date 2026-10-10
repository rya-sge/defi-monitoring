import { useMemo } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TooltipContentProps } from 'recharts';
import { useReport } from '../api/hooks';
import { ErrorState, Loading } from '../components/States';
import { StatRow } from '../components/Stat';
import type { StatProps } from '../components/Stat';
import type { Report, SimulationLayer } from '../api/types';
import { compactUsd, days, num, percent, usd } from '../lib/format';
import { Table, TableBody, TableCell, TableRow } from '@/components/ui/table';

const REASONS = 'grid max-w-measure list-disc gap-2 pl-[1.1em] text-[0.92rem]';
const BLOCKS = 'grid grid-cols-[repeat(auto-fit,minmax(min(400px,100%),1fr))] gap-x-14 gap-y-9';
const BLOCK_SUB = 'mb-3.5 text-[0.82rem] text-muted-foreground';
const TOOLTIP = 'max-w-[320px] border border-foreground bg-background p-2 text-[0.82rem]';

const VERDICT_TONE: Record<string, string> = {
  STAY: 'text-ok',
  REDUCE: 'text-warn',
  EXIT: 'text-critical',
};

/** A label/value pair table; the figures line up, nothing is drawn around it. */
function SpecTable({ rows }: { rows: [string, React.ReactNode][] }) {
  return (
    <Table className="text-[0.86rem] tabular-nums">
      <TableBody>
        {rows.map(([label, value]) => (
          <TableRow key={label}>
            <TableCell className="w-[42%] py-2 pr-3.5 align-top whitespace-normal text-muted-foreground">
              {label}
            </TableCell>
            <TableCell className="py-2 align-top whitespace-normal">{value}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export function PositionPage() {
  const { data, isPending, error } = useReport();

  if (isPending) return <Loading what="the report" />;
  if (error) return <ErrorState what="the report" error={error} />;
  if (!data) return <ErrorState what="the report" error="empty response" />;

  return <PositionView report={data} />;
}

function PositionView({ report }: { report: Report }) {
  const { position, decision, simulation, exit_quote, oracle_sensitivity } = report;

  const stats = useMemo<StatProps[]>(() => {
    const hf = position.health_factor;
    const hfTone: StatProps['tone'] =
      hf == null ? 'neutral' : hf <= 1.02 ? 'critical' : hf <= 1.1 ? 'warn' : 'ok';
    const dropTone: StatProps['tone'] =
      position.liquidation_drop == null
        ? 'neutral'
        : position.liquidation_drop < decision.stress_drop
          ? 'warn'
          : 'ok';
    const netTone: StatProps['tone'] = decision.net_stay_usd < 0 ? 'critical' : 'ok';

    return [
      {
        label: 'Health factor',
        value: num(hf, 3),
        note: `LLTV ${percent(position.lltv, 1)}`,
        tone: hfTone,
      },
      {
        label: 'Liquidating fall',
        value: percent(position.liquidation_drop),
        note: `stress to survive ${percent(decision.stress_drop, 1)}`,
        tone: dropTone,
      },
      {
        label: 'Equity',
        value: usd(position.equity_usd),
        note: `${compactUsd(position.collateral_usd)} collateral − ${compactUsd(position.debt_usd)} debt`,
      },
      {
        label: `Carry (${simulation.horizon_days} d)`,
        value: usd(decision.carry_usd),
        note: `implied ${percent(position.implied_apy, 2)} vs borrow ${percent(position.borrow_apy, 2)}`,
      },
      {
        label: 'Expected loss',
        value: usd(simulation.expected_loss_usd),
        note: `net of carry ${usd(decision.net_stay_usd)}`,
        tone: netTone,
      },
      {
        label: 'Days to maturity',
        value: days(position.days_to_maturity),
        note: position.maturity.slice(0, 10),
      },
    ];
  }, [position, decision, simulation]);

  return (
    <div className="mx-auto max-w-[1120px] px-5.5 pt-9 pb-14">
      <h1>{position.label}</h1>
      <p className="mb-9 text-muted-foreground">
        {position.collateral_symbol} collateral against {position.loan_symbol} · oracle{' '}
        <b>{position.oracle_mode}</b>
        {position.oracle_ambiguous ? ' (ambiguous)' : ''} · report generated {report.generated} from
        data as of {report.data_as_of} ({report.mode})
      </p>

      {/* No box, no rule, no tint: the verdict is the largest thing on the page
          and the only coloured word in it. That is the whole hierarchy. */}
      <section>
        <h2 className="sr-only">Verdict</h2>
        <div
          className={`mb-3.5 text-[clamp(2.2rem,6vw,3.1rem)] leading-none font-extrabold tracking-[-0.03em] ${VERDICT_TONE[decision.verdict]}`}
        >
          {decision.verdict}
        </div>
        <p className="mb-5.5 text-[1.08rem] leading-[1.5]">{decision.headline}</p>
        <ul className={REASONS}>
          {decision.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      </section>

      <h2>Position</h2>
      <StatRow items={stats} />

      <h2>Where the expected loss comes from</h2>
      <div className={BLOCKS}>
        <LayerContributionChart layers={simulation.layers} total={simulation.expected_loss_usd} />
        <TailChart report={report} />
      </div>

      <h2>Exit and sensitivity</h2>
      <div className={BLOCKS}>
        <div>
          <h3>A full exit now</h3>
          <p className={BLOCK_SUB}>{exit_quote.source}</p>
          <SpecTable
            rows={[
              ['exit cost', usd(decision.exit_cost_usd)],
              ['price impact', percent(exit_quote.price_impact)],
              ['fee', usd(exit_quote.fee_usd, 2)],
              ['quote', exit_quote.estimated ? 'estimated (no live quote)' : 'live'],
              [
                'pays off only if incidents are',
                `${num(decision.risk_multiple_to_exit, 1)}× the estimates`,
              ],
            ]}
          />
        </div>

        <div>
          <h3>If the oracle were read differently</h3>
          <p className={BLOCK_SUB}>
            {oracle_sensitivity
              ? `The inference is ambiguous; this is the verdict under the ${oracle_sensitivity.oracle_mode} reading.`
              : 'The oracle reading is unambiguous, so no alternative was computed.'}
          </p>
          {oracle_sensitivity ? (
            <SpecTable
              rows={[
                [
                  'verdict',
                  `${oracle_sensitivity.verdict}${
                    oracle_sensitivity.verdict === decision.verdict ? ' (the same)' : ''
                  }`,
                ],
                [
                  'expected loss',
                  `${usd(oracle_sensitivity.expected_loss_usd)} (vs ${usd(simulation.expected_loss_usd)})`,
                ],
                [
                  'CVaR 99',
                  `${usd(oracle_sensitivity.cvar99_usd)} (vs ${usd(simulation.cvar99_usd)})`,
                ],
                [
                  'P(liquidation)',
                  `${percent(oracle_sensitivity.p_liquidation)} (vs ${percent(simulation.p_liquidation)})`,
                ],
              ]}
            />
          ) : null}
        </div>
      </div>

      {position.notes.length > 0 ? (
        <>
          <h2>Notes and cross-checks</h2>
          <ul className={REASONS}>
            {position.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </>
      ) : null}
    </div>
  );
}

/* ----------------------------------------------------------------- charts */

type LayerDatum = {
  name: string;
  contribution: number;
  layer: SimulationLayer;
};

function LayerContributionChart({ layers, total }: { layers: SimulationLayer[]; total: number }) {
  const data = useMemo<LayerDatum[]>(
    () =>
      [...layers]
        .sort((a, b) => b.contribution_usd - a.contribution_usd)
        .map((layer) => ({ name: layer.layer, contribution: layer.contribution_usd, layer })),
    [layers],
  );

  return (
    <div>
      <h3>Contribution to the expected loss</h3>
      <p className={BLOCK_SUB}>
        {usd(total)} over the horizon, split across the layers that can cause it.
      </p>
      <ResponsiveContainer width="100%" height={40 + data.length * 44}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
          <CartesianGrid stroke="var(--line)" horizontal={false} />
          <XAxis
            type="number"
            stroke="var(--muted)"
            fontSize={11}
            tickFormatter={(v: number) => compactUsd(v)}
          />
          <YAxis
            type="category"
            dataKey="name"
            stroke="var(--muted)"
            fontSize={11}
            width={196}
            tickFormatter={(v: string) => (v.length > 36 ? `${v.slice(0, 35)}…` : v)}
          />
          <Tooltip
            content={(props) => <LayerTooltip {...props} />}
            cursor={{ fill: 'var(--line)', opacity: 0.3 }}
          />
          <Bar dataKey="contribution" fill="var(--muted)" isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function LayerTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload?.length) return null;
  const datum = payload[0].payload as LayerDatum;
  const { layer } = datum;
  return (
    <div className={TOOLTIP}>
      <strong>{layer.layer}</strong>
      {usd(layer.contribution_usd)} of expected loss
      <br />
      {percent(layer.p_horizon)} chance over the horizon
      <br />
      {usd(layer.standalone_loss_usd)} if it happens
      <br />
      liquidates {percent(layer.liquidation_rate, 0)} of the time
    </div>
  );
}

type TailDatum = { name: string; value: number; note: string };

function TailChart({ report }: { report: Report }) {
  const { simulation, position } = report;
  const data: TailDatum[] = [
    { name: 'VaR 95', value: simulation.var95_usd, note: 'loss the worst 5% starts at' },
    { name: 'CVaR 95', value: simulation.cvar95_usd, note: 'mean loss of the worst 5%' },
    { name: 'VaR 99', value: simulation.var99_usd, note: 'loss the worst 1% starts at' },
    { name: 'CVaR 99', value: simulation.cvar99_usd, note: 'mean loss of the worst 1%' },
  ];

  return (
    <div>
      <h3>Tail measures</h3>
      <p className={BLOCK_SUB}>
        {simulation.n.toLocaleString('en-US')} paths over {simulation.horizon_days} days. Equity is{' '}
        {usd(position.equity_usd)}; P(any loss) {percent(simulation.p_any_loss)}, P(liquidation){' '}
        {percent(simulation.p_liquidation)}.
      </p>
      <ResponsiveContainer width="100%" height={236}>
        <BarChart data={data} margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis dataKey="name" stroke="var(--muted)" fontSize={11} />
          <YAxis
            stroke="var(--muted)"
            fontSize={11}
            tickFormatter={(v: number) => compactUsd(v)}
            width={62}
          />
          <Tooltip
            content={(props) => <TailTooltip {...props} equity={position.equity_usd} />}
            cursor={{ fill: 'var(--line)', opacity: 0.3 }}
          />
          <Bar dataKey="value" isAnimationActive={false}>
            {data.map((datum) => (
              <Cell
                key={datum.name}
                fill={datum.value >= position.equity_usd ? 'var(--critical)' : 'var(--muted)'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function TailTooltip({ active, payload, equity }: TooltipContentProps & { equity: number }) {
  if (!active || !payload?.length) return null;
  const datum = payload[0].payload as TailDatum;
  return (
    <div className={TOOLTIP}>
      <strong>
        {datum.name}: {usd(datum.value)}
      </strong>
      {datum.note}
      <br />
      {equity > 0 ? `${percent(datum.value / equity, 0)} of equity` : null}
    </div>
  );
}
