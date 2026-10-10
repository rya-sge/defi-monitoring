import type { ReactNode } from 'react';

export function Loading({ what }: { what: string }) {
  return (
    <p className="state" role="status">
      Loading {what}…
    </p>
  );
}

export function ErrorState({ what, error }: { what: string; error: unknown }) {
  const message = error instanceof Error ? error.message : String(error);
  return (
    <p className="state state-error" role="alert">
      Could not load {what}. {message}
    </p>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="state">{children}</p>;
}
