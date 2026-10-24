## Why

The second technology-explainer film (P39/U72, execution 4, 2026-10-21) was built from real demo footage. The platform could record that material only by working around it: the edit manifest accepts one source per shot, inputs are full copies, planning stages cannot see project material, a work-level method setting wiped the edit methods, and the final mix could not reach normal short-video loudness without clipping. These gaps block the next films from being made the same way inside the platform.

## What Changes

- An edit-manifest shot may map to several exact source cuts, each with its own MaterialRevision, source in/out and composition role, validated against the Master timeline instead of only the shot's single `source_material_revision_id`.
- Edit execution inputs are provided as read-only links to the content-addressed material store, named with their real media extension, instead of full private copies. Hash verification and the existing transfer bounds remain; a copy is used only when linking is impossible and the reason is recorded.
- Video script and shot-plan stages receive the project's referenced material catalog (including local-only restricted material marked as such) so plans can cite exact MaterialRevisions; references outside the catalog stay rejected.
- A work-level production-stage setting overrides only the stages it names; unnamed stages keep the Persona selections instead of becoming empty.
- The audio chain can produce a loudness-mastered narration derivative (integrated target and true-peak ceiling), and edit outputs report measured integrated loudness and true peak so a clipping or too-quiet mix is visible before human review.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-video-production-handoff`: multi-source shots in the edit manifest; linked execution inputs; loudness/true-peak measurement on edit outputs.
- `creation-recipe-stage-control-loop`: video planning stages see the project material catalog.
- `persona-creative-configuration`: work-level production stages override per stage.
- `material-library-v1`: loudness-mastered narration as a derived MaterialRevision.

## Impact

- `apps/api/app/services/web_video_handoff.py` (`validate_edit_manifest`), creative execution input materialization (`creative_executions.py`, media storage helpers), creation recipe context assembly (`creation_recipes.py`), `creative_configuration.frozen_stage` work-stage merge, audio chain (TTS/QC services) for the mastered derivative.
- Existing executions and manifests keep validating: `.bin` input paths and single-source manifests remain accepted.
- No change to rights rules, Master schema, publication gates or the Resolve/AE ownership split.
