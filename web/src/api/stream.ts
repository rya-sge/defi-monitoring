import { USE_MOCKS, watchStreamUrl } from './client';
import type { Alert, WatchQuery, WatchTick } from './types';
import { MOCK_ALERTS, MOCK_TICKS } from '../mocks/alerts';

export type StreamStatus = 'connecting' | 'open' | 'closed' | 'error';

export type StreamHandlers = {
  onAlert: (alert: Alert) => void;
  onTick: (tick: WatchTick) => void;
  onStatus: (status: StreamStatus) => void;
};

const MOCK_INTERVAL_MS = 1500;

/**
 * Subscribes to `/api/watch/stream`, or replays the fixtures when mocking.
 * Returns the unsubscribe function.
 */
export function subscribeWatch(query: WatchQuery, handlers: StreamHandlers): () => void {
  if (USE_MOCKS) return replayMocks(handlers);

  const source = new EventSource(
    watchStreamUrl({ vault: query.vault, user: query.user, min_level: query.min_level }),
  );

  source.addEventListener('open', () => handlers.onStatus('open'));
  source.addEventListener('alert', (event) => {
    const parsed = parse<Alert>(event);
    if (parsed) handlers.onAlert(parsed);
  });
  source.addEventListener('tick', (event) => {
    const parsed = parse<WatchTick>(event);
    if (parsed) handlers.onTick(parsed);
  });
  // The browser reconnects by itself; surface the gap meanwhile.
  source.addEventListener('error', () => {
    handlers.onStatus(source.readyState === EventSource.CLOSED ? 'closed' : 'error');
  });

  return () => {
    source.close();
  };
}

function parse<T>(event: Event): T | null {
  const data: unknown = (event as MessageEvent<string>).data;
  if (typeof data !== 'string') return null;
  try {
    return JSON.parse(data) as T;
  } catch {
    return null;
  }
}

function replayMocks(handlers: StreamHandlers): () => void {
  // Deferred: reporting a status synchronously inside the subscriber's effect
  // would cascade a second render before the first one has painted.
  const opening = setTimeout(() => handlers.onStatus('open'), 0);
  let alertIndex = 0;
  let tickIndex = 0;

  const timer = setInterval(() => {
    if (alertIndex >= MOCK_ALERTS.length) {
      clearInterval(timer);
      handlers.onStatus('closed');
      return;
    }
    const alert = MOCK_ALERTS[alertIndex++];
    const tick = MOCK_TICKS[tickIndex];
    if (tick && tick.block <= alert.block) {
      tickIndex += 1;
      handlers.onTick(tick);
    }
    handlers.onAlert(alert);
  }, MOCK_INTERVAL_MS);

  return () => {
    clearTimeout(opening);
    clearInterval(timer);
  };
}
