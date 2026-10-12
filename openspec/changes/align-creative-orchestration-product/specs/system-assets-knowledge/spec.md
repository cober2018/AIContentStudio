## ADDED Requirements

### Requirement: System Assets and Knowledge owns ordinary daily resource operations

The `/assets` product surface SHALL support ordinary authorized creation/maintenance operations for the existing Material, SourceDocument, Fact and FactPack truths rather than requiring users to leave for legacy pages. It MUST reuse existing APIs/entities and MUST NOT create a generic replacement asset/fact store.

Required parity includes:

- Material upload, provider generation/search acceptance, revision/rights/revoke and Project reference;
- Source text/URL/file import, extraction, fact review/confirm/reject/edit and bounded bulk decisions;
- FactPack create, add/remove items, clone, freeze, history/read;
- Project reuse through existing Source/Material/Fact Boundary references.

#### Scenario: Extract and confirm facts in the new surface
- **WHEN** a user imports a Source in `/assets` or Project Evidence
- **THEN** they can extract/review facts and build/freeze the evidence pack without navigating to legacy `/sources` or `/fact-packs`

### Requirement: Project context and global library share operations without copying truth

Project Evidence/Assets MAY embed scoped versions of global library operations. Creating/importing a Source or Material from a Project SHALL create the existing global truth plus the explicit project reference. It MUST NOT create a hidden project-only clone.

#### Scenario: Upload material inside a Project
- **WHEN** the user uploads a file from Project Assets
- **THEN** one MaterialRevision is stored in the global library and the Project receives an exact reference to that revision

### Requirement: Accepted Creative Execution outputs become ordinary library revisions

An explicitly accepted CreativeExecution output SHALL appear in the existing Material library with source/provenance indicating external execution. Library visibility MUST NOT imply the output is approved content, published, public-use ready or bound to a Master/Variant.

#### Scenario: Accepted professional render
- **WHEN** a user accepts a staged external MP4
- **THEN** the Material library shows the immutable revision and exact execution provenance while content approval/publication remain separate
