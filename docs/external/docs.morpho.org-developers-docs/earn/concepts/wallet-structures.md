# Wallet Structures

> Source: https://docs.morpho.org/developers/earn/concepts/wallet-structures

---

# Wallet Structures

When integrating Morpho Earn, the wallet architecture you choose determines how user assets flow onchain, who holds custody of assets, and how accounting is handled. This page presents the five main wallet structures available to integrators.

## [Overview](#overview)

| # | Structure | Custody | Onchain positions |
| --- | --- | --- | --- |
| 1 | Omnibus only | Integrator | Single shared wallet |
| 2 | Omnibus + custodial wallets | Integrator | Per-user wallets |
| 3 | Custodial wallets only | Integrator | Per-user wallets |
| 4 | Omnibus + non-custodial wallets | User | Per-user wallets |
| 5 | Non-custodial wallets only | User | Per-user wallets |

## [1. Omnibus Only](#1-omnibus-only)

All user assets are pooled in one omnibus account, with virtual accounting handled off-chain.

- **Typical Actors**: CEXs & CeFi
- **Tech Providers**: Bridge, Fireblocks, Taurus or custom KMS
- **Earn integration key points**:

  - Offchain accounting needed (already standard for CeFi)
  - Integrator must handle reward distribution to user balances

![Omnibus Only](https://docs.morpho.org/img/build/earn/omnibus-only.png)

## [2. Omnibus + Custodial Wallets](#2-omnibus--custodial-wallets)

Default omnibus entry point, but with per-user onchain wallets (custodial: the user does not hold the private keys).

- **Typical Actors**: CEX, CeFi, neo-banks
- **Tech Providers**: Bridge, Fireblocks, Taurus
- **Earn integration key points**:

  - Individualized positions onchain
  - Integrator side must manage reward allocation & gas efficiency

![Omnibus + Custodial Wallets](https://docs.morpho.org/img/build/earn/omnibus-custo.png)

## [3. Custodial Wallets Only](#3-custodial-wallets-only)

Only per-user wallets, fully managed by the integrator (no omnibus).

- **Typical Actors**: Stripe-like models, custodial fintechs
- **Tech Providers**: Bridge, Fireblocks, Taurus
- **Earn integration key points**: Straightforward Earn setup, no omnibus complexity

![Custodial Wallets Only](https://docs.morpho.org/img/build/earn/custo-wallet-only.png)

## [4. Omnibus + Non-Custodial Wallets](#4-omnibus--non-custodial-wallets)

Omnibus for entry, but users have non-custodial wallets with some integrator-controlled features.

- **Typical Actors**: CEXs onchain oriented
- **Tech Providers**: Smart contract wallets (Alchemy, Gelato), SDKs & AA tooling (Privy, Turnkey)
- **Earn integration key points**:

  - Earn flows are user-controlled onchain or in the app
  - Integrator can retain some control logic

![Omnibus + Non-Custodial Wallets](https://docs.morpho.org/img/build/earn/omnibus-non-custo.png)

## [5. Non-Custodial Wallets Only](#5-non-custodial-wallets-only)

Pure onchain setup. No omnibus, users fully manage their own wallets.

- **Typical Actors**: Onchain protocols
- **Tech Providers**: Non-custodial wallets (Metamask, Rabby, Safe, Ledger, ...)
- **Earn integration key points**: n/a (fully decentralized)

![Non-Custodial Wallets Only](https://docs.morpho.org/img/build/earn/non-custo-wallet-only.png)[Fee Wrapper

Previous Page

](https://docs.morpho.org/developers/earn/concepts/fee-wrapper/)[Depositing & Withdrawing from Vaults

Next Page

](https://docs.morpho.org/developers/earn/tutorials/assets-flow/)