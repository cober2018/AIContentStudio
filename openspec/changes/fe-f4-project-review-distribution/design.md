## Context

Existing facts:
- `Draft` + checks/media rights are editable production output.
- `build_manifest_v2()` freezes content/media/checks/discoverability/render/workflow execution and hashes canonical JSON.
- `reviews.approve()` currently freezes and approves in one operation.
- `ContentAsset` stores approved immutable content/manifest/hash.
- `Review` stores decision/candidate hash but is draft-first.
- `DeliveryTarget` already stores exact candidate hash, account/channel/action, authorization metadata and capability snapshot.
- `DeliveryAttempt` already enforces prepared→commit→remote→result and unknown requires reconciliation.
- legacy `review_center.py` is Topic-centric and already correctly avoids a ReviewCenter table.

### Apply prerequisite

Before business-code apply, the current workspace MUST expose the archived/canonical FE-F3B implementation/specs. If connector code is still pre-FE-F3B, stop apply and reconcile the workspace first.

Verified for spec review: the primary connector workspace is `1fa4520` and does not contain FE-F3B. This change is prepared in an isolated worktree based on FE-F3B commit `55eba02`; that does not by itself satisfy the connector/apply workspace gate. No business-code apply is authorized by this spec review.

## Goals / Non-Goals

**Goals:** one Project/Unit review projection over existing facts; separate freeze, approval, and delivery authorization; immutable v3 provenance; same ownership boundary on scoped and legacy raw-ID access; backwards-readable legacy Topic flows.

**Non-Goals:** new ReviewCenter/Candidate/DeliveryAuthorization state tables, new publisher/provider, synthetic legacy lineage, learning or Opportunity work, production deployment or migration. An output without a supported content/render adapter remains blocked rather than receiving a fabricated Candidate.

## Decisions

### 1. Review Center remains a projection

No `ProjectReviewCenter`, `ReviewQueueItem` or duplicate state table. Derive from Project/Unit/IdentitySnapshot/ProjectWorkflowOutput/Draft/Checks/ContentAsset/Review/DeliveryTarget/Attempt/Receipt.

### 2. Reuse ContentAsset as frozen Candidate

Evolve additively for project-native provenance:
- `project_id` nullable/indexed
- `content_unit_id` nullable/indexed
- `identity_snapshot_id` nullable
- `workflow_run_id` nullable
- `candidate_hash` for the canonical frozen manifest hash, distinct from nullable `approved_candidate_hash` until a candidate-bound approval exists; legacy approved rows read from `approved_candidate_hash`
- lifecycle state `frozen` vs `approved` on ContentAsset is a compatibility marker; candidate-bound Review remains the approval decision record
- relax legacy-only `topic_brief_id`, `draft_id`, `approved_revision`, and text/fact fields only where project-native source content has no authentic value; never insert invented TopicBrief/Draft IDs or placeholder fact versions to satisfy old constraints

Candidate body/media/manifest/hash are immutable after freeze. Approval changes approval metadata only.

Current code has non-null `ContentAsset.draft_id`, `topic_brief_id`, `fact_pack_id/version`, `approved_revision`, `channel`, `title`, and `final_body`. FE-F4 migration/service must explicitly distinguish real Draft-backed project sources from non-Draft workflow outputs. A first-class source adapter must yield actual content, render, checks, evidence, and lineage for each supported shape. Unsupported output kinds, including media-only output with no publishable composition, fail with a typed blocker. The `ProjectWorkflowOutput` row and producing `WorkflowRun.content_unit_id` must both match the requested Unit; a caller-supplied raw Draft/output ID is insufficient.

### 3. Candidate manifest schema v3

Legacy v1/v2 remain readable. Project v3 freezes:
- project_id / unit_id
- modality/channel/content_form
- IdentitySnapshot ID/checksum
- Project Fact Boundary / FactPack ID/version/checksum
- exact Draft/content revision
- visible title/body/document/structured/timeline data
- media revision IDs, hashes, order, placement, rights snapshot
- citations/declarations
- current deterministic checks + input hashes
- discoverability where required
- renderer key/version/payload/hash
- workflow run ID/key/version/checksum
- plugin/tool execution snapshot
- model/provider/instruction metadata where available
- candidate input/revision hashes

Reuse v2 helpers rather than fork media/check/render/execution logic.

Freeze computes `candidate_hash` over canonical v3 JSON. Repeating a freeze with the same Unit, source revision, and input hashes returns the existing Candidate without a duplicate event; changed inputs create a new immutable Candidate and leave the earlier one readable. If current Unit and producing Run both have identity snapshots, their IDs must agree; v3 records that exact snapshot checksum. A missing or mismatched snapshot blocks v3 freeze rather than substituting the latest identity. Legacy v1/v2 rows remain readable without guessed project links.

### 4. Freeze Candidate and Content Approval are separate

Flow:
`Resolve Blocker → Freeze Candidate → Content Approval → Delivery Authorization → Delivery`

Freeze Candidate:
- project/unit authorized
- server verifies Draft/output belongs to requested unit through persisted lineage
- runs required readiness gates
- builds v3 manifest/hash
- creates immutable candidate ContentAsset
- records `candidate.frozen`
- creates neither approval nor delivery target

