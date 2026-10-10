# Vault V2 Public Allocator

> Source: https://docs.morpho.org/developers/borrow/tutorials/public-allocator

---

# Vault V2 Public Allocator

Build a Vault V2 reallocation snapshot, plan shared liquidity, and attach it to a Morpho Blue action.

This tutorial shows how the Morpho SDK finds Vault V2 liquidity and turns it into Public Allocator calls for a borrow or loan-asset withdrawal. Read the [Public Allocator overview](https://docs.morpho.org/learn/concepts/public-allocator/) first.

Package versionsUse `@morpho-org/morpho-sdk@6.0.0` or later. It re-exports every SDK primitive used below, including the direct REST path's Public Allocator fetcher.

## [Choose discovery or operation planning](#choose-discovery-or-operation-planning)

`VaultV2BlueReallocationData` is a complete snapshot of the markets, vaults, adapters, caps, and Public Allocator settings used by the planner.

Its `computeVaultV2BlueReallocations` method has two modes:

| Mode | Input | Use it for |
| --- | --- | --- |
| Discovery | No `operation` | Measuring friendly shared liquidity the planner can find now |
| Operation planning | `operation: { type, amount }` | Building an ordered plan sized for one borrow or loan-asset withdrawal |

Use operation planning for transactions. Discovery exhausts every route the planner accepts and can move more assets, incur more penalties, and add more calls than the user needs.

For a specific Morpho Blue market, prefer `market.getVaultV2BlueReallocations`. It validates that the snapshot and market use the same chain before calling the planner.

Each result is a flat list. One entry maps to one market-to-market or idle-to-market allocator call:

```
interface VaultV2BlueReallocation {
  readonly vault: Address;
  readonly from:
    | {
        readonly type: "market";
        readonly adapter: Address;
        readonly marketParams: MarketParams;
      }
    | { readonly type: "idle" };
  readonly to: { readonly adapter: Address };
  readonly assets: bigint;
  readonly penalty: bigint;
}
```

The enclosing Morpho Blue action supplies the target market parameters. Keep the returned order and pass only Vault V2 reallocations to the action.

## [How the planner finds liquidity](#how-the-planner-finds-liquidity)

The planner simulates the allocator and Vault V2 accounting instead of adding visible token balances.

1. It accrues every market to one timestamp and filters the loaded vaults through the optional allowlist.
2. For an operation, it simulates the borrow or withdrawal on the target market. If projected utilization stays at or below 90%, it returns no reallocations.
3. Above 90%, it computes the target top-up as `ceil(projected borrows / 90%) - projected supply`.
4. It rejects sources that fail the asset, interest-rate model, adapter, permission, penalty, or cap checks.
5. It computes an initial maximum for every eligible source.
6. It rejects target supply-share overflow, binary-searches non-shared cap upper bounds, then checks the selected amount against every cap after penalty, interest, and share rounding.
7. It keeps the largest candidate per vault, chooses the largest of those candidates, applies it to cloned state, and repeats. This produces the execution order.
8. If friendly sources cannot cover the market's absolute shortfall, it continues from that state with a 100% source-utilization ceiling. It throws when even that liquidity cannot make the operation executable.

A route is eligible only when all of these checks pass:

- The target uses a supported, active `AccrualVaultV2MorphoMarketV1AdapterV2` that belongs to the vault. A market source must also use a supported, active adapter that belongs to that vault.
- The target loan token equals the vault asset, and the target market uses its adapter's Adaptive Curve IRM. A market source must satisfy the same asset and interest-rate-model checks.
- The three Vault V2 allocation records derived from the target have non-zero absolute caps, and the target remains below the allocator's absolute ceiling.
- A market source has pull permission and non-zero allocations for all three derived cap IDs. An idle source needs the vault-wide idle permission.
- The source is not the target market, including when two adapters expose it.
- Supplying the candidate to the target does not mint fewer shares than assets or overflow the market's `uint128` supply shares.

Explicitly disabled permissions and zero caps make a route ineligible. Missing nested allocator or cap state makes the snapshot incomplete and throws a typed error instead of reporting zero liquidity.

For a market source, the initial maximum is the smallest of:

- the target market's `uint128` supply-asset headroom;
- the Public Allocator's target headroom;
- the source adapter's expected assets;
- the amount withdrawable before the source reaches `maxWithdrawalUtilization`.

For an idle source, the vault's current idle balance replaces the last two limits. The planner does not recycle penalty donations as new idle liquidity.

The cap check needs binary search because the relationship is not linear. The penalty changes vault assets, the first call fixes the relative-cap denominator, and Morpho share conversion rounds each simulated move. A cap ID shared by the source and target can impose a lower bound or a non-monotonic rounding constraint. The planner excludes shared IDs from the upper-bound search, then validates the selected amount against every cap.

An operation plan can exceed its preferred amount when a larger move is the first value that satisfies a shared-cap lower bound. If the non-shared maximum still violates a shared cap, the planner omits the candidate instead of scanning every smaller base-unit amount. Discovery metrics can therefore understate executable liquidity in an already-at-or-over-cap snapshot. One canonical market state is shared by every adapter, so each simulated move updates every later candidate that depends on that market.

## [Planner options](#planner-options)

| Option | Default | Effect |
| --- | --- | --- |
| `enabled` | `true` | Set to `false` to return an empty plan. |
| `timestamp` | Latest update in the snapshot | Sets the time for market accrual and for each vault's first simulated allocation. Pass the fetched block timestamp for a coherent plan. |
| `reallocatableVaults` | Every loaded vault | Restricts discovery to the supplied address iterable. |
| `maxWithdrawalUtilization` | 90% | Limits source utilization during friendly discovery. Must be between 0 and 100%. |
| `maxPenalty` | 0% | Ignores vaults with a higher proportional penalty. Set this explicitly to opt into paid reallocations. |
| `operation` | None | Adds an amount-aware `borrow` or `withdraw` plan. The amount must be positive. |

The penalty is WAD-scaled. A value of `1_000_000_000_000_000n` accepts up to 0.1%. Each call charges `ceil(assets × penalty / WAD)` in the target loan token and adds it to the vault.

## [Build the snapshot with the SDK](#build-the-snapshot-with-the-sdk)

The shortest RPC-backed path is `market.getVaultV2BlueReallocationData`. It fetches the target market, each Vault V2 accrual tree, Public Allocator permissions, and allocation caps at one block.

The snippets below assume that `client` is a wallet client extended with viem `publicActions` and `morphoViemExtension`, and that `market` is the target `MorphoBlue` entity. Follow [Supply collateral and borrow](https://docs.morpho.org/developers/borrow/tutorials/assets-flow/#integrate-with-the-morpho-sdk) for that setup. Import `publicActions` from `viem`, then add `.extend(publicActions)` before `.extend(morphoViemExtension(...))`.

### [Step 1: Fetch one coherent snapshot](#step-1-fetch-one-coherent-snapshot)

Use candidate Vault V2 addresses from your own allowlist or discovery service. Fetch the block once, then use it for every SDK read.

```
import type { Address } from "viem";

const vaultAddresses = [
  process.env.VAULT_V2_ADDRESS as Address,
];

const block = await client.getBlock();
const reallocationData = await market.getVaultV2BlueReallocationData({
  vaultAddresses,
  block: {
    number: block.number,
    timestamp: block.timestamp,
  },
});
```

### [Step 2: Build an amount-aware plan](#step-2-build-an-amount-aware-plan)

```
import { parseUnits } from "viem";

const amount = parseUnits("500", 6);
const maxPenalty = 1_000_000_000_000_000n; // 0.1%

const { reallocations, data: simulatedState } =
  market.getVaultV2BlueReallocations({
    reallocationData,
    options: {
      timestamp: block.timestamp,
      reallocatableVaults: vaultAddresses,
      maxPenalty,
      operation: { type: "borrow", amount },
    },
  });
```

`simulatedState` contains the post-plan markets and vaults. Use it for previews and diagnostics. Pass `reallocations` to the action without sorting or regrouping it.

### [Step 3: Build, authorize, simulate, and submit](#step-3-build-authorize-simulate-and-submit)

```
import {
  isRequirementSignature,
  type RequirementSignature,
} from "@morpho-org/morpho-sdk";

const positionData = await market.getPositionData(account.address, {
  blockNumber: block.number,
});
const borrow = market.borrow({
  borrowAssets: amount,
  userAddress: account.address,
  positionData,
  deadline: block.timestamp + 3_600n,
  reallocations,
});

const signatures: RequirementSignature[] = [];
for (const requirement of await borrow.getRequirements()) {
  if (isRequirementSignature(requirement)) {
    signatures.push(await requirement.sign(client, account.address));
  } else {
    const hash = await client.sendTransaction(requirement);
    await client.waitForTransactionReceipt({ hash });
  }
}

const transaction = borrow.buildTx(signatures);
await client.call({
  account: account.address,
  to: transaction.to,
  data: transaction.data,
  value: transaction.value,
});

const hash = await client.sendTransaction(transaction);
await client.waitForTransactionReceipt({ hash });
```

Allocator penalties are accounted for in the BlueBundlesV1 proceeds and do not create a separate funding requirement. BlueBundlesV1 executes every allocator call before the borrow.

A borrow plan also works with `supplyCollateralBorrow`. Pass it as `reallocations` when refinancing into the target market.

For a loan-asset withdrawal, repeat Step 2 with `operation: { type: "withdraw", amount }`. Then pass that new plan to the asset-mode action:

```
const { reallocations: withdrawReallocations } =
  market.getVaultV2BlueReallocations({
    reallocationData,
    options: {
      timestamp: block.timestamp,
      maxPenalty,
      operation: { type: "withdraw", amount },
    },
  });

const withdraw = market.withdraw({
  assets: amount,
  userAddress: account.address,
  positionData,
  deadline: block.timestamp + 3_600n,
  reallocations: withdrawReallocations,
});
```

## [Build the snapshot from REST data](#build-the-snapshot-from-rest-data)

Use REST for the large vault and market state graph when RPC credits matter. Keep RPC reads for the indexed block, Adaptive Curve IRM rates, and Public Allocator state because the REST API does not expose all required state.

### [Use REST directly](#use-rest-directly)

The flow below hydrates a best-effort `VaultV2BlueReallocationData` state graph from the Morpho REST API. It retains one RPC read for the indexed block, one rate read per Adaptive Curve IRM market, and one deployless allocator-state read per vault. The SDK resolves the Vault V2 Blue Public Allocator address from the selected chain's registry; callers do not pass an allocator address.

### [Fetch the REST graph directly](#fetch-the-rest-graph-directly)

Use these `GET` endpoints under `https://api.morpho.org`:

| Data | Path |
| --- | --- |
| Vault configuration | `GET /v0/vaults-v2/{vault-selector}` |
| Vault accounting | `GET /v1/vaults-v2/{vault-selector}/state` |
| Vault adapters, markets, and caps | `GET /v0/vaults-v2/{vault-selector}/allocations` |
| Adapter force-deallocation penalties | `GET /v0/vaults-v2/{vault-selector}/withdrawal-options` |
| Market parameters | `GET /v0/blue/markets/{market-selector}` |
| Market accounting | `GET /v0/blue/markets/{market-selector}/state` |
| Adapter market position | `GET /v0/blue/markets/{market-selector}/users/{user-address}/position` |
| Oracle state | `GET /v0/oracles/{oracle-selector}/state` |

Every REST endpoint in this table wraps its payload in `{ data: ... }`. Read `rateAtTarget` from the Adaptive Curve IRM contract at the validated indexed block; the REST API spec has no IRM operation. The package request helpers and response guards are not public exports, so raw callers must provide their own validation:

```
import {
  type Address,
  type Hex,
  isAddress,
  isAddressEqual,
  isHex,
  size,
  zeroAddress,
} from "viem";

type Validator<T> = (value: unknown) => value is T;

const isApiInteger = (value: unknown): value is number =>
  typeof value === "number" && Number.isSafeInteger(value);
const isDecimalString = (value: unknown): value is string =>
  typeof value === "string" && /^(0|[1-9][0-9]*)$/.test(value);
const isAddressValue = (value: unknown): value is Address =>
  typeof value === "string" && isAddress(value);
const isHexValue = (value: unknown): value is Hex =>
  typeof value === "string" && isHex(value, { strict: true });
const isHashValue = (value: unknown) =>
  isHexValue(value) && size(value) === 32;

const requiredBigInt = (value: unknown, label: string) => {
  if (!isDecimalString(value)) throw new Error(`Invalid ${label}`);
  return BigInt(value);
};
const optionalBigInt = (value: unknown, label: string) =>
  value == null ? undefined : requiredBigInt(value, label);
const requiredInteger = (
  value: unknown,
  label: string,
  min = 0,
  max = Number.MAX_SAFE_INTEGER,
) => {
  if (!isApiInteger(value) || value < min || value > max) {
    throw new Error(`Invalid ${label}`);
  }
  return value;
};
const nullableAddressOrZero = (value: unknown, label: string) => {
  if (value === null) return zeroAddress;
  if (!isAddressValue(value)) throw new Error(`Invalid ${label}`);
  return value;
};
const nullableHexOrEmpty = (value: unknown, label: string) => {
  if (value === null) return "0x";
  if (!isHexValue(value)) throw new Error(`Invalid ${label}`);
  return value;
};
const nullableMetadata = (value: unknown, label: string) => {
  if (value === null) return undefined;
  if (typeof value !== "string") throw new Error(`Invalid ${label}`);
  return value;
};

async function fetchApi<T>(
  path: string,
  validate: Validator<T>,
): Promise<T> {
  const url = new URL(path, "https://api.morpho.org");
  const response = await fetch(url, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${url}`);
  }

  const body: unknown = await response.json();
  const record =
    typeof body === "object" && body !== null && !Array.isArray(body)
      ? (body as Record<string, unknown>)
      : undefined;
  const data = record?.data;
  if (!validate(data)) {
    throw new Error(`Invalid API response from ${url}`);
  }
  return data;
}
```

Treat the API schema as a starting point. Some hydration fields are nullable or omitted from its required lists. Each local validator must require every field used below. It must also match `chain_id` and the requested resource identity, validate arrays and objects, and use the strict checks above. Do not replace validation with a type assertion.

These conversions accept numeric zero. They reject nullish required values, empty or whitespace-only decimal strings, negative or fractional values, unsafe JSON integers, and malformed addresses or hex. Optional bigint fields preserve only `null` and `undefined` as missing.

### [Track REST snapshot boundaries](#track-rest-snapshot-boundaries)

When you build the state directly, align the responses that expose block metadata:

1. Validate every response and its resource identity. Convert decimal-string asset and WAD values with `requiredBigInt` or `optionalBigInt`.
2. Require the same `last_indexed_block` from vault configuration, state, and allocations; market state; oracle state; and adapter positions. Withdrawal options and market parameters do not expose this field; read the adaptive-curve rate through RPC at the validated block.
3. Fetch that exact block through RPC and use its timestamp.
4. Load the target market and every market referenced by an adapter cap.
5. Load each adapter's supply shares, oracle state, and adaptive-curve rate state.
6. Set each hydrated market's `lastUpdate` to the indexed block timestamp. REST totals already include accrual through that block; using the older onchain accrual timestamp would count interest twice.
7. Require every field used to hydrate an SDK entity, including vault decimal metadata, totals, `max_rate_per_second_wad`, adapter positions, and the adaptive-curve rate. Do not replace missing state with zero.

REST responses can span indexed blocksThese REST calls do not all accept a block selector or return `last_indexed_block`. The indexer can advance between requests, so the assembled `VaultV2BlueReallocationData` can contain state from multiple indexed blocks. The force-deallocation penalty can come from another block; the adaptive-curve rate is pinned through RPC. Market parameters also lack a block field, but they are immutable for a market ID. The API usually serves its latest indexed state, so this example accepts this edge case to save RPC reads.

This example gives every market and the planner the validated block timestamp. The rate therefore has no elapsed time to affect the immediate plan, and the Public Allocator planner does not use the force-deallocation penalty. Reusing the state with a later timestamp can change accrued totals, utilization, share conversions, cap headroom, route eligibility, and reallocation amounts. Reusing its vaults for force-deallocation or in-kind redemption calculations can also use a penalty from another block. Treat the plan as a quote, simulate the final transaction, and rebuild after a failed simulation.

Fetch every vault's four resources first. The guard names below stand for the local type guards described above:

```
const chainId = client.chain.id;
const selector = (identifier: string) =>
  `${chainId}:${encodeURIComponent(identifier)}`;

