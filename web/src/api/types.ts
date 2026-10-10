/**
 * Shapes of the `/api` payloads.
 *
 * Everything here was read off the real CLI output committed in `src/mocks/`
 * (`out/graph.json` and `out/report.json`, produced by `python -m riskdep graph`
 * and `python -m riskdep analyze`). Where the two files disagree it is noted on
 * the type; see `ReportGraph` in particular.
 *
 * The report writer passes every payload through a `clean()` that maps `inf` and
 * `nan` to `null`, so a ratio whose denominator can be zero — a health factor
 * with no debt, a risk multiple with no expected loss — arrives as `null`.
 * Those fields are typed `number | null` and every formatter tolerates it.
 */

/* ------------------------------------------------------------------ health */

export type Mode = 'offline' | 'live' | 'refresh';

export type Health = {
  status: 'ok';
  mode: Mode;
  data_as_of: string;
};

/* ------------------------------------------------------------------- graph */

/** The six node kinds of `riskdep graph` (see `riskdep/graph.py`). */
export type GraphNodeKind = 'Actor' | 'Pool' | 'Asset' | 'Oracle' | 'External' | 'Admin';

export const GRAPH_NODE_KINDS: readonly GraphNodeKind[] = [
  'Actor',
  'Pool',
  'Asset',
  'Oracle',
  'External',
  'Admin',
];

export type GraphNode = {
  id: string;
  kind: GraphNodeKind;
  label: string;
  /** Free-form evidence per kind: address, lltv, irm, price_raw, source… */
  details: Record<string, unknown>;
};

export type GraphEdge = {
  source: string;
  target: string;
  /** "supplies", "borrows from", "priced by", "reads", "relies on"… */
  rel: string;
  /** Carried amount in `unit`, when the edge carries one. */
  amount: number | null;
  unit: string | null;
  details: Record<string, unknown>;
};

export type GraphResponse = {
  title: string;
  /** Provenance line: chain, block, how the positions and amounts were read. */
  subtitle: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
};

/* ------------------------------------------------------------------ alerts */

export type AlertLevel = 'info' | 'warn' | 'critical';

export const ALERT_LEVELS: readonly AlertLevel[] = ['info', 'warn', 'critical'];

export type Alert = {
  level: AlertLevel;
  block: number;
  /** Null for state-derived alerts (Exposure, Caps, Liquidity, HealthFactor…). */
  tx: string | null;
  /** "Vault.Deposit", "Adapter.Deallocate", "HealthFactor", "AdminSurface"… */
  event: string;
  title: string;
  detail: string;
  /** In the vault's asset; negative is a loss. Null when not quantified. */
  depositor_impact: number | null;
  data: Record<string, unknown>;
};

export type WatchTick = {
  block: number;
  message: string;
};

/* ------------------------------------------------------------------ report */

export type OracleMode = 'market-tracking' | 'fundamental' | (string & {});

/** The 34 fields of `PositionFacts` as serialised by `riskdep/report.py`. */
export type ReportPosition = {
  label: string;
  collateral_units: number;
  collateral_symbol: string;
  collateral_address: string;
  pt_price_usd: number;
  collateral_decimals: number;
  debt_usd: number;
  loan_symbol: string;
  loan_address: string;
  lltv: number;
  /** Liquidation incentive factor, e.g. 1.0262 for a 2.62% bonus. */
  lif: number;
  borrow_apy: number;
  implied_apy: number;
  /** ISO 8601, e.g. "2026-11-26T00:00:00.000Z". */
  maturity: string;
  days_to_maturity: number;
  oracle_mode: OracleMode;
  oracle_ambiguous: boolean;
  pt_discount: number;
  morpho_market: string;
  borrower: string;
  /** Debt in the loan asset's smallest unit. */
  debt_raw: number;
  loan_decimals: number;
  oracle_price: number;
  /** Null when the position carries no debt (the writer maps `inf` to `null`). */
  health_factor: number | null;
  pendle_market: string;
  underlying_address: string;
  underlying_symbol: string;
  underlying_drawdown_1y: number;
  amm_liquidity_usd: number;
  lending_liquidity_usd: number;
  /** Free-text notes: oracle ambiguity, cross-check results. */
  notes: string[];
  collateral_usd: number;
  equity_usd: number;
  /** Fraction the oracle price must fall by to liquidate; null with no debt. */
  liquidation_drop: number | null;
};

