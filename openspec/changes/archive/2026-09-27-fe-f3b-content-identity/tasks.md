## 0. Change setup and guardrails

- [x] 0.1 Create `codex/fe-f3b-content-identity` from `1fa4520`; preserve the user source directory and other untracked artifacts in the primary checkout, excluding them from FE-F3B commits.
- [x] 0.2 Create this OpenSpec change only; run strict validation and `git diff --check` before apply.
- [x] 0.3 Record baseline backend test count, frontend build status, current Alembic head `f3a000000001`, and no-production-migration constraint.

## 1. Persistence and migration

- [x] 1.1 Add `ContentBrand`, `ContentBrandRevision`, `ContentPersonaRevision`, `ContentAccount`, `ContentAccountRevision`, `ContentSeries`, `ContentSeriesRevision`, `IdentitySnapshot`, `AccountWorkflowDefault`, and `SeriesWorkflowDefault`.
- [x] 1.2 Extend `ContentPersona` with nullable `brand_id` and lifecycle status without changing existing Persona IDs.
- [x] 1.3 Extend `ContentUnit` with nullable `account_id`, `series_id`, `identity_snapshot_id`; extend `WorkflowRun` with nullable `identity_snapshot_id`.
- [x] 1.4 Add indexes/uniqueness constraints for hierarchy revisions and scoped workflow defaults.
- [x] 1.5 Create an additive reversible migration after `f3a000000001`; do not create Brand rows or IdentitySnapshots for legacy data.
- [x] 1.6 Validate isolated SQLite upgrade/downgrade/upgrade with representative FE-F2/F3A project/unit/run history preserved; use PostgreSQL-compatible DDL patterns.

## 2. Identity profile and hierarchy service

- [x] 2.1 Add typed server validation for the canonical identity override profile and reject unknown keys.
- [x] 2.2 Implement missing=inherited, explicit-null=clear, array/object=replace semantics.
- [x] 2.3 Implement Brand → Persona → Account → Series effective resolution and `field_origins`.
- [x] 2.4 Validate hierarchy ownership and parent-child relationships from persisted state; do not trust request IDs.
- [x] 2.5 Reuse `BrandVoiceVersion`; validate resolved references and avoid a second voice model.
- [x] 2.6 Implement append-only revision saves with `expected_revision`, database race handling and HTTP 409.
- [x] 2.7 Implement archive-safe mutation rules for Brand/Persona/Account/Series.

## 3. IdentitySnapshot and production pinning

- [x] 3.1 Implement canonical snapshot checksum over revision references, BrandVoice reference, effective profile and field origins.
- [x] 3.2 Create immutable IdentitySnapshot for new/explicitly rebound ContentUnits.
- [x] 3.3 Extend ContentUnit serialization with account/series/snapshot identity context without exposing unauthorized hierarchy data.
- [x] 3.4 Copy exact unit `identity_snapshot_id` into WorkflowRun at start.
- [x] 3.5 Preserve legacy null snapshot behavior and expose explicit `legacy_identity` state.
- [x] 3.6 Verify later identity revisions cannot mutate old Unit/Run snapshots.

## 4. Safe ContentUnit identity lifecycle

- [x] 4.1 Extend unit create/edit inputs for Account/Series-aware identity selection.
- [x] 4.2 Before execution history, explicit identity rebind updates in place with new snapshot and effective workflow.
- [x] 4.3 After Run/DataSnapshot/ProjectWorkflowOutput history, identity rebind creates replacement unit and archives old unit.
- [x] 4.4 Preserve old unit snapshot, workflow pin and Run history on replacement.
- [x] 4.5 Reject archived identity/unit mutation while keeping historical reads available.

## 5. Hierarchical workflow preferences

- [x] 5.1 Add effective default resolver `Series > Account > Persona`.
- [x] 5.2 Add Account × Modality default read/save with immutable Workflow versions and optimistic binding revision.
- [x] 5.3 Add Series × Modality default read/save with the same semantics.
- [x] 5.4 Reuse FE-F2 workflow definition validation and portability gate; do not fork those validators.
- [x] 5.5 Ensure new scoped defaults never silently rebind existing units/runs.
- [x] 5.6 Apply hierarchy authorization to raw workflow/default entry points.

## 6. Identity APIs

