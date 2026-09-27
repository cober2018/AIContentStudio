# Evidence-bound article handoff implementation plan

> Based on `openspec/changes/add-evidence-bound-article-handoff/`. M1 is local package generation plus manual delivery receipt for WeChat and X Thread; no remote publishing API.

## Scope

- Preserve existing Topic/FactPack/Draft/Review/ContentAsset objects where they already own the lifecycle.
- Add typed, immutable evidence snapshots and legacy-untyped compatibility.
- Add MotherRevision lineage, candidate hash/readiness, ordered draft media, and separate DeliveryTarget authorization.
- Generate public-safe WeChat and X Thread packages; record manual receipts and minimal feedback.
- Guard legacy workflow resume/retry/direct external boundaries for new M1 records.
- Do not add automatic WeChat drafts, X API publishing, scheduling, new channels, or test files.

## Implementation batches

1. **Domain, persistence, and X Thread shape** — extend `apps/api/app/models.py`, `apps/api/app/schemas.py`, `apps/api/app/routers/topics.py`, `apps/api/app/services/generation/orchestrator.py`, `apps/api/app/services/workflow_templates.py`, and `apps/web/src/pages/Workspace.tsx` for the M1 X Thread form only; add enums, constraints, serializers, and one additive Alembic migration. Preserve existing rows and mark old evidence `legacy_untyped`; do not expand to other platforms.
2. **Evidence authority** — implement one snapshot normalizer/reader/validator, then migrate the concrete bypasses in `apps/api/app/routers/fact_packs.py`, `apps/api/app/services/generation/orchestrator.py`, `apps/api/app/routers/generate.py`, `apps/api/app/services/exports.py`, and package readers. Update freeze/clone paths so new packs use immutable snapshots while legacy packs remain readable but ineligible for new M1 approval.
3. **Mother lineage and derived invalidation** — add MotherRevision import/revision, explicit Draft bindings, canonical input hashes, and stale propagation for structured content, citations, checks, renders, and package manifests.
4. **Draft media and candidate approval** — introduce draft-scoped, content-addressed media around the existing `apps/api/app/models.py` AssetMedia shape and `apps/api/app/routers/assets.py`; upload/order/rights-check media before approval, compute an immutable candidate manifest, then create the approved ContentAsset reference. Protect approved bytes and never let legacy asset upload/delete mutate an approved candidate.
5. **Close remote side effects before handoff** — audit and guard `apps/api/app/services/workflow_templates.py` `publish_wechat`, `apps/api/app/services/workflow_engine.py` publish/resume/retry/direct-call boundaries, and `apps/web/src/pages/Workflows.tsx`. New M1 paths can produce only local packages; no `wewrite` call, no remote draft, no automatic retry. Package generation must not call `apps/api/app/services/storage_service.py` object-storage export.
6. **Manual handoff and state semantics** — add idempotent WeChat/X Thread targets, local public-safe package download, independent target state, reconciliation/receipt/feedback records, and audit events. Use `approved → target_authorized → package_ready → awaiting_manual_receipt → human_confirmed / reconciliation_needed`; `human_confirmed` is never `published` or platform-verified.
7. **UI integration** — update `apps/web/src/pages/Topics.tsx`, `Workspace.tsx`, `Review.tsx`, `Assets.tsx`, `Workflows.tsx`, `apps/web/src/App.tsx`, and `apps/web/src/api.ts` for mother import, evidence/revision status, X Thread boundaries, media/order, candidate readiness, separate authorization, local package download, receipt, and feedback. Keep each target independent.
8. **Verification and docs** — migrate the supported local database, run existing backend/frontend checks, exercise one local sample without remote calls or object-storage export, verify legacy/duplicate/stale/account-change/unknown-result cases, update README and tracking files, validate OpenSpec, then request final ChatGPT review before archive.

## File strategy

- Inspect and modify existing model/router/service/page files first; add only narrowly scoped modules where ownership is absent.
- Add one migration under `apps/api/alembic/versions/`; do not synthesize new approval or delivery state for historical rows.
- Keep the real external boundary fail-closed before exposing any new M1 handoff UI.
- Do not overwrite unrelated dirty files or stage/push changes.
- Mark OpenSpec tasks complete immediately after each verified batch; do not archive until all acceptance gates pass.

## Validation commands

- `openspec validate add-evidence-bound-article-handoff --strict --no-interactive`
- existing backend checks and frontend type/build checks from README/Makefile
- scoped diff/format checks and a local end-to-end manual-package exercise
- explicit confirmation that no remote platform call was made during the M1 exercise