Content Approval:
- exact candidate ID + hash
- verifies immutable hash and live invalidators (rights/evidence revocation as applicable)
- creates Review decision bound to candidate
- records `content.approved`
- does not authorize account/delivery

### 5. Review becomes candidate-bound for project flow

Add nullable `content_asset_id` (candidate binding) to Review. FE-F4 project approvals require it. Legacy Review rows may remain draft-only.

`Review.draft_id` and `revision_no` are currently non-null. They must become nullable for a project Candidate without an authentic Draft; a Draft-backed project approval may retain the real values. Project approval requires exact Candidate ID/hash, current rights/evidence/integrity checks, and one transactional Review decision + approval compatibility metadata + ProjectEvent. Changes-requested records another decision without modifying Candidate body/manifest. Legacy `/reviews/drafts/{id}/approve` keeps its existing freeze-and-approve semantics for Topic-only assets; it must not be a bypass for project-bound candidates.

### 6. DeliveryTarget is Delivery Authorization

Do not create another authorization table. Creating a DeliveryTarget is the explicit account/channel/action authorization for an approved exact candidate hash. Project flow rejects authorization before Content Approval.

Existing `manual_handoff` package routes delegate to `article_handoff`, whose v1 builder requires `ContentAsset.draft_id` and v1 `DraftMedia` IDs. For a project v3 Candidate, `manual_handoff` and `copy_package` MUST use a schema-aware v3 package adapter over the frozen manifest/render payload and real MaterialRevision/DraftMedia bytes; it must verify candidate hash, live rights/evidence, actual bytes, and Project ownership before returning a package. It makes no remote call and remains awaiting an explicit receipt. The old article-handoff builder stays only for genuine v1 assets. An unsupported v3 render/media shape returns a typed blocker; it must not fall back to the v1 builder or claim package-ready.

### 7. FE-F3B ContentAccount integration

When FE-F3B exists, add nullable `content_account_id` to DeliveryTarget. New project authorization validates ownership/channel compatibility and also stores historical `account_ref`. Later account edits do not rewrite existing target.

The existing unique constraint keys on `account_ref` but not ContentAccount ID. Replace it with a non-null, immutable `authorization_account_key` in the unique tuple: `content-account:<id>` for project targets with a stable account link, `legacy-ref:<account_ref>` for legacy targets. Backfill this key from actual legacy `account_ref` only; never invent a ContentAccount link. This preserves two distinct ContentAccounts even if their historical `account_ref` strings match. Idempotency lookup and integrity-error readback must use the same tuple/key as the database constraint; a changed account_ref for the same account requires a new explicit authorization version rather than silently rewriting the old target.

`ContentAccount` currently stores Persona, name, and status, not a platform channel, credential, or verified publisher profile. Validate ownership through Persona/Project hierarchy and active state. Validate channel or automatic publisher capability only against an explicit verified account/connection mapping if one exists; do not infer it from the account name or treat `content_account_id` as a remote credential. If unavailable, manual/copy-package authorization may retain an explicit `account_ref` and unverified capability label, while automatic action fails closed. Existing targets with only `account_ref` remain historical and valid under legacy rules.

### 8. Close raw-ID bypasses

Project-bound candidate/delivery rows reachable via legacy raw ID routes receive the same persisted project ownership check before serialization or mutation.

Centralize authorization before any raw Candidate/Asset, Review, DeliveryTarget, Attempt, Receipt, package, feedback, or reconciliation endpoint serializes or mutates project-bound rows, including `/assets/{id}/delivery-targets`, `/delivery-targets/{id}/...`, article-handoff aliases, and Topic-centric read models. Current `_own_target` checks `authorized_by` email but not Project owner; this is insufficient for project-bound resources. Preserve authorized reads of archived history, but disallow new freeze/approve/authorize/deliver/retry on archived Project/Unit. Return a non-disclosing denial for cross-owner raw IDs.

### 9. Derived Review status

Expose structured readiness dimensions: content, evidence, identity, media, checks, candidate, approval, delivery.

Summary states for filters:
- blocked
- stale
- waiting_review
- ready
- approved
- delivery_ready
- unknown
- delivered

Suggested precedence: unknown/reconciliation > blocker/live revocation > stale > waiting review > approved/not-authorized > authorized > delivered. Never persist this projection as a second status truth.

Apply precedence only to the selected/current Candidate and its DeliveryTargets; historical delivered or unknown targets remain in history but must not override the current Candidate's status. A current Candidate with several targets remains unknown while any target has unresolved unknown. An explicitly reconciled outcome may change the projection, but reconciliation itself never makes a second remote call. Overview and `/review` must share the same derivation service rather than implement competing precedence lists.

### 10. Semantics

Blocked = deterministic blocker, invalid evidence/rights/required-media gate.
Stale = upstream editable input/check is no longer current.
Unknown = external side effect cannot be confirmed; must reconcile; no automatic retry.

### 11. Project review APIs

Recommended router: `routers/project_review.py`.

