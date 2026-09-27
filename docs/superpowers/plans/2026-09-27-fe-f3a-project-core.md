# FE-F3A Project Core Implementation Plan

> **For agentic workers:** Execute this plan with `superpowers:executing-plans`. Track detailed acceptance in `openspec/changes/fe-f3a-content-project-core-completion/tasks.md`.

**Goal:** Make all seven persisted ContentProject tabs functional using one project core, without replacing FE-F2 workflow history or global Source/FactPack/Material resources.

**Architecture:** Add five project-owned reference/revision/event tables after the FE-F2 migration. Keep business rules in small services, expose project-scoped APIs, and make the existing persistent project UI consume those APIs. Source, FactPack and Material remain global resources with their existing authorization semantics.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic, React/TypeScript, existing backend test and frontend build tooling.

---

### Phase 1: Persistence and lifecycle

**Files:** `apps/api/app/models.py`, `apps/api/alembic/versions/`, `apps/api/app/routers/content_projects.py`, `apps/api/app/services/project_events.py`.

- [ ] /// Add five FE-F3A models and one reversible migration after `e5fef2000001`.
- [ ] /// Add transactional project-event service and instrument existing project/unit/workflow/data/output writes.
- [ ] /// Change project deletion to idempotent archive; preserve reads and block project-scoped mutations through new and legacy APIs.
- [ ] /// Verify isolated migration upgrade/downgrade/upgrade and FE-F2 historical rows.

### Phase 2: Project-core services and API

**Files:** `apps/api/app/routers/content_projects.py`, `apps/api/app/services/project_brief.py`, `apps/api/app/services/project_evidence.py`, `apps/api/app/services/project_assets.py`, `apps/api/app/services/project_versions.py`, `apps/api/app/services/project_overview.py`, `apps/api/app/services/factpack_service.py`, `apps/api/app/routers/fact_packs.py`.

- [ ] /// Add append-only Brief revisions with checksum and race-safe optimistic save.
- [ ] /// Add Source references and frozen Fact Boundary revisions; share FactPack clone/freeze rules.
- [ ] /// Add explicit MaterialRevision references/upload and unified Shared Assets read model.
- [ ] /// Add bounded Versions/Activity and deterministic Overview reads.
- [ ] /// Check owner/resource permissions and no mutation of frozen/historical global rows.

### Phase 3: Seven persisted project tabs

**Files:** `apps/web/src/product/PersistentProjectPages.tsx`, `apps/web/src/product/project/`.

- [ ] /// Split project tab API/types/components by responsibility while retaining Matrix and Production routes.
- [ ] /// Bind Overview, Brief, Evidence, Assets, Versions and Activity to real project APIs.
- [ ] /// Keep browser-only demo isolated; replace placeholder copy with truthful empty states.
- [ ] /// Build frontend and inspect representative local project flow.

### Phase 4: Verification and handoff

**Files:** `openspec/changes/fe-f3a-content-project-core-completion/tasks.md`, `README.md`, `task_plan.md`, `progress.md`, `findings.md`.

- [ ] /// Run available targeted/full backend checks, frontend build, OpenSpec strict and diff check.
- [ ] /// Exercise isolated local create → Brief → Source → Fact Boundary → Assets → Versions/Activity/Overview → reload flow.
- [ ] /// Record actual evidence and unfinished items. External review is required before archive/commit; no push, merge, deployment or production migration.
