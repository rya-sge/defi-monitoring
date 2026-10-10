# Get Data

> Source: https://docs.morpho.org/developers/earn/tutorials/get-data

---

# Get Data

## [Before Starting](#before-starting)

In this tutorial, you might see different ways to fetch data for Morpho Vaults:

- **API**: Using the Morpho public API (see endpoint below). This is the easiest and most direct way for most applications. Note that only a subset of chains are supported.
- **Typescript**: Using Typescript snippet. For Developers expecting to perform offchain computation.
- **Smart Contract**: Fetching data directly onchain. This is best for real-time or trustless data.
- **SDK**: [Examples Incoming] Using the Morpho SDKs for pre-built abstractions and faster development.

API Endpoint: [api.morpho.org/graphql](https://api.morpho.org/graphql)

Review the [Morpho API main rules](https://docs.morpho.org/developers/api/get-started/#morpho-api-main-rules) before sending requests. By default, the API returns only the first 100 results and targets the Ethereum network unless you specify otherwise.

For each topic below, you'll find short guides for each method (where possible). This avoids redundancy and helps you choose the best approach for your use case.

## [Discovery and Listing](#discovery-and-listing)

### [Vaults List](#vaults-list)

#### [Morpho Vaults V2](#morpho-vaults-v2)

APITypescript - ViemSmart Contract EventAPI
```
query {
  vaultV2s(first: 1000, where: { chainId_in: [1, 8453] }) {
    items {
      address
      symbol
      name
      listed
      asset {
        id
        address
        decimals
      }
      chain {
        id
        network
      }
    }
  }
}
```

```
import "dotenv/config";
import { createPublicClient, http, PublicClient, parseAbiItem } from "viem";
import { mainnet } from "viem/chains";

export async function createMainnetClient(): Promise<PublicClient> {
  const client = createPublicClient({
    chain: mainnet,
    transport: http(process.env.RPC_URL_MAINNET!, {
      retryCount: 2,
      batch: {
        batchSize: 100,
        wait: 200,
      },
    }),
    batch: {
      multicall: {
        batchSize: 2048,
        wait: 100,
      },
    },
  });
  
  return client;
}

// Morpho Vault V2 Factory contract address
const MORPHO_VAULT_V2_FACTORY_ADDRESS = "0xA1D94F746dEfa1928926b84fB2596c06926C0405";

// Block range to search for vault creations
const START_BLOCK = 23716940n;
const END_BLOCK = 23717000n;

// CreateVaultV2 event ABI
const CREATE_VAULT_V2_EVENT = parseAbiItem(
  "event CreateVaultV2(address indexed owner, address indexed asset, bytes32 salt, address indexed newVaultV2)"
);

interface VaultV2CreationEvent {
  newVaultV2: string;
  owner: string;
  asset: string;
  salt: string;
  blockNumber: bigint;
  transactionHash: string;
}

export async function fetchNewVaultV2Creations(
  client: PublicClient,
  startBlock: bigint = START_BLOCK,
  endBlock: bigint = END_BLOCK
): Promise<VaultV2CreationEvent[]> {
  console.log(`Fetching Vault V2 creations from block ${startBlock} to ${endBlock}...`);

  // Get logs for CreateVaultV2 events
  const logs = await client.getLogs({
    address: MORPHO_VAULT_V2_FACTORY_ADDRESS,
    event: CREATE_VAULT_V2_EVENT,
    fromBlock: startBlock,
    toBlock: endBlock,
  });

  console.log(`Found ${logs.length} Vault V2 creation(s)`);

  // Parse and format the logs
  const vaultCreations: VaultV2CreationEvent[] = logs.map((log) => ({
    newVaultV2: log.args.newVaultV2!,
    owner: log.args.owner!,
    asset: log.args.asset!,
    salt: log.args.salt!,
    blockNumber: log.blockNumber!,
    transactionHash: log.transactionHash!,
  }));

  return vaultCreations;
}

export function displayVaultV2Creations(vaultCreations: VaultV2CreationEvent[]): void {
  if (vaultCreations.length === 0) {
    console.log("No new Vault V2s were created in the specified block range.");
    return;
  }

  console.log("\n=== New MetaMorpho Vault V2s Created ===");
  vaultCreations.forEach((vault, index) => {
    console.log(`\n${index + 1}. Vault V2 Address: ${vault.newVaultV2}`);
    console.log(`   Owner: ${vault.owner}`);
    console.log(`   Asset: ${vault.asset}`);
    console.log(`   Salt: ${vault.salt}`);
    console.log(`   Block: ${vault.blockNumber}`);
    console.log(`   Transaction: ${vault.transactionHash}`);
  });
}

export async function main(): Promise<void> {
  try {
    const client = await createMainnetClient();

    // Fetch Vault V2 creations in the specified block range
    const vaultCreations = await fetchNewVaultV2Creations(client, START_BLOCK, END_BLOCK);

    // Display the results
    displayVaultV2Creations(vaultCreations);

  } catch (error) {
    console.error("Error fetching Vault V2 creations:", error);
  }
}

// Run the script if executed directly
if (require.main === module) {
  main();
}
```

**Example Output:**

```
{
  "message": "Fetching Vault V2 creations from block 23716940 to 23717000...",
  "found": "Found 1 Vault V2 creation(s)",
  "vaults": [
    {
      "address": "0x5E5b30c5fD07da26d1e515dfEDb1D37C93417652",
      "owner": "0x46057881E0B9d190920FB823F840B837f65745d5",
      "asset": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "salt": "0x5dbd6b3d5444d58eb3b873a76f4a26158f4a960b67d87125ffcd305053e16a3a",
      "blockNumber": "23716959",
      "transactionHash": "0x73f2c14195c38ca887e44fed4e2bb9619a858ddea7337258d748a3079ef417f0"
    }
  ]
}
```

This example demonstrates how to:

- Listen to `CreateVaultV2` events from the Morpho Vault V2 Factory contract on Ethereum (`0xA1D94F746dEfa1928926b84fB2596c06926C0405`). Factories addresses on resp. chains supported are [here](https://docs.morpho.org/get-started/resources/addresses/).
- Filter events within a specific block range
- Extract all vault creation details from the event logs
- Parse and format the results for easy consumption

One can listen to all `CreateVaultV2` events emitted from the `MorphoVaultV2Factory` contract. The contracts addresses are [here](https://docs.morpho.org/get-started/resources/addresses/).

```
/// @notice Emitted when a new Morpho Vault V2 is created.
/// @param owner The initial owner of the vault.
/// @param asset The address of the underlying asset.
/// @param salt The salt used for the vault's CREATE2 address.
/// @param newVaultV2 The address of the newly created Vault V2.
event CreateVaultV2(
    address indexed owner,
    address indexed asset,
    bytes32 salt,
    address indexed newVaultV2
);
```

## [Vault Metrics](#vault-metrics)

### [Total Deposits & Assets](#total-deposits--assets)

#### [Morpho Vaults V2](#morpho-vaults-v2-1)

APITypescript - ViemSmart ContractEasiest to implement - perfect for most applications

Unique VaultAll Vaults
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    address
     totalAssets
      totalAssetsUsd
      totalSupply
      liquidity
      liquidityUsd
      idleAssetsUsd
  }
}
```

```
query {
  vaultV2s(first: 100) {
    items {
      address
      totalAssets
      totalAssetsUsd
      totalSupply
      liquidityUsd
      idleAssetsUsd
      }
    }
  }
```

The following example demonstrates how to:

- Connect to the Ethereum mainnet using Viem
- Fetch total deposits and assets from a Morpho Vault V2
- Calculate and display formatted vault statistics including total supply, total assets, and USD value
- Parse and format results for easy consumption

```
import "dotenv/config";
import {
  createPublicClient,
  http,
  formatUnits,
  PublicClient,
  parseAbi,
  Address,
} from "viem";
import { mainnet } from "viem/chains";

/**
 * Creates and configures a Viem Public Client for the Ethereum mainnet.
 * It reads the RPC URL from the .env file.
 * @returns {PublicClient} A configured Viem public client.
 */
export function createMainnetClient(): PublicClient {
  const rpcUrl = process.env.RPC_URL_MAINNET;
  if (!rpcUrl) {
    throw new Error(
      "RPC_URL_MAINNET is not set in the .env file. Please add it."
    );
  }

  return createPublicClient({
    chain: mainnet,
    transport: http(rpcUrl, {
      retryCount: 2,
      batch: {
        batchSize: 100,
        wait: 200,
      },
    }),
    batch: {
      multicall: {
        batchSize: 2048,
        wait: 100,
      },
    },
  });
}

// The address of the Morpho Vault V2
const VAULT_ADDRESS: Address = "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145";

// Minimal ABI for an ERC-4626 compliant vault to get total assets, supply, and the underlying asset.
// Vault V2 is ERC-4626 compliant and supports these standard functions.
const MINIMAL_VAULT_ABI = parseAbi([
  "function totalAssets() external view returns (uint256)",
  "function totalSupply() external view returns (uint256)",
  "function asset() external view returns (address)",
]);

// Minimal ABI for an ERC-20 token to get its decimals.
const MINIMAL_ERC20_ABI = parseAbi([
  "function decimals() external view returns (uint8)",
]);

interface VaultStats {
  vaultAddress: Address;
  totalSupply: bigint;
  totalAssets: bigint;
  totalAssetsUsd: number;
  assetAddress: Address;
  assetDecimals: number;
}

/**
 * Fetches the key statistics for a given Morpho vault.
 * @param {PublicClient} client - The Viem public client.
 * @param {Address} vaultAddress - The address of the vault to query.
 * @returns {Promise<VaultStats>} An object containing the vault's stats.
 */
export async function getVaultStats(
  client: PublicClient,
  vaultAddress: Address
): Promise<VaultStats> {
  console.log(`Fetching stats for vault: ${vaultAddress}...`);

  // Use multicall to fetch vault data in a single RPC request for efficiency
  const [totalSupply, totalAssets, assetAddress] = await client.multicall({
    contracts: [
      {
        address: vaultAddress,
        abi: MINIMAL_VAULT_ABI,
        functionName: "totalSupply",
      },
      {
        address: vaultAddress,
        abi: MINIMAL_VAULT_ABI,
        functionName: "totalAssets",
      },
      {
        address: vaultAddress,
        abi: MINIMAL_VAULT_ABI,
        functionName: "asset",
      },
    ],
    allowFailure: false,
  });

  // Fetch the decimals of the underlying asset (in this case, USDC)
  const assetDecimals = await client.readContract({
    address: assetAddress,
    abi: MINIMAL_ERC20_ABI,
    functionName: "decimals",
  });

  // --- USD CONVERSION ---
  // For this script, we use a manual price for the underlying asset (USDC).
  // In a production environment, you should replace this with a dynamic price feed.
  //
  // HOW TO GET A DYNAMIC PRICE:
  // 1. Use an onchain oracle (e.g., Chainlink) if your script runs in a smart contract context.
  // 2. Use the Morpho API's `assetByAddress` query to get `price { usd }`.
  //    Read `price.timestamp` too if freshness matters.
  // 3. Use a third-party price API like DefiLlama, CoinGecko, or a paid service.
  //
  // Since the underlying asset is USDC, its price is pegged to ~$1.00.
  const underlyingAssetPriceUsd = 1.0;

  // Format the totalAssets value from a BigInt to a floating-point number
  const totalAssetsFormatted = parseFloat(
    formatUnits(totalAssets, assetDecimals)
  );

  // Calculate the total value in USD
  const totalAssetsUsd = totalAssetsFormatted * underlyingAssetPriceUsd;

  return {
    vaultAddress,
    totalSupply,
    totalAssets,
    totalAssetsUsd,
    assetAddress,
    assetDecimals,
  };
}

/**
 * Displays the fetched vault statistics in a clean, readable format.
 * @param {VaultStats} stats - The vault statistics object.
 */
export function displayVaultStats(stats: VaultStats): void {
  console.log("\n✅ --- Morpho Vault Stats --- ✅");
  console.log(`\nVault Address: ${stats.vaultAddress}`);
  console.log(`Underlying Asset: ${stats.assetAddress}`);

  // The vault's shares (totalSupply) are typically 18 decimals, regardless of the underlying asset's decimals.
  const totalSupplyFormatted = formatUnits(stats.totalSupply, 18);
  const totalAssetsFormatted = formatUnits(stats.totalAssets, stats.assetDecimals);

  console.log("\n--- Totals ---");
  console.log(
    `Total Supply (Shares): ${totalSupplyFormatted} (raw: ${stats.totalSupply})`
  );
  console.log(
    `Total Assets (${stats.assetDecimals} decimals): ${totalAssetsFormatted} (raw: ${stats.totalAssets})`
  );
  console.log(
    `Total Assets (USD):      $${stats.totalAssetsUsd.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`
  );
  console.log("\n---------------------------------");
}

/**
 * Main function to run the script.
 */
export async function main(): Promise<void> {
  try {
    const client = createMainnetClient();
    const vaultStats = await getVaultStats(client, VAULT_ADDRESS);
    displayVaultStats(vaultStats);
  } catch (error) {
    console.error("An error occurred during script execution:", error);
    process.exit(1);
  }
}

// Run the script if executed directly
if (require.main === module) {
  main();
}
```

**Example Output:**

```
Fetching stats for vault: 0x04422053aDDbc9bB2759b248B574e3FCA76Bc145...

✅ --- Morpho Vault Stats --- ✅

Vault Address: 0x04422053aDDbc9bB2759b248B574e3FCA76Bc145
Underlying Asset: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48

--- Totals ---
Total Supply (Shares): 406046.668299445014491638 (raw: 406046668299445014491638)
Total Assets (6 decimals): 409312.044166 (raw: 409312044166)
Total Assets (USD):      $409,312.04

---------------------------------
```

As it is important to accrue interests on the underlying adapters and markets, consider using the full implementation in the [Morpho Vault V2 Snippets](https://github.com/morpho-org/vault-v2/blob/main/README.md) repository for production use.

Raw Contract Calls
```
/// @notice Returns the total assets deposited into a VaultV2 `vault`.
    /// @dev This includes both idle assets in the vault and assets allocated to adapters.
    /// @dev The value is computed by accruing interest and aggregating adapter positions.
    /// @param vault The address of the VaultV2 vault.
    /// @return totalAssets The total assets controlled by the vault.
    function totalDepositVaultV2(address vault) public view returns (uint256 totalAssets) {
        totalAssets = IVaultV2(vault).totalAssets();
    }
```

### [APY (Native + Rewards)](#apy-native--rewards)

#### [Morpho Vaults V2](#morpho-vaults-v2-2)

API
###### [Morpho Vaults V2 can be eligible for 2 levels of rewards:](#morpho-vaults-v2-can-be-eligible-for-2-levels-of-rewards)

- **Market level rewards:** These are inherited from the underlying Morpho markets where the Morpho Vault V2 allocates assets.
- **Vault level rewards:** These are distributed directly to the Morpho Vault V2 itself.

Note for Morpho Vault V2: all rewards appearing on the Morpho API are displayed directly under the `rewards` section.

###### [APY Components Breakdown:](#apy-components-breakdown)

1. **Native APY:** The base yield earned from the vault's underlying allocations.
2. **Underlying Token Yield:** The yield generated by the underlying token itself (when applicable). For yield-bearing loan assets, this is calculated using daily exchange rate changes queried at 1-day block intervals. Access this via `asset.yield.apr`.
3. **Reward APRs:** Additional incentives visible directly through `rewards`.
4. **Performance Fee Adjustment:** The performance fee is applied only to the Native APY component.
5. **Management Fee Adjustment:** A time-based fee (annual rate, if applicable) deducted from the total assets regardless of performance.

The combination of these components results in the Net APY:

Net APY=Native APY×(1−Performance Fee)+Underlying Token Yield\text{Net APY}= \text{Native APY} \times (1 - \text{Performance Fee}) + \text{Underlying Token Yield}
Net APY=Native APY×(1−Performance Fee)+Underlying Token YieldNet APY=+∑Rewards APR−Management Fee\phantom{\text{Net APY} =} + \sum \text{Rewards APR} - \text{Management Fee}Net APY=+∑Rewards APR−Management FeeWhere:

- Performance Fee is applied **only** to Native APY (as a percentage)
- Management Fee is applied to total assets (as an annual rate)
- Underlying Token Yield applies only to yield-bearing assets (0 otherwise)
- Rewards APR is the sum of all reward incentives

###### [Important UI Reference one might find on apps:](#important-ui-reference-one-might-find-on-apps)

1. `avgNetApyExcludingRewards` represents the native APY (6h average vault APY excluding rewards, before deducting fees).
2. `avgNetApy` represents the complete APY (6h average vault APY including rewards, after deducting fees).

Unique VaultAll Vaults
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    address
    asset {
      yield {
        apr
      }
    }
    avgNetApyExcludingRewards
    avgNetApy
    performanceFee
    managementFee
    maxRate
    rewards {
      asset {
        address
        chain {
          id
        }
      }
      supplyApr
    }
  }
}
```

```
query {
  vaultV2s(first: 10) {
    items {
      address
      asset {
        yield {
          apr
        }
      }
      avgNetApyExcludingRewards
      avgNetApy
      performanceFee
      managementFee
      maxRate
      rewards {
        asset {
          address
          chain {
            id
          }
        }
        supplyApr
      }
    }
  }
}
```

### [Share Price (Token Value)](#share-price-token-value)

**Why You Shouldn't Calculate Manually**

Computing the exchange rate as `totalAssets / totalSupply` can show false "drops" during fee accruals. This happens because these values update at different times, creating temporary inconsistencies.

**How ERC-4626 Calculates Share Price**

The standard includes **virtual offsets** to prevent inflation attacks and ensure consistency:

- **Virtual Assets**: `+1` added to totalAssets
- **Virtual Shares**: `+10^DECIMALS_OFFSET` added to totalSupply

  - DECIMALS_OFFSET matches the underlying asset decimals (6 for USDC, 18 for WETH)

**Formula** for pricing 1 share (10^18 wei):

sharePrice=1018×(totalAssets+1)totalSupply+10DECIMALS_OFFSET\text{sharePrice} = \frac{10^{18} \times (\text{totalAssets} + 1)}{\text{totalSupply} + 10^{\text{DECIMALS\_OFFSET}}}sharePrice=totalSupply+10DECIMALS_OFFSET1018×(totalAssets+1)​The result is in raw underlying asset units. To get the human-readable price, divide by `10^assetDecimals`.

**Recommended Methods:**

- **API**: Use the `sharePrice` field (already computed correctly)
- **Onchain**: Use `convertToAssets(10^18)` instead of manual calculation

**Practical Example with USDC Vault**

Using real data from a USDC vault (6 decimals):

totalAssets: 473,435,155,471,028 (raw USDC units)\text{totalAssets: } 473{,}435{,}155{,}471{,}028 \text{ (raw USDC units)}totalAssets: 473,435,155,471,028 (raw USDC units)totalSupply: 427,784,657,006,652,956,819,706,379 (raw share units)\text{totalSupply: } 427{,}784{,}657{,}006{,}652{,}956{,}819{,}706{,}379 \text{ (raw share units)}totalSupply: 427,784,657,006,652,956,819,706,379 (raw share units)Applying the formula:

sharePrice=1018×473,435,155,471,029427,784,657,006,652,956,819,706,379+106=1,106,713 (raw units)\text{sharePrice} = \frac{10^{18} \times 473{,}435{,}155{,}471{,}029}{427{,}784{,}657{,}006{,}652{,}956{,}819{,}706{,}379 + 10^6} = 1{,}106{,}713 \text{ (raw units)}sharePrice=427,784,657,006,652,956,819,706,379+1061018×473,435,155,471,029​=1,106,713 (raw units)Converting to human-readable:

1,106,713106=1.106713 USDC per share\frac{1{,}106{,}713}{10^6} = 1.106713 \text{ USDC per share}1061,106,713​=1.106713 USDC per shareThis matches the API's `sharePrice` field value!

#### [Morpho Vaults V2](#morpho-vaults-v2-3)

APITypescript - ViemSmart ContractUnique VaultAll Vaults
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    totalAssets
    totalSupply
    sharePrice
  }
}
```

```
query {
  vaultV2s(first: 10) {
    items {
      address
      totalSupply
      totalAssets
      sharePrice
    }
  }
}
```

This example demonstrates how to price a Morpho Vault V2 token using the standard ERC-4626 methodology. Since vault tokens represent a share of the underlying assets, their price appreciates as the vault accrues yield.

The script shows how to:

- Connect to Ethereum mainnet using Viem.
- Use the `convertToAssets` function to determine how many underlying assets correspond to one full vault share token.
- Fetch vault and underlying asset details (symbols, decimals) using `multicall` for efficiency.
- Format the raw price into a human-readable string (e.g., "1.008 USDC").
- Calculate the USD value of the vault token.

```
import "dotenv/config";
import {
  createPublicClient,
  http,
  formatUnits,
  PublicClient,
  parseAbi,
  Address,
} from "viem";
import { mainnet } from "viem/chains";

