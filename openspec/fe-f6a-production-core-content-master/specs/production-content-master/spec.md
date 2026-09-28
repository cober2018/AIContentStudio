## ADDED Requirements

### Requirement: ContentMasterRevision is the project production revision root

The system SHALL persist append-only ContentMasterRevision rows per ContentUnit and modality. A Master revision SHALL freeze its exact payload hash, IdentitySnapshot, CreativeBrief revision when present, Project Fact Boundary revision when present, channel/content form, production provenance, parent revision and creation actor. Historical revisions MUST NOT be rewritten when current project context advances.

#### Scenario: Save next Master revision
- **WHEN** an authorized editor saves valid content with `expected_revision=N`
- **THEN** revision N+1 is created with the current exact context refs and revision N remains unchanged

#### Scenario: Concurrent save
- **WHEN** another save advances the ContentUnit before a stale request commits
- **THEN** the stale request returns 409 and creates no partial Master/ref/check/event rows

#### Scenario: Save incomplete drafting context
- **WHEN** the ContentUnit has IdentitySnapshot but no current Brief or Fact Boundary
- **THEN** the Master revision MAY be saved for drafting but readiness reports the missing context and Candidate freeze is unavailable

### Requirement: Master revision context becomes stale explicitly

The system SHALL derive current/stale state by comparing a Master revision's frozen Identity/Brief/Fact Boundary/channel/content-form context with the ContentUnit's current context. It MUST NOT silently retarget an old revision to newer context.

#### Scenario: Brief advances
- **WHEN** CreativeBrief revision N+1 becomes current after a Master pinned N
- **THEN** the old Master remains readable and its current projection reports stale_brief

#### Scenario: Explicit new save after context change
- **WHEN** the editor explicitly saves a new Master using the current context
- **THEN** a new revision is created and required checks are not inherited as current from the old revision

### Requirement: Text, Graphic and Video use versioned modality payloads

The production core SHALL register versioned payload adapters for `text`, `graphic`, and `video`. The core MAY validate only stable top-level envelopes in F6A; specialized editor semantics remain future modality slices.

#### Scenario: Text payload
- **WHEN** `text.master.v1` contains valid document or markdown content
- **THEN** it can be stored and previewed through the text adapter

#### Scenario: Graphic shell payload
- **WHEN** `graphic.master.v1` contains stable canvas structure but no final rendered image
- **THEN** it may be saved as a Master draft but is not Candidate-ready

#### Scenario: Video shell payload
- **WHEN** `video.master.v1` contains script/shot/timeline structure but no verified final render
- **THEN** it may be saved as a Master draft but is not Candidate-ready

### Requirement: Master assets are exact project-visible MaterialRevision references

ContentMasterAssetRef SHALL bind exact MaterialRevision IDs, hashes, role/order/placement and rights snapshots. The referenced revision MUST already be visible to the Project through ProjectMaterialReference or verified ProjectWorkflowOutput. Raw global MaterialRevision ID knowledge MUST NOT bypass Project scope.

#### Scenario: Reuse project asset
- **WHEN** a Master references a MaterialRevision already in Project Shared Assets
- **THEN** the ref is stored without copying bytes

#### Scenario: Foreign/raw material
- **WHEN** a request supplies a MaterialRevision that is not project-visible
- **THEN** the save is rejected without disclosing or attaching it

### Requirement: Master evidence is bound to the exact Fact Boundary

ContentMasterEvidenceRef SHALL reference FactPackItem rows from the Master revision's exact frozen Project Fact Boundary and preserve the item's snapshot checksum and content locator.

#### Scenario: Valid evidence ref
- **WHEN** a referenced FactPackItem belongs to the frozen boundary and has a snapshot checksum
- **THEN** the evidence ref is persisted without changing the FactPack

#### Scenario: Evidence from another pack
- **WHEN** a request references an item outside the Master revision's exact boundary
- **THEN** the save is rejected

### Requirement: Master checks are append-only and input-bound

ContentMasterCheckRun SHALL be append-only, bound to one Master revision and input hash, and use pass/warning/blocker/incomplete/stale semantics. A check from an older revision MUST NOT be treated as current for a newer revision.

#### Scenario: New revision after passing checks
- **WHEN** revision N+1 is saved after revision N had passing checks
- **THEN** N+1 starts without inherited current checks and must run its own required checks

### Requirement: Workflow Draft output can seed Text Master safely

