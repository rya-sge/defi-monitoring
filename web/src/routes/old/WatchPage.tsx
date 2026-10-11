import { useMemo, useState } from 'react';
import { useSelectedTarget } from '../../api/hooks';
import { USE_MOCKS } from '../../api/client';
import { ALERT_LEVELS } from '../../api/types';
import type { AlertLevel } from '../../api/types';
import { blockNumber } from '../../lib/format';
import { AlertRow } from '../../components/alerts/AlertRow';
import { keyOf, LEVEL_TEXT, STATUS_CLASS, STATUS_LABEL } from '../../components/alerts/alertStyles';
import { useWatchStream } from '../../components/alerts/useWatchStream';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from 'cn';

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
  const { alerts, ticks, status } = useWatchStream(target, minLevel);
  const [expanded, setExpanded] = useState<string | null>(null);

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
