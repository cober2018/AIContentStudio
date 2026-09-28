## MODIFIED Requirements

### Requirement: Freeze Candidate is separate from Content Approval
The system SHALL freeze an immutable project Candidate in an evolved ContentAsset using manifest schema v3 for legacy Draft-backed sources or schema v4 for ContentMasterRevision-backed sources before approval. A project Candidate SHALL have a distinct `candidate_hash`; `approved_candidate_hash` SHALL remain unset until approval. For v3 and workflow-backed v4, Freeze MUST verify persisted Draft or workflow-output lineage to the requested Unit and Run. Manually authored v4 SHALL instead verify Master ownership, pinned context, exact refs, checks and render binding without requiring or inventing Draft/Run lineage. Both paths MUST reject an unsupported or unrenderable source rather than invent TopicBrief, Draft, evidence, or media references.

#### Scenario: Freeze
- **WHEN** current content has supported owned source lineage and satisfies required freeze gates
- **THEN** immutable project/unit/identity/evidence/workflow/content/media/check/render provenance and Candidate hash are stored without approval or delivery authorization

#### Scenario: Blocked freeze
- **WHEN** required checks are stale/blocking or evidence/media rights are invalid
- **THEN** freeze is rejected with typed reasons

#### Scenario: Unsupported output source
- **WHEN** a Unit has no supported content source or renderable artifact with proven project-owned source lineage
- **THEN** freeze returns a typed unsupported-source blocker and creates no Candidate, Review, or DeliveryTarget

#### Scenario: Repeated identical freeze
- **WHEN** an authorized editor repeats freeze with the same Unit, source revision, and input hashes
- **THEN** the server returns the same immutable Candidate without duplicating project history; changed inputs produce a new Candidate and preserve the old one

Project Candidate freeze SHALL support legacy Draft-backed manifest v3 and new ContentMasterRevision-backed manifest v4. Freeze MUST verify the selected source belongs to the requested Project/Unit, is current for its source model, and satisfies the relevant readiness/render gates. Freeze still creates no Content Approval or DeliveryTarget.

#### Scenario: Freeze Master Candidate
- **WHEN** an authorized editor freezes the current ready ContentMasterRevision
- **THEN** immutable manifest v4/Candidate hash are created without approval or delivery authorization

#### Scenario: Unsupported Master render
- **WHEN** the modality cannot produce a verified render snapshot
- **THEN** freeze fails closed and creates no Candidate

#### Scenario: Manual Master without Run
- **WHEN** an authorized editor freezes a current manually authored Master with valid context, refs, checks and render binding but no origin WorkflowRun or Draft
- **THEN** manifest v4 freezes successfully with truthful editor provenance and null absent workflow/Draft links

### Requirement: Project Candidate manifest v3
Manifest v3 SHALL bind exact Project/Unit, modality/channel/content form, IdentitySnapshot ID/checksum, frozen project evidence boundary or FactPack identity/checksum, source content revision, ordered media revisions and rights, required check input hashes/results, renderer identity/payload/hash, and producing WorkflowRun/version/checksum with available plugin/model provenance. Its canonical hash SHALL cover those fields. Historical v1/v2 manifests SHALL remain readable without fabricated project or identity links.

#### Scenario: Identity or workflow advances after freeze
- **WHEN** identity revisions or workflow defaults change after Candidate freeze
- **THEN** the Candidate manifest and hash retain the exact frozen snapshot and producing Run identities

#### Scenario: Legacy manifest
- **WHEN** a v1/v2 ContentAsset has no verified Project/Unit/IdentitySnapshot relationship
- **THEN** the server leaves those links null and labels project identity provenance legacy/unknown rather than backfilling guessed values

Historical v3 Candidates SHALL remain readable and hash-stable. F6A SHALL NOT rewrite them as v4 or fabricate ContentMasterRevision links.

#### Scenario: Read v3 after F6A
- **WHEN** a historical v3 Candidate is opened
- **THEN** its original Draft/workflow/evidence/identity manifest is returned unchanged

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

Content Approval SHALL accept current valid v4 Candidates under the same exact Candidate ID/hash rule used by project Candidates. Approval MUST recheck live rights/evidence revocation and MUST NOT mutate the source ContentMasterRevision.

#### Scenario: Approve v4
- **WHEN** a reviewer approves a valid current v4 Candidate
- **THEN** Review binds the exact Candidate/hash and the Master revision remains unchanged

### Requirement: Project v3 manual package compatibility
Project v3 manual_handoff and copy_package SHALL build local packages from the approved immutable v3 manifest and real verified media bytes without requiring a Draft or v1 Topic asset. Legacy v1 article-handoff SHALL remain unchanged for genuine v1 assets. An unsupported v3 render/media shape MUST fail closed, not fall back to v1 or report package-ready. Package generation SHALL NOT make a remote publishing call.

#### Scenario: Non-Draft project manual handoff
- **WHEN** an approved v3 Candidate has a renderable payload, authentic media, and an authorized manual_handoff target but no Draft ID
- **THEN** the package contains the approved content and verified media, enters awaiting-manual-receipt, and makes no remote call

#### Scenario: Unsupported v3 package
- **WHEN** the v3 render or media bytes cannot be verified
- **THEN** package generation is blocked without a v1 fallback, false receipt, or remote action

Project local packaging SHALL continue to support valid v3 Candidates and SHALL additionally support v4 modality-aware packages. A v4 package MUST use its own manifest/render/assets and MUST NOT fall back to v3/v1 packaging.

#### Scenario: Graphic v4 copy package
- **WHEN** an approved graphic v4 Candidate has a verified final render image
- **THEN** the local package contains the exact render bytes and manifest without requiring Draft

#### Scenario: Video v4 package unavailable
- **WHEN** the v4 Candidate lacks verified packageable video bytes
- **THEN** packaging fails closed without a legacy fallback

### Requirement: Unit review workspace
A selected unit SHALL expose Preview, Changes, Checks and Publish tabs and clearly separate Freeze Candidate, Content Approval, Delivery Authorization and delivery execution.

#### Scenario: Inspect a unit before approval
- **WHEN** an authorized reviewer opens a unit with a frozen but unapproved Candidate
- **THEN** Preview, Changes, and Checks show frozen facts, Publish shows authorization unavailable, and approval is a separate explicit action

#### Scenario: Candidate diff
- **WHEN** a unit has two immutable Candidates
- **THEN** Changes returns a bounded read-only comparison of content, media, evidence, identity, workflow, checks, and render provenance without creating a diff table

Preview/Changes/Checks SHALL render v4 Text/Graphic/Video according to modality. Text similarity is optional for text and MUST NOT be fabricated for Graphic/Video.

#### Scenario: V4 modality review
- **WHEN** a reviewer opens a v4 Candidate
- **THEN** Review shows modality-appropriate preview/diff/check information from the frozen manifest
