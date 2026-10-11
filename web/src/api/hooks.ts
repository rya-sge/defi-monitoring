import { useMutation, useQuery } from '@tanstack/react-query';
import { useSearch } from '@tanstack/react-router';
import { api, EXAMPLE_SHOCK } from './client';
import type {
  AnalyzeRequest,
  Backtest,
  BacktestSummary,
  GraphQuery,
  GraphResponse,
  Health,
  Report,
  ShockRequest,
  ShockTarget,
  ShockTrace,
  Target,
  Market,
  Vault,
} from './types';

export const queryKeys = {
  health: ['health'] as const,
  report: ['report'] as const,
  targets: ['targets'] as const,
  graph: (query: GraphQuery) => ['graph', query] as const,
};

export function useHealth() {
  return useQuery<Health>({
    queryKey: queryKeys.health,
    queryFn: ({ signal }) => api.health(signal),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}

export function useReport() {
  return useQuery<Report>({
    queryKey: queryKeys.report,
    queryFn: ({ signal }) => api.report(signal),
    staleTime: 5 * 60_000,
  });
}

export function useGraph(query: GraphQuery = {}) {
  return useQuery<GraphResponse>({
    queryKey: queryKeys.graph(query),
    queryFn: ({ signal }) => api.graph(query, signal),
    staleTime: 5 * 60_000,
  });
}

export function useShockTrace(body: ShockRequest = EXAMPLE_SHOCK) {
  return useQuery<ShockTrace>({
    queryKey: ['shock-trace', body],
    queryFn: ({ signal }) => api.shockTrace(body, signal),
    staleTime: Infinity,
  });
}

export function useShockTargets(vault: string | undefined) {
  return useQuery<ShockTarget[]>({
    queryKey: ['shock-targets', vault],
    queryFn: ({ signal }) => api.shockTargets(vault!, signal),
    enabled: !!vault,
    staleTime: Infinity,
  });
}

export function useBacktests() {
  return useQuery<BacktestSummary[]>({
    queryKey: ['backtests'],
    queryFn: ({ signal }) => api.backtests(signal),
    staleTime: Infinity,
  });
}

export function useBacktest(episode: string | undefined) {
  return useQuery<Backtest>({
    queryKey: ['backtest', episode],
    queryFn: ({ signal }) => api.backtest(episode!, signal),
    enabled: !!episode,
    staleTime: Infinity,
  });
}

export function useAnalyze() {
  return useMutation<Report, Error, AnalyzeRequest>({
    mutationFn: (body) => api.analyze(body),
  });
}

export function useVault(address: string | undefined) {
  return useQuery<Vault>({
    queryKey: ['vault', address],
    queryFn: ({ signal }) => api.vault(address!, signal),
    enabled: !!address,
    staleTime: 60_000,
  });
}

export function useMarket(id: string) {
  return useQuery<Market>({
    queryKey: ['market', id],
    queryFn: ({ signal }) => api.market(id, signal),
    staleTime: 60_000,
  });
}

export function useTargets() {
  return useQuery<Target[]>({
    queryKey: queryKeys.targets,
    queryFn: ({ signal }) => api.targets(signal),
    staleTime: 60_000,
  });
}

/** `?target=` from the URL, else the first watch target: one vault at a time, never all. */
export function useSelectedTarget(): { target: string | undefined; isPending: boolean } {
  const { target } = useSearch({ strict: false });
  const targets = useTargets();
  return {
    target: target ?? targets.data?.[0]?.target,
    isPending: !target && targets.isPending,
  };
}
