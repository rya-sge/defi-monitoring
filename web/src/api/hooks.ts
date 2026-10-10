import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from './client';
import type { AnalyzeRequest, GraphQuery, GraphResponse, Health, Report } from './types';

export const queryKeys = {
  health: ['health'] as const,
  report: ['report'] as const,
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

export function useAnalyze() {
  return useMutation<Report, Error, AnalyzeRequest>({
    mutationFn: (body) => api.analyze(body),
  });
}
