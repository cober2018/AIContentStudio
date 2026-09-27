## Context

The FE-F0-F1 project list and Content Units are stored in browser `localStorage`; `ProductionShellPage` has no backend link. The backend already persists `Workflow`, `WorkflowRun`, `WorkflowStep`, and immutable step attempts, with node rerun and downstream-stale handling. Its runs are currently addressed by `topic_id`/channel/content_form rather than a Content Unit. Published workflow definitions are versioned, but there is no project-override editor endpoint or dedicated Data Source Plugin. User confirmed FE-F2 must really execute and persist, not just demonstrate the UI.

## Goals / Non-Goals

**Goals:** Every run belongs to one Content Unit, with multiple immutable historical runs allowed; persisted project/unit records, project override revisions, and selectable Persona × Modality default versions; real safe node execution and attempt readback; snapshot-backed data refresh and stale propagation; project-shared workflow outputs; usable text/graphic/video workspace shells with an embedded debugger.

**Non-Goals:** A new generic DAG engine, automatic publication, arbitrary SQL or outbound HTTP from a browser-defined node, all six real connectors, full video production, the full identity hierarchy/management workspace, or retroactive mutation of old workflow runs. A backend fixture does not claim an external platform action occurred.

## Decisions

### Reuse the engine and add a project adapter

Three approaches were considered: (1) retain `localStorage` and overlay API calls, which cannot provide durable project/run identity; (2) replace the workflow engine with a new project-native DAG, which duplicates attempt history and safety gates; (3) persist minimal ContentProject/ContentUnit records and adapt them to the existing engine. Choose (3). Add project/unit tables and explicit project-run association, while retaining existing Topic-oriented APIs. The project and unit IDs are the authorization and query boundary; a URL parameter alone never grants access to an arbitrary run.

### Close legacy API access to project-bound runs and definitions

Use one shared server-side authorization service: `authorize_project_run` resolves a run's persisted project/unit binding, while definition entry points use the same ownership policy through a workflow-scope check. Never trust project/unit IDs supplied by the request. Apply action-specific read/edit/review checks before serialization or mutation. At minimum guard legacy run detail, list, attempts, retry, node rerun, rerun-from-here, human completion, and cancel. Legacy Workflow list/serialization, clone, publish, and raw create-run must also hide, authorize, or reject project-bound definitions/runs; a raw `workflow_id` must not start a project run outside its unit boundary. Persona-default definitions use their own persisted Persona scope and authorization within the same service. Legacy Topic-only runs retain their existing behavior. Denials reveal no protected context, step output, or attempt data. A project-scoped route is not sufficient if an older route still reaches the same row.

### Save project overrides as immutable revisions

Design edits are client-side until explicit Save. Store visual order/layout separately from dependency edges and input/output mappings. Drag-and-drop or keyboard/up-down changes visual order only; editing `depends_on`/edges or mappings is an explicit inspector action. The server validates node IDs, six node types, plugin descriptors/config, missing dependencies, duplicate IDs, cycles, invalid input/output mappings, unsupported executors, execution conditions, failure policies, permissions, and prohibited side effects, then creates a *new* versioned `Workflow` definition linked to that Content Unit as a project override. An existing published definition and its historical runs remain unchanged. Use optimistic revision/checksum to reject concurrent overwrites; show conflict and offer reload. A new run pins the exact saved definition checksum. Do not mutate a workflow already referenced by a run. Visual order may provide a deterministic tie-breaker for independent ready nodes but never creates or removes an edge.

### Save a Persona × Modality default as a separate action

FE-F2 needs the smallest durable Persona/Role identity and binding needed for workflow ownership; an authentication role such as editor/reviewer is not a content Persona. Bind `(persona_id, modality)` to one current default `Workflow` version. A Content Unit stores its stable Persona reference and modality, resolves the current default when created or explicitly rebound, and may hold an independent project override. “Save as new role default” requires an explicit action and authorization, creates a new immutable `Workflow` version under that Persona × Modality family, and atomically updates the default binding with an optimistic precondition. Existing Content Units, overrides, and runs keep their pinned versions until explicitly rebound; a project override save never updates the role default. FE-F2 does not build the complete Brand → Persona → Account → Series management UI.

Before that role-default save, the server constructs a portable definition from allowed structural fields: node types/IDs, graph edges, generic configuration and parameter templates, plugin types, authorized reusable connection/profile references, rules, and model policy. Project/run/unit IDs, DataSnapshot IDs, project AssetRevision/Draft/Candidate IDs, attempt IDs, and actual node outputs are never copied into a Persona default. Typed, safely parameterizable bindings become placeholders/context bindings; unsupported or non-portable values cause a rejected save with a field-level reason. Validate the resulting portable definition again before publishing it. Do not rely on the frontend to strip fields, and do not mutate the project override when the portability gate rejects the role-default save.

