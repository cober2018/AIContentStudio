# AIContentStudio FE-F3A — ContentProject Core Completion OpenSpec（代码级）

> OpenSpec change name: `fe-f3a-content-project-core-completion`  
> Suggested branch: `codex/fe-f3a-project-core-completion`  
> Baseline: clean AIContentStudio commit `734990c`  
> Scope: ContentProject Core Completion only  
> Status: SPEC DRAFT / DO NOT APPLY UNTIL REVIEWED  
> Date: 2026-09-27

---

# 1. proposal.md

## Why

FE-F2 made `ContentProject` / `ContentUnit` / project-scoped Workflow execution real and persistent, but the project workspace is still only partially real: `overview`, `matrix`, and workflow-produced project assets use backend state while `brief`, `evidence`, `versions`, and `activity` are placeholders. This leaves the project acting mainly as a shell around Workflow execution instead of the product-level control plane defined by Frontend Product Contract V1.

The repository already has mature reusable resources for evidence, immutable material bytes, workflows, runs, checks, and candidates. FE-F3A should complete the project core by binding and aggregating those resources instead of inventing parallel Source, Evidence, Asset, or ProjectVersion stores.

## What Changes

- Add immutable `CreativeBriefRevision` records under a ContentProject. Saving a brief creates a new revision with optimistic revision protection; older revisions remain readable. The current brief is the highest committed revision. `ContentProject.objective` remains a compatibility/list-summary field and is not a second authoritative brief store.
- Add project-to-source bindings that reference existing `SourceDocument` rows. Project users can attach/detach existing Sources and can create text/URL/upload Sources through the existing Source APIs, then attach them to the project. No Source bytes/text are copied.
- Add immutable `ProjectFactBoundaryRevision` records that point to existing frozen `FactPack` versions. A project fact boundary never copies FactPack items. Changing the boundary creates a new project boundary revision. Editing evidence requires cloning the frozen FactPack, editing the clone through existing FactPack APIs, freezing it, then binding it as a new project boundary revision.
- Add explicit project references to existing `MaterialRevision` rows for project uploads and system-library references. The project Shared Assets read model becomes the union of explicit project material references plus FE-F2 `ProjectWorkflowOutput` media associations. No material bytes are duplicated.
- Add append-only `ProjectEvent` rows for the project activity timeline. Events use stable event codes and structured payloads; mutable display text is derived in the API/UI. Existing `AuditLog` remains the security/operations log and is not repurposed as the sole product activity source.
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

---

# 2. design.md

## Context

Current clean implementation baseline is AIContentStudio commit `734990c` after FE-F2/R1. FE-F2 introduced real `ContentProject`, `ContentUnit`, minimal `ContentPersona`, project Workflow bindings, project Runs, DataSnapshots, project workflow outputs and a persistent Production Designer. The project page still renders placeholders for Brief, Evidence, Versions and Activity.

The existing repository already contains:

- `SourceDocument` and Source text/URL/upload flows.
- `Fact`, immutable/frozen `FactPack` versions, typed `FactPackItem` evidence snapshots, clone/freeze behavior.
- `Material` / immutable `MaterialRevision`, upload/generate/search and rights metadata.
- `Workflow`, immutable Workflow versions, `WorkflowRun`, `WorkflowStep`, `WorkflowStepAttempt`.
- `ProjectWorkflowOutput` associating verified Draft/Candidate/MaterialRevision outputs to project/unit/run/node/attempt.
- `AuditLog`, which is useful for security/operations evidence but is not a project product-timeline contract.
- Legacy `TopicBrief` / `MotherRevision`, which remain Topic-oriented and must not silently become the new ContentProject brief/master model.

FE-F3A completes the project control plane without replacing these mature resources.

## Goals / Non-Goals

**Goals**

1. Make all seven ContentProject tabs persistent and useful after reload.
2. Make CreativeBrief append-only/versioned.
3. Let a project organize Sources and an immutable Fact Boundary by reference.
4. Unify manual/system/workflow materials in one Project Shared Assets read model without byte duplication.
5. Provide real project Versions and Activity views.
6. Derive Overview status/risks/next action deterministically from real state.
7. Preserve FE-F2 historical workflow/run invariants and archived-unit semantics.

**Non-Goals**

- Full Content Identity hierarchy or identity memory.
- A new Source/Evidence database.
- A new material/blob store.
- A generic `ProjectVersion` blob/table.
- Replacing legacy Topic/MotherRevision APIs in this slice.
- New external Data Source connectors.
- Review/Distribution product rebuild.
- Opportunity, performance learning, or strategy memory.
- Video timeline/render pipeline.
- Production deployment or production DB migration.

## Decisions

### 1. Add only five project-core persistence resources

Add these resources:

```text
CreativeBriefRevision
ProjectSourceBinding
ProjectFactBoundaryRevision
ProjectMaterialReference
ProjectEvent
```

Do **not** add:

```text
ProjectEvidence
ProjectFact
ProjectAssetBytes
ProjectVersion
ProjectWorkflowCopy
```

The first set captures project-local business state; the second set would duplicate existing global/versioned resources.

### 2. CreativeBrief is immutable by revision

Proposed SQLAlchemy shape:

