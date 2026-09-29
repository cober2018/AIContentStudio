# FE-F6C Graphic Production Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the approved North Star Graphic Production Studio on the current F6B production core without fabricating renderer/provider support or rewriting historical Graphic v1 content.

**Architecture:** A server-canonical `graphic.master.v2` document is the only Graphic edit truth. Existing ContentMasterRevision, exact asset/evidence refs, input-bound checks, Candidate v4, Review and local package remain authoritative. The frontend is Graphic-only lazy and keeps Master dirty/save separate from Workflow.

**Tech Stack:** FastAPI, SQLAlchemy, React/TypeScript, existing Vite route splitting and OpenSpec spec-driven workflow. No new business table or migration is planned.

---

## 0. Baseline and artifact gate

**Files:** `openspec/changes/fe-f6c-graphic-production-studio/{proposal,design,tasks}.md`, four delta specs, `progress.md`, `findings.md`, `README.md`.

- [x] /// Confirm local `main@670dd49`, F6B 162/162 and clean tracked files; preserve untracked user source packages.
- [x] /// Run current full backend suite, frontend build/budget, OpenSpec all-strict and diff-check; record actual counts and migration head.
- [x] /// Review normalized F6C requirements against F6A/F6B code and canonical specs; resolve any implementation-breaking contradiction in the active change before business code.

## 1. Backend Graphic document and exact refs

**Files:** Create `apps/api/app/services/graphic_documents.py`; modify `apps/api/app/services/production_modalities.py`, `apps/api/app/services/content_masters.py`, `apps/api/app/routers/content_masters.py`; add bounded F6C regression files under `apps/api/tests/`.

- [x] /// Implement one canonical Graphic v2 payload validator/normalizer for canvas/layer IDs, order, bounds, text runs/styles, geometry, image/chart/shape types and infrastructure-field rejection.
- [x] /// Register a GraphicV2 adapter; keep Graphic v1 and Text/Video dispatch unchanged. Prove same document hashes deterministically.
- [x] /// Validate each layer's exact MaterialRevision against project visibility, kind/hash/bytes/live rights and placement-specific ContentMasterAssetRef; support repeated use without copying bytes.
- [x] /// Validate text-layer evidence locators against the frozen Fact Boundary and make save atomic under current context/CAS/idempotency.
- [x] /// Add explicit current Graphic v1→v2 preview/fork with warnings, conflict rejection and preserved old revision; never loosen generic schema-change protection.

## 2. Backend rendering, checks, Review and provider boundary

**Files:** Modify `apps/api/app/services/production_modalities.py`, `apps/api/app/services/content_masters.py`, `apps/api/app/services/project_review_projection.py`, `apps/api/app/services/production_packages.py`; create focused `graphic_master_checks.py` and `graphic_master_diff.py` if the existing services would otherwise grow unrelated branches. Reuse `apps/api/app/routers/materials.py` and project asset services only through scoped endpoints.

- [x] /// Resolve exact image-classified Channel Profile; reject legacy text-classified forms for direct Graphic freeze and offer dimension/card rules without silently changing payload.
- [x] /// Require one input-bound real render MaterialRevision per canvas in canonical order; retain truthful manual attestation and reject unverified renderer-origin claims.
- [x] /// Make Graphic v2 structure/text-fact/identity/platform checks append-only, input/profile aware and coverage-honest; no fake semantic PASS.
- [x] /// Add structured Graphic diff and frozen Review preview; preserve Candidate v4/Approval/Authorization/local package hashes and ordered image bytes.
- [x] /// Expose project-scoped search/generation/variation/renderer availability and fail closed without a verified capability. Transfer accepted external-result materialization, license/provenance/project attachment and execution/result-response secret redaction with negative tests to F7 without claiming it done in F6C.
- [x] /// Run targeted backend regressions and full suite before frontend work; block on changed v1/Text/Video behavior.

### Current checkpoint: exact Graphic profile and check gate

**Files:** `apps/api/app/services/content_harness/channel_registry.py`, `apps/api/app/services/production_modalities.py`, `apps/api/app/services/content_masters.py`, new `apps/api/app/services/graphic_master_checks.py`, `apps/api/tests/test_f6c_graphic_checks.py`.

- [x] /// Add a failing profile test: only an exact published image-classified form resolves; declared dimensions/card count/cover rules constrain v2 without changing payload; legacy text-classified forms remain unavailable.
- [x] /// Implement the minimal profile projection/validator and rerun the focused test to green; keep absent optional rules absent, not invented.
- [x] /// Add failing check tests for append-only/current input hash, exact profile version freshness, visible text/fact/identity coverage, and provider-unavailable as warning/partial rather than semantic pass.
- [x] /// Implement schema-dispatched Graphic checks in `ContentMasterCheckRun`, rerun focused checks and relevant F6A/F6B regressions.
- [x] /// Freeze one Graphic v2 Candidate through the existing v4 live gate with real per-canvas material bytes, current checks and explicit warning dispositions; inspect manifest/package order and negative rights paths.

## 3. Frontend Graphic Studio

**Files:** Replace `apps/web/src/product/GraphicStudioShell.tsx`; add focused components under `apps/web/src/product/graphic/`; modify only Graphic-facing branches of `apps/web/src/product/{ContentMasterPanel,ModalityWorkspace}.tsx` and the FE-P1 bundle checker if necessary.

- [x] /// Mount typed Graphic v2 state behind the existing Graphic lazy boundary; keep common Production, Text TipTap and Video loads independent.
- [x] /// Implement canvas list/create/duplicate/delete/reorder, stage zoom/selection, bounded text/image/chart/shape layers, exact project asset picker and profile presets.
- [x] /// Show true search/generation/renderer capability states, revision/upgrade/diff/check/render readiness, explicit save, 409 conflict and archived/history read-only UX.
- [x] /// Verify Master/Workflow dirty-state independence, keyboard/accessible controls and all existing FE-P1 route budgets.

### Current frontend checkpoint

- [x] /// From failing model tests, implement bounded stage geometry, text style, media crop/fit/replacement, shapes, layer order/visibility/lock and exact per-canvas final-image binding.
- [x] /// Show the exact published image Profile and user-confirmed presets; legacy text-classified forms remain visibly unavailable.
- [x] /// Run all frontend model tests, TypeScript/Vite and FE-P1 budget after the Graphic-only UI changes.
- [x] /// Bind exact frozen Fact Boundary claims from the Graphic text layer and preview bounded project media only after authenticated byte/hash verification.
- [x] /// Complete isolated browser acceptance for evidence/save/render and real package bytes.

## 4. Isolated end-to-end and final handoff

**Files:** `openspec/changes/fe-f6c-graphic-production-studio/tasks.md`, `progress.md`, `findings.md`, `README.md`.

- [ ] /// On isolated data, prove multi-canvas save/reload, exact image/chart refs, text/evidence changes, stale render, wrong-order/rights failures and explicit v1 upgrade.
- [x] /// In a real browser, pass Graphic v2 → checks → exact per-canvas render → Candidate v4 → Review → Approval → local ordered image package; inspect packaged hashes/bytes.
- [ ] /// Re-run full backend, TypeScript/Vite/bundle, OpenSpec all-strict, relevant Ruff, diff-check and independent spec/backend/frontend review; mark only evidenced tasks.
- [x] /// Record limitations and local implementation commit. Do not push/deploy/run production migrations or canonical-sync/archive without separate authorization. Continue master roadmap to F6D only after F6C implementation gates pass.
