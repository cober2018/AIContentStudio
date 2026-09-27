## 0. Spec / branch gate

- [x] 0.1 Create `codex/fe-f3a-project-core-completion` from tracked-clean `734990c`; verify workspace name is AIContentStudio. Preserve the user-provided untracked source package, ZIP and combined document.
- [x] 0.2 Validate this OpenSpec change with strict mode and `git diff --check` before apply; do not modify business code until review authorizes apply.

## 1. Additive project-core persistence

- [x] 1.1 Add one reversible Alembic revision after `e5fef2000001` creating `creative_brief_revision`, `project_source_binding`, `project_fact_boundary_revision`, `project_material_reference`, and `project_event` with the constraints/indexes described in design.
- [x] 1.2 Add corresponding SQLAlchemy models in `apps/api/app/models.py`; do not add duplicate Source/Fact/Material/ProjectVersion tables and do not rewrite existing FE-F2 rows.
- [x] 1.3 Verify migration on an isolated DB: `e5fef2000001 -> new head -> downgrade -> e5fef2000001 -> new head`; existing FE-F2 ContentProject/ContentUnit/WorkflowRun rows remain readable.

## 2. Project event service and instrumentation

- [x] 2.1 Add `apps/api/app/services/project_events.py` with stable event constants and `record_project_event(...)`; payloads contain IDs/checksums/status transitions/small metadata only.
- [x] 2.2 Emit project events transactionally for project create/edit and ContentUnit create/edit/replace/archive/delete paths.
- [x] 2.3 Instrument FE-F2 project flows: project workflow override save, project-origin Persona-default save, DataSnapshot refresh, and newly associated ProjectWorkflowOutput. Idempotent existing output association MUST NOT duplicate an activity event.
- [x] 2.4 Preserve existing AuditLog semantics; do not replace required security/operations AuditLog entries with ProjectEvent.
- [x] 2.5 Keep each ProjectEvent in the same DB transaction as its mutation; make project deletion an idempotent archive transition and reject mutations on archived projects through new and legacy APIs while preserving historical reads.

## 3. Immutable CreativeBrief

- [x] 3.1 Add `apps/api/app/services/project_brief.py` with canonical payload validation/checksum and current/latest revision lookup.
- [x] 3.2 Add project Brief endpoints: current, revision list, revision detail, and append-only save using `expected_revision`; stale save returns 409 with no partial event/revision.
- [x] 3.3 Update project product UX so Brief is the product source of truth for objective; stop editing Brief objective from the generic project modal. Keep `ContentProject.objective` only as compatibility/list fallback.
- [x] 3.4 Add regressions for revision N→N+1, read old revision, reload persistence, same-content behavior, cross-owner denial, and optimistic conflict.
- [x] 3.5 Translate concurrent unique-revision insert conflicts to 409 without partial Brief/event commit; apply the same race-safe behavior to Fact Boundary revisions.

## 4. Project Sources and Fact Boundary

- [x] 4.1 Add `apps/api/app/services/project_evidence.py` for Source binding and current/history Fact Boundary queries.
- [x] 4.2 Add Source attach/list/detach endpoints referencing existing `SourceDocument`; attach-existing is idempotent and detaching does not modify SourceDocument or frozen FactPack snapshots.
- [x] 4.3 Refactor FactPack clone/freeze business rules into shared `factpack_service` functions where necessary so existing global FactPack routes and project boundary actions use one implementation.
- [x] 4.4 Add Fact Boundary current/history/bind endpoints. Binding accepts only frozen FactPack with checksum and creates immutable `ProjectFactBoundaryRevision` with optimistic `expected_revision`.
- [x] 4.5 Add project boundary clone and freeze-and-bind actions. Clone produces a draft FactPack derived from the current boundary; freeze-and-bind verifies lineage, freezes the draft and advances the project boundary atomically.
- [x] 4.6 Add regressions: draft pack cannot bind; old boundary stays readable; detached Source does not mutate boundary; clone/edit/freeze creates new FactPack + new boundary revision; stale boundary update returns 409; cross-owner project access denied.
- [x] 4.7 Reuse the unique Source binding on reattach; enforce the existing global Source access policy before attach/detail reads and avoid duplicate activity events for idempotent attach.

## 5. Unified Project Shared Assets

- [x] 5.1 Add `apps/api/app/services/project_assets.py` to manage `ProjectMaterialReference` and normalize the unified Shared Assets read model.
- [x] 5.2 Add project material-reference attach/detach endpoints; reference existing `MaterialRevision` without copying bytes.
- [x] 5.3 Add project material upload endpoint that reuses `materials_service.create_material/create_revision`, then stores only a `ProjectMaterialReference` in the project transaction.
- [x] 5.4 Modify existing `GET /content-projects/{project_id}/shared-assets` to union active explicit references with FE-F2 verified `ProjectWorkflowOutput(material_revision)` associations. Preserve run/node/attempt provenance for workflow items.
- [x] 5.5 Add regressions for upload, system reference, duplicate/idempotent reference, detach, rights metadata, no byte duplication, same revision appearing through distinct legitimate origins, and workflow-generated media continuing to pass FE-F2 byte/hash verification.
- [x] 5.6 Reuse the unique MaterialRevision reference on reattach; honor existing global material access policy; handle failed DB upload transactions without a committed orphan reference/revision or deleting shared hash-addressed bytes.

