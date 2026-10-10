# Integrate Rewards Display

> Source: https://docs.morpho.org/developers/rewards/tutorials/integrate-display

---

# Integrate Rewards Display

This tutorial shows you how to build user interfaces that display reward information from Merkl. A well-designed rewards display helps users understand their earnings and encourages engagement with your platform.

## [What to Display](#what-to-display)

A complete rewards integration should show:

1. **Vault/Market Level Rewards** - The APR users can earn
2. **User Claimable Rewards** - How much users have earned and can claim
3. **Combined APY/APR** - Total yield including base + rewards
4. **Reward Token Information** - What tokens are being distributed
5. **Claim Status** - What's claimable now vs. pending

## [Displaying Vault Rewards](#displaying-vault-rewards)

### [Fetching and Calculating Total APY](#fetching-and-calculating-total-apy)

```
import { GraphQLClient, gql } from "graphql-request";

const client = new GraphQLClient("https://api.morpho.org/graphql");

async function getVaultWithRewards(vaultAddress: string, chainId: number) {
  const query = gql`
    query VaultRewards($address: String!, $chainId: Int!) {
      vaultByAddress(address: $address, chainId: $chainId) {
        address
        name
        symbol
        asset {
          symbol
        }
        state {
          apy
          totalAssets
          allRewards {
            supplyApr
            asset {
              address
              symbol
              price {
                usd
              }
            }
          }
        }
      }
    }
  `;

  const response = await client.request(query, {
    address: vaultAddress,
    chainId,
  });

  const vault = response.vaultByAddress;

  return {
    vault: vault.name,
    symbol: vault.symbol,
    asset: vault.asset.symbol,
    baseApy: parseFloat(vault.state.apy),
    rewardsApr: vault.state.allRewards.reduce(
      (sum, r) => sum + parseFloat(r.supplyApr),
      0
    ),
    totalApy:
      parseFloat(vault.state.apy) +
      vault.state.allRewards.reduce((sum, r) => sum + parseFloat(r.supplyApr), 0),
    rewards: vault.state.allRewards.map((r) => ({
      token: r.asset.symbol,
      apr: parseFloat(r.supplyApr),
      tokenAddress: r.asset.address,
    })),
  };
}
```

### [React Component Example](#react-component-example)

```
import React, { useEffect, useState } from "react";

interface VaultRewardsDisplayProps {
  vaultAddress: string;
  chainId: number;
}

function VaultRewardsDisplay({ vaultAddress, chainId }: VaultRewardsDisplayProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getVaultWithRewards(vaultAddress, chainId)
      .then(setData)
      .finally(() => setLoading(false));
  }, [vaultAddress, chainId]);

  if (loading) return <div>Loading...</div>;
  if (!data) return <div>No data</div>;

  return (
    <div className="vault-rewards">
      <h2>{data.vault}</h2>
      <p className="asset">Deposit {data.asset}</p>

      {/* Total APY */}
      <div className="apy-display">
        <h3>Total APY: {data.totalApy.toFixed(2)}%</h3>
        <div className="breakdown">
          <div>Base APY: {data.baseApy.toFixed(2)}%</div>
          <div>Rewards APR: +{data.rewardsApr.toFixed(2)}%</div>
        </div>
      </div>

      {/* Rewards Breakdown */}
      {data.rewards.length > 0 && (
        <div className="rewards-breakdown">
          <h4>Reward Programs:</h4>
          {data.rewards.map((reward) => (
            <div key={reward.tokenAddress} className="reward-item">
              <span>{reward.token}</span>
              <span>{reward.apr.toFixed(2)}% APR</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### [Visual Design Tips](#visual-design-tips)

**Highlight Total Yield:**

```
<div className="total-apy">
  <span className="label">Total APY</span>
  <span className="value">{totalApy.toFixed(2)}%</span>
</div>
```

**Show Breakdown on Hover/Click:**

```
<Tooltip content={
  <div>
    <div>Base APY: {baseApy}%</div>
    <div>MORPHO Rewards: +{morphoApr}%</div>
    <div>Partner Rewards: +{partnerApr}%</div>
  </div>
}>
  <span className="apy">{totalApy}%</span>
