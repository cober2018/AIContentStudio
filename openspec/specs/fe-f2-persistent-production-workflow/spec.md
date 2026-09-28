# fe-f2-persistent-production-workflow Specification

## Purpose
Define the persistent project production workflow contract: versioned definitions and defaults, project-scoped runs and authorization, node execution and inspection, data snapshots, output lineage, and immutable identity context pinned to runs.
## Requirements
### Requirement: Project-scoped persistent workflow

The system SHALL persist ContentProject and ContentUnit records, associate a Content Unit with a stable Persona/Role identity, modality, and immutable workflow definition revision, and address every production run through its owning project and unit. A unit MAY have multiple historical runs; each run MUST pin the exact definition version and checksum used at creation. A new or explicitly rebound unit SHALL pin a server-created IdentitySnapshot; a WorkflowRun started from such a unit SHALL store the exact same snapshot ID. Historical units and runs without a snapshot SHALL remain explicitly legacy/unknown. A Project Candidate manifest SHALL preserve the exact WorkflowRun ID, version, and definition checksum that produced the reviewed content; later workflow changes MUST NOT rewrite it.

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

#### Scenario: Candidate pins producing run
- **WHEN** a candidate is frozen from a unit's persisted workflow output
- **THEN** its manifest records the producing run's exact workflow identity and checksum, which remain unchanged after a new workflow version is saved

### Requirement: Uniform project-run authorization across legacy APIs
Any WorkflowRun bound to a ContentUnit SHALL receive the same persisted Project/Unit ownership and action-specific authorization check whether accessed through a new project-scoped route or any legacy Workflow API. The check MUST happen before a response is serialized or a mutation starts. This includes run detail/list, attempt read, retry, node rerun, rerun-from-here, human completion, and cancel; legacy Workflow definition list/serialization, clone/publish, and raw create-run MUST NOT expose or operate on project-bound definitions outside the same boundary. Legacy Topic-only runs SHALL retain their existing behavior.

#### Scenario: Legacy raw run ID cannot bypass ownership
- **WHEN** a user without access to Project A requests its run or attempts, or invokes retry, rerun, rerun-from-here, human completion, or cancel through a legacy raw-ID endpoint
- **THEN** the request is denied before output disclosure or execution, with no new attempt or side effect

#### Scenario: Legacy list and definition entry points
- **WHEN** a user without access to Project A lists runs/workflows, clones or publishes its definition, or attempts to start a run by its raw workflow ID
- **THEN** Project A's run/definition is hidden or the operation is denied without revealing protected context or creating a project run

### Requirement: Safe workflow design and versioning
The production workspace SHALL allow an authorized editor to add, edit, disable, delete, and drag-and-drop reorder nodes in a project draft, with a keyboard/up-down alternative. Visual order SHALL be stored separately from dependency edges and input/output mappings: reordering MUST NOT silently add, remove, or redirect a dependency. Design Mode SHALL explicitly edit node configuration, input/output mappings, dependencies/connections, Provider/Model/Tool/Data Source, execution conditions, and failure policy. It SHALL show the changed visual order and unsaved state immediately, validate the full graph before save, and create a new immutable project override revision only on explicit save. Concurrent stale saves MUST return a conflict without overwriting the newer revision. Data, AI, Tool, Rule, Human, and System SHALL be distinct node types with type-aware configuration and execution eligibility; unsupported executors MUST be shown as blocked, not as successful.

#### Scenario: Invalid dependency
- **WHEN** a draft contains a missing prerequisite, duplicate node ID, or dependency cycle
- **THEN** the server rejects the save and the previous runnable revision remains unchanged

#### Scenario: Conflicting save
- **WHEN** another editor has saved a newer revision after the current page loaded
- **THEN** the stale save returns a conflict instead of overwriting the newer revision

#### Scenario: Drag and keyboard reorder without rewiring
- **WHEN** an editor drags a node or moves it with the keyboard alternative
- **THEN** the visible order and unsaved indicator update, the dependency edges and mappings remain unchanged, and a valid saved definition reloads in the new visual order

#### Scenario: Explicit graph and mapping edit
- **WHEN** an editor changes a dependency, execution condition, or input/output mapping in the inspector
- **THEN** the changed graph or mapping is shown as unsaved and the server rejects a missing dependency, duplicate node ID, cycle, invalid mapping, unsupported executor, or prohibited side effect before replacing the runnable revision

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

### Requirement: Snapshot-backed Data Node
A Data Node SHALL use a typed, extensible Data Source Plugin registry distinct from Tool nodes. Its descriptor SHALL expose key, name, category, connection mode, search/query/snapshot capabilities, configuration schema, result schema, and server-derived availability/reason. The registry and selector SHALL represent internal data, media data, Notion, Obsidian, API, and SQL/Database without making Studio Source the only possible implementation. A configured executable plugin SHALL persist an immutable bounded snapshot with source/version identity, checksum, lineage, normalized output, and refresh time; downstream nodes SHALL consume its snapshot ID. Changed refresh output MUST mark actual dependent outputs stale; unchanged output MUST NOT stale them. Disconnected or unverified plugins MUST be visibly unavailable and MUST NOT execute successfully.

