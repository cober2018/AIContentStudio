## MODIFIED Requirements

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
