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
        {/* Provenance, not ornament: where the numbers come from and how old
            they are. Only the failure spends colour. */}
        <div className="topbar-right">
          {USE_MOCKS ? <span>mock fixtures</span> : null}
          {health ? (
            <span title={`Backend mode: ${health.mode}`}>
              {health.mode} · data as of {health.data_as_of}
            </span>
          ) : error ? (
            <span style={{ color: 'var(--critical)' }}>backend unreachable</span>
          ) : null}
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
