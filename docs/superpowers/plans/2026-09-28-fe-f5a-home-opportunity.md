# FE-F5A Home + Opportunity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add an owner-scoped ContentOpportunity decision layer and a Home projection without duplicating Topic, Project, Review, Delivery, or Identity state.

**Architecture:** Persist four resources: Opportunity, Signal, append-only AssessmentRevision, and idempotent OpportunityProjectConversion. Convert only by explicit user action into the existing ContentProject/CreativeBrief flow, with optional selected SourceDocument bindings but no automatic Fact Boundary. Home composes existing read models and typed decisions. Keep Home and Opportunity as independent lazy route roots so FE-P1's initial bundle contract remains measurable.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, React, React Router, existing project/review/delivery services, SQLite/PostgreSQL-compatible migration.

---

### Task 1: Baseline and persistence contract

**Files:** `apps/api/app/models.py`, new `apps/api/alembic/versions/f5a000000001_home_opportunity.py`, `apps/api/tests/test_fe_f5a_opportunity.py`.

- [x] /// Verify local workspace descends from FE-P1 commit `85b8c08`, has canonical FE-F4/FE-P1 specs and migration head `f4a000000001` before business-code apply.
- [x] /// Add additive opportunity tables, indexes, lifecycle checks, migration, and owner authorization.
- [x] /// Verify migration reversibility in an isolated database.

### Task 2: Opportunity domain

**Files:** new `apps/api/app/routers/opportunities.py`, new `apps/api/app/services/opportunities.py`, `apps/api/app/main.py`, `apps/api/app/services/project_events.py`, targeted tests.

- [x] /// Add CRUD, audited triage/archive, signal lineage, optimistic append-only assessments, and explicit idempotent conversion API.
- [x] /// Preserve suggestion versus approved evidence/identity semantics and idempotent conversion.

### Task 3: Product projections

**Files:** new `apps/api/app/services/home_projection.py`, new `apps/api/app/routers/home.py`, new `apps/web/src/product/HomePage.tsx`, new `apps/web/src/product/OpportunityPages.tsx`, `apps/web/src/App.tsx`, targeted tests.

- [x] /// Add bounded Home and Opportunity read APIs from authoritative facts with deterministic order, decision precedence, and explicit failure semantics.
- [x] /// Replace placeholder routes with lazy Home/Opportunity workspaces and link existing actions.
- [x] /// Preserve FE-P1 bundle budget and route loading/error behavior.

### Task 4: Acceptance

- [x] /// Add and run targeted backend regressions, isolated migration upgrade/rollback, frontend build/budget, strict OpenSpec, and diff checks.
- [x] /// Browser-verify lifecycle, conversion, ownership, refresh, and Home projection behavior.
- [x] /// Update documentation and request independent review before archive.
