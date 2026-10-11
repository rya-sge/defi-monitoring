import {
  createRootRoute,
  createRoute,
  createRouter,
  lazyRouteComponent,
} from '@tanstack/react-router';
import { AppShell } from './components/AppShell';
import { Loading } from './components/States';

/** `?target=` selects one watch target (vault or "user-<address>"); absent means all. */
const rootRoute = createRootRoute({
  component: AppShell,
  validateSearch: (search: Record<string, unknown>): { target?: string } =>
    typeof search.target === 'string' && search.target ? { target: search.target } : {},
});

/* Recharts and React Flow are both heavy, and no page needs both. Splitting per
   route keeps the first paint off the critical path of either library. */

// Each new page answers one question of the manager, stated at the top of its file.
// The previous pages live under /old until the new ones replace them.

const bookRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: lazyRouteComponent(() => import('./routes/BookPage'), 'BookPage'),
});

const vaultRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/vault',
  component: lazyRouteComponent(() => import('./routes/VaultHubPage'), 'VaultHubPage'),
});

/** What other pages prefill the Scenario lab with. `shock` is an incident shock (`token=PST:0.3`,
 * `borrower=all:0.5:1`, `venue=Binance:0.5`), `trace` an engine shock (`<node>:reads-low:10%`);
 * `book` an example book name, `target` (root) the vault. */
export type ScenarioSearch = { book?: string; shock?: string; trace?: string };

const str = (v: unknown) => (typeof v === 'string' && v ? v : undefined);

const scenarioRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/scenario',
  validateSearch: (search: Record<string, unknown>): ScenarioSearch => ({
    book: str(search.book),
    shock: str(search.shock),
    trace: str(search.trace),
  }),
  component: lazyRouteComponent(() => import('./routes/ScenarioPage'), 'ScenarioPage'),
});

const positionRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/position',
  component: lazyRouteComponent(() => import('./routes/PositionPage'), 'PositionPage'),
});

const contagionRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/contagion',
  component: lazyRouteComponent(() => import('./routes/ContagionPage'), 'ContagionPage'),
});

const graphRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/graph',
  component: lazyRouteComponent(() => import('./routes/DependencyPage'), 'DependencyPage'),
});

const alertsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/alerts',
  component: lazyRouteComponent(() => import('./routes/AlertsPage'), 'AlertsPage'),
});

const trackRecordRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/track-record',
  component: lazyRouteComponent(() => import('./routes/TrackRecordPage'), 'TrackRecordPage'),
});

const marketRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/market/$marketId',
  component: lazyRouteComponent(() => import('./routes/old/MarketPage'), 'MarketPage'),
});

const oldVaultRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/old/vault',
  component: lazyRouteComponent(() => import('./routes/old/VaultPage'), 'VaultPage'),
});

const oldVaultRisksRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/old/vault-risks',
  component: lazyRouteComponent(() => import('./routes/old/VaultRisksPage'), 'VaultRisksPage'),
});

const oldGraphRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/old/graph',
  component: lazyRouteComponent(() => import('./routes/old/GraphPage'), 'GraphPage'),
});

const oldCrossRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/old/cross',
  component: lazyRouteComponent(() => import('./routes/old/CrossPage'), 'CrossPage'),
});

const oldIncidentRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/old/incident',
  component: lazyRouteComponent(() => import('./routes/old/IncidentPage'), 'IncidentPage'),
});

const oldImpactRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/old/impact',
  component: lazyRouteComponent(() => import('./routes/old/ImpactPage'), 'ImpactPage'),
});

const oldWatchRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/old/watch',
  component: lazyRouteComponent(() => import('./routes/old/WatchPage'), 'WatchPage'),
});

const routeTree = rootRoute.addChildren([
  bookRoute,
  vaultRoute,
  scenarioRoute,
  positionRoute,
  contagionRoute,
  graphRoute,
  alertsRoute,
  trackRecordRoute,
  marketRoute,
  oldVaultRoute,
  oldVaultRisksRoute,
  oldGraphRoute,
  oldCrossRoute,
  oldIncidentRoute,
  oldImpactRoute,
  oldWatchRoute,
]);

export const router = createRouter({
  routeTree,
  defaultPendingComponent: () => <Loading what="the page" />,
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
