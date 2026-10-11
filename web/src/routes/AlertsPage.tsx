// What changed, and do I need to act now?
import { Link } from '@tanstack/react-router';
import { useMemo, useState } from 'react';
import { useSelectedTarget } from '../api/hooks';
import { ALERT_LEVELS } from '../api/types';
import type { Alert, AlertLevel } from '../api/types';
import { FormattedText } from '../components/FormattedText';
import { AlertRow, TxLink } from '../components/alerts/AlertRow';
import { keyOf, LEVEL_TEXT, STATUS_CLASS, STATUS_LABEL } from '../components/alerts/alertStyles';
import { useWatchStream } from '../components/alerts/useWatchStream';
import { blockNumber, detailValue, num, signedUsd } from '../lib/format';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from 'cn';

const VERDICT_TEXT: Record<string, string> = {
  STAY: 'text-ok',
  REDUCE: 'text-warn',
  EXIT: 'text-critical',
};

export function AlertsPage() {
  const [minLevel, setMinLevel] = useState<AlertLevel>('info');
  const { target } = useSelectedTarget();

  return (
    <div className="mx-auto grid max-w-[1120px] gap-10 px-5.5 pt-9 pb-14">
      {/* `min_level` and `target` are server-side filters: keying on both remounts the
          subscriber, which drops the collected alerts without resetting state in an effect. */}
      <AlertsView
        key={`${target ?? ''}:${minLevel}`}
        target={target}
        minLevel={minLevel}
        onMinLevelChange={setMinLevel}
      />
    </div>
  );
}

/** Warn and critical alerts that state an impact: a loss on the deposit, or an oracle fall's verdict. */
function actionable(alert: Alert) {
  return (
    alert.level !== 'info' && (alert.depositor_impact != null || alert.event === 'OracleImpact')
  );
}

/** One row per event kind and subject (market, feed, adapter): the newest wins. */
function subjectOf(alert: Alert) {
  const d = alert.data;
  return detailValue(d.market ?? d.feed ?? d.adapter ?? d.collateral ?? alert.title);
}