```python
class CreativeBriefRevision(Base):
    __tablename__ = "creative_brief_revision"
    __table_args__ = (
        UniqueConstraint("project_id", "revision_no", name="uq_creative_brief_project_revision"),
        Index("ix_creative_brief_project_created", "project_id", "created_at"),
    )

    id: int PK
    project_id: FK content_project.id NOT NULL
    revision_no: int NOT NULL
    parent_revision_id: FK creative_brief_revision.id NULL

    objective: Text NOT NULL
    primary_audience: Text NULL
    core_message: Text NULL
    angle: Text NULL

    required_evidence_json: JSON list
    content_constraints_json: JSON list
    identity_scope_json: JSON list
    modality_scope_json: JSON list
    channel_scope_json: JSON list
    cta: Text NULL
    references_json: JSON list

    checksum: String(64) NOT NULL
    created_by: String(255) NULL
    created_at: DateTime NOT NULL
```

The highest committed `revision_no` is the current brief. No update endpoint mutates a prior revision.

Save request:

```json
{
  "expected_revision": 2,
  "objective": "...",
  "primary_audience": "...",
  "core_message": "...",
  "angle": "...",
  "required_evidence": [],
  "content_constraints": [],
  "identity_scope": [1, 2],
  "modality_scope": ["text", "graphic"],
  "channel_scope": ["wechat", "xiaohongshu"],
  "cta": "...",
  "references": [{"kind": "source", "id": 12}]
}
```

Server behavior:

```text
latest revision == expected_revision
    -> validate payload
    -> canonical checksum
    -> INSERT revision_no + 1
    -> emit brief.revision_created
    -> commit

latest revision != expected_revision
    -> HTTP 409
    -> no new revision/event
```

`ContentProject.objective` remains only a compatibility/list fallback. Product UI reads brief objective when a brief exists. The FE-F3A project edit modal stops treating `ContentProject.objective` as the authoritative Brief editor.

### 3. Project Sources are references, not copies

Proposed model:

```python
class ProjectSourceBinding(Base):
    __tablename__ = "project_source_binding"
    __table_args__ = (
        UniqueConstraint("project_id", "source_document_id", name="uq_project_source"),
        Index("ix_project_source_project_status", "project_id", "status"),
    )

    id: int PK
    project_id: FK content_project.id NOT NULL
    source_document_id: FK source_document.id NOT NULL
    status: "active" | "detached"
    note: Text NULL
    attached_by: String(255) NULL
    attached_at: DateTime NOT NULL
    detached_by: String(255) NULL
    detached_at: DateTime NULL
```

Detaching a Source only changes project membership; it never archives/deletes `SourceDocument` and never mutates an already frozen FactPack.

Frontend may:

1. attach an existing Source;
2. call existing `/sources/text`, `/sources/url`, or `/sources/upload`;
3. attach the returned Source ID to the project.

No new project-specific Source ingestion implementation is required.

### 4. Fact Boundary is an immutable binding to a frozen FactPack

Proposed model:

```python
class ProjectFactBoundaryRevision(Base):
    __tablename__ = "project_fact_boundary_revision"
    __table_args__ = (
        UniqueConstraint("project_id", "revision_no", name="uq_project_fact_boundary_revision"),
        Index("ix_project_fact_boundary_project_created", "project_id", "created_at"),
    )

    id: int PK
    project_id: FK content_project.id NOT NULL
    revision_no: int NOT NULL
    parent_revision_id: FK project_fact_boundary_revision.id NULL
    fact_pack_id: FK fact_pack.id NOT NULL
    fact_pack_version: int NOT NULL
    fact_pack_checksum: String(64) NOT NULL
    created_by: String(255) NULL
    created_at: DateTime NOT NULL
```

Only `FactPack.status == frozen` and a non-empty checksum may become a project boundary revision.

Initial bind:

```text
POST /content-projects/{project_id}/fact-boundary
body: { fact_pack_id, expected_revision }
```

Changing evidence:

```text
current frozen FactPack
    -> project-scoped clone action creates draft FactPack using factpack_service
    -> user edits draft through existing FactPack APIs
    -> project-scoped freeze-and-bind freezes that draft
    -> INSERT new ProjectFactBoundaryRevision
    -> prior boundary remains readable
```

Project-scoped convenience endpoints MUST call shared `factpack_service` operations. Do not call router functions from another router.

Refactor only as needed:

```python
factpack_service.clone_pack(...)
factpack_service.freeze_pack(...)
```

Existing global FactPack endpoints then call the same service methods so clone/freeze rules do not diverge.

A detached project Source does not change a prior frozen boundary. The Evidence UI must explicitly show that distinction.

### 5. Project Shared Assets is a union read model

Add:

```python
class ProjectMaterialReference(Base):
    __tablename__ = "project_material_reference"
    __table_args__ = (
        UniqueConstraint("project_id", "material_revision_id", name="uq_project_material_revision"),
        Index("ix_project_material_project_status", "project_id", "status"),
    )

    id: int PK
    project_id: FK content_project.id NOT NULL
    material_revision_id: FK material_revision.id NOT NULL
    origin: "project_upload" | "system_reference"
    status: "active" | "detached"
    note: Text NULL
    attached_by: String(255) NULL
    attached_at: DateTime NOT NULL
    detached_by: String(255) NULL
    detached_at: DateTime NULL
```

Do not insert workflow-produced media into this table. FE-F2 already stores those associations in `ProjectWorkflowOutput`.

`GET /content-projects/{project_id}/shared-assets` becomes:

```text
active ProjectMaterialReference
UNION
ProjectWorkflowOutput(output_kind == material_revision)
    -> hydrate MaterialRevision / Material
    -> normalize response
```

Normalized item:

