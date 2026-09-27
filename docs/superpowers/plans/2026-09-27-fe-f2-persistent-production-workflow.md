# FE-F2 Persistent Production Workflow Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task by task. Steps use checkbox syntax for tracking.

**Goal:** Replace FE-F0-F1 local-only production with project-scoped, persistent workflow design and real safe execution, reusing the existing engine.

**Architecture:** Persist project/unit/persona ownership and bindings separately from existing versioned `Workflow` rows. Enforce authorization in both project and legacy entry points before exposing runs or definitions. Treat Data Nodes and outputs as versioned, auditable project resources; adapt the frontend only after the backend boundary is testable.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, pytest, React, TypeScript, Vite.

**Spec:** `openspec/changes/archive/2026-09-27-fe-f2-persistent-production-workflow/specs/fe-f2-persistent-production-workflow/spec.md` and the archived `design.md`.

## Global Constraints

- Reuse `Workflow`, `WorkflowRun`, `WorkflowStep`, `WorkflowStepAttempt`, rerun and stale logic; do not build a second engine.
- No production migration, remote publication, external connector permission change, or fake successful execution.
- Save project override and Persona × Modality default through distinct actions; role-default portability validation is server-side.
- Visual order never rewires dependency edges.
- Preserve historical definition versions and run checksums.
- Work only on the FE-F2 branch; do not stage unrelated files or push.

## Review Focus

- Legacy raw-ID routes, workflow lists, and definition entry points must not bypass project ownership.
- Role-default saves must not leak project-bound IDs, snapshots or actual outputs.
- Unavailable data plugins must never create a successful snapshot or attempt.
- Snapshot refresh must stale only true descendants when content changes.
- Generated assets must be attached to the owning project and retain attempt/provenance links.

---

### Task 1: Persistent foundation and migration

**Files:** `apps/api/app/models.py`, `apps/api/alembic/versions/<fe-f2>.py`, `apps/api/tests/test_fe_f2_projects.py`.

**Interfaces:** `ContentProject`, `ContentPersona`, `ContentUnit`, `PersonaWorkflowDefault`, `ProjectWorkflowBinding`, `DataSnapshot`, `ProjectWorkflowOutput` mapped by stable IDs. `WorkflowRun.content_unit_id` (or equivalent association) identifies a project-bound run.

- [ ] Write a failing schema test: metadata contains all new entities, unit-to-project/persona and run-to-unit relationships, and old Workflow rows remain valid.
- [ ] Run the test and confirm expected schema failure.
- [ ] Add minimal models and additive/reversible migration from current Alembic head.
- [ ] Run targeted test and local disposable migration check; confirm green.
- [ ] Mark OpenSpec task 1.1 done only after evidence.

### Task 2: Project CRUD and ownership gate

**Files:** `apps/api/app/routers/projects.py`, `apps/api/app/services/project_authorization.py`, `apps/api/app/main.py`, `apps/api/tests/test_fe_f2_projects.py`.

**Interfaces:** project/unit CRUD; `authorize_project_run`, `authorize_project_workflow` shared by new and legacy routes. Persisted owner/member policy determines access, never request-supplied project IDs.

- [ ] Write failing API tests for project/unit CRUD, cross-project denial and legacy raw-ID/list/definition denial.
- [ ] Run tests and confirm expected failures.
- [ ] Implement minimal API and shared authorization, including all legacy read/mutation/definition routes.
- [ ] Run targeted tests and existing workflow tests; confirm green.
- [ ] Mark OpenSpec tasks 1.2–1.3 done only after evidence.

### Task 3: Versioned designer and two save paths

**Files:** `apps/api/app/services/project_workflows.py`, `apps/api/app/routers/projects.py`, `apps/api/tests/test_fe_f2_workflows.py`.

**Interfaces:** validate six node types, visual order and graph independently; save immutable project override with optimistic conflict; server-side portable role-default save with new version and later-unit selection.

- [ ] Write failing tests for invalid graph/mapping, visual reorder preserving edges, override isolation, portability rejection/parameterization, 409 conflict, unchanged old units/runs.
- [ ] Run tests and confirm expected failures.
- [ ] Implement minimal validator and save APIs using existing Workflow rows and checksums.
- [ ] Run targeted and existing workflow tests; confirm green.
- [ ] Mark OpenSpec tasks 2.1–2.4 done only after evidence.

