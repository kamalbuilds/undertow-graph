# Undertow design system

## Art direction
A deep-water instrument panel. The field is nearly black-teal, the way light falls off a few metres under the surface, and the only light in it is the data itself. One cyan accent marks the primary action and the live selection; a warm orange-to-red ramp marks loss and nothing else.

## Typefaces (two, neither on the banned list)
- **IBM Plex Sans** for UI and prose. Engineered and slightly technical, it stays calm at 12 to 15px and is not Inter, Roboto, Arial or a system stack.
- **IBM Plex Mono** for every number, address, symbol and Cypher block. Fixed width so figures align column to column across the rail, the graph labels and the Cypher panel.
Load both from Google Fonts with `display=swap`; do not self-host a second family.

## Type scale (size / tracking)
- display 40px / -0.8px (the headline loss pair)
- h1 28px / -0.4px (section heads)
- h2 20px / -0.2px (panel titles)
- body 15px / 0 (labels, chat)
- label 12px / +0.06em uppercase (muted field labels)
- figure 14px / 0, `tabular-nums` (every value in a column)
- micro 12px / 0 (path text, provenance lines, hit counts)

Negative tracking only on display and section heads. Uppercase small caps only for field labels. Tabular figures only in tables, rails and the graph legend.

## Colour at 70 / 20 / 10
- 70 percent field: `--bg` #07131a, `--panel` #0c1f29, `--line` #16323f
- 20 percent text: `--ink` #e6f1f5, `--muted` #7f9aa6
- 10 percent accent: `--accent` #3ee0c5, one job: the single primary action ("Run shock") and the live-selected row / node outline
- loss ramp (semantic, not accent): `--loss-1` #f4a259 (small loss) to `--loss-2` #e4572e (severe loss). Deeper red means a bigger loss; the ramp never decorates a non-loss element.
No green in the interface. The accent is not a status colour and the loss ramp is not a brand colour.

## Spacing and radius
8px scale: 4, 8, 12, 16, 24, 32, 48, 64. Radii: 8px on panels and cards, 6px on controls and chips. No radius on the top bar or section rules (they are hairlines at `--line`). No pill radius except the short "wrapped by" chips in the asset rail.

## Background atmosphere
One very low-opacity radial wash from `--panel` at the top-left corner into `--bg`, nothing else. No blobs, no neon, no grain, no glow behind the graph. The graph sits on the flat field so node colour is the only thing that lights up.

## Motion
One orchestrated page-load: top bar, left rail, centre graph, right panel rise 8px and fade in over 320ms in a single stagger, then stop. Everything after that is user-triggered: the shock travels the graph as a pulse whose hop delay is `hops * 400ms`, and hit figures count up once. `prefers-reduced-motion: reduce` removes all transforms, keeps opacity fades, and snaps the pulse to its end state immediately.

## Refusal list
No purple, violet or pink gradients. No blue-to-pink. No glassmorphism, frosted blur or neon glow. No "hacker terminal" green-on-black. No three equal feature cards. No big-metric template (giant number plus small label plus accent). No cards inside cards. No emoji icons. No sparkline theatre or elastic bounce. No status pills everywhere. No Inter, Roboto, Arial or system display face. No radius on every surface. No centered marketing hero. No em dashes in visible copy.

## Structure stolen from real screens
- **Hyperliquid** (north star): zoned dense dark terminal, loss expressed as colour, every figure in one tabular grid.
- **Spark** (secondary): ranked left rail where the name sits left and the value sits right, the selected row carrying an accent rule; a one-line inline stat strip above the panel.
- **Morpho Vaults** (the product this replaces): monochrome with hairline row separators, restrained radii, label left and louder value right.
- **d3 force-directed graph**: nodes sized by degree, halo labels so text survives over links, low-opacity links whose weight maps to a value.
- **Our World in Data**: every figure carries a small muted source line directly beneath it, so a number is never naked.

## Screen job
The first screen answers one question: "if this asset were haircut, which of my vaults and whose vaults take the hit, and how far does it travel." The primary action is choose asset then "Run shock". The primary metric is the two-number pair, direct vaults versus graph vaults, in display type. Provenance and the Cypher trail sit behind a click, not above the fold.
