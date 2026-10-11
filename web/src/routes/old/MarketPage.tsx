import { useParams } from '@tanstack/react-router';
import { useMarket } from '../../api/hooks';
import { ErrorState, Loading } from '../../components/States';
import { MarketDetail } from '../../components/vault/MarketDetail';
import { shortHash } from '../../lib/format';

export function MarketPage() {
  const { marketId } = useParams({ from: '/market/$marketId' });
  const { data: market, isPending, error } = useMarket(marketId);

  if (isPending) return <Loading what="the market" />;
  if (error) return <ErrorState what="the market" error={error} />;

  return (
    <div className="mx-auto grid max-w-[1120px] gap-10 px-5.5 pt-9 pb-14">
      <header className="flex items-baseline justify-between gap-6">
        <h1 className="m-0 truncate">{market.label}</h1>
        <span className="mono truncate text-[0.8rem] text-muted-foreground">
          {shortHash(market.id)}
        </span>
      </header>

      <MarketDetail market={market} prominent />
    </div>
  );
}