### Task 4: Project run adapter and Data Node

**Files:** `apps/api/app/services/project_workflows.py`, `apps/api/app/services/data_source_plugins.py`, `apps/api/app/routers/projects.py`, `apps/api/tests/test_fe_f2_execution.py`.

**Interfaces:** project-scoped start/run-node/rerun-from/human/attempt APIs; typed plugin registry and availability; bounded immutable snapshots with lineage and checksum.

- [ ] Write failing tests for safe node attempts, side-effect rerun denial, disconnected plugins, changed/unchanged snapshot stale behavior, historical checksum.
- [ ] Run tests and confirm expected failures.
- [ ] Adapt existing engine and add plugin/snapshot services without generic outbound URL/SQL execution.
- [ ] Run targeted and existing workflow tests; confirm green.
- [ ] Mark OpenSpec tasks 2.5 and 3.1–3.3 done only after evidence.

### Task 5: Project output lineage

**Files:** `apps/api/app/services/project_outputs.py`, `apps/api/app/routers/projects.py`, `apps/api/tests/test_fe_f2_outputs.py`.

- [ ] Write failing tests for supported output appearing in the owning project's asset list and unsupported generator creating nothing.
- [ ] Run tests and confirm expected failures.
- [ ] Persist output references with run/node/attempt and source/rights lineage; expose project asset read API.
- [ ] Run targeted tests; confirm green.
- [ ] Mark OpenSpec task 4.1 done only after evidence.

### Task 6: Production frontend

**Files:** `apps/web/src/product/*`, `apps/web/src/App.tsx`, `apps/web/src/lib/api.ts` (or current client equivalent), frontend tests if supported by existing tooling.

- [ ] Replace real project/unit routes with API repository; leave demo fixtures visibly separate.
- [ ] Build modality-specific workspace shells and project-shared-assets entry.
- [ ] Build server-backed mini canvas, node/attempt/input/output inspector and active-run polling.
- [ ] Build Designer: add/edit/disable/delete, drag and keyboard visual order, explicit edge/mapping/config edits, unsaved/conflict states, separate override/default saves.
- [ ] Wire Data Source selector and real run/rerun/refresh/human actions; unavailable plugins remain blocked.
- [ ] Run `npm run build` and browser acceptance; mark OpenSpec tasks 5.1–5.6 done only after evidence.

### Task 7: Whole-change acceptance and archive

**Files:** `apps/api/tests/test_fe_f2_*.py`, `README.md`, `task_plan.md`, `progress.md`, `findings.md`, OpenSpec tasks.

- [ ] Run targeted and full backend tests, frontend build, OpenSpec strict and diff check; record failures honestly.
- [ ] Exercise local disposable DB migration and all security/portability/stale/output acceptance paths.
- [ ] Review owned diff against the V5 frontend contract, update README and progress, archive only if every task is truly complete.

### Task 8: FE-F2-R1 review follow-up

**Files:** `apps/api/app/routers/content_projects.py`, `apps/api/app/services/project_authorization.py`, `project_workflows.py`, `workflow_engine.py`, `apps/api/app/routers/workflows.py`, `apps/web/src/product/PersistentProjectPages.tsx`, `ProductionDesigner.tsx`, and targeted FE-F2 tests.

- [x] /// Add a failing regression for an old unit pinned to Persona default v1 after v2 publishes; read the pinned definition through a unit endpoint and load it in Design Mode.
- [x] /// Add failing matrix regressions for override-only in-place edit, explicit rebind, historical replacement/archive and read-only old Run; restore the backend/API-backed matrix controls.
- [x] /// Test that project/unit bindings outside runtime-resolved config are rejected when saving a role default, while config bindings remain parameterizable.
- [x] /// Test six-kind step persistence and failed rerun output isolation; clear current output before a new attempt while retaining old attempts.
- [x] /// Run full backend suite, frontend build, OpenSpec strict and diff check; update docs and leave archive/commit for external R1 review.