Read:
- `GET /review-center/projects`
- `GET /review-center/projects/{project_id}`
- `GET /review-center/projects/{project_id}/units/{unit_id}`
- `GET /review-center/projects/{project_id}/units/{unit_id}/candidates`
- `GET /review-center/projects/{project_id}/units/{unit_id}/candidates/{candidate_id}`
- `GET /review-center/projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/diff`

Actions:
- `POST /content-projects/{project_id}/units/{unit_id}/candidates/freeze`
- `POST /content-projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/approve`
- `POST /content-projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/request-changes`
- `POST /content-projects/{project_id}/units/{unit_id}/candidates/{candidate_id}/delivery-authorizations`

Execution/package/receipt/reconcile reuse existing Delivery Router endpoints with shared project authorization.

### 12. Candidate diff is read-only projection

No diff table. Compare immutable manifests: content/media/evidence/identity/workflow/check/render/channel metadata; return structured changed sections plus bounded text-diff metadata.

### 13. Frontend

Replace `/review` placeholder with:
- ProjectReviewCenterPage
- project list/grouping
- ContentUnit list/status filters
- ReviewUnitWorkspace
- Candidate Preview / Changes / Checks / Publish tabs
- Freeze Candidate action
- separate Content Approval action
- Delivery Authorization panel
- DeliveryAttempt timeline
- Reconciliation panel

Aux filters: 待我处理 / Ready / Blocked / Unknown / Approved.

Unknown UI must expose reconciliation and MUST NOT show generic retry.

### 14. FE-F3A integration

Add ProjectEvent codes: candidate.frozen, content.approved, content.changes_requested, delivery.authorized, delivery.succeeded, delivery.failed, delivery.unknown, delivery.reconciled, delivery.receipt_recorded.

Versions aggregates candidates/approvals/delivery facts from real entities. Overview adds pending approval/authorization/reconciliation decisions; Unknown outranks generic ready/approved.

### 15. Identity integration

Candidate v3 freezes FE-F3B IdentitySnapshot ID/checksum. Approval and delivery never resolve latest identity in place of frozen snapshot. Legacy candidate with no snapshot displays legacy/unknown identity.

### 16. Migration

Additive migration after actual FE-F3B head. Likely alters ContentAsset, Review, DeliveryTarget only. Do not rewrite manifest v1/v2 or fabricate project/unit/identity links for legacy rows.

Migration head is `f3b000000001` in the verified worktree. Extend ContentAsset with nullable project/unit/snapshot/run links and `candidate_hash`; relax legacy-only non-null columns for project-native candidates without an authentic Topic/Draft; extend Review with nullable `content_asset_id` and relax `draft_id/revision_no` where candidate-bound; add nullable `DeliveryTarget.content_account_id` and non-null `authorization_account_key`, backfill the latter from authentic legacy account_ref, and replace the old account_ref-only uniqueness constraint with the identity-key tuple. Preserve legacy constraints where feasible via source-specific checks/service gates. Test SQLite upgrade→downgrade→upgrade with representative legacy approved asset/review/target/run and verify v1/v2 hashes, approval, receipts, attempts, and authorization idempotency read unchanged; test two distinct ContentAccounts sharing account_ref. Do not run the migration against production during FE-F4 apply.

## Risks / Trade-offs

- Relaxing old non-null columns can admit incomplete records → require source-specific server validation and migration tests; reject unsupported project output at freeze.
- A frozen Candidate can become unsafe to publish due to later rights/evidence revocation → revalidate live invalidators at approval, authorization, and pre-remote delivery without rewriting the frozen manifest.
- New raw-ID access paths may bypass Project ownership → one shared project-bound resource helper, covering legacy aliases before serialization and mutation.
- Multiple Candidates/targets can make one status ambiguous → derive the current Candidate first, then target-level status with explicit precedence and preserve historical rows separately.
- A v3 Candidate may lack Draft-backed media expected by legacy manual handoff → route v3 packages through a manifest-based adapter with real byte checks, retaining v1 behavior only for true v1 assets.
- Two ContentAccounts may share `account_ref` → use stable authorization-account identity in the unique key, not display/reference text alone.

## Open Questions Before Apply

- Enumerate the FE-F2 output kinds with an actually renderable content adapter for text, graphic, and video. Each unsupported kind must return a typed blocker; no demo/mock success.
- Specify the verified account-to-channel/remote-profile mapping, if any. Until present, `ContentAccount` is a stable identity reference, not a verified publisher connection.

### 17. Required tests

- cross-owner project review denial
- raw candidate/delivery bypass denial
- freeze separate from approval
- immutable v3 hash/provenance
- exact IdentitySnapshot/evidence/workflow freeze
- stale/blocker/media-rights freeze denial
- approval binds exact candidate hash
- old candidate remains after new Draft/new Candidate
- authorization denied before approval
- ContentAccount ownership/channel validation
- target idempotency
- unknown never auto-retries
- reconciliation without second remote action
- deterministic summary precedence
- candidate diff content/media/evidence/identity/workflow
- legacy Topic review remains green
- FE-F2/F3A/F3B regressions green
