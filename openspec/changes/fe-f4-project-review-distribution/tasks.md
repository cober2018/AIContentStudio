## 0. Prerequisite
- [x] 0.1 Verify archived/canonical FE-F3B implementation/specs are visible in the primary local apply workspace, not only an isolated spec-review worktree; connector readback remains unverified and business-code apply still needs explicit approval.
- [x] 0.2 Branch from actual FE-F3B commit `55eba02` for spec review; preserve user source artifacts.
- [x] 0.3 Record baseline tests/build/OpenSpec/Alembic head: isolated SQLite backend 310 passed, frontend build passed, 14 canonical specs strict passed, head `f3b000000001`.

## 1. Candidate compatibility
- [ ] 1.1 Extend ContentAsset additively for project/unit/identity/run provenance, distinct frozen `candidate_hash`, and authentic project-source fields; relax legacy-only Topic/Draft/approval non-null columns where needed.
- [ ] 1.2 Extend Review with nullable Candidate/ContentAsset binding and nullable Draft/revision references for project-native candidates; retain legacy draft-bound rows.
- [ ] 1.3 Add nullable ContentAccount link and immutable authorization-account identity key to DeliveryTarget; replace account_ref-only uniqueness and align idempotency lookup/concurrent readback.
- [ ] 1.4 Add reversible migration from actual FE-F3B head; prove legacy v1/v2 approved asset, Review, target, receipt, and Attempt survive upgrade→downgrade→upgrade with no fabricated links.

## 2. Candidate v3 / Freeze
- [ ] 2.1 Build manifest v3 reusing v2 helpers.
- [ ] 2.2 Freeze Project/Unit/Identity/Evidence/Workflow/Content/Media/Checks/Render provenance.
- [ ] 2.3 Enumerate supported Draft/workflow-output source adapters; verify output, Run, and Unit lineage plus renderability; return typed blocker for unsupported source without fake Candidate.
- [ ] 2.4 Add idempotent Freeze endpoint separate from approval; persist frozen hash, Candidate, and ProjectEvent atomically, preserving older Candidates.

## 3. Candidate-bound approval
- [ ] 3.1 Candidate list/detail/history APIs.
- [ ] 3.2 Separate Content Approval action for exact Candidate ID/hash with live rights/evidence/integrity checks and transactional Review + ProjectEvent.
- [ ] 3.3 Request-changes without mutating Candidate.
- [ ] 3.4 Preserve legacy Topic approval route while preventing it from approving project candidates through raw Draft ID.

## 4. Project Review read models
- [ ] 4.1 Project summaries and unit review detail.
- [ ] 4.2 Structured readiness dimensions and deterministic summary precedence scoped to current Candidate and its targets; share one projection with Project Overview.
- [ ] 4.3 Candidate diff projection.
- [ ] 4.4 Close cross-owner/raw-ID disclosure and mutation across Candidate, Review, Asset, target, Attempt, Receipt, package, article-handoff aliases, and legacy Topic read models.

## 5. Delivery Authorization
- [ ] 5.1 Require approval before DeliveryTarget authorization.
- [ ] 5.2 Validate active ContentAccount ownership/hierarchy; require explicit verified channel/publisher mapping for automatic action rather than infer capability from account name.
- [ ] 5.3 Preserve account_ref/capability history; prove two ContentAccounts with the same account_ref remain distinct authorizations.
- [ ] 5.4 Route project v3 manual_handoff/copy_package through a manifest-based package adapter with real bytes/rights checks; retain v1 article-handoff only for genuine v1 assets, and guard all package/execute/receipt/reconcile routes with shared project authorization.
- [ ] 5.5 Preserve unknown no-auto-retry semantics.

## 6. Project integration
- [ ] 6.1 ProjectEvent candidate/review/delivery codes.
- [ ] 6.2 Versions Candidate/Approval/Delivery aggregation.
- [ ] 6.3 Overview approval/authorization/reconciliation decisions.

## 7. Frontend
- [ ] 7.1 Replace `/review` placeholder.
- [ ] 7.2 Project grouping + status filters.
- [ ] 7.3 Preview / Changes / Checks / Publish tabs.
- [ ] 7.4 Separate Freeze / Approve / Authorize controls.
- [ ] 7.5 Delivery attempt/receipt/reconciliation UI.
- [ ] 7.6 Unknown has no generic retry.
- [ ] 7.7 Preserve legacy `/review-publish`.

## 8. Regression
- [ ] 8.1 cross-owner + raw-ID bypass
- [ ] 8.2 freeze separate from approval
- [ ] 8.3 manifest v3 hash/provenance/IdentitySnapshot
- [ ] 8.4 stale/blocker/rights gates
- [ ] 8.5 approval exact hash
- [ ] 8.6 new Candidate leaves old readable
- [ ] 8.7 authorization only after approval
- [ ] 8.8 account validation + target idempotency
- [ ] 8.9 unknown/reconcile no second action
- [ ] 8.10 deterministic projection + diff
- [ ] 8.11 legacy ReviewPublish + FE-F2/F3A/F3B green
- [ ] 8.12 non-Draft/project output without supported render adapter blocks freeze; no invented TopicBrief/Draft/FactPack IDs
- [ ] 8.13 legacy raw Candidate/Asset/target/receipt/package routes enforce project ownership before read or write
- [ ] 8.14 newer Candidate does not inherit older delivered/unknown summary; archived project/unit history read-only
- [ ] 8.15 freeze idempotency, transactional events, and concurrent DeliveryTarget idempotency
- [ ] 8.16 non-Draft v3 manual package/ZIP contains real approved bytes and receipt path without v1 Draft IDs or remote call
- [ ] 8.17 same account_ref with distinct ContentAccount IDs creates distinct targets, while same account ID/version remains idempotent

## 9. Acceptance
- [ ] 9.1 full backend suite
- [ ] 9.2 frontend build
- [ ] 9.3 OpenSpec strict + git diff --check
- [ ] 9.4 isolated Project→Freeze→Approve→Authorize→Delivery/Receipt flow
- [ ] 9.5 Blocked/Stale/Unknown browser paths
- [ ] 9.6 independent review before archive/commit
