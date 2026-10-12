# Persona Creative Studio Multimedia Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the approved unified Image + Audio generation surface for the local single-user Persona Creative Studio.

**Architecture:** Reuse the existing ProviderGenerationTask, model-capability routing, MaterialRevision and Persona creative-profile truths. Add one typed multimedia request/read model and keep Image and Audio adapter-specific validation behind it. Voice presets are local configuration projections; exact provider/model/profile/voice IDs remain the execution truth.

**Tech Stack:** FastAPI/Python services and Pydantic-style contracts, existing SQLite/local media storage, React/TypeScript product panels, existing OpenSpec task and validation tooling.

---

### Task 1: Reconcile the dependent channel-handoff specification

**Files:**
- Modify: `openspec/changes/complete-multiplatform-content-handoff/`
- Verify: `openspec validate --all --strict`

- [ ] Correct stale `stage.variant.propose` references to `stage.variant.adapt@1` without changing business behavior.
- [ ] Preserve the dependent change's explicit test-scope decision and do not apply its business code.

This dependency remains a separately authorized change; this multimedia batch does not edit or apply it.

### Current continuation order

/// 1. Close batch receipt integrity, exact Custom routing and legacy request compatibility.
/// 2. Connect native MiniMax candidates and exact voice configuration to the existing task/Stage acceptance APIs.
/// 3. Complete local catalog search/favorites and normal/Advanced controls without hidden provider calls.
/// 4. Review the patch, run existing focused regressions plus build/strict/diff gates, and record remaining real-provider acceptance separately.

Final closure: /// unify voice-catalog uniqueness validation and reject unconsumed Audio fields → independent UI review → concentrated existing-suite/build/strict checks → update implementation receipt without formal-library/provider writes.

### Task 2: Add the shared multimedia request contract

**Files:**
- Modify: existing media-generation contracts/services under `apps/api/app/services/`
- Modify: existing provider-generation API projection under `apps/api/app/routers/`

- [x] Define typed normalized Image/Audio request and candidate projections.
- [x] Freeze configuration hash, exact binding, candidate index and output provenance.
- [x] Reject unsupported adapter fields and binding drift before creating a generation task.

### Task 3: Complete Image candidate generation and selection

**Files:**
- Modify: existing image provider/task service and media product panel.
- Modify: existing image/material acceptance projection.

- [x] Support bounded candidate count 1–4 with native-batch capability declaration.
- [x] Permit fan-out only for Auto or an explicitly declared Custom Composition.
- [x] Expose candidate selection and keep unselected outputs out of accepted MaterialRevision truth.

### Task 4: Complete Voice Catalog and Audio Advanced Settings

**Files:**
- Modify: existing model capability routing and provider registry services.
- Modify: existing Persona creative configuration and Models & AI UI.

- [x] Add local Voice Catalog/VoicePreset projection with explicit refresh and search/filter/preview metadata.
- [x] Support manual exact cloned Voice ID registration without secrets or ownership ACLs.
- [x] Show simple controls by default and exact provider/model/profile/voice ID plus adapter-supported fields only in Advanced Settings.
- [x] Block unavailable or scope-mismatched exact voices; never silently substitute.

### Task 5: Verify focused existing contracts

**Files:**
- Modify only if an approved contract defect is reproduced.

- [x] Run focused existing multimedia/persona suites and OpenSpec/diff checks.
- [x] Record unresolved real-provider quality, formal initialization and lifecycle work as open rather than fabricating completion.

## Outstanding requested image routes

Scope recount is now139/156 with17open: two omitted user requirements are explicit, not newly completed. The next steps below are specification/implementation boundaries, not an executed adapter plan or a real-call authorization.

/// Inspect exact registered CPA image protocol/model without provider generation → review the versioned protocol contract → implement it through existing generation tasks and immutable candidates → concentrate offline smoke; separately select ChatGPT manual mode → freeze source/prompt/output → copy prompt for the user → drag-upload local images to existing staging → explicit MaterialRevision acceptance.

- [ ] Task6: CPA Gemini/Grok images. Reuse `model_registration.py` configuration and trusted-target rules; implement a versioned image protocol behind the existing media registry rather than loosening the legacy OpenAI image provider. Bind exact provider/model/profile/credential identity and consume every exposed field. Verify through intercepted/local synthetic responses, without real CPA calls, new persistent tests or formal settings writes. Any new protocol/schema choice must be reviewed before business apply.
- [ ] Task7: ChatGPT **manual** images, replacing the earlier browser-Agent path by the latest confirmed human decision. Business apply explicitly authorized on2026-10-08; in progress, with no formal data/configuration mutation or real calls.

