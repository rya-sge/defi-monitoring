import type { Market } from '../../api/types';
import { LiquidationChart } from '../LiquidationChart';
import { Stat, StatRow } from '../Stat';
import { percent, usd } from '../../lib/format';

/** A Blue market's state and the liquidating fall of its borrowers; `prominent` on its own page only. */
export function MarketDetail({
  market,
  prominent = false,
}: {
  market: Market;
  prominent?: boolean;
}) {
  return (
    <>
      <Stat prominent={prominent} label="Supply" value={usd(market.supply_usd)} />
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
    </>
  );
}
