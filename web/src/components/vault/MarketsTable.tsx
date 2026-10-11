import { Link } from '@tanstack/react-router';
import type { Vault } from '../../api/types';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { percent, usd } from '../../lib/format';
import { BorrowerCell, CushionCell, InlineBar, MAIN_LENDER, OracleCell } from './cells';

// registry.json thresholds, which the frontend cannot read: watch.lender_concentration_warn,
// watch.concentration_top1_warn and watch.concentration_min_borrowers.
const COLUMNS = [
  { name: 'Market', why: 'Collateral / loan token of the Morpho Blue market the vault lends to' },
  { name: 'Allocation', right: true, why: 'USD the vault lends in this market' },
  {
    name: 'Of vault',
    right: true,
    why: "Allocation ÷ the vault's total: the higher, the more a problem here reaches your position",
  },
  {
    name: 'Of market',
    why: "The vault's share of the market's lenders. Main lender at 50%: the vault takes most of any loss and is drained first",
  },
  {
    name: 'Oracle',
    why: 'Tracks price: a collateral fall liquidates borrowers. Constant price: fixed, NAV or exchange rate; nobody is liquidated on a depeg and lenders take the loss. A red ring marks a stale feed',
  },
  {
    name: 'Cushion',
    why: "Light mark: 1 − LLTV, the fall that brings a borrower at max leverage to collateral = debt. Grey or red mark: the collateral's worst 1-year fall. Red: history already went past the cushion. The liquidation incentive makes bad debt start slightly earlier",
  },
  {
    name: 'Top borrower',
    why: "The largest borrower's share of the market's debt. Warns at 50% or under 5 borrowers: the loss is not spread",
  },
  {
    name: 'Utilization',
    right: true,
    why: 'Borrowed ÷ supplied. Near 100%, almost nothing can be withdrawn from this market',
  },
  {
    name: 'LLTV',
    right: true,
    why: 'Loan-to-value at which a borrower is liquidated. The higher, the thinner the cushion',
  },
];

/** The vault's markets: allocation, lender share, oracle, cushion, top borrower. Without `onSelect`, a market links to its page. */
export function MarketsTable({
  vault,
  onSelect,
}: {
  vault: Vault;
  onSelect?: (id: string) => void;
}) {
  return (
    <Table className="text-[0.86rem] tabular-nums">
      <TableHeader>
        <TableRow>
          {COLUMNS.map(({ name, right, why }) => (
            <TableHead key={name} className={right ? 'text-right' : undefined}>
              <HoverTooltip>
                <TooltipTrigger asChild>
                  <span className="cursor-help">{name}</span>
                </TooltipTrigger>
                <TooltipContent className="max-w-72">{why}</TooltipContent>
              </HoverTooltip>
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {vault.markets.map((m) => (
          <TableRow key={m.id}>
            <TableCell>
              {onSelect ? (
                <button
                  type="button"
                  className="cursor-pointer text-left underline-offset-4 hover:underline"
                  onClick={() => onSelect(m.id)}
                >
                  {m.label}
                </button>
              ) : (
                <Link to="/market/$marketId" params={{ marketId: m.id }} search={(prev) => prev}>
                  {m.label}
                </Link>
              )}
            </TableCell>
            <TableCell className="text-right">{usd(m.allocation_usd)}</TableCell>
            <TableCell className="text-right">{percent(m.share_of_vault)}</TableCell>
            <TableCell>
              <span className="flex items-center gap-2">
                <InlineBar value={m.share_of_market} />
                {percent(m.share_of_market)}
                {m.share_of_market >= MAIN_LENDER ? (
                  <span className="text-xs text-warn">main lender</span>
                ) : null}
              </span>
            </TableCell>
            <TableCell>
              <OracleCell market={m} />
            </TableCell>
            <TableCell>
              <CushionCell market={m} />
            </TableCell>
            <TableCell>
              <BorrowerCell market={m} />
            </TableCell>
            <TableCell className="text-right">{percent(m.utilization)}</TableCell>
            <TableCell className="text-right">{percent(m.lltv)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