- [x] 6.1 Add Brand CRUD/archive and revision endpoints.
- [x] 6.2 Extend Persona detail/archive/revision APIs while preserving compatibility list/create routes.
- [x] 6.3 Add Account CRUD/archive and revision endpoints.
- [x] 6.4 Add Series CRUD/archive and revision endpoints.
- [x] 6.5 Add effective identity read endpoint returning effective profile, field origins and revision references.
- [x] 6.6 Add authorized IdentitySnapshot read endpoint.
- [x] 6.7 Return truthful archived/legacy/readiness metadata.

## 7. FE-F3A integration

- [x] 7.1 Extend project Versions to include real IdentitySnapshots and truthful legacy identity state.
- [x] 7.2 Extend project Overview with deterministic identity-readiness risk and next action.
- [x] 7.3 Validate typed CreativeBrief identity-scope references on new Brief revisions without modifying historical Briefs.
- [x] 7.4 Include snapshot changes in project unit lifecycle event payload where relevant; do not create duplicate display-text event systems.

## 8. Identity Workspace frontend

- [x] 8.1 Replace `/identities` placeholder with persistent workspace route/page.
- [x] 8.2 Implement Brand → Persona → Account → Series tree with loading/error/empty/archive states.
- [x] 8.3 Implement Identity tab with positioning/audience/domains and revision history.
- [x] 8.4 Implement Expression & Visual tab with BrandVoice reference, expression style and visual language.
- [x] 8.5 Implement Views & Boundaries tab for long-term views, value propositions, content/risk/public-fact boundaries.
- [x] 8.6 Implement Accounts & Series tab with creation/archive and hierarchy relationships.
- [x] 8.7 Implement Workflow Preferences tab for Persona/Account/Series × modality defaults, showing resolved source scope.
- [x] 8.8 Implement truthful Content Memory tab boundary without learned-strategy fabrication.
- [x] 8.9 Clearly label inherited/overridden/cleared effective fields and origin scope.
- [x] 8.10 Support revision save conflicts/reload; do not silently overwrite newer identity revision.

## 9. Project/Production frontend integration

- [x] 9.1 Extend Content Matrix create/edit/rebind UI for optional Account/Series and explicit identity refresh/rebind.
- [x] 9.2 Show resolved workflow preference source before pinning a unit.
- [x] 9.3 Production Context Header displays Brand/Persona/Account/Series and identity snapshot state.
- [x] 9.4 Add read-only `本内容使用的身份快照` inspector.
- [x] 9.5 Run mode uses frozen snapshot; current identity changes require explicit rebind.
- [x] 9.6 Legacy unit/run visibly shows `Legacy / 未冻结身份`.

## 10. Targeted regression tests

- [x] 10.1 Hierarchy ownership, cross-owner denial and parent-child validation.
- [x] 10.2 Append-only revisions, stale expected revision and DB race conflict.
- [x] 10.3 Inheritance missing/null/replace semantics and field origins.
- [x] 10.4 BrandVoice inheritance/override.
- [x] 10.5 Snapshot immutability/checksum.
- [x] 10.6 Legacy no-fake-snapshot behavior.
- [x] 10.7 New unit/run exact snapshot pinning.
- [x] 10.8 Pre-history rebind in place and post-history replacement/archive.
- [x] 10.9 Series > Account > Persona workflow resolution.
- [x] 10.10 Scoped default portability and no silent rebind.
- [x] 10.11 Archived identity read-only behavior.
- [x] 10.12 Project Versions/Overview/Brief integration.
- [x] 10.13 Existing FE-F2 and FE-F3A regression suites remain green.

## 11. Local acceptance and handoff

- [x] 11.1 Run backend full suite and relevant targeted tests.
- [x] 11.2 Run frontend TypeScript/Vite build.
- [x] 11.3 Run OpenSpec strict validation and `git diff --check`.
- [x] 11.4 In isolated local DB/browser, create Brand→Persona→Account→Series, revisions, defaults and ContentUnit; verify reload.
- [x] 11.5 Verify old snapshot survives new identity revision.
- [x] 11.6 Verify legacy unit remains legacy until explicit rebind.
- [x] 11.7 Verify pre/post-history rebind behaviors.
- [x] 11.8 Independent review before archive; do not archive/commit/push until review passes.