/**
 * The graph embedded in a report is NOT the `/api/graph` shape.
 *
 * `analyze` serialises a networkx graph, so nodes carry flat attributes
 * (`source`, `evidence`, …) with lowercase kinds, and edges use `from`/`to`.
 * `lib/graph.ts` normalises it to `GraphResponse` so one Cytoscape component
 * can render both.
 */
export type ReportGraphNode = {
  id: string;
  /** chain | asset | amm | issuer | offchain | lending | oracle | stable | position */
  kind: string;
  label: string;
  source?: string;
  evidence?: string;
  mode?: string;
  protocol?: string;
  registered?: boolean;
};

export type ReportGraphEdge = {
  from: string;
  to: string;
  rel: string;
};

export type ReportGraph = {
  nodes: ReportGraphNode[];
  edges: ReportGraphEdge[];
};

export type ReportPrior = {
  event: string;
  node: string;
  layer: string;
  p_year: number;
  /** Beta parameters of the severity distribution. */
  a: number;
  b: number;
  basis: string;
  recovery: number;
};

export type SimulationLayer = {
  event: string;
  layer: string;
  node: string;
  p_horizon: number;
  mean_severity: number;
  /** Loss if this layer alone has an incident. */
  standalone_loss_usd: number;
  /** Share of the expected loss attributable to this layer. */
  contribution_usd: number;
  liquidation_rate: number;
  example_path: string[];
  basis: string;
};

export type ReportSimulation = {
  horizon_days: number;
  n: number;
  expected_loss_usd: number;
  var95_usd: number;
  cvar95_usd: number;
  var99_usd: number;
  cvar99_usd: number;
  p_any_loss: number;
  p_liquidation: number;
  layers: SimulationLayer[];
  /** Loss from layers interacting, on top of the sum of contributions. */
  interaction_usd: number;
};

export type Verdict = 'STAY' | 'REDUCE' | 'EXIT';

export type DecisionReduction = Record<string, unknown> & {
  sell_usd?: number;
  new_health_factor?: number;
  new_liquidation_drop?: number;
  cost_usd?: number;
  expected_loss_usd?: number;
  cvar99_usd?: number;
  carry_usd?: number;
  source?: string;
};

export type ReportDecision = {
  verdict: Verdict;
  headline: string;
  carry_usd: number;
  exit_cost_usd: number;
  expected_loss_usd: number;
  net_stay_usd: number;
  /** Null when the expected loss is zero. */
  risk_multiple_to_exit: number | null;
  liquidation_drop: number | null;
  stress_drop: number;
  reduction: DecisionReduction;
  reasons: string[];
};

export type ExitQuote = {
  source: string;
  price_impact: number;
  fee_usd: number;
  /** True when no live quote was available and the figure is modelled. */
  estimated: boolean;
  /** Present on a real Pendle quote; smallest unit, serialised as a string. */
  amount_out_raw?: string;
};

export type OracleSensitivity = {
  oracle_mode: OracleMode;
  verdict: Verdict;
  expected_loss_usd: number;
  cvar99_usd: number;
  p_liquidation: number;
};

export type Report = {
  generated: string;
  data_as_of: string;
  mode: string;
  position: ReportPosition;
  graph: ReportGraph;
  priors: ReportPrior[];
  simulation: ReportSimulation;
  decision: ReportDecision;
  exit_quote: ExitQuote;
  /** Only present when the oracle's behaviour is ambiguous. */
  oracle_sensitivity: OracleSensitivity | null;
};

/* ----------------------------------------------------------------- requests */

export type AnalyzeRequest = {
  market?: string;
  user?: string;
  horizon?: number;
  paths?: number;
  live?: boolean;
};

export type GraphQuery = {
  user?: string;
  vault?: string;
  block?: number;
};

export type WatchQuery = {
  vault?: string;
  user?: string;
  min_level?: AlertLevel;
};
