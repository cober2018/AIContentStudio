## 0. Prerequisite reconciliation and baseline

- [x] 0.1 Verify FE-F5C is archived and `system-assets-knowledge` + `product-settings` are canonical.
- [x] 0.2 Verify actual final post-F5C `main` commit and Alembic head through the connector. If still on pre-archive `main@ac6d4dc`, STOP before business-code apply.
- [x] 0.3 Create dedicated `codex/fe-f6a-production-core-content-master` from the reconciled baseline.
- [x] 0.4 Preserve all user-provided untracked source/spec packages unchanged and exclude them from commits.
- [x] 0.5 Record backend full-suite baseline, frontend build/bundle budgets, OpenSpec all-strict, Ruff and diff-check.
- [ ] 0.6 No push, merge, deploy, production migration or remote publisher changes.

## 1. Additive production-core persistence

- [x] 1.1 Add ContentMasterRevision model with immutable revision/context/payload fields and unit-scoped optimistic-concurrency constraints.
- [x] 1.2 Add ContentMasterAssetRef with exact MaterialRevision/hash/role/order/placement/rights snapshot.
- [x] 1.3 Add ContentMasterEvidenceRef with exact FactPackItem/snapshot checksum/content locator.
- [x] 1.4 Add ContentMasterCheckRun append-only model.
- [x] 1.5 Add nullable ContentAsset.content_master_revision_id FK/index.
- [x] 1.6 Make ContentAsset.final_body nullable only if actual current schema requires it for non-text v4; preserve v1-v3 behavior.
- [x] 1.7 Add ArtifactKind.video without changing historical artifact_kind values.
- [x] 1.8 Create additive reversible migration after actual post-F5C head; no Draft/MotherRevision/Candidate backfill.
- [ ] 1.9 Validate isolated SQLite upgrade/rollback/upgrade and PostgreSQL-compatible DDL/constraints.

## 2. Master revision service and authorization

- [x] 2.1 Add project/unit authorization helpers for Master reads/writes using existing ContentProject boundaries.
- [x] 2.2 Implement list/current/detail read APIs.
- [x] 2.3 Implement explicit append-only save with expected_revision + idempotency key.
- [x] 2.4 Server-resolve current IdentitySnapshot, latest Brief and current Fact Boundary; never trust client-supplied foreign context IDs.
- [x] 2.5 Allow incomplete drafting context but project typed readiness blockers.
- [x] 2.6 Enforce parent revision same unit and payload modality matches ContentUnit.
- [x] 2.7 Validate channel/content-form through Channel Registry when present.
- [x] 2.8 Concurrent unique race returns 409 with no partial refs/check rows/events.
- [x] 2.9 Archived Project/Unit remains historical read-only.

## 3. Context hash and staleness

- [x] 3.1 Implement canonical payload hash.
- [x] 3.2 Implement canonical context hash covering identity/brief/boundary/channel/content-form immutable refs/checksums.
- [x] 3.3 Add readiness/staleness projection for identity, Brief, evidence and channel drift.
- [x] 3.4 Historical rows never update when upstream context advances.
- [x] 3.5 Explicit new save under new context creates a new revision even when content payload is unchanged.
- [x] 3.6 New revision never inherits prior checks as current.

## 4. Modality adapter registry

- [ ] 4.1 Add `ProductionModalityAdapter` registry separate from Workflow Plugin and Channel registries.
- [ ] 4.2 Add text adapter for `text.master.v1`.
- [ ] 4.3 Add graphic adapter for `graphic.master.v1` stable envelope.
- [ ] 4.4 Add video adapter for `video.master.v1` stable envelope.
- [ ] 4.5 Expose adapter descriptor/readiness/unavailable reason.
- [ ] 4.6 Empty/structural Graphic/Video Masters may save but cannot freeze Candidate without real render.
- [x] 4.7 No adapter fabricates generated image/video/media.

## 5. Master asset refs

- [x] 5.1 Validate MaterialRevision exists and exact content hash.
- [x] 5.2 Require revision already visible to Project through ProjectMaterialReference or verified ProjectWorkflowOutput.
- [x] 5.3 Reject foreign/raw material IDs without disclosure.
- [x] 5.4 Persist immutable role/slot/order/placement and rights snapshot.
- [x] 5.5 Do not copy bytes.
- [ ] 5.6 Candidate/live gates recheck current revision status/public-use rights instead of trusting only the saved snapshot.

## 6. Master evidence refs

