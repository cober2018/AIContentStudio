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

### Requirement: Master writes are atomic and request-idempotent

Master save SHALL authorize first, then replay identical unit-scoped idempotency keys by canonical request fingerprint before checking stale expected_revision. Key reuse with changed payload/refs/context intent MUST return 409. Head/parent/context validation, refs and events SHALL commit atomically using database CAS/locking shared with archive and freeze; conflicting writes MUST NOT persist partial rows.

#### Scenario: Retry after lost response
- **WHEN** a committed save is retried with the same request/key and old expected_revision
- **THEN** the same revision returns without another event or revision

#### Scenario: Reuse key for another payload
- **WHEN** a caller reuses the key with changed payload or refs
- **THEN** 409 returns and the original revision remains unchanged

### Requirement: Master history preserves unit identity safety

Any persisted Master SHALL count as production history without a Run. Existing identity/modality/workflow selection changes SHALL Fork + Archive and deletion SHALL archive instead of destroying history. Identity staleness SHALL compare actual unit-pinned context, never automatically resolve latest hierarchy. Hierarchy drift SHALL be advisory until explicit rebind; a same-unit Brief/Boundary rebase SHALL keep pinned identity.

#### Scenario: Delete manually authored unit
- **WHEN** a unit has Masters but no WorkflowRun and is deleted
- **THEN** it archives and authorized Master/Candidate history stays readable

#### Scenario: Persona advances without rebind
- **WHEN** Persona advances while the unit still pins its old snapshot
- **THEN** Master/unit remain pinned without silent replacement or automatic stale_identity

### Requirement: Final render is bound to exact Master inputs

Graphic/Video render SHALL bind project-visible exact revisions to a canonical render-input hash excluding the final-render reference. Provenance SHALL be verified renderer lineage or explicit editor-confirmed manual-render attestation with truthful origin. MIME/kind, bytes/hash, output coverage and live rights SHALL be checked; changed inputs SHALL invalidate binding. Raw media existence MUST NOT prove a render of this Master. Unsupported channel/form/modality SHALL remain unavailable.

#### Scenario: Replace script but keep old video
- **WHEN** payload changes but the final render binding retains old inputs
- **THEN** render readiness blocks until an explicit new valid binding

#### Scenario: Manual final render
- **WHEN** an editor explicitly confirms real project render bytes for exact current inputs
- **THEN** manual attestation/input hash freeze without claiming automated renderer verification

### Requirement: Check authority and legacy seed freshness are exact

Checks SHALL remain immutable and currentness SHALL derive from exact input/profile/adapter version. Latest applicable result per required kind SHALL govern readiness; an old pass MUST NOT hide a later blocker. From-output SHALL prove current same-unit Draft/Run/Step/Attempt lineage and reject failed/stale/replaced attempts. Warning dispositions/source provenance SHALL bind exact inputs without relabeling old execution as new context.

#### Scenario: Later check blocks
- **WHEN** pass is followed by blocker for the same current revision/check kind
- **THEN** freeze uses blocker instead of the older pass

#### Scenario: Failed rerun retains history
- **WHEN** a historical Draft output points to a replaced/failed attempt
- **THEN** from-output rejects it instead of treating historical success as current

### Requirement: V4 routes enforce schema-aware compatibility and authorization

Project and legacy Asset/Export/Review/Target/Package/Run routes SHALL share ownership/archive checks. Schema dispatch SHALL precede text/Draft access. Unsupported legacy v4 export/mutation SHALL fail closed. Approval/new authorization SHALL verify current context-valid Master/exact Candidate hash. V4 remote publishing SHALL be unavailable unless verified for schema/modality/form; F6A MUST NOT infer publisher support or weaken unknown/reconciliation.

#### Scenario: Private raw export
- **WHEN** a foreign caller requests v4 export by raw Candidate ID
- **THEN** no private content/media is disclosed

#### Scenario: Text publisher with video Candidate
- **WHEN** an existing publisher supports only earlier text manifests
- **THEN** v4 video remote action is unavailable and no attempt or remote call occurs

### Requirement: Master payload and downgrade preserve bounds and history

Server validation SHALL bound payload depth/bytes, array/ref counts and pagination and reject unchecked/dangling/duplicate embedded references and non-finite JSON. Downgrade SHALL restore legacy schema on compatible isolated data; retained incompatible v4 history SHALL cause read-only refusal before destructive DDL. No fake text/body backfill or deletion SHALL force rollback.

#### Scenario: Incompatible rollback
- **WHEN** isolated downgrade finds v4 NULL-body or Master-linked history
- **THEN** it fails before schema destruction and leaves history unchanged

#### Scenario: Unchecked payload material
- **WHEN** a slot embeds a MaterialRevision absent from authorized exact refs
- **THEN** save rejects it instead of bypassing project validation