/**
 * Creates and configures a Viem Public Client for the Ethereum mainnet.
 * @returns A configured Viem public client.
 */
export function createMainnetClient(): PublicClient {
  const rpcUrl = process.env.RPC_URL_MAINNET;
  if (!rpcUrl) {
    throw new Error(
      "RPC_URL_MAINNET is not set in the .env file. Please add it."
    );
  }

  return createPublicClient({
    chain: mainnet,
    transport: http(rpcUrl, {
      retryCount: 2,
      batch: {
        batchSize: 100,
        wait: 200,
      },
    }),
    batch: {
      multicall: {
        batchSize: 2048,
        wait: 100,
      },
    },
  });
}

// The address of the Morpho Vault V2
const VAULT_V2_ADDRESS: Address = "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145";

// Minimal ABIs for an ERC-4626 vault and an ERC-20 token.
// Vault V2 is ERC-4626 compliant and supports these standard functions.
const VAULT_V2_ABI = parseAbi([
  "function convertToAssets(uint256 shares) view returns (uint256 assets)",
  "function totalAssets() view returns (uint256)",
  "function totalSupply() view returns (uint256)",
  "function asset() view returns (address)",
  "function symbol() view returns (string)",
]);

const ERC20_ABI = parseAbi([
  "function decimals() view returns (uint8)",
  "function symbol() view returns (string)",
]);

