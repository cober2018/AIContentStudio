## ADDED Requirements

### Requirement: Project-first Review Center
The Review Center SHALL group authorized ContentProjects and ContentUnits and derive state from persisted production, Candidate, Review, DeliveryTarget, DeliveryAttempt, and Receipt facts rather than a second review state table. Legacy Topic-first `/review-publish` SHALL remain available without substituting its queue for project review.

#### Scenario: Open Review Center
- **WHEN** the user opens `/review`
- **THEN** projects/units load with truthful Ready/Blocked/Stale/Unknown/Approved projections

#### Scenario: Legacy review remains separate
- **WHEN** the user opens `/review-publish`
- **THEN** existing Topic-based review remains readable and project candidates are not leaked through that legacy queue

### Requirement: One project authorization boundary
Every project-bound Candidate, Review decision, DeliveryTarget, Attempt, Receipt, package, and reconciliation SHALL enforce owning Project/Unit authorization before serialization or mutation, including legacy raw-ID routes. Archived projects/units SHALL retain authorized historical reads but refuse new freeze, approval, authorization, delivery, or retry actions.

#### Scenario: Raw ID belongs to another project owner
- **WHEN** a user presents a known Candidate or DeliveryTarget ID through a legacy endpoint without owning its project
- **THEN** the server denies access before returning metadata, manifest, bytes, attempts, or receipts

#### Scenario: Archived unit history
- **WHEN** an authorized user opens an archived unit's prior Candidate or Receipt
- **THEN** history remains readable but new project review and delivery mutations are rejected

### Requirement: Freeze Candidate is separate from Content Approval
The system SHALL freeze an immutable project Candidate in an evolved ContentAsset using manifest schema v3 before approval. A project Candidate SHALL have a distinct `candidate_hash`; `approved_candidate_hash` SHALL remain unset until approval. Freeze MUST verify persisted Draft or workflow-output lineage to the requested Unit and Run, and MUST reject an unsupported or unrenderable source rather than invent TopicBrief, Draft, evidence, or media references.

#### Scenario: Freeze
- **WHEN** current content has supported owned source lineage and satisfies required freeze gates
- **THEN** immutable project/unit/identity/evidence/workflow/content/media/check/render provenance and Candidate hash are stored without approval or delivery authorization

#### Scenario: Blocked freeze
- **WHEN** required checks are stale/blocking or evidence/media rights are invalid
- **THEN** freeze is rejected with typed reasons

#### Scenario: Unsupported output source
- **WHEN** a Unit has no supported content source or renderable artifact with proven ProjectWorkflowOutput lineage
- **THEN** freeze returns a typed unsupported-source blocker and creates no Candidate, Review, or DeliveryTarget

#### Scenario: Repeated identical freeze
- **WHEN** an authorized editor repeats freeze with the same Unit, source revision, and input hashes
- **THEN** the server returns the same immutable Candidate without duplicating project history; changed inputs produce a new Candidate and preserve the old one

### Requirement: Project Candidate manifest v3
Manifest v3 SHALL bind exact Project/Unit, modality/channel/content form, IdentitySnapshot ID/checksum, frozen project evidence boundary or FactPack identity/checksum, source content revision, ordered media revisions and rights, required check input hashes/results, renderer identity/payload/hash, and producing WorkflowRun/version/checksum with available plugin/model provenance. Its canonical hash SHALL cover those fields. Historical v1/v2 manifests SHALL remain readable without fabricated project or identity links.

#### Scenario: Identity or workflow advances after freeze
- **WHEN** identity revisions or workflow defaults change after Candidate freeze
- **THEN** the Candidate manifest and hash retain the exact frozen snapshot and producing Run identities

#### Scenario: Legacy manifest
- **WHEN** a v1/v2 ContentAsset has no verified Project/Unit/IdentitySnapshot relationship
- **THEN** the server leaves those links null and labels project identity provenance legacy/unknown rather than backfilling guessed values

### Requirement: Candidate-bound Content Approval
Project Content Approval SHALL create a Review decision bound to one exact immutable Candidate ID/hash and MUST NOT rewrite Candidate content or manifest. Live rights/evidence revocation and candidate integrity SHALL be checked at approval; a changes request SHALL record a decision without mutating the frozen Candidate. Legacy draft-bound review behavior SHALL remain compatible.

#### Scenario: Approve
- **WHEN** a reviewer approves a valid Candidate
- **THEN** Review references that Candidate/hash and no DeliveryTarget is created implicitly

#### Scenario: Candidate changed or invalidated
- **WHEN** the submitted Candidate ID/hash differs from the persisted frozen hash, or required rights/evidence have been revoked
- **THEN** approval is rejected without changing Candidate content or creating an approved Review

#### Scenario: Request changes
- **WHEN** a reviewer requests changes to a frozen Candidate
- **THEN** a candidate-bound decision is recorded and the immutable Candidate remains readable for historical comparison