```ts
interface ProjectSharedAsset {
  key: string
  sourceType: 'project_upload' | 'system_reference' | 'workflow'
  referenceId: number | null
  projectOutputId: number | null
  materialId: number
  materialRevisionId: number
  revisionNo: number
  kind: string
  title: string
  mimeType: string | null
  contentHash: string
  rightsStatus: string | null
  publicUseAllowed: boolean | null
  modelUseAllowed: boolean | null
  commercialUseAllowed: boolean | null
  attributionText: string | null
  runId: number | null
  unitId: number | null
  nodeId: string | null
  attemptId: number | null
  provenance: object
}
```

Project upload endpoint calls `materials_service.create_material()` + `create_revision()` and then creates `ProjectMaterialReference` in one transaction. Existing material bytes remain content-hash addressed and are not copied.

### 6. Project Activity is a product event stream

Add:

```python
class ProjectEvent(Base):
    __tablename__ = "project_event"
    __table_args__ = (
        Index("ix_project_event_project_id_id", "project_id", "id"),
        Index("ix_project_event_project_created", "project_id", "created_at"),
    )

    id: int PK
    project_id: FK content_project.id NOT NULL
    event_type: String(80) NOT NULL
    entity_type: String(50) NULL
    entity_id: String(80) NULL
    actor: String(255) NULL
    payload_json: JSON NOT NULL
    schema_version: int NOT NULL default 1
    created_at: DateTime NOT NULL
```

Stable event codes include at minimum:

```text
project.created
project.updated
brief.revision_created
source.attached
source.detached
fact_boundary.bound
fact_boundary.draft_cloned
fact_boundary.frozen_bound
unit.created
unit.updated
unit.replaced
unit.archived
workflow.override_saved
workflow.role_default_saved
data.snapshot_created
data.snapshot_changed
asset.attached
asset.detached
asset.workflow_generated
draft.generated
candidate.associated
```

Event payload stores IDs/checksums/status transitions/small metadata only. It MUST NOT store large document bodies, material bytes, secrets, raw provider credentials, or mutable display text as its only meaning.

Add helper:

```python
record_project_event(
    db,
    *,
    project_id: int,
    event_type: str,
    actor: str | None,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    payload: dict | None = None,
) -> ProjectEvent
```

Event insertion occurs in the same DB transaction as the business mutation where practical.

`AuditLog` remains separate. Security-sensitive existing AuditLog writes are not removed.

### 7. Instrument existing FE-F2 mutations

FE-F3A must emit project events from existing code paths rather than only from new routes.

At minimum:

- `create_project`, `patch_project`.
- `create_unit`, `patch_unit`, `delete_unit`.
- `save_workflow_override`.
- `save_persona_default` when invoked with `source_project_id/source_unit_id`.
- `data_source_plugins.snapshot_source`.
- `project_outputs.associate_step_output`.

Avoid duplicate events:

```text
same ProjectWorkflowOutput already exists
    -> return existing
    -> DO NOT emit asset.workflow_generated again
```

For Data Snapshot, query the previous snapshot for the same project unit + node and emit `changed: true|false` with old/new checksum.

### 8. Versions is aggregation, not another persistence store

Add `apps/api/app/services/project_versions.py`.

Proposed response:

```ts
interface ProjectVersionsView {
  brief: VersionItem[]
  factBoundary: VersionItem[]
  contentUnits: VersionItem[]
  workflows: VersionItem[]
  runs: VersionItem[]
  materials: VersionItem[]
  contentOutputs: VersionItem[]
}

interface VersionItem {
  kind: string
  id: string
  version: string | number | null
  status: string | null
  checksum: string | null
  createdAt: string | null
  current: boolean
  unitId?: number
  source?: string
  metadata?: Record<string, unknown>
}
```

Queries aggregate real resources:

- all `CreativeBriefRevision` rows;
- all `ProjectFactBoundaryRevision` rows;
- active + archived `ContentUnit`;
- project override Workflow versions with `workflow_key = project.unit.{unit_id}`;
- pinned Persona-default Workflow versions actually used by units/runs where relevant;
- all project `WorkflowRun` rows and frozen checksum;
- all explicit project MaterialRevision refs and workflow-output MaterialRevision refs;
- project workflow outputs of kind Draft/Candidate.

No `ProjectVersion` table.

### 9. Overview uses deterministic business rules

Add `apps/api/app/services/project_overview.py`.

Response:

```ts
interface ProjectOverview {
  stage:
    | 'brief_needed'
    | 'evidence_needed'
    | 'matrix_needed'
    | 'production'
    | 'attention_required'
    | 'waiting_human'
    | 'review_ready'

  activeUnitCount: number
  archivedUnitCount: number
  modalityCounts: { text: number; graphic: number; video: number }
  personas: { id: number; name: string; unitCount: number }[]

  brief: { ready: boolean; revision: number | null }
  factBoundary: {
    ready: boolean
    revision: number | null
    factPackId: number | null
    factPackVersion: number | null
    checksum: string | null
  }

  risks: ProjectRisk[]
  pendingDecisions: ProjectDecision[]
  nextAction: { code: string; label: string; href: string } | null
}
```

Deterministic stage precedence:

```text
no brief -> brief_needed
brief exists, no frozen fact boundary -> evidence_needed
brief + fact boundary, no active ContentUnit -> matrix_needed
any active unit / latest run / evidence state blocked|stale|unknown -> attention_required
else any waiting_input / waiting_human -> waiting_human
else active units exist and at least one production run is running/pending -> production
else all active units are ready/approved or have reviewable content outputs -> review_ready
else -> production
```