interface VaultPriceInfo {
  vaultAddress: Address;
  vaultSymbol: string;
  sharePriceInAssets: bigint; // Raw value from convertToAssets
  underlyingAsset: {
    address: Address;
    symbol: string;
    decimals: number;
  };
  formattedPrice: string; // e.g., "1.026 USDC"
  usdPrice: number;
}

/**
 * Calculates the price of a single vault share in terms of its underlying asset.
 * This function demonstrates the standard ERC-4626 method for pricing shares.
 * @param client The Viem public client.
 * @param vaultAddress The address of the Morpho Vault V2.
 * @returns A promise that resolves to a VaultPriceInfo object.
 */
export async function calculateVaultTokenPrice(
  client: PublicClient,
  vaultAddress: Address
): Promise<VaultPriceInfo> {
  console.log(`Calculating token price for vault: ${vaultAddress}...`);

  // A single vault share token has 18 decimals.
  const oneShare = 10n ** 18n;

  // Use multicall to fetch vault and underlying asset data efficiently.
  const [
    assetsPerShare,
    underlyingAssetAddress,
    vaultSymbol,
    totalSupply,
    totalAssets,
  ] = await client.multicall({
    contracts: [
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "convertToAssets",
        args: [oneShare],
      },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "asset",
      },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "symbol",
      },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "totalSupply",
      },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "totalAssets",
      },
    ],
    allowFailure: false,
  });

  // Fetch details of the underlying asset (e.g., USDC).
  const [underlyingDecimals, underlyingSymbol] = await client.multicall({
    contracts: [
      {
        address: underlyingAssetAddress,
        abi: ERC20_ABI,
        functionName: "decimals",
      },
      {
        address: underlyingAssetAddress,
        abi: ERC20_ABI,
        functionName: "symbol",
      },
    ],
    allowFailure: false,
  });

  // For USD conversion, a dynamic price feed is recommended.
  // For this example with USDC, we can hardcode the price as ~$1.0.
  const underlyingAssetPriceUsd = 1.0;
  const formattedAssetsPerShare = formatUnits(
    assetsPerShare,
    underlyingDecimals
  );
  const usdPrice = parseFloat(formattedAssetsPerShare) * underlyingAssetPriceUsd;

  return {
    vaultAddress,
    vaultSymbol,
    sharePriceInAssets: assetsPerShare,
    underlyingAsset: {
      address: underlyingAssetAddress,
      symbol: underlyingSymbol,
      decimals: underlyingDecimals,
    },
    formattedPrice: `${formattedAssetsPerShare} ${underlyingSymbol}`,
    usdPrice,
  };
}

/**
 * Displays the calculated vault token price information in a clean format.
 * @param priceInfo The object containing the price information.
 */
export function displayVaultTokenPrice(priceInfo: VaultPriceInfo): void {
  console.log("\n✅ --- Morpho Vault V2 Token Price --- ✅");
  console.log(`\nVault: ${priceInfo.vaultSymbol} (${priceInfo.vaultAddress})`);
  console.log(
    `Underlying Asset: ${priceInfo.underlyingAsset.symbol} (${priceInfo.underlyingAsset.address})`
  );

  console.log("\n--- Price ---");
  console.log(`1 ${priceInfo.vaultSymbol} = ${priceInfo.formattedPrice}`);
  console.log(
    `Price (raw units): ${
      priceInfo.sharePriceInAssets
    } (with ${priceInfo.underlyingAsset.decimals} decimals)`
  );
  console.log(
    `Price (USD): $${priceInfo.usdPrice.toLocaleString("en-US", {
      minimumFractionDigits: 4,
      maximumFractionDigits: 4,
    })}`
  );
  console.log("\n----------------------------------------");
}

/**
 * Main function to orchestrate the script execution.
 */
export async function main(): Promise<void> {
  try {
    const client = createMainnetClient();
    const priceInfo = await calculateVaultTokenPrice(client, VAULT_V2_ADDRESS);
    displayVaultTokenPrice(priceInfo);
  } catch (error) {
    console.error("An error occurred during script execution:", error);
    process.exit(1);
  }
}

// Run the script if executed directly
if (require.main === module) {
  main();
}
```

**Example Output:**

```
Calculating token price for vault: 0x04422053aDDbc9bB2759b248B574e3FCA76Bc145...

--- Morpho Vault V2 Token Price ---

Vault: kUSDC (0x04422053aDDbc9bB2759b248B574e3FCA76Bc145)
Underlying Asset: USDC (0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)

--- Price ---
1 kUSDC = 1.008451 USDC
Price (raw units): 1008451 (with 6 decimals)
Price (USD): $1.0085

----------------------------------------
```

```
// Get the price of 1 vault token in underlying asset units
// Works for Morpho Vault V2 (ERC-4626 compliant)
uint256 oneShare = 10**IERC20Metadata(vault).decimals();
uint256 priceInAssets = IERC4626(vault).convertToAssets(oneShare);

// Alternative: Calculate manually using total supply and total assets
uint256 totalSupply = IERC20(vault).totalSupply();
uint256 totalAssets = IERC4626(vault).totalAssets();
uint256 priceManual = (totalAssets * oneShare) / totalSupply;

// Both methods return the same result:
// Price = how many underlying assets 1 vault token is worth
```

**Key Functions:**

- `convertToAssets(shares)`: ERC-4626 standard function that converts vault shares to underlying assets
- `totalAssets()`: Total underlying assets managed by the vault
- `totalSupply()`: Total vault tokens in circulation

**Price Formula:** `Price = totalAssets / totalSupply`

The `convertToAssets` approach is recommended as it handles edge cases and follows the ERC-4626 standard.

## [Allocation & Strategy](#allocation--strategy)

### [Current Allocations](#current-allocations)

#### [Morpho Vaults V2](#morpho-vaults-v2-4)

**Vaults V2 allocate through adapters, not directly to markets.** Each adapter reports its current holdings via `realAssets()`, and the vault aggregates these values to calculate total allocations. Vaults V2 can allocate to Morpho markets and any future approved protocol with an enabled adapter.

APITypescript - ViemUnique VaultAll Vaults
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    address
    totalAssetsUsd
    totalAssets
    totalSupply
    idleAssets
    idleAssetsUsd
    adapters(first: 20) {
      items {
        __typename
        address
        assets
        assetsUsd
        type
        ... on MorphoMarketV1Adapter {
          positions(first: 50) {
            items {
              market {
                marketId
                collateralAsset {
                  symbol
                }
                loanAsset {
                  symbol
                }
              }
              state {
                supplyAssets
                supplyAssetsUsd
              }
            }
          }
        }
        ... on MetaMorphoAdapter {
          metaMorpho {
            address
            name
            asset {
              symbol
            }
          }
        }
        ... on MorphoVaultV2Adapter {
          innerVault {
            address
            name
            asset {
              symbol
            }
          }
        }
      }
    }
  }
}
```

