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