</Tooltip>
```

**Use Badges for Rewards:**

```
{rewards.length > 0 && (
  <span className="rewards-badge">
    +{rewardsApr.toFixed(1)}% Rewards
  </span>
)}
```

## [Displaying User Claimable Rewards](#displaying-user-claimable-rewards)

### [Fetching User Rewards](#fetching-user-rewards)

```
async function getUserAllClaimableRewards(userAddress: string, chainId: number) {
  const merklRewards = await fetchMerklClaimable(userAddress, chainId);

  return { merkl: merklRewards };
}

async function fetchMerklClaimable(userAddress: string, chainId: number) {
  const response = await fetch(
    `https://api.merkl.xyz/v4/users/${userAddress.toLowerCase()}/rewards?chainId=${chainId}`
  );
  const data = await response.json();

  // The endpoint returns an array of per-chain objects; flatten to a list of rewards.
  const rewards = data.flatMap((entry) => entry.rewards);

  const claimable: Array<{
    token: string;
    amount: bigint;
    symbol: string;
    decimals: number;
  }> = [];

  for (const reward of rewards) {
    const unclaimed = BigInt(reward.amount) - BigInt(reward.claimed);
    claimable.push({
      token: reward.token.address,
      amount: unclaimed,
      symbol: reward.token.symbol,
      decimals: reward.token.decimals,
    });
  }

  return claimable;
}
```

### [React Component for User Rewards](#react-component-for-user-rewards)

```
import { formatUnits } from "viem";