Risks/pending decisions are typed, not free-form AI guesses. Examples: `brief_missing`, `fact_boundary_missing`, `unit_blocked`, `unit_stale`, `unit_unknown`, `run_failed`, `run_waiting_human`, `asset_rights_unknown`.

FE-F3A does not use an LLM to decide stage/readiness.

### 10. API surface

Extend project router or split into project subrouters while keeping public prefix `/api/v1`.

#### Brief

```text
GET  /content-projects/{project_id}/brief
GET  /content-projects/{project_id}/brief/revisions
GET  /content-projects/{project_id}/brief/revisions/{revision_id}
POST /content-projects/{project_id}/brief/revisions
```

#### Sources

```text
GET    /content-projects/{project_id}/sources
POST   /content-projects/{project_id}/sources
DELETE /content-projects/{project_id}/sources/{source_document_id}
```

Attach body:

```json
{ "source_document_id": 123, "note": "Primary launch source" }
```

#### Fact Boundary

```text
GET  /content-projects/{project_id}/fact-boundary
GET  /content-projects/{project_id}/fact-boundary/revisions
POST /content-projects/{project_id}/fact-boundary
POST /content-projects/{project_id}/fact-boundary/clone
POST /content-projects/{project_id}/fact-boundary/{fact_pack_id}/freeze-and-bind
```

Initial bind accepts only frozen FactPack.

#### Project materials

```text
POST   /content-projects/{project_id}/materials/references
DELETE /content-projects/{project_id}/materials/references/{reference_id}
POST   /content-projects/{project_id}/materials/upload
GET    /content-projects/{project_id}/shared-assets
```

#### Versions / Activity / Overview

```text
GET /content-projects/{project_id}/versions
GET /content-projects/{project_id}/activity?before_id=<id>&limit=<1..100>
GET /content-projects/{project_id}/overview
```

### 11. Authorization

Reuse FE-F2 owner boundary:

```python
owned_project(db, project_id, user)
```

Read endpoints: `get_current_user`. Mutations: `require_editor` unless an existing narrower permission applies.

Project Source/Material references do not grant ownership of the global Source/Material. They only state project membership.

Do not weaken existing Source/FactPack/Material permissions.

### 12. Migration

Create one additive, reversible Alembic revision after:

```text
down_revision = "e5fef2000001"
```

New tables only:

```text
creative_brief_revision
project_source_binding
project_fact_boundary_revision
project_material_reference
project_event
```

No destructive rewrite of existing evidence/material/workflow/project tables.

Downgrade drops only FE-F3A tables/indexes/FKs.

Migration verification:

1. fresh database -> head;
2. database at `e5fef2000001` -> new head;
3. new head -> downgrade to `e5fef2000001`;
4. upgrade again;
5. existing FE-F2 project/unit/workflow rows remain readable.

### 13. Frontend structure

Recommended split:

```text
apps/web/src/product/
├── PersistentProjectPages.tsx
├── project/
│   ├── types.ts
│   ├── api.ts
│   ├── ProjectOverviewTab.tsx
│   ├── ProjectBriefTab.tsx
│   ├── ProjectEvidenceTab.tsx
│   ├── ProjectAssetsTab.tsx
│   ├── ProjectMatrixTab.tsx
│   ├── ProjectVersionsTab.tsx
│   ├── ProjectActivityTab.tsx
│   └── ProjectSharedAssetsDrawer.tsx
└── ProductionDesigner.tsx
```

Exact filenames may follow repo conventions, but implementation must avoid one giant component accumulating all project-core logic.

#### Brief tab

- load current + revision list;
- edit full Brief;
- dirty state;
- save with `expected_revision`;
- 409 conflict shows reload action;
- revision history is read-only.

#### Evidence tab

Three visual sections: `Project Sources / Evidence-Facts / Current Fact Boundary`.

Actions: attach existing Source; create text/URL/upload Source using existing APIs then attach; inspect Source facts; choose frozen FactPack as initial boundary; clone boundary to draft; edit draft evidence; freeze-and-bind new boundary.

UI must say clearly that detaching a Source does not rewrite an older frozen boundary.

#### Assets tab/drawer

One unified list with source badges: `项目上传 / 系统素材引用 / 工作流生成`.

Actions: upload new project material; reference existing global MaterialRevision; detach explicit reference; inspect rights/provenance. Workflow-generated association remains read-only here unless existing material policies provide another operation.

#### Versions tab

Grouped real resources. No fake identity snapshots. If IdentitySnapshot is not implemented, show a scoped “not available in FE-F3A” note rather than synthetic data.

#### Activity tab

Reverse chronological project events, cursor/pagination capable. Render human labels from stable `event_type + payload`, not stored display strings.

#### Overview tab

Consume `/overview`; no duplicated status calculation in React.

### 14. Compatibility with existing Topic/MotherRevision

FE-F3A does not automatically map `TopicBrief` to `ContentProject` and does not make `MotherRevision` the project-wide master revision.

If a future import/migration maps a Topic to a project, that is a separate explicit change. Existing Topic routes/pages remain reachable.

### 15. Error/status semantics

Use:

```text
404: project/binding/resource not visible in project scope
409: optimistic conflict or immutable/frozen state conflict
422: structurally invalid payload / wrong resource state for action
```

Preferred duplicate Source/Material attach behavior is idempotent return of the existing active binding/reference, and it must be tested.

