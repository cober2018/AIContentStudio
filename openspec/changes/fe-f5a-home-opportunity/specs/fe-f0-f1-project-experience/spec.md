## MODIFIED Requirements

### Requirement: Product shell
The frontend SHALL offer nine primary workspaces with navigable routes and loading, error, and empty views. Existing frontend pages SHALL remain reachable, using legacy aliases when a path is repurposed for a primary workspace. `/identities` SHALL load a persistent Content Identity workspace rather than a long-lived placeholder. `/review` SHALL load a persistent, project-first Review & Distribution workspace rather than a placeholder; `/review-publish` SHALL remain available for legacy Topic workflows.

#### Scenario: Browse primary navigation
- **WHEN** the user opens the application shell
- **THEN** nine primary workspaces are visible and each link resolves to a page or scoped placeholder

#### Scenario: Open identities
- **WHEN** the user opens `/identities`
- **THEN** the application loads backend Brand/Persona/Account/Series state and does not substitute browser fixture identity data

#### Scenario: Open project review
- **WHEN** the user opens `/review`
- **THEN** the workspace loads authorized ContentProjects and ContentUnits from backend state, not browser fixtures or a placeholder

`/home` and `/opportunities` SHALL be real persistent workspaces. Opportunity detail SHALL be addressable at `/opportunities/:id`.

#### Scenario: Open Home
- **WHEN** the user opens `/home`
- **THEN** backend Opportunity/Project/decision projections load with truthful loading/error/empty states

#### Scenario: Open Opportunities
- **WHEN** the user opens `/opportunities`
- **THEN** persisted Opportunity state loads without browser fixture substitution

### Requirement: Project workspace

The frontend SHALL present ContentProject as the business root and provide overview, brief, evidence, assets, matrix, versions, and activity tabs with URL-addressable tab state. For persisted projects, all seven tabs SHALL load real backend state; Brief, Evidence, Versions, and Activity MUST NOT remain persistent placeholder panels.

#### Scenario: Open a persisted project tab
- **WHEN** the user opens any of the seven tabs for a backend-persisted ContentProject
- **THEN** the tab loads the corresponding real project data or a truthful empty state from the backend and can be opened directly by URL

#### Scenario: Reload project tab
- **WHEN** the user reloads a project URL on Brief, Evidence, Assets, Matrix, Versions or Activity
- **THEN** saved project state remains visible without depending on browser-only fixture data

A ContentProject SHALL expose origin Opportunity provenance when created by conversion. Existing Projects without Opportunity origin SHALL remain valid.

#### Scenario: Converted project
- **WHEN** a converted Project is opened
- **THEN** Project can navigate back to its origin Opportunity without copying Opportunity state into Project