const vaultRows = await Promise.all(
  vaultAddresses.map(async (vaultAddress) => {
    const id = selector(vaultAddress);
    const [config, state, allocations, withdrawalOptions] =
      await Promise.all([
        fetchApi(`/v0/vaults-v2/${id}`, isVaultConfig),
        fetchApi(`/v1/vaults-v2/${id}/state`, isVaultState),
        fetchApi(
          `/v0/vaults-v2/${id}/allocations`,
          isVaultAllocations,
        ),
        fetchApi(
          `/v0/vaults-v2/${id}/withdrawal-options`,
          isVaultWithdrawalOptions,
        ),
      ]);
    return { config, state, allocations, withdrawalOptions };
  }),
);
const firstVault = vaultRows[0];
if (firstVault == null) throw new Error("No Vault V2 candidates");

const indexedBlockNumber = requiredBigInt(
  firstVault.config.last_indexed_block,
  `vault ${firstVault.config.address} indexed block`,
);
const assertIndexedBlock = (value: unknown, resource: string) => {
  if (
    requiredBigInt(value, `${resource} indexed block`) !==
    indexedBlockNumber
  ) {
    throw new Error(`Mixed REST indexed block for ${resource}`);
  }
};

for (const { config, state, allocations } of vaultRows) {
  assertIndexedBlock(
    config.last_indexed_block,
    `vault ${config.address} config`,
  );
  assertIndexedBlock(
    state.last_indexed_block,
    `vault ${config.address} state`,
  );
  assertIndexedBlock(
    allocations.last_indexed_block,
    `vault ${config.address} allocations`,
  );
}

