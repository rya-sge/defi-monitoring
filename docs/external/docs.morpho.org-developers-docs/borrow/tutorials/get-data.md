# Get Data

> Source: https://docs.morpho.org/developers/borrow/tutorials/get-data

---

# Get Data

## [Before Starting](#before-starting)

In this tutorial, you'll see three main ways to fetch data for Morpho Markets:

- **API**: Using the Morpho public API. This is the easiest and most direct way to get comprehensive, indexed data for most applications.
- **Smart Contract**: Fetching data directly onchain using read functions (or offchain via libraries like Viem). This is best for real-time, trustless data needed within other smart contracts or sensitive applications.
- **SDK**: Using the Morpho SDKs for pre-built abstractions that handle complex calculations (like interest accrual) and simplify development.

API Endpoint: [api.morpho.org/graphql](https://api.morpho.org/graphql)

For each topic below, you'll find guides for each method where applicable. This structure helps you choose the best approach for your specific use case.

## [Discovery and Listing](#discovery-and-listing)

### [Markets List](#markets-list)

APITypescript - ViemSmart ContractQuickly retrieve a list of all markets or filter for specific ones, like those listed for incentives.

---

All Markets
```
query {
  markets {
    items {
      marketId
      lltv
      oracle {
        address
      }
      irmAddress
      loanAsset {
        address
        symbol
        decimals
      }
      collateralAsset {
        address
        symbol
        decimals
      }
      state {
        borrowAssets
        supplyAssets
        fee
        utilization
      }
    }
  }
}
```

---

Listed Markets
```
query {
  markets(where: { listed: true }) {
    items {
      marketId
      listed
      lltv
      oracle {
        address
      }
      irmAddress
      loanAsset {
        address
        symbol
        decimals
      }
      collateralAsset {
        address
        symbol
        decimals
      }
      state {
        borrowAssets
        supplyAssets
        fee
        utilization
      }
    }
  }
}
```

This example demonstrates how to discover new markets by listening to `CreateMarket` events from the Morpho V1 contract. The script shows how to:

- Monitor market creation events within a specific block range
- Parse market parameters including loan/collateral tokens, oracle, IRM, and LLTV
- Extract and format market IDs and configuration details
- Display results in both detailed and table formats for easy analysis
- Handle LLTV conversion from WAD format to percentage

```
import "dotenv/config";
import { createPublicClient, http, PublicClient, parseAbiItem, Address } from "viem";
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

// Morpho V1 contract address
const MORPHO_BLUE_ADDRESS: Address = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb";

// Block range to search for market creations
const START_BLOCK = 22867292n;
const END_BLOCK = 22867298n;

// CreateMarket event ABI
const CREATE_MARKET_EVENT = parseAbiItem(
  "event CreateMarket(bytes32 indexed id, (address loanToken, address collateralToken, address oracle, address irm, uint256 lltv) marketParams)"
);

interface MarketParams {
  loanToken: Address;
  collateralToken: Address;
  oracle: Address;
  irm: Address;
  lltv: bigint;
}

interface MarketCreationEvent {
  id: `0x${string}`;
  marketParams: MarketParams;
  blockNumber: bigint;
  transactionHash: string;
  lltvPercentage: number;
}

/**
 * Converts LLTV from WAD format to percentage
 */
function formatLLTV(lltv: bigint): number {
  return Number(lltv) / 1e18 * 100;
}

/**
 * Formats an address to a shorter display format
 */
function formatAddress(address: string): string {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

export async function fetchNewMarketCreations(
  client: PublicClient,
  startBlock: bigint = START_BLOCK,
  endBlock: bigint = END_BLOCK
): Promise<MarketCreationEvent[]> {
  console.log(`Fetching market creations from block ${startBlock} to ${endBlock}...`);
  
  // Get logs for CreateMarket events
  const logs = await client.getLogs({
    address: MORPHO_BLUE_ADDRESS,
    event: CREATE_MARKET_EVENT,
    fromBlock: startBlock,
    toBlock: endBlock,
  });

  console.log(`Found ${logs.length} market creation(s)`);

  // Parse and format the logs
  const marketCreations: MarketCreationEvent[] = logs.map((log) => {
    const marketParams = log.args.marketParams!;
    return {
      id: log.args.id!,
      marketParams: {
        loanToken: marketParams.loanToken,
        collateralToken: marketParams.collateralToken,
        oracle: marketParams.oracle,
        irm: marketParams.irm,
        lltv: marketParams.lltv,
      },
      blockNumber: log.blockNumber!,
      transactionHash: log.transactionHash!,
      lltvPercentage: formatLLTV(marketParams.lltv),
    };
  });

  return marketCreations;
}

export function displayMarketCreations(marketCreations: MarketCreationEvent[]): void {
  if (marketCreations.length === 0) {
    console.log("No new markets were created in the specified block range.");
    return;
  }

  console.log("\n✅ --- New Morpho Markets Created --- ✅");
  
  console.log("\n--- Market Summary ---");
  console.log(`Total Markets Created: ${marketCreations.length}`);
  
  console.log("\n--- Market Details ---");
  marketCreations.forEach((market, index) => {
    console.log(`\n${index + 1}. Market ID: ${market.id}`);
    console.log(`   Loan Token: ${market.marketParams.loanToken}`);
    console.log(`   Collateral Token: ${market.marketParams.collateralToken}`);
    console.log(`   Oracle: ${formatAddress(market.marketParams.oracle)}`);
    console.log(`   IRM: ${formatAddress(market.marketParams.irm)}`);
    console.log(`   LLTV: ${market.lltvPercentage.toFixed(2)}%`);
    console.log(`   Block: ${market.blockNumber}`);
    console.log(`   Transaction: ${market.transactionHash}`);
  });

  // Display in table format for better overview
  console.log("\n--- Markets Table ---");
  console.log("ID                                                                 | Loan Token   | Collateral   | LLTV     | Block");
  console.log("-------------------------------------------------------------------+---------------+--------------+----------+----------");
  
  marketCreations.forEach((market) => {
    const shortId = `${market.id.slice(0, 8)}...${market.id.slice(-8)}`;
    const loanToken = formatAddress(market.marketParams.loanToken);
    const collateralToken = formatAddress(market.marketParams.collateralToken);
    const lltv = `${market.lltvPercentage.toFixed(2)}%`.padStart(8);
    
    console.log(
      `${shortId.padEnd(66)} | ${loanToken.padEnd(13)} | ${collateralToken.padEnd(12)} | ${lltv} | ${market.blockNumber}`
    );
  });

  console.log("\n----------------------------------------");
}

export async function main(): Promise<void> {
  try {
    const client = await createMainnetClient();
    
    // Fetch market creations in the specified block range
    const marketCreations = await fetchNewMarketCreations(client, START_BLOCK, END_BLOCK);
    
    // Display the results
    displayMarketCreations(marketCreations);
    
  } catch (error) {
    console.error("Error fetching market creations:", error);
  }
}

// Run the script if executed directly
if (require.main === module) {
  main();
}
```

**Example Output:**

```
Fetching market creations from block 22867292 to 22867298...
Found 1 market creation(s)

✅ --- New Morpho Markets Created --- ✅

--- Market Summary ---
Total Markets Created: 1

--- Market Details ---

1. Market ID: 0x9a33209eee9e93f5f7aed04085f9f5e0ce9a7a103c476f5c30a0e5ca03c3d540
   Loan Token: 0xdAC17F958D2ee523a2206206994597C13D831ec7
   Collateral Token: 0x8ddac7aa85Ce324AF75a3bFcB876375555d43BB8
   Oracle: 0xF470...66e0
   IRM: 0x870a...00BC
   LLTV: 91.50%
   Block: 22867295
   Transaction: 0x4c9e1efb7e86f8bb15c01f3f109d88ec0a0e0d553140628dfc9d852dcc902d51

--- Markets Table ---
ID                                                                 | Loan Token   | Collateral   | LLTV     | Block
-------------------------------------------------------------------+---------------+--------------+----------+----------
0x9a3320...03c3d540                                                | 0xdAC1...1ec7 | 0x8dda...3BB8 |   91.50% | 22867295

----------------------------------------
```

This example demonstrates real-time market discovery by monitoring blockchain events, which is essential for tracking new lending opportunities and market configurations as they're created.

You can discover markets by listening for the `CreateMarket` event emitted from the core `Morpho` contract:

```
// Listen to CreateMarket events
event CreateMarket(
    bytes32 indexed id,
    MarketParams marketParams
);

// Market parameters structure
struct MarketParams {
    address loanToken;
    address collateralToken;
    address oracle;
    address irm;
    uint256 lltv;
}

// Get market details by ID
function idToMarketParams(bytes32 id)
    external view returns (MarketParams memory);

// Check if market exists
function market(bytes32 id) external view returns (
    uint128 totalSupplyAssets,
    uint128 totalSupplyShares,
    uint128 totalBorrowAssets,
    uint128 totalBorrowShares,
    uint128 lastUpdate,
    uint128 fee
);
```

**Key Functions:**

- **Event Monitoring**: Listen to `CreateMarket` events for new markets
- **Market Resolution**: `idToMarketParams(id)` returns full market configuration
- **Market State**: `market(id)` returns current market liquidity and state
- **Market ID**: Computed as `keccak256(abi.encode(marketParams))`

**Event Logs**: See the [Etherscan events log](https://etherscan.io/address/0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb#events) for real examples.

### [Market Parameters](#market-parameters)

APITypescript - ViemSmart ContractFetch the core, immutable parameters for one or more markets.

---

All Markets
```
query {
  markets(
    first: 100
    orderBy: SupplyAssetsUsd
    orderDirection: Desc
    where: { chainId_in: [1, 8453] }
  ) {
    items {
      marketId
      loanAsset { address }
      collateralAsset { address }
      lltv
      irmAddress
      oracle {
        address
      }
    }
  }
}
```

---

Unique Market
```
query {
  marketById(
    marketId: "0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836"
    chainId: 8453
  ) {
    marketId
    loanAsset { address }
    collateralAsset { address }
    lltv
    irmAddress
    oracle {
      address
    }
  }
}
```

This example demonstrates comprehensive market parameter operations including:

- Decoding market IDs to parameters using `idToMarketParams`
- Encoding market parameters to generate market IDs using keccak256
- Validating market ID integrity by round-trip encoding/decoding
- Checking market existence and fetching token information
- Understanding the relationship between market parameters and their unique identifiers

```
import "dotenv/config";
import {
  createPublicClient,
  http,
  PublicClient,
  parseAbi,
  Address,
  keccak256,
  encodeAbiParameters,
  parseAbiParameters,
  formatUnits,
} from "viem";
import { mainnet } from "viem/chains";

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

// Morpho V1 contract address
const MORPHO_BLUE_ADDRESS: Address = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb";

// Example market ID to demonstrate
const EXAMPLE_MARKET_ID: `0x${string}` = "0x9a33209eee9e93f5f7aed04085f9f5e0ce9a7a103c476f5c30a0e5ca03c3d540";

// Minimal Morpho V1 ABI for market parameters
const MORPHO_BLUE_ABI = parseAbi([
  "function idToMarketParams(bytes32 id) view returns (address loanToken, address collateralToken, address oracle, address irm, uint256 lltv)",
  "function market(bytes32 id) view returns (uint128 totalSupplyAssets, uint128 totalSupplyShares, uint128 totalBorrowAssets, uint128 totalBorrowShares, uint128 lastUpdate, uint128 fee)",
]);

// ERC20 ABI for token information
const ERC20_ABI = parseAbi([
  "function symbol() view returns (string)",
  "function name() view returns (string)",
  "function decimals() view returns (uint8)",
]);

interface MarketParams {
  loanToken: Address;
  collateralToken: Address;
  oracle: Address;
  irm: Address;
  lltv: bigint;
}

interface TokenInfo {
  address: Address;
  symbol: string;
  name: string;
  decimals: number;
}

interface MarketInfo {
  id: `0x${string}`;
  params: MarketParams;
  loanToken: TokenInfo;
  collateralToken: TokenInfo;
  lltvPercentage: number;
  exists: boolean;
}

interface MarketState {
  totalSupplyAssets: bigint;
  totalSupplyShares: bigint;
  totalBorrowAssets: bigint;
  totalBorrowShares: bigint;
  lastUpdate: bigint;
  fee: bigint;
}

/**
 * Converts LLTV from WAD format to percentage
 */
function formatLLTV(lltv: bigint): number {
  return Number(formatUnits(lltv, 18)) * 100;
}

/**
 * Fetches token information for a given address
 */
async function getTokenInfo(
  client: PublicClient,
  tokenAddress: Address
): Promise<TokenInfo> {
  try {
    const [symbol, name, decimals] = await client.multicall({
      contracts: [
        { address: tokenAddress, abi: ERC20_ABI, functionName: "symbol" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "name" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "decimals" },
      ],
      allowFailure: false,
    });

    return {
      address: tokenAddress,
      symbol,
      name,
      decimals,
    };
  } catch (error) {
    // If token info fails, return address as fallback
    return {
      address: tokenAddress,
      symbol: `Token(${tokenAddress.slice(0, 6)}...)`,
      name: `Unknown Token ${tokenAddress.slice(0, 6)}...`,
      decimals: 18, // Default fallback
    };
  }
}

/**
 * Checks if a market exists by verifying if any of its state values are non-zero
 */
async function checkMarketExists(
  client: PublicClient,
  marketId: `0x${string}`
): Promise<boolean> {
  try {
    const marketState = await client.readContract({
      address: MORPHO_BLUE_ADDRESS,
      abi: MORPHO_BLUE_ABI,
      functionName: "market",
      args: [marketId],
    }) as [bigint, bigint, bigint, bigint, bigint, bigint];

    // Market exists if it has been created (any non-zero state indicates creation)
    return marketState.some(value => value > 0n);
  } catch (error) {
    return false;
  }
}

/**
 * Encodes market parameters into a market ID using keccak256 hash
 */
export function encodeMarketId(marketParams: MarketParams): `0x${string}` {
  const encoded = encodeAbiParameters(
    parseAbiParameters("address, address, address, address, uint256"),
    [
      marketParams.loanToken,
      marketParams.collateralToken,
      marketParams.oracle,
      marketParams.irm,
      marketParams.lltv,
    ]
  );
  
  return keccak256(encoded);
}

/**
 * Decodes a market ID back to market parameters by querying the Morpho V1 contract
 */
export async function decodeMarketId(
  client: PublicClient,
  marketId: `0x${string}`
): Promise<MarketParams | null> {
  try {
    const [loanToken, collateralToken, oracle, irm, lltv] = await client.readContract({
      address: MORPHO_BLUE_ADDRESS,
      abi: MORPHO_BLUE_ABI,
      functionName: "idToMarketParams",
      args: [marketId],
    }) as [Address, Address, Address, Address, bigint];

    // Check if market actually exists (all zero values indicate non-existent market)
    if (loanToken === "0x0000000000000000000000000000000000000000") {
      return null;
    }

    return {
      loanToken,
      collateralToken,
      oracle,
      irm,
      lltv,
    };
  } catch (error) {
    console.error(`Error decoding market ID ${marketId}:`, error);
    return null;
  }
}

/**
 * Validates that encoding market parameters produces the expected market ID
 */
export async function validateMarketId(
  client: PublicClient,
  marketId: `0x${string}`
): Promise<{ isValid: boolean; params: MarketParams | null; computedId: `0x${string}` | null }> {
  const params = await decodeMarketId(client, marketId);
  
  if (!params) {
    return { isValid: false, params: null, computedId: null };
  }

  const computedId = encodeMarketId(params);
  const isValid = computedId.toLowerCase() === marketId.toLowerCase();

  return { isValid, params, computedId };
}

/**
 * Retrieves comprehensive market information including parameters and token details
 */
export async function getMarketInfo(
  client: PublicClient,
  marketId: `0x${string}`
): Promise<MarketInfo> {
  console.log(`Fetching market information for ID: ${marketId}`);

  const params = await decodeMarketId(client, marketId);
  
  if (!params) {
    return {
      id: marketId,
      params: {
        loanToken: "0x0000000000000000000000000000000000000000",
        collateralToken: "0x0000000000000000000000000000000000000000",
        oracle: "0x0000000000000000000000000000000000000000",
        irm: "0x0000000000000000000000000000000000000000",
        lltv: 0n,
      },
      loanToken: {
        address: "0x0000000000000000000000000000000000000000",
        symbol: "UNKNOWN",
        name: "Unknown Token",
        decimals: 0,
      },
      collateralToken: {
        address: "0x0000000000000000000000000000000000000000",
        symbol: "UNKNOWN", 
        name: "Unknown Token",
        decimals: 0,
      },
      lltvPercentage: 0,
      exists: false,
    };
  }

  // Check if market exists
  const exists = await checkMarketExists(client, marketId);

  // Fetch token information
  const [loanTokenInfo, collateralTokenInfo] = await Promise.all([
    getTokenInfo(client, params.loanToken),
    getTokenInfo(client, params.collateralToken),
  ]);

  return {
    id: marketId,
    params,
    loanToken: loanTokenInfo,
    collateralToken: collateralTokenInfo,
    lltvPercentage: formatLLTV(params.lltv),
    exists,
  };
}

/**
 * Demonstrates market ID encoding and validation
 */
export async function demonstrateMarketIdOperations(
  client: PublicClient,
  marketId: `0x${string}`
): Promise<void> {
  console.log("=== Market ID Operations Demo ===\n");

  // 1. Decode market ID to parameters
  console.log("1. Decoding market ID to parameters...");
  const params = await decodeMarketId(client, marketId);
  
  if (!params) {
    console.log("❌ Market does not exist or failed to decode");
    return;
  }

  console.log("✅ Market parameters decoded successfully:");
  console.log(`   Loan Token: ${params.loanToken}`);
  console.log(`   Collateral Token: ${params.collateralToken}`);
  console.log(`   Oracle: ${params.oracle}`);
  console.log(`   IRM: ${params.irm}`);
  console.log(`   LLTV: ${formatLLTV(params.lltv)}%`);

  // 2. Re-encode parameters to market ID
  console.log("\n2. Re-encoding parameters to market ID...");
  const recomputedId = encodeMarketId(params);
  console.log(`   Original ID:  ${marketId}`);
  console.log(`   Computed ID:  ${recomputedId}`);

  // 3. Validate the match
  console.log("\n3. Validation result:");
  const isMatch = recomputedId.toLowerCase() === marketId.toLowerCase();
  console.log(`   ${isMatch ? "✅" : "❌"} Market ID validation: ${isMatch ? "PASS" : "FAIL"}`);

  // 4. Check if market exists onchain
  console.log("\n4. Checking market existence...");
  const exists = await checkMarketExists(client, marketId);
  console.log(`   ${exists ? "✅" : "❌"} Market exists onchain: ${exists ? "YES" : "NO"}`);
}

/**
 * Displays comprehensive market information
 */
export function displayMarketInfo(marketInfo: MarketInfo): void {
  console.log("\n✅ --- Morpho Market Parameters --- ✅");

  console.log(`\n--- Market Overview ---`);
  console.log(`Market ID: ${marketInfo.id}`);
  console.log(`Exists: ${marketInfo.exists ? "✅ Yes" : "❌ No"}`);

  if (!marketInfo.exists) {
    console.log("This market does not exist on Morpho V1.");
    return;
  }

  console.log(`\n--- Market Parameters ---`);
  console.log(`Loan Token: ${marketInfo.loanToken.name} (${marketInfo.loanToken.symbol})`);
  console.log(`  Address: ${marketInfo.params.loanToken}`);
  console.log(`  Decimals: ${marketInfo.loanToken.decimals}`);
  
  console.log(`Collateral Token: ${marketInfo.collateralToken.name} (${marketInfo.collateralToken.symbol})`);
  console.log(`  Address: ${marketInfo.params.collateralToken}`);
  console.log(`  Decimals: ${marketInfo.collateralToken.decimals}`);

  console.log(`Oracle: ${marketInfo.params.oracle}`);
  console.log(`IRM (Interest Rate Model): ${marketInfo.params.irm}`);
  console.log(`LLTV (Loan-to-Value): ${marketInfo.lltvPercentage.toFixed(2)}%`);

  console.log("\n--- Encoded Parameters ---");
  console.log(`LLTV (Raw): ${marketInfo.params.lltv.toString()}`);
  console.log(`Market ID Validation: ${encodeMarketId(marketInfo.params) === marketInfo.id ? "✅ Valid" : "❌ Invalid"}`);

  console.log("\n----------------------------------------");
}

/**
 * Main function to demonstrate market parameter operations
 */
export async function main(): Promise<void> {
  try {
    const client = createMainnetClient();
    
    // Demonstrate market ID operations
    await demonstrateMarketIdOperations(client, EXAMPLE_MARKET_ID);
    
    // Get comprehensive market information
    const marketInfo = await getMarketInfo(client, EXAMPLE_MARKET_ID);
    
    // Display results
    displayMarketInfo(marketInfo);
    
  } catch (error) {
    console.error("Error in market parameters script:", error);
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
=== Market ID Operations Demo ===

1. Decoding market ID to parameters...
✅ Market parameters decoded successfully:
   Loan Token: 0xdAC17F958D2ee523a2206206994597C13D831ec7
   Collateral Token: 0x8ddac7aa85Ce324AF75a3bFcB876375555d43BB8
   Oracle: 0xF47020f01e77257Fe86B9ECb36552486E0Ae66e0
   IRM: 0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC
   LLTV: 91.5%

2. Re-encoding parameters to market ID...
   Original ID:  0x9a33209eee9e93f5f7aed04085f9f5e0ce9a7a103c476f5c30a0e5ca03c3d540
   Computed ID:  0x9a33209eee9e93f5f7aed04085f9f5e0ce9a7a103c476f5c30a0e5ca03c3d540

3. Validation result:
   ✅ Market ID validation: PASS

4. Checking market existence...
   ✅ Market exists onchain: YES
Fetching market information for ID: 0x9a33209eee9e93f5f7aed04085f9f5e0ce9a7a103c476f5c30a0e5ca03c3d540

✅ --- Morpho Market Parameters --- ✅

--- Market Overview ---
Market ID: 0x9a33209eee9e93f5f7aed04085f9f5e0ce9a7a103c476f5c30a0e5ca03c3d540
Exists: ✅ Yes

--- Market Parameters ---
Loan Token: Tether USD (USDT)
  Address: 0xdAC17F958D2ee523a2206206994597C13D831ec7
  Decimals: 6
Collateral Token: Pendle Market Wrapped (PENDLE-LPT-WRAPPED)
  Address: 0x8ddac7aa85Ce324AF75a3bFcB876375555d43BB8
  Decimals: 18
Oracle: 0xF47020f01e77257Fe86B9ECb36552486E0Ae66e0
IRM (Interest Rate Model): 0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC
LLTV (Loan-to-Value): 91.50%

--- Encoded Parameters ---
LLTV (Raw): 915000000000000000
Market ID Validation: ✅ Valid

----------------------------------------
```

This example demonstrates the bidirectional relationship between market parameters and market IDs, essential for understanding how Morpho Markets are uniquely identified and accessed.

You can retrieve market parameters by using the `idToMarketParams` view function on the `Morpho` contract, passing the `marketId`.

```
// Get market parameters from market ID
(
    address loanToken,
    address collateralToken,
    address oracle,
    address irm,
    uint256 lltv
) = IMorpho(morpho).idToMarketParams(marketId);

// Generate market ID from parameters
struct MarketParams {
    address loanToken;
    address collateralToken;
    address oracle;
    address irm;
    uint256 lltv;
}

// Market ID is the keccak256 hash of encoded parameters
bytes32 marketId = keccak256(abi.encode(marketParams));

// Check if market exists
(
    uint128 totalSupplyAssets,
    uint128 totalSupplyShares,
    uint128 totalBorrowAssets,
    uint128 totalBorrowShares,
    uint128 lastUpdate,
    uint128 fee
) = IMorpho(morpho).market(marketId);

// Market exists if any state value > 0
bool marketExists = totalSupplyAssets > 0 || totalSupplyShares > 0 ||
                   totalBorrowAssets > 0 || totalBorrowShares > 0;
```

**Key Functions:**

- **Parameter Lookup**: `idToMarketParams(marketId)` returns all market configuration
- **Market ID Generation**: `keccak256(abi.encode(marketParams))` creates unique identifier
- **Existence Check**: `market(marketId)` returns state (non-zero values indicate existence)
- **Parameter Validation**: Re-encode parameters to verify market ID integrity

**Important Notes:**

- Market IDs are deterministic based on parameters
- Non-existent markets return zero values from `idToMarketParams`
- LLTV is stored in WAD format (18 decimals)

## [Market Metrics](#market-metrics)

### [Total Collateral, Borrow & Supply](#total-collateral-borrow--supply)

APITypescript - ViemSolidityGet the real-time state of liquidity and debt in a market.

---

All Markets
```
query {
    markets(
      first: 100
      orderBy: SupplyAssetsUsd
      orderDirection: Desc
      where: { chainId_in: [1, 8453] }
    ) {
      items {
        marketId
        state {
          collateralAssets
          collateralAssetsUsd
          borrowAssets
          borrowAssetsUsd
          supplyAssets
          supplyAssetsUsd
          liquidityAssets
          liquidityAssetsUsd
        }
      }
    }
  }
```

---

Unique Market
```
query {
  marketById(
    marketId: "0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836"
    chainId: 8453
  ) {
    state {
      collateralAssets
      borrowAssets
      supplyAssets
      liquidityAssets
    }
  }
}
```

This example demonstrates comprehensive market liquidity analysis including:

- Real-time interest accrual for supply and borrow assets
- Collateral tracking (which doesn't accrue interest)
- Market utilization and available liquidity calculations
- Comparison between stale (last update) and current (accrued) values
- Efficient batch processing for multiple markets
- Important distinction: only loan token amounts (supply/borrow) accrue interest, collateral remains static

The `market()` view function returns values that **do not include** interest accrued since the last onchain interaction. For accurate, up-to-the-second data, you must use the SDK or manually calculate the accrued interest.

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

// Morpho V1 contract address
const MORPHO_BLUE_ADDRESS: Address = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb";

// Example market ID for demonstration
const EXAMPLE_MARKET_ID: `0x${string}` = "0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64";

// Morpho V1 ABI for market operations
const MORPHO_BLUE_ABI = parseAbi([
  "function market(bytes32 id) view returns (uint128 totalSupplyAssets, uint128 totalSupplyShares, uint128 totalBorrowAssets, uint128 totalBorrowShares, uint128 lastUpdate, uint128 fee)",
  "function idToMarketParams(bytes32 id) view returns (address loanToken, address collateralToken, address oracle, address irm, uint256 lltv)",
  "function position(bytes32 id, address user) view returns (uint256 supplyShares, uint128 borrowShares, uint128 collateral)",
]);

// Interest Rate Model ABI
const IRM_ABI = parseAbi([
  "function borrowRateView((address loanToken, address collateralToken, address oracle, address irm, uint256 lltv) marketParams, (uint128 totalSupplyAssets, uint128 totalSupplyShares, uint128 totalBorrowAssets, uint128 totalBorrowShares, uint128 lastUpdate, uint128 fee) market) view returns (uint256)",
]);

// ERC20 ABI for token information
const ERC20_ABI = parseAbi([
  "function symbol() view returns (string)",
  "function name() view returns (string)",
  "function decimals() view returns (uint8)",
  "function totalSupply() view returns (uint256)",
]);

type MarketParams = {
  readonly loanToken: Address;
  readonly collateralToken: Address;
  readonly oracle: Address;
  readonly irm: Address;
  readonly lltv: bigint;
};

type MarketState = {
  readonly totalSupplyAssets: bigint;
  readonly totalSupplyShares: bigint;
  readonly totalBorrowAssets: bigint;
  readonly totalBorrowShares: bigint;
  readonly lastUpdate: bigint;
  readonly fee: bigint;
};

interface TokenInfo {
  address: Address;
  symbol: string;
  name: string;
  decimals: number;
}

interface MarketLiquidityInfo {
  marketId: `0x${string}`;
  params: MarketParams;
  staleState: MarketState;
  currentState: MarketState;
  loanToken: TokenInfo;
  collateralToken: TokenInfo;
  lltvPercentage: number;
  // Current (accrued) values
  totalSupplyAssets: bigint;
  totalBorrowAssets: bigint;
  totalCollateralAssets: bigint;
  // Formatted values
  formattedTotalSupply: string;
  formattedTotalBorrow: string;
  formattedTotalCollateral: string;
  // Metrics
  utilization: bigint;
  utilizationPercentage: number;
  availableLiquidity: bigint;
  formattedAvailableLiquidity: string;
  interestAccrued: bigint;
  formattedInterestAccrued: string;
  lastUpdateTime: Date;
  blockTimestamp: bigint;
}

const WAD = 10n ** 18n;

const wMulDown = (x: bigint, y: bigint): bigint => (x * y) / WAD;
const wDivUp = (x: bigint, y: bigint): bigint => (x * WAD + y - 1n) / y;

const wTaylorCompounded = (x: bigint, n: bigint): bigint => {
  const firstTerm = x * n;
  const secondTerm = (firstTerm * firstTerm) / (2n * WAD);
  const thirdTerm = (secondTerm * firstTerm) / (3n * WAD);
  return firstTerm + secondTerm + thirdTerm;
};

/**
 * Formats LLTV from WAD format to percentage
 */
function formatLLTV(lltv: bigint): number {
  return Number(formatUnits(lltv, 18)) * 100;
}

/**
 * Formats utilization from WAD format to percentage
 */
function formatUtilization(utilization: bigint): number {
  return Number(formatUnits(utilization, 16)); // 18 - 2 = 16 for percentage
}

/**
 * Fetches token information for a given address
 */
async function getTokenInfo(
  client: PublicClient,
  tokenAddress: Address
): Promise<TokenInfo> {
  try {
    const [symbol, name, decimals] = await client.multicall({
      contracts: [
        { address: tokenAddress, abi: ERC20_ABI, functionName: "symbol" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "name" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "decimals" },
      ],
      allowFailure: false,
    });

    return {
      address: tokenAddress,
      symbol,
      name,
      decimals,
    };
  } catch (error) {
    return {
      address: tokenAddress,
      symbol: `Token(${tokenAddress.slice(0, 6)}...)`,
      name: `Unknown Token ${tokenAddress.slice(0, 6)}...`,
      decimals: 18,
    };
  }
}

/**
 * Accrues interest on a market from its last update time to the current block's timestamp.
 * This updates the total supply and borrow assets but NOT the collateral (which doesn't accrue interest).
 */
function accrueInterests(
  marketState: MarketState,
  borrowRate: bigint,
  blockTimestamp: bigint
): { accruedState: MarketState; interestAccrued: bigint } {
  const elapsed = blockTimestamp - marketState.lastUpdate;
  
  if (elapsed === 0n || marketState.totalBorrowAssets === 0n) {
    return { 
      accruedState: marketState, 
      interestAccrued: 0n 
    };
  }

  const interest = wMulDown(
    marketState.totalBorrowAssets, 
    wTaylorCompounded(borrowRate, elapsed)
  );

  const accruedState = {
    ...marketState,
    totalSupplyAssets: marketState.totalSupplyAssets + interest,
    totalBorrowAssets: marketState.totalBorrowAssets + interest,
    lastUpdate: blockTimestamp,
  };

  return { accruedState, interestAccrued: interest };
}

/**
 * Calculates total collateral across all positions in a market.
 * Collateral doesn't accrue interest, so we can sum it directly.
 */
async function getTotalCollateralAssets(
  client: PublicClient,
  marketId: `0x${string}`
): Promise<bigint> {
  // Note: This is a simplified approach. In practice, you'd need to:
  // 1. Track all position holders (via events or an indexer)
  // 2. Sum their collateral amounts
  // For demonstration, we'll use a placeholder approach
  
  // This would require tracking all users who have positions in this market
  // For now, we'll return 0n as a placeholder
  // In a real implementation, you'd:
  // - Listen to SupplyCollateral events
  // - Track all unique addresses
  // - Sum their current collateral positions
  
  console.log("Note: Total collateral calculation requires tracking all position holders");
  return 0n;
}

/**
 * Retrieves comprehensive market liquidity information including real-time accrued values.
 */
export async function getMarketLiquidityInfo(
  client: PublicClient,
  marketId: `0x${string}`
): Promise<MarketLiquidityInfo> {
  console.log(`Fetching liquidity information for market: ${marketId}`);

  // Get current block timestamp
  const block = await client.getBlock({ blockTag: "latest" });
  const blockTimestamp = block.timestamp;

  // Get market state and parameters
  const [marketStateResult, marketParamsResult] = await client.multicall({
    contracts: [
      { address: MORPHO_BLUE_ADDRESS, abi: MORPHO_BLUE_ABI, functionName: "market", args: [marketId] },
      { address: MORPHO_BLUE_ADDRESS, abi: MORPHO_BLUE_ABI, functionName: "idToMarketParams", args: [marketId] },
    ],
    allowFailure: false,
  });

  const staleState: MarketState = {
    totalSupplyAssets: marketStateResult[0],
    totalSupplyShares: marketStateResult[1],
    totalBorrowAssets: marketStateResult[2],
    totalBorrowShares: marketStateResult[3],
    lastUpdate: marketStateResult[4],
    fee: marketStateResult[5],
  };

  const params: MarketParams = {
    loanToken: marketParamsResult[0],
    collateralToken: marketParamsResult[1],
    oracle: marketParamsResult[2],
    irm: marketParamsResult[3],
    lltv: marketParamsResult[4],
  };

  // Get token information
  const [loanToken, collateralToken] = await Promise.all([
    getTokenInfo(client, params.loanToken),
    getTokenInfo(client, params.collateralToken),
  ]);

  // Initialize values
  let currentState = staleState;
  let interestAccrued = 0n;

  // Calculate current state with interest accrual if IRM is set
  if (params.irm !== "0x0000000000000000000000000000000000000000") {
    // Get borrow rate from IRM
    const borrowRate = await client.readContract({
      address: params.irm,
      abi: IRM_ABI,
      functionName: "borrowRateView",
      args: [params, staleState],
    }) as bigint;

    // Accrue interest to get current state
    const accrualResult = accrueInterests(staleState, borrowRate, blockTimestamp);
    currentState = accrualResult.accruedState;
    interestAccrued = accrualResult.interestAccrued;
  }

  // Get total collateral (doesn't accrue interest)
  const totalCollateralAssets = await getTotalCollateralAssets(client, marketId);

  // Calculate metrics
  const utilization = currentState.totalSupplyAssets > 0n 
    ? wDivUp(currentState.totalBorrowAssets, currentState.totalSupplyAssets)
    : 0n;

  const availableLiquidity = currentState.totalSupplyAssets - currentState.totalBorrowAssets;

  return {
    marketId,
    params,
    staleState,
    currentState,
    loanToken,
    collateralToken,
    lltvPercentage: formatLLTV(params.lltv),
    totalSupplyAssets: currentState.totalSupplyAssets,
    totalBorrowAssets: currentState.totalBorrowAssets,
    totalCollateralAssets,
    formattedTotalSupply: formatUnits(currentState.totalSupplyAssets, loanToken.decimals),
    formattedTotalBorrow: formatUnits(currentState.totalBorrowAssets, loanToken.decimals),
    formattedTotalCollateral: formatUnits(totalCollateralAssets, collateralToken.decimals),
    utilization,
    utilizationPercentage: formatUtilization(utilization),
    availableLiquidity,
    formattedAvailableLiquidity: formatUnits(availableLiquidity, loanToken.decimals),
    interestAccrued,
    formattedInterestAccrued: formatUnits(interestAccrued, loanToken.decimals),
    lastUpdateTime: new Date(Number(staleState.lastUpdate) * 1000),
    blockTimestamp,
  };
}

/**
 * Retrieves liquidity information for multiple markets efficiently
 */
export async function getMultipleMarketsLiquidity(
  client: PublicClient,
  marketIds: `0x${string}`[]
): Promise<MarketLiquidityInfo[]> {
  console.log(`Fetching liquidity information for ${marketIds.length} markets...`);

  const liquidityPromises = marketIds.map(marketId => 
    getMarketLiquidityInfo(client, marketId)
  );

  return Promise.all(liquidityPromises);
}

/**
 * Displays comprehensive market liquidity information
 */
export function displayMarketLiquidity(liquidityInfo: MarketLiquidityInfo): void {
  console.log("\n✅ --- Morpho Market Liquidity Information --- ✅");

  console.log(`\n--- Market Overview ---`);
  console.log(`Market ID: ${liquidityInfo.marketId}`);
  console.log(`Loan Token: ${liquidityInfo.loanToken.name} (${liquidityInfo.loanToken.symbol})`);
  console.log(`Collateral Token: ${liquidityInfo.collateralToken.name} (${liquidityInfo.collateralToken.symbol})`);
  console.log(`LLTV: ${liquidityInfo.lltvPercentage.toFixed(2)}%`);

  console.log(`\n--- Current Liquidity (Real-time) ---`);
  console.log(`Total Supply: ${liquidityInfo.formattedTotalSupply} ${liquidityInfo.loanToken.symbol}`);
  console.log(`Total Borrow: ${liquidityInfo.formattedTotalBorrow} ${liquidityInfo.loanToken.symbol}`);
  console.log(`Total Collateral: ${liquidityInfo.formattedTotalCollateral} ${liquidityInfo.collateralToken.symbol}`);
  console.log(`Available Liquidity: ${liquidityInfo.formattedAvailableLiquidity} ${liquidityInfo.loanToken.symbol}`);
  console.log(`Utilization: ${liquidityInfo.utilizationPercentage.toFixed(2)}%`);

  console.log(`\n--- Interest Accrual ---`);
  console.log(`Last Update: ${liquidityInfo.lastUpdateTime.toISOString()}`);
  console.log(`Interest Accrued: ${liquidityInfo.formattedInterestAccrued} ${liquidityInfo.loanToken.symbol}`);

  console.log(`\n--- Stale vs Current Comparison ---`);
  console.log(`Stale Total Supply: ${formatUnits(liquidityInfo.staleState.totalSupplyAssets, liquidityInfo.loanToken.decimals)} ${liquidityInfo.loanToken.symbol}`);
  console.log(`Current Total Supply: ${liquidityInfo.formattedTotalSupply} ${liquidityInfo.loanToken.symbol}`);
  console.log(`Stale Total Borrow: ${formatUnits(liquidityInfo.staleState.totalBorrowAssets, liquidityInfo.loanToken.decimals)} ${liquidityInfo.loanToken.symbol}`);
  console.log(`Current Total Borrow: ${liquidityInfo.formattedTotalBorrow} ${liquidityInfo.loanToken.symbol}`);

  console.log(`\n--- Raw Values ---`);
  console.log(`Total Supply Assets: ${liquidityInfo.totalSupplyAssets}`);
  console.log(`Total Borrow Assets: ${liquidityInfo.totalBorrowAssets}`);
  console.log(`Total Collateral Assets: ${liquidityInfo.totalCollateralAssets}`);
  console.log(`Utilization (WAD): ${liquidityInfo.utilization}`);

  console.log("\n----------------------------------------");
}

/**
 * Displays a summary table of multiple markets liquidity
 */
export function displayMarketsLiquiditySummary(markets: MarketLiquidityInfo[]): void {
  if (markets.length === 0) {
    console.log("No markets to display.");
    return;
  }

  console.log("\n✅ --- Markets Liquidity Summary --- ✅");
  console.log("\nMarket ID                    | Loan/Collateral     | Total Supply | Total Borrow | Utilization | Available");
  console.log("-----------------------------+---------------------+--------------+--------------+-------------+----------");

  markets.forEach((market) => {
    const shortId = `${market.marketId.slice(0, 8)}...${market.marketId.slice(-8)}`;
    const tokenPair = `${market.loanToken.symbol}/${market.collateralToken.symbol}`;
    const totalSupply = parseFloat(market.formattedTotalSupply).toLocaleString('en-US', { maximumFractionDigits: 0 });
    const totalBorrow = parseFloat(market.formattedTotalBorrow).toLocaleString('en-US', { maximumFractionDigits: 0 });
    const utilization = `${market.utilizationPercentage.toFixed(1)}%`.padStart(10);
    const available = parseFloat(market.formattedAvailableLiquidity).toLocaleString('en-US', { maximumFractionDigits: 0 });

    console.log(
      `${shortId.padEnd(28)} | ${tokenPair.padEnd(19)} | ${totalSupply.padStart(12)} | ${totalBorrow.padStart(12)} | ${utilization} | ${available.padStart(8)}`
    );
  });

  console.log("\n----------------------------------------");
}

/**
 * Main function to demonstrate market liquidity calculations
 */
export async function main(): Promise<void> {
  try {
    const client = createMainnetClient();
    
    // Get liquidity information for the example market
    const marketLiquidity = await getMarketLiquidityInfo(client, EXAMPLE_MARKET_ID);
    
    // Display detailed results
    displayMarketLiquidity(marketLiquidity);
    
    // Example: Get liquidity for multiple markets
    const multipleMarkets = [EXAMPLE_MARKET_ID];
    const marketsLiquidity = await getMultipleMarketsLiquidity(client, multipleMarkets);
    
    // Display summary
    displayMarketsLiquiditySummary(marketsLiquidity);
    
  } catch (error) {
    console.error("Error in market liquidity calculation:", error);
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
Fetching liquidity information for market: 0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64
Note: Total collateral calculation requires tracking all position holders

✅ --- Morpho Market Liquidity Information --- ✅

--- Market Overview ---
Market ID: 0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64
Loan Token: USD Coin (USDC)
Collateral Token: Coinbase Wrapped BTC (cbBTC)
LLTV: 86.00%

--- Current Liquidity (Real-time) ---
Total Supply: 522083875.989369 USDC
Total Borrow: 481268818.125629 USDC
Total Collateral: 0 cbBTC
Available Liquidity: 40815057.86374 USDC
Utilization: 92.18%

--- Interest Accrual ---
Last Update: 2025-11-07T10:57:35.000Z
Interest Accrued: 0 USDC

--- Stale vs Current Comparison ---
Stale Total Supply: 522083875.989369 USDC
Current Total Supply: 522083875.989369 USDC
Stale Total Borrow: 481268818.125629 USDC
Current Total Borrow: 481268818.125629 USDC

--- Raw Values ---
Total Supply Assets: 522083875989369
Total Borrow Assets: 481268818125629
Total Collateral Assets: 0
Utilization (WAD): 921822795644868562

----------------------------------------
Fetching liquidity information for 1 markets...
Fetching liquidity information for market: 0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64
Note: Total collateral calculation requires tracking all position holders

✅ --- Markets Liquidity Summary --- ✅

Market ID                    | Loan/Collateral     | Total Supply | Total Borrow | Utilization | Available
-----------------------------+---------------------+--------------+--------------+-------------+----------
0x64d65c...883fcc64          | USDC/cbBTC          |  522,083,876 |  481,268,818 |      92.2% | 40,815,058

----------------------------------------
```

This example shows the crucial difference between stale market data (from last onchain update) and current real-time data (with interest accrued), essential for accurate liquidity analysis.

- As it is important to accrue interests on the underlying markets, Morpho Association provided a library to accrue them onchain.
Feel free to refer to the [Morpho Market Snippets](https://github.com/morpho-org/morpho-snippets/blob/main/src/morpho-blue/MorphoBlueSnippets.sol) for extensive example.

```
/// @notice Calculates the total supply of assets in a specific market.
    /// @param marketParams The parameters of the market.
    /// @return totalSupplyAssets The calculated total supply of assets.
    function marketTotalSupply(MarketParams memory marketParams) public view returns (uint256 totalSupplyAssets) {
        totalSupplyAssets = morpho.expectedTotalSupplyAssets(marketParams);
    }

    /// @notice Calculates the total borrow of assets in a specific market.
    /// @param marketParams The parameters of the market.
    /// @return totalBorrowAssets The calculated total borrow of assets.
    function marketTotalBorrow(MarketParams memory marketParams) public view returns (uint256 totalBorrowAssets) {
        totalBorrowAssets = morpho.expectedTotalBorrowAssets(marketParams);
    }
```

The total collateral on a given market is not easily retrievable onchain. One has to index all positions, and sum through the morpho.position(market, user) calls.

### [Market APY (Native & Rewards)](#market-apy-native--rewards)

APITypescript - ViemSmart ContractGet the real-time APY, interest rates, and accrual information for markets.

The API provides both the native APY from borrowing/lending and the additional APR from reward incentives.

###### [Important UI Reference one might find on apps:](#important-ui-reference-one-might-find-on-apps)

1. `avgSupplyApy` represents the native supplier APY (average supply APY excluding rewards).
2. `avgNetSupplyApy` represents the supplier APY including rewards.
3. `avgBorrowApy` represents the native borrower APY (average borrow APY excluding rewards).
4. `avgNetBorrowApy` represents the borrower APY including rewards.

---

All Markets
```
query {
  markets(
    first: 100
    orderBy: SupplyAssetsUsd
    orderDirection: Desc
    where: { chainId_in: [1, 8453] }
  ) {
    items {
      marketId
      state {
        borrowApy
        avgBorrowApy
        avgNetBorrowApy
        supplyApy
        avgSupplyApy
        avgNetSupplyApy
        rewards {
          asset {
            address
            chain {
              id
            }
          }
          supplyApr
          borrowApr
        }
      }
    }
  }
}
```

---

Unique Market
```
query {
  marketById(
    marketId: "0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836"
    chainId: 8453
  ) {
    state {
      borrowApy
      avgBorrowApy
      avgNetBorrowApy
      supplyApy
      avgSupplyApy
      avgNetSupplyApy
      rewards {
        supplyApr
        borrowApr
      }
    }
  }
}
```

This example demonstrates comprehensive market APY calculations including:

- Real-time interest accrual from last update to current block
- Borrow and supply APY calculations using Interest Rate Models (IRM)
- Market utilization and fee impact on supply rates
- Interest compounding using Taylor expansion for precision
- Comparison between stale and accrued market states
- Efficient batch processing for multiple markets

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

// Morpho V1 contract address
const MORPHO_BLUE_ADDRESS: Address = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb";

// Example market ID for demonstration 
const EXAMPLE_MARKET_ID: `0x${string}` = "0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64";

// Morpho V1 ABI for market operations
const MORPHO_BLUE_ABI = parseAbi([
  "function market(bytes32 id) view returns (uint128 totalSupplyAssets, uint128 totalSupplyShares, uint128 totalBorrowAssets, uint128 totalBorrowShares, uint128 lastUpdate, uint128 fee)",
  "function idToMarketParams(bytes32 id) view returns (address loanToken, address collateralToken, address oracle, address irm, uint256 lltv)",
]);

// Interest Rate Model ABI
const IRM_ABI = parseAbi([
  "function borrowRateView((address loanToken, address collateralToken, address oracle, address irm, uint256 lltv) marketParams, (uint128 totalSupplyAssets, uint128 totalSupplyShares, uint128 totalBorrowAssets, uint128 totalBorrowShares, uint128 lastUpdate, uint128 fee) market) view returns (uint256)",
]);

// ERC20 ABI for token information
const ERC20_ABI = parseAbi([
  "function symbol() view returns (string)",
  "function name() view returns (string)",
  "function decimals() view returns (uint8)",
]);

type MarketParams = {
  loanToken: Address;
  collateralToken: Address;
  oracle: Address;
  irm: Address;
  lltv: bigint;
}

type MarketState = {
  totalSupplyAssets: bigint;
  totalSupplyShares: bigint;
  totalBorrowAssets: bigint;
  totalBorrowShares: bigint;
  lastUpdate: bigint;
  fee: bigint;
}

interface TokenInfo {
  address: Address;
  symbol: string;
  name: string;
  decimals: number;
}

interface MarketAPYInfo {
  marketId: `0x${string}`;
  params: MarketParams;
  state: MarketState;
  accruedState: MarketState;
  loanToken: TokenInfo;
  collateralToken: TokenInfo;
  lltvPercentage: number;
  borrowRate: bigint;
  borrowAPY: bigint;
  supplyAPY: bigint;
  utilization: bigint;
  borrowAPYPercentage: number;
  supplyAPYPercentage: number;
  utilizationPercentage: number;
  lastUpdateTime: Date;
  interestAccrued: bigint;
  blockTimestamp: bigint;
}

const WAD = 10n ** 18n;
const SECONDS_PER_YEAR = 31536000n;

const wMulDown = (x: bigint, y: bigint): bigint => (x * y) / WAD;
const wDivUp = (x: bigint, y: bigint): bigint => (x * WAD + y - 1n) / y;

const wTaylorCompounded = (x: bigint, n: bigint): bigint => {
  const firstTerm = x * n;
  const secondTerm = (firstTerm * firstTerm) / (2n * WAD);
  const thirdTerm = (secondTerm * firstTerm) / (3n * WAD);
  return firstTerm + secondTerm + thirdTerm;
};

/**
 * Formats a WAD-scaled value (18 decimals) to percentage
 */
function formatWADToPercentage(value: bigint): number {
  return Number(formatUnits(value, 16)); // 18 - 2 = 16 for percentage
}

/**
 * Formats LLTV from WAD format to percentage
 */
function formatLLTV(lltv: bigint): number {
  return Number(formatUnits(lltv, 18)) * 100;
}

/**
 * Fetches token information for a given address
 */
async function getTokenInfo(
  client: PublicClient,
  tokenAddress: Address
): Promise<TokenInfo> {
  try {
    const [symbol, name, decimals] = await client.multicall({
      contracts: [
        { address: tokenAddress, abi: ERC20_ABI, functionName: "symbol" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "name" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "decimals" },
      ],
      allowFailure: false,
    });

    return {
      address: tokenAddress,
      symbol,
      name,
      decimals,
    };
  } catch (error) {
    return {
      address: tokenAddress,
      symbol: `Token(${tokenAddress.slice(0, 6)}...)`,
      name: `Unknown Token ${tokenAddress.slice(0, 6)}...`,
      decimals: 18,
    };
  }
}

/**
 * Accrues interest on a market from its last update time to the current block's timestamp.
 * This is crucial for getting the real-time state of the market.
 */
function accrueInterests(
  marketState: MarketState,
  borrowRate: bigint,
  blockTimestamp: bigint
): { accruedState: MarketState; interestAccrued: bigint } {
  const elapsed = blockTimestamp - marketState.lastUpdate;
  
  if (elapsed === 0n || marketState.totalBorrowAssets === 0n) {
    return { 
      accruedState: marketState, 
      interestAccrued: 0n 
    };
  }

  const interest = wMulDown(
    marketState.totalBorrowAssets, 
    wTaylorCompounded(borrowRate, elapsed)
  );

  const accruedState = {
    ...marketState,
    totalSupplyAssets: marketState.totalSupplyAssets + interest,
    totalBorrowAssets: marketState.totalBorrowAssets + interest,
    lastUpdate: blockTimestamp,
  };

  return { accruedState, interestAccrued: interest };
}

/**
 * Calculates comprehensive market APY information including supply and borrow rates.
 */
export async function getMarketAPYInfo(
  client: PublicClient,
  marketId: `0x${string}`
): Promise<MarketAPYInfo> {
  console.log(`Fetching APY information for market: ${marketId}`);

  // Get current block timestamp
  const block = await client.getBlock({ blockTag: "latest" });
  const blockTimestamp = block.timestamp;

  // Get market state and parameters
  const [marketStateResult, marketParamsResult] = await client.multicall({
    contracts: [
      { address: MORPHO_BLUE_ADDRESS, abi: MORPHO_BLUE_ABI, functionName: "market", args: [marketId] },
      { address: MORPHO_BLUE_ADDRESS, abi: MORPHO_BLUE_ABI, functionName: "idToMarketParams", args: [marketId] },
    ],
    allowFailure: false,
  });

  const state: MarketState = {
    totalSupplyAssets: marketStateResult[0],
    totalSupplyShares: marketStateResult[1],
    totalBorrowAssets: marketStateResult[2],
    totalBorrowShares: marketStateResult[3],
    lastUpdate: marketStateResult[4],
    fee: marketStateResult[5],
  };

  const params: MarketParams = {
    loanToken: marketParamsResult[0],
    collateralToken: marketParamsResult[1],
    oracle: marketParamsResult[2],
    irm: marketParamsResult[3],
    lltv: marketParamsResult[4],
  };

  // Get token information
  const [loanToken, collateralToken] = await Promise.all([
    getTokenInfo(client, params.loanToken),
    getTokenInfo(client, params.collateralToken),
  ]);

  // Initialize default values
  let borrowRate = 0n;
  let borrowAPY = 0n;
  let supplyAPY = 0n;
  let utilization = 0n;
  let accruedState = state;
  let interestAccrued = 0n;

  // Calculate rates if IRM is set
  if (params.irm !== "0x0000000000000000000000000000000000000000") {
    // Get borrow rate from IRM
    borrowRate = await client.readContract({
      address: params.irm,
      abi: IRM_ABI,
      functionName: "borrowRateView",
      args: [params, state],
    }) as bigint;

    // Accrue interest to get current state
    const accrualResult = accrueInterests(state, borrowRate, blockTimestamp);
    accruedState = accrualResult.accruedState;
    interestAccrued = accrualResult.interestAccrued;

    // Calculate APYs
    borrowAPY = wTaylorCompounded(borrowRate, SECONDS_PER_YEAR);
    
    // Calculate utilization using accrued state
    if (accruedState.totalSupplyAssets > 0n) {
      utilization = wDivUp(accruedState.totalBorrowAssets, accruedState.totalSupplyAssets);
    }

    // Supply APY = Borrow APY * Utilization * (1 - Fee)
    supplyAPY = wMulDown(
      wMulDown(borrowAPY, utilization),
      WAD - accruedState.fee
    );
  }

  return {
    marketId,
    params,
    state,
    accruedState,
    loanToken,
    collateralToken,
    lltvPercentage: formatLLTV(params.lltv),
    borrowRate,
    borrowAPY,
    supplyAPY,
    utilization,
    borrowAPYPercentage: formatWADToPercentage(borrowAPY),
    supplyAPYPercentage: formatWADToPercentage(supplyAPY),
    utilizationPercentage: formatWADToPercentage(utilization),
    lastUpdateTime: new Date(Number(state.lastUpdate) * 1000),
    interestAccrued,
    blockTimestamp,
  };
}

/**
 * Calculates APY information for multiple markets efficiently
 */
export async function getMultipleMarketsAPY(
  client: PublicClient,
  marketIds: `0x${string}`[]
): Promise<MarketAPYInfo[]> {
  console.log(`Fetching APY information for ${marketIds.length} markets...`);

  const apyPromises = marketIds.map(marketId => 
    getMarketAPYInfo(client, marketId)
  );

  return Promise.all(apyPromises);
}

/**
 * Displays comprehensive market APY information
 */
export function displayMarketAPY(marketInfo: MarketAPYInfo): void {
  console.log("\n✅ --- Morpho Market APY Information --- ✅");

  console.log(`\n--- Market Overview ---`);
  console.log(`Market ID: ${marketInfo.marketId}`);
  console.log(`Loan Token: ${marketInfo.loanToken.name} (${marketInfo.loanToken.symbol})`);
  console.log(`Collateral Token: ${marketInfo.collateralToken.name} (${marketInfo.collateralToken.symbol})`);
  console.log(`LLTV: ${marketInfo.lltvPercentage.toFixed(2)}%`);

  console.log(`\n--- Market Liquidity (Real-time) ---`);
  console.log(`Total Supply: ${formatUnits(marketInfo.accruedState.totalSupplyAssets, marketInfo.loanToken.decimals)} ${marketInfo.loanToken.symbol}`);
  console.log(`Total Borrow: ${formatUnits(marketInfo.accruedState.totalBorrowAssets, marketInfo.loanToken.decimals)} ${marketInfo.loanToken.symbol}`);
  console.log(`Utilization: ${marketInfo.utilizationPercentage.toFixed(2)}%`);

  console.log(`\n--- Interest Rates ---`);
  console.log(`Borrow APY: ${marketInfo.borrowAPYPercentage.toFixed(4)}%`);
  console.log(`Supply APY: ${marketInfo.supplyAPYPercentage.toFixed(4)}%`);
  console.log(`Borrow Rate (per second): ${formatUnits(marketInfo.borrowRate, 18)}`);

  console.log(`\n--- Interest Accrual ---`);
  console.log(`Last Update: ${marketInfo.lastUpdateTime.toISOString()}`);
  console.log(`Interest Accrued: ${formatUnits(marketInfo.interestAccrued, marketInfo.loanToken.decimals)} ${marketInfo.loanToken.symbol}`);
  console.log(`Market Fee: ${formatWADToPercentage(marketInfo.state.fee).toFixed(4)}%`);

  console.log(`\n--- Raw Values (WAD) ---`);
  console.log(`Borrow APY: ${marketInfo.borrowAPY}`);
  console.log(`Supply APY: ${marketInfo.supplyAPY}`);
  console.log(`Utilization: ${marketInfo.utilization}`);

  console.log("\n----------------------------------------");
}

/**
 * Displays a summary table of multiple markets
 */
export function displayMarketsAPYSummary(markets: MarketAPYInfo[]): void {
  if (markets.length === 0) {
    console.log("No markets to display.");
    return;
  }

  console.log("\n✅ --- Markets APY Summary --- ✅");
  console.log("\nMarket ID                    | Loan/Collateral     | Borrow APY | Supply APY | Utilization");
  console.log("-----------------------------+---------------------+------------+------------+------------");

  markets.forEach((market) => {
    const shortId = `${market.marketId.slice(0, 8)}...${market.marketId.slice(-8)}`;
    const tokenPair = `${market.loanToken.symbol}/${market.collateralToken.symbol}`;
    const borrowAPY = `${market.borrowAPYPercentage.toFixed(2)}%`.padStart(10);
    const supplyAPY = `${market.supplyAPYPercentage.toFixed(2)}%`.padStart(10);
    const utilization = `${market.utilizationPercentage.toFixed(2)}%`.padStart(10);

    console.log(
      `${shortId.padEnd(28)} | ${tokenPair.padEnd(19)} | ${borrowAPY} | ${supplyAPY} | ${utilization}`
    );
  });

  console.log("\n----------------------------------------");
}

/**
 * Main function to demonstrate market APY calculations
 */
export async function main(): Promise<void> {
  try {
    const client = createMainnetClient();
    
    // Get APY information for the example market
    const marketAPY = await getMarketAPYInfo(client, EXAMPLE_MARKET_ID);
    
    // Display detailed results
    displayMarketAPY(marketAPY);
    
    // Example: Get APY for multiple markets (add more market IDs here)
    const multipleMarkets = [EXAMPLE_MARKET_ID];
    const marketsAPY = await getMultipleMarketsAPY(client, multipleMarkets);
    
    // Display summary
    displayMarketsAPYSummary(marketsAPY);
    
  } catch (error) {
    console.error("Error in market APY calculation:", error);
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
Fetching APY information for market: 0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64

✅ --- Morpho Market APY Information --- ✅

--- Market Overview ---
Market ID: 0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64
Loan Token: USD Coin (USDC)
Collateral Token: Coinbase Wrapped BTC (cbBTC)
LLTV: 86.00%

--- Market Liquidity (Real-time) ---
Total Supply: 522363906.351897 USDC
Total Borrow: 481268778.178246 USDC
Utilization: 92.13%

--- Interest Rates ---
Borrow APY: 7.5419%
Supply APY: 6.9486%
Borrow Rate (per second): 0.000000002305661164

--- Interest Accrual ---
Last Update: 2025-11-07T10:56:59.000Z
Interest Accrued: 0 USDC
Market Fee: 0.0000%

--- Raw Values (WAD) ---
Borrow APY: 75418869301348230
Supply APY: 69485557173609405
Utilization: 921328545724660480

----------------------------------------
Fetching APY information for 1 markets...
Fetching APY information for market: 0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64

✅ --- Markets APY Summary --- ✅

Market ID                    | Loan/Collateral     | Borrow APY | Supply APY | Utilization
-----------------------------+---------------------+------------+------------+------------
0x64d65c...883fcc64          | USDC/cbBTC          |      7.54% |      6.95% |     92.13%

----------------------------------------
```

This example shows how to calculate real-time market rates, including the crucial interest accrual step that updates market state from the last onchain update to the current block timestamp.

As it is important to accrue interests on the underlying markets, Morpho Association provided a library to accrue them onchain.
Feel free to refer to the [Morpho Market Snippets](https://github.com/morpho-org/morpho-snippets/blob/main/src/morpho-blue/MorphoBlueSnippets.sol) for extensive example.

```
/// @notice Calculates the supply APY (Annual Percentage Yield) for a given market.
    /// @param marketParams The parameters of the market.
    /// @param market The market for which the supply APY is being calculated.
    /// @return supplyApy The calculated supply APY (scaled by WAD).
    function supplyAPY(MarketParams memory marketParams, Market memory market)
        public
        view
        returns (uint256 supplyApy)
    {
        (uint256 totalSupplyAssets,, uint256 totalBorrowAssets,) = morpho.expectedMarketBalances(marketParams);

        // Get the borrow rate
        if (marketParams.irm != address(0)) {
            uint256 utilization = totalBorrowAssets == 0 ? 0 : totalBorrowAssets.wDivUp(totalSupplyAssets);
            supplyApy = borrowAPY(marketParams, market).wMulDown(1 ether - market.fee).wMulDown(utilization);
        }
    }

    /// @notice Calculates the borrow APY (Annual Percentage Yield) for a given market.
    /// @param marketParams The parameters of the market.
    /// @param market The state of the market.
    /// @return borrowApy The calculated borrow APY (scaled by WAD).
    function borrowAPY(MarketParams memory marketParams, Market memory market)
        public
        view
        returns (uint256 borrowApy)
    {
        if (marketParams.irm != address(0)) {
            borrowApy = IIrm(marketParams.irm).borrowRateView(marketParams, market).wTaylorCompounded(365 days);
        }
    }
```

### [Interactive Interest Rate Visualization](#interactive-interest-rate-visualization)

Understanding how the [AdaptiveCurveIRM](https://docs.morpho.org/learn/concepts/irm/#the-adaptivecurveirm) works in practice is crucial for developers integrating with Morpho Markets. This section provides a hands-on guide to implementing and visualizing the interest rate model calculations.

The Morpho protocol uses a kinked interest rate model (IRM) with a target utilization of 90%.

![IRM Breakdown](https://docs.morpho.org/img/build/borrow/irm-breakdown.png)
Below you'll find three approaches to working with this model: using the API, implementing it yourself, or understanding the mathematical foundation.

APIImplementationMath Model**Fetch Pre-Calculated Curve Data**

The easiest way to display the interest rate model is to use the Morpho API, which provides pre-calculated curve data with 101 data points (0% to 100% utilization).

---

**Step 1: Query the GraphQL Endpoint**

```
query GetMarketIrmCurve($marketId: String!, $chainId: Int!) {
  marketById(marketId: $marketId, chainId: $chainId) {
    marketId
    chain {
      id
    }
    irmAddress
    state {
      id
      utilization
    }
    currentIrmCurve {
      utilization
      supplyApy
      borrowApy
    }
  }
}
```

API Endpoint: [api.morpho.org/graphql](https://api.morpho.org/graphql)

This endpoint returns:

- Market identification data
- Current utilization state
- Pre-calculated interest rate curve with 101 data points

---

**Step 2: Integrate with Frontend Component**

```
const ChartInterestRateModelClient = ({ queryResult }) => {
  const marketData = queryResult?.data?.marketById;
  const shouldShowNoDataError = useMemo(
    () =>
      marketData?.currentIrmCurve?.length === 0 ||
      marketData?.irmAddress === undefined,
    [marketData?.currentIrmCurve?.length, marketData?.irmAddress]
  );

  return (
    <Card padding="s" grow={1}>
      <InterestRateModelChart
        statuses={{
          loading: false,
          error: shouldShowNoDataError,
        }}
        height="288px"
        data={marketData?.currentIrmCurve}
        irmAddress={marketData?.irmAddress}
        utilization={marketData?.state?.utilization ?? 0}
      />
    </Card>
  );
};
```

**Benefits of API Approach:**

- No need to implement rate calculations
- Pre-calculated data optimized for visualization
- Always up-to-date with latest protocol parameters
- Minimal code required for integration

**Build Your Own Rate Calculator**

For developers who need to calculate rates independently or integrate calculations into backend systems, you can implement the algorithm directly.

---

**Step 1: Core Algorithm**

The interest rate calculation formula:

```
function rateAtUtilization(apyAtTarget, utilization, fee) {
  let borrowApy;
  const minApy = Math.expm1(Math.log1p(apyAtTarget) / 4);
  const maxApy = Math.expm1(Math.log1p(apyAtTarget) * 4);

  if (utilization <= 0.9) {
    borrowApy = minApy + (apyAtTarget - minApy) * (utilization / 0.9);
  } else {
    borrowApy =
      ((maxApy - apyAtTarget) / 0.1) * (utilization - 0.9) + apyAtTarget;
  }

  const supplyApy = borrowApy * (1 - fee) * utilization;

  return {
    borrowApy,
    supplyApy,
  };
}
```

---

**Step 2: Required Parameters**
To use this function, you need:

1. **`apyAtTarget`**: The target borrow APY at 90% utilization

  - This is derived from the `rateAtTarget` value stored in the [AdaptiveCurveIRM contract](https://docs.morpho.org/get-started/resources/contracts/irm/#mappings)
  - Retrieve `rateAtTarget` for your market's IRM from the contract
  - Convert to APY using: `apyAtTarget = (e^(rateAtTarget × secondsPerYear) - 1)`
  - Example: If `rateAtTarget = 1512768697` (per second rate), this converts to approximately 4.9% APY
2. **`utilization`**: Current utilization ratio (0 to 1)

  - Calculate as: `totalBorrow / totalSupply`
  - Use for calculating rates at specific points
3. **`fee`**: Protocol fee percentage (e.g., 0.1 for 10%)

  - Check [market state](https://docs.morpho.org/get-started/resources/contracts/morpho/#market-struct) for the exact fee
  - This affects the supply APY calculation

---

**Step 3: Generate Curve Data**

```
// Generate 101 data points for visualization
const generateCurveData = (apyAtTarget, fee) => {
  const dataPoints = [];
  for (let i = 0; i <= 100; i++) {
    const utilization = i / 100;
    const { borrowApy, supplyApy } = rateAtUtilization(
      apyAtTarget,
      utilization,
      fee
    );
    dataPoints.push({
      utilization,
      borrowApy,
      supplyApy
    });
  }
  return dataPoints;
};
```

**Use Cases for Direct Implementation:**

- Real-time rate calculations in smart contracts
- Custom analytics and modeling
- Integration with proprietary systems
- Independent verification of API data

**Understanding the Kinked Interest Rate Model**

The AdaptiveCurveIRM uses a two-slope (kinked) model with distinct behavior before and after the target utilization.

---

**Key Parameters**

1. **Target Utilization**: 90% (the kink point)
2. **APY Range**: From minApy (~1/4 target) to maxApy (~4x target)
3. **Formula Elements**:

  - `minApy = Math.expm1(Math.log1p(apyAtTarget) / 4)`
  - `maxApy = Math.expm1(Math.log1p(apyAtTarget) * 4)`

---

**Two-Slope Behavior**

**Below Target (0% - 90% utilization):**

```
borrowApy = minApy + (apyAtTarget - minApy) * (utilization / 0.9)
```

- Linear increase from minApy to apyAtTarget
- Gentle slope to encourage borrowing
- Supply rates gradually increase with utilization

**Above Target (90% - 100% utilization):**

```
borrowApy = ((maxApy - apyAtTarget) / 0.1) * (utilization - 0.9) + apyAtTarget
```

- Steeper linear increase to maxApy
- Discourages over-utilization
- Incentivizes suppliers at high utilization

---

**Mathematical Properties at Key Points**

**At 0% utilization:**

- Borrow APY = minApy (~1/4 of target APY)
- Supply APY = 0 (as utilization is 0)
- Lowest rates to attract initial borrowers

**At 90% utilization (target):**

- Borrow APY = apyAtTarget
- Supply APY = apyAtTarget × (1 - fee) × 0.9
- Optimal balance point for the market

**At 100% utilization:**

- Borrow APY = maxApy (~4x target APY)
- Supply APY = maxApy × (1 - fee)
- Maximum rates to incentivize supply

**Supply APY Formula:**

```
supplyApy = borrowApy × (1 - fee) × utilization
```

- Protocol fee is deducted from borrow interest
- Supply APY scales with utilization

For more on the AdaptiveCurveIRM, explore the [technical reference](https://docs.morpho.org/get-started/resources/contracts/irm/).

## [Asset Information](#asset-information)

### [Assets](#assets)

APITypescript - ViemGet metadata and pricing for specific tokens.

---

API
```
query GetAssetsWithPriceAndYield {
  assets(where: { symbol_in: ["wstETH", "WETH"], chainId_in: [1] }) {
    items {
      symbol
      address
      price(maxLag: 12) {
        usd
        timestamp
      }
      yield {
        apr
        lookback
      }
      chain {
        id
        network
      }
    }
  }
}
```

This example demonstrates comprehensive asset information retrieval including:

- Basic ERC20 metadata (name, symbol, decimals, total supply)
- Asset validation and error handling for invalid tokens
- EIP-2612 permit support detection for gasless approvals
- User balance and allowance tracking
- Portfolio analysis across multiple assets
- Efficient batch processing using multicall
- Formatted display with large number abbreviations (K, M, B, T)

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

// Example token addresses for demonstration
const EXAMPLE_ASSETS: Address[] = [
  "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
  "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", // WETH
  "0xdAC17F958D2ee523a2206206994597C13D831ec7", // USDT
  "0x6B175474E89094C44Da98b954EedeAC495271d0F", // DAI
  "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", // WBTC
];

// Comprehensive ERC20 ABI for asset information
const ERC20_ABI = parseAbi([
  "function name() view returns (string)",
  "function symbol() view returns (string)",
  "function decimals() view returns (uint8)",
  "function totalSupply() view returns (uint256)",
  "function balanceOf(address account) view returns (uint256)",
  "function allowance(address owner, address spender) view returns (uint256)",
]);

// Optional: Extended ERC20 ABI for additional metadata (some tokens support these)
const EXTENDED_ERC20_ABI = parseAbi([
  "function version() view returns (string)",
  "function DOMAIN_SEPARATOR() view returns (bytes32)",
  "function nonces(address owner) view returns (uint256)",
]);

interface AssetInfo {
  address: Address;
  name: string;
  symbol: string;
  decimals: number;
  totalSupply: bigint;
  formattedTotalSupply: string;
  // Optional extended info
  version?: string;
  domainSeparator?: `0x${string}`;
  supportsPermit: boolean;
  isValid: boolean;
  error?: string;
}

interface AssetBalance {
  asset: AssetInfo;
  balance: bigint;
  formattedBalance: string;
  allowance?: bigint;
  formattedAllowance?: string;
}

interface AssetPortfolio {
  userAddress: Address;
  assets: AssetBalance[];
  totalAssetsCount: number;
  validAssetsCount: number;
  invalidAssetsCount: number;
}

/**
 * Checks if an address is a valid ERC20 token by attempting to call basic functions
 */
async function isValidERC20(
  client: PublicClient,
  tokenAddress: Address
): Promise<boolean> {
  try {
    await client.multicall({
      contracts: [
        { address: tokenAddress, abi: ERC20_ABI, functionName: "name" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "symbol" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "decimals" },
      ],
      allowFailure: false,
    });
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Checks if a token supports EIP-2612 permit functionality
 */
async function supportsPermit(
  client: PublicClient,
  tokenAddress: Address
): Promise<boolean> {
  try {
    await client.readContract({
      address: tokenAddress,
      abi: EXTENDED_ERC20_ABI,
      functionName: "DOMAIN_SEPARATOR",
    });
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Formats large numbers with appropriate suffixes (K, M, B, T)
 */
function formatLargeNumber(value: string): string {
  const num = parseFloat(value);
  if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
  if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
  if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`;
  return num.toFixed(6);
}

/**
 * Retrieves comprehensive information about a single asset
 */
export async function getAssetInfo(
  client: PublicClient,
  tokenAddress: Address
): Promise<AssetInfo> {
  try {
    // First check if it's a valid ERC20
    const isValid = await isValidERC20(client, tokenAddress);
    
    if (!isValid) {
      return {
        address: tokenAddress,
        name: "Invalid Token",
        symbol: "INVALID",
        decimals: 0,
        totalSupply: 0n,
        formattedTotalSupply: "0",
        supportsPermit: false,
        isValid: false,
        error: "Not a valid ERC20 token",
      };
    }

    // Get basic ERC20 information
    const [name, symbol, decimals, totalSupply] = await client.multicall({
      contracts: [
        { address: tokenAddress, abi: ERC20_ABI, functionName: "name" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "symbol" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "decimals" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "totalSupply" },
      ],
      allowFailure: false,
    });

    // Check for permit support and get extended info
    const [hasPermit, version, domainSeparator] = await Promise.all([
      supportsPermit(client, tokenAddress),
      client.readContract({
        address: tokenAddress,
        abi: EXTENDED_ERC20_ABI,
        functionName: "version",
      }).catch(() => undefined),
      client.readContract({
        address: tokenAddress,
        abi: EXTENDED_ERC20_ABI,
        functionName: "DOMAIN_SEPARATOR",
      }).catch(() => undefined),
    ]);

    const formattedTotalSupply = formatUnits(totalSupply, decimals);

    return {
      address: tokenAddress,
      name,
      symbol,
      decimals,
      totalSupply,
      formattedTotalSupply,
      version: version as string | undefined,
      domainSeparator: domainSeparator as `0x${string}` | undefined,
      supportsPermit: hasPermit,
      isValid: true,
    };

  } catch (error) {
    return {
      address: tokenAddress,
      name: "Error",
      symbol: "ERROR",
      decimals: 0,
      totalSupply: 0n,
      formattedTotalSupply: "0",
      supportsPermit: false,
      isValid: false,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

/**
 * Retrieves asset information for multiple tokens efficiently
 */
export async function getMultipleAssetsInfo(
  client: PublicClient,
  tokenAddresses: Address[]
): Promise<AssetInfo[]> {
  console.log(`Fetching information for ${tokenAddresses.length} assets...`);

  const assetPromises = tokenAddresses.map(address => 
    getAssetInfo(client, address)
  );

  return Promise.all(assetPromises);
}

/**
 * Gets asset balances and allowances for a specific user
 */
export async function getAssetBalance(
  client: PublicClient,
  tokenAddress: Address,
  userAddress: Address,
  spenderAddress?: Address
): Promise<AssetBalance> {
  const assetInfo = await getAssetInfo(client, tokenAddress);
  
  if (!assetInfo.isValid) {
    return {
      asset: assetInfo,
      balance: 0n,
      formattedBalance: "0",
    };
  }

  try {
    const balance = await client.readContract({
      address: tokenAddress,
      abi: ERC20_ABI,
      functionName: "balanceOf",
      args: [userAddress],
    }) as bigint;

    let allowance: bigint | undefined;
    let formattedAllowance: string | undefined;

    if (spenderAddress) {
      allowance = await client.readContract({
        address: tokenAddress,
        abi: ERC20_ABI,
        functionName: "allowance",
        args: [userAddress, spenderAddress],
      }) as bigint;
      formattedAllowance = formatUnits(allowance, assetInfo.decimals);
    }

    return {
      asset: assetInfo,
      balance,
      formattedBalance: formatUnits(balance, assetInfo.decimals),
      allowance,
      formattedAllowance,
    };

  } catch (error) {
    return {
      asset: {
        ...assetInfo,
        isValid: false,
        error: `Balance fetch failed: ${error instanceof Error ? error.message : "Unknown error"}`,
      },
      balance: 0n,
      formattedBalance: "0",
    };
  }
}

/**
 * Creates a complete asset portfolio for a user
 */
export async function getUserAssetPortfolio(
  client: PublicClient,
  userAddress: Address,
  tokenAddresses: Address[],
  spenderAddress?: Address
): Promise<AssetPortfolio> {
  console.log(`Fetching asset portfolio for user: ${userAddress}`);

  const balancePromises = tokenAddresses.map(tokenAddress =>
    getAssetBalance(client, tokenAddress, userAddress, spenderAddress)
  );

  const assets = await Promise.all(balancePromises);

  const validAssets = assets.filter(asset => asset.asset.isValid);
  const invalidAssets = assets.filter(asset => !asset.asset.isValid);

  return {
    userAddress,
    assets,
    totalAssetsCount: assets.length,
    validAssetsCount: validAssets.length,
    invalidAssetsCount: invalidAssets.length,
  };
}

/**
 * Displays comprehensive asset information
 */
export function displayAssetInfo(assetInfo: AssetInfo): void {
  console.log("\n✅ --- Asset Information --- ✅");
  
  console.log(`\n--- Basic Info ---`);
  console.log(`Address: ${assetInfo.address}`);
  console.log(`Name: ${assetInfo.name}`);
  console.log(`Symbol: ${assetInfo.symbol}`);
  console.log(`Decimals: ${assetInfo.decimals}`);
  console.log(`Valid ERC20: ${assetInfo.isValid ? "✅ Yes" : "❌ No"}`);
  
  if (assetInfo.error) {
    console.log(`Error: ${assetInfo.error}`);
  }

  if (assetInfo.isValid) {
    console.log(`\n--- Supply Info ---`);
    console.log(`Total Supply: ${assetInfo.formattedTotalSupply} ${assetInfo.symbol}`);
    console.log(`Total Supply (formatted): ${formatLargeNumber(assetInfo.formattedTotalSupply)} ${assetInfo.symbol}`);
    console.log(`Total Supply (raw): ${assetInfo.totalSupply}`);

    console.log(`\n--- Extended Features ---`);
    console.log(`Supports Permit (EIP-2612): ${assetInfo.supportsPermit ? "✅ Yes" : "❌ No"}`);
    if (assetInfo.version) {
      console.log(`Version: ${assetInfo.version}`);
    }
    if (assetInfo.domainSeparator) {
      console.log(`Domain Separator: ${assetInfo.domainSeparator}`);
    }
  }

  console.log("\n----------------------------------------");
}

/**
 * Displays a summary table of multiple assets
 */
export function displayAssetsTable(assets: AssetInfo[]): void {
  console.log("\n✅ --- Assets Summary Table --- ✅");
  
  const validAssets = assets.filter(asset => asset.isValid);
  const invalidAssets = assets.filter(asset => !asset.isValid);

  console.log(`\nValid Assets: ${validAssets.length} | Invalid Assets: ${invalidAssets.length}`);
  
  if (validAssets.length > 0) {
    console.log("\n--- Valid Assets ---");
    console.log("Symbol       | Name                    | Decimals | Total Supply       | Permit");
    console.log("-------------+-------------------------+----------+--------------------+-------");
    
    validAssets.forEach(asset => {
      const symbol = asset.symbol.padEnd(12);
      const name = asset.name.length > 23 ? asset.name.slice(0, 20) + "..." : asset.name.padEnd(23);
      const decimals = asset.decimals.toString().padStart(8);
      const supply = formatLargeNumber(asset.formattedTotalSupply).padStart(18);
      const permit = asset.supportsPermit ? "  ✅" : "  ❌";
      
      console.log(`${symbol} | ${name} | ${decimals} | ${supply} | ${permit}`);
    });
  }

  if (invalidAssets.length > 0) {
    console.log("\n--- Invalid Assets ---");
    invalidAssets.forEach(asset => {
      console.log(`❌ ${asset.address}: ${asset.error || "Invalid ERC20"}`);
    });
  }
  
  console.log("\n----------------------------------------");
}

/**
 * Displays user asset portfolio
 */
export function displayAssetPortfolio(portfolio: AssetPortfolio): void {
  console.log("\n✅ --- User Asset Portfolio --- ✅");
  
  console.log(`\n--- Portfolio Overview ---`);
  console.log(`User Address: ${portfolio.userAddress}`);
  console.log(`Total Assets: ${portfolio.totalAssetsCount}`);
  console.log(`Valid Assets: ${portfolio.validAssetsCount}`);
  console.log(`Invalid Assets: ${portfolio.invalidAssetsCount}`);

  const assetsWithBalance = portfolio.assets.filter(asset => 
    asset.asset.isValid && asset.balance > 0n
  );

  if (assetsWithBalance.length > 0) {
    console.log(`\n--- Assets with Balance ---`);
    console.log("Symbol       | Balance              | Allowance (if set)");
    console.log("-------------+----------------------+-------------------");
    
    assetsWithBalance.forEach(assetBalance => {
      const symbol = assetBalance.asset.symbol.padEnd(12);
      const balance = parseFloat(assetBalance.formattedBalance).toLocaleString('en-US', {
        maximumFractionDigits: 6,
      }).padStart(20);
      const allowance = assetBalance.formattedAllowance 
        ? parseFloat(assetBalance.formattedAllowance).toLocaleString('en-US', {
            maximumFractionDigits: 6,
          })
        : "Not checked";
      
      console.log(`${symbol} | ${balance} | ${allowance}`);
    });
  } else {
    console.log(`\n--- No assets with balance found ---`);
  }

  console.log("\n----------------------------------------");
}

/**
 * Main function to demonstrate asset information retrieval
 */
export async function main(): Promise<void> {
  try {
    const client = createMainnetClient();
    
    console.log("=== Asset Information Demo ===\n");
    
    // Demo 1: Get information for a single asset
    console.log("1. Single Asset Info (USDC):");
    const usdcInfo = await getAssetInfo(client, EXAMPLE_ASSETS[0]);
    displayAssetInfo(usdcInfo);
    
    // Demo 2: Get information for multiple assets
    console.log("\n2. Multiple Assets Info:");
    const assetsInfo = await getMultipleAssetsInfo(client, EXAMPLE_ASSETS);
    displayAssetsTable(assetsInfo);
    
    // Demo 3: Get user portfolio (example with zero address - will show zero balances)
    console.log("\n3. User Portfolio (Zero Address - for demo):");
    const zeroAddress = "0x0000000000000000000000000000000000000000";
    const portfolio = await getUserAssetPortfolio(client, zeroAddress, EXAMPLE_ASSETS.slice(0, 3));
    displayAssetPortfolio(portfolio);
    
    console.log("\n=== Demo Complete ===");
    
  } catch (error) {
    console.error("Error in asset information script:", error);
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
=== Asset Information Demo ===

1. Single Asset Info (USDC):

✅ --- Asset Information --- ✅

--- Basic Info ---
Address: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
Name: USD Coin
Symbol: USDC
Decimals: 6
Valid ERC20: ✅ Yes

--- Supply Info ---
Total Supply: 41233587998.984993 USDC
Total Supply (formatted): 41.23B USDC
Total Supply (raw): 41233587998984993

--- Extended Features ---
Supports Permit (EIP-2612): ✅ Yes
Version: 2
Domain Separator: 0x06c37168a7db5138defc7866392bb87a741f9b3d104deb5094588ce041cae335

----------------------------------------

2. Multiple Assets Info:
Fetching information for 5 assets...

✅ --- Assets Summary Table --- ✅

Valid Assets: 5 | Invalid Assets: 0

--- Valid Assets ---
Symbol       | Name                    | Decimals | Total Supply       | Permit
-------------+-------------------------+----------+--------------------+-------
USDC         | USD Coin                |        6 |             41.23B |   ✅
WETH         | Wrapped Ether           |       18 |              2.54M |   ❌
USDT         | Tether USD              |        6 |             74.81B |   ❌
DAI          | Dai Stablecoin          |       18 |              3.64B |   ✅
WBTC         | Wrapped BTC             |        8 |            128.85K |   ❌

----------------------------------------

3. User Portfolio (Zero Address - for demo):
Fetching asset portfolio for user: 0x0000000000000000000000000000000000000000

✅ --- User Asset Portfolio --- ✅

--- Portfolio Overview ---
User Address: 0x0000000000000000000000000000000000000000
Total Assets: 3
Valid Assets: 3
Invalid Assets: 0

--- Assets with Balance ---
Symbol       | Balance              | Allowance (if set)
-------------+----------------------+-------------------
WETH         |         1,086.556748 | Not checked
USDT         |       201,290.112228 | Not checked

----------------------------------------

=== Demo Complete ===
```

This example provides complete asset analysis capabilities essential for DeFi applications, including validation, metadata extraction, and portfolio management.

## [Position Tracking](#position-tracking)

### [User Position on Market](#user-position-on-market)

APITypescript - ViemAPI
```
query {
  marketPositions(
    first: 10,
    orderBy: BorrowShares,
    orderDirection: Desc
    where: {
      marketUniqueKey_in: ["0x698fe98247a40c5771537b5786b2f3f9d78eb487b4ce4d75533cd0e94d88a115"]
    }
  ) {
    items {
      user { address }
      state {
        collateral
        borrowAssets
        borrowAssetsUsd
      }
    }
  }
}
```

This example demonstrates comprehensive user position analysis including:

- Real-time interest accrual for accurate borrow/supply amounts
- Health factor calculation with liquidation risk assessment
- Collateral valuation using oracle prices
- Position safety metrics (LTV, liquidation buffer, liquidation price)
- Multiple market position tracking and portfolio analysis
- Conversion between shares and assets with proper rounding
- Risk assessment and liquidation threshold calculations

User positions require real-time interest accrual to show accurate debt amounts. The raw `position()` function returns shares, which must be converted to assets using current market state for precise calculations.

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

// Morpho V1 contract address
const MORPHO_BLUE_ADDRESS: Address = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb";

// Example user and market for demonstration
const EXAMPLE_USER: Address = "0x4352Cc849b33a936Ad93bB109aFDec1c89653b4f";
const EXAMPLE_MARKET_ID: `0x${string}` = "0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64";

// Morpho V1 ABI for user position operations
const MORPHO_BLUE_ABI = parseAbi([
  "function market(bytes32 id) view returns (uint128 totalSupplyAssets, uint128 totalSupplyShares, uint128 totalBorrowAssets, uint128 totalBorrowShares, uint128 lastUpdate, uint128 fee)",
  "function idToMarketParams(bytes32 id) view returns (address loanToken, address collateralToken, address oracle, address irm, uint256 lltv)",
  "function position(bytes32 id, address user) view returns (uint256 supplyShares, uint128 borrowShares, uint128 collateral)",
]);

// Interest Rate Model ABI
const IRM_ABI = parseAbi([
  "function borrowRateView((address loanToken, address collateralToken, address oracle, address irm, uint256 lltv) marketParams, (uint128 totalSupplyAssets, uint128 totalSupplyShares, uint128 totalBorrowAssets, uint128 totalBorrowShares, uint128 lastUpdate, uint128 fee) market) view returns (uint256)",
]);

// Oracle ABI
const ORACLE_ABI = parseAbi([
  "function price() view returns (uint256)",
]);

// ERC20 ABI for token information
const ERC20_ABI = parseAbi([
  "function symbol() view returns (string)",
  "function name() view returns (string)",
  "function decimals() view returns (uint8)",
]);

type MarketParams = {
  loanToken: Address;
  collateralToken: Address;
  oracle: Address;
  irm: Address;
  lltv: bigint;
}

type MarketState = {
  totalSupplyAssets: bigint;
  totalSupplyShares: bigint;
  totalBorrowAssets: bigint;
  totalBorrowShares: bigint;
  lastUpdate: bigint;
  fee: bigint;
}

type UserPosition = {
  supplyShares: bigint;
  borrowShares: bigint;
  collateral: bigint;
}

type TokenInfo = {
  address: Address;
  symbol: string;
  name: string;
  decimals: number;
}

interface UserPositionInfo {
  user: Address;
  marketId: `0x${string}`;
  marketParams: MarketParams;
  staleMarketState: MarketState;
  currentMarketState: MarketState;
  rawPosition: UserPosition;
  loanToken: TokenInfo;
  collateralToken: TokenInfo;
  lltvPercentage: number;
  
  // User-specific calculated values (real-time with accrued interest)
  supplyAssets: bigint;
  borrowAssets: bigint;
  collateralAssets: bigint;
  
  // Formatted values
  formattedSupplyAssets: string;
  formattedBorrowAssets: string;
  formattedCollateralAssets: string;
  
  // Health metrics
  collateralPrice: bigint;
  maxBorrow: bigint;
  healthFactor: bigint;
  isHealthy: boolean;
  liquidationBuffer: bigint;
  currentLTV: number;
  maxLTV: number;
  
  // Risk metrics
  utilizationOfCollateral: number;
  liquidationPrice: bigint;
  
  // Interest accrual info
  interestAccrued: bigint;
  formattedInterestAccrued: string;
  lastUpdateTime: Date;
  blockTimestamp: bigint;
}

const WAD = 10n ** 18n;
const VIRTUAL_ASSETS = 1n;
const VIRTUAL_SHARES = 10n ** 6n;
const ORACLE_PRICE_SCALE = 10n ** 36n;
const MAX_UINT256 = 2n ** 256n - 1n;

const wMulDown = (x: bigint, y: bigint): bigint => (x * y) / WAD;
const wDivUp = (x: bigint, y: bigint): bigint => (x * WAD + y - 1n) / y;
const wDivDown = (x: bigint, y: bigint): bigint => (x * WAD) / y;
const mulDivDown = (x: bigint, y: bigint, z: bigint): bigint => (x * y) / z;
const mulDivUp = (x: bigint, y: bigint, z: bigint): bigint => (x * y + z - 1n) / z;

const wTaylorCompounded = (x: bigint, n: bigint): bigint => {
  const firstTerm = x * n;
  const secondTerm = (firstTerm * firstTerm) / (2n * WAD);
  const thirdTerm = (secondTerm * firstTerm) / (3n * WAD);
  return firstTerm + secondTerm + thirdTerm;
};

/** Converts shares to assets (rounding down for supply, up for borrow) */
const toAssetsDown = (shares: bigint, totalAssets: bigint, totalShares: bigint): bigint => {
  if (totalShares === 0n) return shares;
  return mulDivDown(shares, totalAssets + VIRTUAL_ASSETS, totalShares + VIRTUAL_SHARES);
};

const toAssetsUp = (shares: bigint, totalAssets: bigint, totalShares: bigint): bigint => {
  if (totalShares === 0n) return shares;
  return mulDivUp(shares, totalAssets + VIRTUAL_ASSETS, totalShares + VIRTUAL_SHARES);
};

/**
 * Formats LLTV from WAD format to percentage
 */
function formatLLTV(lltv: bigint): number {
  return Number(formatUnits(lltv, 18)) * 100;
}

/**
 * Fetches token information for a given address
 */
async function getTokenInfo(
  client: PublicClient,
  tokenAddress: Address
): Promise<TokenInfo> {
  try {
    const [symbol, name, decimals] = await client.multicall({
      contracts: [
        { address: tokenAddress, abi: ERC20_ABI, functionName: "symbol" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "name" },
        { address: tokenAddress, abi: ERC20_ABI, functionName: "decimals" },
      ],
      allowFailure: false,
    });

    return {
      address: tokenAddress,
      symbol,
      name,
      decimals,
    };
  } catch (error) {
    return {
      address: tokenAddress,
      symbol: `Token(${tokenAddress.slice(0, 6)}...)`,
      name: `Unknown Token ${tokenAddress.slice(0, 6)}...`,
      decimals: 18,
    };
  }
}

/**
 * Accrues interest on a market from its last update time to current block timestamp
 */
function accrueInterests(
  marketState: MarketState,
  borrowRate: bigint,
  blockTimestamp: bigint
): { accruedState: MarketState; interestAccrued: bigint } {
  const elapsed = blockTimestamp - marketState.lastUpdate;
  
  if (elapsed === 0n || marketState.totalBorrowAssets === 0n) {
    return { 
      accruedState: marketState, 
      interestAccrued: 0n 
    };
  }

  const interest = wMulDown(
    marketState.totalBorrowAssets, 
    wTaylorCompounded(borrowRate, elapsed)
  );

  const accruedState = {
    ...marketState,
    totalSupplyAssets: marketState.totalSupplyAssets + interest,
    totalBorrowAssets: marketState.totalBorrowAssets + interest,
    lastUpdate: blockTimestamp,
  };

  return { accruedState, interestAccrued: interest };
}

/**
 * Retrieves comprehensive user position information with real-time interest accrual
 */
export async function getUserPositionInfo(
  client: PublicClient,
  userAddress: Address,
  marketId: `0x${string}`
): Promise<UserPositionInfo> {
  console.log(`Fetching position for user: ${userAddress} in market: ${marketId}`);

  // Get current block timestamp
  const block = await client.getBlock({ blockTag: "latest" });
  const blockTimestamp = block.timestamp;

  // Get market data, parameters, and user position
  const [marketStateResult, marketParamsResult, positionResult] = await client.multicall({
    contracts: [
      { address: MORPHO_BLUE_ADDRESS, abi: MORPHO_BLUE_ABI, functionName: "market", args: [marketId] },
      { address: MORPHO_BLUE_ADDRESS, abi: MORPHO_BLUE_ABI, functionName: "idToMarketParams", args: [marketId] },
      { address: MORPHO_BLUE_ADDRESS, abi: MORPHO_BLUE_ABI, functionName: "position", args: [marketId, userAddress] },
    ],
    allowFailure: false,
  });

  const staleMarketState: MarketState = {
    totalSupplyAssets: marketStateResult[0],
    totalSupplyShares: marketStateResult[1],
    totalBorrowAssets: marketStateResult[2],
    totalBorrowShares: marketStateResult[3],
    lastUpdate: marketStateResult[4],
    fee: marketStateResult[5],
  };

  const marketParams: MarketParams = {
    loanToken: marketParamsResult[0],
    collateralToken: marketParamsResult[1],
    oracle: marketParamsResult[2],
    irm: marketParamsResult[3],
    lltv: marketParamsResult[4],
  };

  const rawPosition: UserPosition = {
    supplyShares: positionResult[0],
    borrowShares: positionResult[1],
    collateral: positionResult[2],
  };

  // Get token information
  const [loanToken, collateralToken] = await Promise.all([
    getTokenInfo(client, marketParams.loanToken),
    getTokenInfo(client, marketParams.collateralToken),
  ]);

  // Initialize values
  let currentMarketState = staleMarketState;
  let interestAccrued = 0n;

  // Calculate current state with interest accrual if IRM is set
  if (marketParams.irm !== "0x0000000000000000000000000000000000000000") {
    // Get borrow rate from IRM
    const borrowRate = await client.readContract({
      address: marketParams.irm,
      abi: IRM_ABI,
      functionName: "borrowRateView",
      args: [marketParams, staleMarketState],
    }) as bigint;

    // Accrue interest to get current state
    const accrualResult = accrueInterests(staleMarketState, borrowRate, blockTimestamp);
    currentMarketState = accrualResult.accruedState;
    interestAccrued = accrualResult.interestAccrued;
  }

  // Calculate user's real-time asset amounts
  const supplyAssets = toAssetsDown(
    rawPosition.supplyShares,
    currentMarketState.totalSupplyAssets,
    currentMarketState.totalSupplyShares
  );

  const borrowAssets = toAssetsUp(
    rawPosition.borrowShares,
    currentMarketState.totalBorrowAssets,
    currentMarketState.totalBorrowShares
  );

  const collateralAssets = rawPosition.collateral;

  // Get collateral price and calculate health metrics
  let collateralPrice = 0n;
  let maxBorrow = 0n;
  let healthFactor = MAX_UINT256;
  let isHealthy = true;
  let liquidationPrice = 0n;

  if (marketParams.oracle !== "0x0000000000000000000000000000000000000000") {
    collateralPrice = await client.readContract({
      address: marketParams.oracle,
      abi: ORACLE_ABI,
      functionName: "price",
    }) as bigint;

    // Calculate maximum borrowing capacity
    maxBorrow = wMulDown(
      mulDivDown(collateralAssets, collateralPrice, ORACLE_PRICE_SCALE),
      marketParams.lltv
    );

    // Calculate health factor
    if (borrowAssets > 0n) {
      healthFactor = wDivDown(maxBorrow, borrowAssets);
      isHealthy = healthFactor >= WAD;
      
      // Calculate liquidation price (price at which position becomes unhealthy)
      if (collateralAssets > 0n) {
        liquidationPrice = mulDivUp(
          borrowAssets * ORACLE_PRICE_SCALE,
          WAD,
          mulDivDown(collateralAssets, marketParams.lltv, WAD)
        );
      }
    }
  }

  // Calculate additional metrics
  const liquidationBuffer = maxBorrow > borrowAssets ? maxBorrow - borrowAssets : 0n;
  const currentLTV = maxBorrow > 0n ? Number(wDivDown(borrowAssets, mulDivDown(collateralAssets, collateralPrice, ORACLE_PRICE_SCALE))) / 1e18 * 100 : 0;
  const maxLTV = formatLLTV(marketParams.lltv);
  const utilizationOfCollateral = maxBorrow > 0n ? Number(wDivDown(borrowAssets, maxBorrow)) / 1e18 * 100 : 0;

  return {
    user: userAddress,
    marketId,
    marketParams,
    staleMarketState,
    currentMarketState,
    rawPosition,
    loanToken,
    collateralToken,
    lltvPercentage: maxLTV,
    supplyAssets,
    borrowAssets,
    collateralAssets,
    formattedSupplyAssets: formatUnits(supplyAssets, loanToken.decimals),
    formattedBorrowAssets: formatUnits(borrowAssets, loanToken.decimals),
    formattedCollateralAssets: formatUnits(collateralAssets, collateralToken.decimals),
    collateralPrice,
    maxBorrow,
    healthFactor,
    isHealthy,
    liquidationBuffer,
    currentLTV,
    maxLTV,
    utilizationOfCollateral,
    liquidationPrice,
    interestAccrued,
    formattedInterestAccrued: formatUnits(interestAccrued, loanToken.decimals),
    lastUpdateTime: new Date(Number(staleMarketState.lastUpdate) * 1000),
    blockTimestamp,
  };
}

/**
 * Checks if user has any position in the market
 */
export async function hasPosition(
  client: PublicClient,
  userAddress: Address,
  marketId: `0x${string}`
): Promise<boolean> {
  const position = await client.readContract({
    address: MORPHO_BLUE_ADDRESS,
    abi: MORPHO_BLUE_ABI,
    functionName: "position",
    args: [marketId, userAddress],
  }) as [bigint, bigint, bigint];

  return position[0] > 0n || position[1] > 0n || position[2] > 0n;
}

/**
 * Gets user positions across multiple markets efficiently
 */
export async function getUserPositionsInMarkets(
  client: PublicClient,
  userAddress: Address,
  marketIds: `0x${string}`[]
): Promise<UserPositionInfo[]> {
  console.log(`Fetching positions for user ${userAddress} across ${marketIds.length} markets...`);

  const positionPromises = marketIds.map(marketId =>
    getUserPositionInfo(client, userAddress, marketId)
  );

  const allPositions = await Promise.all(positionPromises);
  
  // Filter out positions with no assets
  return allPositions.filter(position =>
    position.supplyAssets > 0n || position.borrowAssets > 0n || position.collateralAssets > 0n
  );
}

/**
 * Displays comprehensive user position information
 */
export function displayUserPosition(positionInfo: UserPositionInfo): void {
  console.log("\n✅ --- User Position Analysis --- ✅");

  console.log(`\n--- User & Market Info ---`);
  console.log(`User: ${positionInfo.user}`);
  console.log(`Market ID: ${positionInfo.marketId}`);
  console.log(`Loan Token: ${positionInfo.loanToken.name} (${positionInfo.loanToken.symbol})`);
  console.log(`Collateral Token: ${positionInfo.collateralToken.name} (${positionInfo.collateralToken.symbol})`);
  console.log(`Max LTV: ${positionInfo.maxLTV.toFixed(2)}%`);

  console.log(`\n--- Position Assets (Real-time) ---`);
  console.log(`Supply: ${positionInfo.formattedSupplyAssets} ${positionInfo.loanToken.symbol}`);
  console.log(`Borrow: ${positionInfo.formattedBorrowAssets} ${positionInfo.loanToken.symbol}`);
  console.log(`Collateral: ${positionInfo.formattedCollateralAssets} ${positionInfo.collateralToken.symbol}`);

  console.log(`\n--- Health Metrics ---`);
  console.log(`Health Factor: ${formatUnits(positionInfo.healthFactor, 18)}`);
  console.log(`Is Healthy: ${positionInfo.isHealthy ? "✅ Yes" : "❌ No (Liquidatable!)"}`);
  console.log(`Current LTV: ${positionInfo.currentLTV.toFixed(2)}%`);
  console.log(`LTV Utilization: ${positionInfo.utilizationOfCollateral.toFixed(2)}%`);
  console.log(`Liquidation Buffer: ${formatUnits(positionInfo.liquidationBuffer, positionInfo.loanToken.decimals)} ${positionInfo.loanToken.symbol}`);

  console.log(`\n--- Price & Risk Info ---`);
  console.log(`Collateral Price: ${formatUnits(positionInfo.collateralPrice, 36)} ${positionInfo.loanToken.symbol} per ${positionInfo.collateralToken.symbol}`);
  if (positionInfo.liquidationPrice > 0n) {
    console.log(`Liquidation Price: ${formatUnits(positionInfo.liquidationPrice, 36)} ${positionInfo.loanToken.symbol} per ${positionInfo.collateralToken.symbol}`);
    // Price drop to liquidation is mathematically equivalent to: 100% - utilization of collateral
    // This avoids precision issues from bigint-to-number conversion
    const priceDropToLiquidation = 100 - positionInfo.utilizationOfCollateral;
    console.log(`Price Drop to Liquidation: ${priceDropToLiquidation.toFixed(2)}%`);
  }

  console.log(`\n--- Interest Accrual ---`);
  console.log(`Last Update: ${positionInfo.lastUpdateTime.toISOString()}`);
  console.log(`Interest Accrued: ${positionInfo.formattedInterestAccrued} ${positionInfo.loanToken.symbol}`);

  console.log(`\n--- Raw Position Data ---`);
  console.log(`Supply Shares: ${positionInfo.rawPosition.supplyShares}`);
  console.log(`Borrow Shares: ${positionInfo.rawPosition.borrowShares}`);
  console.log(`Collateral (raw): ${positionInfo.rawPosition.collateral}`);

  console.log("\n----------------------------------------");
}

/**
 * Displays a summary table of multiple user positions
 */
export function displayUserPositionsTable(positions: UserPositionInfo[]): void {
  if (positions.length === 0) {
    console.log("No positions found for user.");
    return;
  }

  console.log("\n✅ --- User Positions Summary --- ✅");
  console.log(`\nUser: ${positions[0].user}`);
  console.log(`Total Positions: ${positions.length}`);
  
  console.log("\nMarket                       | Loan/Collateral     | Borrowed    | Collateral  | Health Factor | Status");
  console.log("-----------------------------+---------------------+-------------+-------------+---------------+--------");

  positions.forEach(position => {
    const shortMarketId = `${position.marketId.slice(0, 8)}...${position.marketId.slice(-8)}`;
    const tokenPair = `${position.loanToken.symbol}/${position.collateralToken.symbol}`;
    const borrowed = parseFloat(position.formattedBorrowAssets).toLocaleString('en-US', { maximumFractionDigits: 2 });
    const collateral = parseFloat(position.formattedCollateralAssets).toLocaleString('en-US', { maximumFractionDigits: 2 });
    const healthFactor = Number(formatUnits(position.healthFactor, 18)).toFixed(3);
    const status = position.isHealthy ? "✅ Healthy" : "❌ Risk";

    console.log(
      `${shortMarketId.padEnd(28)} | ${tokenPair.padEnd(19)} | ${borrowed.padStart(11)} | ${collateral.padStart(11)} | ${healthFactor.padStart(13)} | ${status}`
    );
  });

  console.log("\n----------------------------------------");
}

/**
 * Main function to demonstrate user position analysis
 */
export async function main(): Promise<void> {
  try {
    const client = createMainnetClient();
    
    console.log("=== User Position Analysis Demo ===\n");
    
    // Check if user has a position in the market
    const hasPos = await hasPosition(client, EXAMPLE_USER, EXAMPLE_MARKET_ID);
    console.log(`User has position in market: ${hasPos ? "✅ Yes" : "❌ No"}`);
    
    if (!hasPos) {
      console.log("No position found. Exiting demo.");
      return;
    }
    
    // Get detailed position information
    const positionInfo = await getUserPositionInfo(client, EXAMPLE_USER, EXAMPLE_MARKET_ID);
    
    // Display detailed results
    displayUserPosition(positionInfo);
    
    // Example: Get positions across multiple markets (if you have more market IDs)
    const multipleMarkets = [EXAMPLE_MARKET_ID];
    const userPositions = await getUserPositionsInMarkets(client, EXAMPLE_USER, multipleMarkets);
    
    // Display summary table
    displayUserPositionsTable(userPositions);
    
    console.log("\n=== Demo Complete ===");
    
  } catch (error) {
    console.error("Error in user position analysis:", error);
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
=== User Position Analysis Demo ===

User has position in market: ✅ Yes
Fetching position for user: 0x4352Cc849b33a936Ad93bB109aFDec1c89653b4f in market: 0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64

✅ --- User Position Analysis --- ✅

--- User & Market Info ---
User: 0x4352Cc849b33a936Ad93bB109aFDec1c89653b4f
Market ID: 0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64
Loan Token: USD Coin (USDC)
Collateral Token: Coinbase Wrapped BTC (cbBTC)
Max LTV: 86.00%

--- Position Assets (Real-time) ---
Supply: 0 USDC
Borrow: 75883503.679379 USDC
Collateral: 1291.00894824 cbBTC

--- Health Metrics ---
Health Factor: 1.472724337032200696
Is Healthy: ✅ Yes
Current LTV: 58.40%
LTV Utilization: 67.90%
Liquidation Buffer: 35871978.968515 USDC

--- Price & Risk Info ---
Collateral Price: 1006.5634 USDC per cbBTC
Liquidation Price: 683470337724024509145.488769364009452427844856671826760481 USDC per cbBTC
Price Drop to Liquidation: 32.10%

--- Interest Accrual ---
Last Update: 2025-11-07T10:55:11.000Z
Interest Accrued: 66.30546 USDC

--- Raw Position Data ---
Supply Shares: 0
Borrow Shares: 71029026727778728163
Collateral (raw): 129100894824

----------------------------------------
Fetching positions for user 0x4352Cc849b33a936Ad93bB109aFDec1c89653b4f across 1 markets...
Fetching position for user: 0x4352Cc849b33a936Ad93bB109aFDec1c89653b4f in market: 0x64d65c9a2d91c36d56fbc42d69e979335320169b3df63bf92789e2c8883fcc64

✅ --- User Positions Summary --- ✅

User: 0x4352Cc849b33a936Ad93bB109aFDec1c89653b4f
Total Positions: 1

Market                       | Loan/Collateral     | Borrowed    | Collateral  | Health Factor | Status
-----------------------------+---------------------+-------------+-------------+---------------+--------
0x64d65c...883fcc64          | USDC/cbBTC          | 75,883,503.68 |    1,291.01 |         1.473 | ✅ Healthy

----------------------------------------

=== Demo Complete ===
```

This example shows a real borrower position with high LTV utilization (99.95%) but still healthy due to the high maximum LTV (98%) of this particular market. The position demonstrates the importance of real-time interest accrual for accurate risk assessment.

### [All Market Positions](#all-market-positions)

APIAPI
```
query {
  marketPositions(
    first: 10
    orderBy: SupplyShares
    orderDirection: Desc
    where: {
      marketUniqueKey_in: [
        "0x698fe98247a40c5771537b5786b2f3f9d78eb487b4ce4d75533cd0e94d88a115"
      ]
    }
  ) {
    items {
      market {
        marketId
        loanAsset {
          address
          symbol
        }
        collateralAsset {
          address
          symbol
        }
      }
      user {
        address
      }
      state {
        supplyShares
        supplyAssets
        supplyAssetsUsd
        borrowShares
        borrowAssets
        borrowAssetsUsd
        collateral
        collateralUsd
      }
    }
  }
}
```

## [Risk & Oracle Data](#risk--oracle-data)

### [Oracle Data](#oracle-data)

APIAll Markets
```
query Markets($first: Int, $skip: Int, $orderBy: MarketOrderBy, $orderDirection: OrderDirection, $where: MarketFilters) {
  markets(first: $first, skip: $skip, orderBy: $orderBy, orderDirection: $orderDirection, where: $where) {
    items {
      marketId
      oracle {
        address
        type
        data {
          ... on MorphoChainlinkOracleData {
            baseFeedOne {
              address
            }
            baseFeedTwo {
              address
            }
            baseOracleVault {
              address
            }
            quoteFeedOne {
              address
            }
            quoteFeedTwo {
              address
            }
            scaleFactor
            vaultConversionSample
          }
          ... on MorphoChainlinkOracleV2Data {
            baseFeedOne {
              address
            }
            baseFeedTwo {
              address
            }
            baseOracleVault {
              address
            }
            baseVaultConversionSample
            quoteFeedOne {
              address
            }
            quoteFeedTwo {
              address
            }
            quoteOracleVault {
              address
            }
            quoteVaultConversionSample
            scaleFactor
          }
        }
        creationEvent {
          txHash
          timestamp
          blockNumber
        }
      }
    }
  }
}
```

---

Unique Market
```
query {
  marketById(
    marketId: "0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836"
    chainId: 8453
  ) {
    marketId
    oracle {
      address
      type
      creationEvent {
        txHash
        timestamp
        blockNumber
      }
      data {
        ... on MorphoChainlinkOracleV2Data {
          baseFeedOne {
            address
          }
          baseFeedTwo {
            address
          }
          baseOracleVault {
            address
          }
          baseVaultConversionSample
          quoteFeedOne {
            address
          }
          quoteFeedTwo {
            address
          }
          quoteOracleVault {
            address
          }
          quoteVaultConversionSample
          scaleFactor
        }
        ... on MorphoChainlinkOracleData {
          baseFeedOne {
            address
          }
          baseFeedTwo {
            address
          }
          baseOracleVault {
            address
          }
          quoteFeedOne {
            address
          }
          quoteFeedTwo {
            address
          }
          scaleFactor
          vaultConversionSample
        }
      }
    } 
  }
}
```

### [Liquidations](#liquidations)

APIAPI
```
query {
  marketTransactions(
    first: 10
    orderBy: Timestamp
    orderDirection: Desc
    where: {
      marketUniqueKey_in: [
        "0x49bb2d114be9041a787432952927f6f144f05ad3e83196a7d062f374ee11d0ee"
        "0x093d5b432aace8bf6c4d67494f4ac2542a499571ff7a1bcc9f8778f3200d457d"
      ]
      type_in: [Liquidation]
    }
  ) {
    items {
      blockNumber
      txHash
      logIndex
      type
      user {
        address
      }
      market {
        marketId
      }
      data {
        ... on MarketTransactionLiquidationData {
          seizedAssets
          repaidAssets
          badDebtAssets
          liquidator
        }
      }
    }
  }
}
```

### [Market Warnings](#market-warnings)

APIWarning `type` can be:

- `not_whitelisted` & YELLOW level: The market is not listed
- `bad_debt_unrealized` & RED level: Significant unrealized bad debt (>= 5% / 500 BPS of total supply, and at least $100)
- `oracle_price_derivation` & RED level: The on-chain oracle price deviates from the USD-derived price by more than 10x
- `oracle_unusable` & RED level: The market's oracle returns no usable price
- `sustained_low_liquidity` & RED level: The market has had zero available liquidity for 5 full consecutive days
- `custom`: An operator-defined warning; the level is configured per entry

Warning `level` is either:

- YELLOW
- RED

The default response returns active warnings only; market warnings have no `GREEN` level. Market warnings do not propagate to vaults: vaults carry their own warning types, and the exposure-gated ones among them are raised on the vault when its exposure to the flagged markets crosses a threshold. See [Morpho Warnings](https://docs.morpho.org/get-started/resources/app-ecosystem/#morpho-warnings) for the full criteria and thresholds of each type.

---

API
```
query {
  markets {
    items {
      marketId
      warnings {
        type
        level
      }
    }
  }
}
```

## [Integration](#integration)

### [Vault Listing](#vault-listing)

APIThe following query corresponds to which vault has this market in its supply queue

---

API
```
query {
  marketById(
    marketId: "0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836"
    chainId: 8453
  ) {
    marketId
    supplyingVaults {
      address
      name
      symbol
    }
    supplyingVaultV2s {
      address
      name
      symbol
    }
  }
}
```

## [Historical Data](#historical-data)

The `historicalState` allows to get historical data for certain queries. The queries need to be backfilled to return proper data (i.e. the historical data needs to be indexed and stored). Some queries are not backfilled and are flagged as deprecated in [the Morpho API sandbox](https://api.morpho.org/graphql).

Available options when using an `historicalState` query:

- `startTimestamp`: beginning of the historical data in UNIX timestamp format,
- `endTimestamp`: end of the historical data in UNIX timestamp format,
- `interval`: interval of the historical data points (`YEAR`, `QUARTER`, `MONTH`, `WEEK`, `DAY`, `HOUR`).

Inputting these options is not mandatory but it is advised to specify them to control the specific data returned.

If no options are specified, the default values will be:

- `startTimestamp`: 0,
- `endTimestamp`: infinity,
- `interval`: will adjust according to `startTimestamp` and `endTimestamp` to return around 50 data points.

`historicalState` field is not accessible through the markets list queries. Historical data is only available through individual market queries like `market(id: "")` or `marketById(marketId: "", chainId: ...)`.

### [Historical APYs](#historical-apys)

The example below mirrors the structure shown in the Morpho API sandbox, so you can copy/paste it directly when testing queries.

APIAPI
```
query MarketById($marketId: String!, $chainId: Int!, $options: TimeseriesOptions) {
  marketById(marketId: $marketId, chainId: $chainId) {
    historicalState {
      borrowApy(options: $options) {
        x
        y
      }
      supplyApy(options: $options) {
        x
        y
      }
    }
  }
}
```

---

with the following variables

```
{
  "marketId": "0x608929d6de2a10bacf1046ff157ae38df5b9f466fb89413211efb8f63c63833a",
  "chainId": 1,
  "options": {
    "startTimestamp": 1707749700,
    "endTimestamp": 1708354500,
    "interval": "HOUR"
  }
}
```

### [Historical Market States](#historical-market-states)

APIAPI
```
query MarketApys($options: TimeseriesOptions) {
  marketById(
    marketId: "0x608929d6de2a10bacf1046ff157ae38df5b9f466fb89413211efb8f63c63833a"
    chainId: 1
  ) {
    marketId
    historicalState {
      supplyAssetsUsd(options: $options) {
        x
        y
      }
      borrowAssetsUsd(options: $options) {
        x
        y
      }
    }
  }
}
```

### [Historical Asset Price](#historical-asset-price)

APIAPI
```
query {
  wstETHWeeklyPriceUsd: assetByAddress(
    address: "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
    chainId: 1
  ) {
    historicalPriceUsd(
      options: {
        startTimestamp: 1707749700
        endTimestamp: 1708354500
        interval: HOUR
      }
    ) {
      x
      y
    }
  }
}
```

[Supply Collateral, Borrow, Repay & Withdraw Collateral

Previous Page

](https://docs.morpho.org/developers/borrow/tutorials/assets-flow/)[Vault V2 Public Allocator

Build a Vault V2 reallocation snapshot, plan shared liquidity, and attach it to a Morpho Blue action.

](https://docs.morpho.org/developers/borrow/tutorials/public-allocator/)