```
query {
  vaultV2s(first: 10) {
    items {
      address
      totalAssetsUsd
      totalAssets
      totalSupply
      idleAssets
      idleAssetsUsd
      adapters(first: 5) {
        items {
          __typename
          address
          assets
          assetsUsd
          type
          ... on MorphoMarketV1Adapter {
            positions(first: 10) {
              items {
                market {
                  marketId
                  collateralAsset {
                    symbol
                  }
                  loanAsset {
                    symbol
                  }
                }
                state {
                  supplyAssets
                  supplyAssetsUsd
                }
              }
            }
          }
          ... on MetaMorphoAdapter {
            metaMorpho {
              address
              name
              asset {
                symbol
              }
            }
          }
          ... on MorphoVaultV2Adapter {
            innerVault {
              address
              name
              asset {
                symbol
              }
            }
          }
        }
      }
    }
  }
}
```

This example demonstrates how to:

- Fetch all adapters from the Vault V2 and detect their types
- Retrieve allocations from each adapter
- Calculate idle assets held directly by the vault
- Determine allocation amounts and percentages across all destinations
- Display formatted allocation results with adapter breakdown
- Use multicall for efficient batch operations

```
import "dotenv/config";
import {
  createPublicClient,
  http,
  formatUnits,
  PublicClient,
  parseAbi,
  Address,
  keccak256,
  encodeAbiParameters,
} from "viem";
import { mainnet } from "viem/chains";

/**
 * Creates and configures a Viem Public Client for the Ethereum mainnet.
 * It reads the RPC URL from the .env file.
 * @returns A configured Viem public client.
 */
export function createMainnetClient(): PublicClient {
  const rpcUrl = process.env.RPC_URL_MAINNET;
  if (!rpcUrl) {
    throw new Error(
      "RPC_URL_MAINNET is not set in the .env file. Please add it."
    );
  }

  return createPublicClient({
    chain: mainnet,
    transport: http(rpcUrl, { retryCount: 2 }),
  });
}

const VAULT_V2_ADDRESS: Address = "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145";
const MORPHO_BLUE_ADDRESS: Address =
  "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb";

// Minimal ABIs with only the functions we need for this script.
const VAULT_V2_ABI = parseAbi([
  "function adaptersLength() external view returns (uint256)",
  "function adapters(uint256) external view returns (address)",
  "function asset() external view returns (address)",
  "function totalAssets() external view returns (uint256)",
]);

const ADAPTER_ABI = parseAbi([
  "function realAssets() external view returns (uint256)",
  "function morpho() external view returns (address)",
  "function morphoVaultV1() external view returns (address)",
  "function marketParamsListLength() external view returns (uint256)",
  "function marketParamsList(uint256) external view returns (address loanToken, address collateralToken, address oracle, address irm, uint256 lltv)",
]);

const MORPHO_BLUE_ABI = parseAbi([
  "function market(bytes32 id) external view returns (uint128 totalSupplyAssets, uint128 totalSupplyShares, uint128 totalBorrowAssets, uint128 totalBorrowShares, uint128 lastUpdate, uint128 fee)",
  "function idToMarketParams(bytes32 id) external view returns (address loanToken, address collateralToken, address oracle, address irm, uint256 lltv)",
  "function position(bytes32 id, address user) external view returns (uint256 supplyShares, uint128 borrowShares, uint128 collateral)",
]);

const IRM_ABI = parseAbi([
  "function borrowRateView((address loanToken, address collateralToken, address oracle, address irm, uint256 lltv) marketParams, (uint128 totalSupplyAssets, uint128 totalSupplyShares, uint128 totalBorrowAssets, uint128 totalBorrowShares, uint128 lastUpdate, uint128 fee) market) external view returns (uint256)",
]);

const MINIMAL_ERC20_ABI = parseAbi([
  "function decimals() view returns (uint8)",
  "function balanceOf(address) view returns (uint256)",
]);

const MORPHO_VAULT_V1_ABI = parseAbi([
  "function asset() external view returns (address)",
  "function balanceOf(address) external view returns (uint256)",
  "function convertToAssets(uint256) external view returns (uint256)",
]);

type MarketParams = {
  loanToken: Address;
  collateralToken: Address;
  oracle: Address;
  irm: Address;
  lltv: bigint;
};

type MarketState = {
  totalSupplyAssets: bigint;
  totalSupplyShares: bigint;
  totalBorrowAssets: bigint;
  totalBorrowShares: bigint;
  lastUpdate: bigint;
  fee: bigint;
};

enum AdapterType {
  MorphoMarketV1 = "MorphoMarketV1Adapter",
  MorphoVaultV1 = "MorphoVaultV1Adapter",
  Unknown = "Unknown"
}

interface AllocationDestination {
  type: "Market" | "Vault" | "Idle";
  id?: `0x${string}`; // Market ID for markets
  address?: Address; // Vault address for vaults
  allocatedAssets: bigint;
  percentage: number;
}

interface AdapterAllocation {
  adapterAddress: Address;
  adapterType: AdapterType;
  destinations: AllocationDestination[];
  totalAssets: bigint;
}

interface VaultV2Allocations {
  idle: AllocationDestination;
  adapters: AdapterAllocation[];
  totalAllocated: bigint;
}

const WAD = 10n ** 18n;
const VIRTUAL_ASSETS = 1n; // To avoid division by zero
const VIRTUAL_SHARES = 10n ** 6n; // To avoid division by zero

const wMulDown = (x: bigint, y: bigint): bigint => (x * y) / WAD;
const wTaylorCompounded = (x: bigint, n: bigint): bigint => {
  const firstTerm = x * n;
  const secondTerm = (firstTerm * firstTerm) / (2n * WAD);
  const thirdTerm = (secondTerm * firstTerm) / (3n * WAD);
  return firstTerm + secondTerm + thirdTerm;
};

/** Converts a share amount to its corresponding asset amount, rounding down. */
const toAssetsDown = (shares: bigint, totalAssets: bigint, totalShares: bigint): bigint => {
  if (totalShares === 0n) return shares;
  return (shares * (totalAssets + VIRTUAL_ASSETS)) / (totalShares + VIRTUAL_SHARES);
};

/** Detects the adapter type by trying to call specific functions */
async function detectAdapterType(client: PublicClient, adapterAddress: Address): Promise<AdapterType> {
  try {
    // Try to call morphoVaultV1() - if it succeeds, it's a MorphoVaultV1Adapter
    await client.readContract({
      address: adapterAddress,
      abi: ADAPTER_ABI,
      functionName: "morphoVaultV1",
    });
    return AdapterType.MorphoVaultV1;
  } catch {
    try {
      // Try to call morpho() - if it succeeds, it's a MorphoMarketV1AdapterV2
      await client.readContract({
        address: adapterAddress,
        abi: ADAPTER_ABI,
        functionName: "morpho",
      });
      return AdapterType.MorphoMarketV1;
    } catch {
      return AdapterType.Unknown;
    }
  }
}

/** Fetches allocations from a MorphoMarketV1AdapterV2 */
async function getMarketAdapterAllocations(
  client: PublicClient,
  adapterAddress: Address,
  blockTimestamp: bigint
): Promise<AllocationDestination[]> {
  const marketListLength = await client.readContract({
    address: adapterAddress,
    abi: ADAPTER_ABI,
    functionName: "marketParamsListLength",
  }) as bigint;

  if (marketListLength === 0n) {
    return [];
  }

  const calls = Array.from({ length: Number(marketListLength) }, (_, i) => ({
    address: adapterAddress,
    abi: ADAPTER_ABI,
    functionName: "marketParamsList" as const,
    args: [BigInt(i)],
  }));

  const marketParamsList = await client.multicall({ contracts: calls, allowFailure: false });

  const destinations: AllocationDestination[] = [];

  for (const marketParamsResult of marketParamsList) {
    const params: MarketParams = {
      loanToken: marketParamsResult[0],
      collateralToken: marketParamsResult[1],
      oracle: marketParamsResult[2],
      irm: marketParamsResult[3],
      lltv: marketParamsResult[4],
    };

    // Calculate market ID
    const marketId = keccak256(
      encodeAbiParameters(
        [
          { type: "address" },
          { type: "address" },
          { type: "address" },
          { type: "address" },
          { type: "uint256" },
        ],
        [params.loanToken, params.collateralToken, params.oracle, params.irm, params.lltv]
      )
    ) as `0x${string}`;

    // Get adapter's position in this market
    const [marketState, { 0: supplyShares }] = await Promise.all([
      client.readContract({
        address: MORPHO_BLUE_ADDRESS,
        abi: MORPHO_BLUE_ABI,
        functionName: "market",
        args: [marketId],
      }),
      client.readContract({
        address: MORPHO_BLUE_ADDRESS,
        abi: MORPHO_BLUE_ABI,
        functionName: "position",
        args: [marketId, adapterAddress],
      }),
    ]);

    const allocatedAssets = toAssetsDown(
      supplyShares as bigint,
      marketState[0] as bigint,
      marketState[1] as bigint
    );

    if (allocatedAssets > 0n) {
      destinations.push({
        type: "Market",
        id: marketId,
        allocatedAssets,
        percentage: 0, // Will be calculated later
      });
    }
  }

  return destinations;
}

/** Fetches allocations from a MorphoVaultV1Adapter */
async function getVaultAdapterAllocations(
  client: PublicClient,
  adapterAddress: Address
): Promise<AllocationDestination[]> {
  const morphoVaultV1Address = await client.readContract({
    address: adapterAddress,
    abi: ADAPTER_ABI,
    functionName: "morphoVaultV1",
  }) as Address;

  // Get the adapter's balance in the Morpho Vault V1
  const shares = await client.readContract({
    address: morphoVaultV1Address,
    abi: MORPHO_VAULT_V1_ABI,
    functionName: "balanceOf",
    args: [adapterAddress],
  }) as bigint;

  // Convert shares to assets
  const allocatedAssets = await client.readContract({
    address: morphoVaultV1Address,
    abi: MORPHO_VAULT_V1_ABI,
    functionName: "convertToAssets",
    args: [shares],
  }) as bigint;

  if (allocatedAssets > 0n) {
    return [
      {
        type: "Vault",
        address: morphoVaultV1Address,
        allocatedAssets,
        percentage: 0, // Will be calculated later
      },
    ];
  }

  return [];
}

/**
 * Fetches all allocations for a Vault V2
 * @returns VaultV2Allocations object containing idle assets and adapter allocations
 */
export async function getVaultV2Allocations(
  client: PublicClient,
  vaultAddress: Address
): Promise<VaultV2Allocations> {
  // Get idle assets (vault's direct balance)
  const [underlyingAssetAddress, idleAssets, adaptersLength] = await client.multicall({
    contracts: [
      { address: vaultAddress, abi: VAULT_V2_ABI, functionName: "asset" },
      {
        address: vaultAddress,
        abi: MINIMAL_ERC20_ABI,
        functionName: "balanceOf",
        args: [vaultAddress],
      } as any,
      { address: vaultAddress, abi: VAULT_V2_ABI, functionName: "adaptersLength" },
    ],
    allowFailure: false,
  });

  const adapterCount = Number(adaptersLength);

  if (adapterCount === 0) {
    console.log("Vault has no adapters. Only idle assets available.");
    return {
      idle: {
        type: "Idle",
        allocatedAssets: idleAssets as bigint,
        percentage: 100,
      },
      adapters: [],
      totalAllocated: idleAssets as bigint,
    };
  }

  // Fetch all adapter addresses
  const adapterCalls = Array.from({ length: adapterCount }, (_, i) => ({
    address: vaultAddress,
    abi: VAULT_V2_ABI,
    functionName: "adapters" as const,
    args: [BigInt(i)],
  }));

  const adapterAddresses = (await client.multicall({
    contracts: adapterCalls,
    allowFailure: false,
  })) as Address[];

  console.log(`Found ${adapterAddresses.length} adapter(s). Fetching allocations...`);

  const block = await client.getBlock({ blockTag: "latest" });
  const adapterAllocations: AdapterAllocation[] = [];

  // Process each adapter
  for (const adapterAddress of adapterAddresses) {
    const adapterType = await detectAdapterType(client, adapterAddress);
    let destinations: AllocationDestination[] = [];

    if (adapterType === AdapterType.MorphoMarketV1) {
      destinations = await getMarketAdapterAllocations(client, adapterAddress, block.timestamp);
    } else if (adapterType === AdapterType.MorphoVaultV1) {
      destinations = await getVaultAdapterAllocations(client, adapterAddress);
    }

    const totalAssets = destinations.reduce((sum, d) => sum + d.allocatedAssets, 0n);

    if (totalAssets > 0n || destinations.length > 0) {
      adapterAllocations.push({
        adapterAddress,
        adapterType,
        destinations,
        totalAssets,
      });
    }
  }

  // Calculate total allocated across all destinations
  const totalInAdapters = adapterAllocations.reduce((sum, a) => sum + a.totalAssets, 0n);
  const totalAllocated = (idleAssets as bigint) + totalInAdapters;

  // Calculate percentages
  const idleAllocation: AllocationDestination = {
    type: "Idle",
    allocatedAssets: idleAssets as bigint,
    percentage: totalAllocated > 0n ? Number(((idleAssets as bigint) * 10000n) / totalAllocated) / 100 : 0,
  };

  // Update percentages for all adapter destinations
  for (const adapter of adapterAllocations) {
    for (const destination of adapter.destinations) {
      destination.percentage =
        totalAllocated > 0n ? Number((destination.allocatedAssets * 10000n) / totalAllocated) / 100 : 0;
    }
  }

  return {
    idle: idleAllocation,
    adapters: adapterAllocations,
    totalAllocated,
  };
}

/**
 * Displays the vault's allocations in a formatted table, including idle assets and adapter destinations.
 */
export async function displayAllocations(client: PublicClient, vaultAddress: Address, allocations: VaultV2Allocations): Promise<void> {
  const underlyingAssetAddress = await client.readContract({address: vaultAddress, abi: VAULT_V2_ABI, functionName: "asset"});
  const underlyingAssetDecimals = await client.readContract({address: underlyingAssetAddress, abi: MINIMAL_ERC20_ABI, functionName: "decimals"});

  console.log("\n✅ --- Morpho Vault V2 Allocations --- ✅");
  console.log(`\nVault Address: ${vaultAddress}`);
  console.log(`Total Allocated: ${formatUnits(allocations.totalAllocated, underlyingAssetDecimals)}`);
  console.log("--------------------------------------------------------------------------------------------------");

  // Display idle assets
  console.log("\n🏦 Idle Assets:");
  console.log("--------------------------------------------------------------------------------------------------");
  const formattedIdle = formatUnits(allocations.idle.allocatedAssets, underlyingAssetDecimals);
  console.log(
    `Idle (in vault)`.padEnd(68),
    `${parseFloat(formattedIdle).toLocaleString('en-US', {maximumFractionDigits: 2}).padStart(20)}`,
    `${allocations.idle.percentage.toFixed(2).padStart(10)}%`
  );

  // Display adapter allocations
  if (allocations.adapters.length === 0) {
    console.log("\n📦 Adapters: No adapters configured for this vault.");
  } else {
    console.log(`\n📦 Adapters (${allocations.adapters.length}):`);

    for (const adapter of allocations.adapters) {
      console.log("--------------------------------------------------------------------------------------------------");
      console.log(`\nAdapter: ${adapter.adapterAddress}`);
      console.log(`Type: ${adapter.adapterType}`);
      console.log(`Total in Adapter: ${formatUnits(adapter.totalAssets, underlyingAssetDecimals)}`);

      if (adapter.destinations.length === 0) {
        console.log("  No allocations in this adapter.");
      } else {
        console.log("\n  Destinations:");
        console.log("  " + "-".repeat(94));
        console.log("  " + "Destination".padEnd(68), "Allocation".padEnd(20), "Percentage");
        console.log("  " + "-".repeat(94));

        for (const dest of adapter.destinations) {
          const formattedAssets = formatUnits(dest.allocatedAssets, underlyingAssetDecimals);
          let destinationLabel = "";

          if (dest.type === "Market") {
            destinationLabel = `Market: ${dest.id}`;
          } else if (dest.type === "Vault") {
            destinationLabel = `Vault: ${dest.address}`;
          }

          console.log(
            `  ${destinationLabel.padEnd(68)}`,
            `${parseFloat(formattedAssets).toLocaleString('en-US', {maximumFractionDigits: 2}).padStart(20)}`,
            `${dest.percentage.toFixed(2).padStart(10)}%`
          );
        }
      }
    }
  }

  console.log("--------------------------------------------------------------------------------------------------");
}

/**
 * Main function to run the script.
 */
export async function main(): Promise<void> {
  try {
    const client = createMainnetClient();
    const allocations = await getVaultV2Allocations(client, VAULT_V2_ADDRESS);
    await displayAllocations(client, VAULT_V2_ADDRESS, allocations);
  } catch (error) {
    console.error("An error occurred during script execution:", error);
    process.exit(1);
  }
}

// Run the script if executed directly
if (require.main === module) {
  main();
}
```

