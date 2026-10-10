# Vaults & ERC4626 Mechanics

> Source: https://docs.morpho.org/developers/earn/concepts/vault-mechanics

---

# Vaults & ERC4626 Mechanics

**Morpho Vault V2** exposes the standard [ERC‑4626](https://eips.ethereum.org/EIPS/eip-4626) interface for tokenized vaults. Understanding these mechanics is essential for building robust Earn integrations.

## [ERC4626 Standard](#erc4626-standard)

The ERC‑4626 standard defines four core functions for deposits and withdrawals.

### [Core Functions](#core-functions)

#### [Deposit](#deposit)

```
// Deposit a specific amount of underlying assets.
// Example: deposit 10 USDC and receive N vault shares.
function deposit(uint256 assets, address receiver) external returns (uint256 shares);

// Mint a specific amount of shares.
// Example: mint N shares; the corresponding assets are pulled from the user.
function mint(uint256 shares, address receiver) external returns (uint256 assets);
```

#### [Withdraw](#withdraw)

```
// Withdraw a specific amount of assets.
// Example: withdraw 10 USDC; N shares are burned.
function withdraw(uint256 assets, address receiver, address owner) external returns (uint256 shares);

// Redeem a specific amount of shares for assets.
function redeem(uint256 shares, address receiver, address owner) external returns (uint256 assets);
```

## [Assets vs. Shares](#assets-vs-shares)

**Assets** are the underlying token (e.g., USDC, WETH).

**Shares** represent proportional ownership of the vault and typically appreciate as yield accrues.

### [Conversions](#conversions)

```
// Convert assets to shares (pre‑deposit expectation).
const shares = await vault.previewDeposit(assetAmount);

// Convert shares to assets at the current rate.
const assets = await vault.convertToAssets(shareAmount);

// Estimate shares needed to withdraw a target asset amount.
const sharesNeeded = await vault.previewWithdraw(assetAmount);

// Estimate assets received when redeeming shares.
const assetsReceived = await vault.previewRedeem(shareAmount);
```

## [Share Price Appreciation](#share-price-appreciation)

Vault performance is reflected in the share price:

```
// 1 vault share = 1e18
const sharePrice = await vault.convertToAssets(10n ** 18n);
// Example: totalAssets grows from 1.0M to 1.1M with 1.0M shares
// -> price from $1.00/share to $1.10/share (≈10%)
```

## [Inflation Attack Protection](#inflation-attack-protection)

ERC4626 vaults are susceptible to [share inflation attacks](https://docs.openzeppelin.com/contracts/5.x/erc4626), where an attacker manipulates the share price to cause rounding losses for subsequent depositors. This affects all ERC4626-compliant implementations.

### [The Protection Mechanism](#the-protection-mechanism)

Before interacting with a vault, verify that a **dead deposit** has been made to address `0x000000000000000000000000000000000000dEaD`. This initial deposit establishes a baseline share supply that makes inflation attacks economically unfeasible.

The minimum number of dead shares depends on the asset's decimals: `max(1e9, 10^(6 + max(0, 18 - decimals)))`, for example 1e9 shares for an 18-decimal asset and 1e18 shares for a 6-decimal asset. See [Dead Deposit](https://docs.morpho.org/curate/tutorials-v2/dead-deposit/) for the share amount per asset and how it's derived.

**The Check:**

```
// Verify the vault has adequate dead deposit protection
const deadAddress = "0x000000000000000000000000000000000000dEaD";
const deadShares = await vault.balanceOf(deadAddress);

// assetDecimals: decimals() of the vault's underlying asset
const decimalsOffset = BigInt(Math.max(0, 18 - assetDecimals));
const minDeadShares = 10n ** (6n + decimalsOffset);
const threshold = minDeadShares > 1_000_000_000n ? minDeadShares : 1_000_000_000n;

if (deadShares < threshold) {
  throw new Error("Vault lacks adequate inflation protection");
}
```

**Implementation Notes:**

- The dead deposit does not need to be made atomically with your interaction
- Once established, it cannot be withdrawn (by design)
- Morpho Vault V2 integrations should verify that this protection is in place
- Curators and vault deployers are responsible for ensuring this protection exists

This protection is essential for vault security. Always verify the dead deposit exists before integrating a vault into production systems. Learn more about the attack mechanism in the [OpenZeppelin ERC4626 documentation](https://docs.openzeppelin.com/contracts/5.x/erc4626).

## [Additional Considerations: Slippage](#additional-considerations-slippage)

ERC4626 functions do not include built-in slippage checks. While not a security requirement (when dead deposit protection is in place), slippage checks can improve user experience by preventing unexpected exchange rate movements between transaction simulation and execution.

**When to consider slippage protection:**

- Share price may shift due to interest accrual or other vault activity between simulation and inclusion
- User-facing applications benefit from showing expected vs. actual amounts received
- Implement min-received checks around ERC4626 operations for direct integrations

See the [Assets Flow tutorial](https://docs.morpho.org/developers/earn/tutorials/assets-flow/#slippage-for-user-experience) for integration examples.

[Get Started

Previous Page

](https://docs.morpho.org/developers/earn/get-started/)[Yield & Fees

Next Page

](https://docs.morpho.org/developers/earn/concepts/yield-fees/)