const block = await client.getBlock({
  blockNumber: indexedBlockNumber,
});
```

Collect the target market and every cap-linked market, then fetch their state and adapter positions:

```
import { adaptiveCurveIrmAbi } from "@morpho-org/morpho-sdk/abis";
import { getChainAddresses } from "@morpho-org/morpho-sdk/addresses";
import type { MarketId } from "@morpho-org/morpho-sdk/types";

const { adaptiveCurveIrm } = getChainAddresses(chainId);
const marketIds = new Set([market.marketParams.id]);
const adapterMarketPairs = new Map<
  string,
  { adapterAddress: Address; marketId: MarketId }
>();

for (const { allocations } of vaultRows) {
  for (const allocation of allocations.allocations) {
    for (const { market_id: marketId } of allocation.caps) {
      if (marketId == null) continue;
      marketIds.add(marketId);
      adapterMarketPairs.set(
        `${allocation.adapter_address.toLowerCase()}:${marketId.toLowerCase()}`,
        { adapterAddress: allocation.adapter_address, marketId },
      );
    }
  }
}

const marketRows = await Promise.all(
  [...marketIds].map(async (marketId) => {
    const id = selector(marketId);
    const config = await fetchApi(
      `/v0/blue/markets/${id}`,
      isMarketConfig,
    );
    const [state, oracleState, irmState] = await Promise.all([
      fetchApi(`/v0/blue/markets/${id}/state`, isMarketState),
      isAddressEqual(config.oracle_address, zeroAddress)
        ? undefined
        : fetchApi(
            `/v0/oracles/${selector(config.oracle_address)}/state`,
            isOracleState,
          ),
      isAddressEqual(config.irm_address, adaptiveCurveIrm)
        ? client.readContract({
            address: adaptiveCurveIrm,
            abi: adaptiveCurveIrmAbi,
            functionName: "rateAtTarget",
            args: [marketId],
            blockNumber: indexedBlockNumber,
          }).then((rateAtTarget) => ({ rateAtTarget: rateAtTarget.toString() }))
        : undefined,
    ]);

    assertIndexedBlock(state.last_indexed_block, `market ${marketId}`);
    if (oracleState != null) {
      assertIndexedBlock(
        oracleState.last_indexed_block,
        `oracle ${config.oracle_address}`,
      );
    }
    return { config, state, oracleState, irmState };
  }),
);

