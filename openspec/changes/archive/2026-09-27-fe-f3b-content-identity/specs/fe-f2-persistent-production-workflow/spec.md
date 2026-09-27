## MODIFIED Requirements

### Requirement: Project-scoped persistent workflow

The system SHALL persist ContentProject and ContentUnit records, associate a Content Unit with a stable Persona/Role identity, modality, and immutable workflow definition revision, and address every production run through its owning project and unit. A unit MAY have multiple historical runs; each run MUST pin the exact definition version and checksum used at creation. A new or explicitly rebound unit SHALL pin a server-created IdentitySnapshot; a WorkflowRun started from such a unit SHALL store the exact same snapshot ID. Historical units and runs without a snapshot SHALL remain explicitly legacy/unknown.

#### Scenario: Reload a saved project workflow
- **WHEN** an editor saves a valid project workflow override and reloads the selected Content Unit
- **THEN** the same saved revision and ordered nodes are returned from the backend, and prior revisions remain available to existing runs

#### Scenario: Designer shows the pinned workflow
- **WHEN** a Persona default advances from v1 to v2 after a Content Unit pinned v1, without a project override
- **THEN** the unit's effective-workflow read and Design Mode still return v1, and a new Run executes v1 until an explicit rebind

#### Scenario: Reject unrelated run
- **WHEN** a user requests a run ID through a different project or Content Unit
- **THEN** the server denies access without returning the run's nodes, inputs, or outputs

#### Scenario: Identity changes after run
- **WHEN** Brand/Persona/Account/Series receives newer revisions after a Run starts
- **THEN** the historical Run continues to reference its original IdentitySnapshot and workflow definition

### Requirement: Persona × Modality default workflow versions

The system SHALL persist a content Persona/Role identity and a current default Workflow Template Version for each Persona × Modality binding. An authorized editor SHALL be able to explicitly save a project draft as a new immutable version of that binding, separate from saving a project override, only after a server-side portability check. Existing PersonaWorkflowDefault remains valid. FE-F3B SHALL add Account × Modality and Series × Modality overrides without replacing Persona defaults. Effective selection SHALL prefer Series, then Account, then Persona. Existing units, overrides and runs MUST NOT be silently rebound when any default version advances. Authentication roles MUST NOT be treated as content Personas.

The portable default MAY contain node structure, dependency edges, plugin types, generic configuration, parameter templates, rules, model policy, and authorized reusable connection/profile references. It MUST NOT freeze the current project/unit/run ID, DataSnapshot ID, project AssetRevision/Draft/Candidate ID, attempt ID, or actual node output. A project-bound value MAY be converted into an explicit placeholder/context binding only when the server can prove that conversion safe; otherwise the server MUST reject the default save and leave prior bindings unchanged.

#### Scenario: Save a new role default
- **WHEN** an authorized editor explicitly chooses “save as new role default” for a Persona and modality with a valid draft and current binding revision
- **THEN** the backend creates a new immutable Workflow Template Version, advances only that Persona × Modality default binding, and makes it selectable by later Content Units

#### Scenario: Preserve a project override
- **WHEN** an editor saves a project override or a newer role default is published
- **THEN** existing Content Units and historical runs retain their pinned definition versions until explicitly rebound

#### Scenario: Reject conflicting default update
- **WHEN** a role-default binding changed after the editor loaded it
- **THEN** saving a new default returns a conflict without overwriting the newer binding

#### Scenario: Parameterize or reject project-bound values
- **WHEN** a project workflow draft contains project-specific identifiers or actual attempt output and an editor saves it as a default
- **THEN** the server stores only safe placeholders/context bindings for parameterizable fields and rejects any non-portable field without publishing a new default version

#### Scenario: Placeholder resolution boundary
- **WHEN** a project or unit binding appears in node config, which runtime resolves
- **THEN** the portability gate MAY parameterize it
- **WHEN** such a binding appears in input mapping, condition, or another node field not resolved by runtime
- **THEN** the default save is rejected rather than storing an inert placeholder

#### Scenario: Prevent cross-project template leakage
- **WHEN** a later Content Unit in Project B selects the default created from Project A
- **THEN** the selected definition contains no Project A run, snapshot, asset revision, draft, candidate, attempt, or actual output reference

#### Scenario: Resolve hierarchy workflow preference
- **WHEN** a unit is bound to Series and Account
- **THEN** effective default resolution uses Series then Account then Persona and returns the source scope

#### Scenario: Scoped default portability
- **WHEN** an editor saves Account or Series default from a project workflow
- **THEN** the same FE-F2 server portability gate and immutable Workflow version rules apply

### Requirement: Real node execution and inspection

The system SHALL execute supported nodes through the backend engine, persist step status, output and attempt history, and show the server result in the selected unit's mini canvas and inspector. It MUST refuse unsupported or side-effectful generic reruns. Identity updates MUST NOT change the identity context of an existing WorkflowRun.

#### Scenario: Run safe node
- **WHEN** an editor runs a supported non-side-effect node with satisfied prerequisites
- **THEN** a backend attempt is recorded and the canvas displays the persisted result after reload

#### Scenario: Node kind and failed rerun output
- **WHEN** a six-kind node is persisted as a step
- **THEN** its node_type records the actual kind
- **WHEN** a formerly successful node fails on rerun
- **THEN** the failed attempt has no prior successful output, while the old successful attempt remains readable

#### Scenario: Unsafe rerun
- **WHEN** an editor requests generic rerun of a delivery or other side-effect node
- **THEN** execution is rejected without a second external action

#### Scenario: Run inspector
- **WHEN** a user inspects a historical Run
- **THEN** the run view uses its frozen IdentitySnapshot or explicit legacy/unknown state, not current hierarchy settings
