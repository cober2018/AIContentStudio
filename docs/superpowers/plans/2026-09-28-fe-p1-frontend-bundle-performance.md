# FE-P1 Frontend Bundle Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce the actual initial JavaScript dependency closure for `/projects` while preserving current and legacy route behavior.

**Architecture:** Route modules load through React lazy boundaries. Persistent project list, detail, and production become independent import roots with erased type-only links. A manifest-based check measures entry plus project-list static imports, not all generated chunks.

**Tech Stack:** React 18, React Router 6, TypeScript, Vite 5, Node.js. No new runtime dependency or backend change.

---

### Task 1: Baseline and route contract

**Files:** Read `apps/web/src/App.tsx`, `apps/web/src/product/PersistentProjectPages.tsx`, `apps/web/package.json`; update `progress.md` and `findings.md`.

- [x] /// Run `npm run build` in `apps/web` and record JS/CSS raw and gzip baseline.
- [x] /// Record route table, numeric/demo fallback, and direct-link behavior from the current build.
- [x] /// Confirm isolated FE-P1 branch and clean starting state.

### Task 2: Project module separation

**Files:** Split `apps/web/src/product/PersistentProjectPages.tsx` into `apps/web/src/product/PersistentProjectsPage.tsx`, `apps/web/src/product/PersistentProjectPage.tsx`, `apps/web/src/product/PersistentProductionPage.tsx`, and `apps/web/src/product/project/projectTypes.ts`; update `apps/web/src/product/ProductionDesigner.tsx` and `apps/web/src/product/project/ProjectMatrixTab.tsx` type imports.

- [x] /// Extract only shared types, list, detail, and production wrapper; preserve existing request and UI logic.
- [x] /// Replace runtime cross-imports with `import type` and remove the former combined module only after all consumers move.
- [x] /// Run `npx tsc -b` and inspect imports for production designer or tabs reachable from the list.

### Task 3: Route-level lazy loading and resilience

**Files:** Modify `apps/web/src/App.tsx`; add a small route fallback/error boundary only if it cannot stay focused within `App.tsx`.

- [x] /// Convert page imports to dynamic route imports without changing URL patterns, redirects, or demo dispatch.
- [x] /// Keep sidebar/navigation mounted while a route chunk loads; show an announced loading message.
- [x] /// Show a recoverable chunk-load error and reset it on route change; run TypeScript build.

### Task 4: Measured budget

**Files:** Modify `apps/web/package.json` and possibly `apps/web/vite.config.ts`; create `apps/web/scripts/check-bundle.mjs` after verifying the `scripts` parent directory; do not add `manualChunks` in this cut.

- [x] /// Enable Vite manifest in the normal build and map entry plus persistent project-list chunk.
- [x] /// Traverse static imports only, deduplicate emitted JS, compute raw/gzip sizes, and fail on missing mapping or ≥500,000 raw bytes.
- [x] /// Inspect generated chunk graph, verify TipTap/XYFlow are absent from `/projects` initial closure, and report total generated JS separately.

### Task 5: Acceptance and documentation

**Files:** Update `openspec/changes/fe-p1-frontend-bundle-performance/tasks.md`, `README.md`, `task_plan.md`, `progress.md`, `findings.md`.

- [x] /// Run `npm run build`, bundle budget, OpenSpec strict, and `git diff --check`; record exact outputs.
- [x] /// Smoke direct links/refresh/transitions for landing, project list/detail/production, review, identity, legacy workspace/workflows, and demo fallback; verify loading and recoverable failure.
- [x] /// Mark only verified OpenSpec tasks complete; document any unverified behavior and request review before archive.

**Boundary:** No new automated test code, backend/API change, migration, push, merge, deployment, or production write. Archive only after the change passes acceptance review.
