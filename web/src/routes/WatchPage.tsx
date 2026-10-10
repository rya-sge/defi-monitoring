import { useEffect, useMemo, useState } from 'react';
import { subscribeWatch } from '../api/stream';
import type { StreamStatus } from '../api/stream';
import { USE_MOCKS } from '../api/client';
import { ALERT_LEVELS } from '../api/types';
import type { Alert, AlertLevel, WatchTick } from '../api/types';
import { blockNumber, etherscanUrl, shortHash, signedUsd } from '../lib/format';
import { DetailsTable } from '../components/DetailsTable';

const STATUS_LABEL: Record<StreamStatus, string> = {
  connecting: 'connecting…',
  open: 'live',
  closed: 'stream ended',
  error: 'reconnecting…',
};

const STATUS_COLOR: Record<StreamStatus, string> = {
  connecting: 'var(--muted)',
  open: 'var(--fg)',
  closed: 'var(--muted)',
  error: 'var(--warn)',
};

export function WatchPage() {
  const [minLevel, setMinLevel] = useState<AlertLevel>('info');

  return (
    <div className="page">
      <h1>Alerts</h1>
      <p className="lede">
        Server-Sent Events from <code className="mono">/api/watch/stream</code>, newest first.{' '}
        {USE_MOCKS
          ? 'Mock mode: a fixed set of alerts is replayed every 1.5 s, then the stream ends.'
          : 'Polling runs two blocks behind the head; deeper reorgs are not handled.'}
      </p>
      {/* `min_level` is a server-side filter, so changing it must restart the
          stream from scratch. Keying on it remounts the subscriber, which drops
          the collected alerts without resetting state from inside an effect. */}
      <WatchStream key={minLevel} minLevel={minLevel} onMinLevelChange={setMinLevel} />
    </div>
  );
}

function WatchStream({
  minLevel,
  onMinLevelChange,
}: {
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
        { min_level: minLevel },
        {
          onAlert: (alert) => setAlerts((previous) => [alert, ...previous]),
          onTick: (tick) => setTicks((previous) => [tick, ...previous].slice(0, 3)),
          onStatus: setStatus,
        },
      ),
    [minLevel],
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
      <div className="level-counts">
        {ALERT_LEVELS.map((level) => (
          <div className="level-count" key={level} data-level={level}>
            <b>{counts[level]}</b>
            <span>{level}</span>
          </div>
        ))}
      </div>

      <div className="watch-toolbar">
        <span className="watch-status" style={{ color: STATUS_COLOR[status] }}>
          {STATUS_LABEL[status]}
        </span>
        <label htmlFor="min-level">Minimum level</label>
        <select
          id="min-level"
          value={minLevel}
          onChange={(event) => onMinLevelChange(event.target.value as AlertLevel)}
        >
          {ALERT_LEVELS.map((level) => (
            <option key={level} value={level}>
              {level}
            </option>
          ))}
        </select>
      </div>

      {ticks.length > 0 ? (
        <p className="ticks">
          {ticks.map((tick) => (
            <span key={`${tick.block}-${tick.message}`} style={{ display: 'block' }}>
              block {blockNumber(tick.block)} · {tick.message}
            </span>
          ))}
        </p>
      ) : null}

      {shown.length === 0 ? (
        <p className="state" role="status" aria-live="polite">
          {status === 'open' || status === 'connecting'
            ? 'Waiting for the first alert…'
            : 'No alert at this level.'}
        </p>
      ) : (
        <ul className="alert-list" aria-live="polite">
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
    <li className="alert" data-level={alert.level}>
      <div className="alert-head">
        <span className="alert-level">{alert.level}</span>
        <span>block {blockNumber(alert.block)}</span>
        <span className="mono">
          {txUrl && alert.tx ? (
            <a href={txUrl} target="_blank" rel="noreferrer noopener">
              {shortHash(alert.tx)}
            </a>
          ) : (
            <span className="muted">no tx</span>
          )}
        </span>
        <span className="mono">{alert.event}</span>
        {alert.depositor_impact != null ? (
          <span
            className="alert-impact"
            data-sign={alert.depositor_impact < 0 ? 'loss' : 'gain'}
            title="Impact on your deposit, in the vault's asset"
          >
            {signedUsd(alert.depositor_impact)}
          </span>
        ) : null}
      </div>
      <div className="alert-title">{alert.title}</div>
      <div className="alert-detail">{alert.detail}</div>
      {hasData ? (
        <div>
          <button type="button" onClick={onToggle} aria-expanded={expanded}>
            {expanded ? 'Hide data' : 'Show data'}
          </button>
          {expanded ? (
            <div className="alert-data">
              <DetailsTable details={alert.data} />
            </div>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}
