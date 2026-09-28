# system-assets-knowledge Specification

## Purpose

Define the System Assets & Knowledge workspace as a unified projection over existing Material, SourceDocument, FactPack and KnowledgeCollection resources. Reuse resources by reference, preserve real provenance/rights semantics, and avoid a duplicate generic asset truth store.

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
