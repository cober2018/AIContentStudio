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

The frontend SHALL present ContentProject as the business root and provide overview, brief, evidence, assets, matrix, versions, and activity tabs with URL-addressable tab state. For persisted projects, all seven tabs SHALL load real backend state; Brief, Evidence, Versions, and Activity MUST NOT remain persistent placeholder panels.

#### Scenario: Open a persisted project tab
- **WHEN** the user opens any of the seven tabs for a backend-persisted ContentProject
- **THEN** the tab loads the corresponding real project data or a truthful empty state from the backend and can be opened directly by URL

#### Scenario: Reload project tab
- **WHEN** the user reloads a project URL on Brief, Evidence, Assets, Matrix, Versions or Activity
- **THEN** saved project state remains visible without depending on browser-only fixture data

### Requirement: Content matrix editing
The frontend SHALL let the user add, edit, and delete Content Units through the backend project API. A Content Unit MUST show stable content Persona/Role identity, modality, channel, pinned workflow reference, and status. On creation, the user SHALL be able to select the current Persona × Modality default Workflow Template Version or an explicit project override. Browser-only FE-F0-F1 fixture data MUST remain clearly separate from real persisted projects and MUST NOT be imported without an explicit action.

#### Scenario: Edit a unit
- **WHEN** the user changes a unit's identity, modality, channel, workflow, or title and saves
- **THEN** the matrix displays the new values without changing unrelated units, and the values remain after reload

#### Scenario: Edit before execution history
- **WHEN** a unit has no Run, DataSnapshot, or generated output, even if it has a saved project workflow override, and the user changes identity, modality, or workflow
- **THEN** the unit MAY be edited in place; an incompatible old override is detached and the selected or current role default is pinned explicitly

#### Scenario: Replace after execution history
- **WHEN** a unit with Run, DataSnapshot, or generated output changes identity, modality, or workflow
- **THEN** a new unit receives the selected identity and workflow, the old unit is archived, and its runs and outputs remain readable under the old ID but cannot be mutated or re-executed

#### Scenario: Delete a unit
- **WHEN** the user deletes a unit without execution history
- **THEN** the unit is physically removed, including a saved override binding if present
- **WHEN** the unit has execution history
- **THEN** it is archived from the active matrix without deleting its history

#### Scenario: Browser demo data exists
- **WHEN** local FE-F0-F1 demo data exists and the user opens the real project list
- **THEN** no local item is silently written to or substituted for a backend project

#### Scenario: Choose role default for a new unit
- **WHEN** the user creates a Content Unit with a Persona and modality that have a current default Workflow Template Version
- **THEN** that version is offered for selection and the saved unit pins the selected version without changing existing units

### Requirement: Project assets

The frontend SHALL expose Project Shared Assets through a modal or drawer instead of permanently occupying the Production canvas. For persisted projects, the same project asset pool SHALL include explicit project uploads, system MaterialRevision references, and verified workflow-generated material revisions with source/provenance/rights distinctions.

#### Scenario: Open unified shared assets
- **WHEN** the user opens Project Shared Assets from a persisted project or Production Workspace
- **THEN** one dismissible asset browser shows project-upload, system-reference and workflow-generated items from backend state without duplicating the underlying material bytes

### Requirement: Production entry and status semantics
The frontend SHALL navigate from a selected Content Unit to a project-scoped Production Workspace shell. Blocked, stale, unknown, ready, and waiting_human MUST have distinct labels and visual treatments.

#### Scenario: Abnormal project
- **WHEN** the user opens the abnormal fixture
- **THEN** blocked, stale, and unknown units are visibly distinguishable and their meanings are explained