const marketPositions = await Promise.all(
  [...adapterMarketPairs.values()].map(
    async ({ adapterAddress, marketId }) => {
      const position = await fetchApi(
        `/v0/blue/markets/${selector(marketId)}/users/${encodeURIComponent(adapterAddress)}/position`,
        isMarketPosition,
      );
      assertIndexedBlock(
        position.last_indexed_block,
        `position ${adapterAddress}:${marketId}`,
      );
      return position;
    },
  ),
);
```

Keep the field guards local and fail the quote when validation fails.

### [Hydrate SDK entities](#hydrate-sdk-entities)

Create each market from its validated REST rows. The planner does not use `price`, so preserve a missing API price as `undefined`. `rateAtTarget` is required when the market uses the chain's Adaptive Curve IRM:

```
import { Market, MarketParams } from "@morpho-org/morpho-sdk/entities";

type MarketRow = (typeof marketRows)[number];

const hydrateMarket = ({
  config,
  state,
  oracleState,
  irmState,
}: MarketRow) => {
  const rateAtTarget = isAddressEqual(config.irm_address, adaptiveCurveIrm)
    ? requiredBigInt(
        irmState?.rateAtTarget,
        `adaptive-curve rate ${config.market_id}`,
      )
    : undefined;

  return new Market({
    params: new MarketParams({
      loanToken: config.loan_token,
      collateralToken: config.collateral_token,
      oracle: config.oracle_address,
      irm: config.irm_address,
      lltv: requiredBigInt(
        config.lltv_wad,
        `LLTV ${config.market_id}`,
      ),
    }),
    totalSupplyAssets: requiredBigInt(
      state.total_supply_assets,
      `total supply assets ${config.market_id}`,
    ),
    totalSupplyShares: requiredBigInt(
      state.total_supply_shares,
      `total supply shares ${config.market_id}`,
    ),
    totalBorrowAssets: requiredBigInt(
      state.total_borrow_assets,
      `total borrow assets ${config.market_id}`,
    ),
    totalBorrowShares: requiredBigInt(
      state.total_borrow_shares,
      `total borrow shares ${config.market_id}`,
    ),
    lastUpdate: block.timestamp,
    fee: requiredBigInt(state.fee_wad, `fee ${config.market_id}`),
    price: optionalBigInt(
      oracleState?.price,
      `oracle price ${config.market_id}`,
    ),
    rateAtTarget,
  });
};

