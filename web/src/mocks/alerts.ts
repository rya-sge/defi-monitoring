import type { Alert, WatchTick } from '../api/types';

/**
 * Mock stream for `/api/watch/stream`.
 *
 * The `info` and `warn` entries are verbatim copies of recorded CLI output
 * (`out/watch-*.jsonl`). The two `critical` entries are FABRICATED: no recorded
 * run contains a critical alert, so their wording is modelled on the rows of
 * `docs/alert-runbook.md` (`HealthFactor` · liquidatable now, `Admin.Upgraded`)
 * rather than taken from real output. Treat their `data` keys as illustrative.
 */
export const MOCK_ALERTS: readonly Alert[] = [
  {
    level: 'info',
    block: 26162750,
    tx: null,
    event: 'Caps',
    title: 'wstETH/RLUSD (LLTV 86.0%) is being wound down',
    detail: 'its cap is 0 but 1,382,524 RLUSD is still allocated',
    depositor_impact: null,
    data: { market: '0x88abdf8693e663144c3544b9442e9b04520016d6ebc57aa76424c00ab1683c9d' },
  },
  {
    level: 'warn',
    block: 26162750,
    tx: null,
    event: 'Exposure',
    title: '51% of the vault is in kBTC/RLUSD (LLTV 86.0%)',
    detail: '235,131,419 RLUSD; a bad debt there is shared by every depositor',
    depositor_impact: null,
    data: { market: '0x15bb2a6af0c909eed19fb1f2ceeead34ecbdcba626de752c6b09389ee14eec32' },
  },
  {
    level: 'info',
    block: 26162792,
    tx: '0xe6f42b0b7b572dfbf1dc49124bf2251438b930fa929198c11b6dd40f17e5d0d0',
    event: 'Vault.Deposit',
    title: 'Your deposit',
    detail: '9,118 RLUSD (0.0% of the vault)',
    depositor_impact: null,
    // The CLI emits raw wei as a JSON number; it exceeds Number.MAX_SAFE_INTEGER,
    // so this is the double the browser would parse it to anyway.
    data: { assets: 9.118273396251962e21 },
  },
  {
    level: 'warn',
    block: 26162801,
    tx: null,
    event: 'Liquidity',
    title: 'You cannot exit in full with a plain withdrawal',
    detail:
      'your 149,431,791 RLUSD vs 39,237,054 RLUSD payable by a plain withdrawal (idle, no liquidity adapter); 46,351,806 RLUSD more reachable only through forceDeallocate, penalty up to 0.01%',
    depositor_impact: null,
    data: {},
  },
  {
    // FABRICATED — see the note above.
    level: 'critical',
    block: 26162814,
    tx: '0x7a4b1d0c9f3e8a21b5c6d7e8f90123456789abcdef0123456789abcdef012345',
    event: 'UnrealisedBadDebt',
    title: 'Unrealised bad debt in kBTC/RLUSD (LLTV 86.0%)',
    detail:
      '412,905 RLUSD of debt above collateral across 3 borrowers (0.18% of the vault); not written off yet, so it is not in the share price',
    depositor_impact: -268_431.52,
    data: {
      market: '0x15bb2a6af0c909eed19fb1f2ceeead34ecbdcba626de752c6b09389ee14eec32',
      borrowers: 3,
      share_of_vault: 0.0018,
    },
  },
  {
    level: 'info',
    block: 26162820,
    tx: '0x1106ed7329f26883ecc80247e54684dcff8cc2d2328d51f8ae2b4ff9608257b2',
    event: 'Adapter.Deallocate',
    title: 'Deallocate weETH/RLUSD (LLTV 86.0%)',
    detail: 'allocation now 105,547,764 RLUSD (23% of the vault, was 23%)',
    depositor_impact: null,
    data: {
      market: '0xea4bfb18df0ee6bffb7b3f0270899a8adb92ab6b684709634c8276128813cfd4',
      share: 0.23040076274006227,
    },
  },
  {
    level: 'warn',
    block: 26162826,
    tx: null,
    event: 'Timelock',
    title: '4 risk-increasing change(s) can be made with no notice',
    detail:
      'setPerformanceFee, setManagementFee, setIsAllocator, setReceiveSharesGate have a zero timelock and are not abdicated',
    depositor_impact: null,
    data: {},
  },
  {
    // FABRICATED — see the note above.
    level: 'critical',
    block: 26162833,
    tx: '0xbe11c0ffee0042d3adbeef1234567890abcdef1234567890abcdef1234567890',
    event: 'Admin.Upgraded',
    title: 'Oracle 0xa5657b40… was upgraded',
    detail:
      'implementation 0x4be50be3… → 0x9b465523…, unverified; the price feeding kBTC/RLUSD can now read anything the new code says',
    depositor_impact: null,
    data: {
      contract: '0xa5657b406fc4282039861c6fca64452aefec8ac0',
      implementation: '0x9b4655239e91dc9e1f7599bb88fba41b4542de5b',
      verified: false,
    },
  },
  {
    level: 'info',
    block: 26162840,
    tx: null,
    event: 'HealthFactor',
    title: 'HF 1.09 on PST/USDC (LLTV 86.0%)',
    detail: 'an 8.64% fall in the oracle price liquidates the position',
    depositor_impact: null,
    data: { health_factor: 1.0945, liquidation_at: -0.0864 },
  },
  {
    level: 'warn',
    block: 26162847,
    tx: null,
    event: 'LiquidationCurve',
    title: 'Steep liquidation curve on kBTC/RLUSD (LLTV 86.0%)',
    detail: 'a 5% oracle fall makes 31,204,118 RLUSD of debt liquidatable (14% of the market)',
    depositor_impact: null,
    data: { drop: 0.05, debt_at_risk: 31204118.0 },
  },
];

export const MOCK_TICKS: readonly WatchTick[] = [
  { block: 26162750, message: 'start-up: 2 markets, 1 adapter, state read' },
  { block: 26162801, message: 'polling 2 blocks behind the head' },
  { block: 26162847, message: 'cross-check second RPC: ok' },
];
