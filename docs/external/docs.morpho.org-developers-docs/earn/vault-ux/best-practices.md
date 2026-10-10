# Best Practices for Vault Integrators

> Source: https://docs.morpho.org/developers/earn/vault-ux/best-practices

---

# Best Practices for Vault Integrators

These are best practices, not requirements. Every team's product and users are different, so each item should be adapted to the product context. A few items are flagged because they tend to matter most for end-user trust.

## [Product vocabulary](#product-vocabulary)

> **Why it matters.** The words set the expectations. Users who hear *staking* expect lock-ups and validator risk. Users who hear *guaranteed* expect a promise no interface can make. Clean vocabulary is the highest-leverage thing any integration can get right, because it flows into every other screen.

*Particularly important for user trust.*

**Best practices**

- Use **Earn** or **DeFi yield** for vault deposits. Integrators should steer away from *staking* or *investment* because those terms carry expectations that do not match how Morpho Vaults work.
- When describing yield, **variable** or **indicative** is the framing that tends to hold up best.
- Referring to vaults as **Morpho Vaults** or **vault smart contracts** keeps the technical reality intact for users who care to dig in.

## [Yield composition](#yield-composition)

> **Why it matters.** When rewards get blended into a single headline APY, users expect that number to land in their wallet as the deposit asset. When part of it is a different token, on a different schedule, confusion can arise. Rewards are calculated and displayed as APR, not APY, meaning they reflect the simple annual rate without accounting for the effects of compounding.

*Particularly important for user trust.*

**Best practices**

- When rewards exist, split the displayed yield or return into clear components:

  - **Base/native APY:** the borrower-paid interest, autocompounding, paid in the deposit asset.
  - **Rewards APR:** named by token, with schedule where relevant.
- Naming the token each component pays in is the detail that does the most work here. A single blended figure, however accurate on paper, sets the wrong expectation.
- **Variable** or **indicative** is the framing that holds up across market conditions. *Guaranteed* and *risk-free* do not match the reality of on-chain yield.

**Nice to have**

- A short note about autocompounding on the product-detail screen is a genuine selling point that gets lost when APY is flattened.
- If the rewards program has an end date, showing it prevents the awkward moment when rewards expire.

## [Vault transparency](#vault-transparency)

> **Why it matters.** Morpho Vault architecture is designed so users know which vault they're in, who curates it, and what collateral or underlying source it is exposed to.

*Particularly important for risk surfacing and user trust.*

**Best practices**

- Showing the **vault name** on the deposit flow, review screen, and post deposit view preserves the information Morpho architecture is designed to expose. Generic labels like "Earn USDC" or wrapped receipt token names tend to obscure it.
- Making underlying collateral or adapters reachable in a tap or two from product detail goes a long way. Users do not need every market's full composition up front, but they do benefit from knowing what they're exposed to. Alternatively, linking to Morpho’s page can provide all the advanced vault data.
- Adding allocation percentages across underlying markets/adapters, and collateral where relevant gives savvy users a complete picture.
- Surfacing instantly withdrawable liquidity can reassure users. See [Compute deposit and withdrawal limits](https://docs.morpho.org/developers/earn/tutorials/assets-flow/#compute-deposit-and-withdrawal-limits) for how to read it.
- Naming the curator on the product detail or review screen, with their logo where available, treats the curator as the trust signal they are. Links to their website/X account can also be provided.
- Showing the vault’s TVL on the product detail or review screen helps users calibrate.
- A one line vault thesis ("Blue chip markets curated by X") does a lot of work for low effort.

## [Vault benefits messaging](#vault-benefits-messaging)

> **Why it matters.** Morpho Vaults offer three key differentiators for end users within integrators’ earn product: no fixed lock-ups, autocompounding yield, and non-custodial architecture.

**Best practices**

- Communicating the three headline benefits on the product-detail screen tends to work well:

  - **No fixed lock-ups:** users can attempt withdrawals anytime, with execution subject to available vault or adapter liquidity.
  - **Native yield auto-compounds:** yield from the vault’s underlying allocations is reflected in the vault receipt token value and paid in the deposit asset.
  - **Non-custodial:** user assets flow through Morpho Vault smart contracts.

## [Educational redirection](#educational-redirection)

> **Why it matters.** Users who understand what they're depositing into will deposit more and churn less. A little context in-flow tends to outperform extensive docs buried behind a footer link.

**Best practices**

- At least one outbound path to Morpho docs or a top-level Earn explainer from the product-detail screen gives curious users somewhere to go.
- A clear CTA ("Learn more about Morpho", or contextual equivalent) works better than a buried footer link.

## [Activation surfaces](#activation-surfaces)

> **Why it matters.** "Eligible assets" prompts and idle-balance nudges are among the highest-intent moments in an integrator app.

**Best practices**

- When the app surfaces "eligible assets" or an idle-balance prompt, pairing it with a **deposit CTA** inside the component itself keeps the intent alive.
- After deposit, showing the user's Morpho powered position alongside the rest of their balance rather than in a separate tab tends to feel more integrated.

## [A light self-review](#a-light-self-review)

Before launch, a quick pass through this list tends to catch the things that matter most. Treat it as a conversation starter for an internal review, not a checklist to tick off.

- Is the language aligned?
- Is “Powered by Morpho” visible wherever users interact with Morpho functionality?
- Is there a distinct moment where users see the Morpho protocols' disclaimers?
- Is the displayed yield or return transparent about where it comes from and what token each part pays in?
- Can a user name the vault they're depositing into without leaving the flow?
- Is the curator named somewhere a user will actually look?
- Are headline benefits visible on product detail?
- Is there a path to learn more from the product-detail screen?
- Do idle-balance prompts actually go somewhere?

[UX Requirements

Previous Page

](https://docs.morpho.org/developers/earn/vault-ux/ux-requirement/)[Resources

Next Page

](https://docs.morpho.org/developers/earn/resources/all/)