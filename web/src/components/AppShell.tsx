import { Link, Outlet } from '@tanstack/react-router';
import { useHealth } from '../api/hooks';
import { USE_MOCKS } from '../api/client';

export function AppShell() {
  const { data: health, error } = useHealth();

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          riskdep<span>DeFi position risk · Morpho</span>
        </div>
        <nav className="nav" aria-label="Main">
          <Link to="/" activeProps={{ className: 'active' }} activeOptions={{ exact: true }}>
            Position
          </Link>
          <Link to="/graph" activeProps={{ className: 'active' }}>
            Dependency graph
          </Link>
          <Link to="/watch" activeProps={{ className: 'active' }}>
            Alerts
          </Link>
        </nav>
        <div className="topbar-right">
          {USE_MOCKS ? <span className="chip">mock fixtures</span> : null}
          {health ? (
            <span className="chip" title={`Backend mode: ${health.mode}`}>
              <span className="dot" style={{ color: 'var(--ok)' }} />
              {health.mode} · data as of {health.data_as_of}
            </span>
          ) : error ? (
            <span className="chip" style={{ color: 'var(--critical)' }}>
              <span className="dot" />
              backend unreachable
            </span>
          ) : null}
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
