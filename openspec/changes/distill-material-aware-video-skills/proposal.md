## Why

The second technology film (P39, executions 4–5) showed a route that works: real footage found online and registered with rights, code-built motion graphics, and an AE/Resolve edit at normal loudness. The decisions that made it work currently live only in the executing model's session. The user wants them kept as reusable Skills, so other runs and cheaper models can repeat them: script and material shaping each other, knowing when and where to look for material, a fixed motion-design toolkit, and bundled edit combos.

## What Changes

- New built-in versions `studio.video.script@3` and `studio.video.shot-director@3` (v1/v2 unchanged): write and plan against the project material catalog. Check available material while drafting, and when a beat has none, either rewrite the beat to fit what exists or keep it and state a structured material request with acceptable sources (user upload, online free/licensed material, library, platform image generation, website video handoff, code motion graphics). Plans place several exact sources per shot with pacing and crop notes.
- New executor Skill `video-material-scout`: when to search (beat lacks evidence or visual, plan has a gap, review asks for real proof); search order (project library → platform search → primary sources such as project repo, docs, homepage and the author's posts → free/licensed libraries → platform generation → human upload/website handoff → code motion); verification (contact sheets with timecodes, layout stability inside cut ranges, crop-out zones); rights recording and platform registration; returning to the script when nothing fits.
- `video-production-handoff` gains reference cards: a motion-design toolkit (vertical layout grid, footage card with shadow and push-in, headline with accent bar, annotation chips, burned captions, credits and end card, graphic-only beats over blurred same-source footage, timing rules), named edit combos (components, when to use, timing), finishing rules (mastered narration, −14 LUFS mix target, peak ≤ −1 dBTP, punctuation-only caption breaks), and a parameterized AE builder script that turns a cut list and layout spec into native compositions.
- New Capability Memory revisions for the persona edit-stage methods (picture pacing, captions, AE packaging, finish) summarizing the same rules, saved as candidates. Making them the Persona default stays an explicit user adoption.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `studio-creative-skill-pack`: material-aware video script and shot-plan built-in versions.
- `web-video-production-handoff`: executor guidance includes material scouting, the motion toolkit, edit combos and finishing rules.

## Impact

- `apps/api/app/studio_skills/studio.video.script/v3`, `studio.video.shot-director/v3`, catalog registration and trial keys in `studio_creative_catalog.py`.
- `.codex/skills/video-material-scout/` (new), `.codex/skills/video-production-handoff/` references and builder script.
- Capability Memory revisions via the existing API (no code change).
- No change to rights rules, stage contracts, persona defaults or the product six steps.
