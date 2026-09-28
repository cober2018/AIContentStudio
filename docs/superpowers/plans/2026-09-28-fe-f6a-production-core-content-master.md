# FE-F6A Production Core Specification and Implementation Plan

> **For agentic workers:** Apply and local main integration were authorized. The user separately authorized all five canonical-spec updates and F6A archive on 2026-09-29. Remain on local main; do not push, deploy, run production migrations or start F6B+.

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

Source: openspec/fe-f6a-production-core-content-master/ and original ZIP, both untouched. Initial business/test implementation used codex/fe-f6a-production-core-content-master; the user subsequently authorized integrating the stage into main and continuing directly there. No push, deployment or production migration. Implementation acceptance completed at main@d060428; five canonical specs were synchronized under separate archive authorization on 2026-09-29. Archived artifacts reside at openspec/changes/archive/2026-09-29-fe-f6a-production-core-content-master/.

## Implementation sequence

### 1. Baseline and persistence

Files: apps/api/app/models.py; new incremental migration under apps/api/alembic/versions/.

- [x] /// Verify fresh connector/local baseline and existing worktree availability after approval.
- [x] /// Isolated full-suite/build/bundle baseline before code changes.
- [x] /// Four Master tables, FK/history constraints and nullable ContentAsset link/body; no backfill.
- [x] /// SQLite up/down/up and PostgreSQL-compatible constraints; incompatible downgrade fails before destructive DDL. SQLite and actual isolated PostgreSQL16 roundtrips and history refusal passed.

### 2. Master/context/ref services

Files: proposed apps/api/app/services/content_masters.py, production_modalities.py, content_master_checks.py; apps/api/app/routers/content_masters.py; apps/api/app/main.py.

- [x] /// Authorized append-only save, fingerprint idempotency, CAS/head/parent/context transaction gate. Replay, parent, shared archive/context locking and commit revalidation passed.
- [x] /// Frozen unit identity plus Brief/Boundary context and derived stale/readiness, no latest repinning.
- [x] /// Exact project-visible MaterialRevision/FactPackItem refs, payload bounds and typed locators. Bounds/schema, embedded refs and generated-asset lineage all passed.
- [x] /// Immutable current input-bound checks, latest-result authority and warning disposition. Append-only/latest/stale, live rights, renderer and exact latest-warning disposition gates passed.
- [x] /// Three bounded payload adapters, render-input binding and truthful manual-render attestation.

### 3. Existing unit/workflow history

Files: apps/api/app/routers/content_projects.py; apps/api/app/services/project_outputs.py.

- [x] /// Count Master-only history for Fork + Archive and delete safety.
- [x] /// Seed from current verified Draft/Run/Step/Attempt; retain exact old execution provenance.
- [x] /// Optional future Master output association only with persisted verified lineage.

### 4. Candidate v4/review/local package

Files: apps/api/app/services/project_review.py, project_review_projection.py, candidates.py, delivery.py; apps/api/app/routers/project_review.py, assets.py; related legacy export services discovered narrowly during apply.

- [x] /// Exactly one source and current Master validation; dual v3/v4 schema dispatch/hash/idempotency.
- [x] /// Exact-hash review approval/new authorization with live rights and immutable history.
- [x] /// Audit every relevant raw legacy read/mutation/export for common ownership/archive gates.
- [x] /// Real modality preview/diff and local packages; no v4 fallback or unverified remote capability.

### 5. Project/read models and UI

Files: apps/api/app/services/project_versions.py, project_overview.py; apps/web/src/product/ProductionDesigner.tsx, PersistentProductionPage.tsx, ProjectReviewCenter.tsx; new narrowly scoped production components; apps/web/scripts/check-bundle.mjs.

- [x] /// Include exact Master history and derived readiness without duplicate status storage.
- [x] /// Common shell split while preserving actual debugger and archive readonly semantics.
- [x] /// Separate workflow/content dirty/save state, minimal modality payload editing only.
- [x] /// Lazy production boundary and no TipTap/XYFlow leakage to existing entry budgets.

### 6. Acceptance and handoff

Files: targeted existing test infrastructure only after user authorization; standard change tasks.md and root progress/findings/README.

- [x] /// Targeted race/idempotency/history/render/legacy authorization regressions, then full suite.
- [x] /// Isolated browser history/409/seed/check/freeze/review/local package acceptance.
- [x] /// Independent backend/frontend/spec review and fresh strict/build/bundle/Ruff/diff gates.
- [x] /// Record 214/214 acceptance and the authorized local-main implementation commit d060428; canonical sync/archive subsequently authorized and completed separately on 2026-09-29.

## Gate commands

- Specification after archive: openspec validate --all --strict; git diff --check. Historical tasks/artifacts remain at openspec/changes/archive/2026-09-29-fe-f6a-production-core-content-master/.
- Code head only: from apps/api, .venv/bin/python -m alembic heads (no upgrade).
- Future code gates: isolated DATABASE_URL pytest; apps/web npm run build; targeted Ruff. Never substitute prior F5C outcomes for fresh F6A evidence.

## Lifecycle map

Unit-pinned context → Master revision + exact refs → input-bound checks + verified/attested render → Freeze v4 → Content Approval → Delivery Authorization → local package.

Workflow save → Workflow definition/run; Content save → Master revision. Neither action implicitly changes the other.

## Final evidence and next-slice boundary

753 backend tests passed, including 206 F6A cases and two actual PostgreSQL acceptance tests. Browser 20.1–20.14 passed with archived-readonly regression; all three independent reviews APPROVE. See docs/FE_F6A_FINAL_ACCEPTANCE.md for full evidence. The user limited this close to F6A; do not begin F6B or later without a concrete proposal and new confirmation.
