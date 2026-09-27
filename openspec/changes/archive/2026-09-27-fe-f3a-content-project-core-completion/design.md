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

The revision comparison and insert MUST be race-safe. The database uniqueness constraint is the final guard; a competing insert must be translated to 409 after rollback, not leak a 500 or commit an event without its revision. Apply the same rule to Fact Boundary revisions.

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
Re-attaching a detached Source reactivates its existing unique project/source binding; repeating an active attach returns that binding without a second event. The project owner check does not itself grant global Source access: apply the existing global Source read/use policy before exposing details or binding a source. The current global Source model has no owner field, so this change does not claim tenant isolation for that library.

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
Re-attaching a detached revision reactivates its existing unique project/revision reference; repeating an active attach returns it without a second event. Apply the existing global MaterialRevision read/use policy before attaching or exposing rights and provenance. `create_revision()` writes bytes outside the DB transaction; if the DB transaction fails, clean up newly written unreferenced bytes or record them for bounded cleanup, without deleting a hash-addressed object still referenced elsewhere. Never report a successful project upload if the reference/event transaction failed.

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
project.archived
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
unit.deleted
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

Event insertion occurs in the same DB transaction as the business mutation. Call the event helper before the existing route/service commit; no nested commit in the helper. A failed or rolled-back mutation leaves neither its state change nor its event. External byte storage is handled separately as described above.

The existing `DELETE /content-projects/{project_id}` physically deletes projects with no units. Once a project has append-only events or other FE-F3A children, physical deletion would violate retention or fail on foreign keys. FE-F3A changes project deletion to an archive transition (`ContentProject.status = archived`) plus `project.archived` in one transaction. An archived project remains readable for history but all project-scoped mutations, including legacy FE-F2 run mutations, fail closed. Repeating the archive request is idempotent. The project list distinguishes archived from active projects; no FE-F3A child rows are cascaded away. This is a product lifecycle rule, not a new table.

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
