import type {
  AlertPage,
  AnalyzeRequest,
  GraphQuery,
  GraphResponse,
  Health,
  Report,
  ShockTrace,
  Target,
  Vault,
  Market,
  WatchQuery,
  BookSummary,
  IncidentRequest,
  IncidentResponse,
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
  if (!res.ok) {
    const error: unknown = await res.json().catch(() => null);
    const detail =
      error && typeof error === 'object' && 'detail' in error && typeof error.detail === 'string'
        ? error.detail
        : `${res.status} ${res.statusText}`;
    throw new ApiError(res.status, detail);
  }
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
  async books(signal?: AbortSignal): Promise<BookSummary[]> {
    if (USE_MOCKS) return delay((await import('../mocks/books.json')).default as BookSummary[]);
    return get<BookSummary[]>('/api/books', signal);
  },

  async incident(body: IncidentRequest, signal?: AbortSignal): Promise<IncidentResponse> {
    if (USE_MOCKS) {
      const cases = (await import('../mocks/incidents.json')).default as {
        request: IncidentRequest;
        response: IncidentResponse;
      }[];
      const match = cases.find(
        ({ request }) =>
          !body.live &&
          request.example === body.example &&
          JSON.stringify(request.vaults?.map((v) => v.toLowerCase())) ===
            JSON.stringify(body.vaults?.map((v) => v.toLowerCase())) &&
          request.horizon === body.horizon &&
          JSON.stringify(request.shocks) === JSON.stringify(body.shocks),
      );
      if (!match)
        throw new ApiError(
          404,
          'No fixture for this scenario. Try PST −30%, fxSAVE −30%, or the largest borrower of all markets with 50% collateral recovery, over 30 days, on the RockawayX book or one of its vaults. Other scenarios need the offline API with VITE_USE_MOCKS=false.',
        );
      return delay(match.response, 900);
    }
    return post<IncidentResponse>('/api/incident', body, signal);
  },

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
   * A shock trace. No endpoint serves one yet: in both modes this is the committed example
   * (`docs/shock-trace-example.json`: RockawayX USDC Yield, the Ojo PT feed reading 10 % low).
   */
  shockTrace(): Promise<ShockTrace> {
    return delay(MOCK_SHOCK_TRACE);
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
