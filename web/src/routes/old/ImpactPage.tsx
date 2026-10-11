import { useShockTrace } from '../../api/hooks';
import { TraceGraph, TraceSummary } from '../../components/scenario/TraceViews';
import { ErrorState, Loading } from '../../components/States';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

/** The committed example trace: a summary and the graph. */

export function ImpactPage() {
  const { data, isPending, error } = useShockTrace();
  if (isPending) return <Loading what="the shock trace" />;
  if (error) return <ErrorState what="the shock trace" error={error} />;

  const label = (id: string) => data.graph.nodes.find((node) => node.id === id)?.label ?? id;

  return (
    <div className="flex h-full flex-col px-5.5 pt-5.5">
      <header className="mb-3.5">
        <h1>Impact</h1>
        <p className="text-muted-foreground">
          {data.shocks.map((shock) => shock.label).join(' + ')} · block {data.block} ·{' '}
          {data.converged ? 'converged' : 'not converged: numbers are not final'} · example trace
        </p>
      </header>
      <Tabs defaultValue="summary" className="min-h-0 flex-1">
        <TabsList>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="graph">Graph</TabsTrigger>
        </TabsList>
        <TabsContent value="summary" className="overflow-auto pb-9">
          <TraceSummary trace={data} label={label} />
        </TabsContent>
        <TabsContent value="graph" className="relative min-h-[60vh]">
          <TraceGraph trace={data} label={label} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