### Keep execution honest and bounded

The mini canvas reads `WorkflowStep` and `WorkflowStepAttempt` from the backend; it does not invent successful output locally. Run Node is permitted only for resolved, non-side-effect plugins with satisfied prerequisites. Run From Here uses the existing dependency/staleness contract and refuses downstream side-effect nodes. Human gates use the existing completion API and role checks. Unknown or externally uncertain results remain visible as unknown/blocked. The UI polls only active runs and stops on terminal or human-waiting states.

### Data Source Plugin registry is extensible from day one

Add a typed registry separate from Tool nodes. A descriptor exposes stable key/name/category/connection mode, search/query/snapshot capabilities, configuration/result schemas, and availability with a reason. Register selector-visible descriptors for internal data, media data, Notion, Obsidian, API, and SQL/Database without hard-coding the protocol to Studio Source. The first executable adapter reads an existing Studio `Source` record under current access rules, normalizes a bounded payload, and writes an immutable snapshot with checksum, source/version identity, and lineage. The Data Node stores plugin key, connection reference, selector/query parameters, snapshot policy and ID; Refresh creates a new snapshot and compares hashes. Changed output marks actual dependency descendants stale through the existing staleness service; unchanged output preserves their state. A descriptor without a verified connector is shown as disconnected/unexecutable and cannot produce a successful attempt or snapshot. No arbitrary URL/SQL input in this slice.

### Record project-shared workflow outputs

When a supported node creates a draft, image, chart, screenshot, or video clip, persist the resulting Draft/AssetRevision/Candidate reference with run, node, attempt, project, unit, source-snapshot, and rights/provenance linkage as applicable. Generated media revisions become discoverable in the owning project's Shared Assets without copying bytes or losing version history. Unsupported media generation stays blocked; a successful node status alone does not manufacture an asset or approved Candidate.

### Preserve current product semantics

The ContentProject list and seven tabs keep their URLs and become API-backed. Browser demo fixtures remain an explicit demo path; the application must not silently import or overwrite local records. The three modality shells share the run/inspector services but keep different editing surfaces. The canvas is *the selected unit's run*, not a global Workflow page. Project Shared Assets stays in a drawer. Normal UI uses product terms; plugin/provider internals remain in advanced inspection.

## Risks / Trade-offs

- [Existing workflow handlers expect Topic context] → Adapt only existing compatible executors to Content Unit context; reject unsupported steps before run rather than claiming universal execution.
- [Concurrent save overwrites another edit] → Require revision/checksum precondition and return conflict without changing the prior definition.
- [Rerun could repeat remote effects] → Reuse and strengthen side-effect descriptor checks; never expose a generic retry for delivery/publish nodes.
- [Snapshot payload may include restricted source text] → Limit data fields/size, preserve source permissions and provenance, and return only data the current role may inspect.
- [Migration on a dirty worktree] → Isolate FE-F2-owned edits, inspect overlapping user changes before patching, and avoid touching unrelated work.
- [Old local demo data differs from backend] → Explicit demo/real state; no automatic browser-to-database import.
- [A project override accidentally changes a global default] → Separate endpoints/actions and optimistic binding version; historical units/runs retain their pinned definition.
- [A registered but disconnected data source looks usable] → Registry availability and reason are server-derived; execution fails closed until a real connection is verified.
- [Legacy raw-ID endpoints bypass project ownership] → Shared authorization policy covers reads, lists, attempts, mutations, and definition access before serialization or execution.
- [Role default captures a project snapshot or output] → Server-side template allow-list and parameterization/rejection gate; never copy live context or actual output.
- [Drag reorder silently rewires a graph] → Persist visual order separately; only explicit edge/mapping edits change dependencies.

## Migration Plan

1. Add additive project/unit/Persona-default-binding/association/snapshot/output-association tables and API endpoints; do not rewrite existing Workflow or Topic records.
2. Bind project runs and definitions to their owners and close all legacy entry points with shared authorization before exposing project-run creation or output.
3. Add the two distinct save paths, server-side portability gate, plugin registry, and safe execution endpoints; then switch FE-F0-F1 project pages to the real repository behind a clear demo/real boundary.
4. Build the modality workspaces and debugger, and run targeted regression tests plus local development-DB acceptance for legacy-path isolation, portable role defaults, visual-order/edge separation, both save paths, revision conflict, rerun/stale, disconnected-source blocking, project asset lineage, and no unauthorized or external side effect.
5. Apply migrations only in the local test/development environment during this task. Production migration/deployment needs separate authorization and preflight.

## Open Questions

- Exact backend identity and permission ownership are limited by the current development-header model; FE-F2 does not claim production-grade multi-tenant isolation.
- Existing browser-only demo entries are not migrated automatically; an explicit import decision belongs to a separate change if needed.