**Example Output:**

```
Found 1 adapter(s). Fetching allocations...

✅ --- Morpho Vault V2 Allocations --- ✅

Vault Address: 0x04422053aDDbc9bB2759b248B574e3FCA76Bc145
Total Allocated: 380947.871852
--------------------------------------------------------------------------------------------------

🏦 Idle Assets:
--------------------------------------------------------------------------------------------------
Idle (in vault)                                                                         0       0.00%

📦 Adapters (1):
--------------------------------------------------------------------------------------------------

Adapter: 0x0c2D17F72965944e7755C992E052b725Ab5AA5Ea
Type: MorphoMarketV1AdapterV2
Total in Adapter: 380947.871852

  Destinations:
  ----------------------------------------------------------------------------------------------
  Destination                                                          Allocation           Percentage
  ----------------------------------------------------------------------------------------------
  Vault: 0x6C26793c7F1e2785c09b460676e797b716f0Bc8E                              380,947.87     100.00%
--------------------------------------------------------------------------------------------------
```

## [Configuration & Governance](#configuration--governance)

### [Vault Parameters](#vault-parameters)

#### [Morpho Vaults V2](#morpho-vaults-v2-5)

APITypescript - ViemSmart ContractUnique VaultAll Vaults
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    address
    name
    listed
    metadata {
      description
      image
    }
    allocators {
      allocator {
        address
      }
    }
    owner {
      address
    }
    curators {
      items {
        addresses {
          address
        }
      }
    }
    sentinels {
      sentinel {
        address
      }
    }
    timelocks {
      duration
      selector
      functionName
    }
  }
}
```

```
query {
  vaultV2s(first: 10) {
    items {
      address
      name
      listed
      metadata {
        description
        image
      }
      allocators {
        allocator {
          address
        }
      }
      owner {
        address
      }
      curators {
        items {
          addresses {
            address
          }
        }
      }
      sentinels {
        sentinel {
          address
        }
      }
      timelocks {
        duration
        selector
        functionName
      }
    }
  }
}
```

This example demonstrates how to retrieve comprehensive Vault V2 configuration including:

- Basic vault information (name, symbol, decimals)
- Asset details and financial metrics (totalAssets, totalSupply, fees)
- Governance roles (owner, curator)
- Adapter configuration (adaptersLength, adapters, adapterRegistry, liquidityAdapter)
- Vault gates (receiveAssetsGate, sendSharesGate, receiveSharesGate)
- Timelock settings for all critical functions (addAdapter, removeAdapter, setAdapterRegistry, etc.)
- Abdication status for each function
- Max rate and fee configuration

```
import "dotenv/config";
import {
  createPublicClient,
  http,
  formatUnits,
  PublicClient,
  parseAbi,
  Address,
} from "viem";
import { mainnet } from "viem/chains";

/**
 * Creates and configures a Viem Public Client for the Ethereum mainnet.
 * It reads the RPC URL from the .env file.
 * @returns A configured Viem public client.
 */
