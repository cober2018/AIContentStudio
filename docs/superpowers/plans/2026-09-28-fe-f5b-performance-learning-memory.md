# FE-F5B Performance / Learning / Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans after the calibrated proposal is explicitly confirmed. Steps use checkbox syntax.

**Goal:** Close published-content performance → validated learning → explicit Memory promotion without changing Identity, Workflow or channel strategy implicitly.

**Architecture:** Seven additive owner-scoped resources, existing Receipt/Feedback/Candidate provenance, immutable observations/Insights and frozen validation snapshots; reuse Identity hierarchy and Home projection. Legacy receipt timestamps remain confirmation provenance, never fabricated publication dates. Declare metric measurement grain before aggregation.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, React, existing SQLite/PostgreSQL-compatible constraints and frontend bundle tooling.

## Review gate

- [x] /// Verify main `dd71a14`, canonical F5A/FE-P1 and Alembic code head `f5a000000001`.
- [x] /// Preserve unpacked source package; calibrate six delta specs in `openspec/changes/fe-f5b-performance-learning-memory/`.
- [x] /// Independently review the calibrated contract; targeted receipt recovery follow-up APPROVE.
- [x] /// Obtain explicit user confirmation of the calibrated contract and targeted regression scope before apply.

## Implementation sequence after confirmation

1. /// Baseline gates and isolated branch: reuse a free active checkout only after inspecting artifacts and accounting for changes; branch `codex/fe-f5b-performance-learning-memory` from confirmed main. Run existing backend suite against a migrated isolated database, frontend build and strict. Do not include original untracked packages.
2. /// Persistence: modify `apps/api/app/models.py`; create a reversible migration in `apps/api/alembic/versions/` after f5a000000001. Add seven resources, revision counters, receipt/import/source-candidate uniqueness and foreign keys. Verify fresh upgrade and historical upgrade/downgrade/upgrade only in isolated databases.
3. /// Publication and observations: create `apps/api/app/services/published_history.py` and `apps/api/app/routers/performance_history.py`; wire `app/main.py`, generic `routers/delivery.py` and legacy `routers/article_handoff.py` through one owner-validated atomic receipt/history gate. Receipt-less reconciliation is not publication; add explicit POST /published-content/confirm-reconciled and Historical Recovery UI action requiring human attestation, resolved unknowns, exact Candidate/hash and atomic idempotent Receipt/history/events, without changing remote/Target/Attempt state. Add truthful coverage and namespaced snapshot/interval metrics with effective corrections.
4. /// Learning and Memory: create learning service/router modules in `apps/api/app/{services,routers}/`; enforce reference ownership, immutable Insights, serialized candidate/evidence transitions and accepted evidence snapshots. All Memory write paths use the same validation gate; explicit promotion is idempotent and revision saves conflict with 409.
5. /// Projections and UI: integrate `services/home_projection.py`, `apps/web/src/product/IdentityWorkspace.tsx`, `App.tsx` and a lazy LearningWorkspace. Four URL-addressable subviews use bounded APIs with missing/unknown displays; no heavy editor import or automatic configuration mutation. Extend existing `apps/web/scripts/check-bundle.mjs` route checks.
6. /// Verification and handoff: implement targeted regressions defined in tasks once authorized; run full backend, TypeScript/Vite/bundle, strict, diff-check and isolated browser Studio/external flows. Update README/task_plan/progress/findings with real output and request independent review. Canonical sync/archive and local commit require the later explicit authorization recorded in tasks; no push/merge/deploy/production migration.

## Acceptance focus

- Known publication ≠ known publication date; failed/unknown/package-only deliveries cannot become published records.
- Latest cumulative 150 after 100 is 150, not 250; incompatible units/windows remain separate.
- Accepted evidence and historical Memory remain immutable; direct Memory APIs cannot bypass validation.
- Concurrent validation/promotion/revisions are atomic and deterministic, never partial success.
- Home learning validation follows operational decisions; stable Identity/default Workflow/channel data do not change.
