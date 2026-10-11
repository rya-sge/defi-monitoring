import { ChevronDown } from 'lucide-react';
import { cn } from 'cn';
import { useAlerts } from '../../api/hooks';
import type { Alert, Vault } from '../../api/types';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Table, TableBody, TableCell, TableRow } from '@/components/ui/table';
import { Tooltip as HoverTooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { blockNumber, etherscanUrl, shortHash } from '../../lib/format';

/** Governance and admin-surface alerts (docs/alert-runbook.md): what the curator or a dependency changed. */
export const CHANGE =
  /^(Admin|AdminState|Timelock|ExitGate|Blue\.SetOwner)\b|^(Vault|Adapter)\.(Submit|Accept|Revoke|Increase|Decrease|Add|Remove|Set|Abdicate|BurnShares)/;
export const PENDING = /(Submit|CallScheduled)$/;

export function Changes({ vault }: { vault: Vault }) {
  const { data, error } = useAlerts(vault.address);
  const changes = (data?.alerts ?? []).filter((alert) => CHANGE.test(alert.event)).reverse();
  const pending = changes.filter((alert) => PENDING.test(alert.event)).length;
  const critical = changes.some((alert) => alert.level === 'critical');
  const pill = 'rounded-full border px-2.5 py-0.5 text-xs tabular-nums';

  return (
    <Collapsible className="grid gap-4">
      <header className="flex items-center justify-between gap-4">
        <h1 className="m-0 truncate">{vault.name}</h1>
        {error ? (
          <span className={cn(pill, 'text-muted-foreground')}>Not watched</span>
        ) : !data ? null : changes.length ? (
          <CollapsibleTrigger
            className={cn(
              pill,
              'group flex shrink-0 cursor-pointer items-center gap-1',
              critical && 'border-critical text-critical',
            )}
          >
            {changes.length} {changes.length === 1 ? 'change' : 'changes'}
            {pending ? ` · ${pending} pending` : ''}
            <ChevronDown
              size={12}
              className="transition-transform group-data-[state=open]:rotate-180"
            />
          </CollapsibleTrigger>
        ) : (
          <span className={cn(pill, 'text-muted-foreground')}>No change</span>
        )}
      </header>
      <CollapsibleContent>
        <Table className="text-[0.86rem] tabular-nums">
          <TableBody>
            {changes.map((alert, index) => (
              <ChangeRow key={`${alert.block}-${alert.event}-${index}`} alert={alert} />
            ))}
          </TableBody>
        </Table>
      </CollapsibleContent>
    </Collapsible>
  );
}

const LEVEL = { info: 'bg-muted-foreground', warn: 'bg-warn', critical: 'bg-critical' } as const;

function ChangeRow({ alert }: { alert: Alert }) {
  const tx = alert.tx ? etherscanUrl(alert.tx) : null;
  return (
    <TableRow>
      <TableCell className="w-4">
        <span className={cn('block size-2 rounded-full', LEVEL[alert.level])} />
      </TableCell>
      <TableCell className="max-w-0 w-full">
        <HoverTooltip>
          <TooltipTrigger asChild>
            <span className="block truncate">{alert.title}</span>
          </TooltipTrigger>
          <TooltipContent className="max-w-96">{alert.detail}</TooltipContent>
        </HoverTooltip>
      </TableCell>
      <TableCell className="text-muted-foreground">{alert.event}</TableCell>
      <TableCell className="text-right">Block {blockNumber(alert.block)}</TableCell>
      <TableCell className="text-right">
        {tx && alert.tx ? (
          <a href={tx} target="_blank" rel="noreferrer">
            {shortHash(alert.tx)}
          </a>
        ) : (
          '—'
        )}
      </TableCell>
    </TableRow>
  );
}