export function createMainnetClient(): PublicClient {
  const rpcUrl = process.env.RPC_URL_MAINNET;
  if (!rpcUrl) {
    throw new Error(
      "RPC_URL_MAINNET is not set in the .env file. Please add it."
    );
  }

  return createPublicClient({
    chain: mainnet,
    transport: http(rpcUrl, {
      retryCount: 2,
      batch: {
        batchSize: 100,
        wait: 200,
      },
    }),
    batch: {
      multicall: {
        batchSize: 2048,
        wait: 100,
      },
    },
  });
}

// The address of the Morpho Vault V2
const VAULT_V2_ADDRESS: Address = "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145";

// Morpho Vault V2 ABI for configuration retrieval
const VAULT_V2_ABI = parseAbi([
  "function name() view returns (string)",
  "function symbol() view returns (string)",
  "function decimals() view returns (uint8)",
  "function asset() view returns (address)",
  "function totalAssets() view returns (uint256)",
  "function totalSupply() view returns (uint256)",
  "function owner() view returns (address)",
  "function curator() view returns (address)",
  "function adaptersLength() view returns (uint256)",
  "function adapters(uint256) view returns (address)",
  "function adapterRegistry() view returns (address)",
  "function liquidityAdapter() view returns (address)",
  "function timelock(bytes4) view returns (uint256)",
  "function abdicated(bytes4) view returns (bool)",
  "function receiveAssetsGate() view returns (address)",
  "function sendSharesGate() view returns (address)",
  "function receiveSharesGate() view returns (address)",
  "function maxRate() view returns (uint256)",
  "function performanceFee() view returns (uint256)",
  "function managementFee() view returns (uint256)",
]);

const ERC20_ABI = parseAbi([
  "function name() view returns (string)",
  "function symbol() view returns (string)",
  "function decimals() view returns (uint8)",
]);

// Function selectors for timelock queries
const FUNCTION_SELECTORS = {
  setReceiveAssetsGate: "0x04dbf0ce",
  addAdapter: "0x60d54d41",
  increaseRelativeCap: "0x2438525b",
  setReceiveSharesGate: "0x2cb19f98",
  setForceDeallocatePenalty: "0x3e9d2ac7",
  increaseTimelock: "0x47966291",
  removeAdapter: "0x585cd34b",
  setSendSharesGate: "0xc21ad028",
  increaseAbsoluteCap: "0xf6f98fd5",
  setAdapterRegistry: "0x5b34b823",
} as const;

const FUNCTION_NAMES: Record<string, string> = {
  "0x04dbf0ce": "setReceiveAssetsGate",
  "0x60d54d41": "addAdapter",
  "0x2438525b": "increaseRelativeCap",
  "0x2cb19f98": "setReceiveSharesGate",
  "0x3e9d2ac7": "setForceDeallocatePenalty",
  "0x47966291": "increaseTimelock",
  "0x585cd34b": "removeAdapter",
  "0xc21ad028": "setSendSharesGate",
  "0xf6f98fd5": "increaseAbsoluteCap",
  "0x5b34b823": "setAdapterRegistry",
};

interface TimelockInfo {
  selector: string;
  functionName: string;
  duration: number;
  isAbdicated: boolean;
}

interface VaultV2Configuration {
  // Basic Info
  address: Address;
  name: string;
  symbol: string;
  decimals: number;

  // Asset Info
  asset: {
    address: Address;
    name: string;
    symbol: string;
    decimals: number;
  };

  // Financial Info
  totalAssets: bigint;
  totalSupply: bigint;
  performanceFee: number; // As percentage
  managementFee: number; // As percentage
  maxRate: bigint;

  // Governance
  owner: Address;
  curator: Address;

  // Adapters
  adaptersLength: number;
  adapters: Address[];
  adapterRegistry: Address;
  liquidityAdapter: Address;

  // Gates
  receiveAssetsGate: Address;
  sendSharesGate: Address;
  receiveSharesGate: Address;

  // Timelocks
  timelocks: TimelockInfo[];
}

/**
 * Helper function to handle zero address cases
 */
function handleZeroAddress(address: Address): string {
  return address === "0x0000000000000000000000000000000000000000"
    ? "Not set (0x0)"
    : address;
}

/**
 * Helper function to format timelock duration
 */
function formatTimelock(seconds: number): string {
  if (seconds === 0) return "0s (No timelock)";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h ${minutes}m`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m`;
  return `${seconds}s`;
}

/**
 * Retrieves comprehensive Vault V2 configuration information.
 * @param client The Viem public client.
 * @param vaultAddress The address of the Morpho Vault V2.
 * @returns A promise that resolves to a VaultV2Configuration object.
 */
export async function getVaultV2Configuration(
  client: PublicClient,
  vaultAddress: Address
): Promise<VaultV2Configuration> {
  console.log(`Fetching configuration for Vault V2: ${vaultAddress}...`);

  // First multicall to get basic vault information
  const [
    name,
    symbol,
    decimals,
    assetAddress,
    totalAssets,
    totalSupply,
    owner,
    curator,
    adaptersLength,
    adapterRegistry,
    liquidityAdapter,
    receiveAssetsGate,
    sendSharesGate,
    receiveSharesGate,
    maxRate,
    performanceFee,
    managementFee,
  ] = await client.multicall({
    contracts: [
      { address: vaultAddress, abi: VAULT_V2_ABI, functionName: "name" },
      { address: vaultAddress, abi: VAULT_V2_ABI, functionName: "symbol" },
      { address: vaultAddress, abi: VAULT_V2_ABI, functionName: "decimals" },
      { address: vaultAddress, abi: VAULT_V2_ABI, functionName: "asset" },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "totalAssets",
      },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "totalSupply",
      },
      { address: vaultAddress, abi: VAULT_V2_ABI, functionName: "owner" },
      { address: vaultAddress, abi: VAULT_V2_ABI, functionName: "curator" },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "adaptersLength",
      },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "adapterRegistry",
      },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "liquidityAdapter",
      },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "receiveAssetsGate",
      },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "sendSharesGate",
      },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "receiveSharesGate",
      },
      { address: vaultAddress, abi: VAULT_V2_ABI, functionName: "maxRate" },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "performanceFee",
      },
      {
        address: vaultAddress,
        abi: VAULT_V2_ABI,
        functionName: "managementFee",
      },
    ],
    allowFailure: false,
  });

  // Fetch adapter addresses
  const adaptersLengthNum = Number(adaptersLength);
  const adapters: Address[] = [];
  if (adaptersLengthNum > 0) {
    const adapterCalls = Array.from({ length: adaptersLengthNum }, (_, i) => ({
      address: vaultAddress,
      abi: VAULT_V2_ABI,
      functionName: "adapters" as const,
      args: [BigInt(i)],
    }));
    const adapterResults = await client.multicall({
      contracts: adapterCalls,
      allowFailure: false,
    });
    adapters.push(...(adapterResults as Address[]));
  }

  // Fetch asset information
  const [assetName, assetSymbol, assetDecimals] = await client.multicall({
    contracts: [
      { address: assetAddress, abi: ERC20_ABI, functionName: "name" },
      { address: assetAddress, abi: ERC20_ABI, functionName: "symbol" },
      { address: assetAddress, abi: ERC20_ABI, functionName: "decimals" },
    ],
    allowFailure: false,
  });

  // Fetch timelock information for all critical functions
  const timelocks: TimelockInfo[] = [];
  for (const [selector, functionName] of Object.entries(FUNCTION_NAMES)) {
    const [duration, isAbdicated] = await client.multicall({
      contracts: [
        {
          address: vaultAddress,
          abi: VAULT_V2_ABI,
          functionName: "timelock",
          args: [selector as `0x${string}`],
        },
        {
          address: vaultAddress,
          abi: VAULT_V2_ABI,
          functionName: "abdicated",
          args: [selector as `0x${string}`],
        },
      ],
      allowFailure: false,
    });

    timelocks.push({
      selector,
      functionName,
      duration: Number(duration),
      isAbdicated: Boolean(isAbdicated),
    });
  }

  // Calculate fees as percentages
  const performanceFeePercent = Number(formatUnits(performanceFee, 18)) * 100;
  const managementFeePercent = Number(formatUnits(managementFee, 18)) * 100;

  return {
    address: vaultAddress,
    name,
    symbol,
    decimals,
    asset: {
      address: assetAddress,
      name: assetName,
      symbol: assetSymbol,
      decimals: assetDecimals,
    },
    totalAssets,
    totalSupply,
    performanceFee: performanceFeePercent,
    managementFee: managementFeePercent,
    maxRate,
    owner,
    curator,
    adaptersLength: adaptersLengthNum,
    adapters,
    adapterRegistry,
    liquidityAdapter,
    receiveAssetsGate,
    sendSharesGate,
    receiveSharesGate,
    timelocks,
  };
}

/**
 * Displays the Vault V2 configuration in a formatted manner.
 */
