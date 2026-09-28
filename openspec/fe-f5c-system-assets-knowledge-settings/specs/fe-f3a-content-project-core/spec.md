## MODIFIED Requirements

### Requirement: Unified Project Shared Assets by reference

System Library MaterialRevision and SourceDocument resources SHALL enter a Project through existing reference bindings. System Assets & Knowledge does not replace the project Shared Assets pool or duplicate underlying resource bytes/text.

#### Scenario: Add system Material to Project
- **WHEN** the user selects a MaterialRevision from `/assets`
- **THEN** ProjectMaterialReference is created and the same MaterialRevision remains the underlying resource

#### Scenario: Add system Source to Project
- **WHEN** the user selects a SourceDocument from `/assets`
- **THEN** ProjectSourceBinding is created and the existing Source remains the underlying truth

### Requirement: Immutable project Fact Boundary revisions

A FactPack surfaced through System Assets & Knowledge SHALL still require the normal explicit frozen/checksum-valid Fact Boundary bind. KnowledgeCollection membership MUST NOT satisfy or bypass this gate.

#### Scenario: Collection contains frozen FactPack
- **WHEN** a KnowledgeCollection includes a frozen FactPack
- **THEN** the Project has no Fact Boundary until an authorized user explicitly binds that FactPack
