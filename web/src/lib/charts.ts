/** Series colours are defined once in index.css; repeat in the same order everywhere. */
export const CHART_COLORS = Array.from({ length: 5 }, (_, i) => `var(--chart-${i + 1})`);
