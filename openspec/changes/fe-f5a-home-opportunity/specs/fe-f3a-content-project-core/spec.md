## MODIFIED Requirements

### Requirement: Immutable CreativeBrief revisions

Opportunity conversion MAY create CreativeBrief revision 1 from the selected Assessment and explicit user overrides. When created, it SHALL become a normal immutable Brief revision.

#### Scenario: Prefilled Brief
- **WHEN** conversion creates Brief v1
- **THEN** recommendations are copied as editable project inputs and later Opportunity changes do not rewrite the Brief

### Requirement: Project Sources reference existing SourceDocument records

Conversion MAY attach selected SourceDocument signals through normal ProjectSourceBinding, and the binding SHALL preserve the existing source reference semantics.

#### Scenario: Attach Opportunity source
- **WHEN** a selected signal references SourceDocument
- **THEN** Project gets a Source binding and no raw source body is copied

### Requirement: Immutable project Fact Boundary revisions

Opportunity conversion MUST NOT create or bind Fact Boundary implicitly.

#### Scenario: Sources but no boundary
- **WHEN** a converted Project has attached Sources
- **THEN** Fact Boundary stays absent until explicit freeze/bind

### Requirement: Append-only project activity

Conversion SHALL record `project.created_from_opportunity` with Opportunity and Assessment revision references.

#### Scenario: Record origin event
- **WHEN** a conversion transaction commits
- **THEN** the project event is committed with the project, Brief, and selected source bindings, and a failed transaction records no event
