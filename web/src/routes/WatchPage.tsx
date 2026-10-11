import { FormattedText } from '../components/FormattedText';
import { useEffect, useMemo, useState } from 'react';
import { useSelectedTarget } from '../api/hooks';
import { subscribeWatch } from '../api/stream';
import type { StreamStatus } from '../api/stream';
import { USE_MOCKS } from '../api/client';
import { ALERT_LEVELS } from '../api/types';
import type { Alert, AlertLevel, WatchTick } from '../api/types';
import { blockNumber, etherscanUrl, shortHash, signedUsd } from '../lib/format';
import { DetailsTable } from '../components/DetailsTable';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from 'cn';

const LEVEL_TEXT: Record<AlertLevel, string> = {
  info: 'text-info',
  warn: 'text-warn',
  critical: 'text-critical',
};

const STATUS_LABEL: Record<StreamStatus, string> = {
  connecting: 'connecting…',
  open: 'live',
  closed: 'stream ended',
  error: 'reconnecting…',
};

// "live" is the normal state; colour stays for what is wrong.
const STATUS_CLASS: Record<StreamStatus, string> = {
  connecting: 'text-muted-foreground',
  open: 'text-foreground',
  closed: 'text-muted-foreground',
  error: 'text-warn',
};

export function WatchPage() {
  const [minLevel, setMinLevel] = useState<AlertLevel>('info');
  const { target } = useSelectedTarget();

  return (
    <div className="mx-auto max-w-[1120px] px-5.5 pt-9 pb-14">
      <h1>Alerts</h1>
      <p className="mb-9 text-muted-foreground">
        Server-Sent Events from <code className="mono">/api/watch/stream</code>, newest first.{' '}
        {USE_MOCKS
          ? 'Mock mode: a fixed set of alerts is replayed every 1.5 s, then the stream ends.'
          : 'Polling runs two blocks behind the head; deeper reorgs are not handled.'}
      </p>
      {/* `min_level` and `target` are server-side filters, so changing either must restart the
          stream from scratch. Keying on both remounts the subscriber, which drops
          the collected alerts without resetting state from inside an effect. */}
      <WatchStream
        key={`${target ?? ''}:${minLevel}`}
        target={target}
        minLevel={minLevel}
        onMinLevelChange={setMinLevel}
      />
    </div>
  );
}

function WatchStream({
  target,
  minLevel,
  onMinLevelChange,
}: {
  target?: string;
  minLevel: AlertLevel;
  onMinLevelChange: (level: AlertLevel) => void;
}) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [ticks, setTicks] = useState<WatchTick[]>([]);
  const [status, setStatus] = useState<StreamStatus>('connecting');
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(
    () =>
      subscribeWatch(
        { target, min_level: minLevel },
        {
          onAlert: (alert) => setAlerts((previous) => [alert, ...previous]),
          onTick: (tick) => setTicks((previous) => [tick, ...previous].slice(0, 3)),
          onStatus: setStatus,
        },
      ),
    [target, minLevel],
  );

  const counts = useMemo(() => {
    const result: Record<AlertLevel, number> = { info: 0, warn: 0, critical: 0 };
    for (const alert of alerts) result[alert.level] += 1;
    return result;
  }, [alerts]);

  // The mock replay is a fixed list, so the level floor is applied here as well.
  const shown = useMemo(() => {
    const floor = ALERT_LEVELS.indexOf(minLevel);
    return alerts.filter((alert) => ALERT_LEVELS.indexOf(alert.level) >= floor);
  }, [alerts, minLevel]);

  return (
    <>
      <div className="my-5.5 flex flex-wrap gap-x-9 gap-y-5.5">
        {ALERT_LEVELS.map((level) => (
          <div key={level}>
            <b className="text-2xl font-semibold tabular-nums">{counts[level]}</b>
            <span className={cn('block text-[0.8rem] font-semibold', LEVEL_TEXT[level])}>
              {level}
            </span>
          </div>
        ))}
      </div>

      <div className="my-5.5 flex flex-wrap items-baseline gap-2 text-[0.85rem] text-muted-foreground">
        <span className={cn('mr-9', STATUS_CLASS[status])}>{STATUS_LABEL[status]}</span>
        <Label htmlFor="min-level" className="font-normal">
          Minimum level
        </Label>
        <Select value={minLevel} onValueChange={(value) => onMinLevelChange(value as AlertLevel)}>
          <SelectTrigger id="min-level" size="sm" className="w-28">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ALERT_LEVELS.map((level) => (
              <SelectItem key={level} value={level}>
                {level}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {ticks.length > 0 ? (
        <p className="mb-5.5 text-[0.8rem] text-muted-foreground tabular-nums">
          {ticks.map((tick) => (
            <span key={`${tick.block}-${tick.message}`} className="block">
              block {blockNumber(tick.block)} · {tick.message}
            </span>
          ))}
        </p>
      ) : null}

      {shown.length === 0 ? (
        <p className="py-14 text-muted-foreground" role="status" aria-live="polite">
          {status === 'open' || status === 'connecting'
            ? 'Waiting for the first alert…'
            : 'No alert at this level.'}
        </p>
      ) : (
        <ul className="list-none" aria-live="polite">
          {shown.map((alert, index) => {
            const id = keyOf(alert, index);
            return (
              <AlertRow
                key={id}
                alert={alert}
                expanded={expanded === id}
                onToggle={() => setExpanded((previous) => (previous === id ? null : id))}
              />
            );
          })}
        </ul>
      )}
    </>
  );
}

/** Alerts carry no id; a state alert can repeat, so the index keeps rows apart. */
const keyOf = (alert: Alert, index: number) => `${alert.block}-${alert.event}-${index}`;

function AlertRow({
  alert,
  expanded,
  onToggle,
}: {
  alert: Alert;
  expanded: boolean;
  onToggle: () => void;
}) {
  const txUrl = alert.tx ? etherscanUrl(alert.tx) : null;
  const hasData = Object.keys(alert.data).length > 0;

  return (
    // Rows, not cards: one hairline keeps two alerts from reading as one.
    <li className="grid gap-1 border-b border-border/50 py-3.5">
      <div className="flex flex-wrap items-baseline gap-3.5 text-[0.8rem] text-muted-foreground">
        <span className={cn('font-bold', LEVEL_TEXT[alert.level])}>{alert.level}</span>
        <span>block {blockNumber(alert.block)}</span>
        <span className="mono">
          {txUrl && alert.tx ? (
            <a href={txUrl} target="_blank" rel="noreferrer noopener">
              {shortHash(alert.tx)}
            </a>
          ) : (
            'no tx'
          )}
        </span>
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
      <div className="max-w-measure font-bold">{alert.title}</div>
      <div className="max-w-measure text-[0.92rem] text-muted-foreground">{alert.detail}</div>
      {hasData ? (
        <Collapsible open={expanded} onOpenChange={onToggle}>
          <CollapsibleTrigger asChild>
            <Button type="button" variant="outline" size="sm">
              {expanded ? 'Hide data' : 'Show data'}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-2 max-w-[640px]">
            <DetailsTable details={alert.data} />
          </CollapsibleContent>
        </Collapsible>
      ) : null}
    </li>
  );
}