const markets = marketRows.map(hydrateMarket);
```

Then hydrate each compatible adapter and its parent vault. The maps below use lowercase `adapter:market` keys and must throw when a required entry is missing:

```
import {
  AccrualVaultV2,
  AccrualVaultV2MorphoMarketV1AdapterV2,
} from "@morpho-org/morpho-sdk/entities";

const marketById = new Map(
  markets.map((market) => [market.id.toLowerCase(), market]),
);
const positionByAdapterMarket = new Map(
  marketPositions.map((position) => [
    `${position.user_address.toLowerCase()}:${position.market_id.toLowerCase()}`,
    position,
  ]),
);

type VaultRow = (typeof vaultRows)[number];

const hydrateVault = ({
  config: vaultConfig,
  state: vaultState,
  allocations: vaultAllocations,
  withdrawalOptions,
}: VaultRow) => {
  const adapters = vaultAllocations.allocations.map((allocation) => {
    if (allocation.adapter_kind !== "morpho_market_v1_v2") {
      throw new Error(`Unsupported adapter ${allocation.adapter_address}`);
    }

    const adapterMarkets = allocation.caps
      .flatMap(({ market_id }) => (market_id == null ? [] : [market_id]))
      .map((marketId) => {
        const market = marketById.get(marketId.toLowerCase());
        if (market == null) throw new Error(`Missing market ${marketId}`);
        return market;
      });

    return new AccrualVaultV2MorphoMarketV1AdapterV2(
      {
        address: allocation.adapter_address,
        parentVault: vaultConfig.address,
        skimRecipient: zeroAddress,
        marketIds: adapterMarkets.map(({ id }) => id),
        adaptiveCurveIrm,
        supplyShares: Object.fromEntries(
          adapterMarkets.map((market) => {
            const key = `${allocation.adapter_address.toLowerCase()}:${market.id.toLowerCase()}`;
            const position = positionByAdapterMarket.get(key);
            if (position == null) throw new Error(`Missing position ${key}`);
            return [
              market.id,
              requiredBigInt(
                position.supply_shares,
                `supply shares ${key}`,
              ),
            ];
          }),
        ),
      },
      adapterMarkets,
    );
  });

  const assetDecimals = requiredInteger(
    vaultConfig.asset.decimals,
    `asset decimals ${vaultConfig.asset.address}`,
    0,
    255,
  );
  const decimalsOffset = requiredInteger(
    vaultConfig.decimals_offset,
    `decimals offset ${vaultConfig.address}`,
    0,
    18,
  );
  const liquidityAdapterAddress = nullableAddressOrZero(
    vaultConfig.liquidity_adapter,
    `liquidity adapter ${vaultConfig.address}`,
  );
  const liquidityAdapter =
    isAddressEqual(liquidityAdapterAddress, zeroAddress)
      ? undefined
      : adapters.find(({ address }) =>
          isAddressEqual(address, liquidityAdapterAddress),
        );
  if (
    !isAddressEqual(liquidityAdapterAddress, zeroAddress) &&
    liquidityAdapter == null
  ) {
    throw new Error(`Missing liquidity adapter ${liquidityAdapterAddress}`);
  }
  const liquidityData = nullableHexOrEmpty(
    vaultConfig.liquidity_data,
    `liquidity data ${vaultConfig.address}`,
  );
  const penaltyByAdapter = new Map(
    withdrawalOptions.adapter_penalties.map((row) => [
      row.adapter_address.toLowerCase(),
      requiredBigInt(
        row.penalty_rate_wad,
        `force-deallocation penalty ${row.adapter_address}`,
      ),
    ]),
  );

  return new AccrualVaultV2(
    {
      address: vaultConfig.address,
      name: nullableMetadata(
        vaultConfig.name,
        `name ${vaultConfig.address}`,
      ),
      symbol: nullableMetadata(
        vaultConfig.symbol,
        `symbol ${vaultConfig.address}`,
      ),
      decimals: assetDecimals + decimalsOffset,
      asset: vaultConfig.asset.address,
      _totalAssets: requiredBigInt(
        vaultState.total_assets,
        `total assets ${vaultConfig.address}`,
      ),
      totalSupply: requiredBigInt(
        vaultState.total_supply,
        `total supply ${vaultConfig.address}`,
      ),
      virtualShares: 10n ** BigInt(decimalsOffset),
      maxRate: requiredBigInt(
        vaultConfig.max_rate_per_second_wad,
        `max rate ${vaultConfig.address}`,
      ),
      lastUpdate: BigInt(
        requiredInteger(
          vaultState.last_accrual_timestamp,
          `last accrual timestamp ${vaultConfig.address}`,
        ),
      ),
      liquidityAdapter: liquidityAdapterAddress,
      liquidityData,
      liquidityAllocations: undefined,
      performanceFee:
        optionalBigInt(
          vaultConfig.performance_fee_wad,
          `performance fee ${vaultConfig.address}`,
        ) ?? 0n,
      managementFee:
        optionalBigInt(
          vaultConfig.management_fee_wad,
          `management fee ${vaultConfig.address}`,
        ) ?? 0n,
      performanceFeeRecipient: nullableAddressOrZero(
        vaultConfig.performance_fee_recipient,
        `performance fee recipient ${vaultConfig.address}`,
      ),
      managementFeeRecipient: nullableAddressOrZero(
        vaultConfig.management_fee_recipient,
        `management fee recipient ${vaultConfig.address}`,
      ),
    },
    liquidityAdapter,
    adapters,
    requiredBigInt(
      vaultState.idle_assets,
      `idle assets ${vaultConfig.address}`,
    ),
    Object.fromEntries(
      adapters.map((adapter) => {
        const penalty = penaltyByAdapter.get(adapter.address.toLowerCase());
        if (penalty == null) {
          throw new Error(
            `Missing force-deallocation penalty ${adapter.address}`,
          );
        }
        return [adapter.address, penalty];
      }),
    ),
  );
};

