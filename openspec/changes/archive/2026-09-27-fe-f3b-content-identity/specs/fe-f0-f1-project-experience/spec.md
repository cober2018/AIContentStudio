## MODIFIED Requirements

### Requirement: Product shell
The frontend SHALL offer nine primary workspaces with navigable routes and loading, error, and empty views. Existing frontend pages SHALL remain reachable, using legacy aliases when a path is repurposed for a primary workspace. `/identities` SHALL load a persistent Content Identity workspace rather than a long-lived placeholder.

#### Scenario: Browse primary navigation
- **WHEN** the user opens the application shell
- **THEN** nine primary workspaces are visible and each link resolves to a page or scoped placeholder

#### Scenario: Open identities
- **WHEN** the user opens `/identities`
- **THEN** the application loads backend Brand/Persona/Account/Series state and does not substitute browser fixture identity data

### Requirement: Content matrix editing
The frontend SHALL let the user add, edit, and delete Content Units through the backend project API. A Content Unit MUST show stable content Persona/Role identity, optional Account/Series, modality, channel, pinned workflow reference, IdentitySnapshot state, and status. On creation, the user SHALL be able to select the effective Persona/Account/Series × Modality default Workflow Template Version or an explicit project override. Browser-only FE-F0-F1 fixture data MUST remain clearly separate from real persisted projects and MUST NOT be imported without an explicit action.

#### Scenario: Edit a unit
- **WHEN** the user changes a unit's identity, modality, channel, workflow, or title and saves
- **THEN** the matrix displays the new values without changing unrelated units, and the values remain after reload

#### Scenario: Edit before execution history
- **WHEN** a unit has no Run, DataSnapshot, or generated output, even if it has a saved project workflow override, and the user explicitly rebinds identity, modality, or workflow
- **THEN** the unit MAY be edited in place; an incompatible old override is detached and the selected or current hierarchical default is pinned explicitly with a new IdentitySnapshot

#### Scenario: Replace after execution history
- **WHEN** a unit with Run, DataSnapshot, or generated output explicitly rebinds identity, modality, or workflow
- **THEN** a new unit receives the selected identity, IdentitySnapshot and workflow, the old unit is archived, and its runs and outputs remain readable under the old ID but cannot be mutated or re-executed

#### Scenario: Delete a unit
- **WHEN** the user deletes a unit without execution history
- **THEN** the unit is physically removed, including a saved override binding if present
- **WHEN** the unit has execution history
- **THEN** it is archived from the active matrix without deleting its history

#### Scenario: Browser demo data exists
- **WHEN** local FE-F0-F1 demo data exists and the user opens the real project list
- **THEN** no local item is silently written to or substituted for a backend project

#### Scenario: Choose identity default for a new unit
- **WHEN** the user creates a Content Unit with a Persona, optional Account/Series, and modality that have an effective current default Workflow Template Version
- **THEN** that version and its source scope are offered for selection and the saved unit pins the selected version without changing existing units

#### Scenario: Legacy unit
- **WHEN** an older unit has no IdentitySnapshot
- **THEN** the matrix and production entry mark identity as legacy/unknown until explicit rebind
