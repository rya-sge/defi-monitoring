# Claim Rewards

> Source: https://docs.morpho.org/developers/rewards/tutorials/claim-rewards

---

# Claim Rewards

This tutorial shows you how to implement reward claiming for **Merkl** programs in your application.

## [Overview](#overview)

Claiming rewards involves:

1. Fetching claim data (proof + transaction data) from the appropriate API
2. Constructing or using pre-formatted transaction calldata
3. Submitting the claim transaction onchain
4. Handling the response and updating your UI

## [Prerequisites](#prerequisites)

- Understanding of [Distribution Systems](https://docs.morpho.org/developers/rewards/concepts/distribution-system/)
- Familiarity with [Fetching Rewards Data](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/)
- A web3 library (viem, ethers, web3.js)
- User's wallet connected to your app

## [Claiming via Merkl](#claiming-via-merkl)

Merkl is the primary distribution system for current reward programs.

### [Step 1: Fetch Claim Data](#step-1-fetch-claim-data)

**Endpoint:**

```
GET https://api.merkl.xyz/v4/users/{address}/rewards?chainId={chainId}
```

The `{address}` must be lowercase, and `chainId` is required. The same endpoint returns everything you need to claim: the token, the cumulative `amount`, the already-`claimed` amount, and the merkle `proofs`.

**Example:**

```
async function fetchMerklRewards(
  userAddress: string,
  chainId: number
): Promise<MerklReward[]> {
  const response = await fetch(
    `https://api.merkl.xyz/v4/users/${userAddress.toLowerCase()}/rewards?chainId=${chainId}`
  );

  if (!response.ok) {
    throw new Error(`Merkl API error: ${response.status}`);
  }

  // The endpoint returns an array of per-chain objects; flatten to a flat list of rewards.
  const data: MerklChainRewards[] = await response.json();
  return data.flatMap((entry) => entry.rewards);
}
```

**Response Structure:**

```
[
  {
    "chain": { "id": 8453, "name": "Base" },
    "rewards": [
      {
        "token": { "address": "0xTOKEN", "symbol": "MORPHO", "decimals": 18 },
        "amount": "2000000000000000000",
        "claimed": "1000000000000000000",
        "pending": "0",
        "proofs": ["0xproof1a", "0xproof1b"]
      }
    ]
  }
]
```

`amount` is the cumulative total earned to date and `claimed` is the cumulative amount already claimed onchain — both are passed as-is. The distributor transfers the difference (`amount - claimed`), so you do **not** subtract them yourself. `pending` is reward that is not yet in a live merkle root and cannot be claimed.

**Validate claim data before signing.** The `tokens`, `amounts`, and `proofs` come from an external API and are passed straight into an onchain `claim` that moves funds. Treat the response as untrusted: confirm the token addresses are ones you expect and the amounts are non-zero before prompting the user to sign.

### [Step 2: Execute the Claim](#step-2-execute-the-claim)

Using **viem**:

```
import { createWalletClient, custom } from "viem";
import { mainnet } from "viem/chains";

// Same Distributor address across all supported chains
const MERKL_DISTRIBUTOR = "0x3Ef3D8bA38EBe18DB133cEc108f4D14CE00Dd9Ae";

async function claimMerklRewards(
  userAddress: string,
  chainId: number
) {
  // 1. Fetch the user's rewards
  const rewards = await fetchMerklRewards(userAddress, chainId);

  // Keep only genuinely-claimable rewards — entries with no proofs or nothing
  // left to claim make the whole `claim` tx revert with `InvalidProof`.
  const claimable = rewards.filter(
    (r) => r.proofs.length > 0 && BigInt(r.amount) > BigInt(r.claimed)
  );

  // Build the parallel, index-aligned arrays the contract expects
  const users = claimable.map(() => userAddress);
  const tokens = claimable.map((r) => r.token.address);
  const amounts = claimable.map((r) => BigInt(r.amount)); // cumulative; pass as-is
  const proofs = claimable.map((r) => r.proofs);

  // 2. Setup wallet client
  // The claim must be sent from the user's own wallet — a third-party sender
  // reverts with `NotWhitelisted` unless it has been approved as an operator.
  const walletClient = createWalletClient({
    account: userAddress,
    chain: mainnet,
    transport: custom(window.ethereum),
  });

  // 3. Send claim transaction
  const hash = await walletClient.writeContract({
    address: MERKL_DISTRIBUTOR,
    abi: MERKL_ABI,
    functionName: "claim",
    args: [users, tokens, amounts, proofs],
  });

  // 4. Wait for confirmation
  const receipt = await walletClient.waitForTransactionReceipt({ hash });

  return receipt;
}

// Merkl Distributor ABI (claim function)
const MERKL_ABI = [
  {
    inputs: [
      { name: "users", type: "address[]" },
      { name: "tokens", type: "address[]" },
      { name: "amounts", type: "uint256[]" },
      { name: "proofs", type: "bytes32[][]" },
    ],
    name: "claim",
    outputs: [],
    stateMutability: "nonpayable",
    type: "function",
  },
] as const;
```

### [Step 3: Handle the Result](#step-3-handle-the-result)

```
try {
  const receipt = await claimMerklRewards(userAddress, 1);

  if (receipt.status === "success") {
    console.log("✅ Merkl rewards claimed successfully!");
    // Update your UI to reflect claimed rewards
  } else {
    console.error("❌ Claim transaction failed");
  }
} catch (error) {
  console.error("Error claiming Merkl rewards:", error);
  // Show error message to user
}
```

For more details on Merkl claiming, see the [official Merkl documentation](https://docs.merkl.xyz/integrate-merkl/app#claiming-user-rewards).

## [Legacy Rewards (Pre-Merkl)](#legacy-rewards-pre-merkl)

**Legacy Rewards API Deprecated**

The `rewards.morpho.org` API has been deprecated. If you or your users have unclaimed rewards from historical Morpho programs (pre-Merkl migration), they can be claimed directly through the legacy rewards lookup app:

👉 **[rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/)**

All new reward programs are distributed exclusively via [Merkl](https://app.merkl.xyz/). See the [Merkl documentation](https://docs.merkl.xyz/) for integration details.

## [Resources](#resources)

- **Merkl Claim Docs**: [docs.merkl.xyz/integrate-merkl/app#claiming-user-rewards](https://docs.merkl.xyz/integrate-merkl/app#claiming-user-rewards)
- **Legacy Rewards Lookup**: [rewards-legacy.morpho.org](https://rewards-legacy.morpho.org/)

[Fetch Rewards Data

Previous Page

](https://docs.morpho.org/developers/rewards/tutorials/fetch-rewards-data/)[Integrate Rewards Display

Next Page

](https://docs.morpho.org/developers/rewards/tutorials/integrate-display/)