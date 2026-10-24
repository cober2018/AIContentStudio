## Why

The platform's card layout tool (`studio.graphic.layout-compose@1`) stacks text from the top at fixed sizes (title 60/48, body 30–38). Short cards end up with small text crowded at the top and about two-thirds of the canvas empty. This was seen on the 海底光缆 sample (project 41, unit 79) on 2026-10-22. It affects every card set the platform produces, so the user asked to upgrade the tool so type scales to fill the space (2026-10-22).

## What Changes

- **Type scales to the card.** For each card, the tool picks the largest uniform scale (from 1× up to a cap) at which the title, body, bullets and diagram labels still fit the safe area with breathing room. Current sizes are the floor, so a card that fits today never gets smaller text and never newly overflows.
  - Caps: cover title 120, body-card title 84, body and bullets 56, diagram labels 40.
  - Density still sets the base sizes, and the caps scale with density (low larger, high smaller), so density still changes short cards.
- **Content is placed vertically, not stuck to the top.** The whole block (accent bar, title, visual, body, bullets) sits slightly above the optical centre of the safe area.
- **Title height follows its real line count** instead of always reserving two lines.
- **Unchanged:**
  - Margins, palettes and templates.
  - Image and diagram slots.
  - Claim and evidence mapping.
  - The overflow and geometry checks, which use the same text estimate as the fitter.
  - Card count, roles and every blocking rule.
- **Versioning:** the tool keeps the ref `@1`. Its `SKILL.md` is updated, which changes the package hash. Pending proposals made by the old layout are therefore reported as `graphic_composition_tool_changed` and must be regenerated. Already accepted Masters are stored payloads and are not touched.

Out of scope: enlarging key numbers, placing matched images on cards, and font weight or colour changes. These were offered, but the user chose type fill only.

## Impact

- Code: `apps/api/app/services/graphic_composition.py` (`compose`).
- Skill text: `apps/api/app/studio_skills/studio.graphic.layout-compose/v1/SKILL.md`.
- No schema, API, frontend or migration change.
- Sample: unit 79 cards are regenerated with the new layout, rendered, and shown to the user before acceptance.
