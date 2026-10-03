# F8 Storage Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the formal single-operator SQLite/local-media deployment use the same persistent MaterialRevision storage lifecycle while keeping generated results private until explicit human acceptance.

**Architecture:** Keep `Material`/`MaterialRevision` as the library truth and `ProjectMaterialReference` as the project projection. Route verified MaterialRevision reads through the existing `StorageProvider`; retain only a documented legacy bridge for historical DraftMedia paths. `ProviderGenerationTask` remains a private staging area and promotes through the existing explicit acceptance transaction.

**Tech Stack:** FastAPI, SQLAlchemy, existing `MaterialStorage` protocol, local filesystem and existing hash/rights gates. MinIO remains a future deployment profile and is not a gate for this plan.

---

### Batch 1: Storage boundary and immutable reads

**Files:**
- Modify: `apps/api/app/services/material_storage.py`
- Modify: `apps/api/app/services/materials.py`
- Modify: `apps/api/app/services/delivery.py`
- Modify: `apps/api/app/services/production_packages.py`
- Modify: `apps/api/app/services/retention.py`
- Modify: `apps/api/app/config.py`
- Modify: `apps/api/app/services/asset_media.py`

- [ ] Add provider-level immutable existence/hash/diagnostic helpers without exposing physical paths.
- [ ] Replace direct MaterialRevision reads in v4/v5 package and delivery paths with `read_bytes_checked`.
- [ ] Keep legacy DraftMedia absolute/local reads behind an explicit development/test compatibility function.
- [ ] Add explicit local storage-root validation; keep future object-storage validation separate without changing the active local database.
- [ ] Run existing storage/material/package/delivery regressions, `git diff --check`, and OpenSpec strict.

### Batch 2: Generation promotion and project visibility

**Files:**
- Modify: `apps/api/app/services/generation_tasks.py`
- Modify: `apps/api/app/services/provider_media.py`
- Modify: `apps/api/app/routers/materials.py`
- Modify: `apps/web/src/product/ProviderMediaPanel.tsx`

- [ ] Verify the result-ready task is private and cannot appear as a formal library item before acceptance.
- [ ] Verify explicit acceptance creates one immutable MaterialRevision and, for project tasks, one project reference.
- [ ] Verify acceptance is idempotent and rights/bytes are rechecked before project visibility.
- [ ] Verify the UI distinguishes private generated result, accepted system asset, and project reference.
