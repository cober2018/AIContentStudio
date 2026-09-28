## Why

FE-F3A completed ContentProject as the persistent control plane, but content identity is still represented only by a minimal `ContentPersona(name, owner_user_id)` plus Persona × Modality workflow defaults. The product contract and North Star require identity to answer who is speaking, on whose behalf, for whom, how, with which long-term viewpoints and boundaries, and which default production behavior applies.

Without a durable identity hierarchy and immutable identity snapshots, later changes to brand/persona settings could silently change the interpretation of historical content. The current code also has no first-class Account or Series/Column entity, no deterministic inheritance, and no way for a WorkflowRun to prove which identity definition it used.

FE-F3B therefore turns Content Identity into a stable, versioned business domain while preserving the existing ContentPersona IDs, PersonaWorkflowDefault behavior, BrandVoiceVersion assets, ContentUnit history, WorkflowRun history, and legacy Topic/BrandVoice paths.

## What Changes

- Add a versioned Brand → Persona → Account → Series hierarchy. Existing `ContentPersona` remains the Persona entity and is extended rather than replaced.
- Add append-only revisions for Brand, Persona, Account, and Series. Revision payloads are server-validated identity override profiles; current identity state is derived from immutable revisions instead of mutating historical profile rows.
- Define deterministic inheritance: missing field inherits; explicit value overrides; explicit null clears; arrays/objects replace instead of implicit deep merge.
- Reuse the existing `BrandVoiceVersion` as the voice/version primitive. Identity revisions may reference it; no parallel PersonaVoice/BrandTone system is introduced.
- Add immutable `IdentitySnapshot` that freezes resolved Brand/Persona/Account/Series revision references, resolved BrandVoiceVersion, effective profile JSON, field origins, and checksum.
- Extend `ContentUnit` with optional Account/Series/IdentitySnapshot references and extend `WorkflowRun` with the exact IdentitySnapshot used at run creation.
- Preserve historical honesty: legacy ContentUnits/Runs remain with `identity_snapshot_id = null` and are rendered as legacy/unknown. FE-F3B MUST NOT backfill today's identity settings into historical content.
- Extend workflow preference inheritance with Account × Modality and Series × Modality defaults, resolving `Series > Account > Persona`. Reuse FE-F2 immutable Workflow versioning and portability checks.
- Reuse FE-F2/F3A safe unit lifecycle: before execution history, explicit identity rebind may update a unit in place; after Run/DataSnapshot/project-output history exists, rebind creates a replacement unit and archives the old unit.
- Replace `/identities` placeholder with a persistent Identity Workspace showing hierarchy, current revision, revision history, inherited/overridden fields, Brand Voice, workflow preferences, archive state, and truthful Content Memory boundary.
- Integrate IdentitySnapshot into Production Workspace, FE-F3A Versions, FE-F3A Overview identity-readiness, and validated CreativeBrief identity scope.
- Keep Content Identity separate from Content Memory. FE-F3B does not implement automatic Performance → LearningCandidate → Memory/Strategy mutation.

## Capabilities

### New Capabilities

- `fe-f3b-content-identity`: Versioned Brand/Persona/Account/Series identity hierarchy, deterministic inheritance, immutable IdentitySnapshot, scoped workflow preferences, persistent Identity Workspace, and production/project integration.

### Modified Capabilities

- `fe-f0-f1-project-experience`: `/identities` becomes a real primary workspace and Content Matrix identity selection supports Account/Series-aware binding.
- `fe-f2-persistent-production-workflow`: ContentUnit/WorkflowRun pin immutable IdentitySnapshot; workflow-default resolution adds Account/Series scopes while preserving Persona defaults and run immutability.
- `fe-f3a-content-project-core`: Versions/Overview/CreativeBrief identity scope consume real IdentitySnapshot and identity readiness without fabricating legacy snapshots.

## Impact

- Backend: `apps/api/app/models.py`, additive Alembic migration after `f3a000000001`, new identity services/router(s), extensions to project/unit creation and workflow-run startup, workflow-default authorization/resolution, project Versions/Overview, and targeted event/audit integration.
- Frontend: replace `/identities` placeholder; add identity tree/detail/editor/revision/workflow-preference views; extend ContentUnit selection/rebind and Production Workspace identity context/snapshot inspector.
- Data: add Brand/Account/Series entities, append-only revision tables, IdentitySnapshot, Account/Series workflow default bindings, and nullable identity references on ContentUnit/WorkflowRun. Existing ContentPersona IDs and PersonaWorkflowDefault rows remain valid.
- No production migration/deploy, no new external connectors, no Review Center redesign, no full learning loop, and no automatic identity mutation from performance data.
