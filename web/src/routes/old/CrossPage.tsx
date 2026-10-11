import { useMemo, useState } from 'react';
import { Handle, MarkerType, Position, ReactFlow } from '@xyflow/react';
import type { Node, NodeProps } from '@xyflow/react';
import '@xyflow/react/dist/base.css';
import { useGraph, useSelectedTarget } from '../../api/hooks';
import { GRAPH_NODE_KINDS } from '../../api/types';
import type { GraphResponse } from '../../api/types';
import { GraphCanvas } from '../../components/GraphCanvas';
import type { GraphSelection } from '../../components/GraphCanvas';
import { RiskEdge, RiskNode } from '../../components/GraphElements';
import type { RiskEdgeType, RiskNodeType } from '../../components/GraphElements';
import { ErrorState, Loading } from '../../components/States';
import { compactNum } from '../../lib/format';
import { contract, crossView, ego, focusOn, pairEdges, totalExposure } from '../../lib/cross';
import type { CrossView } from '../../lib/cross';
import { edgeWidth, layoutGraph, targetNodeId } from '../../lib/graph';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

/**
 * Cross-market dependencies: what several vaults depend on at once. Four drawings of the same
 * computation (`lib/cross.ts`), side by side to pick one. Exposure only, from the graph.
 */

const ALL_KINDS = new Set(GRAPH_NODE_KINDS);
const SHARED_RING = 'var(--info)';
const shareLabel = (count: number) => `×${count} vaults`;
/** The focus vault's ring: ink, not a severity colour. */
const FOCUS_RING = 'var(--fg)';

