# Yield & Fees

> Source: https://docs.morpho.org/developers/earn/concepts/yield-fees

---

# Yield & Fees

Understanding how yield is generated and fees are applied in Morpho Vaults is crucial for building accurate earn products and setting proper user expectations.

## [Yield Generation](#yield-generation)

**Morpho Vaults V2** generate yield through the adapters enabled by the curator and allocator. Depending on strategy, those adapters can route capital into Morpho markets and other approved yield sources while reporting the vault's real-time asset value back to the parent vault.

![Vault Architecture](https://docs.morpho.org/img/build/earn/morpho-v2-archi-1.png)

### [Where does the yield comes from?](#where-does-the-yield-comes-from)

### [Borrower Interest](#borrower-interest)

Borrowers in underlying Morpho Markets pay interest

### [Market Distribution](#market-distribution)

Interest flows to lenders in each market

### [Vault Collection](#vault-collection)

Vault collects interest as a lender across multiple markets

### [Share Price Increase](#share-price-increase)

Vault's total assets increase, raising share price

### [Depositor Interest](#depositor-interest)

Depositors earn the interest paid by borrowers as the share of their position increased in token's value amount.

## [Fee Mechanism](#fee-mechanism)

**Morpho Vaults V2** implement a performance fee and a management fee that align curator incentives with vault performance.

### [Performance Fee](#performance-fee)

The fee is taken as a cut on the native yield earned by allocating capital, and is capped at 50%.

### [Management Fee](#management-fee)

For Morpho Vaults V2 only, this management fee is taken on the total asset deposited on the vault, and is capped at 5%.

## [Integration Best Practices](#integration-best-practices)

### [Real-Time Updates](#real-time-updates)

- Update share prices regularly
- Show pending yield that hasn't been reflected in share price yet by accruing interests on the underlying markets
- Display historical performance charts

### [User Education](#user-education)

- Clearly explain that performance fees only apply to yield, not principal, while management fee apply on the principal.

### [Performance Monitoring](#performance-monitoring)

- Track vault performance against benchmarks
- Alert users to significant strategy changes
- Provide detailed yield attribution

[Vaults & ERC4626 Mechanics

Previous Page

](https://docs.morpho.org/developers/earn/concepts/vault-mechanics/)[Rewards for Lenders

Next Page

](https://docs.morpho.org/developers/earn/concepts/rewards/)