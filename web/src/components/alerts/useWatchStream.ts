import { useEffect, useState } from 'react';
import { subscribeWatch } from '../../api/stream';
import type { StreamStatus } from '../../api/stream';
import type { Alert, AlertLevel, WatchTick } from '../../api/types';

/**
 * The alerts of one watch target, newest first. `target` and `minLevel` are server-side filters:
 * the caller remounts on a change of either (`key`) instead of resetting state here.
 */
export function useWatchStream(target: string | undefined, minLevel: AlertLevel) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [ticks, setTicks] = useState<WatchTick[]>([]);
  const [status, setStatus] = useState<StreamStatus>('connecting');

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

  return { alerts, ticks, status };
}
