# fe-f0-f1-project-experience Specification

## Purpose
Define the local/mock frontend product shell and ContentProject experience delivered in FE-F0-F1. This specification does not imply backend persistence or FE-F2 workflow debugging.
## Requirements
### Requirement: Product shell
The frontend SHALL offer nine primary workspaces with navigable routes and loading, error, and empty views. Existing frontend pages SHALL remain reachable, using legacy aliases when a path is repurposed for a primary workspace.

#### Scenario: Browse primary navigation
- **WHEN** the user opens the application shell
- **THEN** nine primary workspaces are visible and each link resolves to a page or scoped placeholder

### Requirement: Project workspace
The frontend SHALL present ContentProject as the business root and provide overview, brief, evidence, assets, matrix, versions, and activity tabs with URL-addressable tab state.

#### Scenario: Open a project tab
- **WHEN** the user opens a project and selects any of the seven tabs
- **THEN** the selected panel appears and its URL can be opened directly

### Requirement: Content matrix editing
The frontend SHALL let the user add, edit, and delete Content Units in local mock state. A Content Unit MUST show identity, modality, channel, workflow reference, and status.

#### Scenario: Edit a unit
- **WHEN** the user changes a unit's identity, modality, channel, workflow, or title and saves
- **THEN** the matrix displays the new values without changing unrelated units

### Requirement: Project assets
The frontend SHALL expose Project Shared Assets through a modal or drawer and include uploaded, system-referenced, and workflow-generated mock revisions.

#### Scenario: Open shared assets
- **WHEN** the user selects the shared-assets entry from a project or production page
- **THEN** a dismissible asset browser opens without permanently occupying the production canvas

### Requirement: Production entry and status semantics
The frontend SHALL navigate from a selected Content Unit to a project-scoped Production Workspace shell. Blocked, stale, unknown, ready, and waiting_human MUST have distinct labels and visual treatments.

#### Scenario: Abnormal project
- **WHEN** the user opens the abnormal fixture
- **THEN** blocked, stale, and unknown units are visibly distinguishable and their meanings are explained
