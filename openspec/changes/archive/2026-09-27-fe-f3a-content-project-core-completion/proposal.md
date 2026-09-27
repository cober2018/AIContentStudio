## Why

FE-F2 made `ContentProject` / `ContentUnit` / project-scoped Workflow execution real and persistent, but the project workspace is still only partially real: `overview`, `matrix`, and workflow-produced project assets use backend state while `brief`, `evidence`, `versions`, and `activity` are placeholders. This leaves the project acting mainly as a shell around Workflow execution instead of the product-level control plane defined by Frontend Product Contract V1.

The repository already has mature reusable resources for evidence, immutable material bytes, workflows, runs, checks, and candidates. FE-F3A should complete the project core by binding and aggregating those resources instead of inventing parallel Source, Evidence, Asset, or ProjectVersion stores.

## What Changes

- Add immutable `CreativeBriefRevision` records under a ContentProject. Saving a brief creates a new revision with optimistic revision protection; older revisions remain readable. The current brief is the highest committed revision. `ContentProject.objective` remains a compatibility/list-summary field and is not a second authoritative brief store.
- Add project-to-source bindings that reference existing `SourceDocument` rows. Project users can attach/detach existing Sources and can create text/URL/upload Sources through the existing Source APIs, then attach them to the project. No Source bytes/text are copied.
- Add immutable `ProjectFactBoundaryRevision` records that point to existing frozen `FactPack` versions. A project fact boundary never copies FactPack items. Changing the boundary creates a new project boundary revision. Editing evidence requires cloning the frozen FactPack, editing the clone through existing FactPack APIs, freezing it, then binding it as a new project boundary revision.
- Add explicit project references to existing `MaterialRevision` rows for project uploads and system-library references. The project Shared Assets read model becomes the union of explicit project material references plus FE-F2 `ProjectWorkflowOutput` media associations. No material bytes are duplicated.
- Add append-only `ProjectEvent` rows for the project activity timeline. Events use stable event codes and structured payloads; mutable display text is derived in the API/UI. Existing `AuditLog` remains the security/operations log and is not repurposed as the sole product activity source.
- Preserve that history when a project is deleted: change project deletion to an idempotent archive transition and keep archived projects readable but not mutable through new or legacy project-bound APIs.
- Add project versions and overview read models. Versions aggregate real Brief, Fact Boundary, ContentUnit, Workflow, Run, MaterialRevision, Draft/Candidate and related versioned resources without introducing a monolithic `ProjectVersion` table. Overview derives stage/readiness/risks/next action from persisted state.
- Replace the remaining persistent-project placeholder panels so all seven ContentProject tabs (`overview / brief / evidence / assets / matrix / versions / activity`) use real backend data after reload.
- Preserve all FE-F2 run ownership, archived-unit, pinned-workflow, stale, side-effect and historical-read invariants.

## Capabilities

### New Capabilities

- `fe-f3a-content-project-core`: persistent CreativeBrief revisions, project Source bindings, immutable project Fact Boundary revisions, explicit project MaterialRevision references, project activity, versions aggregation, and derived overview.

### Modified Capabilities

- `fe-f0-f1-project-experience`: all seven real ContentProject tabs become backed by persisted project state instead of placeholder panels.
- `fe-f2-persistent-production-workflow`: Project Shared Assets become a unified project read model combining explicit project material references with workflow-produced material revisions while preserving FE-F2 provenance and byte integrity.

## Impact

- Backend models/migration: `apps/api/app/models.py` and one additive Alembic revision whose `down_revision` is `e5fef2000001`.
- Backend project API: extend `apps/api/app/routers/content_projects.py`; add focused services under `apps/api/app/services/` for project brief, evidence/boundary, assets, events, versions, and overview instead of growing one router into business-logic storage.
- Existing reusable APIs/services: `routers/sources.py`, `routers/fact_packs.py`, `services/factpack_service.py`, `routers/materials.py`, `services/materials.py`, FE-F2 workflow/run/output services.
- Frontend: refactor `apps/web/src/product/PersistentProjectPages.tsx` into real project-tab components/read models while preserving existing routes and production workspace entry.
- Tests: targeted FE-F3A regressions plus existing full backend/frontend gates.
- No production migration/deployment, no third-party connector implementation, no Review Center expansion, no full Brand → Persona → Account → Series identity system, no Opportunity/Learning implementation, and no channel-publishing expansion in this change.
