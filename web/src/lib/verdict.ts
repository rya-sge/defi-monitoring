import type { Verdict } from '../api/types';

export const VERDICT_TONE: Record<Verdict, string> = {
  STAY: 'text-ok',
  REDUCE: 'text-warn',
  EXIT: 'text-critical',
};

export const VERDICT_LABEL: Record<Verdict, string> = {
  STAY: 'Stay',
  REDUCE: 'Reduce',
  EXIT: 'Exit',
};

/** Act first on EXIT, then REDUCE, then STAY. */
export const VERDICT_PRIORITY: Record<Verdict, number> = { EXIT: 0, REDUCE: 1, STAY: 2 };

/** A breakeven probability: at or above 1, leaving never pays. */
export function pStar(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return '—';
  if (value >= 1) return '≥ 100%';
  if (value < 0.01) return '< 1%';
  return `${(value * 100).toFixed(0)}%`;
}
