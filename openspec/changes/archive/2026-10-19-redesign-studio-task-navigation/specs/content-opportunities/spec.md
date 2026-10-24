## ADDED Requirements

### Requirement: Task-oriented opportunity pages
The workspace SHALL provide separate URL-addressable list, recommendation detail, direction, source selection, history and advanced maintenance views. Default detail SHALL show recommendation reasons, suggested direction and source gaps before technical metadata or manual forms. Filters and pagination SHALL survive detail/back navigation.

#### Scenario: Daily recommendation review
- **WHEN** the owner opens a recommended opportunity
- **THEN** the latest persisted assessment is summarized and the owner can proceed without manually recreating it

### Requirement: Truthful assessment provenance and reference preview
The workspace SHALL distinguish daily automatic evaluations, system corrections, manual assessments and missing provenance using returned metadata. Sources SHALL offer original links or authorized read-only document text; missing text and request errors remain explicit.

#### Scenario: System correction
- **WHEN** a system-authored correction is the latest revision
- **THEN** it is identified as a system revision rather than falsely labeled a fresh model evaluation

#### Scenario: Unavailable analysis
- **WHEN** assessment or source text is absent or failed
- **THEN** the page preserves the absence/error and does not invent analysis or re-run the model on page open

### Requirement: Explicit creation from the task flow
The final creation action SHALL explicitly qualify a new/watching opportunity if necessary, then use the existing revision-bound idempotent conversion. Direction drafts and selected source references SHALL persist within current user/opportunity/revision scope. Suggested identity or form SHALL NOT be silently turned into a production unit, approved evidence or delivery authorization.

#### Scenario: Confirm creation
- **WHEN** the owner confirms the creation summary for a new evaluated opportunity
- **THEN** qualification and conversion are explicit audited requests and the UI opens the resulting project with the next creation step

#### Scenario: Stale or repeated creation
- **WHEN** conversion returns conflict or the opportunity already has a project
- **THEN** the UI preserves inputs or opens the existing project without automatic retry or duplicate creation

#### Scenario: Source selection
- **WHEN** the owner selects source-document references
- **THEN** only selected documents are passed as project sources, with no automatic promotion to facts or rights
