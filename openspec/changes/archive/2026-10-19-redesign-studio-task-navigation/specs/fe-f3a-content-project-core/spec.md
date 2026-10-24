## ADDED Requirements

### Requirement: Task-oriented project entry and archive
The project workspace SHALL distinguish project ownership and reference management from the existing content production workspaces. Project lists SHALL support search, status filtering and pagination with URL-preserved state. New project creation SHALL have a separate addressable view with user-scoped draft retention, explicit save, pending-state duplicate prevention and truthful error states.

#### Scenario: Return from a project
- **WHEN** a user opens a project from a filtered page and returns
- **THEN** the list retains its search, status and page without creating or modifying projects

#### Scenario: Read-only user
- **WHEN** the current user lacks editor permissions or permission cannot be verified
- **THEN** project creation and visible project mutation controls are unavailable while readable records remain accessible

### Requirement: Project page responsibility groups
The project workspace SHALL expose overview, works, project resources and history groups while preserving every existing tab deep link and the current backend state. The default overview SHALL explain the current next action and link into existing production workspaces; management and archive actions SHALL be secondary.

#### Scenario: Existing project deep link
- **WHEN** a user opens tab=brief, evidence, assets, matrix, variants, execution, versions or activity
- **THEN** the corresponding existing content remains reachable under its responsibility group and no new workflow action occurs by navigation

#### Scenario: Opportunity-created empty project
- **WHEN** a newly converted project has no content units
- **THEN** the page explains that only the project and initial task brief exist and provides explicit routes to review the brief, sources and create a work without claiming content was generated

#### Scenario: Project switch during read
- **WHEN** a user changes project before previous read requests complete
- **THEN** stale responses do not replace the newly selected project's content
