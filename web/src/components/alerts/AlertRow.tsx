import type { ReactNode } from 'react';
import { Tip } from '../scenario/IncidentParts';
import { FormattedText } from '../FormattedText';
import { DetailsTable } from '../DetailsTable';
import type { Alert } from '../../api/types';
import { LEVEL_TEXT } from './alertStyles';
import { blockNumber, etherscanUrl, shortHash, signedUsd } from '../../lib/format';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { cn } from 'cn';

export function TxLink({ tx }: { tx: string | null }) {
  const url = tx ? etherscanUrl(tx) : null;
  return (
    <span className="mono">
      {url && tx ? (
        <a href={url} target="_blank" rel="noreferrer noopener">
          {shortHash(tx)}
        </a>
      ) : (
        'no tx'
      )}
    </span>
  );
}

export function AlertRow({
  alert,
  expanded,
  onToggle,
  actions,
}: {
  alert: Alert;
  expanded: boolean;
  onToggle: () => void;
  actions?: ReactNode;
}) {
  const hasData = Object.keys(alert.data).length > 0;

  return (
    // Rows, not cards: one hairline keeps two alerts from reading as one.
    <li className="grid gap-1 border-b border-border/50 py-3.5">
      <div className="flex flex-wrap items-baseline gap-3.5 text-[0.8rem] text-muted-foreground">
        <span className={cn('font-bold', LEVEL_TEXT[alert.level])}>{alert.level}</span>
        <span>block {blockNumber(alert.block)}</span>
        <TxLink tx={alert.tx} />
        <span className="mono">{alert.event}</span>
        {alert.depositor_impact != null ? (
          <span
            className={`ml-auto font-semibold tabular-nums ${alert.depositor_impact < 0 ? 'text-critical' : 'text-ok'}`}
            title="Impact on your deposit, in the vault's asset"
          >
            <FormattedText>{signedUsd(alert.depositor_impact)}</FormattedText>
          </span>
        ) : null}
      </div>
      <div className="max-w-measure font-bold">
        {alert.detail ? <Tip label={alert.title} tip={alert.detail} /> : alert.title}
      </div>
      {hasData || actions ? (
        <Collapsible open={expanded} onOpenChange={onToggle}>
          <div className="flex flex-wrap gap-2">
            {hasData ? (
              <CollapsibleTrigger asChild>
                <Button type="button" variant="outline" size="sm">
                  {expanded ? 'Hide data' : 'Show data'}
                </Button>
              </CollapsibleTrigger>
            ) : null}
            {actions}
          </div>
          <CollapsibleContent className="mt-2 max-w-[640px]">
            <DetailsTable details={alert.data} />
          </CollapsibleContent>
        </Collapsible>
      ) : null}
    </li>
  );
}
