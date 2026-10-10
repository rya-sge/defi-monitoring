import { Table, TableBody, TableCell, TableRow } from '@/components/ui/table';
import { cn } from 'cn';
import { detailValue, etherscanUrl, humanKey } from '../lib/format';

/** Renders a `details` bag; addresses and tx hashes become Etherscan links. */
export function DetailsTable({ details }: { details: Record<string, unknown> }) {
  const rows = Object.entries(details).filter(([, value]) => value != null && value !== '');
  if (rows.length === 0) return <p className="text-muted-foreground">No details recorded.</p>;

  return (
    <Table className="text-[0.86rem] tabular-nums">
      <TableBody>
        {rows.map(([key, value]) => {
          const text = detailValue(value);
          const href = typeof value === 'string' ? etherscanUrl(value) : null;
          return (
            <TableRow key={key}>
              <TableCell className="w-[42%] py-2 pr-3.5 align-top whitespace-normal text-muted-foreground">
                {humanKey(key)}
              </TableCell>
              <TableCell
                className={cn(
                  'py-2 align-top [overflow-wrap:anywhere] whitespace-normal',
                  href && 'mono',
                )}
              >
                {href ? (
                  <a href={href} target="_blank" rel="noreferrer noopener">
                    {text}
                  </a>
                ) : (
                  text
                )}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
