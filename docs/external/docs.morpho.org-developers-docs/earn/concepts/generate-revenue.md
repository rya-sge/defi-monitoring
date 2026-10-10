# How can distributors generate revenue on Morpho?

> Source: https://docs.morpho.org/developers/earn/concepts/generate-revenue

---

# How can distributors generate revenue on Morpho?

**There are different ways to generate revenue on Morpho.**

Curators and distributor channels have different ways to charge fees.

A distributor channel is any platform, application, or service that integrates Morpho's functionality to offer it to their own users. This includes wallets, DeFi aggregators, portfolio management apps, or custom interfaces that embed Morpho vaults. These distributors make Morpho accessible to users who might not otherwise directly interact with the Morpho protocol, and they can earn fees by facilitating these interactions.

To generate revenue, a distributor has several possibilities developed below:

- Own its own revenue layer (a Fee Wrapper or a Vault V2 Wrapper)
- Have an agreement with a curator (onchain or offchain)

## [Fees](#fees)

Morpho Vault V2 can charge two types of fees: a **performance fee** on native yield and a **management fee** on assets under curation. See [Fee](https://docs.morpho.org/curate/concepts/fee/) for detailed fee mechanics and caps.

## [Architecture](#architecture)

Here is the setup of the current Earn architecture with USDC as an example

![Earn Architecture](https://docs.morpho.org/img/build/earn/earn-architecture.png)
Here is the vault model illustrating asset flow in terms of allocation

![Vaults Allocation](https://docs.morpho.org/img/build/earn/morpho-v2-archi-1.png)

## [Examples of possible configurations](#examples-of-possible-configurations)

| Model | Control | Trust Required | Complexity | Best For |
| --- | --- | --- | --- | --- |
| **Fee Wrapper** | High | None | Low | B2B distribution, per-customer vaults |
| **V2 Wrapper** | High | None | Low | Independent distributors |
| **Offchain Agreement** | Shared | High | Medium | Strategic partnerships |
| **Onchain Splitter** | Shared | None | High | Formal trustless partnerships |

---

### [1. Fee Wrapper](#1-fee-wrapper)

![Wrapper Model](https://docs.morpho.org/img/build/earn/fee-wrapper.png)
A **Fee Wrapper** is a Vault V2 configured in a specific, constrained mode that enables
distribution channels to add a fee layer on top of an existing Morpho Vault V2.

Fee Wrappers are the recommended approach for B2B distribution, per-customer vaults,
and white-label products. They provide high control with no trust required and low complexity.

For full details on architecture, gates & non-custodiality, deployment, and integration,
see the dedicated [Fee Wrapper](https://docs.morpho.org/developers/earn/concepts/fee-wrapper/) page.

A Fee Wrapper is only non-custodial if both the wrapper and its underlying vault have abdicated their critical gates, and the underlying vault has also abdicated its `sendAssetsGate`. See [Underlying vault gates](https://docs.morpho.org/developers/earn/concepts/fee-wrapper/#underlying-vault-gates).

**The fee recipient wallet must be able to interact with the vault**.
Fees are always minted as shares. To convert them to the underlying asset, the fee recipient must call `redeem()` at some point. Two options:

- **Direct redemption**: the fee recipient periodically calls `redeem()` themselves.
- **Delegated redemption**: the fee recipient calls `approve(claimerAddress, type(uint256).max)` once (approval on the vault receipt token, not the underlying asset), then another address can call `redeem(shares, feeRecipient, feeRecipient)` on an ongoing basis.

The fee recipient must be an address capable of interacting with the vault (EOA, smart wallet, multisig, etc.). A fully passive address that never interacts with the chain won't be able to actually receive the fee in the underlying asset.

---

### [2. Offchain Agreement Model](#2-offchain-agreement-model)

**Setup:** Distributor and curator establish a legal revenue-sharing agreement for liquidity provided.

**Two Options:**

**Option A - New Dedicated Vault:**

![Offchain New](https://docs.morpho.org/img/build/earn/offchain-new-vault-1.png)

- Curator launches a new dedicated vault exclusively for the distributor's users
- Fee split negotiated up-front (e.g., 50/50 on performance fees)
- Clean attribution of liquidity and fees

---

**Option B - Existing Vault:**

![Offchain Existing](https://docs.morpho.org/img/build/earn/offchain-existing-vault-1.png)

- Distributor directs users to existing vault
- Revenue share calculated based on tracked liquidity contribution
- Requires tracking mechanism (transaction mapping, user addresses, time-weighted deposits)

**Considerations:**

- Legal contract enforces agreement
- Option B requires reliable attribution system
- Settlement handled offchain (periodic payouts)

**Use Case:** Best for strategic partnerships where trust exists or when onchain complexity isn't warranted.

---

### [3. Onchain Splitter Contract Model](#3-onchain-splitter-contract-model)

![Splitter Contract](https://docs.morpho.org/img/build/earn/splitter-contract-1.png)
**Setup:** Smart contract automatically splits fees between curator and distributor based on pre-defined terms.

**Requirements:**

- Dedicated new vault for the partnership
- Splitter contract receives fee recipient role
- Automated distribution of fees to both parties

**Fee Flow:**

1. Vault accrues performance/management fees
2. Fees sent to splitter contract
3. Contract automatically distributes per agreement (e.g., 60% curator / 40% distributor, or 50/50)

**Advantages:**

- Trustless execution
- Transparent onchain tracking
- No manual settlement required

**Trade-offs:**

- Requires dedicated vault (curator unlikely to share existing vault)
- Additional smart contract complexity
- Gas costs for splitting operations

**Use Case:** Best for formal partnerships requiring trustless, transparent revenue sharing with onchain guarantees.

[Rewards for Lenders

Previous Page

](https://docs.morpho.org/developers/earn/concepts/rewards/)[Fee Wrapper

Next Page

](https://docs.morpho.org/developers/earn/concepts/fee-wrapper/)