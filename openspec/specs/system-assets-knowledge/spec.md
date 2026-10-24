# system-assets-knowledge Specification

## Purpose
Provide a bounded System Assets & Knowledge workspace over existing materials, sources, evidence packs and reference-based Knowledge Collections. Preserve exact revisions, rights, provenance and authorized usage while requiring explicit project reuse and Fact Boundary decisions.
## Requirements
### Requirement: System library is a projection over existing truth

The system SHALL provide a unified system-library read model over Material, SourceDocument, FactPack and KnowledgeCollection. It MUST NOT copy those resources into a replacement generic Asset table.

#### Scenario: Browse library
- **WHEN** the user opens `/assets`
- **THEN** bounded metadata for materials, sources, evidence packs and collections is shown without loading raw bodies/bytes/full snapshots

### Requirement: Shared scope is explicit

Existing SourceDocument, Material and FactPack resources SHALL remain system-shared under the current V1 authentication model. F5C MUST NOT fabricate per-user ownership from created_by or historical usage.

#### Scenario: Show scope
- **WHEN** a system resource is displayed
- **THEN** the UI/API labels its library scope truthfully rather than claiming owner isolation that does not exist

### Requirement: Knowledge Collections reference knowledge resources

KnowledgeCollection SHALL organize SourceDocument and FactPack references without copying source text, Fact rows or FactPack snapshot data.

#### Scenario: Add Source to collection
- **WHEN** an editor adds a SourceDocument
- **THEN** only a collection-item reference is stored and SourceDocument remains the source of truth

#### Scenario: Add FactPack to collection
- **WHEN** an editor adds a FactPack
- **THEN** the exact FactPack version row is referenced and not cloned

### Requirement: Knowledge Collection is not Fact Boundary

KnowledgeCollection SHALL be organizational only and MUST NOT be treated as FactPack, Project Fact Boundary or publication authorization.

#### Scenario: Use collection in project
- **WHEN** the user wants collection content in a Project
- **THEN** the user selects underlying Sources or a frozen FactPack through their existing explicit project/evidence flows

### Requirement: Rights semantics remain source-specific

Material rights SHALL come from MaterialRevision. Fact/evidence rights SHALL come from FactPackItem snapshots. SourceDocument itself SHALL report publication rights as not decided at source level.

#### Scenario: Source has no rights decision
- **WHEN** a SourceDocument is shown in System Library
- **THEN** the UI does not infer public/model-use permission from trust level or parse status

#### Scenario: FactPack rights summary
- **WHEN** a FactPack is listed
- **THEN** rights readiness is derived from its items and frozen status alone does not imply public-use readiness

### Requirement: Project reuse is by reference

System library resources SHALL be reused in Projects through existing ProjectSourceBinding, ProjectMaterialReference and explicit Fact Boundary bindings.

#### Scenario: Reuse Material
- **WHEN** a MaterialRevision is added to a Project
- **THEN** the Project stores a reference and underlying bytes are not duplicated

#### Scenario: Reuse Source
- **WHEN** a SourceDocument is added to a Project
- **THEN** ProjectSourceBinding is used and source text is not copied

#### Scenario: Reuse FactPack
- **WHEN** a FactPack is selected for Project evidence
- **THEN** existing frozen/checksum validation applies and binding remains an explicit Evidence action

### Requirement: Usage and provenance are bounded read models

Library detail SHALL expose bounded usage/provenance summaries without loading full histories.

#### Scenario: Inspect usage
- **WHEN** a user inspects a Material, Source or FactPack
- **THEN** the system returns recent/count usage refs and deep links without mutating any project/resource

### Requirement: Shared resources do not disclose private usage

The system SHALL scope usage counts, IDs, titles and deep links to the caller's authorized Project and Opportunity records. Shared library resource visibility MUST NOT grant access to private usage. Unsupported usage categories SHALL expose coverage rather than fabricate zero or completeness.