Workflow-produced project assets still require FE-F2 verified association; Shared Assets must not infer media from arbitrary Step output.

## Risks / Trade-offs

- [Brief objective duplicates legacy `ContentProject.objective`] → Treat latest CreativeBrief as product truth; use `ContentProject.objective` only as compatibility/list fallback and stop editing it directly in the new project UX.
- [Source detached after being used in a frozen FactPack] → Source membership and Fact Boundary are separate; detached Source does not mutate prior evidence snapshots.
- [FactPack APIs and project boundary wrappers diverge] → Move clone/freeze rules into shared `factpack_service` functions and call them from both route families.
- [Project events become a second audit system] → ProjectEvent is product timeline only; retain AuditLog for security/ops and do not store secrets/large bodies in ProjectEvent.
- [Versions aggregation becomes slow] → Query per bounded resource group with indexes; cap/paginate high-volume Run/Material/Event lists where needed. Do not solve by denormalizing all history into a ProjectVersion blob.
- [Shared Assets duplicates workflow output rows] → Explicit references and workflow outputs remain separate persistence sources; only the API read model unifies them.
- [Existing global Source/FactPack/Material models are not tenant-owned] → Preserve current app authorization semantics; FE-F3A does not claim production multi-tenancy.
- [FE-F3A scope grows into identity/review/learning] → Keep Persona use read-only/minimal except existing FE-F2 bindings; defer full identity hierarchy, review center and learning.

## Migration / Rollout Plan

1. Create `codex/fe-f3a-project-core-completion` from clean `734990c`.
2. Add the additive migration and model rows.
3. Add project event service first, then instrument project/unit mutations.
4. Add Brief service/API and regressions.
5. Add Source binding + Fact Boundary service/API, refactoring FactPack clone/freeze into shared service functions if necessary.
6. Add explicit MaterialReference + unified Shared Assets service/API.
7. Add Versions and Overview derived services.
8. Split/refactor persistent project frontend and replace all four placeholder tabs.
9. Run isolated DB migration up/down/up, targeted tests, full backend suite, frontend build, OpenSpec strict, and `git diff --check`.
10. Do not run production migration/deployment and do not merge/push until review.

## Open Questions

- Full project-level collaboration beyond current owner-user semantics is deferred.
- ContentUnit-level CreativeBrief overrides are defined in the long-term frontend contract but are not required in FE-F3A; this slice establishes project-level immutable Brief revisions first. A later change may add explicit unit override revisions.
- IdentitySnapshot is not implemented in FE-F3A. Versions UI must not invent it.
- Candidate/Approval project-first review remains FE-F4 even though existing ProjectWorkflowOutput references may already expose Draft/Candidate IDs in Versions.

---

# 3. specs/fe-f3a-content-project-core/spec.md

## ADDED Requirements

### Requirement: Immutable CreativeBrief revisions

The system SHALL persist CreativeBrief as append-only revisions owned by one ContentProject. Each committed revision SHALL include objective, primary audience, core message, angle, required evidence, content constraints, identity scope, modality scope, channel scope, CTA, references, checksum, author and creation time. Saving a Brief SHALL create a new revision; a prior revision MUST NOT be mutated.

#### Scenario: Save next Brief revision
- **WHEN** an editor saves a valid Brief with `expected_revision` equal to the current revision
- **THEN** the backend creates revision N+1, returns its checksum, keeps revision N readable, and records `brief.revision_created`

#### Scenario: Reject stale Brief save
- **WHEN** another editor has already created a newer Brief revision
- **THEN** the stale save returns 409 and creates neither a new revision nor a project event

#### Scenario: Reload Brief
- **WHEN** the user reloads the project
- **THEN** the Brief tab shows the latest committed revision and its prior revisions from backend state

### Requirement: Project Sources reference existing SourceDocument records

A ContentProject SHALL organize Sources through project bindings to existing SourceDocument rows. Attaching or detaching a Source MUST NOT copy, rewrite, archive, or delete the SourceDocument.

#### Scenario: Attach an existing Source
- **WHEN** an editor attaches a visible SourceDocument to a project
- **THEN** an active project-source binding is persisted and the Source appears in the Evidence tab after reload

#### Scenario: Create then attach Source
- **WHEN** an editor creates a text, URL, or uploaded Source using the existing Source APIs and then attaches the returned Source ID
- **THEN** the project references that Source without copying its raw text or bytes

#### Scenario: Detach Source used by historical evidence
- **WHEN** an editor detaches a Source that contributed to an older frozen FactPack
- **THEN** the Source disappears from the project's active Source list but the historical FactPack snapshot and project Fact Boundary remain unchanged

### Requirement: Immutable project Fact Boundary revisions

A ContentProject SHALL represent its factual boundary through immutable ProjectFactBoundaryRevision rows that reference existing frozen FactPack versions. Creating a project boundary revision MUST NOT duplicate FactPack items. Only frozen FactPacks with a checksum MAY become a project boundary.

#### Scenario: Bind initial frozen FactPack
- **WHEN** an editor selects a frozen FactPack for a project with no prior Fact Boundary
- **THEN** boundary revision 1 records the FactPack ID, version and checksum

#### Scenario: Refuse mutable boundary
- **WHEN** an editor attempts to bind a draft FactPack as the current boundary
- **THEN** the request is rejected and the prior boundary remains current

