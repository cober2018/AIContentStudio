# FE-F6A Production Core Specification and Implementation Plan

> **For agentic workers:** Apply and local main integration were authorized. After stage integration, continue in /Users/mshengran/Project/AIContentStudio on main as the user requested. Do not archive, push, deploy or run production migrations.

**Goal:** Introduce an immutable production core and Candidate v4 without replacing legacy workflow/review engines or implementing full modality editors.

**Architecture:** ContentUnit owns append-only Masters and exact project-visible asset/evidence refs. Schema-dispatched adapters freeze v4 and preserve v3; existing ownership, history and delivery gates remain authoritative.

**Tech Stack:** Existing FastAPI, SQLAlchemy/Alembic, React/TypeScript, OpenSpec CLI; no new runtime dependency planned.

## Current phase and gates

- [x] /// Read full original package and identify post-F5C baseline main661e30a.
- [x] /// Record read-only Alembic code head f5c000000001; no database migration.
- [x] /// Standardize all artifacts at openspec/changes/fe-f6a-production-core-content-master.
- [x] /// Independent calibrated proposal/spec/plan review APPROVE; strict24/24, diff and canonical preservation gates pass.
- [x] User confirmed apply; targeted regression tests are interpreted as included in that authorization (the prior confirmation question named both).
- [x] Real connector evidence of final post-F5C canonical/main: user supplied successful reads at main@661e30a, migration f5c000000001.

## Apply scope

Source: openspec/fe-f6a-production-core-content-master/ and original ZIP, both untouched. Initial business/test implementation used codex/fe-f6a-production-core-content-master; the user subsequently authorized integrating the stage into main and continuing directly there. No push, deployment or production migration. Canonical specs remain unchanged until eventual authorized archive. Integration does not mark incomplete implementation as accepted.

## Implementation sequence

### 1. Baseline and persistence

Files: apps/api/app/models.py; new incremental migration under apps/api/alembic/versions/.

- [x] /// Verify fresh connector/local baseline and existing worktree availability after approval.
- [x] /// Isolated full-suite/build/bundle baseline before code changes.
- [x] /// Four Master tables, FK/history constraints and nullable ContentAsset link/body; no backfill.
- [ ] /// SQLite up/down/up and PostgreSQL-compatible constraints; incompatible downgrade fails before destructive DDL. SQLite history refusal is tested; actual PostgreSQL validation remains outstanding.

### 2. Master/context/ref services

Files: proposed apps/api/app/services/content_masters.py, production_modalities.py, content_master_checks.py; apps/api/app/routers/content_masters.py; apps/api/app/main.py.

- [ ] /// Authorized append-only save, fingerprint idempotency, CAS/head/parent/context transaction gate. Replay and parent tests pass; shared archive/context locking remains outstanding.
- [x] /// Frozen unit identity plus Brief/Boundary context and derived stale/readiness, no latest repinning.
- [ ] /// Exact project-visible MaterialRevision/FactPackItem refs, payload bounds and typed locators. Bounds/schema are tested; embedded refs and generated-asset lineage remain outstanding.
- [ ] /// Immutable current input-bound checks, latest-result authority and warning disposition. Append-only/latest/stale tests pass; full rights, renderer and warning-disposition gates remain outstanding.
- [ ] /// Three bounded payload adapters, render-input binding and truthful manual-render attestation.

### 3. Existing unit/workflow history

Files: apps/api/app/routers/content_projects.py; apps/api/app/services/project_outputs.py.

- [ ] /// Count Master-only history for Fork + Archive and delete safety.
- [ ] /// Seed from current verified Draft/Run/Step/Attempt; retain exact old execution provenance.
- [ ] /// Optional future Master output association only with persisted verified lineage.

### 4. Candidate v4/review/local package

Files: apps/api/app/services/project_review.py, project_review_projection.py, candidates.py, delivery.py; apps/api/app/routers/project_review.py, assets.py; related legacy export services discovered narrowly during apply.

- [ ] /// Exactly one source and current Master validation; dual v3/v4 schema dispatch/hash/idempotency.
- [ ] /// Exact-hash review approval/new authorization with live rights and immutable history.
- [ ] /// Audit every relevant raw legacy read/mutation/export for common ownership/archive gates.
- [ ] /// Real modality preview/diff and local packages; no v4 fallback or unverified remote capability.

### 5. Project/read models and UI

Files: apps/api/app/services/project_versions.py, project_overview.py; apps/web/src/product/ProductionDesigner.tsx, PersistentProductionPage.tsx, ProjectReviewCenter.tsx; new narrowly scoped production components; apps/web/scripts/check-bundle.mjs.

- [ ] /// Include exact Master history and derived readiness without duplicate status storage.
- [ ] /// Common shell split while preserving actual debugger and archive readonly semantics.
- [ ] /// Separate workflow/content dirty/save state, minimal modality payload editing only.
- [ ] /// Lazy production boundary and no TipTap/XYFlow leakage to existing entry budgets.

### 6. Acceptance and handoff

Files: targeted existing test infrastructure only after user authorization; standard change tasks.md and root progress/findings/README.

- [ ] /// Targeted race/idempotency/history/render/legacy authorization regressions, then full suite.
- [ ] /// Isolated browser history/409/seed/check/freeze/review/local package acceptance.
- [ ] /// Independent backend/frontend/spec review and fresh strict/build/bundle/Ruff/diff gates.
- [ ] /// Report implementation outcome; archive/canonical sync/local merge need separate authorization.

## Gate commands

- Specification: openspec status --change fe-f6a-production-core-content-master --json; openspec validate --all --strict; git diff --check.
- Code head only: from apps/api, .venv/bin/python -m alembic heads (no upgrade).
- Future code gates: isolated DATABASE_URL pytest; apps/web npm run build; targeted Ruff. Never substitute prior F5C outcomes for fresh F6A evidence.

## Lifecycle map

Unit-pinned context → Master revision + exact refs → input-bound checks + verified/attested render → Freeze v4 → Content Approval → Delivery Authorization → local package.

Workflow save → Workflow definition/run; Content save → Master revision. Neither action implicitly changes the other.