function UserRewardsDisplay({ userAddress, chainId }: {
  userAddress: string;
  chainId: number;
}) {
  const [rewards, setRewards] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getUserAllClaimableRewards(userAddress, chainId)
      .then(setRewards)
      .finally(() => setLoading(false));
  }, [userAddress, chainId]);

  if (loading) return <div>Loading rewards...</div>;
  if (!rewards || rewards.merkl.length === 0) {
    return <div>No claimable rewards</div>;
  }

  return (
    <div className="user-rewards">
      <h3>Your Claimable Rewards</h3>

      {rewards.merkl.map((reward) => (
        <div key={reward.token} className="reward-row">
          <span className="token">{reward.symbol}</span>
          <span className="amount">
            {formatUnits(reward.amount, reward.decimals)} {reward.symbol}
          </span>
        </div>
      ))}

      {/* Show separate counts for transparency */}
      <div className="source-breakdown">
        <small>
          Merkl: {rewards.merkl.length} rewards
        </small>
      </div>

      {/* Claim button */}
      <button onClick={() => handleClaimAll(userAddress, chainId)}>
        Claim All Rewards
      </button>
    </div>
  );
}
```

## [Displaying Rewards in Tables](#displaying-rewards-in-tables)

For portfolio or dashboard views:

```
function VaultPortfolio({ userAddress, chainId }: {
  userAddress: string;
  chainId: number;
}) {
  const [vaults, setVaults] = useState<any[]>([]);

  return (
    <table>
      <thead>
        <tr>
          <th>Vault</th>
          <th>Your Deposit</th>
          <th>Base APY</th>
          <th>Rewards APR</th>
          <th>Total APY</th>
          <th>Claimable</th>
        </tr>
      </thead>
      <tbody>
        {vaults.map((vault) => (
          <tr key={vault.address}>
            <td>{vault.name}</td>
            <td>
              {vault.userDeposit} {vault.asset.symbol}
            </td>
            <td>{vault.baseApy.toFixed(2)}%</td>
            <td className="rewards-apr">
              +{vault.rewardsApr.toFixed(2)}%
            </td>
            <td className="total-apy">
              <strong>{vault.totalApy.toFixed(2)}%</strong>
            </td>
            <td>
              {vault.claimable > 0 ? (
                <button>Claim</button>
              ) : (
                <span>-</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

## [Showing Reward Program Details](#showing-reward-program-details)

Provide transparency about active programs:

```
function RewardProgramsCard({ vaultAddress, chainId }) {
  const [programs, setPrograms] = useState<any[]>([]);

  // Fetch active programs for this vault
  useEffect(() => {
    fetchActivePrograms(vaultAddress, chainId).then(setPrograms);
  }, [vaultAddress, chainId]);

  return (
    <div className="reward-programs">
      <h4>Active Reward Programs</h4>

      {programs.map((program) => (
        <div key={program.id} className="program-card">
          <div className="header">
            <img src={program.tokenIcon} alt={program.token} />
            <span>{program.token} Rewards</span>
          </div>

          <div className="details">
            <div>APR: {program.apr.toFixed(2)}%</div>
            <div>Ends: {formatDate(program.endDate)}</div>
            <div>Source: Merkl</div>
          </div>
        </div>
      ))}
    </div>
  );
}
```

## [Real-Time Updates](#real-time-updates)

### [Polling for Updates](#polling-for-updates)

```
function useRewardsPolling(userAddress: string, chainId: number) {
  const [rewards, setRewards] = useState<any>(null);

  useEffect(() => {
    const fetchRewards = () => {
      getUserAllClaimableRewards(userAddress, chainId).then(setRewards);
    };

    // Initial fetch
    fetchRewards();

    // Poll every 5 minutes for Merkl updates
    const interval = setInterval(fetchRewards, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [userAddress, chainId]);

  return rewards;
}
```

### [Showing Accruing Rewards](#showing-accruing-rewards)

For a more dynamic experience:

```
function AccruingRewardsDisplay({ baseAmount, ratePerSecond }) {
  const [accrued, setAccrued] = useState(baseAmount);

  useEffect(() => {
    const interval = setInterval(() => {
      setAccrued((prev) => prev + ratePerSecond);
    }, 1000);

    return () => clearInterval(interval);
  }, [ratePerSecond]);

  return (
    <div className="accruing-rewards">
      <span>Accruing: </span>
      <span className="animated-number">
        {accrued.toFixed(6)} MORPHO
      </span>
    </div>
  );
}
```

## [Handling Edge Cases](#handling-edge-cases)

### [No Rewards Available](#no-rewards-available)

```
{rewards.length === 0 ? (
  <div className="no-rewards">
    <p>No active reward programs for this vault</p>
    <p>Check back later or explore other vaults</p>
  </div>
) : (
  <RewardsList rewards={rewards} />
)}
```

### [Failed to Fetch Rewards](#failed-to-fetch-rewards)

```
{error ? (
  <div className="error-state">
    <p>Unable to load rewards data</p>
    <button onClick={retry}>Retry</button>
  </div>
) : (
  <RewardsDisplay />
)}
```

### [Dust Amounts](#dust-amounts)

Don't show tiny amounts that aren't worth claiming:

```
const DUST_THRESHOLD = 0.01; // $0.01 USD

function filterDust(rewards: any[], tokenPrices: Record<string, number>) {
  return rewards.filter((reward) => {
    const usdValue =
      parseFloat(formatUnits(reward.amount, 18)) * tokenPrices[reward.token];
    return usdValue > DUST_THRESHOLD;
  });
}
```

## [Accessibility Considerations](#accessibility-considerations)

- **Use semantic HTML**: `<table>` for tabular data, `<button>` for actions
- **Provide labels**: Screen readers should understand what APY/APR values mean
- **Keyboard navigation**: Ensure all interactive elements are keyboard-accessible
- **Loading states**: Clear indication when data is loading

```
<div role="status" aria-live="polite">
  {loading ? "Loading rewards..." : `${rewards.length} rewards available`}
</div>
```

## [Resources](#resources)

- **Morpho API Playground**: [api.morpho.org/graphql](https://api.morpho.org/graphql)
- **Design Inspiration**: [app.morpho.org](https://app.morpho.org)

## [Next Steps](#next-steps)

- **Implement claiming**: [Claim Rewards tutorial](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/)

[Claim Rewards

Previous Page

](https://docs.morpho.org/developers/rewards/tutorials/claim-rewards/)[Resources

Next Page

](https://docs.morpho.org/developers/rewards/resources/all/)