- [x] 6.1 Require current Master Fact Boundary before accepting evidence refs.
- [x] 6.2 Validate FactPackItem belongs to exact boundary FactPack.
- [ ] 6.3 Require frozen item snapshot checksum and supported evidence kind for Candidate-readiness path.
- [x] 6.4 Persist immutable role/locator/order/checksum.
- [x] 6.5 Evidence refs never mutate FactPack or Fact Boundary.
- [ ] 6.6 Live revocation later blocks freeze/approval/package without rewriting history.

## 7. Master checks

- [ ] 7.1 Implement Master check runner/service with canonical input hash.
- [x] 7.2 Add common master_schema check.
- [x] 7.3 Add evidence check.
- [x] 7.4 Add rights check.
- [ ] 7.5 Add render-readiness check through modality adapter.
- [ ] 7.6 Preserve warning/blocker/incomplete/stale semantics.
- [x] 7.7 Add list/current-check read API.
- [x] 7.8 Do not silently treat missing/incomplete check as pass.

## 8. Draft workflow compatibility seed

- [x] 8.1 Add `master-revisions/from-output`.
- [ ] 8.2 Accept only verified same-unit current Draft ProjectWorkflowOutput initially.
- [ ] 8.3 Preserve Draft ID/revision/input hash and WorkflowRun/node/attempt/output provenance.
- [ ] 8.4 Convert Draft document/markdown/structured content into text.master.v1.
- [ ] 8.5 Map only provable MaterialRevision refs into MasterAssetRef.
- [ ] 8.6 Map only provable FactPackItem refs into MasterEvidenceRef.
- [ ] 8.7 Unmappable legacy claims/media become explicit warning/incomplete state rather than invented lineage.
- [ ] 8.8 Foreign/stale Draft output is rejected.

## 9. ProjectWorkflowOutput extension

- [ ] 9.1 Add output kind serialization/support for `content_master_revision`.
- [ ] 9.2 Associate it only when an actual future node emits a persisted same-unit Master ID.
- [ ] 9.3 Do not change existing Draft/Material/Candidate output semantics.
- [ ] 9.4 Raw Master ID from unrelated unit/run is rejected.

## 10. Candidate manifest v4

- [ ] 10.1 Add canonical manifest-v4 builder from exact ContentMasterRevision.
- [ ] 10.2 Freeze Project/Unit/modality/channel/content-form.
- [ ] 10.3 Freeze exact IdentitySnapshot ID/checksum.
- [ ] 10.4 Freeze exact Brief revision ID/checksum.
- [ ] 10.5 Freeze exact Fact Boundary/FactPack ID/version/checksum.
- [ ] 10.6 Freeze Master ID/revision/payload schema/payload hash/context hash/parent.
- [ ] 10.7 Freeze full bounded modality content snapshot required for audit/package.
- [ ] 10.8 Freeze exact asset refs/hash/rights snapshot/order/placement.
- [ ] 10.9 Freeze exact evidence refs/snapshot checksum/locator.
- [ ] 10.10 Freeze current Master checks/input hashes/results.
- [ ] 10.11 Freeze modality render snapshot.
- [ ] 10.12 Freeze origin WorkflowRun/output/node/attempt/edit provenance.
- [ ] 10.13 Include citations/declarations where payload supports them.
- [ ] 10.14 Candidate hash covers every frozen v4 section.
- [ ] 10.15 Canonical hash is deterministic across key ordering.

## 11. Dual-path Candidate freeze

- [x] 11.1 Evolve Freeze input to require exactly one of legacy project_output_id or content_master_revision_id.
- [x] 11.2 Preserve existing v3 Draft freeze behavior.
- [ ] 11.3 Add expected_payload_hash gate for v4.
- [ ] 11.4 Require v4 source is current/latest Master for the unit.
- [ ] 11.5 Reject stale Identity/Brief/Evidence/channel context.
- [ ] 11.6 Require all mandatory Master checks current.
- [ ] 11.7 Require live asset/evidence rights.
- [ ] 11.8 Require real modality render snapshot.
- [ ] 11.9 Repeated identical v4 freeze returns existing Candidate/event exactly once.
- [ ] 11.10 Changed Master revision produces new Candidate and preserves old one.

## 12. ContentAsset compatibility

- [ ] 12.1 Populate content_master_revision_id for v4 only.
- [ ] 12.2 Keep draft_id/topic_brief_id/mother_revision_id null for non-Draft v4.
- [ ] 12.3 Do not fabricate legacy links.
- [ ] 12.4 Text v4 may populate final_body compatibility projection; Graphic/Video need not.
- [ ] 12.5 ArtifactKind.video persists/serializes safely.
- [ ] 12.6 Existing asset serializers and authorization accept null Draft text lineage for v4.

