// Under this scenario, which pocket of my book do I act on first, and what does acting cost against not acting?
import { useState } from 'react';
import { Link } from '@tanstack/react-router';
import { FlaskConical, Gauge } from 'lucide-react';
import { useBooks, useIncidentImpact } from '../api/hooks';
import type { BookSummary, IncidentResponse, VaultLine } from '../api/types';
import { FormattedText } from '../components/FormattedText';
import { Stat, StatRow } from '../components/Stat';
import { ErrorState, Loading } from '../components/States';
import { percent, usd } from '../lib/format';
import { VERDICT_LABEL, VERDICT_PRIORITY, VERDICT_TONE, pStar } from '../lib/verdict';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

const HORIZON = 30;
const DEFAULT_BOOK = 'rockawayx-ethereum';

// The scenarios the mock fixtures hold (scripts/export_incident_fixtures.py); any other needs the API.
const SCENARIOS = [
  { shock: 'token=PST:0.3', label: 'PST −30%' },
  { shock: 'token=fxSAVE:0.3', label: 'fxSAVE −30%' },
  { shock: 'borrower=all:0.5:1', label: 'Largest borrower defaults, 50% recovered' },
  { shock: 'venue=Binance:0.5', label: 'Binance loses 50% of USDe backing' },
] as const;

