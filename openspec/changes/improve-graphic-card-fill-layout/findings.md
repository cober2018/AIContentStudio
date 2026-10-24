# Findings

- 2026-10-22: layout-compose@1 uses fixed sizes (title 60/48, body 30–38) and stacks from the top; the 海底光缆 cover preview left about two-thirds empty.
- The renderer wraps text in boxes with `lineHeight: normal`; the composer and QC estimate 1.4× line height, so fitting with the same estimate keeps compose and QC consistent.
- Persona configs reference the tool by ref only (no package hash), so updating SKILL.md does not break persona resolution; pending proposals report tool_changed by design.
- User chose type fill only; key-number emphasis and images on cards are out of scope.
- With fixed caps, every density hit the same caps on short cards, so density stopped changing the output; caps now scale by density body base / 34.
- Sample result: all 7 cards reach the caps (title 120/84, body 56). Text is about 2× larger and the block sits mid-card, but short cards (cover, card 1) still leave the lower ~40% empty — caps, not fitting, now limit them.
- The text estimate counts every character as full width; lines with digits/Latin render shorter, so some boxes reserve an extra line (visible as uneven bullet gaps on card 6). Pre-existing estimate, shared with QC; not changed here.
