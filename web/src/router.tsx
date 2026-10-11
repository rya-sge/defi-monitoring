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

/* Recharts and Cytoscape are both heavy, and no page needs both. Splitting per
   route keeps the first paint off the critical path of either library. */

const vaultRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: lazyRouteComponent(() => import('./routes/VaultPage'), 'VaultPage'),
});

const vaultRisksRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/vault-risks',
  component: lazyRouteComponent(() => import('./routes/VaultRisksPage'), 'VaultRisksPage'),
});

const marketRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/market/$marketId',
  component: lazyRouteComponent(() => import('./routes/MarketPage'), 'MarketPage'),
});

const graphRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/graph',
  component: lazyRouteComponent(() => import('./routes/GraphPage'), 'GraphPage'),
});

const watchRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/watch',
  component: lazyRouteComponent(() => import('./routes/WatchPage'), 'WatchPage'),
});

const impactRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/impact',
  component: lazyRouteComponent(() => import('./routes/ImpactPage'), 'ImpactPage'),
});

const incidentRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/incident',
  component: lazyRouteComponent(() => import('./routes/IncidentPage'), 'IncidentPage'),
});

const crossRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/cross',
  component: lazyRouteComponent(() => import('./routes/CrossPage'), 'CrossPage'),
});

const routeTree = rootRoute.addChildren([
  vaultRoute,
  vaultRisksRoute,
  marketRoute,
  graphRoute,
  crossRoute,
  impactRoute,
  incidentRoute,
  watchRoute,
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
