import { FormattedText } from './FormattedText';
import {
  Archive,
  BookOpen,
  ChevronRight,
  FlaskConical,
  Gauge,
  Network,
  Share2,
} from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';
import { Link, Outlet, useNavigate, useRouterState, useSearch } from '@tanstack/react-router';
import { useBooks, useGraph, useHealth, useSelectedTarget, useTargets } from '../api/hooks';
import { INCIDENT } from '../mocks/incident';
import { USE_MOCKS } from '../api/client';
import { detailValue, shortHash } from '../lib/format';
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
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarProvider,
  SidebarTrigger,
} from './ui/sidebar';

const NAV = [
  { to: '/', label: 'Book', icon: BookOpen, exact: true },
  { to: '/vault', label: 'Vault', icon: Gauge, exact: false },
  { to: '/scenario', label: 'Scenario lab', icon: FlaskConical, exact: false },
  { to: '/contagion', label: 'Contagion', icon: Share2, exact: false },
  { to: '/graph', label: 'Dependency graph', icon: Network, exact: false },
] as const;

const OLD_NAV = [
  { to: '/old/vault', label: 'Vault' },
  { to: '/old/vault-risks', label: 'Vault risks' },
  { to: '/old/graph', label: 'Dependency graph' },
  { to: '/old/cross', label: 'Cross-market' },
  { to: '/old/incident', label: 'Incident' },
  { to: '/old/impact', label: 'Impact' },
  { to: '/old/watch', label: 'Alerts' },
] as const;

// Pages with a selector of their own (a book, an episode) hide the top bar's vault selector.
const OWN_SELECTOR = ['/', '/track-record'];

export function AppShell() {
  const { data: health, error } = useHealth();
  const pathname = useRouterState({ select: (state) => state.location.pathname });

  return (
    <SidebarProvider>
      <Sidebar variant="inset">
        <SidebarHeader className="px-4 pt-3.5">
          <img src="/logo.png" alt="agencetousrisk" className="h-auto w-full invert" />
        </SidebarHeader>
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
                      <FormattedText>{label}</FormattedText>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
              <Collapsible asChild defaultOpen={pathname.startsWith('/old/')} className="group/old">
                <SidebarMenuItem>
                  <CollapsibleTrigger asChild>
                    <SidebarMenuButton className="h-10">
                      <Archive />
                      <span>Old</span>
                      <ChevronRight className="ml-auto transition-transform group-data-[state=open]/old:rotate-90" />
                    </SidebarMenuButton>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <SidebarMenuSub>
                      {OLD_NAV.map(({ to, label }) => (
                        <SidebarMenuSubItem key={to}>
                          <SidebarMenuSubButton asChild isActive={pathname === to}>
                            <Link to={to} search={(prev) => prev} className="no-underline">
                              {label}
                            </Link>
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                      ))}
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </SidebarMenuItem>
              </Collapsible>
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
      <SidebarInset className="m-1 h-[calc(100svh-8px)] min-w-0 overflow-hidden rounded-[6px] bg-[var(--surface)] shadow-none md:m-1 md:ml-0 md:rounded-[6px]">
        <div className="flex items-center gap-2 px-5.5 py-2 text-[0.85rem] text-muted-foreground">
          {/* Below md the sidebar is a sheet: this is the only way to open it there. */}
          <SidebarTrigger className="md:hidden" />
          {pathname === '/old/incident' ? (
            <IncidentVaultSelect />
          ) : OWN_SELECTOR.includes(pathname) ? null : (
            <TargetSelect />
          )}
        </div>
        <div className="min-h-0 flex-1 overflow-auto">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

function IncidentVaultSelect() {
  const { data: books } = useBooks();
  const { target } = useSearch({ strict: false });
  const navigate = useNavigate();
  const vaults = books?.find((book) => book.name === INCIDENT.example)?.vaults ?? [];
  const selected = vaults.some((vault) => vault.address.toLowerCase() === target?.toLowerCase())
    ? target!.toLowerCase()
    : INCIDENT.defaultVault;

  return (
    <>
      <span id="incident-vault-label">Vault</span>
      <Select
        value={selected}
        onValueChange={(value) =>
          void navigate({ to: '.', search: (prev) => ({ ...prev, target: value }) })
        }
      >
        <SelectTrigger aria-labelledby="incident-vault-label" size="sm" className="w-72">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {vaults.map((vault) => (
            <SelectItem key={vault.address} value={vault.address.toLowerCase()}>
              {vault.label ?? shortHash(vault.address)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </>
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
              <FormattedText>{label}</FormattedText>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </>
  );
}
