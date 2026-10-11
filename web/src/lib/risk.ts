import type { Vault } from '../api/types';

/** The vault's bad debt, in USD, if every collateral fell by `drop` at once: max(0, debt − collateral × (1 − drop) / LIF). */
export function badDebt(vault: Vault, drop: number): number {
  const lif = new Map(vault.markets.map((m) => [m.id, m.lif]));
  return vault.liquidations.reduce(
    (sum, l) =>
      sum +
      Math.max(0, l.debt_usd - (l.collateral_usd * (1 - drop)) / (lif.get(l.market ?? '') ?? 1)),
    0,
  );
}