export function CrossPage() {
  const { data, isPending, error } = useGraph();
  const { target } = useSelectedTarget();
  const [withLoanTokens, setWithLoanTokens] = useState(false);
  const focus = target ? targetNodeId(target) : '';
  const all = useMemo(() => data && crossView(data, withLoanTokens), [data, withLoanTokens]);
  const view = useMemo(() => all && focusOn(all, focus), [all, focus]);

  if (isPending) return <Loading what="the dependency graph" />;
  if (error) return <ErrorState what="the dependency graph" error={error} />;
  if (!all || !view) return null;

  const vault = all.vaults.find((v) => v.id === focus);
  if (!vault) {
    return (
      <p className="px-5.5 py-14 text-muted-foreground">
        Pick a vault in the selector above: the page shows what that vault shares with others.
      </p>
    );
  }

  const key = `${focus}-${withLoanTokens}`;
  return (
    <div className="flex h-full flex-col px-5.5 pt-5.5">
      <header className="mb-3.5 flex flex-wrap items-baseline gap-x-5.5">
        <h1>Cross-market</h1>
        <p className="text-muted-foreground tabular-nums">
          {vault.label} shares {view.shared.length} dependencies with {view.vaults.length - 1} other
          vaults
        </p>
        <Label className="ml-auto flex items-center gap-2 font-normal">
          <Checkbox
            checked={withLoanTokens}
            onCheckedChange={(checked) => setWithLoanTokens(checked === true)}
          />
          include loan tokens
        </Label>
      </header>
      <Tabs defaultValue="bipartite" className="min-h-0 flex-1">
        <TabsList>
          <TabsTrigger value="bipartite">Shared below</TabsTrigger>
          <TabsTrigger value="network">Vault network</TabsTrigger>
          <TabsTrigger value="boxes">Vaults as boxes</TabsTrigger>
          <TabsTrigger value="heat">Full graph, heat</TabsTrigger>
        </TabsList>
        <TabsContent value="bipartite" className="relative min-h-[60vh]">
          <Bipartite key={key} view={view} focus={focus} graph={data} />
        </TabsContent>
        <TabsContent value="network" className="relative min-h-[60vh]">
          <Network key={key} view={view} focus={focus} />
        </TabsContent>
        <TabsContent value="boxes" className="relative min-h-[60vh]">
          <Boxes key={key} view={view} focus={focus} graph={data} />
        </TabsContent>
        <TabsContent value="heat" className="relative min-h-[60vh]">
          <Heat key={key} view={view} graph={data} focus={focus} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

/** What a selected node shares: for a shared node, its vaults; for a vault, its shared nodes. */
function SharedPanel({ view, id }: { view: CrossView; id: string | null }) {
  if (!id) return null;
  const label = (vid: string) => view.vaults.find((v) => v.id === vid)?.label ?? vid;
  const shared = view.shared.find((s) => s.node.id === id);
  const vault = view.vaults.find((v) => v.id === id);
  const rows = shared
    ? [...shared.exposure].map(([vid, amount]) => [label(vid), compactNum(amount)])
    : vault
      ? view.shared
          .filter((s) => s.exposure.has(id))
          .map((s) => [
            s.node.label,
            `${compactNum(s.exposure.get(id))} · ${shareLabel(s.exposure.size)}`,
          ])
      : [];
  return (
    <aside className="absolute top-3.5 right-3.5 max-h-[calc(100%-28px)] w-[340px] overflow-auto rounded-lg border bg-background p-5.5 shadow-sm">
      <p className="mb-1 font-semibold">{shared?.node.label ?? vault?.label ?? id}</p>
      <p className="mb-3.5 text-muted-foreground">
        {shared
          ? `${shareLabel(shared.exposure.size)} depend on it · ${compactNum(totalExposure(shared))} supplied upstream`
          : vault
            ? `${rows.length} shared dependencies · ${view.privateNodes.get(id)?.length ?? 0} of its own`
            : 'not shared'}
      </p>
      <ul className="grid gap-1 text-[0.86rem] tabular-nums">
        {rows.map(([name, value]) => (
          <li key={name} className="flex justify-between gap-3.5">
            <span className="truncate">{name}</span>
            <span className="shrink-0 text-muted-foreground">{value}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}

function useSelectedId() {
  const [selection, setSelection] = useState<GraphSelection>(null);
  const id = selection?.type === 'node' ? selection.node.id : null;
  return { selection, setSelection, id };
}

/* -------------------------------------------- 1. vaults on top, shared below */

type FocusProps = { view: CrossView; focus: string };

/**
 * The vault and the vaults it shares with on top, the shared nodes below in their own
 * hierarchy (market → oracle → feed), paths through unshared nodes shortened to one edge.
 */
function Bipartite({ view, focus, graph }: FocusProps & { graph: GraphResponse }) {
  const { selection, setSelection, id } = useSelectedId();
  const { nodes, edges, overlay } = useMemo(
    () => ({
      nodes: [...view.vaults, ...view.shared.map((s) => s.node)],
      edges: contract(graph, view),
      overlay: {
        ...Object.fromEntries(
          view.shared.map((s) => [s.node.id, { amount: [shareLabel(s.exposure.size)] }]),
        ),
        [focus]: { ring: FOCUS_RING, amount: [] },
      },
    }),
    [view, focus, graph],
  );
  return (
    <>
      <GraphCanvas
        nodes={nodes}
        edges={edges}
        visibleKinds={ALL_KINDS}
        search=""
        selection={selection}
        onSelect={setSelection}
        overlay={overlay}
      />
      <SharedPanel view={view} id={id} />
    </>
  );
}

/* --------------------------------------------------- 2. vault ↔ vault network */

/** The vault in the middle, the vaults it shares something with around it. */
function Network({ view, focus }: FocusProps) {
  const { selection, setSelection, id } = useSelectedId();
  const { edges, positions } = useMemo(
    () => ({
      edges: pairEdges(view),
      positions: ego(
        focus,
        view.vaults.filter((v) => v.id !== focus).map((v) => v.id),
      ),
    }),
    [view, focus],
  );
  return (
    <>
      <GraphCanvas
        nodes={view.vaults}
        edges={edges}
        visibleKinds={ALL_KINDS}
        search=""
        selection={selection}
        onSelect={setSelection}
        positions={positions}
        undirected
      />
      <SharedPanel view={view} id={id} />
    </>
  );
}

/* ------------------------------------------------------- 3. vaults as boxes */

type BoxData = { title: string; own: string[]; focus: boolean };
type BoxNodeType = Node<BoxData, 'box'>;

const BOX = { width: 220, header: 34, row: 18, rows: 8, gap: 40 };

/** A vault and what only it depends on: inside the box is its own, outside is shared. */
function VaultBox({ data }: NodeProps<BoxNodeType>) {
  const shown = data.own.slice(0, BOX.rows);
  return (
    <div
      className={`size-full rounded-lg border bg-muted px-2 py-1.5 ${data.focus ? 'border-2 border-foreground' : ''}`}
    >
      <div className="mb-1 truncate text-[0.8rem] font-semibold">{data.title}</div>
      <ul className="text-[0.72rem] leading-[18px] text-muted-foreground">
        {shown.map((name, i) => (
          <li key={`${name}-${i}`} className="truncate">
            {name}
          </li>
        ))}
        {data.own.length > shown.length ? <li>+{data.own.length - shown.length} more</li> : null}
        {data.own.length === 0 ? <li>nothing of its own</li> : null}
      </ul>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!opacity-0"
        isConnectable={false}
      />
    </div>
  );
}

const boxTypes = { box: VaultBox, risk: RiskNode };
const boxEdgeTypes = { risk: RiskEdge };

function Boxes({ view, focus, graph }: FocusProps & { graph: GraphResponse }) {
  const [selected, setSelected] = useState<string | null>(null);
  const { nodes, edges } = useMemo(() => {
    const height = (n: number) => BOX.header + BOX.row * (Math.min(n, BOX.rows) + 1);
    const boxH = Math.max(
      ...view.vaults.map((v) => height(view.privateNodes.get(v.id)?.length ?? 0)),
    );
    const xOf = new Map(view.vaults.map((v, i) => [v.id, i * (BOX.width + BOX.gap)]));
    const boxes: BoxNodeType[] = view.vaults.map((v) => ({
      id: v.id,
      type: 'box',
      position: { x: xOf.get(v.id)!, y: 0 },
      style: { width: BOX.width, height: height(view.privateNodes.get(v.id)?.length ?? 0) },
      data: {
        title: v.label,
        own: (view.privateNodes.get(v.id) ?? []).map((n) => n.label),
        focus: v.id === focus,
      },
    }));
    // The shared nodes keep their own hierarchy (market → oracle → feed), laid out below the
    // boxes; the vaults' edges reach the first shared node on each of their paths.
    const edgesAll = contract(graph, view);
    const vaultIds = new Set(view.vaults.map((v) => v.id));
    const sharedNodes = view.shared.map((s) => s.node);
    const inner = edgesAll.filter((e) => !vaultIds.has(e.source));
    const layout = layoutGraph(sharedNodes, inner);
    const minX = Math.min(...[...layout.values()].map((p) => p.x));
    const shared: RiskNodeType[] = view.shared.map((s) => {
      const p = layout.get(s.node.id)!;
      return {
        id: s.node.id,
        type: 'risk',
        position: { x: p.x - minX, y: p.y + boxH + 160 },
        data: { node: s.node, amount: [shareLabel(s.exposure.size)] },
      };
    });
    const links: RiskEdgeType[] = edgesAll.map((edge) => ({
      id: `${edge.source}-${edge.target}`,
      type: 'risk' as const,
      source: edge.source,
      target: edge.target,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: 'var(--edge)',
        width: 14,
        height: 14,
        markerUnits: 'userSpaceOnUse' as const,
      },
      data: {
        edge,
        label: edge.amount ? compactNum(edge.amount) : '',
        width: edgeWidth(edge.amount),
        colour: edge.amount != null ? 'var(--edge)' : 'var(--line)',
      },
    }));
    return {
      nodes: [...boxes, ...shared] as (BoxNodeType | RiskNodeType)[],
      edges: links,
    };
  }, [view, focus, graph]);

  const lit = selected
    ? new Set([
        selected,
        ...edges
          .filter((e) => e.source === selected || e.target === selected)
          .flatMap((e) => [e.source, e.target]),
      ])
    : null;

  return (
    <>
      <ReactFlow
        className="absolute inset-0"
        nodes={nodes.map((n) => ({
          ...n,
          style: { ...n.style, opacity: lit && !lit.has(n.id) ? 0.15 : 1 },
        }))}
        edges={edges.map((e) => ({
          ...e,
          style: {
            opacity:
              lit &&
              !(
                lit.has(e.source) &&
                lit.has(e.target) &&
                (e.source === selected || e.target === selected)
              )
                ? 0.08
                : 0.85,
          },
        }))}
        nodeTypes={boxTypes}
        edgeTypes={boxEdgeTypes}
        nodesConnectable={false}
        nodesDraggable={false}
        minZoom={0.05}
        fitView
        proOptions={{ hideAttribution: true }}
        onNodeClick={(_, node) => setSelected(node.id)}
        onPaneClick={() => setSelected(null)}
      />
      <SharedPanel view={view} id={selected} />
    </>
  );
}

/* ------------------------------------------------- 4. full graph with heat */

function Heat({ view, graph, focus: vault }: FocusProps & { graph: GraphResponse }) {
  const { selection, setSelection, id } = useSelectedId();
  const [sharedOnly, setSharedOnly] = useState(true);
  const { overlay, focus } = useMemo(() => {
    const keep = new Set([...view.vaults.map((v) => v.id), ...view.shared.map((s) => s.node.id)]);
    return {
      overlay: Object.fromEntries([
        ...view.shared.map((s): [string, { ring: string; amount: string[] }] => [
          s.node.id,
          { ring: SHARED_RING, amount: [shareLabel(s.exposure.size)] },
        ]),
        [vault, { ring: FOCUS_RING, amount: [] }],
      ]),
      focus: {
        nodes: keep,
        edges: new Set(
          graph.edges.flatMap((e, i) =>
            keep.has(e.source) && keep.has(e.target) ? [`e${i}`] : [],
          ),
        ),
      },
    };
  }, [view, graph, vault]);
  return (
    <>
      <GraphCanvas
        nodes={graph.nodes}
        edges={graph.edges}
        visibleKinds={ALL_KINDS}
        search=""
        selection={selection}
        onSelect={setSelection}
        overlay={overlay}
        focus={sharedOnly ? focus : null}
      />
      <Label className="absolute top-3.5 left-3.5 flex items-center gap-2 rounded-md bg-background/80 px-2 py-1 font-normal">
        <Checkbox checked={sharedOnly} onCheckedChange={(c) => setSharedOnly(c === true)} />
        fade what is not shared
      </Label>
      <SharedPanel view={view} id={id} />
    </>
  );
}
