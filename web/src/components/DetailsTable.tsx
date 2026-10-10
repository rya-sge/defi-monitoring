import { detailValue, etherscanUrl, humanKey } from '../lib/format';

/** Renders a `details` bag; addresses and tx hashes become Etherscan links. */
export function DetailsTable({ details }: { details: Record<string, unknown> }) {
  const rows = Object.entries(details).filter(([, value]) => value != null && value !== '');
  if (rows.length === 0) return <p className="muted">No details recorded.</p>;

  return (
    <table className="detail-table">
      <tbody>
        {rows.map(([key, value]) => {
          const text = detailValue(value);
          const href = typeof value === 'string' ? etherscanUrl(value) : null;
          return (
            <tr key={key}>
              <td>{humanKey(key)}</td>
              <td className={href ? 'mono' : undefined}>
                {href ? (
                  <a href={href} target="_blank" rel="noreferrer noopener">
                    {text}
                  </a>
                ) : (
                  text
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
