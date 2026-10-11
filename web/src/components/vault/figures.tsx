import { cn } from 'cn';
import type { Vault, VaultMarket } from '../../api/types';
import { Table, TableBody, TableCell, TableHead, TableRow } from '@/components/ui/table';
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { num, percent, usd } from '../../lib/format';
import { badDebt, badDebtBy } from '../../lib/risk';
import { MAIN_LENDER, TOP1_WARN } from './cells';

export type Figure = { label: string; tip: string; value: string; critical?: boolean };

/** The vault's risk figures: exit, run coverage, distance to bad debt, historical worst, oracles, concentration. */
function vaultFigures(vault: Vault): Figure[] {
  const exit = vault.exit ?? null;
  const loss = (drop: number) => badDebt(vault, drop);
  const ofAllocation = (keep: (m: VaultMarket) => boolean) =>
    vault.markets.filter(keep).reduce((sum, m) => sum + m.share_of_vault, 0);
  const leavable = exit ? exit.plain + exit.forced : 0;
  const run = exit?.holders
    .filter((h) => h.address !== exit.depositor)
    .slice(0, 3)
    .reduce((sum, h) => sum + h.assets, 0);
  const tolerated = Array.from({ length: 101 }, (_, i) => i / 100).find(
    (d) => loss(d) > 0.01 * vault.total_assets_usd,
  );
  const drawdowns = new Map(vault.markets.map((m) => [m.id, m.collateral_drawdown_1y]));
  const atWorst = badDebtBy(vault, (id) => drawdowns.get(id) ?? null);
  const skipped = vault.markets.filter((m) => m.collateral_drawdown_1y == null).length;
  return [
    {
      label: 'Your exit now',
      tip: 'Share of your position that can leave at par now: idle, liquidity market and forceDeallocate',
      value: exit && exit.position > 0 ? percent(Math.min(1, leavable / exit.position)) : '—',
    },
    {
      label: 'Run coverage',
      tip: 'What can leave now ÷ the three largest other holders: below 1×, they alone empty it',
      value: run ? `${num(leavable / run, 1)}×` : '—',
      critical: !!run && leavable < run,
    },
    {
      label: 'Distance to bad debt',
      tip: 'The uniform collateral fall at which bad debt passes 1% of the vault',
      value: tolerated == null ? '> −100%' : `−${percent(tolerated)}`,
    },
    {
      label: 'Loss at historical worst',
      tip: `Bad debt if each collateral fell by its worst 1-year drawdown${skipped ? `; ${skipped} market${skipped > 1 ? 's' : ''} without history left out` : ''}`,
      value: `${usd(atWorst)} (${percent(vault.total_assets_usd > 0 ? atWorst / vault.total_assets_usd : null)})`,
      critical: atWorst > 0,
    },
    {
      label: 'Behind constant-price oracles',
      tip: 'Allocation in markets whose oracle does not follow the collateral: a depeg liquidates nobody',
      value: vault.markets.some((m) => m.oracle_class != null)
        ? percent(ofAllocation((m) => m.oracle_class === 'constant-price'))
        : '—',
    },
    {
      label: 'Concentrated',
      tip: 'Allocation in markets with one borrower above half the debt, or where the vault is the main lender',
      value: percent(
        ofAllocation((m) => (m.top1_share ?? 0) >= TOP1_WARN || m.share_of_market >= MAIN_LENDER),
      ),
    },
  ];
}

/** The figures as a two-column table, each label with its tooltip. */
export function RiskFigures({ vault }: { vault: Vault }) {
  return (
    <Table className="text-[0.86rem] tabular-nums">
      <TableBody>
        {vaultFigures(vault).map((item) => (
          <TableRow key={item.label}>
            <TableHead scope="row" className="w-full max-w-0 font-normal text-muted-foreground">
              <HoverTooltip>
                <TooltipTrigger asChild>
                  <span className="block cursor-help truncate">{item.label}</span>
                </TooltipTrigger>
                <TooltipContent className="max-w-72">{item.tip}</TooltipContent>
              </HoverTooltip>
            </TableHead>
            <TableCell
              className={cn('text-right whitespace-nowrap', item.critical && 'text-critical')}
            >
              {item.value}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