#### Scenario: Clone, edit, freeze and advance boundary
- **WHEN** an editor clones the current boundary, edits the draft using existing FactPack operations, and uses the project freeze-and-bind action
- **THEN** the draft is frozen and a new immutable project boundary revision points to that new frozen FactPack while the old revision remains readable

### Requirement: Unified Project Shared Assets by reference

Project Shared Assets SHALL combine explicit project references to existing MaterialRevision rows with FE-F2 verified workflow-produced MaterialRevision associations. The system MUST NOT duplicate underlying material bytes merely to add an item to a project.

#### Scenario: Reference system material
- **WHEN** an editor adds an existing MaterialRevision to a project
- **THEN** an explicit project material reference is stored and the unified Shared Assets response returns its original revision/rights/provenance data

#### Scenario: Upload project material
- **WHEN** an editor uploads a material from the project
- **THEN** the existing material service creates Material + immutable MaterialRevision and the project stores only a reference to that revision

#### Scenario: Workflow material appears in same pool
- **WHEN** FE-F2 records a verified workflow-generated MaterialRevision in ProjectWorkflowOutput
- **THEN** the same project Shared Assets API displays it with source type `workflow` without creating a duplicate project material reference

#### Scenario: Detach explicit reference
- **WHEN** an editor detaches a project-upload/system-reference item
- **THEN** the project reference becomes inactive while the global MaterialRevision and workflow histories remain unchanged

### Requirement: Append-only project activity

The system SHALL maintain an append-only product event stream per ContentProject. Events SHALL use stable event codes, entity references and structured payloads. Large content bodies, material bytes, secrets and mutable display text MUST NOT be the event contract.

#### Scenario: Business mutation records event
- **WHEN** project, Brief, Source, boundary, ContentUnit, Workflow, DataSnapshot or project-asset state changes through an FE-F3A/FE-F2 project flow
- **THEN** the same transaction records the corresponding ProjectEvent unless the underlying operation is idempotently returning an already-recorded association

#### Scenario: Activity survives display copy changes
- **WHEN** frontend wording changes
- **THEN** historical activity is still renderable from stable `event_type` and structured payload fields

#### Scenario: AuditLog remains separate
- **WHEN** an operation already has a security/operations AuditLog requirement
- **THEN** FE-F3A does not remove that AuditLog merely because a ProjectEvent also exists

### Requirement: Aggregated project Versions view

The system SHALL expose a project Versions read model aggregated from actual versioned resources. It MUST NOT introduce a monolithic ProjectVersion persistence table solely for UI presentation.

The view SHALL aggregate, when present: CreativeBrief revisions, ProjectFactBoundary revisions, active/archived ContentUnits, relevant Workflow versions, WorkflowRuns with frozen checksums, project MaterialRevisions, and workflow-associated Draft/Candidate references.

#### Scenario: Historical versions remain visible
- **WHEN** newer Brief, boundary, Workflow or material versions exist
- **THEN** older project-relevant versions remain visible and their IDs/checksums are not rewritten

#### Scenario: Missing IdentitySnapshot
- **WHEN** FE-F3A has no IdentitySnapshot implementation
- **THEN** Versions does not fabricate one and the UI clearly scopes that item to a later identity phase

### Requirement: Derived project Overview

The backend SHALL derive ContentProject overview stage, counts, readiness, risks, pending decisions and next action from persisted state using deterministic rules. The frontend MUST NOT duplicate an independent stage engine.

#### Scenario: Missing Brief
- **WHEN** a project has no CreativeBrief revision
- **THEN** overview stage is `brief_needed` and next action points to the Brief tab

#### Scenario: Missing Fact Boundary
- **WHEN** a project has a Brief but no frozen project Fact Boundary
- **THEN** overview stage is `evidence_needed`

#### Scenario: Attention state
- **WHEN** active units/runs contain blocked, stale, unknown or failed states
- **THEN** overview returns typed risks and an attention-required stage rather than flattening them into a generic failure

#### Scenario: Waiting human
- **WHEN** no higher-priority blocker exists and an active production run is waiting for human input
- **THEN** overview returns `waiting_human` with a typed pending decision

### Requirement: Project-core authorization and historical safety

All FE-F3A project endpoints SHALL reuse persisted ContentProject ownership checks and existing resource permissions. FE-F3A MUST preserve FE-F2 archived-unit, pinned-workflow, frozen-run and side-effect safety semantics.

#### Scenario: Cross-project read
- **WHEN** a user without access to a project requests its Brief, Sources, boundary, assets, Versions, Activity or Overview
- **THEN** the request returns no protected project data

#### Scenario: Historical run after project-core changes
- **WHEN** Brief, Fact Boundary, Sources or assets advance after a historical Run
- **THEN** the Run still reads its frozen Workflow definition and historical attempts exactly as before FE-F3A

---

# 4. specs/fe-f0-f1-project-experience/spec.md

## MODIFIED Requirements

### Requirement: Project workspace

The frontend SHALL present ContentProject as the business root and provide overview, brief, evidence, assets, matrix, versions, and activity tabs with URL-addressable tab state. For persisted projects, all seven tabs SHALL load real backend state; Brief, Evidence, Versions, and Activity MUST NOT remain persistent placeholder panels.

#### Scenario: Open a persisted project tab
- **WHEN** the user opens any of the seven tabs for a backend-persisted ContentProject
- **THEN** the tab loads the corresponding real project data or a truthful empty state from the backend and can be opened directly by URL

