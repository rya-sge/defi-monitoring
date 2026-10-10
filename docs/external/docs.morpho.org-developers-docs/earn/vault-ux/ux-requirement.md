# UX Requirements

> Source: https://docs.morpho.org/developers/earn/vault-ux/ux-requirement

---

# UX Requirements

When building an Earn product on Morpho, you must follow these UX requirements to help users understand what they're interacting with and ensure a transparent experience.

## [Brand & attribution](#brand--attribution)

> **Why it matters.** The Powered by Morpho badge is the shortest way to communicate to users that your app is the interface and Morpho is the protocol. Integrators who get this framing right tend to have cleaner regulatory conversations and clearer user support.

- Surface “Powered by Morpho” on the screens where users actually interact with Morpho functionality, typically the deposit flow, the review step, the post-deposit view, and the product detail screen.
- The official `powered-by-morpho` web component or the official static badge both work. If either does not fit a surface, contact the support team so the asset pack can be adapted rather than rebuilding the mark.
- Matching the badge theme to the UI surface (light on light, dark on dark) tends to read best.
- Somewhere reachable from the badge, users benefit from seeing the short disclaimer. The web component does this via tooltip.

**Reference.** [https://brand.morpho.org](https://brand.morpho.org) / [snippet.js](https://brand.morpho.org/snippet.js)

## [Morpho disclosures](#morpho-disclosures)

> **Why it matters.** Morpho is an immutable, permissionless, and non-custodial protocol and its partners provide interfaces. A distinct moment where users see the Morpho protocols' disclaimers keeps that line legible for users and regulators alike, and protects both sides.

Before or upon any end user’s first interaction with the Morpho protocols through an integrator product, present a notice substantially in the following form and ask the user to acknowledge it:

“*Accessing the Morpho Protocol through this app is governed by [Integrator’s] Terms of Use and [Morpho’s Disclaimer](https://morpho.org/disclaimers/). By using it, you acknowledge that you have read and understood these terms and the risks involved*.”

This acknowledgment should happen before the user accesses or interacts with the Morpho protocols through the product.

**Reference:** [morpho.org/disclaimers](https://morpho.org/disclaimers)

[Integrate Rewards for Earn Products

Previous Page

](https://docs.morpho.org/developers/earn/tutorials/rewards/)[Best Practices for Vault Integrators

Next Page

](https://docs.morpho.org/developers/earn/vault-ux/best-practices/)