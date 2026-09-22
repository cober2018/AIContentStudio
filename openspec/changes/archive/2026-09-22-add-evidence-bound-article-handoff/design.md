## Context

The current modular monolith already owns Source, Fact, FactPack, TopicBrief, ContentJob, Draft, Review, ContentAsset, AssetMedia, ExportRecord, AuditLog, and persistent workflow steps. The M1 change must reuse those concepts rather than introduce a second content center. Today, however, freezing a FactPack does not copy the referenced fact values, each platform draft is generated independently, media is attached after a ContentAsset is approved, and export or workflow state is not a reliable record of what a human delivered to which account.

M1 is a narrow vertical slice for an existing satisfactory article. It creates complete WeChat and X Thread packages and records manual handoff, receipt, and feedback. It does not add remote draft creation or publication. Existing records must remain readable, and migration must not invent evidence or approval.

## Goals / Non-Goals

**Goals:**

- Freeze the exact evidence used by an article while preserving the distinction between facts, events, quotations, and author opinions.
- Preserve an imported article as an immutable mother revision and make every platform draft declare the mother revision it adapts.
- Approve the complete deliverable candidate, including actual media and review results, before authorizing a target account and action.
- Produce public WeChat and X Thread packages and record independent manual delivery receipts and feedback.
- Keep legacy data readable while preventing it from silently acquiring new approval or delivery eligibility.

**Non-Goals:**

- WeChat remote draft creation, X API publication, automatic scheduling, or automatic retry of external side effects.
- Channels other than WeChat and X Thread, full editorial locking/comparison, or a general evidence platform.
- Video, digital humans, multi-tenant SaaS, subscriptions, billing, or a replacement workflow engine.
- Rewriting an imported article merely to enter the M1 workflow.

## Decisions

### 1. Extend FactPackItem with a typed immutable snapshot

`FactPackItem` gains an evidence kind and versioned snapshot payload. The allowed kinds are `fact`, `event`, `third_party_quote`, `author_opinion`, and `legacy_untyped`. A fact-backed item may keep `fact_id`; non-fact evidence may omit it. Freeze validation is kind-specific and copies the statement/value/excerpt, attribution, source locator/version, time scope, units, and permission flags needed downstream.

The frozen snapshot, not the live Fact row, is authoritative for generation, checking, preview, and package construction. Clone creates editable copies that freeze into a new snapshot. Existing items migrate to `legacy_untyped`; they remain readable but cannot satisfy a new M1 approval until reviewed and re-frozen. This is preferred to a new generic Evidence table because the existing FactPack is already the content evidence boundary.

### 2. Introduce a small immutable MotherRevision

`MotherRevision` belongs to a TopicBrief and stores `body_markdown`, optional title, source/import metadata, the frozen evidence checksum, a parent revision, and a body hash. Importing a satisfactory article creates the first revision without regenerating it. Editing creates a new revision; old revisions are never overwritten.

`Draft` remains the platform-editable revision and gains an explicit `mother_revision_id` plus `input_hash`. A normal newer mother revision does not silently replace a draft bound to an older revision. Evidence correction, rights revocation, or approval revocation marks affected uncompleted candidates for review.

### 3. Treat Markdown as canonical and invalidate derived artifacts

Mother and platform Markdown are canonical. Structured JSON, X thread boundaries, citation maps, checks, render output, and package manifests record the input hash that produced them. A title/body/thread-order/media change makes dependent artifacts stale. Stale artifacts may remain for history but cannot be approved or newly handed off.

This avoids introducing a second rich-text source of truth while retaining existing Draft revision behavior.

### 4. Add draft-stage media without mutating approved assets

A focused `DraftMedia` relation records content-addressed file identity, order, role, rights/permission metadata, and the draft revision it belongs to. Approval creates an immutable candidate manifest and ContentAsset references/copies that manifest; approved bytes are not overwritten or deleted while referenced. Existing `AssetMedia` remains the approved-asset view.

This is preferred to making one mutable media row alternate between Draft and ContentAsset ownership, because re-parenting would weaken historical approval guarantees.

### 5. Bind content approval to a complete candidate hash

The approval candidate manifest includes final title, canonical body, ordered media hashes, citations, declarations, and current review/check records. `Review` records the candidate hash and completion metadata; `ContentAsset` records the same approved hash. Missing, failed, truncated, or stale semantic review is incomplete rather than passed. A warning requires a recorded disposition; objective factual conflicts, fabricated experience, unsupported objective claims, and misattribution remain blocking.

Any candidate material change creates a new hash and invalidates the prior approval for that candidate. A previously approved immutable version remains historically valid unless its evidence/rights/approval is explicitly revoked.

### 6. Separate target authorization from content approval

`DeliveryTarget` binds one approved ContentAsset hash to product/topic, platform, content form, account reference, action, and authorization version. M1 allows only the manual-handoff action for WeChat and X Thread. Changing the account or action requires new target authorization; changing candidate content also requires new content approval.

The UI may collect both confirmations in one user interaction, but AuditLog entries and stored states remain separate. Each target advances independently so one waiting or failed target does not block another.

### 7. Use deterministic packages and manual receipts

A handoff package is generated from the approved manifest and contains the final public text, actual public media in order, publishable source/attribution statements, declarations, a manifest, and human instructions. Private FactPack payloads, source originals, or media without public rights are excluded.

Creating a target uses a stable uniqueness key so duplicate clicks return the same intent. Receipt updates are idempotent, but the system does not claim exactly-once behavior for human or platform actions. A receipt records operator, time, action, link or evidence, and verification method. Minimal feedback is recorded against the target or topic.

### 8. Guard legacy automatic delivery without expanding it

New M1 records cannot invoke WeChat remote draft creation. Existing workflow entry points, resume paths, retries, and direct calls must reject a new M1 external action unless a separately supported automatic action, approved hash, and matching target authorization exist. This proposal creates no such automatic action, so its new targets remain manual only.

Historical completed workflow records remain readable. The implementation must not label an export or manual receipt as remotely verified publication, and must not upgrade legacy drafts or FactPacks into the new approval state.

## Risks / Trade-offs

- **More states may complicate the current UI** → Show a single guided M1 flow while retaining separate stored approval and authorization records.
- **Legacy automatic workflows may have relied on permissive entry points** → Preserve history, make the new guard explicit in release notes, and do not silently map old runs to new targets.
- **JSON snapshots can drift in shape** → Store an explicit snapshot schema version and normalize it through one service used by freeze, clone, generation, checking, preview, and export.
- **Content-addressed media may leave unused files** → Keep approved references immutable and add only bounded orphan cleanup after reference checks; deletion is not part of the approval transaction.
- **Manual receipt can be inaccurate** → Label its provenance as human-confirmed and never present it as platform-verified.

## Migration Plan

1. Add nullable snapshot/type fields and new tables/relations without changing existing reads.
2. Backfill existing FactPackItem rows as `legacy_untyped`; do not synthesize snapshots or approval.
3. Add dual-read compatibility for legacy displays and typed-snapshot reads for new M1 operations.
4. Add MotherRevision import, draft binding, DraftMedia, complete candidate approval, DeliveryTarget, package, receipt, and feedback APIs/UI.
5. Add guards at actual external-call boundaries and legacy resume/retry entry points before exposing the M1 flow.
6. Validate one existing satisfactory article through independent WeChat and X Thread manual handoff without invoking remote publishing.

Rollback disables new M1 entry points first. New tables/columns remain additive for data preservation; legacy reads continue. No migration downgrade may delete receipt, approval, or evidence history.

## Open Questions

None for proposal approval. Future proposals must separately choose the automatic-delivery channels and reliability contract.
