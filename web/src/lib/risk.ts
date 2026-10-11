import type { Vault } from '../api/types';

/**
 * The vault's bad debt, in USD, when each market's collateral falls by `dropOf(market)`, a market
 * with a null drop left out: max(0, debt − collateral × (1 − drop) / LIF).
 */
export function badDebtBy(vault: Vault, dropOf: (market: string) => number | null): number {
  const lif = new Map(vault.markets.map((m) => [m.id, m.lif]));
  return vault.liquidations.reduce((sum, l) => {
    const drop = dropOf(l.market ?? '');
    if (drop == null) return sum;
    return (
      sum +
      Math.max(0, l.debt_usd - (l.collateral_usd * (1 - drop)) / (lif.get(l.market ?? '') ?? 1))
    );
  }, 0);
}

/** The vault's bad debt, in USD, if every collateral fell by `drop` at once. */
export function badDebt(vault: Vault, drop: number): number {
  return badDebtBy(vault, () => drop);
}
