import { useParams } from '@tanstack/react-router';
import { useMarket } from '../api/hooks';
import { ErrorState, Loading } from '../components/States';
import { LiquidationChart } from '../components/LiquidationChart';
import { Stat, StatRow } from '../components/Stat';
import { usd, percent, shortHash } from '../lib/format';

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

      <Stat prominent label="Supply" value={usd(market.supply_usd)} />
      <StatRow
        items={[
          { label: 'Borrow', value: usd(market.borrow_usd) },
          { label: 'Liquidity', value: usd(market.liquidity_usd) },
          { label: 'Utilization', value: percent(market.utilization) },
          { label: 'Borrow APY', value: percent(market.borrow_apy) },
          { label: 'LLTV', value: percent(market.lltv) },
          { label: 'Borrowers', value: String(market.borrowers) },
          { label: 'Collateral price', value: usd(market.collateral_price_usd, 2) },
        ]}
      />

      <LiquidationChart liquidations={market.liquidations} price={market.collateral_price_usd} />
    </div>
  );
}
