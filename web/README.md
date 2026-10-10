# riskdep web

Frontend for the `riskdep` DeFi risk tool: the analyze verdict, the dependency graph and the live
alert stream, as three pages over the FastAPI backend in `riskdep/`.

Vite + React + TypeScript, TanStack Router (code-based) and TanStack Query. Cytoscape.js draws the
dependency graph — the backend already emits Cytoscape-shaped nodes and edges, and the colours,
shapes and layout here are copied from `riskdep/graph.py` so the web graph and the CLI's standalone
HTML read alike. Recharts draws the loss-contribution and tail-measure charts. No CSS framework:
one stylesheet, light and dark, driven by `prefers-color-scheme` with the same tokens the CLI uses.

## Running

```bash
pnpm install          # pnpm 11, node 26
pnpm dev              # http://localhost:5173
pnpm build            # tsc -b && vite build -> dist/
pnpm lint             # eslint + prettier --check
pnpm format           # prettier --write
```

`pnpm dev` proxies `/api` to `http://127.0.0.1:8000`, so the backend needs no CORS configuration.

## Mock mode

`VITE_USE_MOCKS` (in `.env`, **default `true`**) decides where the data comes from:

| value   | behaviour                                                               |
| ------- | ----------------------------------------------------------------------- |
| `true`  | the hooks resolve the fixtures in `src/mocks/`; no backend is contacted |
| `false` | the hooks call `/api`, proxied to `127.0.0.1:8000`                      |

The fixtures are real CLI output, copied verbatim:

- `src/mocks/report.json` — `python -m riskdep analyze --demo` (`out/report.json`)
- `src/mocks/graph.json` — `python -m riskdep graph` (`out/graph.json`)

They are the source of truth for the types in `src/api/types.ts`. Refresh them by re-running the
CLI and copying `out/*.json` across.

`src/mocks/alerts.ts` stands in for the SSE stream: ten alerts replayed one per 1.5 s, then the
stream reports itself closed. The `info` and `warn` entries are copied from recorded runs
(`out/watch-*.jsonl`); the two `critical` entries are **fabricated**, because no recorded run
contains one — their wording follows the rows of `docs/alert-runbook.md`.

## API contract

Base `/api`.

```
GET  /api/health
  -> { status: "ok", mode: "offline"|"live"|"refresh", data_as_of: string }

GET  /api/graph?user=<addr>&vault=<addr>&block=<int>   (all optional)
  -> { title, subtitle, nodes: GraphNode[], edges: GraphEdge[] }

GET  /api/report
  -> Report   (the latest available analyze report)

POST /api/analyze
  body { market?: string, user?: string, horizon?: number, paths?: number, live?: boolean }
  -> Report

GET  /api/watch/stream?vault=<addr>&user=<addr>&min_level=info|warn|critical
  -> Server-Sent Events, two event types:
       event: alert   data: Alert
       event: tick    data: { block: number, message: string }
```

`GraphNode`, `GraphEdge`, `Alert` and `Report` are declared in `src/api/types.ts`, field for field
against the fixtures. Two notes on what the fixtures show:

- **The graph inside a `Report` is not the `/api/graph` shape.** `analyze` serialises a networkx
  graph: lowercase kinds (`lending`, `oracle`, `offchain`…), flat node attributes (`source`,
  `evidence`) and `from`/`to` edges. `lib/graph.ts` normalises it onto the six `/api/graph` kinds so
  one Cytoscape component renders both. The `/graph` page uses `/api/graph` and never needs it.
- **Numbers can arrive as `null`.** The report writer maps `inf` and `nan` to `null`, so a ratio
  whose denominator can be zero (`health_factor` with no debt, `risk_multiple_to_exit` with no
  expected loss) is `number | null`. Every formatter in `lib/format.ts` renders those as an em dash.

## Pages

| route    | what it shows                                                                                                                                                                                   |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/`      | the STAY / REDUCE / EXIT verdict with its headline and reasons, the position KPIs, each layer's contribution to the expected loss, the tail measures, the exit quote and the oracle sensitivity |
| `/graph` | the dependency graph full-page: colour and shape per `kind`, kind filter, search, click a node or edge for its `details`; `subtitle` is the provenance line                                     |
| `/watch` | the SSE alert feed, newest first, with per-level counters and a minimum-level filter                                                                                                            |

## Layout

```
web/
├── index.html
├── vite.config.ts            dev server + /api proxy
├── eslint.config.js          typescript-eslint (type-checked), react-hooks, react-refresh, prettier
├── tsconfig.{json,app,node}  strict, noUnusedLocals/Parameters, verbatimModuleSyntax
├── pnpm-workspace.yaml       allows esbuild's postinstall
└── src/
    ├── main.tsx              QueryClient + RouterProvider
    ├── router.tsx            three code-based routes, each lazily loaded
    ├── styles.css            one stylesheet, light + dark tokens
    ├── api/
    │   ├── types.ts          the shapes, read off the fixtures
    │   ├── client.ts         fetch wrappers; the mock switch lives here
    │   ├── hooks.ts          TanStack Query hooks
    │   └── stream.ts         SSE subscription, and the mock replay
    ├── mocks/
    │   ├── report.json       out/report.json, verbatim
    │   ├── graph.json        out/graph.json, verbatim
    │   └── alerts.ts         replayed alerts (two are fabricated; see above)
    ├── lib/
    │   ├── format.ts         usd / percent / hashes, all null-tolerant
    │   └── graph.ts          kind palette and shapes from graph.py, report-graph normaliser
    ├── components/
    │   ├── AppShell.tsx      top bar, nav, backend mode chip
    │   ├── GraphCanvas.tsx   Cytoscape, kind filter, search, selection
    │   ├── DetailsTable.tsx  a `details` bag; addresses link to Etherscan
    │   ├── Kpi.tsx
    │   └── States.tsx
    └── routes/
        ├── PositionPage.tsx
        ├── GraphPage.tsx
        └── WatchPage.tsx
```

Routes are split per page: Recharts and Cytoscape are both large and no page needs both, so neither
is on the critical path of the first paint.
