# FE-F4 Project-first Review & Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Deliver the project-scoped Candidate → Review → DeliveryTarget flow specified by `openspec/changes/fe-f4-project-review-distribution/`, preserving legacy Topic delivery and fail-closed unknown semantics.

**Architecture:** Extend existing ContentAsset, Review and DeliveryTarget records; derive Review Center state from them and FE-F2/F3 identity/run facts. Keep project ownership checks shared across scoped and raw-ID routes. Unsupported output and unverified remote account capability remain blocked.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, SQLite test database, React/TypeScript, OpenSpec CLI.

---

### Task 1: Persistence and migration

**Files:** `apps/api/app/models.py`, new `apps/api/alembic/versions/f4...py`, `apps/api/tests/test_fe_f4_project_review.py`.

- [x] /// Add a failing isolated migration/model regression for legacy rows and new project-only candidate fields.
- [x] /// Extend existing tables, then write a reversible migration from `f3b000000001`; preserve authentic legacy identifiers and hashes.
- [x] /// Run migration upgrade→downgrade→upgrade and focused tests before marking OpenSpec 1.1–1.4.

### Task 2: Candidate freeze and approval

**Files:** `apps/api/app/services/candidates.py`, `apps/api/app/services/project_review.py`, `apps/api/app/routers/project_review.py`, `apps/api/app/routers/reviews.py`, focused tests.

- [x] /// Red-test source lineage, identity/run/evidence/check gates, immutable v3 hash, idempotent freeze, and separate approval.
- [x] /// Implement typed blockers and project-scoped read/action endpoints; preserve Topic-only legacy approval.
- [x] /// Verify focused tests and mark OpenSpec sections 2–3 only where complete.

### Task 3: Delivery and raw-ID safety

**Files:** `apps/api/app/services/delivery.py`, `apps/api/app/routers/delivery.py`, `apps/api/app/services/project_authorization.py`, v3 package adapter, focused tests.

- [x] /// Red-test cross-owner raw IDs, pre-approval authorization, stable account-key idempotency, real-byte v3 manual package, unknown reconciliation.
- [x] /// Implement shared project-bound checks and fail-closed capability gates; keep v1 article handoff intact.
- [x] /// Verify existing delivery suite plus new regressions, then mark completed OpenSpec sections 4.4 and 5.

### Task 4: Projection and frontend

**Files:** `apps/api/app/services/project_overview.py`, `apps/api/app/services/project_versions.py`, project Review read model, `apps/web/src/App.tsx`, new Review workspace UI.

- [x] /// Derive current-Candidate status, diff, events/versions/overview from persisted facts, not another table.
- [x] /// Replace `/review` placeholder with project/unit, Preview/Changes/Checks/Publish, separate actions and reconciliation; retain `/review-publish`.
- [x] /// Run focused API tests and frontend build; mark OpenSpec sections 4, 6, 7 where verified.

### Task 5: Acceptance

**Files:** `openspec/changes/fe-f4-project-review-distribution/tasks.md`, `README.md`, `task_plan.md`, `progress.md`, `findings.md`.

- [x] /// Run full backend suite in isolated SQLite, frontend build, OpenSpec strict, `git diff --check`, migration roundtrip, and bounded browser flow.
- [x] /// Obtain independent review, fix findings, update docs and task checkboxes; do not claim complete while any acceptance task is open.
- [x] /// Archive only after implementation and explicit review gate; do not push, merge, deploy or run production migrations.
