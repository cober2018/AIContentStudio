## 1. Data contract and migration

- [x] 1.1 Add evidence-kind and versioned snapshot fields to FactPackItem, MotherRevision, DraftMedia, candidate/approval metadata, and DeliveryTarget models with database constraints for valid ownership and target uniqueness.
- [x] 1.2 Add an Alembic migration that creates the additive schema, marks existing evidence `legacy_untyped`, preserves existing rows, and does not synthesize new approval or delivery state.
- [x] 1.3 Add request/response schemas and enum serialization for typed evidence, mother revisions, draft media, candidate readiness, target authorization, packages, receipts, and feedback.

## 2. Typed evidence freeze

- [x] 2.1 Implement one versioned evidence-snapshot normalizer/validator for fact, event, third-party quotation, author opinion, and legacy-untyped entries.
- [x] 2.2 Update FactPack freeze and clone paths so new frozen packs store immutable payloads and checksums while legacy packs remain readable but ineligible for new M1 approval.
- [x] 2.3 Update generation, rewriting, checking, preview, approval, and package readers used by M1 to consume frozen snapshots instead of mutable Fact values, and enforce separate public/model-use permissions.

## 3. Mother revision and derived-content lineage

- [x] 3.1 Implement import/read/create-revision operations for MotherRevision so an existing satisfactory article can enter unchanged and later edits append immutable lineage.
- [x] 3.2 Bind WeChat and X Thread Draft revisions to an explicit MotherRevision and snapshot checksum; preserve ordered X post boundaries.
- [x] 3.3 Compute canonical input hashes and mark structured content, citations, checks, renders, and package manifests stale after material text, thread, declaration, or media changes.

## 4. Draft-stage media and complete approval

- [x] 4.1 Implement content-addressed DraftMedia upload/list/order/remove behavior with rights metadata and protection for bytes referenced by approved candidates.
- [x] 4.2 Build an immutable candidate manifest from final title, Markdown, ordered media hashes, citations, declarations, and current checks, with explicit readiness reasons.
- [x] 4.3 Update review approval so incomplete/stale checks or missing final media block approval, recorded warning dispositions remain auditable, and ContentAsset stores the approved candidate hash without implying publication.

## 5. Manual delivery targets and packages

- [x] 5.1 Implement idempotent DeliveryTarget creation and authorization for manual WeChat article and X Thread targets, binding account/action/authorization version to the approved content hash.
- [x] 5.2 Implement deterministic public-safe package construction and download for WeChat and X Thread without invoking remote platform APIs.
- [x] 5.3 Implement independent target states, reconciliation-needed handling, human-confirmed receipt capture, minimal feedback capture, and AuditLog events.
- [x] 5.4 Guard legacy workflow resume/retry/direct external-call boundaries so they cannot grant M1 state or invoke remote delivery for new M1 content without a separately supported automatic action and matching authorization.

## 6. Guided M1 interface

- [x] 6.1 Update the existing Topics flow to import/confirm a mother article, show its evidence classification and immutable revision lineage, and create WeChat/X Thread adaptations.
- [x] 6.2 Update Review and Assets surfaces to show actual ordered media, completeness/staleness, the approved hash, and the distinction between content approval and target authorization.
- [x] 6.3 Add the manual target/package/receipt/feedback flow to the existing content pages, keeping each channel target independently actionable and labeling human confirmation accurately.

## 7. Verification and documentation

- [x] 7.1 Apply migrations in the supported local database path, run existing backend checks and frontend type/build checks, and resolve only regressions caused by this change; do not add test code unless separately requested.
- [x] 7.2 Exercise one existing satisfactory article through typed freeze, unchanged mother import, WeChat/X adaptation, actual-media approval, independent package downloads, manual receipts, and feedback; verify no remote draft/publish call occurs.
- [x] 7.3 Verify legacy reads, duplicate target requests, stale-candidate rejection, account changes, evidence/rights revocation, interrupted/unknown manual outcomes, and one-target-fails/other-target-continues behavior.
- [x] 7.4 Update README, task_plan.md, progress.md, findings.md, and any affected flow diagram with implemented behavior, remaining V1 scope, startup/migration instructions, and evidence-backed acceptance status.
- [x] 7.5 Run strict OpenSpec validation and scoped diff checks, record the final implementation evidence, obtain ChatGPT review, and archive the change only after all acceptance gates pass.
