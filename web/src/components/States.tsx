import type { ReactNode } from 'react';

const STATE = 'py-14 text-muted-foreground';

export function Loading({ what }: { what: string }) {
  return (
    <p className={STATE} role="status">
      Loading {what}…
    </p>
  );
}

export function ErrorState({ what, error }: { what: string; error: unknown }) {
  const message = error instanceof Error ? error.message : String(error);
  return (
    <p className="py-14 text-critical" role="alert">
      Could not load {what}. {message}
    </p>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className={STATE}>{children}</p>;
}
