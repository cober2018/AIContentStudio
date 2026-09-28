# FE-F5A Home + Opportunity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an owner-scoped ContentOpportunity decision layer and a Home projection without duplicating Topic, Project, Review, Delivery, or Identity state.

**Architecture:** Persist opportunities, immutable signals, and append-only assessment revisions. Convert only by explicit user action into the existing ContentProject/CreativeBrief flow; Home composes existing read models and typed decisions. Keep Home and Opportunity as independent lazy route roots so FE-P1's initial bundle contract remains measurable.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, React, React Router, existing project/review/delivery services, SQLite/PostgreSQL-compatible migration.

---

### Task 1: Baseline and persistence contract

- [ ] /// Verify connector/workspace reads FE-P1 commit `85b8c08` and canonical spec before business-code apply.
- [ ] /// Add additive opportunity tables, indexes, lifecycle checks, migration, and owner authorization.
- [ ] /// Verify migration reversibility in an isolated database.

### Task 2: Opportunity domain

- [ ] /// Add CRUD, triage, signal lineage, append-only assessments, and explicit conversion API.
- [ ] /// Preserve suggestion versus approved evidence/identity semantics and idempotent conversion.

### Task 3: Product projections

- [ ] /// Add bounded Home and Opportunity read APIs from authoritative facts.
- [ ] /// Replace placeholder routes with lazy Home/Opportunity workspaces and link existing actions.
- [ ] /// Preserve FE-P1 bundle budget and route loading/error behavior.

### Task 4: Acceptance

- [ ] /// Run isolated backend migration/regression, frontend build/budget, strict OpenSpec, and diff checks.
- [ ] /// Browser-verify lifecycle, conversion, ownership, refresh, and Home projection behavior.
- [ ] /// Update documentation and request independent review before archive.