### Requirement: Delivery Authorization is separate
DeliveryTarget creation SHALL represent explicit Delivery Authorization for an approved exact Candidate hash, account, channel, content form, action, and capability snapshot. It MUST NOT occur implicitly at freeze or approval. A nullable ContentAccount ID MAY provide a stable identity reference, but authorization SHALL also freeze `account_ref`; account name alone MUST NOT be treated as verified platform/channel capability. Project-target uniqueness/idempotency SHALL use the stable ContentAccount identity when present, not account_ref alone; legacy targets SHALL preserve account_ref-based identity. Two distinct ContentAccounts sharing account_ref MUST remain distinct authorizations. Concurrent requests for the same identity/version SHALL return one target.

#### Scenario: Authorize before approval
- **WHEN** Candidate lacks Content Approval
- **THEN** authorization is rejected

#### Scenario: Account ownership and capability
- **WHEN** a project delivery authorization selects a ContentAccount
- **THEN** the server verifies that account is active and owned through the Candidate's identity hierarchy, and validates channel/capability only against explicit verified account or publisher configuration; absent verification is marked unavailable for automatic action

#### Scenario: Account edits after authorization
- **WHEN** ContentAccount name or profile changes after DeliveryTarget creation
- **THEN** the target retains its original account_ref and capability snapshot without rewriting historical authorization

#### Scenario: Equal account references, distinct identities
- **WHEN** two different active ContentAccounts use the same account_ref for the same Candidate, channel, action, and authorization version
- **THEN** each can receive a distinct DeliveryTarget, while repeating authorization for either account returns that account's existing target

### Requirement: Project v3 manual package compatibility
Project v3 manual_handoff and copy_package SHALL build local packages from the approved immutable v3 manifest and real verified media bytes without requiring a Draft or v1 Topic asset. Legacy v1 article-handoff SHALL remain unchanged for genuine v1 assets. An unsupported v3 render/media shape MUST fail closed, not fall back to v1 or report package-ready. Package generation SHALL NOT make a remote publishing call.

#### Scenario: Non-Draft project manual handoff
- **WHEN** an approved v3 Candidate has a renderable payload, authentic media, and an authorized manual_handoff target but no Draft ID
- **THEN** the package contains the approved content and verified media, enters awaiting-manual-receipt, and makes no remote call

#### Scenario: Unsupported v3 package
- **WHEN** the v3 render or media bytes cannot be verified
- **THEN** package generation is blocked without a v1 fallback, false receipt, or remote action

### Requirement: Unknown remains unknown
Unknown remote results SHALL require reconciliation and SHALL NOT be automatically retried or silently converted to delivered. A further attempt is allowed only after an explicit, audited not-delivered reconciliation under the existing DeliveryAttempt rules.

#### Scenario: Timeout
- **WHEN** publisher result cannot be confirmed
- **THEN** Review projects Unknown/reconciliation-needed with no generic retry

#### Scenario: Reconcile without duplicate side effect
- **WHEN** an operator records a delivered or not-delivered reconciliation for an unknown attempt
- **THEN** the attempt/target history records that outcome without making a second remote call during reconciliation

### Requirement: Derived review status
Blocked, stale, waiting_review, ready, approved, delivery_ready, unknown, and delivered SHALL be deterministic projections, not another mutable state source. Projection SHALL be scoped to the selected/current Candidate and its targets; older Candidates remain historical. For that scope, unresolved unknown SHALL outrank blockers/revocations, stale, waiting_review, approved, delivery_ready, and delivered. The same underlying facts SHALL drive project Review and Overview.

#### Scenario: Old delivery does not approve new Candidate
- **WHEN** a newer Candidate is frozen after an older Candidate was delivered
- **THEN** the current unit projection returns the newer Candidate's review state while the old delivery remains visible in history

#### Scenario: Unknown outranks approved
- **WHEN** the current Candidate has an unresolved unknown DeliveryAttempt and an approved Review
- **THEN** the summary is unknown/reconciliation-needed rather than approved or delivered

### Requirement: Unit review workspace
A selected unit SHALL expose Preview, Changes, Checks and Publish tabs and clearly separate Freeze Candidate, Content Approval, Delivery Authorization and delivery execution.

#### Scenario: Inspect a unit before approval
- **WHEN** an authorized reviewer opens a unit with a frozen but unapproved Candidate
- **THEN** Preview, Changes, and Checks show frozen facts, Publish shows authorization unavailable, and approval is a separate explicit action

#### Scenario: Candidate diff
- **WHEN** a unit has two immutable Candidates
- **THEN** Changes returns a bounded read-only comparison of content, media, evidence, identity, workflow, checks, and render provenance without creating a diff table

### Requirement: Project history integration
Candidate/approval/delivery lifecycle SHALL appear in project Activity, Versions and Overview from underlying facts. ProjectEvent and local state changes SHALL commit together; failed or idempotently repeated actions MUST NOT create misleading duplicate activity.

#### Scenario: Approve and authorize history
- **WHEN** a Candidate is approved and then separately authorized for a delivery target
- **THEN** Versions and Activity expose two distinct real records/events and Overview derives the remaining next action
