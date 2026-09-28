## MODIFIED Requirements

### Requirement: Project-shared workflow outputs

ProjectWorkflowOutput SHALL continue to preserve verified Draft, MaterialRevision and Candidate outputs. It MAY additionally associate `content_master_revision` only when a workflow node actually emits a persisted `content_master_revision_id` that belongs to the same ContentUnit/Run lineage. F6A does not require existing plugins to emit Master revisions.

#### Scenario: Verified future Master output
- **WHEN** a workflow node emits a real ContentMasterRevision created for its own ContentUnit
- **THEN** ProjectWorkflowOutput may associate it with run/node/attempt provenance

#### Scenario: Raw Master ID
- **WHEN** a step reports a ContentMasterRevision from another unit or without valid lineage
- **THEN** no ProjectWorkflowOutput association is created

### Requirement: Modality production shells

The frontend SHALL provide a common Production control shell plus explicit Text/Graphic/Video modality extension points. The common shell owns project context, frozen identity, workflow run/debugger and Shared Assets; the modality shell owns content-specific revision UI. Content editing and Workflow design MUST remain separate explicit actions.

#### Scenario: Current Master
- **WHEN** a unit has ContentMaster revisions
- **THEN** Production shows the current revision/readiness/history alongside the existing workflow controls

#### Scenario: No Master yet
- **WHEN** a unit has no ContentMaster revision
- **THEN** the modality shell offers an explicit initialize/save path and does not invent a generated result
