## 0. Prerequisite
- [ ] 0.1 Verify archived/canonical FE-F3B implementation/specs are visible in current workspace; stop apply otherwise.
- [ ] 0.2 Branch from actual FE-F3B commit; preserve user source artifacts.
- [ ] 0.3 Record baseline tests/build/OpenSpec/Alembic head.

## 1. Candidate compatibility
- [ ] 1.1 Extend ContentAsset additively for project/unit/identity/run provenance.
- [ ] 1.2 Extend Review with nullable Candidate/ContentAsset binding.
- [ ] 1.3 Add nullable ContentAccount link to DeliveryTarget when FE-F3B exists.
- [ ] 1.4 Add reversible migration; no fabricated legacy links.

## 2. Candidate v3 / Freeze
- [ ] 2.1 Build manifest v3 reusing v2 helpers.
- [ ] 2.2 Freeze Project/Unit/Identity/Evidence/Workflow/Content/Media/Checks/Render provenance.
- [ ] 2.3 Verify Draft/output lineage to unit.
- [ ] 2.4 Add Freeze endpoint separate from approval.

## 3. Candidate-bound approval
- [ ] 3.1 Candidate list/detail/history APIs.
- [ ] 3.2 Separate Content Approval action exact candidate/hash.
- [ ] 3.3 Request-changes without mutating Candidate.
- [ ] 3.4 Preserve legacy approval route.

## 4. Project Review read models
- [ ] 4.1 Project summaries and unit review detail.
- [ ] 4.2 Structured readiness dimensions and deterministic summary precedence.
- [ ] 4.3 Candidate diff projection.
- [ ] 4.4 Close cross-owner/raw-ID disclosure.

## 5. Delivery Authorization
- [ ] 5.1 Require approval before DeliveryTarget authorization.
- [ ] 5.2 Validate ContentAccount/channel where available.
- [ ] 5.3 Preserve account_ref/capability history.
- [ ] 5.4 Reuse package/execute/receipt/reconcile routes.
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

## 9. Acceptance
- [ ] 9.1 full backend suite
- [ ] 9.2 frontend build
- [ ] 9.3 OpenSpec strict + git diff --check
- [ ] 9.4 isolated Project→Freeze→Approve→Authorize→Delivery/Receipt flow
- [ ] 9.5 Blocked/Stale/Unknown browser paths
- [ ] 9.6 independent review before archive/commit
