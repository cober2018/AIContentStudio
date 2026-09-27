## Why

FE-F0-F1 established a project-first frontend, but projects and Content Units live only in browser storage while the existing backend workflow engine is Topic-oriented. A visible debugger would otherwise misrepresent real execution and lose its edits on another device. FE-F2 must make the selected project's workflow editable, executable, and persistent end to end.

## What Changes

- Persist ContentProject and ContentUnit identities in the backend, including a stable Persona/Role reference and modality for each unit. Resolve its workflow from the Persona × Modality default or an explicit project override, and pin the chosen version to each run. Provide a bounded path to replace the FE-F0-F1 local demo repository without silently migrating browser-only data.
- Reuse the existing Workflow/WorkflowRun/WorkflowStep engine and attempt history. Add project-scoped workflow endpoints, then apply the same project/unit authorization to every legacy route that can list, read, create, inspect, retry, rerun, complete, cancel, clone, or publish a project-bound run or definition. Preserve immutable published definitions and historical runs.
- Build text, graphic, and video Production Workspace shells with a unit-scoped mini canvas, six first-class node types (Data/AI/Tool/Rule/Human/System), node inspector, design mode, add/edit/delete, drag-and-drop visual reorder with a keyboard alternative, explicit dependency/edge and input/output mapping editing, unsaved-change indicator, and input/output/attempt views. Moving a card never silently changes graph dependencies.
- Support two explicit, separate save actions: save an immutable project override, or save a new immutable Persona × Modality default Workflow Template Version. The latter passes a server-side portability gate that parameterizes safe project bindings and rejects non-portable project/run/snapshot/output references. A saved role default is selectable by later Content Units; saving a project override never changes that default silently.
- Introduce an extensible, typed Data Source Plugin registry and selector for internal data, media data, Notion, Obsidian, API, and SQL/Database. One verified read-only Studio Source adapter is the initial executable implementation; other descriptors may be registered but must display disconnected/unexecutable until a real connector is configured and verified. Refresh creates a persisted snapshot and changed output marks dependent nodes stale.
- Persist supported workflow-produced Draft/AssetRevision/Candidate references; generated image, chart, screenshot, and video-clip revisions automatically appear in the owning project's Shared Assets with provenance, without fabricating output for unsupported nodes.
- Reuse existing permissions and fail closed on unsupported node types, missing credentials, invalid dependencies or mappings, non-portable role templates, and side-effectful reruns. Add targeted regression tests for these FE-F2 invariants using the existing test infrastructure. FE-F2 does not auto-publish, grant remote access, or convert an unknown external result into success.
- Keep the broader identity hierarchy, role-management workspace, and full media-rendering pipeline for later phases; FE-F2 includes only the minimum persistent Persona/Role identity needed to own and select default workflow versions.

## Capabilities

### New Capabilities

- `fe-f2-persistent-production-workflow`: Project-scoped workflow persistence and execution, Persona × Modality default-template versioning, Data Source Plugin registry and snapshots, debugger, project asset outputs, and three modality workspaces.

### Modified Capabilities

- `fe-f0-f1-project-experience`: Replace project/unit local-mock CRUD with backend persistence while retaining the existing project-first navigation and seven tabs.

## Impact

- Backend: `apps/api/app/models.py`, an incremental Alembic migration, minimal Persona/Role and template-version bindings, project/workflow routers, workflow engine adapters, data-source registry, and output-asset association.
- Frontend: `apps/web/src/product/`, `apps/web/src/App.tsx`, existing API client and reusable UI components; existing legacy Workflow pages remain reachable.
- Data: new project/unit/override/default-binding/snapshot/output-association records; existing workflow definitions and run history are not rewritten. Existing browser-only demo entries remain local until an explicit import policy is chosen.
- No production deployment, remote publication, secret migration, or actual external connector permission changes are included.