const vaults = vaultRows.map(hydrateVault);
```

REST vault timestamp driftThe REST `total_assets` value is live at `last_indexed_block`, but `last_accrual_timestamp` can be older. Hydrating that pair can make subsequent SDK accrual count part of the gap again and affect the simulated total assets or relative-cap headroom. The relative overstatement is bounded by approximately `gapSeconds × max_rate_per_second_wad / 1e18`; multiply that fraction by `total_assets` to express it in asset units. This example accepts that drift to save RPC reads. Use the RPC snapshot path when exact cap headroom is required.

The force-deallocation penalty above belongs to Vault V2 adapter accounting. It is not the caller-paid Public Allocator penalty, which the remaining onchain read returns.

After producing `markets` and `vaults`, fetch the remaining allocator state and assemble the final snapshot:

```
import { fetchVaultV2BluePublicAllocatorData } from "@morpho-org/morpho-sdk/blue/fetch";
import { VaultV2BlueReallocationData } from "@morpho-org/morpho-sdk/entities";

const allocatorEntries = await Promise.all(
  vaults.map(async (vault) => ({
    vault,
    data: await fetchVaultV2BluePublicAllocatorData(vault, client, {
      blockNumber: indexedBlockNumber,
      chainId,
      targetMarketParams: market.marketParams,
    }),
  })),
);