## 6. Versions / Activity / Overview read models

- [x] 6.1 Add `apps/api/app/services/project_versions.py`; aggregate Brief, Fact Boundary, active/archived units, relevant Workflow versions, Runs/checksums, MaterialRevision references, and Draft/Candidate project outputs. Do not persist a `ProjectVersion` table.
- [x] 6.2 Add `GET /content-projects/{project_id}/versions` with bounded, typed groups and stable IDs/checksums.
- [x] 6.3 Add `GET /content-projects/{project_id}/activity` with `before_id` cursor and bounded `limit`; renderable payload is stable independent of frontend wording.
- [x] 6.4 Add `apps/api/app/services/project_overview.py` with deterministic stage/readiness/risk/pending-decision/next-action rules.
- [x] 6.5 Add `GET /content-projects/{project_id}/overview`; frontend MUST consume it instead of implementing a separate stage engine.
- [x] 6.6 Add regressions for stage precedence, modality/persona counts, blocked/stale/unknown/waiting-human distinctions, archived-unit exclusion from active counts, version aggregation retaining history, event pagination/order, and cross-owner denial.

## 7. Frontend seven-tab completion

- [x] 7.1 Split the persisted project UI into focused project-tab components/types/API helpers under `apps/web/src/product/project/` (or equivalent repo-convention structure); avoid placing all FE-F3A logic in one growing `PersistentProjectPages.tsx`.
- [x] 7.2 Implement real Overview tab from backend `/overview`: stage, modality distribution, personas, readiness, risks, pending decisions, next action.
- [x] 7.3 Implement Brief tab: current revision, full editable Brief form, dirty state, explicit save, optimistic conflict/reload, read-only revision history.
- [x] 7.4 Implement Evidence tab with distinct Source / Evidence / Fact Boundary sections; attach existing source, create-source-then-attach flows, inspect facts, bind frozen pack, clone boundary, edit draft via existing FactPack UI/API, freeze-and-bind.
- [x] 7.5 Implement Assets tab and shared-assets drawer against unified asset API with badges for project upload / system reference / workflow, rights/provenance, upload/reference/detach actions.
- [x] 7.6 Preserve and extract existing Matrix behavior; active/archived ContentUnit semantics and Production links remain unchanged.
- [x] 7.7 Implement Versions tab grouped by real resource type. Do not fabricate IdentitySnapshot or other not-yet-implemented versions.
- [x] 7.8 Implement Activity tab with reverse chronological events and cursor pagination.
- [x] 7.9 Remove the persistent-project “尚未接入持久化” treatment for Brief/Evidence/Versions/Activity. Empty persisted states use truthful empty-state copy instead.

## 8. Compatibility / safety regression

- [x] 8.1 Re-run FE-F2 targeted regressions for project ownership, pinned workflow, archived-run read-only semantics, rerun/stale, DataSnapshot, project outputs, and side-effect safety.
- [x] 8.2 Verify historical WorkflowRun definition/checksum and attempts are unchanged after newer Brief, boundary, Sources, or asset references are created.
- [x] 8.3 Verify existing Source, FactPack and Materials pages/routes still work and no project action mutates their immutable historical rows unexpectedly.
- [x] 8.4 Verify browser-only `/projects/demo` remains explicitly separate and is not auto-imported into FE-F3A backend state.
- [x] 8.5 Verify project archive/delete is idempotent; historical Brief, boundary, events and Runs remain readable; all project-scoped mutations, including legacy raw-run endpoints, fail closed after archive.

## 9. Final verification / handoff

- [x] 9.1 Run FE-F3A targeted backend tests and the full available backend suite; record actual counts and any environment-specific failures rather than masking them.
- [x] 9.2 Run frontend build/typecheck available in the repo; keep the existing >500 kB bundle warning as a non-blocking performance debt unless FE-F3A materially regresses it.
- [x] 9.3 Run OpenSpec strict validation for all affected specs and `git diff --check`.
- [x] 9.4 Perform local isolated-DB/browser acceptance: create project → save Brief revisions → attach Source → bind/clone/freeze Fact Boundary → upload/reference material → verify unified assets → inspect Versions/Activity/Overview → reload each of seven tabs.
- [x] 9.5 Update README/progress/findings/task plan with actual implemented scope and known non-goals. Do not claim FE-F3B Identity, FE-F4 Review, FE-F5 Opportunity/Learning, real external connectors, or production deployment.
- [x] 9.6 External review must pass before OpenSpec archive/commit. Do not push, merge, deploy, or execute production migrations without separate authorization.