function AlertsView({
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
  const [event, setEvent] = useState<string | null>(null);

  // The mock replay is a fixed list, so the level floor is applied here as well.
  const atLevel = useMemo(() => {
    const floor = ALERT_LEVELS.indexOf(minLevel);
    return alerts.filter((alert) => ALERT_LEVELS.indexOf(alert.level) >= floor);
  }, [alerts, minLevel]);

  const counts = useMemo(() => {
    const levels: Record<AlertLevel, number> = { info: 0, warn: 0, critical: 0 };
    const events = new Map<string, number>();
    for (const alert of atLevel) {
      levels[alert.level] += 1;
      events.set(alert.event, (events.get(alert.event) ?? 0) + 1);
    }
    return { levels, events: [...events].sort((a, b) => b[1] - a[1]) };
  }, [atLevel]);

  const actNow = useMemo(() => {
    const seen = new Set<string>();
    return alerts
      .filter(actionable)
      .filter((alert) => {
        const key = `${alert.event}:${subjectOf(alert)}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      })
      .sort(
        (a, b) =>
          ALERT_LEVELS.indexOf(b.level) - ALERT_LEVELS.indexOf(a.level) ||
          (a.depositor_impact ?? 0) - (b.depositor_impact ?? 0),
      );
  }, [alerts]);

  const shown = event ? atLevel.filter((alert) => alert.event === event) : atLevel;
  const vault = target && !target.startsWith('user-') ? target : undefined;

  return (
    <>
      <header className="flex flex-wrap items-baseline gap-x-5.5 gap-y-2">
        <h1 className="m-0">Alerts</h1>
        <span className={cn('text-[0.85rem]', STATUS_CLASS[status])}>{STATUS_LABEL[status]}</span>
        {ticks[0] ? (
          <span className="text-[0.8rem] text-muted-foreground tabular-nums">
            block {blockNumber(ticks[0].block)}
          </span>
        ) : null}
      </header>

      <section aria-label="Act now" className="grid gap-3">
        <h2 className="m-0">
          Act now <span className="text-muted-foreground tabular-nums">{actNow.length || ''}</span>
        </h2>
        {actNow.length === 0 ? (
          <p className="text-muted-foreground" role="status">
            Nothing to act on.
          </p>
        ) : (
          <ul className="grid list-none gap-0">
            {actNow.map((alert, index) => (
              <ActionRow key={keyOf(alert, index)} alert={alert} vault={vault} />
            ))}
          </ul>
        )}
      </section>

      <section aria-label="All alerts" className="grid gap-4">
        <h2 className="m-0">All alerts</h2>
        <div className="flex flex-wrap items-end gap-x-9 gap-y-4">
          {ALERT_LEVELS.map((level) => (
            <div key={level}>
              <b className="text-2xl font-semibold tabular-nums">{counts.levels[level]}</b>
              <span className={cn('block text-[0.8rem] font-semibold', LEVEL_TEXT[level])}>
                {level}
              </span>
            </div>
          ))}
          <div className="ml-auto flex items-baseline gap-2 text-[0.85rem] text-muted-foreground">
            <Label htmlFor="min-level" className="font-normal">
              Minimum level
            </Label>
            <Select
              value={minLevel}
              onValueChange={(value) => onMinLevelChange(value as AlertLevel)}
            >
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
        </div>

        {counts.events.length > 0 ? (
          <div className="flex flex-wrap gap-2" role="group" aria-label="Event kind">
            {counts.events.map(([name, count]) => (
              <Button
                key={name}
                type="button"
                size="sm"
                variant={event === name ? 'secondary' : 'outline'}
                aria-pressed={event === name}
                onClick={() => setEvent((previous) => (previous === name ? null : name))}
              >
                <span className="mono">{name}</span>
                <span className="text-muted-foreground tabular-nums">{count}</span>
              </Button>
            ))}
          </div>
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
                  actions={<Actions alert={alert} vault={vault} />}
                />
              );
            })}
          </ul>
        )}
      </section>
    </>
  );
}

/** The engine shock that replays an alert, when the alert names a node the engine can take. */
function traceOf(alert: Alert): string | undefined {
  if (alert.event === 'FeedStale' && typeof alert.data.feed === 'string')
    return `${alert.data.feed}:frozen`;
  return undefined;
}

function Actions({ alert, vault }: { alert: Alert; vault?: string }) {
  if (!actionable(alert) && !traceOf(alert)) return null;
  const trace = traceOf(alert);
  return (
    <>
      {vault ? (
        <Button asChild size="sm" variant="outline">
          <Link to="/vault" search={(prev) => ({ ...prev, target: vault })}>
            Open vault
          </Link>
        </Button>
      ) : null}
      <Button asChild size="sm" variant="outline">
        <Link to="/scenario" search={(prev) => ({ ...prev, trace })}>
          Simulate
        </Link>
      </Button>
    </>
  );
}

const n = (value: unknown) => (typeof value === 'number' ? value : null);

function ActionRow({ alert, vault }: { alert: Alert; vault?: string }) {
  const d = alert.data;
  const verdict = typeof d.verdict === 'string' ? d.verdict : null;
  const figures =
    alert.event === 'OracleImpact'
      ? [
          { label: 'Vault loss', value: num(n(d.vault_loss), 0) },
          { label: 'Loss if you stay', value: num(n(d.loss_if_stay), 0) },
          { label: 'Leaves at par now', value: num(n(d.can_leave_now), 0) },
          { label: 'Loss if you exit first', value: num(n(d.loss_if_exit_first), 0) },
        ]
      : [];

  return (
    <li className="grid gap-2 border-b border-border/50 py-3.5">
      <div className="flex flex-wrap items-baseline gap-3.5 text-[0.8rem] text-muted-foreground">
        <span className={cn('font-bold', LEVEL_TEXT[alert.level])}>{alert.level}</span>
        <span className="mono">{alert.event}</span>
        <span>block {blockNumber(alert.block)}</span>
        <TxLink tx={alert.tx} />
        {verdict ? (
          <span className={cn('ml-auto font-semibold', VERDICT_TEXT[verdict])}>{verdict}</span>
        ) : alert.depositor_impact != null ? (
          <span
            className={`ml-auto font-semibold tabular-nums ${alert.depositor_impact < 0 ? 'text-critical' : 'text-ok'}`}
            title="Impact on your deposit, in the vault's asset"
          >
            <FormattedText>{signedUsd(alert.depositor_impact)}</FormattedText>
          </span>
        ) : null}
      </div>
      <div className="max-w-measure font-bold">{alert.title}</div>
      {figures.length > 0 ? (
        <dl className="flex flex-wrap gap-x-9 gap-y-2 text-[0.85rem] tabular-nums">
          {figures.map(({ label, value }) => (
            <div key={label}>
              <dt className="text-muted-foreground">{label}</dt>
              <dd className="m-0">
                <FormattedText>{value}</FormattedText>
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Actions alert={alert} vault={vault} />
      </div>
    </li>
  );
}