#### Scenario: Another user's project uses a shared Source
- **WHEN** a caller inspects the shared Source's usage
- **THEN** no foreign project/Opportunity IDs, titles, links or existence counts are disclosed

### Requirement: Collection mutations are revision guarded

System-shared Knowledge Collections SHALL support ordered reference items, idempotent add/detach/reactivate, and archive-as-delete without copying resources. Collection metadata, item edits, reorders and archive SHALL enforce expected_revision with a conditional write gate; stale/concurrent conflicting writes SHALL return 409 without partial changes. Archived collections SHALL remain readable and reject every mutation. New membership SHALL reject archived resources while historical references remain readable.

#### Scenario: Concurrent reorder and archive
- **WHEN** a reorder and archive target the same collection revision
- **THEN** only one commits and the other returns 409, with no post-archive item mutation

#### Scenario: Reactivate detached membership
- **WHEN** an editor explicitly readds a previously detached resource with current revision
- **THEN** the same unique item is reactivated without cloning its resource or membership

### Requirement: Library pagination and rights summaries are honest

The unified list SHALL use deterministic, database-bounded pagination and typed validated filters, without fetching raw text, bytes, full snapshots or histories. Rights SHALL distinguish allowed, denied, unknown and revoked; revocation overrides grants, Source rights remain not_decided_at_source_level, and empty/unknown packs SHALL NOT be reported public-ready.

#### Scenario: Invalid rights filter
- **WHEN** a caller submits a filter unsupported by the selected resource type
- **THEN** the API rejects the invalid combination rather than returning an apparently filtered result

### Requirement: Accepted provider media remains an exact library revision
Provider search/generation/TTS/renderer output SHALL enter the existing Material/MaterialRevision truth only after explicit acceptance and byte, MIME, hash, provenance and rights/license validation. Unknown or revoked public-use rights MUST block public-ready project reuse; Project Shared Assets SHALL reference the exact revision without duplicating bytes or assigning false ownership.

#### Scenario: Unknown license
- **WHEN** a provider result has valid bytes but no proven public-use right
- **THEN** the revision remains not-public-ready and cannot satisfy Candidate or package media gates

#### Scenario: Cross-unit Project use
- **WHEN** a generated MaterialRevision is accepted and explicitly attached to a Project
- **THEN** authorized Units in that Project may reference the same revision subject to live rights, while the generating run/provenance remains inspectable

### Requirement: Resource list detail and explicit use pages
The shared library SHALL expose URL-preserved classification, search, status, type, rights and real pagination. Resource overview, exact revisions, usage, explicit project reuse and management SHALL have distinct views while retaining existing resource/id and generation task links. Tools SHALL load only when explicitly selected and navigation MUST NOT generate, accept, freeze, attach or archive resources.

#### Scenario: Return from a resource
- **WHEN** a user opens a resource or explicit tool and returns
- **THEN** list filters and pagination remain available without a resource mutation

#### Scenario: Exact project reuse
- **WHEN** an authorized editor selects an owned project for a material revision or frozen FactPack
- **THEN** the workspace names the project and preserves the existing exact-version, checksum, revision and explicit-confirmation gates

#### Scenario: Read failure or invalid link
- **WHEN** a selected resource or list cannot be read or its identifier is invalid
- **THEN** the UI shows that uncertainty rather than a prior resource or a successful empty result

### Requirement: Resource management remains explicit
Default resource and collection overview SHALL keep current rights limitations visible while placing edit, revoke, archive and collection-member mutations behind explicit views. Existing user permission, archived state, collection snapshot/version conflict and source-specific rights semantics SHALL be retained.

#### Scenario: Collection member is not fact approval
- **WHEN** a source or FactPack is organized into a knowledge collection
- **THEN** this does not grant public or model-use rights or bind a project fact boundary

#### Scenario: Conflicting collection revision
- **WHEN** a collection edit encounters a newer revision
- **THEN** the user's input is not automatically retried against the new version and an explicit reread is required
