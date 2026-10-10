import { Bell, Gauge, Network, Waypoints, Zap } from 'lucide-react';
import { Link, Outlet, useNavigate, useRouterState } from '@tanstack/react-router';
import { useGraph, useHealth, useSelectedTarget, useTargets } from '../api/hooks';
import { USE_MOCKS } from '../api/client';
import { detailValue } from '../lib/format';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from './ui/sidebar';

const NAV = [
  { to: '/', label: 'Vault', icon: Gauge, exact: true },
  { to: '/graph', label: 'Dependency graph', icon: Network, exact: false },
  { to: '/cross', label: 'Cross-market', icon: Waypoints, exact: false },
  { to: '/impact', label: 'Impact', icon: Zap, exact: false },
  { to: '/watch', label: 'Alerts', icon: Bell, exact: false },
] as const;

export function AppShell() {
  const { data: health, error } = useHealth();
  const pathname = useRouterState({ select: (state) => state.location.pathname });

  return (
    <SidebarProvider>
      <Sidebar>
        <SidebarHeader className="px-4 pt-3.5 font-bold tracking-[-0.01em]">riskdep</SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarMenu aria-label="Main">
              {NAV.map(({ to, label, icon: Icon, exact }) => (
                <SidebarMenuItem key={to}>
                  <SidebarMenuButton
                    asChild
                    className="h-10 no-underline"
                    isActive={exact ? pathname === to : pathname.startsWith(to)}
                  >
                    <Link to={to} search={(prev) => prev}>
                      <Icon />
                      {label}
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
        </SidebarContent>
        {/* Provenance, not ornament: where the numbers come from and how old
            they are. Only the failure spends colour. */}
        <SidebarFooter className="px-4 pb-3.5 text-[0.75rem] text-muted-foreground">
          {USE_MOCKS ? <span>mock fixtures</span> : null}
          {health ? (
            <span title={`Backend mode: ${health.mode}`}>
              {health.mode} · data as of {health.data_as_of}
            </span>
          ) : error ? (
            <span className="text-critical">backend unreachable</span>
          ) : null}
        </SidebarFooter>
      </Sidebar>
      <SidebarInset className="h-svh min-w-0">
        <div className="flex items-center gap-2 border-b px-5.5 py-2 text-[0.85rem] text-muted-foreground">
          {/* Below md the sidebar is a sheet: this is the only way to open it there. */}
          <SidebarTrigger className="md:hidden" />
          <TargetSelect />
        </div>
        <div className="min-h-0 flex-1 overflow-auto">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

function TargetSelect() {
  const { target } = useSelectedTarget();
  const navigate = useNavigate();
  const { data: targets } = useTargets();
  const { data: graph } = useGraph();
  // Every vault of the graph (the last one written, or the fixture) and every watched address,
  // the watched targets first: they are the ones with alerts.
  const watched = new Set(targets?.map((t) => t.target));
  const options = (graph?.nodes ?? [])
    .filter(
      (n) => n.id.startsWith('user:') || detailValue(n.details.actor_type).startsWith('Vault'),
    )
    .map((n) => ({ value: n.id.replace(/^user:/, 'user-'), label: n.label }))
    .sort(
      (a, b) =>
        Number(watched.has(b.value)) - Number(watched.has(a.value)) ||
        a.label.localeCompare(b.label),
    );

  return (
    <>
      <span id="target-label">Vault</span>
      <Select
        value={target ?? ''}
        onValueChange={(value) =>
          void navigate({
            to: '.',
            search: (prev) => ({ ...prev, target: value }),
          })
        }
      >
        <SelectTrigger aria-labelledby="target-label" size="sm" className="w-72">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map(({ value, label }) => (
            <SelectItem key={value} value={value}>
              {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </>
  );
}