export function BookPage() {
  const { data: books, isPending, error } = useBooks();
  const [bookName, setBookName] = useState<string>();
  const [shock, setShock] = useState<string>(SCENARIOS[0].shock);

  if (isPending) return <Loading what="the books" />;
  if (error) return <ErrorState what="the books" error={error} />;
  const book =
    books.find((b) => b.name === bookName) ??
    books.find((b) => b.name === DEFAULT_BOOK) ??
    books[0];
  if (!book) return null;

  return (
    <div className="mx-auto grid max-w-[1280px] gap-9 px-5.5 pt-7 pb-14">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="m-0">{book.title}</h1>
        <div className="flex flex-wrap gap-3 text-[0.85rem]">
          <Select value={book.name} onValueChange={setBookName}>
            <SelectTrigger aria-label="Book" size="sm" className="w-64">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {books.map((b) => (
                <SelectItem key={b.name} value={b.name}>
                  {b.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={shock} onValueChange={setShock}>
            <SelectTrigger aria-label="Scenario" size="sm" className="w-72">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SCENARIOS.map((s) => (
                <SelectItem key={s.shock} value={s.shock}>
                  <FormattedText>{s.label}</FormattedText>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </header>
      <BookIncident book={book} shock={shock} />
    </div>
  );
}

function BookIncident({ book, shock }: { book: BookSummary; shock: string }) {
  const { data, isPending, error } = useIncidentImpact({
    example: book.name,
    shocks: [shock],
    horizon: HORIZON,
    // the conditional distribution draws a markdown's size: a borrower default has none
    conditional: !shock.startsWith('borrower='),
  });
  if (isPending) return <Loading what="the incident" />;
  if (error) return <ErrorState what="the incident" error={error} />;
  return <BookView book={book} shock={shock} result={data} />;
}

function BookView({
  book,
  shock,
  result,
}: {
  book: BookSummary;
  shock: string;
  result: IncidentResponse;
}) {
  const b = result.book;
  const c = b.conditional;
  const rows = [...b.lines].sort(
    (x, y) =>
      VERDICT_PRIORITY[x.verdict] - VERDICT_PRIORITY[y.verdict] ||
      (x.p_star ?? Infinity) - (y.p_star ?? Infinity) ||
      y.loss_usd - x.loss_usd ||
      x.name.localeCompare(y.name),
  );
  const kinds = new Map(book.vaults.map((v) => [v.address.toLowerCase(), v.kind ?? 'vault']));
  const outside = new Map(
    result.vaults.map((v) => [v.vault.toLowerCase(), v.outside.join('\n')] as const),
  );

  return (
    <>
      <section aria-label="Book totals" className="grid gap-9 sm:grid-cols-[auto_1fr]">
        <Stat prominent label="Book loss" value={usd(b.loss_usd)} />
        <StatRow
          items={[
            { label: 'Book value', value: usd(b.value_usd) },
            { label: 'Exposure', value: usd(b.exposure_usd) },
            {
              label: `Breakeven p* over ${b.horizon_days} d`,
              value: pStar(b.p_star),
              note: b.p_star_year != null ? `${pStar(b.p_star_year)} per year` : undefined,
            },
          ]}
        />
      </section>
      {c ? (
        <section aria-label="Stay or leave">
          <h2 className="mt-0">Stay or leave, given the incident</h2>
          <StatRow
            items={[
              {
                label: 'Stay, mean loss',
                value: usd(c.stay_mean),
                note: `p95 ${usd(c.stay_p95)} · p99 ${usd(c.stay_p99)}`,
              },
              { label: 'Leave, mean cost', value: usd(c.leave_mean) },
              {
                label: 'Staying is worse',
                value: percent(c.p_stay_worse),
                note: `${c.paths.toLocaleString('en-US')} paths`,
                tone: c.p_stay_worse >= 0.5 ? 'warn' : 'neutral',
              },
              { label: 'No liquidator', value: percent(c.no_liquidator_share) },
            ]}
          />
        </section>
      ) : null}
      <section aria-label="Pockets">
        <h2 className="mt-0">Act first on</h2>
        <Table className="tabular-nums">
          <TableHeader>
            <TableRow>
              <TableHead>Pocket</TableHead>
              <TableHead>Action</TableHead>
              <TableHead className="text-right">Exposure</TableHead>
              <TableHead className="text-right">Loss if stay</TableHead>
              <TableHead className="text-right">Exit cost</TableHead>
              <TableHead className="text-right">Saved by exit</TableHead>
              <TableHead className="text-right">p*</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((line) => (
              <PocketRow
                key={line.vault}
                line={line}
                book={book.name}
                shock={shock}
                isVault={kinds.get(line.vault.toLowerCase()) !== 'borrow'}
                outside={outside.get(line.vault.toLowerCase())}
              />
            ))}
          </TableBody>
        </Table>
      </section>
    </>
  );
}

function PocketRow({
  line,
  book,
  shock,
  isVault,
  outside,
}: {
  line: VaultLine;
  book: string;
  shock: string;
  isVault: boolean;
  outside?: string;
}) {
  const priced = (value: number) => (line.priced ? usd(value) : '—');
  const hit = line.hit_markets.length > 0;
  const target = line.vault.toLowerCase();
  return (
    <TableRow>
      <TableCell className="max-w-64 whitespace-normal font-medium">{line.name}</TableCell>
      <TableCell>
        <span
          className={`text-xs font-semibold ${hit ? VERDICT_TONE[line.verdict] : 'text-muted-foreground'}`}
        >
          {line.reason ? (
            <Tooltip>
              <TooltipTrigger className="cursor-help">
                {hit ? VERDICT_LABEL[line.verdict] : 'Unaffected'}
              </TooltipTrigger>
              <TooltipContent className="max-w-80">{line.reason}</TooltipContent>
            </Tooltip>
          ) : hit ? (
            VERDICT_LABEL[line.verdict]
          ) : (
            'Unaffected'
          )}
        </span>
      </TableCell>
      <TableCell className="text-right">{priced(line.exposure_usd)}</TableCell>
      <TableCell className="text-right">{priced(line.loss_usd)}</TableCell>
      <TableCell className="text-right">{priced(line.exit_cost_usd)}</TableCell>
      <TableCell className="text-right">{priced(line.saved_usd)}</TableCell>
      <TableCell className="text-right">
        {outside ? (
          <Tooltip>
            <TooltipTrigger className="cursor-help underline decoration-dotted underline-offset-4">
              <FormattedText>{pStar(line.p_star)}</FormattedText>
            </TooltipTrigger>
            <TooltipContent className="max-w-sm whitespace-pre-line">{outside}</TooltipContent>
          </Tooltip>
        ) : (
          <FormattedText>{pStar(line.p_star)}</FormattedText>
        )}
      </TableCell>
      <TableCell>
        <div className="flex justify-end gap-1">
          {isVault ? (
            <Button asChild variant="ghost" size="icon" title="Open vault">
              <Link to="/vault" search={(prev) => ({ ...prev, target })}>
                <Gauge />
              </Link>
            </Button>
          ) : null}
          <Button asChild variant="ghost" size="icon" title="Open in Scenario lab">
            <Link to="/scenario" search={{ book, shock, target }}>
              <FlaskConical />
            </Link>
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
}
