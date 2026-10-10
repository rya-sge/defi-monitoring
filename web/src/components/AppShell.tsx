import { Link, Outlet } from '@tanstack/react-router';
import { useHealth } from '../api/hooks';
import { USE_MOCKS } from '../api/client';

const NAV_BASE = 'text-[0.92rem] no-underline hover:underline';
const NAV_ACTIVE = { className: 'font-bold text-foreground' };
const NAV_INACTIVE = { className: 'text-muted-foreground hover:text-foreground' };

export function AppShell() {
  const { data: health, error } = useHealth();

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 flex flex-wrap items-baseline gap-5.5 border-b border-border bg-background px-5.5 py-3.5">
        <div className="font-bold tracking-[-0.01em]">
          riskdep
          <span className="ml-2 text-[0.82rem] font-normal text-muted-foreground">
            DeFi position risk · Morpho
          </span>
        </div>
        <nav className="flex gap-3.5" aria-label="Main">
          <Link
            to="/"
            className={NAV_BASE}
            activeProps={NAV_ACTIVE}
            inactiveProps={NAV_INACTIVE}
            activeOptions={{ exact: true }}
          >
            Position
          </Link>
          <Link
            to="/graph"
            className={NAV_BASE}
            activeProps={NAV_ACTIVE}
            inactiveProps={NAV_INACTIVE}
          >
            Dependency graph
          </Link>
          <Link
            to="/watch"
            className={NAV_BASE}
            activeProps={NAV_ACTIVE}
            inactiveProps={NAV_INACTIVE}
          >
            Alerts
          </Link>
        </nav>
        {/* Provenance, not ornament: where the numbers come from and how old
            they are. Only the failure spends colour. */}
        <div className="ml-auto flex items-baseline gap-5.5 text-[0.8rem] text-muted-foreground">
          {USE_MOCKS ? <span>mock fixtures</span> : null}
          {health ? (
            <span title={`Backend mode: ${health.mode}`}>
              {health.mode} · data as of {health.data_as_of}
            </span>
          ) : error ? (
            <span className="text-critical">backend unreachable</span>
          ) : null}
        </div>
      </header>
      <main className="min-h-0 flex-1">
        <Outlet />
      </main>
    </div>
  );
}
