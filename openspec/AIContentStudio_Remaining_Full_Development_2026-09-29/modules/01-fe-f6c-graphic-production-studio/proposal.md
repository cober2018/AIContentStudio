## Why

FE-F6A made Graphic a first-class modality but only shipped a JSON shell over `graphic.master.v1`. The North Star requires a professional image/graphic production engine: multi-canvas/card composition, text-on-image as content, project assets, AI-generated imagery, charts, platform dimensions, ordering, rights and variants.

## What Changes

- Add `graphic.master.v2` as the default professional Graphic schema.
- Keep `graphic.master.v1` historical compatibility.
- Add a Studio-owned graphic document: canvases + stable layers.
- Support text, image, chart and basic shape/background layers.
- Treat all visible text as Candidate content, not decoration.
- Bind every image/chart layer to exact project-visible MaterialRevision.
- Add canvas size/aspect presets from exact channel/content-form profiles.
- Add deterministic structure checks plus graphic-specific rights/render checks.
- Add AI/search capability hooks that always materialize selected/generated media into MaterialRevision before use.
- Add multi-canvas reorder, duplication, variants and structured diff.
- Keep final Candidate readiness bound to exact verified/manual final render bytes.
- Build a professional Graphic Studio frontend with canvas list, stage, layers, asset/search/generation side panels and revision history.
- Target no new business table/migration; reuse ContentMasterRevision and existing refs/checks.

## Non-goals

- Full Photoshop/Figma replacement.
- Arbitrary plugin canvas runtime.
- Unverified remote image generation claims.
- Remote publishing changes.
