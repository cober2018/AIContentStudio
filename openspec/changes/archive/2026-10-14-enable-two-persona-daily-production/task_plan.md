# Two Persona Daily Production Implementation Plan

> **For agentic workers:** Use executing-plans task by task; the root owns the normal browser and formal data mutations. Read-only plan/contract/quality reviewers must not write configuration or dispatch providers.

**Goal:** 两角色正式日常配置补齐，从正常页面生成、接受并持久保存文字、图文、音频，给用户能直接使用的项目。

**Architecture:** 复用现有Persona修订、默认Recipe/Stage、FactPack、Master、素材和renderer；不新增平行内容真源。先备份，根独占正式页面实跑；仅修复阻断该目标的真实缺陷。

**Tech Stack:** FastAPI/SQLite、React/Vite、现有CPA/MiniMax、Chromiumrenderer、现有离线ASR。

## Task 1 — Baseline and backup

**Files:** 当前README/规范；`apps/api/content_studio.db`及既有素材根只读在线备份至ignored `backups/`；私有startup配置只备份不回显；`receipts/preflight.json`只保存安全摘要。

- [x] /// Read normal identities/settings and current launchd/runtime → read exact local DB/media path → snapshot original rows/media/config and archive/code SHAs → create safe receipt and zero-dispatch ledger. SQLite backup API must be used; do not copy a live main DB without its WAL.
- [x] /// Confirm selected routes/limits/voices from existing catalog and normal capability status; no paid smoke before defaults and bounds are explicit.

## Task 1.4 — Confirmed blocking permission control

**Files:** `apps/api/app/routers/fact_packs.py`, `apps/web/src/pages/FactPacks.tsx` only. No schema/new endpoint/new dependency/new persistent tests.

- [x] /// Preserve current two-file hashes → reproduce current missing model-use property/control → return the already persisted model_use_allowed in existing serialization → show a separate permission checkbox and existing PATCH only on draft → existing relevant permission/API/frontend checks and normal-page before/after → independent Python/TypeScript review. Default false, public permission and frozen enforcement remain intact.

## Task 1.5 — Confirmed required-cover control

**Files:** `apps/web/src/product/TextStudioModel.ts`, `apps/web/src/product/TextStudioShell.tsx` only. Existing normal Text and Stage-candidate editor share this component.

- [x] /// Preserve current two-file bytes → confirm insertAsset hardcodes inline while platform requires cover → expose minimal explicit cover action for exact cleared project image, reusing actual image block/ref and existing save → existing model/TS checks → independent review → normal page save/current-QC proof. No platform weakening, implicit rights, schema/API/dependency/new tests.

## Task 2 — Persist daily configuration and inputs

**Files:** 正常页面 `/identities`、`/settings`、`/projects`；产品修订与两个新项目数据；`receipts/configuration.json`和输入边界文档。

- [x] /// Use existing Persona configuration editor/CAS → choose actual voice and existing Text/Graphic default Recipe for each role; Audio persists the chosen voice on Persona and a project Audio Recipe on the accepted Text Unit → save only missing/mismatched settings → reload/new Unit preview resolves intended defaults.
- [x] /// Create technology architecture-opinion and lifestyle explicitly fictional daily projects → enter Brief/source/FactPack through normal pages → freeze valid boundaries → create appropriate text/graphic units; after Text acceptance explicitly select and persist its project Audio Recipe through the existing entry.

## Task 3 — Full fresh Text workflows

**Files:** 新项目正常Production页及真实WorkflowRun/Attempt/Master；安全逐链回执。

- [x] /// For technology nine-stage default Recipe: Preview → execute one stage → inspect real result → explicit acceptance → next stage → final Master/checks → reload.
- [x] /// Repeat the full intended lifestyle default chain using explicit non-current fictional scope; actual evidence guards stay active. Record each real dispatch once, ten-second starts, no Unknown replay.

## Task 4 — Fresh Graphic workflows

**Files:** 现有Graphic Studio/Recipe、素材库、真实render产物与Master。

- [x] /// For each role: derive visual direction/card plan from accepted new text → choose exact material rights and deterministic composition → use at most one real image submission per role if required → render/inspect actual PNGs → explicit accept/save Master → current QC/reload.

## Task 5 — Fresh Audio workflows

**Files:** 项目已有Audio Recipe与媒体任务/素材；真实音频原件和回执。

- [x] /// For each role: accepted article → complete spoken adaptation → voice direction with explicit configured ID → one TTS submission → exact accepted real WAV/rights → existing full audio QC and offline ASR/acoustics → reload accepted result.

## Task 6 — Review, directly usable handoff and local closure

**Files:** 本change成果/安全receipts，必要根README增量；如出现真实源码缺陷，先更新同一spec/tasks，再仅修改确切阻断文件。

- [x] /// Independent read-only source/artifact quality review → correct genuine gaps without hiding semantic unavailable/human limitations → final normal-page links and usage steps.
- [x] /// Compare old rows/rights/media/archives/adjacent code against baseline; verify exact actual call ledger and normal8000/5173 readiness → strict/diff → canonical sync/archive → whitelist local commit and readback. Keep normal work studio available.

## Execution authority

用户直接要求“把两个角色的日常生产配置补齐，从正常页面完整跑通文字、图文和音频流程，确认我可以直接使用，剩下的你全权处理”。这是本change范围内的配置、真实生成、明确采用、质量评审和必要修复授权；既有“先规范”通过本proposal/design/spec/tasks完成，不重复请求已经明确的执行确认。未授权推送/公开发布或无关扩展。
