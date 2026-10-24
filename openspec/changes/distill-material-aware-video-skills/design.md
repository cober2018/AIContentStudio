## Context

Evidence: `../improve-persona-content-methods/findings.md` (2026-10-21) and `../improve-video-edit-real-footage-handoff/` (catalog for persona video stages, multi-source manifests, cloned inputs, loudness step). Stage models cannot browse the web, so searching is executor work; stage models plan against the catalog and emit requests.

## Decisions

1. **Split by who acts.** Built-in stage Skills (model in the platform) get the planning logic and the request vocabulary. The executor Skill (Codex/Claude with tools) gets searching, fetching, verifying, registering and building. Capability Memory holds the persona-specific edit preferences. No file duplicates another's text; each links to the others.
2. **Script ↔ material loop (stage side).** Draft beats → check the catalog → for each beat choose: use catalog material, rewrite the beat to fit available material, or keep it with a structured request (slot, purpose, acceptable sources, what would prove the claim). A shot may combine several catalog sources with in/out intent and crop notes. Pacing defaults: hook first 3 s, demonstration by the second beat, 2–5 s shots, no single still longer than about 5 s.
3. **Scout order (executor side).** Library → platform search → primary sources → free/licensed libraries → platform generation → human upload/website handoff → code motion graphics (material only). Every fetched item is registered through the platform with source URL, attribution, rights and hash before use; local-only authorization stays local-only.
4. **Toolkit as parameters, not a single style.** Layout tokens (1080×1920 grid, card zone, headline zone, caption zone, credit line), components and timing are documented. The AE builder takes a spec (cuts, crops, headlines, chips, captions) so a new film changes data, not code.
5. **Combos.** Each combo lists components, trigger, timing and a failure check, for example: proof cut (claim line → real footage within 1 s, card push-in + credit); concept beat (keywords pop on blurred same-source footage); annotated demo (footage card + chips at cue times); limits beat (evidence crop + stacked limit chips); closing question (scrim + question + credits + fade).
6. **Adoption.** v3 Skills are trial methods like v2; Capability Memory revisions are candidates. Neither changes Persona defaults without explicit user adoption.

## Risks / Trade-offs

- Over-fitting to one film → cards state when not to use each component; values are defaults, not gates.
- Source-site terms change (for example YouTube sign-in) → the scout records failures and moves to the next source instead of bypassing protections.
