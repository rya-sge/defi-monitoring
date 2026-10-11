import type { StreamStatus } from '../../api/stream';
import type { Alert, AlertLevel } from '../../api/types';

export const LEVEL_TEXT: Record<AlertLevel, string> = {
  info: 'text-info',
  warn: 'text-warn',
  critical: 'text-critical',
};

export const STATUS_LABEL: Record<StreamStatus, string> = {
  connecting: 'connecting…',
  open: 'live',
  closed: 'stream ended',
  error: 'reconnecting…',
};

// "live" is the normal state; colour stays for what is wrong.
export const STATUS_CLASS: Record<StreamStatus, string> = {
  connecting: 'text-muted-foreground',
  open: 'text-foreground',
  closed: 'text-muted-foreground',
  error: 'text-warn',
};

/** Alerts carry no id; a state alert can repeat, so the index keeps rows apart. */
export const keyOf = (alert: Alert, index: number) => `${alert.block}-${alert.event}-${index}`;
