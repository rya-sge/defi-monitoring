import { useParams } from '@tanstack/react-router';
import { useMarket } from '../api/hooks';
import { ErrorState, Loading } from '../components/States';
import { LiquidationChart } from '../components/LiquidationChart';
import { StatRow } from '../components/Stat';
import { compactUsd, percent, usd } from '../lib/format';

export function MarketPage() {
  const { marketId } = useParams({ from: '/market/$marketId' });
  const { data: market, isPending, error } = useMarket(marketId);

  if (isPending) return <Loading what="the market" />;
  if (error) return <ErrorState what="the market" error={error} />;

  return (
    <div className="mx-auto grid max-w-[1120px] gap-10 px-5.5 pt-9 pb-14">
      <header className="flex items-baseline justify-between gap-6">
        <h1 className="m-0 truncate">{market.label}</h1>
        <span className="mono truncate text-[0.8rem] text-muted-foreground">{market.id}</span>
      </header>

      <StatRow
        items={[
          { label: 'Supply', value: compactUsd(market.supply_usd) },
          { label: 'Borrow', value: compactUsd(market.borrow_usd) },
          { label: 'Liquidity', value: compactUsd(market.liquidity_usd) },
          { label: 'Utilization', value: percent(market.utilization, 1) },
          { label: 'Borrow APY', value: percent(market.borrow_apy, 2) },
          { label: 'LLTV', value: percent(market.lltv, 1) },
          { label: 'Borrowers', value: String(market.borrowers) },
          { label: 'Collateral price', value: usd(market.collateral_price_usd, 2) },
        ]}
      />

      <LiquidationChart liquidations={market.liquidations} price={market.collateral_price_usd} />
    </div>
  );
}
