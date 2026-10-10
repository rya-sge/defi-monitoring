<!-- SEED: established with the user before implementation; re-run /impeccable document once there's code to capture the actual tokens and components. -->
---
name: riskdep
description: A near-default-HTML reading surface for DeFi position risk, where layout, hierarchy, colour and proximity do all the work.
---

# Design System: riskdep

## Overview

**Thesis.** Start from the browser's own defaults and add only what carries meaning. The document — not a dashboard chrome — is the design: an analyst reads a page, not a product. Every element earns its existence by answering *what is this, how bad is it, what is next to it*. The four basics are the whole brief for now: **layout, hierarchy, colour, proximity**. Nothing else is in scope, and "nothing else" is the point — no cards stacked on cards, no panels, no shadows, no decorative chrome, no gradient, no icon that duplicates a label.

**Material character.** Flat and paper-like. One surface, no layers. Borders only where they separate two things that would otherwise be confused; whitespace does the rest.

**Imagery stance.** None. Data and type only. The dependency graph and the charts are the only non-text objects, and they inherit the same restraint.

**Motion grammar.** None by default. Motion is reserved for a state actually changing (a new alert arriving), never for decoration or entrance.

**Reusable signature.** Severity is readable at a glance in a page that is otherwise monochrome: colour appears almost nowhere, so where it appears it means *act on this*.

## Colors

Strategy: **Restrained** — a monochrome document plus severity. Colour is a signal, not a surface treatment: no coloured regions, no tinted panels, no accent sprinkled for liveliness.

Roles:

- **Ground** — the page background, essentially white (or essentially the UA default). One ground, no secondary surface colour.
- **Ink** — body text at full contrast; a single muted ink for secondary and tabular metadata.
- **Rule** — one hairline colour for the few borders and table rules that remain.
- **Severity: info / warn / critical** — three and only three semantic colours, the one place colour is allowed. They must stay distinguishable without relying on hue alone (a word or a weight carries the level too), because severity is the product's load-bearing signal.
- **Link** — may reuse the info role rather than introducing a fourth hue.

Exact values `[to be resolved during implementation]`. Dark mode `[to be resolved during implementation]`: the current implementation ships one, and whether the minimal world keeps it is undecided.

## Typography

One family, no pairing: the **system UI stack** for prose and labels, and the **system monospace stack** for every machine value (addresses, hashes, amounts, block numbers, health factors). That split is semantic — mono means "this came from the chain" — and it is the only typographic distinction the world needs.

Hierarchy comes from **size, weight and space**, in that order, over as few steps as possible: a page title, a section title, body, and a small metadata size. No letter-spaced micro-caps labels, no italic display, no third weight where two will do. Tabular figures wherever numbers are compared down a column.

Scale ratio and exact sizes `[to be resolved during implementation]`.

## Layout

One column of document flow, measured for reading, with tables and the graph allowed to break out to full width. No sidebar, no sticky chrome beyond the thin nav the routes need.

**Proximity is the primary structural tool**: related things sit close with no container around them, and unrelated things are separated by space rather than by a border or a box. A group that reads as a group needs no card.

Spacing is one small scale, used consistently; the gap between a label and its value is visibly smaller than the gap between two groups, and that difference is what makes the page scan.

Responsive behaviour: the column narrows, tables scroll inside their own horizontal overflow, nothing reflows into a different information architecture. Exact breakpoints and measures `[to be resolved during implementation]`.

## Elevation & Depth

**There is no depth.** No shadows, no overlays, no stacked surfaces, no `z` layering beyond what the nav genuinely requires. If two things need separating, use space, then a hairline rule — never elevation.

## Shapes

Square by default. Corner radius is `0` or near-`0`, applied only where a control would otherwise read as an unfinished rectangle. Borders are 1px hairlines and rare. Form controls stay close to their native appearance.

## Do's and Don'ts

### Do:

- Delete before adding. If removing an element loses no meaning, it was decoration.
- Use space to group; use a border only to prevent a genuine misreading.
- Let severity be the only colour event on the page.
- Keep machine values in mono and prose in the UI face, always.
- Render an absent value as an em dash and a missing check as plain words ("not checked") — absence is information the layout must leave room for.
- Keep severity legible without colour: a level is also a word.

### Don't:

- Don't wrap content in a card, panel or bordered box by reflex.
- Don't add shadows, gradients, radii beyond the near-zero default, or any entrance animation.
- Don't introduce a display face, a second body family, or a fourth hue.
- Don't use colour to make the page feel designed.
- Don't invent a KPI, a trend arrow or a sparkline the CLI does not actually produce.
