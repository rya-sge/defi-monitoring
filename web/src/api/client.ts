import type {
  AlertPage,
  Backtest,
  BacktestSummary,
  AnalyzeRequest,
  GraphQuery,
  GraphResponse,
  Health,
  Report,
  ShockGraph,
  ShockRequest,
  ShockSweep,
  ShockSweepRequest,
  ShockTarget,
  ShockTrace,
  Target,
  Vault,
  Market,
  WatchQuery,
} from './types';
import graphFixture from '../mocks/graph.json';
import shockTraceFixture from '../mocks/shock-trace.json';
import reportFixture from '../mocks/report.json';

/** `VITE_USE_MOCKS` defaults to true: the frontend runs with no backend at all. */
export const USE_MOCKS = import.meta.env.VITE_USE_MOCKS !== 'false';

const MOCK_LATENCY_MS = 250;

const MOCK_GRAPH = graphFixture as unknown as GraphResponse;
const MOCK_SHOCK_TRACE = shockTraceFixture as unknown as ShockTrace;
const MOCK_REPORT = reportFixture as unknown as Report;

/** The trace `api.shockTrace()` returns with no request: the committed example. */
export const EXAMPLE_SHOCK: ShockRequest = {
  vault: ['0xe0181090c22579b6a217f1522cbf8c9f1f0c1965'],
  shocks: ['Ojo PT:reads-low:10%'],
};

type ShockFixtures = {
  graphs: ShockGraph[];
  targets: Record<string, ShockTarget[]>;
  sweep: Record<string, ShockSweep>;
};
type BacktestFixtures = { list: BacktestSummary[]; episodes: Record<string, Backtest> };

// recorded from the API (`/api/shock*`, `/api/backtest*`) on the committed fixtures; loaded on demand
const shockFixtures = async () => (await import('../mocks/shock.json')).default as ShockFixtures;
const backtestFixtures = async () =>
  (await import('../mocks/backtests.json')).default as unknown as BacktestFixtures;

function delay<T>(value: T, ms = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

function fixture<T>(value: T | undefined, what: string): Promise<T> {
  return value ? delay(value) : Promise.reject(new ApiError(404, `no fixture for ${what}`));
}

export class ApiError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, { signal, headers: { accept: 'application/json' } });
  if (!res.ok)
    throw new ApiError(res.status, `GET ${path} failed: ${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

async function post<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    signal,
    headers: { 'content-type': 'application/json', accept: 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok)
    throw new ApiError(res.status, `POST ${path} failed: ${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

function queryString(params: Record<string, string | number | undefined>): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') sp.set(key, String(value));
  }
  const s = sp.toString();
  return s ? `?${s}` : '';
}

export const api = {
  health(signal?: AbortSignal): Promise<Health> {
    if (USE_MOCKS) {
      return delay<Health>({
        status: 'ok',
        // Mirrors the fixture: the committed report was produced offline.
        mode: 'offline',
        data_as_of: MOCK_REPORT.data_as_of,
      });
    }
    return get<Health>('/api/health', signal);
  },

  graph(query: GraphQuery = {}, signal?: AbortSignal): Promise<GraphResponse> {
    if (USE_MOCKS) return delay(MOCK_GRAPH);
    return get<GraphResponse>(`/api/graph${queryString({ ...query })}`, signal);
  },

  /**
   * A shock trace (`POST /api/shock`). Mocking, only the committed example is available
   * (`docs/model/shock-trace-example.json`: RockawayX USDC Yield, the Ojo PT feed reading 10 % low).
   */
  shockTrace(body: ShockRequest = EXAMPLE_SHOCK, signal?: AbortSignal): Promise<ShockTrace> {
    if (USE_MOCKS) return delay(MOCK_SHOCK_TRACE);
    return post<ShockTrace>('/api/shock', body, signal);
  },

  /** The graphs recorded for offline shocks: pass a `target` as `vault` (or `user`). */
  async shockGraphs(signal?: AbortSignal): Promise<ShockGraph[]> {
    if (USE_MOCKS) return delay((await shockFixtures()).graphs);
    return get<ShockGraph[]>('/api/shock/graphs', signal);
  },

  /** The nodes of a vault's graph that can be shocked, held markets first. */
  async shockTargets(vault: string, signal?: AbortSignal): Promise<ShockTarget[]> {
    if (USE_MOCKS)
      return fixture((await shockFixtures()).targets[vault], `shock targets of ${vault}`);
    return get<ShockTarget[]>(`/api/shock/targets${queryString({ vault })}`, signal);
  },

  async shockSweep(body: ShockSweepRequest, signal?: AbortSignal): Promise<ShockSweep> {
    if (USE_MOCKS) {
      // the fixture is the reads-low 10 % sweep of the example vault
      const vault = body.vault?.[0] ?? '';
      return fixture((await shockFixtures()).sweep[vault], `shock sweep of ${vault}`);
    }
    return post<ShockSweep>('/api/shock/sweep', body, signal);
  },

  async backtests(signal?: AbortSignal): Promise<BacktestSummary[]> {
    if (USE_MOCKS) return delay((await backtestFixtures()).list);
    return get<BacktestSummary[]>('/api/backtests', signal);
  },

  async backtest(episode: string, signal?: AbortSignal): Promise<Backtest> {
    if (USE_MOCKS)
      return fixture((await backtestFixtures()).episodes[episode], `backtest ${episode}`);
    return get<Backtest>(`/api/backtest/${episode}`, signal);
  },

  async vault(address: string, signal?: AbortSignal): Promise<Vault> {
    if (USE_MOCKS) {
      // Every Vault V2 of the fixture graph, recorded; loaded on demand, it is the largest fixture.
      const vaults = (await import('../mocks/vaults.json')).default as Record<string, Vault>;
      return fixture(vaults[address], `vault ${address}`);
    }
    return get<Vault>(`/api/vault/${address}`, signal);
  },

  async market(id: string, signal?: AbortSignal): Promise<Market> {
    if (USE_MOCKS) {
      const markets = (await import('../mocks/markets.json')).default as Record<string, Market>;
      return fixture(markets[id], `market ${id}`);
    }
    return get<Market>(`/api/market/${id}`, signal);
  },

  report(signal?: AbortSignal): Promise<Report> {
    if (USE_MOCKS) return delay(MOCK_REPORT);
    return get<Report>('/api/report', signal);
  },

  analyze(body: AnalyzeRequest, signal?: AbortSignal): Promise<Report> {
    if (USE_MOCKS) return delay(MOCK_REPORT, 900);
    return post<Report>('/api/analyze', body, signal);
  },

  targets(signal?: AbortSignal): Promise<Target[]> {
    if (USE_MOCKS) {
      // The targets of the committed alert fixtures.
      return delay(
        [
          '0x6dc58a0fdfc8d694e571dc59b9a52eeea780e6bf',
          'user-0xb03d620e49b6a21ea9d02142831c3f61c2fcbabc',
          'user-0xdf81987465681d0515058fe0a47a3bd174012730',
        ].map((target) => ({ target, alerts: 0, last_block: null })),
      );
    }
    return get<Target[]>('/api/targets', signal);
  },

  /** One page of alerts after a block cursor. Pass the returned `cursor` back as `since`. */
  alerts(query: WatchQuery & { since?: number } = {}, signal?: AbortSignal): Promise<AlertPage> {
    return get<AlertPage>(
      `/api/alerts${queryString({
        target: query.target,
        since: query.since,
        level: query.min_level,
      })}`,
      signal,
    );
  },
};