export function displayVaultV2Configuration(
  config: VaultV2Configuration
): void {
  console.log("\n✅ --- Morpho Vault V2 Configuration --- ✅");

  console.log("\n--- Basic Information ---");
  console.log(`Vault Name: ${config.name}`);
  console.log(`Vault Symbol: ${config.symbol}`);
  console.log(`Vault Address: ${config.address}`);
  console.log(`Vault Decimals: ${config.decimals}`);

  console.log("\n--- Asset Information ---");
  console.log(`Asset Name: ${config.asset.name}`);
  console.log(`Asset Symbol: ${config.asset.symbol}`);
  console.log(`Asset Address: ${config.asset.address}`);
  console.log(`Asset Decimals: ${config.asset.decimals}`);

  console.log("\n--- Financial Information ---");
  console.log(
    `Total Assets: ${formatUnits(config.totalAssets, config.asset.decimals)} ${config.asset.symbol}`
  );
  console.log(
    `Total Supply: ${formatUnits(config.totalSupply, config.decimals)} ${config.symbol}`
  );
  console.log(
    `Performance Fee: ${config.performanceFee.toFixed(4)}% (annual)`
  );
  console.log(
    `Management Fee: ${config.managementFee.toFixed(4)}% (annual)`
  );

  // Calculate and display max rate as APR
  const maxRateNumber = Number(config.maxRate);
  const secondsPerYear = 31557600; // 365.25 days
  const maxRateAPR =
    maxRateNumber > 0
      ? ((maxRateNumber / 1e18) * secondsPerYear * 100).toFixed(2)
      : "0";
  console.log(`Max Rate: ${maxRateAPR}% APR`);

  console.log("\n--- Governance ---");
  console.log(`Owner: ${config.owner}`);
  console.log(`Curator: ${handleZeroAddress(config.curator)}`);

  console.log("\n--- Adapters ---");
  console.log(`Adapters Length: ${config.adaptersLength}`);
  console.log(`Adapter Registry: ${config.adapterRegistry}`);
  console.log(`Liquidity Adapter: ${config.liquidityAdapter}`);
  if (config.adapters.length > 0) {
    console.log(`Configured Adapters:`);
    config.adapters.forEach((adapter, i) => {
      console.log(`  ${i + 1}. ${adapter}`);
    });
  }

  console.log("\n--- Vault Gates ---");
  console.log(
    `Receive Assets Gate: ${handleZeroAddress(config.receiveAssetsGate)}`
  );
  console.log(`Send Shares Gate: ${handleZeroAddress(config.sendSharesGate)}`);
  console.log(
    `Receive Shares Gate: ${handleZeroAddress(config.receiveSharesGate)}`
  );

  console.log("\n--- Timelocks & Abdications ---");
  console.log("Function".padEnd(30), "Duration".padEnd(20), "Abdicated");
  console.log("-".repeat(70));
  config.timelocks.forEach((tl) => {
    console.log(
      tl.functionName.padEnd(30),
      formatTimelock(tl.duration).padEnd(20),
      tl.isAbdicated ? "Yes" : "No"
    );
  });

  console.log("\n----------------------------------------");
}

/**
 * Main function to run the script.
 */
export async function main(): Promise<void> {
  try {
    const client = createMainnetClient();

    // Get Vault V2 configuration
    const config = await getVaultV2Configuration(client, VAULT_V2_ADDRESS);
    displayVaultV2Configuration(config);
  } catch (error) {
    console.error("An error occurred during script execution:", error);
    process.exit(1);
  }
}

// Run the script if executed directly
if (require.main === module) {
  main();
}
```

**Example Output:**

```
Fetching configuration for Vault V2: 0x04422053aDDbc9bB2759b248B574e3FCA76Bc145...

--- Morpho Vault V2 Configuration ---

--- Basic Information ---
Vault Name: Keyrock USDC
Vault Symbol: kUSDC
Vault Address: 0x04422053aDDbc9bB2759b248B574e3FCA76Bc145
Vault Decimals: 18

--- Asset Information ---
Asset Name: USD Coin
Asset Symbol: USDC
Asset Address: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
Asset Decimals: 6

--- Financial Information ---
Total Assets: 380908.53096 USDC
Total Supply: 377706.886328436653684714 kUSDC
Performance Fee: 0.0000% (annual)
Management Fee: 0.0000% (annual)
Max Rate: 15.01% APR

--- Governance ---
Owner: 0xbA75546ACD56b3a9142f94F179b03970eE4283Fd
Curator: 0xbA75546ACD56b3a9142f94F179b03970eE4283Fd

--- Adapters ---
Adapters Length: 1
Adapter Registry: 0x3696c5eAe4a7Ffd04Ea163564571E9CD8Ed9364e
Liquidity Adapter: 0x0c2D17F72965944e7755C992E052b725Ab5AA5Ea
Configured Adapters:
  1. 0x0c2D17F72965944e7755C992E052b725Ab5AA5Ea

--- Vault Gates ---
Receive Assets Gate: Not set (0x0)
Send Shares Gate: Not set (0x0)
Receive Shares Gate: Not set (0x0)

--- Timelocks & Abdications ---
Function                       Duration             Abdicated
----------------------------------------------------------------------
setReceiveAssetsGate           7d 0h 0m             No
addAdapter                     3d 0h 0m             No
increaseRelativeCap            3d 0h 0m             No
setReceiveSharesGate           7d 0h 0m             No
setForceDeallocatePenalty      3d 0h 0m             No
increaseTimelock               7d 0h 0m             No
removeAdapter                  7d 0h 0m             No
setSendSharesGate              7d 0h 0m             No
increaseAbsoluteCap            3d 0h 0m             No
setAdapterRegistry             0s (No timelock)     Yes

----------------------------------------
```

```
// Basic vault information
string memory vaultName = IMorphoVaultV2(vault).name();
string memory vaultSymbol = IMorphoVaultV2(vault).symbol();
uint8 vaultDecimals = IMorphoVaultV2(vault).decimals();
address assetAddress = IMorphoVaultV2(vault).asset();

// Financial metrics
uint256 totalAssets = IMorphoVaultV2(vault).totalAssets();
uint256 totalSupply = IMorphoVaultV2(vault).totalSupply();
uint256 performanceFee = IMorphoVaultV2(vault).performanceFee(); // In WAD (18 decimals)
uint256 managementFee = IMorphoVaultV2(vault).managementFee(); // In WAD (18 decimals)
uint256 maxRate = IMorphoVaultV2(vault).maxRate(); // Max rate in WAD per second

// Governance roles
address owner = IMorphoVaultV2(vault).owner();
address curator = IMorphoVaultV2(vault).curator();

// Adapter configuration
uint256 adaptersLength = IMorphoVaultV2(vault).adaptersLength();
address adapterRegistry = IMorphoVaultV2(vault).adapterRegistry();
address liquidityAdapter = IMorphoVaultV2(vault).liquidityAdapter();

// Get specific adapter by index
for (uint256 i = 0; i < adaptersLength; i++) {
    address adapter = IMorphoVaultV2(vault).adapters(i);
    // Process adapter...
}

// Vault gates
address receiveAssetsGate = IMorphoVaultV2(vault).receiveAssetsGate();
address sendSharesGate = IMorphoVaultV2(vault).sendSharesGate();
address receiveSharesGate = IMorphoVaultV2(vault).receiveSharesGate();

// Timelock and abdication for specific function
bytes4 functionSelector = bytes4(keccak256("addAdapter(address,uint256,uint256)"));
uint256 timelockDuration = IMorphoVaultV2(vault).timelock(functionSelector);
bool isAbdicated = IMorphoVaultV2(vault).abdicated(functionSelector);
```

**Key Functions:**

- **Basic Info**: `name()`, `symbol()`, `decimals()`, `asset()`
- **Financial**: `totalAssets()`, `totalSupply()`, `performanceFee()`, `managementFee()`, `maxRate()`
- **Roles**: `owner()`, `curator()`
- **Adapters**: `adaptersLength()`, `adapters(index)`, `adapterRegistry()`, `liquidityAdapter()`
- **Gates**: `receiveAssetsGate()`, `sendSharesGate()`, `receiveSharesGate()`
- **Timelocks**: `timelock(bytes4 selector)`, `abdicated(bytes4 selector)`

**Important Notes:**

- Vault V2 uses adapters for asset allocation instead of direct market queues
- Timelocks are function-specific, identified by their 4-byte selector
- Abdication means a function's control has been permanently given up (timelock set to infinity)
- High-risk functions typically have 7-day timelocks, medium-risk have 3-day timelocks
- Gates control access to deposit/withdrawal/transfer operations (address(0) means no gate)

### [Pending Actions](#pending-actions)

All governance/configuration changes go through a **submit → (wait) → accept/revoke** lifecycle enforced by the timelock. The three events to watch are `Submit`, `Revoke`, and `Accept`.

#### [Monitoring & Alerts](#monitoring--alerts)

To get notified when pending actions are submitted, accepted, or revoked, you have two options:

1. **Build your own notification system** leveraging the query below (API, TypeScript/viem, or from the smart contract).
2. **Off-the-shelf threat monitoring with [Hypernative](https://www.hypernative.io/blog/morpho-integrates-hypernative-to-secure-onchain-lending-for-professional-investors)**. Offering out-of-the-box threat/monitoring alerts for Morpho vaults.

#### [Morpho Vaults V2](#morpho-vaults-v2-6)

APITypescript - ViemSmart Contract
```
query VaultV2PendingActions {
  vaultV2ByAddress(
    address: "VAULT_ADDRESS"
    chainId: 1
  ) {
    address
    name

    # pending timelocked actions
    pendingConfigs(first: 100) {
      items {
        validAt
        functionName
        txHash
        decodedData {
          __typename

          ... on VaultV2SetIsAllocatorPendingData {
            isAllocator
            account { address }
          }

          ... on VaultV2SetReceiveSharesGatePendingData {
            receiveSharesGate
          }

          ... on VaultV2SetSendSharesGatePendingData {
            sendSharesGate
          }

          ... on VaultV2SetReceiveAssetsGatePendingData {
            receiveAssetsGate
          }

          ... on VaultV2SetSendAssetsGatePendingData {
            sendAssetsGate
          }

          ... on VaultV2SetAdapterRegistryPendingData {
            adapterRegistry
          }

          ... on VaultV2AdapterPendingData {
            adapterAddress
          }

          ... on VaultV2TimelockPendingData {
            timelock
            selector
            functionName
          }

          ... on VaultV2SetPerformanceFeePendingData {
            performanceFee
          }

          ... on VaultV2SetManagementFeePendingData {
            managementFee
          }

          ... on VaultV2SetPerformanceFeeRecipientPendingData {
            performanceFeeRecipient
          }

          ... on VaultV2SetManagementFeeRecipientPendingData {
            managementFeeRecipient
          }

          ... on VaultV2IncreaseCapPendingData {
            cap
            config {
              id
              type
            }
          }

          ... on VaultV2SetForceDeallocatePenaltyPendingData {
            adapterAddress
            forceDeallocatePenalty
          }

          ... on VaultV2AbdicatePendingData {
            selector
            functionName
          }
        }
      }
    }
  }
}
```

```
import { createPublicClient, http, parseAbiItem } from 'viem'
import { mainnet } from 'viem/chains'

