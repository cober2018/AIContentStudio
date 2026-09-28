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

## Decisions

### 1. Review Center remains a projection

No `ProjectReviewCenter`, `ReviewQueueItem` or duplicate state table. Derive from Project/Unit/IdentitySnapshot/ProjectWorkflowOutput/Draft/Checks/ContentAsset/Review/DeliveryTarget/Attempt/Receipt.

### 2. Reuse ContentAsset as frozen Candidate

Evolve additively for project-native provenance:
- `project_id` nullable/indexed
- `content_unit_id` nullable/indexed
- `identity_snapshot_id` nullable
- `workflow_run_id` nullable
- lifecycle metadata sufficient for `frozen` vs `approved`
- optional explicit `candidate_hash` only if needed to avoid semantic misuse of `approved_candidate_hash`; preserve read fallback for legacy rows

Candidate body/media/manifest/hash are immutable after freeze. Approval changes approval metadata only.

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

### 6. DeliveryTarget is Delivery Authorization

Do not create another authorization table. Creating a DeliveryTarget is the explicit account/channel/action authorization for an approved exact candidate hash. Project flow rejects authorization before Content Approval.

### 7. FE-F3B ContentAccount integration

When FE-F3B exists, add nullable `content_account_id` to DeliveryTarget. New project authorization validates ownership/channel compatibility and also stores historical `account_ref`. Later account edits do not rewrite existing target.

### 8. Close raw-ID bypasses

Project-bound candidate/delivery rows reachable via legacy raw ID routes receive the same persisted project ownership check before serialization or mutation.

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