#### Scenario: Reload project tab
- **WHEN** the user reloads a project URL on Brief, Evidence, Assets, Matrix, Versions or Activity
- **THEN** saved project state remains visible without depending on browser-only fixture data

### Requirement: Project assets

The frontend SHALL expose Project Shared Assets through a modal or drawer instead of permanently occupying the Production canvas. For persisted projects, the same project asset pool SHALL include explicit project uploads, system MaterialRevision references, and verified workflow-generated material revisions with source/provenance/rights distinctions.

#### Scenario: Open unified shared assets
- **WHEN** the user opens Project Shared Assets from a persisted project or Production Workspace
- **THEN** one dismissible asset browser shows project-upload, system-reference and workflow-generated items from backend state without duplicating the underlying material bytes

---

# 5. specs/fe-f2-persistent-production-workflow/spec.md

## MODIFIED Requirements

### Requirement: Project-shared workflow outputs

The system SHALL persist references to supported workflow-produced Draft, MaterialRevision, and Candidate outputs with owning project, unit, run, node, attempt, and applicable source/rights provenance. Generated image, chart, screenshot, and video-clip revisions SHALL appear in the owning project's Shared Assets. FE-F3A MAY add explicit project MaterialRevision references for project upload/system-library use, but those references SHALL remain a separate persistence source from ProjectWorkflowOutput. The project Shared Assets API SHALL unify both sources at read time and MUST NOT create a synthetic material, duplicate bytes, or infer an asset merely because a node reports success.

#### Scenario: Workflow material and explicit material coexist
- **WHEN** a project has both explicit MaterialRevision references and a verified workflow-generated MaterialRevision
- **THEN** the Shared Assets response includes both with distinct source types and preserves the workflow item's run/node/attempt provenance

#### Scenario: Explicit detach does not erase workflow history
- **WHEN** an editor detaches an explicit project material reference
- **THEN** any separate ProjectWorkflowOutput association to the same MaterialRevision remains intact and historical runs are not modified

---

# 6. tasks.md

## 0. Spec / branch gate

- [ ] 0.1 Create `codex/fe-f3a-project-core-completion` from clean `734990c`; verify workspace name is AIContentStudio and worktree is clean before edits.
- [ ] 0.2 Validate this OpenSpec change with strict mode and `git diff --check` before apply; do not modify business code until review authorizes apply.

## 1. Additive project-core persistence

- [ ] 1.1 Add one reversible Alembic revision after `e5fef2000001` creating `creative_brief_revision`, `project_source_binding`, `project_fact_boundary_revision`, `project_material_reference`, and `project_event` with the constraints/indexes described in design.
- [ ] 1.2 Add corresponding SQLAlchemy models in `apps/api/app/models.py`; do not add duplicate Source/Fact/Material/ProjectVersion tables and do not rewrite existing FE-F2 rows.
- [ ] 1.3 Verify migration on an isolated DB: `e5fef2000001 -> new head -> downgrade -> e5fef2000001 -> new head`; existing FE-F2 ContentProject/ContentUnit/WorkflowRun rows remain readable.

## 2. Project event service and instrumentation

- [ ] 2.1 Add `apps/api/app/services/project_events.py` with stable event constants and `record_project_event(...)`; payloads contain IDs/checksums/status transitions/small metadata only.
- [ ] 2.2 Emit project events transactionally for project create/edit and ContentUnit create/edit/replace/archive/delete paths.
- [ ] 2.3 Instrument FE-F2 project flows: project workflow override save, project-origin Persona-default save, DataSnapshot refresh, and newly associated ProjectWorkflowOutput. Idempotent existing output association MUST NOT duplicate an activity event.
- [ ] 2.4 Preserve existing AuditLog semantics; do not replace required security/operations AuditLog entries with ProjectEvent.

## 3. Immutable CreativeBrief

- [ ] 3.1 Add `apps/api/app/services/project_brief.py` with canonical payload validation/checksum and current/latest revision lookup.
- [ ] 3.2 Add project Brief endpoints: current, revision list, revision detail, and append-only save using `expected_revision`; stale save returns 409 with no partial event/revision.
- [ ] 3.3 Update project product UX so Brief is the product source of truth for objective; stop editing Brief objective from the generic project modal. Keep `ContentProject.objective` only as compatibility/list fallback.
- [ ] 3.4 Add regressions for revision N→N+1, read old revision, reload persistence, same-content behavior, cross-owner denial, and optimistic conflict.

## 4. Project Sources and Fact Boundary

- [ ] 4.1 Add `apps/api/app/services/project_evidence.py` for Source binding and current/history Fact Boundary queries.
- [ ] 4.2 Add Source attach/list/detach endpoints referencing existing `SourceDocument`; attach-existing is idempotent and detaching does not modify SourceDocument or frozen FactPack snapshots.
- [ ] 4.3 Refactor FactPack clone/freeze business rules into shared `factpack_service` functions where necessary so existing global FactPack routes and project boundary actions use one implementation.
- [ ] 4.4 Add Fact Boundary current/history/bind endpoints. Binding accepts only frozen FactPack with checksum and creates immutable `ProjectFactBoundaryRevision` with optimistic `expected_revision`.
- [ ] 4.5 Add project boundary clone and freeze-and-bind actions. Clone produces a draft FactPack derived from the current boundary; freeze-and-bind verifies lineage, freezes the draft and advances the project boundary atomically.
- [ ] 4.6 Add regressions: draft pack cannot bind; old boundary stays readable; detached Source does not mutate boundary; clone/edit/freeze creates new FactPack + new boundary revision; stale boundary update returns 409; cross-owner project access denied.