const reallocationData = new VaultV2BlueReallocationData({
  chainId,
  markets: Object.fromEntries(markets.map((item) => [item.id, item])),
  vaults: Object.fromEntries(vaults.map((vault) => [vault.address, vault])),
  allocations: Object.fromEntries(
    allocatorEntries.map(({ vault, data }) => [
      vault.address,
      data.allocations,
    ]),
  ),
  publicAllocatorConfigs: Object.fromEntries(
    allocatorEntries.map(({ vault, data }) => [
      vault.address,
      data.publicAllocatorConfig,
    ]),
  ),
  activeAdapters: Object.fromEntries(
    allocatorEntries.map(({ vault, data }) => [
      vault.address,
      data.activeAdapters,
    ]),
  ),
  marketPublicAllocatorConfigs: Object.fromEntries(
    allocatorEntries.map(({ vault, data }) => [
      vault.address,
      data.marketPublicAllocatorConfigs,
    ]),
  ),
});
```

The allocator fetcher uses one deployless `eth_call` per vault by default and falls back to direct reads. Leave `deployless` unset for the low-credit path. Use `deployless: "force"` only when a predictable call count matters more than fallback compatibility.

Finally, run Step 2 with `timestamp: block.timestamp`. The block-tagged market accounting and allocator reads then share the API's indexed block. Untagged REST state can still come from another indexed block, and a vault's cached accrual timestamp can differ, as described above.

REST hydration is not always possible. Use `getVaultV2BlueReallocationData` when the vault has another SDK-supported adapter, or when a receive-share gate is combined with a management or performance fee. Exclude the vault if the RPC path throws `UnsupportedBlueVaultV2AdapterError`.

## [Handle stale or incomplete plans](#handle-stale-or-incomplete-plans)

| Failure | Response |
| --- | --- |
| `InsufficientSharedLiquidityError` | Reduce the operation or load more eligible vaults, then rebuild. |
| `ReallocationWithdrawExceedsMarketSupplyError` | Reduce the loan-asset withdrawal. |
| `NegativeInputError` | Keep utilization and penalty limits at or above 0%. |
| `InputExceedsMaxError` | Respect the error's `field` and `max`; utilization and penalty limits cannot exceed 100%, and reallocation assets must fit in `uint128`. |
| `NonPositiveInputError` | Pass a positive operation amount, and do not add zero or negative reallocation assets. |
| `ChainIdMismatchError` | Rebuild the snapshot for the target market's chain. |
| `UnknownReallocation*` or `ReallocationAllocationUnderflowError` | Treat the snapshot as incomplete or inconsistent and rebuild it. |
| `InvalidReallocation*`, `InconsistentReallocationPenaltyError`, or `ReallocationWithdrawalOnTargetMarketError` | Do not hand-edit a plan. Rebuild it and preserve its order and fields. |
| `UnknownAddressError` or `UnsupportedChainIdError` | Do not offer Vault V2 Public Allocator liquidity on that chain. |
| Mixed REST indexed blocks | Discard the responses and fetch one coherent snapshot again. |
| Invalid or missing REST field | Fail the quote. Do not coerce it to zero or reuse partial state. |
| Simulation or submission failure | Fetch fresh state and rebuild the whole plan. Do not reuse its order or amounts. |

A plan represents one block-state simulation. A cap change, another reallocation, or changing market shares can invalidate it before inclusion. Always simulate the final transaction after resolving approvals.

## [Source references](#source-references)

- [Vault V2 planner and state simulation](https://github.com/morpho-org/sdks/blob/%40morpho-org%2Fmorpho-sdk-v6.0.0/packages/morpho-sdk/src/entities/vaultV2BlueReallocationData.ts)
- [RPC snapshot construction](https://github.com/morpho-org/sdks/blob/%40morpho-org%2Fmorpho-sdk-v6.0.0/packages/morpho-sdk/src/entities/blue/blue.ts)
- [Allocator fetcher re-export](https://github.com/morpho-org/sdks/blob/%40morpho-org%2Fmorpho-sdk-v6.0.0/packages/morpho-sdk/src/blue/fetch.ts)

[Get Data

Previous Page

](https://docs.morpho.org/developers/borrow/tutorials/get-data/)[Integrate Rewards for Borrow Products

Next Page

](https://docs.morpho.org/developers/borrow/tutorials/rewards/)