## 13. Approval and live invalidation

- [ ] 13.1 Existing Candidate approval endpoint accepts valid current v4.
- [ ] 13.2 Approval binds exact Candidate hash, never Master row.
- [ ] 13.3 Recheck Master/Candidate integrity.
- [ ] 13.4 Recheck live evidence revocation.
- [ ] 13.5 Recheck live MaterialRevision rights/revocation.
- [ ] 13.6 Changes request preserves frozen Candidate and Master history.
- [ ] 13.7 Old approved Candidate stays historical after new Master/Candidate.

## 14. Review and diff v4

- [x] 14.1 Candidate serialization exposes master_revision_id/schema version.
- [ ] 14.2 Text preview renders bounded markdown/document summary.
- [ ] 14.3 Graphic preview exposes canvas summary + exact render asset.
- [ ] 14.4 Video preview exposes script/shot/timeline summary + exact render asset.
- [ ] 14.5 Diff compares payload/context/assets/evidence/identity/workflow/check/render.
- [ ] 14.6 Text similarity only for text.
- [ ] 14.7 Graphic/Video do not emit fake text similarity.
- [ ] 14.8 v1/v2/v3 Review remains readable.

## 15. V4 local packaging

- [ ] 15.1 Extend copy_package/manual_handoff to manifest v4.
- [ ] 15.2 Text package emits master content projection and exact media.
- [ ] 15.3 Graphic package emits exact final rendered image bytes + manifest.
- [ ] 15.4 Video package emits exact final rendered video bytes + manifest and declared companion assets.
- [ ] 15.5 Verify file hash and current public-use rights at package time.
- [ ] 15.6 V4 unsupported render/package fails closed.
- [ ] 15.7 Never fall back from v4 to v3/v1 package code.
- [ ] 15.8 No new remote publisher action added.

## 16. Project Versions / Overview

- [ ] 16.1 Add ContentMasterRevision to Versions aggregation.
- [ ] 16.2 Include exact payload/context hashes and Identity/Brief/Boundary/Run refs.
- [ ] 16.3 Do not synthesize Master rows for legacy units.
- [ ] 16.4 Overview exposes Master incomplete/stale/check-blocked/render-unready risks.
- [ ] 16.5 Existing review/delivery Unknown precedence remains higher where applicable.
- [ ] 16.6 Next-action links back to the correct Production unit.

## 17. Production Workspace component split

- [ ] 17.1 Extract ProductionWorkspace orchestration from monolithic ProductionDesigner.
- [ ] 17.2 Extract ProductionContextHeader.
- [ ] 17.3 Extract WorkflowMiniCanvas.
- [ ] 17.4 Extract NodeInspector.
- [ ] 17.5 Extract ProductionAssetDrawer.
- [ ] 17.6 Add ContentMasterPanel for current revision/readiness/history/save/check controls.
- [ ] 17.7 Add ModalityWorkspace adapter boundary.
- [ ] 17.8 Add TextStudioShell minimal Master summary/development editor.
- [ ] 17.9 Add GraphicStudioShell minimal Master summary/development editor.
- [ ] 17.10 Add VideoStudioShell minimal Master summary/development editor.
- [ ] 17.11 Workflow design save and Master content save remain separate dirty states/actions.
- [ ] 17.12 Preserve existing run/debug/history/human-node behavior.

## 18. FE-P1 performance

- [ ] 18.1 Production route stays lazy from App shell.
- [ ] 18.2 Do not import legacy Workspace TipTap into common Production core.
- [ ] 18.3 Do not import global XYFlow Workflows page.
- [ ] 18.4 Modality-specific future heavy editors use lazy boundaries where practical.
- [ ] 18.5 Existing `/projects`, `/assets`, `/settings`, `/learning` budgets remain green.
- [ ] 18.6 Record Production initial chunk baseline after refactor.

## 19. Targeted regression tests

