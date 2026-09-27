## MODIFIED Requirements

### Requirement: Content matrix editing
The frontend SHALL let the user add, edit, and delete Content Units through the backend project API. A Content Unit MUST show stable content Persona/Role identity, modality, channel, pinned workflow reference, and status. On creation, the user SHALL be able to select the current Persona × Modality default Workflow Template Version or an explicit project override. Browser-only FE-F0-F1 fixture data MUST remain clearly separate from real persisted projects and MUST NOT be imported without an explicit action.

#### Scenario: Edit a unit
- **WHEN** the user changes a unit's identity, modality, channel, workflow, or title and saves
- **THEN** the matrix displays the new values without changing unrelated units, and the values remain after reload

#### Scenario: Browser demo data exists
- **WHEN** local FE-F0-F1 demo data exists and the user opens the real project list
- **THEN** no local item is silently written to or substituted for a backend project

#### Scenario: Choose role default for a new unit
- **WHEN** the user creates a Content Unit with a Persona and modality that have a current default Workflow Template Version
- **THEN** that version is offered for selection and the saved unit pins the selected version without changing existing units
