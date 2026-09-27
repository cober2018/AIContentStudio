# FE-F3B Content Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver persistent Brand → Persona → Account → Series identity, immutable revisions/snapshots, scoped workflow defaults, and the real Identity/Production UI without rewriting FE-F2/F3A history.

**Architecture:** Extend the existing Persona and workflow services rather than creating a second runtime. Stable hierarchy rows own append-only override revisions; a server resolver freezes the effective identity into a snapshot pinned to each new unit and copied to its runs. Historical null snapshots remain explicitly legacy.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy/Alembic, React/TypeScript, existing pytest and Vite build.

---

### Task 1: Specification and baseline

**Files:** `openspec/changes/fe-f3b-content-identity/{proposal,design,tasks}.md`, `openspec/changes/fe-f3b-content-identity/specs/*/spec.md`, `task_plan.md`, `progress.md`, `findings.md`.

- [x] Create an isolated worktree from `1fa4520` and standard OpenSpec change; preserve the source package in the primary checkout.
- [x] Audit delta specs against full FE-F0/F1, FE-F2 and FE-F3A main requirements; clarify global BrandVoice access, archived ancestors, brandless Persona, and child-selection semantics.
- [x] Validate OpenSpec strict and verify baseline: 296 backend tests with an initialized isolated worker DB; frontend build succeeds with existing bundle warning.
- [x] Mark setup tasks complete and record exact constraints in progress/findings.

### Task 2: Identity persistence and reversible migration

**Files:** `apps/api/app/models.py`, `apps/api/alembic/versions/f3b000000001_content_identity.py`, `apps/api/tests/test_fe_f3b_content_identity.py`.

- [x] Add stable Brand/Account/Series rows, Persona parent/status, append-only revision rows, IdentitySnapshot and scoped default tables; add nullable references on Unit/Run.
- [x] Add a reversible migration on `f3a000000001`, preserving all historical IDs and null snapshots.
- [ ] Verify isolated upgrade/downgrade/upgrade with representative FE-F3A rows and no synthetic Brand or snapshot.

### Task 3: Resolver, authorization and revision API

**Files:** `apps/api/app/services/content_identity.py`, `apps/api/app/routers/content_identities.py`, `apps/api/app/main.py`, `apps/api/tests/test_fe_f3b_content_identity.py`.

- [ ] Validate typed override keys and persisted hierarchy ownership; missing inherits, null clears, arrays/objects replace.
- [ ] Implement immutable revision save with optimistic precondition and database-conflict 409; reject archived ancestor writes.
- [ ] Reuse global published BrandVoiceVersion, resolve effective profile/origins, create canonical immutable snapshot and authorize snapshot read.
- [ ] Expose Brand/Persona/Account/Series hierarchy, archive, revisions and effective reads without breaking legacy Persona list/create.

### Task 4: Workflow and unit/run pinning

**Files:** `apps/api/app/services/identity_workflows.py`, `apps/api/app/routers/content_projects.py`, `apps/api/app/services/workflow_engine.py`, `apps/api/app/services/project_authorization.py`, `apps/api/app/routers/workflows.py`, `apps/api/tests/test_fe_f3b_content_identity.py`.

- [ ] Resolve scoped default Series > Account > Persona; save immutable Account/Series default versions through FE-F2 validators and portability gate.
- [ ] Extend new Unit creation and explicit rebind; preserve FE-F2 pre-history in-place and post-history replacement/archive behavior.
- [ ] Before every new project Run, reject any archived Brand/Persona/Account/Series in the selected Unit hierarchy; then copy the Unit's exact snapshot ID to the Run. Legacy null remains legacy.
- [ ] Close legacy raw-workflow access to Account/Series scoped definitions through shared authorization.

### Task 5: Project-core integration

**Files:** `apps/api/app/services/project_versions.py`, `apps/api/app/services/project_overview.py`, `apps/api/app/routers/content_projects.py`, `apps/api/tests/test_fe_f3b_content_identity.py`.

- [ ] Include only real linked snapshots in Versions, label historical nulls, and derive identity-readiness for active units. A real but empty snapshot from a brandless Persona without an authored profile is still incomplete, not ready.
- [ ] Validate typed Brief identity references on new revisions; preserve untyped historical labels and prior revisions.
- [ ] Record old/new snapshot IDs in rebind/replacement project events.

### Task 6: Persistent Identity Workspace and production UI

**Files:** `apps/web/src/App.tsx`, `apps/web/src/product/identity/*`, `apps/web/src/product/PersistentProjectPages.tsx`, `apps/web/src/product/ProductionDesigner.tsx`, `apps/web/src/product/project/*`.

- [ ] Build real `/identities` tree and detail tabs with loading/error/empty/archived states, revision editor/history, inherited-origin display, and truthful Content Memory boundary.
- [ ] Show Persona/Account/Series workflow preference and resolved scope; never imply a disconnected or unbound default is runnable.
- [ ] Add Account/Series selection and explicit rebind to Matrix; show frozen Unit/Run identity and legacy label in Production.
- [ ] Build TypeScript/Vite and inspect the integrated routes.

### Task 7: Verification and handoff

**Files:** `README.md`, `progress.md`, `findings.md`, `task_plan.md`, OpenSpec task file.

- [ ] Run targeted and full backend tests with isolated initialized worker DB, frontend build, strict OpenSpec, and `git diff --check`.
- [ ] Verify isolated migration and browser journeys, including legacy truth and pre/post-history rebind.
- [ ] Specifically verify archived-ancestor Run rejection and empty brandless-Persona snapshot `identity_unready` in Overview.
- [ ] Request independent review; resolve findings before archive or commit.
- [ ] Archive/sync OpenSpec only after acceptance; do not push, merge, deploy or run production migration.
