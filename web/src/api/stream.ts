import { api, ApiError, USE_MOCKS } from './client';
import type { Alert, WatchQuery, WatchTick } from './types';
import { MOCK_ALERTS, MOCK_TICKS } from '../mocks/alerts';

export type StreamStatus = 'connecting' | 'open' | 'closed' | 'error';

export type StreamHandlers = {
  onAlert: (alert: Alert) => void;
  onTick: (tick: WatchTick) => void;
  onStatus: (status: StreamStatus) => void;
};

const MOCK_INTERVAL_MS = 1500;
const POLL_INTERVAL_MS = 3000;

/**
 * Follows the watcher, or replays the fixtures when mocking. Returns the unsubscribe function.
 *
 * The real transport is a poll of `GET /api/alerts` with a block cursor, not a socket: the
 * watcher is a separate process appending to `out/watch-*.jsonl`, and the API reads it. The
 * cursor is a block number — the same unit the watcher resumes from — so moving to a push
 * transport later changes this function and nothing above it.
 */
export function subscribeWatch(query: WatchQuery, handlers: StreamHandlers): () => void {
  if (USE_MOCKS) return replayMocks(handlers);

  let cursor: number | undefined;
  let stopped = false;
  let timer: ReturnType<typeof setTimeout> | undefined;

  const poll = async (): Promise<void> => {
    try {
      const page = await api.alerts({ ...query, since: cursor });
      if (stopped) return;
      const first = cursor === undefined;
      cursor = page.cursor;
      handlers.onStatus('open');
      for (const alert of page.alerts) handlers.onAlert(alert);
      // No per-block feed to report: say where the cursor stands, once, and after a catch-up.
      if (first || page.alerts.length > 0) {
        handlers.onTick({ block: page.cursor, message: `${page.target} · read up to block` });
      }
    } catch (error) {
      if (stopped) return;
      // 404 means the watcher has written nothing yet — that is a closed stream, not a failure.
      handlers.onStatus(error instanceof ApiError && error.status === 404 ? 'closed' : 'error');
    } finally {
      if (!stopped) timer = setTimeout(() => void poll(), POLL_INTERVAL_MS);
    }
  };

  handlers.onStatus('connecting');
  void poll();

  return () => {
    stopped = true;
    if (timer !== undefined) clearTimeout(timer);
  };
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
