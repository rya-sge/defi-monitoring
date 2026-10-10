import type { GraphEdge, GraphNode, GraphResponse } from '../api/types';
import { nodeRole, reach } from './graph';

/**
 * Cross-vault dependencies, read off the dependency graph alone: which nodes several vaults
 * depend on, and how much each vault has riding on them. Exposure only — no probability and
 * no joint loss; that is the Python side's job.
 */
export type Shared = {
  node: GraphNode;
  /** vault id → what it supplies into the markets that lead to this node, in loan units. */
  exposure: Map<string, number>;
};

export type CrossView = {
  vaults: GraphNode[];
  /** Nodes two or more vaults depend on, most shared first. */
  shared: Shared[];
  /** vault id → the nodes only it depends on. */
  privateNodes: Map<string, GraphNode[]>;
  /** Pairs of vaults → the shared nodes they have in common. */
  pairs: { a: string; b: string; common: GraphNode[] }[];
};

export const totalExposure = (s: Shared) => [...s.exposure.values()].reduce((a, b) => a + b, 0);

/**
 * `includeLoanTokens`: a loan token (USDC…) is common to every vault lending it and drowns
 * the signal, so it is left out unless asked for.
 */
export function crossView(graph: GraphResponse, includeLoanTokens = false): CrossView {
  const { nodes, edges } = graph;
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const vaults = nodes.filter((n) => nodeRole(n) === 'vault');
  // A vault's asset ("denominated in") and every market's loan token ("lends").
  const loanTokens = new Set(
    edges.filter((e) => e.rel === 'denominated in' || e.rel === 'lends').map((e) => e.target),
  );
  const ignored = (id: string) =>
    byId.get(id)?.kind === 'Actor' || (!includeLoanTokens && loanTokens.has(id));

  const users = new Map<string, Map<string, number>>();
  for (const vault of vaults) {
    const supplies = edges.filter((e) => e.source === vault.id && e.rel === 'supplies');
    for (const id of reach(vault.id, edges)) {
      if (id === vault.id || ignored(id)) continue;
      const exposure = supplies
        .filter((s) => s.target === id || reach(s.target, edges).has(id))
        .reduce((sum, s) => sum + (s.amount ?? 0), 0);
      const perVault = users.get(id) ?? new Map<string, number>();
      perVault.set(vault.id, exposure);
      users.set(id, perVault);
    }
  }

  const shared: Shared[] = [...users]
    .filter(([, perVault]) => perVault.size > 1)
    .map(([id, exposure]) => ({ node: byId.get(id)!, exposure }))
    .sort((a, b) => b.exposure.size - a.exposure.size || totalExposure(b) - totalExposure(a));

  const privateNodes = new Map(
    vaults.map((v) => [
      v.id,
      [...users]
        .filter(([, perVault]) => perVault.size === 1 && perVault.has(v.id))
        .map(([id]) => byId.get(id)!),
    ]),
  );

  const pairs: CrossView['pairs'] = [];
  vaults.forEach((a, i) =>
    vaults.slice(i + 1).forEach((b) => {
      const common = shared
        .filter((s) => s.exposure.has(a.id) && s.exposure.has(b.id))
        .map((s) => s.node);
      if (common.length) pairs.push({ a: a.id, b: b.id, common });
    }),
  );

  return { vaults, shared, privateNodes, pairs };
}

/**
 * The view from one vault: only the shared nodes it depends on, and only the vaults it shares
 * them with (`vault` first). Everything else is dropped, not faded.
 */
export function focusOn(view: CrossView, vault: string): CrossView {
  const shared = view.shared.filter((s) => s.exposure.has(vault));
  const peers = new Set(shared.flatMap((s) => [...s.exposure.keys()]));
  return {
    vaults: view.vaults
      .filter((v) => v.id === vault || peers.has(v.id))
      .sort((a, b) => Number(b.id === vault) - Number(a.id === vault)),
    shared,
    privateNodes: view.privateNodes,
    pairs: view.pairs.filter((p) => p.a === vault || p.b === vault),
  };
}

/**
 * Vault ↔ vault: one edge per pair. Its amount is the overlap — for each shared node, the
 * smaller of the two vaults' exposures to it, summed — so a thick edge means both have a lot
 * riding on the same things.
 */
export function pairEdges(view: CrossView): GraphEdge[] {
  const byNode = new Map(view.shared.map((s) => [s.node.id, s.exposure]));
  return view.pairs.map(({ a, b, common }) => ({
    source: a,
    target: b,
    rel: 'shares',
    amount:
      common.reduce((sum, n) => {
        const e = byNode.get(n.id)!;
        return sum + Math.min(e.get(a) ?? 0, e.get(b) ?? 0);
      }, 0) || null,
    unit: null,
    details: { shared: common.map((n) => n.label).join(', ') },
  }));
}

/** The focus vault in the middle, its peers evenly on a circle around it. */
export function ego(focus: string, peers: string[], radius = 360) {
  return new Map([
    [focus, { x: 0, y: 0 }],
    ...peers.map((id, i): [string, { x: number; y: number }] => {
      const angle = (2 * Math.PI * i) / peers.length - Math.PI / 2;
      return [id, { x: radius * Math.cos(angle), y: radius * Math.sin(angle) }];
    }),
  ]);
}

/**
 * The graph contracted onto `keep` (the vaults and the shared nodes), keeping its hierarchy:
 * an edge between two kept nodes stays as it is, and a path through nodes that are not kept
 * becomes one edge to the first kept node it reaches (a vault → the shared oracle behind its
 * own market). A vault's edges carry its exposure to the node they lead to.
 */
export function contract(graph: GraphResponse, view: CrossView): GraphEdge[] {
  const keep = new Set([...view.vaults.map((v) => v.id), ...view.shared.map((s) => s.node.id)]);
  const exposure = new Map(view.shared.map((s) => [s.node.id, s.exposure]));
  const out = new Map<string, GraphEdge[]>();
  for (const e of graph.edges) out.set(e.source, [...(out.get(e.source) ?? []), e]);

  const result: GraphEdge[] = [];
  for (const from of keep) {
    const seen = new Set([from]);
    const queue: { id: string; first: GraphEdge }[] = (out.get(from) ?? []).map((e) => ({
      id: e.target,
      first: e,
    }));
    for (let item = queue.shift(); item; item = queue.shift()) {
      if (seen.has(item.id)) continue;
      seen.add(item.id);
      if (keep.has(item.id)) {
        const direct = item.first.target === item.id;
        const vaultExposure = exposure.get(item.id)?.get(from);
        result.push({
          source: from,
          target: item.id,
          rel: direct ? item.first.rel : `${item.first.rel} (via unshared)`,
          amount: vaultExposure ?? (direct ? item.first.amount : null),
          unit: direct ? item.first.unit : null,
          details: {},
        });
        continue; // stop at the first kept node: what lies below it is its own edges' job
      }
      for (const e of out.get(item.id) ?? []) queue.push({ id: e.target, first: item.first });
    }
  }
  return result;
}
