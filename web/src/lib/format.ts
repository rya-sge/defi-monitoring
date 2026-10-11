const EM_DASH = '—';

export function usd(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return EM_DASH;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

/** Signed, for a depositor impact: a loss keeps its minus sign. */
export function signedUsd(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return EM_DASH;
  const formatted = usd(Math.abs(value), digits);
  return value < 0 ? `-${formatted}` : `+${formatted}`;
}

export function compactUsd(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return EM_DASH;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
}

export function percent(fraction: number | null | undefined): string {
  if (fraction == null || !Number.isFinite(fraction)) return EM_DASH;
  return `${(fraction * 100).toFixed(0)}%`;
}

export function num(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) return EM_DASH;
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

export function compactNum(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return EM_DASH;
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 2 }).format(
    value,
  );
}

export function days(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return EM_DASH;
  return `${value.toFixed(1)} d`;
}

export function shortHash(hash: string | null | undefined, lead = 5, tail = 3): string {
  if (!hash) return EM_DASH;
  if (hash.length <= lead + tail + 1) return hash;
  return `${hash.slice(0, lead)}...${hash.slice(-tail)}`;
}

export const isAddress = (value: string): boolean => /^0x[0-9a-fA-F]{40}$/.test(value);
export const isTxHash = (value: string): boolean => /^0x[0-9a-fA-F]{64}$/.test(value);

export function etherscanUrl(value: string): string | null {
  if (isAddress(value)) return `https://etherscan.io/address/${value}`;
  if (isTxHash(value)) return `https://etherscan.io/tx/${value}`;
  return null;
}

export function blockNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

/** Renders an unknown `details` value as a single readable line. */
export function detailValue(value: unknown): string {
  if (value == null) return EM_DASH;
  if (typeof value === 'string')
    return isAddress(value) || isTxHash(value) ? shortHash(value) : value;
  if (typeof value === 'number') return num(value, Number.isInteger(value) ? 0 : 2);
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  return JSON.stringify(value);
}

/** `share_of_market` -> `share of market` */
export function humanKey(key: string): string {
  return key.replace(/_/g, ' ');
}