The production core SHALL provide an explicit compatibility action that converts a verified same-unit Draft ProjectWorkflowOutput into `text.master.v1` while preserving exact Draft/Run/node/attempt lineage.

#### Scenario: Seed from Draft output
- **WHEN** a valid current Draft workflow output belongs to the requested ContentUnit
- **THEN** the new Master records that source provenance and converts only provable document/media/evidence references

#### Scenario: Unmappable Draft reference
- **WHEN** an old Draft claim/media reference cannot be proven against current Master context
- **THEN** it is reported as incomplete/warning rather than fabricated

### Requirement: Candidate manifest v4 freezes ContentMasterRevision

The system SHALL support Candidate manifest schema v4 sourced from one exact ContentMasterRevision. V4 SHALL freeze project/unit/modality/channel/content-form, IdentitySnapshot, Brief, Fact Boundary, Master payload/context hashes, exact asset/evidence refs, current checks, render snapshot, production provenance, citations and declarations. V4 MUST NOT require Draft, TopicBrief or MotherRevision.

#### Scenario: Freeze v4 Candidate
- **WHEN** the current Master is context-current, passes required gates and its modality adapter can produce a real render snapshot
- **THEN** an immutable Candidate v4 is created without Content Approval or Delivery Authorization

#### Scenario: Stale Master
- **WHEN** Identity/Brief/Evidence/channel context advanced after the Master was saved
- **THEN** v4 freeze is rejected and no Candidate is created

#### Scenario: Graphic/video render unavailable
- **WHEN** a graphic/video Master lacks a verified final render asset and no deterministic renderer exists
- **THEN** freeze fails closed with render_unavailable rather than fabricating media

### Requirement: Candidate freeze remains backward compatible

The project Candidate endpoint SHALL accept exactly one supported source path: legacy Draft-backed ProjectWorkflowOutput for v3, or ContentMasterRevision for v4. V1/v2/v3 history SHALL remain readable and MUST NOT be rewritten as v4.

#### Scenario: Existing v3 Draft
- **WHEN** an existing unit freezes a supported Draft output
- **THEN** current v3 behavior remains compatible

#### Scenario: Historical Candidate
- **WHEN** a historical v1/v2/v3 Candidate is opened after F6A
- **THEN** its original manifest/schema/provenance remains unchanged

### Requirement: Non-text v4 Candidate does not fabricate text lineage

ContentAsset MAY link `content_master_revision_id`. V4 Graphic/Video Candidates SHALL NOT fabricate Draft, TopicBrief or MotherRevision IDs. Text-centric compatibility fields may remain null where not applicable.

#### Scenario: Video Candidate
- **WHEN** a video Master freezes successfully
- **THEN** the Candidate records ArtifactKind video and Master provenance without fake Draft/MotherRevision lineage

### Requirement: V4 approval and delivery preserve live safety gates

Content Approval and local package generation SHALL operate on the exact v4 Candidate hash and recheck live evidence/material rights. They MUST NOT mutate ContentMasterRevision.

#### Scenario: Rights revoked after freeze
- **WHEN** a referenced MaterialRevision or evidence item loses required public-use rights after Candidate freeze
- **THEN** approval/package is blocked while the frozen Candidate remains historically readable

### Requirement: V4 Review is modality-aware

Review Preview/Changes/Checks SHALL understand v4 Text/Graphic/Video without forcing every modality into markdown comparison.

#### Scenario: Graphic diff
- **WHEN** two Graphic Candidates differ in canvas/assets
- **THEN** Review reports changed content/assets/render sections and does not invent a text similarity score

#### Scenario: Video preview
- **WHEN** a Video Candidate has a verified render asset
- **THEN** Review can show script/shot/timeline summary plus the exact render reference

### Requirement: Production Workspace separates control plane from modality editor

The frontend SHALL keep Context Header, Workflow Mini Canvas, Node Inspector and Shared Assets as common Production components and mount Text/Graphic/Video modality shells through explicit extension points.

#### Scenario: Open Graphic unit
- **WHEN** a Graphic ContentUnit opens
- **THEN** the same persisted Workflow/Identity context loads while the Graphic modality shell owns content-specific presentation

#### Scenario: Workflow editor remains separate
- **WHEN** a user edits Workflow nodes
- **THEN** content payload is not implicitly changed, and content revision save remains a separate explicit action