const client = createPublicClient({
  chain: mainnet,
  transport: http(),
})

const VAULT_ADDRESS = '0xVAULT_ADDRESS' as `0x${string}`
const FROM_BLOCK = 0n // set to vault deployment block

// Vault V2 timelocked-action lifecycle events
const submitEvent = parseAbiItem('event Submit(bytes4 indexed selector, uint256 validAt, bytes data)')
const revokeEvent = parseAbiItem('event Revoke(bytes4 indexed selector)')
const acceptEvent = parseAbiItem('event Accept(bytes4 indexed selector)')

const [submitLogs, revokeLogs, acceptLogs] = await Promise.all([
  client.getLogs({ address: VAULT_ADDRESS, event: submitEvent, fromBlock: FROM_BLOCK }),
  client.getLogs({ address: VAULT_ADDRESS, event: revokeEvent, fromBlock: FROM_BLOCK }),
  client.getLogs({ address: VAULT_ADDRESS, event: acceptEvent, fromBlock: FROM_BLOCK }),
])

// simplified: assumes at most one submit/revoke cycle per selector
const resolvedSelectors = new Set([
  ...revokeLogs.map((l) => l.args.selector),
  ...acceptLogs.map((l) => l.args.selector),
])

const pendingActions = submitLogs.filter((l) => !resolvedSelectors.has(l.args.selector))

for (const log of pendingActions) {
  const executableAt = new Date(Number(log.args.validAt) * 1000)
  console.log(`Pending selector ${log.args.selector} - executable at ${executableAt.toISOString()}`)
}
```

```
// Timelock duration for a specific function
bytes4 addAdapterSelector = bytes4(keccak256("addAdapter(address,uint256,uint256)"));
uint256 duration = IMorphoVaultV2(vault).timelock(addAdapterSelector);

// Listen onchain for Submit / Revoke / Accept events:
// event Submit(bytes4 indexed selector, uint256 validAt, bytes data)
// event Revoke(bytes4 indexed selector)
// event Accept(bytes4 indexed selector)
//
// A config is pending when Submit was emitted and neither Revoke nor Accept
// has been emitted for the same selector.

// Check if a pending action's timelock has elapsed (can be accepted)
// validAt comes from the Submit event args
bool canAccept = block.timestamp >= validAt;
```

### [Risk Indicators](#risk-indicators)

#### [Morpho Vault Warnings](#morpho-vault-warnings)

Vault V2 warning `type` can be:

- `not_whitelisted` (YELLOW)
- `timelock` (RED)
- `low_liquidity` (YELLOW)
- `deposit_disabled` (RED)
- `bad_debt_unrealized` (RED, exposure-gated)
- `oracle_unusable` (RED, exposure-gated)
- `oracle_price_derivation` (RED, exposure-gated)
- `custom` (level configured per entry)

Vault V1 uses a different set:

- `short_timelock` (RED)
- `not_whitelisted` (YELLOW)
- `deposit_disabled` (RED)
- `low_liquidity` (YELLOW)
- `oracle_unusable` (RED, exposure-gated)
- `oracle_price_derivation` (RED, exposure-gated)
- `custom` (level configured per entry)

The default response returns active warnings only. Vault V2 also defines a `GREEN` level for passing checks, but `level_in` replaces the default `[YELLOW, RED]` filter rather than extending it, so `level_in: [GREEN]` hides every active warning. Market warnings do not propagate to vaults: the exposure-gated types above are raised on the vault itself when its exposure to the flagged markets crosses a threshold.

See [Morpho Warnings](https://docs.morpho.org/get-started/resources/app-ecosystem/#morpho-warnings) for the full type list, criteria, and thresholds.

API - Morpho Vaults V2API
```
query {
  vaultV2s(first: 5) {
    items {
      name
      warnings {
        type
        level
      }
    }
  }
}
```

## [Fee Wrapper](#fee-wrapper)

### [FeeWrapper List](#feewrapper-list)

APIUnique FeeWrapperAll FeeWrappers
```
query VaultV2ByAddress {
  vaultV2ByAddress(
    address: "0xd4468EF3745c315949a97090eD27b3F73b9b7C02"
    chainId: 8453
  ) {
    type
    address
    name
  }
}
```

```
query VaultV2s {
  vaultV2s(skip: 0, first: 20, where: { type_in: [FeeWrapper] }) {
    items {
      address
      name
    }
  }
}
```

### [FeeWrapper Exposure](#feewrapper-exposure)

APIUnique FeeWrapperAll FeeWrappers
```
query VaultV2ByAddress {
  vaultV2ByAddress(
    address: "0xd4468EF3745c315949a97090eD27b3F73b9b7C02"
    chainId: 8453
  ) {
    type
    adapters {
      items {
        type
        address
        ... on MorphoVaultV2Adapter {
          address
          innerVault {
            address
            name
          }
        }
      }
    }
    historicalState {
      sharePrice(options: {
        startTimestamp: 1771015645
        endTimestamp: 1771915645
        interval: HOUR
      }) {
        x
        y
      }
    }
  }
}
```

```
query VaultV2s {
  vaultV2s(skip: 0, first: 20, where: { type_in: [FeeWrapper] }) {
    items {
      type
      address
      adapters {
        items {
          type
          address
          ... on MorphoVaultV2Adapter {
            address
            innerVault {
              address
              name
            }
          }
        }
      }
      historicalState {
        sharePrice(options: {
          startTimestamp: 1771015645
          endTimestamp: 1771915645
          interval: HOUR
        }) {
          x
          y
        }
      }
    }
  }
}
```

### [FeeWrapper Yield](#feewrapper-yield)

APIUnique FeeWrapperAll FeeWrappers
```
query VaultV2ByAddress {
  vaultV2ByAddress(
    address: "0xd4468EF3745c315949a97090eD27b3F73b9b7C02"
    chainId: 8453
  ) {
    type
    apy
    avgNetApyExcludingRewards
    avgNetApy
    performanceFee
    performanceFeeRecipient
    managementFee
    managementFeeRecipient
    rewards {
      asset {
        symbol
        address
      }
      supplyApr
    }
  }
}
```

```
query VaultV2s {
  vaultV2s(skip: 0, first: 20, where: { type_in: [FeeWrapper] }) {
    items {
      type
      address
      apy
      avgNetApyExcludingRewards
      avgNetApy
      performanceFee
      performanceFeeRecipient
      managementFee
      managementFeeRecipient
      rewards {
        asset {
          symbol
          address
        }
        supplyApr
      }
    }
  }
}
```

## [Position Tracking](#position-tracking)

### [User All Vaults Position](#user-all-vaults-position)

#### [Morpho Vaults V2](#morpho-vaults-v2-7)

API
```
query GetUserVaultPositions($address: String!, $chainId: Int!) {
  userByAddress(address: $address, chainId: $chainId) {
    address
    chain {
      id
    }
    vaultV2Positions {
      shares
      vault {
        address
        symbol
      }
    }
    vaultPositions {
      state {
        shares
      }
      vault {
        address
        symbol
      }
    }
  }
}
```

### [Vault Depositors](#vault-depositors)

#### [Morpho Vaults V2](#morpho-vaults-v2-8)

APIUnique Vault
```
query {
  vaultV2ByAddress(
    address: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
    chainId: 1
  ) {
    positions(first: 10, skip:0) {
      items {
        user {
          address
        }
        assets
        assetsUsd
        shares
      }
    }
    totalSupply
    asset {
      address
      symbol
    }
  }
}
```

### [User Earnings](#user-earnings)

#### [Unique Vault](#unique-vault)

API - Morpho Vault V2API
```
query {
  vaultV2PositionByAddress(
    userAddress: "USERADDRESS"
    vaultAddress: "MORPHOVAULTV2ADDRESS"
    chainId: 1
  ) {
    vault {
      name
      address
    }
    assets
    assetsUsd
    shares
    pnl
    pnlUsd
    roe # time-weighted return since inception (non-annualized)
  }
}
```

#### [All Vaults](#all-vaults)

API
```
query {
  userByAddress(address: "USERADDRESS", chainId: 1) {
    vaultV2Positions {
      vault {
        name
        address
      }
      assets
      assetsUsd
      shares
      pnl
      pnlUsd
      roe # time-weighted return since inception (non-annualized)
    }
    vaultPositions {
      vault {
        name
        address
      }
      state {
        assets
        assetsUsd
        shares
        pnl
        pnlUsd
        roe # time-weighted return since inception (non-annualized)
      }
    }
  }
}
```

### [Transaction History](#transaction-history)

#### [Morpho Vaults V2](#morpho-vaults-v2-9)

APIUnique Vault
```
query {
  vaultV2transactions(
    skip: 0
    first: 10
    orderBy: Time
    orderDirection: Desc
    where: {
      vaultAddress_in: "0x04422053aDDbc9bB2759b248B574e3FCA76Bc145"
      chainId_in: [1]
    }
  ) {
    items {
      vault {
        address
      }
      type
      shares
      blockNumber
      timestamp
      txHash
      txIndex
      logIndex
    }
  }
}
```

## [Historical Data](#historical-data)

### [APY Historical State](#apy-historical-state)

#### [Morpho Vaults v2](#morpho-vaults-v2-10)

Coming soon.

[Exit an illiquid vault in kind

Previous Page

](https://docs.morpho.org/developers/earn/tutorials/in-kind-redemption/)[Integrate Rewards for Earn Products

Next Page

](https://docs.morpho.org/developers/earn/tutorials/rewards/)