## MODIFIED Requirements

### Requirement: Project workspace

The frontend SHALL present ContentProject as the business root and provide overview, brief, evidence, assets, matrix, versions, and activity tabs with URL-addressable tab state. For persisted projects, all seven tabs SHALL load real backend state; Brief, Evidence, Versions, and Activity MUST NOT remain persistent placeholder panels.

#### Scenario: Open a persisted project tab
- **WHEN** the user opens any of the seven tabs for a backend-persisted ContentProject
- **THEN** the tab loads the corresponding real project data or a truthful empty state from the backend and can be opened directly by URL

#### Scenario: Reload project tab
- **WHEN** the user reloads a project URL on Brief, Evidence, Assets, Matrix, Versions or Activity
- **THEN** saved project state remains visible without depending on browser-only fixture data

### Requirement: Project assets

The frontend SHALL expose Project Shared Assets through a modal or drawer instead of permanently occupying the Production canvas. For persisted projects, the same project asset pool SHALL include explicit project uploads, system MaterialRevision references, and verified workflow-generated material revisions with source/provenance/rights distinctions.

#### Scenario: Open unified shared assets
- **WHEN** the user opens Project Shared Assets from a persisted project or Production Workspace
- **THEN** one dismissible asset browser shows project-upload, system-reference and workflow-generated items from backend state without duplicating the underlying material bytes