**Files:**
- Modify: `apps/web/src/product/ProviderMediaPanel.tsx` — expose `ChatGPT（手动生图）` separately from executable automatic provider bindings, show prompt/copy and manual upload UI.
- Add: `apps/web/src/product/ManualChatGPTImagePanel.tsx` — lazy, scoped manual handoff UI; keep the large existing automatic panel and its native routing untouched.
- Modify/reuse: `apps/web/src/product/CreativeExecutionPanel.tsx` — reuse package/source/output projection and selected human acceptance without building a second result truth.
- Modify/reuse: `apps/api/app/services/creative_packages.py`, `apps/api/app/services/creative_executions.py`, `apps/api/app/routers/creative_orchestration.py` — consume the reviewed manual handoff through existing immutable source/output/staging/rights/CAS services; add only narrowly needed projection/upload wiring, no table/migration.
- Update: this change's docs and existing README/flow/receipt after implementation.

/// Add explicit manual selector → compile full safe prompt without model calls → prepare/freeze existing current-source package → expose one-click copy → user independently generates/downloads on ChatGPT → drag/drop or choose files → immediately enqueue/upload temporary candidates → validate actual bytes/contract → preview/select → explicit 接受入库 → separate Master reference/save.

- [ ] Build the manual selector and complete prompt from accepted visual context, style, usage, ratio/size, requested1–4count and reference/output obligations. No hidden LLM call, browser/session dependency or Auto/provider fallback.
- [ ] Reuse exact current Master/Variant package/source checks and immutable prompt/output contract. Prompt/source/config edits prepare a new package; no in-place frozen edits or fake native success receipt.
- [ ] Add multi-file drop/file-picker handling with immediate temporary upload, per-file pending/uploading/validating/ready/error state, thumbnails, selection/removal and visible bounded errors. Keep valid rows on another file's failure; pending-row removal never deletes accepted material.
- [ ] Server-side MIME/dimensions/bytes/count/hash validation and exact immutable output attempts precede acceptance. Label origin user-declaredChatGPT; never attest an unknown website model/runtime or create forged LLMRun/ProviderGenerationTask receipts.
- [ ] Explicit selected acceptance invokes existing idempotent MaterialRevision/live-derived-rights gates with external_execution source kind. No Master/Variant/Candidate/Approval/publication mutation from upload/accept alone.
- [ ] After apply, run existing relevant regression suites, TypeScript/Vite, FE-P1, strict/diff and concentrated isolated local page/API smoke for copy/drag-upload/selection/accept, invalid/failed upload, stale source, duplicate accept and unchanged Master. No new persistent test code or real-provider/formal writes without separate authorization.

The prior one-request Chrome smoke actually generated one image, but download completion was interrupted and unverified. No replay is scheduled, and that external smoke does not close product task10.12.

Primary inspected CPA evidence: [installed-revision route registration](https://github.com/router-for-me/CLIProxyAPI/blob/fd48ea68/internal/api/server_routes.go) and [image model/protocol handler](https://github.com/router-for-me/CLIProxyAPI/blob/fd48ea68/sdk/api/handlers/openai/openai_images_handlers.go). These expose an image API and model validation; they do not attest the user's configured model/credential can generate images.

## Previous batch implementation receipt

Task count139/154;13.6 remains open because no new persistent tests were authorized for this batch. Native image outputs1–4 are immutable and one selected result is explicitly accepted. VoicePresetPicker is shared by generation/Persona surfaces with all-catalog search and at most100 matching options. Existing audio preview never callsTTS. The independent frontend findings and stale-refresh follow-up are fixed; scopedAPPROVE. Final full backend2479passed/28skipped122.98s, Web/FE-P1, scopedRuff, strict38/38 and six isolated headless gates pass. Gemini/Grok direct-image and ChatGPT website execution remain unimplemented. No migration, formal writes, Provider calls or commit/archive/push.

```text
Image configuration → exact frozen task → immutable candidates1–4
                                         → explicit index/hash selection → MaterialRevision

Voice Catalog → explicit Persona/Account/Series voice configuration
              → exact Stage/request receipt → audio result → explicit MaterialRevision

MaterialRevision → explicit Master reference/save (never automatic)
```
