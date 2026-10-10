import {
  createRootRoute,
  createRoute,
  createRouter,
  lazyRouteComponent,
} from '@tanstack/react-router';
import { AppShell } from './components/AppShell';
import { Loading } from './components/States';

const rootRoute = createRootRoute({ component: AppShell });

/* Recharts and Cytoscape are both heavy, and no page needs both. Splitting per
   route keeps the first paint off the critical path of either library. */

const positionRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: lazyRouteComponent(() => import('./routes/PositionPage'), 'PositionPage'),
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

const routeTree = rootRoute.addChildren([positionRoute, graphRoute, watchRoute]);

export const router = createRouter({
  routeTree,
  defaultPendingComponent: () => <Loading what="the page" />,
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