#### Scenario: Changed source
- **WHEN** a configured read-only Data Node refreshes and its new snapshot hash differs
- **THEN** the previous snapshot remains inspectable and dependent succeeded outputs become stale

#### Scenario: Unavailable source
- **WHEN** the selected plugin is not configured or access is denied
- **THEN** the node is blocked with a reason and no synthetic successful snapshot is created

#### Scenario: Select a disconnected plugin
- **WHEN** an editor selects Notion, Obsidian, media data, API, or SQL without a verified connector
- **THEN** the selector retains the typed plugin configuration but labels it disconnected/unexecutable, and Run Node cannot produce a successful attempt

#### Scenario: Unchanged source
- **WHEN** a Data Node refresh produces the same normalized output checksum
- **THEN** the new refresh remains auditable without marking dependent successful steps stale

The typed Data Source Plugin registry SHALL remain authoritative for Data Node availability/capabilities. Product Settings MAY expose and manage related connector configuration, but MUST NOT create a second plugin registry or mark an unavailable plugin executable without verified runtime support.

#### Scenario: Settings shows disconnected plugin
- **WHEN** a registered Data Source Plugin is unavailable
- **THEN** Settings shows the same unavailable reason that prevents Data Node execution

#### Scenario: Connector configuration does not imply plugin executor
- **WHEN** a generic Connector is configured
- **THEN** Data Source Plugin execution eligibility changes only through its explicit verified runtime contract

### Requirement: Project-shared workflow outputs

The system SHALL persist references to supported workflow-produced Draft, MaterialRevision, and Candidate outputs with owning project, unit, run, node, attempt, and applicable source/rights provenance. Generated image, chart, screenshot, and video-clip revisions SHALL appear in the owning project's Shared Assets. FE-F3A MAY add explicit project MaterialRevision references for project upload/system-library use, but those references SHALL remain a separate persistence source from ProjectWorkflowOutput. The project Shared Assets API SHALL unify both sources at read time and MUST NOT create a synthetic material, duplicate bytes, or infer an asset merely because a node reports success. Freezing a Project Candidate SHALL verify that every referenced Draft, Candidate, and workflow output belongs to the requested ContentUnit through persisted output/run lineage. A raw output ID alone MUST NOT establish ownership.

#### Scenario: Workflow material and explicit material coexist
- **WHEN** a project has both explicit MaterialRevision references and a verified workflow-generated MaterialRevision
- **THEN** the Shared Assets response includes both with distinct source types and preserves the workflow item's run/node/attempt provenance

#### Scenario: Explicit detach does not erase workflow history
- **WHEN** an editor detaches an explicit project material reference
- **THEN** any separate ProjectWorkflowOutput association to the same MaterialRevision remains intact and historical runs are not modified

#### Scenario: Reject unrelated output at freeze
- **WHEN** a candidate-freeze request references a Draft or workflow output from another ContentUnit
- **THEN** the server rejects the request without creating a Candidate or disclosing the foreign output

ProjectWorkflowOutput SHALL continue to preserve verified Draft, MaterialRevision and Candidate outputs. It MAY additionally associate `content_master_revision` only when a workflow node actually emits a persisted `content_master_revision_id` that belongs to the same ContentUnit/Run lineage. F6A does not require existing plugins to emit Master revisions.

#### Scenario: Verified future Master output
- **WHEN** a workflow node emits a real ContentMasterRevision created for its own ContentUnit
- **THEN** ProjectWorkflowOutput may associate it with run/node/attempt provenance

#### Scenario: Raw Master ID
- **WHEN** a step reports a ContentMasterRevision from another unit or without valid lineage
- **THEN** no ProjectWorkflowOutput association is created

### Requirement: Modality production shells
The frontend SHALL provide distinct text, graphic, and video Production Workspace shells for a selected Content Unit, each with the same project-scoped workflow mini canvas, node inspector, explicit save/run controls, and a compact Project Shared Assets entry.

#### Scenario: Open a video unit
- **WHEN** the user opens a video Content Unit from the project matrix
- **THEN** the video workspace loads with that unit's persisted workflow and without a permanently open asset browser

The frontend SHALL provide a common Production control shell plus explicit Text/Graphic/Video modality extension points. The common shell owns project context, frozen identity, workflow run/debugger and Shared Assets; the modality shell owns content-specific revision UI. Content editing and Workflow design MUST remain separate explicit actions.

#### Scenario: Current Master
- **WHEN** a unit has ContentMaster revisions
- **THEN** Production shows the current revision/readiness/history alongside the existing workflow controls

#### Scenario: No Master yet
- **WHEN** a unit has no ContentMaster revision
- **THEN** the modality shell offers an explicit initialize/save path and does not invent a generated result