## 5. Unified Project Shared Assets

- [ ] 5.1 Add `apps/api/app/services/project_assets.py` to manage `ProjectMaterialReference` and normalize the unified Shared Assets read model.
- [ ] 5.2 Add project material-reference attach/detach endpoints; reference existing `MaterialRevision` without copying bytes.
- [ ] 5.3 Add project material upload endpoint that reuses `materials_service.create_material/create_revision`, then stores only a `ProjectMaterialReference` in the project transaction.
- [ ] 5.4 Modify existing `GET /content-projects/{project_id}/shared-assets` to union active explicit references with FE-F2 verified `ProjectWorkflowOutput(material_revision)` associations. Preserve run/node/attempt provenance for workflow items.
- [ ] 5.5 Add regressions for upload, system reference, duplicate/idempotent reference, detach, rights metadata, no byte duplication, same revision appearing through distinct legitimate origins, and workflow-generated media continuing to pass FE-F2 byte/hash verification.

## 6. Versions / Activity / Overview read models

- [ ] 6.1 Add `apps/api/app/services/project_versions.py`; aggregate Brief, Fact Boundary, active/archived units, relevant Workflow versions, Runs/checksums, MaterialRevision references, and Draft/Candidate project outputs. Do not persist a `ProjectVersion` table.
- [ ] 6.2 Add `GET /content-projects/{project_id}/versions` with bounded, typed groups and stable IDs/checksums.
- [ ] 6.3 Add `GET /content-projects/{project_id}/activity` with `before_id` cursor and bounded `limit`; renderable payload is stable independent of frontend wording.
- [ ] 6.4 Add `apps/api/app/services/project_overview.py` with deterministic stage/readiness/risk/pending-decision/next-action rules.
- [ ] 6.5 Add `GET /content-projects/{project_id}/overview`; frontend MUST consume it instead of implementing a separate stage engine.
- [ ] 6.6 Add regressions for stage precedence, modality/persona counts, blocked/stale/unknown/waiting-human distinctions, archived-unit exclusion from active counts, version aggregation retaining history, event pagination/order, and cross-owner denial.

## 7. Frontend seven-tab completion

- [ ] 7.1 Split the persisted project UI into focused project-tab components/types/API helpers under `apps/web/src/product/project/` (or equivalent repo-convention structure); avoid placing all FE-F3A logic in one growing `PersistentProjectPages.tsx`.
- [ ] 7.2 Implement real Overview tab from backend `/overview`: stage, modality distribution, personas, readiness, risks, pending decisions, next action.
- [ ] 7.3 Implement Brief tab: current revision, full editable Brief form, dirty state, explicit save, optimistic conflict/reload, read-only revision history.
- [ ] 7.4 Implement Evidence tab with distinct Source / Evidence / Fact Boundary sections; attach existing source, create-source-then-attach flows, inspect facts, bind frozen pack, clone boundary, edit draft via existing FactPack UI/API, freeze-and-bind.
- [ ] 7.5 Implement Assets tab and shared-assets drawer against unified asset API with badges for project upload / system reference / workflow, rights/provenance, upload/reference/detach actions.
- [ ] 7.6 Preserve and extract existing Matrix behavior; active/archived ContentUnit semantics and Production links remain unchanged.
- [ ] 7.7 Implement Versions tab grouped by real resource type. Do not fabricate IdentitySnapshot or other not-yet-implemented versions.
- [ ] 7.8 Implement Activity tab with reverse chronological events and cursor pagination.
- [ ] 7.9 Remove the persistent-project “尚未接入持久化” treatment for Brief/Evidence/Versions/Activity. Empty persisted states use truthful empty-state copy instead.

## 8. Compatibility / safety regression

- [ ] 8.1 Re-run FE-F2 targeted regressions for project ownership, pinned workflow, archived-run read-only semantics, rerun/stale, DataSnapshot, project outputs, and side-effect safety.
- [ ] 8.2 Verify historical WorkflowRun definition/checksum and attempts are unchanged after newer Brief, boundary, Sources, or asset references are created.
- [ ] 8.3 Verify existing Source, FactPack and Materials pages/routes still work and no project action mutates their immutable historical rows unexpectedly.
- [ ] 8.4 Verify browser-only `/projects/demo` remains explicitly separate and is not auto-imported into FE-F3A backend state.

## 9. Final verification / handoff

- [ ] 9.1 Run FE-F3A targeted backend tests and the full available backend suite; record actual counts and any environment-specific failures rather than masking them.
- [ ] 9.2 Run frontend build/typecheck available in the repo; keep the existing >500 kB bundle warning as a non-blocking performance debt unless FE-F3A materially regresses it.
- [ ] 9.3 Run OpenSpec strict validation for all affected specs and `git diff --check`.
- [ ] 9.4 Perform local isolated-DB/browser acceptance: create project → save Brief revisions → attach Source → bind/clone/freeze Fact Boundary → upload/reference material → verify unified assets → inspect Versions/Activity/Overview → reload each of seven tabs.
- [ ] 9.5 Update README/progress/findings/task plan with actual implemented scope and known non-goals. Do not claim FE-F3B Identity, FE-F4 Review, FE-F5 Opportunity/Learning, real external connectors, or production deployment.
- [ ] 9.6 External review must pass before OpenSpec archive/commit. Do not push, merge, deploy, or execute production migrations without separate authorization.