- [ ] 19.1 Master authorization / cross-owner denial
- [x] 19.2 append-only expected_revision conflict
- [x] 19.3 idempotent save
- [ ] 19.4 parent same-unit constraint
- [ ] 19.5 exact IdentitySnapshot pin
- [ ] 19.6 exact Brief/Boundary pin
- [ ] 19.7 incomplete context allowed but not freeze-ready
- [ ] 19.8 context stale after upstream changes
- [x] 19.9 project-visible asset requirement
- [ ] 19.10 no asset byte copy
- [ ] 19.11 exact boundary evidence requirement
- [ ] 19.12 check input hash / no carry-forward
- [ ] 19.13 modality payload validation
- [ ] 19.14 graphic/video no fake render
- [ ] 19.15 Draft→Text Master lineage
- [ ] 19.16 foreign/stale Draft output denial
- [ ] 19.17 v4 ContentAsset no fake Draft/MotherRevision
- [x] 19.18 ArtifactKind.video
- [ ] 19.19 manifest v4 hash determinism
- [ ] 19.20 v4 freeze idempotency
- [ ] 19.21 stale Master freeze denial
- [ ] 19.22 rights revocation freeze/approval/package denial
- [ ] 19.23 v3 freeze regression
- [ ] 19.24 v1/v2/v3 read compatibility
- [ ] 19.25 modality-aware Review diff
- [ ] 19.26 v4 text package
- [ ] 19.27 v4 graphic/video render package
- [ ] 19.28 unsupported package closed
- [ ] 19.29 Versions Master aggregation
- [ ] 19.30 Overview stale/readiness
- [ ] 19.31 archive safety
- [ ] 19.32 F2/F3A/F3B/F4/F5 regressions green

## 20. Local/browser acceptance

- [ ] 20.1 Create/save Text Master and reload.
- [ ] 20.2 Create/save Graphic shell Master and reload.
- [ ] 20.3 Create/save Video shell Master and reload.
- [ ] 20.4 Demonstrate stale save 409/reload preservation.
- [ ] 20.5 Advance Brief/Fact Boundary or identity and see old Master stale.
- [ ] 20.6 Seed Text Master from a real Draft ProjectWorkflowOutput.
- [ ] 20.7 Run Master checks.
- [ ] 20.8 Freeze v4 Text Candidate.
- [ ] 20.9 Freeze Graphic/Video only after binding real final render MaterialRevision.
- [ ] 20.10 Review Preview/Changes/Checks for v4.
- [ ] 20.11 Approve and build local package.
- [ ] 20.12 Open historical v3 Candidate unchanged.
- [ ] 20.13 Workflow debugger run/rerun/human completion still works.
- [ ] 20.14 Production component split has no navigation/state regression.

## 21. Final gates and handoff

- [ ] 21.1 Run full backend suite and all targeted F6A tests.
- [ ] 21.2 Run frontend TypeScript/Vite build and FE-P1 bundle checks.
- [ ] 21.3 Run all canonical/active OpenSpec strict validation.
- [ ] 21.4 Run relevant Ruff and git diff --check.
- [ ] 21.5 Run isolated browser acceptance on a migrated temporary DB.
- [ ] 21.6 Independent SPEC review.
- [ ] 21.7 Independent backend/production-core code review.
- [ ] 21.8 Independent frontend/Review/package review.
- [ ] 21.9 Do not archive or sync canonical specs until explicit authorization.
- [ ] 21.10 Do not push, merge, deploy or run production migration.

## 22. Audited implementation boundaries

- [x] 22.1 Confirm calibrated proposal/apply and targeted test authorization; record real connector freshness and f5c000000001 code head before implementation.
- [ ] 22.2 Prove full post-F5C MODIFIED requirement/scenario retention before archive.
- [ ] 22.3 Authorized identical idempotency replay before expected_revision, changed fingerprint conflict and atomic head/context CAS/locking.
- [ ] 22.4 Include Master/Candidate-only unit history; pinned identity and explicit Fork + Archive, no latest hierarchy repinning.
- [ ] 22.5 Bind verified/manual render to exact inputs with typed MIME/hash/rights and full multi-canvas coverage; unsupported registry combinations unavailable.
- [ ] 22.6 Latest immutable checks/warning dispositions; reject stale/failed/replaced Draft-output attempts with truthful provenance.
- [ ] 22.7 Shared authorization/schema dispatch for legacy APIs; current Master gate at new approval/authorization; unverified v4 publisher denied.
- [ ] 22.8 Payload bounds/embedded reference validation, pagination and safe projections; no arbitrary file paths/URLs.
- [ ] 22.9 Downgrade preflight rejects incompatible history without deletion/fake-body backfill; validate real PG storage constraints.
- [ ] 22.10 After test-code authorization, add regressions for 22.3–22.9 including commit races, render attestation, Master-only delete, latest blocker and legacy denial.
- [ ] 22.11 Verify ready manually authored Master freezes without Draft/Run; retain strict actual lineage checks for v3 and workflow-backed v4.
