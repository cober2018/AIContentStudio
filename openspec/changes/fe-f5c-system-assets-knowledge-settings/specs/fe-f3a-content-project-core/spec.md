## MODIFIED Requirements

### Requirement: Unified Project Shared Assets by reference

Project Shared Assets SHALL combine explicit project references to existing MaterialRevision rows with FE-F2 verified workflow-produced MaterialRevision associations. The system MUST NOT duplicate underlying material bytes merely to add an item to a project.

#### Scenario: Reference system material
- **WHEN** an editor adds an existing MaterialRevision to a project
- **THEN** an explicit project material reference is stored and the unified Shared Assets response returns its original revision/rights/provenance data

#### Scenario: Upload project material
- **WHEN** an editor uploads a material from the project
- **THEN** the existing material service creates Material + immutable MaterialRevision and the project stores only a reference to that revision

#### Scenario: Workflow material appears in same pool
- **WHEN** FE-F2 records a verified workflow-generated MaterialRevision in ProjectWorkflowOutput
- **THEN** the same project Shared Assets API displays it with source type `workflow` without creating a duplicate project material reference

#### Scenario: Detach explicit reference
- **WHEN** an editor detaches a project-upload/system-reference item
- **THEN** the project reference becomes inactive while the global MaterialRevision and workflow histories remain unchanged

#### Scenario: Upload transaction fails
- **WHEN** creating the project material reference or event fails after byte storage
- **THEN** the API does not report success or leave a committed MaterialRevision without its project reference; newly unreferenced bytes are cleaned up or tracked for bounded cleanup without deleting shared content

System Library MaterialRevision and SourceDocument resources SHALL enter a Project through existing reference bindings. System Assets & Knowledge does not replace the project Shared Assets pool or duplicate underlying resource bytes/text.

#### Scenario: Add system Material to Project
- **WHEN** the user selects a MaterialRevision from `/assets`
- **THEN** ProjectMaterialReference is created and the same MaterialRevision remains the underlying resource

#### Scenario: Add system Source to Project
- **WHEN** the user selects a SourceDocument from `/assets`
- **THEN** ProjectSourceBinding is created and the existing Source remains the underlying truth

### Requirement: Immutable project Fact Boundary revisions

A ContentProject SHALL represent its factual boundary through immutable ProjectFactBoundaryRevision rows that reference existing frozen FactPack versions. Creating a project boundary revision MUST NOT duplicate FactPack items. Only frozen FactPacks with a checksum MAY become a project boundary.

#### Scenario: Bind initial frozen FactPack
- **WHEN** an editor selects a frozen FactPack for a project with no prior Fact Boundary
- **THEN** boundary revision 1 records the FactPack ID, version and checksum

#### Scenario: Refuse mutable boundary
- **WHEN** an editor attempts to bind a draft FactPack as the current boundary
- **THEN** the request is rejected and the prior boundary remains current

#### Scenario: Clone, edit, freeze and advance boundary
- **WHEN** an editor clones the current boundary, edits the draft using existing FactPack operations, and uses the project freeze-and-bind action
- **THEN** the draft is frozen and a new immutable project boundary revision points to that new frozen FactPack while the old revision remains readable

#### Scenario: Concurrent boundary advancement
- **WHEN** two editors advance the same boundary revision concurrently
- **THEN** at most one new revision and event commit; the other request returns 409 and leaves the current boundary unchanged

Opportunity conversion MUST NOT create or bind Fact Boundary implicitly.

#### Scenario: Sources but no boundary
- **WHEN** a converted Project has attached Sources
- **THEN** Fact Boundary stays absent until explicit freeze/bind

A FactPack surfaced through System Assets & Knowledge SHALL still require the normal explicit frozen/checksum-valid Fact Boundary bind. KnowledgeCollection membership MUST NOT satisfy or bypass this gate.

#### Scenario: Collection contains frozen FactPack
- **WHEN** a KnowledgeCollection includes a frozen FactPack
- **THEN** the Project has no Fact Boundary until an authorized user explicitly binds that FactPack
